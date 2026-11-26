# Joint demo v0.1 Rev 4.1: demo first — a working demo, then parts added each update

**Rev 4.9, 25 Oct 2026.** Prepared by Abdul Hadhee | IT Executive.
**Status: APPROVED — build may start** (plan-critic round 5 = APPROVE-WITH-CHANGES; its N1–N4 applied in 4.5, §17). Rev 4.6 adds §18 (decisions from the S1-demo AC tagging); plan-critic on the tagging = APPROVE-WITH-CHANGES, applied in 4.7 (§19).
- Rev 4.3 → round 4 **BLOCK** on one point (no source for the end customer) + N1–N7 (`…-rev4-critic-round-4.md`).
  Response table: §16.
- Rev 4.2 → round 3 **BLOCK** on one point (Job No `pick` depends on unverified V3 projects API) + N1–N6
  (`…-rev4-critic-round-3.md`). Response table: §15.
- Rev 4.0 → plan-critic round 1 **BLOCK** (B1–B4, N1–N12; `…-rev4-critic-round-1.md`). Response table: §13.
- Rev 4.1 → round 2 **BLOCK** on one point (B1 template leftovers / Job No) + N1–N9 (`…-rev4-critic-round-2.md`).
  Response table: §14.
- **Owner, 24 Oct:** **P0 approved** (the demo gateway); Vap Poya = **Sun 25 Oct** (no working day lost).

Delta over **J31** = `wiki/specs/2026-10-21-joint-demo-v0-1.md` Rev 3.1 (APPROVED), which stays in force except where
this file says otherwise. **OP** = `wiki/specs/2026-10-18-order-portal-spec.md` Rev 3.2, **PDD** =
`2026-10-21-pd-demo-release.md`, **FR** = `2026-10-08-pd-managers-full-release.md` Rev 3.2.

State on 24 Oct (test runs today):
- Portal `/root/dev/order-portal`, `feature/s0-foundation`: OP S0 built, 150/150. Security re-audit PASS-WITH-CHANGES
  (follow-ups in `LATER.md`); code re-review round 2 **BLOCK** C1–C3 — fixes in progress (test-first).
- Dashboard `/root/dev/production-dashboard-v01`, `feature/joint-demo-v0.1`: 375 pass, 49 fail = J31 track-B tests
  written first; implementation in progress. Web has only Login and Change password pages.

## 0. Owner decisions (24 Oct; `/root/CLAUDE.md` §1)
- **E1 Demo first.** First release = a working demo of both real apps end to end; each update adds parts. Safety that
  only matters for live writes moves to the live-write update.
- **E2 Live reads, load shared.** SPS through the **API** (itexe@ read key, P1); SH through the **rizwan@ browser**
  (CDP `127.0.0.1:9333`, read-only). Conditions: the API budget must not run down; the browser must never be
  rate-blocked or signed out.
- **E3 Writes go to a stand-in**, never live Zoho, in v0.1. J31 §4 (G3 live TEST on the demo morning) leaves v0.1.
- **E4 UI = "Calm cards"** (`reports/2026-10-21-pd-demo-plan/ui-samples/project/Calm.dc.html`) for My jobs and the
  portal screens.
- J31 D1, D3–D6 stand.
- **P0 (approved 24 Oct):** the owner approved the **demo gateway** (§2) as a new demo-only local process
  (doctrine §4 hard stop "new service" cleared by the owner).

## 1. The shape

```mermaid
flowchart LR
  subgraph Portal [Order Portal :4800]
    P1[New order] --> P2[Decide: stock / production<br/>SH Kohalwila stock shown]
    P2 --> P3[Production queue: accept]
    P3 --> P4[Approve + Job No → job order]
  end
  subgraph GW [Demo gateway :4850, loopback]
    G1[(sandbox:<br/>DEMO job orders)]
    G2[GET pass-through<br/>READ-scoped token]
    G3[/demo page:<br/>advance packed · shipped · invoiced/]
  end
  subgraph Dash [Production Dashboard :4300]
    D1[Sync every 2 min] --> D2[My jobs · Calm cards]
  end
  P4 -- POST salesorders --> G1
  Portal -- GET --> G2
  D1 -- GET --> G2
  G2 -- GET only --> Z[(Live SPS Zoho API)]
  G1 -. merged into list + detail .-> D1
  Portal -- CDP GET ≤50/min --> SH[(rizwan@ browser :9333<br/>SH Zoho, read-only)]
```

An approved portal line creates a **DEMO job order in the gateway's sandbox**, cloned from a real recorded SPS job
order so it has every field the dashboard needs. The dashboard reads live SPS **plus** the sandbox through the
gateway, so the job lands in the unit's My jobs within one cycle with a DEMO chip. Nothing is written to live Zoho.

## 2. The demo gateway (demo only; P0)

Folder **`/root/dev/order-portal/tools/demo-gateway/`** (portal repo; Node built-ins + `express` +
`better-sqlite3` 13.0.3 for the read-only portal-DB lookup, both already in the portal lock: **no new dependency**). Retired when live writes start (v0.5, own delta).

**2.1 Pass-through (reads)**
- `GET /inventory/v1/<path>` → `https://www.zohoapis.com/inventory/v1/<path>` with the gateway's own access token,
  refreshed from **a READ-scoped** refresh token (`ZOHO_READ_REFRESH_TOKEN` in the gateway `.env`; read scopes only).
- Upstream allow-list: GET, host `www.zohoapis.com`, prefix `/inventory/v1/`, `organization_id=843825512` only;
  anything else refused before any network call.
- **No cache and no budget of its own** (round 1 B2: different watermarks give no cache hits). Each app's existing,
  tested cap does the budgeting (§2.6).
- **Rate:** upstream calls are **evenly spaced ≥667 ms apart** (≤90/min) through a FIFO queue — spacing, not a
  60-s window, so no burst (round 3 N2). Max wait **10 s** (leaves ~20 s of the apps' 30 s timeout for Zoho's own
  answer; round 4 N6); a request that would wait longer gets 429 in Zoho's JSON shape. Upstream 429/5xx are passed through. Sandbox POSTs make no upstream call, so
  they never wait in this queue.
- Never logs tokens or bodies; logs path, status, wait ms.

**2.2 Tokens (round 1 N1)**
- The gateway's `POST /oauth/v2/token` accepts only the configured demo client (`DEMO_CLIENT_ID`/`DEMO_CLIENT_SECRET`)
  and the two demo refresh tokens `DEMO_READ_REFRESH`/`DEMO_WRITE_REFRESH`; it returns random access tokens tagged
  read or write, valid 1 h (pattern: portal `test/helpers/fake-zoho.js:122-138,161-162`).
- `GET` needs a read or write tag; sandbox `POST` needs a write tag; wrong or missing → 401 in Zoho's shape.
- Both apps keep their required secret keys (dashboard `config.js:50-53`; portal `config.js:64-70`) filled with the
  demo values. No real Zoho secret is in either app's `.env`.

**2.3 Sandbox writes and hydration contract (round 1 B1)**
- Only `POST /inventory/v1/salesorders` and `POST /inventory/v1/salesorders/<sandbox id>/status/confirmed`; never
  forwarded. Any other non-GET → 405, logged.
- **Allow-list, built from an empty object (round 2 B1).** No recorded order is cloned. The hydrated detail holds
  **only** the keys the dashboard (`config/zoho-columns.json` `so_headers`/`so_lines`, the shape check
  `zoho-sync.js:251-265`) and the portal mirror (`sps-sync.js` detail mapping) read; the exact key list is a test
  fixture (`tools/demo-gateway/test/fixtures/allowed-keys.json`) built from those two files, and a test fails if the
  hydrated detail has any other key. Recorded details are used only to learn the shape and the id → name maps.
  (Dashboard sections: `so_headers`, `so_line_items`, `zoho-columns.json:142`.)
- **Lookups: all offline, zero upstream calls per POST (round 3 simpler alternative).** A script builds
  `tools/demo-gateway/data/maps.json` (gitignored; ids, names and item flags only, no prices or addresses) once from
  the 309 recorded details in `reports/2026-10-08-pd-zoho-study/pulls/details.json`. Checked 24 Oct: they hold 1
  customer (`Standard Holdings (Pvt) Ltd`, the SPS customer on every job order), **272 projects** (line
  `project_id` → `project_name`, e.g. `OPD5288`), **234 items** (line `item_id` → name, sku, unit, `item_type`,
  `is_combo_product`, `combo_type`, seen on 327 lines), tag options, custom-field api names, and **111 end
  customers** (`cf_order_received_from_unformatted` contact id → `cf_order_received_from` name; checked 25 Oct: they
  include TACO BELL, PIZZA HUT, Keells Super, Marriott, Spar SL (Private ) Limited).
  - Items not in the map: read from the **portal's demo DB, read-only** (`sps_items` raw JSON, path in the gateway
    config), opened with `better-sqlite3` `{readonly: true, fileMustExist: true}` and no pragmas — **not** through the
    portal's `openDb` (it creates an empty DB, `open.js:13-16`). `sps_items.raw_json` holds the list row, which
    probably lacks `combo_type`; such an item → the POST fails with Zoho's error shape and nothing is stored. In
    practice only the 234 mapped items work in v0.1 (presenter note, §12).
  - Unknown customer, project, tag option or custom field id → the POST fails the same way.
  - Live lookups move to v0.5 with live writes.
- **Projects for `pick` (round 3 B1):** the gateway serves `GET /inventory/v1/projects` (list, paged) and
  `projects/<id>` **from the map, never forwarded** (V3 is still open, OP:826). The portal's S1-demo includes an
  `sps_projects` sync through the gateway (zero upstream calls; the portal still counts each call against its own
  budget, `sps-sync.js:75-85`, `budget.js:17`, so it runs at the existing project cadence). **v0.1 uses `pick`**; `later`
  stays coded but is not shown in the demo. Whether real projects can be read through `/inventory/v1/` is a v0.5
  question (V3).
- **End customers (round 4 B1):** the gateway serves `GET /inventory/v1/contacts` (list, paged) and `contacts/<id>`
  for the 111 end-customer contacts **from the map, never forwarded**. The portal's S1-demo includes an
  `sps_contacts` sync through the gateway (zero upstream calls, but counted by the portal's budget like projects,
  so it runs **at the project cadence**, not every 5-minute cycle; round 5 N4: a 5-minute cadence would add ~288
  counted calls/day and halve the history allowance). The **placeholder contact** (`4892105000000168085`, the SH
  customer, OP §6.1:294) is **left out** of the served contacts, and hydration checks for the placeholder before
  the map lookup (round 5 N3). Screen 1's end-customer picker lists them. The SPS
  customer on the order stays `Standard Holdings (Pvt) Ltd`. On hydration, `cf_order_received_from` = the picked
  contact's name and `cf_order_received_from_unformatted` = its id. When the line uses the OP placeholder
  (`end_contact_id` = placeholder, OP P4), the name comes from the payload notes `End customer: <name>` (OP:378).
- **Served row shapes (round 4 N1):** projects rows = `project_id`, `project_name`, `status: "active"`,
  `last_modified_time` = the recording time (`2026-10-08T00:00:00+0530`); contacts rows = `contact_id`,
  `contact_name`, `status: "active"`, `last_modified_time` = the same; both paged with `page_context.page`,
  `per_page`, `has_more_page` as the portal's `fetchPage` expects (`sps-sync.js:93-97`).
- **Lookup-type custom fields (round 4 N3, round 5 N2):** four fields are lookups — the payload sends an id
  (OP:380-384): `cf_job_no` (project), `cf_order_received_from` (contact), `cf_material_to_be_used` and
  `cf_additional_other_material_t` (items). For these four, the hash stores `<api>` = the name from the map (items:
  map, then portal mirror) and `<api>_unformatted` = the id (as in the recorded details). **Every other** custom field
  (text, dropdown; e.g. `cf_portal_ref`) stores the value as sent.
- **Overlay from the OP §6.9 payload** (ids only, OP 371-399):
  - header: `customer_id`, `customer_name`; `cf_order_received_from` = the end-customer name (text, as the dashboard
    shows); `reference_number`; `date`; `status` = `draft`, then `confirmed` after the confirm call (the dashboard hides
    drafts, `line-jobs.js:134`); `shipped_status` and `invoiced_status` = the not-started values, taken from a recorded
    order that had not shipped (V-G2: confirmed from the recorded list rows before the gateway tests are written);
    `created_time` = `last_modified_time` = now; **the confirm call bumps `last_modified_time`** (the portal skips an
    order whose modified time it already holds, `sps-sync.js:179`; round 3 N3);
  - lines: `line_item_id` from the sandbox counter; `item_id`, `name`, `sku`, `unit`, `item_type`,
    `is_combo_product`, `combo_type` **from the item lookup**; `quantity`, `rate` from the payload; the other quantity
    keys the shape check requires = 0;
  - line `tags`: `tag_id`/`tag_option_id` → `tag_name` + `tag_option_name` from the offline map, so the job places by
    its line tag even under an OPD bucket header (`zoho-sync.js:266-277`, `line-jobs.js:57-60`); an unknown tag
    option id → the POST fails;
  - header `custom_fields` → `custom_field_hash` by api name from the offline map. The Portal Ref uses the stand-in
    id `DEMO_PORTAL_REF_FIELD_ID` → api name **`cf_portal_ref`** (G1 must create the real field with this api name).
  - **Job No per mode (round 2 B1):**
    - `pick`: line `project_id` and `project_name` from the project lookup; header `cf_job_no` = the project name and
      `cf_job_no_unformatted` = the project id (as in the recorded details). The dashboard then shows the picked Job No
      (`line-jobs.js:261`).
    - `later`: no project fields and no `cf_job_no`, so the portal's `job_no_to_add` flag stays (OP 364).
- **Atomic files (round 2 N7):** sandbox and counter writes go to a temp file + rename, fsync'd, **before** the 2xx.
  A start that finds a torn or unreadable sandbox file stops with an error (never starts empty).
- **Ids and numbers:** id `99` + 17 digits from a persisted counter (real SPS ids start `4892105…`; V-G1 confirms no
  real id starts `99`); number **`DEMO-<yymmdd><nnnn>` (see §21; the digits after the date come from one global counter, not a daily one)**. The counter file is never reset; numbers are never
  reused (the dashboard keys orders by number, `zoho-sync.js:289-290`; round 1 N3).

**2.4 Merge (reads)**
- **Filters (round 3 N4, round 4 N2):** the gateway implements exactly the list filters both apps send, per list
  path (`salesorders`, `bundles` `zoho-sync.js:32`, `items`, `projects`, `contacts`, and any list S1 adds) — the list
  is a test fixture **regenerated from the S1-demo code before the gateway's final review**. A list request with any
  other filter key → **400 in Zoho's shape**, never ignored, logged at error level as `filter_refused` and counted on
  the gateway's `/health` (the portal files a 400 as a quiet `upstream` error, `sps-sync.js:43`, so the gateway must
  make it loud).
- `GET salesorders` (list): sandbox orders that match the request's filters are added to **page 1 only** (page 1 may
  then hold more than `per_page`); other pages are passed through untouched, so each app's page count equals Zoho's
  (round 2 N2). Both apps sort newest first (`zoho-sync.js:166`, `sps-sync.js:90`), and sandbox orders are always
  the newest, so page 1 is their sorted place anyway.
- **List-row shape (round 2 N3):** the list row = the hydrated header cut down to the keys of a recorded SPS list row
  (`pulls/so_modified_p*.json`), including `status`, `shipped_status`, `invoiced_status` and `last_modified_time`
  (the dashboard takes these from list rows only, `zoho-sync.js:279`, `zoho-queue.js:12,86`). All ids are strings
  (`columns.js:18-19` throws on unsafe 19-digit numbers).
- `GET salesorders/<sandbox id>`: the hydrated detail. Sandbox orders never appear for another org.

**2.5 Demo page (round 1 N9)** — `GET /demo` on the gateway (loopback, through the SSH tunnel; token-protected):
lists DEMO orders and has buttons **Packed → Shipped → Invoiced**. Each step sets line and header
`quantity_packed` / `quantity_shipped` / `quantity_invoiced` = `quantity` and `status` / `shipped_status` /
`invoiced_status`, and bumps `last_modified_time` so the dashboard re-fetches (`zoho-sync.js:158-167`,
`zoho-queue.js:12,84-87`). (There is no "Checked" step; the strip detectors are package / shipment / invoice,
`006:6`, `002-seed.sql:26-30`.) The dashboard gets **no** demo button and stays GET-only.
After **Invoiced** the job is `closed` (`line-jobs.js:255`) and leaves the default open view (`job-queries.js:136`);
the demo shows the last tick by switching My jobs to **All** (`state=all`) (round 2 N4).

**2.6 Budget (round 1 B2)**
- Dashboard `ZOHO_DAILY_CALL_CAP=4500` (J31) + portal `ZOHO_DAILY_CALL_CAP=2000` (the config maximum,
  `config.js:74`) = **6,500 ≤ 7,500**, leaving 1,000 for manual checks. Nothing else uses the SPS API (0 calls in the
  30 days to 7 Oct, `reports/2026-10-07-zoho-api-limit/`).
- **Portal history in demo:** a new config `SPS_HISTORY_DAYS` (demo value **30**) stops the backfill at that age
  (today it has no cutoff, `sps-sync.js:233`). Default unset = OP behaviour. Arithmetic (round 2 N1): 2,000 − 300
  reserve (`config.js:76`) − ~1,060 steady (`budget.js:5,25`) − ~100 held for items (`sps-sync.js:22,322`) ≈ **540
  history calls/day**; ~390 SPS orders a month → ~390 details + a few list pages ≈ **1 day** for 30 days of history.
  The demo needs only recent orders (the walkthrough uses this week's jobs and new DEMO orders).
- **Warm-up:** both apps start syncing through the gateway on the **warm-up date** (§2.7) so the dashboard's history
  lane and the portal's 90-day backfill finish before the demo.
- Demo `.env`: dashboard `ZOHO_SYNC_INTERVAL_MIN=2` (default is 1, `config.js:55`; round 1 N11).

**2.7 Where it runs (round 1 B3)**
- For v0.1 nothing is deployed to a live directory and `/root/production-dashboard` is **not** created (the first
  real deploy moves to v0.2).
- The human makes three **pinned demo checkouts** with `git worktree add` at a tagged demo commit:
  `/root/demo/order-portal`, `/root/demo/production-dashboard`, gateway = `/root/demo/order-portal/tools/demo-gateway`.
  Ongoing dev work never changes the running demo; moving the demo to a newer commit is a human step.
- Supervisor: three PM2 processes `demo-gateway`, `demo-dashboard`, `demo-portal` from an ecosystem file I write
  (`tools/demo-gateway/ecosystem.demo.config.cjs`); the human starts them and runs `pm2 save` so they survive a
  reboot. No shdeploy rows. All three bind 127.0.0.1 only; viewers use an SSH tunnel.
- Each process has its own DB / data folder inside its checkout; the SPS read secret lives only in the gateway's
  `.env` (the human puts it there).
- **Demo `.env` values (round 2 N5), checked by the ecosystem file's pre-start script:** dashboard `BRIDGE_HOST=`
  (empty; default is `172.17.0.1`, `config.js:44`), `APP_ORIGIN=http://localhost:4300`; portal
  `APP_ORIGIN=http://localhost:4800`, `BRIDGE_HOST=`; both `TRUSTED_PROXY_IPS=192.0.2.1` (never matches a peer;
  security r2 R1), `NODE_ENV=production`, `DEMO_GATEWAY=1`.
- **Nothing secret or commercial in git:** `tools/demo-gateway/.env`, `data/` (sandbox, counter, maps) are
  gitignored; no recorded detail is copied into the repo.
- **Visible demo mode:** both apps' `/health` and start log say `DEMO MODE (gateway)` when `DEMO_GATEWAY=1`, so a v0.2
  live deploy cannot inherit it unseen; the v0.2 deploy package checks that `DEMO_GATEWAY` is unset.
- **Warm-up date:** the human starts the three processes once tracks G and B (server side) pass their reviews
  (target **Fri 30 Oct**), and at least 3 days before the demo. The UI parts arrive later by moving the pinned
  checkouts (DBs kept).

## 3. SH reads through the browser (portal; OP S2 reduced)

OP §8.3 rules apply **as written** (`cdp` on a robots.txt tab with the `1+1` probe, GET only, allow-list, ids
`^\d{1,25}$`, **≥1,200 ms apart (≤50/min), ≤40 per cycle, ≤6,000/day**, 60 s timeout, never navigate / close / sign
in or out / kill Chrome, persisted stop states `login_required` and `rate_paused`). Reductions:
- **Stock only:** `items/<id>` for SH items matched to lines on the Decide screen (≤20 per cycle, cached 5 min) and
  one `locations` read per day. No SH lists (V12 not needed).
- **Locations (OQ5, round 1 N8):** the admin view lists every location from the `locations` read with a tick box; the
  owner picks the Kohalwila stock locations **before the rehearsal**. Until picked, stock shows "unknown". (A name
  rule would also catch "SPS Kohalwila Factory".)
- **OQ20 = yes:** no full SH pull runs while the reader runs.
- **:9333 sharing (round 1 N12):** the 200/min ceiling is not enforced in code. Rule for demo week: the portal reader
  (≤50/min) plus at most one other tool at a time (e.g. abdullah-report, ~50/min); no full pulls. Stated as a risk.
- Matching per OP §6.4 (name, then SKU, from the 18 Oct catalogue import); "unknown" when unmatched, stopped, or >30
  min old.
- ACs: OP AC55–AC61. The dashboard reads no SH data.

## 4. Portal v0.1 = "S1-demo" (OP S1 split)
- **In:** OP §4.3 screens 1, 2, 3 (with SH stock), 4, 6 (users, divisions/people, Sync view, SH locations, **ledger view with L15/L16/L27 — §18 F3**) —
  vanilla HTML/JS (OP §4.3), Calm cards. OP §5 transition rules in full (role + division, `version` 409, one
  transaction with event + audit) for the order and line states up to `so_created`. On approve: OP §7.2 pre-checks
  **as written** (forced delta + ref check, against the gateway), then `so_create` + `so_confirm` to the gateway,
  recorded in the `zoho_writes` ledger (OP schema).
- **Restart rule in v0.1 (round 1 N5; exact rule in §18 F4):** a line found in `so_writing` with an `in_flight` write at startup → `so_unknown` (a never-sent `pending` write → `accepted`, OP AC38), never auto-retried;
  shown in the admin view.
- **Way out of `so_unknown` (round 2 N6, round 3):** OP **L15** and **L16** are **in v0.1**, as written (OP:273-274):
  L15 = admin enters the DEMO order id, a GET of it returns this line's ref → `so_created` (links the stored order,
  no second one); L16 = forced delta + mirror find no ref → `accepted` for a new approve. **L15 onto a draft** (the
  crash fell between create and confirm) → `so_created_draft` **and queues an `so_confirm` row** at once (L27 alone
  needs a failed confirm, OP:276; the dashboard hides drafts, `line-jobs.js:139`) (round 4 N4). The admin view lists the
  sandbox orders by Portal Ref to make L15 easy.
- **Writes guard:** `ZOHO_WRITES_ENABLED=true` only with `DEMO_GATEWAY=1` and a loopback Zoho base (R4-AC2). This
  refusal stays in code until the v0.5 safety ACs pass.
- **Moved to v0.5 (OP unchanged):** reconciliation beyond the restart rule, Reconcile refs (L29), kill switch UI,
  `docs/RESTORE-RUNBOOK.md`, S1b, the restore_pending clear path (LATER.md R7).
- **AC tagging:** test-author tags every OP S1 AC `v0.1` or `v0.5`; that list goes to **plan-critic before the S1
  build starts**.
- Out (J31): bought-in lines, per-line decisions, new item/customer, images, weekly report.

## 5. Dashboard v0.1
- J31 §2 scope: ready-to-run, set-up script, migration 007, display filter, My jobs (**Calm cards**), Unassigned,
  loopback listener. The 49 committed tests define done.
- **DEMO chip** on a job whose SO number starts `DEMO-`; such a job carries a Portal Ref, so it is always shown
  (J-AC2). No schema change.
- **Gateway base URL:** `server/zoho/client.js:3-4` hard-codes the Zoho URLs. New config `ZOHO_API_BASE` /
  `ZOHO_TOKEN_URL`, accepted only with `DEMO_GATEWAY=1` and an `http://127.0.0.1:<port>` value; otherwise refused at
  start. `NODE_ENV=production` stays on in the demo (security r2 R1).

## 6. Acceptance criteria (new in Rev 4.1)
- **G-AC1** Starts only on 127.0.0.1; refuses an upstream request that is not GET to `www.zohoapis.com/inventory/v1/…`
  with org `843825512`, before any network call.
- **G-AC2** No code path forwards a non-GET: a test sends every HTTP method to every route and asserts zero upstream
  non-GET calls. (The token itself is created with read scopes only by the human, P1; whether Zoho lets the gateway
  read a token's scopes at start is unverified, so that check is not an AC.)
- **G-AC3** Pacing: upstream calls ≥667 ms apart (≤90 in any 60 s); a request that would wait >10 s gets 429 in
  Zoho's JSON shape.
- **G-AC4** Token route: only the demo client and demo refresh tokens; a read-tagged token on a sandbox POST → 401.
- **G-AC5** `POST salesorders` + confirm with an OP §6.9 payload → a sandbox order with zero upstream calls; any other
  non-GET → 405. Ids `99…`, numbers never reused across a restart.
- **G-AC6** Hydration: (a) the hydrated detail has only allow-listed keys (fixture test); (b) a dashboard-repo test
  feeds gateway-produced list row + detail fixtures through the dashboard's **real sync** against its fake Zoho
  (the shape check and `divisionTag` are closures inside `startZohoSync`, `zoho-sync.js:251,266`, so not imported)
  and asserts: no `bad_shape`, a job exists, `division_source='tag'`, `job_no` = the picked project name (`pick`) or
  empty (`later`), `customer` = the end-customer name, no Bundle step for a non-combo item.
- **G-AC7** Merge: sorted insertion honouring `last_modified_time` and sort; correct `page_context`; never for
  another org.
- **G-AC8** `/demo` advance steps set the quantities and statuses and bump `last_modified_time`; without the token →
  401.
- **G-AC9** No token or response body in the gateway log (checked in a test).
- **R4-AC1** Dashboard: `ZOHO_API_BASE` only with `DEMO_GATEWAY=1` and a loopback URL; else the start stops.
- **R4-AC2** Portal: `ZOHO_WRITES_ENABLED=true` without `DEMO_GATEWAY=1` + loopback base stops the start;
  `DEMO_GATEWAY=1` works with `NODE_ENV=production` (no `ZOHO_FAKE_URL`, which stays test-only).
- **R4-AC3 (cross-app e2e)** Harness `test/e2e/joint-demo.spec.js` in the dashboard repo starts a fake upstream,
  the gateway and both apps (portal path from `PORTAL_REPO`) on test ports. Sales order for an **OPD-bucket header**
  with a MacPro-tagged line → Production → accept → approve with Job No → signed in as the **MacPro coordinator**,
  the job is in My jobs with the DEMO chip within one cycle, showing the **picked Job No** and the **end customer
  TACO BELL** (a real key customer from the map; round 4 B1);
  the item's route starts at MACPRO (set-up script routes); Job card tick and Send next work; three `/demo` steps
  tick Packed, Shipped, Invoiced, the last one seen in My jobs → All.
- **R4-AC4** SH stock on Decide: OP AC55–AC61 with the fake CDP; a matched line shows stock "as of HH:MM" at the
  picked locations; no picked locations → "unknown".
- **R4-AC5** Portal `SPS_HISTORY_DAYS=30`: the backfill stops at orders older than 30 days and reports complete.
- **R4-AC6** Gateway sandbox/counter: a write killed between temp file and rename leaves the previous file intact; a
  torn sandbox file stops the start.
- **R4-AC7** With `DEMO_GATEWAY=1`, each app's `/health` and start log say `DEMO MODE (gateway)`.
- **G-AC10** A sandbox POST + confirm makes **zero** upstream calls (all lookups from the map / portal mirror); an
  unknown item, project, tag option or custom field id → Zoho-shape error, nothing stored.
- **G-AC11** `GET projects` / `projects/<id>` are answered from the map with zero upstream calls; the portal's
  `sps_projects` sync fills from them and the Approve screen's Job No picker lists them.
- **G-AC12** A list request with a filter key outside the fixture list → 400, zero upstream calls.
- **G-AC13** The confirm call bumps `last_modified_time`; the portal mirror then shows `confirmed`.
- **G-AC14** `GET contacts` / `contacts/<id>` answered from the map with zero upstream calls; the portal's
  `sps_contacts` sync fills from them; a DEMO order for TACO BELL shows `cf_order_received_from = "TACO BELL"` with
  its id in `_unformatted`; a placeholder line takes the name from the `End customer:` note; the placeholder contact is not in the served list.
- **G-AC15** Lookup-type fields: `cf_job_no` stores the project name with the id in `_unformatted`; a text field
  (`cf_portal_ref`) stores the value as sent; the two material fields store item names with ids in `_unformatted`.
- **R4-AC8** L15 onto a draft order queues an `so_confirm`; after it the line is `so_created` and the job shows on the
  dashboard.
- **Tests run (round 1 N10):** the portal's `npm test` glob is extended to `tools/demo-gateway/test/*.test.js`.
- J31 J-AC1–J-AC8, J-AC10 and the OP S1 ACs tagged `v0.1` apply. J-AC9 is replaced by R4-AC2 + G-AC5.

## 7. Versions

| Update | Not before | Adds | Waits on |
|---|---|---|---|
| **v0.1 Working demo** | **target Mon 9 Nov**, latest Thu 12 Nov | Portal S1-demo + SH stock; dashboard My jobs (Calm cards); gateway; end-to-end DEMO hand-off on live reads | P0, P1, P3, P4; reviews |
| v0.2 | Sun 15 Nov | First real deploy of the dashboard (live dir, shdeploy); per-line decisions; bought-in / made-for-stock lines; Send selected, attention sort, customer search, drawer timeline, GM view | own delta + plan-critic |
| v0.3 | Sun 22 Nov | Approval-only website sign-in (PDD §4, migration 008) for both apps; public address; fresh dashboard DB + re-sync | PDD §4 reviews; DNS + Traefik; DD-5 |
| v0.4 | Sun 29 Nov | All units and routes (Q0–Q14); wait-limit flags; weekly review report | managers' answers |
| v0.5 | Sun 6 Dec | Live writes, one division: OP S1 safety parts (§4), G1–G3 incl. the live TEST job order; how the gateway is retired; a **fresh portal DB** (or a purge of `99…` ledger rows) before pointing at live Zoho (round 2 N8) — **own spec delta** | that delta's APPROVE; G1–G3 |
| v1.0 | at the v0.5 review | as J31 §6 | as J31 §6 |

## 8. Build plan for v0.1 (working days from Mon 26 Oct; Saturday half day; an estimate, not a promise)

| Track | Steps | Days |
|---|---|---|
| **G Gateway** (after P0) | tests → pass-through, tokens, pacing → sandbox + hydration + merge → `/demo` page → ecosystem file | 3–4 |
| **A Portal** | S0 round-2 fixes (C1–C3) → re-review → `DEMO_GATEWAY` config + `SPS_HISTORY_DAYS` → S1-demo AC tagging → plan-critic → tests → build → screens (Calm cards) → SH stock reader | 9–12 |
| **B Dashboard** | the 49 tests green → base-URL config → reviews (code, security, db-migration for 007) → My jobs Calm cards + DEMO chip | 6–8 |
| **C Gates** | warm-up start (human, after G + B server side) → R4-AC3 e2e → final reviews → demo run package (release-captain) → rehearsal with 3 sample orders | 2–3 |

Critical path = A then C: **11–15 working days → about Mon 9 Nov to Thu 12 Nov.** Vap Poya is Sun 25 Oct (owner),
so no working day is lost; Il Poya (late Nov) affects v0.4 only. **Check point Fri 30 Oct:**
gateway built, dashboard server side green and reviewed, warm-up started. If missed, the demo date moves by the slip;
there is no snapshot fallback (round 1 B4) — **v0.1 waits for P1**.

## 9. Preconditions (owner)
- **P0** Approve the demo gateway (§2) — **given 24 Oct**.
- **P1** SPS read key (read scopes only) into the gateway `.env` — before the warm-up (Fri 30 Oct).
- **P3** key-customer account names; **P4** demo account names and unit owners (J31 §9).
- **Demo checkouts + PM2** (§2.7): the human creates the worktrees, starts the processes, `pm2 save`.
- **SH browser:** keep rizwan@ signed in; no full SH pulls in demo week; pick the Kohalwila locations before the
  rehearsal.
- J31 P2 (write key, Portal Ref field) is not needed for v0.1.

## 10. Non-goals for v0.1
Any write to live Zoho · public address · first real deploy · SH reads by the dashboard · SH lists · snapshot mode ·
J31 §10 items.

## 11. Rollback
`pm2 delete demo-gateway demo-dashboard demo-portal`, `pm2 save`; remove `/root/demo/*` worktrees. Sandbox file and
demo DBs are disposable. Nothing in live Zoho to undo.

## 12. Risks
- **Hydration fidelity** — guarded by G-AC6 and R4-AC3 (dashboard's own code judges the DEMO order).
- **New local process** — P0; demo-only; PM2 from pinned checkouts; retired at v0.5.
- **P1 late** — the warm-up and the demo slip by the same amount.
- **SH session dies** — reader stops (`login_required`), Decide shows "unknown"; the owner signs in again; no retries.
- **:9333 shared by other tools** — rule in §3; not enforced in code.
- **Three tracks, one review queue** — reviews per slice.
- **Presenter notes (round 3 N5):** project names in the picker come from the 8 Oct recording (new projects after 8
  Oct are not listed in v0.1); with 30 days of history most price pre-fills have no basis, so many demo lines show
  the price-changed flag; only the **234 mapped items** can be approved in v0.1 (most of the 2,708 catalogue items
  are refused at approve, round 4 N7) — the rehearsal and demo use mapped items; end customers are the 111 in the
  recording.
- **Combo items (round 3 N6):** `combo_type` is taken from recorded SO lines, not item detail; G-AC6 also covers one
  combo item from the map.

## 13. Response to plan-critic round 1
| Finding | Change |
|---|---|
| B1 | §2.3 hydration contract from a real recorded detail; §2.5 steps Packed/Shipped/Invoiced with quantities, statuses, modified time; G-AC6; R4-AC3 coordinator + OPD-bucket header |
| B2 | Cache and gateway budget removed; pacing queue instead of 429 (§2.1, G-AC3); caps 4,500 + 1,500 = 6,000 ≤ 7,500 (§2.6); `SPS_HISTORY_DAYS=90` (R4-AC5); warm-up scheduled |
| B3 | P0 added (§0, §9); §2.7 runtime: pinned demo worktrees, PM2 by the human, `pm2 save`, no live dir, warm-up Fri 30 Oct |
| B4 | Snapshot mode dropped; v0.1 waits for P1 (§8, §10) |
| N1 | §2.2 token route with demo client and tagged read/write tokens; portal write client is S1 code |
| N2 | G-AC2 read-scope check |
| N3 | §2.3 persisted counter, dated numbers, never reused; §2.4 sorted insertion |
| N4 | Stand-in field id → api_name `cf_portal_ref`; G1 must use that api name |
| N5 | AC tagging to plan-critic before S1 build; R4-AC2 kept until v0.5; OP §7.2 pre-checks in; `so_writing` restart rule |
| N6 | v0.5 gateway retirement = own delta |
| N7 | Dates re-estimated (target Mon 9 Nov, latest Thu 12 Nov); warm-up dated; Poya noted |
| N8 | Locations picked from a list before the rehearsal |
| N9 | Advance on the gateway's `/demo` page; dashboard stays GET-only |
| N10 | Gateway tests in the portal `npm test` glob; cross-app e2e harness named |
| N11 | Pacing instead of gateway 429s; interval 2 in the demo `.env` |
| N12 | :9333 sharing rule in §3, stated as a risk |

## 14. Response to plan-critic round 2
| Finding | Change |
|---|---|
| B1 | §2.3 rewritten: allow-list from an empty object (fixture-tested), no cloning; item/contact/project lookups at POST; Job No per mode (`pick` project fields + `cf_job_no`/`_unformatted`; `later` none); combo fields from the item; header statuses reset; G-AC6 and R4-AC3 check Job No, `division_source='tag'`, customer |
| N1 | Portal cap 2,000; `SPS_HISTORY_DAYS=30`; arithmetic in §2.6 |
| N2 | Sandbox rows on page 1 only, no re-paging (§2.4) |
| N3 | List-row shape from a recorded list row; ids as strings (§2.4) |
| N4 | Invoiced seen in My jobs → All (§2.5, R4-AC3) |
| N5 | Demo `.env` values checked at pre-start; gitignore; DEMO MODE in health/log; v0.2 package checks it (§2.7, R4-AC7) |
| N6 | L16 in v0.1 (§4) |
| N7 | Atomic sandbox/counter writes; torn file stops the start (§2.3, R4-AC6) |
| N8 | v0.5 delta: fresh portal DB or purge `99…` rows (§7) |
| N9 | G-AC6 via the dashboard's real sync on fixtures, not imports |
| Simpler alternative | Adopted: offline id→name maps from recorded details + on-demand item/contact/project GETs; no startup/daily lookup |

## 15. Response to plan-critic round 3
| Finding | Change |
|---|---|
| B1 | v0.1 uses `pick`; the gateway serves projects from the offline map (272 recorded projects), never forwarded; portal `sps_projects` sync through the gateway; G-AC11. No V3 dependency in v0.1 |
| N6 (round 2, partly) | L15 and L16 both in v0.1, as written (§4) |
| N1 | All POST lookups offline (map + portal item mirror, read-only): zero upstream calls per POST; G-AC10 |
| N2 | Even spacing ≥667 ms; POST never queues upstream (§2.1) |
| N3 | Confirm bumps `last_modified_time`; G-AC13 |
| N4 | Fixed filter list; unknown filter → 400; G-AC12 |
| N5 | Presenter notes in §12 |
| N6 | `combo_type` from recorded lines; G-AC6 covers one combo item |
| Nit | `so_line_items` named |

## 16. Response to plan-critic round 4
| Finding | Change |
|---|---|
| B1 | 111 end customers in the map; gateway serves `contacts` from the map; portal `sps_contacts` sync; placeholder name from the notes; R4-AC3 uses TACO BELL; G-AC14 |
| N1 | Projects and contacts row shapes + paging defined (§2.3) |
| N2 | Filter fixture per list path, regenerated from S1 code; `filter_refused` at error level + on `/health` |
| N3 | Lookup-type fields (`cf_job_no`, `cf_order_received_from`) store name + `_unformatted` id; specific rule wins; G-AC15 |
| N4 | L15 onto a draft queues `so_confirm`; R4-AC8 |
| N5 | `better-sqlite3` named (in the lock); readonly + fileMustExist, not `openDb` |
| N6 | Max queue wait 10 s |
| N7 | Presenter note: only the 234 mapped items can be approved |

## 17. Response to plan-critic round 5 (APPROVE-WITH-CHANGES)
| Finding | Change |
|---|---|
| N1 | G-AC3 set to 10 s and even spacing |
| N2 | Four lookup fields listed; every other field stored as sent; G-AC15 |
| N3 | Placeholder contact left out of the served list; checked before the map lookup; G-AC14 |
| N4 | Contacts sync at the project cadence; budget wording corrected |

## 18. Decisions from the S1-demo AC tagging (Rev 4.6; list: `2026-10-25-portal-s1-demo-ac-tagging.md`)
| Flag | Decision |
|---|---|
| F1 | The **portal** gets the same two settings as the dashboard: `ZOHO_API_BASE` and `ZOHO_TOKEN_URL`, accepted only with `DEMO_GATEWAY=1` and an `http://127.0.0.1:<port>` value; `ZOHO_FAKE_URL` stays test-only (`config.js:52`). R4-AC2 tests both |
| F2 | OP §7.6 **confirm settle** (GET the order by id after a confirm timeout) is in v0.1, so a line cannot sit unseen in `so_created_draft`; AC30d tagged `v0.1-modified` |
| F3 | Screen 6 (Admin) includes the **ledger view** with L15, L16 and Retry confirm (L27) |
| F4 | Both rules hold: OP AC38 as written (a never-sent `pending` write → `accepted`) **and** the Rev 4.5 restart rule (`so_writing` with an `in_flight` write → `so_unknown`) |
| F5 | In v0.1 the restore_pending **set** stays (CLI + admin), and the admin view says plainly "clears in v0.5"; it only blocks writes |
| F6 | The rehearsal uses the shared fulfilment login (owner 17 Oct). LATER **R6** is met in v0.1 by a documented deactivate-and-recreate rotation (no new route) |
| F7 | Stale SH stock threshold = **30 min** everywhere (AC61 text aligned) |
| F8 | NP-4 in v0.1: the API refuses `item_request_id` and customer-request input with 422 until S3/S4 |
| F9 | NP-5 in v0.1: a failed pre-check read writes nothing and leaves the line `accepted`, with the reason shown |
| F10 | Portal S1 test fixtures use ids that exist in the gateway map fixture, and the R4-AC3 e2e is the final check |
| Migration | The portal's `sps_projects` and `sps_contacts` tables come in a new portal migration **002** (001 is never edited again once applied); db-migration-guard reviews it |

## 19. Response to plan-critic on the tagging (APPROVE-WITH-CHANGES)
| Finding | Change |
|---|---|
| N1 | AC30d / §18 F2: a **5-minute `so_confirm`-only settle loop** (no `so_create` reconciliation) re-reads draft orders; still draft in two reads ≥10 min apart → confirm `failed`, which offers L27. Tested with a fake clock |
| N2 | §18 F1: with `DEMO_GATEWAY=1`, **both** `ZOHO_API_BASE` and `ZOHO_TOKEN_URL` must be set and both loopback, otherwise the start stops; R4-AC2 tests each half on its own (same rule for the dashboard, R4-AC1) |
| N3 | AC40 / L16 (v0.1-modified): if the forced delta or ref check **cannot finish** (lease timeout, gateway 429, 5xx, network) → **409**, the line stays `so_unknown`, the write row is unchanged. "Absent" only after a complete check |
| N4 | §4 lines now point to §18 F3 (ledger view) and F4 (restart rule) |
| N5 | G1 folded into AC26: one happy-path and one wrong-role/wrong-division case per allowed row (OP:216-220). **G3 is a v0.1 AC:** `/api/health` shows `draftsAwaitingConfirm` and the admin view shows a banner when it is >0. G2 stays v0.5. G4: synthetic fixture for AC45 |
| N6 | W9: "writes" = every state-changing POST/PUT/PATCH/DELETE under `/api` except login/logout; an approval counts in both limits; key = the user id after auth; reuses `makeLimiter` (`auth/rate-limit.js:3`); 429 with a `rate_limited` error |
| N7 | F6: one test that deactivating the shared user ends its sessions (`sessions.js:25,46`) |

## 20. Rev 4.8 — from the gateway code + security reviews (25 Oct)
- **Materials (code C1):** item-type custom fields (`cf_material_to_be_used`, `cf_additional_other_material_t`) need a
  **name only**: map `items` → a new map `materials` (material id → name pairs recorded in `custom_field_hash`
  `<api>`/`<api>_unformatted`; 102 distinct ids in the recording) → the portal mirror's `sps_items.name`. The six-flag
  rule applies to `line_items` only.
- **Bundle step (code W1; main session decision, demo realism):** 231 of the 234 mapped items are combo assemblies
  whose strip has a Bundle step ticked only from `/bundles` (`line-jobs.js:224-239, 435-438`). The gateway therefore
  keeps **sandbox bundles**: the `/demo` page gets a **Bundled** step (before Packed) that creates a bundle record for
  the order's combo lines, merged into `GET bundles` (page 1 only, same filter rules) with the shape of a recorded
  bundle row; `packed` also sets `quantity_picked` so the Pick list step ticks. The demo order of steps is
  Bundled → Packed → Shipped → Invoiced; R4-AC3 gains the Bundled tick for a combo item.
- **Security S1/S2 (must be fixed before the real read key goes into `.env`):** the upstream query is rebuilt from
  the validated values with `organization_id` fixed (never the raw `url.search`); both upstream fetches use
  `redirect: 'error'` and a 20 s timeout.

## 21. Rev 4.9 — DEMO order number format (gateway code review round 2, C1)
- The dashboard links bundles (and its re-fetch queue) to orders through `soKey()` (`shared/text.js:7-11`, regex
  `^([A-Z]+-\d+)(\s*-.*)?$`). `DEMO-JOBORDER-<yymmdd>-<nnn>` gives `null`, so a DEMO bundle never ticks the Bundle step.
- **New format: `DEMO-<yymmdd><nnnn>`** (letters, one hyphen, digits only; e.g. `DEMO-2610250001`), never reused (the
  counter rule stands). It keeps the `DEMO-` prefix the DEMO chip uses (§5). Bundle `reference_number` =
  `<order number> - F`, so `soKey()` returns the order number.
- The gateway's tests check this with a verbatim copy of the dashboard's `soKey` regex (contract test), not their own
  rule. The shared dashboard `soKey` is **not** widened (it parses every real bundle reference).
- **Step labels (dashboard review round 2, W2; lead decision 25 Oct):** the dashboard strip keeps the SPS document
  names from PDD §3 — package = "Packed (SmarTAG)", shipment = "Checked (Standardization)", invoice = "Invoiced (to
  SH)". The gateway `/demo` buttons use the same visible labels (Bundled · Packed (SmarTAG) · Checked
  (Standardization) · Invoiced (to SH)); the underlying steps stay bundled/packed/shipped/invoiced. Wherever this
  spec says "Shipped" as a visible label, read "Checked (Standardization)".

## 22. Rev 4.10 — source of the SH item list (S1-demo review D3, 27 Oct)
- **Gap:** §3 says "No SH lists" and matching "from the 18 Oct catalogue import", but that catalogue holds SPS items
  only. Nothing fills `sh_items`, so `matchShItems` links nothing and Decide always shows "stock unknown" (R4-AC4
  cannot pass). Found by the migration and security reviews of the S1-demo build.
- **Source (lead decision):** the SH sales-order export already on the VPS,
  `/root/exports/zoho/native/2026-10-18/sh/SH_Sales_Order_2026-09-19_2026-10-18.xlsx` (columns `Product ID`, `Item
  Name`, `SKU`): 1,656 distinct SH items, 772 with a SKU. A one-off step outside the repo turns it into
  `sh-items.json` = `[{"id","name","sku"}]` (id, name and SKU only; no prices, customers or quantities).
- **CLI `node cli/import-sh-items.js --file <sh-items.json>`** (no new dependency, no Zoho or CDP call):
  - The file is a JSON array of at most 20,000 objects and at most 5 MB. Anything else is refused before any write.
  - Per row: `id` must match `^\d{1,25}$`, `name` must be a non-empty string of at most 300 characters after trim,
    and `sku` is a string of at most 100 characters or empty/null. Other keys are ignored. Bad rows are skipped and
    counted.
  - In one transaction: upsert into `sh_items` (insert new ids; update name and SKU of known ids; never delete),
    then run `matchShItems`, then write one audit row `sh_items.imported` with the counts.
  - It prints only counts: read, inserted, updated, unchanged, refused, links made.
  - Idempotent: a second run of the same file inserts 0, updates 0 and adds no links.
- **Coverage limit (stated risk):** only SH items sold in that 30-day window can match; any other item shows
  "unknown", as §3 already allows. Refresh = a newer export plus the same CLI. Replaced at v0.5 by SH lists or the SH
  API.
- **Run by the human** against the demo database, as a step in the demo run package after the first portal start
  (migration 002 applied), before the rehearsal.
- **ACs:**
  - D3-AC1: the import fills `sh_items` and makes `item_links` for a line whose SPS item matches by name, then SKU;
    Decide then reads that SH item's stock through the reader.
  - D3-AC2: a second run changes nothing.
  - D3-AC3: bad rows are counted and skipped; a non-array, oversize or unreadable file writes nothing.
  - D3-AC4: one audit row carries the counts; the output holds counts only.
- **§22 amendments after plan-critic (APPROVE-WITH-CHANGES, 27 Oct):**
  - **Checked 27 Oct (offline):** every `Product ID` cell is text (7,923 of 7,923 lines), each id is 19 digits, and
    all 439 SH `item_id`s in the recorded SH order details (`…/2026-10-18-customized-catalogue/pulls/unused-live/
    sh-so-detail-partial/`) appear among the export's 1,656. So `Product ID` is the SH `item_id` the reader needs.
  - **C1 ids are strings:** `id` must be a JSON string (`typeof id === 'string'`) and match `^\d{1,25}$`. A number is
    a refused row, because 19-digit ids are above 2^53 and would be rounded. The conversion step aborts if any
    `Product ID` cell is not text. New D3-AC5: a 19-digit id round-trips exactly into `sh_items.item_id`, and a
    numeric id is counted as refused.
  - **C3 the actual match rule** (`sh-match.js:23-24`): link by normalised name when exactly one SH item has that
    name; else, only when no SH item has that name, by SKU when exactly one SH item has that SKU; else no link.
    D3-AC1's test covers both: two SH items with the same name give no link, and two with the same SKU give no
    link.
  - **C4 conversion:** a short script `scripts/sh-items-from-export.py` kept beside the demo run package (not in the
    portal repo). It dedupes by id, keeps the name and SKU from the row with the latest `Order Date`, and prints
    how many ids had more than one name (5 in the 18 Oct export). The refresh is the same script plus the same CLI.
  - **C2 undo:** a wrong link is removed with `DELETE FROM item_links WHERE sps_item_id = ?` on the demo database;
    the next reader cycle re-matches it (`sh-reader.js:206`). Full revert of §22: delete all rows of
    `item_links`, `sh_stock` and `sh_items` on the demo database. The CLI prints the links made split by
    `matched_by` (name / sku), so the owner can check the SKU links before the rehearsal.
  - **N1:** the CLI may run while the portal is up (WAL, `busy_timeout`, as `create-admin.js`). `matchShItems` uses
    `INSERT OR IGNORE` into `item_links`, so a reader cycle and the CLI cannot collide on the primary key.
  - **N2:** if the SPS item sync has not finished when the CLI runs, "links made" is 0. That is not a failure: the
    reader links them on its next cycle. The run package says so.
  - **N3:** §22 overrides §3 lines 235 and 242: SH items come from this import, not from SH lists or the 18 Oct
    catalogue.
  - **N4:** D3-AC2's test holds the SPS items fixed between the two runs.
