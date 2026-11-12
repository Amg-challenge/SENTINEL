# Sentinel API · contract

The contract between the **back-end** (`backend/`, deployed on **Railway**) and the **front-end** (`frontend/`, deployed on **Vercel**). Change it only with the group's agreement, together with `backend/tests/test_api.py`.

- Base URL: the Railway domain, e.g. `https://<your-service>.up.railway.app` → in the front-end as the env var `VITE_API_URL`.
- JSON in, JSON out. No authentication (demo with synthetic data only).
- **Stateless:** consent, decisions taken on stage and the simulated clocks live in the front-end.
- Interactive docs once deployed: `<base URL>/docs`.
- **Offline fallback:** `frontend/public/demo-fallback.json` holds the same answers (`GET /demo-bundle`). If the API does not answer within ~3 seconds, the front-end uses it, so the demo never stops.

## Endpoints

| Method | Path | What it returns |
|---|---|---|
| GET | `/health` | `{"status": "ok", "version": "…"}` — Railway's health check |
| GET | `/config` | Threshold, response window, revocation delay, scope, default contact, the protected person |
| GET | `/scenarios` | The five demo scenarios |
| GET | `/scenarios/{id}` | One scenario (404 if unknown) |
| POST | `/evaluate` | Score + decision for one operation or scenario |
| POST | `/revocation` | When a deactivation / rule change would take effect (72 h) |
| GET | `/stats` | Simulation results and curves for the appendix |
| GET | `/demo-bundle` | Everything above in one file (= the offline fallback) |

## POST /evaluate

Request: pass **either** `scenario_id` **or** `operation`.

```json
{
  "scenario_id": "fake-police-cash",
  "contact": {"name": "Anna", "has_power_of_attorney": false, "co_holder": false},
  "contact_answered": false,
  "minutes_elapsed": 0
}
```

`operation` fields: `channel` (`counter` | `atm` | `safe_deposit_box` | `transfer` | `card`), `amount` (CHF ≥ 0), `payee`, `new_payee`, `foreign`, `initiated_by` (`holder` | `poa_holder` | `contact` | a name), `bank_alert`.

Response (fake police officer, default contact):

```json
{
  "score": 0.694,
  "threshold": 0.54,
  "paused": true,
  "pause_origin": "score",
  "destination": "trusted_contact",
  "destination_reason": "no conflict of interest",
  "response_window_expired": false,
  "minutes_left": 30.0,
  "reasons": [
    {
      "text": "amount far above this person's habits for the channel",
      "weight": 3.82
    }
  ],
  "operation": {
    "channel": "counter",
    "amount": 40000.0,
    "payee": "",
    "new_payee": false,
    "foreign": false,
    "initiated_by": "holder",
    "bank_alert": false
  }
}
```

The same with the internal-abuse scenario — the contact initiated it, so the **bank** verifies:

```json
{
  "score": 0.6238,
  "paused": true,
  "pause_origin": "score",
  "destination": "bank",
  "destination_reason": "the contact initiated the transaction",
  "minutes_left": null
}
```

How the front-end uses it:

| Field | Screen |
|---|---|
| `paused` | Counter: "On hold" vs "Proceed" |
| `reasons[].text` | Counter and bank queue: "why it was paused" |
| `destination` = `trusted_contact` | Contact's phone shows the notification |
| `destination` = `bank` | Bank case queue; the contact's phone says "not forwarded to you" |
| `minutes_left` | Countdown on the phone (send `minutes_elapsed` from the demo clock) |
| `response_window_expired` | Counter: "escalated to the bank, the contact did not answer" |
| `pause_origin` = `bank_antifraud` | Shows that Sentinel works on top of the bank's system |

Errors: `422` invalid input (unknown channel, negative amount, both or neither of `operation`/`scenario_id`), `404` unknown scenario.

## GET /config

```json
{
  "engine_version": "0.1.0",
  "threshold": 0.54,
  "response_window_minutes": 30,
  "revocation_delay_hours": 72,
  "scope": [
    "counter",
    "atm",
    "safe_deposit_box",
    "transfer"
  ],
  "out_of_scope": {
    "card": "covered by the bank's card antifraud"
  },
  "default_contact": {
    "name": "Anna",
    "has_power_of_attorney": false,
    "co_holder": false
  },
  "protected_person": {
    "label": "Your father",
    "branch": "Mendrisio",
    "usual_weekly_cash_chf": 246
  }
}
```

## GET /scenarios (first item)

```json
{
  "id": "fake-police-cash",
  "title": "Fake police officer: cash at the counter",
  "story": "A man claiming to be a police officer has been on the phone with the client for an hour: his savings are 'at risk' and must be handed over for safekeeping.",
  "phone_message": "is withdrawing CHF 40,000 in cash at the Mendrisio branch.",
  "operation": {
    "channel": "counter",
    "amount": 40000.0,
    "payee": "",
    "new_payee": false,
    "foreign": false,
    "initiated_by": "holder",
    "bank_alert": false
  }
}
```

Scenario ids: `fake-police-cash`, `fake-grandchild-transfer`, `safe-deposit-box`, `internal-abuse`, `bank-flagged`.

## POST /revocation

Request `{}` or `{"requested_at": "2026-12-17T09:00:00+01:00"}`. Response:

```json
{
  "requested_at": "2026-11-12T13:58:54.896012+00:00",
  "effective_at": "2026-11-15T13:58:54.896012+00:00",
  "delay_hours": 72,
  "contact_notified": true
}
```

## GET /stats

```json
{
  "threshold": 0.54,
  "auc": 0.9903,
  "simulated_clients": 150,
  "alerts_per_client_year": 1.14,
  "share_resolved_by_contact": 0.754,
  "share_escalated_to_bank": 0.246,
  "cost_to_serve_chf": 6.63,
  "fraud_episodes_caught": 0.862,
  "fraud_money_protected": 0.941,
  "note": "Synthetic data. Money protected is a benefit for the client and the family; the bank pays for trust, retention of senior clients and fewer complaints.",
  "cost_curve": "[{threshold, cost_chf}, …]",
  "roc_curve": "[{fpr, tpr}, …]"
}
```

## Keeping things in sync

After changing the engine, the scenarios or the threshold, run from `backend/`:

```bash
python scripts/export_demo_data.py
```

It rewrites `backend/data/demo.json` (read by the API at start-up) and `frontend/public/demo-fallback.json` (the fallback). `test_bundle_matches_live_evaluation` checks that the two agree.
