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


def _riga(data, canale, importo, beneficiario="", estero=False,
          avviato_da="titolare", alert_banca=False, frode=False) -> dict:
    return dict(data=data, canale=canale, importo=round(float(importo), 2),
                beneficiario=beneficiario, estero=estero, avviato_da=avviato_da,
                alert_banca=alert_banca, frode=frode)


def genera_storico(profilo: str, giorni: int = 365, seed: int = 0) -> pd.DataFrame:
    """Storico 'normale' di un cliente over 65 (nessuna frode).

    Abitudini: prelievo settimanale di CHF 200-300, pagamenti mensili ricorrenti,
    accesso raro alla cassetta. Il profilo cambia solo chi ha accesso al conto.
    """
    if profilo not in PROFILI:
        raise ValueError(f"Profilo sconosciuto: {profilo}. Disponibili: {list(PROFILI)}")
    rng = np.random.default_rng(seed)
    inizio = pd.Timestamp("2025-01-01")
    righe = []
    for g in range(giorni):
        giorno = inizio + pd.Timedelta(days=g)
        if giorno.weekday() == 0:  # prelievo settimanale del lunedì
            canale = "bancomat" if rng.random() < 0.7 else "sportello"
            righe.append(_riga(giorno, canale, rng.uniform(200, 300)))
        if giorno.day == 1:  # pagamenti ricorrenti
            for b in _BENEFICIARI_ABITUALI:
                righe.append(_riga(giorno, "bonifico", rng.uniform(80, 1400), beneficiario=b))
        if rng.random() < 0.004:  # accesso raro alla cassetta
            righe.append(_riga(giorno, "cassetta", 0.0))
        # chi ha una procura fa ogni tanto piccole spese legittime per il titolare
        if profilo == "abuso_interno" and giorno.day == 15:
            righe.append(_riga(giorno, "bancomat", rng.uniform(100, 200), avviato_da="procuratore"))
    return pd.DataFrame(righe, columns=COLONNE)


def inietta_frode(storico: pd.DataFrame, profilo: str, n: int = 1, seed: int = 0) -> pd.DataFrame:
    """Aggiunge in coda allo storico n episodi di frode tipici del profilo."""
    rng = np.random.default_rng(seed)
    ultimo = storico["data"].max()
    nuove = []
    for i in range(n):
        giorno = ultimo + pd.Timedelta(days=1 + i * 7)
        if profilo == "truffa_esterna":
            nuove.append(_riga(giorno, "cassetta", 0.0, frode=True))
            nuove.append(_riga(giorno, "sportello", rng.uniform(25_000, 50_000), frode=True))
        elif profilo == "abuso_interno":
            for k in range(3):
                nuove.append(_riga(giorno + pd.Timedelta(days=k), "bancomat",
                                   rng.uniform(900, 1_000), avviato_da="procuratore", frode=True))
        elif profilo == "bonifico_estero":
            nuove.append(_riga(giorno, "bonifico", rng.uniform(8_000, 20_000),
                               beneficiario=f"IBAN estero #{rng.integers(1000, 9999)}",
                               estero=True, alert_banca=True, frode=True))
        else:
            raise ValueError(f"Profilo sconosciuto: {profilo}")
    return pd.concat([storico, pd.DataFrame(nuove, columns=COLONNE)], ignore_index=True)
