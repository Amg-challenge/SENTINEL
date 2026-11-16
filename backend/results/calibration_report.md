# Engine calibration · results (Utente 1)

*Generated on 16.11.2026 from `notebooks/calibrazione.ipynb`. All customer data are synthetic; the external figures come from the public sources listed at the end.*

## In one paragraph

The decision engine has been checked against public Swiss sources and recalibrated on 1,800 simulated seniors. The cost-optimal threshold is **0.50**: the bootstrap range is 0.46–0.50, while the API currently uses 0.54. At 0.50 the simulation reproduces the operational assumptions of the business model (v6): **1.5 alerts per client per year, 21% escalated to the bank, cost to serve CHF 7.2**. The fraud amounts in the code are lower than those reported by the police, so detection figures are conservative. The score keeps its ranking quality when every weight is moved by ±30%. A black-box model (Isolation Forest) reaches the same AUC but cannot say why it paused an operation.

## 1. Assumptions vs public sources

| Assumption | In the code | Sources | Verdict |
|---|---|---|---|
| Customers with a material fraud episode per year | 1% | 55+: 11.8% lost money over 5 years (~2.4%/yr, mostly small); scams 4.8% and financial maltreatment 5.2% over 5 years (~1%/yr each) [1] | Consistent (test 0.5%–2%) |
| Shock-call scam paid in cash | median CHF 10k, mean ~15k | Ticino: 22 scams / ~CHF 0.8m (2022) [3]; ~30 / > CHF 1.5m (2023) [4]; 46 / > CHF 2m (2023) [5]. Mean **CHF 36k–50k** | Conservative |
| Small scams (fake bank employee, card handover) | lower tail from CHF 1k | > 5,000 cases since 2022, ~CHF 18m, **mean CHF 3,600** [6] | Partly out of scope (cards) |
| POA abuse | CHF 1.2k–10k per episode | Financial maltreatment: median **CHF 112,888** [1]; POA / bank-access abuse ~CHF 216m/yr, the 2nd costliest form [2] | Very conservative |
| Customers with a POA holder | 15% | 20% have a *Vorsorgeauftrag* (CH, 2021) [7]; 44% have a bank POA (DE) [8] | Probably 20%–40%: risk for the cost to serve |
| Large legitimate counter withdrawals | 2/yr | No public source | Pilot |
| Contacts not answering in 30 min | 15% | No public source | Pilot |
| Transfers to new foreign accounts | 30%–40% of episodes | Online investment-fraud reports rose almost fivefold in H1 2025 [9]; money sent abroad is rarely recovered [10] | Threat confirmed, no amounts |

## 2. Threshold

| | Threshold |
|---|---|
| One book of 300 customers (6 seeds) | 0.54, 0.50, 0.46, 0.48, 0.50, 0.46 |
| **Pooled book, 1,800 customers (526 fraud episodes)** | **0.50** |
| Bootstrap over customers, 5%–95% | 0.46–0.50 |
| API today (one book of 150 customers) | 0.54 |

What the threshold means for the bank and for the client. The operational load is measured on 900 customers at the real prevalence of 1%, and detection on the pooled book:

| Threshold | Alerts/client/year | To the bank | Cost to serve CHF | Fraud episodes caught | Fraud money protected | Expected cost CHF/client |
|---|---|---|---|---|---|---|
| 0.46 | 1.88 | 21% | 8.68 | 92% | 97% | 12.87 |
| 0.48 | 1.67 | 21% | 7.89 | 91% | 97% | 12.94 |
| **0.50** | **1.48** | **21%** | **7.23** | **89%** | **96%** | **12.75** |
| 0.54 | 1.16 | 20% | 5.87 | 84% | 92% | 16.25 |

**Sensitivity.** Optimal threshold by cost per false alarm and real prevalence:

| Cost per false alarm | prevalence 0.5% | 1% | 2% |
|---|---|---|---|
| CHF 1 | 0.44 | 0.40 | 0.12 |
| **CHF 5** | 0.50 | **0.50** | 0.44 |
| CHF 20 | 0.54 | 0.54 | 0.50 |

## 3. Robustness and stress tests

| Test | Result |
|---|---|
| Each weight ±30% (one at a time) and 10 joint random draws | AUC 0.969–0.981: ranking robust. Calibrated threshold 0.28–0.64: **recalibrate whenever a weight changes**. Most sensitive: `importo` (protection) and `beneficiario_nuovo` (false alarms) |
| Fraud amounts from the sources (scam median CHF 25k, larger POA abuse) | Episodes caught at 0.50: 97% (vs 88% with the amounts in the code); threshold 0.52 |
| Isolation Forest, same per-person features | AUC 0.983 vs Sentinel 0.977: same accuracy, no reasons |
| Isolation Forest, generic | AUC 0.977 |

## 4. Appendix slide for the deck (Utente 4)

**Title:** *Every pause comes with its reason*

- Figure: `results/figures/why_paused.png`. The score is a starting point plus one contribution per signal: the same reasons appear at the counter, on the contact's phone and in the bank queue.
- **Same accuracy as a black box:** AUC 0.98 for Sentinel and 0.98 for an Isolation Forest on the same data, but only Sentinel says why.
- **Threshold chosen by cost, not by accuracy:** CHF 5 per disturbance vs money lost. At 0.50 there are 1.5 alerts per client per year.
- **Robust:** with every weight moved by ±30%, the AUC stays at 0.97–0.98.
- In line with FINMA Guidance 08/2024 on AI: governance, robustness, explainability.
- Optional second figure: `results/figures/roc.png`.

Say it on stage as *"synthetic data, to be confirmed in a pilot"*.

## 5. Decisions and hand-offs

| For | What | Status |
|---|---|---|
| Group | Adopt **0.50** as the engine threshold (the API today recalibrates on 150 customers and gets 0.54). `/stats` and the offline data change; none of the 5 demo scenarios changes outcome | to decide |
| Utente 2 | Re-run `simula_portafoglio.py` with the threshold fixed at 0.50, so report, demo and deck use one set of numbers; add the source-based amounts and POA 30% as sensitivity rows | to do |
| Utente 4 | v6 can keep **CHF 7** as the cost to serve (simulated: CHF 7.2 at 0.50); appendix slide above | ready |
| Pilot | Large legitimate counter withdrawals, contacts' response time, real share of POA holders | open |

## Sources

1. Pro Senectute Svizzera / ILCE (HEG Arc), *Abusi finanziari*, study 2023, pp. 15–19 — https://ag.prosenectute.ch/dam/jcr:4d2b91b4-54f1-4575-936e-590e08477d02/2024.01.12_studio_abusi_finanziari_2023.pdf
2. Pro Senectute, one-pager 2023 — https://ag.prosenectute.ch/dam/jcr:d1e311a3-b303-45d8-9f56-3e26f86b5a31/2023.09_Onepager_Abusi%20finanziari_IT.pdf
3. Polizia cantonale TI, 2022 report (tio.ch, 29.03.2023) — https://www.tio.ch/ticino/cronaca/1656132/ventidue-truffe-ai-danni-degli-anziani-bottino-da-800-000-franchi
4. Polizia cantonale TI / fedpol, press release 28.09.2023 — https://www4.ti.ch/user_allegati/DI/Polizia/comunicati-stampa/pdf-ComunicatiStampa-203458293716.pdf
5. RSI, 15.12.2024 — https://www.rsi.ch/info/ticino-grigioni-e-insubria/Telefonate-shock-il-punto-sulla-gravit%C3%A0-del-fenomeno--2431512.html
6. tio.ch / ATS, French-speaking cantons and fedpol — https://www.tio.ch/svizzera/cronaca/1936127/fedpol-cantoni-romandi-svizzera-francia
7. Swiss Life, citing the Pro Senectute 2021 survey (gfs-zürich) — https://www.swisslife.ch/de/private/vorsorge-vermoegen/ratgeber/vorsorgeauftrag.html
8. Versicherungsbote (German survey) — https://www.versicherungsbote.de/id/4907853/Vorsorgevollmacht-und-Patienverfugung-Mehr-Burgerinnen-und-Burger-sorgen-vor/
9. NCSC, semi-annual report 2025/1 — https://www.ncsc.admin.ch/ncsc/en/home/dokumentation/berichte/lageberichte/halbjahresbericht-2025-1.html
10. NCSC / BACS, *Financial loss – what should you do?* — https://www.bacs.admin.ch/en/financial-loss
11. FINMA Guidance 08/2024, *Governance and risk management when using artificial intelligence* — https://www.finma.ch/en/news/2024/12/20241218-mm-finma-am-08-24/
