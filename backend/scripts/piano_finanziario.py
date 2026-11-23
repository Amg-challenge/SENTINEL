"""Five-year financial plan of Sentinel, rebuilt from explicit assumptions.

Owner: Utente 4 (with Utente 2) · writes results/financial_plan.csv and prints the table.

Why this script exists: the plan in project document v6 reached 32,000 clients in year 5,
which needs all 10 banks at maturity, while the bank-level model (slide 6) assumes a bank
reaches 8% of its 65+ clients only after two years. Here every number follows from the
same assumptions, so slide 4 (SOM), slide 6 (one bank), slide 11 (five years), slide 12
(the ask) and appendix A3 agree.

Usage (from backend/):  python scripts/piano_finanziario.py
"""
from __future__ import annotations

import os

import pandas as pd

# ---- assumptions (document v6 unless noted)
CLIENTI_65_PER_BANCA = 40_000      # clients aged 65+ of a typical bank
ADOZIONE = {1: 0.04, 2: 0.08}      # share of them protected after 1 year, after 2+ years (v6: 8% after two years)
CLIENTI_PILOTA = 500               # year 1: one pilot bank, 500 clients (then the normal ramp)
NUOVE_BANCHE = [1, 2, 2, 3, 2]     # banks signed in years 1..5 (v6: 1, 3, 5, 8, 10 at year end)
PREZZO_ANNO = 30.0                 # CHF 2.50 per client per month, list price also in the pilot
SETUP_FEE = 25_000                 # one-off per bank
SETUP_FEE_PILOTA = 10_000          # reduced setup fee for the pilot bank, in exchange for data and a case study
PRE_SEED = 900_000                 # amount raised (group decision 23.11.2026; was 800,000)
SEED = 3_000_000                   # seed round at month 18, only if adoption is close to the base case
COSTO_SERVIZIO = 7.0               # CHF per client per year (simulation: 7.23)
INTEGRAZIONE_PER_BANCA = 20_000    # one-off integration cost per new bank (covered by the setup fee)
COSTI_FISSI = [500_000, 600_000, 900_000, 1_200_000, 1_400_000]   # v6 totals: team, product, compliance, sales

# Our breakdown of the v6 totals (planning assumption, 23.11.2026; v6 gives only the totals).
# Personnel = fully loaded cost (gross salary + employer social charges of about 13-19%).
# Years 1-2: four founders on reduced pay (about CHF 65k loaded each, ~CHF 4,700 gross a
# month) plus a part-time hire in year 2. From year 3: progressive hires; the average loaded
# cost per FTE (93k -> 104k) stays BELOW the Swiss market for software roles (median gross
# salary about CHF 96k-110k, i.e. CHF 110k-130k loaded). See SCENARIO_STIPENDI_MERCATO.
FTE = [4, 4.5, 6, 8, 9]
COMPONENTI_FISSI = {
    "personnel":                     [260_000, 330_000, 560_000, 790_000, 940_000],
    "tech development & maintenance": [80_000, 80_000, 90_000, 100_000, 110_000],   # external security review, tools, licences
    "cloud & infrastructure (base)":  [30_000, 40_000, 60_000, 80_000, 90_000],     # environments, backups, monitoring; per-client platform cost is variable (CHF 2 inside the CHF 7)
    "compliance, security & legal":   [70_000, 70_000, 90_000, 110_000, 120_000],   # contracts, data protection, bank audits, insurance
    "sales & commercial":             [60_000, 80_000, 100_000, 120_000, 140_000],  # travel, events, materials; with sales staff this is the CAC
}
assert all(sum(c[i] for c in COMPONENTI_FISSI.values()) == COSTI_FISSI[i] for i in range(5)), "breakdown must add up to v6"


def clienti_fine_anno() -> list[int]:
    """Year-end protected clients. A bank signed in year k is live from the start of year k:
    pilot bank 500 clients in year 1; every bank has 4% of its 65+ clients after one year
    and 8% from its second year on."""
    coorti = []                         # (year signed, is pilot)
    out = []
    for anno, n in enumerate(NUOVE_BANCHE, start=1):
        coorti += [(anno, anno == 1 and i == 0) for i in range(n)]
        tot = 0
        for firmato, pilota in coorti:
            eta = anno - firmato + 1    # years live, 1 = first year
            if pilota and eta == 1:
                tot += CLIENTI_PILOTA
            elif pilota and eta == 2:
                tot += round(CLIENTI_65_PER_BANCA * ADOZIONE[1])      # pilot extended to the whole bank
            else:
                tot += round(CLIENTI_65_PER_BANCA * ADOZIONE[min(eta, 2)])
        out.append(tot)
    return out


# Alternative: market salaries from year 3 (CHF 120k loaded per FTE), everything else equal.
PERSONALE_MERCATO = [260_000, 330_000, 6 * 120_000, 8 * 120_000, 9 * 120_000]
COSTI_FISSI_MERCATO = [COSTI_FISSI[i] - COMPONENTI_FISSI["personnel"][i] + PERSONALE_MERCATO[i]
                       for i in range(5)]


def piano(costi_fissi: list[float] | None = None) -> pd.DataFrame:
    costi_fissi = costi_fissi or COSTI_FISSI
    fine = clienti_fine_anno()
    inizio = [0] + fine[:-1]
    righe = []
    banche = 0
    for i in range(5):
        banche += NUOVE_BANCHE[i]
        medi = (inizio[i] + fine[i]) / 2
        setup = SETUP_FEE_PILOTA + SETUP_FEE * (NUOVE_BANCHE[i] - 1) if i == 0 else SETUP_FEE * NUOVE_BANCHE[i]
        ricavi_ric = medi * PREZZO_ANNO
        variabili = medi * COSTO_SERVIZIO + INTEGRAZIONE_PER_BANCA * NUOVE_BANCHE[i]
        costi = variabili + costi_fissi[i]
        ricavi = ricavi_ric + setup
        righe.append({"year": i + 1, "banks": banche, "clients_end": fine[i], "clients_avg": medi,
                      "recurring_revenue": ricavi_ric, "setup_fees": setup, "revenue": ricavi,
                      "variable_costs": variabili, "fixed_costs": costi_fissi[i], "costs": costi,
                      "ebitda": ricavi - costi, "run_rate_end": fine[i] * PREZZO_ANNO})
    df = pd.DataFrame(righe)
    df["cumulative"] = df["ebitda"].cumsum()
    return df


if __name__ == "__main__":
    df = piano()
    os.makedirs("results", exist_ok=True)
    df.round(0).to_csv("results/financial_plan.csv", index=False)
    k = df.copy()
    for c in k.columns:
        if c not in ("year", "banks", "clients_end"):
            k[c] = (k[c] / 1000).round(0)
    print("CHF thousand (clients in units)")
    print(k.to_string(index=False))
    burn_18 = -(df.loc[0, "ebitda"] + df.loc[1, "ebitda"] / 2)
    print("\nFixed costs, CHF thousand (our breakdown of the v6 totals)")
    comp = pd.DataFrame(COMPONENTI_FISSI, index=[f"Y{i}" for i in range(1, 6)]).T / 1000
    comp.loc["total"] = comp.sum()
    comp.loc["personnel share %"] = (comp.loc["personnel"] / comp.loc["total"] * 100).round(0)
    comp.loc["loaded cost per FTE"] = (comp.loc["personnel"] / pd.Series(FTE, index=comp.columns)).round(1)
    comp.loc["FTE"] = FTE
    print(comp.round(1).to_string())
    comp.round(1).to_csv("results/fixed_costs.csv")
    print(f"\nCumulative EBITDA loss, months 1-18: CHF {burn_18:,.0f} (≈ CHF {burn_18 / 18:,.0f} a month)")
    print("  = cumulative EBITDA loss of months 1-18. Taken as the cash need: the model has no capex"
          " (software is expensed), no income tax (losses), VAT is neutral; receivables at 30 days"
          " would add only about one month of revenue (< CHF 10k).")
    # use of funds over 18 months, from the same plan (gross spending, by line)
    m = {k: v[0] + v[1] / 2 for k, v in COMPONENTI_FISSI.items()}
    var18 = df.loc[0, "variable_costs"] + df.loc[1, "variable_costs"] / 2
    ric18 = df.loc[0, "revenue"] + df.loc[1, "revenue"] / 2
    usi = {"team": m["personnel"],
           "product, cloud and service": m["tech development & maintenance"] + m["cloud & infrastructure (base)"] + var18,
           "compliance, security and legal": m["compliance, security & legal"],
           "sales and commercial": m["sales & commercial"]}
    lordo = sum(usi.values())
    riserva = PRE_SEED + ric18 - lordo
    print(f"\nSources and uses, months 1-18")
    print(f"  sources: pre-seed CHF {PRE_SEED:,.0f} + pilot revenue CHF {ric18:,.0f} = CHF {PRE_SEED + ric18:,.0f}")
    print(f"  uses:    spending CHF {lordo:,.0f}")
    for k, v in usi.items():
        print(f"    {k:32s} CHF {v:9,.0f}  {v / lordo:5.0%} of spending")
    print(f"  reserve at month 18: CHF {riserva:,.0f} = {riserva / (burn_18 / 18):.1f} months of the average"
          f" net burn (CHF {burn_18 / 18:,.0f}/month); {riserva / (lordo / 18):.1f} months of gross spending")
    cassa = PRE_SEED + SEED + df["ebitda"].sum()
    print(f"  cash at the end of year 5 with pre-seed + seed (CHF {(PRE_SEED + SEED) / 1e6:.1f} m): CHF {cassa:,.0f}")
    contrib = PREZZO_ANNO - COSTO_SERVIZIO
    print(f"Break-even (year-5 fixed costs / contribution): {COSTI_FISSI[-1] / contrib:,.0f} clients "
          f"≈ {COSTI_FISSI[-1] / contrib / (CLIENTI_65_PER_BANCA * ADOZIONE[2]):.0f} banks at maturity")
    b = CLIENTI_65_PER_BANCA * ADOZIONE[2] * contrib
    print(f"One bank at maturity: {CLIENTI_65_PER_BANCA * ADOZIONE[2]:,.0f} clients, revenue CHF "
          f"{CLIENTI_65_PER_BANCA * ADOZIONE[2] * PREZZO_ANNO:,.0f}, contribution CHF {b:,.0f}, "
          f"LTV/CAC {b / 0.10 / 100_000:.1f}x, payback {100_000 / b * 12:.1f} months")


# ---- appendix A3: the three adoption scenarios with the same ramp logic
SCENARI = {
    #            adoption at maturity, price/yr, cost to serve, CAC, banks signed per year
    "prudent":    dict(adozione=0.03, prezzo=24.0, costo=8.0, cac=120_000, banche=[1, 1, 1, 1, 1]),
    "base":       dict(adozione=0.08, prezzo=30.0, costo=7.0, cac=100_000, banche=NUOVE_BANCHE),
    "optimistic": dict(adozione=0.15, prezzo=30.0, costo=7.0, cac=60_000, banche=[1, 3, 3, 4, 4]),
}


def scenario(adozione, prezzo, costo, cac, banche, churn=0.10):
    maturi = CLIENTI_65_PER_BANCA * adozione
    contrib = maturi * (prezzo - costo)
    # payback with the ramp: year 1 average = half of the year-1 clients (adoption/2), year 2 average
    # = (adoption/2 + adoption)/2, then full; contribution accrues month by month
    mesi, cum = 0, 0.0
    while cum < cac and mesi < 240:
        anno = mesi // 12 + 1
        fine_prec = 0 if anno == 1 else (maturi / 2 if anno == 2 else maturi)
        fine = maturi / 2 if anno == 1 else maturi
        m = mesi % 12 + 0.5
        clienti = fine_prec + (fine - fine_prec) * m / 12
        cum += clienti * (prezzo - costo) / 12
        mesi += 1
    # year-end clients after 5 years (by year 5 the pilot bank is mature in every scenario)
    tot, coorti = 0, []
    for anno, n in enumerate(banche, start=1):
        coorti += [anno] * n
    for firmato in coorti:
        eta = 5 - firmato + 1
        tot += maturi / 2 if eta == 1 else maturi
    return {"clients_per_bank": maturi, "contribution_bank": contrib, "ltv_cac": contrib / churn / cac,
            "payback_maturity_m": cac / contrib * 12, "payback_ramp_m": mesi,
            "banks_y5": sum(banche), "clients_y5": tot, "run_rate_y5": tot * prezzo}


if __name__ == "__main__":
    alt = piano(COSTI_FISSI_MERCATO)
    print("\nAlternative · market salaries from year 3 (CHF 120k loaded per FTE)")
    print(f"  fixed costs (k): {[round(x / 1000) for x in COSTI_FISSI_MERCATO]}")
    print(f"  EBITDA (k): {[round(x / 1000) for x in alt['ebitda']]}; cumulative 5 years:"
          f" CHF {alt['cumulative'].iloc[-1] / 1e6:.2f} m (base {df['cumulative'].iloc[-1] / 1e6:.2f} m)")
    print(f"  break-even: {COSTI_FISSI_MERCATO[-1] / contrib:,.0f} clients"
          f" ≈ {COSTI_FISSI_MERCATO[-1] / contrib / (CLIENTI_65_PER_BANCA * ADOZIONE[2]):.0f} mature banks;"
          " the first 18 months do not change")
    print(f"  cash at the end of year 5 with pre-seed + seed: CHF {PRE_SEED + SEED + alt['ebitda'].sum():,.0f}")
    print("\nAppendix A3 · per bank and after five years")
    print(pd.DataFrame({k: scenario(**v) for k, v in SCENARI.items()}).round(1).to_string())
