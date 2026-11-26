# Codemap: production dashboard, Release 0 as a foundation for the manager-preview build (28 Sep 2026)

Read-only mapping. Repo: `/root/dev/production-dashboard`, HEAD `b0cd339` (not deployed, not pushed). No code changed to produce this map.

Written for: PD-05D (Zoho sync, absorbed job-creation/job-page/handovers) and PD-06/PD-04D (managers' job list), against the 28 Sep user decisions in `/root/Project Management/reports/2026-09-27-sps-sh-inventory-analysis/work/DECISIONS.md` and the plan `/root/Project Management/reports/2026-09-28-role-based-scope/PLAN-MANAGER-FIRST.md`.

---

## 1. What Release 0 already provides (reusable as-is)

**Auth / sessions / roles**
- Session cookie auth, scrypt password hashing, must-reset flow: `server/auth/sessions.js`, `server/auth/password.js`, `server/auth/middleware.js`.
- `requireAuth`, `requireRole(...roles)` middleware (`server/auth/middleware.js:36-43`) — generic role gate, ready to protect a new `/api/jobs*` router with `requireRole('manager','gm','admin')` etc.
- Roles are a JSON array on `users.roles` (`server/db/migrations/001-schema.sql:93`); the UI's known role vocabulary is `web/src/admin/Users.tsx:10` (`requester, triage, coordinator, manager, stores, invoicing, approver_stores, approver_invoicing, gm, coo, analyst, admin`) — `manager` and `gm` already exist as role strings, `coo`/`analyst` too.
- **Manager ↔ division assignment already has a table and admin UI**: `division_pairs` (`001-schema.sql:115-119`, one row per division/manager/coordinator pair, `UNIQUE(division_code, manager_user_id, coordinator_user_id)`), CRUD at `server/routes/admin-config.js:244-276`, UI at `web/src/admin/Divisions.tsx` (manager dropdown filtered to users with the `manager` role, `Divisions.tsx:96`). This is the natural place to seed Ishan/Mubeena/Ranga/Samitha against their divisions — **no schema change needed for the mapping itself.**
- No code currently *reads* `division_pairs` to scope what a manager sees (confirmed by grep — only the admin CRUD writes/reads it, `server/routes/admin-config.js:83,246,253,268,273,276`). Scoping a manager's job list to their divisions is new work, but the source-of-truth table exists.

**Schema — mirror tables (`server/db/migrations/001-schema.sql`)**
All written only by `cli/import` (never by the sync-to-be-built directly — see §2):
| Table | Grain | Key columns | Line |
|---|---|---|---|
| `zoho_so_headers` | one row per SO | `cf_job_no`, `cf_order_received_from`, `cf_manufacturing_division`, `cf_order_type`, `cf_job_nature`, `cf_sh_sales_order_ref`, status/qty fields | :4-14 |
| `zoho_so_lines` | one row per SO line | `item_name`, `sku`, `quantity_ordered/packed/invoiced/cancelled`, `rate_cents`, `amount_cents` — **no CF.\* custom fields at all** | :15-21 |
| `zoho_so_line_sets` | one row per SO | line count / capture bookkeeping for the xlsx line-replace logic | :23-26 |
| `zoho_bundles` | one row per bundle | `so_key` (derived from `reference_number`, e.g. `JOBORDER-xxxxx`), `composite_item_name`, `status` | :27-33 |
| `zoho_package_lines`, `zoho_shipment_lines`, `zoho_invoices`, `zoho_picklists` + `zoho_picklist_sos`, `zoho_items` | linked to `so_number` (whole SO), not to a line | :34-71 |
| `zoho_so_facts` | **one row per (org, so_number, stage_id)** — the materialised "stage N done at T" fact the job page/list reads | :72-76 |
| `zoho_import_runs` | one row per import batch, `changed_so_numbers` JSON, `full_list` flag, freshness bookkeeping | :77-87 |

**Stage-detection engine**
- `server/services/facts.js` computes `zoho_so_facts` from six SQL rules keyed on `so_number` (stages 4 SO, 5 bundle via `so_key`, 6 picklist, 7 package, 8 shipment, 10 invoice) — `facts.js:3-17`. Called after every import batch (`cli/import/run.js:83,109`) and rebuildable in bulk (`facts.js:55-69`). **All rules operate at SO level, not SO-line level** — confirmed no `line_no` anywhere in `RULES`.
- `server/services/freshness.js` gates "shipped" data as fresh/stale from `zoho_import_runs` (`shippedFresh`, :6-14) and gives per-org "bundles data age" (:22-25). This is the freshness-gating logic the manager plan (`PLAN-MANAGER-FIRST.md` line 19) explicitly reuses.

**Jobs / people / audit domain (all in 001, already migrated)**
- `jobs` (`001-schema.sql:146-155`): `job_no` **nullable**, `division_code`, `org` default `'SPS'`, `order_id` nullable FK to a portal `orders` row, entered_* fields, `created_by`. Designed for a job **born manually** (coordinator/portal), not auto-derived from a Zoho SO line.
- `job_so_links` (`:156-161`, append-only): links a job to **a whole `salesorder_number`**, action `link_pending|link|unlink` — **no `line_no` column.** One job ↔ one SO (or none), never one job ↔ one line.
- `job_status_events`, `job_assignment_events` (uses `division_pairs.id`), `manual_stage_events` (stages 1,2,3,9,11 only — the four Zoho can't see, plus inventory adjustment), `stage_overrides` (stages 4,5,6,7,8,10 — manual force/clear of Zoho-detected stages), `handovers`, `blockers`, `output_entries`, `outbox` (write-back queue, permanently `state='held'`, :292-295) — all exist, all append-only where the spec requires it (guard triggers :303-340).
- `server/services/sweep.js`: on a timer (`startSweepTimer`, no external calls — it only re-reads local mirror tables), resolves `link_pending` job↔SO links once the SO header lands (`resolvePendingLink`) and re-matches Stores/ITN reference numbers (`rematchReferences`). This is pure local bookkeeping, not a Zoho poller.

**UI shell**
- React 19 + Vite + TS + Tailwind + shadcn/ui (`web/src`), React Router, TanStack Query (`web/src/lib/api.ts`).
- Only admin screens exist: Users, Teams, Divisions, Calendar, ListEditor (reason codes/reject reasons/order-type aliases), Imports, Audit (`web/src/App.tsx:1-13,29-40`).
- **Non-admin logged-in users see a stub**: `App.tsx:20-26` — `Home()` renders "Your workspace arrives in the next release" for anyone without the `admin` role. There is no manager route, no job list page, no job page component anywhere in `web/src`.
- `server/routes/index.js:6-8` registers exactly four routers: `adminImportRoutes`, `adminUserRoutes`, `eventRoutes` (SSE), `adminConfigRoutes`. **No `/api/jobs` router exists.**

**Tests / deploy runbook**
- 143 tests (`test/*.test.js` + `test/e2e/*.spec.js`), `npm test` / `npm run test:e2e` (`package.json:6-9`).
- Runbook: `docs/runbook-release-0.md` — private-deploy steps, not yet executed (repo not pushed, `git status` shows no remote push).

---

## 2. What does NOT exist yet (must be built for "AUTOMATIC read-only Zoho sync from day one")

- **No live Zoho API client anywhere in the codebase.** The only Zoho-facing code is:
  - `cli/import-zoho.js` (31 lines) + `cli/import/run.js` — a **manual CLI** that reads **already-downloaded files** (`.xlsx` backfill exports or `.json` "pull" captures) from a local directory (`--dir`) and upserts them. It never makes an HTTP request itself.
  - `tools/zoho-pull-snippet.js` — a **browser-console script**, pasted by a signed-in human into a Zoho Inventory tab, that calls Zoho's own web endpoints with the browser's session cookie (`X-ZCSRF-TOKEN`, `credentials:'include'`) and downloads JSON files (`zoho-pull-snippet.js:1-4,31-69`). Manual, session-cookie-based, not OAuth, not scheduled.
- **No OAuth config anywhere.** `.env.example` (`/root/dev/production-dashboard/.env.example`) has no `ZOHO_CLIENT_ID`/`ZOHO_CLIENT_SECRET`/`ZOHO_REFRESH_TOKEN`/similar; `server/config.js:22-45` (`loadConfig`) reads no Zoho credentials at all. `LATER.md` items L7/L19 (`/root/Production Dashboard/LATER.md`) record this explicitly: "Zoho self-client automatic sync... needed before Release 1b" — not built.
- **No scheduler/cron dependency.** `package.json` has no `node-cron` or similar; the only interval timer in the codebase is `startSweepTimer` (`server/services/sweep.js`, bottom), which re-processes **already-imported** rows every `SWEEP_INTERVAL_MS` — it makes zero external calls.
- **No `/api/jobs*` routes, no job list/job page UI, no manager workspace** — see §1 above. `PROJECT-MEMORY.md` (25 Sep) independently confirms: "Release 1b Zoho-sync addendum: **Not written**" and "December spec delta... **Not written**" (`/root/Project Management/reports/2026-09-25-sps-business-plan/projects/production-dashboard/PROJECT-MEMORY.md`, §2 table).
- **PD-05 and PD-06 prompts are specs to build, not built code.** PD-05 (`.../dev/production-dashboard/prompts/PD-05-release-1b-zoho-sync.md:1-79`) scopes "the sync module: GET requests only, read-only OAuth scopes" as new work, reusing `cli/import-zoho.js`'s upsert functions (line 30-31) — it explicitly is not yet a live sync. PD-06 (`.../PD-06-release-2-managers.md:1-83`) scopes the manager workspace (Today/My jobs/Incoming/Blocked/Floor entries/Reports tabs, 13 ACs) as new work against Release 0's schema, "No schema change expected."

## 3. What must change for "jobs auto-created from SPS SO lines"

This is the sharpest divergence between the 28 Sep decision and what Release 0 built:

- **Decision (28 Sep, `DECISIONS.md` line 21):** "one job = one SPS sales-order line (with its job number)... clicking a sales order shows every item on it with its own progress, even items in other divisions."
- **What's built:** `jobs` is a manually-created "file" (`001-schema.sql:146-155`) linked, via `job_so_links`, to **one whole `salesorder_number`** (`:156-161`, no `line_no`). The design spec itself says stage-detection facts are "materialised per SO" as the one shared implementation for both list and job-page reads (`/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md:347`). Everything downstream — `zoho_so_facts` (one row per `(org, so_number, stage_id)`, `001-schema.sql:72-76`), `facts.js`'s six rules (keyed on `so_number` only), `freshness.js`'s `shippedFresh`/`shippedState` — assumes **one document set per whole SO**, not per line.
- **The custom fields the new model needs (`CF.Job No`, `CF.Manufacturing Division`, `CF.Order Received from`) are captured only at header level today.** `zoho_so_lines` (`001-schema.sql:15-21`) and the line import spec (`config/zoho-columns.json`'s `"so_xlsx"` block, lines 2-33) carry `item_name`, `sku`, quantities and rate/amount — **no `cf_*` columns at all**. If a real SO can contain lines belonging to different divisions (which "shows every item on it with its own progress, even items in other divisions" implies), the current schema has no field to say which division or job number a given *line* belongs to — that only exists on the header row, i.e. one value for the whole SO.
- **Consequence:** building "one job per SO line" is not a matter of wiring a new UI onto Release 0's tables. It needs: (a) a line-level capture of `CF.Job No` / `CF.Manufacturing Division` (new column(s) on `zoho_so_lines`, or a new mirror table, or evidence from Zoho that these fields are in fact SO-level only, not line-level, in which case the "different divisions on one SO" scenario can't happen and the decision's wording needs the user's confirmation); and (b) either a new per-line stage/fact model, or an explicit decision that stage 5-10 detection stays SO-level (all lines on an SO show the same document strip) while only stages 1-3/9/11 (manual) become line-scoped. This is a schema and spec question for `db-migration-guard` and `plan-critic`, not an implementation detail.

## 4. Division → manager modelling

- `divisions` (`001-schema.sql:103-108`): code/name/active/provisional/`floor_live`, no manager reference on the row itself.
- `division_pairs` (`:115-119`): **many-to-many** table, one row per (division, manager, coordinator) pair, `active` flag — this is deliberate (spec/CLAUDE.md §5.3: "Offset routing is a runtime decision... manager and coordinator belong on the job, not the division"). Ishan covering PSU/Offset/Packpro/RWU, and OPD being shared between Ishan and Ranga, both fit this model directly: two active `division_pairs` rows for `OPD` (one with Ishan, one with Ranga).
- Seeded divisions (`002-seed.sql:5-10`): `OPD, SHPS, PSU, RWU, MOBA, MOBA_P, FPP, CPU, PACKPRO, PCU, PCLU, DPU, PPU, CWU` — all 4 named managers' divisions exist already (Screen Printing = `SHPS`, Packpro = `PACKPRO`, provisional flag on several). **No `division_pairs` rows are seeded** (002-seed.sql comment line 1: "Pairs are NOT seeded (created by the admin at go-live)") — Ishan/Mubeena/Ranga/Samitha's pairings must be entered via the existing admin UI (`web/src/admin/Divisions.tsx`) once their user accounts exist, or via a new migration/seed row if the pairing should ship as fixed config instead of admin-editable data (open choice, not yet decided in any file read).
- Samitha (GM) is described as "all divisions, view only" (`DECISIONS.md` line 22) — the `gm` role string exists (`Users.tsx:10`) but nothing in `division_pairs` or `requireRole` today expresses "sees everything read-only across all divisions"; that's new authorization logic on top of the existing `requireRole` primitive.

## 5. What the sync needs from the user

- A **Zoho API self-client (OAuth)** for the SPS org, created by the Zoho admin (the user) in the Zoho API console — referenced as available in PD-05 ("SPS self-client is already available to IT-as-admin", `PD-05-release-1b-zoho-sync.md:17`) but **no client ID/secret currently exists in this repo or its `.env.example`** — must be created and its secrets placed in a server env file only (never chat/git), per `PLAN-MANAGER-FIRST.md` line 52 and `Production Dashboard/CLAUDE.md`'s "no secrets in source" rule.
- **Read-only OAuth scopes only** — PD-05 requires this enforced by "a static test on the OAuth scopes" (`PD-05-...md:49`), not yet written since the sync module doesn't exist.
- **API budget**: `Production Dashboard/CLAUDE.md` §4 table — 1,000 calls/day, 100/min hard cap, ~415/day working budget for SPS (24 token refresh + ~320 delta poll + ~20 nightly reconcile + ~50 manual refresh). PD-05 requires instrumenting and logging actual call counts, not assuming (`PD-05-...md:52-53,76-79`). The computed task's own text flags this budget assumption needs re-confirming against the real Zoho plan tier — unverified in every file read during this mapping.
- A full-list SO-header pull **at least once per working day** to keep `shippedFresh` true (`PD-05-...md:36`, `freshness.js:6-14`).

## 6. Divergence and hazards found

- **Two Zoho ingestion paths already coexist and are about to become three.** (1) xlsx backfill via `cli/import-zoho.js`, (2) browser-console JSON pull (`tools/zoho-pull-snippet.js`) fed into the same CLI, (3) the not-yet-built live OAuth sync (PD-05). All three are meant to converge on the same `upsertGuarded`/`MODULE_HANDLERS` functions (`cli/import/upsert.js`) — PD-05 explicitly requires reusing them rather than writing a fourth path (`PD-05-...md:30-31,50-51`). Confirm this discipline is followed when PD-05 is built; a fourth ad hoc writer to `zoho_*` tables is the highest-value thing to catch in that code review.
- **SO-level vs line-level granularity mismatch** (detailed in §3) is the central open hazard for the manager-preview build — it affects schema, the facts engine, and the UI's "every item with its own progress" requirement simultaneously.
- **`job_so_links` and `zoho_so_facts` were designed around "one job = one manually-created file, optionally linked to one whole SO"** (spec-confirmed, `.../2026-09-17-production-dashboard-design.md:347`), which is the opposite creation direction from "jobs auto-created from SO lines." PD-05's own scope note calls out that its "New file (direct)" screen is **manual entry, no automatic SO-import job creation** (`PD-05-...md:9-11`, citing `01c-dashboard-december-feasibility.md` §1 option 4 as "the recommended low-risk choice for December"). That recommendation directly conflicts with the 28 Sep decision that jobs come from SO lines "automatically... nobody has to type them in" (`PLAN-MANAGER-FIRST.md` line 24). This conflict has not been resolved in any file read during this mapping — flag to `spec-writer`/`plan-critic` before implementation starts.
- **`output_entries.division_code` is not FK-tied to its job's division for existing rows** (pre-003 rows only; 003 added a guard for new inserts) — `db-migration-guard` memory, `.claude/agent-memory/db-migration-guard/production-dashboard-schema.md:16`. Not relevant to a read-only manager preview (no output entries written), but relevant the moment `PD-0810D` (write-heavy) starts.
- **`recursive_triggers` must be ON before any release writes output rows** (`server/db/open.js` — not yet verified landed; flagged as a blocker by `PD-06-...md:35-36,81-83` and `LATER.md` L35). Read-only manager preview doesn't need this, but don't let it slip past that gate.
- **No route currently checks `division_pairs` at all** — building the manager scoping query is net-new code with no existing pattern to imitate beyond the admin CRUD reads.
- **`.claude/` and `CLAUDE.md` are untracked in the dev repo** (`git status` — `.claude/`, `CLAUDE.md` untracked) — not itself a hazard, but means agent memory files there won't survive a clean clone/push unless committed deliberately.

## 7. Unverified

- Whether Zoho's `CF.Manufacturing Division` / `CF.Job No` custom fields are genuinely capturable at the sales-order-**line** level via the API (vs. header-only, as currently mirrored) — not checked against live Zoho in this mapping; the computed task's own "known Zoho facts" paragraph describes them as line-level ("SO lines carry... CF.Manufacturing Division, CF.Job No") but the current import code and schema only ever captured them at header level, so this needs a live-API check before committing to a line-level schema change.
- The real Zoho OAuth daily-call quota for SPS (self-client / API console tier) — `Production Dashboard/CLAUDE.md` §4's ~1,000/day figure is stated as a plan assumption, not verified against the actual current Zoho plan; PD-05's stop condition depends on it.
- Whether `division_pairs` should be seeded as fixed migration data or entered once via the existing admin UI for Ishan/Mubeena/Ranga/Samitha — no decision found in any file read.
- Whether Samitha's GM "all divisions, view-only" access should be a new role check, a synthetic `division_pairs` row per division, or a dedicated `/api/jobs?all=1` gm-only endpoint — no design found.
