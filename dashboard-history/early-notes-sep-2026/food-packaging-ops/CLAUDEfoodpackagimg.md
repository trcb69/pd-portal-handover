# Operation Food Packaging Division — its place in the order tracker

19 September 2026 · For the CEO, the COO, the division manager and the three team leads.

**One line.** Every order gets one number the moment it is placed, and whoever placed it or is responsible for it can see where it is without asking anyone.

**Where things stand.** The factory side (SmartPack) is designed and approved (design spec Rev 7.3, 17 Sep). This division's side is on the list but not yet designed (LATER.md L27, 18 Sep). Every fact below comes from the team chart or the spec. Anything not in those sources is marked *(assumed)*.

---

## 1. Where the division sits

Every order starts in Team 03 and ends in Team 02. The factory is in the middle only for customised items.

```
Requester ──► Order ──► TEAM 03 ──┬─ customised ─► SmartPack factory makes it ──┐
(salesperson,           creates    │   (production is one of the products)      ├─► TEAM 02 ──► Delivered
 COO, CEO)              the        └─ ex-stock ──► picked from stock ───────────┘    checks, packs,
                        sales order               (Team 01 keeps the stock)           ships
```

| Team | Lead | Owns (from the team chart) |
|---|---|---|
| 01 Inventory & Stock Control | Abdullah | re-orders, 3PL warehouse, stock adjustments, GRN paperwork, draft invoice clearing |
| 02 Order Checking, Packing & Shipment | Saman Kumara | key customer orders, print order arrangement, checking, picklist, package, shipment, GRN goods check |
| 03 Order Creation & Branch Distribution | Senuri Wasana | sales order creation, picklist printing, arranging, stickers, inter-branch requests, IBR |

---

## 2. How it runs today

Three routes. All start in Team 03; two pass through Team 02 before they close. (Team chart, page 6.)

```
FLOW 1  Normal sales order
  Senuri (T03)                 ──► Kavinda (T03)                   ──► Pasindu (T03)
  creates the sales order,         arranges the items                  sticker on every package
  prints the picklist              against the picklist

FLOW 2  Inter-branch consumption & retail chain
  New employee (T03)           ──► Rashaad (T03)                   ──► Saman's team (T02)
  creates the order,               arranges the order                  takes it from there
  same steps as Flow 1

FLOW 3  Inter-branch transfer & sales
  New employee (T03)           ──► Rashaad (T03)   ──► Saman's team (T02) ──► Pasindu (T03)
  creates the IBR document         arranges             checks the order       sticker
```

**Where the order lives today.** In three places that never meet:

1. **WhatsApp / phone** — the request itself. *(assumed: the sources document the WhatsApp order group for factory orders; how ex-stock requests reach Team 03 is not written down.)*
2. **Zoho** — sales order, picklist, package, shipment, invoice, IBR. Zoho holds the documents but no status beyond "confirmed" and "invoiced".
3. **Paper** — the printed picklist and the stickers.

**Pain points, from the sources.**

- The order's start time is recorded nowhere. The WhatsApp receipt date exists in no system, so the 14-day promise is measured from nowhere (brief §5.4, job-file spec §7.3).
- Nobody outside the division can see status without calling someone. Zoho's own dashboard shows everything to everyone, so nobody uses it (brief §1).
- There is no on-time figure for this division. On the factory side the exports give customised on-time ≈ 57 % (Jul–Aug 2026); nothing equivalent exists here.
- The tracker cannot yet read this division's Zoho data: the September export of the Standard Holdings organisation could see only Head Office, 1 of 10 locations (8 picklists exported of about 43,000).

---

## 3. How we plan it

The same portal the factory side already has (spec §7.2), with this division as the first and last stop.

```
Requester          Order number      Triage                    Job
submits in    ──►  back at once ──►  Accept / Reject / Ask ──► created ──┬─ customised ─► SmartPack factory (its own stages) ──┐
the portal         OR-000123         (name + time recorded)              │                                                     ├─►
(name + time)      (time recorded)                                       └─ ex-stock ──► Team 03: sales order + picklist ──────┘
                                                                                           arranges, sticker

──► Team 02 checks and packs ──► Team 02 ships ──► Invoice ──► Completed
    (Zoho package: date)         (Zoho shipment: date)  (Zoho: date)
```

Rules that hold at every step (spec §7.2, brief §2):

- Every step carries a time and a name, taken from the click, never typed.
- An order's lines never change after submit. A change ("customer wants 500 more") is a message on the order, so the record stays honest.
- Nothing is written to Zoho. The tracker only reads.

**Branch and IBR routes (Flows 2 and 3).** Galle, Kandy, Office and Consumption submit through the same portal with order type "internal" (the spec already has that type). Triage accepts; Team 03 creates the sales order or the IBR document in Zoho as now. *(assumed: IBR / transfer orders are not yet in the tracker's Zoho tables, so the IBR step would first show as a manual tick.)*

**What each person sees.**

| Who | Sees |
|---|---|
| Salesperson, COO, CEO (as requesters) | **My orders**: order no, customer, submitted, required date, plain status — Submitted → Accepted → In production → Packed → Shipped → Invoiced → Completed (or Rejected with reason, or Cancelled). Plus the message thread. *(assumed: the words between Accepted and Packed for an ex-stock order, e.g. "Picking", are still to be chosen.)* |
| COO | Everything above, plus the late list: overdue, at risk, blocked (with owner and age), grouped by stage and division (spec §7.5, §7.6). |
| CEO | On-time % (customised and ex-stock separately) and median days per stage from the Zoho dates (spec §7.6). *(assumed: the spec has no CEO role yet; the CEO would get a requester account plus the COO view.)* |
| Team leads | Their own queue: incoming orders, orders waiting on them, done. |

---

## 4. Why this division must be in the tracker

1. **It is the first and the last step of every order.** All three routes start in Team 03; Team 02 packs and ships everything that leaves.
2. **Ex-stock orders never reach a factory.** Without this division they would be invisible to the tracker altogether.
3. **Its Zoho documents give the timestamps.** Sales order, picklist, package, shipment and invoice are detected from Zoho, no typing (spec §8.2). Seven of the eleven order stages are Zoho documents with dates.

---

## 5. Not a burden to maintain — how

- **The teams keep working in Zoho exactly as now.** The tracker reads the sales order, picklist, package, shipment and invoice dates. It never writes to Zoho (spec D15).
- **Getting the data in.** Phase 1: once a working day, IT exports from Zoho and imports into the tracker (spec §14.2). Later: an automatic read-only sync every 15 minutes in working hours (Release 1b).
- **The only new actions.**
  - The requester submits in the portal instead of WhatsApp. WhatsApp stays for conversation.
  - Triage presses Accept, Reject or Ask.
  - Once per order, the Zoho sales order number is typed into the tracker so the two can be matched (spec §7.2.3). *(suggestion, not in the spec: if Team 03 puts the portal order number in the sales order's Reference field, this match can be automatic.)*
- **Nothing is typed twice.** If Zoho has it, the tracker reads it (brief §2.5).
- **Honest limits.** The picklist cannot yet be tied to a sales order from the export (LATER L5). The package gives a date, not a time. The Zoho shipment date may be the day it was typed, not the day goods left; that is what the tracker will show until it is checked.

---

## 6. Open questions and next steps

| # | Question | Needed for |
|---|---|---|
| Q7 | Who triages ex-stock orders? *(suggestion: Team 03 lead, Senuri, who creates the sales orders today)* | Portal go-live |
| Q8 | Is the WhatsApp order group switched off on day 1, or run in parallel? Who enters orders that still arrive by WhatsApp? | Portal go-live |
| L27 | Standard Holdings Zoho access for all 10 locations, so picklists, packages and shipments are complete | Any timestamp from this division |
| new | CEO account: requester plus the COO view? | Portal go-live |
| new | Flow 1: who makes the package and shipment in Zoho? The chart lists both under Team 02, but draws Flow 1 without Team 02. | Correct stage owner |
| new | Does SmartPack wait on the sales order Team 03 creates? 676 factory orders carry "SH Sales Order Ref: to be received". | Cross-company blocker view |

**Next steps.** (1) Answer the six questions above. (2) Complete the Standard Holdings Zoho export. (3) Write this division's part of the spec (LATER L27). (4) Pilot the portal with the three team leads and the COO and CEO accounts.

---

Sources: `/root/Operation Food Packaging Division — Team Structure.pdf` · `/root/Production Dashboard/CLAUDE.md` (brief) · `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` (spec) · `/root/Production Dashboard/LATER.md` · `/root/Production Dashboard/digital-job-file-spec.md`.
