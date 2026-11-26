# Order portal — the finished product

**Changed 25 Sep 2026:** credit-limit data source is now DECIDED (Zoho Inventory, no Books) — §7's
success-criteria row updated from "three open questions" to "two open questions."

What the order portal must be able to do once every step (OP-01…OP-14, plus OP-15/OP-16 when
unblocked) is built. Written by Abdul Hadhee | IT Exec | Standard-Holdings, 25 Sep 2026. Sources
cited throughout; see `PROJECT-MEMORY.md` for the full file map.

This describes the **target**, not today's state — see `PROJECT-MEMORY.md` §2 for what's actually
built now (nothing of Release 1 yet).

---

## 1. A day in the life, by role

### Requester (SPS order desk, SH Rizwan's Food Packaging team, branches)
Logs in on a desk PC. Opens "New order," picks the customer (from a real picker, not free text —
OP-11), the company (SPS or SH — OP-07), and for SH, the location. Types required date, item
lines, notes, attaches artwork/spec files. Submits — gets an order number (`OR-000123`)
immediately, with the server's own submit time, not whatever the browser clock says (AC1.1). Sees
"My orders" and "Team orders" with a plain-word status per order: `Submitted → Accepted → In
production → Packed → Shipped → Invoiced → Completed` (or `Question for you` / `Rejected` /
`Cancelled`) — never a raw database state (spec §6.4). Can message the order thread, and can raise
a cancel request at any point before completion. Sees no job internals, no prices, no worker names
(spec §5.1, tested AC1.2).

### Triage (name TBD — SPS side unnamed, SH suggested: Senuri)
Opens three tabs: **Incoming** (oldest first, cancel-pending on top), **Questions**, **Enter on
behalf** (for stragglers still arriving by WhatsApp during the transition). For each order:
**Accept** (picks division + manager/coordinator pair; a job is created in the same transaction),
**Reject** (a reason code plus a required public note), or **Ask** (a public question, order moves
to Questions until the requester replies). Uses Enter on behalf to log an order that came in by
WhatsApp, typing the actual receipt time — audited, indistinguishable to the requester from a
normal submission except in the audit trail.

### Coordinator (Nimesha, Madushi, Nirmani, Umanda)
Picks up an accepted job. Sets the job number (opaque, typed exactly, never validated against a
shape). Searches for or types the pending Zoho SO number to link it — the sweep resolves a
not-yet-imported SO automatically once it appears (within poll interval + 5s). Attaches production
documents. Sends the job to production. Sees the order thread and can post internal notes (never
visible to the requester or to GM/COO).

### Manager (Mubeena, Ranga, Ishan)
Sees jobs assigned to them across every division they run (Ishan: four divisions, one dashboard).
This is Release 2's own workspace, but the order portal is what feeds it a job the moment triage
accepts an order — the manager's first sight of a job is a portal-created one, not a paper file.

### Credit & Billing Reviewer (Hazeem's function) — once OP-08 ships
On any order whose `pending dues + this order's value` exceeds the customer's credit limit, sees
an "On Hold – Credit Review" order and either releases or rejects it, per whichever block-vs-hold
decision Finance and the COO settle on. Visible only to Senuri, the order's placer, CEO, COO and
both GMs — nobody else, not even other triage staff.

### Stores (Ilham, SPS) / Invoicing (Darshani)
Own the two closing checklist stages: shipment reference and ITN reference. Each fills one
reference number on the order/job when their step happens. Release 3 builds their own workspace;
the order portal is what makes their input show up as the requester's "Shipped"/"Invoiced" status
change, live.

### GM (Samitha) / COO
Read everything, redacted: worker identity replaced with "operator" everywhere, no `payload_json`,
minutes only as division×process×week aggregates with ≥2 distinct workers or "—" (spec §5.4). See
public messages only — never internal notes, never the files attached to them (Rev 5 N5). Never
see SPS and SH order values summed into one number, anywhere.

### Admin (the user)
Configures divisions, manager/coordinator pairs, reason codes, order-type aliases, calendar and
holidays. Manages users and their roles. Runs and monitors Zoho imports/sync. Reads the audit log.
Sees the "unverified" flag on the 7 unconfirmed SH locations until sync access covers all 10.

---

## 2. Screens

- **New order** (requester) — customer/company/location pickers backed by real Zoho-sourced
  lookup data (not free text, OP-11); item lines; attachments; required date.
- **My orders / Team orders** (requester) — list with plain-word status, filterable.
- **Order thread** (requester + staff) — messages (public/internal), attachments, status history.
- **Triage workspace** — Incoming / Questions / Enter on behalf tabs; accept/reject/ask actions.
- **Coordinator workspace** — job creation from an accepted order, job-number entry, SO search and
  link/unlink, attachments, send-to-production.
- **Credit review** (once OP-08 ships) — queue of held orders, release/reject action, restricted
  visibility.
- **Admin** — divisions, manager/coordinator pairs, reason codes, order-type aliases, users,
  imports, audit log, SH-location verification flags.
- **GM/COO view** — redacted order/job overview; no per-worker data.

All screens are desk-first (laptops/desktops) for Release 1 — no phone-first layout is required
unless the user says otherwise; nothing in the spec or brief asks for mobile use of the portal
specifically (`plans/40...` §14).

---

## 3. Notifications

The next actor is notified **instantly** on order creation or any state move — **in-app (SSE) plus
email**, which are the system of record. **WhatsApp is an optional urgent alert only**, and only
once the separately-scoped, currently-paused Hub WhatsApp project resumes — never a bespoke sender
built inside this project, and never anything resembling anti-detection behaviour. A backup owner
exists for the notification pipeline so a silent failure has a named person to page (OP-09).

---

## 4. Reports

Release 1 itself ships no standing report beyond the order/job lists above — reporting is a later
release's concern (R4, GM/analyst views) built on the same redaction rules. What the order portal
*must* guarantee for any report built on top of it, now or later:
- Never sum SPS and SH order values in one number (structural rule, checked by `code-reviewer` as
  a standing item for every report/screen the release adds — OP-07 AC3).
- GM/COO-facing views always apply the redaction rule (§5.4) — worker identity hidden, minutes
  only as aggregates with ≥2 distinct workers.
- List endpoints answer within the AC1.28 performance discipline (`GET /api/jobs`-style: under
  300ms median over 5,000 rows, keyset-paged chunks of ≤500, no single sync DB call blocking the
  event loop over 100ms) — applied to any new order-list endpoint (OP-14).

---

## 5. Integrations

### With Zoho (spec §6.2, §8; `plans/40...` §7, §11)
- **Read-only mirror only.** The portal never writes to Zoho — the `outbox` table stays `held`
  forever by design (spec D15). A browser-only helper fills Senuri's Zoho form; she clicks Save.
- **SPS side (OP-05, OP-11, OP-12):** a scheduled read-only sync (superseding the Release-0 manual
  import CLI) keeps `zoho_*` mirror tables fresh, with `captured_at` discipline (an older capture
  never overwrites a newer one). SO search/link/unlink against the mirror, using the exact
  `so_key` regex (never a naive string match). A "Portal Order No" custom field on the SH SO,
  ideally made mandatory in Zoho settings, closes the ~17–18%-fill-rate linking gap.
- **SH side (OP-16, floating, blocked on SH Zoho admin access):** a much larger-volume sync once
  the `ithelp@` login can see all 10 locations, not just Head Office; Senuri's helper page; "way
  A" automatic linking once sync exists (superseding the "way B" paste-and-validate fallback OP-12
  builds first).

### With the production dashboard (same codebase, later releases)
An accepted portal order creates exactly one job (`orders.id` FK, partial-unique so an order can
never produce two jobs). Everything downstream — manager dashboards (R2), stores/invoicing (R3),
raw-material blockers (R4), GM/COO views (R4), floor stations (R5) — reads and acts on that same
`jobs` row. The order portal is the front door; the rest of the app is what happens to a job after
triage accepts it.

### With the inventory/stock system (separate, paused project)
**Not built by this project.** The order portal's only obligation, when that project resumes and
the safety-stock policy is signed off, is to keep `order_type` as an extensible lookup table so a
future "against buffer stock" call-off order type is a seeded INSERT, not a schema change (OP-15,
wiring only — no draw-down logic, no `buffer_stock` value, until the policy and the stock system
are both ready). This is the mechanism the Keells/Spar cutlery line and the Oct–Dec 2026
key-customer plan already use informally.

### With Power BI / the BI reporting layer (separate project)
No direct integration is scoped for Release 1. If a future BI layer reads order-portal data, it
must read from the same mirror/core-table split and the same never-sum-SH-and-SPS rule — flag this
explicitly if that integration is ever proposed, don't assume it inherits the rule automatically.

---

## 6. Non-functional qualities

- **Desk-first, not mobile-first** for Release 1 (spec D5; requesters, triage, coordinators all
  work from a desk). Mobile use is an explicitly open question to ask the user, not an assumption
  either way (`plans/40...` §14).
- **No offline tolerance required** — "Offline tablets" is a spec Non-goal (§3); the order portal
  itself has no offline requirement.
- **Performance:** `GET /api/jobs`-class list endpoints answer in <300ms median over 5,000 rows;
  no single synchronous DB call blocks the event loop over 100ms (spec §8.2, AC1.28) — the same
  discipline applies to any new order-list endpoint this release adds.
- **Audit:** every job-no change, override, attachment-visibility flip and admin action writes an
  append-only `audit_log` row (spec §6.3). Append-only enforced by DB triggers, not just
  application logic, on `orders`, `order_lines`, `order_events`, `order_messages` and several
  other tables (spec §6.3 "(A)" tables) — so immutability holds even if a future route tries to
  violate it.
- **Backups:** online backups, pruning and a monthly restore check are already built in Release 0
  (`git log`: `d2d6fba feat: online backups, pruning and the monthly restore check`) and carry
  forward unchanged for Release 1's data.
- **Security:** scrypt auth, hashed session ids, `HttpOnly/Secure/SameSite=Strict` cookies, CSRF
  via required `Origin`, server-side role checks on every route, magic-byte-checked uploads,
  GM/COO redaction — all spec §11, all tested (AC1.2, AC1.14, AC1.30), all reviewed by
  `security-auditor` before Release 1 ships (spec §11).
- **Uptime:** no formal SLA found in any source read for this project; treat as a standard
  desk-office internal tool (same operational tier as Release 0's existing admin app), not a
  customer-facing or safety-critical system.

---

## 7. Measurable success criteria

Baselines below are the best numbers this build has, each cited to its source; mark clearly where
a number is a proxy, not a direct measurement.

| Metric | Baseline (today) | Source | What "success" looks like once Release 1 is live |
|---|---|---|---|
| SPS→SH SO link rate | ~17–18% of SPS orders carry a usable `CF.SH Sales Order Ref` (1,398 of 8,286 independently recomputed; 1,472/8,325 per an earlier check) | `plans/40-order-portal-developer-brief.md` §7, `so.pkl` | Every new order has a `job_so_links` row or a pending link that the sweep resolves automatically — the manual-typo failure mode this baseline measures should not recur for orders placed through the portal |
| Orders mis-tagged to "Standard Holdings" instead of the real customer | ~29% of key-customer order lines | `BRIEF.md:48` | 0% for orders placed through the portal — the requester picks the real customer at entry from a real picker (OP-11), not free text after the fact |
| Order-to-production lead time (customised, last 12 m) | OPD median 20 d / p80 30 d; SHPS 10/20; PCU 21/26; MOBA 20/31; CPU 4/7 | `BRIEF.md:47` | The portal alone doesn't move this number — it's a Release 2–4 (raw-material blocker, manager workspace) outcome — but Release 1 is the precondition: it's what gives every order a real, server-recorded start time to measure lead time *from*, replacing the current unknown WhatsApp receipt time |
| Finished-goods stock for key-customer items | 0 for every key-customer item on 19 Sep 2026 (make-to-order today) | `BRIEF.md:46` | Unaffected by Release 1 itself; this is the metric the future call-off order type (OP-15, gated on the separate stock project) would eventually move |
| Order status visibility | None today — the only way to check status is to call or find the physical file | `CLAUDE.md:1` ("Zoho's centralised dashboard... nobody uses it"; a paper file whose location is the only status) | Every order has a live, plain-word status any authorised person can check without a phone call (AC1.7 — status never regresses on an internal handover) |
| Credit exposure caught before an order ships | Manual, ad hoc, by Hazeem, today | `CLAUDE.md §17.2` (20-Sep draft) | Automatic at submission, exact LKR-over-limit amount shown, read from Zoho Inventory (`analysis/research/zoho-credit-limit.md`, DECIDED 25 Sep 2026) — once OP-08's remaining two open questions (block-vs-hold; dues definition) are answered (this metric cannot be claimed complete until then) |
| SH locations visible to the sync | 1 of 10 (Head Office only) | `plans/40...` §6, `memory/zoho-inventory-export.md` | All 10, each order correctly tagged, no silent default to Head Office (OP-07) — blocked on SH Zoho admin access |

**What Release 1 alone does not fix** (named so it isn't silently claimed as a Release-1 outcome):
actual lead-time reduction, raw-material shortage visibility, and true OTIF measurement are R2–R4
outcomes that depend on Release 1's data existing first, not something Release 1 itself delivers.

---

## 8. What "done" for this project actually means

Per `/root/.claude/CLAUDE.md` §1.5: "Done" means tests pass, the spec (plus its approved delta)
is satisfied, and the diff has been reviewed — not that a feature looks built. Concretely, per
`dev/order-portal/02-process-steps.md` OP-14: the AC1.27 end-to-end Playwright test passes in CI
(requester submits → triage accepts → coordinator sets job no, links pending SO, attaches docs,
sends to production → import+sweep resolve the SO → requester sees "In production" live via SSE),
every new list endpoint meets the AC1.28 performance discipline, `security-auditor` and
`db-migration-guard` both return PASS on the full Release-1 diff, and a go-live checklist names an
owner for every item flagged "blocks go-live" across OP-01–OP-13 (not blocking the build itself).

---

Abdul Hadhee | IT Exec | Standard-Holdings
