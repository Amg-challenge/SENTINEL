"""API tests: the service layer (always) and the HTTP routes (when FastAPI is installed).

Run from backend/:  python -m pytest -q
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pytest  # noqa: E402
except ImportError:  # minimal stand-in so `python tests/test_api.py` works without pytest
    import contextlib
    import types

    @contextlib.contextmanager
    def _raises(exc):
        try:
            yield
        except exc:
            return
        raise AssertionError(f"{exc.__name__} not raised")

    pytest = types.SimpleNamespace(raises=_raises)

from api import service  # noqa: E402

EXPECTED = {  # scenario -> destination with the default contact (v6 rules)
    "fake-police-cash": "trusted_contact",
    "fake-grandchild-transfer": "trusted_contact",
    "safe-deposit-box": "trusted_contact",
    "internal-abuse": "bank",          # the contact initiated it: conflict of interest
    "bank-flagged": "trusted_contact",  # below threshold, paused by the bank's antifraud
}


def test_every_demo_scenario_is_paused_and_routed_as_in_v6():
    for sid, dest in EXPECTED.items():
        r = service.evaluate(scenario_id=sid)
        assert r["paused"] and r["destination"] == dest, sid
    assert service.evaluate(scenario_id="bank-flagged")["pause_origin"] == "bank_antifraud"


def test_conflict_and_response_window_go_to_bank():
    poa = service.evaluate(scenario_id="fake-police-cash",
                           contact={"name": "Anna", "has_power_of_attorney": True})
    late = service.evaluate(scenario_id="fake-police-cash", minutes_elapsed=31)
    answered = service.evaluate(scenario_id="fake-police-cash", minutes_elapsed=31, contact_answered=True)
    assert poa["destination"] == "bank" and late["destination"] == "bank"
    assert late["response_window_expired"] and answered["destination"] == "trusted_contact"


def test_normal_operation_is_not_paused():
    r = service.evaluate(operation={"channel": "atm", "amount": 250})
    assert not r["paused"] and r["destination"] is None and r["minutes_left"] is None


def test_card_is_out_of_scope():
    r = service.evaluate(operation={"channel": "card", "amount": 5000, "payee": "Shop", "new_payee": True})
    assert r["score"] == 0.0 and not r["paused"]


def test_invalid_input_is_rejected():
    for kwargs in ({}, {"scenario_id": "nope"}, {"operation": {"channel": "fax", "amount": 1}},
                   {"operation": {"channel": "atm", "amount": -5}},
                   {"operation": {"channel": "atm"}, "scenario_id": "bank-flagged"}):
        with pytest.raises(service.ApiError):
            service.evaluate(**kwargs)


def test_revocation_takes_72_hours():
    r = service.revocation()
    assert r["delay_hours"] == 72 and r["contact_notified"]


def test_bundle_matches_live_evaluation():
    """The front-end fallback must say exactly what the live API says."""
    b = service.demo_bundle()
    assert len(b["scenarios"]) == len(service.SCENARIOS)
    for s in b["scenarios"]:
        assert s["results"]["default"]["destination"] == service.evaluate(scenario_id=s["id"])["destination"]
    assert 0 < b["stats"]["threshold"] < 1 and b["config"]["revocation_delay_hours"] == 72


def test_http_routes():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from api.main import app
    c = TestClient(app)
    assert c.get("/health").json()["status"] == "ok"
    assert c.get("/config").json()["revocation_delay_hours"] == 72
    assert len(c.get("/scenarios").json()) == 5
    assert c.get("/scenarios/nope").status_code == 404
    r = c.post("/evaluate", json={"scenario_id": "internal-abuse"}).json()
    assert r["destination"] == "bank"
    assert c.post("/evaluate", json={"operation": {"channel": "fax", "amount": 1}}).status_code == 422
    assert c.post("/evaluate", json={}).status_code == 422
    assert c.post("/revocation", json={}).json()["delay_hours"] == 72
    assert "threshold" in c.get("/stats").json()


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_") and nome != "test_http_routes":
            f()
            print("ok ", nome)
