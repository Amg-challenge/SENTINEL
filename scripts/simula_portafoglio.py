"""Portfolio simulation: alerts, contact/bank split, cost to serve, fraud protected,
and the effect on the unit economics of the pitch (document v6, page 3).

Owner: Utente 2 · branch `dati-economia`.

Usage (from the repo folder):
    python scripts/simula_portafoglio.py                 # 500 customers per run
    python scripts/simula_portafoglio.py --clienti 1000 --seed 7

Writes:
    results/simulation_report.md   readable report (numbers for the pitch)
    results/sensitivity.csv        full table

Method
- Each customer has two years: year 1 teaches the engine their habits, alerts are
  counted on year 2.
- Operational load (alerts, contact/bank split, cost to serve) is measured on a book
  at the REAL fraud prevalence (1% of customers per year, assumption to calibrate).
- Detection is measured on a separate book where frauds are oversampled (30%), so
  there are enough episodes to count; the threshold is calibrated on that book with
  frauds re-weighted to the real prevalence.
- Every paused operation is routed with workflow.destinazione_finale: conflict of
  interest -> bank; contact who does not answer within 30 minutes -> bank.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from sentinel import economics, profiles  # noqa: E402

PREVALENZA_REALE = 0.01
PREVALENZA_SIM = 0.30   # oversampled: more episodes -> more stable threshold


def _book(clienti, seed, prob_frode, **kw):
    return economics.punteggia_portafoglio(
        profiles.genera_portafoglio(n_clienti=clienti, prob_frode=prob_frode, seed=seed, **kw))


def run(nome, clienti, seed, soglia=None, detection=True, eventi=None, gen_kw=None,
        p_non_risposta=0.15, par=None):
    gen_kw = dict(gen_kw or {})
    print(f"  · {nome}", flush=True)
    det = {}
    if detection or soglia is None:
        sim = _book(clienti, seed + 1, PREVALENZA_SIM, eventi=eventi, **gen_kw)
        if soglia is None:
            _, soglia = economics.calibra_soglia(sim, prevalenza_reale=PREVALENZA_REALE)
        det = economics.importo_protetto(sim, soglia)
    reale = _book(clienti, seed, PREVALENZA_REALE, eventi=eventi, **gen_kw)
    carico = economics.stima_alert(reale, soglia, par=par, p_non_risposta=p_non_risposta, seed=seed)
    return {"scenario": nome, "threshold": soglia,
            "alerts/client/year": carico["alert_per_cliente_anno"],
            "resolved by contact": carico["quota_contatto"],
            "to the bank": carico["quota_banca"],
            "to the bank for conflict of interest": carico["quota_banca_conflitto"],
            "bank cases/client/year": carico["casi_banca_per_cliente_anno"],
            "cost to serve CHF": carico["cost_to_serve"],
            "fraud episodes caught": det.get("episodi_intercettati", float("nan")),
            "fraud money protected": det.get("importo_protetto", float("nan")),
            **{k.replace("importo_protetto_", "money protected · ").replace(
                "episodi_intercettati_", "episodes caught · "): v
               for k, v in det.items() if k.startswith(("importo_protetto_", "episodi_intercettati_"))}}


def fmt(v, col):
    if isinstance(v, float) and v != v:
        return "—"
    if isinstance(v, float) and any(w in col for w in ("resolved", "to the bank", "caught", "protected")) \
            and "cases" not in col:
        return f"{v:.0%}"
    return str(v)


def md_table(df, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df[cols].iterrows():
        out.append("| " + " | ".join(fmt(r[c], c) for c in cols) + " |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clienti", type=int, default=500)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    n, sd = a.clienti, a.seed

    print(f"Base scenario ({n} customers per book)…", flush=True)
    base = run("Base", n, sd)
    s = base["threshold"]
    print(f"Calibrated threshold: {s}. Sensitivity at the same threshold…", flush=True)
    pg = profiles.PRESET["anziano"].prelievi_straordinari
    rows = [base,
            run(f"Large legit cash withdrawals: 1/year (base {pg:g})", n, sd, s, eventi={"prelievi_straordinari": 1.0}),
            run("Large legit cash withdrawals: 4/year", n, sd, s, eventi={"prelievi_straordinari": 4.0}),
            run("Legit transfers abroad: 1.5/year (base 0.5)", n, sd, s, detection=False,
                eventi={"bonifici_esteri": 1.5}),
            run("Bank antifraud false positives: 1/year (base 0.3)", n, sd, s, detection=False,
                eventi={"falsi_alert_banca": 1.0}),
            run("Contacts not answering in 30 min: 30% (base 15%)", n, sd, s, detection=False, p_non_risposta=0.30),
            run("Contacts not answering in 30 min: 5%", n, sd, s, detection=False, p_non_risposta=0.05),
            run("Customers with a POA holder: 30% (base 15%)", n, sd, s, detection=False,
                gen_kw={"prob_procuratore": 0.30}),
            run("Bank review cost per case: CHF 25 (base 15)", n, sd, s, detection=False,
                par=economics.ParametriServizio(costo_revisione_banca=25.0))]
    df = pd.DataFrame(rows)

    print("Robustness: base scenario with two more seeds…", flush=True)
    rob = pd.DataFrame([base] + [run(f"Base, seed {sd + k}", n, sd + k) for k in (100, 200)])
    rob.loc[0, "scenario"] = f"Base, seed {sd}"

    # effect on the pitch's unit economics (v6 page 3)
    cts = base["cost to serve CHF"]
    ue = []
    for sc in economics.SCENARI_BUSINESS:
        v6 = economics.unit_economics_banca(sc, 8.0 if sc == "prudente" else 7.0)
        sim = economics.unit_economics_banca(sc, cts)
        ue.append({"business scenario": sc,
                   "contribution/client v6": v6["contribution_cliente"],
                   "contribution/client simulated": sim["contribution_cliente"],
                   "LTV/CAC v6": v6["ltv_su_cac"], "LTV/CAC simulated": sim["ltv_su_cac"],
                   "CAC payback months v6": v6["rientro_cac_mesi"],
                   "CAC payback months simulated": sim["rientro_cac_mesi"]})
    ue = pd.DataFrame(ue)

    os.makedirs("results", exist_ok=True)
    pd.concat([df, rob.iloc[1:]]).to_csv("results/sensitivity.csv", index=False)
    rng_ = {c: (rob[c].min(), rob[c].max()) for c in ["threshold", "alerts/client/year", "to the bank",
                                                       "cost to serve CHF", "fraud money protected"]}
    main_cols = ["scenario", "alerts/client/year", "to the bank", "cost to serve CHF",
                 "fraud episodes caught", "fraud money protected"]
    threat_cols = [c for c in df.columns if c.startswith(("money protected · ", "episodes caught · "))]
    b = df.iloc[0]
    report = f"""# Portfolio simulation · results

*Generated on {date.today():%d.%m.%Y} with `python scripts/simula_portafoglio.py --clienti {n} --seed {sd}`. All data are synthetic.*

## Base scenario vs the pitch (document v6)

| Indicator | Simulation | v6 assumption |
|---|---|---|
| Alerts per client per year | **{b['alerts/client/year']:.2f}** | ~1.5 |
| Resolved by the trusted contact | **{b['resolved by contact']:.0%}** | ~80% |
| Escalated to the bank | **{b['to the bank']:.0%}** (conflict of interest: {b['to the bank for conflict of interest']:.0%} of alerts) | ~20% |
| Bank cases per client per year | {b['bank cases/client/year']:.2f} | — |
| Cost to serve per client per year | **CHF {b['cost to serve CHF']:.2f}** | CHF 7 |
| Fraud episodes caught | **{b['fraud episodes caught']:.0%}** | — |
| Fraud money protected (stopped from the first pause on) | **{b['fraud money protected']:.0%}** | — |

Calibrated threshold: **{s}** (minimum expected cost at {PREVALENZA_REALE:.0%} real prevalence, CHF 5 per false alarm).

**Robustness.** Repeating the base scenario with three different seeds (each with its own calibrated threshold):

{md_table(rob, ["scenario", "threshold", "alerts/client/year", "to the bank", "cost to serve CHF", "fraud money protected"])}

Range to quote in the pitch: **{rng_['alerts/client/year'][0]:.1f}–{rng_['alerts/client/year'][1]:.1f} alerts per client per year, {rng_['to the bank'][0]:.0%}–{rng_['to the bank'][1]:.0%} to the bank, cost to serve CHF {rng_['cost to serve CHF'][0]:.1f}–{rng_['cost to serve CHF'][1]:.1f}.** The cost curve is shallow around its minimum, so small differences between simulated books move the calibrated threshold by a few hundredths, and the cost to serve with it.

By threat:

{md_table(df.iloc[[0]], threat_cols)}

## Effect on the unit economics of a typical bank (v6, page 3)

Same adoption, price and CAC as v6; only the cost to serve changes (simulated: CHF {cts:.2f}).

{md_table(ue, list(ue.columns))}

## Sensitivity (same threshold)

{md_table(df, main_cols)}

## How to read these results

- **Scope.** Sentinel looks at cash at the counter, safe deposit box visits and transfers to new or foreign accounts (v6). Card payments are left to the bank's card antifraud, so they never raise a Sentinel alert.
- **Where alerts come from.** New payees and transfers abroad, rare safe deposit box visits, very large cash withdrawals, and the bank's own antifraud flags. Each is an assumption on behaviour that only a pilot with a bank can confirm.
- **What drives the cost to serve.** Cases escalated to the bank: contacts who do not answer in 30 minutes and conflicts of interest (the contact holds a power of attorney).
- **Detection is high on synthetic data.** Small scams (a few thousand francs) are the ones that slip through; with real, subtler fraud the rate will be lower. Present it as a result to verify in the pilot, not as a promise.
- **Money protected is a benefit for the client and the family** (v6). The bank pays for trust, retention of senior clients, the link with the heirs and fewer complaints.
- **Assumptions to calibrate (Utente 1):** fraud prevalence, frequency of unusual legitimate operations, share of customers with a POA holder, response time of contacts.
"""
    with open("results/simulation_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(df[main_cols].to_string(index=False))
    print()
    print(ue.to_string(index=False))
    print("\nReport: results/simulation_report.md")


if __name__ == "__main__":
    main()
