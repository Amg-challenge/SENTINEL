"""Motore di decisione: QUANDO coinvolgere il contatto di fiducia.

Responsabile: Utente 1 · branch `modello`.

Sentinel non sostituisce l'antifrode della banca: ne riceve gli alert (colonna
`alert_banca`, es. NetGuardians) e aggiunge le soglie personali e i canali fisici
(sportello, cassetta). Il punteggio è trasparente: ogni punto ha un motivo leggibile.

CONTRATTO (firme stabili):
    adatta_baseline(storico: pd.DataFrame) -> dict
    punteggia(df: pd.DataFrame, base: dict) -> pd.DataFrame   # aggiunge 'punteggio' e 'motivi'
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Pesi del punteggio: da calibrare in notebooks/calibrazione.ipynb
PESI = {
    "importo": 1.0,             # per ogni MAD robusta sopra la mediana (max 6)
    "beneficiario_nuovo": 2.0,
    "estero": 1.5,
    "cassetta": 2.0,            # accesso alla cassetta, raro per definizione
    "procuratore": 1.0,         # operazione avviata da chi ha una procura
    "alert_banca": 2.0,         # segnalato dall'antifrode già in uso dalla banca
    "frequenza": 2.0,           # più operazioni insolite nello stesso giorno/settimana
}


def adatta_baseline(storico: pd.DataFrame) -> dict:
    """Abitudini della persona: mediana e MAD degli importi per canale, beneficiari noti."""
    base: dict = {"per_canale": {}, "beneficiari_noti": set()}
    for canale, gruppo in storico.groupby("canale"):
        importi = gruppo["importo"].to_numpy()
        mediana = float(np.median(importi))
        mad = float(np.median(np.abs(importi - mediana))) * 1.4826
        base["per_canale"][canale] = {"mediana": mediana, "mad": max(mad, 50.0)}
    base["beneficiari_noti"] = set(storico.loc[storico["beneficiario"] != "", "beneficiario"])
    # spesa settimanale abituale di chi ha una procura
    proc = storico[storico["avviato_da"] == "procuratore"]
    base["procuratore_settimanale"] = float(
        proc.groupby(proc["data"].dt.to_period("W"))["importo"].sum().median()) if len(proc) else 0.0
    return base


def punteggia(df: pd.DataFrame, base: dict) -> pd.DataFrame:
    """Restituisce una copia di df con le colonne 'punteggio' (float) e 'motivi' (str)."""
    out = df.copy()
    punteggi, motivi = [], []
    proc = out[out["avviato_da"] == "procuratore"]
    settimana_proc = proc.groupby(proc["data"].dt.to_period("W"))["importo"].sum().to_dict()
    for _, r in out.iterrows():
        p, m = 0.0, []
        ref = base["per_canale"].get(r["canale"], {"mediana": 0.0, "mad": 50.0})
        z = (r["importo"] - ref["mediana"]) / ref["mad"]
        if z > 3:
            p += PESI["importo"] * min(z, 6.0)
            m.append(f"importo insolito per il canale {r['canale']}")
        if r["beneficiario"] and r["beneficiario"] not in base["beneficiari_noti"]:
            p += PESI["beneficiario_nuovo"]; m.append("beneficiario mai visto")
        if r["estero"]:
            p += PESI["estero"]; m.append("conto estero")
        if r["canale"] == "cassetta":
            p += PESI["cassetta"]; m.append("accesso alla cassetta")
        if r["avviato_da"] == "procuratore":
            p += PESI["procuratore"]; m.append("avviata da chi ha una procura")
            sett = settimana_proc.get(r["data"].to_period("W"), 0.0)
            if base.get("procuratore_settimanale", 0) and sett > 3 * base["procuratore_settimanale"]:
                p += PESI["frequenza"]; m.append("spese del procuratore molto sopra il solito")
        if r["alert_banca"]:
            p += PESI["alert_banca"]; m.append("segnalata dall'antifrode della banca")
        punteggi.append(round(p, 2)); motivi.append("; ".join(m))
    out["punteggio"], out["motivi"] = punteggi, motivi
    return out
