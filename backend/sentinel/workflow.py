"""Decision rule: when to pause an operation and WHO is asked to confirm it.

Owner: Utente 1 · branch `modello`.

Guiding principle (documents v6 and work plan v2): Sentinel does NOT detect fraud
in place of the bank. It sits on top of the existing antifraud system (or its own
score) and decides two things: WHEN to involve someone, and WHO - the trusted
contact or, when there is a conflict of interest, the bank itself.
This human process, not detection, is the heart of the product.

CONTRACT (stable signatures):
    instrada(operazione, contatto) -> (destinazione, motivo)       # "contatto" | "banca"
    decidi(operazione, punteggio, soglia, contatto, alert_esterno=False) -> Decisione
    destinazione_finale(operazione, contatto, risponde, minuti_trascorsi=0.0, ...) -> (dest, motivo)
    richiesta_revoca(ora=None) -> dict                              # 72-hour safety delay
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

FINESTRA_RISPOSTA_MIN = 30   # minutes the contact has to answer before the bank takes over
ATTESA_REVOCA_ORE = 72       # safety delay on deactivation or rule changes


@dataclass
class Contatto:
    """The trusted contact chosen by the protected person."""

    nome: str
    ha_procura: bool = False      # holds a power of attorney on the account
    cotitolare: bool = False      # co-holder of the account


@dataclass
class Decisione:
    """Outcome of the evaluation of a single operation."""

    in_pausa: bool
    destinazione: str | None      # "contatto" | "banca" | None
    motivo: str


def instrada(operazione, contatto: Contatto) -> tuple[str, str]:
    """Who verifies. Returns (destination, reason).

    Conflict-of-interest rule (v6): if the contact initiated the operation, benefits
    from it, holds a power of attorney or co-holds the account, they cannot approve
    it and the case goes automatically to the bank's manual review. This is the
    answer to the risk "the contact is the one abusing the account".
    """
    if operazione.get("avviata_da") == contatto.nome:
        return "banca", "the contact initiated the transaction"
    if operazione.get("beneficiario") and operazione.get("beneficiario") == contatto.nome:
        return "banca", "the contact is the beneficiary of the transaction"
    if contatto.ha_procura:
        return "banca", "the contact holds a power of attorney on the account"
    if contatto.cotitolare:
        return "banca", "the contact is a co-holder of the account"
    return "contatto", "no conflict of interest"


def decidi(operazione, punteggio: float, soglia: float, contatto: Contatto,
           alert_esterno: bool = False) -> Decisione:
    """Pause or not, and who is asked.

    `alert_esterno` is a flag from the bank's antifraud system (e.g. NetGuardians):
    Sentinel works ON TOP of that system, so its flag triggers the process even
    below Sentinel's own threshold.
    """
    oltre_soglia = bool(punteggio >= soglia)
    in_pausa = bool(oltre_soglia or alert_esterno)
    if not in_pausa:
        return Decisione(False, None, "transaction within normal behaviour")
    origine = ("score above threshold" if oltre_soglia
               else "flagged by the bank antifraud system")
    destinazione, motivo = instrada(operazione, contatto)
    return Decisione(True, destinazione, f"{origine}; {motivo}")


def destinazione_finale(operazione, contatto: Contatto, risponde: bool,
                        minuti_trascorsi: float = 0.0,
                        finestra: float = FINESTRA_RISPOSTA_MIN) -> tuple[str, str]:
    """Destination after the response window.

    The trusted contact is not an operator on duty: they may be asleep, at work,
    with a flat battery. If they do not answer within the window, the operation is
    not left hanging: it goes to the bank's manual review. This is the second route
    to the bank, next to the conflict of interest.
    """
    dest, motivo = instrada(operazione, contatto)
    if dest != "contatto":
        return dest, motivo
    if not risponde and minuti_trascorsi >= finestra:
        return "banca", "the contact did not answer within the window"
    return dest, motivo


def richiesta_revoca(ora: datetime | None = None) -> dict:
    """Deactivation or rule change: effective only after 72 hours, contact notified at once.

    This is what stops a fraudster from having the protection switched off during
    the phone call.
    """
    ora = ora or datetime.now()
    return {"richiesta": ora, "effettiva_dal": ora + timedelta(hours=ATTESA_REVOCA_ORE),
            "avviso_contatto": True}
