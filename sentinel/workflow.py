"""Instradamento: A CHI chiedere conferma (contatto di fiducia o banca).

Responsabile: Utente 1 · branch `modello`.

Regola sul conflitto d'interesse: se il contatto ha avviato l'operazione, ne è
beneficiario, ha una procura sul conto o è co-titolare, NON può approvarla e il
caso passa automaticamente alla banca.

CONTRATTO (firma stabile):
    instrada(operazione: dict, contatto: dict) -> tuple[str, str]
        restituisce ("contatto" | "banca", motivo)

Chiavi attese:
    operazione: avviato_da, beneficiario
    contatto:   nome, ha_procura (bool), cointestatario (bool), raggiungibile (bool, opz.)

Regola anti-coercizione (72 ore): vedi `richiesta_revoca`.
"""
from __future__ import annotations

from datetime import datetime, timedelta

ATTESA_REVOCA = timedelta(hours=72)


def instrada(operazione: dict, contatto: dict) -> tuple[str, str]:
    nome = contatto.get("nome", "")
    if contatto.get("ha_procura"):
        return "banca", "conflitto d'interesse: il contatto ha una procura sul conto"
    if contatto.get("cointestatario"):
        return "banca", "conflitto d'interesse: il contatto è co-titolare del conto"
    if operazione.get("avviato_da") in ("procuratore", nome) and nome:
        return "banca", "conflitto d'interesse: il contatto ha avviato l'operazione"
    if nome and operazione.get("beneficiario") == nome:
        return "banca", "conflitto d'interesse: il contatto è il beneficiario"
    if contatto.get("raggiungibile", True) is False:
        return "banca", "contatto non raggiungibile: decide la banca"
    return "contatto", "verifica affidata al contatto di fiducia"


def richiesta_revoca(ora: datetime | None = None) -> dict:
    """Revoca o modifica delle regole: effettiva solo dopo 72 ore, con avviso al contatto."""
    ora = ora or datetime.now()
    return {"richiesta": ora, "effettiva_dal": ora + ATTESA_REVOCA, "avviso_contatto": True}
