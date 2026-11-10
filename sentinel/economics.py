"""Risk economics: threshold choice, operational load, cost to serve, link to the pitch.

Owner: Utente 2 · branch `dati-economia`.

The threshold is not chosen for "accuracy" but by minimising the expected cost:

    C(t) = p_frode * L * FNR(t) + (1 - p_frode) * c_attrito * FPR(t)

where FNR = missed frauds, FPR = false alarms on legitimate operations.

Positioning (document v6): the loss avoided is a benefit for the CLIENT and the
family, NOT the argument for the price. In authorised-push scams the loss often
stays with the client; the bank pays for trust, retention of senior/affluent
clients, the link with the heirs and fewer complaints. The bridge between this
code and the business model is `stima_alert` -> cost to serve -> unit economics.

CONTRACT (stable signatures):
    curva_costo(score_legit, score_frode, par) -> (DataFrame, soglia)
    curva_roc(score_legit, score_frode) -> (DataFrame, auc)
    perdita_attesa_evitata(score_frode, soglia, par, frodi_attese_anno) -> (chf, tasso)
    punteggia_portafoglio(portafoglio) -> DataFrame              # adds 'punteggio'
    calibra_soglia(scored, ...) -> (DataFrame, soglia)
    stima_alert(scored, soglia, par=None, ...) -> dict            # PER CUSTOMER
    importo_protetto(scored, soglia) -> dict
    unit_economics_banca(scenario, cost_to_serve, ...) -> dict
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from sentinel.model import adatta_baseline, punteggia
from sentinel.workflow import Contatto, destinazione_finale

# ---------------------------------------------------------------- generic curves


@dataclass
class ParametriCosto:
    """Per-OPERATION cost parameters.

    p_frode is the prior that a single operation is fraudulent. With ~1% of customers
    defrauded per year, ~2 fraudulent operations per episode and ~350 operations per
    customer per year, p_frode ~ 0.01 * 2 / 350 ~ 6e-5. (An earlier version used 0.01,
    which overstates fraud ~170 times and pushes the threshold far too low.)
    """

    perdita: float = 10_000.0       # L: typical loss of a missed fraud operation (CHF)
    costo_attrito: float = 5.0      # cost of a false alarm: friction for the contact
    p_frode: float = 6e-5


def curva_costo(score_legit, score_frode, par: ParametriCosto | None = None,
                n: int = 101) -> tuple[pd.DataFrame, float]:
    """Expected cost, FPR and FNR as the threshold varies; also returns the optimal threshold."""
    par = par or ParametriCosto()
    sl = np.asarray(score_legit, dtype=float)
    sf = np.asarray(score_frode, dtype=float)
    righe = []
    for t in np.linspace(0.0, 1.0, n):
        fpr = float(np.mean(sl >= t)) if sl.size else 0.0
        fnr = float(np.mean(sf < t)) if sf.size else 0.0
        costo = par.p_frode * par.perdita * fnr + (1 - par.p_frode) * par.costo_attrito * fpr
        righe.append((t, fpr, fnr, costo))
    df = pd.DataFrame(righe, columns=["soglia", "fpr", "fnr", "costo_atteso"])
    minimo = df["costo_atteso"].min()
    soglia = float(df.loc[np.isclose(df["costo_atteso"], minimo), "soglia"].max())
    return df, soglia


def curva_roc(score_legit, score_frode) -> tuple[pd.DataFrame, float]:
    """ROC curve and AUC: how well the score separates, independently of costs."""
    sl = np.asarray(score_legit, dtype=float)
    sf = np.asarray(score_frode, dtype=float)
    soglie = np.linspace(0.0, 1.0, 201)
    fpr = np.array([float(np.mean(sl >= t)) if sl.size else 0.0 for t in soglie])
    tpr = np.array([float(np.mean(sf >= t)) if sf.size else 0.0 for t in soglie])
    ordine = np.argsort(fpr)
    auc = float(np.trapezoid(tpr[ordine], fpr[ordine]))
    return pd.DataFrame({"soglia": soglie, "fpr": fpr, "tpr": tpr}), auc


def perdita_attesa_evitata(score_frode, soglia: float, par: ParametriCosto | None = None,
                           frodi_attese_anno: float = 0.01) -> tuple[float, float]:
    """Expected loss avoided per customer per year = P(fraud) * loss * detection rate.

    A benefit for the client and the family (v6), not the justification of the price.
    """
    par = par or ParametriCosto()
    sf = np.asarray(score_frode, dtype=float)
    tasso = float(np.mean(sf >= soglia)) if sf.size else 0.0
    return frodi_attese_anno * par.perdita * tasso, tasso

# ---------------------------------------------------------------- portfolio


@dataclass
class ParametriServizio:
    """Operating costs of the service, per customer (CHF)."""

    costo_notifica: float = 0.50         # alert handled by the trusted contact in the app
    costo_revisione_banca: float = 15.0  # case escalated to the bank's manual review
    costo_base: float = 2.0              # platform and cloud, per customer per year


def punteggia_portafoglio(portafoglio: pd.DataFrame) -> pd.DataFrame:
    """For each customer, learn the habits on year 1 ('storico') and score year 2 ('valutazione')."""
    pezzi = []
    for _, cli in portafoglio.groupby("cliente", sort=False):
        base = adatta_baseline(cli[cli["periodo"] == "storico"])
        val = cli[cli["periodo"] == "valutazione"].copy()
        val["punteggio"] = punteggia(val, base)
        pezzi.append(val)
    return pd.concat(pezzi, ignore_index=True)


def _in_pausa(scored: pd.DataFrame, soglia: float) -> pd.Series:
    """Paused = own score above threshold OR flagged by the bank's antifraud."""
    return (scored["punteggio"] >= soglia) | scored["alert_banca"].astype(bool)


def _perdite_episodi(scored: pd.DataFrame, soglia: float) -> tuple[float, float, int, int]:
    """Fraud amount lost before the first pause (the episode stops there).

    Returns (lost, total, episodes detected, episodes)."""
    frodi = scored[scored["frode_reale"]].sort_values("data", kind="stable")
    persi = totale = 0.0
    visti = n = 0
    for _, ep in frodi.groupby("cliente", sort=False):
        pausa = _in_pausa(ep, soglia).to_numpy()
        primo = int(pausa.argmax()) if pausa.any() else len(ep)
        persi += float(ep["importo"].iloc[:primo].sum())
        totale += float(ep["importo"].sum())
        visti += int(pausa.any())
        n += 1
    return persi, totale, visti, n


def calibra_soglia(scored: pd.DataFrame, prevalenza_reale: float = 0.01,
                   costo_falso_allarme: float = 5.0, passo: float = 0.02) -> tuple[pd.DataFrame, float]:
    """Cost-optimal threshold on a simulated portfolio, at the REAL fraud prevalence.

    cost(t) per customer = false alarms * friction + money lost before the first pause.
    Fraud episodes may be oversampled in the simulation: they are re-weighted to
    `prevalenza_reale`. Ties go to the higher threshold (less disturbance).
    """
    n_clienti = scored["cliente"].nunique()
    clienti_frodati = scored.loc[scored["frode_reale"], "cliente"].nunique()
    prev_sim = clienti_frodati / n_clienti if n_clienti else 0.0
    peso = prevalenza_reale / prev_sim if prev_sim > 0 else 0.0
    legit = scored[~scored["frode_reale"]]
    righe = []
    for t in np.arange(0.0, 1.0 + 1e-9, passo):
        fa = float(_in_pausa(legit, t).sum()) / n_clienti
        persi, _, _, _ = _perdite_episodi(scored, t)
        perdita = persi / n_clienti * peso
        righe.append((round(float(t), 4), fa, perdita, fa * costo_falso_allarme + perdita))
    df = pd.DataFrame(righe, columns=["soglia", "falsi_allarmi_cliente", "perdita_cliente", "costo"])
    minimo = df["costo"].min()
    return df, float(df.loc[np.isclose(df["costo"], minimo), "soglia"].max())


def stima_alert(scored: pd.DataFrame, soglia: float, par: ParametriServizio | None = None,
                p_non_risposta: float = 0.15, seed: int = 0) -> dict:
    """Operational load PER CUSTOMER PER YEAR, and the cost to serve.

    The contact/bank split is MEASURED, not assumed: every paused operation is routed
    with workflow.destinazione_finale (conflict of interest -> bank; contact who does
    not answer within the window -> bank). Works on one customer or on a portfolio
    (column 'cliente'); expects one year of operations per customer.
    """
    par = par or ParametriServizio()
    rng = np.random.default_rng(seed)
    n_clienti = int(scored["cliente"].nunique()) if "cliente" in scored.columns else 1
    alert = scored[_in_pausa(scored, soglia)]
    procura = (alert["contatto_procura"].astype(bool) if "contatto_procura" in alert.columns
               else pd.Series(False, index=alert.index))
    conflitti = banca = 0
    for (_, op), proc in zip(alert.iterrows(), procura):
        contatto = Contatto("contatto", ha_procura=bool(proc))
        risponde = bool(rng.random() >= p_non_risposta)
        dest, motivo = destinazione_finale(op, contatto, risponde=risponde, minuti_trascorsi=30)
        if dest == "banca":
            banca += 1
            conflitti += int("did not answer" not in motivo)
    n = len(alert)
    alert_anno = n / n_clienti
    q_banca = banca / n if n else 0.0
    costo_var = alert_anno * ((1 - q_banca) * par.costo_notifica + q_banca * par.costo_revisione_banca)
    return {
        "alert_per_cliente_anno": round(alert_anno, 3),
        "quota_contatto": round(1 - q_banca, 3),
        "quota_banca": round(q_banca, 3),
        "quota_banca_conflitto": round(conflitti / n, 3) if n else 0.0,
        "casi_banca_per_cliente_anno": round(alert_anno * q_banca, 3),
        "costo_variabile": round(costo_var, 2),
        "cost_to_serve": round(par.costo_base + costo_var, 2),
    }


def importo_protetto(scored: pd.DataFrame, soglia: float) -> dict:
    """Share of fraud money stopped (from the first pause on), overall and per threat."""
    out = {}
    persi, totale, visti, n = _perdite_episodi(scored, soglia)
    out["episodi_intercettati"] = round(visti / n, 3) if n else float("nan")
    out["importo_protetto"] = round(1 - persi / totale, 3) if totale else float("nan")
    if "minaccia" in scored.columns:
        for m, g in scored[scored["frode_reale"]].groupby("minaccia"):
            p, t, v, k = _perdite_episodi(g, soglia)
            out[f"importo_protetto_{m}"] = round(1 - p / t, 3) if t else float("nan")
            out[f"episodi_intercettati_{m}"] = round(v / k, 3) if k else float("nan")
    return out

# ---------------------------------------------------------------- link to the pitch (v6, page 3)

SCENARI_BUSINESS = {
    "prudente": {"adesione": 0.03, "prezzo_mese": 2.00, "cac_banca": 120_000},
    "base": {"adesione": 0.08, "prezzo_mese": 2.50, "cac_banca": 100_000},
    "ottimistico": {"adesione": 0.15, "prezzo_mese": 2.50, "cac_banca": 60_000},
}


def unit_economics_banca(scenario: str, cost_to_serve: float, clienti_over65: int = 40_000,
                         churn_banca: float = 0.10) -> dict:
    """Unit economics of a typical bank (v6, page 3) for a given cost to serve.

    With cost_to_serve = 7 (8 in the prudent case) it reproduces the v6 table;
    plug in the simulated value to see the effect on the pitch.
    """
    s = SCENARI_BUSINESS[scenario]
    clienti = clienti_over65 * s["adesione"]
    contribution_cliente = s["prezzo_mese"] * 12 - cost_to_serve
    contribution = clienti * contribution_cliente
    ltv = contribution / churn_banca
    return {
        "clienti_protetti": round(clienti),
        "contribution_cliente": round(contribution_cliente, 2),
        "contribution_annua": round(contribution),
        "ltv_su_cac": round(ltv / s["cac_banca"], 1),
        "rientro_cac_mesi": round(s["cac_banca"] / (contribution / 12), 1) if contribution > 0 else float("inf"),
    }
