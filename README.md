# 🛡️ Sentinel · prototype

> When the bank sees something strange, it calls the right person: the one you trust.

Sentinel is a white-label module for banks. A person **chooses** to activate it and names a **trusted contact**. When an unusual operation happens - cash at the counter, a safe deposit box visit, a transfer to a new or foreign account - it is put **on hold** until the contact confirms or blocks it. Sentinel **does not replace the bank's antifraud system** (e.g. NetGuardians): it receives its alerts and adds the missing link, the verification by a person who really knows the client.

Product rules implemented in the code (document v6):

- **Consent first:** nothing happens without the person's explicit activation.
- **The contact never sees the account:** they can only approve or block the flagged operation.
- **Conflict of interest:** if the contact initiated the operation, benefits from it, holds a power of attorney or co-holds the account, they cannot approve it - the case goes to the bank (`sentinel/workflow.py`).
- **Response window:** if the contact does not answer within 30 minutes, the bank takes over.
- **Anti-coercion:** switching Sentinel off or changing the rules takes effect only after **72 hours**, and the contact is told at once.
- **Scope:** cash, safe deposit box and transfers. Card payments stay with the bank's card antifraud.

The prototype builds on the first version written by Stefano (interface, workflow, scoring formula), extended with the v6 features (channels, safe deposit box, power of attorney, foreign transfers) and a portfolio simulation that measures the numbers used in the pitch.

---

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py                 # opens in the browser on http://localhost:8501
python -m pytest -q                  # contract tests
python scripts/simula_portafoglio.py # portfolio simulation (~4 min) -> results/
```

No installation: on GitHub, **Code → Codespaces → Create codespace**, then the same commands.

## The demo (`app.py`)

| Screen | What the jury sees |
|---|---|
| 1 · Protected person | Consent, choice of the contact, what the contact can and cannot do, 72-hour delay on revocation |
| 2 · Bank counter | The operation on hold, the score and **why** it was paused |
| 3 · Trusted contact | The notification on the phone, approve / block, 30-minute window |
| 4 · Bank case queue | Conflict-of-interest and unanswered cases |
| Appendix · Analysis | Cost curve, ROC, operational load, three populations |

Five scenarios: fake police officer (cash at the counter, the hero story), fake grandchild (transfer abroad), safe deposit box opened, internal abuse by the contact, flagged by the bank's antifraud. The *Demo controls* in the sidebar simulate the clocks (30 minutes, 72 hours) on stage.

## Structure and owners (work plan v2)

| File | What it does | Owner | Branch |
|---|---|---|---|
| `sentinel/model.py` | Engine: **when** to involve the contact; explainable score | Utente 1 | `modello` |
| `sentinel/workflow.py` | **Who** verifies: contact or bank; 30-minute window; 72 hours | Utente 1 | `modello` |
| `notebooks/calibrazione.ipynb` | Calibration on public sources, ROC, sensitivity | Utente 1 | `modello` |
| `sentinel/profiles.py` | Synthetic data: populations, legitimate behaviour, three threats, portfolio | Utente 2 | `dati-economia` |
| `sentinel/economics.py` | Threshold, cost curve, ROC, cost to serve, link to the unit economics | Utente 2 | `dati-economia` |
| `scripts/simula_portafoglio.py`, `results/` | Portfolio simulation and report | Utente 2 | `dati-economia` |
| `app.py`, `.streamlit/` | The demo | Utente 3 | `interfaccia` |
| `pitch/` | Reference documents (v6, work plan v2), deck | Utente 4 | — |
| `docs/project-diary.pdf` | Group diary (required for the written deliverable) | everyone | — |
| `tests/test_contratti.py` | Checks that shared signatures and v6 rules hold | everyone | — |

## Contracts (change only with the group's agreement)

Data columns: `data, canale, importo, beneficiario, nuovo_beneficiario, estero, avviata_da, alert_banca, frode_reale`
with `canale` in `sportello | bancomat | cassetta | bonifico | carta`.

```python
# profiles (Utente 2)
genera_storico(cfg, giorni=365, seed=0, ha_procuratore=False) -> DataFrame
inietta_frode(storico, minaccia="truffa_esterna", seed=0, importo=None) -> DataFrame
genera_frodi_simulate(n=300, seed=1, mix=None) -> DataFrame
genera_portafoglio(n_clienti=300, mix_popolazione=None, prob_frode=0.01, ...) -> DataFrame

# model (Utente 1)
adatta_baseline(storico) -> Baseline
punteggio(tx, base) -> float              # one operation, in [0, 1]
punteggia(df, base) -> np.ndarray
spiega(tx, base) -> list[(reason, contribution)]

# workflow (Utente 1)
instrada(operazione, contatto) -> (destination, reason)        # "contatto" | "banca"
decidi(operazione, punteggio, soglia, contatto, alert_esterno=False) -> Decisione
destinazione_finale(operazione, contatto, risponde, minuti_trascorsi=0.0) -> (destination, reason)
richiesta_revoca(ora=None) -> dict

# economics (Utente 2)
curva_costo(score_legit, score_frode, par) -> (DataFrame, threshold)
curva_roc(score_legit, score_frode) -> (DataFrame, auc)
punteggia_portafoglio(portafoglio) -> DataFrame
calibra_soglia(scored, prevalenza_reale=0.01, costo_falso_allarme=5.0) -> (DataFrame, threshold)
stima_alert(scored, soglia, par=None, p_non_risposta=0.15) -> dict      # per customer
importo_protetto(scored, soglia) -> dict
unit_economics_banca(scenario, cost_to_serve) -> dict                    # v6, page 3
```

## How we work

1. Everyone works **only on their own branch** and their own files.
2. Before a Pull Request: `python -m pytest -q` must pass.
3. Pull Request to `main` every 2-3 days; someone else reviews and approves it.
4. To change a signature: agree in the group first, then change it together with its test.
5. One source of truth for the pitch: `pitch/Sentinel-v6.pdf` and `pitch/Sentinel-work-plan-v2.pdf`.

## Simulation results (base scenario, three seeds)

| | Simulation | v6 assumption |
|---|---|---|
| Alerts per client per year | 1.4 - 1.8 | ~1.5 |
| Escalated to the bank | 21 - 22% | ~20% |
| Cost to serve per client per year | CHF 7.1 - 8.4 | CHF 7 |
| Fraud money protected (synthetic data) | 97 - 98% | — |

The v6 assumptions hold within the simulated range; the cost to serve is slightly above CHF 7, which lowers the base-case contribution per client from CHF 23 to CHF 21.6-22.9 (LTV/CAC 6.9-7.3× instead of 7.4×). Details and sensitivity: `results/simulation_report.md`.

## Calendar

| Date | Milestone |
|---|---|
| 29 November | First complete demo, end to end |
| 6 December | Code freeze |
| 10 December | Final deploy and backup video |
| 17 December | Presentation |
| Mid-January | Written deliverable (incl. project diary and rebuttal of the jury's critique) |

## Deploy

[share.streamlit.io](https://share.streamlit.io) → sign in with GitHub → **New app** → this repo, branch `main`, file `app.py` → Deploy. You get a public link for the pitch.

---
*All data are synthetic: no real customer data.*
