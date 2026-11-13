"""Service layer of the Sentinel API: everything the front-end needs, framework-free.

The FastAPI routes in `api/main.py` are a thin shell over this module, so the logic
can be tested without a web server.

The API speaks ENGLISH keys (for the front-end team); the engine keeps its internal
Italian column names. The translation happens only here.

Demo state (consent given, decisions taken, simulated clocks) lives in the
front-end: the API is stateless.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np

from sentinel import __version__, economics, model, profiles
from sentinel.workflow import (ATTESA_REVOCA_ORE, FINESTRA_RISPOSTA_MIN, Contatto, decidi,
                               destinazione_finale, richiesta_revoca)

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "demo.json"
SEED_PERSONA = 7          # the protected person of the demo: a typical senior
SEED_CALIBRAZIONE = 11    # simulated book used to calibrate the threshold

# ---------------------------------------------------------------- English <-> engine
CHANNELS = {"counter": "sportello", "atm": "bancomat", "safe_deposit_box": "cassetta",
            "transfer": "bonifico", "card": "carta"}
CHANNELS_BACK = {v: k for k, v in CHANNELS.items()}
DESTINATIONS = {"contatto": "trusted_contact", "banca": "bank"}

# ---------------------------------------------------------------- demo scenarios
SCENARIOS: list[dict] = [
    {
        "id": "fake-police-cash",
        "title": "Fake police officer: cash at the counter",
        "story": ("A man claiming to be a police officer has been on the phone with the client for an "
                  "hour: his savings are 'at risk' and must be handed over for safekeeping."),
        "phone_message": "is withdrawing CHF 40,000 in cash at the Mendrisio branch.",
        "operation": {"channel": "counter", "amount": 40000.0, "payee": "", "new_payee": False,
                      "foreign": False, "initiated_by": "holder", "bank_alert": False},
    },
    {
        "id": "fake-grandchild-transfer",
        "title": "Fake grandchild: transfer abroad",
        "story": ("A distressing call from a 'grandchild' in trouble: an urgent payment is needed "
                  "today, to an account abroad."),
        "phone_message": "is sending CHF 18,000 to a foreign account he has never used before.",
        "operation": {"channel": "transfer", "amount": 18000.0, "payee": "Foreign IBAN LT62 …",
                      "new_payee": True, "foreign": True, "initiated_by": "holder", "bank_alert": False},
    },
    {
        "id": "safe-deposit-box",
        "title": "Safe deposit box opened",
        "story": ("Fake police officers often ask victims to empty the safe deposit box first: gold "
                  "and cash leave no trace in the payment systems."),
        "phone_message": "is opening his safe deposit box at the Mendrisio branch. He has not opened it in over a year.",
        "operation": {"channel": "safe_deposit_box", "amount": 0.0, "payee": "", "new_payee": False,
                      "foreign": False, "initiated_by": "holder", "bank_alert": False},
    },
    {
        "id": "internal-abuse",
        "title": "Internal abuse: the contact initiated it",
        "story": ("The withdrawal was initiated by the trusted contact. They cannot verify themselves, "
                  "so the case goes straight to the bank."),
        "phone_message": "is withdrawing CHF 12,000 in cash.",
        "operation": {"channel": "atm", "amount": 12000.0, "payee": "", "new_payee": False,
                      "foreign": False, "initiated_by": "contact", "bank_alert": False},
    },
    {
        "id": "bank-flagged",
        "title": "Flagged by the bank's antifraud",
        "story": ("An ordinary withdrawal, below Sentinel's own threshold. The bank's antifraud system "
                  "flags it: Sentinel works on top of that system, not in its place."),
        "phone_message": "is withdrawing CHF 200 at an ATM.",
        "operation": {"channel": "atm", "amount": 200.0, "payee": "", "new_payee": False,
                      "foreign": False, "initiated_by": "holder", "bank_alert": True},
    },
]
SCENARIOS_BY_ID = {s["id"]: s for s in SCENARIOS}

DEFAULT_CONTACT = {"name": "Anna", "has_power_of_attorney": False, "co_holder": False}


class ApiError(ValueError):
    """Invalid input: the route turns it into an HTTP 422/404."""

    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------- engine state (built once)
@lru_cache(maxsize=1)
def _baseline() -> model.Baseline:
    return model.adatta_baseline(profiles.genera_storico("anziano", seed=SEED_PERSONA))


def _calibrate(n_clienti: int = 150) -> dict:
    """Threshold and statistics from a simulated book of seniors (frauds oversampled 15%,
    re-weighted to 1% real prevalence). Deterministic: same seed, same numbers."""
    port = profiles.genera_portafoglio(n_clienti=n_clienti, prob_frode=0.15, seed=SEED_CALIBRAZIONE)
    scored = economics.punteggia_portafoglio(port)
    curva, soglia = economics.calibra_soglia(scored)
    in_scope = scored[scored["canale"] != "carta"]
    roc, auc = economics.curva_roc(in_scope.loc[~in_scope["frode_reale"], "punteggio"],
                                   in_scope.loc[in_scope["frode_reale"], "punteggio"])
    carico = economics.stima_alert(scored[~scored["frode_reale"]], soglia)
    prot = economics.importo_protetto(scored, soglia)
    roc_small = roc.iloc[::10]
    return {
        "threshold": round(float(soglia), 4),
        "auc": round(float(auc), 4),
        "simulated_clients": int(n_clienti),
        "alerts_per_client_year": carico["alert_per_cliente_anno"],
        "share_resolved_by_contact": carico["quota_contatto"],
        "share_escalated_to_bank": carico["quota_banca"],
        "cost_to_serve_chf": carico["cost_to_serve"],
        "fraud_episodes_caught": prot["episodi_intercettati"],
        "fraud_money_protected": prot["importo_protetto"],
        "cost_curve": [{"threshold": round(float(r.soglia), 3), "cost_chf": round(float(r.costo), 3)}
                       for r in curva.itertuples()],
        "roc_curve": [{"fpr": round(float(r.fpr), 4), "tpr": round(float(r.tpr), 4)}
                      for r in roc_small.itertuples()],
        "note": ("Synthetic data. Money protected is a benefit for the client and the family; "
                 "the bank pays for trust, retention of senior clients and fewer complaints."),
    }


@lru_cache(maxsize=1)
def stats() -> dict:
    """Pre-computed statistics (data/demo.json) if present, else computed once (~10 s)."""
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("engine_version") == __version__ and "stats" in data:
            return data["stats"]
    return _calibrate()


def threshold() -> float:
    return float(stats()["threshold"])


# ---------------------------------------------------------------- public functions
def config() -> dict:
    return {
        "engine_version": __version__,
        "threshold": threshold(),
        "response_window_minutes": FINESTRA_RISPOSTA_MIN,
        "revocation_delay_hours": ATTESA_REVOCA_ORE,
        "scope": ["counter", "atm", "safe_deposit_box", "transfer"],
        "out_of_scope": {"card": "covered by the bank's card antifraud"},
        "default_contact": DEFAULT_CONTACT,
        "protected_person": {"label": "Your father", "branch": "Mendrisio",
                             "usual_weekly_cash_chf": round(float(np.expm1(_baseline().per_gruppo["contanti"][0])))},
    }


def list_scenarios() -> list[dict]:
    return [{k: s[k] for k in ("id", "title", "story", "phone_message", "operation")} for s in SCENARIOS]


def get_scenario(scenario_id: str) -> dict:
    if scenario_id not in SCENARIOS_BY_ID:
        raise ApiError(f"unknown scenario '{scenario_id}'", status=404)
    s = SCENARIOS_BY_ID[scenario_id]
    return {k: s[k] for k in ("id", "title", "story", "phone_message", "operation")}


def _to_engine(op: dict, contact_name: str) -> dict:
    channel = op.get("channel")
    if channel not in CHANNELS:
        raise ApiError(f"channel must be one of {sorted(CHANNELS)}")
    amount = float(op.get("amount", 0.0))
    if amount < 0:
        raise ApiError("amount must be >= 0")
    who = op.get("initiated_by", "holder")
    avviata_da = {"holder": "titolare", "poa_holder": "procuratore", "contact": contact_name}.get(who, who)
    return {"canale": CHANNELS[channel], "importo": amount, "beneficiario": op.get("payee", "") or "",
            "nuovo_beneficiario": bool(op.get("new_payee", False)), "estero": bool(op.get("foreign", False)),
            "avviata_da": avviata_da, "alert_banca": bool(op.get("bank_alert", False))}


def evaluate(operation: dict | None = None, scenario_id: str | None = None, contact: dict | None = None,
             contact_answered: bool = False, minutes_elapsed: float = 0.0) -> dict:
    """Score one operation and decide: pause or not, and who verifies.

    Pass either `operation` (English keys) or `scenario_id`. `contact_answered` and
    `minutes_elapsed` drive the 30-minute window: an unanswered notification older than
    the window goes to the bank.
    """
    if (operation is None) == (scenario_id is None):
        raise ApiError("pass exactly one of 'operation' or 'scenario_id'")
    if scenario_id is not None:
        operation = get_scenario(scenario_id)["operation"]
    c = {**DEFAULT_CONTACT, **(contact or {})}
    if not str(c["name"]).strip():
        raise ApiError("contact name must not be empty")
    op = _to_engine(operation, c["name"])
    contatto = Contatto(c["name"], ha_procura=bool(c["has_power_of_attorney"]), cotitolare=bool(c["co_holder"]))

    score = model.punteggio(op, _baseline())
    soglia = threshold()
    dec = decidi(op, score, soglia, contatto, alert_esterno=op["alert_banca"])
    reasons = [{"text": t, "weight": w} for t, w in model.spiega(op, _baseline())]
    if op["alert_banca"]:
        reasons.append({"text": "flagged by the bank's antifraud system", "weight": None})

    destination, why, window_expired = None, dec.motivo, False
    if dec.in_pausa:
        dest, why = destinazione_finale(op, contatto, risponde=contact_answered,
                                        minuti_trascorsi=minutes_elapsed)
        destination = DESTINATIONS[dest]
        window_expired = dec.destinazione == "contatto" and dest == "banca"
    origin = None
    if dec.in_pausa:
        origin = "score" if score >= soglia else "bank_antifraud"

    return {
        "score": round(score, 4),
        "threshold": soglia,
        "paused": dec.in_pausa,
        "pause_origin": origin,
        "destination": destination,
        "destination_reason": why,
        "response_window_expired": window_expired,
        "minutes_left": (max(0.0, FINESTRA_RISPOSTA_MIN - float(minutes_elapsed))
                         if destination == "trusted_contact" else None),
        "reasons": reasons,
        "operation": {**operation, "initiated_by": operation.get("initiated_by", "holder")},
    }


def revocation(requested_at: datetime | None = None) -> dict:
    r = richiesta_revoca(requested_at or datetime.now(timezone.utc))
    return {"requested_at": r["richiesta"].isoformat(), "effective_at": r["effettiva_dal"].isoformat(),
            "delay_hours": ATTESA_REVOCA_ORE, "contact_notified": r["avviso_contatto"]}


def demo_bundle() -> dict:
    """Everything the front-end needs offline: config, scenarios with their default
    evaluation (and the variants used on stage), statistics. Written to data/demo.json
    and to the front-end's fallback file by scripts/export_demo_data.py."""
    scen = []
    for s in SCENARIOS:
        scen.append({**get_scenario(s["id"]), "results": {
            "default": evaluate(scenario_id=s["id"]),
            "contact_has_power_of_attorney": evaluate(
                scenario_id=s["id"], contact={**DEFAULT_CONTACT, "has_power_of_attorney": True}),
            "contact_did_not_answer_30min": evaluate(scenario_id=s["id"], minutes_elapsed=30),
        }})
    return {"engine_version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "config": config(), "scenarios": scen, "stats": stats()}


def allowed_origins() -> list[str]:
    """CORS origins from the ALLOWED_ORIGINS env var (comma-separated). Default: any."""
    raw = os.environ.get("ALLOWED_ORIGINS", "*")
    return [o.strip() for o in raw.split(",") if o.strip()] or ["*"]
