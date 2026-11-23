# Pitch materials (Utente 4)

**Single source of truth for the whole group:**

| File | What it is |
|---|---|
| `Sentinel-v6.pdf` | Project document **v6**: idea, canvas, market, go-to-market, unit economics, projection, deck structure. Check: the canvas says "v6". |
| `Sentinel-work-plan-v4.pdf` | Division of work and progress **v4** (16 November 2026), in Italian: what each part has done and what is left. Replaces v2. |
| **Pitch deck** | https://claude.ai/artifact/C7xGAz6TkSK3oEEGBiNJX4: 13 slides plus a 9-slide appendix, in English, with the spoken script in the speaker notes. The repository owner shares it with the group (*Share*). Export it as PowerPoint or PDF from *Share › Export*. |
| `pitch-script-and-qa.md` | Running order and speakers, the draft 90-second demo script, likely jury questions with answers, rehearsal plan, corrections to v6. |

Older versions (v5 and earlier, work plan v2 and v3) are superseded: please do not circulate them.

## Numbers used in the deck

Every figure comes from v6 or from the simulation (`backend/results/simulation_report.md`, section 1 "Numbers for the deck"), which uses the same simulated clients as the demo's `/stats`.

| | Deck | Source |
|---|---|---|
| Alerts per protected client per year | 1.5 | simulation (1.48) |
| Resolved by the contact / to the bank | 79% / 21% | simulation |
| Cost to serve per client per year | ≈ CHF 7 (simulated CHF 7.2) | v6 · simulation |
| Price | CHF 2.50 per client per month, setup fee CHF 25,000 | v6 |
| Typical bank, base scenario | 4% adoption in year 1, 8% from year 2 · 3,200 clients · CHF 96,000 revenue · LTV/CAC 7.4× · payback ≈ 16 months at maturity, 29 with the ramp | v6 · `backend/scripts/piano_finanziario.py` |
| Pilot | 500 clients, list price per client, setup fee CHF 10,000 instead of 25,000 | revised 23.11 |
| Five years (base) | 10 banks, 28,800 clients at the end of year 5 · revenue year 5 CHF 794 k · run-rate CHF 864 k · cumulative EBITDA −CHF 3.34 m | `backend/results/financial_plan.csv` |
| TAM / SAM / SOM | CHF 680 m / 27 m / 0.9 m a year (SOM = run-rate at the end of year 5) | v6, revised |
| Ask | CHF 800,000 pre-seed for the 500-client pilot, 18 months, net burn ≈ CHF 770 k (≈ 43 k a month) | v6, revised |

The problem and competition figures were checked online on 16 November 2026 and again on 23 November 2026 (KBC Guardian Angel, Swiss main-bank shares, population 65+ in Germany and Austria). The five-year plan was rebuilt on 23 November so that slides 4, 6, 11, 12 and A3 follow from the same assumptions: see `pitch-script-and-qa.md` §5. Sources are on the deck's last appendix slide and in `pitch-script-and-qa.md` §5.

## Still to do (Utente 4)

- **By 29 November:** fill the placeholders (team name, names, email, experience) and run the first timed read-through.
- **With Utente 3:** finalise the 90-second demo script (who speaks, what is shown).
- **11–16 December:** timed rehearsals and Q&A drill, then export the deck to PDF and PowerPoint.
- **Ongoing:** keep the project diary (`docs/project-diary.pdf`) up to date; after 17 December, write the rebuttal of the jury's critique for the January deliverable.
