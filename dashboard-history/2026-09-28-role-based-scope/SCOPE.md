# "Your part of Zoho": the scope of the three systems

Draft, 28 Sep 2026, for review. It covers the order portal, the production dashboard and the inventory system for Standard Holdings (SH) and SmartPack (SPS).
Evidence: `evidence/A-production-dashboard.md`, `evidence/B-portal-inventory-combined.md` and `evidence/C-zoho-record-gaps.md`. User decisions are in `/root/Project Management/reports/2026-09-27-sps-sh-inventory-analysis/work/DECISIONS.md`.

---

## 1. The problem, in one paragraph

Zoho is one central system that shows every module, field and option to everyone. Most of the people who have to keep Zoho up to date (coordinators, stores, sales staff, floor supervisors) are not computer people. They see screens built for accountants and administrators, so steps get skipped, records are left open and documents stay half-done. The data proves it:

| What is left undone in Zoho | Number | Source |
|---|---|---|
| SH sales orders never marked "delivered" (stuck at "shipped") | **11,556 of 15,900** confirmed SOs | C:15-17 |
| SH sales orders left as drafts | 133 (22 in 2024, 34 in 2025, 77 in 2026, rising) | C:25 |
| Cancelled or short-closed order lines with a reason recorded | **0 of 2,213** | C:37 |
| SPS orders closed short (the rest cancelled, not delivered) | 15.6% → 22.9% → 38.9% of closed SOs (2024 → 2026) | C:65 |
| Transfers stuck between warehouses | 142 not yet moved (68 waiting approval, 50 in transit, 24 approved; 34.6 days on average) | C:85 |
| SPS raw materials recorded in the wrong warehouse | 266 of 423 (62.9%) | C:106 |
| SH "delivery date" filled after the fact, so it is useless as a promise date | 0 of 24,143 orders packed after it | C:136-140 |
| SH items with a reorder level (Zoho's own low-stock alert) | 116 of 11,297 | C:189 |
| SPS items with no matching SH item | 156 items, 5.9M units | C (item master) |

Most of these are not system faults. **They are steps a person was meant to do and didn't, because the step was buried in a screen full of things that were not theirs.**

## 2. What we are building

**One idea across three systems: each person opens a simple screen that shows only their part of the work. The screen tells them what is waiting for them and what they missed. Managers see the same thing for their whole department.** Zoho stays the official record: all data lives there, and all accounting stays there. Our screens sit on top of it.

```
                 ZOHO (SH org + SPS org) — the official record, unchanged
                        ▲ people still save in Zoho (helped, prefilled)
                        │ we only READ (live mirror)
   ┌────────────────────┼─────────────────────────────────────────────┐
   │                SHARED CORE: one login · one set of roles · one job record ·
   │                one "missing steps" engine · one audit trail
   ├──────────────┬──────────────────────────┬─────────────────────────┤
   │ ORDER PORTAL │  PRODUCTION DASHBOARD    │  INVENTORY SYSTEM        │
   │ requester    │  coordinator · manager   │  storekeeper (SPS, raw   │
   │ triage       │  stores (Ilham) ·        │  materials only)         │
   │ credit review│  invoicing (Darshani) ·  │  Operations–Packaging    │
   │              │  floor (later)           │  (SH, non-chemical items)│
   ├──────────────┴──────────────────────────┴─────────────────────────┤
   │  MANAGERS: their department(s) only · GM / COO: every department, summarised │
   └────────────────────────────────────────────────────────────────────┘
```

### 2.1 Five rules every screen follows

1. **Only your part.** Each login sees only its own orders, jobs, divisions or items. This is enforced by the system (the data a login may read), not only by what the menus show.
2. **Your list, not a module.** A person's home screen is a to-do list ("waiting for you", "you missed", "done this week"), not a menu of Zoho modules.
3. **A missed step shows up by itself.** Every process has an expected set of Zoho records. When one is missing past its due point, the person who owns that step sees it on their list. If it stays open, it moves to their manager. Nobody has to remember to check.
4. **Plain words, few fields.** Show the three to six things that matter, in the words the team uses. Everything else stays in Zoho for the few people who need it.
5. **Zoho is still the record.** We read Zoho. People still save in Zoho, and we make that easier: a page that prefills or copies the values, so they don't have to hunt for fields. The one planned write-back (the reorder level) stays switched off until it is explicitly approved.

### 2.2 Who sees what (logins)

| Login | Sees only | Their "missed" list catches, for example |
|---|---|---|
| **Requester** (portal) | their own and their team's orders, in plain status | order not confirmed, question unanswered |
| **Triage** (portal) | the incoming order queue | order waiting past its due point, no Zoho SO created for an accepted order |
| **Credit reviewer** (portal) | orders held for credit | hold not decided |
| **Coordinator** (dashboard) | their own job files | SO not linked, artwork or job card missing, job not closed after it was invoiced |
| **Manager** (dashboard) | jobs in **their** divisions | blocked jobs, past-due jobs, produced but not shipped, and anything their team missed that has not been fixed |
| **Stores – Ilham** (dashboard) | jobs waiting on stores | shipment not recorded, delivery not confirmed (the 11,556 problem) |
| **Invoicing – Darshani** (dashboard) | jobs waiting on invoicing | invoice not raised after shipment |
| **Storekeeper** (inventory, SPS) | **raw materials only** | goods received but not entered, material in the wrong warehouse (62.9% today), transfer not received |
| **Operations–Packaging** (inventory, SH) | non-chemical items SH buys and sells, including raw materials sold to SPS | reorder point breached, cancellation with no reason, draft SO left open |
| **GM / COO** | every department, as counts and exceptions (no prices on screens they don't need) | departments with the most missed steps |
| **Admin (IT)** | configuration and audit | sync failures, data out of date |

Chemicals (the SD, Specialities Division) are **outside** this scope for now. The item list for the two inventory logins has already been split: `…/2026-09-27-sps-sh-inventory-analysis/item-classification/SH-Item-Classification.xlsx`.

### 2.3 The "missing steps" engine (the heart of the idea)

One shared list of expected steps per process. For each step it records who owns it, how the system can tell it is done in Zoho, and when it becomes overdue:

- **Order → job → dispatch → invoice.** Portal order accepted → Zoho SO exists → job file opened → bundle → pick list → package → shipment → **delivered** → invoice → job closed. The dashboard already detects 7 of its 11 stages from Zoho records (A: §Missed-step).
- **Stock.** Purchase received → stock in the right warehouse → transfer sent → **transfer received** → adjustment has a reason.
- **Closing.** Short-closed or cancelled line → **reason recorded**. Draft SO → confirmed or deleted.

Each missing step appears once: on the owner's list first, then on their manager's list after a set number of days. Each list is capped at a short number of items (the plan's rule is 15 or fewer per list) so people aren't flooded. **Old backlog is cleaned up once, in a trial run with the user's go-ahead, before the lists go live.** Otherwise day one would bring thousands of alerts, for example the ~1,083 SPS order lines open for more than a year.

## 3. Why this is the best option for us

| Option | What it means | Why not / why |
|---|---|---|
| A. Train everyone on full Zoho | Keep Zoho as it is and run more training | Zoho's own role permissions can hide modules, but they can't turn a module into a personal to-do list. They can't show one job across two Zoho organisations (SH and SPS). They can't chase a missing step. Our numbers show training alone has not worked. |
| B. Replace Zoho with our own system | Build a full ERP (enterprise resource planning system) | Accounting, tax and invoicing live in Zoho, and replacing them is years of work and high risk. It also moves the documentation problem instead of fixing it. |
| **C. Our screens on top of Zoho (this scope)** | Zoho stays the record; each person gets a simple, role-limited screen that catches their missed steps | It goes straight at the real cause (the steps people miss), uses what we already have (Zoho data, the dashboard's Release 0, the plans), needs no data migration, and can be measured against the baseline in §1. |

We already have the parts: the dashboard's 12 roles and 11-stage checklist (A), the portal and inventory role plans (B), and the Zoho data pulls and analysis from this week.

## 4. What changes in the current plans

1. **Real per-division containment in the dashboard.** Today a manager or coordinator is not technically limited to their own divisions; "PSU first" is only a rollout choice (A:Gaps 1). This needs a spec change before Release 1 goes live.
2. **Stores and invoicing:** their default screen is only the jobs waiting on them. Search across all jobs stays available as an explicit action (A:Gaps 2).
3. **Storekeeper screen shows raw materials only.** The inventory screen currently shows all 79 items (11 finished goods and 68 raw materials) (B §6).
4. **A build slot for the Operations–Packaging (SH) login.** Three phase-1 requirements are tagged to it, but it has no step yet (B §6). Default order stays **SPS first, SH after SPS phase 1 sign-off** unless you decide otherwise.
5. **A home for GM, production managers and the RM stock manager in the inventory system.** They fit neither login today (B §6). Proposal: managers get read-only department views; the RM stock manager is a storekeeper-side role.
6. **One GM view, not three.** Today the three systems could each show the GM different numbers (B §6). The GM's view reads from the shared core.
7. **Per-person "you missed" lists.** Today missed work shows only in shared exception lists (B §4). The engine in §2.3 adds the per-person list and the move to the manager.
8. **Shared login and roles** across the three systems, so a person who works in more than one (for example a manager) signs in once.

## 5. How we will know it works (targets, measured monthly from Zoho)

| Measure | Today | Target after 3 months live (proposal) |
|---|---|---|
| Orders stuck at "shipped" (new ones, per month) | 11,556 backlog | backlog cleaned up once; new cases closed within 7 days |
| Cancellations with a reason | 0% | 90% or more |
| Draft SOs older than 14 days | 133 in total, rising | close to 0 |
| Transfers not received after 7 days | 142 | fewer than 10 |
| Raw materials in the wrong warehouse | 62.9% | under 10% |
| Items in scope with a reorder level | 116 of 11,297 (SH) | every item on the two inventory logins' lists |

## 6. Phasing (keeps the dates already set)

1. **Now – Dec 2026: production dashboard.** PSU pilot 8 Dec, Screen Printing 21 Dec, GM tile 22 Dec. Add division containment (§4.1) and the job-flow part of the missing-steps engine.
2. **Jan 2027: inventory, SPS phase 1** (storekeeper login, raw materials only, go-live 5 Jan). Stock steps in the engine.
3. **Feb 2027: order portal** (15 Feb). Order steps in the engine, plus the Zoho prefill helper page.
4. **After SPS phase 1 sign-off: Operations–Packaging (SH) login**, the SH customer-facing requirements, and cross-company warnings (SPS short → SH customer).
5. **Before each go-live:** a one-time trial cleanup of that area's backlog, with your go-ahead.

## 7. Decisions you need to make

1. Who is **triage**, and who are the **approvers** (stores and invoicing)? These are still open.
2. **Per-division containment:** confirm that managers and coordinators are strictly limited to their divisions.
3. **When the SH Operations–Packaging login is built:** after SPS phase 1 (the default) or earlier.
4. **Backlog cleanup:** approve a trial on one area first (for example, 100 of the SOs stuck at "shipped" at one branch).
5. **The targets in §5:** accept, or set your own.

Abdul Hadhee | IT Exec | Standard-Holdings
