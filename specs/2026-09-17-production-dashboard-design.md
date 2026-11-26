# Production Dashboard: design spec

**Date:** 2026-09-17 · **Revision:** 7.3 (clarifications from the Release 0 plan reviews: §4 sweep scope, §6.2 pull takeover and SO line sets). Rev 7 (`564b767`) got **plan-critic: PASS**; its 1 major and 4 minor carry-over items are folded in (Appendix F, last rows). Rev 6 (`aed1986`) got **plan-critic: BLOCK** (2 blocking findings, 2 major, 5 minor), all addressed in Appendix F. Rev 5 (`e78a98e`) got **plan-critic: BLOCK** (1 blocking finding, 4 major, 5 minor), all addressed in Appendix E. Rev 4 (`97cd68e`) got **plan-critic: BLOCK** (1 blocking finding, 4 major, 7 minor), all addressed in Appendix D. Rev 3 (`83410a5`) got **plan-critic: BLOCK** (3 blocking findings, 8 major, 15 minor), all addressed in Appendix C. Rev 2 (`243f2a3`) got **plan-critic: BLOCK** (2 blocking findings, 10 major, 9 minor), all addressed in Appendix B; Rev 3 also adds the **Order portal** and the P1/P2 decisions. Rev 2 note: Rev 1 (`0e1fb00`) got **plan-critic: BLOCK** with 5 blocking findings, 12 major and 15 minor. Every finding is addressed below; see Appendix A.
**Status:** design approved by the user on 2026-09-17, including the dependencies, test tools, domain, P1 = a, P2 = a and the order portal. **plan-critic: PASS** (Rev 7). Next: implementation plan.
**Service:** `production-dashboard` · **Dev:** `/root/dev/production-dashboard` · **Live:** `/root/production-dashboard` · **Port:** 4300 · **URL:** `https://production.standard-holdings.lk`

**Sources (authoritative):**
- `/root/Production Dashboard/CLAUDE.md` (**B§**), the brief
- `/root/Production Dashboard/digital-job-file-spec.md` (**J§**), the paper file
- `/root/Production Dashboard/LATER.md` (**L-n / X-n**), deferred items
- The Operations Review artifact (16 Sep), which confirms that every SPS invoice is an **Internal Transfer Note** to SH. So "ITN" = a Zoho SPS invoice = stage 10.

---

## 0. Prerequisites and decisions on them

| # | Prerequisite | Decision (user, 2026-09-17) | Blocks |
|---|---|---|---|
| **P1** | A read-only way to look up EPF numbers. Employee Master today has one shared `SERVICE_TOKEN` with full create/update/delete (`employee-master-service/auth.js:11,23`; `routes/employees.js:63,96,154`), and its list endpoint returns NIC, address, phone and device PIN (`routes/employees.js:28-36`). | **(a)** A separate Employee Master change adds a second token limited to GET. It has its own spec, review and deploy (L18). | Release 5 only |
| **P2** | Fresh Zoho data. | **(a)** A Zoho **self-client**, used **only with read scopes** (Inventory sales orders, packages, shipments, invoices, items, composite items: all `.READ`). The token therefore **cannot** write to Zoho at all. The sync is **Release 1b** and gets **its own spec addendum** before it is built (call budget, detail calls for lines, token storage, 429 handling). **Until Release 1b ships**, the daily manual export/import in §14.2 is the interim. | Release 1b; how fresh the Release 1/3 lists are |

Releases 0–4 are buildable without P1, and with either data path, because the import CLI and the sync share the same upsert functions (§8).

## 1. Purpose

Replace the paper job file, the monthly Excel job sheet and the unused Zoho dashboard (B§1) with one system that:

1. shows every job's stage, location and blockers to the people responsible for it;
2. records **who did what, and when, from the action itself**;
3. answers **capacity or readiness / post-production handling?** (B§12).

Success means the analyst desk stops asking for the Excel sheet (B§13), and "where is the file?" is answered on screen.

## 2. Decisions already made (do not reopen)

| # | Decision |
|---|---|
| D1 | Standalone service on port 4300 at `production.standard-holdings.lk`, not inside the Hub |
| D2 | Its own user accounts, for everyone including order requesters |
| D3 | Zoho data enters through shared upsert functions, fed by the import CLI now and by read-only sync from Release 1b |
| D4 | SPS first; every mirror row has `org` (`SPS` / `SH`) |
| D5 | Desk users use laptops and desktops |
| D6 | Production workers use a shared tablet mounted per department |
| D7 | Workers type their EPF number and confirm their name. No PIN |
| D8 | EPF numbers come from Employee Master through a read-only token (P1 a) |
| D9 | The coordinator creates the file (usually by converting an accepted portal order), links the SO, attaches documents, and hands the file to production |
| D10 | QMS forms stay on paper. The system records a tick with who and when (L1) |
| D11 | Rollout: order portal + coordinators → managers → stores/invoicing → GM/COO/analyst → floor workers last, per division |
| D12 | Releases 0–4 cover all divisions. Release 5 goes per division |
| D13 | React + Vite + TS + Tailwind + shadcn/ui; Node 24 + Express + better-sqlite3; SSE |
| D14 | Deferred items go to LATER.md the same turn |
| D15 | **Zoho stays read-only through the pilot and beyond**, until both systems are proven to be in step. The sync token has read scopes only. Write-back is a separate, later decision (B§13.7). The interim header pull (§14.2) uses a Zoho **web session**, which technically *could* write; its script issues GET requests only, and it should run under a Zoho user whose role is read-only |
| D16 | **Order portal:** replaces the WhatsApp order group. Everyone who places or updates manufacturing orders uses it with their own account |
| D17 | Dev/test tools `@axe-core/playwright` and `jsqr` approved |

## 3. Non-goals

These are out of scope. Items added in Rev 2 point to LATER.

- Any write to Zoho. The `outbox` stays `held`.
- Webhooks, the SH mirror, and cross-org stages beyond a manual tick.
- Digital QMS forms (L1).
- WhatsApp or any other notifications.
- Individual staff productivity in GM/COO responses.
- Parsing job numbers.
- Writing to Employee Master.
- Offline tablets.
- Native apps.
- **Cut to LATER in Rev 2 (finding 17):**
  - dark mode and keyboard shortcuts (L11)
  - the table column chooser and manager CSV export; the analyst export covers the need (L12)
  - the divergence rule "Zoho document disappeared", which an upsert importer cannot detect (L13)
  - the OPD floor forms, until B§/J§ Q5 on standard minutes is answered (L14)
  - COO "live" capacity extensions, until 28 days of data exist (L15)
  - carrying forward staff assignments (L16)
  - off-box backups (L17)

## 4. Architecture

```
Browser / tablet ─► https://production.standard-holdings.lk ─► Traefik ─► 172.17.0.1:4300
production-dashboard (PM2, Node 24, single process)
 ├─ Express: /api/*  ·  /api/events (SSE)  ·  /files/:id  ·  /* (web/dist)
 ├─ SQLite data/production.db  (WAL, foreign_keys=ON, busy_timeout=10000 on every connection)
 ├─ data/files/  ·  data/backups/
 ├─ import-zoho CLI  ─┐
 ├─ sync (Release 1b)─┴─► shared upsert functions → zoho_* mirror (read-only copy of Zoho)
 └─ Employee Master client (Release 5, read-only token)
Detected checklist stages = the per-SO facts (materialised at upsert) of the job's current SO link (§8.2).
```

**Binding, independent of the firewall (review 2, M2):**
- The server listens on **`127.0.0.1:4300`**, for health checks and CLI calls, and on **`172.17.0.1:4300`**, the Docker bridge that Traefik reaches. It never binds `0.0.0.0`.
- If `172.17.0.1` is not yet available at boot, the server retries that listener every 5 s and logs it. The loopback listener serves meanwhile.
- The ufw rules in §14 are extra protection only. ufw was inactive on 2026-09-17.

**Proxy trust (Rev 4, N1):**
- `trust proxy` is a function that trusts **only the addresses in `TRUSTED_PROXY_IPS`** (default `172.18.0.3`, Traefik's docker_gwbridge address, verified 2026-09-17). Other containers on the same bridge are not trusted, so their `X-Forwarded-For` is ignored.
- Ports 80/443 are published in **host** mode, so Traefik's `X-Forwarded-For` carries the real client address.
- A request arriving from an untrusted Docker address with `X-Forwarded-For` is logged and counted; Admin → Imports & health shows "proxy address changed?" when such requests are seen, because Traefik's address can change after a container restart.
- `req.ip` feeds logs and the per-IP limits only. The per-username and global limits (§5.2, §5.3) are the controls that matter.
- Post-deploy check: the logged `req.ip` equals the office public IP.

**SSE:** per B§3, with no compression on `/api/events`.

**Post-import sweep (Rev 4, M6).** The import CLI and the sync write **only** mirror tables (B§2.4). Everything that touches core tables after an import is owned by the **server**:
- **Trigger:** every 30 s (injectable) and at startup, the server looks for `zoho_import_runs` rows with `finished_at` set and `processed_at` NULL, in any id order, successful or failed. Runs finishing out of order or while the server was down are therefore never skipped.
- **Sweep (idempotent; step 1 covers every pending link, not only the run's SOs):**
  1. Resolve **every** pending SO link whose SO now exists in the mirror. Each resolution runs in `BEGIN IMMEDIATE` and inserts the `link` row **only if the job's highest-id link row is still that same `link_pending` row**, so a coordinator's unlink or relink made meanwhile always wins.
  2. Re-match current, unmatched reference rows (§7.4) on jobs whose linked SO changed in the processed runs **or whose link was resolved in step 1** (Rev 7.3; rows on other jobs cannot gain a match). Release 3 also matches at entry, link and relink time, so nothing waits for an unrelated import.
  3. Broadcast job and order events for jobs linked to the runs' `changed_so_numbers`.
  4. Set `processed_at` on those runs.
- **Also on link:** writing a `link_pending` row runs step 1 for that job at once and broadcasts the result, so an SO already in the mirror resolves immediately (Rev 5 N4).
- A crash mid-sweep is harmless: steps 1–2 are idempotent and the runs stay unprocessed until step 4.

### 4.1 Repository layout

```
production-dashboard/
  package.json + package-lock.json   (ONE lockfile at the root)
  server/   app.js · db/ (migrations/NNN-*.sql, migrate.js) · routes/ · services/ (derive.js, facts.js, sweep.js, …) · auth/ · sse.js
  shared/   time.js · forms.js · schemas.js · text.js (normalisers) · labels.js (display only)
  cli/      import-zoho.js · create-admin.js · backup.js · restore-check.js
  tools/    zoho-pull-snippet.js (interim header pull, §14.2)
  web/      Vite React app; build output web/dist (committed) + web/dist/.build-stamp
  config/   forms/*.json · zoho-columns.json   (seed data lives in migration 002, §6.1)
  test/     *.test.js (node --test) · compat/ · e2e/*.spec.js (Playwright)
  data/     (gitignored)
```

- **One root lockfile:** shdeploy runs `npm ci --no-audit --no-fund` (dev dependencies included) where a lockfile changed (`/root/ops/shdeploy:70`), so the live tree also gets dev dependencies. That is harmless, and it is noted in the README.
- **Build stamp (review 2, M5):** `.build-stamp` holds a SHA-256 over the **contents** of `web/src/**`, `web/vite.config.*`, `web/index.html` and `package-lock.json`. A test recomputes it and fails on mismatch. File modification times are never used.

### 4.2 Dependencies (approved by the user on 2026-09-17)

- **Runtime:**
  - express, better-sqlite3, dotenv, multer, exceljs (already used on the VPS)
  - react, react-dom, react-router-dom, @tanstack/react-query, @tanstack/react-table, zod, qrcode, clsx, tailwind-merge, class-variance-authority, lucide-react, @radix-ui/* (shadcn source copied in)
- **Build:** vite, @vitejs/plugin-react, typescript, tailwindcss.
- **Dev/test:** supertest, playwright, @axe-core/playwright, jsqr.
- **Not dependencies:** password hashing uses `crypto.scrypt`, and scanning uses `BarcodeDetector`, falling back to typing the number.
- **Anything else needs the user's approval first.**

## 5. People, roles and access

### 5.1 Roles

| Role | People | Can |
|---|---|---|
| `requester` | anyone who places manufacturing orders (sales, SH teams, order desk) | order portal only: new order, **their own and their team's orders** (plain status, messages, portal-visible attachments), messages and cancel requests on those orders (a team member may request cancellation of a colleague's order; the actor is recorded). **No** job internals, worker data, prices or other teams |
| `triage` | to be named (Q7) | incoming order queue: accept (choose division + pair → job), reject with reason, ask a question, decide cancel requests before acceptance, enter orders **on behalf of** a requester (§7.2.2); reads every order and its thread |
| `coordinator` | Nimesha, Madushi, Nirmani, Umanda | create files (from an accepted order or directly), link/unlink SO, attach documents, send and receive files, manual ticks and overrides, their reference sections, close/cancel, reply in order threads for their jobs |
| `manager` | Mubeena, Ranga, Ishan | jobs they currently manage, receive, ticks and overrides, blockers, day plans, output (divisions not `floor_live`), floor review, approvals for coordinator sections, reassign/close/cancel/reopen, reply in order threads |
| `stores` | Ilham | receive, shipments section, send to invoicing; **read-only** search over all open jobs (intended, to find files) |
| `invoicing` | Darshani | receive, ITN section, stage 11, close; read-only search as stores |
| `approver_stores` / `approver_invoicing` | to be named (Q2) | approve shipments / ITN rows |
| `gm`, `coo` | Production GM, COO | read everything, **redacted** (§5.4) |
| `analyst` | analyst desk | read everything; full export |
| `admin` | IT | configuration, users (incl. requesters and teams), devices, imports, audit |

- **Flags and teams:** `can_create_files` and `can_receive_files` are set per user. `users.team_id` comes from the admin-managed `teams` table and defines team visibility in the portal. **A user with the `requester` role must have a team** (admin API → 400 otherwise, Rev 4 M7).
- **Mixed roles (Rev 4, N11):** a desk user may also hold `requester`. The **route** decides the scope and serializer: portal routes (`/api/orders…`) use the requester scope and the minimal serializer; desk routes use the desk scope. A user whose only role is `requester` gets 403 on every desk route.
- **Scope:**
  - A manager sees jobs where the **current** manager is them.
  - A coordinator sees jobs where they are the current coordinator or the creator, plus accepted orders assigned to them.
  - A requester sees orders where `requester_id = me`, **or** the order's `team_id` equals the requester's `team_id` **and both are non-NULL** (a NULL team matches nothing, Rev 4 M7).
  - Order threads and order files for desk roles follow the matrix in §7.2.4.

### 5.2 Desk authentication

- **Passwords:** scrypt via the async API, N=2^15, r=8, p=1, **`maxmem: 64 MiB`**, 16-byte salt (finding 21). Minimum 10 characters. An admin can force a reset.
- **Sessions:** a random 256-bit id, stored only as its hash. Cookie `pd_sid` (`HttpOnly; Secure; SameSite=Strict; Path=/`). A session ends after 12 h idle or 7 days, and every session of a user is revoked when their roles change, they are deactivated, or their password is reset.
- **Rate limits:** 10 failures per username per 15 min give 429. **100** failures per IP per 15 min give 429; the office sits behind one NAT address (finding 22).
- **CSRF:** every non-GET request needs an `Origin` header equal to the configured origin. **A missing `Origin` is rejected too** (finding 22).
- **Secrets:** there is **no `SESSION_SECRET`**, because nothing is signed (finding 20).
- **First admin:** created with `node cli/create-admin.js`, run by the human.

### 5.3 Floor station (tablet) authentication

- **Enrollment (findings 11, 31):**
  - An admin clicks **Admin → Floor tablets → New code** (division, device name). The code is **10 characters of Crockford base32 (50 bits)**, valid for 10 minutes and single-use.
  - The tablet enters it at `/floor/enroll` and receives the cookie `pd_dev` (random 256-bit, stored as a hash, `HttpOnly; Secure; SameSite=Strict`, valid 1 year), bound to one division.
  - **Lockout:** 10 failed enroll attempts per IP per 15 min, or **25 failed attempts globally per hour, invalidate all outstanding codes** and write an audit entry.
- **Revoke:** from the admin page. The next request gets 401, and open SSE streams for the device are closed (§9.2).
- **Worker sign-in (P1):**
  - The worker types their EPF number, and the server looks it up (§9.3).
  - If **exactly one employee** matches, the tablet shows name + department with **This is me / Not me** (finding 18: Employee Master has no "active" field).
  - If no employee or more than one matches, the tablet shows "EPF not found — ask your coordinator".
  - If the employee's department doesn't map to the device's division, it still allows sign-in but shows a yellow note "Not listed in <division>" and flags the submission `dept_mismatch` (finding 32).
  - EPF lookups are limited to 20 per device per 5 min.
- **Worker session (finding 13):**
  - The session ends **after every submit**, on **Done**, or after **3 minutes idle**.
  - Every write button shows **"Submitting as <name>"**.
  - Each write stores `worker_epf`, a snapshot of `worker_name`, `device_id` and `dept_mismatch`.
- **Drafts (finding 13):** unfinished floor forms are saved as **drafts** keyed by (device, worker EPF, job, form), so a worker can come back after the session ends. The RWU card is built for this: the worker adds intervals through the shift, and the card is submitted at the end.
- **Scope:** a device sees only its division's open jobs and those jobs' attachments. It can only use floor routes, and never reports, admin routes, other divisions or user data.
- **Known risk (D7, accepted):** someone can type another person's EPF. The mitigations are device binding, the "Submitting as" label, the department-mismatch flag, manager review, and the audit log. A PIN can be added later (`floor_sessions.pin_verified_at`).

### 5.4 Redaction (review 1 #10, review 2 M7)

For a user whose roles are only `gm` and/or `coo`, the server:

- **Worker identity:** replaces every worker identity with the text "operator". That covers `worker_epf`, `worker_name`, `worker_label`, and **every `actor_label` and `actor_id` on rows with `actor_type = 'worker'`** (handovers, stage rows, submissions, history, SSE).
- **Form contents:** never sends `payload_json` of floor submissions, only form name, time and review state.
- **Minutes:** sends no per-job minutes or operator counts. Labour figures appear only as division × process × week aggregates, and only when **at least 2 distinct workers** contributed. Otherwise the cell shows "—".

**Requesters** get a separate, minimal serializer: plain status, their order fields, the order's messages, and portal-visible attachments. Nothing else is sent to them.

## 6. Data model

- **Engine:** SQLite in WAL mode, with `PRAGMA foreign_keys=ON` and `busy_timeout=10000` on every connection.
- **Times:** stored as **UTC ISO strings ending in `Z`**. **Colombo calendar dates** (for "today", entry dates, weeks and checkpoints) come only from `shared/time.js` (`colomboDate(utcIso)`, a fixed +05:30 with no DST), and never depend on the VPS time zone (finding 9).
- **Money:** LKR cents.

### 6.1 Migrations and seed data (review 1 #15, review 2 M4, M6)

**Migrations:**
- **Files and order:** numbered SQL files in `server/db/migrations/`, applied in order by `migrate.js`, which tracks `user_version`. Running it again is a no-op.
- **Forbidden:** `DROP TABLE`, `ALTER TABLE … DROP COLUMN` and any `RENAME`.
- **Allowed:** `DROP VIEW|TRIGGER|INDEX IF EXISTS`, but only when the **same file** re-creates an object of that name. A test parses every migration and enforces both rules.
- **Newer schema:** code that finds `user_version` above its highest migration starts normally and logs a warning.
- **Migrations folder override:** `migrate.js` reads migrations from `PD_MIGRATIONS_DIR` when it is set (default `server/db/migrations`). This exists from Release 0 (AC0.15).
- **Compatibility check (from Release 1 on):** `npm run test:compat` checks out the previous release tag in a temporary git worktree and runs **its** `test/` suite with `PD_MIGRATIONS_DIR` pointing at the **new** migrations folder, so the old code runs against the new schema. Release 0 has no previous tag, so the check is skipped there.
- **Deploys migrate automatically:** migrations run on startup. shdeploy prints "migration files changed … run them yourself" whenever a changed path matches `migrat|schema\.sql|seed` (`/root/ops/shdeploy:136-137`; `002-seed.sql` matches). **For this service, ignore that message: do not run `migrate.js` by hand.** The release notes list each new migration.

**Seed data (Rev 4, M5):**
- **Seed is a migration:** `002-seed.sql` inserts the divisions, stages, stage orders, processes, aliases, pairs, reason codes, reject reasons and order-type aliases (§6.5). Because migrations run once per database, in order, a fresh database and a long-lived one end in the **same** state, and a row an admin deleted never comes back.
- **Changing seed values later:** a new numbered migration (`UPDATE …`). On a fresh database it runs after 002, so it applies there too.
- **After the first start the database is authoritative**, and admin edits survive restarts.
- **Form definitions:** at startup, each `config/forms/*.json` is hashed. When the hash differs from the latest stored version of that form, a **new version row** is inserted. Old versions stay, because existing submissions reference them.

### 6.2 Mirror tables (a read-only copy of Zoho, written only by the shared upsert functions)

| Table | Key | Columns |
|---|---|---|
| `zoho_so_headers` | (org, salesorder_number) | zoho_id, order_date, **expected_shipment_date** (from `shipment_date` / "Expected Shipment Date"; this is the job's delivery date, because Zoho's `delivery_date` is empty), reference_number, status, shipped_status, invoiced_status, quantity, quantity_packed, **quantity_shipped**, quantity_invoiced, total_cents, cf_job_no, cf_order_received_from, cf_order_type, cf_manufacturing_division, cf_job_nature, cf_material_to_be_used, cf_sh_sales_order_ref, cf_clickup_link, cf_artwork_availablility, cf_dye_cutter_availablity, cf_screen_plate_availability_2, created_at, modified_at, source, source_file, last_synced_at, sync_state, **captured_at** (the capture that last wrote this row; Rev 7 B1) |
| `zoho_so_lines` | (org, salesorder_number, line_no) | item_name, sku, quantity_ordered, quantity_packed, quantity_invoiced, quantity_cancelled, usage_unit, rate_cents, amount_cents, source_file |
| `zoho_bundles` | (org, zoho_id) | reference_number, **so_key** (computed at upsert, below; indexed with org), date, composite_item_name, quantity, status, created_at, last_synced_at |
| `zoho_package_lines` | (org, package_number, line_no) | so_number, packing_date, status, item_name, sku, quantity_packed, last_synced_at. Index (org, so_number) |
| `zoho_shipment_lines` | (org, shipment_number, line_no) | so_number, packing_number, shipment_date, delivery_date, status, created_at, modified_at, last_synced_at. Index (org, so_number). **No quantity: the export has none (verified 2026-09-17)** |
| `zoho_invoices` | (org, invoice_number) | so_number (from header JSON `reference_number` **or** xlsx `Sales Order Number`), invoice_date, status, created_at, last_synced_at. Index (org, so_number) |
| `zoho_picklists` | (org, zoho_id) | picklist_number, date, status, salesorder_numbers (as received), created_at, captured_at |
| `zoho_picklist_sos` | (org, picklist_id, so_number) | one row per SO listed on a picklist, rewritten with its picklist. Index (org, so_number) |
| `zoho_items` | (org, zoho_id) | name, sku, unit, status, is_composite |
| **`zoho_so_facts`** | (org, so_number, stage_id) | done_at, at_precision, source_ref. **Materialised by the upsert functions** (§8.2) |
| `zoho_import_runs` | id | org, module, source, file, **captured_at** (when the data was taken from Zoho, never the import time; Rev 5 B1), **full_list** (bool: the run covers every record of the module, e.g. the full header pull), status (NULL while running; set to `ok` / `warning` / `failed` only when the run finishes, together with `finished_at`; Rev 7 B2), started_at, finished_at, **processed_at**, rows_read, rows_upserted, rows_skipped, **changed_so_numbers** (JSON), error |

**Capture guard on every mirror table (Rev 7.1 M1):** `zoho_so_lines`, `zoho_bundles`, `zoho_package_lines`, `zoho_shipment_lines`, `zoho_invoices`, `zoho_picklists` and `zoho_items` also carry `captured_at` (the capture that last wrote the row). Every upsert, in every table, writes only when the run's `captured_at` ≥ the row's stored `captured_at`, so an older folder never undoes a newer one.

**`so_key` (bundles):** trim, upper-case, then match `^([A-Z]+-\d+)(\s*-.*)?$`; `so_key` = group 1, otherwise NULL. So `JOBORDER-08338 - C` and `joborder-08338` give `JOBORDER-08338`, and `JOBORDER-083381` gives `JOBORDER-083381` (a different SO).

**Capture time (Rev 5 B1, Rev 6).** Every import run must know when its data left Zoho.
- **`captured.json`** in the folder: `{ "<file name>": { "captured_at": "<ISO time with offset>", "full_list": true|false, "rows": n } }`. The pull snippet writes its own entries (`captured_at` = the pull's **start** time); for UI exports the human types the time they clicked Export (`full_list` false).
- **`--captured-at <ISO time>`** only fills in files **missing** from `captured.json`, and is refused (exit 1) for a header-pull file (the fixed `zoho-pull-*.json` names, §14.2), because `full_list` can only come from `captured.json`.
- **Refusals:** a file with no capture time, or a capture time in the future (more than 5 minutes ahead), fails that file.
- **`full_list` is checked, not trusted:** the CLI keeps it true only when the entry's `rows` equals the de-duplicated row count in the file **and** that count is at least 98 % of the previous full-list run for the same module (the finished `ok`/`warning` full-list run with the latest `captured_at`; Rev 7.1 m4); otherwise the run is recorded with `full_list = false` and a warning.
- **Warning:** when a header file's capture is earlier than a package or shipment capture in the same folder, the CLI prints and records a warning (the result is simply `shipped_fresh = false`).
- **Run row first:** the run row, with `captured_at`, is inserted **before** the first batch, and `rows_upserted` is updated with each committed batch, so a crashed run still counts as a movement capture (§6.4). A crashed run keeps status NULL and `finished_at` NULL.
- The Release 1b sync records the request start time. Re-importing unchanged data changes no mirror row (AC0.7); only the run row records the capture.

**Materialised facts (Rev 4 M1/M2, Rev 5 M2).** Whenever an upsert batch touches rows for an SO (header, lines, bundles, picklists, packages, shipments, invoices), the same transaction recomputes that SO's `zoho_so_facts` rows, **and those of the SO the row pointed at before**, when a bundle's `so_key` or a package, shipment, invoice or picklist's SO changed. These are **mirror** tables (still B§2.4-clean): they are keyed by SO, not by job, so linking, unlinking or relinking a job still changes its stages instantly. `node cli/import-zoho.js --rebuild-facts` recomputes all of them; a test checks that incremental results equal a full rebuild.
- **Rules version:** the code carries `FACTS_RULES_VERSION` (shared by server and CLI; the CLI refuses to run while `settings.facts_rules_version` differs from its own). At startup, if `settings.facts_rules_version` differs (a new release changed a rule, or a rollback went back to older rules), the server rebuilds all facts inside one transaction before it starts listening, then stores the version. The rebuild is idempotent and must finish within 15 s on the full SPS mirror (AC0.23), inside shdeploy's health wait (`/root/ops/shdeploy:46-53`).

**Column mapping:** `config/zoho-columns.json` maps xlsx headers and JSON keys (the real ones) to mirror columns. Missing required headers fail the file.

**Normalisation (`shared/text.js`, review 2 m6):**
- **Text:** every `cf_*` value and every name is trimmed, and internal runs of spaces are collapsed.
- **Comparison keys:** comparisons use a lower-cased key. The original value is kept for display.

**Which source wins:**
- **Header fields:** from the headers JSON (or sync). From `Sales_Order.xlsx` only when no header row exists.
- **Line fields:** from `Sales_Order.xlsx` (or sync).
- **Conflicts between sources:** the newest `modified_at` wins, with the run's `captured_at` used when a source has no modified time.
- **Same source, full-list header runs (Rev 6, Rev 7 B1):** a row is overwritten whenever **any** mapped value differs, regardless of `modified_at` (and `modified_at` itself counts as a mapped value, so any Zoho edit refreshes the row and its `captured_at`; a pull also always takes over a row that `Sales_Order.xlsx` created, because `source` counts too; Rev 7.1 m2), so a changed `quantity_shipped` is never dropped — **but only when the run's `captured_at` ≥ the row's stored `captured_at`**. An older capture never overwrites a newer one, so importing folders out of date order ends in the same mirror as importing them in order.
- **Pull over xlsx (Rev 7.2):** a header row that only `Sales_Order.xlsx` created is always taken over by a pull or sync row, whatever the capture times, and the xlsx never overwrites a pulled or synced header. This is what lets out-of-order imports converge.
- **SO line sets (Rev 7.2):** `Sales_Order.xlsx` has no line number, so `line_no` is the row's position within its SO in the file. A mirror table `zoho_so_line_sets(org, salesorder_number, captured_at, line_count)` records the capture that last wrote each SO's lines: a file's lines for an SO are used only when its capture is at least that new, and lines beyond the new count are then deleted. An older file therefore never brings back a removed line.
- **Header runs with `full_list = false`** (partial pulls, or runs whose count check failed): the newest `modified_at` wins, with `captured_at` as the tie-break, and never against a row with a newer stored `captured_at` (Rev 7 N5). (Verified 2026-09-17: for all 7,539 SPS SOs with a shipment before 2026-09-15, the header's `last_modified_time` is at or after the newest shipment's created time, so Zoho does move it; the rule does not depend on that.)
- **No lines yet:** a header without lines shows the product as **"lines pending"**, falling back to the job's `entered_product` if one exists (review 2 m6).

**Times:** converted to UTC `Z` before any compare or store. Accepted formats:
- `…+0530`
- epoch milliseconds
- Excel date cells
- `YYYY-MM-DD`, stored as 00:00 Colombo with precision `date`

**Batches and cut-off:**
- **Batches:** 2,000 rows per transaction, each opened with `BEGIN IMMEDIATE` (better-sqlite3 `.immediate()`, because the capture guard and the fact recompute read before they write; Rev 7.1 m3), and upserts are idempotent. A file that fails part-way leaves its earlier batches committed; that is safe, because re-running the file converges on the same result (Rev 4, M6).
- **Cut-off:** rows dated before 2024-01-01 are skipped, and the count is logged.

### 6.3 Core tables

**Append-only tables are marked (A):** triggers abort any UPDATE or DELETE on them.

**Ordering rule (review 2 B1):** in every event table, **"latest" means the highest `id`**. The `at` column is used only for display and duration maths.

| Table | Purpose / rules |
|---|---|
| `users` | id, username UNIQUE, display_name, password_hash, roles JSON, team_id FK (nullable), can_create_files, can_receive_files, active, must_reset, created_at |
| `teams` | id, name UNIQUE, active |
| `sessions` | id_hash PK, user_id FK, created_at, last_seen_at, expires_at, ip, user_agent |
| `divisions` | code PK, name, active, provisional, floor_live, **counting_process** (nullable; composite FK `(code, counting_process)` → `processes(division_code, code)`), **quantity_form_id** (plain form id text, validated in code against `form_definitions`, because forms load after migrations; the one floor form whose quantities count for this division; default `inline_inspection_run`; RWU = `rwu_internal_job_card`) (review 2 B2, Rev 5 M4) |
| `processes` | (division_code, code) PK, label, active. Seeded per division from J§ (e.g. SHPS `print`, `packing`; RWU `rewinding`, `cutting`, `packing`; PSU `forming`, `packing`) |
| `division_aliases` | zoho_value PK → division_code |
| `division_pairs` | id, division_code, manager_user_id, coordinator_user_id, active. **Not seeded** (users don't exist when migrations run); the admin creates them at go-live (§14.1) |
| `stage_catalog` | id 1–11, name, **detected** (bool: 4, 5, 6, 7, 8, 10), detector key |
| `division_stages` | division_code, stage_id, sort_order |
| `jobs` | id, **file_no** (`GENERATED ALWAYS AS ('PD-' \|\| printf('%06d', id)) VIRTUAL`), **job_no (nullable until set, Rev 4 B1)**, division_code, **org** (default `SPS`), order_id FK (nullable; the portal order it came from), entered_product, entered_customer, entered_ordered_qty, entered_unit, entered_delivery_date, **order_type** (`customised` / `ex_stock` / `internal`), job_nature, order_received_at, created_by, created_at. UNIQUE(division_code, job_no) (NULLs don't collide). **Partial unique `(order_id) WHERE order_id IS NOT NULL`**, so one order can never produce two jobs (Rev 4 B2). Updates are allowed only through the routes in §10, each audited |
| `order_type_aliases` | zoho_value PK → order_type. Seed: `Customized Order` → customised, `Ex Stock` → ex_stock, `Internal SH Order` → internal, `Make to Order (MTO)` → customised (provisional, Q11). Values verified in the SPS headers 2026-09-17. The **displayed** order type is the linked SO's mapped `cf_order_type` when there is one, otherwise `jobs.order_type` |
| `job_so_links` (A) | id, job_id, action (`link_pending` / `link` / `unlink`), salesorder_number, actor_type, actor_id, at, note |
| `job_status_events` (A) | id, job_id, status (`open` / `closed` / `cancelled`), actor_id, at, reason |
| `job_assignment_events` (A) | id, job_id, pair_id, actor_id, at, reason |
| `manual_stage_events` (A) | id, job_id, stage_id, action (`tick` / `untick`), actor_type, actor_id, actor_label, at, note (required for `untick`). **Only for non-detected stages** (1, 2, 3, 9, 11) |
| `stage_overrides` (A) | id, job_id, stage_id, action (`force_done` / `force_not_done` / `clear`), **salesorder_number** (the job's `linked_so` when written, or NULL), actor_id, at, note (required). **Only for detected stages**; this is how a human corrects detection (review 2 B1). An override applies only while `linked_so` still equals its `salesorder_number` (Rev 4 N2) |
| `handovers` (A) | id, job_id, kind (§7.0), from_state, to_state, actor_type, actor_id, actor_label, device_id, at, note |
| `blockers` | id, job_id, reason_code, note, **owner_label (set at creation only; to change it, close the blocker and open a new one)**, opened_by, opened_at, closed_by, closed_at. Partial unique `(job_id, reason_code) WHERE closed_at IS NULL`. A trigger allows only the one-time `closed_*` update |
| `reason_codes` | code PK, label, default_owner_label, active |
| `day_plans` | (job_id, plan_date, process) PK, planned_qty, set_by, set_at. Replacing a plan is allowed; the history lives in `audit_log` |
| `attachments` | id, **job_id or order_id** (exactly one; CHECK), **message_id** (nullable FK → order_messages; set when the file was posted with a message), kind, **portal_visible** (bool; rules in §7.2.4), original_name, stored_name, mime, size_bytes, sha256, uploaded_by, uploaded_at, deleted_by, deleted_at, delete_reason. Updates allowed only for the one-time soft delete and for `portal_visible` on job attachments (audited); a trigger guards both |
| `form_definitions` | (id, version) PK, division_code (null = all), title, schema_json, output_map_json, content_hash, active |
| `floor_drafts` | id, device_id, worker_epf, job_id, form_id, form_version, payload_json, created_at, updated_at. UNIQUE(device_id, worker_epf, job_id, form_id). **Mutable by design**; deleted on submit or after 7 days |
| `form_submissions` (A) | id, job_id NOT NULL, form_id, form_version, payload_json, actor_type, actor_id, actor_label, device_id, dept_mismatch, submitted_at, supersedes_id UNIQUE. A submission and everything that supersedes it form a **chain**. A superseding submission must have the same `job_id` and `form_id` as the one it supersedes (400 otherwise, Rev 5 N2) |
| `submission_reviews` (A) | id, submission_id, decision (`accepted` / `queried`), note, actor_id, at. **State machine (review 2 B2, Rev 4 N3):** `pending` (no review row) → `accepted` (**terminal**) or `queried`. Only the **head** of a chain (the submission nothing supersedes) can be reviewed or superseded; anything else → 409. A superseding submission (a correction of a queried **or** an accepted one) is made by any signed-in worker on a device of the job's division and starts `pending` |
| `output_entries` (A) | id, job_id NOT NULL, division_code, entry_date, checkpoint, process (composite FK `(division_code, process)` → processes), **line_no NOT NULL**, quantity (nullable; **always stored as submitted**, Rev 4 N4), minutes (nullable), **source_form_id** (for submission rows), worker_epf, worker_label, missed_reason_code, source (`manager` / `submission`), source_submission_id, entered_by_type, entered_by_id, entered_at, device_id, supersedes_id UNIQUE. **CHECK: `source='submission'` ⇒ `source_submission_id` and `worker_epf` NOT NULL.** **Partial unique `(source_submission_id, line_no) WHERE source='submission'`** |
| `reference_entries` (A) | id, job_id, section, reference_no, qty, entered_by, entered_at, supersedes_id UNIQUE, voided. **A void is a new superseding row with `voided = 1`** (review 2 M10). The current row of a chain = the one no other row supersedes; it is ignored if it is voided. Only a user correction creates a new row |
| `reference_matches` (A) | id, reference_entry_id, zoho_ref, actor_type (`user` at entry / `system` from the sweep), at. **Rev 4 M4:** matching never touches the entry chain, so approvals (keyed to `reference_entry_id`) and `entered_by` stay intact. A row's match = its highest-id match row. The sweep inserts only if the entry is still the current row of its chain (checked inside `BEGIN IMMEDIATE`; otherwise it skips, and the next sweep handles the new row) |
| `reference_approvals` (A) | id, reference_entry_id, decision, actor_id, at, note. Approvers: coordinator sections → the job's current manager; shipments → `approver_stores`; ITN → `approver_invoicing` |
| `qc_ticks` (A) | id, job_id, kind, paper_doc_ref, actor_id, at |
| `orders` (immutable: a trigger aborts UPDATE and DELETE) | id, **order_no** (`GENERATED ALWAYS AS ('OR-' \|\| printf('%06d', id)) VIRTUAL`), requester_id, team_id (copied from the requester at submit), customer, required_date, order_type, division_hint (nullable), notes, **submitted_at** (the true order start: server time for `portal`; the typed WhatsApp receipt time for `on_behalf`), **entered_at** (server time, always), **created_via** (`portal` / `on_behalf`), entered_by |
| `order_lines` (immutable) | (order_id, line_no) PK, item_description, qty, unit, notes. Written once at submit |
| `order_events` (A) | id, order_id, event (`submitted` / `asked` / `answered` / `accepted` / `rejected` / `cancel_requested` / `cancel_declined` / `cancel_resolved` / `cancelled`), reject_reason_code, actor_id, at, note, job_id (set on `accepted`). Transitions in §7.2.0 |
| `reject_reasons` | code PK, label (seed: not feasible, duplicate, missing information, needs approval/price, other) |
| `order_messages` (A) | id, order_id, author_id, body (≤ 4,000 characters), at, **internal** (bool: staff notes that requesters never see) |
| `order_message_hides` (A) | id, message_id UNIQUE, actor_id, at, reason. A hidden message is removed from the requester serializer and shown struck through to staff (Rev 4 N11) |
| `floor_devices` | id, name, division_code, token_hash, enrolled_by, enrolled_at, revoked_at, last_seen_at |
| `floor_sessions` | id_hash, device_id, worker_epf, worker_name, started_at, last_seen_at, ended_at, pin_verified_at |
| `enrollment_codes` | code_hash, division_code, device_name, created_by, created_at, expires_at, used_at, invalidated_at |
| `enroll_failures` | ip, at (pruned after 1 h) |
| `upload_quota` | (user_id, colombo_date) PK, files, bytes, messages. Requester limits per day: 50 files, 200 MB, 100 messages → 429 (Rev 4 N11) |
| `outbox` | id, job_id, target, payload_json, state (`held`), created_at. **Never dispatched (D15)** |
| `audit_log` (A) | id, at, actor, action, entity, entity_id, detail_json |
| `settings` | key PK, value. Includes `live_since` (UTC time of the first job created in the app, set once; used by §7.6) |

**Generated columns (review 2 m4):** `file_no` and `order_no` are VIRTUAL, which avoids the insert-time NULL problem of STORED generated columns over `INTEGER PRIMARY KEY`. A test inserts a row and reads the value back.

### 6.4 Derived state (`server/services/derive.js` + SQL; **server only**, Rev 4 M2)

**One implementation.** Detection facts are materialised per SO (§6.2), so list endpoints and the job page read the **same** rows with one indexed join (`linked_so` → `zoho_so_facts`, plus the header row). The rules below are evaluated on the server only; the client receives computed values and `shared/` holds display helpers only. List SQL and single-job code share one set of query builders; a test compares every job of the 200-SO fixture through both endpoints.

| Name | Definition |
|---|---|
| `status`, `manager`, `coordinator`, `so_link` | the highest-id row of the respective event table |
| `linked_so` | the current `so_link` when its action is `link` (null when `link_pending` or `unlink`) |
| `so` | the header row of `linked_so`. Displayed product/customer/qty/delivery date = the SO values when linked (product from lines, §6.2), otherwise `entered_*`, with an "entered" badge |
| `so_ordered_qty` | the sum of `quantity_ordered` over lines when all lines share a unit; otherwise the header `quantity`, flagged `mixed_units` |
| **`detected[s]`** (stages 4, 5, 6, 7, 8, 10) | the `zoho_so_facts` row for (`job.org`, `linked_so`, s), giving `{done, at, at_precision, source_ref}` (rules in §8.2). `at` is the **earliest** matching document time. Unlinking or changing the SO changes the result immediately, with nothing to void (review 2 B1) |
| **`stage_state[s]`** | detected stages: the highest-id `stage_overrides` row, **if** its action is not `clear` **and** its `salesorder_number` equals the current `linked_so` (`force_done` → done at the override's `at`; `force_not_done` → not done); otherwise `detected[s]`. An override written for a different SO is ignored and shown as "override from previous SO (JOBORDER-…)" with a Clear button (Rev 4 N2). Manual stages: the highest-id `manual_stage_events` row (`tick` → done). A `clear` override returns the stage to automatic detection, so every stage can always be repaired |
| `current_stage`, `days_in_stage` | the last done stage in division order; now − its `at` |
| `file_location` | from the highest-id handover's `to_state` (§7.0); `closed` / `cancelled` if the status says so |
| `submission_state` | the latest review decision, else `pending`; plus **`replaced`** when a later submission in its chain is `accepted` (Rev 4 N3) |
| **`counted submission`** | per chain, the **highest-id `accepted`** submission. An accepted submission keeps counting until its correction is accepted; a pending or queried correction changes nothing |
| **`produced_qty`** | the sum of `output_entries.quantity` where process = the division's `counting_process` and the row is not superseded, counting **only**: `source = manager`; or `source = submission` **and** `source_form_id` equals the division's **current** `quantity_form_id` **and** the row's submission is its chain's counted submission (review 2 B2; Rev 4 N3, N4). Changing `quantity_form_id` therefore re-evaluates all history consistently |
| `pending_qty` | computed at read time by applying the form's `output_map` to the `payload_json` of each chain head that is `pending` (no output rows exist until acceptance, Rev 5 N1), with the same process and form filters, **shown separately and labelled** (a pending correction shows its quantity here while the accepted original still counts above) |
| `produced_qty` fallback | when neither of the above has rows: SO `quantity_packed`, labelled "packed (Zoho)" |
| **`shipped_fresh`** (per org, one value; Rev 5 B1, Rev 6) | true when **H ≥ M** and H is **recent**, where **H** = MAX(`captured_at`) over SO-header runs with `full_list = true`, `finished_at` NOT NULL and status `ok` or `warning` (never "highest id"; an unfinished or crashed header run never counts, Rev 7 B2); **M** = MAX(`captured_at`) over **every** packages or shipments run that wrote at least one row, whatever its status, including runs with no `finished_at`; and **recent** = `colomboDate(H) >= previousWorkingDay(colomboToday)` (`shared/time.js`; a weekend or holiday capture newer than the previous working day also counts, Rev 7 N1). When no packages or shipments run exists (M is NULL), fresh = H is recent (Rev 7 N6). The full list contains every SO, so it already reflects every package and shipment captured before it. A shipment made between the two captures can only put the header *ahead* of stage 8, never behind |
| **`shipped_state`** (per job) | `fresh` when `shipped_fresh` is true and the linked SO's header came from the pull or the sync; `no_header` when the SO is known only from `Sales_Order.xlsx`; otherwise `stale` |
| **`shipped_qty`** (Rev 4 B3, Rev 5 B1) | For a linked SO: `zoho_so_headers.quantity_shipped`, which only the header pull or the sync supplies (`Sales_Order.xlsx` has no shipped column, verified 2026-09-17). **Package quantities are never summed as a substitute:** on the 2026-09-16 exports they under-count against Zoho's header on 1,937 of 8,231 unchanged SOs (e.g. JOBORDER-08405: header 1,000, packages 900). Without a linked SO: `shipped_qty` = the sum of `qty` over current, non-voided shipments reference rows, and `shipped_state = fresh` |
| **shipped-based flags** | `overdue`, `at_risk`, `produced_not_shipped`, `short_delivery` and COO on-time use `shipped_qty` **only when `shipped_state = fresh`**. Otherwise the job is left out of those flags and shows **"shipped: unknown (Zoho header stale)"**, and the Today screen shows the count of such jobs as a grey note, never as overdue |
| `overdue` | open **and** delivery date < Colombo today **and** shipped_qty < ordered (fresh only) |
| `at_risk` | open, delivery date within the next 3 days, shipped < ordered (fresh only) |
| `produced_not_shipped` | open, produced ≥ ordered, shipped < ordered (fresh only) |
| `over_production` | produced > ordered × 1.02 |
| `short_delivery` | status closed and shipped < ordered (fresh only) |
| `ready_to_hand_off` | file at production, produced ≥ ordered |
| `waiting_on_stores` | file in `stores_transit` or `at_stores` with no current shipments reference row; **or** Package done and Shipment not done |
| `waiting_on_invoicing` | file in `invoicing_transit` or `at_invoicing`, **or** Shipment done, with stage 10 not done |
| **`sh_blocked`** | the normalised `cf_sh_sales_order_ref` matches `^to\s+(b|be)?\s*rec` (covers the variants in the data: "to be received", "to receive", "to be receivde", "to b received", "to be receives", "to be recevied", "to be recevide", "to be recived", "to be recevived"; 676 SPS headers, verified 2026-09-17) |
| **`order_state`** | from `order_events` per the §7.2.0 table: `submitted`, `questions`, `accepted`, `rejected`, `cancelled`; plus **`cancel_pending`** = the highest-id `cancel_requested` event is newer than every `cancel_declined` / `cancel_resolved` / `cancelled` event. When a job is cancelled or closed while `cancel_pending`, the same transaction writes an order event **`cancel_resolved`** (Rev 5 M1), so reopening the job never brings the request back |
| **`order_status`** (portal, plain words) | Before acceptance, from `order_state`: **Submitted**, **Question for you**, **Rejected**, **Cancelled**. **After acceptance the job is the only source (Rev 4 B2):** job cancelled → **Cancelled**; job closed → **Completed**; else stage 10 done → **Invoiced**; stage 8 → **Shipped**; stage 7 → **Packed**; **any `to_production` handover ever** → **In production** (it does not fall back when the file comes back, N13); else **Accepted**. Reopening a job therefore restores the right status automatically. "Cancellation requested" is shown alongside while `cancel_pending` |

### 6.5 Seed configuration (migration `002-seed.sql`; the DB is authoritative after that, §6.1)

- **Stage orders (J§1.2):**
  - OPD `1,2,3,4,6,5,7,8,9,10,11`
  - SHPS `1,2,3,4,5,6,7,8,9,10,11`
  - PSU `1,2,3,4,5,7,8,9,10,11`
  - RWU `2,3,4,5,7,8,9,10,11`
  - MOBA, MOBA_P, FPP, CPU, PACKPRO and the Rev 6 additions **PCU** (Paper Cup Unit), **PCLU** (Paper Cup Lid Unit), **DPU** (Digital Printing Unit), **PPU** (Paper Plate Unit) and **CWU** (Cake Wrapper Unit) use the OPD order and are `provisional` (L3, L4, L20).
- **Detected stages:** 4, 5, 6, 7, 8 and 10. Stage 6 is detected but rarely matches while L5 is open, so people mark it with `force_done`.
- **Processes:** a provisional list per division, editable by admin. Q6 asks the user to confirm.
  - SHPS: `print`, `curing`, `packing`
  - RWU: `rewinding`, `cutting`, `packing`, `personal` (breaks; never counted in production sums)
  - PSU: `forming`, `cutting`, `packing`
  - OPD, MOBA, MOBA_P, FPP, CPU, PACKPRO, PCU, PCLU, DPU, PPU and CWU: `print`, `die_cut`, `pasting`, `packing` (provisional)
- **counting_process:** SHPS `print`, RWU `rewinding`, PSU `packing`, all others `packing`.
- **quantity_form_id:** RWU `rwu_internal_job_card`; every other division `inline_inspection_run`.
- **Division aliases:** all 12 values in the SPS headers (verified 2026-09-17, SO counts in brackets): `Offset Printing Division (OPD)` (3,805) → OPD; `Screen Printing Division (SHPS)` (2,330) → SHPS; `Paper Straw Unit (PSU)` (738) → PSU; `Rewinding Unit (RWU)` (551) → RWU; `Paper Cup Unit (PCU)` (483) → PCU; `Customized Packing Unit (CPU)` (157) → CPU; `MOBA Punching Unit` (98) → MOBA; `Paper Cup Lid Unit` (81) → PCLU; `Food Product Processing (FPP)` (44) → FPP; `Digital Printing Unit (DPU)` (22) → DPU; `Paper Plate Unit` (9) → PPU; `Cake Wrapper Unit` (7) → CWU. MOBA_P's and Packpro's values are unknown (L8).
- **Divisions without a pair** (PCU, PCLU, DPU, PPU, CWU until L20 is answered) can hold jobs; the admin adds their pair before a coordinator can create files for them.
- **Manager + coordinator pairs (B§5.3), created by the admin at go-live, not by 002:** OPD {Ranga+Nirmani, Ishan+Umanda}; MOBA, MOBA_P, FPP {Ranga+Nirmani}; CPU {Ranga+Nirmani, provisional (L4)}; SHPS {Mubeena+Madushi}; RWU, PSU, PACKPRO {Ishan+Umanda}. Nimesha's pair is set by the admin once confirmed (Q2).
- **Order-type aliases:** §6.3.
- **Insert order in 002 (Rev 5 M4):** divisions (with `counting_process` NULL) → processes → `UPDATE divisions SET counting_process` → stage catalog → division stages → aliases → reason codes → reject reasons → order-type aliases. A test runs 002 on an empty database with `foreign_keys=ON`, and `PRAGMA foreign_key_check` returns nothing.
- **Reject reasons and reason codes:** as listed in §6.3 and B§9.

## 7. Screens

### 7.0 File movement (review 1 #5, #8; review 2 M9)

**States:** `at_coordinator`, `production_transit`, `at_production`, `coordinator_transit`, `stores_transit`, `at_stores`, `invoicing_transit`, `at_invoicing`.

**Start:** a new job has no handover rows, and its location is **`at_coordinator`** by definition.

**Complete transition table.** Every other combination returns **409**.

| From | Kind | To | Who may click |
|---|---|---|---|
| at_coordinator | `to_production` | production_transit | coordinator (also for rework or a further production run) |
| production_transit | `received_by_production` | at_production | manager; floor device (Release 5); coordinator on production's behalf |
| production_transit | `recall` | at_coordinator | the sender (coordinator) |
| at_production | `to_coordinator` | coordinator_transit | manager; floor device; coordinator on production's behalf |
| coordinator_transit | `received_by_coordinator` | at_coordinator | coordinator |
| coordinator_transit | `recall` | **the `from_state` of the send being undone** (at_production, at_stores or at_invoicing) | the sender |
| at_coordinator | `to_stores` | stores_transit | coordinator |
| stores_transit | `received_by_stores` | at_stores | stores |
| stores_transit | `recall` | at_coordinator | the sender |
| at_stores | `to_invoicing` | invoicing_transit | stores |
| at_stores | `to_coordinator` | coordinator_transit | stores (send back, note required) |
| invoicing_transit | `received_by_invoicing` | at_invoicing | invoicing |
| invoicing_transit | `recall` | at_stores | the sender |
| at_invoicing | `to_coordinator` | coordinator_transit | invoicing (send back, note required) |

**Rules:**
- **Atomic checks:** each request carries `expected_from_state`. The server runs `BEGIN IMMEDIATE`, compares it with the current state, and inserts or returns 409.
- **Recall (Rev 4 M3):** a recall undoes the **latest** handover (the send into the current transit state). Its `to_state` is that handover's `from_state`, and only the user or device that made that send may recall it. Every `recall` row in the table follows this rule.
- **Closed or cancelled jobs:** every handover returns 409.
- **Job no required (Rev 4 B1):** `to_production` returns 400 "Job no missing" while `jobs.job_no` is NULL.
- **Reopen:** the location stays where it was at closing.
- **Recording on production's behalf:** allowed only while none of the job's division is `floor_live`. The row records who actually clicked.

### 7.1 Job page

**Tabs:**

| Tab | Content |
|---|---|
| **Overview** | Header: file no, job no, SO or "SO pending: JOBORDER-…" or "No SO"; division; customer; product; ordered / produced (+ pending) / shipped; delivery date and days left; file location and its age; status; manager and coordinator; open blockers with **owner** and age. Also: the Zoho SO block (read-only; gates shown as badges; SH-blocked badge), and a link to the **portal order and its message thread** when the job came from the portal |
| **Checklist** | The division's stages in order. **Detected stages** show "auto" with the source document and time (a date when precision is `date`). **Override** (force done / force not done, note required) and **Clear override** return the stage to automatic. **Manual stages** have Tick / Untick (untick needs a note). Every stage can always be corrected (review 2 B1) |
| **Production** | Handover timeline; progress per process (counting process highlighted; produced vs pending); submissions with their state; output entries; day plans |
| **Reference sheet** | All five sections are visible to desk roles (a deliberate deviation from J§7.1, so the whole baton is visible). Only the section owner writes, and only the approver approves. Rows show auto-match status |
| **QC** | "Inspection done" / "QC approved" ticks with the paper reference |
| **Documents** | Job attachments (previews for images and PDFs), each marked **"visible to requester"** or not, plus a read-only **"From the order"** list of the order's files |
| **Messages** | The portal order thread, when there is one. Staff can post **public** or **internal** notes, with attachments (§7.2.4) |
| **History** | Every stored event, redacted per §5.4. Detected stages have no stored rows, so History shows each detected stage's current fact ("Package detected — PKG-… on 2026-09-02") marked **detected**, next to the override rows (N13) |

**Actions bar:** only actions valid for the viewer and the job state are shown.
- File movement buttons (§7.0).
- **Close:** open jobs only. Manager, coordinator or invoicing. A reason is required if stage 10 is not done or shipped < ordered.
- **Cancel:** manager or coordinator, reason required.
- **Reopen:** manager, reason required.
- **Status changes are guarded (Rev 5 N3):** each carries `expected_status`; the server runs `BEGIN IMMEDIATE` and returns 409 when it differs, so a close and a cancel sent together cannot both be written.
- **Reassign:** manager or coordinator; active pairs of the division only.
- **Link / change / unlink SO:** coordinator. Detected stages recompute immediately.
- **Set job no (Rev 4 B1):** coordinator or manager. The first set needs no reason; a later change needs a reason. A duplicate within the division → 409. Every change is written to `audit_log`. A **"Job no missing"** badge shows until it is set.
- **Cancel-request banner (Rev 4 B2):** while `cancel_pending`, the job page shows "Requester asked to cancel: <message>" with **Cancel job** and **Decline cancellation** (public note required).

### 7.2 Order portal, triage and coordinator workspace (Release 1)

#### 7.2.0 Order state machine (Rev 4 B2)

**States:** `submitted`, `questions`, `accepted`, `rejected`, `cancelled` (the last three are terminal for the order; after acceptance the job carries the status). `cancel_pending` is a flag, not a state (§6.4).

| From | Event | To | Who |
|---|---|---|---|
| (new) | `submitted` | submitted | requester (portal) or triage (on behalf) |
| submitted | `asked` (public message) | questions | triage |
| questions | `answered` (written automatically by a requester's public message) | submitted | requester or team member |
| submitted, questions | `accepted` (creates the job) | accepted | triage; **refused (409) while `cancel_pending`**: the request must be decided first |
| submitted, questions | `rejected` (reason code + public note) | rejected | triage |
| submitted, questions | `cancelled` (only while `cancel_pending`) | cancelled | triage |
| submitted, questions, accepted | `cancel_requested` (+ message) | unchanged; sets `cancel_pending` | requester or team member. **409** if already pending, if the order is rejected or cancelled, or if the job is closed or cancelled |
| any, while `cancel_pending` | `cancel_declined` (public note) | unchanged; clears the flag | triage before acceptance; the job's coordinator or manager after |
| accepted, while `cancel_pending` | `cancel_resolved` (written automatically when the job is cancelled or closed) | unchanged; clears the flag | whoever cancels or closes the job (§7.1) |

**Edge cases (Rev 5 N3):** a triage public message while the order is already in `questions` is a plain message (no event). Requesters cannot post on rejected or cancelled orders (409); staff still can.

**Rules:** every request carries `expected_state` (and `expected_last_event_id` for `cancel_requested`, `cancel_declined` and `cancelled`). The server runs `BEGIN IMMEDIATE`, re-derives the state and inserts or returns **409**. The partial unique index on `jobs.order_id` is a second guard: two accepts can never create two jobs. Orders are never reopened; a rejected or cancelled order is re-submitted as a new order.

#### 7.2.1 Order portal (requesters)

**Tabs:** New order · My orders · Team orders

**New order:**
- **Fields:** customer\*, required date\*, order type\* (customised / ex-stock / internal), division (optional hint), items\* (repeat: description, qty, unit, note), notes, attachments (artwork, PO, photos; sent in the same multipart request).
- **On submit:** `submitted_at` is the **server time**, the true start of the order (B§16). The order gets its `OR-` number, and the requester sees a confirmation with that number.

**My orders / Team orders:**
- **List:** order no, customer, submitted, required date, **plain status** (§6.4 `order_status`), last message.
- **Order page:**
  - the requester's own order data
  - the status timeline (Submitted → Accepted → In production → Packed → Shipped → Invoiced → Completed; or Rejected with its reason, or Cancelled)
  - the **message thread**: public messages only, with attachments visible to the requester
  - **Send update**, e.g. "customer wants 500 more": a public message, with optional attachments (linked through `message_id`). While the order is in Questions, this is the answer
  - **Request cancellation**: writes a `cancel_requested` event and a message (§7.2.0). Triage decides before acceptance; the coordinator or manager decides after.

**Visibility:** requesters never see job internals, the checklist, workers, prices, other teams' orders, or internal notes.

**Updates are not edits:** an order's fields and lines never change after submit. Updates are written down as messages. Quantity changes are applied by the coordinator on the job (entered fields or SO), with the message as the record.

#### 7.2.2 Triage (Release 1)

**Tabs:** Incoming (state `submitted`, oldest first, with age; cancel-pending orders on top) · Questions (state `questions`, i.e. asked and not yet answered) · Recently decided · **Enter on behalf**

For each order, triage chooses one of:
- **Accept:**
  1. Choose the division and the manager+coordinator pair.
  2. The job file is created in the same transaction, with `order_received_at = submitted_at`, `entered_*` taken from the order (first item, plus "(+n more)"), and `order_id` set.
  3. The chosen coordinator sees it under **New from portal**.
- **Reject:** a reject reason is required, plus a public note.
- **Ask:** a public message. The order moves to Questions until the requester replies.

**Cancel requests:** before acceptance, triage cancels the order or declines the request (§7.2.0). After acceptance, the request appears on the job (banner) and in the coordinator's and manager's **Cancel requested** list; cancelling the job is what makes the requester see Cancelled (§6.4).

**Enter on behalf (Rev 4 N10):** for orders that still arrive by WhatsApp (Q8). Triage picks the requester (their team is copied), types the **received time** from the WhatsApp message (must be in the past and within 60 days), and fills the normal fields. The order is stored with `created_via = on_behalf`, `submitted_at` = the typed time, `entered_at` = now, `entered_by` = triage, plus an audit row. The requester sees it in My orders like any other.

**Accepted job fields (Rev 4 B1):** `org = SPS` (D4); `order_type` = the order's type; `job_no` is left empty unless triage types it in the accept dialog (optional, duplicate → 409); the coordinator sets it later (§7.1).

#### 7.2.3 Coordinator workspace (Release 1)

**Tabs:** New from portal · New file · My files (at coordinator / at production / overdue / SO pending / no SO) · Returned · Closing

**New from portal:** accepted orders assigned to this coordinator whose files have not been sent yet, with a **"Job no missing"** badge where applicable. The coordinator opens one, sets the job no, links the SO (search, or type the JOBORDER number as pending), adds documents, prints the cover sheet, and clicks **Send to production**.

**Cancel requested:** the jobs in scope with `cancel_pending` (§6.4), also shown to their manager in Release 2.

**New file (direct, for orders that didn't come through the portal):**
1. Division and pair.
2. Job no.
3. Order received date (defaults to now).
4. SO: search, pending JOBORDER, or No SO. **No SO** needs the four `entered_*` fields.
5. Order type and nature.
6. Attachments.

**Pending SO links:** a pending JOBORDER link is resolved by the server's post-import sweep (§4), written by the system. It is highlighted after 3 days.

**Cover sheet (J§1.4):**
- **Fields:** the J§1.4 fields plus the order number.
- **Dispatch table:** shows dispatch no and qty.
- **PSU/RWU variant:** shows processed qty and date (J§4.1).
- **QR code:** encodes `https://production.standard-holdings.lk/j/<job id>`.

**Messages:** the coordinator sees the order thread for their jobs and can reply publicly (the requester sees it) or post an internal note (§7.2.4).

#### 7.2.4 Order threads and files: who sees what (Rev 4 M8)

| Viewer | Order data + public messages | Internal messages | Order files | Job files | Post public / internal | Hide a message |
|---|---|---|---|---|---|---|
| requester (own or team order) | read | — | read if `portal_visible` | read if `portal_visible` and the job came from their order | public only (+ files) | — |
| triage | read, all orders | read | read all | — | both (+ files) | yes |
| coordinator, manager (job in their scope) | read | read | read all | read all (existing rules) | both (+ files) | own messages |
| stores, invoicing, analyst (job they can read) | read | read | read all | read all | — | — |
| gm, coo | read | — (Rev 5 N5) | read, except files of internal notes | read all | — | — |
| admin | read | read | read all | read all | — | yes |
| floor device | — | — | — | own division (existing rules) | — | — |

**Requester file rule (Rev 5 M3):** a requester may read an order file only if `portal_visible` is true **and** its `message_id` is NULL or not hidden; a job file only if `portal_visible` is true and the job came from their order. The serializer and `/files/:id` use this one function (404 otherwise).

**`portal_visible` rules:** an order file uploaded by the requester, or posted with a **public** message, is `true`. A file posted with an **internal** message is `false`. A job file defaults to `false`; the coordinator or manager can switch it (audited). The requester serializer and `/files/:id` apply exactly this matrix. **Internal notes are free text and could name workers, so `gm` and `coo` see public messages only** (Rev 5 N5); files posted with internal notes are hidden from them too.

**Uploads from requesters (Rev 4 N11):** the §11 allow-list and per-day quotas (`upload_quota`) apply. A message posted public by mistake is hidden with `order_message_hides`.

### 7.3 Manager workspace (Release 2)

**Tabs:** Today · My jobs · Incoming · Blocked · Floor entries (shown once any of their divisions has `floor_live`) · Reports.

**Today (B§10, finding 12):**
- **Counters:**
  - Blocked
  - Past delivery date
  - Due in 3 days
  - Incoming
  - **In production**
  - **Ready to hand off**
  - Produced, not shipped
  - Waiting on Stores
  - **Cancel requested**
- **"Shipped unknown" note:** a grey count of jobs left out of the shipped-based counters because their Zoho header is stale (§6.4).
- **Clicking a counter filters one list** on the same screen.
- **Each row:** status, job/SO, customer, division, checklist dots, produced/ordered (plus pending), due date, location + age, blocker + age + **owner**, and **operators and minutes today** (manager view only).
- **Division chips:** shown for managers with several divisions.
- **Type tags:** customised and ex-stock are tagged, and never averaged together.

**Other tabs:**
- **Incoming:** Receive, one at a time or several at once.
- **Blocked:** grouped by reason; close; change reason (close + open).
- **Day plan (optional, Q4):** set today's planned quantity per job and process. The missed-reason buttons appear on an output entry only when a plan exists and quantity < plan.
- **Record output:** a job, then the checkpoint (the next one due in Colombo time), then the process (defaults to the counting process), then quantity (the last three distinct values as chips, or a keypad). **Hidden for divisions with `floor_live`**, because floor forms feed output there (finding 13).
- **Floor entries:** Accept or Query, one at a time or batch-accept.

### 7.4 Stores (Ilham) and Invoicing (Darshani) (Release 3)

**Tabs:** Incoming · Waiting on me · Done (30 days) · Search (read-only, all open jobs)

**Stores:**
- receives the file
- enters the shipment reference and the dispatched **qty** (the qty is what the cover sheet's dispatch table and `shipped_qty` use when there is no linked SO)
- sends the file to invoicing

**Matching (review 2 m8):**
- **At entry:** a reference row is matched against `zoho_shipment_lines` for the linked SO; a match writes a `reference_matches` row (`actor_type = user`).
- **Re-matching:** current rows still unmatched are re-matched by every post-import sweep (§4); a match writes a `reference_matches` row with `actor_type = system`. The entry, its `entered_by` and its approvals are untouched (Rev 4 M4).
- **Stage 8:** is done when the mirror has a shipment for the SO (detected). The reference row is the Stores record, not the source of the tick.

**Invoicing:**
- receives the file
- enters the ITN reference (matched against `zoho_invoices` for the SO, the same way)
- **Stage 10:** detected from `zoho_invoices`.
- **Stage 11:** ticked manually by invoicing (or the coordinator or manager).
- **Close.**

**Approvals:** approvers see an Approvals tab.

### 7.5 GM (Release 4)

**Tabs:**
- **7 AM work list:** blocked jobs (longest first, with owner); **at-risk**, overdue and produced-not-shipped jobs; yesterday's output by division and process
- **Pipeline:** division × file location; a cell click filters
- **Blocked reasons**
- **Overdue**

**Redaction:** everything is redacted per §5.4.

### 7.6 COO (Release 4)

**Weekly:**
- **Hidden until 28 days after `settings.live_since`** (N13).
- On-time % (Colombo date of the first shipment's `shipment_date` ≤ the delivery date, both as Colombo dates; jobs with `shipped_state` ≠ fresh are excluded and counted), separately for customised and ex-stock
- Average blocked days
- Throughput per Colombo week: jobs closed and their ordered qty, per type
- Over-production **count and cost**: surplus qty × SO line rate, labelled as "at transfer price" (finding 28)
- Short-delivery count

**Capacity vs readiness:** the history view from the mirror, with the fixed caveat that these are recording dates. Live extensions are deferred (L15).

### 7.7 Analyst (Release 4)

- **Export:** an xlsx with **12 sheets** (N6, N13): jobs (with derived state), **stage state** (current state per job × stage, with source: detected / override / manual), stage corrections (manual stage events + overrides), handovers, status events, assignments, blockers, output entries, submissions + reviews, reference entries + matches + approvals, orders, order events.
- **Access:** analyst and admin only.

### 7.8 Admin (Release 0; floor tablet page in Release 5)

**Tabs:**
- **Users:** desk users and **requesters** (a team is required), teams, roles, flags, reset, deactivate. Bulk-create requesters from a CSV of name, username and team, with a temporary password shown once each.
- **Teams**
- **Working days:** weekdays that count (default Monday–Friday) and a holiday list (Poya and public holidays), used by `shared/time.js` `previousWorkingDay()` (Rev 6)
- **Divisions & checklists:** aliases, pairs, stage order, **processes**, counting process, quantity form, provisional; **floor_live**, which can only be switched on when the Employee Master read-only client is configured and answers. Otherwise the API returns 409 "Employee Master not configured" (review 2 M3).
- **EPF coverage:** percentage per department, available once P1 is live.
- **Forms:** read-only, with versions.
- **Reason codes and reject reasons**
- **Floor tablets:** new code, list, revoke.
- **Imports:** runs (with `processed_at`), per-module freshness, stale warning after 1 working day (interim) or after 1 h without a successful sync (Release 1b), `shipped_fresh` with the capture times it was computed from, the number of jobs with `shipped_state` ≠ fresh, **runs started more than 30 minutes ago with no `finished_at`** (a crashed CLI, Rev 5 N4), **unmapped division values with their SO counts** (informational; they don't change the run status, Rev 6), and the "proxy address changed?" warning (§4).
- **Divergence**
- **Audit**

**Startup and Employee Master:** startup **never** refuses to run because Employee Master settings are missing. It logs a warning, and `/api/health` reports `employeeMaster: 'not_configured'`.

### 7.9 Floor station (Release 5)

```
EPF keypad → "Nilaka Perera · Rewinding — This is me / Not me"
→ Jobs (this division): Incoming · At production · [Scan QR]
→ Job: header + attachments · [Receive] · [Continue draft]/[Fill form] · [Return to coordinator] · queried notes
→ Form (draft auto-saves) → "Submit as Nilaka Perera" → confirmation → worker session ends
```

**Touch targets:** at least 48 px, with high contrast. **Process fields are always a select** from `processes` for the device's division; free text is never used for a process (review 2 B2).

**Forms (OPD deferred, L14):**

| Form | Divisions | Key fields | output_map (applied on **accept**, one output row per `line_no`) |
|---|---|---|---|
| `inline_inspection_run` | all live divisions | processed date (D), processed by (D), processed qty, batch no, process (select, default counting process) | line 1: process, worker ← signed-in worker, quantity ← processed qty (always stored; it counts only while this form is the division's `quantity_form_id`, §6.4) |
| `shps_processing_order` | SHPS | components (repeat: component, qty), duration hours, impressions, printer name, confirmation, remark | line 1: process `print`, **minutes** ← duration × 60, quantity null |
| `rwu_internal_job_card` | RWU | intervals (repeat: from, to, minutes D, **process (select)**, qty, personal flag); footer totals D | one row per interval, `line_no` = interval index: process, minutes, quantity (counts because this form is RWU's `quantity_form_id`). Personal intervals give minutes only, with process `personal` excluded from production sums |
| `psu_time_claim` | PSU | minutes, staff (repeat: EPF → name), impressions, book serial no | one row per staff member (`line_no` = staff index): process `packing`, minutes split evenly (rounded; the remainder goes to line 1), quantity null |

**Review:**
- **Accepting** creates the rows once; the partial unique index `(source_submission_id, line_no)` guards this.
- **A queried submission** can only be superseded, by a worker submitting a corrected version that starts `pending`.
- **Correcting an accepted submission** is also done with a superseding submission (any signed-in worker on a device of the division). The original keeps counting until the correction is **accepted**; then the original is `replaced` and only the correction counts (§6.4). Only a chain's head can be superseded.

**Manager output entry** is hidden and refused (403) for `floor_live` divisions.

**Rollout order:** SHPS → RWU → PSU, each after at least one device is enrolled and P1 is live.

## 8. Zoho data: import, sync and stage detection

### 8.1 Import CLI (Release 0) and sync (Release 1b)

```
node cli/import-zoho.js --org SPS --dir <folder> [--dir <folder>] [--dry-run]
```

**Import CLI:**
- **Input and connection:** reads the formats in the export README through `config/zoho-columns.json`, and writes through its own connection (`busy_timeout = 10000`).
- **Deduplication:** rows are de-duplicated by key within a run.
- **Unmapped division values (Rev 6, replaces Rev 5 N6):** the mirror stores the raw value and **never skips rows** for it; mapping matters only for jobs and reports. Admin → Imports lists unmapped values with their SO counts, and the run status is unaffected. Fix: add the division or alias in Admin; no re-import is needed.
- **File order within a run:** irrelevant for correctness; freshness comes from `captured_at` (§6.4).
- **Change record:** the run writes `changed_so_numbers` for every SO whose header, lines, bundles, picklists, packages, shipments or invoices changed, and recomputes those SOs' facts in the same transactions (§6.2).
- **Core tables:** never written by the CLI or the sync (§4 post-import sweep).

**Sync (Release 1b, P2 a):**
- **Code path:** calls the same upsert functions with **read-scoped** credentials only.
- **Never writes to Zoho (D15):** the sync client exposes only GET requests, and a test fails if any non-GET call exists in the sync module.
- **Details deferred:** schedule, call budget, detail calls for line items, token storage and 429 back-off are left to the **Release 1b spec addendum**.

### 8.2 Stage detection (materialised per SO; review 2 B1, Rev 4 M1)

**How it works (Rev 4 M1/M2):**
- **No per-job ticks:** the rules below are evaluated **per SO at upsert time** into `zoho_so_facts` (a mirror table, §6.2). A job's detected stages are the facts of its current `linked_so`, filtered by `job.org`, read with one indexed join. Unlinking or relinking changes the result at once.
- **Performance target:** `/api/jobs` over 5,000 jobs with the full 2026-09-16 mirror answers in under 300 ms, and no single synchronous database call blocks the event loop for more than 100 ms (AC1.28). Large lists are therefore read in keyset-paged chunks of at most 500 jobs, yielding to the event loop between chunks.

| Stage | Done when (SPS mirror, SO = X, same `org`) | `at` / precision |
|---|---|---|
| 4 Sales order | a header row or a line row for X exists | header `created_at` / time; else order date / date |
| 5 Bundle | a `zoho_bundles` row with status `bundled` and `so_key = X` | earliest bundle `created_at` / time |
| 6 Pick list | a `zoho_picklist_sos` row for X (rare while L5 is open) | picklist `created_at` / time |
| 7 Package | a `zoho_package_lines` row with `so_number = X` | earliest packing date / **date** (the xlsx has no created time; verified) |
| 8 Shipment | a `zoho_shipment_lines` row with `so_number = X` | earliest shipment `created_at` / time |
| 10 Sales invoice to SH | a `zoho_invoices` row with `so_number = X` | invoice `created_at` / time if known; else invoice date / date |

**Freshness of detection (Rev 4, N14):** stage 5 depends on the bundles data, which only the header/bundles pull provides (§14.2). When the bundles module has no **full-list** run with `finished_at` set, status `ok` or `warning`, and `colomboDate(captured_at) >= previousWorkingDay(colomboToday)` (exactly the H rule; Rev 7.1 m1), stage 5 shows "auto — bundle data n days old" and people can use `force_done`.

**Correcting detection:**
- **Manual correction:** a human uses `stage_overrides`. `clear` returns the stage to detection. Nothing is ever voided.
- **Unlink or change the SO:** detection simply follows the new link.

**Divergence report (admin, analyst, GM):**
- a detected stage forced done while detection says not done, and the reverse
- SO invoiced while the job is open
- job closed while the SO is not invoiced
- SO link pending for more than 3 days
- reference rows still unmatched 2 days after entry
- linked jobs whose `shipped_state` is not `fresh` (with the reason: header capture older than the movements, too old, or no header)

## 9. Integrations

### 9.1 Traefik

- **Router:** `production` → `http://172.17.0.1:4300`, with Let's Encrypt, in `/root/dev/traefik-custom/custom.yaml`. The user copies it into place.

### 9.2 SSE

- **Endpoint:** `GET /api/events`.
- **Visibility:** each event is sent only to connections allowed to see that job **or order**, re-checked per event.
  - A requester receives `{type:'order', order_id}` for their own and their team's orders.
  - Triage users receive `{type:'order_queue'}` whenever an order is submitted, answered, or gets or loses `cancel_pending` (N15).
  - GM/COO payloads are redacted (§5.4).
- **Midnight:** the server sends `{type:'day'}` to every stream at 00:00:05 Colombo, and clients refetch, so date-based flags (overdue, due in 3 days) roll over without a user action (N15).
- **Closing streams:** a stream is closed on logout, revoke, role or team change, deactivation, or worker sign-out.
- **Heartbeat:** every 25 s.
- **No compression** on this route.

### 9.3 Employee Master (Release 5; P1)

- **Endpoint:** `GET {EMPLOYEE_MASTER_URL}/employees` with a Bearer token (read-only token per P1(a)).
- **Minimisation (finding 1):** the client **immediately reduces each record to `{id, name, dept, epfNumber}`** and never logs or keeps any other field.
- **Cache:** 60 s, refreshed on a miss at most once per 10 s. EPF values are normalised (trimmed, spaces removed, leading zeros removed for comparison). Duplicates are refused.
- **Down:** the floor sign-in shows "Staff list unavailable"; desk screens are unaffected.

## 10. API outline

- **Validation:** zod on every route, returning 400 with field errors.
- **Scope:** checked on the server for every route.
- **Auth key:** `S` = desk session, `R` = requester session, `D` = device plus worker session.

```
POST /api/auth/login|logout · GET /api/me                                            S/R
POST /api/orders (multipart: fields + files) · GET /api/orders?mine|team · GET /api/orders/:id   R (minimal serializer)
POST /api/orders/:id/messages (multipart: body, internal?, files)                     R (public only) · S per §7.2.4
POST /api/orders/:id/cancel-request {expected_state, expected_last_event_id, message}                        R
POST /api/orders/:id/decline-cancel {expected_last_event_id, note}                   S triage (before accept) · coordinator|manager of the job (after)
POST /api/order-messages/:id/hide {reason}                                           S per §7.2.4
GET  /api/triage/orders · POST /api/triage/orders/:id/{accept,reject,ask,cancel} {expected_state, …}   S triage
POST /api/triage/orders (on behalf: requester_id, received_at, fields, files)        S triage
GET  /api/staff/orders/:id (thread + files for desk roles, §7.2.4)                   S
GET  /api/jobs?view=&division=&location=&stage=&type=&overdue=&q=                    S (scoped)
POST /api/jobs                                                                       S coordinator + can_create_files
GET  /api/jobs/:id · GET /api/jobs/:id/history · PATCH /api/jobs/:id (entered_*, order_received_at; audited)   S
POST /api/jobs/:id/job-no    {job_no, reason?}   (reason required when changing; 409 duplicate)   S coordinator|manager
POST /api/jobs/:id/so        {action: link|link_pending|unlink, salesorder_number}   S coordinator
POST /api/jobs/:id/status    {status, expected_status, reason}                       S per §7.1 (409 on stale)
POST /api/jobs/:id/assign    {pair_id, reason}                                       S manager|coordinator
POST /api/jobs/:id/manual-stages/:stageId {action: tick|untick, note}                S coordinator|manager (manual stages only); invoicing for stage 11
POST /api/jobs/:id/overrides/:stageId     {action: force_done|force_not_done|clear, note}   S coordinator|manager (detected stages only)
POST /api/jobs/:id/handovers {kind, expected_from_state, note}                       S/D (409 on stale)
POST /api/jobs/:id/blockers · POST /api/blockers/:id/close                           S manager|coordinator
PUT  /api/jobs/:id/day-plan · POST /api/jobs/:id/output                              S manager (403 when floor_live)
POST /api/jobs/:id/attachments · PATCH /api/attachments/:id {portal_visible} · DELETE /api/attachments/:id · GET /files/:id   S (R: the §7.2.4 requester file rule; D: own division)
POST /api/jobs/:id/reference/:section · POST /api/reference/:id/approval             S owner / approver
POST /api/jobs/:id/qc                                                                S manager|coordinator
GET/PUT /api/floor/drafts/:jobId/:formId · POST /api/jobs/:id/forms/:formId          D
POST /api/submissions/:id/review · POST /api/submissions/review-batch                S manager|coordinator
GET  /api/so/search?q=                                                               S coordinator|triage
GET  /api/reports/{manager,gm,coo,divergence} · GET /api/export.xlsx                 S role-gated, redacted
POST /api/floor/enroll · /signin · /signout · GET /api/floor/jobs                    D (enroll: no auth)
GET  /api/events                                                                     S/R/D
GET  /api/health                                                                     public
/api/admin/*                                                                         S admin
```

**Role separation:** a user whose only role is `requester` gets **403 on every non-portal route**. Desk roles without `triage` get 403 on the triage routes. Portal routes always use the requester scope and serializer, even for users who also hold desk roles (§5.1).

## 11. Security

- **Headers:**
  - CSP `default-src 'self'; img-src 'self' data: blob:; frame-src 'self'; frame-ancestors 'none'` on app pages
  - `/files/:id?inline=1` gets `frame-ancestors 'self'` and **no `sandbox`** (so the Chrome PDF viewer works), plus `nosniff`, `Referrer-Policy: same-origin` and HSTS (finding 24)
- **Uploads:**
  - allow-listed types, checked by magic bytes where possible: PDF, PNG, JPEG, WebP, XLSX, DOCX, AI (PDF-based), PSD, CDR, ZIP. **SVG, HTML, XML and any script type are never accepted**
  - only images and PDFs are ever served inline; everything else is `attachment` with `nosniff`
  - requester quotas per day (§6.3 `upload_quota`)
  - 25 MB per file, 20 files per request
  - random stored names, outside the web root
  - served only through `/files/:id` after an auth and scope check
  - `Content-Disposition` with an RFC 5987 `filename*`; `attachment` unless `inline=1` and the file is an image or PDF
- **No secrets** in logs or responses. Error bodies carry a request id only.
- **Worker data:** EPF and names never reach GM/COO responses (§5.4).
- **Rate limits:** login, enroll and EPF lookup (§5).
- **Dependency audit:** `npm audit --omit=dev` must show no high or critical findings before each release.
- **security-auditor** reviews Release 0, **Release 1 (the order portal)**, Release 5, and the P1 Employee Master change (N7).

## 12. Operations

- **PM2:** `production-dashboard`, a single instance, with the listeners in §4.
- **Startup:** runs migrations and the seed (§6.1), then starts. **It never refuses to start because Employee Master or Zoho settings are missing**; it warns instead (review 2 M3).
- **Backups:**
  - `cli/backup.js` runs nightly at 01:30 (cron, added by the human). It uses SQLite's online backup to `data/backups/`, keeps 14 copies, and syncs the files folder.
  - `cli/restore-check.js` is run monthly by the human (AC0.11b).
  - Off-box copies are deferred (L17).
- **Health:** `/api/health` **always returns 200** while the process and database are up. Body: `{ok, db, employeeMaster: 'ok'|'down'|'not_configured', lastImport, lastSync}`.
- **shdeploy registry line** (added by the human):
  ```
  production-dashboard|/root/production-dashboard|production-dashboard|data/production.db|http://127.0.0.1:4300/api/health|docs/
  ```
- **Deploys:** every deploy runs migrations at restart; do **not** run `migrate.js` by hand (§6.1). The live tree also gets dev dependencies via shdeploy's `npm ci` (§4.1).
- **Logs:** JSON lines, with user ids only. The `req.ip` of the first request after a deploy is logged, for the proxy check in §4.

## 13. Releases and acceptance criteria

**Check types:**
- **T** = node --test + supertest on a temp DB (clock and poll interval injected)
- **E** = Playwright
- **C** = a single command

**Definition of done:** all ACs pass, test-runner is clean, code-reviewer passes, and security-auditor passes for Releases 0, 1 (portal) and 5.

### Release 0: Foundation

| AC | Criterion | Check |
|---|---|---|
| 0.1 | `npm test` passes from a clean checkout with no network, Employee Master stubbed and Zoho absent | C |
| 0.2 | Starting twice on the same DB leaves `user_version` and every row count unchanged | T |
| 0.3 | UPDATE and DELETE abort on every (A) table. On `blockers` and `attachments` only the one-time close or soft-delete update is allowed, and a second one aborts. `order_lines` cannot change after insert | T |
| 0.4 | Login: correct → 200 with HttpOnly/Secure/SameSite=Strict cookie; wrong → 401; 11th failure in 15 min for a username → 429; 101st from one IP → 429 | T |
| 0.5 | A non-GET with a foreign `Origin`, or with no `Origin`, → 403 | T |
| 0.6 | Without auth, every route except login, health, enroll and the SPA shell → 401. The walk covers `/api/*` and `/files/:id` | T |
| 0.7 | Fixture import gives the expected counts. Re-running changes nothing. 2023 rows are skipped. Duplicate ids are collapsed. `changed_so_numbers` lists exactly the changed SOs | T |
| 0.8 | Shuffled columns import identically. A missing required header fails that file and records the error | T |
| 0.9 | An unmapped division value: the rows are imported with the raw value, the run status stays `ok`, and Admin lists the value with its SO count | T |
| 0.10 | Times: `…+0530`, epoch ms, an Excel date and `YYYY-MM-DD` normalise correctly. `colomboDate('2026-09-16T19:00:00Z') = '2026-09-17'` and `colomboDate('2026-09-16T18:29:59Z') = '2026-09-16'`. `cf_*` values are trimmed (`"Reorder "` → `"Reorder"`) | T |
| 0.11 | Backup: `integrity_check = ok`, pruned to 14. **0.11b:** restore-check reports matching counts | T / C |
| 0.12 | `/api/health` → 200 with no secrets, including when Employee Master is `not_configured` or down | T |
| 0.13 | The server listens on 127.0.0.1 and 172.17.0.1 only (a bind to 0.0.0.0 is never attempted). `X-Forwarded-For` from a non-Docker source doesn't change `req.ip`. Security headers match §11 | T |
| 0.14 | Admin creates users (desk and requester) with roles and team. A non-admin → 403 on `/api/admin/*`. A role or team change ends that user's sessions and open SSE streams | T |
| 0.15 | The migration linter rejects `DROP TABLE`, `DROP COLUMN` and `RENAME`, and rejects `DROP VIEW/TRIGGER/INDEX` without a matching re-create in the same file. Code facing a higher `user_version` starts with a warning. **`PD_MIGRATIONS_DIR` pointing at a temp folder with an extra migration is honoured** | T |
| 0.16 | The content hash in `web/dist/.build-stamp` equals the recomputed hash | T |
| 0.17 | Seed is migration 002: an admin edit (e.g. `counting_process`) survives a restart; **an alias the admin deleted stays deleted after a restart**; a later migration that updates a seed value gives the same result on a fresh DB as on an existing one. A changed form JSON creates a new version, and the old version stays | T |
| 0.20 | Mirror facts: importing the 200-SO fixture in two different file orders, and in one run versus split runs, gives identical `zoho_so_facts`; `--rebuild-facts` gives the same again. **Moving a bundle's reference from SO A to SO B recomputes both** | T |
| 0.20b | `shipped_fresh` (Rev 5 B1), with an injected clock: (a) an **unchanged** header list re-imported with a later `captured_at`, after a shipments file whose status changed → fresh; (b) a header list captured **before** a shipments file that contains a new shipment → not fresh, **whatever order the files are imported in**; (c) re-importing unchanged files changes no mirror row, only run rows; (d) a header capture older than 1 working day → not fresh; (e) an SO known only from `Sales_Order.xlsx` → `no_header`; (f) the CLI refuses a folder with no `captured.json` and no `--captured-at`; (g) a full-list header run ending `warning` still counts for H; (h) a **failed or unfinished** shipments run captured after the header, having written rows → not fresh; (i) a newer folder imported **before** an older one → H and M are the maxima, **and every mirror row in every mirror table (including `quantity_shipped`, bundle `status`/`so_key` and package `so_number`; bookkeeping columns `source_file` and `last_synced_at` excluded) equals the result of importing them in date order**; an A→B→A value change across three folders, imported 1, 3, 2, ends at A; (i2) an **unfinished** full-list header run with a later `captured_at` does not move H; (j) the fixture includes a PCU header row and a `to be recevied` value (→ `sh_blocked`); (k) `--captured-at` for a header file → refused; a capture time in the future → refused; `rows` in `captured.json` not matching the file → `full_list` false; (l) Friday's header capture is fresh on Monday morning and not on Tuesday; a **Sunday** capture before a holiday Monday is fresh on Tuesday; a Saturday capture is fresh on Monday | T |
| 0.20c | Same source, full list: a header with the same `modified_at` but a different `quantity_shipped` is updated | T |
| 0.21 | Post-import sweep: two runs that finish out of id order, and a run that finishes while the server is stopped, are all processed (`processed_at` set) and their pending links resolved. A coordinator unlink written between the import and the sweep is not overwritten. A failed run is also marked processed | T |
| 0.22 | Proxy trust: `X-Forwarded-For` from `TRUSTED_PROXY_IPS` sets `req.ip`; the same header from another 172.x address is ignored and counted | T |
| 0.23 | Changing `FACTS_RULES_VERSION` and restarting rebuilds all facts once, within 15 s on the full SPS mirror; a second restart does nothing; the CLI refuses to run while the versions differ | T |
| 0.24 | Migration 002 on an empty DB with `foreign_keys=ON` succeeds and `foreign_key_check` is empty; an output row with a process from another division is refused | T |
| 0.25 | The pull snippet (run against a stubbed list API in Playwright) sends GET requests only, follows pages until `has_more_page` is false, de-duplicates by id, and writes `captured.json` with the start time, `full_list` and the **de-duplicated** `rows`; a stub that repeats a row across pages still gives `full_list: true` and the right count; a stubbed error mid-way gives `full_list: false`; the output file names are exactly those in §14.2 | E |
| 0.18 | `file_no` and `order_no` read back correctly right after insert | T |
| 0.19 | Admin pages render with no console errors | E |

### Release 1: Order portal, triage and coordinators

| AC | Criterion | Check |
|---|---|---|
| 1.1 | A requester submits an order with 2 items and 1 attachment. `submitted_at` is server time (a client-sent time is ignored). The order is listed in My orders as **Submitted** | T+E |
| 1.2 | A requester sees their own and their team's orders only. Another team's order → 404. **Two requesters without a team (created directly in the DB) cannot see each other's orders; the admin API refuses a requester without a team (400).** A requester-only user → 403 on every non-portal route. Responses contain no job internals, prices, worker fields or internal messages (a key/value scan on seeded data) | T |
| 1.3 | Order fields and lines can't be changed after submit (the API has no such route, and the triggers on `orders` and `order_lines` abort) | T |
| 1.4 | Triage **accept** creates a job in the same transaction, with `order_received_at = submitted_at`, `entered_*` from the order, `order_id` set, `org = SPS` and the order's type. The order shows **Accepted**, and the job appears in that coordinator's "New from portal" with "Job no missing". **Two simultaneous accepts (and a retried accept) → one 200, one 409, exactly one job.** Accept while `cancel_pending` → 409 | T |
| 1.5 | Triage **reject** needs a reason code, and the requester sees **Rejected** and the reason. **Ask** moves the order to Questions; the requester's reply writes `answered` and moves it back to Incoming. Every §7.2.0 combination not in the table → 409 | T |
| 1.6 | Every cell of the §7.2.4 matrix is checked in both directions: e.g. a requester sees public messages, order files that are `portal_visible`, and job files switched to visible; never internal notes, files posted with them, or hidden messages. The job's Documents tab lists the order's files. Staff replies from the job page reach the order thread with their files. `POST /api/orders/:id/messages` with files links them through `message_id` | T |
| 1.7 | Plain status follows §6.4: accepted → sent to production → package detected → shipment detected → invoice detected → closed, and the requester sees each step. **A file sent back to the coordinator still shows In production** | T |
| 1.8 | Cancel before acceptance: request → triage cancels → Cancelled; or triage declines → flag cleared, public note visible. After acceptance: the request shows as a banner on the job and in the coordinator's **Cancel requested** list; cancelling the job → requester sees Cancelled; **reopening the job → the requester sees the job-derived status again**. A cancel request on a closed job, a rejected order, or while one is pending → 409. **Request → job cancelled → job reopened: no banner, no Cancel requested entry, and a new request is accepted** | T |
| 1.9 | A requester SSE stream receives events for their orders only | T |
| 1.10 | Linking an SO from the mirror shows its Z fields, and stage 4 is detected. **Unlink → stage 4 not done immediately; re-link the same SO → done again** (review 2 B1) | T |
| 1.11 | A pending JOBORDER link resolves in the post-import sweep after the next import (system `link` row), and SSE clients get a job event within poll interval + 5 s | T |
| 1.12 | "No SO" requires the four `entered_*` fields. A duplicate (division, job_no) → 409, both at creation and through `POST /job-no`. `RWU/IMP2357/QPP/00025/BIO` is stored as typed. **`to_production` with no job no → 400; setting it writes an audit row; changing it without a reason → 400** | T |
| 1.13 | A pair that isn't active for the division → 400 | T |
| 1.14 | Uploads: 26 MB → 413; renamed `.exe` → 415. Downloads use an RFC 5987 `Content-Disposition`. A PDF preview renders in the Documents tab | T+E |
| 1.15 | Out of scope → 404 on the job, its history and its files | T |
| 1.16 | Handovers: every row of the §7.0 table works, and every other combination → 409. Recall works for the sender only and returns to the undone send's `from_state`: **stores sends back → recall → at_stores; invoicing sends back → recall → at_invoicing; invoicing_transit → recall → at_stores**. Handovers on a closed job → 409. The client can't set `at` or the actor | T |
| 1.17 | A manual tick or untick on a detected stage → 400. An override on a manual stage → 400. Untick and overrides without a note → 400 | T |
| 1.18 | **Override path:** stage 7 detected → force_not_done → not done → clear → done again. force_done on stage 6 with no picklist → done. **Relink to another SO → the stage-6 override no longer applies and is shown as "from previous SO"** | T |
| 1.19 | Stage 7 detection has `at_precision = date`. After an import adds an earlier package for the SO, `at` becomes the earlier date. Importing again changes nothing | T |
| 1.20 | Bundle match: `JOBORDER-08338 - C` and `joborder-08338` match SO `JOBORDER-08338`; `JOBORDER-083381` doesn't. An invoice links through the header `reference_number` and through the xlsx `Sales Order Number`. **An SH row with the same SO number never ticks an SPS job** | T |
| 1.21 | Cover sheet: the §7.2.3 fields are shown, `jsqr` decodes the QR to `/j/<id>`, and the RWU variant shows processed qty and date | E |
| 1.22 | Close, cancel and reopen follow the §7.1 roles and reason rules, and each writes a status event with the actor. A close and a cancel sent together with the same `expected_status` → one 200, one 409 | T |
| 1.23 | Reassign offers only active pairs and moves the job into the new manager's scope | T |
| 1.24 | Displayed values: from the SO when linked (`entered_*` unchanged). A multi-line SO shows "first (+n more)" and the summed qty when units match. A header without lines shows "lines pending" or the entered product | T |
| 1.25 | Search by job no, order no, SO and customer | T |
| 1.26 | Stage orders match §6.5 | T |
| 1.27 | Flow: requester submits → triage accepts → coordinator (New from portal) sets the job no, links a pending SO, attaches documents, prints the cover sheet, sends to production → import + sweep resolve the SO → the requester's status shows "In production", live | E |
| 1.28 | Performance: with 5,000 jobs and the full 2026-09-16 SPS mirror, `GET /api/jobs` (all open, coordinator scope = all) answers in < 300 ms (median of 5), and `perf_hooks.monitorEventLoopDelay` max stays < 100 ms during the call | T |
| 1.29 | On behalf: triage enters an order with a received time 2 days ago → `submitted_at` = that time, `entered_at` = now, `created_via = on_behalf`, audit row written; a future time or one older than 60 days → 400; a non-triage user → 403 | T |
| 1.30 | Requester limits: the 51st file or the 101st message in a Colombo day → 429. An SVG or HTML file (also renamed to `.png`) → 415. A message hidden by triage disappears from the requester's view, **and a file posted with it returns 404 to the requester**. A requester post on a rejected order → 409 | T |
| 1.31 | Triage SSE: a new submission sends `order_queue` to triage streams only | T |

### Release 1b: Zoho read-only sync

The ACs are defined in the Release 1b spec addendum. The one fixed in advance:
- **1b.0:** the sync module makes GET requests only (static test), and its OAuth scopes are read-only (config test).
- **1b.1 (Rev 6):** the sync records a **full-list** SO-header run at least once per working day, after that cycle's package and shipment fetches, so `shipped_fresh` stays true while sync is healthy; or the addendum redefines `shipped_fresh` for sync with its own AC. §14.3 step 4 waits for this.

### Release 2: Managers

| AC | Criterion | Check |
|---|---|---|
| 2.1 | A manager sees exactly the jobs whose current manager is them. Other jobs → 404 | T |
| 2.2 | Each Today counter equals the **hand-computed** count for the seeded fixture (listed in the test), and equals the length of its filtered list (M2) | T |
| 2.3 | §6.4 states on boundary fixtures: due today (Colombo); `quantity_shipped` = ordered; produced = 1.02×; **multi-process fixture** (print 1,000 + die_cut 1,000 + packing 1,000 with counting process `packing` → produced 1,000) | T |
| 2.4 | A job fully produced, with a **fresh** header showing `quantity_shipped` 0, past its due date, is both `overdue` and `produced_not_shipped`. **The same job with a shipment imported after its header (`stale`) is in neither flag, shows "shipped: unknown", and is counted in the grey note** | T |
| 2.13 | At 00:00:05 Colombo (injected clock) streams get `{type:'day'}`, and a job due yesterday becomes overdue on refetch | T |
| 2.5 | Batch receive of 3 jobs → 3 rows | T+E |
| 2.6 | Blockers: reason required; `other` needs a note; a duplicate open reason → 409; close records who and when; owner defaults from the reason and can't be updated (the trigger aborts) | T |
| 2.7 | Output chips are the last three distinct quantities. Output → 403 for a `floor_live` division | T |
| 2.8 | Missed-reason buttons appear only when a day plan exists and quantity < plan | E |
| 2.9 | Manager reports never combine customised and ex-stock | T |
| 2.10 | SSE: manager A gets only A's jobs. After a reassignment to B, A stops getting that job. Logout closes the stream | T |
| 2.11 | Two simultaneous `received_by_production` requests → one 200 and one 409, and exactly one row | T |
| 2.12 | Flow: coordinator sends → Incoming updates live → Receive → Today shows the job "In production" | E |

### Release 3: Stores and Invoicing

| AC | Criterion | Check |
|---|---|---|
| 3.1 | Waiting on stores includes a job sent to stores **before** any Zoho package exists, and a job with Package done and Shipment not done | T |
| 3.2 | A shipment reference that matches the mirror gets a `reference_matches` row (`user`). A non-matching one stays unmatched, and after an import that adds the shipment the sweep writes a `system` match row; **the entry row, its `entered_by` and an existing approval are unchanged** (M4). Qty is stored. With no linked SO, `shipped_qty` = the sum of current reference qty | T |
| 3.3 | Only `stores` writes shipments and only `invoicing` writes ITN. The coordinator → 403 on both | T |
| 3.4 | Correction and void: a superseding row replaces the old one. A void row (`voided = 1`) removes it from the current set. A second supersede of the same row → 409 | T |
| 3.5 | Approvals by the defined approvers only. `entered_by` is unchanged | T |
| 3.6 | Invoicing flow: receive → ITN → stage 10 detected from the mirror → tick 11 → close. The requester sees Invoiced, then Completed | T+E |

### Release 4: GM, COO, Analyst

| AC | Criterion | Check |
|---|---|---|
| 4.1 | The work list's blocked section is ordered by age, and at-risk jobs are included | T |
| 4.2 | Pipeline cell counts equal the counts of the filtered list | T |
| 4.3 | **For GM-only and COO-only users, on seed data that includes tablet handovers, floor submissions (RWU and PSU), worker-entered output and internal order notes with files:** no response from reports, `/api/jobs`, job detail, history or SSE contains an EPF, a worker name, a worker `actor_label`, a `payload_json`, per-job minutes, or any labour cell with fewer than 2 workers. The export → 403 | T |
| 4.4 | COO Weekly returns `{collecting:true, days:n}` until 28 days after `live_since` | T |
| 4.5 | On-time % is separate per type and matches a hand-computed fixture. Over-production cost = surplus × line rate | T |
| 4.6 | The history medians match a hand-computed fixture | T |
| 4.7 | The export has the 12 sheets of §7.7. GM → 403 | T |
| 4.8 | The divergence report lists the six §8.2 cases on fixtures | T |

### Release 5: Floor stations (per division; needs P1)

| AC | Criterion | Check |
|---|---|---|
| 5.1 | Enroll codes: 10 base32 characters, single-use, 10-min expiry. 10 failures per IP in 15 min → 429. 25 failures globally in an hour invalidate outstanding codes (a valid code fails afterwards) | T |
| 5.2 | A revoked device → 401, and its SSE stream closes | T |
| 5.3 | EPF lookup: exactly one match → name; unknown or duplicated → "not found"; department mismatch → signs in and sets the flag | T |
| 5.4 | The worker session ends on submit, on Done, and after 3 min idle | T |
| 5.5 | An RWU device → 404 for SHPS jobs, 403 for reports and admin | T |
| 5.6 | Missing required E fields → 400. Client-sent Z and D values are ignored. A process value not in the division's `processes` → 400 | T |
| 5.7 | RWU minutes and totals are computed on the server. Overlapping intervals → 400. Drafts persist across worker sessions and are deleted on submit | T |
| 5.8 | EPF, name snapshot, device and mismatch flag are stored and can't be set by the client | T |
| 5.9 | **Accepting an RWU card with two `rewinding` intervals by the same worker** creates 2 output rows (line 1 and 2). Accepting again → 409. `produced_qty` counts both intervals. An `inline_inspection_run` on the same RWU job stores its quantity but does not change `produced_qty`; **after the admin switches RWU's `quantity_form_id` to `inline_inspection_run`, old and new inspection rows count alike and the RWU cards stop counting** | T |
| 5.10 | SHPS processing order → one row with minutes only. SHPS `inline_inspection_run` → quantity counted. PSU time claim → one row per staff member with the minutes split (the remainder on line 1) | T |
| 5.11 | **Review states:** a correction for a different job or form → 400. reviewing a non-pending submission or one that is not its chain's head → 409. A queried submission can't be accepted. A superseding submission starts pending. **While the correction of an accepted submission is pending or queried, the original still counts and the correction shows in `pending_qty` (computed from its payload);** accepting the correction swaps them, so the total is never double-counted or dropped | T |
| 5.12 | `pending_qty` is labelled and not counted in `produced_qty` | T |
| 5.13 | The Employee Master cache holds only `id, name, dept, epfNumber`. Setting `floor_live` without Employee Master configured → 409 | T |
| 5.14 | Tablet handovers are written with `actor_type = worker`. Recording on production's behalf by the coordinator → 409 once the division is `floor_live` | T |
| 5.15 | Floor pages have touch targets ≥ 48 px, and axe finds no serious violations | E |
| 5.16 | Flow (tablet viewport): enroll → sign in → receive → SHPS processing order + inline inspection run → submit → manager accepts → produced qty updates | E |
| 5.17 | Employee Master down: the floor shows "unavailable" while desk and portal pages load | T |

## 14. Human runbook (summary; the full steps go in the plan)

### 14.1 One-time setup

1. **GitHub repo:** `trcb69/production-dashboard` (private).
2. **Firewall (extra protection; the app already binds only to internal addresses, §4):**
   ```
   ufw allow 22/tcp
   ufw allow from 172.16.0.0/12 to any port 4300
   ufw deny 4300
   ```
   These sit alongside X2. Enable ufw only as part of X2, with SSH allowed first.
3. **Traefik:** copy the updated `custom.yaml`, which adds the `production.` router.
4. **Live:**
   - clone to `/root/production-dashboard`
   - create `.env` (`PORT=4300`, `APP_ORIGIN=https://production.standard-holdings.lk`)
   - run `npm ci --no-audit --no-fund` (the same install shdeploy uses, N9)
   - run `node cli/create-admin.js`
   - run `pm2 start server/app.js --name production-dashboard && pm2 save`
   - Check: `curl -s http://127.0.0.1:4300/api/health`.
   - After the first real browser visit, check that the logged `req.ip` is the office public IP.
5. **shdeploy:** add the registry line (§12). **Do not run `migrate.js` by hand**, even when shdeploy suggests it.
6. **Cron:** nightly backup at 01:30, and a monthly restore check.
7. **Users:**
   - desk users
   - **manager + coordinator pairs** per division (the §6.5 list), in Admin → Divisions
   - **requesters**: bulk-create them from a CSV in Admin → Users, and hand out the temporary passwords
   - teams, triage and approvers (Q2, Q7)
8. **Tell everyone:** the WhatsApp order group is replaced by the portal from the go-live date. Orders that still arrive by WhatsApp are entered by triage with **Enter on behalf**, using the time the WhatsApp message arrived (§7.2.2, Q8).

### 14.2 Keeping Zoho data fresh until Release 1b (interim, daily)

**What the interim can and cannot do (Rev 4 B3, verified 2026-09-17):** the UI exports give lines, packages, shipments and invoices, but **no shipped quantity** (`Sales_Order.xlsx` has Ordered/Invoiced/Packed/Cancelled only). Shipped quantity comes only from the SO **header** (web-app list API, the same pull used for the 2026-09-17 export). All SPS headers are about 42 pages of 200, so the pull takes the **whole list**, never a date window, and no header goes stale for being old.

1. **Once a working day (for example 08:30):**
   - **UI exports (SmartPack):** Sales Orders, Packages, Shipments, Invoices, each for the **last 30 days** (well under the 185-day and 25k-row limits). **Once a week**, the same four for the **last 185 days**, to catch late edits to older documents.
   - **Header pull (mandatory):** all SPS **sales order headers**, **bundles** and **invoice headers**, with **`tools/zoho-pull-snippet.js`** (Release 0): open Zoho Inventory in a browser, logged in as a Zoho user with a **read-only role** (D15), open the developer console, paste the snippet and run it. It uses the web-app list API (the method in `/root/exports/zoho/native/2026-09-17/README.md`), sends GET requests only, pages until Zoho reports no more pages, and downloads the three JSON files plus its `captured.json` entries. **Output names (fixed, Rev 7 N7):** `zoho-pull-so-headers.json`, `zoho-pull-bundles.json`, `zoho-pull-invoice-headers.json`; the CLI treats a file as a header pull only by these names. **`rows`** is the count after de-duplicating by Zoho id (pages shift while new records are created, README L16-17; Rev 7 N2).
2. **Save** the files to `/root/exports/zoho/native/<YYYY-MM-DD>/`. Clear old downloads first: a browser-renamed copy such as `zoho-pull-so-headers (1).json` is not a recognised name, and **the CLI fails any file whose name it does not recognise** (Rev 7.1 m4).
3. **Run** `node cli/import-zoho.js --org SPS --dir /root/exports/zoho/native/<YYYY-MM-DD>` in `/root/production-dashboard`. The folder must contain `captured.json` (§6.2 format) with the time each file was taken from Zoho (merge the snippet's entries; for the UI exports, type the time you clicked Export). **Do the header pull after the UI exports**, so the header list is the newest capture and `shipped_fresh` is true.
4. **Check** Admin → Imports: all modules are green, and the "shipped unknown" count is near zero. A red module means that file had a problem; batches already written stay, and re-running after fixing the file is safe (idempotent). Unmapped division values are listed for information only: add the division or alias in Admin → Divisions; no re-run is needed.
5. **Owner:** IT (the user). The Admin page warns when no import has run for more than 1 working day.
6. **If the header pull is skipped:** the app stays correct but cautious: shipped-based flags leave those jobs out and say "shipped: unknown"; stage 5 shows its data age (§8.2).

**Release order consequence:** Release 2's manager counters and Release 4's on-time figures depend on fresh headers. They can go live on the interim **only** if the daily header pull is actually run; otherwise they wait for Release 1b.

### 14.3 Release 1b (after its addendum is approved)

1. Create the Zoho self-client with **read-only scopes**.
2. Put the credentials in the live `.env` (never in chat).
3. Deploy.
4. Stop the daily interim import once sync shows green for 2 days **and** `shipped_fresh` has stayed true on sync alone for those 2 days (AC 1b.1).

### 14.4 Release 5

- **Prerequisites:** the P1 Employee Master change is deployed, HR has filled in EPF numbers (L2), and the admin EPF coverage for the division is at least 95 %.
- **Then:** enroll one tablet per department and switch the division to `floor_live`.

### Rollback

- **Code:** `shdeploy rollback production-dashboard`. Older code runs on the newer schema (§6.1).
- **Removing the service:** `pm2 delete production-dashboard`, remove the Traefik router, delete the folder.
- **Zoho is never written to**, so there is nothing to undo there (D15).

## 15. Testing approach

- **Server:** `node --test` + supertest, with a temp DB per file. Employee Master and the clock are injected (a fixed "now" for the Colombo boundaries).
- **Fixtures:** hand-made files with the real headers, plus a 200-SO sample taken from the real exports.
- **UI:** Playwright at desk size (1440×900) and tablet size (1024×768, touch), using `@axe-core/playwright` and `jsqr`.
- **Derived state** lives on the server only (§6.4); `shared/` holds pure display, time and text helpers, unit-tested once.
- **Performance fixture:** the full 2026-09-16 SPS mirror plus 5,000 generated jobs (AC1.28), built by a script in `test/fixtures/`.
- **Order:** test-author → implementer → test-runner → code-reviewer. security-auditor reviews Release 0, Release 1 (portal), Release 5 and the P1 change.

## 16. Risks

| Risk | Handling |
|---|---|
| Stale Zoho data (P2) | Pending links; handover-driven lists; stale-import warning; `shipped_fresh` keeps stale headers out of the flags (§6.4) |
| The interim header pull needs a Zoho web login | Read-only Zoho role; GET-only script; Release 1b replaces it |
| Entries batched at the end of the day (L10) | Click timestamps; floor tablets; drafts for shift-long forms |
| Coordinators skip "Send" | "At coordinator" for more than 2 days appears on the GM list |
| EPF gaps (L2) | Per-division gating; the admin EPF coverage % |
| Provisional config (L3, L4) | Marked in the UI; config-only fixes |
| EPF impersonation (D7) | Device binding, "Submitting as", department-mismatch flag, review, audit |
| Recording dates versus event dates | COO banner; `at_precision`; live events labelled |
| Scope for one developer | Rev 2 cuts (§3); releases ship independently |

## 17. Open questions

| # | Question | Blocks |
|---|---|---|
| P1 | ~~Employee Master access~~ **(a) read-only token, chosen 2026-09-17** (L18) | Release 5 |
| P2 | ~~Zoho freshness~~ **(a) read-only self-client sync, chosen 2026-09-17**; Release 1b addendum still to write (L19) | Release 1b |
| Q1 / Q1b | ~~Dependencies and test tools~~ approved 2026-09-17 | — |
| Q2 | User list: GM, COO and analyst accounts; who approves Stores and ITN rows | go-live; AC3.5 data |
| Q3 | ~~Domain~~ confirmed | — |
| Q4 | Day plans: optional manager input (default) or drop? | Release 2 detail |
| Q5 | OPD standard minutes (J§2.1) | L14 |
| Q6 | ~~Process lists and `counting_process` per division~~ **confirmed by the user 2026-09-18**: SHPS print/curing/packing (counts `print`); RWU rewinding/cutting/packing/personal (counts `rewinding`); PSU forming/cutting/packing (counts `packing`); all other divisions print/die_cut/pasting/packing (counts `packing`). The seeded codes are now fixed: after the first output row they can only be deactivated and replaced, never renamed | — |
| Q7 | **Who does triage** for portal orders (Mubeena's desk? the order managing desk?) | Release 1 go-live |
| Q8 | **Portal go-live:** is the WhatsApp order group switched off on day 1, or run in parallel for a transition period? Who enters orders that still arrive by WhatsApp? | Release 1 go-live |
| Q9 | Are requesters only Standard Holdings staff (internal), or also outside customers? This spec assumes **internal staff only** | portal security review |
| Q10 | RWU Internal Job Card: one card per **job**, or one per **shift** covering several jobs? This spec assumes per job, with one draft per job | RWU form |
| Q11 | Zoho order type "Make to Order (MTO)" (38 SOs): treat as **customised** (assumed) or as its own type? | report grouping only |
| Q12 | Who runs the daily header pull until Release 1b, and can a read-only Zoho user be created for it? | shipped-based flags on the interim (§14.2) |
| Q13 | The 5 divisions added in Rev 6 (PCU, Paper Cup Lid, DPU, Paper Plate, Cake Wrapper): who manages and coordinates each, and what are their stages and processes? (L20) | files for those divisions |
| Q14 | Is Saturday a working day for the freshness rule? (default: no) | Monday-morning freshness only |

## Appendix A: plan-critic Rev 1 findings → where they are fixed

*Historical record. AC numbers and some names refer to Rev 1/Rev 2 (`auto_void`, the auto-tick index and `manual_allowed` were removed in Rev 3; detection is now materialised per SO, Rev 4). The current design is the body of this document.*

| # | Sev | Fix |
|---|---|---|
| 1 | BLOCK | P1; §9.3 minimisation; AC5.11; Release 0–4 don't use Employee Master |
| 2 | BLOCK | `submission_reviews` (A); partial unique index on output from submissions; AC5.9 |
| 3 | BLOCK | `divisions.counting_process`; `output_map` per form; SHPS and PSU give minutes only; AC2.3 multi-process fixture; AC5.9 per form |
| 4 | BLOCK | P2; `link_pending` auto-resolve (AC1.2); lists driven by handovers (§6.4, AC3.1); import changes broadcast |
| 5 | BLOCK | `job_status_events`, `job_assignment_events`, `job_so_links`, `auto_void`; §7.0 state machine incl. stores/invoicing receive; §7.1 actions; AC1.12, 1.14, 1.15, 3.6 |
| 6 | MAJOR | `entered_*` columns + derived display; `zoho_so_headers` / `zoho_so_lines`; `zoho-columns.json` with real keys; source precedence; multi-line rule (AC1.18) |
| 7 | MAJOR | partial unique auto-tick index; `busy_timeout`; 2,000-row chunks; server polls import runs → SSE; untick rule (AC1.10) |
| 8 | MAJOR | `BEGIN IMMEDIATE` state machine, 409; AC2.11 |
| 9 | MAJOR | UTC normalisation; `shared/time.js`; AC0.10 |
| 10 | MAJOR | §5.4 redaction everywhere; AC4.3 widened |
| 11 | MAJOR | ufw rules in §14 before the first start; `trust proxy` limited to Docker subnets (AC0.13); 50-bit codes; global lockout (AC5.1) |
| 12 | MAJOR | Ready to hand off, In production (operators/minutes); blocker `owner_label`; `day_plans`; carry-forward of staff assignments → L16 |
| 13 | MAJOR | `floor_drafts`; session ends on submit; "Submit as"; manager output hidden when `floor_live`; `pending_qty` shown separately |
| 14 | MAJOR | `reference_approvals` (A) with defined approvers; AC3.5 |
| 15 | MAJOR | §6.1 migration policy; AC0.15; deploy = migration noted |
| 16 | MAJOR | overdue / at-risk on shipped qty; `produced_not_shipped`; AC2.4 |
| 17 | MAJOR | §3 cuts → L11–L17 |
| 18 | MINOR | "exactly one employee" |
| 19 | MINOR | health always 200 |
| 20 | MINOR | `SESSION_SECRET` removed |
| 21 | MINOR | scrypt `maxmem`, async |
| 22 | MINOR | missing `Origin` rejected; IP limit 100 |
| 23 | MINOR | SSE per-event re-check and closing; AC2.10, AC5.2 |
| 24 | MINOR | `/files` inline headers; RFC 5987; PDF preview E check |
| 25 | MINOR | `/files/:id` in AC0.6 |
| 26 | MINOR | `@axe-core/playwright`, `jsqr` listed (Q1b) |
| 27 | MINOR | single root lockfile; build-stamp test AC0.16 |
| 28 | MINOR | PSU/RWU cover variant; dispatch qty; reference visibility choice recorded; `manual_allowed`; COO over-production cost; GM at-risk |
| 29 | MINOR | `foreign_keys`; `job_id NOT NULL`; partial unique blockers; unique `supersedes_id`; generated `file_no` |
| 30 | MINOR | restore-check (AC0.11b); off-box backup → L17 |
| 31 | MINOR | enrollment code from the admin UI |
| 32 | MINOR | department-mismatch flag; EPF lookup rate limit |

**Unverified assumptions from the review, now checked on 2026-09-17:**
- **Package_ALL:** has `SO Number` and `Packing Date` but **no created time** (§8.2 uses the date). It is the merged full file, not the 25k-capped copy.
- **Shipment_ALL:** has `SO Number` and `Created Time`.
- **Invoice.xlsx:** has `Sales Order Number`.
- **Port 4300:** free.
- **Node:** v24.18.0.
- **VPS time zone:** Asia/Colombo, although the code does not rely on it.
- **`production.standard-holdings.lk`:** resolves to 45.151.122.105.
- **ITN:** means an SPS invoice (Operations Review).

## Appendix B: plan-critic Rev 2 findings → where they are fixed (Rev 3)

*Historical record; items later changed are noted in Appendix C.*

| # | Sev | Fix |
|---|---|---|
| B1 | BLOCK | Detected stages are **computed at read time** from the mirror plus the current link (§6.4, §8.2), so `auto_tick`, `auto_void` and the unique index are gone. Human correction uses `stage_overrides` (force_done / force_not_done / clear) on detected stages; manual stages use `manual_stage_events`. "Latest" = highest id. ACs 1.10, 1.17, 1.18, 1.19 |
| B2 | BLOCK | `divisions.quantity_form_id` (only one form's quantity counts); process is a select from `processes`; `line_no` NOT NULL and part of the unique key; review state machine (accepted is terminal; queried only superseded); `produced_qty` definition excludes superseded and non-accepted submissions. ACs 5.9–5.12 |
| M1 | MAJOR | `shipped_qty` = header `quantity_shipped`; shipment lines have no qty (verified). Fallback to reference qty. AC3.2, 2.4 |
| M2 | MAJOR | Binds 127.0.0.1 and 172.17.0.1 only (§4), with a retry for the bridge. AC0.13. ufw is extra protection |
| M3 | MAJOR | Startup only warns; the admin API refuses `floor_live` without Employee Master configured. AC5.13, 0.12 |
| M4 | MAJOR | DROP policy narrowed; `test:compat` mechanism via worktree + `PD_MIGRATIONS_DIR`, skipped for Release 0 (§6.1). AC0.15 |
| M5 | MAJOR | Build stamp is a content hash. AC0.16 |
| M6 | MAJOR | Seed once with INSERT OR IGNORE; the DB is authoritative; config changes ship as migrations; form versions by hash. AC0.17 |
| M7 | MAJOR | Redaction by `actor_type='worker'`, no `payload_json`, k ≥ 2, no per-job minutes (§5.4). AC4.3 seed widened |
| M8 | MAJOR | Release 1b gets its own addendum; the interim daily import procedure is written (§14.2); 1b.0 guarantees read-only |
| M9 | MAJOR | Full transition table incl. recall, rework, stores/invoicing send-back, closed-job refusal, reopen location (§7.0). AC1.16 |
| M10 | MAJOR | `owner_label` set at creation only; void semantics defined. AC2.6, 3.4 |
| m1 | MINOR | "Don't run migrate.js by hand" (§6.1, §12, §14) |
| m2 | MINOR | Dev dependencies in the live tree noted (§4.1, §12) |
| m3 | MINOR | Poll interval injectable; AC1.11 allows the interval + 5 s |
| m4 | MINOR | VIRTUAL generated columns + AC0.18 |
| m5 | MINOR | CHECK makes `worker_epf` NOT NULL for submission rows |
| m6 | MINOR | Delivery date = `shipment_date`; trimming; invoice link via `reference_number`; "lines pending". AC0.10, 1.20, 1.24 |
| m7 | MINOR | Accepted risk: the global enroll lockout can be triggered by anyone, which only delays enrolment; admins can issue a new code. Recorded here |
| m8 | MINOR | Unmatched reference rows are re-matched after every import. AC3.2 |
| m9 | MINOR | Stores and invoicing search over all open jobs is intended and read-only (§5.1) |

**New in Rev 3 (user decisions, 2026-09-17):**
- **Order portal + triage** (§7.2; `requester`, `triage`, orders tables; ACs 1.1–1.9, 1.27)
- **P1 = a** and **P2 = a**, with Zoho strictly read-only (D15)
- **Test tools approved** (D17)

## Appendix C: plan-critic Rev 3 findings → where they are fixed (Rev 4)

| # | Sev | Fix |
|---|---|---|
| B1 | BLOCK | `jobs.job_no` nullable; `POST /job-no` (set once, change with reason, audited, 409 duplicate); `to_production` refused without it; "Job no missing" badge; accepted jobs get `org = SPS` and the order's type; `order_type_aliases` maps Zoho values (verified). §6.3, §7.0, §7.1, §7.2.2. AC1.4, 1.12, 1.27 |
| B2 | BLOCK | Order state machine §7.2.0 with `expected_state` + `BEGIN IMMEDIATE`; partial unique `jobs(order_id)`; accept refused while `cancel_pending`; cancel request after accept → job banner + Cancel requested list; `reopened` removed, and after acceptance the job is the only source of status. AC1.4, 1.5, 1.8 |
| B3 | BLOCK | **Verified 2026-09-17:** `Sales_Order.xlsx` has no shipped column; package-line sums under-count Zoho's header on 1,937 of 8,231 unchanged SOs, so they are not used. `shipped_qty` = header value with `shipped_state` (fresh / stale / no_header); shipped-based flags use fresh values only and show "unknown" otherwise; the header + bundles pull is mandatory in §14.2, covers the whole list, and runs GET-only under a read-only Zoho role (D15). AC0.20, 2.4 |
| M1 | MAJOR | Per-SO facts materialised at upsert (`zoho_so_facts`, `zoho_so_rollup`), `so_key` on bundles, `zoho_picklist_sos`, `(org, so_number)` indexes, `org` filter. Performance AC1.28 |
| M2 | MAJOR | Derived state is server-only; one set of query builders; parity test over the 200-SO fixture; AC2.2 anchored to hand-computed counts |
| M3 | MAJOR | Recall returns to the undone send's `from_state`; AC1.16 covers the stores and invoicing send-back recalls |
| M4 | MAJOR | `reference_matches` (A) records matches; the entry chain and approvals are untouched |
| M5 | MAJOR | Seed is migration `002-seed.sql`; deleted rows stay deleted; fresh and old DBs converge. AC0.17 |
| M6 | MAJOR | Server-owned post-import sweep over all pending links and unmatched rows, driven by `processed_at`, run at startup; link resolution guarded by "latest row is still this pending row"; §14.2 wording fixed. AC0.21 |
| M7 | MAJOR | NULL team matches nothing; requesters must have a team. AC1.2 |
| M8 | MAJOR | Visibility matrix §7.2.4; `message_id` on attachments; multipart order and message routes; staff order route; Documents tab lists order files. AC1.6 |
| N1 | MINOR | Trust only `TRUSTED_PROXY_IPS`; untrusted forwarded headers counted and flagged. AC0.22 |
| N2 | MINOR | Overrides carry `salesorder_number` and apply only to that SO. AC1.18 |
| N3 | MINOR | Chain semantics: the original counts until its correction is accepted; who may supersede is defined. AC5.11 |
| N4 | MINOR | Quantity always stored; filtered by `source_form_id` against the current `quantity_form_id`. AC5.9 |
| N5 | MINOR | Invoicing may tick stage 11 (§10) |
| N6 | MINOR | Export is 12 sheets in both places |
| N7 | MINOR | security-auditor covers Release 1 in §11, §13 and §15 |
| N8 | MINOR | "As in Rev 2" references replaced with the actual content; Appendix A marked historical |
| N9 | MINOR | First deploy uses `npm ci --no-audit --no-fund`, as shdeploy does |
| N10 | MINOR | Enter on behalf: triage-only route, `created_via = on_behalf`, typed received time, `entered_at`, audit. AC1.29 |
| N11 | MINOR | Mixed roles decided by route; per-day quotas; SVG/HTML refused; triggers on `orders`; `order_message_hides`; "unanswered" = state `questions`; team members may request cancellation. AC1.30 |
| N12 | MINOR | `PD_MIGRATIONS_DIR` in Release 0. AC0.15 |
| N13 | MINOR | "In production" = ever sent; throughput, on-time date rule and `live_since` defined; History and export show detected stages as current facts |
| N14 | MINOR | Bundles are part of the mandatory pull; stage 5 shows its data age |
| N15 | MINOR | `{type:'day'}` at Colombo midnight; `order_queue` events for triage. AC1.31, 2.13 |

## Appendix D: plan-critic Rev 4 findings → where they are fixed (Rev 5)

| # | Sev | Fix |
|---|---|---|
| B1 | BLOCK | Freshness no longer compares database write times. Every run records `captured_at` (from `captured.json` or `--captured-at`; the CLI refuses to run without one) and `full_list`. `shipped_fresh` (per org) = the latest full-list header capture is at or after the latest package and shipment captures, and less than 1 working day old (the reviewer's simpler alternative). `zoho_so_rollup` removed. Re-imports change no mirror rows. §6.2, §6.4, §14.2. AC0.20b (a)–(f) |
| M1 | MAJOR | A `cancel_resolved` order event is written when a job is cancelled or closed while a request is pending. AC1.8 |
| M2 | MAJOR | `FACTS_RULES_VERSION` triggers a rebuild at startup; the old and the new SO are both recomputed when a row's SO changes. AC0.20, 0.23 |
| M3 | MAJOR | One requester file rule: `portal_visible` and a message that is not hidden; §10 aligned. AC1.30 |
| M4 | MAJOR | Composite FKs for processes; `quantity_form_id` validated in code; pairs created by the admin at go-live; the insert order in 002 is defined. AC0.24 |
| N1 | MINOR | `pending_qty` computed from the payload through `output_map` |
| N2 | MINOR | A supersede requires the same job and form. AC5.11 |
| N3 | MINOR | Messages in the Questions state, posting on closed orders, `expected_last_event_id` on cancel-request, guarded job status changes. AC1.22 |
| N4 | MINOR | Immediate resolution on `link_pending`; crashed runs listed in Admin |
| N5 | MINOR | GM/COO see public order messages only. AC4.3 |
| N6 | MINOR | Unmapped divisions are skipped with a warning instead of failing the run. AC0.9 |
| N7 | MINOR | §8.2 heading, six divergence cases, shdeploy pattern, chunked list reads |

## Appendix E: plan-critic Rev 5 findings → where they are fixed (Rev 6)

| # | Sev | Fix |
|---|---|---|
| B-new-1 | BLOCK | `shipped_fresh` pinned down: H = MAX(`captured_at`) of full-list header runs with status ok or warning; M = MAX(`captured_at`) of every package or shipment run that wrote rows, any status, including unfinished runs; never "highest id". Unmapped divisions no longer skip rows or change the run status. All 12 real division values mapped (5 new provisional divisions). AC0.9, 0.20b (g)–(j) |
| MAJOR-1 | MAJOR | `--captured-at` only fills missing files and is refused for header pulls; future times and missing times fail; a warning when the header capture is earlier than a movement capture. AC0.20b (k) |
| MAJOR-2 | MAJOR | `tools/zoho-pull-snippet.js` (Release 0) named; `captured.json` schema; `full_list` verified against the row count and the previous run. AC0.25 |
| MAJOR-3 | MAJOR | Full-list header rows are overwritten when any value differs. Verified that Zoho moves `last_modified_time` on shipping (7,539 of 7,539 SOs). AC0.20c |
| MAJOR-4 | MAJOR | Fixed-in-advance AC 1b.1; §14.3 step 4 waits for it |
| MINOR-1 | MINOR | Working days and holidays in Admin; `previousWorkingDay()`; Q14 (Saturday). AC0.20b (l) |
| MINOR-2 | MINOR | 15 s rebuild budget; the CLI refuses to run while the rules versions differ. AC0.23 |
| MINOR-3 | MINOR | `sh_blocked` regex widened to `^to\s+(b|be)?\s*rec` (676 real matches); variants listed; fixture value in AC0.20b (j) |
| MINOR-4 | MINOR | PCU, PCLU, DPU, PPU and CWU seeded as provisional; Q13 and LATER L20 |
| MINOR-5 | MINOR | AC rows reordered; AC4.3 formatting fixed |

## Appendix F: plan-critic Rev 6 findings → where they are fixed (Rev 7)

| # | Sev | Fix |
|---|---|---|
| B1 | BLOCK | `zoho_so_headers.captured_at`; a full-list run overwrites a row only when its capture is at least as new as the row's. AC0.20b (i) now compares every mirror row |
| B2 | BLOCK | Run status is NULL until the run finishes; H requires `finished_at`. AC0.20b (i2) |
| N1 | MAJOR | recent = `colomboDate(H) >= previousWorkingDay(today)`; AC (l) names the Sunday and Saturday cases |
| N2 | MAJOR | `rows` is the de-duplicated count; AC0.25 stubs a repeated row |
| N3 | MINOR | §14.2 step 4 wording matches the Rev 6 unmapped-division rule |
| N4 | MINOR | Stage 5 data age uses the same finished-run rule as H |
| N5 | MINOR | Update rule for header runs without `full_list` stated |
| N6 | MINOR | M NULL → fresh when H is recent |
| N7 | MINOR | Fixed snippet output names; the CLI recognises header pulls by them |
| M1 (Rev 7 review) | MAJOR | Option (a): `captured_at` and the capture guard on every mirror table; AC0.20b (i) covers all tables and excludes bookkeeping columns |
| m1 (Rev 7 review) | MINOR | Stage 5 data age uses exactly the H rule, full-list bundles runs only |
| m2 (Rev 7 review) | MINOR | `modified_at` and `source` count as mapped values; A→B→A fixture in AC (i) |
| m3 (Rev 7 review) | MINOR | Upsert batches use `BEGIN IMMEDIATE` |
| m4 (Rev 7 review) | MINOR | "Previous full-list run" defined; unrecognised file names fail; runbook note on renamed downloads |
