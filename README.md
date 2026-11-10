# 🛡️ Sentinel · prototipo

> Quando la banca vede qualcosa di strano, chiama la persona giusta: quella di cui ti fidi.

Sentinel è un modulo white-label per le banche. La persona sceglie un **contatto di fiducia**; quando c'è un'operazione insolita (prelievo di contanti, accesso alla cassetta, bonifico verso un conto nuovo o estero) l'operazione resta in pausa finché il contatto non la verifica. Sentinel **non sostituisce l'antifrode della banca**: ne usa gli alert e aggiunge la verifica umana.

Regole chiave del prodotto, già nel codice:
- **Conflitto d'interesse:** se il contatto ha avviato l'operazione, ne beneficia, ha una procura o è co-titolare, non può approvarla: il caso va alla banca (`sentinel/workflow.py`).
- **Anti-coercizione:** disattivare Sentinel o cambiare le regole richiede **72 ore** e il contatto viene avvisato.

---

## Avvio rapido

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py             # si apre nel browser
python -m pytest -q              # test dei contratti tra moduli
```

Senza installare nulla: dal repo su GitHub, **Code → Codespaces → Create codespace**, poi gli stessi comandi nel terminale.

## Struttura

| File | Cosa fa | Responsabile | Branch |
|---|---|---|---|
| `sentinel/profiles.py` | Dati sintetici: 3 profili = 3 tipi di minaccia, iniezione frodi | Utente 2 | `dati-economia` |
| `sentinel/economics.py` | Curva costo/soglia, perdita evitata, **stima alert e cost to serve** | Utente 2 | `dati-economia` |
| `sentinel/model.py` | Motore di decisione: **quando** coinvolgere il contatto | Utente 1 | `modello` |
| `sentinel/workflow.py` | Instradamento: **a chi** chiedere (contatto o banca), regola 72 ore | Utente 1 | `modello` |
| `notebooks/calibrazione.ipynb` | Calibrazione su fonti pubbliche, ROC, sensibilità | Utente 1 | `modello` |
| `app.py` | Demo Streamlit: flusso, sotto il cofano, confronto | Utente 3 | `interfaccia` |
| `pitch/` | Deck e documenti (o link alla cartella condivisa) | Utente 4 | — |
| `scripts/simula_portafoglio.py` | Simula centinaia di clienti: alert, quota banca, cost to serve, sensibilità | Utente 2 | `dati-economia` |
| `risultati/` | Report e tabelle generate dalla simulazione | Utente 2 | `dati-economia` |
| `tests/test_contratti.py` | Controlla che le firme non cambino | tutti | — |

## I contratti (firme da non cambiare senza accordo)

```python
genera_storico(profilo, giorni=365, seed=0) -> DataFrame
inietta_frode(storico, profilo, n=1, seed=0) -> DataFrame
adatta_baseline(storico) -> dict
punteggia(df, base) -> DataFrame            # aggiunge 'punteggio' e 'motivi'
instrada(operazione, contatto) -> (destinazione, motivo)   # "contatto" | "banca"
curva_costo(df, costo_falso_allarme=5.0, soglie=None) -> DataFrame
perdita_attesa_evitata(df, soglia) -> float
stima_alert(df, soglia, ...) -> dict        # PER CLIENTE: alert/anno, quote contatto/banca, cost to serve
genera_portafoglio(n_clienti=300, mix=None, prob_frode=0.01, ...) -> DataFrame
punteggia_portafoglio(portafoglio) -> DataFrame
riepilogo_portafoglio(scored, soglia=None, ...) -> dict
applica_soglia_contanti(scored, soglia_chf) -> DataFrame
```

## Come lavoriamo

1. Ognuno lavora **solo sul proprio branch** e sui propri file.
2. Prima di aprire una Pull Request: `python -m pytest -q` deve passare.
3. Pull Request verso `main` ogni 2–3 giorni; un'altra persona la guarda e la approva.
4. Se serve cambiare una firma: prima si scrive nel gruppo, poi si cambia insieme al test.

## Prossimi passi per ciascuno

- **Utente 1:** calibrare pesi e soglia nel notebook su un portafoglio di molti clienti; curva ROC; sensibilità.
- **Utente 2:** fatto il primo giro: `python scripts/simula_portafoglio.py` (circa 2 minuti) produce `risultati/simulazione_portafoglio.md`. Prossimi passi: calibrare con Utente 1 le ipotesi (prevalenza delle frodi, prelievi straordinari legittimi, quota di procure, risposta dei contatti) e passare i numeri a Utente 4.
- **Utente 3:** rifinire grafica e testi della demo; schermata di attivazione più ricca; deploy su Streamlit Community Cloud; video di backup.
- **Utente 4:** deck in 11 slide; agganciare il cost to serve ai risultati di Utente 2.

## Risultati della simulazione (scenario base, 600 clienti)

| | Simulazione | Ipotesi del pitch v6 |
|---|---|---|
| Alert per cliente all'anno | ~2,2 | ~1,5 |
| Passati alla banca | ~29% | ~20% |
| Cost to serve | ~CHF 11 | CHF 7 |

Il dettaglio e l'analisi di sensibilità sono in `risultati/simulazione_portafoglio.md`. Con una soglia contanti concordata di CHF 5'000 il cost to serve scende a ~CHF 5, ma l'importo protetto passa dal ~100% al ~94%.

## Calendario

| Data | Tappa |
|---|---|
| 29 novembre | Prima demo completa dall'inizio alla fine |
| 6 dicembre | Blocco del codice |
| 10 dicembre | Deploy definitivo e video di backup |
| 17 dicembre | Presentazione |

## Deploy

[share.streamlit.io](https://share.streamlit.io) → accedi con GitHub → **New app** → scegli il repo, branch `main`, file `app.py` → Deploy. Si ottiene un link pubblico da usare nel pitch.

---
*Dati interamente sintetici: nessun dato reale di clienti.*
