"""Simulazione di un portafoglio di clienti: alert, quota alla banca, cost to serve.

Responsabile: Utente 2 · branch `dati-economia`.

Uso (dalla cartella del repo):
    python scripts/simula_portafoglio.py               # 600 clienti per scenario
    python scripts/simula_portafoglio.py --clienti 1500 --seed 7

Scrive:
    risultati/simulazione_portafoglio.md   report leggibile (da portare nel pitch)
    risultati/sensibilita.csv              tabella completa

Metodo, in breve
- Ogni cliente ha 2 anni di storico: il primo anno serve a imparare le abitudini, sul
  secondo si contano gli alert.
- Le frodi sono sovra-campionate (10% dei clienti) per avere abbastanza casi da misurare
  il tasso di intercettazione. Alert e costi vengono poi ricalcolati alla prevalenza
  realistica (1% di clienti frodati all'anno, ipotesi da calibrare): gli alert sui clienti
  legittimi non dipendono dalla prevalenza, quelli sulle frodi sì.
- Ogni alert viene instradato con workflow.instrada (conflitto d'interesse -> banca);
  una quota dei contatti non risponde in tempo e il caso passa alla banca.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from sentinel.economics import applica_soglia_contanti, punteggia_portafoglio  # noqa: E402
from sentinel.profiles import _EVENTI_LEGITTIMI, genera_portafoglio  # noqa: E402
from sentinel.workflow import instrada  # noqa: E402

PREVALENZA_REALE = 0.01      # clienti frodati all'anno (ipotesi)
PREVALENZA_SIM = 0.10        # sovra-campionamento per misurare l'intercettazione
COSTO_FALSO_ALLARME = 5.0    # CHF: disturbo al contatto per un alert legittimo
BASE = dict(soglia_contanti=None, quota_non_risponde=0.15, costo_caso_banca=15.0,
            costo_infrastruttura=2.0, eventi_legittimi=None, prob_contatto_con_procura=0.5)


def _quota_conflitti(alert: pd.DataFrame) -> float:
    if len(alert) == 0:
        return 0.0
    dest = [instrada({"avviato_da": r.avviato_da, "beneficiario": r.beneficiario},
                     {"nome": "contatto", "ha_procura": bool(r.contatto_procura),
                      "cointestatario": False})[0] for r in alert.itertuples()]
    return dest.count("banca") / len(dest)


def soglia_ottimale_pesata(scored: pd.DataFrame) -> float:
    """Soglia di costo minimo alla prevalenza REALE (le frodi sovra-campionate pesano meno)."""
    peso = PREVALENZA_REALE / PREVALENZA_SIM
    migliore, costo_min = 0.0, np.inf
    for s in np.arange(0, 12.5, 0.5):
        allarme = scored["punteggio"] >= s
        costo = ((allarme & ~scored["frode"]).sum() * COSTO_FALSO_ALLARME
                 + scored.loc[~allarme & scored["frode"], "importo"].sum() * peso)
        if costo <= costo_min:  # a parità di costo: soglia più alta, meno disturbo
            migliore, costo_min = float(s), costo
    return migliore


def metriche(scored: pd.DataFrame, soglia: float, p: dict) -> dict:
    n = scored["cliente"].nunique()
    clienti_frodati = scored.loc[scored["frode"], "cliente"].unique()
    alert = scored[scored["punteggio"] >= soglia]
    legit = alert[~alert["frode"]]
    fraud = alert[alert["frode"]]
    # alert per cliente all'anno alla prevalenza reale
    a_legit = len(legit) / n
    a_fraud = (len(fraud) / max(len(clienti_frodati), 1)) * PREVALENZA_REALE
    alert_anno = a_legit + a_fraud
    q_confl = (_quota_conflitti(legit) * a_legit + _quota_conflitti(fraud) * a_fraud) / max(alert_anno, 1e-9)
    q_banca = q_confl + (1 - q_confl) * p["quota_non_risponde"]
    casi_banca = alert_anno * q_banca
    # intercettazione per profilo: cliente frodato con almeno un'operazione di frode sopra soglia
    fr = scored[scored["frode"]].groupby(["profilo", "cliente"])["punteggio"].max() >= soglia
    per_profilo = fr.groupby("profilo").mean()
    # importo protetto: dal primo alert in poi l'episodio si ferma; prima, il denaro è perso
    tot, persi = {}, {}
    for (prof, _), g in scored[scored["frode"]].sort_values("data").groupby(["profilo", "cliente"]):
        sopra = (g["punteggio"] >= soglia).to_numpy()
        primo = int(sopra.argmax()) if sopra.any() else len(g)
        tot[prof] = tot.get(prof, 0.0) + g["importo"].sum()
        persi[prof] = persi.get(prof, 0.0) + g["importo"].iloc[:primo].sum()
    protetto = {k: 1 - persi[k] / tot[k] for k in tot if tot[k] > 0}
    protetto_tot = 1 - sum(persi.values()) / max(sum(tot.values()), 1e-9)
    return {
        "soglia": soglia,
        "alert/cliente/anno": round(alert_anno, 2),
        "di cui falsi allarmi": round(a_legit, 2),
        "quota contatto": round(1 - q_banca, 3),
        "quota banca": round(q_banca, 3),
        "di cui per conflitto d'interesse": round(q_confl, 3),
        "casi banca/cliente/anno": round(casi_banca, 3),
        "cost to serve CHF": round(p["costo_infrastruttura"] + casi_banca * p["costo_caso_banca"], 2),
        "intercettazione totale": round(float(fr.mean()), 3) if len(fr) else float("nan"),
        **{f"intercettazione {k}": round(float(v), 3) for k, v in per_profilo.items()},
        "importo protetto": round(float(protetto_tot), 3),
        **{f"importo protetto {k}": round(float(v), 3) for k, v in protetto.items()},
    }


def scenario(nome: str, clienti: int, seed: int, soglia: float | None = None, **override) -> dict:
    p = {**BASE, **override}
    port = genera_portafoglio(n_clienti=clienti, prob_frode=PREVALENZA_SIM,
                              prob_contatto_con_procura=p["prob_contatto_con_procura"],
                              eventi_legittimi=p["eventi_legittimi"], seed=seed)
    scored = applica_soglia_contanti(punteggia_portafoglio(port), p["soglia_contanti"])
    s = soglia if soglia is not None else soglia_ottimale_pesata(scored)
    print(f"  · {nome}", flush=True)
    return {"scenario": nome, **metriche(scored, s, p)}


def tabella_md(df: pd.DataFrame, colonne: list[str]) -> str:
    righe = ["| " + " | ".join(colonne) + " |", "|" + "---|" * len(colonne)]
    for _, r in df[colonne].iterrows():
        righe.append("| " + " | ".join(f"{v:.0%}" if isinstance(v, float) and ("quota" in c or "intercett" in c or "protetto" in c)
                                         else str(v) for c, v in zip(colonne, r)) + " |")
    return "\n".join(righe)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clienti", type=int, default=600)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    print(f"Scenario base ({a.clienti} clienti)…", flush=True)
    base = scenario("Base", a.clienti, a.seed)
    s = base["soglia"]
    print(f"Soglia ottimale: {s}. Analisi di sensibilità alla stessa soglia…", flush=True)
    pg = _EVENTI_LEGITTIMI["prelievo_grande"]
    righe = [base,
             scenario(f"Prelievi grandi legittimi: 1/anno (base {pg:g})", a.clienti, a.seed, s,
                      eventi_legittimi={"prelievo_grande": 1.0}),
             scenario("Prelievi grandi legittimi: 4/anno", a.clienti, a.seed, s,
                      eventi_legittimi={"prelievo_grande": 4.0}),
             scenario("Soglia contanti concordata: CHF 5'000", a.clienti, a.seed, s, soglia_contanti=5_000),
             scenario("Soglia contanti concordata: CHF 10'000", a.clienti, a.seed, s, soglia_contanti=10_000),
             scenario("Contatti che non rispondono: 25% (base 15%)", a.clienti, a.seed, s, quota_non_risponde=0.25),
             scenario("Contatti che non rispondono: 5%", a.clienti, a.seed, s, quota_non_risponde=0.05),
             scenario("Costo per caso alla banca: CHF 25 (base 15)", a.clienti, a.seed, s, costo_caso_banca=25.0),
             scenario("Contatto con procura (abuso interno): 25% (base 50%)", a.clienti, a.seed, s,
                      prob_contatto_con_procura=0.25)]
    df = pd.DataFrame(righe)

    os.makedirs("risultati", exist_ok=True)
    df.to_csv("risultati/sensibilita.csv", index=False)
    principali = ["scenario", "alert/cliente/anno", "quota banca", "cost to serve CHF",
                  "intercettazione totale", "importo protetto"]
    profili = ([c for c in df.columns if c.startswith("intercettazione ") and c != "intercettazione totale"]
               + [c for c in df.columns if c.startswith("importo protetto ")])
    b = df.iloc[0]
    md = f"""# Simulazione del portafoglio · risultati

*Generato il {date.today():%d.%m.%Y} con `python scripts/simula_portafoglio.py --clienti {a.clienti} --seed {a.seed}`. Dati interamente sintetici.*

## Scenario base

| Indicatore | Simulazione | Ipotesi del pitch (v6) |
|---|---|---|
| Alert per cliente all'anno | **{b['alert/cliente/anno']}** | ~1,5 |
| … di cui falsi allarmi | {b['di cui falsi allarmi']} | — |
| Risolti dal contatto | **{b['quota contatto']:.0%}** | ~80% |
| Passati alla banca | **{b['quota banca']:.0%}** (di cui {b["di cui per conflitto d'interesse"]:.0%} per conflitto d'interesse) | ~20% |
| Cost to serve per cliente | **CHF {b['cost to serve CHF']:.2f}** | CHF 7 |
| Frodi intercettate (almeno un alert nell'episodio) | **{b['intercettazione totale']:.0%}** | — |
| Importo protetto (fermato dal primo alert in poi) | **{b['importo protetto']:.0%}** | — |

Soglia di coinvolgimento: **{s}** (costo minimo con prevalenza delle frodi all'{PREVALENZA_REALE:.0%} e costo di un falso allarme CHF {COSTO_FALSO_ALLARME:.0f}).

Per tipo di minaccia:

{tabella_md(df.iloc[[0]], profili)}

## Analisi di sensibilità (stessa soglia)

{tabella_md(df, principali)}

## Come leggere i risultati

- **Perché l'intercettazione è così alta.** La soglia ottimale coinvolge il contatto per qualsiasi prelievo molto sopra le abitudini: le frodi vengono viste quasi sempre, ma il prezzo sono i falsi allarmi. È il compromesso centrale del prodotto, non un risultato "gratis". Con frodi reali più sottili l'intercettazione sarà più bassa: va verificata nel pilota.
- **Da dove vengono gli alert.** Quasi tutti i falsi allarmi sono prelievi allo sportello legittimi ma grandi (qualche migliaio di franchi). Il loro numero dipende da un'ipotesi che oggi non è verificata: quanti prelievi straordinari fa un over 65 in un anno.
- **La leva di prodotto.** Una soglia di importo sui contanti concordata tra persona e contatto riduce molto il disturbo; il prezzo da pagare è che i piccoli prelievi ripetuti (abuso interno) vengono intercettati meno. Va mostrato come scelta consapevole.
- **Cosa pesa sul cost to serve.** Le escalation alla banca: conflitti d'interesse (contatto con procura) e contatti che non rispondono in tempo.
- **Ipotesi da calibrare (Utente 1):** prevalenza delle frodi, frequenza dei prelievi straordinari, quota di clienti con una procura, tempo di risposta dei contatti.
"""
    with open("risultati/simulazione_portafoglio.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(df[principali].to_string(index=False))
    print("\nReport: risultati/simulazione_portafoglio.md")


if __name__ == "__main__":
    main()
