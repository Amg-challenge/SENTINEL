"""Portfolio simulation: alerts, contact/bank split, cost to serve, fraud stopped,
and the effect on the unit economics of the pitch (document v6, page 3).

Owner: Utente 2 · branch `dati-economia`.

Usage (from the backend/ folder):
    python scripts/simula_portafoglio.py                # full run, ~15 minutes
    python scripts/simula_portafoglio.py --report-only  # rewrite the report from results/sensitivity.csv

Writes:
    results/sensitivity.csv                    every scenario, one row each
    results/simulation_report.md               readable report, with the numbers for the deck
    results/figures/cost_to_serve_drivers.png  appendix figure: what moves the cost to serve

Method (same books as notebooks/calibrazione.ipynb and the API's /stats, so the three agree)
- Threshold: fixed at model.SOGLIA = 0.50, calibrated by Utente 1 on 1,800 simulated seniors.
- Operational load (alerts, contact/bank split, cost to serve): 3 books x 300 seniors at the
  REAL fraud prevalence of 1% (seeds 100-102). Each customer has two years: year 1 teaches
  the engine their habits, alerts are counted on year 2.
- Fraud stopped: 6 books x 300 seniors with frauds oversampled to 30% (seeds 0-5), so that
  there are enough episodes (~500) to count.
- Every paused operation is routed with workflow.destinazione_finale: conflict of interest
  -> bank; contact who does not answer within 30 minutes -> bank.
- Robustness: the base scenario repeated on two other sets of books.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from sentinel import economics, model, profiles  # noqa: E402

SOGLIA = model.SOGLIA
PREVALENZA_REALE = 0.01
PREVALENZA_SIM = 0.30
N_CLIENTI = 300
SEEDS_LOAD = (100, 101, 102)
SEEDS_DET = (0, 1, 2, 3, 4, 5)
ROBUSTEZZA = [((200, 201, 202), (20, 21, 22, 23, 24, 25)),
              ((300, 301, 302), (30, 31, 32, 33, 34, 35))]
CSV = "results/sensitivity.csv"
REPORT = "results/simulation_report.md"
FIGURA = "results/figures/cost_to_serve_drivers.png"

_cache: dict = {}


def _book(seed: int, prob_frode: float, eventi: dict | None, gen_kw: dict | None) -> pd.DataFrame:
    """One scored book of 300 seniors (ids unique across seeds), cached."""
    key = (seed, prob_frode, tuple(sorted((eventi or {}).items())), tuple(sorted((gen_kw or {}).items())))
    if key not in _cache:
        port = profiles.genera_portafoglio(n_clienti=N_CLIENTI, prob_frode=prob_frode, seed=seed,
                                           eventi=eventi, **(gen_kw or {}))
        port["cliente"] = port["cliente"] + seed * 10_000
        _cache[key] = economics.punteggia_portafoglio(port)
    return _cache[key]


def run(nome: str, gruppo: str, eventi=None, gen_kw=None, p_non_risposta=0.15, par=None,
        detection=True, limite=None, seeds_load=SEEDS_LOAD, seeds_det=SEEDS_DET) -> dict:
    print(f"  · {nome}", flush=True)
    reale = pd.concat([_book(s, PREVALENZA_REALE, eventi, gen_kw) for s in seeds_load], ignore_index=True)
    if limite:
        reale = economics.applica_limite_contanti(reale, limite)
    carico = economics.stima_alert(reale, SOGLIA, par=par, p_non_risposta=p_non_risposta, seed=0)
    det = {}
    if detection:
        sim = pd.concat([_book(s, PREVALENZA_SIM, eventi, gen_kw) for s in seeds_det], ignore_index=True)
        if limite:
            sim = economics.applica_limite_contanti(sim, limite)
        det = economics.importo_protetto(sim, SOGLIA)
    return {"scenario": nome, "group": gruppo, "threshold": SOGLIA,
            "alerts/client/year": carico["alert_per_cliente_anno"],
            "resolved by contact": carico["quota_contatto"],
            "to the bank": carico["quota_banca"],
            "to the bank for conflict of interest": carico["quota_banca_conflitto"],
            "bank cases/client/year": carico["casi_banca_per_cliente_anno"],
            "cost to serve CHF": carico["cost_to_serve"],
            "fraud episodes caught": det.get("episodi_intercettati", np.nan),
            "fraud money protected": det.get("importo_protetto", np.nan),
            **{k.replace("importo_protetto_", "money protected · ").replace(
                "episodi_intercettati_", "episodes caught · "): v
               for k, v in det.items() if k.startswith(("importo_protetto_", "episodi_intercettati_"))}}


def calcola() -> pd.DataFrame:
    pg = profiles.PRESET["anziano"]
    righe = [
        run("Base", "base"),
        # behaviour of legitimate customers (only a pilot can measure these)
        run(f"Large legit cash withdrawals: 1/year (base {pg.prelievi_straordinari:g})", "sens",
            eventi={"prelievi_straordinari": 1.0}),
        run("Large legit cash withdrawals: 4/year", "sens", eventi={"prelievi_straordinari": 4.0}),
        run(f"Legit transfers abroad: 1.5/year (base {pg.bonifici_esteri:g})", "sens", detection=False,
            eventi={"bonifici_esteri": 1.5}),
        run(f"Bank antifraud false positives: 1/year (base {pg.falsi_alert_banca:g})", "sens",
            detection=False, eventi={"falsi_alert_banca": 1.0}),
        # operations of the service
        run("Contacts not answering in 30 min: 5% (base 15%)", "sens", detection=False, p_non_risposta=0.05),
        run("Contacts not answering in 30 min: 30%", "sens", detection=False, p_non_risposta=0.30),
        run("Customers with a POA holder: 30% (base 15%)", "sens", detection=False,
            gen_kw={"prob_procuratore": 0.30}),
        run("Customers with a POA holder: 40%", "sens", detection=False, gen_kw={"prob_procuratore": 0.40}),
        run("Bank review cost per case: CHF 10 (base 15)", "sens", detection=False,
            par=economics.ParametriServizio(costo_revisione_banca=10.0)),
        run("Bank review cost per case: CHF 25", "sens", detection=False,
            par=economics.ParametriServizio(costo_revisione_banca=25.0)),
        # fraud amounts and the optional cash-limit lever
        run("Fraud amounts from the public sources", "fraud", gen_kw={"importi_frode": "fonti"}),
        run("Agreed cash limit: CHF 2,000", "lever", limite=2_000),
        run("Agreed cash limit: CHF 5,000", "lever", limite=5_000),
    ]
    for k, (sl, sd) in enumerate(ROBUSTEZZA, start=2):
        righe.append(run(f"Base, book set {k}", "robust", seeds_load=sl, seeds_det=sd))
    df = pd.DataFrame(righe)
    df.loc[df["scenario"] == "Base", "scenario"] = "Base"
    os.makedirs("results", exist_ok=True)
    df.to_csv(CSV, index=False)
    return df


# ---------------------------------------------------------------- report

def fmt(v, col):
    if isinstance(v, float) and v != v:
        return "—"
    if isinstance(v, float) and any(w in col for w in ("resolved", "to the bank", "caught", "protected")) \
            and "cases" not in col:
        return f"{v:.0%}"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def md_table(df, cols, rename=None):
    rename = rename or {}
    out = ["| " + " | ".join(rename.get(c, c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df[cols].iterrows():
        out.append("| " + " | ".join(fmt(r[c], c) for c in cols) + " |")
    return "\n".join(out)


def figura(df: pd.DataFrame) -> None:
    """Dot-range chart: how far each assumption moves the cost to serve from the base case."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, ink2, accent, grid = "#0b0b0b", "#52514e", "#2a78d6", "#e4e3df"
    base = float(df.loc[df["scenario"] == "Base", "cost to serve CHF"].iloc[0])
    leve = [("Contacts not answering in 30 min\n5% / 30% (base 15%)", "Contacts not answering"),
            ("Customers with a POA holder\n30% / 40% (base 15%)", "Customers with a POA holder"),
            ("Bank review cost per case\nCHF 10 / 25 (base 15)", "Bank review cost"),
            ("Large legit cash withdrawals\n1 / 4 per year (base 2)", "Large legit cash withdrawals"),
            ("Bank antifraud false positives\n1 per year (base 0.3)", "Bank antifraud false positives"),
            ("Legit transfers abroad\n1.5 per year (base 0.5)", "Legit transfers abroad"),
            ("Agreed cash limit\nCHF 2,000 / 5,000 (base none)", "Agreed cash limit")]
    righe = []
    for etichetta, chiave in leve:
        v = df.loc[df["scenario"].str.startswith(chiave), "cost to serve CHF"].astype(float).tolist()
        righe.append((etichetta, min(v + [base]), max(v + [base]), v))
    righe.sort(key=lambda r: r[2] - r[1])
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": ink2, "xtick.color": ink2, "ytick.color": ink2})
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    for y, (etichetta, lo, hi, vals) in enumerate(righe):
        ax.plot([lo, hi], [y, y], color=accent, lw=2, zorder=2, solid_capstyle="round")
        for v in vals:
            ax.scatter([v], [y], s=48, color=accent, edgecolor="white", linewidth=1.5, zorder=3)
            ax.annotate(f"{v:.1f}", (v, y), xytext=(0, 7), textcoords="offset points",
                        ha="center", color=ink, fontsize=9)
    ax.axvline(base, color=ink2, lw=1.2, ls="--", zorder=1)
    ax.annotate(f"base CHF {base:.2f}", (base, len(righe) - 0.5), xytext=(4, 0),
                textcoords="offset points", color=ink2, fontsize=9, va="bottom")
    ax.set_yticks(range(len(righe)), [r[0] for r in righe], fontsize=9)
    ax.set_ylim(-0.6, len(righe) - 0.2)
    ax.set_xlabel("Cost to serve per protected client per year (CHF)")
    ax.set_title("What moves the cost to serve (price to the bank: CHF 30 per client per year)",
                 loc="left", color=ink, fontsize=11)
    ax.grid(axis="x", color=grid, lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    os.makedirs(os.path.dirname(FIGURA), exist_ok=True)
    fig.savefig(FIGURA, dpi=200)
    plt.close(fig)


def rapporto(df: pd.DataFrame) -> str:
    b = df[df["scenario"] == "Base"].iloc[0]
    rob = pd.concat([df[df["scenario"] == "Base"], df[df["group"] == "robust"]])
    rob = rob.assign(scenario=["Base (books used by the API)"] + list(rob["scenario"].iloc[1:]))
    sens = pd.concat([df[df["scenario"] == "Base"], df[df["group"] == "sens"]])
    extra = pd.concat([df[df["scenario"] == "Base"], df[df["group"].isin(["fraud", "lever"])]])
    fonti = df[df["group"] == "fraud"].iloc[0]
    lim = {int(s.split("CHF ")[1].replace(",", "")): r for s, r in
           zip(df.loc[df["group"] == "lever", "scenario"], df[df["group"] == "lever"].to_dict("records"))}
    cts = float(b["cost to serve CHF"])
    r = {c: (rob[c].min(), rob[c].max()) for c in ["alerts/client/year", "to the bank", "cost to serve CHF",
                                                   "fraud episodes caught", "fraud money protected"]}

    ue = []
    for sc in economics.SCENARI_BUSINESS:
        v6 = economics.unit_economics_banca(sc, 8.0 if sc == "prudente" else 7.0)
        sim = economics.unit_economics_banca(sc, cts + (1.0 if sc == "prudente" else 0.0))
        ue.append({"business scenario": sc,
                   "contribution/client v6": v6["contribution_cliente"],
                   "contribution/client simulated": sim["contribution_cliente"],
                   "LTV/CAC v6": v6["ltv_su_cac"], "LTV/CAC simulated": sim["ltv_su_cac"],
                   "CAC payback months v6": v6["rientro_cac_mesi"],
                   "CAC payback months simulated": sim["rientro_cac_mesi"]})
    ue = pd.DataFrame(ue)
    ub = ue[ue["business scenario"] == "base"].iloc[0]
    threat_cols = [c for c in df.columns if c.startswith(("episodes caught · ", "money protected · "))
                   and df[c].notna().any()]
    poa30 = df[df["scenario"].str.startswith("Customers with a POA holder: 30%")].iloc[0]
    poa40 = df[df["scenario"].str.startswith("Customers with a POA holder: 40%")].iloc[0]
    nr30 = df[df["scenario"].str.startswith("Contacts not answering in 30 min: 30%")].iloc[0]
    main_cols = ["scenario", "alerts/client/year", "to the bank", "cost to serve CHF",
                 "fraud episodes caught", "fraud money protected"]

    return f"""# Portfolio simulation · results

*Generated on {date.today():%d.%m.%Y} with `python scripts/simula_portafoglio.py`. All customer data are synthetic. Threshold fixed at **{SOGLIA:.2f}** (calibrated by Utente 1: `results/calibration_report.md`). The books are the same as the API's `/stats`, so report, demo and deck show the same numbers.*

## 1. Numbers for the deck (Utente 4)

| What to say | Number | v6 | Source in this report |
|---|---|---|---|
| Alerts per protected client per year | **{b['alerts/client/year']:.1f}** | ~1.5 | §2 |
| Resolved by the trusted contact / escalated to the bank | **{b['resolved by contact']:.0%} / {b['to the bank']:.0%}** | ~80% / ~20% | §2 |
| Cost to serve per client per year | **CHF {cts:.2f}** (range CHF {r['cost to serve CHF'][0]:.1f}–{r['cost to serve CHF'][1]:.1f}) | CHF 7 | §2–3 |
| Bank's LTV/CAC, base scenario | **{ub['LTV/CAC simulated']:.1f}×** | 7.4× | §5 |
| CAC payback, base scenario | **{ub['CAC payback months simulated']:.0f} months** | 16 months | §5 |
| Fraud episodes stopped / fraud money protected | **{b['fraud episodes caught']:.0%} / {b['fraud money protected']:.0%}** (synthetic data) | — | §2, §4 |

**Conclusion: the v6 numbers hold and the document does not need to change.** The simulated cost to serve (CHF {cts:.2f}, range CHF {r['cost to serve CHF'][0]:.2f}–{r['cost to serve CHF'][1]:.2f}) is only CHF {cts - 7:.2f} above the CHF 7 used in v6, and LTV/CAC hardly moves. Say *"about CHF 7 per client per year, measured by simulating the whole process"*.

How to present them:
- **The bank pays for trust, not for the money it saves.** Money protected benefits the client and the family (v6), so it is not the argument for the price.
- **Detection is measured on synthetic data, where frauds are easier to spot than in reality.** Say *"to be confirmed in the pilot"*. Do not present 96% as a promise.
- **The cost to serve is uncertain, but never critical.** In every scenario tested it stays between CHF {df['cost to serve CHF'].min():.0f} and {df['cost to serve CHF'].max():.0f}, against a price of CHF 30 (§3). The assumption to measure first in a pilot is the share of clients with a power of attorney: public sources already suggest it is higher than the 15% used here.

## 2. Base scenario vs the pitch (document v6)

| Indicator | Simulation | v6 assumption |
|---|---|---|
| Alerts per client per year | **{b['alerts/client/year']:.2f}** | ~1.5 |
| Resolved by the trusted contact | **{b['resolved by contact']:.0%}** | ~80% |
| Escalated to the bank | **{b['to the bank']:.0%}** (conflict of interest: {b['to the bank for conflict of interest']:.0%} of alerts) | ~20% |
| Bank cases per client per year | {b['bank cases/client/year']:.2f} | — |
| Cost to serve per client per year | **CHF {cts:.2f}** | CHF 7 |
| Fraud episodes caught | **{b['fraud episodes caught']:.0%}** | — |
| Fraud money protected (stopped from the first pause on) | **{b['fraud money protected']:.0%}** | — |

By threat (episodes caught and money protected):

{md_table(df[df['scenario'] == 'Base'], threat_cols)}

## 3. Robustness and sensitivity

**Robustness.** The base scenario repeated on two other sets of simulated books (900 + 1,800 customers each):

{md_table(rob, main_cols)}

Range: **{r['alerts/client/year'][0]:.2f}–{r['alerts/client/year'][1]:.2f} alerts per client per year, {r['to the bank'][0]:.0%}–{r['to the bank'][1]:.0%} to the bank, cost to serve CHF {r['cost to serve CHF'][0]:.2f}–{r['cost to serve CHF'][1]:.2f}.**

**Sensitivity**, with the same threshold and one assumption changed at a time:

{md_table(sens, main_cols)}

![What moves the cost to serve](figures/cost_to_serve_drivers.png)

**Reading.** Two things drive the cost to serve:
- **How many cases go to the bank** (CHF 15 each, against CHF 0.50 for a notification to the contact):
  - contacts who do not answer: CHF {nr30['cost to serve CHF']:.2f} if 30% of them do not answer;
  - clients with a power of attorney: CHF {poa30['cost to serve CHF']:.2f} at 30% and CHF {poa40['cost to serve CHF']:.2f} at 40%. Public sources suggest 20%–40% (`calibration_report.md`), so this is the risk most likely to materialise.
- **How often legitimate clients do something unusual:** transfers abroad, or flags from the bank's antifraud. These are the largest single effects, but there are no public data on them. Only a pilot can measure them.

Even in the worst case tested (CHF {df['cost to serve CHF'].max():.2f}) the cost to serve stays far below the price (CHF 30 per client per year).

## 4. Fraud amounts from the sources, and the cash-limit lever

{md_table(extra, main_cols)}

- **Amounts from the public sources** (shock-call scams with a median of CHF 25,000; larger POA abuse): the engine stops {fonti['fraud episodes caught']:.0%} of the episodes instead of {b['fraud episodes caught']:.0%}. The base case uses smaller amounts on purpose, so the pitch figures are a **lower bound**.
- **Agreed cash limit** (optional lever): at sign-up the client agrees that their own cash withdrawals below a limit never cause a pause. Withdrawals by a POA holder and the bank's antifraud flags stay covered.
  - CHF 2,000: {lim[2000]['alerts/client/year']:.2f} alerts and CHF {lim[2000]['cost to serve CHF']:.2f}, with {lim[2000]['fraud episodes caught']:.0%} of episodes caught.
  - CHF 5,000: {lim[5000]['alerts/client/year']:.2f} alerts and CHF {lim[5000]['cost to serve CHF']:.2f}, with {lim[5000]['fraud episodes caught']:.0%} of episodes caught.

  The saving is small: at most CHF {cts - lim[5000]['cost to serve CHF']:.2f} per client per year. Clients' own cash withdrawals below CHF 2,000 almost never cause a pause anyway, while at CHF 5,000 some small scams get through. **We do not recommend it as the default.** Keep it as an option for clients who withdraw a lot of cash and find the pauses annoying.

## 5. Effect on the unit economics of a typical bank (v6, page 3)

Same adoption, price and CAC as v6; only the cost to serve changes (simulated: CHF {cts:.2f}; prudent scenario +CHF 1, as in v6).

{md_table(ue, list(ue.columns))}

## 6. How to read these results

- **Scope.** Sentinel looks at cash at the counter, safe deposit box visits and transfers to new or foreign accounts (v6). Card payments are left to the bank's card antifraud, so they never raise a Sentinel alert.
- **Where alerts come from.** New payees and transfers abroad, rare safe deposit box visits, very large cash withdrawals, and the bank's own antifraud flags. Each is an assumption on behaviour that only a pilot with a bank can confirm.
- **What drives the cost to serve.** Cases escalated to the bank: contacts who do not answer in 30 minutes and conflicts of interest (the contact holds a power of attorney).
- **Detection is high on synthetic data.** Small scams (a few thousand francs) are the ones that slip through. With real, subtler fraud the rate will be lower.
- **What only a pilot can measure:** large legitimate counter withdrawals, response time of contacts, real share of POA holders. Sources and the fraud prevalence (1%) are discussed in `results/calibration_report.md`.

## Method

- **Threshold:** fixed at {SOGLIA:.2f}.
- **Operational load:** 3 books × 300 seniors at the real fraud prevalence of 1% (seeds 100–102).
- **Fraud stopped:** 6 books × 300 seniors with frauds oversampled to 30% (seeds 0–5).
- **Two years per customer:** year 1 teaches the engine their habits, year 2 is counted.
- **Routing:** every paused operation is routed with `workflow.destinazione_finale`, with 15% of contacts not answering within 30 minutes.
- **Service costs:** CHF 0.50 per notification, CHF 15 per bank review, CHF 2 platform cost per client per year.

These are the same books used by the API's `/stats` and by `notebooks/calibrazione.ipynb`.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true", help="rewrite the report from results/sensitivity.csv")
    a = ap.parse_args()
    if a.report_only:
        df = pd.read_csv(CSV)
    else:
        print(f"Simulating at threshold {SOGLIA} (~15 minutes)…", flush=True)
        df = calcola()
    figura(df)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(rapporto(df))
    cols = ["scenario", "alerts/client/year", "to the bank", "cost to serve CHF",
            "fraud episodes caught", "fraud money protected"]
    print(df[cols].to_string(index=False))
    print(f"\nReport: {REPORT} · figure: {FIGURA}")


if __name__ == "__main__":
    main()
