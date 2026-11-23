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
COSTO_SERVIZIO = 7.0               # CHF per client per year (simulation: 7.23)
INTEGRAZIONE_PER_BANCA = 20_000    # one-off integration cost per new bank (covered by the setup fee)
COSTI_FISSI = [500_000, 600_000, 900_000, 1_200_000, 1_400_000]   # team, cloud, compliance, sales (CAC inside)


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


def piano() -> pd.DataFrame:
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
        costi = variabili + COSTI_FISSI[i]
        ricavi = ricavi_ric + setup
        righe.append({"year": i + 1, "banks": banche, "clients_end": fine[i], "clients_avg": medi,
                      "recurring_revenue": ricavi_ric, "setup_fees": setup, "revenue": ricavi,
                      "variable_costs": variabili, "fixed_costs": COSTI_FISSI[i], "costs": costi,
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
    print(f"\nNet burn over the first 18 months: CHF {burn_18:,.0f} (≈ CHF {burn_18 / 18:,.0f} a month)")
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
    print("\nAppendix A3 · per bank and after five years")
    print(pd.DataFrame({k: scenario(**v) for k, v in SCENARI.items()}).round(1).to_string())
