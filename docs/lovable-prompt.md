# Lovable prompt · Sentinel front-end (design direction A, "Clean fintech")

How to use it:
1. In Lovable, create a new project and paste **MESSAGE 1** as the first prompt.
2. When it has finished building, paste **MESSAGE 2** (it adds the offline data file and lists the checks).
3. Iterate in Lovable until it looks right, then export the code into `frontend/` (see `frontend/README.md`). From then on the code is edited in the repo, not in Lovable.
4. On Vercel: Root Directory = `frontend`, environment variable `VITE_API_URL` = the Railway URL (no trailing slash).

The two messages are also available as separate files: `lovable-prompt-part1.md` and `lovable-prompt-part2.md`.
API contract: `api.md`. Fallback data: `frontend/public/demo-fallback.json` (regenerate with `python backend/scripts/export_demo_data.py`, then update MESSAGE 2 if you rebuild in Lovable).

---

## MESSAGE 1

# Build "Sentinel" — the pitch demo front-end

## 1. What you are building

Sentinel is a white-label module for banks. An elderly client **chooses** to activate it and names a **trusted contact** (e.g. their daughter Anna). When an unusual operation happens — cash at the counter, a safe deposit box visit, a transfer to a new or foreign account — the bank puts it **on hold** until the trusted contact confirms or blocks it. Sentinel does **not** replace the bank's antifraud system: it sits on top of it and decides **when** to involve someone and **who** (the trusted contact, or the bank itself when there is a conflict of interest).

Tagline (use verbatim): **"When the bank sees something strange, it calls the right person: the one you trust."**

This app is a **live demo shown on a projector during a 10-minute investor pitch**. It must look like a real, polished fintech product, be readable from the back of a room, and **never break on stage**. All data are synthetic. All UI text is in **English**.

## 2. Tech stack and hard constraints

- Vite + React + TypeScript + Tailwind CSS. shadcn/ui components are fine. Icons: `lucide-react` only (stroke icons). Charts: `recharts`.
- **No Supabase, no authentication, no database, no server code, no edge functions, no analytics.** The back-end already exists (Python FastAPI on Railway); this app only calls it.
- API base URL comes from `import.meta.env.VITE_API_URL` (no trailing slash). If it is empty or undefined, run fully on the bundled fallback data (see §6).
- All demo state (consent, approve/block decisions, simulated clocks, revocation) lives in the front-end (React context). The API is stateless.
- Never use emoji. Never invent numbers: every score, reason, threshold and statistic shown comes from the API or the fallback file.
- Routing with `react-router-dom`. Code organised as: `src/lib/api.ts` (types + client + fallback), `src/state/DemoContext.tsx`, `src/components/…`, `src/pages/…`.

## 3. Visual design — "Clean fintech" (follow exactly)

Calm, airy, premium neobank look (think a modern Swiss private-banking app). Light theme only.

**Colours (define as CSS variables / Tailwind theme tokens):**

| Token | Hex | Use |
|---|---|---|
| `bg` | `#F4F6FA` | page background |
| `surface` | `#FFFFFF` | cards, phone screen |
| `surface-2` | `#F8FAFC` | inner panels (notification bubble) |
| `border` | `#E2E8F0` | 1px card borders, dividers |
| `ink` | `#0F172A` | main text, phone frame |
| `ink-2` | `#334155` | body text |
| `muted` | `#475569` | secondary text (≥4.5:1 on white) |
| `subtle` | `#64748B` | labels, captions |
| `accent` | `#2448D8` | brand blue: logo tile, active steps, score bar, links |
| `accent-soft` | `#EEF2FF` / text `#1E3A8A` | info panels ("Waiting for Anna…") |
| `alert` | `#C2410C` | "Block" button, on-hold dot |
| `alert-soft` | `#FFEDD5` / text `#9A3412` | "On hold" / "Action needed" pills |
| `ok` | `#15803D` / soft `#DCFCE7` | "Approved" / "Proceed" states (always with a text label, never colour alone) |

**Typography:** headings and big numbers in **Space Grotesk** (600–700, letter-spacing −0.02em); everything else **Inter** (400–600). Load both from Google Fonts. Sizes for a projector: body 16px minimum, labels 13–14px, card titles 18–20px, page titles 40px, big amounts 44–56px.

**Shapes:** cards radius 24px, 1px `border`, very soft shadow `0 8px 24px rgba(15,23,42,0.06)`; buttons radius 16px, height 56px; pills fully rounded; inputs radius 12px. Generous spacing (cards padding 28px, gaps 16–24px). No gradients, no glassmorphism, no left-border "callout" cards.

**Logo:** a 44×44 rounded-12 tile in `accent` with a white lucide `ShieldCheck` icon, next to the word "Sentinel" in Space Grotesk 24px bold.

**Phone mockup component (`PhoneFrame`)**: 380×780 outer, radius 52, background `ink`, 12px padding; inner screen radius 42, white, padding 40px 24px 28px. **No fake status bar** (no clock/battery icons).

## 4. Screens

A persistent **top bar** on every page: logo + tagline (truncate on small screens) on the left; centre: step navigation as numbered pills `1 Person · 2 Counter · 3 Contact · 4 Bank` plus `Stage` and `Appendix` links (active = filled `accent`, white number; inactive = `#E2E8F0` circle, muted text); right: **scenario selector** (shadcn Select listing the 5 scenario titles), a **"Reset demo"** button (clears decisions, clocks and revocation; keeps consent and contact), and a **"Demo controls"** popover (see §5). Show a small status chip "Live API" (blue) or "Offline data" (grey) depending on whether the API answered.

### Stage `/` (the hero view used during the pitch)
Three columns on a ≥1280px screen (stack vertically below 1024px):
1. **Left (360px):** logo, H1 *"When the bank sees something strange, it calls the right person."* (Space Grotesk 40px), one-paragraph explanation *"The person chooses a trusted contact. Unusual cash, safe deposit visits and transfers abroad wait for their confirmation."*, then the four steps as a vertical list (1 Protected person gives consent · 2 Counter: operation on hold · 3 Trusted contact decides · 4 Bank reviews conflicts) — steps relevant to the current state are highlighted in `accent`.
2. **Centre:** the `PhoneFrame` with the trusted contact's notification (same component as the Contact screen).
3. **Right:** the counter console card (same component as the Counter screen) and under it three small timeline cards: *Requested 09:38 · Contact notified 09:38 · Bank takes over 10:08* (bank time = 09:38 + response window from config).
Clicking Approve/Block on the phone updates the console instantly.

### 1 · Protected person `/person`
Two cards side by side.
- **Activation:** checkbox *"I consent to activating Sentinel on my account"* (unchecked by default — the demo starts by switching it on); text input *Trusted contact* (default from `config.default_contact.name`); checkboxes *"Holds a power of attorney on my account"* and *"Is a co-holder of the account"*.
- **What the contact sees, and what they can do:** status banner (`ok` soft: "Sentinel is active. Your trusted contact is **Anna**." / `alert-soft`: "Sentinel is not active: without your consent it does not intervene."). Bullet list: notified only for cash at the counter, safe deposit box visits and transfers to new or foreign accounts outside the normal pattern; cannot see balance or history and cannot move money; can only approve or block; if they have an interest in the transaction the case goes to the bank; if they don't answer within {response_window_minutes} minutes the bank takes over; switching off or changing rules waits {revocation_delay_hours} hours. If power of attorney or co-holder is ticked, an `accent-soft` note: "Because Anna has access to your account, every flagged case will go to the bank, never to them."
- **Revocation card (full width, below):** title *"Revocation and changes · 72-hour safety delay"*. Buttons *Request deactivation* and *Request contact change* (with a text input for the new name). On request, call `POST /revocation` and show an `alert-soft` banner: *"Pending: deactivation of Sentinel. It takes effect in **N hours**. Protection stays active meanwhile, and Anna has already been notified."* with *Cancel request*. N = `revocation_delay_hours − demo hours elapsed`. When the demo clock reaches the delay, apply it (deactivate, or switch the contact name) and show *"The 72-hour delay has elapsed: the request has been applied."*

### 2 · Bank counter `/counter`
Above the console, the scenario `story` in italic muted text. If consent is off: a warning card *"Sentinel is not active on this account: the transaction proceeds without verification."*
**Counter console card** (design centrepiece):
- Header row: label *"COUNTER 2 · MENDRISIO"* (13px, uppercase, tracking 0.06em, `subtle`) and a status pill.
- Big amount (Space Grotesk 52px) — `CHF 40,000` formatted with thousands separators — or *"Safe deposit box access"* when amount is 0; on the right the operation label (counter → "Cash withdrawal", atm → "ATM withdrawal", transfer → "Transfer", safe_deposit_box → "Box access").
- **Score bar:** label row *"Anomaly score"* / *"0.69 · threshold 0.54"*; 10px rounded track `border` colour, fill `accent` at `score × 100%`, a 2px `ink` tick at `threshold × 100%`.
- **"Why it was paused"**: list of `reasons[].text`, each with a 6px `accent` dot (capitalise the first letter).
- Bottom panel by state:
  - not paused → `ok` soft: *"Within normal behaviour: no verification needed, proceed."*
  - paused, destination `trusted_contact`, no decision → `accent-soft` with phone icon: *"Waiting for Anna, the trusted contact. Do not pay out."*
  - paused, destination `bank` → `accent-soft`: *"Escalated to the bank's internal review: {destination_reason}."*
  - `response_window_expired` → *"Anna did not answer within 30 minutes: the case has been escalated to the bank's internal review. A transaction is never left hanging."*
  - approved → `ok` soft *"Approved by Anna. The teller may proceed."*; blocked → `alert-soft` *"Blocked. Do not execute the transaction; suggest contacting the police."*
- If `pause_origin` is `bank_antifraud`, add a small caption: *"Flagged by the bank's antifraud system — Sentinel works on top of it."*

Status pill: *On hold* (alert-soft with alert dot) / *Proceed* (ok) / *Approved* (ok) / *Blocked* (alert) / *With the bank* (accent-soft).

### 3 · Trusted contact `/contact`
Centred `PhoneFrame`. Inside, header "Sentinel" + pill *"Action needed"* (alert-soft). States:
- destination `trusted_contact`, pending: notification bubble (`surface-2`, radius 24, padding 22): *"Mendrisio branch · just now"* caption; *"Your father"* + the scenario `phone_message` — render the amount in it as a big Space Grotesk 44px line (e.g. "Your father is withdrawing" / **CHF 40,000** / "in cash at the Mendrisio branch."; if the message has no amount, show it as plain text); then *"Have you spoken to him? Do you approve?"*. Two info rows with lucide icons: `Clock` *"{minutes_left} minutes left, then the bank takes over"*, `Lock` *"You never see his balance or history"*. Buttons at the bottom: primary **"Block"** (`alert` background, white text) and secondary **"I spoke to him, approve"** (white, 1.5px `#CBD5E1` border).
- after a decision: confirmation (*"You blocked the withdrawal. Call your father."* / *"You approved it."*).
- destination `bank`: *"This case was not forwarded to you."* + reason + caption *"Sentinel never asks someone with an interest in the transaction to confirm it."*
- response window expired: *"The 30-minute window has expired. The case has gone to the bank's internal review."*
- not paused / consent off: an empty state *"Nothing to verify right now."*
- If a revocation is pending, a red-orange banner at the top of the phone: *"A request to switch Sentinel off was made. It takes effect in N hours. If you know nothing about it, call your father or the bank."*

### 4 · Bank case queue `/bank`
Card with a table (horizontal scroll on small screens): for **all five scenarios** evaluated with the current contact settings and clocks, list those whose `paused` is true and `destination` is `bank`. Columns: Scenario · Transaction (label + amount) · Score · Why it was paused (reasons joined) · Why it came to the bank (`destination_reason`, or "no answer within 30 minutes") · Status ("To review" / "Blocked" / "Approved") with *Block* and *Approve* buttons per row. Empty state: *"No cases in the queue."* + hint *"Tick 'holds a power of attorney' on screen 1, or pick the internal-abuse scenario."*

### Appendix `/appendix`
Title *"How the engine is calibrated"*, caption *"Synthetic data — the real test is a pilot with a bank."* From `GET /stats`:
- Six stat tiles: Alerts per client per year · Resolved by the contact (%) · Escalated to the bank (%) · Cost to serve (CHF/client/year) · Fraud money protected (%) · AUC.
- **Cost curve** (recharts LineChart, `cost_curve` points `{threshold, cost_chf}`, y axis log scale, x 0–1) with a dashed `alert` reference line at the threshold; caption *"The threshold is an economic decision: it balances disturbing the contact and letting money go."*
- **ROC curve** (`roc_curve` points `{fpr, tpr}`) in `accent` with a dashed grey diagonal; caption with the AUC.
- Table *"Scenario scores"*: title, score, paused yes/no, reasons.
- Show `stats.note` verbatim at the bottom. Never present money protected as the reason the bank pays.

## 5. Demo controls (popover in the top bar)

Clocks are simulated: on stage nobody can wait 30 minutes or 72 hours.
- Slider *"Minutes since the notification"* 0–60 (step 1).
- Slider *"Hours since the revocation request"* 0–`revocation_delay_hours` (step 1).
- Toggle *"Force offline data"* (uses the fallback even if the API works — useful for rehearsals).

## 6. Data layer — the API contract (do not change names)

`src/lib/api.ts` must export these TypeScript types and functions.

```ts
export type Channel = "counter" | "atm" | "safe_deposit_box" | "transfer" | "card";
export interface Operation { channel: Channel; amount: number; payee: string; new_payee: boolean; foreign: boolean; initiated_by: string; bank_alert: boolean; }
export interface Contact { name: string; has_power_of_attorney: boolean; co_holder: boolean; }
export interface Reason { text: string; weight: number | null; }
export interface Evaluation {
  score: number; threshold: number; paused: boolean;
  pause_origin: "score" | "bank_antifraud" | null;
  destination: "trusted_contact" | "bank" | null; destination_reason: string;
  response_window_expired: boolean; minutes_left: number | null;
  reasons: Reason[]; operation: Operation;
}
export interface Scenario { id: string; title: string; story: string; phone_message: string; operation: Operation; }
export interface Config {
  engine_version: string; threshold: number; response_window_minutes: number; revocation_delay_hours: number;
  scope: Channel[]; out_of_scope: Record<string, string>; default_contact: Contact;
  protected_person: { label: string; branch: string; usual_weekly_cash_chf: number };
}
export interface Stats {
  threshold: number; auc: number; simulated_clients: number; alerts_per_client_year: number;
  share_resolved_by_contact: number; share_escalated_to_bank: number; cost_to_serve_chf: number;
  fraud_episodes_caught: number; fraud_money_protected: number; note: string;
  cost_curve: { threshold: number; cost_chf: number }[]; roc_curve: { fpr: number; tpr: number }[];
}
export interface Revocation { requested_at: string; effective_at: string; delay_hours: number; contact_notified: boolean; }
```

Endpoints (base = `VITE_API_URL`):
- `GET /health` → `{status: "ok", version}`
- `GET /config` → `Config`
- `GET /scenarios` → `Scenario[]` (ids: `fake-police-cash`, `fake-grandchild-transfer`, `safe-deposit-box`, `internal-abuse`, `bank-flagged`)
- `POST /evaluate` body `{ scenario_id: string, contact: Contact, contact_answered: boolean, minutes_elapsed: number }` → `Evaluation`. Set `contact_answered` to true once Approve/Block was pressed for that scenario; `minutes_elapsed` = demo minutes slider.
- `POST /revocation` body `{}` → `Revocation`
- `GET /stats` → `Stats`

**Reliability rules (critical):**
1. Every request has a **3-second timeout** (AbortController). On error/timeout, or if `VITE_API_URL` is not set, or "Force offline data" is on, use the fallback file `/demo-fallback.json` (fetch it once from `public/`, cache in memory). Show the "Offline data" chip.
2. Fallback shape: `{ config: Config, scenarios: (Scenario & { results: { default: Evaluation; contact_has_power_of_attorney: Evaluation; contact_did_not_answer_30min: Evaluation } })[], stats: Stats }`.
3. Offline `evaluate`: pick `contact_has_power_of_attorney` if the contact has power of attorney **or** is a co-holder (if co-holder only, replace `destination_reason` with "the contact is a co-holder of the account"); else pick `contact_did_not_answer_30min` if no decision yet and minutes ≥ `response_window_minutes`; else `default`, recomputing `minutes_left = max(0, response_window_minutes − minutes)` when the destination is the trusted contact. For the `internal-abuse` scenario keep the precomputed result (always bank).
4. Offline `revocation`: `effective_at = now + revocation_delay_hours`.
5. On start-up call `GET /health`; then load config, scenarios and stats in parallel. Re-evaluate the current scenario (and, on the Bank page, all five) whenever consent, contact, decisions or the minutes slider change — debounce 250 ms, keep the previous result visible while loading (no flashing spinners on stage).
6. If consent is off, do not call `/evaluate`: show the "not active" states.

## 7. Quality bar

- Pixel-clean at 1920×1080 and 1440×900 (projector); usable at 1280×800; stacks gracefully on a phone.
- Accessible: real `<button>`/`<label>`/`<input>`, visible focus rings in `accent`, `aria-label` on icon-only buttons, text contrast ≥ 4.5:1, states never conveyed by colour alone.
- Subtle motion only: 150–200 ms fades when the phone notification appears and when the status pill changes. Respect `prefers-reduced-motion`.
- Amounts: `CHF 40,000` (en-CH grouping with comma as in the API messages); scores with 2 decimals; percentages with 0 decimals.
- No placeholder lorem ipsum, no fake logos of real banks, no real people's names other than "Anna" and "Your father".

Build everything above in one go. Wait for my next message, which contains the content of `public/demo-fallback.json`.


---

## MESSAGE 2

Create the file `public/demo-fallback.json` with **exactly** the JSON below (copy it verbatim, do not reformat values, do not add or remove fields). The app must load it as described in §6 of my previous message, and it must work fully on this file when `VITE_API_URL` is not set — which is the case here in Lovable.

After creating it, check that:
1. With consent off, the Counter shows "Sentinel is not active".
2. With consent on and scenario "Fake police officer: cash at the counter": the console shows CHF 40,000, score 0.69 vs threshold 0.54, "On hold", and the phone shows the notification with 30 minutes left.
3. Pressing "Block" on the phone turns the console to "Blocked".
4. Moving "Minutes since the notification" to 30+ without a decision escalates the case to the bank (Bank queue shows it).
5. Scenario "Internal abuse: the contact initiated it" never reaches the phone and appears in the Bank queue.
6. Scenario "Flagged by the bank's antifraud" is paused although its score (0.05) is below the threshold.
7. The Appendix shows the six tiles and both charts.

```json
{"engine_version":"0.1.0","generated_at":"2026-11-12T13:57:52+00:00","config":{"engine_version":"0.1.0","threshold":0.54,"response_window_minutes":30,"revocation_delay_hours":72,"scope":["counter","atm","safe_deposit_box","transfer"],"out_of_scope":{"card":"covered by the bank's card antifraud"},"default_contact":{"name":"Anna","has_power_of_attorney":false,"co_holder":false},"protected_person":{"label":"Your father","branch":"Mendrisio","usual_weekly_cash_chf":246}},"scenarios":[{"id":"fake-police-cash","title":"Fake police officer: cash at the counter","story":"A man claiming to be a police officer has been on the phone with the client for an hour: his savings are 'at risk' and must be handed over for safekeeping.","phone_message":"is withdrawing CHF 40,000 in cash at the Mendrisio branch.","operation":{"channel":"counter","amount":40000.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":false},"results":{"default":{"score":0.694,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"trusted_contact","destination_reason":"no conflict of interest","response_window_expired":false,"minutes_left":30.0,"reasons":[{"text":"amount far above this person's habits for the channel","weight":3.82}],"operation":{"channel":"counter","amount":40000.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":false}},"contact_has_power_of_attorney":{"score":0.694,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"bank","destination_reason":"the contact holds a power of attorney on the account","response_window_expired":false,"minutes_left":null,"reasons":[{"text":"amount far above this person's habits for the channel","weight":3.82}],"operation":{"channel":"counter","amount":40000.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":false}},"contact_did_not_answer_30min":{"score":0.694,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"bank","destination_reason":"the contact did not answer within the window","response_window_expired":true,"minutes_left":null,"reasons":[{"text":"amount far above this person's habits for the channel","weight":3.82}],"operation":{"channel":"counter","amount":40000.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":false}}}},{"id":"fake-grandchild-transfer","title":"Fake grandchild: transfer abroad","story":"A distressing call from a 'grandchild' in trouble: an urgent payment is needed today, to an account abroad.","phone_message":"is sending CHF 18,000 to a foreign account he has never used before.","operation":{"channel":"transfer","amount":18000.0,"payee":"Foreign IBAN LT62 …","new_payee":true,"foreign":true,"initiated_by":"holder","bank_alert":false},"results":{"default":{"score":0.7311,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"trusted_contact","destination_reason":"no conflict of interest","response_window_expired":false,"minutes_left":30.0,"reasons":[{"text":"payee never seen before","weight":2.0},{"text":"foreign account","weight":1.5},{"text":"outgoing transfer","weight":0.5}],"operation":{"channel":"transfer","amount":18000.0,"payee":"Foreign IBAN LT62 …","new_payee":true,"foreign":true,"initiated_by":"holder","bank_alert":false}},"contact_has_power_of_attorney":{"score":0.7311,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"bank","destination_reason":"the contact holds a power of attorney on the account","response_window_expired":false,"minutes_left":null,"reasons":[{"text":"payee never seen before","weight":2.0},{"text":"foreign account","weight":1.5},{"text":"outgoing transfer","weight":0.5}],"operation":{"channel":"transfer","amount":18000.0,"payee":"Foreign IBAN LT62 …","new_payee":true,"foreign":true,"initiated_by":"holder","bank_alert":false}},"contact_did_not_answer_30min":{"score":0.7311,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"bank","destination_reason":"the contact did not answer within the window","response_window_expired":true,"minutes_left":null,"reasons":[{"text":"payee never seen before","weight":2.0},{"text":"foreign account","weight":1.5},{"text":"outgoing transfer","weight":0.5}],"operation":{"channel":"transfer","amount":18000.0,"payee":"Foreign IBAN LT62 …","new_payee":true,"foreign":true,"initiated_by":"holder","bank_alert":false}}}},{"id":"safe-deposit-box","title":"Safe deposit box opened","story":"Fake police officers often ask victims to empty the safe deposit box first: gold and cash leave no trace in the payment systems.","phone_message":"is opening his safe deposit box at the Mendrisio branch. He has not opened it in over a year.","operation":{"channel":"safe_deposit_box","amount":0.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":false},"results":{"default":{"score":0.6225,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"trusted_contact","destination_reason":"no conflict of interest","response_window_expired":false,"minutes_left":30.0,"reasons":[{"text":"safe deposit box visit (rare for this person)","weight":3.5}],"operation":{"channel":"safe_deposit_box","amount":0.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":false}},"contact_has_power_of_attorney":{"score":0.6225,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"bank","destination_reason":"the contact holds a power of attorney on the account","response_window_expired":false,"minutes_left":null,"reasons":[{"text":"safe deposit box visit (rare for this person)","weight":3.5}],"operation":{"channel":"safe_deposit_box","amount":0.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":false}},"contact_did_not_answer_30min":{"score":0.6225,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"bank","destination_reason":"the contact did not answer within the window","response_window_expired":true,"minutes_left":null,"reasons":[{"text":"safe deposit box visit (rare for this person)","weight":3.5}],"operation":{"channel":"safe_deposit_box","amount":0.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":false}}}},{"id":"internal-abuse","title":"Internal abuse: the contact initiated it","story":"The withdrawal was initiated by the trusted contact. They cannot verify themselves, so the case goes straight to the bank.","phone_message":"is withdrawing CHF 12,000 in cash.","operation":{"channel":"atm","amount":12000.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"contact","bank_alert":false},"results":{"default":{"score":0.6238,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"bank","destination_reason":"the contact initiated the transaction","response_window_expired":false,"minutes_left":null,"reasons":[{"text":"amount far above this person's habits for the channel","weight":3.51}],"operation":{"channel":"atm","amount":12000.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"contact","bank_alert":false}},"contact_has_power_of_attorney":{"score":0.6238,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"bank","destination_reason":"the contact initiated the transaction","response_window_expired":false,"minutes_left":null,"reasons":[{"text":"amount far above this person's habits for the channel","weight":3.51}],"operation":{"channel":"atm","amount":12000.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"contact","bank_alert":false}},"contact_did_not_answer_30min":{"score":0.6238,"threshold":0.54,"paused":true,"pause_origin":"score","destination":"bank","destination_reason":"the contact initiated the transaction","response_window_expired":false,"minutes_left":null,"reasons":[{"text":"amount far above this person's habits for the channel","weight":3.51}],"operation":{"channel":"atm","amount":12000.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"contact","bank_alert":false}}}},{"id":"bank-flagged","title":"Flagged by the bank's antifraud","story":"An ordinary withdrawal, below Sentinel's own threshold. The bank's antifraud system flags it: Sentinel works on top of that system, not in its place.","phone_message":"is withdrawing CHF 200 at an ATM.","operation":{"channel":"atm","amount":200.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":true},"results":{"default":{"score":0.0474,"threshold":0.54,"paused":true,"pause_origin":"bank_antifraud","destination":"trusted_contact","destination_reason":"no conflict of interest","response_window_expired":false,"minutes_left":30.0,"reasons":[{"text":"flagged by the bank's antifraud system","weight":null}],"operation":{"channel":"atm","amount":200.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":true}},"contact_has_power_of_attorney":{"score":0.0474,"threshold":0.54,"paused":true,"pause_origin":"bank_antifraud","destination":"bank","destination_reason":"the contact holds a power of attorney on the account","response_window_expired":false,"minutes_left":null,"reasons":[{"text":"flagged by the bank's antifraud system","weight":null}],"operation":{"channel":"atm","amount":200.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":true}},"contact_did_not_answer_30min":{"score":0.0474,"threshold":0.54,"paused":true,"pause_origin":"bank_antifraud","destination":"bank","destination_reason":"the contact did not answer within the window","response_window_expired":true,"minutes_left":null,"reasons":[{"text":"flagged by the bank's antifraud system","weight":null}],"operation":{"channel":"atm","amount":200.0,"payee":"","new_payee":false,"foreign":false,"initiated_by":"holder","bank_alert":true}}}}],"stats":{"threshold":0.54,"auc":0.9903,"simulated_clients":150,"alerts_per_client_year":1.14,"share_resolved_by_contact":0.754,"share_escalated_to_bank":0.246,"cost_to_serve_chf":6.63,"fraud_episodes_caught":0.862,"fraud_money_protected":0.941,"cost_curve":[{"threshold":0.0,"cost_chf":1322.7},{"threshold":0.02,"cost_chf":536.967},{"threshold":0.04,"cost_chf":536.967},{"threshold":0.06,"cost_chf":276.967},{"threshold":0.08,"cost_chf":36.967},{"threshold":0.1,"cost_chf":36.967},{"threshold":0.12,"cost_chf":28.567},{"threshold":0.14,"cost_chf":28.567},{"threshold":0.16,"cost_chf":28.533},{"threshold":0.18,"cost_chf":28.5},{"threshold":0.2,"cost_chf":28.367},{"threshold":0.22,"cost_chf":28.2},{"threshold":0.24,"cost_chf":28.067},{"threshold":0.26,"cost_chf":27.833},{"threshold":0.28,"cost_chf":26.306},{"threshold":0.3,"cost_chf":26.006},{"threshold":0.32,"cost_chf":25.606},{"threshold":0.34,"cost_chf":25.694},{"threshold":0.36,"cost_chf":25.227},{"threshold":0.38,"cost_chf":15.094},{"threshold":0.4,"cost_chf":16.612},{"threshold":0.42,"cost_chf":15.712},{"threshold":0.44,"cost_chf":15.774},{"threshold":0.46,"cost_chf":16.135},{"threshold":0.48,"cost_chf":14.901},{"threshold":0.5,"cost_chf":14.001},{"threshold":0.52,"cost_chf":13.135},{"threshold":0.54,"cost_chf":12.701},{"threshold":0.56,"cost_chf":16.452},{"threshold":0.58,"cost_chf":18.508},{"threshold":0.6,"cost_chf":22.45},{"threshold":0.62,"cost_chf":30.364},{"threshold":0.64,"cost_chf":36.68},{"threshold":0.66,"cost_chf":47.19},{"threshold":0.68,"cost_chf":47.19},{"threshold":0.7,"cost_chf":60.664},{"threshold":0.72,"cost_chf":60.664},{"threshold":0.74,"cost_chf":80.478},{"threshold":0.76,"cost_chf":80.478},{"threshold":0.78,"cost_chf":85.109},{"threshold":0.8,"cost_chf":85.109},{"threshold":0.82,"cost_chf":88.774},{"threshold":0.84,"cost_chf":88.774},{"threshold":0.86,"cost_chf":88.774},{"threshold":0.88,"cost_chf":103.718},{"threshold":0.9,"cost_chf":103.718},{"threshold":0.92,"cost_chf":103.718},{"threshold":0.94,"cost_chf":103.718},{"threshold":0.96,"cost_chf":103.718},{"threshold":0.98,"cost_chf":103.718},{"threshold":1.0,"cost_chf":103.718}],"roc_curve":[{"fpr":1.0,"tpr":1.0},{"fpr":0.5158,"tpr":1.0},{"fpr":0.0659,"tpr":1.0},{"fpr":0.0503,"tpr":1.0},{"fpr":0.0499,"tpr":1.0},{"fpr":0.049,"tpr":1.0},{"fpr":0.0448,"tpr":0.9737},{"fpr":0.0428,"tpr":0.8947},{"fpr":0.0225,"tpr":0.8421},{"fpr":0.0148,"tpr":0.7895},{"fpr":0.0101,"tpr":0.7895},{"fpr":0.0077,"tpr":0.7105},{"fpr":0.0077,"tpr":0.6316},{"fpr":0.0043,"tpr":0.5263},{"fpr":0.0043,"tpr":0.4211},{"fpr":0.0,"tpr":0.1053},{"fpr":0.0,"tpr":0.0789},{"fpr":0.0,"tpr":0.0263},{"fpr":0.0,"tpr":0.0},{"fpr":0.0,"tpr":0.0},{"fpr":0.0,"tpr":0.0}],"note":"Synthetic data. Money protected is a benefit for the client and the family; the bank pays for trust, retention of senior clients and fewer complaints."}}
```
