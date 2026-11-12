# Portfolio simulation · results

*Generated on 10.11.2026 with `python scripts/simula_portafoglio.py --clienti 500 --seed 7`. All data are synthetic.*

## Base scenario vs the pitch (document v6)

| Indicator | Simulation | v6 assumption |
|---|---|---|
| Alerts per client per year | **1.76** | ~1.5 |
| Resolved by the trusted contact | **78%** | ~80% |
| Escalated to the bank | **22%** (conflict of interest: 8% of alerts) | ~20% |
| Bank cases per client per year | 0.38 | — |
| Cost to serve per client per year | **CHF 8.36** | CHF 7 |
| Fraud episodes caught | **95%** | — |
| Fraud money protected (stopped from the first pause on) | **98%** | — |

Calibrated threshold: **0.48** (minimum expected cost at 1% real prevalence, CHF 5 per false alarm).

**Robustness.** Repeating the base scenario with three different seeds (each with its own calibrated threshold):

| scenario | threshold | alerts/client/year | to the bank | cost to serve CHF | fraud money protected |
|---|---|---|---|---|---|
| Base, seed 7 | 0.48 | 1.758 | 22% | 8.36 | 98% |
| Base, seed 107 | 0.5 | 1.57 | 22% | 7.89 | 97% |
| Base, seed 207 | 0.5 | 1.446 | 21% | 7.07 | 97% |

Range to quote in the pitch: **1.4–1.8 alerts per client per year, 21%–22% to the bank, cost to serve CHF 7.1–8.4.** The cost curve is shallow around its minimum, so small differences between simulated books move the calibrated threshold by a few hundredths, and the cost to serve with it.

By threat:

| money protected · abuso_interno | episodes caught · abuso_interno | money protected · bonifico_estero | episodes caught · bonifico_estero | money protected · truffa_esterna | episodes caught · truffa_esterna |
|---|---|---|---|---|---|
| 96% | 100% | 100% | 100% | 97% | 92% |

## Effect on the unit economics of a typical bank (v6, page 3)

Same adoption, price and CAC as v6; only the cost to serve changes (simulated: CHF 8.36).

| business scenario | contribution/client v6 | contribution/client simulated | LTV/CAC v6 | LTV/CAC simulated | CAC payback months v6 | CAC payback months simulated |
|---|---|---|---|---|---|---|
| prudente | 16.0 | 15.64 | 1.6 | 1.6 | 75.0 | 76.7 |
| base | 23.0 | 21.64 | 7.4 | 6.9 | 16.3 | 17.3 |
| ottimistico | 23.0 | 21.64 | 23.0 | 21.6 | 5.2 | 5.5 |

## Sensitivity (same threshold)

| scenario | alerts/client/year | to the bank | cost to serve CHF | fraud episodes caught | fraud money protected |
|---|---|---|---|---|---|
| Base | 1.758 | 22% | 8.36 | 95% | 98% |
| Large legit cash withdrawals: 1/year (base 2) | 1.506 | 21% | 7.36 | 95% | 98% |
| Large legit cash withdrawals: 4/year | 2.166 | 22% | 10.04 | 94% | 97% |
| Legit transfers abroad: 1.5/year (base 0.5) | 2.752 | 22% | 12.25 | — | — |
| Bank antifraud false positives: 1/year (base 0.3) | 2.384 | 23% | 11.2 | — | — |
| Contacts not answering in 30 min: 30% (base 15%) | 1.758 | 36% | 12.1 | — | — |
| Contacts not answering in 30 min: 5% | 1.758 | 12% | 6.07 | — | — |
| Customers with a POA holder: 30% (base 15%) | 1.726 | 27% | 9.68 | — | — |
| Bank review cost per case: CHF 25 (base 15) | 1.758 | 22% | 12.14 | — | — |

## How to read these results

- **Scope.** Sentinel looks at cash at the counter, safe deposit box visits and transfers to new or foreign accounts (v6). Card payments are left to the bank's card antifraud, so they never raise a Sentinel alert.
- **Where alerts come from.** New payees and transfers abroad, rare safe deposit box visits, very large cash withdrawals, and the bank's own antifraud flags. Each is an assumption on behaviour that only a pilot with a bank can confirm.
- **What drives the cost to serve.** Cases escalated to the bank: contacts who do not answer in 30 minutes and conflicts of interest (the contact holds a power of attorney).
- **Detection is high on synthetic data.** Small scams (a few thousand francs) are the ones that slip through; with real, subtler fraud the rate will be lower. Present it as a result to verify in the pilot, not as a promise.
- **Money protected is a benefit for the client and the family** (v6). The bank pays for trust, retention of senior clients, the link with the heirs and fewer complaints.
- **Assumptions to calibrate (Utente 1):** fraud prevalence, frequency of unusual legitimate operations, share of customers with a POA holder, response time of contacts.
