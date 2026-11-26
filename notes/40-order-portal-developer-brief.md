# Order portal — developer brief

**Changed 25 Sep 2026:** §5 (credit check) rewritten — data source is now **DECIDED**: Zoho
Inventory, read automatically, no Zoho Books access needed (user decision 3, 25 Sep). Removed the
Books-vs-Inventory conflict and the "present both positions" instruction. Added the field/endpoint/
formula/rate-limit/what-Zoho-already-blocks detail from `analysis/research/zoho-credit-limit.md`.
Two questions remain genuinely open (block-vs-hold; dues definition) — kept as open, not decided
here. §18 Credit controller/Finance question list updated to match (one fewer question). Added a
pointer to the dated master schedule for OP-08/OP-14's calendar dates.

Prepared by Abdul Hadhee | IT Exec | Standard-Holdings, 25 Sep 2026.

**Audience:** the developer building this (an agentic AI coding assistant, supervised by the
user). This is not a new spec — it is everything you need to know before you touch the order
portal (production-dashboard, Release 1), gathered from the approved design, the working notes
that came after it, and the business-plan analysis that touches the same ground. Where a fact
comes from a file, the file is named. Where something is still undecided, it says so and names
who decides it — do not guess and do not build around it silently.

**Authoritative source, always:** `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md`
(Rev 7.3), **plan-critic: PASS**. This brief explains it, adds what has changed or been decided
since (`analysis/research/dashboard-state.md`, `/root/Production Dashboard/CLAUDE.md` §17), and
flags where the two disagree. If this brief and the spec ever conflict on something the spec
already decided, **the spec wins** — come back and fix this brief, don't silently follow it.

**Where things stand today (25 Sep 2026):** Release 0 (foundation: schema, auth, admin, Zoho
import CLI) is built, tested (143 tests green) and reviewed, but **not deployed** —
`analysis/research/dashboard-state.md:2`. Release 1 (the order portal, this brief's subject) is
**not built**. A "Release 1 v2 spec delta" — covering credit check, multi-job orders,
notifications, company+SH location tagging and MFA — is **not yet written**
(`dashboard-state.md:3`). Parts of this brief describe things that need that delta and a
**plan-critic pass** before code, per the house pipeline (`/root/.claude/CLAUDE.md` §2) — each
such item is marked **NEEDS SPEC DELTA** below.

---

## 1. Purpose

Replace three things that are failing today, all doing the same job badly in different ways:
a WhatsApp order group with no record of when an order really started; a paper job file whose
physical location is the only status anyone can check; and a monthly Excel sheet re-typed from
data Zoho already holds (`CLAUDE.md:15-19`). The order portal is the front door: every order —
SmartPack (SPS) customised production, SPS ex-stock, or Standard Holdings (SH) trading orders —
starts here, gets a number immediately, and is visible end to end to the people who placed it,
the people who action it, and management (spec §1, §7.2).

It is not a new system of record for Zoho. Zoho Inventory (two orgs, SPS and SH) stays the
system that actually holds sales orders, stock and invoices. The portal is the front end and the
status tracker; Zoho is never written to (spec Non-goal, §3: "Any write to Zoho. The `outbox`
stays `held`."). Everything the portal shows about Zoho comes from a local read-only mirror
(§6.2), never a live API call.

## 2. Users and roles

From spec §5.1, with the actual people currently assigned (`spec §6.5`, `CLAUDE.md §5.3`,
`BRIEF.md`):

| Role | Who (today) | Scope |
|---|---|---|
| `requester` | Anyone who places orders — SPS sales/order desk staff, SH teams (Rizwan's Food Packaging desk, branches) | New order, their own + their team's orders only, messages, cancel requests. No job internals, no prices, no worker data (spec §5.1) |
| `triage` | **Not named yet — spec Q7.** Suggested in `food-packaging-ops-flow.html:846` and `CLAUDEfoodpackagimg.md:124`: Senuri (SH Team 03 lead, who already creates SH sales orders). For SPS-side triage, no name proposed anywhere read for this brief. | Accept/reject/ask on incoming orders, choose division + manager/coordinator pair, enter-on-behalf for WhatsApp stragglers |
| `coordinator` | Nimesha, Madushi, Nirmani, Umanda (`spec §6.5`) | Create/receive job files, link SO, attachments, cover sheet |
| `manager` | Mubeena, Ranga, Ishan (`spec §6.5`) | Their jobs, receive, ticks, blockers, output, approvals |
| **Credit & Billing Reviewer** | Hazeem, Assistant Manager – Billing, reports to Finance (`CLAUDE.md §17.2` step 3). Finance has not yet named a backup (`CLAUDE.md §17.6`). | Release or hold an order on credit grounds — **see §5, this is not yet in the frozen state machine** |
| `stores` | Ilham (SPS), plus SH-side Saman's team (check/pack) and Pasindu (packaging slip) once SH is in scope | Shipment reference, dispatch qty |
| `invoicing` | Darshani | ITN reference, stage 10/11 |
| `gm`, `coo` | Samitha (SmartPack GM); COO | Read everything, redacted (§5.4 — no worker names/EPF/minutes) |
| `admin` | IT (the user) | Config, users, imports, audit |

**Requesters are internal staff only** in this design (spec Q9: "This spec assumes internal staff
only"). A hidden `customer_portal` flag defaults to `false` so a customer-facing view can be
switched on later without a redesign (`CLAUDE.md §17.2`) — do not build any customer-visible
route now.

**Open naming decisions (block go-live, not code):** who triages SPS orders (spec Q7); who
triages SH orders vs Senuri doing it as today; Finance's backup for Hazeem; who holds
`approver_stores` / `approver_invoicing` (spec Q2).

## 3. Order lifecycle and statuses

**Authoritative state machine:** spec §7.2.0 (states `submitted → questions → accepted →
rejected/cancelled`, plus the `cancel_pending` flag) and §6.4 `order_status` derivation. Build
against this table — it is what Release 1's tests (§13 Release 1 ACs) check.

```
submitted → (triage: ask) → questions → (requester replies) → submitted
submitted / questions → (triage: accept) → accepted → job created
submitted / questions → (triage: reject, reason required) → rejected  [terminal]
submitted / questions → (triage: cancel, only while cancel_pending) → cancelled  [terminal]
```

**What the requester actually sees** (plain-word status, computed server-side, spec §6.4
`order_status`, never a client-side guess):

```
Submitted → Accepted → In production → Packed → Shipped → Invoiced → Completed
                                    (or: Question for you / Rejected / Cancelled)
```

After acceptance, **the job is the only source of truth for status** — reopening a closed/
cancelled job restores the correct status automatically (spec §6.4, Rev 4 B2). This one rule is
tested explicitly (AC1.7, AC1.8) because getting it wrong means a requester sees "Completed" on a
job that was just reopened for a correction.

**Cancel requests** are a flag (`cancel_pending`), not a state, and can be raised before or after
acceptance; before acceptance triage decides, after acceptance the job's manager/coordinator
decides (spec §7.2.0 table, full transition rules with exact 409 conditions).

## 4. Triage

Spec §7.2.2. Three tabs: **Incoming** (state `submitted`, oldest first, cancel-pending on top),
**Questions** (state `questions`), **Enter on behalf** (for orders still arriving by WhatsApp,
spec Q8 — is the WhatsApp group switched off day 1 or run in parallel?).

For each order triage does exactly one of: **Accept** (choose division + manager/coordinator
pair; this creates the job in the same transaction, `order_received_at = submitted_at`,
`entered_*` copied from the order's first line + "(+n more)"), **Reject** (reason code +
required public note), or **Ask** (a public message, order moves to Questions until answered).

**Enter on behalf** (spec §7.2.2, Rev 4 N10): triage types the WhatsApp receipt time (must be in
the past, within 60 days), picks the requester, fills the normal fields. Stored with
`created_via = on_behalf`, audited. This is how the portal absorbs orders that still come in by
WhatsApp during the transition — it is not a separate intake path, it is the same `orders` table
with a flag.

## 5. Credit check — one decision now closed, two still open

**Status: the mechanism is sketched but not yet in the frozen state machine.** Spec §7.2.0 (the
tested, approved state machine) has **no credit-hold state at all** — it only has
submitted/questions/accepted/rejected/cancelled. The credit step described below comes from
`CLAUDE.md §17.2` step 3 and §17.5, written **before** the spec's Rev 7.3 state machine was
finalised, and `dashboard-state.md:3` confirms this delta was never folded in ("credit … NOT
written"). **Do not build the credit check as a bolt-on side effect — it needs its own state (or
gate) added to §7.2.0 by a spec delta, reviewed by `plan-critic`, before any code.**

**What the user has already decided (21 Sep, supersedes an earlier 20-Sep manual-check draft,
`CLAUDE.md §17.2` step 3):**
- Credit check is **automatic at order placement**, not a manual look-up by Hazeem.
- Formula: `over_by = (pending dues + this order's value) − credit limit`. If `over_by > 0`, show
  an error popup quoting the exact LKR amount.
- Draft status enums exist from the 20-Sep design (`CLAUDE.md §17.5`): requester-visible order
  status `Released / Rejected / Held until customer pays / Cancel / Change order`; reviewer-only
  status `Credit Hold / Released / Rejected / On Hold / Sent for review`. **These predate and do
  not match the spec's actual `order_events` enum** (§7.2.0) — reconcile them in the spec delta,
  don't implement both.
- Visibility: "On Hold – Credit Review" is seen only by Senuri, the order's placer, CEO, COO and
  both GMs (`CLAUDE.md §17.2`, "Who sees what").

**DECIDED (user, 25 Sep 2026) — where the credit limit lives.** Zoho Inventory, read
automatically. **No Zoho Books access is needed** — drop the earlier "Hazeem is requesting a
[Books] login" ask (`CLAUDE.md §17.1`) for good; it was already dropped once in the 22-Sep memory
note and that position is now the settled one. This closes the conflict `dashboard-state.md:7` had
flagged between `CLAUDE.md §17.1` and `memory/production-dashboard.md:56`. Full research, every
claim cited to a URL or our own export data: `analysis/research/zoho-credit-limit.md`.

- **Field and endpoint:** `credit_limit` lives on the Zoho **Contact** object — the same record
  Inventory and Books share. `GET /contacts/{contact_id}?organization_id={id}` (Zoho Inventory API
  v1) returns it alongside `outstanding_receivable_amount_bcy` and
  `unused_credits_receivable_amount_bcy` — use the `_bcy` (LKR) versions so the numbers line up
  with order totals in LKR. Confirmed **live in our own SPS org's data today**, not just in Zoho's
  docs: `/root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json` carries a
  nested `contact.credit_limit` field (currently `0`/unset for the one contact visible there — the
  8 key customers' real limits need a one-off `GET /contacts` pull plus someone with Zoho's
  "configure credit limit" permission to set them before go-live; that's a data/config task, not a
  new integration).
- **Formula**, now mapped to the real Zoho fields (same 21-Sep shape, just naming the source):
  `available_credit = credit_limit − (outstanding_receivable_amount_bcy − unused_credits_receivable_amount_bcy)`;
  the order is over the line when `this_order_total > available_credit`.
- **Zoho already blocks/warns on this natively — the portal does not rebuild it.** Settings →
  Preferences → Customers and Vendors offers "Restrict" (hard block) or "Show a warning and allow
  users to proceed" (soft), plus an "include sales orders' amount" checkbox. This fires at Zoho's
  own **API** layer, not just its UI — so Zoho remains the backstop even if the portal's own
  pre-check has a bug. The portal's job is only to read the numbers *before* checkout so the
  customer sees a clean message instead of a raw Zoho error.
- **Rate limit:** 100 req/min/org, uniform across plans — one `GET` per checkout is a rounding
  error against that ceiling. A ~60-second per-customer cache is a cheap optional optimisation, not
  a correctness requirement.
- **Who maintains the limit:** Zoho's own permission model (admin, or a user with "configure credit
  limit") — a Finance/business decision made inside Zoho, not a portal feature. The portal only
  ever **reads** `credit_limit`; it never writes it.

**One thing this decision does not settle — "dues" still needs an answer (see below), but the
research has a recommendation:** use **all unpaid invoices**, not overdue-only. A credit *limit* is
a ceiling on total exposure — a customer who is current on terms but has simply ordered up to
their ceiling should still be stopped, or the limit means nothing. Zoho's own
`outstanding_receivable_amount` is already the all-unpaid figure and needs no extra logic;
`status = overdue` (vs `sent`) is available separately in our own SH export if the business ever
wants the stricter variant.

**Two things genuinely still open — put these to the user, they are not the developer's call:**

| # | Question | Why it matters |
|---|---|---|
| 1 | **Block outright, or hold for release?** `dashboard-state.md:7` records this as still open. `CLAUDE.md`'s earlier draft assumed hold-for-Hazeem, but the 21-Sep "automatic" decision doesn't say what happens to a blocked order — does it just refuse submission, or sit in a queue someone must release? | Changes the state machine shape (a new terminal-ish state vs. a hard 400 at submit) |
| 2 | **What counts as "dues"?** All unpaid invoices, or only overdue ones? (`dashboard-state.md:7`) The research above recommends all-unpaid as the default — but this is still the user's/Finance's call to confirm, not decided by this brief. | Changes the formula and how aggressive the block is — an unpaid-but-not-due invoice is very different from a 90-day-overdue one |

**What this means for the build order:** the order **submission and state machine** (spec
§7.2.0–§7.2.3) can be built and tested now, against the frozen spec, with **no credit gate**.
Wire the credit check in as its own reviewed delta once the two remaining questions above are
answered — don't let them block the whole release.

**Build window (dated master schedule, 25 Sep 2026):** OP-08 (credit-check spec delta + build)
starts **27 Nov 2026**, builds through **4 Dec 2026**, and ships as part of OP-14's single Release-1
go-live: internal IT test **21–26 Jan 2027**, UAT **27 Jan – 10 Feb 2027** (2 weeks — longer than a
typical UAT window because this release includes the automated credit check and touches money),
full release **11 Feb 2027**, live for everyone. Full schedule, every step and its own dates:
`dev/01b-dated-schedule.md`, `dev/dated-schedule.json` (rows `OP-08`, `OP-14`) — do not invent
different dates than what's published there.

## 6. SPS vs SH tagging

**Decision already made, not yet in the schema.** `CLAUDE.md §17.1b`: "SH and SPS are separate
companies. Their records stay in separate reports and are never summed" — this is a business
rule your data model must make structurally hard to violate, not just a reporting convention.
Mirror tables already carry `org` (`SPS`/`SH`) per row (spec D4, §6.2). **The `orders` table does
not yet** — spec §6.3's `orders` table (as frozen in migrations 001–004) has no company/org
column at all. `dashboard-state.md:7` confirms this is part of the un-written delta: "SH vs SPS:
company tag + SH location."

**What to add (needs the spec delta + a new additive migration, not a change to 001–004):**
- `orders.company` (`SPS` / `SH`), required at submission.
- For `company = SH`, an `orders.location` (or a locations table + FK) — SH has 10 locations,
  only 3 currently show up in sales-order data (Head Office 55,874, South Branch 13,873, Central
  Branch 2,235 orders — `zoho-helper-userscript-spec.md:42`), and the `ithelp@` sync login can
  currently see only Head Office (`memory/zoho-inventory-export.md`, "SH login is
  location-restricted") — a real access gap, not just a UI question; flag it, don't route around
  it by hard-coding Head Office.
- Spec D4 already establishes the pattern (`org` on every mirror row) — extend the same
  convention to `orders`, don't invent a second one.

**Reminder for every report or screen you build on top of this:** never sum SPS and SH order
values in one number. This is the single most repeated rule across every source document read for
this brief (`BRIEF.md:8`, `CLAUDE.md §17.1b`, `/root/.claude/CLAUDE.md` global memory note on
"user role").

## 7. Linking to Zoho SOs

**The core problem, with a verified number.** SPS raises its own SO (`JOBORDER-…`, customer
always "Standard Holdings") for a customised order; SH separately raises its own SO for the real
end customer. They are linked today only by a hand-typed SPS field, `CF.SH Sales Order Ref`
(mirror column `cf_sh_sales_order_ref`, spec §6.2). **That field holds a real, usable SH order
number in just 18% of orders** — `CLAUDE.md §17.1b`: "1,472 of 8,325 checked." I re-derived this
independently from the same source data (`so.pkl`, Apr 2024–15 Sep 2026 window, 8,286 orders):
**1,398 of 8,286 orders (16.9%)** match a genuine SH-SO-shaped reference
(`[A-Z]{2,4}SO\d{5,}`, e.g. `HTXSO2602734`); the rest are blank, or one of a handful of
placeholder strings — `"To be Received"` (601+314 case variants), `"For SH Stock"` (462+13),
`"BTN#"` (273, literally the placeholder, no number) — computed from `so.pkl`, column
`CF.SH Sales Order Ref`. Both counts land in the same ~17–18% range; treat "roughly one order in
six or seven" as the reliable figure, not either exact percentage.

**This is also exactly what the spec's own derived field encodes** (§6.4): `sh_blocked` flags any
SO whose ref matches `^to\s+(b|be)?\s*rec…` — 676 SPS headers, verified 2026-09-17 (spec §6.4).
That's the subset stuck on a placeholder; it doesn't count the ones on "For SH Stock" or blank,
so the true un-linked rate is higher than 676/8,325 alone suggests.

**The fix already designed, not yet built:** a **"Portal Order No"** custom field on the SH
sales order (`zoho-helper-userscript-spec.md §4`, admin action **A1**). The portal's OR-number
(`OR-000123`) is written into this field when Senuri saves the Zoho SO through the browser
helper; the portal's read-only sync then finds the SO by that field and links it back
automatically (`zoho-helper-userscript-spec.md §5`). **Today that field is specced as "text, not
mandatory"** (`zoho-helper-userscript-spec.md:46,80`).

**Recommendation for this brief, given the 18% figure above: make it mandatory, not optional.**
An optional field with a 18%-ish fill rate on its predecessor is not a fix, it's the same problem
with a new name. Two ways to enforce it, present both to the user:
1. **Zoho-side (strongest):** mark the "Portal Order No" custom field mandatory in Zoho SH SO
   settings. Blocks Senuri from saving without it. Needs Zoho admin access (the user has this,
   `BRIEF.md`/`user-admin-context` — "the user owns Zoho... admin actions").
2. **Helper-side (weaker, no Zoho admin needed):** the portal helper page/userscript refuses to
   show "ready to fill" until the portal order number is confirmed present in the field before
   Senuri clicks through — but since the helper **never blocks the Zoho Save button itself**
   (`zoho-helper-userscript-spec.md §2` rule 1: "It never writes to Zoho by itself… never clicks
   Save"), this only nags, it doesn't enforce.

**Until SH admin access arrives** (open item, `CLAUDE.md §17.6`), the fallback stands as designed:
Senuri pastes the Zoho SO number onto the portal order, and the portal validates it exists in the
mirror (`zoho-helper-userscript-spec.md §5b`, "way B"). **Never** guess the link from customer +
date + line match ("way C" — explicitly rejected, it links the wrong orders,
`zoho-helper-userscript-spec.md §5b`, `BUILD-ORDER-2026-09-20.md`).

**For the SPS side of linking (spec §7.2.3, §6.3 `job_so_links`):** already fully specced and
frozen — search, or type the pending `JOBORDER-…` number, resolved automatically by the
post-import sweep once that SO appears in a later import (spec §4 "Post-import sweep", §6.3
`job_so_links`). Build this part as written; it needs no new decision.

## 8. Job number rules

**Job numbers are opaque strings. Never parse them.** This is stated as a hard rule in three
independent places (`CLAUDE.md §2` rule 8; `digital-job-file-spec.md:300`; spec `jobs.job_no`
column note). Real examples on file: `OPD6700`, `CPU-155`, `PSU/BTN/989`,
`RWU/IMP2357/QPP/00025/BIO` (`CLAUDE.md:210`). Formats vary by division and by person; do not
build any validation, extraction or auto-numbering logic that assumes a shape.

**Schema (spec §6.3):** `jobs.job_no` is **nullable until set** — a job can exist (created from an
accepted portal order) before anyone has typed a job number, so `to_production` with no job no is
a 400 (spec API table, §10). Setting it later goes through `POST /api/jobs/:id/job-no`
(`{job_no, reason?}`), 409 on a duplicate within `(division_code, job_no)` (NULLs don't collide —
spec §6.3 UNIQUE constraint note). Changing an already-set job number needs a `reason` and writes
an audit row (spec AC1.12).

**Do not conflate job number with the SO number.** They are different identifiers on different
systems (portal job_no vs Zoho `SalesOrder Number`), linked only through `job_so_links` — this
confusion is exactly what produced the join-rate gap in the historical data (`CLAUDE.md §8.1`:
joining on `SalesOrder Number` gets 86% match to the job sheet; joining on `CF.Job No` gets only
65%, because "Screen Printing writes `JN-xxxx` on its sheet while Zoho holds `SHP…`").

## 9. Notifications

**Decided (`CLAUDE.md §17.2` step 2):** the next actor is notified **instantly** on order
creation or any state move — **in-app plus email**, which are the record of the notification.
**WhatsApp is an optional urgent alert only, never the system of record.** One outbox table, one
sender (spec §6.3 `outbox` table already exists, currently `held`/never dispatched by design —
spec D15, table note "Never dispatched").

**Still open, per `dashboard-state.md:7`:**
- A **separate `notifications` table is recommended** but not yet decided — don't reuse `outbox`
  as-is for in-app notifications; `outbox` as specced is a Zoho write-back placeholder, a
  different concern.
- **SMTP account** — not yet provisioned (open item, `dashboard-state.md:7`, spec §7).
- **WhatsApp group** for the urgent-alert channel — Q8 in the spec, unresolved: is the existing
  order WhatsApp group repurposed, or a new one built. **Do not build any WhatsApp-sending
  capability** without checking the standing project rule first: **"never build anti-detection"**
  for WhatsApp automation (`memory/hub-whatsapp-notifications.md` — that project is paused on
  its own open questions and the anti-detection line is explicit and non-negotiable).
- **Backup owner** for the notification pipeline if it fails silently — not yet named.

## 10. Attachments and artwork

Fully specced, build as written (spec §11 Security, §7.2.4 visibility matrix). Key rules, because
getting any one wrong is a security finding, not a style choice:

- **Allow-listed types only, checked by magic bytes:** PDF, PNG, JPEG, WebP, XLSX, DOCX, AI
  (PDF-based), PSD, CDR, ZIP. **SVG, HTML, XML and any script type are never accepted** — SVG
  specifically because it can carry script content (spec §11).
- Only images and PDFs are ever served **inline**; everything else is forced `attachment`.
- 25 MB per file, 20 files per request; requester daily quotas (50 files / 200 MB / 100 messages,
  spec §6.3 `upload_quota`) — 429 past that.
- Random stored names, outside the web root, served only through `/files/:id` after an auth +
  scope check — never a direct static path.
- **`portal_visible` matrix** (spec §7.2.4): a requester-uploaded file, or one posted with a
  **public** message, is visible to the requester; one posted with an **internal** note is not,
  and neither are its files, even to a requester who could otherwise see the order. GM/COO see
  public messages only, never internal notes or their files (Rev 5 N5) — internal notes are free
  text and could name a worker.

## 11. Key-customer call-off orders against buffer stock

This is a **2027 production-plan design, not yet a portal feature** — link it, don't build it
yet, until the plan is agreed. Source: `plans/11-production-plan-2027.md` §3–4.

**The shape of it:** today, finished-goods stock is 0 for every key-customer item, even ones
that sell every month to the same customer — everything is made to order (`BRIEF.md`,
`05-capacity.md` §4). The 2027 plan proposes a **hybrid MTS/MTO split**: keep one-off customised
work as make-to-order, move proven-repeat, high-margin items (six named candidates, e.g. SH-8oz
S/Wall Paper Cup 73.6% margin, Chefs Choice Cling Film 55.5%/52.5% — `11-production-plan-2027.md`
§4 table) onto a rolling **safety-stock buffer** (recommended: 2 weeks of average monthly demand,
sized to each division's own lead time). Once that buffer exists, a **key-customer call-off
order** is a portal order that draws down against it instead of triggering a fresh production
run — this is the mechanism already informally in place for the Keells/Spar cutlery line and the
Oct–Dec 2026 key-customer plan (`11-production-plan-2027.md` §3, "Quarterly / call-off" row), and
`13-business-growth-2027.md` §3 proposes formalising it as a blanket/call-off contract.

**What this means for the portal's data model, when that decision lands:**
- An order needs to be able to say "against buffer stock" as an order type or a flag, distinct
  from a normal MTO customised order or a plain ex-stock order — the current `order_type` enum
  (`customised` / `ex_stock` / `internal`, spec §6.3 `order_type_aliases`) has no such value yet.
- The buffer level itself (Abdullah's role, `BRIEF.md:10`: "SH key-customer buffer stock") lives
  in a **separate, currently-paused stock system project** (`memory/stock-system-key-customers.md`
  — paused 20 Sep, not this developer's scope to build). The order portal's job here is only to
  **link to it**, not to own the buffer-stock logic itself.
- **Do not build this now.** It needs: (a) the safety-stock policy signed off by Samitha and
  Finance (`11-production-plan-2027.md` §4, "not yet agreed"), (b) the paused stock-system
  project to resume, and (c) its own spec delta. Flag it as a **known future order type**, wire
  the `order_type` field to be extensible (an aliased lookup table, as it already is — spec
  §6.3), and stop there.

## 12. Data model notes

**Additive migrations only. Schema is frozen at 001–004.** Spec §6.1: "Forbidden: `DROP TABLE`,
`ALTER TABLE … DROP COLUMN` and any `RENAME`. Allowed: `DROP VIEW|TRIGGER|INDEX IF EXISTS`, but
only when the same file re-creates an object of that name." A test parses every migration and
enforces both rules (spec §6.1) — don't try to slip a rename past it. Every new field this brief
proposes (§6 `orders.company`/`.location`, §7's mandatory-field enforcement, §11's future order
type) is a **new numbered migration**, never a change to 001–004.

**Two clean layers, never mixed (spec §6.2 vs §6.3; `CLAUDE.md §2` rule 3):**
- **Mirror tables** (`zoho_*`) — a read-only copy of Zoho, written only by the shared upsert
  functions (import CLI now, read-only sync in Release 1b). Never write a mirror table from a
  portal route.
- **Core tables** (`orders`, `jobs`, `order_events`, `order_messages`, etc., spec §6.3) — owned by
  the app. The **post-import sweep** (spec §4, run every 30s + at startup) is the only thing that
  touches core tables as a side effect of an import — resolving pending SO links, re-matching
  reference rows, broadcasting changes. Never a mixed write inside a single route handler unless
  it is explicitly one of the documented sweep steps.

**Every write is append-only where it matters, and the spec marks which ones:** `orders`,
`order_lines`, `order_events`, `order_messages`, `manual_stage_events`, `stage_overrides`,
`handovers`, `form_submissions` and several others are marked **(A)** — a trigger aborts any
UPDATE or DELETE (spec §6.3). `order_lines` specifically: "written once at submit" — an order's
fields and lines never change after submit; a quantity change is a **message**, applied by the
coordinator on the job, never an edit to the order record (spec §7.2.1, "Updates are not edits").

**Money is LKR cents; times are UTC ISO ending `Z`; Colombo-calendar dates come only from
`shared/time.js`** (spec §6, `colomboDate()`, fixed +05:30, no DST) — never derive "today" from
the VPS clock directly.

## 13. Security

Spec §11, plus §5.2–5.3 for auth specifics. Build to these exactly; they are tested (Release 0
AC0.4–0.6, Release 1 AC1.14, AC1.30) and reviewed by `security-auditor` before Release 1 ships
(spec §11: "security-auditor reviews Release 0, Release 1 (the order portal), Release 5").

- **Auth:** desk sessions via scrypt (N=2^15, r=8, p=1, `maxmem: 64 MiB`), 256-bit session id
  stored only as its hash, `HttpOnly; Secure; SameSite=Strict` cookie, 12h idle / 7-day absolute
  expiry, every session revoked on role change/deactivation/password reset (spec §5.2).
- **Rate limits:** 10 login failures per username / 15 min, 100 per IP / 15 min → 429 (the office
  sits behind one NAT address, spec finding 22). Requester upload quotas separately (§10 above).
- **CSRF:** every non-GET needs `Origin` equal to the configured origin; a **missing** `Origin` is
  also rejected (spec §5.2, finding 22 — a common miss: don't allow no-Origin through).
- **Roles checked server-side on every route**, not just hidden in the UI (spec §10, "Scope:
  checked on the server for every route"). A user whose only role is `requester` gets 403 on
  every non-portal route — this is a specific tested case (AC1.2), not an assumption.
- **Audit:** `audit_log` is append-only (spec §6.3); every job-no change, override, attachment
  visibility flip and admin action writes to it.
- **Redaction for GM/COO** (spec §5.4): worker identity replaced with "operator" everywhere,
  `payload_json` never sent, minutes only as division×process×week aggregates with ≥2 distinct
  workers or "—". This applies to whatever GM/COO-facing order-portal reporting you build too, not
  just the floor-forms features it was written for.

## 14. Non-functional

- **Desk vs floor:** desk users (coordinators, managers, triage) use laptops/desktops (spec D5);
  production workers use a shared tablet per department (D6) — but that's Release 5, not this
  release. **The order portal itself is a desk/office tool in Release 1** — requesters, triage,
  coordinators all work from a desk. Design for that, not for a phone-first layout, unless the
  user says otherwise; nothing read for this brief specifies mobile use for the portal
  specifically.
- **Sinhala / Tamil:** **not mentioned anywhere** in the spec, `CLAUDE.md`, or any research file
  read for this brief. This is a genuinely open question, not a documented "later" — ask the user
  directly whether English-only is acceptable for Release 1, rather than assuming either way.
- **Offline tolerance:** explicitly out of scope for the whole system — "Offline tablets" is a
  spec Non-goal (§3). The order portal (desk-based) has no offline requirement at all; don't add
  one.
- **Performance target that does apply to portal list views:** `GET /api/jobs` over 5,000 jobs
  answers in under 300ms median, no single sync DB call blocks the event loop over 100ms (spec
  §8.2, AC1.28) — the same query-builder discipline (keyset-paged chunks of ≤500) should be
  applied to any order-list endpoint you add, even though the AC as written is about jobs.

## 15. Acceptance criteria per feature

Use spec §13 Release 1 (AC1.1–AC1.31) as the actual, already-written acceptance criteria — don't
re-derive them. Highlights most relevant to what this brief covers, verbatim from the spec:

- **Order submission (AC1.1):** `submitted_at` is server time; a client-sent time is ignored.
- **Scope isolation (AC1.2):** a requester sees only their own + their team's orders; a
  requester-only user gets 403 on every non-portal route; no job internals/prices/worker
  fields/internal messages leak — checked by a key/value scan on seeded data, not just a
  route-by-route eyeball.
- **Immutability (AC1.3):** order fields/lines can't change after submit — no such route exists,
  and the DB triggers abort it even if one did.
- **Accept race safety (AC1.4):** two simultaneous accepts on one order → exactly one 200, one
  409, exactly one job. Accept while `cancel_pending` → 409.
- **Visibility matrix (AC1.6):** every cell of the §7.2.4 table checked in both directions.
- **Plain status correctness (AC1.7):** a file sent back to the coordinator still shows "In
  production" to the requester — status never regresses on an internal handover.
- **Cancel lifecycle (AC1.8):** covers before/after acceptance, decline, reopen — reopening after
  a cancelled job clears the banner and allows a fresh cancel request.
- **SO link correctness (AC1.10, AC1.11, AC1.20):** unlink → stage 4 not done immediately;
  re-link → done again; pending JOBORDER resolves on the next import within poll interval + 5s;
  `JOBORDER-08338 - C` and `joborder-08338` both match `JOBORDER-08338`, `JOBORDER-083381` does
  not — an SH row with the same SO number **never** ticks an SPS job (org isolation, tested).
- **Job number (AC1.12):** "No SO" requires all four `entered_*` fields; duplicate
  `(division, job_no)` → 409 both at creation and via `POST /job-no`; opaque strings like
  `RWU/IMP2357/QPP/00025/BIO` stored exactly as typed.
- **Uploads (AC1.14, AC1.30):** 26MB → 413; renamed `.exe` → 415; an SVG or HTML file (even
  renamed to `.png`) → 415; 51st file or 101st message in a Colombo day → 429.
- **End-to-end flow (AC1.27):** requester submits → triage accepts → coordinator sets job no,
  links pending SO, attaches docs, sends to production → import+sweep resolve the SO → requester
  sees "In production," live (SSE) — this is the one Playwright test that proves the whole chain
  works together, run it early as a smoke test, not last.

**For anything this brief adds that isn't in spec §13 yet** (credit check, company/location
tagging, mandatory Portal Order No, buffer-stock call-off orders): **write its acceptance
criteria as part of the spec delta**, following the same style (a numbered AC, a one-line
criterion, a check type T/E/C) — don't invent ad hoc criteria at implementation time.

## 16. What NOT to build

**Zoho Inventory already does these — don't rebuild them:**
- Low-stock alerts / reorder points — native (`research/market-and-zoho.md`, "Reorder point /
  low-stock alerts: native").
- Composite items / kit bundling — native, this is what BOMs/recipes already use.
- Basic reports, pivot/summary views, KPI widgets, workflow rules, Deluge functions, webhooks —
  all native to Zoho Inventory (`market-and-zoho.md` capability table).
- **Sales order creation itself** — the portal never writes to Zoho (spec Non-goal, §3, D15). The
  helper fills a form on Senuri's screen; Senuri clicks Save in Zoho
  (`zoho-helper-userscript-spec.md`). Do not build a "create SO" API call anywhere.

**Explicitly out of scope for this release, per the spec's own Non-goals (§3):**
- Any write to Zoho (the `outbox` stays `held`).
- Webhooks, the SH mirror as a webhook source, cross-org stages beyond a manual tick.
- Digital QMS forms.
- Individual staff productivity in GM/COO responses.
- Parsing job numbers (§8 above).
- Writing to Employee Master.
- Offline tablets, native apps.
- **True manufacturing work orders / MRP** — Zoho's own documentation states it doesn't support
  manufacturing modules (`market-and-zoho.md`, "Zoho Inventory's own knowledge base states
  explicitly: 'As of now, we are yet to support manufacturing modules.'"). The production
  dashboard's job/stage tracking is the custom build that fills this gap — that's already this
  project, don't duplicate it inside the order portal too.

## 17. Pitfalls (known traps, verified against real data)

- **`SubTotal`/`Total` repeat the order total on every line in these Zoho exports** — never sum
  them across lines; only `Item Total` (or `Amount`) is additive (`01-business-history.md`,
  verified on a 6-line order). This applies to any order-value display you build from SO line
  data, including inside the portal.
- **`Customer Name` on SPS sales orders is unusable** — 10,440 of 10,442 rows read "Standard
  Holdings (Pvt) Ltd" (`CLAUDE.md §8.1`). The real customer is `CF.Order Received from`. About
  **29% of key-customer order lines are logged under "Standard Holdings" instead of the real
  customer** (`BRIEF.md:48`) — this is exactly the mis-tagging the order portal is designed to
  fix by capturing the real customer at order entry, not after the fact.
- **Division values need alias mapping, don't hard-code them.** 12 real division values exist in
  Zoho headers with wildly different labels than the internal short codes (spec §6.5 seed table,
  e.g. `Offset Printing Division (OPD)` → `OPD`). Unmapped values are **never skipped** — they're
  stored raw and flagged in Admin (spec §8.1) — don't write validation that rejects an unknown
  division value.
- **`so_key` matching is a specific regex, not a naive string compare** — trim, uppercase, match
  `^([A-Z]+-\d+)(\s*-.*)?$`, group 1 is the key (spec §6.2). `JOBORDER-08338 - C` and
  `joborder-08338` are the same SO; `JOBORDER-083381` is a different one. Get this wrong and
  bundle-to-SO matching silently drops or misattributes records.
- **A blank status cell does not mean "not done."** The Sep-2026 job sheet has 47 blank status
  cells in one register alone, plus inconsistent free text ("Cancle item", "SH has stock - Hold
  Packing") — `CLAUDE.md §8.2`. Don't treat missing data as a negative signal without checking
  other columns (qty done, hourly checkpoints) first, exactly as `jobs_in_production.py` already
  does for the existing job-sheet ingestion.
- **Capture-time discipline matters more than import order** (spec §6.2, "Capture time"): every
  import file needs a `captured_at`, and an older capture must never overwrite a newer one,
  regardless of when the file happened to be imported. If you add any new mirror-adjacent data
  source (e.g. for the credit check, once §5 is resolved), carry this same discipline — don't
  build a second, simpler freshness rule.

## 18. Ingredients list and question pack per role

Use this section as-is to prepare for each conversation — one ready-to-ask block per person, each
question tied to the part of this brief it unblocks.

### Sales coordinators / Senuri (SH Team 03, order creation)
1. Are you willing to triage SH-side orders in the new portal, as suggested in the earlier
   food-packaging-ops notes (§2)? If not, who should?
2. When the "Portal Order No" field is made mandatory on the SH sales order (§7), does that
   change anything about how you currently save an order — any case where you genuinely don't
   have a portal order number yet (e.g. a walk-in, a phone order taken before the portal is used)?
3. For the helper page/userscript (`zoho-helper-userscript-spec.md`): which of Zoho's dropdown
   values (Business Unit, Order Pick Type, Invoice Type, Delivery method — §4 of that spec) do you
   actually use day to day, so the helper's field list can be trimmed to what's real?

### Triage owner (name not yet decided — put to Samitha/GM or whoever names the role)
1. Who is triage for SPS orders, and separately, who is triage for SH orders (§2, spec Q7)?
2. Is the WhatsApp order group switched off on day one, or run in parallel for a transition period
   — and if parallel, for how long (spec Q8)?
3. Who enters orders that still arrive by WhatsApp during that transition — is it triage itself,
   via "enter on behalf" (§4), or someone else?

### Credit controller / Finance (Hazeem's function, §5)
**Decided, no need to ask:** the credit limit is read automatically from Zoho Inventory — drop the
earlier Books-access request entirely (§5, DECIDED 25 Sep 2026).
1. Block the order outright over the credit limit, or hold it for a named person to release?
2. Do "pending dues" mean every unpaid invoice, or only the overdue ones? (§5's research recommends
   all-unpaid as the default — confirm or override it.)
3. Who is Hazeem's backup, so the credit-review step has continuity?
4. Should this brief's §5 items go to you as one short standalone memo before the wider planning
   meeting, given how much of the order flow depends on the answer?

### GM (Samitha)
1. Sign-off needed on the safety-stock / MTS buffer policy (§11) before any call-off order type
   is added to the portal — is this ready to approve, or does it need more numbers first?
2. Confirm the manager/coordinator pairs and which divisions still need one assigned (spec §6.5:
   PCU, PCLU, DPU, PPU, CWU have no pair yet).
3. Any objection to English-only for Release 1 (§14), or should Sinhala/Tamil support be scoped
   in now rather than added later?

### COO
1. Confirm the redaction rules in §13 match what you and the CEO actually need to see — is
   division×process×week aggregation (with the 2-worker minimum) enough, or is there a
   legitimate business need for anything more granular that the current design deliberately
   withholds?
2. Any objection to the block-vs-hold decision in §5 being made by Finance/Hazeem alone, or does
   it need COO sign-off given it can stop a customer's order?

---

## Files this brief draws on (read these, don't re-derive them)

- `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` (Rev 7.3) — the
  frozen, approved spec. Sections cited throughout: §1, §3, §5, §6, §7.2, §8, §9, §10, §11, §13,
  §17.
- `/root/Production Dashboard/CLAUDE.md` §17 — the order-to-shipment concept, credit check
  mechanism, Zoho form helper, people, flowcharts (A–E). Written 19–20 Sep, **partly superseded**
  by the frozen spec's state machine — see §5's warning above before trusting its status enums.
- `/root/Production Dashboard/zoho-helper-userscript-spec.md` — the Portal Order No field,
  linking mechanism, Senuri's workflow. **Draft, not approved, no code yet.**
- `/root/Project Management/reports/2026-09-25-sps-business-plan/analysis/research/dashboard-state.md`
  — current build status and the open items (notifications table, company+SH location) as of 25
  Sep. Its credit/Books conflict note predates this brief's §5 update — the data-source question is
  now DECIDED here (25 Sep 2026); `dashboard-state.md` itself is not this brief's file to edit.
- `/root/.claude/projects/-root/memory/production-dashboard.md` — the 22-Sep decision dropping the
  Zoho Books / EPF asks.
- `/root/.claude/projects/-root/memory/zoho-inventory-export.md` — the SH location-access gap
  referenced in §6.
- `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/11-production-plan-2027.md`
  §3–4 — the MTS/buffer-stock proposal referenced in §11.
- `/root/Project Management/reports/2026-09-25-sps-business-plan/analysis/research/market-and-zoho.md`
  — what Zoho Inventory/Analytics natively covers, referenced in §16.
- `/root/Project Management/reports/2026-09-25-sps-business-plan/analysis/research/zoho-credit-limit.md`
  — new 25 Sep 2026, the full credit-limit field/endpoint/formula/rate-limit research behind §5's
  DECIDED data-source note.
- `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/01b-dated-schedule.md` and
  `dev/dated-schedule.json` — new 25 Sep 2026, the dated master schedule §5 cites for OP-08/OP-14's
  calendar dates.
- `so.pkl` (`/tmp/claude-0/-root/6c14ef71-1188-411a-9073-1b873a8ccc0f/scratchpad/so.pkl`) — the
  18%/16.9% SH-SO-ref fill-rate figure in §7 was independently recomputed from this file, column
  `CF.SH Sales Order Ref`, Apr 2024–15 Sep 2026 window (8,286 orders).
