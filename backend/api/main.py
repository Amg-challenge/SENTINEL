"""Sentinel API (FastAPI) - deployed on Railway, called by the front-end on Vercel.

Run locally (from the backend/ folder):
    uvicorn api.main:app --reload
Interactive docs: http://localhost:8000/docs

The contract (endpoints and JSON shapes) is documented in docs/api.md. All logic is
in api/service.py; this file only declares the routes and the data models.
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api import service
from sentinel import __version__

app = FastAPI(
    title="Sentinel API",
    version=__version__,
    description=("When the bank sees something strange, it calls the right person. "
                 "Stateless API over the Sentinel decision engine (synthetic data only)."),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=service.allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- models
class Operation(BaseModel):
    channel: Literal["counter", "atm", "safe_deposit_box", "transfer", "card"]
    amount: float = Field(0.0, ge=0, description="CHF; 0 for a safe deposit box visit")
    payee: str = Field("", description="empty for cash")
    new_payee: bool = False
    foreign: bool = False
    initiated_by: str = Field("holder", description="'holder', 'poa_holder', 'contact' or a person's name")
    bank_alert: bool = Field(False, description="flagged by the bank's own antifraud system")


class Contact(BaseModel):
    name: str = "Anna"
    has_power_of_attorney: bool = False
    co_holder: bool = False


class EvaluateRequest(BaseModel):
    operation: Optional[Operation] = None
    scenario_id: Optional[str] = None
    contact: Contact = Contact()
    contact_answered: bool = False
    minutes_elapsed: float = Field(0.0, ge=0)


class RevocationRequest(BaseModel):
    requested_at: Optional[str] = Field(None, description="ISO 8601; default: now")


# ---------------------------------------------------------------- routes
def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except service.ApiError as e:
        raise HTTPException(status_code=e.status, detail=str(e)) from e


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/config")
def get_config() -> dict:
    return service.config()


@app.get("/scenarios")
def get_scenarios() -> list[dict]:
    return service.list_scenarios()


@app.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict:
    return _call(service.get_scenario, scenario_id)


@app.post("/evaluate")
def post_evaluate(req: EvaluateRequest) -> dict:
    return _call(service.evaluate,
                 operation=req.operation.model_dump() if req.operation else None,
                 scenario_id=req.scenario_id,
                 contact=req.contact.model_dump(),
                 contact_answered=req.contact_answered,
                 minutes_elapsed=req.minutes_elapsed)


@app.post("/revocation")
def post_revocation(req: RevocationRequest = RevocationRequest()) -> dict:
    from datetime import datetime
    when = None
    if req.requested_at:
        try:
            when = datetime.fromisoformat(req.requested_at)
        except ValueError as e:
            raise HTTPException(status_code=422, detail="requested_at must be ISO 8601") from e
    return service.revocation(when)


@app.get("/stats")
def get_stats() -> dict:
    return service.stats()


@app.get("/demo-bundle")
def get_demo_bundle() -> dict:
    """Everything at once: what the front-end stores as its offline fallback."""
    return service.demo_bundle()
