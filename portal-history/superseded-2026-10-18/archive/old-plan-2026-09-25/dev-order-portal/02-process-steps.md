# Order portal — process/feature steps, in build order

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** the user decided PSU and
Screen Printing must both go live by December 2026, managers only, which forced changes to this
track (full reasoning: `dev/01b-dated-schedule.md` §0.5, `dev/01c-dashboard-december-feasibility.md`
§3): **OP-01/OP-02 no longer include MFA** (it moves to a new dashboard-track migration, `PD-03D`,
since it's a "going public" gate, not a portal feature) or the `recursive_triggers` pragma fix
(also `PD-03D`); **OP-11 is removed** — its content ships ~10 weeks earlier as `PD-05D`, because the
December dashboard needs live SPS SO data too, not just the portal (the SH-side sync half stays
under OP-16, unchanged); **OP-05's SO-linking scope narrows** to portal-accepted orders only
(direct-job linking for PSU/SHPS already ships in `PD-04D`). Every step's **Dates** line below is
updated to the rebuilt `dev/01b-dated-schedule.md` — OP-01/OP-02 start ~3 weeks later (the shared
developer works the December track first) and every step from OP-12 onward lands within ~2 working
days of its original date (removing OP-11 roughly cancels the later start). Full release now
computes to **15 Feb 2027** (2 working days after the 11 Feb 2027 target — see OP-14's note).

**Changed 25 Sep 2026 (earlier the same day):** OP-08's credit-limit data source is now **DECIDED**
(Zoho Inventory, no Zoho Books) — rewrote OP-08's Goal, build steps, acceptance criteria and
open-questions list to match; removed the Books-vs-Inventory conflict everywhere it appeared in
this file. Added a **Dates** line to every step (OP-01…OP-16), pulled from the published dated
master schedule (`dev/01b-dated-schedule.md`, `dev/dated-schedule.json`) — no dates were invented
here.

Prepared by Abdul Hadhee | IT Exec | Standard-Holdings, 25 Sep 2026.

**What this is.** The order portal is **Release 1 of the production-dashboard app**
(`/root/dev/production-dashboard`), not a separate codebase — it shares the schema, auth,
migrations and pipeline of the production dashboard already partly built there
(`analysis/research/dashboard-state.md:2`, plans/`40-order-portal-developer-brief.md` §1). This
file is its own project's step list because it is a separately staffable, separately scoped body
of work (Release 1 vs Release 0's foundation, already built, and Releases 2–6, someone else's
plan) — but every step below assumes Release 0 (schema 001–004, auth, admin, import CLI) exists
and is frozen, and every migration here is **additive on top of it**
(`plans/40-order-portal-developer-brief.md` §12; design spec §6.1).

**Numbering:** `OP-01` … `OP-16`, in the order a developer should build them — each step is
buildable once the steps in its `depends-on` are done. Two steps are explicitly **not build-now**
(OP-15, OP-16) and are listed so their place in the sequence and their blockers are visible, not
because they start this quarter.

**Authoritative sources for every step below** (cited inline, not re-derived):
`/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` (Rev 7.3, the
frozen spec), `plans/40-order-portal-developer-brief.md` (this project's brief, itself fully
cited), `analysis/research/dashboard-state.md`, `/root/Production Dashboard/CLAUDE.md` §17,
`/root/Production Dashboard/BUILD-ORDER-2026-09-20.md`, `/root/Production Dashboard/LATER.md`.

**Effort basis:** weeks for one developer, supervised by an agentic AI coder, working test-first
against an already-scaffolded Express + better-sqlite3 + React codebase
(`/root/dev/production-dashboard/package.json`) with an existing auth/session/RBAC layer to extend
rather than build from scratch. Estimates assume the step's own **ingredients** (below) are ready
when the developer starts — an unanswered question turns a week into an open-ended wait, not a
longer week.

**Total, OP-01 → OP-14 (the steps this release actually needs to go live):** ~12.0 developer-weeks
as originally scoped; **~10.5 developer-weeks now that OP-11 (1.5 weeks) has moved out to `PD-05D`**
in the December dashboard track (25 Sep 2026, later the same day — see the banner above). MFA's
removal from OP-01/OP-02 isn't separately re-quantified here; treat the ~10.5 figure as directional,
not re-verified line by line. OP-15 and OP-16 (≈1.75 weeks) are scoped but explicitly deferred —
see their own entries.

---

## OP-01 — Spec delta "Release 1 v2" (non-credit) + plan-critic pass

**Goal:** turn the still-informal decisions that Release 1 needs — company/SH-location tagging on
`orders`, growing enums replaced by lookup tables, a separate `notifications` table, several child
jobs per order, `customer_portal=false` — into a written, numbered spec delta with its own
acceptance criteria, reviewed and passed by `plan-critic`, **before any Release-1 code is written**.
**MFA is no longer part of this delta (25 Sep 2026, later the same day)** — it moves to the
December dashboard track's own spec delta (`PD-02D`) and migration (`PD-03D`), since it's a "going
public" gate needed for the December managers-only release, not portal-specific content
(`docs/runbook-release-0.md:4`, `01c-dashboard-december-feasibility.md` §3).
This is `BUILD-ORDER-2026-09-20.md` row 2, and it is a **hard pipeline gate**
(`/root/.claude/CLAUDE.md` §2: "no code without a spec"). The credit check is deliberately **not**
in this step — it has its own open questions and its own step, OP-08, so it never blocks the
rest of the release (`plans/40...` §5, "don't let an unresolved dependency block the whole release").
OP-08's data-source question is now DECIDED (Zoho Inventory, 25 Sep 2026); two questions remain.

**What the development must do:** no application code. Write the delta as an amendment to
`/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` (or a dated
companion file the spec then points to), covering: `orders.company` / `orders.location` (§6 of the
brief); `order_type`, `order_events.event` and `reject_reasons`-style enums that will grow,
converted to seeded lookup tables per `LATER.md:54` (L31 item D6, D7); a `notifications` table
decision, separate from `outbox` (`BUILD-ORDER-2026-09-20.md` §6, "recommended: a separate
`notifications` table"); several child jobs per one accepted order (today's spec has one job per
order — confirm the multi-job shape before schema, not after); `customer_portal=false` as a stored flag, not a
convention (spec Q9). Each item gets its own numbered acceptance criterion in the spec's own style
(a criterion + check type T/E/C), matching `plans/40...` §15's instruction: "write its acceptance
criteria as part of the spec delta... don't invent ad hoc criteria at implementation time."

**Inputs:** `plans/40-order-portal-developer-brief.md` §5, §6, §9, §11; `BUILD-ORDER-2026-09-20.md`
row 2; `CLAUDE.md` §17.5–17.6; `dashboard-state.md:3,7`; `LATER.md:54` (L31 D6, D7).

**Outputs:** an approved spec delta (merged text or a dated companion doc the spec references), a
`plan-critic: PASS` verdict on file, no schema or code changes yet.

**Acceptance criteria:**
1. `plan-critic` returns `PASS`, not "approve with changes" left unresolved — every finding closed
   or explicitly deferred with the deferral in writing.
2. Every item in the "what the development must do" list above has at least one numbered,
   falsifiable acceptance criterion in the delta text, in the same T/E/C style as spec §13.
3. The delta names, for every enum it converts to a lookup table, the exact seed rows and the
   table's foreign-key shape (so OP-02 needs no further design decisions).
4. Credit check is explicitly out of this delta's scope, with a one-line pointer to OP-08.

**Depends-on:** none inside this project. External prerequisite (already satisfied):
production-dashboard Release 0 (`dashboard-state.md:2`, schema 001–004 frozen, 143 tests green).

**Estimated effort:** 0.5 week (writing + one plan-critic review cycle).

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
22–23 Oct 2026 (**FORCED**: ~3 weeks later than originally scoped — the shared developer works the
December dashboard track first, `01b-dated-schedule.md` §0.5). Sub-step — no separate release;
ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

**Ingredients list:** the current frozen spec and its migrations (already exist); the LATER.md
D6/D7 items open; someone available to run `plan-critic`.

**Questions that must be answered first:**
- Confirm the multi-job-per-order shape is actually needed for Release 1 go-live, or can wait —
  **GM Samitha** (does any current order genuinely split into several jobs at once, e.g. one order
  spanning two divisions?), tagged: unblocks OP-01 item 3, needs no mini-report.
- Any objection to English-only for Release 1, or should Sinhala/Tamil be scoped in now (this
  changes whether i18n plumbing belongs in this delta) — **GM Samitha**
  (`plans/40...` §14), tagged: unblocks OP-01 and OP-14, no mini-report.

---

## OP-02 — Additive schema migration (portal half)

**Changed 25 Sep 2026 (later the same day):** renamed from "Additive schema migration + MFA" — MFA
and the `recursive_triggers` pragma fix both moved to the December dashboard track's own migration,
`PD-03D`. This step now covers only the order-portal-specific schema: `orders.company`/
`orders.location`, the enum→lookup-table conversion, and the `notifications` table.

**Goal:** implement OP-01's delta as code: a new numbered migration (005+, never a change to
001–004), the new tables/columns it specifies.

**What the development must do:** write `server/db/migrations/005-release1-v2.sql` (and further
numbered files if the delta needs more than one, e.g. lookup tables in one file, `orders` columns
in another) purely additive — no `DROP TABLE`, no `DROP COLUMN`, no `RENAME`
(spec §6.1, enforced by the existing migration linter, `server/db/lint-migrations.js`). Extend
`server/db/migrate.js`'s hash-guard coverage and `MANIFEST.json` per `LATER.md:54` (L31 D3, D6,
D7): lookup-table FKs `NOT NULL` and seeded in the same migration's seed section, with a
`foreign_key_check` test and delete-protection triggers so a lookup row can't be deleted while
referenced. (MFA fields/tables behind a config flag, and the `recursive_triggers` pragma fix, are
built in `PD-03D` instead — not part of this migration.)

**Inputs:** OP-01's approved delta; `server/db/migrations/001-schema.sql` through `004-...sql`
(read for the existing pattern — additive migrations, hash guard, lint rules); `LATER.md:54,58`.

**Outputs:** one or more new migration files, an updated `MANIFEST.json`, updated
`server/db/lint-migrations.js` coverage if the delta introduces a pattern the linter doesn't yet
check.

**Acceptance criteria:**
1. `npm test` (the full existing suite, including the migration-parsing test) stays green after
   the new migration lands — no existing test is edited to accommodate a forbidden operation.
2. A fresh `npm start` against an empty `data/production.db` and against a copy of the current dev
   database both apply the new migration idempotently (spec's own idempotency rule, README.md
   "Migrations run automatically at server startup... idempotent by design").
3. Every new lookup table has a `foreign_key_check`-covering test and a delete-protection trigger
   test (insert a referencing row, attempt to delete the referenced lookup row, expect failure).
4. `db-migration-guard` returns `PASS` on this diff before it merges (schema-touching change,
   `/root/.claude/CLAUDE.md` §2 table).

**Depends-on:** OP-01.

**Estimated effort:** 1 week (unchanged; the MFA/pragma removal isn't separately re-quantified —
see the front-matter total note).

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
28 Oct – 3 Nov 2026 (**FORCED**: later start; MFA schema and the `recursive_triggers` pragma fix
removed — both now `PD-03D`). Sub-step — no separate release; ships as part of OP-14's single
Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

**Ingredients list:** OP-01's delta text with exact seed rows; a copy of the current dev database
to test idempotency against (never the live tree — `/root/dev/production-dashboard` only).

**Questions that must be answered first:** none beyond OP-01's own — this step is pure translation
of an already-approved delta into migrations. **Stop and ask IT (the user)** only if the delta
turns out to be ambiguous about a seed value or a column type; do not guess (`/root/.claude/CLAUDE.md`
§1, "no confident guessing").

---

## OP-03 — Order submission and core lifecycle

**Goal:** build the state machine that is already fully specced and frozen — order submission,
`submitted → questions → accepted/rejected/cancelled`, immutability of fields/lines after submit —
with **no credit gate and no company/location requirement yet** (those are OP-05 and OP-08), so the
core flow is testable against the spec's own written acceptance criteria without waiting on either.

**What the development must do:** implement `POST /api/orders` (customer, required date, type,
division hint, items, attachments; server sets `submitted_at`, ignoring any client-sent time — spec
AC1.1), `GET /api/orders/mine`, `GET /api/orders/:id` (thread view), `POST /api/orders/:id/messages`
(public/internal), `POST /api/orders/:id/cancel-request` and `POST /api/orders/:id/decline-cancel`
(spec's exact route table, `plans/40...` §3, design spec route list). Add the DB triggers that
abort UPDATE/DELETE on `orders`, `order_lines`, `order_events`, `order_messages` (spec's **(A)**
append-only tables, §6.3) — enforced by triggers, not just application logic, so AC1.3 holds even
if a future route tries to violate it. Implement `order_status` derivation server-side exactly per
spec §6.4 (never a client-side guess) for the plain-word status shown to requesters.

**Inputs:** design spec §6.3 (`orders`, `order_lines`, `order_events`, `order_messages` schema),
§6.4 (`order_state`/`order_status` derivation), §7.2.0 (state table), §7.2.1
("Updates are not edits"), route table (`plans/40...` §3 route list); AC1.1, AC1.3, AC1.7 (spec §13).

**Outputs:** the four routes above, working against a test DB with append-only triggers; a server-
side `order_status` function with unit tests covering every branch of §6.4's derivation.

**Acceptance criteria (verbatim from spec, don't re-derive — `plans/40...` §15):**
1. AC1.1: `submitted_at` is server time; a client-sent time is ignored.
2. AC1.3: no route can change order fields/lines after submit; the DB triggers abort it even if a
   route tried.
3. AC1.7: a file sent back to the coordinator still shows "In production" — status never regresses
   on an internal handover (testable once OP-04's job creation exists; write the test now, mark it
   skip/pending until OP-04 lands, per test-first discipline).
4. Every §7.2.0 transition not explicitly in the table returns 409, tested by an exhaustive
   transition-matrix test.

**Depends-on:** OP-02.

**Estimated effort:** 1.5 weeks.

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
4–16 Nov 2026 (**FORCED**: later start only, content/effort unchanged). Sub-step — no separate
release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target
11 Feb).

**Ingredients list:** none beyond the spec text and OP-02's schema — this step needs no new
external decision.

**Questions that must be answered first:** none. This is the one step in the whole release that is
fully unblocked by open questions — start here once OP-02 lands.

---

## OP-04 — Triage workspace

**Goal:** the three-tab triage queue (Incoming, Questions, Enter on behalf) and its three actions
(Accept, Reject, Ask), per spec §7.2.2 — this is where an accepted order becomes a job.

**What the development must do:** implement `GET /api/triage/orders` (oldest-first, cancel-pending
orders on top) and `POST /api/triage/orders/:id/{accept,reject,ask,cancel}`, each taking
`expected_state` (and `expected_last_event_id` where the spec's route table specifies it) for
optimistic-concurrency safety. **Accept** creates the job in the same DB transaction
(`order_received_at = submitted_at`, `entered_*` copied from the order's first line + "(+n more)"
— spec Rev 4 B1) and requires the accept dialog to collect division + manager/coordinator pair.
**Reject** requires a reason code (`reject_reasons` lookup) and a public note. **Ask** posts a
public message and moves the order to Questions; a requester reply writes `answered` and moves it
back to Incoming. Implement `POST /api/triage/orders` for **Enter on behalf** (spec Rev 4 N10):
triage types a WhatsApp receipt time that must be in the past and within 60 days, picks the
requester (their team is copied), fills the normal order fields; stored with `created_via =
on_behalf`, `submitted_at` = the typed time, `entered_at` = now, plus an audit row.

**Inputs:** design spec §7.2.2 (full triage rules), route table entries for
`/api/triage/orders*`; `plans/40...` §4; AC1.4, AC1.5 (spec §13); `CLAUDE.md:398` (the seeded
manager/coordinator pairs, several divisions still missing one — see questions below).

**Outputs:** the triage API and its UI tabs; the accept-race and reject/ask flows fully tested.

**Acceptance criteria:**
1. AC1.4: two simultaneous accepts on one order → exactly one 200, one 409, exactly one job.
   Accept while `cancel_pending` → 409.
2. AC1.5: reject without a reason code → 400; every §7.2.0 combination not in the table → 409.
3. Enter on behalf: a receipt time in the future, or more than 60 days in the past, is rejected;
   the resulting order is indistinguishable to the requester from one they typed themselves, except
   for the audit trail (test both — the requester view **and** the audit row).
4. Accept without a valid manager/coordinator pair for the chosen division → 400, not a job created
   against an unassigned division (protects against the gap `CLAUDE.md:398` flags: PCU, PCLU, DPU,
   PPU, CWU have no pair yet as of this brief).

**Depends-on:** OP-03.

**Estimated effort:** 1 week.

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
17–25 Nov 2026 (**FORCED**: later start; answer deadline moves to 3 Nov 2026). Sub-step — no
separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027**
(target 11 Feb).

**Ingredients list:** the manager/coordinator pair table fully populated for every division that
will go live in Release 1 (today missing PCU, PCLU, DPU, PPU, CWU — `CLAUDE.md:398`); the named
triage owner(s) for SPS and, separately, SH (open question below — building the *feature* doesn't
need the name, but go-live does, and the accept-dialog role check needs at least one real triage
account to test against).

**Questions that must be answered first:**
- Who is triage for SPS orders, and separately, who is triage for SH orders — **GM Samitha / COO**
  (spec Q7, `plans/40...` §2, §18). Blocks: go-live only, not the build itself. No mini-report.
- Confirm the manager/coordinator pairs for PCU, PCLU, DPU, PPU, CWU — **GM Samitha**
  (`plans/40...` §18, `CLAUDE.md:398`). Blocks: OP-04 acceptance test data, go-live. No mini-report.
- Is the WhatsApp order group switched off on day one, or run in parallel — **GM Samitha /
  triage owner** (spec Q8). Blocks: go-live decision on Enter-on-behalf's actual usage volume, not
  the build. No mini-report.

---

## OP-05 — SPS ↔ Zoho SO linking

**Changed 25 Sep 2026 (later the same day):** scope narrows to **portal-accepted orders only** —
direct-job linking for the December-live divisions (PSU, SHPS) already shipped early in `PD-04D`,
using the same `so_key` matching rule this step builds. Not a date-affecting change, just a scope
note (`01c-dashboard-december-feasibility.md` §4).

**Goal:** the SPS side of linking a portal order/job to its Zoho sales order — already fully
specced and frozen (`plans/40...` §7: "Build this part as written; it needs no new decision").

**What the development must do:** implement `GET /api/so/search?q=` and `POST /api/jobs/:id/so`
(`{action: link|link_pending|unlink, salesorder_number}`) against the existing Release-0 mirror
(`zoho_*` tables, already populated by the import CLI). Use the exact `so_key` regex from spec §6.2
— trim, uppercase, match `^([A-Z]+-\d+)(\s*-.*)?$`, group 1 is the key — never a naive string
compare (`plans/40...` §17, the single most-repeated pitfall in this brief). Hook the **post-import
sweep** (already built in Release 0, `server/services/sweep.js`) to resolve a `link_pending`
reference once its SO appears in a later import, writing a system `link` row and broadcasting an
SSE job event within poll interval + 5s.

**Inputs:** design spec §6.2 (`so_key` matching rule), §6.3 (`job_so_links`), §7.2.3; existing
`server/services/sweep.js` (read before touching — do not duplicate its matching logic, extend it);
AC1.10, AC1.11, AC1.20 (spec §13).

**Outputs:** the SO search/link/unlink routes; sweep extended to resolve pending links.

**Acceptance criteria (verbatim, spec §13):**
1. AC1.10: linking an SO shows its Zoho fields and stage 4 is detected; unlink → stage 4 not done
   immediately; re-link the same SO → done again.
2. AC1.11: a pending `JOBORDER-…` link resolves in the post-import sweep after the next import
   (system `link` row); SSE clients get a job event within poll interval + 5s.
3. AC1.20: `JOBORDER-08338 - C` and `joborder-08338` both match `JOBORDER-08338`;
   `JOBORDER-083381` does not; an SH row with the same SO number never ticks an SPS job (org
   isolation, tested).

**Depends-on:** OP-03.

**Estimated effort:** 1 week.

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
26 Nov – 3 Dec 2026 (**FORCED**: later start only). Sub-step — no separate release; ships as part
of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

**Ingredients list:** none new — the mirror tables and sweep already exist from Release 0.

**Questions that must be answered first:** none. Build as written.

---

## OP-06 — Job number assignment

**Goal:** `jobs.job_no`, nullable until set, opaque, never parsed — spec §6.3, §8.

**What the development must do:** implement `POST /api/jobs/:id/job-no` (`{job_no, reason?}`),
409 on a duplicate within `(division_code, job_no)` (`NULL`s don't collide — spec §6.3 UNIQUE note),
`reason` required and an audit row written when changing an already-set number (spec AC1.12). Make
`to_production` return 400 when `job_no` is still null (spec API table §10). Store the string
exactly as typed — no validation, extraction, or auto-numbering logic that assumes a shape
(`RWU/IMP2357/QPP/00025/BIO` must round-trip unchanged, per real examples on file,
`plans/40...` §8).

**Inputs:** design spec §6.3 (`jobs.job_no` note), §8 (job-number rules), §10 (API table); AC1.12.

**Outputs:** the job-no route; a 400 test for `to_production` with no job number.

**Acceptance criteria:**
1. AC1.12: "No SO" requires all four `entered_*` fields; duplicate `(division, job_no)` → 409 both
   at job creation and via `POST /job-no`; opaque strings stored exactly as typed.
2. Changing an already-set job number without `reason` → 400; with `reason` → 200 + audit row.
3. `to_production` with `job_no` still null → 400.

**Depends-on:** OP-04.

**Estimated effort:** 0.5 week.

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
4–8 Dec 2026 (**FORCED**: later start only). Sub-step — no separate release; ships as part of
OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

**Ingredients list:** none new.

**Questions that must be answered first:** none.

---

## OP-07 — Company (SPS/SH) and SH-location tagging on orders

**Goal:** make "never sum SPS and SH" structurally hard to violate at the data-entry point, not
just a reporting convention (`plans/40...` §6, the single most-repeated rule in every source
document read for this brief).

**What the development must do:** using OP-02's new `orders.company` (`SPS`/`SH`, required at
submission) and `orders.location` columns, wire the order-submission form to require `company` and,
for `company = SH`, a location picker. **Do not hard-code Head Office as the default or the only
option** — the `ithelp@` sync login can currently see only Head Office out of SH's 10 locations
(`plans/40...` §6, a real access gap). Instead: seed `orders.location` as a free-choice list of
all 10 known SH locations from `zoho-helper-userscript-spec.md:42` (Head Office, South Branch,
Central Branch and the 7 not yet seen in sales-order data), flagged in Admin as
"not yet verified against a live sync" for the 7 unconfirmed ones, so the gap is visible on screen
rather than silently worked around.

**Inputs:** `plans/40...` §6; spec D4 (the `org` pattern already used on every mirror row — extend
the same convention, don't invent a second one); `zoho-helper-userscript-spec.md:42`.

**Outputs:** `company` and `location` required on the order-submission form and API; an Admin flag
per location row for "unverified" ones; every existing report/screen this release adds is checked
for cross-company summing (a lint rule or a code-review checklist item, not just a test).

**Acceptance criteria:**
1. `POST /api/orders` without `company` → 400.
2. `company = SH` without `location` → 400.
3. No query anywhere in the Release-1 codebase sums `orders.value` (or any derived total) across
   `company` values without an explicit, named exception — checked by `code-reviewer` as a
   standing rule for this release, not just this step's diff.
4. The 7 unconfirmed SH locations are visibly flagged "unverified" wherever they appear in Admin or
   any picker.

**Depends-on:** OP-02, OP-03.

**Estimated effort:** 0.5 week.

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
9–11 Dec 2026 (**FORCED**: later start; answer deadline moves to 25 Nov 2026). Sub-step — no
separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027**
(target 11 Feb).

**Ingredients list:** the confirmed list of all 10 SH locations and their correct display names
(only 3 are confirmed from live order data today — `plans/40...` §6).

**Questions that must be answered first:**
- Confirm the names and existence of the other 7 SH locations (today only Head Office, South
  Branch, Central Branch are confirmed from order data) — **SH Rizwan / Abdullah**, tagged:
  unblocks OP-07 seed data, no mini-report.
- SH admin access to see all 10 locations through the sync login, not just Head Office — **IT
  (the user), pending SH admin grant** (`plans/40...` §6, `LATER.md:50`). Unblocks: OP-07's
  "unverified" flags becoming "verified"; OP-16 (which now also carries OP-11's old SH-side sync
  gate). No mini-report, but this is the single access item that unblocks the most downstream work
  — flag it as priority #1 in the meeting.

---

## OP-08 — Credit check (spec delta + build, gated)

**Goal:** the automatic credit gate at order placement — mechanism sketched, **not yet in the
frozen state machine** (`plans/40...` §5). This step is deliberately isolated from OP-01–OP-07 so
it never blocks the rest of the release; it starts only once the two open questions below are
answered (the data-source question that used to be a third open item is now DECIDED — see below —
and no longer blocks the start).

**What the development must do, in two phases:**
1. **Spec delta** (same discipline as OP-01, its own `plan-critic` pass): add whatever state or
   gate the answers to the two open questions require to spec §7.2.0 — a new terminal-ish
   `credit_hold` state, or a hard 400 at submit with a release queue, depending on question 1's
   answer. Reconcile the 20-Sep draft status enums (`CLAUDE.md §17.5`: requester-visible
   `Released / Rejected / Held until customer pays / Cancel / Change order`; reviewer-only
   `Credit Hold / Released / Rejected / On Hold / Sent for review`) with the spec's actual
   `order_events` enum (§7.2.0) — **implement one set, not both** (`plans/40...` §5).
2. **Build:** implement the formula
   `available_credit = credit_limit − (outstanding_receivable_amount_bcy − unused_credits_receivable_amount_bcy)`,
   `over_by = (this order's value) − available_credit`; on `over_by > 0`, show an error popup
   quoting the exact LKR amount at submission time. Data source is **DECIDED: Zoho Inventory** —
   call `GET /contacts/{contact_id}?organization_id={id}` (Zoho Inventory API v1) for the
   logged-in customer's org (SH and SPS checked and cached separately, never summed), reading
   `credit_limit`, `outstanding_receivable_amount_bcy`, `unused_credits_receivable_amount_bcy`.
   **No Zoho Books integration, token or login is built** — that data source is closed, not just
   deferred. Visibility: "On Hold – Credit Review" seen only by Senuri, the order's placer, CEO,
   COO and both GMs (`CLAUDE.md §17.2`).

**Inputs:** `plans/40...` §5 in full (this is the most-detailed single section of the brief for a
reason); `CLAUDE.md §17.2` step 3, §17.5; `dashboard-state.md:3,7`;
`analysis/research/zoho-credit-limit.md` (the field/endpoint/formula/rate-limit research behind
the DECIDED data source).

**Outputs:** the credit-check spec delta (merged into the frozen spec), the gate itself, and its
visibility rule.

**Acceptance criteria:**
1. A new numbered AC exists in the spec for each of the two resolved questions plus the DECIDED
   data source, in spec style (criterion + check type), written as part of the delta, not invented
   at implementation time.
2. An order whose `over_by > 0` at submission is blocked or held (per question 1's answer) and the
   popup shows the exact LKR amount, computed from the actual Zoho Inventory fields via the formula
   above, not a placeholder.
3. "On Hold – Credit Review" (or whatever the delta names the state) is visible only to the roles
   listed above — tested the same way as the §7.2.4 visibility matrix (a key/value scan on seeded
   data, per AC1.2's method).
4. `plan-critic` and, because this touches auth/visibility, `security-auditor` both return `PASS`
   before this ships.
5. No code path in the diff calls Zoho Books, requests a Books token, or references a Books login —
   a code-review checklist item, since the data source is Zoho Inventory only.

**Depends-on:** OP-03.

**Estimated effort:** 1 week (once the two remaining questions are answered — an unanswered
question adds open-ended wait, not more build time; the data-source question, formerly a third
open item, is now DECIDED and no longer adds wait).

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row
`OP-08`):** build 14–21 Dec 2026 (**FORCED**: later start; answer deadline moves to 30 Nov 2026;
the Zoho-Inventory-as-data-source decision is unaffected). Sub-step — no separate release; ships as
part of OP-14's single Release-1 go-live: IT test 26–28 Jan 2027, UAT 29 Jan – 12 Feb 2027, full
release **15 Feb 2027** (target 11 Feb).

**Ingredients list:** the two answers below; the credit-limit data source is already decided
(Zoho Inventory) and its field/endpoint are already identified — see "DECIDED" note below.

**DECIDED (user, 25 Sep 2026) — data source, no longer an open question:** the credit limit is
read automatically from **Zoho Inventory**, not Zoho Books. No Books access, login or token is
needed. Field: `credit_limit` on the shared Zoho Contact object, returned by
`GET /contacts/{contact_id}?organization_id={id}` (Zoho Inventory API v1) alongside
`outstanding_receivable_amount_bcy` and `unused_credits_receivable_amount_bcy` (use the `_bcy`,
LKR, versions). Confirmed live in our own SPS org's data
(`/root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json`,
`contact.credit_limit`) — currently `0`/unset for the one contact visible there, so before go-live
someone with Zoho's "configure credit limit" permission needs to set real limits for the 8 key
customers (a data/config task, not new development). Zoho already blocks/warns on this natively at
its own API layer (Settings → Preferences → Customers and Vendors, "Restrict" or "Show a warning");
the portal pre-checks so the customer sees a clean message, it does not rebuild Zoho's enforcement.
Rate limit 100 req/min/org — one `GET` per checkout is negligible; a ~60s per-customer cache is
optional. Full research, every claim cited: `analysis/research/zoho-credit-limit.md`.

**Questions that must be answered first — put to the user, not the developer's call
(`plans/40...` §5, §18):**
1. Block the order outright over the credit limit, or hold it for a named person to release? —
   **Credit controller / Finance (Hazeem's function)**. Tagged: blocks OP-08 phase 1 entirely.
   Needs a mini-report: **yes** — `plans/40...` §18 recommends this go to Hazeem as "one short
   standalone memo before the wider planning meeting, given how much of the order flow depends on
   the answer."
2. Do "pending dues" mean every unpaid invoice, or only the overdue ones? — **Finance (Hazeem)**.
   Tagged: blocks OP-08 phase 2 formula. Same mini-report as above. The credit-limit research
   (`analysis/research/zoho-credit-limit.md` §e) recommends **all unpaid invoices** as the default
   — Zoho's own `outstanding_receivable_amount` is already that figure — but this is still
   Finance's call to confirm, not decided here.
3. Who is Hazeem's backup, so the credit-review step has continuity? — **Finance / GM Samitha**.
   Tagged: go-live only, not the build. No mini-report.
4. Any objection to the block-vs-hold decision being made by Finance/Hazeem alone, or does it need
   COO sign-off given it can stop a customer's order? — **COO**. Tagged: decision-authority check
   on question 1, no mini-report beyond the one above.

---

## OP-09 — Notifications

**Goal:** notify the next actor instantly on order creation or any state move — in-app + email,
which are the record; WhatsApp is an optional urgent alert only, never the system of record
(`CLAUDE.md §17.2` step 2, `plans/40...` §9).

**What the development must do:** add the `notifications` table decided in OP-01 (separate from
`outbox`, which stays the held Zoho write-back queue, per `BUILD-ORDER-2026-09-20.md` §6). Build
one sender for it — in-app (SSE, reusing the existing `server/services/sse.js`) plus email via
whatever SMTP account is provisioned. **Do not build any WhatsApp-sending capability** in this
step — the standing rule "never build anti-detection" for WhatsApp automation is explicit and
non-negotiable (`memory/hub-whatsapp-notifications.md`, `plans/40...` §9); if WhatsApp alerts are
approved later, they route through the already-paused, separately-scoped Hub WhatsApp project, not
a bespoke sender built here. Name a backup owner for the pipeline (a config value / on-call
contact, not code) so a silent failure has a human to page.

**Inputs:** `CLAUDE.md §17.2` step 2; `plans/40...` §9; `BUILD-ORDER-2026-09-20.md` §6;
`memory/hub-whatsapp-notifications.md` (the anti-detection rule).

**Outputs:** `notifications` table + sender; SSE delivery for in-app; email delivery once SMTP
exists; no WhatsApp code at all.

**Acceptance criteria:**
1. Every state transition in OP-03/OP-04's tested transition matrix produces exactly one
   notification row addressed to the correct next actor (a test asserts this per transition, not
   just for the happy path).
2. Email delivery is retried on transient failure and marked failed (not silently dropped) after a
   bounded number of retries, visible in Admin.
3. No code path sends, drafts, or stages a WhatsApp message.
4. A named backup owner exists in the on-call config before this ships (a checklist item, verified
   by whoever runs `release-captain`, not a test).

**Depends-on:** OP-03, OP-04.

**Estimated effort:** 1 week (assumes SMTP account is already provisioned — see ingredients; if
not, this step's calendar time extends but the work itself doesn't grow).

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
22–31 Dec 2026 (**FORCED**: later start; answer deadline moves to 8 Dec 2026). Sub-step — no
separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027**
(target 11 Feb).

**Ingredients list:** an SMTP account for the portal to send from (not yet provisioned,
`dashboard-state.md:7`); the `notifications` table decision from OP-01; a named backup owner for
the pipeline.

**Questions that must be answered first:**
- Provision an SMTP account (who owns it, what "From" address) — **IT (the user) / COO for budget
  if a paid service is needed**. Tagged: blocks OP-09 email delivery. No mini-report.
- Name a backup owner for the notification pipeline — **GM Samitha or COO**. Tagged: go-live
  checklist item, doesn't block the build. No mini-report.
- Is the existing WhatsApp order group repurposed for the (future, separately-scoped) urgent-alert
  channel, or a new one built (spec Q8) — **triage owner / GM Samitha**. Tagged: does not block
  OP-09 (no WhatsApp code is built here regardless); relevant only if/when that separate project
  resumes. No mini-report.

---

## OP-10 — Attachments and artwork

**Goal:** fully specced, build as written (`plans/40...` §10) — the one feature area in this
release with zero open questions, because getting any rule here wrong is a security finding, not a
style choice.

**What the development must do:** implement `POST /api/orders/:id/messages` and
`POST /api/jobs/:id/attachments` with multipart upload, allow-listed types checked by **magic
bytes**, not extension (PDF, PNG, JPEG, WebP, XLSX, DOCX, AI, PSD, CDR, ZIP — never SVG, HTML, XML
or any script type, spec §11). Only images and PDFs served inline; everything else forced
`attachment`. 25MB/file, 20 files/request, requester daily quotas (50 files / 200MB / 100 messages,
spec §6.3 `upload_quota`) → 429 past that. Random stored names, outside the web root, served only
through `GET /files/:id` after an auth + scope check. Implement the `portal_visible` matrix exactly
(spec §7.2.4): requester-uploaded or publicly-posted files visible to the requester; internal-note
files never visible to the requester, and GM/COO see public messages only, never internal notes or
their files.

**Inputs:** design spec §11 (Security), §7.2.4 (visibility matrix), §6.3 (`upload_quota`,
`attachments`); AC1.14, AC1.30, AC1.6.

**Outputs:** the upload/serve routes; the visibility matrix enforced server-side.

**Acceptance criteria (verbatim, spec §13):**
1. AC1.14: 26MB → 413; renamed `.exe` → 415; an SVG or HTML file (even renamed to `.png`) → 415;
   51st file or 101st message in a Colombo day → 429.
2. AC1.6: every cell of the §7.2.4 matrix checked in both directions on seeded data.
3. A direct request to a stored file's on-disk path (bypassing `/files/:id`) fails — files are
   outside the web root, verified by a test, not just code inspection.

**Depends-on:** OP-03.

**Estimated effort:** 1 week.

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
1–8 Jan 2027 (**FORCED**: later start only). Sub-step — no separate release; ships as part of
OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

**Ingredients list:** none — fully specced, no open questions.

**Questions that must be answered first:** none.

---

## ~~OP-11~~ — Zoho read-only sync (SPS) + master-data import — **REMOVED, 25 Sep 2026, later the same day**

**This step is removed from the order-portal track.** Its content ships **~10 weeks earlier**, as
`PD-05D` in the December dashboard track, because the December-live divisions (PSU, SHPS) need live
SPS Sales-Order data too, not just the portal — waiting for the portal's own Feb 2027 date would
have delayed the December demo (`01b-dated-schedule.md` §0.5, §4). The SH-side sync half (gated on
CEO SH Zoho admin access) is unaffected and stays under `OP-16`. The body below is kept **for
reference only** — read `dev/production-dashboard/02-process-steps.md` / `dev/01b-dated-schedule.md`
for `PD-05D`'s actual, current spec; do not build against this entry.

**Goal:** replace the one-off Release-0 import CLI's manual runs with the automatic, scheduled
read-only sync the spec's Release 1b addendum describes, plus import customer and item master data
so the order-submission form's pickers are backed by real data, not free text
(`BUILD-ORDER-2026-09-20.md` row 3, row 4's stub note: "SPS customer picker from the distinct
`cf_order_received_from` values; SH items from the 19 Sep snapshot").

**What the development must do:** extend the existing shared upsert functions
(`server/services/` — the same functions the import CLI already uses, per spec's "mirror tables
written only by the shared upsert functions" rule, `plans/40...` §12) into a scheduled sync with
its own SPS API call budget (an SPS self-client, read scopes only — admin action, not code).
Import customer master data (distinct `CF.Order Received from` values from the SPS mirror) and
item master data (from the 19 Sep SH snapshot, `/root/exports/zoho/native/2026-09-19/`) into
lookup tables the order-submission form's pickers read from, flagged where the data source is a
point-in-time snapshot rather than a live sync (so a stale item never looks live).

**Inputs:** `BUILD-ORDER-2026-09-20.md` rows 3–4; spec's Release 1b addendum note (§ referenced in
`plans/40...` §1); existing `server/services/facts.js`, `server/services/freshness.js`,
`server/services/mirror-report.js` (read before extending — reuse the freshness/capture-time
discipline already built, `plans/40...` §17 last bullet: "carry this same discipline — don't build
a second, simpler freshness rule").

**Outputs:** a scheduled sync job (SPS only — SH sync is OP-16's concern, blocked on SH admin);
customer/item lookup tables backing the order form's pickers; a freshness indicator reusing the
existing `captured_at` discipline.

**Acceptance criteria:**
1. The sync respects a stated call budget (a config value, tested that the sync never exceeds it
   in a single run).
2. Every mirror row it writes carries `captured_at`, and an older capture never overwrites a newer
   one — tested directly, per the existing rule (`plans/40...` §17).
3. The order-submission form's customer and item pickers are backed by the imported lookup tables,
   not free text, with a visible "as of [snapshot date]" flag on any data that isn't from a live
   sync.
4. `db-migration-guard` PASS on any new mirror table this step adds.

**Depends-on:** OP-02.

**Estimated effort:** 1.5 weeks.

**Dates:** none — this step no longer exists in the order-portal track. Its content is `PD-05D`,
build 28 Sep – 13 Oct 2026 (`01b-dated-schedule.md` §3).

**Ingredients list:** an SPS self-client with read scopes (admin action — the user has SmartPack
Zoho admin, `plans/40...` Files section / `BRIEF.md`); the 19 Sep SH snapshot files already on disk
(`/root/exports/zoho/native/2026-09-19/`).

**Questions that must be answered first:**
- Confirm the SPS self-client's read-scope list is sufficient for what this sync needs (sales
  orders, customers, items) — **IT (the user)**, since the user holds SPS Zoho admin. No
  mini-report; a five-minute confirmation.

---

## OP-12 — Portal Order No field enforcement

**Goal:** the fix already designed for the SH-SO linking problem (only ~17–18% of SPS orders
currently carry a usable SH SO reference, `plans/40...` §7) — a "Portal Order No" custom field on
the SH sales order, written by the portal's OR-number when Senuri saves the SO through the browser
helper, then read back automatically by the portal's sync.

**What the development must do:** two parts, one config-only, one code. **(a) Zoho-side
(config, not code, but the developer verifies it):** with the user's Zoho admin access, mark the
existing "Portal Order No" custom field mandatory in Zoho SH SO settings — today it is "text, not
mandatory" (`zoho-helper-userscript-spec.md:46,80`). This is the strongest enforcement and needs no
new code (`plans/40...` §7, recommendation 1). **(b) Portal-side (code, the actual build here):**
until SH admin sync access arrives, implement the fallback already designed — Senuri pastes the
Zoho SO number onto the portal order, and the portal validates it exists in the mirror
(`zoho-helper-userscript-spec.md §5b`, "way B"). **Never** implement "way C" (guessing the link
from customer + date + line match) — explicitly rejected, it links the wrong orders
(`plans/40...` §7, `BUILD-ORDER-2026-09-20.md`).

**Inputs:** `plans/40...` §7 in full; `zoho-helper-userscript-spec.md` §4, §5, §5b (draft, not
approved — read it, don't build the helper's other fields from it without the developer brief's
own scoping); `BUILD-ORDER-2026-09-20.md` floating-builds table, "SH fulfilment" row.

**Outputs:** the mandatory-field change in Zoho (config); the paste-and-validate fallback route and
UI on the portal side.

**Acceptance criteria:**
1. Zoho SH SO settings: "Portal Order No" is mandatory — verified by attempting to save an SH SO
   without it in a Zoho sandbox/test order and observing the block (a manual check the developer
   runs once, documented, not an automated test since it's Zoho-side).
2. A pasted SO number that doesn't exist in the mirror → 400 with a clear message; one that does →
   linked exactly as OP-05's `so_key` matching rule (reuse it, don't reimplement).
3. No code path implements "way C" (fuzzy matching by customer/date/line) anywhere in this step's
   diff — a code-review checklist item, not just a test.

**Depends-on:** OP-05, OP-07.

**Estimated effort:** 0.5 week.

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
11–13 Jan 2027 (**FORCED**: later start, but lands within 2 working days of the original 7 Jan
start — removing OP-11 (9 wd) almost exactly cancels the later start). Sub-step — no separate
release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target
11 Feb).

**Ingredients list:** Zoho admin access to the SH org's SO custom-field settings (the user has
this per `BRIEF.md`); the `zoho-helper-userscript-spec.md` draft, read but not built beyond this
step's own scope (the full helper page is a separate, floating build — see OP-16).

**Questions that must be answered first:**
- Will marking the field mandatory break any existing workflow for Senuri — any order type where
  she genuinely won't have a portal order number yet (a walk-in, a phone order predating the
  portal)? — **Sales coordinators / Senuri**, tagged (`plans/40...` §18): unblocks OP-12 acceptance
  criterion 1, no mini-report.

---

## OP-13 — Security hardening and redaction for Release 1

**Goal:** the release-specific items from spec §11 that don't fall inside any single feature step
above — auth, rate limits, CSRF, audit, and the GM/COO redaction rule applied to whatever
order-portal reporting exists by this point.

**What the development must do:** confirm (not re-decide) auth is scrypt N=2^15/r=8/p=1/64MiB,
256-bit session id stored only as its hash, `HttpOnly; Secure; SameSite=Strict`, 12h idle/7-day
absolute expiry (spec §5.2 — this is Release-0 code already built; this step audits it still holds
under Release-1 routes, it doesn't rebuild it). Add rate limits (10 login failures/username/15min,
100/IP/15min → 429) if any Release-1 route bypasses the existing limiter. Enforce CSRF (`Origin`
header equal to configured origin on every non-GET; a **missing** Origin also rejected — spec
finding 22) on every new Release-1 route. Verify server-side role checks on every new route (a
`requester`-only user gets 403 on every non-portal route — AC1.2). Apply the GM/COO redaction rule
(worker identity → "operator", `payload_json` never sent, minutes only as aggregates with ≥2
distinct workers or "—", spec §5.4) to whatever GM/COO order-portal view this release ships.

**Inputs:** design spec §11, §5.2–5.4; `plans/40...` §13; `LATER.md:47,55` (L24, L32 — the
Release-0 security re-audit items still open, several of which touch shared middleware this release
also uses, e.g. login-failure dedup, empty-env-value refusal).

**Outputs:** a security review pass on the full Release-1 diff, `security-auditor: PASS` recorded.

**Acceptance criteria:**
1. AC1.2: scope isolation — a requester sees only their own + team orders; a requester-only user
   gets 403 on every non-portal route; no job internals/prices/worker fields/internal messages
   leak, checked by a key/value scan on seeded data.
2. AC1.14, AC1.30 (cross-checked here, built in OP-10): still pass under this step's rate-limit and
   CSRF changes.
3. `security-auditor` returns `PASS` on the full Release-1 diff before it ships (spec §11: "reviews
   Release 0, Release 1... Release 5").
4. LATER.md L24 items (a)–(d) closed or explicitly deferred with a reason, since they touch
   shared auth/audit code this release depends on.

**Depends-on:** OP-03, OP-04, OP-05, OP-06, OP-07, OP-08, OP-09, OP-10, OP-12 (every step that adds
a Release-1 route this step must audit; OP-11 is removed from this list — it added a sync job, not
a route, and has in any case moved to `PD-05D` — see `prompts/OP-13-security-hardening.md`).

**Estimated effort:** 0.5 week.

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`):** build
15–19 Jan 2027 (**FORCED**: lands within 2 working days of the original 12 Jan start). Sub-step —
no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb
2027** (target 11 Feb).

**Ingredients list:** none new — this step audits and closes gaps in code already built by earlier
steps in this release.

**Questions that must be answered first:** none.

---

## OP-14 — End-to-end smoke test and go-live readiness

**Goal:** prove the whole chain works together, and confirm the non-functional decisions this
release has been carrying as open (desk-first layout, English-only) are either settled or
explicitly deferred, before `release-captain` signs off.

**What the development must do:** write and run the one Playwright test that proves the whole
Release-1 chain end to end (AC1.27): requester submits → triage accepts → coordinator sets job no,
links pending SO, attaches docs, sends to production → import+sweep resolve the SO → requester sees
"In production," live via SSE. Run this early as a smoke test during development, not only at the
end (`plans/40...` §15: "run it early as a smoke test, not last" — this step is where it's made
part of CI, having likely already been used informally throughout OP-03–OP-11). Apply the
list-view performance discipline already required for `GET /api/jobs` (keyset-paged chunks of
≤500, no single sync DB call blocking the event loop over 100ms, spec §8.2/AC1.28) to any new
order-list endpoint this release added. Confirm English-only (or the i18n decision from OP-01) and
desk-first layout (no phone-first redesign, spec/brief §14) are both reflected in the actual UI,
not just assumed.

**Inputs:** spec §13 AC1.27, §8.2/AC1.28; `plans/40...` §14, §15.

**Outputs:** the AC1.27 Playwright test in CI; a go-live checklist confirming every open item in
this file that's tagged "blocks go-live only" (not "blocks the build") has an owner and a date, even
if the date is "before go-live" rather than a calendar date.

**Acceptance criteria:**
1. AC1.27 passes in CI, not just once locally.
2. Any new order-list endpoint answers in line with the AC1.28 discipline (measured, not assumed).
3. A go-live checklist exists naming every unresolved "blocks go-live" item from OP-01–OP-13 with
   an owner.

**Depends-on:** OP-13.

**Estimated effort:** 0.5 week.

**Ingredients list:** none new.

**Questions that must be answered first:** none beyond the go-live-only items already listed under
earlier steps (collected here, not new).

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row
`OP-14`):** build 20–25 Jan 2027 (**FORCED**: later start, propagated from OP-01's ~3-week shift
minus OP-11's 9-wd removal); internal IT test 26–28 Jan 2027; UAT 29 Jan – 12 Feb 2027 (2 weeks —
Ishan, Umanda, Hazeem, Samitha — longer than a typical UAT window because this release includes the
automated credit check, money); **full release 15 Feb 2027, Release 1 + 1b live for everyone** (2
working days after the original 11 Feb 2027 target — a side-effect of the December-track forced
changes above, not a new decision; `01b-dated-schedule.md` §4 explains how to close the gap if the
exact date must be held).

---

## OP-15 — Key-customer call-off order type (wiring only — do not build the feature yet)

**Goal:** make the `order_type` field extensible enough that a future "against buffer stock" order
type is a lookup-table INSERT later, not a schema change — and stop there. This is a **2027
production-plan design, not yet a portal feature** (`plans/40...` §11): "link it, don't build it
yet, until the plan is agreed."

**What the development must do:** confirm (from OP-01/OP-02's lookup-table conversion of
`order_type`) that adding a new value is already just a seeded INSERT, needing no migration beyond
what OP-02 already built. Do **not** add a `buffer_stock` value, do **not** build any draw-down
logic against a stock buffer that doesn't exist yet (the stock system for Abdullah/Ilham is a
paused, separately-scoped project — `plans/40...` §11, `memory/stock-system-key-customers.md`).

**Inputs:** `plans/40...` §11 in full; `11-production-plan-2027.md` §3–4 (the MTS/MTO proposal and
the six named candidate items: SH-8oz S/Wall Paper Cup 73.6% margin, Chefs Choice Cling Film
55.5%/52.5%, ST-Cling Film 37.5%, SP-Chicken Bucket+Lid 21.6%, Taco Bell's 5 standing items, Paper
White Straw 68.0%); `13-business-growth-2027.md` §3 (the blanket/call-off contract proposal).

**Outputs:** nothing shippable — this "step" is a confirmation that OP-01/OP-02 already leaves the
door open, plus a one-paragraph note in the spec pointing at where the future value would be added.

**Acceptance criteria:**
1. A written confirmation (in the spec or a short note) that `order_type` is a lookup table, not a
   CHECK enum, by the time OP-02 ships — no further criterion, because no feature code exists yet.

**Depends-on:** OP-02 (where `order_type`'s lookup-table conversion is actually built, not OP-07,
which tags an unrelated column).

**Estimated effort:** 0.25 week (a confirmation + a note, not a feature).

**Dates:** not scheduled (`dev/01b-dated-schedule.md` row `PD-21 / OP-15`, "NOT SCHEDULED") — waits on the safety-stock/MTS policy sign-off and the paused key-customer stock-system project, both outside this document's control.

**Ingredients list:** the safety-stock policy signed off by Samitha and Finance
(`11-production-plan-2027.md` §4, "not yet agreed") — required before this step becomes an actual
feature, not before this step's confirmation-only work.

**Questions that must be answered first — this step stays wiring-only until these are answered:**
- Sign off the safety-stock / MTS buffer policy, or say it needs more numbers first — **GM
  Samitha**, tagged (`plans/40...` §18): this is what turns OP-15 from a note into a real feature
  step (not yet numbered, would become OP-17+). **Needs a mini-report: yes** — the safety-stock
  policy itself, with the six candidate items and their margins, is worth a short paper before the
  meeting, not a verbal ask.
- Confirm the paused stock-system project (Abdullah/Ilham) is ready to resume — **COO** (it's the
  one who paused it, per `memory/stock-system-key-customers.md`). Tagged: same gate as above.

---

## OP-16 — SH-side triage and fulfilment (floating; not scheduled, listed for completeness)

**Goal:** the SH half of the order lifecycle — Senuri's SO-approval workflow, the helper page, "way
A" automatic linking once SH sync exists, ex-stock dispatch (Saman's team checks, Pasindu's
packaging slip) — explicitly a **floating build** in `BUILD-ORDER-2026-09-20.md`'s own terms: "SH
fulfilment... starts the moment SH admin rights arrive," not on the SPS critical path.

**What the development must do, once unblocked:** its own spec delta (not written yet, per
`plans/40...` §11 and the SH fulfilment row of `BUILD-ORDER-2026-09-20.md`'s floating-builds
table); SH sync (a much larger volume than SPS, needing its own call budget,
`BUILD-ORDER-2026-09-20.md`); the browser helper/userscript for Senuri's SO-save workflow
(`zoho-helper-userscript-spec.md`, still draft); "way A" linking via the now-mandatory Portal Order
No field (OP-12 built the fallback "way B" already; this step is what makes way B obsolete for new
orders once sync exists). **None of this starts until SH admin access is granted** — the
`ithelp@` login sees only Head Office today (`plans/40...` §6).

**Inputs:** `LATER.md:50` (L27, "brainstormed, not specced"); `BUILD-ORDER-2026-09-20.md`
floating-builds table, "SH fulfilment" and "Zoho sync, SH" rows; `zoho-helper-userscript-spec.md`
(draft, unapproved); `/root/Operation Food Packaging Division — Team Structure.pdf` (team
structure referenced by L27, not read for this brief — read it before scoping this step for real).

**Outputs:** not yet defined — this step is a placeholder in the sequence until its own spec delta
exists. Do not start code against this entry as written; it is not detailed enough to build from
(deliberately — that detail is a future step's job, once SH admin access lands and a spec delta is
written per the same OP-01 pattern).

**Acceptance criteria:** none yet — write these as part of this step's own future spec delta, in
the same style as every other step, once it is unblocked.

**Depends-on:** OP-04 (SH-side triage reuses the same triage mechanism); external: SH Zoho admin
access.

**Estimated effort:** 1.5 weeks, once scoped (a rough order-of-magnitude estimate only, based on
its similarity to OP-04+OP-05+OP-12 combined — **not a committed number**, this step needs its own
spec delta before any real estimate is possible).

**Dates:** not scheduled (`dev/01b-dated-schedule.md` row `OP-16`, "NOT SCHEDULED") — waits on the CEO granting SH Zoho admin access across all 10 locations.

**Ingredients list:** SH admin access (all 10 locations, not just Head Office); the team-structure
PDF read; the userscript spec reviewed and approved (currently draft); a decision on custom-item
entry and ex-stock/customised routing (`LATER.md:50`, "gaps agreed" lists some of these already
resolved — re-verify before starting, this brief did not re-check them).

**Questions that must be answered first:**
- Grant SH Zoho admin access covering all 10 locations — **CEO (SH is the CEO's company) / SH
  Rizwan**, tagged (`plans/40...` §6, `LATER.md:50`): blocks this entire step. **Needs a
  mini-report: yes** — the access gap and what it blocks (this step, OP-07's "unverified" flags,
  OP-11's SH-side equivalent) is worth stating once, clearly, since it recurs across three parts of
  this project.
- Is Senuri willing to triage SH-side orders in the new portal (same question as OP-04, restated
  here because it also gates this step's helper workflow) — **Sales coordinators / Senuri**. No
  mini-report beyond OP-04's.

---

## Summary table

| ID | Title | Weeks | Depends on |
|---|---|---:|---|
| OP-01 | Spec delta "Release 1 v2" (non-credit, **non-MFA**) | 0.5 | — |
| OP-02 | Additive schema migration (portal half) | 1 | OP-01 |
| OP-03 | Order submission and core lifecycle | 1.5 | OP-02 |
| OP-04 | Triage workspace | 1 | OP-03 |
| OP-05 | SPS ↔ Zoho SO linking (portal-accepted orders only) | 1 | OP-03 |
| OP-06 | Job number assignment | 0.5 | OP-04 |
| OP-07 | Company (SPS/SH) + SH-location tagging | 0.5 | OP-02, OP-03 |
| OP-08 | Credit check (spec delta + build, gated) | 1 | OP-03 |
| OP-09 | Notifications | 1 | OP-03, OP-04 |
| OP-10 | Attachments and artwork | 1 | OP-03 |
| ~~OP-11~~ | ~~Zoho read-only sync (SPS) + master data~~ **REMOVED — see `PD-05D`** | — | — |
| OP-12 | Portal Order No field enforcement | 0.5 | OP-05, OP-07 |
| OP-13 | Security hardening and redaction | 0.5 | OP-03–OP-12 |
| OP-14 | End-to-end smoke test and go-live readiness | 0.5 | OP-13 |
| OP-15 | Call-off order type — wiring only, not built | 0.25 | OP-02 |
| OP-16 | SH-side triage and fulfilment — floating, not scheduled (now also carries OP-11's old SH-side sync gate) | ~1.5 (rough) | OP-04, external SH admin |

**OP-01 → OP-14 total: ~12.0 developer-weeks as originally scoped; ~10.5 now OP-11 (1.5 weeks) has
moved to `PD-05D`.** OP-15 (0.25 week, wiring only) and OP-16 (~1.5 weeks, unscoped) sit outside
that total because neither is a committed build yet.

**Steps needing a separate mini-report before the meeting:** OP-08 (credit check — two questions
remaining, one memo to Hazeem, `plans/40...` §18 already drafts the ask; the data-source question
is DECIDED, 25 Sep 2026); OP-15 (safety-stock/MTS policy paper
for Samitha, with the six candidate items and margins); OP-16 (the SH admin access gap, stated once
since it blocks three parts of this project).
