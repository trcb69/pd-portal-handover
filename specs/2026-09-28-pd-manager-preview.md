# PD manager preview: managers' job list with its documentation strip, fed by a read-only Zoho sync (SPS)

Spec delta on top of Release 0 (`/root/dev/production-dashboard`, HEAD `b0cd339`). Parent spec: `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` (Rev 7.3). Where this delta and the parent disagree, this delta wins **for the preview only**. Written 28 Sep 2026 by spec-writer. **Rev 11** (29 Sep): ten corrections and missing sentences found by the second test slice (58 failing tests plus 5 gated to-dos; see "Revision 11 changes"); no new mechanism. **Rev 10** (29 Sep): corrections found by `test-author` writing 117 failing tests against Rev 9 (five wrong or ambiguous acceptance-criteria texts and two design sentences; see "Revision 10 changes"); no structural change. **Rev 9** (29 Sep): plan-critic round 9 APPROVED Rev 8; Rev 9 carries its three required edits (AC97(a) made consistent, the recovery-reset daily-cap hole closed, two AC97 fixture facts) and five one-liners (see "Revision 9 changes"). Test-author may start on the criteria round 9 cleared. **Rev 8** (29 Sep): plan-critic round 8 APPROVED Rev 7; Rev 8 carries its five required pre-implementer edits and the lead's per-SO outage guard with an automatic recovery reset (see "Revision 8 changes"). **Rev 7** (29 Sep): answered plan-critic round 7, which blocked Rev 6 (B1-B3, N1-N10; see "Revision 7 changes"); all three blocking findings are answered in the body sections they name. **Rev 6** (29 Sep): answered plan-critic round 5 (BLOCK: B1, B2, N1-N6) and plan-critic round 6 (BLOCK: B1-B6, N1-N10; round 6 confirms round 5's B1, B2 and N1-N6 and raises round-5 N1 to blocking B6). All six blocking findings are answered in the body sections they name, and every non-blocking finding is applied or declined with a reason in "Revision 6 changes". The human decided Q3 and Q10 on 29 Sep (see "Answered questions"). Rev 5 (28 Sep) was the lead design decision "two-level freshness"; Rev 4 fixed round 3, Rev 3 fixed round 2, Rev 2 fixed round 1. All nine critics' text is kept at the end. Status: **NEEDS-INFO** (Q1 and Q2 are still open; see the open questions). One lead decision is pending but does not block the build (see "Pending lead decision"). Codemap: `2026-09-28-pd-manager-preview-codemap.md` (a Release 0 map; Rev 9 changes none of the code facts it records).

---

## Pending lead decision (does not block the build)

Waiting for a yes or no from the human, Abdul Hadhee. **Nothing in Rev 6 is designed around it, and the build does not wait for it.** If the answer is yes, it is a Rev 7 spec-writer pass, not an implementer decision.

**The alternative (plan-critic round 6, "simpler alternative considered"): take the daily header full list off the critical path.**
- Level 1 (§4) would stop requiring an `ok` header full list within 50 h. It would be derived from the deltas only (`delta_stale`, `bundles_stale`).
- The header full list would run **weekly** (Sunday, next to the bundles full list) purely for the `missing_in_zoho` reconcile (§5.4). When that reconcile is overdue, the admin sync screen would say so; it would never blank the screen for every user.
- What it would delete or shrink:
  - **B5 goes away outright**: the 02:00 full list as a single point of failure, its first-cycle trigger, its same-night retry and its acceptance criterion (§5.2 "Full-list attempts" would apply to the bundles list only).
  - **B4 shrinks and the N8 nightly churn shrinks**: the nightly full list is what rewrites changed headers at 02:00 and puts them into the night P1 queue.
  - **About 43 calls a day**: the weekday steady total goes from 280 to 237 (Sunday from 340 to 297). Sunday would then have real headroom instead of landing exactly on the cap of 400 with the 60 margin (§5.5).
- What it would cost: a header quantity change that does not move `last_modified_time` would be picked up weekly instead of nightly. Round 6's view is that the P0 confirmation rule (§4, AC51) already covers that case.
- **Round 7's observation:** adopting it would invalidate AC84 and AC85 and part of AC94 (the 02:00 header full-list schedule, its retry and the go-live first-cycle header list). The decision is therefore needed **before test-author starts**, or those three ACs get written twice.
- **Needs: a yes or no from the human.**

**Also for the lead (raised by round-6 B1, not decided by the lead in Rev 5):** AC64's "exactly 5 requests over 3 days, one retry per 24 h in night slots only" is replaced by a per-SO backoff retry (§5.2 "Backoff retry") that heals by itself, plus an env-file reset lever. The first three attempts, the `sync_problem` state, the admin list and the "IT notified" meaning are unchanged. Both round 5 and round 6 blocked the 24 h night-only retry as irreversible at 2am; confirm the backoff, or say what to restore.

---

## Problem

Today SPS production managers (Ishan, Mubeena, Ranga) and the GM (Samitha) have no screen that lists the production jobs in their divisions or shows which Zoho documents exist for each job. They have to open Zoho, which shows every module and record to everyone. The result is documentation steps that are missed and nobody notices: a bundle that was never recorded, a package with no shipment, a shipment with no invoice. The dashboard code that exists (Release 0) has login, roles and the Zoho mirror tables, but a non-admin user who logs in sees a stub page. There is no live Zoho feed. The detection engine also works per whole sales order, not per line. The user decided on 28 Sep that the first thing to build and show is a read-only "My jobs" screen. One job = one SPS sales-order line. It is routed to the manager of that line's division, has a documentation strip, and is fed automatically from Zoho from day one. Zoho is never written to. For the fast first preview, a missing bundle is shown in the strip but not raised as a flag (lead decision, Rev 4; follow-up V7 decides whether the flag comes back). One sales order that Zoho cannot serve must never blank the screen for everyone (lead decision, Rev 5): sync health decides whether the screen is shown; each job's own data decides whether that job's flags are shown.

## Readings of the request (rule 1: ambiguity)

| # | Phrase | Readings | Assumed | Why |
|---|---|---|---|---|
| R1 | "one job = one SO line with its job number" | (a) one job per SO line; (b) one job per SO | (a) | The user chose it explicitly (`DECISIONS.md:21`). |
| R2 | "the manager of that item's division" | (a) the line's reporting tag `Division` (`tags[].tag_name="Division"`, e.g. `salesorders_since_2026-09-15.json:127-135`); (b) the SO header custom field `cf_manufacturing_division` (`:541`) | (a), with (b) as the fallback when the line has no tag | The two **disagree** in the sample: JOBORDER-08597 and -08592 have header `Paper Cup Unit (PCU)` but line tag `MOBA Unit` (`:2135/:2533`, `:4085/:4511`). RWU lines carry no tag (`:6003-6085`). Only (a) is per item. **Blocking question Q2.** Evidence now exists at `/root/Project Management/reports/2026-09-28-role-based-scope/evidence/Q2-division-conflict-example.md` (2 of 22 sampled lines disagree, 16 agree, 4 have no tag, all four RWU). Its recommendation is: line tag wins, header as fallback, plus a "division conflict" marker on the admin list. The human has **not confirmed** it, so Q2 stays open and blocking. |
| R3 | "its job number" | (a) the line's `project_name` (`:163`); (b) the header `cf_job_no` (`:535`) | (a), with (b) as the fallback | Per line, and equal to (b) in all 22 samples. |
| R4 | "lines without division or job no → admin unassigned list" | (a) such lines appear **only** on the admin list; (b) on the admin list **and** still in the manager's list, labelled | (b) for lines that have a division but no job number; (a) for lines with no resolvable division | Hiding real production work from its manager is the worse failure. A line with no division has no manager to show it to. **Recorded conflict (round-7 N6):** a line carrying two distinct Division tags gets `division_code` NULL (§5.2 "Line column map") and so is hidden from both managers, which is the outcome R4 calls the worse failure. Behaviour left as it is (no sample has such a line; the job is on the admin Unassigned list with the raw text). |
| R5 | "only jobs created or changed from go-live raise missing flags" (`PLAN-MANAGER-FIRST.md:20`) | (a) SO **created** on or after the cutoff; (b) created **or modified** on or after the cutoff | (a) | Under (b), any old SO touched by an invoice or package after go-live would start raising flags, which is the flood the critic warned about. |
| R6 | "every production job" | (a) every inventory line on an SPS SO; (b) only composite ("assembly") lines | (a), excluding non-inventory lines (`item_type != 'inventory'`, e.g. "Screen Charges", `scout-zoho-probe.md:32-33,53-55`) | Ex-stock lines are still work that the manager ships. Service lines are never shipped, so they are not jobs. |
| R7 | "Offset" in Ishan's list | the OPD division (`002-seed.sql:6`) | OPD, shared with Ranga | Matches the parent spec pairs, OPD {Ranga, Ishan} (`design.md:398`). |
| R8 | "automatic sync from day one" | (a) scheduled polling; (b) Zoho webhooks | (a) | Webhooks need a public endpoint and quota planning (`Production Dashboard/CLAUDE.md:63-64`), and they are not needed to meet the freshness target. |
| R9 | "every production job" vs. ~1,400 open SOs, 170 of them from 2024 (`scout-sps.md:72-74`) | (a) all open jobs count equally in the counters; (b) very old open jobs are shown but kept out of the counters and the default list | (b), with "legacy" = SO `order_date` more than 180 days before today (Colombo) | Otherwise "Past due" and "In production" are flooded on day one by stuck SOs (critic N3). Legacy jobs stay one click away ("Legacy open" filter). Non-blocking question Q12. |
| R10 | "sync problem — IT notified" (lead, Rev 5) | (a) the SO is listed on the admin "Sync problems" screen and one `error` log line is written; (b) a message (WhatsApp, email) is sent to IT | (a) | Notifications are a non-goal of the preview. The admin (IT) is the only person who acts on sync problems, and the admin screen plus the error log reach them without a new channel. |
| R11 | "open" SO for the sync scope (round-4 B2) | (a) the lead's formula `status NOT IN ('fulfilled','void','closed','draft') OR quantity_shipped < quantity OR quantity_invoiced < quantity`; (b) the same, but a `void` or `draft` SO is never open even when its quantities are short | (b) | Reconciles with the line-level `state` rule (§2), which makes every line of a void SO `cancelled`; under (a) every void SO (shipped 0 < ordered) would be fetched for nothing. Old drafts are not work in progress; a draft created after the cutoff is still loaded because it is flag-eligible (§5.2). |

---

## Current behaviour (with file:line evidence)

**App and access**
- A non-admin user who logs in sees a stub: "Your workspace arrives in the next release" (`web/src/App.tsx:19-26`). There is no manager route.
- Only four routers exist: admin-imports, admin-users, events and admin-config (`server/routes/index.js:6-8`). There is no `/api/jobs`. A health route exists (`server/routes/health.js:6`, mounted at `server/create-app.js:37`).
- `requireAuth` and `requireRole(...roles)` exist (`server/auth/middleware.js:34-43`). The role strings `manager` and `gm` exist (`web/src/admin/Users.tsx:10`).
- The manager↔division mapping table `division_pairs` exists (`001-schema.sql:115-119`) with admin CRUD (`server/routes/admin-config.js:240-277`). A pair **requires** an active user with the `coordinator` role (`admin-config.js:246`). No pairs are seeded (`002-seed.sql:1`). Nothing reads `division_pairs` to scope data.
- Working days: `working_weekdays` is seeded Mon–Fri `[1,2,3,4,5]` (`002-seed.sql:77`) and is editable by the admin through `PUT /api/admin/calendar` (`admin-config.js:392-401`); holidays through `POST/DELETE /api/admin/holidays` (`admin-config.js:406-426`). `server/services/calendar.js:2-5` reads both.

**Zoho data**
- There is no live Zoho client and no OAuth configuration: `server/config.js:28-49` reads no Zoho keys.
- Ingestion happens in only two ways, both manual:
  - the xlsx/json CLI (`cli/import/run.js`);
  - the browser cookie script (`tools/zoho-pull-snippet.js:8-12`), which pulls SO headers, bundles and invoices only.
- All mirror writes go through `upsertGuarded` / `MODULE_HANDLERS` (`cli/import/upsert.js:5-23,37-161`).
- `upsertGuarded` writes `rec[c] ?? null` for **every** listed field on update (`upsert.js:19-21`), so a record that lacks a field nulls it. It skips the write entirely when every listed field is unchanged (`upsert.js:18`), and on every write it sets `captured_at` to the capture time passed in (`upsert.js:8,19-21`).
- The `so_headers` handler always writes `source: 'pull'` (`upsert.js:42-43`).
- The `so_headers` column map lists `quantity_shipped` as a **required** key (`config/zoho-columns.json:96`); the CLI throws `missing required keys` when the **first** row lacks one of them: it checks only the first row's key names, not every row (`cli/import/run.js:86-89`). The SO **detail** object has no header `quantity_shipped`, only `total_quantity` (`salesorders_since_2026-09-15.json:70`).
- `zoho_so_lines` is keyed by an **ordinal** `line_no` taken from the xlsx row order (`001-schema.sql:15-21`, `upsert.js:69-72`). The xlsx importer trims lines above the new count (`upsert.js:77-87`). The table has no Zoho `line_item_id`, no division, no job number, no shipped or picked quantity.
- `zoho_bundles` has no `composite_item_id` and no `sync_state` (`001-schema.sql:27-32`), so a bundle cannot be matched to a line and a deleted bundle cannot be marked. The Zoho bundle list does carry `composite_item_id` and `last_modified_time` (`2026-09-19/sps/bundles_and_recent_sos.json:12,24`).
- Bundle field mapping: the Zoho list field is `quantity_to_bundle`, not `quantity` (`bundles_and_recent_sos.json:15`). The `bundles` column map maps it to `quantity` (`config/zoho-columns.json:126-138`, line `:134`). The `bundles` handler's field list is `reference_number, so_key, date, composite_item_name, quantity, status, created_at, modified_at` (`upsert.js:131-132`): no `composite_item_id`.
- The Zoho SO **list** row carries header-level `quantity`, `quantity_packed`, `quantity_shipped`, `quantity_invoiced`, `status`, `shipped_status`, `invoiced_status` and `last_modified_time` (`bundles_and_recent_sos.json:261798-261808`). `zoho_so_headers` already stores all of them (`001-schema.sql:4-14`, `upsert.js:25-29`). In the real rows the header `quantity_packed`, `quantity_shipped` and `quantity_invoiced` **include cancelled units**: JOBORDER-08602's list row has `quantity` 15496, `quantity_packed` 15496, `quantity_shipped` 1496 and `quantity_invoiced` 1496 (`bundles_and_recent_sos.json:261800-261803`), while its detail line has packed 14000, shipped 0, invoiced 0 and cancelled 1496 (`salesorders_since_2026-09-15.json:142-149`). The SO **detail** object has no header `quantity`, `quantity_packed`, `quantity_shipped` or `quantity_invoiced` at all, only `total_quantity` (`:70`), and its `cf_*` values exist only inside `custom_field_hash` (`:525-558`), with no top-level `cf_*` key.
- **The API `status` vocabulary differs from the xlsx export.** The API `status` field (mapped at `config/zoho-columns.json:103`) takes values such as `confirmed`, `partially_shipped`, `shipped`, `fulfilled` (e.g. `bundles_and_recent_sos.json:264214` `"status": "partially_shipped"` on an SO with `quantity` 1000, `quantity_shipped` 100, `quantity_invoiced` 100, `:264206-264214`; also `:267685,261808`; detail `salesorders_since_2026-09-15.json:8639,9397`). "Partially invoiced" is a value of a separate field, `invoiced_status` (`bundles_and_recent_sos.json:264211`, `salesorders_since_2026-09-15.json:54`). `partially_invoiced` as a `Status` value comes from the xlsx export (`scout-sps.md:28-29`). The full API list (including `draft`, `void`, `closed`, `onhold`) is unverified (V1).
- `zoho_import_runs` has `started_at TEXT NOT NULL`, `captured_at TEXT NOT NULL` (`001-schema.sql:79`) and `finished_at` per run (`:77-85`). Release 0 sets `rows_upserted += rows.length`, i.e. rows processed, not rows changed (`cli/import/run.js:80`), and stores `err.message` in `error` (`run.js:116`).
- The CLI skips a record whose date field is before 2024-01-01 Colombo (`cli/import/run.js:8,99`; `so_headers` uses `order_date`, `bundles` uses `date`: `upsert.js:40,129`).
- `runSweep` processes every finished run with `processed_at IS NULL` and parses its `changed_so_numbers` as JSON (`server/services/sweep.js:56-80`).
- Stage facts are computed **per SO**, never per line (`server/services/facts.js:3-17`, `design.md:347`).
- Freshness: `shippedFresh` needs a full-list `so_headers` run captured on or after the previous working day, and turns stale whenever a package/shipment import is newer than the header list (`server/services/freshness.js:6-14`, `shared/time.js:52-53`).

**Jobs table**
- `jobs` is a manually created file: `created_by NOT NULL`, `order_type NOT NULL`, `UNIQUE(division_code, job_no)` (`001-schema.sql:146-154`).
- It is linked to a whole SO through `job_so_links`, which has no line (`:156-160`).

**Migrations**
- Migrations are forward-only and run at startup inside a transaction with a hash check (`server/db/migrate.js:32-71`).
- The lint rejects DROP TABLE/COLUMN and RENAME (`lint-migrations.js:71-73`).
- Files 001–004 are frozen (`/root/dev/production-dashboard/CLAUDE.md`, "Migrations are additive only; 001–004 are frozen"). 005 is not written or deployed yet, so its content can still change.
- If the database is newer than the code, the app starts anyway with a warning (`migrate.js:36-38`).

**Deployment**
- Release 0 has never been deployed, and production-dashboard is not yet in the shdeploy table (`/root/.claude/CLAUDE.md` §4b). **Decided 29 Sep (Q10, "Answered questions"):** the app is registered properly before its first deploy: PM2 name `production-dashboard`, port 4300 (default at `server/config.js:35`; `PORT` must also be set in the env file, `server/config.js:29`), live directory `/root/production-dashboard`, a row in the shdeploy table and a `deny /root/production-dashboard` line in `/root/.claude/scripts/protected-paths.conf`. The human does all of that and runs every deploy command; see "Rollback plan".

**Zoho facts observed** (SPS SO detail, 22 SOs dated 15–18 Sep, `/root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json`)
- Each line carries these fields, per line:
  - `line_item_id` (:73), `item_id` (:77), `is_combo_product` (:90), `combo_type` (:91, value `"assembly"` in all 22), `name` (:95), `item_type` (:123)
  - a `Division` tag (:127-135) and `project_name` (:163)
  - quantities `quantity` (:102), `quantity_invoiced` (:142), `quantity_packed` (:143), `quantity_shipped` (:144), `quantity_picked` (:146), `quantity_cancelled` (:149), `quantity_delivered` (:150)
- `item_custom_fields` is empty (:140). `CF.Job No` and `CF.Manufacturing Division` are **header** custom fields (`custom_fields[].search_entity="salesorder"`, :356-415; `custom_field_hash` :525-558).
- The SO number is the JOBORDER number (`salesorder_number: "JOBORDER-08602"`, :19). A bundle's `reference_number` is that SO number, sometimes with a suffix (`"JOBORDER-07835 - F"`, bundles file :17). `soKey` strips the suffix (`shared/text.js:7-10`).
- Bundles are normally recorded minutes before the package: the JOBORDER-08602 bundle was created 16:35:56 (`bundles_and_recent_sos.json:45`) and the SO was last modified 16:45:49 with everything packed (`:261798,261802`).
- All 22 sampled SOs have exactly one line. Multi-line SOs do exist: 10,442 line rows across 8,299 SH SO IDs (`scout-sps.md:10-11,31`).
- `is_combo_product` is a JSON boolean (`true` in 22 of 22 lines). `tags` holds exactly one `Division` element on 18 lines and none on 4 (all four RWU); no line has two. Ids (`line_item_id`, `item_id`) are JSON strings; `sku` is `""` on 19 of the 22 lines and `unit` on 5.
- Line tag values seen: `Paper Straw Unit`, `OPD - PackPro Unit`, `MOBA Unit`, `MOBA Punching Unit`, `Screen Printing Unit`, `Customized Packing Unit`.
- Partial deliveries are common: 288 partial lines in 2026, and 1,576 lines with status `partially_invoiced` (`scout-sps.md:28,51`; xlsx vocabulary).
- Open SOs by the xlsx `Status` column (`confirmed` or `partially_invoiced`) at the 16 Sep export: 2024: 60+110, 2025: 82+664, 2026: 190+294, about 1,400 in total (`scout-sps.md:72-74`). This count uses the xlsx vocabulary and is **not** the in-scope count of this spec (§5.2 defines "open" from API fields); the real count is logged by the first full list (§5.5).
- Unmeasured: what share of packed assembly lines have a bundle referencing their **own** SO. Ex-stock orders may be packed from stock bundled under another reference (order type `Ex Stock`, `002-seed.sql:58`). This is why the preview raises no bundle flag (§4) and V7 measures it.

## Proposed behaviour

### 1. Users and what each sees

| Role (existing strings) | Sees in "My jobs" | SO drill-down | Admin screens |
|---|---|---|---|
| `manager` (Ishan, Mubeena, Ranga) | Jobs whose resolved division is in `SELECT division_code FROM division_pairs WHERE manager_user_id = :me AND active = 1`. Never jobs with no division. | Allowed if at least one line of the SO is visible to them. Then it shows **every** line of that SO, including other divisions', read-only. | none |
| `gm` (Samitha) | All jobs, including those with no resolvable division (grouped "No division"). | Any SO. | none |
| `admin` | Same as `gm`. Also sees the "Unassigned" list and the sync status, including "Sync problems". | Any SO. | existing, plus Unassigned and Zoho sync |
| anyone else (for example a `coordinator` only) | existing stub page | 403 (round-11: these are internal staff, so there is nothing to hide, and 403 matches `/api/jobs` for the same role, AC24) | none |

- A user with several roles gets the widest view.
- Nobody can write anything through the preview: every new endpoint is `GET`.
- Division pairs for Ishan, Mubeena and Ranga are entered by the admin in the existing Divisions UI, per `design.md:398`. They are **not** seeded by a migration. `OPD - PackPro Unit` (Q3, answered 29 Sep) maps to `PACKPRO`, managed by **Ishan only**: a PACKPRO job is in Ishan's list and not in Ranga's. `PACKPRO` is already seeded (`002-seed.sql:8`), so this is a tag-alias rule (one row in 005), not a schema change.
- **Divisions with no manager (Rev 6).** Five seeded divisions have no manager in the 28 Sep mapping (and none in `design.md:398`): **PCU, PCLU, DPU, PPU and CWU** (`002-seed.sql:9-10`). (`MOBA_P`, seeded at `:7`, has no alias in `002-seed.sql:43-55`, so no tag or header value resolves to it.) A job that resolves to one of the five would be invisible to every manager. Rule: such a job is **not** hidden and **not** guessed onto someone. It is on the admin **Unassigned** list with reason `no_manager`, it is visible to `gm` and `admin` in the full list with its division shown, and it counts in their counters. It appears for a manager only when the admin adds an active `division_pairs` row for that division (the existing Divisions UI; a pair also needs a coordinator account, `admin-config.js:246`). No code change is needed then (AC89).

### 2. Job definition and derivation

A **job** is one row of the new mirror table `zoho_so_line_items` where all of the following hold:
- `org = 'SPS'`;
- `item_type = 'inventory'`;
- its SO header exists and `zoho_so_headers.sync_state` is not `'missing_in_zoho'`;
- its SO header `status` is not `'draft'` (round-6 N5, below).

Jobs are **not** inserted into `jobs`. They are computed when read, from the mirror, by one server module `server/services/line-jobs.js`. The list, the SO drill-down and the counters all use it.

Consequences:
- **Created:** automatically, when the sync first writes the line.
- **Updated:** on every sync that changes it.
- **Duplicates:** impossible, because the primary key is `(org, line_item_id)`.
- **Removed:** when Zoho removes the line or the SO (§5.4), or when a detail fetch answers "not found" (§5.2).
- **Not yet loaded:** an SO whose detail has never been fetched has no jobs yet. The list shows "History loading: X of Y SOs loaded" until the detail queue (§5.2) has fetched every in-scope SO once. X and Y **exclude SOs that are sync problems** (§5.2): a never-loaded SO that becomes a sync problem leaves Y, so the line cannot stay forever (round-5 N2, round-6 N9); it is on the admin Sync problems list instead (AC79).
- **Drafts (round-6 N5, decided in Rev 6).** A draft SO is not work a manager can pack or ship, so its lines are not jobs while `H.status = 'draft'`: they are absent from `/api/jobs`, and `/api/sales-orders/:number` answers 404 for it (§6). A draft created after the cutoff is still loaded (flag-eligible, §5.2), so its lines appear as soon as a delta shows it confirmed (AC87).

**Open SO (header level, round-4 B2, reading R11).** An SO header H is **open** when `H.status NOT IN ('void','draft')` **and** at least one of these holds:
- `H.status NOT IN ('fulfilled','closed')`;
- `COALESCE(H.quantity_shipped,0) < COALESCE(H.quantity,0)`;
- `COALESCE(H.quantity_invoiced,0) < COALESCE(H.quantity,0)`.

The values are the API's (`status`, `quantity`, `quantity_shipped`, `quantity_invoiced` of the list row, `bundles_and_recent_sos.json:264206-264214`). The rule is the header-level mirror of the line `state` rule below: a line is `closed` when shipped and invoiced reach its effective quantity, and `cancelled` when its SO is void. A status value not in the known list (V1) counts as not excluded, so the SO is loaded rather than hidden (fail toward loading; logged, §Observability). In the real list rows the header `quantity_packed`, `quantity_shipped` and `quantity_invoiced` **include cancelled units** (Current behaviour), so an SO with cancelled units looks more closed at header level, not less: header shipped ≥ header quantity exactly when line shipped ≥ `qty_effective`, which is the line rule (one sampled SO shows it; V3(c) confirms it on more). The two quantity clauses therefore match the line rule. The clause `H.status NOT IN ('fulfilled','closed')` only adds SOs whose quantities are already complete (for example status `shipped` or `onhold` with everything shipped and invoiced); each costs one fetch and yields closed jobs. It is kept because it is the lead's R11 formula, and the census of the first full list (`in_scope_by_status`, §5.5) measures its cost; dropping it is a lead decision (round-5 N4 declined for that reason).

Derived fields, per line L of SO H:

| Field | Definition |
|---|---|
| `division_code` | 1. `L.division_tag` (extracted from `line.tags` by the rule in §5.2 "Line column map"; several distinct Division tags give a joined text that maps to nothing), mapped through `division_aliases` by `cmpKey` (`shared/text.js:6`); `division_source='tag'`. The tag `OPD - PackPro Unit` maps to `PACKPRO` (Q3; alias row in 005). 2. If L has **no** Division tag: `H.cf_manufacturing_division` mapped the same way; `division_source='header'`. 3. Otherwise NULL, and `division_source` is `null` (API `null`, round-6 N10). A tag that is present but **unmapped** gives NULL (reason `unmapped_division`); it does **not** fall back to the header. |
| `division_conflict` | true when both the tag and the header map and give different codes |
| `job_no` | `L.project_name` if non-blank, else `H.cf_job_no`, else NULL |
| `customer` | `H.cf_order_received_from` |
| `qty_ordered`, `qty_cancelled` | `L.quantity`, `L.quantity_cancelled` |
| `qty_effective` | `qty_ordered − qty_cancelled` |
| `is_assembly` | `L.is_combo_product = 1 AND L.combo_type = 'assembly'` |
| `bundle_pool` | Σ `zoho_bundles.quantity` where `org='SPS' AND so_key = H.salesorder_number AND composite_item_id = L.item_id AND lower(status)='bundled' AND sync_state IS NULL` |
| `qty_bundled` | If L is the only job line of H with this `item_id`: `bundle_pool`. If k > 1 job lines of H share the `item_id`: the pool is allocated in `item_order` ascending (ties by `line_item_id`), each line taking `min(remaining, qty_effective)`; the last line in that order also takes any remainder. The sum over the k lines always equals `bundle_pool` (no double counting, critic N7). |
| `qty_produced`, `produced_basis` | When `is_assembly`: `max(qty_bundled, L.quantity_packed)`, with `produced_basis='bundled'` if `qty_bundled >= L.quantity_packed`, else `'packed'`. Otherwise: `L.quantity_packed`, `'packed'` (labelled "packed (Zoho)", as in `design.md:363`). A packed quantity is always produced, so an assembly line packed without a matched bundle is not counted "In production" (Rev 4; V7 may revisit). |
| `qty_packed`, `qty_shipped`, `qty_invoiced` | the matching `L.quantity_*` |
| `due_date` | `H.expected_shipment_date` |
| `days_late` | calendar days from `due_date` to today (Colombo) when `due_date < today` and `qty_shipped < qty_effective`, else 0 |
| `state` | `cancelled` if `qty_effective <= 0` or `H.status = 'void'`; else `closed` if `qty_shipped >= qty_effective AND qty_invoiced >= qty_effective`; else `open` |
| `legacy` | `H.order_date < today − LEGACY_DAYS` (Colombo calendar days; `LEGACY_DAYS = 180`, constant in `shared/missing-rules.js`, a **new file**: it does not exist in Release 0) |
| `flag_status` | per SO, the same for every job of H (§4, level 2). For a **flag-eligible** H: `sync_problem` if `H.detail_fail_count >= DETAIL_FAIL_LIMIT`; else `checking` if H has `row_quarantine_at` not NULL or a refresh reason (§5.2); else `current`. An SO that is not flag-eligible has no flag that could be hidden, so its jobs are always `current` (round-5 N3; the value then only says that no flag is being held back) |

### 3. Documentation strip (per job)

- **Stages shown.** The strip shows the stages of the job's division in `division_stages` order (`002-seed.sql:33-41`). A job with no division uses the OPD order.
- **Stage 6 (Pick list)** is therefore not shown for PSU or RWU, because it is not in their stage list.
- **Stages Zoho cannot show (1, 2, 3, 9, 11)** always show the state `not_tracked` with the label "not tracked yet".
- **Stage 5 (Bundle)** is shown as `detected` / `not_detected` only (or `n_a`). It never raises a flag in the preview (lead decision, Rev 4). `not_detected` is drawn as a neutral grey "○ no bundle seen", never as the red ✘ used for `not_done`, so it does not read as a missing document.
- The strip is always drawn from the stored mirror, whatever the job's `flag_status`; `flag_status` only decides whether missing-document flags are shown (§4).

| Stage (`stage_catalog`) | Zoho evidence, matched to **this line** | `done` | `partial` | `not_done` | `n_a` | `at` shown |
|---|---|---|---|---|---|---|
| 4 Sales order | the line exists | always | — | — | — | `H.created_at` |
| 5 Bundle (produced) | `qty_bundled` (§2) | — (state `detected` when `qty_bundled > 0`; the tooltip shows `qty_bundled` of `qty_effective`) | — | — (state `not_detected` when `qty_bundled = 0`) | `NOT is_assembly` | earliest matched bundle `created_at`; none when `not_detected` |
| 6 Pick list | `L.quantity_picked` | `>= qty_effective` | `> 0` | `= 0` | — | `picked_seen_at` |
| 7 Package | `L.quantity_packed` | same rule | same | same | — | `packed_seen_at` |
| 8 Shipment | `L.quantity_shipped` | same rule | same | same | — | `shipped_seen_at` |
| 10 Sales invoice to SH | `L.quantity_invoiced` | same rule | same | same | — | `invoiced_seen_at` |

The strip `state` values are exactly `{done, partial, not_done, n_a, not_tracked, detected, not_detected}`; `detected` and `not_detected` occur only for stage 5.

Two observed timestamps are kept per quantity (picked, packed, shipped, invoiced). Both are sync capture times, not Zoho timestamps. The UI labels them "seen by sync".
- **`*_seen_at`** is the capture time at which the quantity was first seen above 0. It is shown in the strip. It is reset to NULL if the quantity goes back to 0.
- **`*_changed_at`** (packed, shipped, invoiced only) is the capture time of the latest detail fetch at which the quantity was **higher** than the stored value (including 0 → above 0). A decrease or no change leaves it as it is. It is reset to NULL if the quantity goes back to 0. The missing-document timers (§4) run from it, so a second partial package or shipment restarts the timer (critic B3).
- **Why observed times are used.** Zoho line quantities carry no date, and the SO's document dates are per SO, not per line.
- **Why this is safe.** Flags only apply to SOs created after the cutoff (§4), and those are observed from creation.
  - Every flag rule (package, shipment, invoice) is a line-quantity rule. A flag is shown only after a confirming detail fetch made after its threshold was reached (§4), and only while the job's detail is at least as new as its header (`flag_status='current'`, §4).
  - A list row for the SO that is quarantined on every run would leave its data frozen; §5.2 "Row quarantine" marks that SO `checking` (fail closed) when the row identifies it, so this claim holds for it too (round-7 B2).
  - **This holds only if V4 confirms that a package, a shipment and an invoice each move the SO's `last_modified_time`** (round-6 B2). Then the header delta reads every change within one slot, the header row moves, the job goes to `checking` (flags hidden) until its detail is re-fetched, and a lag in observing a quantity change cannot produce a false flag. **V4 is a pre-build gate:** if any of the three does not move `last_modified_time`, this spec returns to the spec-writer and the build does not start. This design has no accepted stale window: the nightly full list and the P2 re-confirmation are not a substitute for the delta seeing the change. Without V4 the exposure would be a real invoice not seen for up to about 20 h, with `invoice_missing` shown as "checked HH:MM" in the meantime; that is why it is a gate and not a tolerated case.
  - Bundles come from a **different list** that is polled less often than the SO detail (§5.3). The only flag that reads bundles is `package_missing`, and it needs a matched bundle to exist: a bundle not yet mirrored makes its condition false, so the lag can only delay that flag, never raise it falsely. There is no `bundle_missing` flag in the preview.
  - **Exception (round-4 N3):** a bundle **deleted or redone** in Zoho is only seen at the weekly bundles reconcile (§5.4). Until then it keeps counting in `qty_bundled`, which can raise a false `package_missing` for up to 7 days. V7(c) measures how often SPS deletes bundles; the Failure-modes table records it.

### 4. Counters, missing-document flags, cutoff, freshness

**Stored flag and shown flag.** A job has a **stored flag** for rule r when all of these hold on the stored data (no freshness term):
1. **Cutoff.** Env `PD_FLAGS_SINCE` (YYYY-MM-DD, Colombo) is set, and the Colombo date of `H.created_at` is on or after it. If `PD_FLAGS_SINCE` is unset, no job ever has a stored flag. An SO that meets this rule is **flag-eligible**.
2. **Open.** `state = 'open'`.
3. **Rule.** r's condition holds and `wd(x) >= k` (table below).
4. **Confirmed.** `H.detail_fetched_at >= threshold_instant` of r (defined below).

A stored flag is **shown** (in `missing`, in the "Documents missing" counter, as a chip) only when **both** freshness levels allow it: `preview_fresh(SPS)` is true (level 1) **and** the job's `flag_status = 'current'` (level 2). When 1–3 hold but 4 does not, nothing is shown and the SO is queued for a confirmation (§5.2, P0). The re-confirmation queue (P2) reads stored flags, not shown flags, so no queue depends on freshness and no freshness level depends on a queue.

**Level 1: `preview_fresh(SPS)` = sync health only** (lead decision, Rev 5). It replaces `shippedFresh` for the preview only (`freshness.js` itself is unchanged). It reads only `zoho_import_runs`; it does **not** read the detail queue, any per-SO failure, any backlog or any header's `captured_at`. It is true when all of these hold; the first one that fails gives the `reason`:
- `no_full_header`: there is at least one `zoho_import_runs` row with `org='SPS'`, `source='sync'`, `module='so_headers'`, `full_list=1`, `status='ok'`;
- `full_list_old`: the newest such row has `finished_at` within the last 50 hours;
- `delta_stale`: the newest `org='SPS'`, `source='sync'`, `module='so_headers'`, `status='ok'` run **of either kind** (delta or full list, Rev 6) has `finished_at` within `HEADER_MAX_AGE` (45 min when now is 06:15–20:00 Colombo; 135 min otherwise);
- `bundles_stale`: the same for `module='bundles'` within `BUNDLES_MAX_AGE` (75 min when now is 06:15–20:00; 135 min otherwise).

**Boundaries (round-11).** Every "within" is inclusive: elapsed **≤** 45 min, ≤ 75 min, ≤ 135 min and ≤ 50 h are fresh, one second more is stale. The day windows apply when `06:15:00 ≤ now ≤ 20:00:00` Colombo, both ends inclusive; the night windows otherwise. **`status='ok'` is required deliberately:** this differs from Release 0's `server/services/freshness.js`, which treats a `warning` run as ok (`status IN ('ok','warning')`, `freshness.js:3-4`); the stricter rule matches the watermark rule that only an `ok` run moves `W(m)`. Do not "fix" it to match `freshness.js` (AC34).

A full list is a superset of a delta, so an `ok` full list also satisfies `delta_stale` and `bundles_stale`. That is what lets a go-live deploy at 10:00 show data after its first cycle (§5.2 "Full-list attempts", AC84).

When level 1 is false: the grey banner, every counter and both notes are `null` ("—"), and every job's `missing` is `[]`.

**Level 2: per-job `flag_status`** (lead decision, Rev 5). Computed per **flag-eligible** SO H and shared by every job of H. An SO that is not flag-eligible has no flag that could be hidden, so its jobs are always `current` and never show "checking" or "sync problem" (Rev 6, round-5 N3; AC90):
- `sync_problem` when `H.detail_fail_count >= DETAIL_FAIL_LIMIT` (`DETAIL_FAIL_LIMIT = 3`, constant in `server/services/zoho-sync.js`; §5.2 "Per-SO detail failures");
- else `checking` when H has `row_quarantine_at` not NULL (a list row for it was quarantined and not yet re-read, §5.2 "Row quarantine"), or at least one **refresh reason** (§5.2). The lead rule is "the SO detail is at least as new as its header", i.e. `H.detail_fetched_at >= H.captured_at`. Its negation is refresh reason (b). Reasons (c) and (d) cannot be true without (b) also being true, because any change to `modified_at` or to a signature field rewrites the header row and so moves `captured_at` (`upsert.js:8,18-21`); they are kept so that "checking" and "queued for a refresh" are the same set by definition;
- else `current`.

Effect of `checking` or `sync_problem` on one job, with level 1 true:
- the job stays in the list with its strip, quantities and due date;
- its `missing` is `[]`; the UI shows "checking with Zoho…" (`checking`) or "sync problem — IT notified" (`sync_problem`) in place of the chips;
- it is not in "Documents missing" (it has no shown flag); it is counted in the small note next to that counter: "being checked: N · sync problem: M" (API `checking.being_checked`, `checking.sync_problem`; each part hidden when 0);
- every other counter and every other job is unaffected. The other four counters count it on its stored data.

"Being checked" and "sync problem" counts are over the same jobs as the counters: visible to the user, `state='open'`, `legacy = false`.

Waiting P0 and P2 work is measured, not gated: a P0 confirmation waits from its `threshold_instant`, a P2 re-confirmation from `H.detail_fetched_at + 20 h`. The oldest of each is reported on the status screen (§6) and in the run log, together with the oldest refresh wait (`oldest_refresh_wait_min`, from `H.captured_at` of the oldest in-scope, non-problem SO with a refresh reason). A waiting P0 means a flag appears later; a waiting P2 means a shown flag keeps an older "checked HH:MM"; a waiting refresh means that SO's jobs show "checking with Zoho…". None of them hides the screen or another SO's jobs.

Old SOs still waiting for their first detail fetch do **not** make the data stale (critic B1b); they have no jobs yet and are counted only in "History loading". Manual package or shipment imports do **not** affect `preview_fresh` (critic N8).

**Missing-document rules.** `wd(x)` = working days `d` with `colomboDate(x) < d <= colombo today`. Working days come from settings `working_weekdays` and `holidays` (`002-seed.sql:77`, `001-schema.sql:128`), read through `server/services/calendar.js`. For a rule with threshold k ≥ 1 measured from time x, **`threshold_instant`** = 00:00 Colombo of the k-th working day after `colomboDate(x)`.

| Code | Missing step | Condition | Measured from x = | Threshold k |
|---|---|---|---|---|
| `package_missing` | 7 | `is_assembly AND qty_bundled >= qty_effective AND qty_packed = 0` | latest matched bundle `created_at` | 2 working days |
| `shipment_missing` | 8 | `qty_packed > qty_shipped` | `packed_changed_at` | 3 working days |
| `invoice_missing` | 10 | `qty_shipped > qty_invoiced` | `shipped_changed_at` | 2 working days |

- These three are the only flag codes. `bundle_missing` is **not** part of the preview (lead decision, Rev 4); follow-up V7 decides whether it returns.
- Thresholds are constants in `shared/missing-rules.js` (a **new file** created by this build; Release 0 has none), with the values above. Q5 asks the user to confirm them.
- Working days are Mon–Fri as seeded. If SPS packs, ships or invoices on Saturdays, flags come about one day late; they are never false. Changing this needs no code: the admin edits the weekdays through `PUT /api/admin/calendar` (`admin-config.js:392-401`). Q13 asks the user.
- Pick list is **never** flagged, because Zoho allows packages without pick lists.
- Each missing entry carries `since = threshold_instant` and `checked_at = H.detail_fetched_at`. The UI shows "checked HH:MM".

**Counters.** Over the jobs visible to the user, `state='open'` and `legacy = false` only. When `preview_fresh` is false, **every** counter and both notes are `null` and show "—". While the history is still loading (§2), counters are computed over the loaded jobs and the response has `counters_complete=false`; the UI shows "(history loading)" next to the counters.

| Counter | Rule |
|---|---|
| Due in 3 days | `today <= due_date <= today+3` (calendar) and `qty_shipped < qty_effective` |
| Past due | `due_date < today` and `qty_shipped < qty_effective` |
| In production | `qty_produced < qty_effective` |
| Produced, not shipped | `qty_produced >= qty_effective` and `qty_shipped < qty_effective` |
| Documents missing | at least one shown flag (so never a job whose `flag_status` is not `current`) |

**Freshness line.**
- Always shown: "Zoho data as of HH:MM (Colombo)", from the latest ok `so_headers` run's `finished_at` (delta or full list).
- When `preview_fresh` is false, also a grey banner "Zoho data is not current — flags and counters hidden (reason: <code>)". The reason is one of `no_full_header`, `full_list_old`, `delta_stale`, `bundles_stale`.
- While the history is loading, also a blue line "History loading: X of Y SOs loaded" (X = in-scope SOs with `detail_fetched_at` not NULL, Y = in-scope SOs, both **excluding sync-problem SOs**, §2; API keys `history.loaded` and `history.in_scope`).

### 5. Read-only sync (Release 1b, trimmed to what the preview needs)

**5.1 Transport and credentials**
- **Zoho endpoints.** API base `https://www.zohoapis.com/inventory/v1`. OAuth token endpoint `https://accounts.zoho.com/oauth/v2/token`. US data centre, org `843825512`.
- **New env keys** in `server/config.js`:
  - `ZOHO_SYNC_ENABLED` (`true`/`false`, default `false`);
  - `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`: required non-empty when enabled; startup throws otherwise;
  - `ZOHO_ORG_ID_SPS` (default `843825512`);
  - `ZOHO_DAILY_CALL_CAP` (default 400; startup throws if above 500 or below 250);
  - `PD_FLAGS_SINCE`;
  - `ZOHO_RESET_SYNC_PROBLEMS` (`true`/`false`, default `false`): the 2am reset lever of §5.2 "Reset lever" (round-6 B1);
  - `ZOHO_FORCE_FULL_LIST` (`true`/`false`, default `false`): the operator lever of §5.2 "Full-list attempts" (round-6 B5).
  - Both levers are read once at scheduler start; each is a value in the env file that the human sets and unsets, never a screen action.
- **Secrets** live in the server env file only. They are never logged, never returned by any endpoint and never committed.
- **Access token.** Kept in memory only. It is refreshed when it expires or on a 401, at most once per request.
- **Only one non-GET request exists:** the token refresh `POST` to the token endpoint above.
- **Scopes** (config constant): `ZohoInventory.salesorders.READ` plus the read scope that the bundles endpoint needs (verified in V2). Every scope string must end in `.READ`.
- **HTTP client.** A single module `server/zoho/client.js` exposes only `get(path, query)` and an internal `refreshToken()`.
- **Throttle.** At most 30 calls per minute, well under Zoho's hard cap of 100 per minute (`Production Dashboard/CLAUDE.md:52`).
- **Capture time.** Every row written from a response carries `capturedAt` = the instant that response was received (UTC ISO). Cycles are single-flight (§5.3), so capture times grow monotonically across list pages and detail fetches.
- **Run row `captured_at`** (NOT NULL, `001-schema.sql:79`, round-6 N3): the instant the run's first response was received, or its `started_at` for a run that sends no request.
- **Effect on Release 0 freshness (round-6 N3).** A sync run with `full_list=1` and `status='ok'` also moves `shippedFresh` and `bundlesDataAge` for SPS, because they select by module and `full_list` only (`server/services/freshness.js:3-4,22-25`). The preview does not read either (level 1 has its own rule, §4). This is intended and harmless: the older SO-level features then see SPS header and bundle freshness follow the sync.

**5.2 What it pulls**

All writes go through `MODULE_HANDLERS`: no fourth writer.

**Field mapping (critic round 2 N2; round-6 B3, N1, N4).** Every list row and detail object is mapped only through the column maps in `config/zoho-columns.json` and `mapRow` (`cli/import/columns.js:12-38`). The sync code has **no field mapping of its own** except the hand-coded derivations named in "Hand-coded derivations" below. Three sections are in play: `so_headers` (list rows, and the detail header for the fields the detail may write), `bundles` (list rows) and the **new `so_line_items`** (detail lines, "Line column map" below). Changes to the file: one new entry in `bundles`, `"composite_item_id": { "from": ["composite_item_id"], "type": "raw" }`, and the new `so_line_items` section. A bundle's `quantity` keeps coming from `quantity_to_bundle` (`zoho-columns.json:134`). The `bundles` handler's field list (`upsert.js:131-132`) gains `composite_item_id` **only when `ctx.source === 'sync'`** (round-6 N4; the same scoping as `sync_state` below), so a Release 0 pull import of bundle rows that lack the key can never null a stored value (AC92). The map's `required` list applies to list rows **per row** (see "Row quarantine"): not to the first row only, as the CLI does (`run.js:86-89`), and not to the detail object, which has its own shape check (`so_detail` handler, step 0).

**Present source keys only, on list rows too (round-6 N1).** `mapRow` returns every field of the section and yields `null` for a field whose source key is absent (`columns.js:15`), and `upsertGuarded` writes `rec[c] ?? null` for every field it is given (`upsert.js:19-21`). For a sync list row the handler is therefore given `fields = (the handler's field list) ∩ (the fields whose source key occurs among that raw row's keys)`, computed before `mapRow` from the section's `from` lists. A field whose source key is absent is left as stored on UPDATE and is NULL on INSERT. The evidence that list rows carry flattened `cf_*` keys comes from the **browser** endpoint (`bundles_and_recent_sos.json:261819-261836`, `tools/zoho-pull-snippet.js:28`); V1 records whether the OAuth list at `zohoapis.com/inventory/v1` has them. If it does not, no delta can blank `cf_job_no`, `cf_manufacturing_division` or `cf_order_received_from` (AC93); they then arrive only through the detail. The same rule applies to the detail header write.

**Hand-coded derivations** (everything that is not a `from` lookup; each has an AC): (1) `division_tag`, extracted from `line.tags[]` (below); (2) the detail header's `cf_*` values, which exist only inside `salesorder.custom_field_hash` (`salesorders_since_2026-09-15.json:525-558`; no top-level `cf_*` key): its entries are copied onto the object as top-level keys, where absent, before `mapRow`; (3) `source='sync'` and `sync_state`; (4) the observed times `*_seen_at` / `*_changed_at` (handler step 3).

**Line column map: the new `so_line_items` section of `config/zoho-columns.json` (round-6 B3).** Each element of `salesorder.line_items` is mapped by `mapRow` with this section. The types are the ones `mapRow` implements (`columns.js:17-26`):

```json
"so_line_items": {
  "id": "line_item_id",
  "required": ["line_item_id"],
  "fields": {
    "line_item_id":       { "from": ["line_item_id"],       "type": "raw" },
    "item_id":            { "from": ["item_id"],            "type": "raw" },
    "item_name":          { "from": ["name"],               "type": "text" },
    "sku":                { "from": ["sku"],                "type": "text" },
    "unit":               { "from": ["unit"],               "type": "text" },
    "item_order":         { "from": ["item_order"],         "type": "number" },
    "item_type":          { "from": ["item_type"],          "type": "text" },
    "is_combo_product":   { "from": ["is_combo_product"],   "type": "bool" },
    "combo_type":         { "from": ["combo_type"],         "type": "text" },
    "quantity":           { "from": ["quantity"],           "type": "number" },
    "quantity_cancelled": { "from": ["quantity_cancelled"], "type": "number" },
    "quantity_picked":    { "from": ["quantity_picked"],    "type": "number" },
    "quantity_packed":    { "from": ["quantity_packed"],    "type": "number" },
    "quantity_shipped":   { "from": ["quantity_shipped"],   "type": "number" },
    "quantity_delivered": { "from": ["quantity_delivered"], "type": "number" },
    "quantity_invoiced":  { "from": ["quantity_invoiced"],  "type": "number" },
    "project_name":       { "from": ["project_name"],       "type": "text" }
  }
}
```

These 17 entries plus the hand-coded `division_tag` are the 18 line fields of the new table. The table's other columns are the key parts (`org`, `salesorder_number`), the seven observed-time columns (handler step 3) and the meta columns `source_file`, `last_synced_at`, `captured_at`, which `upsertGuarded` fills (`upsert.js:8`). The rules the implementer builds from:
- **`bool` for `is_combo_product`.** The real payload is a JSON boolean (`salesorders_since_2026-09-15.json:90`, `true` in 22 of 22 lines). `mapRow`'s `bool` maps `true` to 1, `false` to 0 and an absent or blank key to NULL (`columns.js:26`). better-sqlite3 refuses to bind a JavaScript boolean, so this is the only route into the column. The column is **nullable** (Data model changes): `upsertGuarded` binds `rec[c] ?? null` on INSERT and UPDATE (`upsert.js:12,21`), so a `NOT NULL DEFAULT 0` could never apply and a line whose response omitted the key would abort the whole SO. NULL means "key absent" and reads as "not a combo product" (`is_assembly` needs `= 1`).
- **`raw` for `line_item_id` and `item_id`.** `mapRow` throws on a JSON number that is not a safe integer (`columns.js:18-20`), so an id that Zoho ever sends as a number fails loudly (outcome `handler_error`) instead of being stored rounded. The real ids are JSON strings (`:73,77`).
- **`number` for every quantity and `item_order`.** `toNumber` throws on non-numeric text (`shared/text.js:13-17`), which is `handler_error`; a blank value is NULL. The shape check requires all seven quantity keys on every job line (`item_type='inventory'`), so a job line's quantity is never NULL and never read as 0 by mistake (round-7 B3). For a line that is not a job the rule 'present source keys only' applies to the line write too: the handler passes `upsertGuarded` only the fields whose source key occurs in that line, so an absent key never overwrites a stored value; on INSERT it is NULL, and `COALESCE(x,0)` reads it as 0 (such a line is not a job, so no flag reads it).
- **`text`** for names and codes: `cleanText` collapses whitespace and turns blank into NULL (`sku` is `""` on 19 of the 22 sampled lines and `unit` on 5, so NULL).
- **`division_tag` extraction (hand-coded; input `line.tags`).**
  1. `tags` absent or `[]`: `division_tag` is NULL (no Division tag; §2 falls back to the header).
  2. `tags` present but not an array of objects: outcome `bad_shape` (never guess a division).
  3. Otherwise take the elements whose `tag_name`, compared with `cmpKey`, equals `division`; map each to `cleanText(tag_option_name)`; drop blanks; remove duplicates by `cmpKey`. Zero left: NULL. Exactly one: that text (for example `MOBA Unit`, `OPD - PackPro Unit`).
  4. Two or more distinct values: `division_tag` is the values sorted and joined with ` | ` (for example `MOBA Unit | Paper Cup Unit`) and the run's `warnings` gets `division_tag_multiple` with the SO number. That text is in no alias, so §2 gives `division_code = NULL` with reason `unmapped_division` and **no** header fallback: the job goes to the admin Unassigned list with the raw text visible. It is never guessed. (The sample has no two-tag line; the rule is defensive and tested, AC82.)

**`sync_state` on write (critic round 3 N2; round-4 non-blocking 2).** Every header or bundle row the sync writes (delta, full list or detail) is written with `sync_state = NULL`. Because `upsertGuarded` skips a write whose listed fields are all unchanged (`upsert.js:18`), the `so_headers` and `bundles` handlers add `sync_state` to their field list when `ctx.source === 'sync'` (and only then), so a stored `'missing_in_zoho'` compares unequal to NULL and is overwritten. So a row wrongly marked `missing_in_zoho` by a full list (a row modified while the list was being paged can be skipped by offset paging) is cleared by the next delta that reads it, at the latest in the next slot.

**Delta watermark (critic round 2 N1).** For a delta of module m (`so_headers` or `bundles`):
- `W(m)` = `started_at` of the newest `zoho_import_runs` row with `org='SPS'`, `source='sync'`, `module=m`, `status='ok'`, whether it was a delta or a full list.
- Paging stops at the first row with `last_modified_time < W(m) − 10 min`. Both sides are compared as instants (Zoho's offset-bearing timestamp against our UTC `started_at`). The 10 min covers clock skew between Zoho and the VPS.
- If no such run exists there is no watermark and no delta can run: the cycle makes the **first full-list attempt** instead ("Full-list attempts" below). It is credited `full_list=1` when it completes and passes the 95% rule, and its pages double as the first delta, so nothing is paged twice (round-6 B5).
- A run that ends `failed` or `warning` never moves `W(m)`, whatever it committed. Rows it did commit stay (they are correct data); the next delta re-reads their range, and `upsertGuarded` makes that a no-op for unchanged rows (AC8).
- Why this closes gaps: every ok run has read every row modified from `W − 10 min` up to its own start (the list is newest-first from the moment of each page request). Consecutive ok runs therefore cover a continuous range, and a failed run in between leaves no hole.
- The old rule `W = max(modified_at) FROM zoho_so_headers` (Rev 2) is dropped: with a newest-first sort, a run that committed page 1 and failed on page 2 would have moved W past the rows on page 2.
- If a delta cannot finish within the cycle's request limit (§5.3), it ends `failed` with `error='delta_incomplete'`; W does not move and the next cycle continues from the same W. The 02:00 full list, once ok, also resets W.

| Job | Endpoint | Paging / incremental rule | Handler |
|---|---|---|---|
| SO header delta | `GET /salesorders?organization_id=…&sort_column=last_modified_time&sort_order=D&per_page=200&page=n` | Stop at `W(so_headers) − 10 min` (above). Run row: `module='so_headers', full_list=0`. | `so_headers`, extended with `ctx.source` so it writes `source='sync'` |
| SO header full list | the same endpoint with no stop rule, until `page_context.has_more_page=false` | When it runs: "Full-list attempts" below. Run row: `full_list=1` **only if** the pages completed **and** rows received (quarantined rows count as received; rows dropped by the 2024 cutoff do not) ≥ 95% of the local count of non-missing SPS headers. Otherwise `status='failed'`, `error='suspect_short_list'`. | `so_headers` |
| Bundles delta | `GET /bundles?…&sort_column=last_modified_time&sort_order=D&per_page=200` | Stop at `W(bundles) − 10 min`. Run row: `module='bundles', full_list=0`. | `bundles`, with `composite_item_id` added (field mapping above) |
| Bundles full list | the same endpoint, all pages | Weekly (Sunday 03:00, §5.3) and by the same attempt rules as the header list, including the first cycle in which no `org='SPS', source='sync', module='bundles', full_list=1, status='ok'` run exists (critic N2, AC45). The same 95% rule as the header full list. `full_list=1`. | `bundles` |
| SO detail (lines) | `GET /salesorders/{zoho_id}?organization_id=…` | From the detail queue below. Run rows: `module='so_detail'` for live-lane P0, P1 and P3 requests, `module='so_detail_reconfirm'` for P2 requests, `module='so_detail_retry'` for sync-problem retries, `module='so_detail_history'` for the history lane. | new `so_detail` |

**Full-list attempts (round-6 B5; headers and bundles alike).** An *attempt* is any run of module m that pages the list with no stop rule. It is recorded with `file='full_list'` (`zoho_import_runs.file`, an existing nullable column) and has `full_list=1` only when it earns the credit (pages complete, 95% rule passed, `status='ok'`). A full list of module m is **due** in a cycle when at least one of these holds and the limits below allow it:
1. **Schedule:** the header list at 02:00 daily (night slot), the bundles list at 03:00 on Sunday (§5.3).
2. **First cycle:** no `ok` `full_list=1` run of m exists. This is also the case when no sync run of m has ever succeeded, so there is no watermark and a delta cannot run; the first attempt then **is** the run that credits `full_list=1` (see "Delta watermark"). A go-live deploy at 10:00 therefore has data after its first cycle instead of `no_full_header` until 02:00 next morning (AC84).
3. **Retry:** an earlier attempt today ended non-`ok` with a retryable error (`rate_limited`, `auth`, `upstream`, `delta_incomplete`, `crashed`) and at least 60 min have passed since it started. The retry runs in the next slot at or after that time (03:00 after a failed 02:00; the next hourly or 15-minute slot after a failed first-cycle attempt).
4. **Force:** `ZOHO_FORCE_FULL_LIST=true` at process start: the first cycle attempts both lists once, whatever the limits below except the daily call cap, **but skipped for a module if an `ok` `full_list=1` run of that module already exists today** (round-7 N4: a crash loop with the flag left on cannot repeat 103 calls per restart). A restart with the flag left on costs about 103 calls the first time that day and nothing after; the status screen shows `force_full_list_enabled`.

Limits. At most `FULL_LIST_MAX_ATTEMPTS_PER_DAY = 2` attempts per module per Colombo day (constant in `server/services/zoho-sync.js`), so a bad slot cannot repeat itself in every slot. A **second** attempt in a day starts only if `live_available >= P` (§5.3), where P is the page count of the last ok list of that module (43 for headers, 60 for bundles today): it may draw on the day reserve, once per module per day, which is the price of not leaving the screen blank. `suspect_short_list`, `daily_cap_reached` and `too_many_bad_rows` are **not** retried: a second attempt would repeat the same 43 calls and get the same answer; they raise their `error` log and show on the status screen (`last_full_list`). Level 1 survives one missed night, because `full_list_old` needs 50 h and 02:00 and 03:00 on two consecutive nights give four attempts before it trips.

**Row quarantine (round-6 B6, elevated from round-5 N1).** One bad row must never blank the screen for everyone. A list page fails as a whole (`status='failed'`, `error='bad_shape'`) **only** when the response is not JSON, has no array under the module key (`salesorders` / `bundles`), or has no `page_context`. **Every other defect is a row defect and never fails the page or the run.** A list row is **quarantined** when any of these holds:
1. it is not a JSON object (`not_object`);
2. its id key (`salesorder_id` / `bundle_id`) is missing or blank (`no_id`);
3. a key of the **sync's own per-row required keys** is absent from **that row's own keys** (`missing_required:<key>`). Those keys are, for headers, `salesorder_id`, `salesorder_number`, `last_modified_time`, and for bundles, `bundle_id`, `reference_number` (round-7 N3). The sync does **not** use the column map's `required` list, which includes the list-only `quantity_shipped` (`config/zoho-columns.json:96`) written for the browser/xlsx pull; an absent `quantity_shipped` is handled by the present-keys rule, not quarantine. The sync checks every row; it does not copy the CLI's first-row-only check (`cli/import/run.js:86-89`);
4. `mapRow` throws on it: an unparseable time, a non-numeric quantity, an unsafe integer (`map_error`);
5. the handler throws while writing it (`write_error`). Each row is written inside its own SAVEPOINT (a nested `db.transaction`), so a throwing row rolls back alone and the rest of the page commits. The nested transaction re-throws after rolling back, so the page loop **must catch per row** (try/catch around each row's write) for the rest of the page to commit (round-7).

A quarantined row is **skipped**: nothing of it is written. It is appended to the run's `warnings` as `{row_quarantined, id, reason}` (the id and the reason code only, never the row body; at most 20 entries, then one final count), counted in the run's `rows_skipped` and in the log field `rows_quarantined`, and the run logs one `warn` `zoho_row_quarantined {module, count}`. **The run still ends `ok`, not `warning`:** W(m) moves only on an `ok` run (§5.2 "Delta watermark") and level 1 requires an `ok` run (§4), so a `warning` would leave the bad row inside every later delta window and rebuild the permanent stale screen this rule exists to stop. In a full list a quarantined row counts as *received* for the 95% rule, and its stored mirror row is left as it is and is **not** marked `missing_in_zoho` (it was in the list). **Per-SO fail-closed marking (round-7 B2).** When the quarantined **header** row carries `salesorder_number` or `salesorder_id` (this covers most `missing_required`, `map_error` and `write_error` rows) and a header for that SO exists locally, the handler sets `zoho_so_headers.row_quarantine_at = <the run's capture instant>` on it with one `UPDATE` (matched by `salesorder_number`, else by `zoho_id`). The identity is read from the **raw row**, not the mapped record (a `map_error` row has none), and is **trimmed exactly as `mapRow` trims a `raw` field** (`String(v).trim()`, `cli/import/columns.js:21`; `salesorder_number` is type `raw`, `config/zoho-columns.json:99`) before matching, so a padded value cannot silently mark nothing. The `UPDATE` is issued **after the row's SAVEPOINT has rolled back, in the page transaction**, never inside the savepoint: inside it the mark would be rolled back with the row, which would unfix B2 for the most plausible case, a row that violates a constraint on every run (AC98). While `row_quarantine_at` is not NULL, a **flag-eligible** SO's `flag_status` is `checking` (its stored flags are hidden, not shown on frozen data), it is counted in "being checked", and it is listed on the admin problems route with `reason='row_quarantined'` so a human can see which SO is stuck and for how long. The mark is cleared (`row_quarantine_at = NULL`) by the next list row for that SO that is written successfully, delta or full list: the `so_headers` handler adds `row_quarantine_at` to its field list when `ctx.source === 'sync'`, like `sync_state`, so an unchanged row still clears it. It is not a detail-queue reason (a detail fetch cannot repair a list row) and it does not change `detail_fail_count`. **Accepted residual:** a `not_object` row, or a row with neither `salesorder_number` nor `salesorder_id`, cannot be tied to any SO, so no SO is marked; and a quarantined **bundle** row is not marked per SO. That is safe for a *new* bundle (not mirrored, it can only delay `package_missing`) but **not** for a quarantined *update* to an existing bundle (quantity corrected down, status moved off `bundled`): `qty_bundled` stays overstated, the same false-`package_missing` exposure §3 accepts for deleted bundles, except that a permanently quarantining row is never marked `missing_in_zoho`, so the window is indefinite rather than 7 days. Accepted; no mechanism is added. Both remain visible only through the run's `warnings`, the log line and the status screen (`rows_quarantined_today`). No other SO or user is affected (AC98). **Systemic guard:** if a run quarantines at least 10 rows **and** more than 5% of the rows it read, it ends `failed` with `error='too_many_bad_rows'` (Zoho probably changed a key): W does not move, an `error` is logged, and it is not retried the same day. AC86.

**Consequences of the sync's own required keys (round-8).** A bundle row lacking `status` or `created_time` is now mirrored with NULLs rather than quarantined, since the sync no longer uses the column map's `required` list. A NULL `status` drops the bundle out of `bundle_pool` (`lower(status)='bundled'` is false), which can only lower `qty_bundled`; a NULL `date` bypasses the 2024 cutoff test (`cli/import/run.js:99` skips only a non-empty date before the cutoff), so that row is written.

**Record cutoff (round-5 N5, round-6 N9).** The sync applies the same 2024-01-01 Colombo cutoff as the CLI (`cli/import/run.js:8,99`): a list row whose `order_date` (headers) or `date` (bundles) is earlier is not written and is counted in `rows_skipped`. So pre-2024 open SOs are never in scope. The 95% rule compares the rows that pass the cutoff with the local count of non-missing SPS headers, which the same cutoff already shaped (AC95).

**Run rows and `runSweep` (critic round 3 N6).** Every sync run row writes `changed_so_numbers` as a JSON array of the SO numbers it touched (`[]` when none). `runSweep` processes finished rows with `processed_at IS NULL` (`sweep.js:56-80`), so it will also process the ≈170 sync rows a day; with no `job_so_links` rows for them this changes nothing, and it must not throw. In a sync run `rows_read` counts every row received, `rows_upserted` counts the rows whose write changed something (the handler returned a non-empty touched set), and `rows_skipped` counts cutoff-skipped and quarantined rows. `rows_upserted` is therefore **not** Release 0's rows-processed count (`run.js:80`) (round-6 N2, AC8). A sync run's `error` column holds only a code from a fixed set (`rate_limited`, `auth`, `upstream`, `bad_shape`, `delta_incomplete`, `daily_cap_reached`, `suspect_short_list`, `too_many_bad_rows`, `crashed`, `detail_outage`), never `err.message` or any part of a response (round-6 N10, AC91).

**In-scope SOs** (rows in `zoho_so_headers` with `org='SPS'` and `sync_state` not `'missing_in_zoho'`) are those that are flag-eligible, **or** open (§2, "Open SO", from API fields; round-4 B2), **or** already have `detail_fetched_at` set (so a loaded job keeps updating until it closes). Closed SOs created before the cutoff that were never loaded are never fetched (critic simpler alternative). A pre-cutoff SO with API status `partially_shipped`, `shipped`, or `fulfilled` but not fully invoiced is open, so it is in scope (AC68).

**The detail queue** is derived from the DB, with no queue table. An in-scope SO whose `detail_fail_count < DETAIL_FAIL_LIMIT` is queued when any of these holds:
- (a) `detail_fetched_at IS NULL` (never loaded);
- (b) `detail_fetched_at IS NOT NULL AND H.captured_at > H.detail_fetched_at` (the header row changed after the last detail fetch; Rev 5, the lead's per-job rule);
- (c) `detail_fetched_at IS NOT NULL AND H.modified_at > H.detail_modified_at` (the SO changed in Zoho);
- (d) `detail_fetched_at IS NOT NULL AND H.detail_sig` ≠ the current signature of H. The signature is `quantity|quantity_packed|quantity_shipped|quantity_invoiced|status|shipped_status|invoiced_status` of the header row, **stored as the pipe-joined field values in that order, not hashed** (round-11; debuggable): each value is `String(v)` of the stored value with NULL as the empty string, for example `1000|100|100|100|partially_shipped|partially_shipped|partially_invoiced`. A NULL or non-matching `detail_sig` on a loaded SO is a refresh reason, so every fixture that seeds a loaded SO must store a matching signature. Only the list writes these seven fields (the detail path never does, handler step 1), so (d) is a **second net** behind V4's gate: it catches a list-reported quantity or status change that did not move `last_modified_time` and was first seen by the nightly full list. It is not the primary path and does not replace V4 (§3, round-6 B2);
- a **confirmation** is due: a job of H meets points 1–3 of the stored-flag definition (§4) for some rule, and `H.detail_fetched_at < threshold_instant` of that rule;
- a **re-confirmation** is due: a job of H has a stored flag (§4, points 1–4; no freshness term) and `H.detail_fetched_at + 20 h < now`.

(a)–(d) are the **refresh reasons**. A loaded **flag-eligible** SO with a refresh reason has `flag_status='checking'` (§4); for any other SO the reasons only queue the refresh. The "not NULL" guards on (b)–(d) mean a never-loaded SO has exactly one reason, so its NULL `detail_sig` cannot move it out of the history lane (critic round 3 N3). An SO with `detail_fail_count >= DETAIL_FAIL_LIMIT` is in none of P0–P5; it is only in the retry lane PR ("Backoff retry" below).

**Two lanes (critic round 2 B1).**
- A queued SO is **history** when all of these hold: its only reason is (a), it is not flag-eligible, and the Colombo date of `H.created_at` is more than 7 days before today. Every other queued SO is **live**.
- So an SO created or changed today is always live, whether or not `PD_FLAGS_SINCE` is set.

**Queue order** (critic B1c). Within each priority, `H.modified_at` descending:
- live lane:
  - P0: confirmations;
  - P1: flag-eligible SOs with a refresh reason;
  - P2: re-confirmations, at most `RECONFIRM_DAILY_MAX = 30` requests per Colombo day (constant in `server/services/zoho-sync.js`), counted as Σ `api_calls` of today's `so_detail_reconfirm` runs;
  - P3: other live SOs, non-legacy before legacy. This includes refreshes of pre-cutoff SOs that are already loaded (round-6 N9): they are **not** in the §5.5 plan. Within one cycle P3 runs after P0–P2, but that is **not** a guarantee across slots: morning P3 spending lowers `live_available` for a later slot, so a 14:00 P0 confirmation can wait behind it (round-7 N2); the wait is measured (`oldest_p0_wait_min`, `p3_calls_today`) and delays a flag, never shows a false one;
  - PR: sync-problem retries ("Backoff retry" below), last in the live lane;
- history lane:
  - P4: non-legacy history SOs;
  - P5: legacy history SOs.

An SO with several reasons takes its highest priority. When P2 has reached `RECONFIRM_DAILY_MAX`, the remaining P2 SOs wait until the next Colombo day; their flags stay shown with the older `checked_at`, and one `warn` log `zoho_reconfirm_limit_reached` is written that day.

**Per-SO detail failures (Rev 5 lead decision; round-4 B1).** Each detail request has exactly one outcome:

| Outcome | When | Effect (one `IMMEDIATE` transaction per SO) |
|---|---|---|
| `ok` | 2xx and the shape check passes | the `so_detail` handler below; also `detail_fail_count = 0`, `detail_last_error = NULL`, `detail_last_error_at = NULL`, `detail_outage_hits = NULL` |
| `not_found` | HTTP 404 **and** the body's `code` equals `ZOHO_SO_NOT_FOUND_CODE` (constant in `server/zoho/client.js`, value recorded by V3) | the header gets `sync_state='missing_in_zoho'` at once (round-4 B1a) and `detail_fail_count = 0`; the SO number is recorded as touched. Its lines stay in the table and are excluded from every job query (§5.4), so its jobs are gone from every list from the end of that cycle. It leaves the in-scope set, so it is never requested again unless a later delta or full list returns it (which sets `sync_state=NULL`, §5.2). |
| SO failure | HTTP 5xx (`upstream_5xx`); no response within 30 s (`timeout`); HTTP 404 with any other body code (`http_404_other`); any other 4xx except 401 and 429 (`http_4xx`); a non-JSON body or a failed shape check (`bad_shape`); an exception thrown while the handler wrote that SO (`handler_error`, round-6 B3: a `mapRow` error, a constraint violation or any other exception) | nothing is written for that SO's lines or header fields (for `handler_error` its transaction is rolled back, header included); the SO number and reason go into the run's `warnings` (for `handler_error` also the first 120 characters of the exception message, never a response body); the count is applied at the end of the cycle (below). `handler_error` is counted exactly like `bad_shape`, so a line that always throws cannot keep its SO re-requested every cycle for ever with `detail_fail_count` stuck at 0 (AC83) |
| cycle stop | 401 after the one refresh-and-retry, 429, the daily cap, a lost lease | the existing handling (Failure modes); **not** counted against the SO |

- **Counting.** At the end of the cycle, every SO with an SO failure in that cycle gets `detail_fail_count + 1`, `detail_last_error = <reason>`, `detail_last_error_at = <capture time of the failed request>`, **except** a failure of class `upstream_5xx` or `timeout` in a cycle that ended `detail_outage` (below) for an SO whose `detail_outage_hits`, after this cycle's increment, is still below 3: that failure is suppressed (`detail_fail_count`, `detail_last_error` and `detail_last_error_at` are not touched). An SO is requested at most once per cycle, so a count only rises once per cycle.
- **Outage guard.** A cycle whose header delta did not end `ok` sends no detail request. Within a cycle, after 3 consecutive detail requests that ended `upstream_5xx` or `timeout`, the cycle sends no further detail request; its current detail run ends `warning` with `error='detail_outage'`, and the cycle sets the `settings` key `zoho_detail_outage_pending`. This keeps a short Zoho-wide outage from turning healthy SOs into sync problems. **Lane PR retries are excluded from the consecutive counter** (they neither add to it nor reset it), so one live failure plus two PR retry failures in a healthy system cannot trip `detail_outage` and cost that cycle its history lane (round-8 gap; PR failures are counted normally, as retries).
- **Per-SO outage counter (Rev 8; replaces Rev 7's cycle-level `outage_streak`, which is deleted, and its overloading of `zoho_import_runs.file`, a column the admin Imports screen renders).** New nullable column `zoho_so_headers.detail_outage_hits INTEGER` (NULL reads as 0), in 005. It counts the cycles in which that SO's `upstream_5xx` or `timeout` failure was suppressed by the guard. Each such failure adds 1, up to a maximum of 3: the value **stops at 3** and does not keep rising once failures are counted (AC97(a) asserts "still 3" at the reset). The cycle-end accounting for one SO (the hits increment plus `detail_fail_count`, `detail_last_error` and `detail_last_error_at`) is **one transaction per SO**. `detail_outage_hits` is in no `upsertGuarded` field list (it is written by its own `UPDATE`), unlike `sync_state` and `row_quarantine_at`. An `ok` detail response for that SO sets it to NULL (nothing else resets it, not even the recovery reset below). When the new value reaches 3, that SO's failure is **counted normally** from then on (Counting above): it takes `detail_fail_count` forward and at `DETAIL_FAIL_LIMIT` becomes a sync problem and leaves lanes P0-P5. `detail_fail_count` keeps its Rev 5 meaning and is untouched in outage cycles until then. This is what guarantees progress: genuinely broken SOs at the head of the queue (or behind fresher P1 work; a broken SO's `modified_at` stops moving while the queue sorts `modified_at` descending, so in production they sort behind) cannot freeze the cycle for ever. The state sits next to `detail_fail_count`, where every other per-SO fact of this design lives.
- **The honest limit.** During a sustained Zoho-wide detail outage this converts **3 SOs per 5 cycles** (about 0.6 per cycle, about 40 over a full outage day of 66 cycles): cycles 1 and 2 suppress, cycle 3 counts, cycles 4 and 5 count, the trio is converted at the end of cycle 5, and the next trio starts at cycle 6. It is bounded by the queue, not by three. The per-SO counter does not prevent that; it only bounds it (without suppression a 45-minute blip would convert 3 SOs per cycle instead of 0.6, so the guard bounds the damage and the reset repairs it; the pairing is deliberate and is not to be simplified to either half). The recovery reset below is what removes the damage.
- **Automatic recovery reset (Rev 8, lead addition; Rev 9 fixes).** In the first cycle that produces an `ok` detail response after a cycle that ended `detail_outage` (the `settings` key `zoho_detail_outage_pending` is set), and that does not itself end `detail_outage` (a tripped guard means the channel is still failing), the cycle end runs, before applying this cycle's own failures, **one `IMMEDIATE` transaction** containing all three of: (1) `UPDATE zoho_so_headers SET detail_fail_count = 0, detail_last_error = NULL, detail_last_error_at = NULL WHERE org = 'SPS' AND sync_state IS NOT 'missing_in_zoho' AND detail_last_error IN ('upstream_5xx','timeout')` (so a header marked missing that still carries an old error is neither reset nor counted in `reset: n`); (2) the `DELETE` of `zoho_detail_outage_pending`; (3) the write of `zoho_recovery_reset_day` = today's Colombo date. It then logs one `info` `zoho_detail_recovery_reset {reset: n}`. Both `settings` keys are written with the existing `INSERT ... ON CONFLICT(key) DO UPDATE SET value = excluded.value` pattern and a **non-empty** value (`settings.value` is `NOT NULL`, `001-schema.sql:129`, so a bare `INSERT INTO settings(key)` would throw); the pending key's value is the instant the outage cycle ended. It includes SOs already at `DETAIL_FAIL_LIMIT`. Only the transient classes are reset; `http_404_other`, `http_4xx`, `bad_shape`, `handler_error` and `row_quarantined` are real defects and stay. It is idempotent and needs no human. **Daily limit:** at most **once per Colombo day**, so an SO that is permanently 5xx cannot make the reset loop: it re-converts after 3 counted failures (its `detail_outage_hits` is still 3, so its very next failures count) and stays converted until the next day, at the cost of a few frozen cycles a day. **`zoho_detail_outage_pending` is deleted only by a reset that actually runs.** When a qualifying cycle is blocked by `zoho_recovery_reset_day`, the pending key survives, and the **first qualifying cycle of the next Colombo day** performs the reset (so a three-SO blip that spent the day's reset at 06:15 cannot leave a 14:00 outage's conversions without an automatic heal). A second outage on the same day heals through lane PR or `ZOHO_RESET_SYNC_PROBLEMS` **until the next Colombo day's reset**. Written with the real mechanism: a Zoho-wide detail outage converts 3 SOs per 5 cycles while it lasts; when Zoho recovers, the first qualifying cycle clears every SO whose last error was `upstream_5xx` or `timeout`, so the converted set heals in one cycle rather than through lane PR (AC97).
- **The `zoho_detail_outage` error log (round-9 loose end; AC77).** A cycle *ended `detail_outage`* when a detail run of that cycle has `error='detail_outage'`. A cycle's runs are those started between its header-run's `started_at` (the `so_headers` run, delta or full list) and the next header run's `started_at`. The log fires once per outage episode, at the end of the cycle that makes the newest three such cycles all `detail_outage` while the cycle before them was not; a healthy cycle ends the episode, so a re-conversion after a recovery reset is a new episode and logs again (AC97(a)). This is derived from the run rows, needs no counter and survives a restart; the `zoho_import_runs.file` column is not used.
- **Sync problem.** When `detail_fail_count` reaches `DETAIL_FAIL_LIMIT` (3), the SO leaves lanes P0–P5 (it is retried only by lane PR, below), its jobs show `flag_status='sync_problem'` (§4), it appears on the admin "Sync problems" list (§6), and one `error` log `zoho_detail_sync_problem {salesorder_number, reason, detail_fail_count}` is written (R10: this is the "IT notified").
- **Backoff retry (Rev 6, round-6 B1; replaces the Rev 5 "24 h, night slots only, 10 a day" retry).** A failure counter that a code rollback does not reset, and that three quick failures in a 45-minute Zoho blip can fill for every queued SO, must heal by itself. After each counted failure the SO's next try is `detail_last_error_at + delay(n)`, where n is the new `detail_fail_count`: `delay(1) = delay(2) = 0` (the next cycle, as in Rev 5, so the first three attempts are unchanged), and for n ≥ 3 `delay(n) = min(15 min × 2^(n−3), 6 h)`, that is 15, 30, 60, 120, 240, then 360 min. An SO with n ≥ 3 (a sync problem) is retried in the **retry lane PR**, in the first slot, day or night, whose start is at or after `detail_last_error_at + delay(n) − 5 min` (the 5 min lets a slot exactly one delay later qualify, whatever second the failed request was answered). PR is the last group of the live lane (§5.3), oldest `detail_last_error_at` first, at most 2 requests per cycle and at most `PROBLEM_RETRY_DAILY_MAX = 10` requests per Colombo day (constant in `server/services/zoho-sync.js`; counted as Σ `api_calls` of today's `so_detail_retry` runs). A retry's outcome is applied as above: `ok` returns the SO to normal at once (count 0, off the list, `flag_status='current'` at the end of that cycle); `not_found` marks it missing; a failure raises n and moves `detail_last_error_at`, so the next delay is longer. A 45-minute blip therefore costs an SO's flags 15 minutes after Zoho recovers, not a day (AC73). The problems route shows `next_retry_at = detail_last_error_at + delay(n)` (§6).
- **Reset lever (Rev 6, round-6 B1).** With `ZOHO_RESET_SYNC_PROBLEMS=true` in the env file, scheduler start-up runs one statement before its first cycle: `UPDATE zoho_so_headers SET detail_fail_count = 0, detail_last_error = NULL, detail_last_error_at = NULL WHERE org = 'SPS' AND detail_fail_count > 0`. It logs one `warn` `zoho_reset_sync_problems {reset: n}`. It needs no hand-written database write and is idempotent (a second start finds nothing to reset). It is the 2am recipe after a bad build: roll back the code, set the flag, restart, then set the flag back to `false`. A flag left on only re-queues problem SOs at each start, at most 3 requests each; the status screen shows `reset_sync_problems_enabled`. It is an operator lever in the env file, not a screen action (Non-goals; AC74).
- **Cost bound.** A failing SO costs at most 3 requests before it becomes a sync problem (one per cycle), then at most 4 a day at the 6 h delay (about 7 on its first day), all inside `PROBLEM_RETRY_DAILY_MAX` per day across every SO. A build that fails every detail costs at most 3 requests per queued SO until the code is fixed, and at most 10 requests a day after that; the reset lever then clears the counts at once.

**`so_detail` handler.** It runs one `IMMEDIATE` transaction per SO:
0. **Shape check** (replaces the column map's `required` list for the detail object): the body parses as JSON, `salesorder` is an object, `salesorder.salesorder_id` and `salesorder.salesorder_number` are non-empty and `salesorder.salesorder_number` equals H's number, and `salesorder.line_items` is an array whose every element is an object with a non-empty `line_item_id`, an `item_type` key, and whose `tags`, when present, is an array of objects; **and every line with `item_type='inventory'` (a job line) carries all seven quantity keys `quantity`, `quantity_cancelled`, `quantity_picked`, `quantity_packed`, `quantity_shipped`, `quantity_delivered` and `quantity_invoiced`, each numeric, meaning `toNumber` yields a non-null number (`shared/text.js:13-17`), so a JSON number and a numeric string both pass; `typeof v === 'number'` is wrong because Zoho sends numeric strings for some fields** (round-7 B3: fail closed, because a NULL quantity reads as 0 and would raise a false flag). A missing quantity key on a job line is `bad_shape` for the whole SO: nothing is written, the stored quantities stay, the count rises (AC96). Otherwise the outcome is `bad_shape` and nothing is written. Any exception after this check (a `mapRow` error, a constraint violation, anything) rolls the SO's transaction back and is the outcome `handler_error`.
1. Overlay `salesorder.custom_field_hash` onto the object (top-level keys, where absent), then upsert the header with `source='sync'` and `sync_state=NULL` through the `so_headers` column map (`config/zoho-columns.json:94-124`), without its `required` check. Only fields that are **detail-writable** *and* whose **source key** is present in the object before mapping are written; fields whose source key is absent are left untouched (this avoids the null-out at `upsert.js:19-21`; critic round 3 N5).
   - **Detail-writable** header fields: `zoho_id`, `order_date`, `expected_shipment_date`, `reference_number` and the twelve `cf_*` fields.
   - **List-owned** fields, never written by the detail path (round-6 N8): the seven signature fields `quantity`, `quantity_packed`, `quantity_shipped`, `quantity_invoiced`, `status`, `shipped_status`, `invoiced_status`, plus `total_cents`, `created_at` and `modified_at`. The real detail has **no** header `quantity`, `quantity_packed`, `quantity_shipped` or `quantity_invoiced` at all, only `total_quantity` (`salesorders_since_2026-09-15.json:70`), so those four are list-derived whatever is done. If the detail also wrote the three status fields, `detail_sig` would be list-derived for quantities and detail-derived for statuses, any list/detail disagreement (V3(b)) would be systematic, and every in-scope SO (about 1,400 or more) would be re-fetched every night and flipped to `checking`. With only the list writing the seven fields, the header signature changes only when Zoho's list says something changed.
2. Upsert every line of `salesorder.line_items` into `zoho_so_line_items` through `upsertGuarded`, with keys `(org, line_item_id)`; each record is `mapRow(so_line_items, line)` ("Line column map") plus `division_tag`, `org` and `salesorder_number`; the field list given to `upsertGuarded` is restricted to fields whose source key is present in that line (round-7 B3; for job lines the shape check already guarantees the seven quantities). `rate`, `item_total` and every other price field are **not** stored.
3. Maintain the observed times for each of picked, packed, shipped and invoiced, where `before` is the stored row (or none):
   - `seen_at`: `NULL` when `qty = 0`; else `before.seen_at ?? capturedAt`;
   - `changed_at` (packed, shipped, invoiced): `NULL` when `qty = 0`; else `capturedAt` when `before` is none or `qty > before.qty`; else `before.changed_at`.
4. **Delete** the SO's rows whose `line_item_id` is not in the response.
5. Set on the header: `detail_fetched_at = capturedAt`, `detail_modified_at = H.modified_at`, `detail_sig =` the signature of the header row **after** step 1, `detail_fail_count = 0`, `detail_last_error = NULL`, `detail_last_error_at = NULL`, `detail_outage_hits = NULL`. After this step `detail_fetched_at >= captured_at`, so the SO has no refresh reason unless the signature or `modified_at` differ.
6. Return the SO number as touched.

**5.3 Schedule**

The scheduler is `server/services/zoho-sync.js`, started from `server/app.js` like `startSweepTimer` (`app.js:21`, `sweep.js:88-93`). It uses a `setTimeout` chain and no new dependency. The chain **aligns to the wall clock** (round-6 N6): each timeout is computed to the next slot boundary in Colombo time (:00, :15, :30, :45 in day slots, :00 in night slots), never as "now + 15 min", so slots do not drift. A process start at 06:07 waits for the 06:15 boundary and runs no immediate cycle, except that a due first-cycle or forced full list (§5.2) runs at that boundary. Slots missed while the process was down are not replayed one by one: the delta watermark covers the gap in a single run (§5.2), so a restart never bursts (AC94).

| When (Colombo) | Runs |
|---|---|
| Every 15 min, 06:00–20:00 (57 slots, the **day slots**) | SO header delta; at :00 and :30 also the bundles delta (29 slots); then **live** detail calls (P0–P3, then sync-problem retries PR) up to the per-cycle limit. No history calls. |
| Every 60 min, 21:00–05:00 (9 slots, the **night slots**) | SO header delta, bundles delta, then live detail calls (P0–P3, then PR), then **history** detail calls, up to the per-cycle limit |
| 02:00 daily (in the 02:00 night slot, before its deltas) | SO header full list (attempt 1 of at most 2; a retryable failure is retried in the 03:00 slot, §5.2 "Full-list attempts"), then the `missing_in_zoho` reconcile (§5.4) |
| 03:00 Sunday (in the 03:00 night slot, before its deltas) | bundles full list, then its reconcile (§5.4). Night slots run on the hour only, so there is no 02:30 slot (round-5 N6). |
| First cycle after a start, when due | the first-cycle or forced full lists (§5.2 "Full-list attempts"), at the next slot boundary |

Night deltas close the "hidden every night" gap (critic N4): the freshness limits in §4 allow for the hourly night cadence.

**Detail calls per cycle** (critic B1a, rewritten for critic round 2 B1). Definitions, all per Colombo day:
- `used` = calls counted today (§5.5), re-read before each lane and before each priority group within the night live lane;
- `list_reserve` = the list calls still scheduled for the rest of the day: 1 per remaining header-delta slot + 1 per remaining bundles-delta slot + 43 if a header full list is still due today (§5.2 "Full-list attempts": its 02:00 slot has not run, or a first-cycle, retry or forced attempt is pending and has not completed) + 60 if a bundles full list is still due today (the Sunday 03:00 slot has not run, or a first-cycle or forced attempt is pending). A **second** attempt of a day is not reserved; it is funded from `live_available`;
- `DAY_DETAIL_RESERVE` = 130, a constant in `server/services/zoho-sync.js` (the ≈80 changed-SO fetches + ≈20 confirmations + 30 re-confirmations of §5.5; the ≈3 first attempts of failing SOs fit in the estimate's rounding);
- `day_reserve_left` = `max(0, DAY_DETAIL_RESERVE − Σ api_calls of today's 'so_detail' and 'so_detail_reconfirm' runs started in day slots)` while at least one day slot of today is still to come or running; `0` after the 20:00 slot has run;
- `retry_reserve_left` = `max(0, PROBLEM_RETRY_DAILY_MAX − Σ api_calls of today's 'so_detail_retry' runs)` while at least one day slot of today is still to come or running; `0` after the 20:00 slot has run. It carves the retries' own daily allowance out of the history allowance, so the night history load cannot eat those calls (round-6 B1). It does **not** guarantee that PR gets them: PR is the last group of the live lane, behind the per-slot cap of 20 and behind P0-P3, so on a busy day a retry can wait (round-7 N7); the status screen shows `pr_due`;
- `live_available = cap − used − list_reserve − 60` (the 60 is a margin that is never planned for);
- `history_available = cap − used − list_reserve − day_reserve_left − retry_reserve_left − 60`.

Per cycle, after the deltas (and only if the header delta, or the header full list that took its place, ended `ok`; §5.2 outage guard):
1. Live lane:
   - day slot: `min(live_available, 20)` requests, in this order: P0, then P1, then P2 (within its daily maximum), then P3, then PR (at most 2 requests, within `PROBLEM_RETRY_DAILY_MAX`);
   - night slot, in this order:
     - P0 up to `min(live_available, 250 − all calls made in this cycle)`;
     - **P1 up to `min(history_available, 250 − all calls made in this cycle)`** (round-6 B4: the 02:00 full list rewrites every header whose fields changed, which moves `captured_at` and puts each flag-eligible one in P1, so night P1 shares the history allowance and cannot draw on the day's reserve);
     - P2 up to `min(live_available, 250 − all calls made in this cycle)`, within its daily maximum;
     - P3 up to `min(history_available, 250 − all calls made in this cycle)` (round-4 non-blocking 4);
     - PR up to `min(live_available, 2, PROBLEM_RETRY_DAILY_MAX − retry calls today, 250 − all calls made in this cycle)`.
2. History lane (night slots only): `min(history_available, 250 − all calls made in this cycle)` requests, P4 before P5. In a day slot the history lane sends 0 requests, whatever the budget.
3. A lane or group whose allowance is `<= 0` sends nothing; the deltas still run. `used` is re-read before each group.

What this guarantees:
- The deltas can never be starved by detail work: `list_reserve` is subtracted from every lane. The only way a delta is skipped is the hard cap (§5.5), which the reserve keeps out of reach unless the estimates in §5.5 are wrong. The one deliberate exception to "reserve first" is a second full-list attempt (§5.2), which may draw on the day reserve once per module per day.
- History, night P1, night P3 and the day's retries can never eat the day's live budget. At 00:00 on a weekday at cap 400, `history_available = 400 − 0 − (66 + 38 + 43) − 130 − 10 − 60 = 53` (the 10 is `retry_reserve_left`). From 01:00 to 05:00 `used` rises by exactly what `list_reserve` falls, so history and night P1 get ≈0 more. **Night P1, night P3 and history share that one allowance, P1 first.** Night P0 (bounded by the flags that fall due, about 20 a day) and night P2 (bounded by `RECONFIRM_DAILY_MAX = 30`) are the only night detail work drawn from the day reserve rather than from the history allowance. So at 06:00, `live_available ≥ DAY_DETAIL_RESERVE − (night P0 spend + night P2 spend)`: at least 80 on the §5.5 estimates, and 130 when there was none. Night P1 that the allowance cannot fund waits for the day slots (up to 20 requests a slot from 06:00) and shows "checking with Zoho…" meanwhile (AC72). Any part of the day reserve not spent by 20:00 flows to history in the 21:00–23:00 slots.
- A new flag-eligible SO created during the day is fetched in the first day slot after its header delta, because its P1 entry sits in the live lane.
- No single SO can hide the screen or another SO's flags: level-1 freshness reads no queue (§4), a failing SO leaves lanes P0–P5 after 3 attempts, and a malformed list row is quarantined without failing its run, while the SO it belongs to (when identifiable) goes to `checking` instead of showing flags on frozen data (§5.2 "Row quarantine"; accepted residual for unidentifiable rows stated there).

**Single flight.**
- Before a cycle, the process takes a lease: `settings` key `zoho_sync_lease` holds `{owner:pid, until:now+10min}`.
- The lease is taken by an atomic `INSERT … ON CONFLICT DO UPDATE … WHERE json_extract(value,'$.until') < now`. If no row changes, the process skips the cycle.
- After **every** request the holder renews the lease (`until = now+10min`) with an `UPDATE … WHERE json_extract(value,'$.owner') = :pid`, and in the **same transaction** increments the current run row's `api_calls` by 1 (critic round 3 N4; the increment follows the response, it does not precede the request). If the renewal changes no row, the cycle stops at once (critic N5).
- No cycle sends more than 250 requests (at 30/min that is at most about 8.4 min, inside one lease period even without renewal).
- The lease is released at the end of the cycle.

**Crash recovery.** At the start of every cycle, sync runs with `finished_at IS NULL AND started_at < now − 30 min` are closed with `status='failed', finished_at=now, error='crashed'` (the same shape as `freshness.js:27-28`). Their `api_calls` already hold every request sent before the crash (per-request increment above). SO failures of a crashed cycle are not counted (the count is applied at cycle end); those SOs are simply retried.

**Manual imports while the sync is on** (critic N8). The CLI (`cli/import/run.js`) refuses an SPS import of module `so_headers` or `bundles` when the DB has a `zoho_import_runs` row with `org='SPS'`, `source='sync'`, `status='ok'` of **any module** finished in the last 7 days (the guard exists to stop a manual import colliding with an active sync, and any recent ok sync run means the sync is active; the implementation must not filter by module). It exits non-zero with `sync_active: SPS so_headers/bundles are owned by the sync` and writes nothing. xlsx SO imports stay allowed: they only write headers that are absent or xlsx-sourced (`upsert.js:51-53`) and never touch `zoho_so_line_items`.

**5.4 Deletions**
- The delta cannot see deletions.
- **SO headers.** After a header full list that earned `full_list=1`, every SPS header that is not in the list gets `sync_state='missing_in_zoho'`, whatever its `source` (xlsx, pull or sync). Every header in the list gets `sync_state=NULL`. A header wrongly marked because it was modified while the list was paged is cleared by the next delta (§5.2, `sync_state` on write). A detail `not_found` marks the header at once (§5.2), without waiting for the full list. A header that was quarantined during the list (§5.2 "Row quarantine") counts as present: it is not marked.
- Lines of missing SOs stay in the table but are excluded from every job query.
- **Bundles** (critic N6). After a bundles full list that earned `full_list=1`, every SPS bundle not in the list gets `sync_state='missing_in_zoho'`; every bundle in the list gets `sync_state=NULL`. Missing bundles are excluded from `bundle_pool` (§2). The same delta clearing applies. Bundle deletions are therefore seen weekly only (§3 exception; round-4 N3).

**5.5 API budget (SPS, per Colombo day)**

| Use | Calls/day |
|---|---|
| SO header delta, 57 + 9 = 66 slots × ≥1 page | 66 (+1 page per 200 changed SOs in a slot) |
| Bundles delta, 29 + 9 = 38 slots × ≥1 page | 38 |
| SO header full list, about 8,400 SOs ÷ 200 | 43 (grows by 1 per 200 new SOs) |
| Live lane: SO detail for new and changed SOs, about 13 new SOs/day × about 6 changes each (estimate; instrumented in the status screen) | about 80 |
| Live lane P0: confirmations (estimate: at most 3 rules per flag-eligible line reaching a threshold; instrumented) | about 20 |
| Live lane P2: re-confirmations, 1 call per SO with a stored flag every 20 h (≤ 1.2 calls per flagged SO per day), hard-limited by `RECONFIRM_DAILY_MAX` | at most 30 (= 25 flagged SOs × 1.2; beyond 25 flagged SOs the extra wait a day, §5.2) |
| Live lane: first attempts of a failing SO, 3 per newly failing SO (estimate ≤ 1 per day; instrumented as `sync_problems`) | about 3 |
| Bundles full list (Sunday only, and once at first start), 11,898 ÷ 200 (`2026-09-19/sps/README.md:17`) | 60 |
| **Steady total** | **about 280 (weekday), about 340 (Sunday)** |
| Margin never planned for | 60 |
| `DAY_DETAIL_RESERVE` (§5.3): the four live-lane rows above (≈133), protected from history | 130 (inside the steady total) |
| Sync-problem backoff retries (any slot, lane PR; not in the steady total: `retry_reserve_left` carves them out of the history allowance, §5.3) | at most 10 (`PROBLEM_RETRY_DAILY_MAX`); about 4 for one problem SO at the 6 h delay |
| Second full-list attempt after a retryable failure (§5.2), at most one per module per day, funded from `live_available`, not planned | 43 (headers) or 60 (bundles) on a bad day only |
| P3 refreshes of loaded pre-cutoff SOs (round-6 N9; **unmeasured, not planned**): only what P0–P2 and the day reserve leave; instrumented as `p3_calls_today` | unknown; AC38(a) catches an overspend |

- **Headroom check.** Steady total + margin = 340 (weekday) and 400 (Sunday), both ≤ the default cap of 400. Retries and history take only what the cap leaves after that, so they can never push the planned total over the cap. A second full-list attempt is the one unplanned draw on the day reserve, and only after a failure. **On Sunday the planned total already equals `cap − 60`** (340 + 60 = 400 at cap 400), so the 10 retries, any P3 work and any second attempt displace planned live detail work that day; nothing planned is added, and the deltas stay protected by `list_reserve` (round-7).
- **History load (backfill).** The history lane runs in night slots only and gets what the cap leaves after the list reserve, the day detail reserve, the retry reserve, the margin, night P1 and night P3: at the default cap of 400, about 53 at 00:00 on a weekday (0 on Sunday: 3 less the 10 retry reserve), plus any unspent day reserve at 21:00–23:00; at cap 500, about 153 (93 on Sunday) plus the same. In queue order (P4 before P5), the non-legacy history SOs load first. Open SOs created in the last 7 days and all flag-eligible SOs are live, not history, so they load in the day. The number of in-scope SOs is only known after the first full list: the "about 1,400 open" figure (`scout-sps.md:72-74`) uses the xlsx status vocabulary and understates the API-defined open set (§2), which also includes pre-cutoff SOs that are shipped or fulfilled but not fully invoiced. The first full list logs `in_scope_sos`, `non_legacy_to_load`, a per-status census and an ETA in days for each group. Q11 asks whether the cap may be 500 during the history load; Q14 asks what to do if the in-scope count is far larger than expected.
- **Hard cap.** `ZOHO_DAILY_CALL_CAP` (default 400) is counted as Σ `zoho_import_runs.api_calls` for `org='SPS'`, `source='sync'` on the current Colombo day. It counts every attempted request to `zohoapis.com`, including failed ones. `api_calls` is incremented after each response, in the lease-renewal transaction (§5.3), so a crash loses at most the one request in flight.
- **At the cap**, all sync stops until the next Colombo midnight. Freshness then goes stale, so flags hide (fail closed), and an `error` log is written: `zoho_daily_cap_reached`.
- **Token refreshes** (at most about 24 a day) go to the accounts server. They are logged but not counted against the Inventory cap.
- **Daily quota.** The 1,000/day per-org figure is an assumption (`Production Dashboard/CLAUDE.md:52`). The same SPS org quota is also drawn on by the planned INV services (500/day each, `/root/CLAUDE.md` §2). Q1(b) asks for the org-wide total and who else draws on it.

**5.6 Sync failure handling:** see the failure-mode table.

### 6. API and UI

**New router** `server/routes/jobs.js`, registered in `routes/index.js`. Every route is `GET`, behind `requireAuth`.

| Route | Roles | Returns |
|---|---|---|
| `GET /api/jobs?state=open\|all&division=CODE&missing=1&legacy=1` | manager, gm, admin | `{ freshness:{fresh, reason, as_of}, history:{loaded, in_scope}, flags_since, counters_complete, counters:{due_3d, past_due, in_production, produced_not_shipped, docs_missing} (each null when not fresh), checking:{being_checked, sync_problem} (each null when not fresh), jobs:[JobDTO] }`. Without `legacy=1`, legacy jobs are left out of `jobs`. `legacy=1` **includes** legacy jobs alongside the others (it does not return only legacy jobs, AC48). `state=all` does **not** bring legacy jobs back: legacy is a separate axis from open/closed (round-11). |
| `GET /api/sales-orders/:number` | manager (only if at least one visible line), gm, admin | `{ salesorder_number, customer, due_date, status, lines:[JobDTO incl. other divisions], non_job_lines:int }`. Returns 404 when the SO is unknown, `missing_in_zoho`, has header `status='draft'` (§2), **or** is not visible to a caller whose role is allowed (all indistinguishable). A caller whose roles are not `manager`, `gm` or `admin` (for example `coordinator` only) gets **403**, not 404 (round-11). |
| `GET /api/admin/unassigned-jobs` | admin | `[JobDTO + reasons[] + division_tag]` (`division_tag` = the stored raw `zoho_so_line_items.division_tag` text, `null` when the line has no Division tag; it is on this admin route **only**, never in the JobDTO, which is manager-facing and stays clean: the person who can fix the Zoho data sees it here); `reasons ⊆ {no_division, unmapped_division, division_conflict, no_manager, no_job_no}`. `no_manager` means the resolved division has no active pair: today PCU, PCLU, DPU, PPU and CWU (§1, AC89). Open jobs only, legacy included. The route returns a flat list; the screen groups by reason and shows the count per division for `no_manager` (**(UI)**). |
| `GET /api/admin/zoho-sync/status` | admin | `runs` (the last 20 sync runs, the array key named as in `/api/admin/imports`) `[{module, full_list, status, api_calls, rows_read, rows_upserted, started_at, finished_at, error}]` (`error` is a code from the fixed set of §5.2, never an exception message or a response fragment), `calls_today`, `cap`, `list_reserve`, `day_reserve_left`, `history_calls_today`, `reconfirm_calls_today`, `retry_calls_today`, `retry_reserve_left`, `detail_queue:{p0,p1,p2,p3,p4,p5,pr_due}` (sync-problem SOs are in none of p0–p5; `pr_due` counts those whose backoff has elapsed), `p3_calls_today`, `rows_quarantined_today`, `quarantined_sos` (count of headers with `row_quarantine_at` set and `sync_state` not `'missing_in_zoho'`), `outage_pending`, `last_recovery_reset`, `full_list_attempts_today:{so_headers,bundles}`, `last_full_list:{so_headers,bundles}` each `{finished_at,status,error}`, `reset_sync_problems_enabled`, `force_full_list_enabled`, `oldest_p0_wait_min`, `oldest_p2_wait_min`, `oldest_refresh_wait_min`, `sync_problems` (count), `in_scope_sos`, `loaded_sos`, `enabled` |
| `GET /api/admin/zoho-sync/problems` | admin | `[{salesorder_number, detail_fail_count, reason, last_error_at, next_retry_at, flag_eligible, open_jobs}]` for every SPS header with (`detail_fail_count >= DETAIL_FAIL_LIMIT` **or** `row_quarantine_at` not NULL) and `sync_state` not `'missing_in_zoho'`, ordered by `last_error_at` (or `row_quarantine_at`) descending. A row-quarantine entry has `reason='row_quarantined'`, `detail_fail_count` as stored, `last_error_at = row_quarantine_at` and `next_retry_at = null` (it clears when a later list row for the SO is written; the nightly full list re-reads it). `reason ∈ {upstream_5xx, timeout, http_404_other, http_4xx, bad_shape, handler_error}` (= `detail_last_error`) or `row_quarantined`; `next_retry_at = last_error_at + delay(detail_fail_count)` (§5.2 "Backoff retry": 15 min at 3 failures, doubling to 6 h; the earliest instant, the retry runs in the first slot at or after it minus 5 min that has allowance); `open_jobs` = count of its jobs with `state='open'`. |

**Release 0 behaviour change (Rev 8, round-8 N5).** The sync writes about 170 run rows a day, and `GET /api/admin/imports` returns `SELECT * FROM zoho_import_runs ORDER BY id DESC LIMIT 100` (`server/routes/admin-imports.js:18`), which `web/src/admin/Imports.tsx:32,44` renders with its `file` column. From day one that screen would show only sync runs and no manual import history. The query gains `WHERE source <> 'sync'`: the sync has its own screen (§6 "Zoho sync"). Nothing else in that route changes (AC99).

**Date and time formats (round-11, applied to every DTO and route field).** **Business dates** (`due_date`, `since`, `flags_since`, and a `due_date` in the SO drill-down) are Colombo calendar dates as `YYYY-MM-DD`. **Observation instants** (`checked_at`, `strip[].at`, `freshness.as_of`, and every field that records when we saw or did something: `started_at`, `finished_at`, `last_error_at`, `next_retry_at`, `last_full_list.finished_at`, `last_recovery_reset`) are ISO 8601 with the `+05:30` offset (for example `2026-09-18T16:45:49+05:30`); the stored UTC ISO values are converted by the serializer.

**JobDTO.** It is an allowlist; the serializer emits exactly these keys:
- identity: `line_item_id, salesorder_number, job_no, division_code, division_source, division_conflict, customer, item_name, unit` (`division_source ∈ {tag, header, null}`; `null` exactly when `division_code` is null)
- quantities: `qty_ordered, qty_cancelled, qty_effective, qty_bundled, qty_produced, produced_basis, qty_packed, qty_shipped, qty_invoiced` (`qty_bundled` added in Rev 11: AC29 and the stage-5 tooltip need it)
- dates and state: `due_date, days_late, state, legacy, flag_status` (`flag_status ∈ {current, checking, sync_problem}`)
- `strip:[{stage_id, name, state, at, at_label, ref}]` (`state` values as in §3). **`at`** is the observation instant of §3's "at shown" column, or `null`. **`at_label`** is a fixed string: `"created in Zoho"` for stages 4 and 5 (Zoho's own creation time of the SO or bundle) and `"seen by sync"` for stages 6, 7, 8 and 10 (the `*_seen_at` are sync capture times, §3); `null` when `at` is `null`. **`ref`** is the Zoho document reference the mirror actually holds: the SO number for stage 4, the earliest matched bundle's `zoho_id` for stage 5 when `detected`, and `null` for every other stage (the mirror stores no per-line pick-list, package, shipment or invoice numbers) (AC29)
- `missing:[{code, stage_id, since, checked_at}]`: `code ∈ {package_missing, shipment_missing, invoice_missing}`; always `[]` when flags are not shown (level 1 false, or `flag_status ≠ 'current'`)

**UI**
- `Home` (`App.tsx:19-26`) sends a user with the `manager` or `gm` role (and no `admin`) to `/jobs`.
- Admin nav gains "Jobs", "Unassigned" and "Zoho sync". The "Zoho sync" screen shows the status and, below it, a "Sync problems" table from `GET /api/admin/zoho-sync/problems` with the SO number, reason, failures, last error time and next retry.
- `/jobs` shows, in order:
  - the freshness line (and the history-loading line when it applies);
  - the 5 counters, each clickable as a filter, with the note "being checked: N · sync problem: M" beside "Documents missing" (each part hidden when 0);
  - a table with columns job no, SO no (a link to `/so/:number`), customer, item, division, ordered/produced/shipped/invoiced, due date, days late, strip (6–11 icons: ✔ done or detected, ◐ partial, ✘ not done, grey ○ "no bundle seen" (stage 5 only), – n/a, grey "not tracked yet") and missing chips with "checked HH:MM"; in place of the chips, "checking with Zoho…" when `flag_status='checking'` and "sync problem — IT notified" when `flag_status='sync_problem'`;
  - filters for division (the user's own only), open/all, "documents missing only" and "Legacy open".
- `/so/:number` lists every line with the same columns and a strip. Other divisions' lines are marked "other division". Nothing is editable.
- The page refetches every 5 min through TanStack Query. There is no SSE in the preview.

---

## Acceptance criteria

Each AC is one automated test unless it is marked (M), a manual check. A clause marked **(UI)** describes screen text or layout that the API cannot carry; it is verified by hand on the private deploy with AC38 and AC39, and is not an API test (round-11: labelled so that a gap in the API is not blamed on the tests). The fixtures are built from the real JSON shapes cited above.

**Sync: read-only and budget**
- **AC1**: Given the sync enabled against a fake Zoho server, when a full schedule day is simulated (66 header-delta slots, 38 bundles-delta slots, a full list, a weekly bundle list, a backfill), then every outgoing request recorded by the fake transport is `GET` to `www.zohoapis.com`, except requests that are `POST` to `https://accounts.zoho.com/oauth/v2/token`. Any other method or host fails the test.
- **AC2**: Static test: no file under `server/zoho/` or `server/services/zoho-sync.js` contains `method:` with a value other than `'GET'`, except the token refresh function. Every entry of the configured scope list matches `/\.READ$/`.
- **AC3**: Given `ZOHO_SYNC_ENABLED=true` and `ZOHO_REFRESH_TOKEN` unset or `''`, when `loadConfig` runs, then it throws. Given `ZOHO_DAILY_CALL_CAP=501` or `249`, it throws.
- **AC4**: Given the calls already recorded today = cap − 1, when a cycle needs 5 calls, then exactly 1 request is sent, the run ends `status='warning'` with `error='daily_cap_reached'`, and no further request is sent until the Colombo date changes (clock-driven test).
- **AC5**: Given a fake server that answers 429 on the 3rd request, when a cycle runs, then the cycle stops after that request, the run is `failed` with `error='rate_limited'`, rows from requests 1–2 are committed, and the next cycle starts at its normal time. It does not retry immediately. If the 3rd request was a detail request, that SO's `detail_fail_count` is unchanged.
- **AC6**: Given a 401 on a GET, when the client handles it, then it refreshes the token once and retries once. A second 401 fails the run with `error='auth'` and no third request is sent.
- **AC7**: Given any sync log line, when the test captures all log output from a cycle with a known token `TKN123` and secret `SEC456`, then neither string appears.
- **AC40** (backfill day; rewritten for critic round 2 B1/N4, Rev 5 two-level freshness): Given cap 400, `PD_FLAGS_SINCE` set to yesterday, 2,000 open in-scope SOs never loaded and created more than 7 days ago (history), a fake server with 1 page per delta, and 13 SOs created in Zoho during the day (one at 10:05, the others spread over 06:00–19:00, each changed twice after creation), when a full weekday is simulated from 00:00 to 23:59 Colombo, then:
  - (a) the 10:05 SO's detail is fetched in the 10:15 cycle, and no later than the 10:30 cycle;
  - (b) at the end of every day slot, `/api/jobs` returns `freshness.fresh=true` with numeric counters, and no job of a flag-eligible SO has `flag_status='checking'` whose header `captured_at` is more than 30 min old;
  - (c) all 66 header-delta runs and all 38 bundles-delta runs end `ok`, and no run has `error='daily_cap_reached'`;
  - (d) `calls_today <= cap − 60`;
  - (e) every `so_detail_history` run started in a night slot, and their `api_calls` sum to at least 80.
- **AC41** (lanes): Given a day slot with `live_available = 7`, 30 live SOs and 100 history SOs queued, then exactly 7 detail requests are sent, all for live SOs. Given a day slot with `live_available = 50` and the same queue, then 20 live requests and 0 history requests are sent. Given the 22:00 night slot with no live SO queued and `history_available = 40`, then exactly 40 history requests are sent, P4 SOs before P5. Given `live_available <= 0`, the header delta is still sent and 0 detail requests are sent.
- **AC58** (critic round 3 B1c, re-confirmation budget): Given cap 400, 40 flag-eligible SOs with a stored flag, all with `detail_fetched_at` 21 h before 06:00 and unchanged in Zoho, when a full weekday is simulated, then Σ `api_calls` of today's `so_detail_reconfirm` runs is exactly 30, the other 10 SOs still show their flag with the previous `checked_at`, exactly one `warn` `zoho_reconfirm_limit_reached` is logged that day, and `calls_today <= cap − 60`.
- **AC62** (critic round 3 N4): Given a cycle that sends 5 requests and the process is killed before the run finishes (the counter increments **after each response is received**, in the lease-renewal transaction of §5.3, never before the request is sent; a request in flight at the kill is not yet counted), when the next cycle starts after 30 min, then the crashed run has `api_calls = 5` and `calls_today` includes those 5.
- **AC71** (round-4 non-blocking 4, night P3): Given the 02:00 night slot with 0 P0–P2 SOs, 200 P3 SOs queued, `live_available = 165` and `history_available = 25` (consistent under §5.3: at the 02:00 slot `day_reserve_left = 130` and `retry_reserve_left = 10`, so `history_available = live_available − 140`; the Rev 9 pair 180 and 25 was impossible), then exactly 25 P3 requests are sent and 0 history requests; with `history_available <= 0`, 0 P3 requests are sent and a queued P0 SO is still fetched.

**Sync: correctness and idempotency**
- **AC8**: Given an empty mirror, when the same delta page fixture is processed twice, then the row counts of `zoho_so_headers`, `zoho_so_line_items` and `zoho_bundles` are equal after run 1 and run 2, **no row's `captured_at` changes in run 2**, and run 2 reports `rows_upserted = 0`. In a sync run `rows_upserted` counts rows whose write changed something; it is not Release 0's rows-processed count (`cli/import/run.js:80`) (round-6 N2).
- **AC9**: Given a delta list whose rows are sorted by `last_modified_time` descending and a newest ok `so_headers` sync run that started at T0, when paging, then the client stops at the first row older than `T0 − 10 min` and requests no further page.
- **AC10**: Given an SO detail with lines {A, B} stored, when a new detail returns {A} only, then B is deleted in the same transaction as A's update. If the handler throws in the middle, then neither the A update nor the B delete is visible, and `detail_fetched_at` is unchanged.
- **AC11**: Given a detail response without `salesorder.line_items`, or a non-JSON body, then nothing is written for that SO's header fields or lines, the run records the SO in `warnings` with reason `bad_shape`, the SO stays in the detail queue, and at the end of the cycle its `detail_fail_count` is 1 and `detail_last_error='bad_shape'`.
- **AC12**: Given a full list (headers or bundles) that completes with fewer rows than 95% of the local non-missing SPS count, then the run is `failed` with `error='suspect_short_list'`, it has `full_list=0`, and no row's `sync_state` changes.
- **AC13**: Given a complete full list that lacks SO X (tested once each with X `source='sync'`, `'pull'` and `'xlsx'`), then X gets `sync_state='missing_in_zoho'` and its lines disappear from `/api/jobs` and `/api/sales-orders/X` (404). When X reappears in a later full list, `sync_state` becomes NULL.
- **AC14**: Given two processes that start a cycle at the same instant on one DB, then exactly one acquires `zoho_sync_lease` and the other sends 0 requests.
- **AC15**: Given a sync run row with `finished_at IS NULL` started 31 min ago, when the next cycle starts, then that row has `status='failed', error='crashed'` and a non-null `finished_at`.
- **AC16**: Given the line's `quantity_packed` goes 0 → 500 at capture T1, 500 → 800 at T2, 800 → 800 at T3, then 800 → 0 at T4: `packed_seen_at` is T1, T1, T1, NULL and `packed_changed_at` is T1, T2, T2, NULL after T1, T2, T3, T4 respectively.
- **AC17**: The `zoho_so_line_items` schema has no column matching `/rate|amount|price|total|cents/`.
- **AC42** (critic B2): Given SO H loaded at T0 with `detail_sig` S0, when a later **full list** changes H's `quantity_shipped` but not its `last_modified_time`, then H enters the detail queue, its jobs have `flag_status='checking'` until the next cycle fetches it, and afterwards its line `quantity_shipped` and `detail_sig` are updated and `flag_status='current'`.
- **AC43**: Given a detail response whose `salesorder` object has no `shipped_status` key, when it is processed, then the stored `zoho_so_headers.shipped_status` is unchanged. Given a detail whose `custom_field_hash` lacks `cf_job_no`, the stored `cf_job_no` is unchanged.
- **AC44** (critic N6): Given bundle B (600, same SO and item) stored, when a complete bundles full list lacks B, then B has `sync_state='missing_in_zoho'` and the line's `qty_bundled` drops by 600.
- **AC45** (critic N2): Given a DB with SPS bundles whose `composite_item_id` is NULL and no ok sync bundles full list, when the first cycle runs, then it runs a bundles full list, and afterwards each bundle present in that list has its `composite_item_id` set.
- **AC46** (critic N8): Given an ok SPS sync run of **any module** (`so_headers`, `bundles`, `so_detail`, `so_detail_history`, ...) finished 1 hour ago (an ok `so_detail` run alone is enough), when the CLI imports an SPS `so_headers` or `bundles` file, then it exits non-zero with `sync_active` and no row of any table changes. An SPS `so_xlsx` import still succeeds. An **SH** `so_headers` or `bundles` import with that same SPS sync run present also succeeds: the guard is SPS-only (round-6 N4).
- **AC47** (critic N5): Given a lease holder whose lease row was taken over by another owner, when the holder tries to renew after its next request, then it sends no further request in that cycle.
- **AC53** (critic round 2 N1): Given the newest ok `so_headers` delta run started at T0, and a new delta whose page 1 (200 newest rows) is committed and whose page 2 request answers 503, then the run is `failed` with `error='upstream'`. In the next cycle the delta uses `W = T0` (not the `max(modified_at)` written by page 1), pages until a row older than `T0 − 10 min`, and every SO that was on the failed page 2 is present in `zoho_so_headers` afterwards. The same test with bundles.
- **AC55** (critic round 2 N2): Given a sync bundles page containing a row with `quantity_to_bundle: 600` and `composite_item_id: "X"`, when it is processed, then the stored bundle has `quantity = 600` and `composite_item_id = 'X'`. A static test asserts the sync code contains no bundle field mapping of its own: it imports the `bundles` section of `config/zoho-columns.json`.
- **AC60** (critic round 3 N2; round-4 non-blocking 2): Given SO X marked `missing_in_zoho` by a full list, and a header delta that returns X with every other field identical to the stored row, then after that delta X has `sync_state = NULL` and its jobs are back in `/api/jobs`. The same test with a bundle and the bundles delta.
- **AC61** (critic round 3 N3): Given a never-loaded, non-flag-eligible SO created 30 days ago (`detail_fetched_at`, `detail_modified_at`, `detail_sig` all NULL), then it is queued in the history lane (P4) with exactly one reason, and a day slot sends no request for it.
- **AC63** (critic round 3 N6): Given one simulated day of sync runs, then every sync run row's `changed_so_numbers` parses as a JSON array, and `runSweep` processes all of them without throwing and sets their `processed_at`.
- **AC68** (round-4 B2, API "open"): Given `PD_FLAGS_SINCE` set to today and these pre-cutoff SOs created 30 days ago and never loaded: S1 `status='partially_shipped'`, `quantity=1000`, `quantity_shipped=100`, `quantity_invoiced=100`; S2 `status='fulfilled'`, `quantity=500`, `quantity_shipped=500`, `quantity_invoiced=0`; S3 `status='fulfilled'`, all quantities 500; S4 `status='void'`, `quantity=500`, shipped 0; S5 `status='draft'`, shipped 0; S6 `status='onhold_test_value'` (unknown), then S1, S2 and S6 are in scope and queued in the history lane (P4) with one reason, and after a night slot with enough `history_available` S1's job appears in `/api/jobs` for the gm; S3, S4 and S5 are not in scope and are never requested; one `warn` `zoho_unknown_so_status` with value `onhold_test_value` is logged at the next full list.
- **AC69** (Rev 5 outage guard): Given a day slot whose header delta ends `ok`, 6 live SOs queued, and a fake server whose detail endpoint answers 503 for every SO, then exactly 3 detail requests are sent, the detail run ends `warning` with `error='detail_outage'`, no SO's `detail_fail_count` changes and each of the 3 has `detail_outage_hits=1`. Given a cycle whose header delta ends `failed`, then 0 detail requests are sent.
- **AC70** (round-4 non-blocking 1; extended for round-6 N8): Given the real detail object of `salesorders_since_2026-09-15.json` for one SO (no header `quantity`, `quantity_packed`, `quantity_shipped` or `quantity_invoiced`, only `total_quantity`) and a stored header with `quantity=1000`, `quantity_packed=100`, `quantity_shipped=300`, `quantity_invoiced=200`, `status='confirmed'`, `shipped_status='pending'`, `invoiced_status='not_invoiced'` (values that differ from the detail's own), when it is processed, then the outcome is `ok`, its lines are written, `detail_fail_count=0`, and all seven stored signature fields are unchanged, because the detail path never writes them; a stored `cf_job_no` that differs from the detail's `custom_field_hash` is updated.

**Sync: Rev 6 additions (plan-critic rounds 5 and 6)**
- **AC72** (round-6 B4, night P1): (a) Given the 02:00 night slot right after a header full list that changed the headers of 150 flag-eligible SOs (150 queued in P1), 0 P0 and P2 SOs, `live_available = 165` and `history_available = 25`, then exactly 25 P1 requests are sent and 0 P3 and 0 history requests; with `history_available <= 0`, 0 P1 requests are sent and a queued P0 SO is still fetched. Derivation of the pair (round-10 fix; the Rev 9 pair 193 and 25 was impossible, the gap is `day_reserve_left + retry_reserve_left = 140`): the 02:00 slot runs its full list first and **its header and bundles deltas still run after it**, and detail work comes after the deltas, so at the detail phase `used = 2 + 2 + 43 + 1 + 1 = 49` (the 00:00 and 01:00 slots, the full list, the 02:00 header delta and bundles delta) and `list_reserve = 63 + 35 = 98` (header delta slots 03:00-05:00, 57 day slots and 21:00-23:00; bundles the same with 29 day slots), giving `live_available = 400 − 49 − 98 − 60 = 193` and `history_available = 53` when nothing else was spent. The fixture's 25 therefore assumes night history has already spent 28 calls in the 00:00 and 01:00 slots (`used = 77`), which gives `live_available = 165`. (b) Given the same night simulated through to 06:00 with no night P0 or P2 work, then at 06:00 `live_available >= DAY_DETAIL_RESERVE` (130), all 150 P1 SOs are fetched by the end of the day (about 53 at night and the rest in the day slots at up to 20 requests a slot, within the 130 reserve), every delta run ends `ok`, and `calls_today <= cap − 60` at the end of the day (147 list calls + 53 + about 97 = about 297 ≤ 340).
- **AC73** (round-6 B1, a blip heals): Given a flag-eligible SO A with a shown flag whose header changes at 06:00, and a fake server whose detail endpoint answers 503 from 06:00 up to (not including) 06:45 and 200 afterwards, with A the only queued SO in each slot, then A is requested at 06:00, 06:15 and 06:30 (`detail_fail_count=3`, `flag_status='sync_problem'` at the end of the 06:30 slot), is requested again at 06:45 by the retry lane (`delay(3)` = 15 min; recorded under `module='so_detail_retry'`), the request succeeds, and at the end of the 06:45 slot `detail_fail_count=0`, `flag_status='current'`, A's flag is shown again and `checking.sync_problem=0`.
- **AC74** (round-6 B1, reset lever): Given 12 SPS SOs with `detail_fail_count >= 3` and a recent `detail_last_error_at`, when the process starts with `ZOHO_RESET_SYNC_PROBLEMS=true`, then before the first cycle all 12 have `detail_fail_count=0`, `detail_last_error=NULL` and `detail_last_error_at=NULL`, exactly one `warn` `zoho_reset_sync_problems` with `reset=12` is logged, and the problems route lists none. A second start with the flag still true logs `reset=0`. With the flag unset or `false`, nothing is reset. No other column of those rows changes.
- **AC75** (round-6 N7, `PROBLEM_RETRY_DAILY_MAX`): Given 11 sync-problem SOs whose backoff has elapsed at 06:00 and a fake server answering 200, when a weekday is simulated, then Σ `api_calls` of that day's `so_detail_retry` runs is exactly 10, no cycle sends more than 2 retry requests, the 11th (newest `detail_last_error_at`) is not requested that day and is requested first on the next Colombo day; with `live_available <= 0` in a slot, no retry is sent in it while the header delta still is.
- **AC76** (round-6 N7, `zoho_sync_throttled`): Given a fake server answering 429 in three consecutive cycles, then the next 4 cycles send 0 requests, one `error` `zoho_sync_throttled` is logged, and the cycle after them runs normally.
- **AC77** (round-6 N7, `zoho_detail_outage`): Given three consecutive cycles that each end `detail_outage` (the fake answers 503 for every detail), then one `error` `zoho_detail_outage` is logged after the third and none after the first two; a fourth consecutive outage cycle logs nothing more, and a cycle without `detail_outage` ends the streak (the count is derived from the run rows, §5.2; it survives a restart).
- **AC78** (round-6 N7, `counters_complete` and `flags_since`): Given `PD_FLAGS_SINCE` set and 300 open non-flag-eligible history SOs, when the night lane has loaded the last of them, then `counters_complete=true` and `history.loaded = history.in_scope`; and `flags_since` in the `/api/jobs` response equals `PD_FLAGS_SINCE` when it is set and is `null` when it is unset.
- **AC79** (round-5 N2, history with a problem SO): Given 10 never-loaded history SOs, one with `detail_fail_count >= 3`, then `history.in_scope = 9`; when the other nine are loaded, `history.loaded = 9`, `counters_complete=true`, the blue line is gone, and the problem SO is on the problems list.
- **AC80** (round-6 B3, real payload): Given the 22 real detail objects of `salesorders_since_2026-09-15.json` served by the fake transport, when each is processed, then all 22 outcomes are `ok`, 22 lines are stored, every `is_combo_product` is stored as integer 1 (JSON `true`), `combo_type='assembly'`, `quantity_cancelled` of JOBORDER-08602's line is 1496, `sku` and `unit` are NULL where the source is `""`, and `division_tag` is set on the 18 lines that carry a Division tag and NULL on the other 4.
- **AC81** (round-6 B3, `is_combo_product`): Given a line without the `is_combo_product` key, then the row is written with NULL and its SO's outcome is `ok`. Given `is_combo_product: false`, it is stored as 0. In both cases `is_assembly` is false. A JavaScript boolean is never bound to SQLite (the test fails on a bind error).
- **AC82** (round-6 B3, Division-tag extraction): Given lines whose `tags` are (a) absent, (b) `[]`, (c) one Division tag `MOBA Unit`, (d) the Division tag twice (`Paper Straw Unit` and `paper straw unit `), (e) two distinct Division tags (`MOBA Unit`, `Paper Cup Unit`), (f) a Division tag with a blank `tag_option_name`, (g) only a non-Division tag, (h) `tags` = `"x"`, then `division_tag` is NULL, NULL, `MOBA Unit`, `Paper Straw Unit`, `MOBA Unit | Paper Cup Unit` (with `division_tag_multiple` in the run's `warnings`), NULL, NULL, and for (h) the SO's outcome is `bad_shape`. For (e) the job has `division_code` NULL with reason `unmapped_division` and no header fallback, and its entry on the admin Unassigned list carries `division_tag` = `MOBA Unit | Paper Cup Unit` (the raw text is on the admin route only; the JobDTO has no key for it and `/api/jobs` shows none).
- **AC83** (round-6 B3, `handler_error`): Given a detail whose line has `line_item_id` = 12345678901234567890 as a JSON number (`mapRow` throws, `columns.js:18-20`), then the outcome is `handler_error`: nothing of that SO is written (header included), `detail_fetched_at` is unchanged, at the end of the cycle `detail_fail_count=1` and `detail_last_error='handler_error'`; after the third failed cycle the SO is a sync problem and its next request waits for `delay(3)`. It is never requested in every cycle for ever with the count stuck at 0.
- **AC84** (round-6 B5, go-live day): Given `ZOHO_SYNC_ENABLED=true` started at 10:07 Colombo on a weekday with no sync run of any module in the DB, a fake server with 43 header pages and 60 bundle pages, then: the first cycle (10:15) makes the header full-list attempt and the bundles full-list attempt, both `ok` with `full_list=1` (the header attempt is the first read, no delta precedes it); at the end of the 10:15 slot `/api/jobs` returns `freshness.fresh=true`; every later header delta uses W = the full list's `started_at`; no further header full list is attempted before 02:00 next day; no run ends `daily_cap_reached` and `calls_today <= cap − 60` at 23:59. `list_reserve` at 10:15 counts the 43 and the 60 only while their attempts are pending.
- **AC85** (round-6 B5, failed full list): (a) Given the 02:00 header full list answers 503 on page 5, then that run is `failed`, `error='upstream'`, `full_list=0`, `file='full_list'`; the 03:00 slot makes attempt 2, which completes and passes 95% and is `ok` with `full_list=1`; there is no attempt at 04:00 or 05:00. (b) Given attempt 2 also fails, no third attempt is made that day and the next attempt is at 02:00 the next day. (c) Given `suspect_short_list` at 02:00, there is no retry at 03:00 and an `error` is logged. (d) Given `ZOHO_FORCE_FULL_LIST=true` at process start, the first cycle attempts both lists once whatever today's attempt count; with the flag unset it does not.
- **AC86** (round-6 B6, quarantine): Given a 200-row `so_headers` delta page in which row 57 lacks `salesorder_number`, when it is processed, then the run ends **`ok`**, 199 rows are written, `rows_skipped = 1`, `warnings` holds exactly one `{row_quarantined, id, reason:'missing_required:salesorder_number'}` entry and no row body, W(so_headers) moves to this run's `started_at`, and the next `/api/jobs` returns `freshness.fresh=true`. The same holds for a row without `salesorder_id` (`no_id`), a non-object row (`not_object`), a row with `last_modified_time: 'garbage'` (`map_error`) and a row whose write throws (`write_error`; the other 199 rows still commit and the throwing row's SAVEPOINT is rolled back). A page with no `page_context` gives a `failed` run with `bad_shape` and nothing written. A page with 11 bad rows of 200 gives `failed`, `too_many_bad_rows`, W unchanged and one `error` log; 10 bad rows of 200 gives `ok`. In a full list, a quarantined row's stored SO is not marked `missing_in_zoho`.
- **AC91** (round-6 N10, error hygiene): Given a fake server whose 500 response body contains `TKN123`, `SEC456` and `<html>secret</html>`, when a cycle runs, then that run's `zoho_import_runs.error` is exactly `upstream`, its `warnings` contain none of those strings, and `GET /api/admin/zoho-sync/status` and `/api/admin/zoho-sync/problems` contain none of them. For a `handler_error`, `detail_last_error` is `handler_error` and the run's warning carries at most 120 characters of the exception message.
- **AC92** (round-6 N4, `composite_item_id` scoping): Given a DB with sync-written SPS bundles whose `composite_item_id` is set and no sync run in the last 7 days, when a Release 0 pull import of an SPS bundles file whose rows lack `composite_item_id` runs, then the stored `composite_item_id` values are unchanged. A sync bundles run whose rows carry the key writes it (AC55).
- **AC93** (round-6 N1, list path, present keys only): Given a stored SPS header with `cf_job_no='OPD6710'`, `cf_manufacturing_division='Offset Printing Division (OPD)'` and `cf_order_received_from='X'`, and a delta list row for it with a newer `last_modified_time` and none of the `cf_*` keys, then after the run the three stored values are unchanged and the other list fields are updated. For a row with no stored header, the three are NULL.
- **AC94** (round-6 N6, slot alignment): Given a clock-driven test, a process started at 06:07 runs its first cycle at 06:15 and the next at 06:30, with no cycle at 06:07. A 06:15 cycle that ends at 06:33 is followed by the 06:45 cycle (the 06:30 slot is skipped, not queued). The long cycle comes from **slow replies, not request volume** (at 30 requests a minute and at most 250 requests a cycle cannot last 18 minutes by volume alone): model it as a 108-page delta with each reply delayed 10 seconds. The bundles delta runs at :00 and :30 only in day slots. On a Sunday the bundles full list runs in the 03:00 slot and nothing runs at 02:30.
- **AC95** (round-5 N5, record cutoff): Given header list rows with `date` 2023-12-30 and 2024-01-01 (Colombo), then only the second is written and `rows_skipped` counts the first. Given a full list of 1,000 rows of which 60 predate the cutoff, against a local count of 940 non-missing SPS headers, then the list passes the 95% rule.
- **AC96** (round-7 B3, absent quantity key on a line): Given a stored job line with `quantity_invoiced=500` and `quantity_shipped=500`, and a detail whose inventory line omits `quantity_invoiced` (all other keys present), then the outcome is `bad_shape`: nothing is written, the stored `quantity_invoiced` is still 500, `detail_fail_count` rises by 1, and no `invoice_missing` (or any other) flag appears for it. The same for an omitted `quantity_shipped`. A **non-job** line (`item_type='sales'`) that omits a quantity key does not fail the SO, and its stored value is left as it was (present-keys rule).
- **AC97** (Rev 8, exact in Rev 9): per-SO outage counter and recovery reset. All cases use day slots with the header delta `ok` each cycle. In (a) to (c) lane PR is **stubbed off** (the day's retry allowance is 0) so the cycle numbers hold; (e) covers PR on.
  - (a) **Head of queue.** Given 3 flag-eligible SOs that sort first (newest `modified_at`) and answer 503 for ever, plus 200 other queued live SOs answering 200, then in cycles 1 to 3 exactly 3 requests are sent per cycle, each cycle ends `detail_outage`, and `detail_outage_hits` goes 1, 2, 3; `detail_fail_count` is unchanged in cycles 1 and 2 and rises to 1, 2, 3 in cycles 3, 4 and 5 (the hits stay at 3); exactly one `error` `zoho_detail_outage` has been logged at the end of cycle 3 and still exactly one after cycle 5. At the end of cycle 5 all three have `flag_status='sync_problem'` and are in none of P0-P5. In cycle 6 the 200 others are fetched (up to the per-slot cap of 20) and at its end the recovery reset fires in one transaction: the three are back at `detail_fail_count=0` with no `detail_last_error`, `detail_outage_hits` is still 3, one `info` `zoho_detail_recovery_reset` with `reset=3` is logged, `zoho_detail_outage_pending` is deleted and `zoho_recovery_reset_day` is today's date. In cycles 7, 8 and 9 the three are counted 1, 2, 3 (each failure counts at once), each of those cycles ends `detail_outage` and sets the pending key again, and they are sync problems at the end of cycle 9; cycles 7 to 9 are three consecutive outage cycles after the healthy cycle 6, so `zoho_detail_outage` fires **again** at the end of cycle 9: exactly **two** such logs after cycle 10 (one error log per outage episode is intended, and a re-conversion after a recovery reset is a new episode); **the pending key survives** because the daily key blocks a second reset; no second reset happens that Colombo day. From cycle 10 the 200 others continue and in the night slots the history lane loads; `freshness.fresh=true` throughout.
  - (b) **Production ordering.** Given the same 3 broken SOs sorting **behind** fresher P1 work, where **17 fresh P1 SOs arrive every cycle and there is no starting backlog** (round-10 fix: with the per-slot cap of 20, exactly the three broken SOs fit behind 17 fresh ones each cycle; a 200 backlog would starve them for about 67 cycles and test nothing), then each cycle fetches the fresher SOs first (up to the slot cap) and reaches the broken three last; a cycle that reaches them ends `detail_outage` and does not reset; the same conversion (hits 1, 2, 3, then counted 1, 2, 3) and the same one-reset-per-day behaviour follow; the fresher SOs are fetched in every cycle throughout, and the cycle numbers are those of (a).
  - (c) **Recovery.** Given N=40 SOs converted with `detail_last_error='upstream_5xx'` (or `'timeout'`), one SO converted with `detail_last_error='handler_error'`, one SO with `sync_state='missing_in_zoho'` and an old `upstream_5xx` error, `zoho_detail_outage_pending` set and today's reset not yet used, when the fake server then answers 200, then at the end of the first cycle with an `ok` detail response that does not itself end `detail_outage`: the 40 have `detail_fail_count=0`, no `detail_last_error`, are back in the lanes and off the problems list; the `handler_error` SO is still a sync problem; the missing SO is untouched and not counted; exactly one `info` `zoho_detail_recovery_reset` with `reset=40` is logged; the pending key is deleted and `zoho_recovery_reset_day` is today. Then, still the same day, given a second outage that converts 30 more SOs and a recovery, nothing is reset, the pending key is **still set**, and the 30 stay converted; when the clock passes to the next Colombo day, the first qualifying cycle resets the remaining transient-class SOs, deletes the pending key and writes the new day. An `ok` response for an SO with `detail_outage_hits=2` sets it to NULL.
  - (d) **PR excluded.** Given one live SO failing 503 and two PR retries failing 503 in one cycle, then the cycle does not end `detail_outage`.
  - (e) **PR on.** Given fixture (a) with lane PR enabled, then at cycle 6 PR sends 2 requests for two of the three converted SOs (oldest `detail_last_error_at` first; `delay(3)` = 15 min has elapsed); both answer 503 and are counted **after** the reset, so those two end cycle 6 at `detail_fail_count=1` and the third at 0; all three are sync problems no later than the end of cycle 9.
- **AC98** (round-7 B2, quarantine marks the SO; Rev 8 adds `write_error`): Given a flag-eligible SO X with a shown `invoice_missing` flag, and a delta list row for X (carrying `salesorder_number`) that quarantines on every run for 3 days, tested once with `last_modified_time: 'garbage'` (`map_error`) **and once with a row whose write violates a constraint on every run (`write_error`, the mark must survive the row's rolled-back SAVEPOINT)**, then after the first such run `X.row_quarantine_at` is set, X's jobs have `flag_status='checking'` and `missing=[]`, X is counted in `checking.being_checked`, and X is on `GET /api/admin/zoho-sync/problems` with `reason='row_quarantined'`; the run itself ends `ok` and no other SO changes. When a later list row for X is written successfully, `row_quarantine_at` is NULL again, X is off the list and `flag_status` is `current`. A `not_object` row and a row with neither `salesorder_number` nor `salesorder_id` mark no SO (accepted residual) and still appear in the run's `warnings`.
- **AC99** (Rev 8, imports screen): Given 150 sync run rows and 5 manual import rows (`source` `xlsx` or `pull`) in `zoho_import_runs`, then `GET /api/admin/imports` returns exactly the 5 manual runs (and would return up to 100 manual runs regardless of how many sync rows are newer); the `orgs`, `unmapped` and `crashed` parts of its response are unchanged; `GET /api/admin/zoho-sync/status` still lists the last 20 sync runs.

**Jobs, routing, visibility**
- **AC18**: Given line tag `MOBA Unit` (aliased to MOBA) and header `Paper Cup Unit (PCU)`, then `division_code='MOBA'`, `division_source='tag'`, `division_conflict=true`, and the job is listed for the MOBA manager and appears in Unassigned with reason `division_conflict`. *(This rule depends on Q2.)*
- **AC19**: Given a line with no Division tag and header `Rewinding Unit (RWU)`, then `division_code='RWU'`, `division_source='header'`.
- **AC20**: Given a tag `Foo Unit` with no alias, then `division_code` is NULL (with no header fallback), the job is absent from every manager's list, it is present for gm/admin, and it is in Unassigned with `unmapped_division`.
- **AC21**: Given `project_name=''` and header `cf_job_no='OPD6710'`, then `job_no='OPD6710'`. Given both blank, then `job_no` is NULL, the job appears for its division's manager with `job_no: null` and it is in Unassigned with `no_job_no`; the label "no job no" is **(UI)** text.
- **AC22**: Given pairs Ishan→{PSU, OPD, PACKPRO, RWU}, Ranga→{OPD, MOBA, FPP, CPU}, Mubeena→{SHPS}, and one job per division plus one PCU job, then:
  - Ishan sees exactly the PSU, OPD, PACKPRO and RWU jobs;
  - Ranga sees exactly OPD, MOBA, FPP and CPU;
  - Mubeena sees exactly SHPS;
  - the gm sees all 9 (including PCU);
  - the PCU job is in Unassigned with `no_manager`.
- **AC23**: Given SO S with an SHPS line and a PSU line, when Mubeena calls `/api/sales-orders/S`, then both lines are returned with strips. When a user who can see no line of S calls it, the response is 404 with a body identical to the one for an unknown SO number **apart from `requestId`** (the app's 404 body carries a random per-request `requestId`, so two responses can never be literally identical).
- **AC24**: Given a user whose roles are `["coordinator"]`, then `/api/jobs` → 403, `/api/sales-orders/:number` → 403 (not 404; round-11) and `/api/admin/unassigned-jobs` → 403. Given no session, then 401.
- **AC25**: Given `?division=SHPS` sent by Ishan, then the result is `jobs: []` (the filter is intersected with his scope, never widened).
- **AC26**: Given a line with `item_type='sales'`, then it is not a job: it is absent from `/api/jobs` and counted in `non_job_lines` of the SO drill-down.
- **AC27**: Given `quantity=1000, quantity_cancelled=1000`, then `state='cancelled'`: the job is absent with `state=open`, present with `state=all`, and excluded from all counters.
- **AC28**: Every JobDTO key set in every response of `/api/jobs`, `/api/sales-orders/:n` and `/api/admin/unassigned-jobs` equals the allowlist in §6 exactly (including `flag_status`; for `/api/admin/unassigned-jobs` each entry is the allowlist plus exactly `reasons` and `division_tag`), and no response body of those routes or of `/api/admin/zoho-sync/status` and `/api/admin/zoho-sync/problems` contains a key matching `/rate|amount|price|total|cents|balance/`.
- **AC48** (R9): Given an open job whose SO `order_date` is 181 days ago and one 179 days ago, both past due, then only the second is in `/api/jobs` without `legacy=1` and in `past_due`; with `legacy=1` both are listed, `legacy` is true for the first, and `past_due` is unchanged.

**Strip, flags, counters, freshness**
- **AC29**: Given an assembly line with `qty_effective=1000`, `quantity_packed=0`, and bundles for the same SO {600 with the same `composite_item_id`, 400 with a different `composite_item_id`}, then stage 5 is `detected` with `ref` = the earliest matched bundle's `zoho_id` and `at_label` "created in Zoho", the DTO has `qty_bundled=600`, `qty_produced=600` and `produced_basis='bundled'`; for stages 6, 7, 8 and 10 `ref` is `null` and `at_label` is "seen by sync" when `at` is set. The tooltip "600 of 1000 bundled" is **(UI)**, built from `qty_bundled` and `qty_effective`.
- **AC30**: Given a non-combo line, and separately a line with `is_combo_product=1, combo_type='kit'`, then in both stage 5 is `n_a` and `qty_produced = quantity_packed` with `produced_basis='packed'` (critic N1).
- **AC31**: Given a PSU job, then the strip stage ids equal `[1,2,3,4,5,7,8,9,10,11]` and stages 1, 2, 3, 9 and 11 have `state='not_tracked'`.
- **AC32**: For each of `package_missing`, `shipment_missing` and `invoice_missing`, with fresh data, `flag_status='current'`, cutoff set, the SO created after the cutoff, and `detail_fetched_at` after `threshold_instant`:
  - at threshold − 1 working day the flag is absent;
  - at threshold it is present;
  - a holiday inside the window pushes the flag one day later.
- **AC33**: Given the same job as AC32 at its threshold but with `H.created_at` on the Colombo day before `PD_FLAGS_SINCE`, then `missing=[]`. The rule is the Colombo calendar date of `created_at` (§4): an SO created 23:59 Colombo on the day before the cutoff is **not** flag-eligible, and one created 00:30 Colombo on the cutoff day (19:00 UTC the previous day) **is**. Given `PD_FLAGS_SINCE` unset, then `missing=[]` for every job.
- **AC34** (level 1): Given every flag condition met, but the last ok `so_headers` delta run finished 46 min ago at 10:00 Colombo, then `freshness.fresh=false` (45 min exactly is still fresh, 46 min is not; likewise 75 vs 76 min and 50 h vs 50 h 1 s), `reason='delta_stale'`, every counter and both `checking` values are `null`, and every job's `missing=[]`. The same holds for `no_full_header`, `full_list_old` (51 h) and `bundles_stale` (76 min at 10:00). At 23:00 a header delta finished 100 min ago is still fresh. Given all four conditions met and, in addition, a flag-eligible SO with a refresh reason whose `captured_at` is 3 h old, a never-loaded flag-eligible SO, and a sync-problem SO, then `freshness.fresh=true` (level 1 reads no queue or per-SO state).
- **AC35**: Given a fixture with known expected counts (at least 2 jobs per counter plus boundary cases due=today+3 and due=today−1), then each counter equals the expected value, and each counter equals the number of jobs in the **unfiltered** `/api/jobs` list that satisfy that counter's own rule (§4), recomputed from the returned DTO fields (`due_date`, `qty_*`, `state`, `legacy`, `missing`). The API has only the `missing=1` filter (for `docs_missing`); no filter parameter is added for the other four (round-11).
- **AC49** (critic B1b): Given `PD_FLAGS_SINCE` set, 500 pre-cutoff open SOs never loaded, and no flag-eligible SO queued, then `freshness.fresh=true`, counters are numbers, `counters_complete=false`, and `history.loaded < history.in_scope`.
- **AC50** (critic B3, two-step shipment): Given a flag-eligible line with `qty_effective=800`: day 1 packed 500, shipped 500, invoiced 500; day 10 (working) packed 800 and shipped 800 captured at 10:00, invoiced still 500. Then on day 10 and on the next working day `invoice_missing` is absent, and on the 2nd working day after day 10 it is present. The same shape with packages: day 1 packed 500 and shipped 500, day 10 packed 800 → `shipment_missing` absent until the 3rd working day after day 10.
- **AC51** (confirmation, critic B2): Given a job whose stored data meets `invoice_missing` at its threshold but `detail_fetched_at < threshold_instant`, then `missing=[]` and the SO is in queue P0; when the next fetch returns `quantity_invoiced = quantity_shipped`, then no flag is ever shown; when it returns unchanged quantities, then the flag is shown with `checked_at` = that fetch's capture time.
- **AC52** (critic N7): Given one SO with two assembly lines of the same `item_id` (`item_order` 1: 600 effective, 2: 400 effective) and bundles of 700 for that item, then line 1 `qty_bundled=600`, line 2 `qty_bundled=100`; with 1,100 bundled, line 1 = 600 and line 2 = 500.
- **AC54** (bundle then package, rewritten for the Rev 4 lead decision): Given a flag-eligible assembly line (`qty_effective=1000`), fresh data, the newest ok bundles run started at 10:00, a bundle of 1000 for that SO and item created in Zoho at 10:05, and a detail fetch at 10:15 that sees `quantity_packed=1000`, then:
  - at 10:20, `missing=[]`, stage 5 is `not_detected`, and the SO is not in queue P0;
  - after the 10:30 bundles delta (which returns the bundle) ends `ok`, `missing=[]` and stage 5 is `detected`.
  - Variant: Zoho never has a bundle for the line. Then at every later time `missing=[]`, stage 5 is `not_detected`, and `qty_produced=1000` with `produced_basis='packed'`.
- **AC56** (critic round 3 B1a; rewritten for Rev 5; retry cadence changed by round-6 B1): Given `PD_FLAGS_SINCE` set, a flag-eligible job J whose `shipment_missing` threshold_instant is today 00:00 with `detail_fetched_at` yesterday (P0 due at 00:00), another flag-eligible job K with a shown flag, and a fake server whose detail endpoint answers 503 for J's SO all day (all other requests succeed), when a weekday is simulated, then:
  - J's SO is requested in the 00:00, 01:00 and 02:00 night slots; after the 02:00 slot its `detail_fail_count = 3` and it is in none of P0–P5;
  - after that it is requested only by the retry lane, in the slots 03:00, 04:00, 05:00, 07:00, 11:00, 17:00 and 23:00 (delays 15, 30, 60, 120, 240 and 360 min, each retry in the first slot at or after its delay minus 5 min; §5.2), so Σ `api_calls` of that day's `so_detail_retry` runs is 7, at most `PROBLEM_RETRY_DAILY_MAX`;
  - at the end of every slot from 06:00 to 20:00, `/api/jobs` returns `freshness.fresh=true` with numeric counters, J has `flag_status='sync_problem'` and `missing=[]`, `checking.sync_problem = 1`, and K's flag is shown and counted in `docs_missing`;
  - exactly one `error` `zoho_detail_sync_problem` is logged for J's SO.
- **AC57** (critic round 3 B1b): Given 30 flag-eligible SOs with a stored flag whose `detail_fetched_at + 20 h` all fall between 05:45 and 06:00 today, unchanged in Zoho, when the 06:00 and 06:15 day slots run, then 20 of them are re-fetched at 06:00 and 10 at 06:15, `freshness.fresh=true` at the end of both slots, all 30 flags stay in `missing` throughout, and each `checked_at` changes to its re-fetch time.
- **AC59** (Rev 4 lead decision, B2): Across every fixture of the test suite, no `missing` entry has `code='bundle_missing'` or `stage_id=5`, and the new file `shared/missing-rules.js` exports exactly the three codes of §4.
- **AC64** (Rev 5 lead AC: one failing SO for 3 days; retry cadence changed by round-6 B1): Given two flag-eligible SOs A and B, each with one job with a shown flag, when from day 1 at 06:00 A changes in Zoho (the 06:00 header delta returns a newer `last_modified_time`) and A's detail endpoint answers 503 for 3 simulated weekdays while every other request succeeds, then:
  - at the end of every slot of the 3 days, `freshness.fresh=true`, every counter is a number, B's flag is shown and B is counted in `docs_missing`;
  - A's job has `flag_status='checking'` at the end of the 06:00 and 06:15 slots of day 1 and `'sync_problem'` from the end of the 06:30 slot onward; it is never counted in `docs_missing` from 06:00 day 1 onward; `checking.being_checked=1` at the end of the 06:00 and 06:15 slots and `checking.sync_problem=1` afterwards;
  - A's detail is requested 17 times over the 3 days: 06:00, 06:15 and 06:30 on day 1 (the three counted failures), then by the retry lane at 06:45, 07:15, 08:15, 10:15, 14:15 and 21:00 on day 1, and at 03:00, 09:00, 15:00 and 21:00 on each of days 2 and 3 (delays 15, 30, 60, 120, 240, then 360 min; each retry in the first slot at or after its delay minus 5 min; §5.2), never more than 10 retry requests in a Colombo day;
  - `GET /api/admin/zoho-sync/problems` lists A with `reason='upstream_5xx'` from the end of the 06:30 slot of day 1.
- **AC65** (Rev 5 lead AC; round-4 B1a, 404): Given SO X loaded with one open job, when a header delta queues X and its detail answers HTTP 404 with body code `ZOHO_SO_NOT_FOUND_CODE`, then at the end of that cycle X has `sync_state='missing_in_zoho'` and `detail_fail_count=0`, X's job is absent from `/api/jobs` for the gm and for its manager, `/api/sales-orders/X` returns 404, and no later cycle requests X. Given instead a 404 with any other body code, X is not marked, and at the end of the cycle `detail_fail_count=1` and `detail_last_error='http_404_other'`.
- **AC66** (Rev 5 lead AC: sync-problems list): Given SO Y with 3 counted `bad_shape` failures, the last at T, then `GET /api/admin/zoho-sync/problems` as admin returns exactly one row for Y with `detail_fail_count=3`, `reason='bad_shape'`, `next_retry_at = T + 15 min`, and the status route returns `sync_problems=1`. As a manager or gm the route returns 403; without a session, 401. When Y's next retry succeeds, Y is no longer listed, `detail_fail_count=0`, and its jobs have `flag_status='current'`.
- **AC67** (Rev 5 level 2, one changed SO): Given `fresh=true`, three flag-eligible jobs on SOs P, Q and R each with a shown flag (`docs_missing=3`), when a header delta changes P's header (its `captured_at` becomes later than its `detail_fetched_at`) and the same cycle has `live_available = 0`, then at the end of the cycle P's job has `flag_status='checking'` and `missing=[]`, `docs_missing=2`, `checking.being_checked=1`, Q's and R's flags are unchanged, and all other counters equal their values before the change. After the next cycle fetches P with unchanged quantities, P's flag is shown again and `docs_missing=3`.

**Jobs and flags: Rev 6 additions**
- **AC87** (round-6 N5, drafts): Given a flag-eligible SO with header `status='draft'` and one inventory line, loaded by the sync, then `/api/jobs` for the gm does not list its line and `/api/sales-orders/:number` answers 404 for the gm and the admin. After a header delta shows it `confirmed` and its detail is re-fetched, the job appears.
- **AC88** (Q3 answered): Given a line tagged `OPD - PackPro Unit` on an SO whose header says `Offset Printing Division (OPD)`, and pairs Ishan→{PSU, OPD, PACKPRO, RWU} and Ranga→{OPD, MOBA, FPP, CPU}, then `division_code='PACKPRO'`, `division_source='tag'`, the job is in Ishan's list and **not** in Ranga's. Header OPD and tag PACKPRO map to different codes, so `division_conflict=true` and the job is also on the Unassigned list with reason `division_conflict`. With Ishan's PACKPRO pair removed, it is on Unassigned with `no_manager` and in no manager's list.
- **AC89** (divisions with no manager): Given one open job in each of PCU, PCLU, DPU, PPU and CWU (through the aliases of `002-seed.sql:43-55`) and manager pairs as in AC22, then no manager sees any of the five; the gm and the admin see all five with their `division_code`; `/api/admin/unassigned-jobs` lists all five with reason `no_manager` as a flat list, each with its `division_code` (grouping by division is **(UI)**); the gm's counters include them. After the admin adds an active pair PCU→Ranga (with a coordinator), Ranga sees the PCU job and it leaves the `no_manager` list, with no code change and no restart.
- **AC90** (round-5 N3, `flag_status` only for flag-eligible SOs): Given a non-flag-eligible loaded SO whose header has a refresh reason, and another non-flag-eligible SO with `detail_fail_count = 3`, then their jobs have `flag_status='current'`, are absent from `checking.being_checked` and `checking.sync_problem`, and their strips still draw from the mirror; the same two conditions on flag-eligible SOs give `checking` and `sync_problem`. The non-flag-eligible problem SO is still on the admin Sync problems list.

**Migration**
- **AC36**: Given a copy of a Release 0 database at `user_version=4` with data, when the app starts, then 005 applies:
  - `user_version=5`;
  - existing rows in `zoho_bundles`, `zoho_so_headers` and `zoho_import_runs` are unchanged in every pre-existing column, with the new columns NULL (`api_calls` 0, `detail_fail_count` 0);
  - the five alias rows of 005 exist, including `OPD - PackPro Unit` → `PACKPRO`, and an alias an admin had already added with the same value is neither duplicated nor overwritten;
  - a second start applies nothing and the hash check passes.
- **AC37** (strengthened, critic N10): Given a fixture DB at `user_version=5` containing rows in every new column, when the Release 0 code (`b0cd339`) runs against it, then:
  - startup logs the "newer than this code" warning (`migrate.js:36-38`) and `GET /api/health` (`server/routes/health.js:6`, mounted at `create-app.js:37`) answers 200;
  - a Release 0 **pull** import of an SPS bundles JSON fixture succeeds and updates an existing bundle row, leaving its `composite_item_id` and `sync_state` values unchanged;
  - a Release 0 xlsx SO import succeeds and inserts one new `zoho_so_headers` row with `detail_fetched_at` NULL and `detail_fail_count` 0;
  - `startRun` (`cli/import/run.js:11-13`) inserts a run row whose `api_calls` is 0.

**Manual (M)**
- **AC38 (M)**: After a private deploy with real SPS credentials, the human checks:
  - (a) on every day, `calls_today` in `/api/admin/zoho-sync/status` is ≤ the cap, and on the first weekday after the history load completes (P4 and P5 empty) it is ≤ 340. Above 340 means the §5.5 estimates are wrong and the spec returns to the spec-writer.
  - (b) 5 randomly chosen SPS SO lines agree with Zoho's own SO page on quantity packed, shipped and invoiced and on the Division tag;
  - (c) (pre-build gate, checked here) the V4 result recorded in this spec says `last_modified_time` moved for a package, a shipment and an invoice; without it the build should not have started (round-6 B2).
- **AC39 (M)**: Ishan, Mubeena, Ranga and Samitha each log in and see only the divisions in §1.

## Non-goals

- Any write to Zoho, of any kind, including reorder levels or status fixes. Also no bulk clean-up of the old backlog.
- The `bundle_missing` flag (lead decision, Rev 4). Stage 5 is shown as detected / not detected only. Whether the flag returns is decided by follow-up V7 in a later spec.
- Manual ticks for stages 1, 2, 3, 9 and 11; stage overrides; blockers; handovers; output entries; floor devices. Their tables exist but no preview route writes them.
- Creating or linking rows in `jobs` / `job_so_links`. **How auto-derived line jobs relate to the manual "files" of PD-05D (`PD-05-release-1b-zoho-sync.md:9-11,40-46`) is deliberately left for a later spec.** The preview does not touch those tables.
- The SH org: no SH sync, and no SH invoice/bill (stage 11) detection.
- Webhooks, SSE live updates, notifications (WhatsApp or email), exports, Power BI. "IT notified" for a sync problem means the admin "Sync problems" list plus the `error` log line (R10); no message is sent.
- An admin **screen** action to force a retry, clear a sync problem or edit a failure count. The ways out of the list are a successful backoff retry, a `not_found`, and the operator lever `ZOHO_RESET_SYNC_PROBLEMS` in the env file (§5.2 "Reset lever"). The full-list lever `ZOHO_FORCE_FULL_LIST` is the same kind of thing.
- Line detail for closed SOs created before the cutoff that were never loaded.
- Rates, amounts, totals, customer balances: they are not stored in the new table and not shown anywhere.
- Master-data import of customers and items (PD-05 scope). Pick lists, packages, shipments and invoices as separate mirrored modules: line quantities replace them for the preview.
- Changes to `facts.js`, `freshness.js`, `sweep.js` or `zoho_so_facts` (they stay SO-level and unchanged). **The sync never recomputes `zoho_so_facts`** (it does not call `recomputeFacts`/`afterBatch`), so the table goes stale for sync-written SOs; the blast radius is nil today because no route in Release 0 or in this preview reads it (round-7 N9). A later feature that reads it must recompute first.
- New login methods (SSO, OTP). The preview uses Release 0's username and password.
- A settings UI for the thresholds, the cutoff, `LEGACY_DAYS`, `DAY_DETAIL_RESERVE`, `RECONFIRM_DAILY_MAX`, `DETAIL_FAIL_LIMIT` or `PROBLEM_RETRY_DAILY_MAX`. (Working weekdays already have one, `admin-config.js:392-401`; it is not changed.)
- Registering the service with shdeploy, adding it to `protected-paths.conf` or creating the PM2 process. The human does these before the first deploy (decided 29 Sep, Q10; "Rollback plan"); nothing in the build does.

## Data model changes

**One migration: `server/db/migrations/005-line-jobs.sql`.** It is additive only. Its hash is added to `MANIFEST.json`, following `MANIFEST.json:1-6`.

```sql
CREATE TABLE zoho_so_line_items (
  org TEXT NOT NULL, line_item_id TEXT NOT NULL, salesorder_number TEXT NOT NULL,
  item_id TEXT, item_name TEXT, sku TEXT, unit TEXT, item_order INTEGER, item_type TEXT,
  is_combo_product INTEGER, combo_type TEXT,  -- nullable: NULL = key absent. upsertGuarded binds rec[c] ?? null, so a NOT NULL DEFAULT 0 could never apply (round-6 B3)
  quantity REAL, quantity_cancelled REAL, quantity_picked REAL, quantity_packed REAL,
  quantity_shipped REAL, quantity_delivered REAL, quantity_invoiced REAL,
  division_tag TEXT, project_name TEXT,
  picked_seen_at TEXT, packed_seen_at TEXT, shipped_seen_at TEXT, invoiced_seen_at TEXT,
  packed_changed_at TEXT, shipped_changed_at TEXT, invoiced_changed_at TEXT,
  source_file TEXT, last_synced_at TEXT NOT NULL, captured_at TEXT NOT NULL,
  PRIMARY KEY (org, line_item_id)
);
CREATE INDEX ix_so_line_items_so ON zoho_so_line_items(org, salesorder_number);
ALTER TABLE zoho_so_headers ADD COLUMN detail_fetched_at TEXT;
ALTER TABLE zoho_so_headers ADD COLUMN detail_modified_at TEXT;
ALTER TABLE zoho_so_headers ADD COLUMN detail_sig TEXT;
ALTER TABLE zoho_so_headers ADD COLUMN detail_fail_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE zoho_so_headers ADD COLUMN detail_last_error TEXT;
ALTER TABLE zoho_so_headers ADD COLUMN detail_last_error_at TEXT;
ALTER TABLE zoho_so_headers ADD COLUMN detail_outage_hits INTEGER;  -- Rev 8: per-SO count of guard-suppressed outage failures
ALTER TABLE zoho_so_headers ADD COLUMN row_quarantine_at TEXT;  -- Rev 7: set when a list row for this SO is quarantined, cleared by the next good list row
ALTER TABLE zoho_bundles ADD COLUMN composite_item_id TEXT;
ALTER TABLE zoho_bundles ADD COLUMN sync_state TEXT;
CREATE INDEX ix_bundles_so_item ON zoho_bundles(org, so_key, composite_item_id);
ALTER TABLE zoho_import_runs ADD COLUMN api_calls INTEGER NOT NULL DEFAULT 0;
INSERT OR IGNORE INTO division_aliases(zoho_value, zoho_key, division_code) VALUES
  ('Paper Straw Unit','paper straw unit','PSU'),
  ('Screen Printing Unit','screen printing unit','SHPS'),
  ('Customized Packing Unit','customized packing unit','CPU'),
  ('MOBA Unit','moba unit','MOBA'),
  ('OPD - PackPro Unit','opd - packpro unit','PACKPRO');  -- Q3, answered 29 Sep: PackPro, Ishan only
```

Rev 3 and Rev 4 added no schema change. **Rev 5 adds three columns to 005** (`detail_fail_count`, `detail_last_error`, `detail_last_error_at`); 005 is not written or deployed yet, so this changes no applied migration. The delta watermark is derived from the existing `zoho_import_runs.started_at` (`001-schema.sql:81`), and the lane split, the re-confirmation count and the retry count are recorded through the free-text `module` value (`so_detail` / `so_detail_reconfirm` / `so_detail_retry` / `so_detail_history`) of the existing runs table. The config changes are the `composite_item_id` entry in the `bundles` section and the new `so_line_items` section of `config/zoho-columns.json` (§5.2). **Rev 6 added no column; Rev 7 adds `zoho_so_headers.row_quarantine_at` (nullable, round-7 B2); Rev 8 adds `zoho_so_headers.detail_outage_hits` (nullable INTEGER, the per-SO outage counter). 005 therefore carries two new nullable columns beyond Rev 5's.** In 005 Rev 6 makes `is_combo_product` nullable (round-6 B3) and adds the fifth alias row `OPD - PackPro Unit` → `PACKPRO` (Q3); full-list attempts are recorded in the existing `zoho_import_runs.file` column (§5.2), and the backoff delay is computed from `detail_last_error_at` and `detail_fail_count`, so it needs no column either. 005 is still not written or deployed, so none of this changes an applied migration.

**Justification for the new table (rule 5).**

| Rejected alternative | Why it fails |
|---|---|
| Add columns to `zoho_so_lines` | That table is keyed by an ordinal `line_no` assigned from the xlsx row order (`upsert.js:69-72`). The xlsx line-set logic deletes lines above the new count (`upsert.js:81-84`). A later xlsx import would renumber or delete sync rows. It has no `line_item_id` to join bundles or detect removed lines. |
| Insert into `jobs` | `UNIQUE(division_code, job_no)` (`001-schema.sql:153`) is violated by a multi-line SO whose lines share one job number. `created_by`/`order_type NOT NULL` would need a fake user and a guessed type. Jobs are manually owned "files" in the parent spec. |

**Justification for the new columns.**
- `zoho_so_headers.detail_*`: per-SO detail bookkeeping (queue, confirmation, signature). Rejected: keeping it per line (Rev 1 `so_modified_at`), because an SO with zero lines or a partial delete would have no row to hold it.
- `zoho_so_headers.detail_fail_count`, `detail_last_error`, `detail_last_error_at` (Rev 5): per-SO failure state for the sync-problem rule and its backoff retry (§5.2; the retry cadence was changed in Rev 6). Rejected: (1) a new `zoho_detail_failures` table, because there is at most one failure state per SO, which is exactly one header row, and a new table would be a fourth piece of sync state for no gain (rule 5); (2) deriving the count from the runs' `warnings`, because the count must survive across runs and reset on success, which would need a scan of every run's JSON on every read; (3) a `settings` JSON row, because it cannot be joined in the job query that computes `flag_status`.
- `zoho_bundles.sync_state`: needed for bundle deletion reconcile (N6); it matches the existing header column (`001-schema.sql:12`).
- Rejected for the watermark (Rev 3): a new `watermark` column on `zoho_import_runs`. `started_at` of the newest ok run already carries the same information, so no column is needed.
- Rejected for the re-confirmation count (Rev 4) and the retry count (Rev 5): a counter row in `settings`. A separate `module` value on the existing run rows gives the same number with no new state.

**Other decisions**
- **No queue table and no watermark table.** Both are derived from the mirror and the runs table (§5.2). The sync-problems list is a query over `zoho_so_headers`, not a table.
- **No settings table rows.** The cutoff is an env var. The only runtime settings row is the `zoho_sync_lease`, which lives in the existing `settings` table.
- **Forward step:** `runMigrations` applies 005 in one transaction with `user_version=5` and its hash row (`migrate.js:59-68`).
- **Idempotency:** 005 runs once per DB, guarded by `user_version`. `INSERT OR IGNORE` makes the alias rows safe even if an admin already added the same alias.
- **Rollback step:** no destructive down-migration exists (the lint forbids DROP, `lint-migrations.js:71-73`).
  - Rollback is the **code**: the previous build starts on `user_version=5` (`migrate.js:36-38`).
  - It ignores the new table and the new columns. The new columns are nullable or defaulted, and Release 0 UPDATEs list their columns explicitly (`upsert.js:19-21`), so Release 0 INSERTs and UPDATEs still succeed (proven by AC37).
  - The 5 alias rows are harmless to Release 0. They can be deleted through the existing `DELETE /api/admin/aliases/:zoho_value` (`admin-config.js:223-233`).
  - The `composite_item_id` entry in `config/zoho-columns.json` is reverted with the code; Release 0's bundles handler does not list the column, so it never writes it (AC37).

## Failure modes and required handling

| Failure | Detection | System response |
|---|---|---|
| Zoho 429 (per-minute or daily) | HTTP status 429 | Stop the cycle. Run `failed`, `rate_limited`. Rows already committed stay. No retry until the next scheduled cycle. Not counted against any SO (AC5). After 3 consecutive 429 cycles, skip the next 4 cycles and log `error zoho_sync_throttled`. |
| Own daily cap reached | Σ `api_calls` today ≥ cap | No request is sent. Run `warning`, `daily_cap_reached`. The data goes stale, so flags hide (AC4, AC34). The §5.3 list reserve makes this unreachable unless the estimates are wrong. |
| Detail work would starve the deltas | `live_available <= 0` or `history_available <= 0` (§5.3) | That lane sends nothing; deltas still run (AC40, AC41). |
| History load, night P1 or night P3 would starve the day's live detail | the history lane, P1 or P3 at night | Prevented by construction: `history_available` subtracts `day_reserve_left` and `retry_reserve_left`; the history lane, night P1 and night P3 are all limited by it and share it, and history never runs in day slots (AC40, AC41, AC71, AC72). Night P0 and P2 are the only night detail work drawn from the day reserve; they are bounded by due flags (about 20 a day) and `RECONFIRM_DAILY_MAX` (§5.3). |
| Live detail needs more than `DAY_DETAIL_RESERVE` on a busy day | `day_reserve_left = 0` while P0/P1 are non-empty | Live work continues only as far as `live_available` allows (it can use budget history did not take). SOs waiting for a refresh show "checking with Zoho…" on their own jobs only; level-1 freshness and every other job are unaffected (AC67). Waiting P0/P2 SOs only delay a flag or its "checked" time (AC57). One `warn` log per day: `zoho_day_detail_reserve_exhausted` with the P0/P1/P2 sizes. The status screen shows `day_reserve_left`, `oldest_p0_wait_min`, `oldest_p2_wait_min`, `oldest_refresh_wait_min`. |
| More flagged SOs than the re-confirmation limit | `reconfirm_calls_today = RECONFIRM_DAILY_MAX` with P2 non-empty | Remaining P2 SOs wait for the next day; their flags stay shown with the older `checked_at`. One `warn` `zoho_reconfirm_limit_reached` per day (AC58). Any Zoho change on those SOs still re-queues them with a refresh reason, which hides their flags ("checking") until re-fetched. |
| 401 / token expired | HTTP 401 | Refresh once and retry once. On a second failure: run `failed`, `auth`. Not counted against any SO. The next cycle tries again. After 3 consecutive auth failures, log `error zoho_sync_auth_failing`. |
| Token endpoint down or refresh token revoked | a non-200 from the token endpoint | Run `failed`, `auth`. No Inventory calls are made. Stale data, flags hidden. |
| Zoho 5xx / network timeout (30 s) on a **list** request | status ≥ 500 or a timeout | Run `failed`, `upstream`. Committed pages stay. `W` is the `started_at` of the newest **ok** run (§5.2), which a failed run never moves, so the next delta re-reads the whole range including the pages that were missed (AC53). A failed header delta means no detail request in that cycle (§5.2 outage guard). |
| Delta fails after some pages were committed (429, 5xx, lost lease, cap) | run status not `ok` | As above: W unchanged, the next ok delta covers the gap. Until then no newer ok delta exists, so `delta_stale` applies after `HEADER_MAX_AGE` (AC34, AC53). |
| Delta too long for one cycle | the cycle's 250-request limit is reached while paging | Run `failed`, `delta_incomplete`; W unchanged; the next cycle continues. |
| Empty delta page | `salesorders: []` with `has_more_page=false` | Normal: nothing changed. Run `ok`, `rows_read=0`. This still counts toward freshness. |
| Malformed list **page** (not JSON, no array under the module key, no `page_context`) | a shape check (same rules as `zoho-pull-snippet.js:38-41`) | Nothing from that page is written. Run `failed`, `bad_shape`. |
| Malformed list **row** (not an object, no id, a `required` key missing from that row, a `mapRow` error, a handler error; round-6 B6) | the per-row checks of §5.2 "Row quarantine" | The row alone is quarantined: skipped, id and reason in `warnings`, counted in `rows_skipped`. The run still ends **`ok`**, W moves, level 1 is unaffected, and no other SO or user is affected (AC86). A genuine change carried by that row is not applied until a later read of it succeeds (nightly full list) or Zoho is fixed; the admin sees it on the status screen. |
| Systemic bad rows (at least 10 quarantined and more than 5% of the run) | §5.2 "Row quarantine" | Run `failed`, `too_many_bad_rows`; W does not move; `error` logged; not retried the same day (AC86). |
| Suspiciously short full list (headers or bundles) | rows < 95% of the local count | `failed`, `suspect_short_list`. No `missing_in_zoho` marking and no `full_list` credit (AC12). Not retried the same day (§5.2 "Full-list attempts"); the `error` log fires and the status screen shows it; level 1 survives one missed night. |
| A header or bundles full list is missing or fails (a deploy at 10:00; 429, auth, 5xx, cap or a crash mid-list; round-6 B5) | no `ok` `full_list=1` run (`no_full_header`), or a non-`ok` attempt | First cycle: the first attempt runs at the next slot boundary and, if it completes and passes 95%, is credited `full_list=1`, so data shows after the first cycle. A retryable failure is retried once in the next slot at least 60 min later (03:00 after a failed 02:00), at most 2 attempts per module per day. `ZOHO_FORCE_FULL_LIST` forces one attempt per start. Level 1 survives one missed night (50 h, four attempts) (AC84, AC85). |
| Row skipped by offset paging during a full list (modified mid-list) | not detectable at the time | Wrongly marked `missing_in_zoho`; cleared by the next delta that writes it with `sync_state=NULL`, which works because `sync_state` is in the sync handlers' field list (AC60). |
| Detail call fails for one SO (5xx, timeout, other 404, other 4xx, bad shape, handler error) | the outcome classes of §5.2 | Nothing written for it; reason in the run's `warnings`; `detail_fail_count + 1` at cycle end (AC11). Its own jobs show "checking with Zoho…" (if it has a refresh reason); nothing else changes. After 3 counted failures: sync problem, out of lanes P0–P5, jobs show "sync problem — IT notified", listed on the admin screen, one `error` log, and retried by backoff (15 min doubling to 6 h, at most 10 retries a day in any slot, §5.2), so it heals by itself when Zoho recovers (AC56, AC64, AC66, AC73). After a bad build the operator lever `ZOHO_RESET_SYNC_PROBLEMS` clears every count at the next start (AC74). |
| SO deleted in Zoho before its detail fetch | detail HTTP 404 with the not-found code (V3) | Header marked `missing_in_zoho` in the same cycle; its jobs leave every list; never requested again (AC65). |
| 404 that is not "SO not found" (e.g. wrong org id or path) | 404 with another body code | Counted as an SO failure `http_404_other`, never marks the SO missing (AC65). If it hits every SO, each becomes a sync problem after 3 cycles and the problems list and error logs show it; flags are hidden per job, never falsely raised. |
| Zoho-wide detail outage while lists work | 3 consecutive `upstream_5xx`/`timeout` detail requests in one cycle | The cycle stops detail work, run `warning`, `detail_outage`; each failed SO's `detail_outage_hits` rises and its `detail_fail_count` is untouched until the hits reach 3 (AC69). Jobs of queued SOs show "checking". After 3 consecutive cycles with `detail_outage`, one `error` log `zoho_detail_outage`. An SO whose hits reach 3 is then counted normally and becomes a sync problem, so persistently broken SOs stop blocking the queue; a sustained outage converts about one SO per cycle, and the first healthy cycle afterwards resets every `upstream_5xx`/`timeout` SO once per day (AC97). |
| Detail handler throws (a line `mapRow` rejects, a constraint error; round-6 B3) | outcome `handler_error` (§5.2) | The SO's transaction is rolled back. It is counted like `bad_shape`, so it is not re-requested every cycle for ever: 3 counted failures make it a sync problem, then backoff (AC83). |
| A job resolves to a division with no manager (PCU, PCLU, DPU, PPU, CWU) | reason `no_manager` | Not hidden and not guessed: on the admin Unassigned list, visible to gm and admin, absent from every manager's list until the admin adds a pair (AC89). |
| Crash mid-cycle with SO failures already seen | run closed as `crashed` | Failure counts are applied only at cycle end, so none are applied; the SOs are retried next cycle. |
| Detail object without the list-only `required` keys | always (no header `quantity_shipped` in the detail, `salesorders_since_2026-09-15.json:70`) | The `required` list is not applied to the detail; its own shape check is (§5.2 handler step 0; AC70). |
| Unknown SO `status` value from the API | a value outside the known list (V1) | Treated as not excluded, so the SO is in scope if nothing else closes it (loaded, never hidden). One `warn` `zoho_unknown_so_status` per value per full list (AC68). |
| List and detail disagree on `status` / `shipped_status` / `invoiced_status` | V3(b) records both for 20 SOs | No effect on the design: the detail path never writes the seven signature fields (§5.2 handler step 1), so there is no ping-pong and no systematic nightly re-fetch of every in-scope SO (round-6 N8). `state='void'` reads the list's status. |
| Packing/shipping/invoicing does not move the SO's `last_modified_time` | V4 (pre-build gate) | **The build does not start; this spec returns to the spec-writer (round-6 B2).** The design assumes the header delta sees every change within a slot. If it did not, a change would be seen only by the nightly full list or a P2 re-confirmation, and a job could show `invoice_missing` "checked HH:MM" for up to about 20 h after the invoice exists. That window is not accepted. The `detail_sig` check (AC42) is a second net for a list-reported change that the delta paged past; it does not make a V4 failure safe. |
| Packed assembly line has no bundle referencing its own SO (ex-stock, other reference) | stage 5 `not_detected` with `qty_packed > 0` | No flag (there is no `bundle_missing` in the preview). `qty_produced` falls back to `qty_packed`, so the job is not counted "In production" (AC54 variant). V7 measures how often this happens. |
| Bundle deleted or redone in Zoho (round-4 N3) | seen only at the weekly bundles full list (§5.4) | Until then `qty_bundled` stays too high, which can raise a false `package_missing` for up to 7 days. Accepted for the preview; V7(c) measures how often SPS deletes bundles. If it is common, a later spec moves the bundles full list to daily (about 60 calls, which does not fit the cap-400 budget without other cuts). |
| Bundle list mapped wrongly (quantity NULL) | AC55 at build time | Prevented: the sync uses the `bundles` column map, `quantity` ← `quantity_to_bundle` (`zoho-columns.json:134`). |
| Detail response lacks a header field | source key absent in `salesorder` (or in its `custom_field_hash`) | That header column is left as it is (AC43). |
| Crash or restart mid-cycle | a run with `finished_at` NULL older than 30 min | Closed as `crashed` at the next cycle (AC15). Per-page and per-SO transactions mean no half-written SO. Spent calls are already counted (AC62). |
| Two instances (PM2 overlap on restart) | the lease | The second instance skips (AC14). A holder that loses the lease stops (AC47). |
| Duplicate processing of the same page | an unchanged `upsertGuarded` | No change and no duplicate rows (AC8). |
| Line removed, SO or bundle deleted in Zoho | the detail line set / a detail `not_found` / a complete full list | The line row is deleted, or the SO/bundle is marked `missing_in_zoho` (AC10, AC13, AC44, AC65). |
| Manual SPS header/bundle import while the sync runs | CLI check (§5.3) | Refused with `sync_active`, nothing written (AC46). |
| Division tag or value unknown | no alias | The job gets NULL division and appears in Unassigned (`unmapped_division`). It is never guessed. |
| History not yet loaded | `history.loaded < history.in_scope` | Blue "History loading" line; counters marked incomplete; flags unaffected (AC49). |
| SPS works Saturdays but `working_weekdays` is Mon–Fri | Q13 answer | Flags up to one day late, never false. Fix is a config change by the admin (`PUT /api/admin/calendar`). |
| Sync disabled or no credentials | `ZOHO_SYNC_ENABLED=false` | The scheduler does not start. The UI shows the stale banner `no_full_header` / `delta_stale`. The pages still work on whatever is mirrored. |
| Clock / DST | Colombo has no DST; all day maths uses `shared/time.js` | — |

## Observability

**Log lines.** One `info` log line per run, through the existing `server/log.js`, with these fields:
- `{event:'zoho_sync_run', module, full_list, status, pages, rows_read, rows_upserted, api_calls, calls_today, cap, list_reserve, day_reserve_left, retry_reserve_left, reconfirm_calls_today, retry_calls_today, p3_calls_today, rows_quarantined, full_list_attempts_today, watermark, detail_queue, oldest_p0_wait_min, oldest_p2_wait_min, oldest_refresh_wait_min, sync_problems, detail_failures, loaded_sos, in_scope_sos, duration_ms, error}` (`watermark` = the W used, delta runs only; `detail_failures` = `[{salesorder_number, reason}]` of this run, detail runs only)
- The line never contains a token, a secret, a response body or any price field.
- After each header full list: one `info` line `{event:'zoho_history_eta', in_scope_sos, loaded_sos, non_legacy_to_load, legacy_to_load, eta_days_non_legacy, eta_days_all}` and one `info` line `{event:'zoho_status_census', counts:{<status>: n}, in_scope_by_status:{<status>: n}}`.

**Warning and error logs.** `warn` for `zoho_day_detail_reserve_exhausted` and `zoho_reconfirm_limit_reached` (each at most once per Colombo day), `zoho_unknown_so_status` (once per unknown value per full list), `zoho_row_quarantined` (once per run that quarantines a row) and `zoho_reset_sync_problems` (once per start with the lever on); one `info` `zoho_detail_recovery_reset {reset}` when the automatic recovery reset fires (at most once per Colombo day). The `error` level is used for `zoho_daily_cap_reached`, `zoho_sync_throttled`, `zoho_sync_auth_failing`, `suspect_short_list`, `too_many_bad_rows`, `zoho_detail_sync_problem` (once per SO each time it reaches `DETAIL_FAIL_LIMIT` from below), `zoho_detail_outage` (after 3 consecutive `detail_outage` cycles), and for 3 consecutive failed cycles of any kind.

**Status screen.** `/admin` → "Zoho sync" shows `GET /api/admin/zoho-sync/status` and the "Sync problems" table (`GET /api/admin/zoho-sync/problems`).

**How a human confirms it works**, all read-only, on the deployed DB:
1. `sqlite3 -readonly <db> "SELECT module, full_list, status, api_calls, finished_at, error FROM zoho_import_runs WHERE source='sync' ORDER BY id DESC LIMIT 12"`. Expect `ok` header-delta rows within the last 15 min during 06:00–20:00, and within the last 60 min at night.
2. `sqlite3 -readonly <db> "SELECT substr(started_at,1,10) d, sum(api_calls) FROM zoho_import_runs WHERE source='sync' GROUP BY d ORDER BY d DESC LIMIT 7"`. Expect ≤ cap every day; after the history load, weekdays about 280 (AC38a).
3. `sqlite3 -readonly <db> "SELECT module, substr(started_at,12,2) h, sum(api_calls) FROM zoho_import_runs WHERE source='sync' AND module LIKE 'so_detail%' AND started_at >= date('now','-1 day') GROUP BY module, h"`. Expect `so_detail_history` rows only in night hours (UTC hours 15–23, i.e. 21:00–05:00 Colombo), `so_detail_retry` rows in any hour, a daily `so_detail_reconfirm` sum of at most 30 and a daily `so_detail_retry` sum of at most 10.
4. `sqlite3 -readonly <db> "SELECT salesorder_number, detail_fail_count, detail_last_error, detail_last_error_at FROM zoho_so_headers WHERE org='SPS' AND detail_fail_count >= 3 AND (sync_state IS NULL OR sync_state <> 'missing_in_zoho')"`. Expect the same rows as the "Sync problems" screen; normally none or a handful. Open each in Zoho to see whether the SO is broken there.
5. Open `/jobs` as the gm. The freshness line must show a time less than 20 min old in the day, and no grey banner. The history line shows X of Y rising each day until it disappears. The "being checked" note is 0 or small and changes between refreshes.
6. Pick one JOBORDER in Zoho, open `/so/<number>`, and compare the quantities and division (AC38).

## Rollback plan

The preview is a new service: nothing else on the VPS reads its DB or calls its API, so stopping it harms no other system. Release 0 has never been deployed. **Deploy target (decided 29 Sep, Q10):** PM2 name `production-dashboard`, port 4300 (`server/config.js:35`), live directory `/root/production-dashboard`. Before the first deploy the human adds it to the shdeploy table (`/root/.claude/CLAUDE.md` §4b) and adds `deny /root/production-dashboard` to `/root/.claude/scripts/protected-paths.conf`. The human runs every deploy, restart and rollback command; the steps below are commands for the human, never for the build.
1. **Stop the sync, keep the screens:** set `ZOHO_SYNC_ENABLED=false` in the server env file, then `pm2 restart production-dashboard` (or the shdeploy restart once registered). The UI keeps working on the last mirror, shows the stale banner and hides the flags.
2. **Remove the preview entirely:** `pm2 stop production-dashboard`. Once registered with shdeploy, `shdeploy rollback production-dashboard` returns to the previous build instead; migration 005 stays applied and is inert for Release 0 (AC37).
3. **Revoke Zoho access:** delete the self-client in the Zoho API console. This affects nothing else, because no other system uses it.
4. **Zoho data:** nothing to undo. Nothing was ever written to Zoho.
5. **Recover from a bad build at 2am (round-6 B1, B5):** `shdeploy rollback production-dashboard`; set `ZOHO_RESET_SYNC_PROBLEMS=true` in the env file **and make sure `ZOHO_SYNC_ENABLED=true`** (the lever runs at scheduler start, and the scheduler does not start while the sync is disabled, so after rollback step 1 the reset is a silent no-op) and restart, which zeroes every sync-problem count (idempotent); confirm the "Sync problems" table is empty; set the flag back to `false`. If the screen still shows `no_full_header` or `full_list_old`, set `ZOHO_FORCE_FULL_LIST=true` for one restart (about 103 calls), then set it back to `false`.

## Pre-build verification (by the implementer, once the OAuth client exists; about 30 GET calls plus offline checks)

- **V1.** `GET /salesorders?sort_column=last_modified_time&sort_order=D&per_page=5` returns rows sorted that way, with `last_modified_time`, `status`, `shipped_status`, `invoiced_status`, `shipment_date`, header `quantity_*` and `cf_*` fields. Also record the SO `status` vocabulary (round-4 B2): the distinct `status` values in one page of 200 rows, plus Zoho's documented status list for sales orders. The known list this spec assumes is `draft, pending_approval, approved, confirmed, partially_shipped, shipped, fulfilled, closed, void, onhold`; any other value, or any of `void`/`draft`/`closed`/`fulfilled` being spelled differently, is written into §2 "Open SO" before the build. Also record (round-6 N1): whether the OAuth list rows carry flattened `cf_*` keys, and whether the list's default filter returns every status (a default filter that hides some statuses would make the 95% rule fail every night, which round 6 named as the most likely trigger of B5; if it does, §5.2 returns to the spec-writer). Also record (round-7 N3) whether every row of a 200-row OAuth page carries the sync's own required keys (headers `salesorder_id`, `salesorder_number`, `last_modified_time`; bundles `bundle_id`, `reference_number`). **If any row of the 200-row page omits any of them, record the key and the count and §5.2 returns to the spec-writer** (the spec-writer may still judge a one-off). These keys are structural: 2 rows of 200 is consistent with tens to hundreds of SOs pinned in `checking`, a missing `last_modified_time` also breaks the watermark, and neither the systemic guard (at least 10 rows and more than 5%) nor anything else would trip.
- **V2.** The same for `GET /bundles`, including `composite_item_id` and `quantity_to_bundle`. Also record the OAuth scope that the endpoint requires.
- **V3.** `GET /salesorders/{id}` through OAuth returns the line `tags`, `project_name`, `combo_type`, `quantity_picked` and `quantity_shipped` exactly as in the cookie sample. **Record all seven quantity keys (`quantity`, `quantity_cancelled`, `quantity_picked`, `quantity_packed`, `quantity_shipped`, `quantity_delivered`, `quantity_invoiced`) on every inventory line of every sampled SO, including one SO with no pick list and one SO carrying a service line, and whether each value is a number or a numeric string (round-8). If any of the seven is omitted on any inventory line, §5.2 returns to the spec-writer, the same status as V4:** the step-0 shape check would otherwise turn every SO into `bad_shape`, then a sync problem, and on go-live no job would ever load. Record which `HEADER_FIELDS_PULL` keys the detail's `salesorder` object carries, and whether the `so_headers` column map reads the `cf_*` values from `custom_field_hash` (§5.2 handler step 1). Also record (Rev 5): (a) the HTTP status and body `code` of `GET /salesorders/{id}` for a well-formed id that does not exist; this becomes `ZOHO_SO_NOT_FOUND_CODE` (if it is not a 404, §5.2 returns to the spec-writer); (b) for **20** SOs chosen across statuses (round-6 N8), whether the list row and the detail agree on `status`, `shipped_status` and `invoiced_status`. Rev 6 does not depend on the answer, because the detail path never writes those fields; the record shows whether `state='void'` (the list's status) can disagree with the detail; (c) (round-5 N4) for every sampled SO that has a line with `quantity_cancelled > 0`, the list row's `quantity`, `quantity_packed`, `quantity_shipped` and `quantity_invoiced` against the detail lines' quantities, to confirm that the header quantities include cancelled units (§2 "Open SO").
- **V4** (critic B2; round-6 B2; a pre-build **gate**). With the SPS team, pick one open SO in normal work. Record its list-row `last_modified_time` and `quantity_packed/shipped/invoiced` before and after each of: a package, a shipment, an invoice (and a pick list if one is made). The outcome is recorded in this spec. **Pass:** `last_modified_time` moves for each of the package, the shipment and the invoice. **Fail: it does not move for any one of the three: this spec returns to the spec-writer and the build does not start.** Rev 5's "no change is needed either" is withdrawn: the signature check and the confirmation rule cannot close a window of up to about 20 h in which a real change is unseen and a false `..._missing` is shown (AC38(c)).
- **V5** (offline, on the mirrored 11,898 SPS bundles). The share of bundles whose `soKey(reference_number)` equals an existing SPS `salesorder_number`. Below 95% → stage 5 matching returns to the spec-writer.
- **V6** (offline, SPS `items.json`). Whether any SPS composite item is not `assembly` (for example kits). The result only changes how often AC30's kit path is exercised; no spec change.

If V1, V2, V3, V4 or V5 fails, the relevant section returns to the spec-writer. The fallback is not to be invented during the build.

## Follow-up checks (do not block the preview)

- **V7** (offline; plan-critic round 3 B2; decides whether `bundle_missing` returns). From `/root/exports/zoho/native/2026-09-16/Package_ALL.xlsx` (2026 packages of composite items) and the mirrored SPS bundles:
  - (a) the share of packed assembly lines that have a bundle with `soKey(reference_number)` = the package's own SO number and `composite_item_id` = the line's item, split by the SO's order type (`cf_order_type`, joined through the SO number; the implementer records which columns were used);
  - (b) the lag from bundle `created_at` to package creation for the matched pairs: median, 95th percentile, and the share of packages created before their bundle;
  - (c) (round-4 N3) how often SPS deletes or redoes bundles: the number of SPS bundles marked `missing_in_zoho` by the first 4 weekly reconciles, per week, and how many of them had a matched packed-zero line at the time.
  - **Decision rule** (for a later spec, not this one): an order type whose match rate is ≥ 95% may get `bundle_missing` back, with a gate or threshold at least the measured 95th-percentile lag; an order type below 95% keeps stage 5 in the strip only. The result and the decision are written into this spec's revision notes before any bundle flag is built.

## Open questions (blocking)

- **Q1: Zoho API access for SPS.** Blocks V1–V4 and any live sync.
  - (a) The user (Zoho admin) creates a **Self Client** in the US API console (api-console.zoho.com). They generate a refresh token with read-only scopes (`ZohoInventory.salesorders.READ` plus the bundles read scope from V2) and place the ID, secret and token in the server env file themselves, never in chat or git.
  - (b) What is the real **org-wide** daily API limit on SPS's Zoho Inventory plan, and which other clients draw on it (the planned INV services at 500/day each, PD-05D, any integrations)? The 1,000/day figure is unverified (`Production Dashboard/CLAUDE.md:52`), and the cap default of 400 depends on it.
- **Q2: Which division decides the manager when the line tag and the SO's "Manufacturing Division" disagree?** Evidence: JOBORDER-08597 and -08592 have header "Paper Cup Unit (PCU)" but line tag "MOBA Unit". Proposed: the line tag wins (it goes to Ranga), and the header is used only when the line has no tag (the RWU lines). **Evidence now exists** at `/root/Project Management/reports/2026-09-28-role-based-scope/evidence/Q2-division-conflict-example.md` (2 of 22 sampled lines disagree, 16 agree, 4 have no tag, all RWU); its recommendation is the proposal above plus a "division conflict" marker on the admin list (which §6 already has). **The human has not confirmed it, so Q2 stays open and blocking.**

## Answered questions (decided by the human, Abdul Hadhee, 29 Sep 2026)

- **Q3: ANSWERED.** The line tag `OPD - PackPro Unit` maps to division code `PACKPRO`, managed by **Ishan only** (not Ranga). It sits on OPD-header SOs JOBORDER-08600, -08598, -08590, -08586 and -08575. `PACKPRO` is already seeded (`server/db/migrations/002-seed.sql:8`), so this is a tag-mapping rule, not a schema change: 005 adds the alias row `('OPD - PackPro Unit','opd - packpro unit','PACKPRO')` (Data model changes), §1 and §2 state the routing, AC88 tests it. **Consequence to note:** those five SOs have header `OPD` and tag `PackPro`, so `division_conflict` is true for them (§2) and they appear on the admin Unassigned list with reason `division_conflict` although they are routed to Ishan. Whether that particular pair should count as a conflict belongs to Q2 and is not decided here.
- **Q10: ANSWERED.** The app is registered properly: PM2 name `production-dashboard`, port 4300, live directory `/root/production-dashboard`, added to the shdeploy table and to `protected-paths.conf` before the first deploy. The human runs every deploy command. Recorded in Current behaviour ("Deployment") and the Rollback plan; the build touches none of it (Non-goals).

## Open questions (non-blocking; the stated default applies unless answered)

- **Q4: Manager login.** Default: Release 0 username and password. The admin creates accounts, and the user must change the password at first login (`001-schema.sql:96`).
- **Q5: Missing-document thresholds.** Default: package 2, shipment 3, invoice 2 working days. Timers run from the latest increase (§3). No bundle flag in the preview (V7).
- **Q6: Go-live cutoff `PD_FLAGS_SINCE`.** Default: the Colombo date on which the production sync first completes a full list.
- **Q7: Coordinator accounts.** Pairs require a coordinator account (`admin-config.js:246`). Default: the admin creates coordinator accounts for Nirmani, Umanda and Madushi now (per `design.md:398`). They see the stub page until a later release.
- **Q8: "MOBA Unit" and "MOBA Punching Unit".** Default: both map to MOBA (`MOBA Punching Unit` is already seeded, `002-seed.sql:50`). The manager is the same (Ranga) either way.
- **Q9: Link to PD-05D manual files.** How line jobs relate to PD-05D's manual "files" has to be decided before any write feature (blockers, ticks) is built on top of the preview.
- **Q11: Cap during the history load.** Default: 400. If Q1(b) shows headroom, `ZOHO_DAILY_CALL_CAP=500` for the first two weeks gives the history lane about 100 more calls a night (about 53 → 153 on a weekday, §5.5).
- **Q12: Legacy open jobs.** Default: SOs ordered more than 180 days ago are "legacy": shown under the "Legacy open" filter, left out of the counters and the default list, and loaded last.
- **Q13: Does SPS pack, ship or invoice on Saturdays?** (critic round 2 N3). Default: Mon–Fri as seeded (`002-seed.sql:77`). If yes, the admin sets the weekdays to Mon–Sat in the existing calendar screen (`PUT /api/admin/calendar`, `admin-config.js:392-401`); no code change. Until then flags on Saturday work come up to one day late, never falsely.
- **Q14: Old SOs that are shipped but not fully invoiced** (Rev 5, from round-4 B2). The API-defined open set includes every pre-cutoff SO whose header `quantity_invoiced < quantity`, however old. Default: all are in scope; those older than 180 days are legacy (P5, loaded last, out of the counters and the default list). If the first full list's census shows the in-scope count makes the history ETA longer than 30 days, the user decides whether legacy SOs with `status IN ('shipped','fulfilled')` are dropped from scope (a later spec change, not an implementer decision).

VERDICT: NEEDS-INFO — Q1 (SPS OAuth self-client + real org-wide daily API quota and who shares it), Q2 (line Division tag vs header Manufacturing Division when they disagree; evidence and a recommendation exist, the human has not confirmed it). Q3 and Q10 were answered on 29 Sep (see "Answered questions"); one lead decision is pending and does not block the build (see "Pending lead decision").

Abdul Hadhee | IT Exec | Standard-Holdings

## Revision 11 changes (second test slice)

**Every item came from the second test slice (test-author: 63 tests for the jobs, screen and API family; 0 pass, 58 fail, 5 gated to-dos; no production file touched; Release 0 still 136/136), not from review.** The slice also built a throwaway reference implementation and ran **seven deliberate mutations** against its own tests (shipment threshold, header window, drafts counted as jobs, legacy boundary, holidays ignored, flag status on non-eligible SOs, counters including legacy); **every mutation was caught**. That is the evidence these tests are worth what they cost, and where a test disagrees with the spec the test is usually right. Corrections and missing sentences only. Untouched: the budget, backoff cadences, `so_line_items` map, both 005 columns, the outage-guard and recovery-reset pairing, AC numbering (AC1-AC99) and the five Rev 10 fixes.

| # | Item | Fix | Where |
|---|---|---|---|
| 1 | AC23 "body identical" impossible (random `requestId`) | "identical apart from `requestId`". | AC23 |
| 2 | AC35 asserts filters that do not exist | Each counter equals the number of jobs in the unfiltered list satisfying its own rule, recomputed from DTO fields; no filter parameters added. | AC35 |
| 3 | Status route array unnamed | Named `runs`. | §6 |
| 4 | Date and time formats unspecified | Business dates (`due_date`, `since`, `flags_since`) are Colombo `YYYY-MM-DD`; observation instants (`checked_at`, `strip[].at`, `as_of`, all `*_at` fields) are ISO 8601 with `+05:30`. | §6 |
| 5 | `detail_sig` stored format | Pipe-joined `String(v)` values in the listed order, NULL as empty, not hashed; a NULL or mismatched signature is a refresh reason. | §5.2 (queue reason d) |
| 6 | AC34 boundaries; `status='ok'` vs Release 0 | All windows inclusive (≤ 45 min, ≤ 75, ≤ 135, ≤ 50 h; day windows 06:15:00 to 20:00:00 inclusive); `status='ok'` kept deliberately and noted as differing from `freshness.js:3-4` so nobody "fixes" it. | §4, AC34 |
| 7 | Coordinator on `/api/sales-orders/:n`: §1 said 404, §6 implied 403 | 403 everywhere (internal staff, matches AC24); 404 wording removed; AC24 extended. | §1, §6, AC24 |
| 8 | AC33 "one day before" | Colombo-date rule with both edges (00:30 Colombo on the cutoff day is eligible; 23:59 the day before is not). | AC33 |
| 9 | Undefined query parameters | `legacy=1` includes legacy alongside the others; `state=all` does not bring legacy back. | §6 |
| 10 | Screen behaviour the API cannot carry | **(UI)** label convention added: "no job no" label, the stage-5 tooltip and grouping by division are UI-layer, verified by hand on the private deploy. Defined for real: `strip[].ref` (SO number for stage 4, earliest matched bundle's `zoho_id` for stage 5, `null` otherwise because the mirror holds no per-line document numbers) and `strip[].at_label` (`created in Zoho` for stages 4 and 5, `seen by sync` for 6, 7, 8, 10); `qty_bundled` added to the JobDTO. | §6 (JobDTO), AC21, AC29, AC89 |

## Revision 10 changes (corrections found by writing the tests)

**Every item below was found by writing the tests (test-author, 117 tests against Rev 9: 116 failing because the feature is absent, 1 `test.todo` for AC65; the 136 Release 0 tests still pass), not by any of the nine plan-critic rounds.** That is worth knowing when someone asks whether test-first was worth the time on this spec. All are corrections inside existing ACs plus two design sentences; nothing structural. Untouched: the budget structure, the backoff cadences, the `so_line_items` map, both 005 columns, the outage-guard and recovery-reset pairing, and AC numbering (AC1-AC99).

| Item | Fix | Where |
|---|---|---|
| AC71 and AC72(a): impossible number pairs (`live_available` 180 or 193 with `history_available = 25`; under §5.3 they differ by `day_reserve_left + retry_reserve_left = 140`) | Consistent pair `live_available = 165`, `history_available = 25`, with the derivation: at the detail phase `used = 49` (the 02:00 header and bundles deltas **still run after the full list**), `list_reserve = 98`, giving 193 and 53 when nothing else was spent; the fixture's 25 assumes 28 calls of night history in the 00:00 and 01:00 slots. Outcomes unchanged. | AC71, AC72(a) |
| AC97(b) not deterministic (a 200 backlog starves the trio for about 67 cycles) | 17 fresh P1 SOs per cycle, no starting backlog; cycle numbers as in (a). | AC97(b) |
| AC97(a) omitted a second `zoho_detail_outage` log | Stated: exactly one log after cycles 3 to 5 and exactly two after cycle 10 (cycles 7 to 9 are a new outage episode after healthy cycle 6). §5.2 log derivation says one per episode. | AC97(a), §5.2 |
| AC82(e) asserted something the API cannot expose | The raw tag is on the admin Unassigned entry as `division_tag` (stored `zoho_so_line_items.division_tag`), not in the JobDTO; route text and AC28 updated (allowlist plus exactly `reasons` and `division_tag`). | §6, AC28, AC82(e) |
| AC46 guard scope | Stated: an ok sync run of **any module** blocks a manual SPS `so_headers`/`bundles` import; implementers must not filter by module. | §5.3, AC46 |
| AC94 "06:15 cycle ends 06:33" unreachable by volume | Stated: the long cycle comes from slow replies (108-page delta, 10 s per reply). | AC94 |
| AC62 "killed" | Stated: `api_calls` increments after each response, in the lease-renewal transaction; a request in flight is not counted; §5.5 "a crash loses no counted call" corrected to "at most the one request in flight". | AC62, §5.3, §5.5 |

## Revision 9 changes (plan-critic round 9 APPROVED Rev 8; three required edits and five one-liners)

Round 9's verdict was **APPROVE**. It verified that both Rev 8 refinements (no reset in a cycle that itself ends `detail_outage`; the once-per-day limit) were necessary and correctly reasoned, and that the settings-key marker is strictly better than an in-memory flag. Not touched: the budget (AC72(b) still 297 at most 340, no line moves), the backoff cadences, the `so_line_items` map, both 005 columns (`detail_outage_hits` is in no `upsertGuarded` field list and must stay so), AC69, AC numbering (AC1-AC99) and the four smaller Rev 8 edits. Round 9 considered dropping `detail_outage_hits` and relying on the reset alone and **rejected** it: without suppression a 45-minute blip converts 3 SOs per cycle instead of 0.6, so the guard bounds the damage and the reset repairs it. That pairing must not be unpicked as a "simplification".

| Item | Fix | Where |
|---|---|---|
| R1 (must): AC97(a) contradictory | Reworded: hits go 1, 2, 3 in cycles 1 to 3; `detail_fail_count` unchanged in cycles 1 and 2 and 1, 2, 3 in cycles 3, 4, 5 (cycle 3 counts because the hits reach 3). | AC97(a) |
| R2 (must): daily cap left the marker deleted | `zoho_detail_outage_pending` is deleted only by a reset that runs; a blocked qualifying cycle leaves it, and the first qualifying cycle of the next Colombo day resets. The UPDATE, the DELETE and the `zoho_recovery_reset_day` write are one `IMMEDIATE` transaction. Both keys use `INSERT ... ON CONFLICT(key) DO UPDATE SET value = excluded.value` with a non-empty value (`001-schema.sql:129`). The "second outage the same day" sentence corrected ("until the next Colombo day's reset"). AC97(c) gains the blocked-reset and next-day clause. | §5.2 (recovery reset), AC97(c) |
| R3 (should): AC97 fixtures | Lane PR stubbed off in (a)-(c) with a new case (e) for PR on (2 requests at cycle 6, counted after the reset, so two SOs end cycle 6 at count 1); (b) says about 20 new or changed P1 SOs arrive each cycle. | AC97 |
| N1 | Raw identity trimmed as `mapRow` trims (`String(v).trim()`, `columns.js:21`) before matching the quarantine mark. | §5.2 (row quarantine) |
| N2 | `detail_outage_hits` stops at 3; stated not to be in any field list. | §5.2 (per-SO counter) |
| N3 | Cycle-end accounting (hits plus the three error fields) is one transaction per SO. | §5.2 (per-SO counter) |
| N4 | Conversion rate stated precisely: 3 SOs per 5 cycles (about 0.6 per cycle, about 40 over a 66-cycle outage day) with the derivation, replacing "one per cycle"; the guard-plus-reset pairing recorded as deliberate. | §5.2 (honest limit) |
| N5 | `sync_state IS NOT 'missing_in_zoho'` added to the reset's WHERE; AC97(c) checks it. | §5.2, AC97(c) |
| Loose end: `zoho_detail_outage` log counter | Given a home: derived from run rows (a cycle is the span between two `so_headers` run starts; ended `detail_outage` if a detail run in it has that error; fires once when the newest three cycles all did and the one before did not). No counter, no `file` column. | §5.2, AC77 |

## Revision 8 changes (plan-critic round 8 APPROVED Rev 7; five required edits and the lead's outage-guard change)

Round 8's verdict was **APPROVE**. Rev 8 carries its five required pre-implementer edits plus the lead's change to the outage guard. Round 9 re-reads only B1's new mechanism and the recovery reset. Untouched, because rounds 7 and 8 verified them: the call budget (AC72(b) is 297 at most 340, no budget line moves), the backoff cadences, the `so_line_items` map, `row_quarantine_at` in 005 (additive, nullable, lint-clean, clearing on an unchanged row verified at `upsert.js:18-21`) and AC numbering (AC1-AC99, no collisions).

| Item | Fix | Where |
|---|---|---|
| **B1 gaps (round 8 graded PARTIAL):** the cycle-level `outage_streak` needed predicates no run-row field answers, defined precedence twice, and "heals 15 min after recovery" was false above about five SOs (lane PR heals 2 per cycle, 10 per day) | **History of the decision:** the lead first adopted the critic's simpler per-SO guard on the critic's recommendation ("the damage is those three"). I showed it does not hold as described: converted SOs leave lanes P0-P5, the next three surface, and either mechanism converts about **one SO per cycle** during a sustained outage. The lead then chose the per-SO version **on its own merits** (one nullable column, no cycle-level reasoning, state next to `detail_fail_count`, no overloading of the `file` column that the Imports screen renders), plus an automatic recovery reset for the real damage (the six-day heal tail). `outage_streak` and the `file` overloading are deleted. New `zoho_so_headers.detail_outage_hits`: counts guard-suppressed `upstream_5xx`/`timeout` failures per SO, reset only by an `ok` response for that SO; at 3 the failure is counted normally. **Recovery reset:** the first cycle with an `ok` detail response after an outage cycle (and not itself ending `detail_outage`) clears count and error for every SO whose `detail_last_error` is `upstream_5xx` or `timeout`, at most once per Colombo day (two `settings` keys), one `info` log; deterministic classes are not reset; `ZOHO_RESET_SYNC_PROBLEMS` stays as backstop. The honest limit (one SO per cycle while it lasts; a permanently 5xx SO re-converts after each daily reset and costs a few frozen cycles a day) is stated in the spec. "Heals 15 min after recovery" deleted. Lane PR excluded from the consecutive-failure counter. | §5.2 (outcomes, Counting, Outage guard, per-SO counter, honest limit, recovery reset, handler step 5), Data model (SQL and text: 005 now has two new nullable columns, `row_quarantine_at` and `detail_outage_hits`), Failure modes, Observability, AC69, AC97 (four cases: head of queue, production ordering, recovery, PR excluded) |
| B2: quarantine mark can be lost in the rolled-back SAVEPOINT | Stated: identity is read from the raw row, and the mark is written **after** the row's SAVEPOINT has rolled back, in the page transaction. AC98 now tests `write_error` as well as `map_error`. Bundle residual reworded: a quarantined *update* leaves `qty_bundled` overstated indefinitely (no 7-day bound; never marked `missing_in_zoho`); accepted, no mechanism added. `quarantined_sos` excludes `missing_in_zoho` rows (my call). | §5.2 (row quarantine), §6 (status), AC98 |
| B3: gate load-bearing on an unsampled endpoint | V3 records all seven quantity keys on every inventory line of every sampled SO, including one SO with no pick list and one with a service line, and whether each is a number or numeric string; omission is a return-to-spec-writer outcome like V4. "Numeric" defined as `toNumber` yielding a non-null number (`shared/text.js:13-17`). | Pre-build verification (V3), §5.2 handler step 0 |
| V1 gate 1% | Changed to "any row of the 200-row page, recording the key and the count", with the reasoning (structural keys; the 5% systemic guard would not trip). | Pre-build verification (V1) |
| N5: the sync floods `GET /api/admin/imports` | Recorded as a **Release 0 behaviour change**: `WHERE source <> 'sync'` on `server/routes/admin-imports.js:18`; AC99. | §6, AC99 |
| Consequences of the sync's own required keys | A bundle row lacking `status` or `created_time` is mirrored with NULLs; a NULL `status` can only lower `qty_bundled`; a NULL `date` bypasses the 2024 cutoff and the row is written. | §5.2 |

## Revision 7 changes (answers to plan-critic round 7)

Rev 7 needs a plan-critic round 8 (a targeted re-read of B1, B2, B3 and AC72(b)). Round 7 re-derived and confirmed the budget, both backoff cadences, the quarantine thresholds, the `so_line_items` map, migration 005 and AC numbering; none of that was touched. `MOBA_P` needs no change.

| Finding | Fix | Where |
|---|---|---|
| **B1: three broken SOs freeze all detail work** | New `outage_streak` (consecutive detail cycles ending `detail_outage`, derived from the detail run rows, survives restart). While it is 3 or more, the guard still stops the cycle after 3 failures but the failures **are counted**, so the SOs become sync problems, leave the queue, and everything behind them proceeds. Safe because backoff heals a real outage 15 min after recovery. | §5.2 (Counting, Outage guard), Failure modes, AC97 (AC69 unchanged) |
| **B2: a row that quarantines every run leaves flags shown on frozen data** | New nullable column `zoho_so_headers.row_quarantine_at` (005): set when a header row carrying `salesorder_number` or `salesorder_id` is quarantined, cleared by the next good list row. While set, a flag-eligible SO is `checking` (flags hidden), counted in "being checked", and listed on the problems route with `reason='row_quarantined'`. `not_object` / no-id rows and bundle rows are the stated accepted residual. §3 and the §5.3 "no single SO" sentence corrected. | §2 (flag_status), §3, §4 (level 2), §5.2 (row quarantine), §5.3, §6 (problems, status), Data model changes, AC98 |
| **B3: line write nulls an absent quantity, NULL reads as 0, false flag** | Both fixes: the shape check requires all seven quantity keys, numeric, on every `item_type='inventory'` line (absence is `bad_shape`, fail closed), and the line write passes `upsertGuarded` only fields whose source key is present (covers non-job lines). The unconditional "NULL reads as 0" sentence is narrowed. | §5.2 (line column map, handler steps 0 and 2), AC96 |
| N1: AC72(b) unsatisfiable | Fixture shrunk to 150 P1 SOs with the arithmetic (about 297 calls, at most 340). | AC72 |
| N2: P3 guarantee false across slots | Sentence corrected: holds within a cycle only; a later P0 can wait; measured, never a false flag. | §5.2 (queue order) |
| N3: `required` list contains `quantity_shipped` | The sync uses its own per-row keys (headers `salesorder_id`, `salesorder_number`, `last_modified_time`; bundles `bundle_id`, `reference_number`); the map's `required` is not used. V1 now records the required keys on a 200-row page; omission on more than 1% of rows is a return-to-spec-writer outcome. | §5.2 (row quarantine), Pre-build verification (V1) |
| N4: force lever crash loop | Forced attempt skipped for a module if an `ok` `full_list=1` run of it exists today. | §5.2 (full-list attempts) |
| N5: reset lever no-op when sync disabled | Rollback step 5 says the sync must be enabled. | Rollback plan |
| N6 (record only) | Two-Division-tag conflict with R4 stated; behaviour unchanged. | Readings (R4) |
| N7: `retry_reserve_left` wording | Reworded: protects the calls from night history, does not guarantee PR gets them. | §5.3 |
| N8: `shared/missing-rules.js` | Marked as a new file. | §2, §4, AC59 |
| N9: `zoho_so_facts` | Stated: the sync never recomputes it; nil blast radius today. | Non-goals |
| N10 (record only) | Rev 3 archive table: "(later raised to 130)". | Revision 3 changes |
| Two sentences | Nested transaction re-throws, page loop must catch per row; Sunday: retries, P3 and second attempts displace planned live work. | §5.2, §5.5 |
| Pending lead decision | Round 7's observation added: adopting it invalidates AC84, AC85 and part of AC94, so decide before test-author starts. Section otherwise unchanged; still not adopted. | Pending lead decision |

## Revision 6 changes (answers to plan-critic rounds 5 and 6)

Rev 6 needs a plan-critic round 7 before test-author starts. Round 6 confirms and supersedes round 5's overlapping items (its B1, B2 and N1-N6); the rows below cite both. "Applied" means the body sections in the last column changed; "declined" gives the reason.

| Finding / decision | Fix | Where |
|---|---|---|
| **Round 6 B1 (= round 5 B1): the sync-problem exile is irreversible at 2am** | The 24 h, night-only, 10-a-day retry is replaced by **per-SO backoff**: `delay(1)=delay(2)=0`, then 15 min doubling to 6 h; retries run in a new live-lane group PR in any slot, at most 2 a cycle and `PROBLEM_RETRY_DAILY_MAX = 10` a day, funded by a new `retry_reserve_left` carved out of `history_available`. The first three attempts, the 3-strike `sync_problem` state, the admin list and R10 are unchanged. One env-file lever `ZOHO_RESET_SYNC_PROBLEMS` zeroes the counts at start (idempotent, no hand-written DB write). Conflict noted: this changes the retry rows of the lead's AC64 and of AC56/AC66, which round 5 and round 6 both blocked; flagged for the lead in "Pending lead decision". No new column (the delay is derived). | §5.1, §5.2 (per-SO failures: backoff retry, reset lever, cost bound, queue order), §5.3 (schedule, definitions, lanes, guarantees), §5.5, §6 (status, problems), Non-goals, Failure modes, Observability, Rollback plan, AC56, AC64, AC66, AC73, AC74, AC75 |
| **Round 6 B2 (= round 5 B2): "cannot produce a false flag" if V4 fails** | Took the return-to-spec-writer route: V4 is now a **pre-build gate**; "no change is needed either" is withdrawn; failure means the build does not start. §3 and the failure table say the guarantee holds only if V4 passes and state the ~20 h window that a V4 failure would mean. `detail_sig` re-described as a second net. | §3, §5.2 (queue reason d), Failure modes, Pre-build verification (V4), AC38(c) |
| **Round 6 B3: 18 line columns with no mapping, types or shape rules** | New `so_line_items` section of `config/zoho-columns.json` (17 typed entries; `bool` for `is_combo_product`, `number` for quantities, `raw` for ids); `is_combo_product` made nullable in 005; `division_tag` extraction rule from `tags[]` (zero, one, several distinct, blank, malformed); fifth outcome class `handler_error` counted like `bad_shape`; line shape check (`quantity` numeric, `tags` array); the false claim "there is no second mapping" rewritten with the four hand-coded derivations named. Also the header write from the detail is limited to detail-writable fields (see round 6 N8). | Current behaviour, §5.2 (field mapping, line column map, per-SO failure outcomes, handler steps 0-2), Data model changes (SQL), Failure modes, AC80, AC81, AC82, AC83, AC55 (static test now also covers lines) |
| **Round 6 B4: night P1 unbounded, §5.3 guarantee text wrong** | Night P1 now shares the history allowance (`min(history_available, ...)`) with night P3 and history, P1 first; night P0 and P2 are named as the only night detail work drawn from the day reserve; the guarantee text is corrected (at 06:00 `live_available >= 130 − night P0/P2 spend`, at least 80 on the estimates). Numbers moved by the retry carve-out: history at 00:00 63 → 53 (Sunday 3 → 0; cap 500: 163 → 153, 103 → 93). Steady totals 280 / 340 unchanged. | §5.3 (definitions, lanes, guarantees), §5.5, Q11, Failure modes, AC72 |
| **Round 6 B5: the 02:00 header full list is a single point of failure** | New "Full-list attempts" rule for headers and bundles: first-cycle trigger; the no-watermark first delta **is** the full list and is credited `full_list=1` (no double paging); a retryable failure is retried in the next slot at least 60 min later (03:00 after 02:00), at most `FULL_LIST_MAX_ATTEMPTS_PER_DAY = 2`, second attempt funded from `live_available`; `suspect_short_list`, cap and `too_many_bad_rows` not retried; level 1 accepts a full list as a delta; `list_reserve` counts the 43 / 60 only while an attempt is due; operator lever `ZOHO_FORCE_FULL_LIST`. The 02:30 Sunday bundles list moves to the 03:00 slot (round-5 N6). Pending lead decision records the simpler alternative and is **not** adopted. | §4 (level 1, freshness line), §5.1, §5.2 (watermark, run table, full-list attempts), §5.3 (schedule, `list_reserve`), Failure modes, Rollback plan, Pending lead decision, AC84, AC85 |
| **Round 6 B6 (= round-5 N1, elevated): one malformed row blanks the screen** | New "Row quarantine": only a page-level defect fails the page; every row defect (not an object, no id, a `required` key missing from that row, `mapRow` error, handler error in a per-row SAVEPOINT) skips that row, records id and reason in `warnings`, and the run **still ends `ok`** so W moves. Systemic guard `too_many_bad_rows` (at least 10 and more than 5%). The sync checks every row, not the first row only. Residual effect stated. | §5.2 (row quarantine, field mapping), §5.4, Failure modes, Observability, AC86 |
| Round 6 N1: list path still nulls header fields | Applied: "present source keys only" for list rows too; V1 records whether the OAuth list has `cf_*` keys and whether its default filter returns every status. | §5.2, Pre-build verification (V1), AC93 |
| Round 6 N2: AC8 vs `rows_upserted` | Applied: AC8 also asserts no `captured_at` change; the sync's `rows_upserted` meaning (rows changed) is stated against `run.js:80`. | §5.2 (run rows), Current behaviour, AC8 |
| Round 6 N3: run `captured_at`; freshness side effect | Applied: run `captured_at` defined; the effect on `shippedFresh` / `bundlesDataAge` stated as intended and harmless. | §5.1 |
| Round 6 N4: `composite_item_id` unconditional; SH import not tested | Applied: `composite_item_id` written only when `ctx.source==='sync'`; AC92; AC46 extended to an SH import. | §5.2 (field mapping), AC46, AC92 |
| Round 6 N5: drafts | Applied (exclude): a draft SO's lines are not jobs and the drill-down answers 404; drafts are still loaded when flag-eligible. | §2, §6, AC87 |
| Round 6 N6 (with round-5 N6): slot alignment; 02:30 | Applied: wall-clock alignment, restart behaviour and no replay stated; Sunday bundles list moved to the 03:00 slot. | §5.3, AC94 |
| Round 6 N7: missing ACs | Applied: AC75 (`PROBLEM_RETRY_DAILY_MAX`), AC76 (`zoho_sync_throttled`), AC77 (`zoho_detail_outage`), AC78 (`counters_complete=true`, `flags_since`). | Acceptance criteria |
| Round 6 N8: detail lacks all four header quantities; ping-pong cost | Applied, and fixed at the cause: the detail path never writes the seven signature fields nor `total_cents`, `created_at`, `modified_at`, so `detail_sig` is wholly list-derived and no list/detail disagreement can cost one extra fetch per in-scope SO per night. AC70 extended to all four quantities and the three status fields; V3(b) samples 20 SOs. | §5.2 (handler step 1), Current behaviour, Failure modes, Pre-build verification (V3), AC70 |
| Round 6 N9 (= round-5 N2-N5): four stale items | (1) History loading: sync-problem SOs leave X and Y (AC79). (2) `checking` and the note limited to flag-eligible SOs; P3 refreshes of loaded pre-cutoff SOs named as unplanned, last in the live lane (budget row, `p3_calls_today`); not folded into the 280 because the count is unmeasured. (3) The backwards `:120` header-quantity claim corrected with evidence. (4) The sync inherits the 2024 cutoff (AC95). Round-5 N4's "consider dropping the status clause" **declined**: it is the lead's R11 formula and the first full-list census measures its cost. | §2, §4, §5.2 (queue order, record cutoff), §5.5, Current behaviour, AC79, AC90, AC95 |
| Round 6 N10: `division_source` when NULL; error column | Applied: `division_source` is `null` when `division_code` is null; the run `error` column holds only fixed codes; AC91. | §2, §5.2 (run rows), §6 (JobDTO, status), AC91 |
| Round 5 / round 6 simpler alternatives | **Not adopted:** (a) the daily header full list off the critical path is a lead decision; recorded in "Pending lead decision" with its effect (43 calls a day, 280 → 237). (b) A `detail_next_try_at` column replacing the exile: declined, the delay is derived from `detail_last_error_at` and `detail_fail_count`, and the 3-strike state is the lead's. (c) Dropping P2 re-confirmation: declined, it is the lead's call and unchanged since Rev 5. | Pending lead decision |
| Human decision: Q3 answered | `OPD - PackPro Unit` maps to `PACKPRO`, Ishan only. Alias row in 005 (a tag-mapping rule, not a schema change). Consequence noted: PackPro-tag / OPD-header SOs are `division_conflict` on the admin list until Q2 is decided. | §1, §2, Data model changes, Answered questions, AC36, AC88 |
| Human decision: Q10 answered | PM2 `production-dashboard`, port 4300, live directory `/root/production-dashboard`, registered in shdeploy and protected-paths before the first deploy; the human runs every deploy command. | Current behaviour, Non-goals, Rollback plan, Answered questions |
| Q2 evidence | Evidence file cited, recommendation stated, **not confirmed**: Q2 stays open and blocking. | Readings (R2), Open questions |
| New evidence: five seeded divisions have no manager | PCU, PCLU, DPU, PPU, CWU (`002-seed.sql:9-10`): such a job is on the admin Unassigned list with `no_manager`, visible to gm and admin, absent from every manager's list until the admin adds a pair. (`MOBA_P` is unreachable: no alias.) | §1, §6, Failure modes, AC89 |
| Stale citations found and fixed (rule 6) | `run.js:88` → `86-89` (first row only); `salesorders_since_2026-09-15.json:143-149` → `142-149`; `zoho-pull-snippet.js:38-45` → `38-41` (row check is `:42-45`); the seed lines `9-11` → `9-10`; the `:120` header-quantity claim and the `run.js:87-88` "as today" claim corrected. Every other `file:line` in the body was re-checked against `/root/dev/production-dashboard` (HEAD `b0cd339`) and the 19 Sep samples. | Current behaviour, §5.2, Failure modes |
| Codemap | No change: it maps Release 0 code and records none of the Rev 6 additions. | none |

## Revision 5 changes (lead design decision 28 Sep; answers to plan-critic round 4)

Rev 5 needs a plan-critic round 5 before test-author starts.

| Finding / decision | Fix | Where |
|---|---|---|
| Lead decision: two-level freshness (rounds 3 and 4 both blocked on "one SO blanks the whole screen") | Level 1 `preview_fresh(SPS)` = sync health only (`no_full_header`, `full_list_old`, `delta_stale`, `bundles_stale`); `flag_backlog` removed entirely (definition, reason code, status field, log field, AC34 case, AC40(b), AC56/57 assertions, failure-mode text, §5.3 guarantee). Level 2 per-job `flag_status ∈ {current, checking, sync_problem}`: `checking` when the SO has a refresh reason, whose core is the lead rule `detail_fetched_at < captured_at` (new refresh reason (b)); a shown flag needs level 1 **and** `current`. "Being checked: N · sync problem: M" note next to Documents missing; `checking` object in `/api/jobs`; `flag_status` in JobDTO; `oldest_refresh_wait_min` measured instead of gated. | Problem, §2, §3, §4, §5.2, §5.3, §6, Failure modes, Observability, AC34, AC40, AC42, AC56, AC57, AC67 |
| Round-4 B1a: detail 404 | Outcome `not_found` (HTTP 404 + the not-found body code recorded by V3) marks the header `missing_in_zoho` at once; any other 404 is an SO failure `http_404_other`. | §5.2, §5.4, Failure modes, V3, AC65 |
| Round-4 B1b: per-SO failure counter | New 005 columns `detail_fail_count`, `detail_last_error`, `detail_last_error_at`. Counted outcome classes; applied at cycle end; outage guard (3 consecutive 5xx/timeouts stop detail work and count nothing; no detail after a failed header delta). After `DETAIL_FAIL_LIMIT = 3`: out of every lane, admin "Sync problems" list (`GET /api/admin/zoho-sync/problems`), one `error` log, retried once per 24 h in night slots (`PROBLEM_RETRY_DAILY_MAX = 10`, module `so_detail_retry`, history allowance). Budget row added; steady total 277/337 → 280/340. "IT notified" defined (R10). | R10, §2, §5.2, §5.3, §5.5, §6, Non-goals, Data model, Failure modes, Observability, AC5, AC11, AC36, AC37, AC56, AC64, AC66, AC69 |
| Round-4 B1c | AC56 rewritten (P0 SO answering 503 all day: sync problem after 3 night attempts, screen fresh 06:00–20:00, other job's flag shown); AC64 (one SO failing 3 days), AC65 (404 disappears at the end of that cycle), AC66 (sync-problems list). | Acceptance criteria |
| Round-4 B2: "open" used xlsx status values | "Open SO" defined from API fields (R11, §2): `status NOT IN ('void','draft')` and (`status NOT IN ('fulfilled','closed')` or shipped < ordered or invoiced < ordered); unknown statuses fail toward loading. In-scope uses it. The "~1,400 open" figure marked as xlsx vocabulary. V1 records the status vocabulary; first full list logs a status census. Q14 added for the size risk. | R11, Current behaviour, §2, §5.2, §5.5, Failure modes, Observability, V1, AC68, Q14 |
| Round-4 non-blocking 1: `required` list vs detail | The column map's `required` list applies to list rows only; the detail has its own shape check (handler step 0). | Current behaviour, §5.2, Failure modes, AC70 |
| Round-4 non-blocking 2: `sync_state` in field list | Sync handlers add `sync_state` to their field list when `ctx.source='sync'`. | §5.2, AC60 |
| Round-4 non-blocking 3: bundle deletions weekly | Stated as an exception to the §3 safety claim and as a failure mode; V7(c) measures bundle deletions. Daily bundles full list not adopted (≈60 calls; does not fit the cap-400 budget). | §3, §5.4, Failure modes, V7 |
| Round-4 non-blocking 4: night P3 not limited by the day reserve | Night P3 limited by `history_available`; AC71. | §5.3, AC71 |
| Round-4 non-blocking 5: signature loop | V3(b) records list-vs-detail status agreement; failure-mode row added. | V3, Failure modes |
| Round-4 simpler alternative (drop P2) | Not adopted: the lead did not decide it, and P2 is independent of the two-level freshness change. Recorded for the lead. | — |
| Codemap | No change: the codemap maps Release 0 code and has no reference to `flag_backlog`, the in-scope status list or the detail queue. | — |

## Revision 4 changes (answers to plan-critic round 3)

Rev 4 needs a plan-critic round 4 before test-author starts.

| Finding | Fix | Where |
|---|---|---|
| B1 `flag_backlog` blanks the screen; circular definition | `flag_backlog` counts only P1 reasons, aged from `captured_at`. P0 waits from `threshold_instant`, P2 from `detail_fetched_at + 20 h`; both reported (`oldest_p0_wait_min`, `oldest_p2_wait_min`), neither gates freshness. "Stored flag" (no freshness term) vs "shown flag" defined; P2 reads stored flags, so the loop is gone. Re-confirmations budgeted: `RECONFIRM_DAILY_MAX = 30`, own run module `so_detail_reconfirm`, `DAY_DETAIL_RESERVE` 100 → 130, steady total 247/307 → 277/337, history at 00:00 93 → 63 (Sunday 33 → 3), AC38(a) 320 → 340. ACs (a), (b), (c) added. | §4, §5.2, §5.3, §5.5, §6 status, Failure modes, Observability, AC34, AC38, AC56, AC57, AC58, Q11 |
| B2 `bundle_missing` unverified, may flood | Lead decision: `bundle_missing` removed from the preview. Stage 5 shows `detected` / `not_detected` (neutral grey) / `n_a`. Consequence: for assembly lines `qty_produced = max(qty_bundled, qty_packed)` so an unmatched but packed line is not stuck "In production" (reversible after V7). V7 recorded as a follow-up that decides whether the flag returns. | Problem, Current behaviour, §2, §3, §4, §6, Failure modes, Non-goals, AC29, AC30, AC32, AC54, AC59, Q5, Follow-up V7 |
| N1 AC28 vs `history.total` | Key renamed `history.in_scope`. | §4, §6, AC49, Failure modes |
| N2 wrong `missing_in_zoho` from offset paging | Every sync write sets `sync_state=NULL`; the next delta clears a wrong mark. | §5.2, §5.4, Failure modes, AC60 |
| N3 NULL `detail_sig` breaks the lane split | Reasons 2 and 3 apply only when `detail_fetched_at IS NOT NULL`. | §5.2, AC61 |
| N4 crash hides spent calls | `api_calls` incremented per request in the lease-renewal transaction. | §5.3, §5.5, AC62 |
| N5 "present" header fields | Detail header goes through the `so_headers` column map; presence judged on the source key (`custom_field_hash` for `cf_*`); V3 records it. | §5.2, AC43, V3 |
| N6 `runSweep` picks up sync runs | Stated; sync runs write a JSON array in `changed_so_numbers`; `sweep.js` unchanged. | Current behaviour, §5.2, Non-goals, AC63 |

## Revision 3 changes (answers to plan-critic round 2)

| Finding | Fix | Where |
|---|---|---|
| B1 midnight slot eats the day's detail budget | Queue split into a live lane (P0–P3) and a history lane (P4–P5). History runs in night slots only and is limited to `cap − used − list_reserve − day_reserve_left − 60`, with `DAY_DETAIL_RESERVE = 100` (later raised to 130) protected for live work during 06:00–20:00. Run rows `so_detail` / `so_detail_history` make the split measurable. | §5.2 (lanes, queue order), §5.3 (budget formulas), §5.5, §6 status, Failure modes, Observability, AC40, AC41, AC38(a) |
| B2 `bundle_missing` false alarm on bundle-then-package | Bundles-seen gate: shown only once an ok bundles run started after `packed_seen_at`; not queued for confirmation while waiting. §3 safety claim corrected. | §3, §4, Failure modes, AC32, AC54, Q5 |
| N1 watermark skips rows after a partial failure | `W(m)` = `started_at` of the newest **ok** sync run of the module (delta or full list); failed/warning runs never move it; `delta_incomplete` case added. No schema change. | §5.2 (delta watermark), Failure modes, AC9, AC53 |
| N2 bundle field mapping | Sync reuses `config/zoho-columns.json` `bundles` map (`quantity` ← `quantity_to_bundle`, `:134`); one new `composite_item_id` entry; handler field list gains it. | Current behaviour, §5.2, Data model (config note), AC55, V2 |
| N3 Saturdays | Stated in §4; Q13 added (config-only answer via the existing calendar screen). | Current behaviour, §4, Failure modes, Q13 |
| N4 AC40 locks the bug in | AC40 rewritten to the critic's shape: 10:05 SO fetched by 10:15/10:30, `flag_backlog=0` all day, fresh at 14:00, history only at night. | AC40 |

## Revision 2 changes (answers to plan-critic round 1)

| Finding | Fix | Where |
|---|---|---|
| B1a daytime detail starves deltas | Detail calls per cycle = `min(cap − used − reserve − 60, 20/250)`; reserve covers every remaining list call of the day | §5.3, AC40, AC41 |
| B1b backlog hides everything | `detail_backlog` replaced by `flag_backlog` (flag-eligible SOs only); "History loading X of Y" line; `counters_complete` | §4, §6, AC49 |
| B1c backfill order/scope | In-scope = flag-eligible ∪ open ∪ already loaded; queue P0–P4, legacy last | §5.2 |
| B1d budget table, AC38(a) | Table rebuilt (night cadence, bundles every 30 min, confirmations, margin); AC38(a) = ≤ cap daily, ≤ 320 after load; AC40 backfill day | §5.5, AC38, AC40 |
| B2 `last_modified_time` unverified | `detail_sig` from list quantities/statuses re-queues SOs; flags need a confirming fetch after the threshold; V4 added | §4, §5.2, AC42, AC51, V4 |
| B3 partial deliveries | `*_changed_at` (latest increase); shipment/invoice rules generalised to `packed > shipped`, `shipped > invoiced` | §3, §4, AC16, AC50 |
| N1 kit combos | `combo_type` stored; bundle rules only for `assembly` | §2, §3, §4, AC30, V6 |
| N2 bundles unmatched until Sunday | Bundles full list at first cycle without one | §5.2, AC45 |
| N3 old SOs flood counters | `legacy` (> 180 days) out of counters/default list; Q12 | R9, §2, §4, AC48 |
| N4 hidden every night | Hourly night deltas; day/night max ages | §4, §5.3, AC34 |
| N5 lease expiry | Renew per request; stop on lost lease; ≤ 250 requests/cycle | §5.3, AC47 |
| N6 bundle deletions | `zoho_bundles.sync_state` + weekly reconcile | §5.4, data model, AC44 |
| N7 repeated item | Deterministic allocation by `item_order` | §2, AC52 |
| N8 manual imports | CLI refuses SPS header/bundle imports while sync active; `shippedFresh` dropped from preview freshness; `missing_in_zoho` for any source | §4, §5.3, §5.4, AC13, AC46 |
| N9 rollback target | PM2/shdeploy status stated; rollback in PM2 terms; Q10 | Rollback plan, Q10 |
| N10 AC37 weak | Four concrete assertions on a v5 fixture | AC37 |
| N11 shared quota | Q1(b) asks for the org-wide total and co-users | §5.5, Q1 |
| Unverified: bundle reference = SO number | V5 offline check | Pre-build verification |
| Also found | Detail header upsert could null list-only fields (`upsert.js:19-21`) → only present fields written | §5.2, AC43 |

## Plan-critic round 1

VERDICT: BLOCK

The design is mostly sound, but three things need fixing in the spec before any code is written. Two of them make it fail the user's "show it ASAP" goal: for roughly the first week, counters and flags would be hidden and the job lists incomplete. The third makes the missing-document flags fire wrongly on partial deliveries.

## Blocking findings

**[B1] The daytime detail budget breaks the daily call cap, and the history backfill hides the whole screen for about a week after go-live.**
- **The cap problem:**
  - A daytime cycle is 1 header delta + 1 bundles delta + up to 20 detail calls, so 22 calls. 57 cycles a day comes to 1,254 calls, against `ZOHO_DAILY_CALL_CAP` of 400 (spec §5.2 row "SO detail", §5.3).
  - The §5.5 table (about 237 a day) leaves out the daytime detail spend. It never reserves calls for the deltas.
  - While a backlog exists, the cap is hit after about 18 cycles, around 10:30. Then "all sync stops until the next Colombo midnight" (§5.5), so the delta goes stale and everything is hidden for the rest of the day.
- **The backlog problem:**
  - The backfill covers every in-scope SO: open SOs of any age plus the last 90 days. Open SOs alone are 1,400 (60+110+82+664+190+294, `scout-sps.md:72-74`), plus about 900–1,200 recent ones, so roughly 2,000+.
  - `preview_fresh` requires `detail_backlog = 0` (§4 point 2). So counters and flags stay hidden until the backfill drains, which takes about 7 or more days at about 285 detail calls a day.
  - Jobs only exist once their lines are fetched (§2), so managers' lists are also incomplete during that time.
  - AC38(a) (≤300 calls a day) will fail by design during the backfill.
- **Required change:**
  - (a) Daytime detail budget = `cap − used − (remaining delta cycles × 2) − 60`, so the deltas can never be starved.
  - (b) Limit the `detail_backlog` freshness term to flag-eligible SOs (created on or after `PD_FLAGS_SINCE`). Show backfill progress ("history loading X/Y") instead of hiding everything.
  - (c) Narrow or order the backfill: open SOs from the last N months first, older open SOs last.
  - (d) Fix the §5.5 budget table and AC38(a) to match, and add an AC for "deltas still run on a backfill day".

**[B2] The main assumption is unverified: that packing, shipping, invoicing or pick lists update the SO's `last_modified_time`.**
- Line quantities (picked, packed, shipped, invoiced) are only re-fetched when `H.modified_at > max(line.so_modified_at)` (§5.2 detail queue).
- If Zoho does not update the SO's `last_modified_time` when a package, shipment or invoice is created, then:
  - the lines freeze after the first fetch;
  - `shipment_missing` and `invoice_missing` fire falsely;
  - jobs never close.
- The freshness gate cannot catch this, because `detail_backlog` relies on the same signal. The nightly full list is no safety net either: `upsertGuarded` does not change `modified_at` in that case (`cli/import/upsert.js:17-18`).
- The evidence is only suggestive. JOBORDER-08589 was created 09:15:44, last modified 11:09:45, and has a pick list and two packages (`salesorders_since_2026-09-15.json:6488-6489,6103-6112,6551-6610`). The time difference could just as well be an edit to the SO itself. Shipments and invoices were never observed.
- **Required change:** add pre-build check V4. Watch a real SPS SO before and after a package, a shipment and an invoice are created, and record `last_modified_time` each time. Write the fallback into the spec now, for example: re-fetch the detail when the header `shipped_status`, `invoiced_status` or `status` changes. That needs one stored "status at last detail fetch" column.

**[B3] The `*_seen_at` timestamps cause false alarms on partial and repeated deliveries.**
- `seen_at` is the first moment a quantity went above 0, and it never moves on later increases (§3, AC16).
- `invoice_missing` is `qty_invoiced < qty_shipped AND wd(shipped_seen_at) >= 2` (§4). Example:
  - day 1: 500 shipped and invoiced;
  - day 10: 300 more shipped;
  - the job is flagged immediately, before anyone could raise the invoice.
- `shipment_missing` has the same problem with partial packages.
- Partial lines are common: 288 lines in 2026, and 1,576 lines have status partially_invoiced (`scout-sps.md:28,51`).
- **Required change:** also store the capture time of the latest increase (for example `shipped_changed_at`, `packed_changed_at`) and measure the working days from that. Add an AC with a two-step shipment.

## Non-blocking findings

- **[N1] Bundle rule uses the wrong field.** Every sample line has `is_combo_product: true` with `combo_type: "assembly"` (`:6020-6021`). If kit-type combos exist, they are never bundled, so `bundle_missing` would fire the moment they are packed. Store `combo_type` and apply the bundle rule only to `assembly`.
- **[N2] Existing bundles can't match lines until Sunday.** Bundles already mirrored get `composite_item_id` NULL (AC36). They stay unmatched until the Sunday full list, so stage 5 shows ✘ and `qty_produced=0` for combo lines until then. Run a bundles full list on first start, or whenever any SPS bundle has a NULL `composite_item_id`.
- **[N3] Old open SOs flood the counters.** Only flags have a cutoff. About 1,400 open SOs, including 170 from 2024 (`scout-sps.md:72`), will fill "Past due" and "In production" on day one. The user should decide: a separate "legacy open" bucket, or a default filter.
- **[N4] Counters are hidden every night.** The delta runs only 06:00–20:00 and the freshness window is 45 min, so counters show "—" every day from about 20:45 to 06:15, including when the GM checks in the evening. Either say so in the UI or run the header delta at night as well.
- **[N5] The lease can expire mid-cycle at night.** The lease lasts 10 min, but a night cycle can run longer: 340 calls at 30 a minute is about 11.3 min (§5.3). Renew the lease per page, or cap each night cycle at 250 calls or fewer.
- **[N6] Bundle deletions are never reconciled.** §5.4 only handles SO headers, so a deleted or cancelled bundle keeps counting. The weekly full list should mark missing bundles the same way.
- **[N7] Double counting on repeated items.** If the same `item_id` appears on two lines of one SO, `qty_bundled` counts the same bundles on both lines. Document this or apportion.
- **[N8] Manual imports can undo the sync's bookkeeping.**
  - The manual CLI pull still writes `source='pull'` (`upsert.js:43`). Any header it overwrites falls out of the delta watermark and out of `missing_in_zoho` marking, both of which filter on `source='sync'`. Block the SPS pull imports while the sync is enabled.
  - `shippedFresh`'s `header_older_than_movements` check (`freshness.js:8-11`) means one manual package or shipment import hides the whole preview until the next 02:00 full list. The preview does not read those tables, so drop that term from `preview_fresh`.
- **[N9] The rollback plan points at a service that isn't set up.** Steps 2 and 3 use `shdeploy rollback <service>` and "the human restarts the service". production-dashboard is not in the service table in `/root/.claude/CLAUDE.md` §4b, and Release 0 has never been deployed. Name the PM2 service (port 4300, `server/config.js:35`) and the runbook steps.
- **[N10] AC37 is too weak.** "Running the import CLI once" does not prove the claim about the 143 tests. Require specific assertions against a v5 fixture database: a Release 0 bundles import and an import-runs insert both succeed, and startup logs the "newer than this code" warning (`migrate.js:36-38`).
- **[N11] The daily quota is shared.** The SPS org's daily API limit is shared with the INV services (500 a day each, `/root/CLAUDE.md` §2). Q1(b) must confirm the org-wide total, not just this service's share.

**Checked and found fine:**
- **Idempotency:** the `(org, line_item_id)` key, `upsertGuarded`, and AC8.
- **Partial failure:** one transaction per SO, crash recovery, AC10/AC15.
- **Access control:** manager scoping, intersecting the division filter, the drill-down returning the same 404 for "unknown" and "not visible", GM sees all (AC22–AC25).
- **Read-only Zoho:** AC1/AC2.
- **Migration 005:** additive, passes the lint (`lint-migrations.js:71-73`), and Release 0 starts on a newer database (`migrate.js:36-38`).
- **Scope:** nothing out of scope.
- **Code facts the spec relies on:**
  - Stage seeds match AC31 (`002-seed.sql:36`).
  - `MOBA Punching Unit`→MOBA already exists (`002-seed.sql:50`), so Q8's default holds.
  - `cmpKey` is whitespace-collapsed lowercase (`shared/text.js:6`), which matches the migration's alias keys.
  - Pairs require a coordinator (`admin-config.js:246`).
  - The alias delete route exists (`admin-config.js:223`).
  - `jobs` UNIQUE and NOT NULL constraints justify the new table (`001-schema.sql:146-154`).

## Assumptions I could not verify

- Whether Zoho updates an SO's `last_modified_time` when packages, shipments, invoices or pick lists are created (B2).
- Whether `/bundles` supports sorting by `last_modified_time`, which OAuth scope it needs, and whether it returns `composite_item_id` (spec V2).
- Whether the SO list endpoint returns the `cf_*` fields and sorts by modification time (spec V1).
- Whether every bundle's `reference_number` is the SO number (some may carry only a job number).
- Whether kit-type combo items exist in SPS (N1).
- The real daily API quota for the SPS org, and who else draws from it.
- The deploy target and PM2 service name for the dashboard.

## Simpler alternative considered

- Drop `shippedFresh` from `preview_fresh`. Use only: header delta fresh, bundles delta fresh, and no backlog for flag-eligible SOs.
- Keep the nightly full list only for deletions.
- Limit detail fetching to open SOs from the last 90 days plus anything created on or after the cutoff.

That removes the backfill problem (B1), the manual-import coupling (N8), and most of the budget risk. It costs a little history for jobs that are years old.

**Files referenced:**
- /root/Project Management/wiki/specs/2026-09-28-pd-manager-preview.md
- /root/dev/production-dashboard/cli/import/upsert.js
- /root/dev/production-dashboard/server/services/freshness.js
- /root/dev/production-dashboard/server/db/migrations/002-seed.sql
- /root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json
- /root/Project Management/reports/2026-09-27-sps-sh-inventory-analysis/work/scout-sps.md

## Plan-critic round 2

VERDICT: BLOCK

## Verdict
BLOCK

## Blocking findings

- **[B1] While the history loads, the midnight slot uses up the whole day's detail budget. After that no daytime detail calls can run, so managers get no counters and no flags for about a week after go-live.**
  - **Why it fails.** The `reserve` in §5.3 (spec:260) only counts calls for list-type runs: header deltas, bundle deltas and full lists. It sets nothing aside for daytime detail calls. The first slot of each Colombo day is 00:00, which is a night slot with a limit of 250.
    - At 00:00: `available = 400 − 0 − (66 + 38 + 43) − 60 ≈ 193`. The slot spends all of it on P3/P4 history.
    - From then on, each slot raises `used` by 1–2 calls and lowers `reserve` by the same amount. So `available` stays about 0 for every day slot from 06:00 to 20:00.
  - **What follows.**
    - SOs created during the day never get their detail fetched. Their jobs are missing from "My jobs".
    - Those SOs are flag-eligible and sit in the queue for more than 45 min. Then `flag_backlog > 0`, `preview_fresh` goes false, and counters and flags are hidden for most of every working day.
    - This lasts until P3/P4 drain: about 1,400 in-scope SOs at about 190 a day, so 7 or more days (`scout-sps.md:72-74`).
    - P0 priority does not help, because a queue order is useless when `available` is 0.
  - **The test locks the bug in.** AC40 (spec:348) requires "detail calls made equal cap − 60 − list calls made ± 20", which is exactly this behaviour.
  - **Required change.**
    - Add a daytime detail reserve to `reserve`. For example, `DAY_DETAIL_RESERVE` = about 120, less what has already been spent in today's day slots. Only P0–P2 (and new or changed P3 SOs) may use it.
    - Alternatively, P3/P4 history work may spend only `available − DAY_DETAIL_RESERVE`.
    - Rewrite AC40 as follows. On a backfill day, a flag-eligible SO created at 10:05 is fetched in the 10:15 or 10:30 slot, `flag_backlog` stays 0 during the day, and `fresh=true` at 14:00.

- **[B2] `bundle_missing` gives false alarms on the normal, correct workflow.**
  - **The rule.** It has threshold 0, measured from `packed_seen_at` (spec:167). For threshold 0, `threshold_instant = x` (spec:163), and `x` is the capture time of the fetch that saw the package. So condition 4 ("confirmed") is met at once.
  - **The timing gap.** Header deltas and detail fetches run every 15 min. Bundle deltas run only at :00 and :30, and hourly at night (spec:253-254). Bundle data up to 75 min old still counts as fresh (spec:158).
  - **The normal sequence.** Real data shows a bundle recorded, then the package minutes later. For example, the JOBORDER-08602 bundle was created at 16:35:56 (`bundles_and_recent_sos.json:45`) and the SO was last modified at 16:45:49 with everything packed (`:261798,261802`).
  - **What goes wrong.** Suppose a bundle is created at 10:05 and packed at 10:10. The 10:15 detail fetch sees the package, but the bundle is not yet mirrored. The flag shows until 10:30, or up to 60 min at night. This happens on almost every assembly line that is packed soon after bundling.
  - **The spec's own safety claim is wrong.** "A lag in observing a change cannot produce a false flag" (spec:144) does not hold for this rule.
  - **Required change.**
    - Show `bundle_missing` only if the latest ok bundles-delta run started after `packed_seen_at`. A threshold of at least 1 working day would also work.
    - Add an AC: a bundle created before the package, with the next bundles delta not yet run, means `missing=[]`.

## Non-blocking findings

- **[N1] The claim that the watermark closes a gap after a failure (spec:499) is false for a descending sort.**
  - Delta pages come newest first (spec:215). If page 1 is committed and page 2 then fails (429, 5xx or a lost lease), `W = max(modified_at)` has already moved to the newest row. The next delta stops before the rows it missed.
  - Those SOs are only picked up by the 02:00 full list. Meanwhile the data shows as fresh, because a later ok delta satisfies `delta_stale`.
  - New flag-eligible SOs lost this way are not in `flag_backlog` either, because they have no header row.
  - Fix: base W on the last run that finished `ok`, for example `min(max(modified_at), that run's started_at) − 10 min`. Or store a watermark on the run row only when the run succeeds. Add an AC for a 2-page delta that fails on page 2.
- **[N2] Bundle field mapping.**
  - Zoho's bundle list has `quantity_to_bundle`, not `quantity` (`bundles_and_recent_sos.json:15`). Release 0 maps it in `config/zoho-columns.json:134`.
  - The spec should say the sync reuses that mapping and adds `composite_item_id` to it. Otherwise a sync-only `bundles` path would store NULL quantities, and every stage 5 would show ✘.
- **[N3] Thresholds skip Saturdays.**
  - `working_weekdays` is seeded as Mon–Fri (`002-seed.sql:77`), so a Saturday does not count as a working day.
  - If SPS packs, ships or invoices on Saturdays, flags come about a day late. They are never false.
  - Confirm with the user alongside Q5.
- **[N4] AC40 must be replaced as described in B1.** As written, it passes against the broken budget.

**Checked, nothing found:**
- **Idempotency.** The `(org, line_item_id)` key, `upsertGuarded` (`upsert.js:5-23`) and AC8 hold up.
- **Partial failure.** Each SO is written in its own transaction (AC10), and crashed runs are closed (AC15).
- **Access control.** `requireRole` does a some-match (`middleware.js:42-43`). AC22–AC25 are sound, including the identical 404 for "unknown" and "not visible".
- **Read-only Zoho.** AC1/AC2 cover it.
- **Detail header upsert.** The detail response has no header-level `quantity_*` fields (only the line fields at `salesorders_since_2026-09-15.json:142-150`). So `detail_sig` cannot loop against list values.
- **Ex-stock orders.** They do get bundles referencing the SO (JOBORDER-08589 at `bundles_and_recent_sos.json:303`; JOBORDER-08602 at `:39`). No false-alarm flood comes from ex-stock lines.
- **Migration 005.** It passes `lint-migrations.js:68-84`. The alias inserts target existing division codes (`002-seed.sql:43-55`), and a Release 0 build can still start on the upgraded database (AC37).
- **Scope.** Nothing is out of scope.

## Assumptions I could not verify
- That the SO list endpoint sorts by `last_modified_time` and returns every status, including under OAuth (V1).
- The scope for `/bundles` and whether it can sort by `last_modified_time` (V2).
- Whether packages, shipments and invoices move the SO's `last_modified_time` (V4). The signature check mitigates this.
- The real org-wide daily quota for SPS and who else draws on it (Q1b).
- Whether SPS works on Saturdays (N3).

## Simpler alternative considered
- **B1.** Instead of the whole `reserve` calculation, set a fixed history allowance: P3/P4 may use at most 150 calls a day, in night slots only. All other detail work is limited only by `cap − used − remaining list calls − 60`.
- **B2.** Drop `bundle_missing` from the preview and keep only the package, shipment and invoice rules. Stage 5 stays visible in the strip as done or partial.

Files: /root/Project Management/wiki/specs/2026-09-28-pd-manager-preview.md, /root/dev/production-dashboard/cli/import/upsert.js, /root/dev/production-dashboard/config/zoho-columns.json, /root/dev/production-dashboard/server/db/migrations/002-seed.sql, /root/exports/zoho/native/2026-09-19/sps/bundles_and_recent_sos.json

## Plan-critic round 3

VERDICT: BLOCK

## Verdict
BLOCK. Two findings must be fixed before any code is written. Both are small text fixes to the spec and do not need a redesign. Everything else checks out on Release 0 (details at the end).

## Blocking findings

- **[B1] The `flag_backlog` gate can hide every counter and flag for every user, and its definition loops back on itself.**
    - **What the spec says:**
      - `flag_backlog` counts flag-eligible SOs that are in the detail queue. Their age is measured "from `H.captured_at` of the header change that queued them" (spec:165).
      - The queue also holds P0 confirmations and P2 re-confirmations (spec:247-248). No header change queues those.
      - `upsertGuarded` moves `captured_at` only when a field changes (`/root/dev/production-dashboard/cli/import/upsert.js:8,18-21`).
    - **Why it fails:**
      - A P0 or P2 SO has a `captured_at` that is usually days old. So it counts as backlog the moment it is queued, and `preview_fresh` goes false for everyone.
      - P0 confirmations all fall due at 00:00 on their threshold day. P2 re-confirmations fall due 20 h after each flagged SO's last fetch, so they spread across the working day.
      - Each one blanks the whole screen until it is fetched. On a busy day, when `live_available` reaches 0 (spec:552), the screen stays blank for the rest of the day.
      - The definitions are circular:
        - P2 depends on a job that "currently shows a flag";
        - showing a flag needs `preview_fresh`;
        - `preview_fresh` needs `flag_backlog = 0`;
        - `flag_backlog` counts P2.
        - So the result either flip-flops or depends on how it is implemented.
      - Re-confirmation costs 1 call per flagged SO per day. Flags on open SOs build up over time, and the budget has only "≈20" for this (spec:330).
      - No AC catches any of this: AC40 has no flags, and AC34 only covers P1.
    - **Required change:**
      - Count only P1 (header-change) reasons in `flag_backlog`, aged from `captured_at`.
      - Or age P0 from `threshold_instant` and P2 from `detail_fetched_at + 20h`.
      - Define "currently shows a flag" on the stored-data flag condition alone, without the freshness gate.
      - Add ACs for these cases:
        - (a) a P0 confirmation falls due at 00:00, and the 06:00–20:00 counters are still numbers;
        - (b) 30 flagged SOs fall due for re-confirmation in one day slot, and `fresh` stays true;
        - (c) re-confirmation calls per day are counted in the budget.

- **[B2] `bundle_missing` rests on an unverified assumption and could flood on day one.**
    - **The rule:** it fires straight away (threshold 0) on every packed assembly line that has no bundle whose `so_key` is that SO and whose `composite_item_id` is that item (spec:173).
    - **What the spec checks:**
      - V5 checks the other direction: what share of *bundles* map to an SO (spec:609).
      - Nothing measures what share of *packed assembly lines* have a bundle for their own SO.
    - **Why it matters:**
      - Ex-stock orders of assembly items can be packed from stock bundled earlier or under another reference. The `Ex Stock` order type exists (`002-seed.sql:58`).
      - One bundle refers to an old SO: "JOBORDER-07835 - F" is dated 18 Sep 2026 (`/root/exports/zoho/native/2026-09-19/sps/bundles_and_recent_sos.json:17`).
      - Round 2's "no flood from ex-stock" rests on 2 examples.
      - The scope critic's rule is that missing-step flags must not flood.
    - **Required change:**
      - Add an offline check, V7. Take 2026 packages of composite items (`/root/exports/zoho/native/2026-09-16/Package_ALL.xlsx`) and measure what share have a bundle matching their own SO and item, split by `cf_order_type`.
      - Measure the bundle-created vs package-created lag at the same time.
      - If the match rate is below about 95% for any order type, do one of two things:
        - limit `bundle_missing` to the order types that pass;
        - or drop the rule from the preview and keep stage 5 in the strip only (round 2's simpler alternative).

## Non-blocking findings

- **[N1]** **AC28 fails as designed.** `/api/jobs` returns `history:{loaded, total}` (spec:350), but AC28 forbids any response key matching `/total/` (spec:431). Rename the key, e.g. `history.in_scope`.
- **[N2]** **Some SOs can be wrongly marked `missing_in_zoho`.**
    - Offset paging on a list sorted newest-first can skip a row that is modified while the full list is being read (it jumps to page 1, which was already read).
    - The reconcile then marks that SO `missing_in_zoho` (spec:318).
    - Only a full list clears `sync_state`, so the SO's jobs vanish for about 24 h.
    - Fix: either only mark headers whose `modified_at` is older than the full list's `started_at`, or have delta and detail upserts set `sync_state=NULL`. Bundles have the same problem.
- **[N3]** **The history/live lane split breaks depending on how NULL is compared.**
    - A history SO must have `detail_fetched_at IS NULL` as its *only* reason (spec:251).
    - For a never-loaded SO, `detail_sig` is NULL. In JS, `null !== sig` is true, which adds a second reason. Every SO then goes to the live lane, and round-2 B1 comes back.
    - AC40 would catch it, but the spec should say it outright: reasons 2 and 3 apply only when `detail_fetched_at IS NOT NULL`.
- **[N4]** **Crashes can hide spent calls from the daily cap.**
    - The spec does not say when `api_calls` is written. If it is written only when a run finishes, a crash loses up to 250 calls from the cap count.
    - Fix: persist the count per request, in the same statement as the lease renewal.
- **[N5]** **"Present" fields in the detail header upsert need a clearer definition.**
    - In the detail response, `cf_*` fields are nested in `custom_field_hash` (`salesorders_since_2026-09-15.json:535,541`). Top-level keys are raw names (`created_time`, `last_modified_time`, `shipment_date`).
    - State that the detail header goes through the `so_headers` column map (`config/zoho-columns.json:94-124`), and that "present" is judged on the source key before mapping.
- **[N6]** **Sync runs will be picked up by `runSweep`.** It processes every finished run with `processed_at IS NULL` (`server/services/sweep.js:56-80`). That means about 150 sync runs a day. It is harmless, since there are no job links, but the spec should say so. Sync runs must write valid JSON in `changed_so_numbers`.

**Checked, nothing found:**
- Migration 005 passes `server/db/lint-migrations.js:68-84`; 005 is the next free number.
- The alias targets exist, and `Rewinding Unit (RWU)` is already seeded, so AC19 holds (`002-seed.sql:43-55`).
- The columns the spec relies on exist: `order_date`, `created_at`, `captured_at`, `expected_shipment_date` (`001-schema.sql:4-14`), and `settings(key,value)` for the lease (`:129`).
- AC37's claim that Release 0 still writes safely to a v5 database holds, because updates only list their own columns (`upsert.js:19-21,131-132`).
- Idempotency, per-SO transactions, the watermark after a failed run, the lease, read-only Zoho (AC1/AC2), access scoping (AC22–AC25) and scope are all sound.

## Assumptions I could not verify
- The SPS org-wide daily API quota and who else draws on it (Q1b). At the assumed 1,000/day, 400 for this service plus the planned INV services at 500 each already exceeds it.
- That `/bundles` sorts by `last_modified_time` under OAuth, and which scope it needs (V2).
- Whether packages, shipments and invoices move `last_modified_time` (V4). The signature check mitigates this.
- Q2 (line tag vs header division) and Q3 ("OPD - PackPro Unit") are still open.

## Simpler alternative considered
Drop `bundle_missing` and P2 re-confirmation from the preview. Keep the package, shipment and invoice flags, confirmed once after their threshold, and keep stage 5 in the strip only. That removes B2, most of B1, and the unbudgeted daily re-confirmation cost, for a small loss: an assembly job that was packed without a bundle would not get a flag.

Files: /root/Project Management/wiki/specs/2026-09-28-pd-manager-preview.md, /root/dev/production-dashboard/cli/import/upsert.js, /root/dev/production-dashboard/server/services/sweep.js, /root/dev/production-dashboard/server/db/migrations/001-schema.sql, /root/dev/production-dashboard/server/db/migrations/002-seed.sql, /root/dev/production-dashboard/config/zoho-columns.json, /root/exports/zoho/native/2026-09-19/sps/bundles_and_recent_sos.json, /root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json, /root/Project Management/reports/2026-09-27-sps-sh-inventory-analysis/work/scout-sps.md

## Plan-critic round 4

VERDICT: BLOCK

## Verdict
BLOCK. Round 3's B1 and B2 are fixed, and the B2 fix did not create a new contradiction. Two new blocking findings remain. Both come from checking the spec against real Zoho API data and the Release 0 code.

**Round-3 status**
- **Round-3 B1: fixed.** `flag_backlog` now counts only P1 reasons, aged from `captured_at` (spec:172). "Stored flag" and "shown flag" are separate ideas, so the circular definition is gone (spec:159-165). P0 and P2 are measured but no longer gate freshness. Re-confirmations are budgeted: `RECONFIRM_DAILY_MAX`, the `so_detail_reconfirm` module, and 130 reserved calls for daytime detail. AC56, AC57 and AC58 cover the three cases asked for.
- **Round-3 B2: fixed, consistently.** `bundle_missing` is gone from §3, §4, the JobDTO (spec:377), the non-goals and AC59. Stage 5 is now `detected` / `not_detected` / `n_a`, and `qty_produced = max(qty_bundled, qty_packed)` agrees with AC29, AC30 and the AC54 variant. The codemap has no conflicting references. The spec matches `DECISIONS.md:20-23` (including "Offset" meaning OPD for Ishan, R7/AC22).

## Blocking findings
1. **[B1] One SO whose detail call keeps failing hides counters and flags for every user, for hours or for good.**
   - **What the spec says:**
     - A failed detail call is skipped, the SO "stays queued" and is retried every cycle (spec:590, AC11 spec:418).
     - `flag_backlog` counts any flag-eligible SO that has a P1 reason and a `captured_at` more than `HEADER_MAX_AGE` old (spec:172). There is no exception for SOs whose fetch is failing.
   - **Case 1: an SO deleted in Zoho after a delta saw a change or its creation, but before its detail fetch** (for example when `live_available` is 0, or during a 429 or cap stop). The detail call returns 404 on every retry. The SO is only marked `missing_in_zoho` at the 02:00 full list (§5.4). Until then `preview_fresh=false` and every manager sees "—".
   - **Case 2: an SO whose detail always fails the shape check or always returns 5xx.** Nothing ever clears it, so the screen stays blank until someone steps in. The spec gives no operator action for this.
   - **Cost:** each such SO also uses one P1 call per slot, about 66 a day, out of the 130-call day reserve.
   - This is the same kind of fault as round-3 B1 (one record blanks the whole preview), just through P1.
   - **Required change:**
     - (a) Treat a detail 404 as authoritative: mark that header `missing_in_zoho` straight away.
     - (b) Record per-SO detail failures (for example `detail_error_at` / `detail_fail_count` in 005, which is not yet deployed so can still change). After N consecutive failures:
       - take the SO out of `flag_backlog`;
       - suppress that SO's own flags instead;
       - back off its retries;
       - show it on the status screen as `detail_failing`.
     - (c) Add an AC: a flag-eligible SO whose detail returns 404, or bad shape, all day leaves `fresh=true` from 06:00 to 20:00.

2. **[B2] "Open" uses status values from the xlsx export that the API never returns, so partly shipped open jobs never load.**
   - **What the spec says:** in-scope means `status IN ('confirmed','partially_invoiced')` (spec:251).
   - **Why that does not match the API:**
     - `partially_invoiced` is a value from the xlsx `Status` column (`scout-sps.md:28-29`).
     - The API's `status` field, which the sync writes through the `so_headers` map (`config/zoho-columns.json:103`), takes the values `confirmed`, `partially_shipped`, `shipped` and `fulfilled`. Evidence: `bundles_and_recent_sos.json:264214,267685,261808`, and in the detail, `salesorders_since_2026-09-15.json:8639,9397`. "Partially invoiced" lives in a different field, `invoiced_status` (`:54`).
   - **Effect after the first full list:**
     - Every SO created before the cutoff with API status `partially_shipped` or `shipped` (shipped but not fully invoiced) is out of scope and is never fetched, even when it changes later.
     - Those are the partial deliveries, which are real open work (288 partial lines in 2026, `scout-sps.md`). They never appear in managers' lists or counters.
     - `history.in_scope`, the backfill ETA and the "about 1,400" estimate all rest on the wrong vocabulary.
   - **Required change:**
     - Define "open" from the API: for example `status NOT IN ('fulfilled','void','closed','draft')`, or header quantities (`quantity_shipped < quantity OR quantity_invoiced < quantity`), in line with the line-level `state` (spec:128).
     - Add the status list to V1.
     - Add an AC: a pre-cutoff SO with API `status='partially_shipped'` is in scope and loads in the history lane.

## Non-blocking findings
1. **The `required` check of the column map would reject every detail response.** The `so_headers` map lists `quantity_shipped` as required (`zoho-columns.json:96`, enforced at `cli/import/run.js:87-88`). The detail's `salesorder` object has no header `quantity_shipped`, only `total_quantity` (`salesorders_since_2026-09-15.json:70`). The spec should say the `required` list does not apply to the detail object. Otherwise every detail fails the AC11 path, which combined with B1 blanks the preview for good.
2. **Clearing `sync_state` needs `sync_state` in the handler's field list.** `upsertGuarded` skips the write when every listed field is unchanged (`upsert.js:18`), so "written with `sync_state=NULL`" (spec:230) only happens if the column is listed. AC60 would catch this, but the spec text should say it.
3. **Bundle deletions are reconciled only weekly, which can raise false `package_missing` flags.**
   - A bundle deleted or redone in Zoho keeps counting until the Sunday reconcile (§5.4). That inflates `qty_bundled` and `qty_produced` and can raise a false `package_missing` flag for up to about 7 days.
   - The safety claim at spec:155 covers only the lag in seeing new bundles, not deletions.
   - Either say so in the failure-mode table and have V7 measure how often bundles are deleted, or run the bundles full list daily. That needs about 60 calls; the weekday total becomes 397 against a cap of 400, which is tight.
4. **Night-time live detail work is not limited by the day reserve.**
   - The claim "at 06:00 `live_available ≈ 130`" (spec:316) assumes no live detail calls at night.
   - P3 SOs re-queued by the 02:00 full list's signature check (many, if V4 fails) are fetched from the live lane in the 02:00 slot. That lane only subtracts `list_reserve`, so those calls come out of the next day's budget.
   - Limit P3 in night slots by `day_reserve_left`, as history already is.
5. **Signature loop risk.** `detail_sig` includes `status`, `shipped_status` and `invoiced_status`, and the detail upsert writes them. If the list and detail endpoints ever disagree on one of these values, every such SO is re-fetched every night. The sample agrees (confirmed, fulfilled, partially_shipped), but V3 should record that they match.

## Assumptions I could not verify
- The real org-wide daily API quota for SPS (Q1b).
- The sort order and OAuth scope of `/bundles` (V2).
- Whether packages, shipments and invoices move `last_modified_time` (V4).
- The full API `status` vocabulary, including `draft`, `void` and `onhold`.
- How often SPS deletes SOs or bundles.

## Simpler alternative considered
Round 3's suggestion still applies: drop P2 re-confirmation. Any Zoho change already re-queues a flagged SO as P1 (spec:580), so P2 only refreshes the "checked HH:MM" label. Dropping it removes `RECONFIRM_DAILY_MAX`, the `so_detail_reconfirm` module, AC57, AC58 and 30 calls a day from the budget.

## Files
- /root/Project Management/wiki/specs/2026-09-28-pd-manager-preview.md
- /root/dev/production-dashboard/cli/import/upsert.js
- /root/dev/production-dashboard/cli/import/run.js
- /root/dev/production-dashboard/config/zoho-columns.json
- /root/exports/zoho/native/2026-09-19/sps/bundles_and_recent_sos.json
- /root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json
- /root/Project Management/reports/2026-09-27-sps-sh-inventory-analysis/work/scout-sps.md

## Plan-critic round 5

VERDICT: BLOCK

## Verdict
BLOCK

**Round-4 status**
- **Round-4 B1: partly resolved.** The 404 path (a) is fixed: `not_found` marks the SO `missing_in_zoho` at once (AC65). Level-1 freshness now reads only `zoho_import_runs`, so one SO can no longer blank the screen through the queue (AC34, AC56, AC64, AC67). But the fix for (b) creates a new problem, described in B1 below.
- **Round-4 B2: resolved.** "Open" is now defined from API fields (R11, §2), and AC68 matches the real row at `bundles_and_recent_sos.json:264206-264214` (`status` `partially_shipped`, `invoiced_status` `partially_invoiced`).
- **Non-blocking items 1–5 from round 4:** all applied.
- **Consistency across sections, ACs and DTOs:** checked. `flag_status` is in the JobDTO and AC28. The `checking` object, the problems route, the AC64 retry timing (06:00, 06:15, 06:30, then 21:00 on day 2 and 21:00 on day 3) and the AC56 slot timing all agree with §5.2–§5.3.
- **Budget arithmetic:** checked. 66+38+43+80+20+30+3 = 280 on a weekday and 340 on Sunday. History at 00:00 on a weekday is 400−147−130−60 = 63 (3 on Sunday; 163 and 103 at cap 500). The formula is right; B-level issues are in the estimates, see N3.

## Blocking findings

**[B1] A short Zoho outage, or one bad deploy, exiles many SOs as "sync problems" for 1.5 days to weeks, and there is no fast way to undo it.**
- **Why the outage guard does not fire.** It needs 3 consecutive 5xx or timeout answers *within one cycle* (spec:318). Day-slot live queues are about 1–2 SOs (about 13 new SOs a day, spec:393), so the guard almost never triggers.
- **What happens instead.** A 45-minute detail-only blip counts one failure per slot against each queued SO. AC64 (spec:537-541) actually codifies this: three failed slots (06:00, 06:15, 06:30) make an SO a sync problem.
- **How long the damage lasts.**
  - Recovery is one retry per SO, at least 24 h after the last failure, in night slots only, capped at `PROBLEM_RETRY_DAILY_MAX = 10` a day (spec:320).
  - A flag-eligible SO that fails at 09:00 therefore loses its flags until about 21:00 the next day.
  - A build that returns `bad_shape` or `http_4xx` for every detail (a regression in our shape check or column map, or a Zoho payload change) exiles about 20 SOs every 45 min.
- **Why rollback does not help.** A code rollback leaves `detail_fail_count` in the DB. The spec forbids any admin reset (Non-goals, spec:571). So getting out means either a live DB write or weeks at 10 SOs a day. That fails the "undo in five minutes at 2am" test.
- **Evidence:** spec:314-321, 490, 537-541, 571, 664.
- **Required change:**
  - Stop the exile from firing on systemic failures. Either:
    - count an SO failure only when the same cycle also had at least one `ok` detail response, and extend the guard to "the last K detail requests across cycles" of *any* failure class; or
    - replace the hard exile with per-SO backoff (for example 15 min × 2^n, capped at 6 h). The SO would still show `sync_problem` after 3 failures, but it would not be limited to 10 retries a day at night only.
  - Also give a 2am lever with no DB write, for example "a restart with `ZOHO_RESET_SYNC_PROBLEMS=true` zeroes the counts", which is idempotent.
  - Add an AC: detail answers 503 for 45 min with one SO queued per slot, then recovers → the SO's flags are back within one cycle of recovery.

**[B2] The spec says missed changes cannot cause a false flag. If V4 fails, they can.**
- **How it happens.** V4 checks whether a package, shipment or invoice moves the SO's `last_modified_time`. If it does not, the delta never sees the change, because paging stops on `last_modified_time` (spec:263).
- **Why the new level 2 does not catch it.** The header row is only rewritten by the 02:00 full list. Until then `captured_at` does not move, so `flag_status` stays `current`.
- **The effect.** An invoice created at 10:00 leaves `invoice_missing` shown with "checked HH:MM" until the 02:00 full list or the P2 re-confirmation (20 h). That is about 16 h of a "missing" document that exists, which is exactly what the lead's per-job rule was meant to prevent.
- **The spec contradicts itself.** §3 (spec:167) and the failure-mode row (spec:670) claim a missed change "cannot produce a false flag", and V4 (spec:718) says "no change is needed" if `last_modified_time` does not move.
- **Required change:** make "`last_modified_time` does not move on package/shipment/invoice" a return-to-spec-writer outcome of V4. Or, if the stale window is accepted, state it (up to about 20 h) in §3 and in the failure-mode table and remove the "never false" claims.

## Non-blocking findings

- **[N1] One malformed list row can still blank the screen for every user.**
  - A list page with "a row without an id, a row missing a required key" fails the whole run (spec:659).
  - W never moves, so the bad row stays inside every later delta window and inside the full list. The result is permanent `delta_stale` and then `full_list_old`.
  - The guarantee "No single SO can hide the screen" (spec:367) is therefore overstated.
  - All 200 sampled list rows carry the required keys, and the one blank bundle `reference_number` is present as `""`. So the risk is low, but the fix is cheap: skip the row and warn instead of failing the page (keep the page-level failure only for a missing array or `page_context`).
  - Note that Release 0 checks required keys only on the first row's key names (`cli/import/run.js:87-88`), not per row. Say which behaviour the sync uses.
- **[N2] "History loading" never finishes.** A never-loaded SO that becomes a sync problem stays in Y (`history.in_scope`) and never in X. The blue line and `counters_complete=false` then stay forever, which contradicts Observability step 5 (spec:702). Exclude sync-problem SOs from Y, or report them separately.
- **[N3] Level 2 marks jobs "checking" when they can never have flags, and that refresh work is not budgeted.**
  - `flag_status='checking'` applies to every loaded SO, including pre-cutoff jobs.
  - Pre-cutoff open SOs that ship or invoice during the day re-queue as P3. §5.5 budgets only "13 new SOs × 6 changes" (spec:393), not changes to the roughly 1,400+ old open SOs.
  - Result: the "being checked: N" note can be large and permanent, and managers see "checking with Zoho…" on jobs that have no chips to hide.
  - Fix: limit `checking` (and the note) to flag-eligible SOs, and add a budget row for P3 refreshes of old SOs. AC38(a) will catch a wrong estimate, but only after deploy.
- **[N4] Wrong fact about header quantities (it does not change the outcome).**
  - The spec says an SO with cancelled units "stays open at header level" (spec:120).
  - Real data shows the reverse. For JOBORDER-08602 the list row has `quantity_shipped: 1496`, `quantity_invoiced: 1496`, `quantity_packed: 15496` (`bundles_and_recent_sos.json:261800-261803`). The detail shows line shipped 0, packed 14000, **cancelled 1496** (`salesorders_since_2026-09-15.json:143-149`). So header quantities count cancelled units as packed, shipped and invoiced.
  - That makes the quantity clauses match the line rule's `qty_effective` exactly. The `status NOT IN ('fulfilled','closed')` clause then only adds SOs whose quantities are already complete (for example a status of `shipped` or `onhold` with everything done). These cost history fetches and produce only closed or cancelled jobs.
  - Correct the note, add "header qty includes cancelled" to the V3 checks, and consider dropping the status clause.
- **[N5] `run.js` date cutoff: say whether the sync applies it.** `cli/import/run.js:8,99` skips records dated before 2024-01-01 Colombo. The spec does not say whether the sync inherits this skip. The choice affects the 95% full-list count and whether pre-2024 open SOs are ever in scope.
- **[N6] The Sunday bundles full list runs outside the slot schedule.** It is listed at 02:30 (spec:343), but night slots run on the hour only. Say which slot runs it.

## Assumptions I could not verify
- Whether Zoho moves the SO's `last_modified_time` on package, shipment or invoice (V4). B2 depends on this.
- The body code of Zoho's detail 404 (V3a), the full `status` vocabulary (V1), and the org-wide daily quota (Q1b).
- How often SPS pre-cutoff open SOs change per day. N3 depends on this.
- Whether list rows ever omit `quantity_shipped` or `reference_number` for draft or stock rows. 200 of 200 sampled rows had them.

## Simpler alternative considered
- **Per-SO failures.** Replace the whole mechanism (the 3-strike count, the 24 h night-only retry, `PROBLEM_RETRY_DAILY_MAX` and the `so_detail_retry` module) with one backoff column, `detail_next_try_at`. The SO shows `sync_problem` when `detail_fail_count >= 3`, but it keeps being retried on the backoff schedule. That is less code, heals by itself after a transient or systemic failure, and fixes B1.
- **P2 re-confirmation.** Dropping P2 is still worth doing: any Zoho change already re-queues a flagged SO (refresh reason (b)), so P2 only refreshes the "checked HH:MM" label. Dropping it removes `RECONFIRM_DAILY_MAX`, AC57, AC58 and 30 calls a day.

## Files
- /root/Project Management/wiki/specs/2026-09-28-pd-manager-preview.md
- /root/dev/production-dashboard/cli/import/upsert.js
- /root/dev/production-dashboard/cli/import/run.js
- /root/dev/production-dashboard/config/zoho-columns.json
- /root/dev/production-dashboard/server/db/migrations/001-schema.sql
- /root/exports/zoho/native/2026-09-19/sps/bundles_and_recent_sos.json
- /root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json

## Plan-critic round 6 — PD manager preview (29 Sep 2026)

Reviewed: `2026-09-28-pd-manager-preview.md` body (Rev 5), against Release 0 HEAD `b0cd339` and the
19 Sep SPS Zoho samples. All line numbers are that spec file unless another path is given.

**VERDICT: BLOCK**

**Framing note.** The spec file *already contains* an appended `## Plan-critic round 5` (`:1166-1244`,
VERDICT BLOCK, B1+B2+N1-N6) written by another pass, while the body still says "Rev 5 has not yet had a
plan-critic round" (`:3`) and there is no "Revision 6 changes" table. The body is therefore unrevised
against **two** critic rounds. Round 6 reviewed the body independently; where it reaches the same
conclusion as the appended round 5 it says "confirmed".

## What Rev 5 got right (checked, not findings)

Level 1 (`:181-187`) reads only `zoho_import_runs` — no queue, no per-SO state, no `captured_at` — and
AC34's last sentence (`:521`) tests exactly that. Level 2 (`:189-202`) is per-SO and its `checking` rule
is consistent with refresh reason (b) and with `upsertGuarded`'s skip-if-unchanged behaviour
(`cli/import/upsert.js:18-21`), so an unchanged header does not spuriously flip a job to "checking".
`flag_backlog` is gone from the whole body; the only occurrences left are in the Rev 3/4/5 change tables
and the archived critic text. `flag_status` is consistent across §2 (`:141`), §4 (`:189-202`), §6 JobDTO
(`:427`), AC28 (`:509`) and the UI (`:437`). The §5.5 budget arithmetic is internally correct:
66+38+43+80+20+30+3 = 280 weekday / 340 Sunday (`:390-398`), and 400 − 147 − 130 − 60 = 63 at 00:00
(`:365`) reproduces. No N-series finding from rounds 1-4 was silently dropped. Migration 005 is additive,
passes `server/db/lint-migrations.js:68-84`, is `user_version`-guarded and idempotent on the tenth
restart; its four `INSERT OR IGNORE` alias rows collide with nothing in `002-seed.sql:43-55`. AC37's
rollback assertions are sound.

## Blocking findings

**[B1] (confirmed, round-5 B1) The sync-problem exile is irreversible at 2am.** `detail_fail_count`
survives a code rollback; the only exits are a 24 h night-only retry capped at 10/day (`:320`) or a
`not_found`; Non-goals forbid any admin reset (`:571`). A 45-minute detail-only blip counts one failure
per slot against each queued SO, and the in-cycle outage guard (`:318`) almost never fires because a day
slot has 1-2 queued SOs. **Required:** make the failure counter self-healing (per-SO backoff, or count a
failure only in a cycle that also saw an `ok` detail response, and extend the guard across cycles), plus
one env-driven, idempotent reset lever that needs no DB write.

**[B2] (confirmed, round-5 B2) §3 and the failure table claim a missed change "cannot produce a false
flag"; if V4 fails, they can.** `:167`, `:670`, against V4's "no change is needed either" (`:718`).
**Required:** either make "`last_modified_time` does not move" a return-to-spec-writer outcome of V4, or
state the ~20 h false-`missing` window in §3 and in the failure table and delete the "never false" wording.

**[B3] The 18 new line columns have no field mapping, no type conversion and no shape rules — and §5.2
asserts that no such mapping exists.** `:257` says "There is no second mapping in the sync code… The only
mapping change is one new entry in the `bundles` section", but `:326` writes 18 line fields into a new
table with no map. Three certain consequences:
1. `is_combo_product INTEGER NOT NULL DEFAULT 0` (`:588`) is written by `upsertGuarded`, which lists the
   column explicitly and binds `rec[c] ?? null` on INSERT and UPDATE (`upsert.js:12,21`), so the
   `DEFAULT 0` can never apply: any line whose response omits the key aborts the whole SO transaction
   with a NOT NULL violation.
2. The real payload carries a JSON boolean (`/root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json:90`
   `"is_combo_product": true`). better-sqlite3 refuses to bind a JavaScript boolean, so this throws
   unless the value goes through `mapRow`'s `bool` type (`cli/import/columns.js:26`) — which only exists
   if a column-map section is defined.
3. `division_tag` (`:591`) is not a key lookup: it must be extracted from `line_items[].tags[]` where
   `tag_name='Division'` (`salesorders_since_2026-09-15.json:127-135`). Nothing says how, or what to do
   with a line carrying two Division tags.
And the §5.2 outcome table (`:311-316`) has no class for "the handler threw": a line that reliably throws
leaves `detail_fetched_at` NULL, so refresh reason (a) persists, the SO is re-requested every cycle
forever, `detail_fail_count` never rises, and its jobs sit at "checking" permanently — the very class
Rev 5 set out to close. **Required:** add a `so_line_items` section to `config/zoho-columns.json` with
explicit types (`bool` for `is_combo_product`, `number` for quantities, `raw` for `line_item_id`/`item_id`),
specify the Division-tag extraction, make `is_combo_product` nullable (or guarantee `?? 0`), and add a
fifth outcome class `handler_error` counted exactly like `bad_shape`.

**[B4] Night P1 is unbounded and can eat the entire day's live detail reserve; §5.3 claims otherwise.**
`:365` says "Night P0–P2 are the only detail work not limited by `day_reserve_left`, and they are bounded
by the flags that fall due (P0) and `RECONFIRM_DAILY_MAX` (P2)" — P1 is in neither bound, and `:358`
bounds the night live lane only by `min(live_available, 250 − list calls)`, which at 00:00 is
400 − 0 − 147 − 60 = 193. The trigger is the design's own nightly event: the 02:00 full list rewrites the
header row of every SO whose fields changed, which moves `captured_at` (`upsert.js:18-21`) and is refresh
reason (b) (`:284`); every flag-eligible one lands in **P1**, not P3. Rev 5's answer to round-4
non-blocking 4 capped night **P3** only (`:358`, AC71 `:465`). Effect: one 02:00 slot can spend ~190 calls,
leaving `live_available ≈ 0` at 06:00 for the whole working day. **Required:** bound the night live lane
by `day_reserve_left` as well (or give night P1 its own per-cycle max), fix the §5.3 guarantee text, and
add an AC71-shaped case for P1.

**[B5] The 02:00 header full list is a single point of failure for the whole screen, with no retry, no
first-cycle trigger and no operator lever.** Level 1 requires an `ok` `full_list=1` `so_headers` run within
50 h (`:182-183`); that run happens once a day at 02:00 (`:342`), and any of `rate_limited` (`:647`),
`auth` (`:653`), `upstream` (`:655`), `daily_cap_reached` (`:648`) or `suspect_short_list` (`:660`) kills
it for that day with nothing retrying. Two consecutive misses → `full_list_old` → every counter `null`,
every flag hidden, for every user (`:187`, `:220`, `:232`), with no admin action permitted (`:571`). Two
further inconsistencies in the same place: the **bundles** full list has a "first cycle if none exists"
trigger (`:275`, AC45) but the header full list does not, so a go-live deploy at 10:00 shows
`no_full_header` until 02:00 next morning — even though the first header delta already pages the entire
list (`:264`) but records `full_list=0` (`:272`), so those ~43 calls earn no credit and are spent twice;
and that 43-page first delta breaks day-one `list_reserve`, which budgets 1 call per header-delta slot
(`:349`), a case AC40 never exercises because it specifies "1 page per delta" (`:456`). **Required:** give
the header full list the same first-cycle trigger; credit `full_list=1` when the first delta completes all
pages and passes the 95% rule; retry a non-`ok` full list in the next night slot of the same day; add an
AC for a failed 02:00 full list.

**[B6] (round-5 N1, elevated to blocking) One malformed list row permanently blanks the screen for
everyone, recoverable only by a deploy.** A row without an id or missing a `required` key fails the whole
page and the whole run (`:659`); `W` moves only on an `ok` run (`:262`, `:265`); level 1 needs an `ok`
delta within 45 min (`:184`). The bad row sits inside every later delta window forever: permanent
`delta_stale`, then `full_list_old`, then the banner and `null` counters for every user, with no lever
(`:571`). This contradicts `:367` ("No single SO can hide the screen or another SO's flags") and the lead
decision at `:9`. The spec also defers the required-key check to "as today (`run.js:88`)" (`:257`) without
noticing that `cli/import/run.js:87-88` checks only the **first** row's key names. **Required:** quarantine
the offending row (skip it, record it in the run's `warnings` and a counted metric) and still end the run
**`ok`** so `W` moves — a `warning` status is not enough, because `:262` and `:184` both demand `ok`. Keep
page-level failure only for a missing array or missing `page_context`. Add an AC: a 200-row page with one
malformed row → run `ok`, 199 rows written, `W` moves, `fresh=true`.

## Non-blocking findings

- **[N1] The list path still nulls header fields; only the detail path was fixed.** `:325` makes the
  detail write "only fields whose source key is present"; the delta/full-list path keeps writing
  `rec[c] ?? null` for all of `HEADER_FIELDS_PULL` (`upsert.js:25-29`, `:19-21`). The evidence that the
  list carries flattened `cf_*` keys comes from the **browser internal** endpoint
  (`bundles_and_recent_sos.json:261819-261836`, `tools/zoho-pull-snippet.js:28`), not from
  `zohoapis.com/inventory/v1`. If the OAuth list omits them, every delta silently blanks `cf_job_no`,
  `cf_manufacturing_division` and `cf_order_received_from` estate-wide. Apply the "present source keys
  only" rule to list rows too.
- **[N2] AC8 contradicts the existing meaning of `rows_upserted`.** AC8 (`:468`) asserts
  `rows_upserted = 0` on a repeat run, but `cli/import/run.js:80` sets `upserted += rows.length` — rows
  processed, not changed. Restate AC8 as "no row's `captured_at` changes", or state the differing meaning.
- **[N3] `zoho_import_runs.captured_at` is NOT NULL (`001-schema.sql:79`) and the spec never says what a
  sync run writes there.** Also: a sync `full_list=1` run does move `shippedFresh` and `bundlesDataAge`
  for SPS (`server/services/freshness.js:3-4,22-25`) though the preview no longer reads them — say this is
  intended and harmless.
- **[N4] `composite_item_id` is added to the `bundles` handler unconditionally** (`:257`), unlike
  `sync_state`, which is scoped to `ctx.source==='sync'` (`:259`). A pull bundles import whose rows lack
  the key would null a stored value. Scope it the same way; add an AC that an **SH** bundles import is
  never refused by the `sync_active` guard (`:378` is SPS-only; AC46 does not test SH).
- **[N5] Draft SOs become visible jobs and nobody decided that.** R11 keeps post-cutoff drafts in scope
  (`:25`) and §2's `state` rule (`:139`) makes a draft line `open`. State the intent; exclude or label.
- **[N6] Slot alignment is unspecified.** `:336` says "a `setTimeout` chain"; the whole budget and AC40
  assume alignment to the wall-clock grid (`:340-341`, `:390-391`). Say that the chain aligns to
  :00/:15/:30/:45 and what the first cycle does after a restart at 06:07. Round-5 N6 stands: the 02:30
  Sunday bundles list (`:343`) is not on the hourly night grid.
- **[N7] Missing ACs:** `PROBLEM_RETRY_DAILY_MAX` has none (11 problem SOs → exactly 10 retry calls, none
  in a day slot) while `RECONFIRM_DAILY_MAX` got AC58; `zoho_sync_throttled` (`:647`) has none;
  `zoho_detail_outage` after 3 consecutive `detail_outage` cycles (`:665`) has none (AC69 tests one
  cycle); `counters_complete=true` after the history load has none (AC49 only tests `false`);
  `flags_since` (`:418`) is never asserted.
- **[N8] `:325` understates what the detail object lacks, and `:669` understates the ping-pong cost.**
  The real detail has **no** header `quantity`, `quantity_packed`, `quantity_shipped` or
  `quantity_invoiced` at all — only `total_quantity` (`salesorders_since_2026-09-15.json:70`; compare
  `bundles_and_recent_sos.json:261800-261803`). Extend AC70 to all four. It follows that `detail_sig` is
  permanently list-derived for quantities and detail-derived for the three status fields, so a
  disagreement is systematic: one extra detail fetch for *every* in-scope SO every night, not "at most 1
  per such SO". Make V3(b) sample more than 3 SOs.
- **[N9] Round-5 N2–N5 are still unanswered in the body and round 6 confirms all four:** "History
  loading" never finishes while any never-loaded SO is a sync problem (`:233` vs `:702`);
  `flag_status='checking'` applies to pre-cutoff jobs that can never have chips, and P3 refreshes of the
  ~1,400 old open SOs are not in the §5.5 table; the header-quantity claim at `:120` is backwards (real
  rows include cancelled units in `quantity_shipped`/`quantity_invoiced`,
  `bundles_and_recent_sos.json:261800-261803` vs `salesorders_since_2026-09-15.json:143-149`, so cancelled
  units make an SO look *more* closed); and it is still unsaid whether the sync inherits the 2024 record
  cutoff at `cli/import/run.js:8,99`.
- **[N10] Two one-liners.** `division_source` is undefined when `division_code` is NULL (`:126`, `:425`) —
  say `null`. AC7 (`:455`) covers log output only; the status route returns the raw run `error` string
  (`:421`), which per `run.js:116` is `err.message` — assert that no token, secret or response body can
  reach that column.

## Assumptions the critic could not verify

- Whether the OAuth list endpoint returns flattened `cf_*` keys and whether its default filter returns
  every status — both sampled only from the browser internal endpoint (N1). The second decides whether
  the 95% `suspect_short_list` rule (`:273`) fails every night, which is B5's most likely trigger.
- Whether every line of every SPS SO carries `is_combo_product` (22/22 sampled do).
- Zoho's detail-404 body code (V3a), the full `status` vocabulary (V1), whether `last_modified_time` moves
  on package/shipment/invoice (V4), the org-wide daily quota (Q1b) — all already open.
- How many of the ~1,400+ pre-cutoff open SOs change per day, which decides whether B4 and round-5 N3 bite.

## Simpler alternative considered

**Take the daily header full list off the critical path.** Level 1 currently hard-depends on an `ok` full
list within 50 h (`:182-183`), which creates B5, drives the nightly `captured_at`/signature churn behind
B4 and N8, and costs 43 of the 280 daily calls. Instead: derive level 1 from the deltas only; run the
header full list **weekly** (alongside the bundles one) purely for deletion reconcile; and when the
reconcile is overdue, show that on the admin sync screen, never as a screen-wide blank. That deletes one
blocking finding outright, shrinks two others, removes ~43 calls/day (weekday steady 280 → 237, giving
Sunday real headroom instead of landing exactly on the cap), and loses only the nightly refresh of header
quantities for changes that do not move `last_modified_time` — a case the P0 confirmation rule (`:177`,
AC51) already prevents from producing a false flag.

The two alternatives the appended round 5 offers still stand and are compatible: replace the exile
mechanism with a single `detail_next_try_at` backoff column (fixes B1, deletes three columns, a module, a
constant and four ACs), and drop P2 re-confirmation (deletes `RECONFIRM_DAILY_MAX`, AC57, AC58 and 30
calls/day).

**Status of the simplification: NOT adopted — it is a lead decision waiting on Abdul Hadhee.**

(Archived verbatim from `2026-09-28-pd-manager-preview-critic-round-6.md`. Its line numbers refer to Rev 5 of this file as it stood on 29 Sep 2026, before Rev 6 changed the body. Rev 6's answers are in "Revision 6 changes".)

## Plan-critic round 7

Reproduced from the coordinator's message of 29 Sep 2026 (the critic's own text was not saved to disk). Line numbers refer to Rev 6 of this file.

**VERDICT: BLOCK** (B1, B2, B3; N1-N10)

Round 7 independently re-derived and confirmed: the whole budget (weekday and Sunday, cap 400 and 500), both backoff cadences in AC56, AC64 and AC73, the quarantine thresholds, the entire `so_line_items` map against `columns.js` and the real payload, migration 005 against the linter and the migration tests, and AC numbering (AC1-AC95, no collisions). `MOBA_P` needs no change: it is a dead provisional division, and all five `no_manager` divisions have aliases, so AC89 is reachable.

**[B1] The detail-outage guard makes three simultaneously broken SOs immortal and freezes all detail work.** `:412` stops detail work for the cycle after 3 consecutive `upstream_5xx`/`timeout`, and `:411` says no SO's count changes in a cycle that ended `detail_outage`. If three genuinely broken SOs sit adjacent in queue order (`H.modified_at` descending, `:389`), every cycle sends 3 requests, the guard trips, no counts are applied, they never reach `DETAIL_FAIL_LIMIT`, never become sync problems and never leave the queue; everything behind them is skipped for ever, including lane PR and the history lane. Every flag-eligible SO stays `checking`, `counters_complete` stays false, and level 1 still reports `fresh=true` because it reads no queue. `ZOHO_RESET_SYNC_PROBLEMS` does nothing because the counts are 0. Round 6 B1 asked for "extend the guard across cycles" and Rev 6 took only the first half. Required: guarantee progress, for example apply the counts normally after K consecutive cycles ending `detail_outage` (reuse K=3 from `:834`), or require the 3 failures to be on at least 2 distinct SOs and suppress counting only when a control request also failed. Backoff makes this safe. Add an AC: 3 SOs answering 503 for ever plus 200 other queued SOs, the 3 become sync problems, the other 200 are fetched, history keeps loading.

**[B2] A row that quarantines on every run leaves its SO's flags shown on frozen data.** Nothing is written, so `H.captured_at` does not move, there is no refresh reason (`:377`), `flag_status` stays `current` (`:217`), and a stored `shipment_missing` or `invoice_missing` keeps showing with an old `checked_at` while Zoho has moved on. This contradicts §3 (`:190-191`) and `:470`, and is an unbounded version of the roughly 20 h window round 6 B2 refused. Visibility is a per-run `warnings` array capped at 20 plus a daily count; an SO quarantined every run for a week is on no list. Required: when the row's id is known (`missing_required`, `map_error`, `write_error`), record it per SO (a counted failure on the header, or a problems-route entry with reason `row_quarantined`) so its jobs go to `checking` and a human can see which SO is stuck. State plainly that for `not_object` and `no_id` no SO can be identified and that is the accepted residual.

**[B3] The line write nulls a quantity whose source key is absent, and a NULL quantity reads as 0, which raises a false flag.** Handler step 2 (`:423`) upserts each line with the full field list through `upsertGuarded`, which writes `rec[c] ?? null` on UPDATE (`cli/import/upsert.js:19-21`; `mapRow` yields `null` for an absent key, `columns.js:15`). The present-source-keys protection at `:290` covers list rows and the detail header only. With `:325` ("every rule reads a NULL quantity as 0") and the flag rules at `:237-238`, one response omitting `quantity_invoiced` overwrites a stored 500 with NULL, `qty_shipped > qty_invoiced` becomes true, and `invoice_missing` is shown for an invoice that exists, and it persists. Same for `quantity_shipped`. All 22 sampled lines carry all seven quantity keys, so the trigger is a Zoho shape change, but no AC would catch it. Required: apply present-source-keys to the line write, or add the seven quantity keys to step 0's shape check so absence is `bad_shape`. Add an AC: a detail whose line omits `quantity_invoiced` must not change the stored value and must not raise a flag.

**Non-blocking**
- **N1** AC72(b) cannot pass as written (`:599`): its 200-P1-SO fixture makes "remaining P1 SOs are fetched in the day slots" and `calls_today <= cap - 60` mutually exclusive by 7 calls. Shrink to at most 150 or assert "at least N fetched, the rest carry to the next day".
- **N2** §5.3's P3 guarantee is false across slots (`:394`): it holds within a cycle, not across them. Correct the sentence or cap P3 per slot.
- **N3** The quarantine rule inherits a `required` list containing `quantity_shipped` (`config/zoho-columns.json:96`), written for the browser/xlsx pull. If the OAuth list omits it on more than 5% of rows, every run ends `too_many_bad_rows` and the screen blanks permanently. Name the sync's own per-row required keys and make "the OAuth list omits a required key" a V1 return-to-spec-writer outcome.
- **N4** Guard `ZOHO_FORCE_FULL_LIST` against a crash loop: skip the forced attempt if an `ok` `full_list=1` run of that module exists today.
- **N5** The reset lever is unreachable in one documented rollback order: `:415` runs it at scheduler start, `:824` says the scheduler does not start when `ZOHO_SYNC_ENABLED=false`. Say in step 5 that the sync must be enabled.
- **N6** (record only) A line with two distinct Division tags is hidden from both managers; state the conflict with R4 (`:36`) and leave the behaviour.
- **N7** Reword `retry_reserve_left` (`:450`): it stops night history eating the 10 calls; it does not guarantee PR gets them.
- **N8** Mark `shared/missing-rules.js` as a new file (`:163`, `:241`, AC59); it does not exist in Release 0.
- **N9** State that the sync never recomputes `zoho_so_facts` and that the blast radius is nil today because no route reads it.
- **N10** (record only) The Rev 3 archive table's stale `DAY_DETAIL_RESERVE = 100`: add "(later raised to 130)".
- Also asked for: at `:365`, that the nested transaction re-throws so the page loop must catch per row; and in §5.5, that on Sunday the 10 retries and any P3 work displace planned live detail work because the planned total already equals `cap - 60`.
- Observation on the pending lead decision: adopting it would invalidate AC84, AC85 and part of AC94, so it is needed before test-author starts.

Round 8 is to be a targeted re-read of B1, B2, B3 and AC72(b) only.

## Plan-critic round 8

Reconstructed from the coordinator's message of 29 Sep 2026 (the critic's own text was not saved to disk). Line numbers refer to Rev 7.

**VERDICT: APPROVE**, with five sentence-level edits required before the implementer starts.

- **B1 graded PARTIAL.** Three gaps, all from the streak being a cycle-level counter: (1) the derivation predicates are unspecified (nothing on a run row says a cycle had an `ok` detail response, and a detail run with three SO failures still ends `status='ok'`); (2) the precedence between "any `ok` resets" and "ended `detail_outage` increments" is defined twice and decides the behaviour; (3) "heals 15 min after Zoho recovers" is false above about five SOs, because lane PR heals 2 per cycle and 10 per day (AC75), so a day-long outage converts roughly 60-100 SOs that take about six days to heal. The critic offered a simpler alternative (make the outage guard per SO). Round 8 also raised: the guard's consecutive-failure window spans lane boundaries (1 live failure plus 2 PR failures can trip `detail_outage` in a healthy system); the production ordering in which broken SOs sort behind fresher P1 work; and N1, N2, N3, N8 as consequences of the streak.
- **B2.** The quarantine mark can be lost: each row is written in its own SAVEPOINT that rolls back and re-throws, so an `UPDATE ... SET row_quarantine_at` issued inside it is rolled back with the row. AC98 exercises only `map_error`; add `write_error`. The bundle residual is slightly false: a quarantined update to an existing bundle leaves `qty_bundled` overstated indefinitely, since a permanently quarantining row is never marked `missing_in_zoho`. Optional: exclude `missing_in_zoho` rows from `quarantined_sos`.
- **B3.** The shape gate requiring all seven quantity keys is load-bearing on an endpoint never sampled: if the OAuth detail omits one, every SO becomes `bad_shape`, then a sync problem, and no job loads on go-live. V3 promises to check only two of the seven. Record all seven on every inventory line, including one SO with no pick list and one with a service line; make omission a return-to-spec-writer outcome. Define "numeric" as `toNumber` yielding a non-null number (`shared/text.js:13-17`).
- **V1's 1% gate is wrong.** On a 200-row page 1% tolerates 2 rows; these keys are structural, a missing `last_modified_time` breaks the watermark, and 1% trips neither the systemic guard (at least 10 rows and more than 5%) nor anything else. Make it "any row".
- **N5.** The sync writes about 170 run rows a day and `GET /api/admin/imports` returns `SELECT * FROM zoho_import_runs ORDER BY id DESC LIMIT 100` (`server/routes/admin-imports.js:18`), rendered with its `file` column (`web/src/admin/Imports.tsx:32,44`); from day one the screen shows only sync runs. Add `AND source <> 'sync'` and an AC.
- **Consequences noted:** a bundle row lacking `status` or `created_time` is mirrored with NULLs rather than quarantined; a NULL `status` only lowers `qty_bundled`; a NULL `date` bypasses the 2024 cutoff at `cli/import/run.js:99`.
- Confirmed unchanged: budget (AC72(b) 297 <= 340), backoff cadences, `so_line_items` map, migration 005's `row_quarantine_at`, AC numbering AC1-AC98.

## Plan-critic round 9

Reconstructed from the coordinator's message of 29 Sep 2026 (the critic's own text was not saved to disk). Line numbers refer to Rev 8.

**VERDICT: APPROVE**, with three edits required before test-author writes AC97 and five one-liners.

- Both Rev 8 refinements were verified necessary: the loop analysis (an unconditional reset would revert the broken SOs every cycle) was confirmed exactly, and the settings-key marker was judged strictly better than an in-memory flag.
- **R1 (must).** AC97(a) is internally contradictory: it asserts "in cycles 1 to 3 no `detail_fail_count` changes" and "in cycles 3, 4 and 5 the three are counted (1, 2, 3)". Per §5.2 the failure is counted when the incremented `detail_outage_hits` reaches 3, so cycle 3 counts. Suggested wording: "in cycles 1 to 3 exactly 3 requests are sent per cycle, each cycle ends `detail_outage` and `detail_outage_hits` goes 1, 2, 3; `detail_fail_count` is unchanged in cycles 1 and 2 and rises to 1, 2, 3 in cycles 3, 4 and 5."
- **R2 (must).** The daily cap has a hole: the spec does not say what happens to `zoho_detail_outage_pending` when a qualifying cycle is blocked by `zoho_recovery_reset_day`. If it is deleted anyway, that outage never heals automatically and lane PR takes about four days (against six). Fix: the marker is deleted only by a reset that runs; the first qualifying cycle of the next Colombo day performs the reset; correct the "second outage the same day" sentence; add a clause to AC97(c); the UPDATE, the DELETE and the day-key write are one `IMMEDIATE` transaction; both keys use `INSERT ... ON CONFLICT(key) DO UPDATE SET value = excluded.value` with a non-empty value because `settings.value` is `NOT NULL` (`001-schema.sql:129`).
- **R3 (should).** Two AC97 fixture facts cannot hold: "lane PR empty" (the trio's `delay(3)` is 15 min, so PR is due from cycle 6); and case (b)'s "fresher SOs are fetched in every cycle" (200 SOs at 20 per slot are exhausted after about cycle 10).
- **N1.** Trim the raw identity as `mapRow` does before matching the quarantine mark (`columns.js:21`, `config/zoho-columns.json:99`). **N2.** `detail_outage_hits` stops at 3. **N3.** Cycle-end counting is one transaction per SO. **N4.** The conversion rate is 3 SOs per 5 cycles (about 0.6 per cycle, about 40 over an outage day). **N5.** Add `sync_state <> 'missing_in_zoho'` to the reset's WHERE.
- **Loose end.** The counter behind the `zoho_detail_outage` log (about `:853`, AC77) has no stated home since Rev 7's `outage_streak` was deleted; derive it from the last three detail run rows or say so.
- Confirmed unchanged: budget (AC72(b) 297 <= 340), backoff cadences, `so_line_items` map, both 005 columns (`detail_outage_hits` correctly in no field list), AC69, AC numbering AC1-AC99, the four smaller Rev 8 edits. The critic considered dropping `detail_outage_hits` and relying on the reset alone and rejected it.
