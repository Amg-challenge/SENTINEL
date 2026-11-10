# Simulazione del portafoglio · risultati

*Generato il 10.11.2026 con `python scripts/simula_portafoglio.py --clienti 600 --seed 7`. Dati interamente sintetici.*

## Scenario base

| Indicatore | Simulazione | Ipotesi del pitch (v6) |
|---|---|---|
| Alert per cliente all'anno | **2.17** | ~1,5 |
| … di cui falsi allarmi | 2.15 | — |
| Risolti dal contatto | **71%** | ~80% |
| Passati alla banca | **29%** (di cui 16% per conflitto d'interesse) | ~20% |
| Cost to serve per cliente | **CHF 11.45** | CHF 7 |
| Frodi intercettate (almeno un alert nell'episodio) | **100%** | — |
| Importo protetto (fermato dal primo alert in poi) | **100%** | — |

Soglia di coinvolgimento: **6.0** (costo minimo con prevalenza delle frodi all'1% e costo di un falso allarme CHF 5).

Per tipo di minaccia:

| intercettazione abuso_interno | intercettazione bonifico_estero | intercettazione truffa_esterna | importo protetto abuso_interno | importo protetto bonifico_estero | importo protetto truffa_esterna |
|---|---|---|---|---|---|
| 100% | 100% | 100% | 97% | 100% | 100% |

## Analisi di sensibilità (stessa soglia)

| scenario | alert/cliente/anno | quota banca | cost to serve CHF | intercettazione totale | importo protetto |
|---|---|---|---|---|---|
| Base | 2.17 | 29% | 11.45 | 100% | 100% |
| Prelievi grandi legittimi: 1/anno (base 2) | 1.21 | 30% | 7.42 | 100% | 100% |
| Prelievi grandi legittimi: 4/anno | 4.16 | 28% | 19.67 | 100% | 100% |
| Soglia contanti concordata: CHF 5'000 | 0.69 | 31% | 5.22 | 77% | 94% |
| Soglia contanti concordata: CHF 10'000 | 0.22 | 33% | 3.06 | 56% | 77% |
| Contatti che non rispondono: 25% (base 15%) | 2.17 | 37% | 14.17 | 100% | 100% |
| Contatti che non rispondono: 5% | 2.17 | 21% | 8.72 | 100% | 100% |
| Costo per caso alla banca: CHF 25 (base 15) | 2.17 | 29% | 17.75 | 100% | 100% |
| Contatto con procura (abuso interno): 25% (base 50%) | 2.17 | 25% | 10.13 | 100% | 100% |

## Come leggere i risultati

- **Perché l'intercettazione è così alta.** La soglia ottimale coinvolge il contatto per qualsiasi prelievo molto sopra le abitudini: le frodi vengono viste quasi sempre, ma il prezzo sono i falsi allarmi. È il compromesso centrale del prodotto, non un risultato "gratis". Con frodi reali più sottili l'intercettazione sarà più bassa: va verificata nel pilota.
- **Da dove vengono gli alert.** Quasi tutti i falsi allarmi sono prelievi allo sportello legittimi ma grandi (qualche migliaio di franchi). Il loro numero dipende da un'ipotesi che oggi non è verificata: quanti prelievi straordinari fa un over 65 in un anno.
- **La leva di prodotto.** Una soglia di importo sui contanti concordata tra persona e contatto riduce molto il disturbo; il prezzo da pagare è che i piccoli prelievi ripetuti (abuso interno) vengono intercettati meno. Va mostrato come scelta consapevole.
- **Cosa pesa sul cost to serve.** Le escalation alla banca: conflitti d'interesse (contatto con procura) e contatti che non rispondono in tempo.
- **Ipotesi da calibrare (Utente 1):** prevalenza delle frodi, frequenza dei prelievi straordinari, quota di clienti con una procura, tempo di risposta dei contatti.
