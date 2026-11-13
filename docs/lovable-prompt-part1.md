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
