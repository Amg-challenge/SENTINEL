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
| 3 | Solution | [Name 4] | 0:45 | The client chooses, Sentinel pauses, the trusted contact decides; the bank when there is a conflict or no answer. |
| 4 | Market | [Name 2] | 0:40 | Switzerland is the launch pad; the venture size is in DACH. |
| 5 | Product: live demo | [Name 3] (drives and narrates) | 1:30 | See §2. |
| 6 | Business model | [Name 2] | 0:50 | The bank pays CHF 2.50 per client per month for trust, not for the money saved. |
| 7 | Go-to-market | [Name 2] | 0:35 | One pilot bank in Ticino, then the sister banks. |
| 8 | Traction | [Name 1] | 0:40 | The simulated bank confirms the plan: 1.5 alerts, 21% to the bank, CHF 7.2. |
| 9 | Competition | [Name 1] | 0:50 | KBC proved the idea; we make it a product for every bank, with the counter and internal abuse covered. |
| 10 | Team | [Name 1] | 0:25 | Four people, one part of the product each. |
| 11 | Financials | [Name 4] | 0:45 | J-curve; break-even at about 60,000 clients, with DACH. |
| 12 | The ask | [Name 4] | 0:35 | CHF 800,000 pre-seed, 18 months, three milestones. |
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
| 0:30–0:50 | **Contact** | Click **Block** | “Anna gets this message. She calls him, understands it is a scam, and blocks. The counter turns red.” |
| 0:50–1:10 | **Person**, then **Contact** | Click *Request deactivation*; show the alert on Anna’s phone | “The scammers come back and make him switch Sentinel off. It takes 72 hours, and Anna is told at once.” |
| 1:10–1:30 | **Bank** | Switch scenario to *Internal abuse: the contact initiated it* | “And if the person asked to confirm is the one who benefits, Sentinel never asks them: the case goes straight to the bank.” |

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
| What does it cost you per client? | About CHF 7 a year, measured by simulating the whole process: CHF 2 platform, 0.6 notifications, 4.6 bank reviews. Never above about CHF 11 in our stress tests, against a CHF 30 price. | [Name 2] · A2 |
| When do you break even? | At about 60,000 clients (≈ 19 banks), in years 6–7, with Germany and Austria. Each funding round is tied to a milestone. | [Name 4] · 11 |
| What do investors get, and who could buy you? | Exposure to a regulated, sticky B2B niche. Natural acquirers: antifraud and core-banking vendors that want the module for their banks. | [Name 4] · 12 |

### Competition
| Question | Short answer | Owner · slide |
|---|---|---|
| KBC already does this: why would banks not build it? | Large banks can; mid-sized and small banks lack the resources, and they are our market. KBC covers digital transfers only, and if the guardian does not answer the payment goes through. | [Name 1] · 9 |
| What if KBC or Vyntra (ex-NetGuardians) offers it? | KBC says other organisations are interested, so speed matters: we want to be first in Switzerland, with the counter, the safe deposit box and internal abuse covered. We see Vyntra as a partner and channel, not a rival. | [Name 1] · A6 |
| What is your moat? | Honestly none today. Switching costs (integration, contacts and rules already set) and scale (integration and compliance spread over many banks) come with adoption. | [Name 1] · 9 |

### Product and technology
| Question | Short answer | Owner · slide |
|---|---|---|
| Won’t clients be annoyed by alerts? | About 1.5 a year per client in our simulation, and only on unusual operations. The threshold is set by cost; an optional agreed cash limit exists for heavy cash users. | [Name 1] · A2 |
| What if the trusted contact is the abuser? | If they initiated the operation, benefit from it, hold a power of attorney or are co-holder, they are never asked: the bank decides. They never see the balance and cannot move money. | [Name 3] · A4 |
| The client waits 30 minutes at the counter? | Most contacts answer in minutes; after 30 minutes the bank decides, and nothing is approved by default. In the pilot we would also let the branch send a case to the bank’s review at once. | [Name 3] · A4 |
| What if the scammer makes the victim switch Sentinel off? | It takes 72 hours and the contact is told immediately (tested: active at 71 h, off at 72 h). | [Name 3] · A4 |
| Is the AI a black box? | No. Every pause comes with its reason. An Isolation Forest reaches the same accuracy on our data but cannot say why. | [Name 1] · A1 |
| Your numbers come from synthetic data? | Yes, and we say so. The engine is calibrated on Swiss public sources (Pro Senectute 2023, cantonal police, fedpol); real data come from the pilot. | [Name 1] · A1, A8 |
| How does it plug into a bank? | As a white-label module: it reads operations and the bank’s antifraud alerts through an API, and sends notifications through the bank’s app. Card payments stay with the bank’s card antifraud. | [Name 3] · 3 |

### Regulation and ethics
| Question | Short answer | Owner · slide |
|---|---|---|
| Do you need a banking licence? | No: Sentinel never receives or holds money. It is software sold to banks. | [Name 4] · A5 |
| Banking secrecy and data protection? | Notifying a contact is based on the client’s explicit consent, given at the branch (nFADP). The contact sees only the paused operation. | [Name 4] · A5 |
| Who is liable if the contact approves a scam? | The decision stays with the client and the person they chose; Sentinel adds a check, it does not take over the decision. Contract terms with the bank are to be defined with its compliance team (not legal advice). | [Name 4] · A5 |
| Is this paternalistic towards older people? | The client chooses: consent, their own contact and rules, no label, no age test. Switching it off is always possible, with a 72-hour safety delay. | [Name 4] · 3 |

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
2. **KBC Guardian Angel** was extended to over 4 million clients in 2026 after a 2,000-user pilot, and KBC says other organisations are interested. This is in the deck: it is both proof of the idea and a risk.
3. **FINMA reference.** The rules on outsourcing (audits, exit plan) are in Circular **2018/3**; Circular 2023/1 covers operational resilience. The deck cites both.
4. **LTV/CAC.** v6 shows ≈15× per client (page 2) and 7.4× per bank (page 3). The deck uses only the per-bank figure, 7.4×.
5. **Team roles.** The deck uses the parts each person actually built (engine, data and economics, interface, business), not the v6 roles (idea, technology, marketing, design). The group to confirm.
6. **Problem figures.** Updated to Pro Senectute 2023 (CHF 675 m a year; CHF 216 m via powers of attorney or account access) and Ticino 2023 (46 scams, more than CHF 2 m, RSI).

## 6. Cut list if the time limit is shorter

- **7 minutes:**
  - Market: 25 s, on the three numbers only.
  - Go-to-market: 25 s, on the pilot and the sister banks only.
  - Team: 15 s.
  - Traction: 30 s, on the three numbers only.
  - Competition: 40 s, with only two of the four differences.
- **5 minutes:** also drop the Go-to-market slide (one sentence on slide 6) and shorten the demo to 60 s (stop after *Block*).
