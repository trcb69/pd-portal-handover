# Order Portal + Production Dashboard: earliest joint demo, then updates to the full release

Draft, 21 Oct 2026. Owner direction (21 Oct): goods gatepass moves after 25 Nov; build the earliest demo
of **both** systems together, covering every kind of item from order to dispatch; then add parts in
numbered updates up to the full release. Research: `research/item-flows-research.md`.

## The business in one picture (from the research)

| Kind | SH order lines 19 Sep–17 Oct | Who supplies | Path |
|---|---|---|---|
| Bought-in (import / local, resold) | 5,480 (69%) | Purchasing | order → stock at Kohalwila, or "to purchase" → PO → GRN → stock |
| Customized | 927–1,346 (12–17%) | SPS production units | order → production (job order, units) → SPS internal invoice → SH stock |
| Made-for-stock by SPS (straws, rolls, plain cups) | 624 (8%) | SPS production | order → stock, or a top-up job |

- 317 SH orders mix customized and bought-in lines → the stock-or-production choice is **per line**.
- SPS job orders (8 Oct pull, 8,571): Customized 68 %, Ex Stock 25 %, Internal SH 6 %, MTO 0.4 %.
- All three kinds end in the same dispatch block (SH SO → picklist → package → shipment → invoice →
  gate pass), which is the goods-gatepass project (after 25 Nov).
- Today nothing links an SH order to its SPS job; the portal's `Portal Ref` creates that link.

## Two choices that make the demo early (owner decides)

1. **One website, one app.** Build the order portal **inside the production-dashboard app** (its own repo
   notes already say "Release 1 of it is the order portal"): one login, one admin, one Zoho sync, one
   deploy, one address. The 18 Oct portal spec (separate service, port 4800, own auth) keeps its
   business rules (flow, roles, states, write safety); only the "separate service" part changes.
2. **Demo on a "demo Zoho".** One stand-in Zoho server, loaded with a real snapshot of our SPS/SH data,
   that both parts read and write. The portal "creates" job orders there; the dashboard picks them up
   within a minute; a small demo-control panel moves a job to packed / checked / invoiced to show the
   strip ticking itself. No live Zoho writes, no wait for the Zoho key, safe to show anywhere. Live data
   comes in v0.2.

## The versions

| Version | What you get | Data | Who can open it |
|---|---|---|---|
| **v0.1 Joint demo** | **Portal:** salesperson enters an order (item search, customer, qty, price pre-filled); each line shows a suggested route — *customized → production*, *in stock → pick at Kohalwila*, *bought-in and short → to purchase*; Rizwan's team decides per line; production coordinator accepts, manager approves with a Job No → **job order created**. **Dashboard:** the new job appears in the unit's My jobs; ready-to-run chips (artwork / die cutter / screen-plate from the order); Job card tick; Send next MacPro → PackPro (or the unit's route); demo control moves it packed → checked → invoiced → closed. The stock and to-purchase lines end at "pick at Kohalwila" / "to purchase" with a note. | demo Zoho (real snapshot, dated) | IT runs it privately for the managers and the GM (existing password login) |
| **v0.2 Live + private website** | Reads switch to **live SPS Zoho** (read-only key). The **approval-only website** on standard-holdings.lk: company email (.com/.lk) → code → admin approves the browser → saved, 0-click daily use, with the security fixes. First real deploy. Dashboard extras: attention sort, customer search, drawer with the timeline. | live, read-only | approved people and browsers |
| **v0.3 Write pilot (one division)** | The portal **creates real SPS job orders** for one division (OPD customized) with the full write safety (ledger, reconciliation, restore runbook, kill switch). One live TEST job order first. Price-change flag. ClickUp keeps running alongside. | live read + live write (one division) | pilot users |
| **v0.4 All units** | Every division and unit: routes confirmed with the managers (the Q0–Q14 answers: Stripping, MacPro first, cups, lids, CPU), Send selected, Send back, Unassigned, GM view, wait-limit flags, weekly review report to Mr. Samitha and Mr. Adnaan. | live | all production + sales |
| **v0.5 Stock and purchasing branch** | **Live SH stock** for the decide screen (SH reader: browser now, API later); the *to purchase* list for bought-in and made-for-stock items feeds the reorder screen (inventory system); new-item and new-customer requests; item images. | live SH + SPS | + purchasing / Abdullah |
| **v1.0 Full release** | Hand-over to **goods gatepass** (dispatch after 25 Nov); Stores/Logistics receive step (QR on the job order); "Material issued" from transfer orders; paper checks moved into Zoho fields; SH API instead of the browser reader once granted. | live | everyone |

## v0.1 build steps (working days, Saturday half day; an estimate, not a promise)

| # | Step | Days |
|---|---|---|
| 1 | Root-cause and fix the 17 failing dashboard tests | 1–3 |
| 2 | Demo Zoho: one local server built from the dashboard's test fake + portal write endpoints, loaded from the saved exports; a config switch so the app talks to it (refused in production) | 2–3 |
| 3 | Portal module in the app: new order, per-line suggested route, decide screen, production queue, approve → job order in demo Zoho with Portal Ref | 5–7 |
| 4 | Dashboard My jobs page (list, strip, ready-to-run chips, Job card tick, Send next) + demo-control panel | 3–4 |
| 5 | Units / routes / steps set-up script (MacPro first, Stripping, hide Artwork and Item photo) | 1 |
| 6 | Code + security + database reviews, fixes | 2 |
| 7 | Rehearsal with three sample orders: a customized OPD bag, PSU straws from stock, a bought-in wooden spoon | 0.5 |
| | **Total** | **14.5–20.5** |

**Earliest v0.1 demo: about Mon 9 Nov; likely about Tue 17 Nov** (counting from Thu 22 Oct). Later versions about two weeks apart
each, depending on the owner's answers and the Zoho key; dates for v0.2+ are set after the demo.

## What v0.1 needs from the owner
- Yes to the two choices above.
- Nothing from Zoho (the key is needed for v0.2).
- Which sales person, coordinator and manager names to show on the demo accounts.
