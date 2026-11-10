"""Economia del rischio: soglia, costo atteso, alert e cost to serve.

Responsabile: Utente 2 · branch `dati-economia`.

Nota di posizionamento (documento di progetto v6): la perdita evitata è un
beneficio per il cliente e la famiglia, NON la giustificazione del prezzo.
Il collegamento con il business model passa da `stima_alert` -> cost to serve.

CONTRATTO (firme stabili):
    curva_costo(df: pd.DataFrame, costo_falso_allarme: float = 5.0,
                soglie=None) -> pd.DataFrame
    perdita_attesa_evitata(df: pd.DataFrame, soglia: float) -> float
    stima_alert(df: pd.DataFrame, soglia: float, giorni: int = 365,
                quota_conflitti: float | None = None, quota_non_risponde: float = 0.15,
                costo_caso_banca: float = 15.0, costo_infrastruttura: float = 2.0) -> dict
`df` deve avere le colonne 'punteggio' (da model.punteggia), 'importo', 'frode'.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from sentinel.model import adatta_baseline, punteggia
from sentinel.workflow import instrada

SCENARI = {  # coerenti con il documento di progetto v6
    "prudente": {"adesione": 0.03, "prezzo_mese": 2.00, "cac_banca": 120_000},
    "base": {"adesione": 0.08, "prezzo_mese": 2.50, "cac_banca": 100_000},
    "ottimistico": {"adesione": 0.15, "prezzo_mese": 2.50, "cac_banca": 60_000},
}


def curva_costo(df: pd.DataFrame, costo_falso_allarme: float = 5.0, soglie=None) -> pd.DataFrame:
    """Costo atteso per soglia = falsi allarmi × costo disturbo + importi di frode non fermati."""
    soglie = np.arange(0, 12.5, 0.5) if soglie is None else soglie
    righe = []
    for s in soglie:
        allarme = df["punteggio"] >= s
        fp = int((allarme & ~df["frode"]).sum())
        fn_importo = float(df.loc[~allarme & df["frode"], "importo"].sum())
        tp = int((allarme & df["frode"]).sum())
        righe.append(dict(soglia=float(s), falsi_allarmi=fp, frodi_fermate=tp,
                          importo_non_fermato=fn_importo,
                          costo=fp * costo_falso_allarme + fn_importo))
    return pd.DataFrame(righe)


def soglia_ottimale(curva: pd.DataFrame) -> float:
    """Soglia con il costo minimo; a parità sceglie la più alta (meno disturbo al contatto)."""
    minimo = curva["costo"].min()
    return float(curva.loc[curva["costo"] == minimo, "soglia"].max())


def perdita_attesa_evitata(df: pd.DataFrame, soglia: float) -> float:
    """Importo di frode intercettato alla soglia data (beneficio per il cliente)."""
    return float(df.loc[(df["punteggio"] >= soglia) & df["frode"], "importo"].sum())


def stima_alert(df: pd.DataFrame, soglia: float, giorni: int = 365,
                quota_conflitti: float | None = None, quota_non_risponde: float = 0.15,
                costo_caso_banca: float = 15.0, costo_infrastruttura: float = 2.0) -> dict:
    """Alert per cliente/anno, ripartizione contatto/banca e cost to serve.

    Funziona su un cliente solo o su un portafoglio (colonna 'cliente'): i valori
    sono sempre PER CLIENTE. Se c'è la colonna 'contatto_procura', ogni alert viene
    instradato con `workflow.instrada` (regola sul conflitto d'interesse).

    Ipotesi del pitch da verificare: ~1,5 alert/anno, ~80% al contatto, ~20% alla
    banca, cost to serve ~CHF 7 (2 infrastruttura + 5 gestione casi).
    """
    alert = df[df["punteggio"] >= soglia]
    n_clienti = int(df["cliente"].nunique()) if "cliente" in df.columns else 1
    anni = max(giorni / 365, 1e-9)
    alert_anno = len(alert) / anni / n_clienti
    if quota_conflitti is None:
        if len(alert) == 0:
            quota_conflitti = 0.0
        elif "contatto_procura" in alert.columns:
            destinazioni = [instrada({"avviato_da": r.avviato_da, "beneficiario": r.beneficiario},
                                     {"nome": "contatto", "ha_procura": bool(r.contatto_procura),
                                      "cointestatario": False})[0]
                            for r in alert.itertuples()]
            quota_conflitti = destinazioni.count("banca") / len(destinazioni)
        else:  # un solo cliente senza dati sul contatto: chi ha una procura è il contatto
            quota_conflitti = float((alert["avviato_da"] == "procuratore").mean())
    quota_banca = quota_conflitti + (1 - quota_conflitti) * quota_non_risponde
    casi_banca = alert_anno * quota_banca
    return {
        "alert_per_cliente_anno": round(alert_anno, 2),
        "quota_contatto": round(1 - quota_banca, 3),
        "quota_banca": round(quota_banca, 3),
        "casi_banca_per_cliente_anno": round(casi_banca, 3),
        "cost_to_serve": round(costo_infrastruttura + casi_banca * costo_caso_banca, 2),
    }


def punteggia_portafoglio(portafoglio: pd.DataFrame) -> pd.DataFrame:
    """Per ogni cliente impara le abitudini sull'anno 'storico' e punteggia l'anno 'valutazione'."""
    pezzi = []
    for _, cli in portafoglio.groupby("cliente", sort=False):
        base = adatta_baseline(cli[cli["periodo"] == "storico"])
        pezzi.append(punteggia(cli[cli["periodo"] == "valutazione"], base))
    return pd.concat(pezzi, ignore_index=True)


def applica_soglia_contanti(scored: pd.DataFrame, soglia_chf: float | None) -> pd.DataFrame:
    """Regola concordata tra persona e contatto: i prelievi di contanti sotto `soglia_chf`
    non generano alert (il punteggio viene azzerato). None = nessuna soglia.

    Serve per l'analisi di sensibilità: meno disturbo al contatto, ma attenzione agli
    abusi interni fatti con tanti prelievi piccoli.
    """
    if soglia_chf is None:
        return scored
    out = scored.copy()
    sotto = out["canale"].isin(["sportello", "bancomat"]) & (out["importo"] < soglia_chf)
    out.loc[sotto, "punteggio"] = 0.0
    return out


def riepilogo_portafoglio(scored: pd.DataFrame, costo_falso_allarme: float = 5.0,
                          soglia: float | None = None, **kwargs_alert) -> dict:
    """Numeri da portare nel pitch: soglia ottimale, frodi fermate, alert e cost to serve."""
    s = soglia if soglia is not None else soglia_ottimale(
        curva_costo(scored, costo_falso_allarme=costo_falso_allarme))
    frodi = scored[scored["frode"]]
    clienti_frodati = frodi["cliente"].nunique() if len(frodi) else 0
    fermati = frodi[frodi["punteggio"] >= s]["cliente"].nunique() if len(frodi) else 0
    return {
        "clienti": int(scored["cliente"].nunique()),
        "soglia_ottimale": s,
        "clienti_con_frode": int(clienti_frodati),
        "frodi_intercettate": f"{fermati}/{clienti_frodati}",
        "importo_intercettato_chf": round(perdita_attesa_evitata(scored, s)),
        **stima_alert(scored, s, **kwargs_alert),
    }
