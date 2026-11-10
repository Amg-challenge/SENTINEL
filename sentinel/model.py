"""Decision engine: WHEN to involve the trusted contact.

Owner: Utente 1 · branch `modello`.

Sentinel does not replace the bank's antifraud system (e.g. NetGuardians): it
receives its alerts (column `alert_banca`, handled in workflow.decidi) and adds
what a payments-only system sees less well: the person's own habits, cash at the
counter, the safe deposit box, operations by a power-of-attorney holder.

Design choice: a TRANSPARENT, explainable score instead of a black box. FINMA asks
for governance and explainability of AI, and in the pitch we can show *why* an
operation was paused (see `spiega`).

Score in [0, 1] = sigmoid(bias + sum of contributions):
  - amount above the person's habits for that channel (cash / transfers / card),
    on a log scale and saturating, so CHF 3'600 and CHF 40'000 stay distinguishable
  - payee never seen before; foreign account; transfer
  - safe-deposit-box visit (weighted by how rarely the person goes there)
  - cassetta + counter withdrawal on the same day (typical fake-police pattern)
  - operation by the power-of-attorney holder, and their weekly total far above normal

Scope (v6): cash, safe deposit box and transfers. Card payments are OUT of scope -
they are covered by the bank's card antifraud - so they always score 0 here (they
still count in the baseline as part of the person's habits).

CONTRACT (stable signatures):
    adatta_baseline(storico) -> Baseline
    punteggio(tx, base) -> float                  # one operation (dict or Series)
    punteggia(df, base) -> np.ndarray             # one score per row
    spiega(tx, base) -> list[tuple[str, float]]   # human-readable reasons, largest first
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

GRUPPI = {"sportello": "contanti", "bancomat": "contanti", "bonifico": "bonifico", "carta": "carta"}

# Weights: starting values, to calibrate in notebooks/calibrazione.ipynb (Utente 1).
PESI: dict[str, float] = {
    "bias": -3.0,
    "importo": 4.0,             # max contribution of the amount term
    "soglia_sd": 3.0,           # tolerance: robust std devs above the median before it counts
    "scala_log": float(np.log(10)),  # a further 10x above tolerance ~ 76% of the max
    "beneficiario_nuovo": 2.0,
    "estero": 1.5,
    "bonifico": 0.5,
    "cassetta_base": 2.0,       # any safe-deposit-box visit
    "cassetta_rara": 1.5,       # extra if the person almost never goes there
    "combo_cassetta_contanti": 1.0,
    "procuratore": 1.0,
    "procuratore_eccesso": 2.0,
}
SD_MIN = 0.25  # floor on the log-scale spread: avoids over-sensitivity on very regular accounts


@dataclass
class Baseline:
    """Normal behaviour learned from one person's legitimate history."""

    per_gruppo: dict[str, tuple[float, float]]   # group -> (median log-amount, robust sd)
    globale: tuple[float, float]
    beneficiari_noti: set[str] = field(default_factory=set)
    accessi_cassetta_anno: float = 0.0
    procuratore_settimana: float = 0.0            # typical weekly total by the POA holder


def _robusto(x: np.ndarray) -> tuple[float, float]:
    if x.size == 0:
        return 0.0, 1.0
    med = float(np.median(x))
    return med, max(1.4826 * float(np.median(np.abs(x - med))), SD_MIN)


def adatta_baseline(storico: pd.DataFrame) -> Baseline:
    """Learn the normal behaviour from legitimate operations only."""
    legit = storico[~storico["frode_reale"].astype(bool)]
    con_importo = legit[legit["canale"] != "cassetta"]
    per_gruppo = {}
    for gruppo in set(GRUPPI.values()):
        canali = [c for c, g in GRUPPI.items() if g == gruppo]
        x = np.log1p(con_importo.loc[con_importo["canale"].isin(canali), "importo"].to_numpy(float))
        if x.size >= 5:
            per_gruppo[gruppo] = _robusto(x)
    globale = _robusto(np.log1p(con_importo["importo"].to_numpy(float)))
    noti = set(legit.loc[legit["beneficiario"] != "", "beneficiario"])
    giorni = max((legit["data"].max() - legit["data"].min()).days, 1) if legit["data"].notna().any() else 365
    accessi = float((legit["canale"] == "cassetta").sum()) * 365 / giorni
    proc = legit[legit["avviata_da"] == "procuratore"]
    settimanale = (proc.groupby(proc["data"].dt.to_period("W"))["importo"].sum().median()
                   if len(proc) and proc["data"].notna().any() else 0.0)
    return Baseline(per_gruppo, globale, noti, accessi, float(settimanale))


def _contributi(df: pd.DataFrame, base: Baseline, pesi: dict | None = None) -> pd.DataFrame:
    """One column per signal, one row per operation (vectorised)."""
    p = {**PESI, **(pesi or {})}
    out = pd.DataFrame(index=df.index)
    canale = df["canale"].astype(str)
    importo = df["importo"].astype(float).to_numpy()

    med = np.array([base.per_gruppo.get(GRUPPI.get(c, ""), base.globale)[0] for c in canale])
    sd = np.array([base.per_gruppo.get(GRUPPI.get(c, ""), base.globale)[1] for c in canale])
    eccesso = np.log1p(importo) - med - p["soglia_sd"] * sd
    out["importo"] = np.where(canale == "cassetta", 0.0,
                              p["importo"] * np.tanh(np.clip(eccesso, 0, None) / p["scala_log"]))

    nuovo = df["nuovo_beneficiario"].astype(bool) | (
        (df["beneficiario"] != "") & ~df["beneficiario"].isin(base.beneficiari_noti))
    out["beneficiario_nuovo"] = np.where(nuovo & (df["beneficiario"] != ""), p["beneficiario_nuovo"], 0.0)
    out["estero"] = np.where(df["estero"].astype(bool), p["estero"], 0.0)
    out["bonifico"] = np.where(canale == "bonifico", p["bonifico"], 0.0)

    rarita = 1.0 - min(base.accessi_cassetta_anno / 2.0, 1.0)
    out["cassetta"] = np.where(canale == "cassetta", p["cassetta_base"] + p["cassetta_rara"] * rarita, 0.0)

    combo = np.zeros(len(df))
    if df["data"].notna().any():
        giorno = df["data"].dt.normalize()
        giorni_cassetta = set(giorno[canale == "cassetta"].dropna())
        contanti_sopra = (canale == "sportello") & (out["importo"] > 0)
        con_cassetta = giorno.isin(giorni_cassetta)
        combo = np.where((contanti_sopra & con_cassetta) | ((canale == "cassetta") &
                         giorno.isin(set(giorno[contanti_sopra].dropna()))),
                         p["combo_cassetta_contanti"], 0.0)
    out["combo_cassetta_contanti"] = combo

    proc = (df["avviata_da"] == "procuratore").to_numpy()
    out["procuratore"] = np.where(proc, p["procuratore"], 0.0)
    eccesso_proc = np.zeros(len(df))
    if proc.any() and df["data"].notna().any() and base.procuratore_settimana > 0:
        sett = df["data"].dt.to_period("W")
        tot = df[proc].groupby(sett[proc])["importo"].sum()
        sopra = sett.map(tot).fillna(0).to_numpy() > 3 * base.procuratore_settimana
        eccesso_proc = np.where(proc & sopra, p["procuratore_eccesso"], 0.0)
    out["procuratore_eccesso"] = eccesso_proc
    out.loc[(canale == "carta").to_numpy(), :] = 0.0   # out of scope: bank's card antifraud
    return out


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def punteggia(df: pd.DataFrame, base: Baseline, pesi: dict | None = None) -> np.ndarray:
    """Anomaly score in [0, 1] for every row of a DataFrame of operations (0 for card payments)."""
    if len(df) == 0:
        return np.array([], dtype=float)
    p = {**PESI, **(pesi or {})}
    score = _sigmoid(p["bias"] + _contributi(df, base, p).sum(axis=1).to_numpy())
    return np.where(df["canale"].to_numpy() == "carta", 0.0, score)


def _come_df(tx) -> pd.DataFrame:
    r = dict(tx)
    r.setdefault("data", pd.NaT)
    r.setdefault("beneficiario", "")
    r.setdefault("nuovo_beneficiario", False)
    r.setdefault("estero", False)
    r.setdefault("avviata_da", "titolare")
    r.setdefault("alert_banca", False)
    r.setdefault("frode_reale", False)
    df = pd.DataFrame([r])
    df["data"] = pd.to_datetime(df["data"])
    return df


def punteggio(tx, base: Baseline, pesi: dict | None = None) -> float:
    """Score of a single operation (dict or pd.Series with canale/importo/...)."""
    return float(punteggia(_come_df(tx), base, pesi)[0])


ETICHETTE = {
    "importo": "amount far above this person's habits for the channel",
    "beneficiario_nuovo": "payee never seen before",
    "estero": "foreign account",
    "bonifico": "outgoing transfer",
    "cassetta": "safe deposit box visit (rare for this person)",
    "combo_cassetta_contanti": "safe deposit box and cash withdrawal on the same day",
    "procuratore": "initiated by the power-of-attorney holder",
    "procuratore_eccesso": "power-of-attorney withdrawals far above normal this week",
}


def spiega(tx, base: Baseline, pesi: dict | None = None) -> list[tuple[str, float]]:
    """Why this operation was scored as it was: (reason, contribution), largest first."""
    c = _contributi(_come_df(tx), base, pesi).iloc[0]
    return sorted(((ETICHETTE[k], round(float(v), 2)) for k, v in c.items() if v > 0.01),
                  key=lambda x: -x[1])
