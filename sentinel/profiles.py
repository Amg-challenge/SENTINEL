"""Dati sintetici: storici dei clienti e iniezione delle frodi.

Responsabile: Utente 2 · branch `dati-economia`.

CONTRATTO (firme stabili, non cambiarle senza accordo del gruppo):
    genera_storico(profilo: str, giorni: int = 365, seed: int = 0) -> pd.DataFrame
    inietta_frode(storico: pd.DataFrame, profilo: str, n: int = 1, seed: int = 0) -> pd.DataFrame

Colonne del DataFrame:
    data (datetime), canale (str: "sportello" | "bancomat" | "cassetta" | "bonifico"),
    importo (float, CHF), beneficiario (str), estero (bool),
    avviato_da (str: "titolare" | "procuratore"), alert_banca (bool), frode (bool)

I tre profili corrispondono ai tre tipi di minaccia del pitch.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PROFILI: dict[str, str] = {
    "truffa_esterna": "Truffa esterna: falso poliziotto, prelievo di contanti allo sportello",
    "abuso_interno": "Abuso interno: chi ha una procura svuota gradualmente il conto",
    "bonifico_estero": "Bonifico verso un conto estero nuovo, su pressione telefonica",
}

COLONNE = ["data", "canale", "importo", "beneficiario", "estero",
           "avviato_da", "alert_banca", "frode"]

_BENEFICIARI_ABITUALI = ["Cassa malati", "Affitto", "Elettricità", "Telefono", "Farmacia"]

# Frequenza annua di eventi insoliti ma legittimi (ipotesi da calibrare con Utente 1).
# Sono loro a generare i falsi allarmi: senza, la simulazione sarebbe irrealisticamente pulita.
_EVENTI_LEGITTIMI = {
    "prelievo_grande": 2.0,      # prelievi straordinari allo sportello all'anno
    "beneficiario_nuovo": 3.0,   # bonifici a beneficiari mai visti all'anno
    "bonifico_estero": 0.5,      # bonifici all'estero all'anno
    "falso_alert_banca": 0.3,    # segnalazioni dell'antifrode su operazioni legittime
}

# Composizione di default del portafoglio simulato (quota di clienti per profilo).
MIX_DEFAULT = {"truffa_esterna": 0.5, "abuso_interno": 0.2, "bonifico_estero": 0.3}


def _riga(data, canale, importo, beneficiario="", estero=False,
          avviato_da="titolare", alert_banca=False, frode=False) -> dict:
    return dict(data=data, canale=canale, importo=round(float(importo), 2),
                beneficiario=beneficiario, estero=estero, avviato_da=avviato_da,
                alert_banca=alert_banca, frode=frode)


def genera_storico(profilo: str, giorni: int = 365, seed: int = 0) -> pd.DataFrame:
    """Vedi `_genera`: usa le frequenze di default degli eventi legittimi."""
    return _genera(profilo, giorni, seed, _EVENTI_LEGITTIMI)


def _genera(profilo: str, giorni: int, seed: int, eventi: dict) -> pd.DataFrame:
    """Storico 'normale' di un cliente over 65 (nessuna frode).

    Abitudini: prelievo settimanale di CHF 200-300, pagamenti mensili ricorrenti,
    accesso raro alla cassetta. Il profilo cambia solo chi ha accesso al conto.
    """
    if profilo not in PROFILI:
        raise ValueError(f"Profilo sconosciuto: {profilo}. Disponibili: {list(PROFILI)}")
    rng = np.random.default_rng(seed)
    inizio = pd.Timestamp("2025-01-01")
    # Ogni cliente ha abitudini proprie: la scala di spesa varia da persona a persona.
    scala = float(rng.lognormal(mean=0.0, sigma=0.35))
    righe = []
    for g in range(giorni):
        giorno = inizio + pd.Timedelta(days=g)
        if giorno.weekday() == 0:  # prelievo settimanale del lunedì
            canale = "bancomat" if rng.random() < 0.7 else "sportello"
            righe.append(_riga(giorno, canale, rng.uniform(200, 300) * scala))
        if giorno.day == 1:  # pagamenti ricorrenti
            for b in _BENEFICIARI_ABITUALI:
                righe.append(_riga(giorno, "bonifico", rng.uniform(80, 1400) * scala, beneficiario=b))
        if rng.random() < 0.004:  # accesso raro alla cassetta
            righe.append(_riga(giorno, "cassetta", 0.0))
        # chi ha una procura fa ogni tanto piccole spese legittime per il titolare
        if profilo == "abuso_interno" and giorno.day == 15:
            righe.append(_riga(giorno, "bancomat", rng.uniform(100, 200) * scala, avviato_da="procuratore"))
        # --- eventi insoliti ma LEGITTIMI: generano i falsi allarmi realistici ---
        p = eventi
        if rng.random() < p["prelievo_grande"] / 365:  # vacanza, regalo, spesa straordinaria
            righe.append(_riga(giorno, "sportello", rng.uniform(1_500, 6_000) * scala))
        if rng.random() < p["beneficiario_nuovo"] / 365:  # artigiano, medico, nuovo fornitore
            righe.append(_riga(giorno, "bonifico", rng.uniform(150, 2_500) * scala,
                               beneficiario=f"Nuovo #{rng.integers(10_000, 99_999)}"))
        if rng.random() < p["bonifico_estero"] / 365:  # familiari o vacanze all'estero
            righe.append(_riga(giorno, "bonifico", rng.uniform(300, 3_000) * scala,
                               beneficiario=f"Estero #{rng.integers(10_000, 99_999)}", estero=True))
        if rng.random() < p["falso_alert_banca"] / 365:  # falso positivo dell'antifrode della banca
            righe.append(_riga(giorno, "bonifico", rng.uniform(100, 1_500) * scala,
                               beneficiario=_BENEFICIARI_ABITUALI[0], alert_banca=True))
    return pd.DataFrame(righe, columns=COLONNE)


def inietta_frode(storico: pd.DataFrame, profilo: str, n: int = 1, seed: int = 0) -> pd.DataFrame:
    """Aggiunge in coda allo storico n episodi di frode tipici del profilo.

    Le frodi sono volutamente VARIE, non solo i casi da manuale (ipotesi da calibrare
    con le fonti di Utente 1):
    - truffa_esterna: importo log-normale (mediana ~CHF 15'000, tra 3'000 e 80'000);
      nel 30% dei casi diviso in due prelievi in giorni consecutivi; accesso alla
      cassetta nel 50% dei casi.
    - abuso_interno: prelievi graduali di chi ha una procura, CHF 400-1'000 a settimana
      per 4-8 settimane (il caso più difficile da vedere).
    - bonifico_estero: CHF 5'000-40'000 verso un conto estero nuovo; l'antifrode della
      banca lo segnala solo nel 60% dei casi.
    """
    rng = np.random.default_rng(seed)
    ultimo = storico["data"].max()
    nuove = []
    for i in range(n):
        giorno = ultimo + pd.Timedelta(days=1 + i * 60)
        if profilo == "truffa_esterna":
            totale = float(np.clip(rng.lognormal(np.log(15_000), 0.7), 3_000, 80_000))
            if rng.random() < 0.5:
                nuove.append(_riga(giorno, "cassetta", 0.0, frode=True))
            if rng.random() < 0.3:
                quota = rng.uniform(0.4, 0.6)
                nuove.append(_riga(giorno, "sportello", totale * quota, frode=True))
                nuove.append(_riga(giorno + pd.Timedelta(days=1), "sportello",
                                   totale * (1 - quota), frode=True))
            else:
                nuove.append(_riga(giorno, "sportello", totale, frode=True))
        elif profilo == "abuso_interno":
            for k in range(int(rng.integers(4, 9))):
                nuove.append(_riga(giorno + pd.Timedelta(days=7 * k), "bancomat",
                                   rng.uniform(400, 1_000), avviato_da="procuratore", frode=True))
        elif profilo == "bonifico_estero":
            nuove.append(_riga(giorno, "bonifico", rng.uniform(5_000, 40_000),
                               beneficiario=f"IBAN estero #{rng.integers(1000, 9999)}",
                               estero=True, alert_banca=bool(rng.random() < 0.6), frode=True))
        else:
            raise ValueError(f"Profilo sconosciuto: {profilo}")
    return pd.concat([storico, pd.DataFrame(nuove, columns=COLONNE)], ignore_index=True)


def genera_portafoglio(n_clienti: int = 300, mix: dict | None = None, prob_frode: float = 0.01,
                       prob_contatto_con_procura: float = 0.5, eventi_legittimi: dict | None = None,
                       seed: int = 0) -> pd.DataFrame:
    """Portafoglio simulato di molti clienti, per stimare alert e cost to serve.

    Per ogni cliente: 2 anni di storico. Il primo anno ("storico") serve a imparare
    le abitudini; il secondo ("valutazione") è quello su cui si contano gli alert.
    Con probabilità `prob_frode` il cliente subisce una frode nell'anno di valutazione.

    Colonne: quelle di COLONNE più
        cliente (int), profilo (str), periodo ("storico" | "valutazione"),
        contatto_procura (bool: il contatto di fiducia ha una procura sul conto)

    `prob_contatto_con_procura` vale per i clienti del profilo "abuso_interno"
    (chi ha la procura è anche il contatto); per gli altri profili è il 5%.
    `eventi_legittimi` sostituisce in parte o del tutto `_EVENTI_LEGITTIMI` (analisi di sensibilità).

    Nota: `prob_frode` = 1% di clienti frodati all'anno è un'ipotesi da calibrare (Utente 1).
    Per misurare il TASSO DI INTERCETTAZIONE conviene sovra-campionare (es. 0.10): non
    cambia gli alert sui clienti legittimi, ma dà abbastanza casi di frode da contare.
    """
    mix = mix or MIX_DEFAULT
    eventi = {**_EVENTI_LEGITTIMI, **(eventi_legittimi or {})}
    rng = np.random.default_rng(seed)
    profili, pesi = list(mix), np.array(list(mix.values()), dtype=float)
    pesi = pesi / pesi.sum()
    confine = pd.Timestamp("2025-01-01") + pd.Timedelta(days=365)
    pezzi = []
    for c in range(n_clienti):
        profilo = str(rng.choice(profili, p=pesi))
        df = _genera(profilo, 730, seed * 100_000 + c, eventi)
        if rng.random() < prob_frode:
            df = inietta_frode(df, profilo, n=1, seed=seed * 100_000 + c)
        p_proc = prob_contatto_con_procura if profilo == "abuso_interno" else 0.05
        pezzi.append(df.assign(cliente=c, profilo=profilo,
                               periodo=np.where(df["data"] < confine, "storico", "valutazione"),
                               contatto_procura=bool(rng.random() < p_proc)))
    return pd.concat(pezzi, ignore_index=True)
