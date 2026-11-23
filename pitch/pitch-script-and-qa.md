# Sentinel pitch · running order, demo script, jury Q&A and rehearsals

*Utente 4 · status 16 November 2026 · presentation on Wednesday 17 December 2026.*

**Deck:** https://claude.ai/artifact/C7xGAz6TkSK3oEEGBiNJX4. It has 13 slides plus a 9-slide appendix. The full spoken script is in each slide's speaker notes. Export it as PowerPoint or PDF from *Share › Export*, and keep a PDF copy on a USB stick for the day.

**Placeholders to fill before 29 November:** `[Team name]`, `[Name 1–4]`, `[team email]`, and one line of real experience per person on the Team slide.

---

## 1. Running order and speakers

Assumption: a pitch of **about 9 minutes, then questions**. Confirm the time limit with the professor. If it is shorter, see the cut list in §6.

Each person presents the part they built (Team slide): [Name 1] decision engine · [Name 2] data and risk economics · [Name 3] product and interface · [Name 4] business and pitch.

| # | Slide | Speaker | Time | The one line to land |
|---|---|---|---|---|
| 1 | Title | [Name 4] | 0:15 | “When the bank sees something unusual, it calls the right person: the one you trust.” |
| 2 | Problem | [Name 4] | 1:00 | The payment is authorised by the client; under pressure, the client confirms it. |
| 3 | Solution | [Name 4] | 0:45 | The client chooses, Sentinel pauses, the trusted contact confirms or requests a bank review; the bank decides when there is a conflict, no answer, or a review request. |
| 4 | Market | [Name 2] | 0:40 | Switzerland is the launch pad; the venture size is in DACH. |
| 5 | Product: live demo | [Name 3] (drives and narrates) | 1:30 | See §2. |
| 6 | Business model | [Name 2] | 0:50 | The bank pays CHF 2.50 per client per month for trust, not for the money saved. |
| 7 | Go-to-market | [Name 2] | 0:35 | One pilot bank in Ticino, then the sister banks. |
| 8 | Prototype and early validation | [Name 1] | 0:40 | A live prototype; the simulated bank shows the plan is consistent (1.5 alerts, 21% to the bank, CHF 7.3) — the pilot must prove it. |
| 9 | Competition | [Name 1] | 0:50 | KBC runs the idea at scale; we make it a ready module for every bank, with the counter, the safe box and internal abuse covered. |
| 10 | Team | [Name 1] | 0:25 | Four people, one part of the product each. |
| 11 | Financials | [Name 4] | 0:45 | J-curve; break-even at about 60,000 clients, with DACH. |
| 12 | The ask | [Name 4] | 0:35 | CHF 800,000 pre-seed to run the 500-client pilot, 18 months, three milestones. |
| 13 | Closing | [Name 4] | 0:20 | “We are looking for a Ticino bank for a 500-client pilot.” |
| | **Total** | | **9:10** | |

Handovers: 3→4, 4→5, 5→6, 7→8 and 10→11. The person finishing names the next speaker (“Now [Name 3] will show you the product”).

## 2. Demo script (90 seconds) · draft to finalise with Utente 3

**Before going on stage:**
- Open https://sentinel-lilac-two.vercel.app in a fresh tab at 100% zoom, scenario *Fake police officer: cash at the counter*.
- Press *Reset demo* and check that the chip shows **Live API**.
- Have the backup video open in a second tab.

| Time | Screen | Do | Say |
|---|---|---|---|
| 0:00–0:10 | **Person** | Tick *I consent to activating Sentinel on my account*; Anna is the trusted contact | “At the branch, the father switches Sentinel on and names his daughter Anna. Anna never sees his balance.” |
| 0:10–0:30 | **Counter** | Show the paused operation | “The fake police call: he asks for CHF 40,000 in cash. The teller sees *On hold*: score 0.69 against a threshold of 0.50, and the reason in plain words. Do not pay out.” |
| 0:30–0:50 | **Contact** | Click **Stop · ask the bank to check** | “Anna gets this message. She calls him, understands it is a scam, and asks the bank to review it. The counter says: do not pay out, the bank will speak with him first. Anna cannot freeze his money on her own: she hands the case to the bank.” |
| 0:50–1:10 | **Person**, then **Contact** | Click *Request deactivation*; show the alert on Anna’s phone | “The scammers come back and make him switch Sentinel off. It takes 72 hours, and Anna is told at once — a rule we propose to the bank.” |
| 1:10–1:30 | **Bank** | Show Anna’s case in the queue; then switch scenario to *Internal abuse: the contact initiated it* | “Here is Anna’s case: the bank talks to the father and takes the final decision. And if the person asked to confirm is the one who benefits, Sentinel never asks them: the case comes here directly.” |

**If something fails:**
- No network: the demo switches to offline data by itself (chip *Offline data*); carry on.
- Laptop problem: play the backup video (Utente 3, ready by 10 December).
- Never debug on stage.

To check with Utente 3 when rehearsing: where the *Demo controls* (minutes and hours since the request) are needed, and whether the order above fits the screens in 90 seconds.

## 3. Likely jury questions

Answers in two or three sentences. **Owner** is who answers first; *A1–A8* are the appendix slides to open.

### Business model
| Question | Short answer | Owner · slide |
|---|---|---|
| Why would a bank pay, if the scam loss usually stays with the client? | It pays for trust and relationships: its reputation, its senior and affluent clients, a link with the heirs, fewer complaints. About CHF 96,000 a year for a typical bank, less than one full-time employee. | [Name 2] · 6 |
| Is 8% adoption realistic? | It is our main uncertainty, and the pilot measures it first. The model works above about 3% (LTV/CAC ≥ 3×); a 12-month payback needs about 11%. | [Name 2] · A3 |
| Why not charge the client or the family? | The bank owns the relationship and the channel (app, counter). A direct family plan is an option, not the base case. | [Name 2] · A7 |
| What does it cost you per client? | About CHF 7 a year, measured by simulating the whole process: CHF 2 platform, 0.6 notifications, 4.7 bank reviews (CHF 7.3). Never above about CHF 11 in our stress tests, against a CHF 30 price. | [Name 2] · A2 |
| When do you break even? | At about 60,000 clients (≈ 19 mature banks), not before years 7–8, with Germany and Austria. Each funding round is tied to a milestone. | [Name 4] · 11 |
| What are your fixed costs made of, and why do they grow? | Mostly people: the team is 52% of fixed costs in year 1 and 67% in year 5, from 4 founders on reduced pay (CHF 260 k, about CHF 4,700 gross a month each) to 9 people in year 5 (CHF 940 k). The rest: development and maintenance (80 → 110 k), base cloud (30 → 90 k), compliance, security and legal (70 → 120 k), sales (60 → 140 k). They grow with each bank: integration, supplier audits, support. This split of the v6 totals is our planning assumption (`backend/results/fixed_costs.csv`). Salaries are lean: from year 3 hires average about CHF 100 k loaded, below the Swiss market for software roles (median gross about CHF 96–110 k, plus 13–19% employer charges). At market pay the five-year loss is CHF 3.81 m instead of 3.34 m, the seed would need to be about CHF 3.5 m, and break-even moves to ≈ 67,000 clients; the first 18 months do not change. | [Name 4] · 11 |
| Is CHF 800,000 enough? | Just. In months 1–18 the plan spends CHF 851 k and earns ≈ CHF 82 k from the pilot: an EBITDA loss of ≈ CHF 770 k, which is also the cash need (no capex, no tax on losses, receivables under CHF 10 k). About CHF 31 k is left, three weeks of costs. A late pilot would need the non-dilutive money or an earlier seed. | [Name 4] · 12 |
| What do investors get, and who could buy you? | Exposure to a regulated, sticky B2B niche. Natural acquirers: antifraud and core-banking vendors that want the module for their banks. | [Name 4] · 12 |

### Competition
| Question | Short answer | Owner · slide |
|---|---|---|
| KBC already does this: why would banks not build it? | Large banks can. Our hypothesis, still to test in interviews, is that many mid-sized and small banks would rather buy a ready module than build one. KBC’s Guardian Angel works on transfers in its app, flagged by its own fraud system; according to KBC’s FAQ, without an answer the transfer can still go ahead after a waiting period. Sentinel adds the counter and the safe deposit box, a conflict-of-interest rule and the bank after 30 minutes. | [Name 1] · 9 |
| What if KBC or Vyntra (ex-NetGuardians) offers it? | KBC offers the concept to other financial institutions on request, so speed matters: we aim to move early in Switzerland, with the counter, the safe deposit box and internal abuse covered. We see Vyntra as a partner and channel, not a rival. | [Name 1] · A6 |
| What is your moat? | Honestly none today. Switching costs (integration, contacts and rules already set) and scale (integration and compliance spread over many banks) come with adoption. | [Name 1] · 9 |

### Product and technology
| Question | Short answer | Owner · slide |
|---|---|---|
| Won’t clients be annoyed by alerts? | About 1.5 a year per client in our simulation, and only on unusual operations. The threshold is set by cost; an optional agreed cash limit exists for heavy cash users. | [Name 1] · A2 |
| What if the trusted contact is the abuser? | If they initiated the operation, benefit from it, hold a power of attorney or are co-holder, they are never asked: the bank decides. They never see the balance and cannot move money. | [Name 3] · A4 |
| The client waits 30 minutes at the counter? | Most contacts answer in minutes; after 30 minutes the bank decides, and nothing is approved by default. In the pilot we would also let the branch send a case to the bank’s review at once. | [Name 3] · A4 |
| What if the scammer makes the victim switch Sentinel off? | It takes 72 hours and the contact is told immediately (tested: active at 71 h, off at 72 h). It is a rule we propose: a client can normally revoke an instruction at any time (for a mandate, art. 404 CO), so the bank’s lawyers must confirm whether and how the delay can be agreed. | [Name 3] · A4, A5 |
| Is the 72-hour delay legal? | We do not assume it is. It is a proposed service rule, to be agreed with each bank and its lawyers; the right to revoke an instruction at any time is the first point to check. | [Name 4] · A5 |
| Is the AI a black box? | No. Every pause comes with its reason. On our synthetic data an Isolation Forest ranks operations as well (similar AUC) but cannot say why. | [Name 1] · A1 |
| An AUC of 0.98 is too good to be true? | Yes, on real data it would be. AUC measures ranking, not accuracy, and ours is measured on synthetic data generated with the same logic as the engine: it shows the engine is coherent, not that it is validated. At 0.50 it catches 89% of episodes and 96% of the money; almost every alert is a false alarm, which is why each must be cheap. | [Name 1] · A1 |
| CHF 5 per false alarm on A1, CHF 15 per case on A2: which is it? | Two different things. CHF 5 is a weight for the nuisance of a false alarm, used only to choose the threshold. The cash costs are CHF 0.50 per alert the contact confirms and CHF 15 per case the bank reviews; they give the CHF 7.3 cost to serve. | [Name 1] · A1, A2 |
| What does the 1% fraud rate mean? | Our assumption: 1% of protected clients have at least one material fraud episode a year. It is consistent with Pro Senectute (about 1% a year each for scams and for financial maltreatment among people 55+); we tested 0.5%–2%. | [Name 1] · A1 |
| Your numbers come from synthetic data? | Yes, and we say so. The engine’s parameters come from Swiss public sources (Pro Senectute 2023, cantonal police, fedpol); the simulation uses the same assumptions as the business plan, so it shows consistency, not proof. Real data come from the pilot. | [Name 1] · A1, A8 |
| How does it plug into a bank? | As a white-label module: it reads operations and the bank’s antifraud alerts through an API, and sends notifications through the bank’s app. Card payments stay with the bank’s card antifraud. | [Name 3] · 3 |

### Regulation and ethics
| Question | Short answer | Owner · slide |
|---|---|---|
| Do you need a banking licence? | We do not expect so: Sentinel never receives or holds money, it is software sold to banks. To be confirmed with counsel. | [Name 4] · A5 |
| Banking secrecy and data protection? | The client releases the bank from secrecy towards the contact, in writing at the branch, and asks it to hold flagged operations (nFADP, banking secrecy). The contact sees only the paused operation. | [Name 4] · A5 |
| The contact requests a review, but the client wants the money: who wins? | The client, after the bank’s check. The contact is consulted because the client asked for it; a review request holds the operation, it is not a veto. The bank talks to the client and decides after its own checks; the client can also switch Sentinel off (72 h). | [Name 3] · A4 |
| Who is liable if the contact approves a scam? | The operation is the client’s own instruction; the contact’s “confirm” only releases the hold the client asked for, and the bank keeps its usual duties. Sentinel adds a check, it does not take over the decision. Liability between bank, Sentinel and contact is set by contract, with the contact’s liability limited — to be defined with counsel and the bank’s compliance team (not legal advice). | [Name 4] · A5 |
| Is this paternalistic towards older people? | The client chooses: consent, their own contact and rules, no label, no age test. Switching it off is always possible, with a proposed 72-hour safety delay. | [Name 4] · 3 |

## 4. Rehearsal plan

| When | What | Who |
|---|---|---|
| By 29 November | Deck v1 complete (placeholders filled); first full read-through, timed | All |
| 30 Nov – 6 Dec | Each speaker rehearses their slides alone to the target time; demo script finalised with Utente 3 | All · Utente 3 + 4 |
| 6 December | Code freeze: from here only fixes | Utente 3 |
| 10 December | Backup video recorded; deck exported to PDF and PowerPoint | Utente 3 · Utente 4 |
| 11–14 December | Two timed run-throughs a day; Q&A drill: one person fires questions from §3, the owner answers in under 30 seconds | All |
| 15–16 December | Dress rehearsal on a projector, with the real laptop and adapters | All |
| 17 December | Presentation | All |

At each run-through, note the time per slide and the handovers that drag. Cut words, not slides.

**Checklist for the day:** laptop charged, HDMI and USB-C adapters, deck as PDF on a USB stick, demo tab and video tab open, phone on silent, a printed copy of §3.

## 5. Corrections to document v6 found while building the deck

1. **NetGuardians is now Vyntra** (merger with Intix, June 2025). The deck says “Vyntra (ex-NetGuardians)”.
2. **KBC Guardian Angel** was opened to more than 4 million Belgian clients on 15 September 2026 after a 2,000-user pilot. It is free; KBC’s fraud system (Secure4u) holds suspicious transfers, KBC phones the guardian, who sees only that transfer; according to KBC’s FAQ, without an answer the transfer goes ahead after 72 hours (another KBC page says one week). KBC offers the concept to other institutions on request. Proof of the idea and a risk: both in the deck.
3. **FINMA reference.** The rules on outsourcing (audits, exit plan) are in Circular **2018/3**; Circular 2023/1 covers operational resilience. The deck cites both.
4. **LTV/CAC.** v6 shows ≈15× per client (page 2) and 7.4× per bank (page 3). The deck uses only the per-bank figure, 7.4×.
5. **Team roles.** The deck uses the parts each person actually built (engine, data and economics, interface, business), not the v6 roles (idea, technology, marketing, design). The group to confirm.
6. **Problem figures.** Updated to Pro Senectute 2023 (CHF 675 m a year; CHF 216 m via powers of attorney or account access) and Ticino 2023 (46 scams, more than CHF 2 m, RSI).
7. **Five-year plan (revised 23.11.2026).** v6 reached 32,000 clients in year 5, i.e. all ten banks at 8% at once, while the per-bank model needs two years to reach 8%. Rebuilt in `backend/scripts/piano_finanziario.py` with one set of assumptions: banks live from the year they sign, 4% adoption in year 1 and 8% from year 2, pilot 500 clients with a CHF 10,000 setup fee at list price, revenue on average clients, CHF 7 per client plus CHF 20,000 integration per new bank, v6 fixed costs. Result: 28,800 clients in year 5, revenue CHF 794 k, run-rate CHF 864 k (the SOM, now CHF 0.9 m instead of 1 m), cumulative loss CHF 3.34 m, break-even not before years 7–8. CAC payback is 16 months at maturity but 29 with the ramp.
8. **The ask.** The plan’s cumulative EBITDA loss in months 1–18 is ≈ CHF 770 k (≈ 43 k a month, not 44 k); with no capex it is also the cash need. The v6 use of funds (45/20/25/10% with a 10% reserve) did not match the plan: the reserve is not available. Slide 12 now shows the 18-month spending from the plan (team 50%, product/cloud/service 26%, compliance and legal 12%, sales 12%); ≈ CHF 31 k is left. The ask is tied explicitly to the 500-client pilot.
9. **Pilot terms.** v6 spoke of a “reduced price”; the deck now says a reduced setup fee at the list price per client, consistent with the revenue in year 1.
10. **Market.** The problem figures cover people 55+, the market only 65+ (conservative). “About half” for the SAM rests on the HSLU main-bank study (cantonal 28% + Raiffeisen 25%, all ages).

## 6. Cut list if the time limit is shorter

- **7 minutes:**
  - Market: 25 s, on the three numbers only.
  - Go-to-market: 25 s, on the pilot and the sister banks only.
  - Team: 15 s.
  - Traction: 30 s, on the three numbers only.
  - Competition: 40 s, with only two of the four differences.
- **5 minutes:** also drop the Go-to-market slide (one sentence on slide 6) and shorten the demo to 60 s (stop after *Stop · ask the bank to check*).
