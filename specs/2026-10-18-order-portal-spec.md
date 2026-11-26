# Customized-Items Order Portal: trial build spec (Rev 3.2)

Prepared by Abdul Hadhee | IT Executive. Date: 18 Oct 2026.
Status: **Rev 3.2.** This revision applies the coordinator's decision after plan-critic round 4.
- Dev repo: `/root/dev/order-portal` (does not exist yet).
- Service: `order-portal`, port **4800**.

Not used as input: anything in `/root/Project Management/archive/`, OP-xx notes, and the production-dashboard add-on/extension design. This is a fresh design built on the Zoho API.

## Change log
- **Rev 3.2 (18 Oct)**: coordinator decision after plan-critic round 4.
  - **Removed:** `data/audit-highwater`, automatic restore detection, and the restore-detection risk. Plan-critic round 4 found two problems with it:
    - it misses the most likely restore (copying the whole `data/` folder);
    - it needed four more cases specified.
  - **Kept:** `restore_pending`, now an **admin toggle** stored in `settings`.
    - While it is set, writes are off whatever the env says.
    - It survives restarts.
    - Only an admin can clear it, and only after a completed Reconcile refs run.
    - An offline CLI (`npm run restore-pending -- on|status`) can set it on the DB file **before** the service starts. The web UI can't do that, because the restored DB holds the old value.
  - **§7.5** is now a mandatory printed runbook: set `restore_pending` (or `ZOHO_WRITES_ENABLED=false`) **before** restarting on a restored DB → Reconcile refs → clear.
  - **AC46** now tests the toggle, not file detection.
  - **OQ24** stays: who restores, and that they follow the runbook.
- **Rev 3.1 (18 Oct)**: plan-critic round 3.
  - C1: L28 (ref found before POST) and L29 (Reconcile refs); `declined`/`cancelled`/`stock` matches are listed, not moved; O8 is checked in the same transaction; AC26 aligned; AC46c added.
  - n1: forced delta waits at most 30 s for the lease (AC33c).
  - n2: writes-off is mandatory after a restore.
- **Rev 3 (18 Oct)**: plan-critic round 2.
  - R1: status rule + `so_confirm`.
  - R2: `project_create` keyed by name; `waiting_project`.
  - R3: placeholder = "no customer" for pre-fill; `last_rate_basis`.
  - R4: `cf_portal_ref` in the mirror; forced delta + mirror check.
  - R5: request ids on linked lines; `request_rejected`.
  - S1 = `pick`/`later` only; `api` mode moves to S1b.
  - N-a, N-c, N-d, N-e.
- **Rev 2 (18 Oct)**: user answers (`/root/CLAUDE.md:40-41`); round-1 BLOCK fixes B1–B4, N1–N12.
- **Rev 1 (18 Oct)**: first draft.

---

## 0. Facts that change the 18 Oct demo

The demo (`reports/2026-10-18-customized-catalogue/portal-demo/`) is the UI baseline. A real SPS job-order detail read through the API changes the demo's write payload (`template.html:212-214`). The detail file is `/root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json`, called **SOJ** below.

| # | Fact | Evidence | Consequence |
|---|---|---|---|
| F1 | All 11 custom fields are on the job-order **header**. The line's `custom_field_hash` is empty. The line carries a `Division` tag | SOJ:276-523, :141, :127-135 | **One job order per portal line.** The 22 samples have 22 lines between them |
| F2 | "Order Received from" is a **lookup to an SPS customer contact** | SOJ:283-298 | 11 of the 22 samples use the placeholder "Standard Holdings (Pvt) Ltd" (e.g. SOJ:527, 4494, 5797) |
| F3 | "Job No" (`cf_job_no`) is a **lookup to a project**. The line carries the same `project_id` | SOJ:353-369, :162-163 | A project must exist (§6.9) |
| F4 | Base and additional material are **item lookups** | SOJ:306-325, :4275-4291 | Item ids are sent, not names |
| F5 | Dropdown values contain typos and trailing spaces | SOJ:455, :477, :499 | Options are read from Zoho (V1) |
| F6 | All 22 samples are `confirmed`. Salesperson, delivery method and notes are empty | SOJ:24,53; :574; :47; :271,963 | V2 checks what status a new job order gets. The dashboard hides drafts (`/root/dev/production-dashboard/server/services/line-jobs.js:134`, `job-queries.js:18`, `zoho-queue.js:53`) |
| F7 | Job orders are auto-numbered `JOBORDER-nnnnn` (the user says the next is 08944) | SOJ:19; `/root/CLAUDE.md:41` | The portal never sets the number |

---

## 1. Problem

**Today:**
- A salesperson posts the customized-item request in the "SH MANUFACTURING ORDER REQUEST" group.
- A production manager adds it to a job.
- A coordinator retypes it into SPS Zoho as a job order (`/root/CLAUDE.md:38`; for example, SOJ:68 shows `productioncoordinator02@` as the creator).
- Rizwan's team decides between stock and production, but nothing records the decision.

**Desired:**
1. The salesperson enters the order once, with fields pre-filled.
2. Rizwan's team decides per order.
3. Production accepts the order.
4. The manager approves each line with a Job No.
5. The portal creates the job order through the API, and the Production Dashboard sync picks it up (`zoho-sync.js:31`).

New items, new customers and images follow the same path: request → manager approval → Zoho write. A weekly report goes to Mr. Samitha and Mr. Adnaan (`/root/CLAUDE.md:40`).

**Who is harmed today:**
- coordinators, who retype every order;
- salespeople, who see no status;
- managers, who do not see price changes;
- nobody owns the stock/production decision;
- most items have no image (e.g. `items.json:52-54`).

---

## 2. Readings I had to choose between

| # | Ambiguity | Decision | Basis |
|---|---|---|---|
| A1 | Decide per order or per line | **Per order**: Stock / Production / Send back. To split an order, send it back to the salesperson. Production can return a single line (L6) | `/root/CLAUDE.md:38` |
| A3 | Which price is edited | The job-order rate (SPS→SH) | `/root/CLAUDE.md:41` |
| A4 | Accept vs approve | A coordinator or manager accepts. Only a manager approves, and only for their own divisions | `/root/CLAUDE.md:40` (2) |
| A5 | What "customers" means | SH billing customer = a manual request. SPS end-customer contact = created through the API from **S4**. In S1: the placeholder plus a note (**P4**) | F2, F6 |
| A7 | Separate service | Yes, `order-portal` | `/root/CLAUDE.md:38` (the dashboard's CLAUDE.md note can be updated by the user; not blocking) |

---

## 3. Current behaviour (evidence)

### 3.1 Zoho
**Orgs and API**
- US data centre. SPS org `843825512`, SH org `843061977` (`/root/.claude/projects/-root/memory/zoho-inventory-export.md:11`).
- API base `https://www.zohoapis.com/inventory/v1`; token endpoint `https://accounts.zoho.com/oauth/v2/token` (`/root/dev/production-dashboard/server/zoho/client.js:3-4`).

**Limits**
- SPS: **7,500 calls/day** for the whole org; 0 were used in the 30 days to 7 Oct (`reports/2026-10-07-zoho-api-limit/README.md:6-7`).
- SH: daily limit unknown (`:14-18`).
- Per-minute limits: unknown for both orgs.

**Existing Self Client and dashboard settings**
- Self Client steps: `/root/dev/production-dashboard/docs/zoho-self-client-setup.md:16-66`. Scope format: `ZohoInventory.<module>.<op>` (`:29`).
- The dashboard's daily cap defaults to 7,500 (`server/config.js:83`); its setup doc suggests 400 (`zoho-self-client-setup.md:79`). It throttles itself to 100/min (`client.js:9`).

**SH browser access**
- `ithelp@` sees only Head Office.
- The rizwan@ browser on CDP `127.0.0.1:9333` sees all 10 locations, including "SPS Kohalwila Factory" (`zoho-inventory-export.md:21`; `/root/.claude/projects/-root/memory/zoho-inventory-browser.md:15`).
- About 600 req/min blocks the whole account for about 5 min; 200/min was clean (`zoho-inventory-browser.md:18`).
- Raw-CDP pattern already in use: `/root/tools/abdullah-report/zget.mjs:9-47`.
- SH list pages take 30–90 s (`portal-demo/PLAN.md:32`).

**SPS items and SH customers**
- SPS items carry `status`, `last_modified_time`, `image_document_id`, `cf_bu`, `cf_fg_*`, accounts and a `Division` tag (`items.json:10-90`).
- 2,708 items are Customized (`reports/2026-10-18-customized-catalogue/pulls/merge_stats.json:8`).
- Recipes are `mapped_items` (`/root/exports/zoho/native/2026-09-19/sps/README.md:12,28`).
- SH has 2,698 active customers, with Salesperson/BU filled on 99.8%. About 70 new customers and about 85 new customized items a month; 62% of the new items are copies (`PLAN.md:40-42`).

**Fixed ids and record ownership**
- Warehouse `4892105000000201016` (SOJ:92-93). Standard Holdings contact `4892105000000168085` (SOJ:31-32).
- Zoho shows the token owner as the creator of a record (SOJ:68-69).

### 3.2 Production Dashboard (downstream reader)
- **Sync:** every SPS job order, ordered by `last_modified_time` (`zoho-sync.js:31,166-167`).
- **Division:** the line tag first, then `cf_manufacturing_division` (`:312-316`).
- **Job no:** `project_name ?? cf_job_no` (`line-jobs.js:254`).
- **Hidden:** `draft` and `missing_in_zoho` (`line-jobs.js:134`). Because the not-found code is still `null` (`client.js:6-7`; `zoho-sync.js:380-381`), a deleted job order stays in its mirror.
- It is not in shdeploy yet (`/usr/local/bin/shdeploy:24-30`).

### 3.3 Conventions to match (production-dashboard)
- **Stack:** Node ≥24, ESM, Express 5, better-sqlite3, zod, multer 2, dotenv; tests with node:test and supertest (`package.json:6-51`).
- **Auth:**
  - scrypt passwords (`server/auth/password.js`);
  - hashed sessions, 12 h idle / 7 d max (`sessions.js:3-34`);
  - `__Host-` cookie with SameSite=Strict (`middleware.js:3-7`);
  - Origin check (`:21-26`);
  - role guard (`:83-84`).
- **Rate limits:** login 10 per user and 100 per IP per 15 min (`routes/auth.js:20-21`); writes 60/min (`routes/jobs.js:33`).
- **HTTP:** headers (`create-app.js:26-31`), 1 MB body (`:35`). Binds 127.0.0.1 + 172.17.0.1 only (`config.js:44,62-63`; `listen.js:10-24`).
- **DB and sync:** append-only triggers (`001-schema.sql:296-299,335-340`); sync lease (`zoho-sync.js:72-74`); call counting (`:77-94`); GET-only client (`client.js:1-2`).
- **Deploy:** `shdeploy` backs up the listed DBs at deploy time. `rollback` resets **code only** (`/usr/local/bin/shdeploy:203-209`).

---

## 4. Proposed behaviour

### 4.1 Flow

```
 Salesperson                 Rizwan's team (shared login)        Production (coord / manager)                 Zoho SPS
 search item → customer
 → prefill → lines → SEND ─► per ORDER:
                             [Stock] ─► order STOCK (picking in SH Zoho by hand)
                             [Production] ─► every line to its division queue
                             [Send back] ─► salesperson (reason)
                                                                 [Accept] line (coord/mgr of the division)
                                                                 Job No: pick existing / type new
                                                                 [Approve] (manager of the division) ─► (S1b: project create)
                                                                                                      ─► POST job order (1 per line)
                                                                                                      ─► (if draft) confirm
                                                                 ◄─────────────── JOBORDER-nnnnn ───────
                                                                                                         ▼ Production Dashboard sync
 New item / new customer requests ─────────────────────────────► manager approves ─► item / contact create (S3/S4)
 Images ───────────────────────────────────────────────────────► manager picks ─► attach to Zoho item (S5)
 Monday 06:00 Colombo: weekly review report (S6)
```

### 4.2 Roles

| Role | Who | Login | Can do |
|---|---|---|---|
| `sales` | each SH salesperson | individual | Own orders: create, edit and send; edit and resend after a send-back; cancel orders in `submitted` / `returned_to_sales`; cancel lines in `returned_to_sales`; raise requests; upload to own requests |
| `fulfilment` | Rizwan's team | **one shared account**; acting person required | Decide per order; decide returned lines (L6/L7); SH-customer list, CSV, and mark created |
| `coordinator` | production coordinators | individual | **Own divisions**: accept, fill fields, send back. No approvals |
| `manager` | production managers | individual | Coordinator rights for **own divisions**, plus approve/decline lines and requests, images, and reassign |
| `report_reader` | Mr. Samitha, Mr. Adnaan | individual | Weekly report and CSVs |
| `admin` | IT | individual | Users, team, divisions/people, field rule, sync health, ledger, L15/L16, Retry confirm (L27), **set/clear `restore_pending`**, Reconcile refs (L29), SH Resume |

**Proposals (OQ23)**
- P1: admin ≠ manager.
- P2: the shared login has a 2 h idle timeout.
- P3: office IP for the shared login (§10).
- P4: placeholder + "End customer:" note in S1.

Login follows the dashboard's pattern: cookie `__Host-op_sid`, and `must_reset` on first login.

### 4.3 Screens (vanilla HTML/JS)
1. **Sales, New order:**
   - the demo flow (`PLAN.md:6-11`);
   - per line: item, end customer (existing or "new: <name>"), qty, unit, rate, required-by, job nature, artwork/dye/screen (§6.8), notes;
   - optional SH SO ref;
   - a price badge with its basis.
2. **Sales, My orders:** open orders, plus a **Done** tab (stock / cancelled / done). Shows states, events and reasons, with actions per §5.
3. **Fulfilment, Decide:**
   - `submitted` orders, then `returned_to_fulfilment` lines;
   - matched SH item, Kohalwila stock "as of HH:MM" or "unknown";
   - orders with a new item: "contains a NEW item", and Stock is disabled;
   - an acting person must be picked first.
4. **Production, Queue (own divisions):**
   - lines in `to_production`, `accepted`, `waiting_*`, `so_unknown` and `so_created_draft`;
   - the demo manager card (`template.html:203-209`) plus Job No (pick/type), materials, order type and a payload preview;
   - a "Job No to add in Zoho" list.
5. **Production, Requests:** `template.html:279-292`, plus Approve/Reject and an image picker.
6. **Admin:** users, team, divisions/people, field rule, Sync & writes, ledger (Retry confirm, L15/L16, Reconcile refs), **restore_pending toggle**, settings view.
7. **Reports:** weekly report, missing images, SH-customer list and CSV.

---

## 5. State machines

**Rules for every transition**
- It checks the role **and** the division.
- It checks the client's `version`; a stale version → `409 stale`.
- It writes the state, one event row and one `audit_log` row **in one transaction**.
- System/admin transitions (L10–L14b, L20q/r, L21–L29) re-read the row inside their transaction.
- Any transition not listed below → `409 invalid_transition` and nothing is written.

### 5.1 Order
States: `draft`, `submitted`, `returned_to_sales`, `stock`, `in_production`, `done`, `cancelled`. Before `in_production`, lines are `with_order`.

| # | From | To | Who | Condition / input | Written |
|---|---|---|---|---|---|
| O1 | draft | submitted | sales (owner) | ≥1 line. Each line has an active item **or** a non-`rejected` item request, **and** an end customer: a contact, the placeholder (P4), or a non-`rejected` customer request. A rejected request → 409 `request_rejected`; other failures → 422 | `submitted_at`; price flags |
| O2 | submitted | stock | fulfilment | acting person; no item-request line | stock snapshot per line |
| O3 | submitted | in_production | fulfilment | acting person; every line has a division; no `rejected` request (→ 409 `request_rejected`) | lines → `to_production` |
| O4 | submitted | returned_to_sales | fulfilment | reason ≥5 | — |
| O5 | returned_to_sales | submitted | sales (owner) | edited and resent; O1 rules apply | diff; `version+1` |
| O6 | submitted, returned_to_sales | cancelled | sales (owner) | reason | — |
| O7 | stock | in_production | fulfilment | reason; division per line | lines → `to_production` |
| O8 | in_production | done | system | Checked in the same transaction as every line transition that ends in a terminal state, **including L28 and L29**. Fires when every line is in {`so_created`, `declined`, `cancelled`, `stock`} | `done_at` |

- `stock` can only leave via O7.
- `done` and `cancelled` are terminal.
- Default lists hide `stock`, `done` and `cancelled`; the Done tab shows them.

### 5.2 Line (after `in_production`)
States:
- `to_production`, `accepted`, `returned_to_sales`, `returned_to_fulfilment`;
- `waiting_item`, `waiting_customer`, `waiting_project` (S1b);
- `so_writing`, `so_unknown`, `so_created_draft`;
- terminal: `so_created`, `declined`, `cancelled`, `stock`.

| # | From | To | Who | Condition / input | Written |
|---|---|---|---|---|---|
| L1 | (O3/O7) | to_production | system | — | division |
| L2 | to_production | accepted | coord/mgr of the division | — | `accepted_by` |
| L3 | to_production, accepted | same state, new division | manager of the current division | target ≠ current | `reassigned` |
| L4 | to_production, accepted, waiting_item, waiting_customer | returned_to_sales | coord/mgr of the division | reason ≥5 | — |
| L5 | returned_to_sales | to_production | sales (owner) | edited and resent; picking an existing item sets `item_request_id` = NULL; a `rejected` request → 409 `request_rejected` | diff; `version+1` |
| L6 | to_production, accepted | returned_to_fulfilment | coord/mgr of the division | reason | — |
| L7 | returned_to_fulfilment | stock / to_production | fulfilment | acting person; division needed for `to_production` | — |
| L8 | returned_to_sales | cancelled | sales (owner) | reason | — |
| L9 | to_production, accepted, waiting_item, waiting_customer | declined | manager of the division | reason ≥5 | — |
| L10 | accepted | waiting_item | system | item request not `created` | — |
| L11 | waiting_item | accepted | system | request `created` | — |
| L12 | waiting_item, to_production, accepted | returned_to_sales | system | item request `rejected` | "New item rejected: <reason>" |
| L13 | accepted | waiting_customer | system (S4+) | customer request not `created` | — |
| L14a | waiting_customer | accepted | system (S4+) | customer request `created` | — |
| L14b | waiting_customer, to_production, accepted | returned_to_sales | system (S4+) | customer request `rejected` | "New customer rejected: <reason>" |
| L20 | accepted | so_writing | manager of the division | §7.2 steps 1–3 pass and the ref is **not** found | §7.2 |
| L28 | accepted | so_created / so_created_draft | system, during an L20 attempt | §7.2.1 ref check finds this line's ref → §7.6 status rule. No write row, no POST | id, number, status; `ref_found_before_post`; O8 |
| L20p | accepted | waiting_project | manager of the division | **S1b, mode `api`**: new Job No | `project_create` row created/reused |
| L20q | waiting_project | so_writing | system | project write `done`; pre-checks run again | `project_id` |
| L20r | waiting_project | accepted | system | project write `failed` | — |
| L21 | so_writing | so_created / so_created_draft | system | 2xx with id; status rule | id, number, status; O8 |
| L24 | so_writing | accepted | system | definite failure, or `so_create` still `pending` at startup | write `failed` |
| L25 | so_writing | so_unknown | system | timeout, network, 5xx or non-JSON; or `in_flight` at startup | write `unknown` |
| L26 | so_unknown | so_created / so_created_draft / accepted | system (reconciler) | ref found → status rule; absent in two reads ≥10 min apart → `accepted` | O8 |
| L15 | so_unknown | so_created / so_created_draft | admin | a GET of the entered id returns this line's ref; status rule | O8 |
| L16 | so_unknown | accepted | admin | reason ≥10; forced delta + mirror (+ live filter if V8 allows) finds no ref | write `failed (admin_absent)` |
| L23 | so_created_draft | so_created | system | `so_confirm` `done` | status; O8 |
| L27 | so_created_draft | so_created_draft | admin | Retry confirm, only when the latest confirm `failed` | new `so_confirm` row |
| L29 | any non-terminal line state (`to_production`, `accepted`, `returned_to_sales`, `returned_to_fulfilment`, `waiting_item`, `waiting_customer`, `waiting_project`, `so_writing`, `so_unknown`) | so_created / so_created_draft | admin, Reconcile refs (§7.5) | The matched job order carries this line's ref → status rule. Not moved, only listed for the human: lines in `declined`/`cancelled`/`stock`. Left as they are: lines already `so_created`/`so_created_draft` with the same id | id, number, status; `restore_reconcile`; O8 in the same transaction |

- While a `project_create` is `in_flight` or `unknown`, the line stays `waiting_project`.
- There is no transition out of `so_created` (N3).

### 5.3 Requests
- **Item request:** `requested → approved_writing → created | failed (→ requested on re-approve) | unknown (→ reconciled)`. Also `requested → rejected`, and `requested → created` with `linked_existing=1` (no write).
- **Customer request (S4):** the same states, plus `sh_state ∈ {not_needed, open, done, cancelled}`.
- **R5:**
  - `created`: the Zoho id goes onto **every** linked line, whatever its state, in the same transaction. Waiting lines take L11/L14a.
  - `rejected`: lines in the L12/L14b states are returned. Any other linked line is refused at O1/O3/L5 with `request_rejected`.

---

## 6. Detailed behaviour

### 6.1 Pre-fill (`template.html:221-233`)
- The placeholder `4892105000000168085` never counts as a customer.
- The "last line" is chosen in this order:
  1. the newest mirror line with the same item **and** the same real customer → `last_rate_basis = customer`;
  2. else the newest line for the item (placeholder lines included) → `basis = item`;
  3. else nothing is pre-filled → `basis = none`.
- Pre-filled from the last line: qty, rate, artwork, dye, screen.
- Job nature: "Reorder" only when the basis is `customer`; otherwise "New Order" (option text from V1).
- Required-by: +10 days for a reorder, +14 days for a new order (Colombo date).
- Manager fields (division, materials, order type, Job No) come from the last line, then the item's Division tag.

### 6.2 Price flag
- `last_rate` and `last_rate_basis` are stored when the order is sent.
- `price_changed = 1` when the rate differs from `last_rate` at 2 dp, or when the basis is `none`.
- The basis is shown on screen and in the report.
- A resend recomputes the flag; the old values stay in the diff.

### 6.3 Salesperson mapping
- Source: the SH Salesperson field (S2). Until S2: a one-time catalogue import (README:9-11).
- The mapping only orders search results. It never grants or blocks access.

### 6.4 Stock for Rizwan's team (S2)
- Matching: normalised name, then SKU (catalogue `README.md:9`), stored in `item_links`.
- Stock is shown at the OQ5 locations, with its fetch time. It is advice only.
- "Unknown" when there is no match, the reader is stopped, or the value is more than 30 min old.

### 6.5 New item (S3)
- Two paths: copy or brand-new (`template.html:256-277`).
- Requests go through Rizwan's team, with Stock disabled.
- The manager sets: prefix (OQ7), name, `cf_bu`, `cf_fg_nature`, unit, Division tag, recipe, cost (OQ19).
- Fixed: `cf_fg_type = Customized`; sub-category from the BU (`items.json:65-76`); accounts copied.
- Duplicate check: mirror plus live search (V8) → "link existing".

### 6.6 New customer
- **S1 (P4):**
  - the demo's duplicate check (`template.html:238-255`);
  - the placeholder goes into `end_contact_id`, and the typed name into `new_end_customer_name`;
  - notes start with `End customer: <name>`;
  - listed in the weekly report.
- **S4:**
  - approval creates the SPS contact, then L14a;
  - a new SH billing customer goes on a list + CSV only (`template.html:254` fields, no credit/terms);
  - it is created by hand by the OQ8 owner and auto-linked by exact name on the next pull;
  - the job order never waits for it.

### 6.7 Images (S5)
- **Display:** read token, 24 h cache, **100 fetches/day** cap.
- **Uploads:**
  - artwork PDF/PNG/JPEG; photos PNG/JPEG;
  - 10 MB per file, 5 per request, 100 MB per user per day, 20 per minute;
  - type checked from the file's leading bytes only; SVG, HTML and Office files refused;
  - stored outside the static root; downloaded through an authenticated route.
- **Attach:** the manager picks one image → an `item_image` write.
- **Missing-images list:** Customized items with no image, sorted by line count over 12 months.

### 6.8 Division-specific fields: a PROPOSAL needing the production managers' confirmation (OQ6)
- Seed rule (`PLAN.md:19`; `template.html:226-227`):
  - artwork: always;
  - dye cutter: OPD, PCU, MOBA, CPU, FPP;
  - screen/plate: OPD, SHPS.
- The demo code also shows dye for SHPS (`template.html:123`).
- The rule is stored in `division_fields`.
- A hidden field is sent as its exact "not applicable" option (V1). If no such option exists, the field is shown for every division.
- Shown as "not yet confirmed" until a manager confirms it.

### 6.9 Job No / project and the payload
The manager picks a Job No from `sps_projects` or types a new one. If a typed name matches an existing project (after `lower(trim())`), the portal makes them pick that project instead.

| Mode | Built in | When | New Job No |
|---|---|---|---|
| `pick` | **S1** | V3: projects readable, not creatable | Refused: "ask your coordinator to create project <name> in Zoho, then pick it" |
| `later` | **S1** | V3: projects not readable **and** V2: a job order can be created without project fields | Written without project fields; `reference_number` = Job No; `job_no_to_add=1`. The coordinator adds the project; the flag clears when the sync sees `cf_job_no` |
| `api` | **S1b** | V3: projects readable and creatable | `project_create` keyed `project_create:<lower(trim(name))>`, with a partial unique index. Approval reuses the row: `done` → use its id; `pending`/`in_flight`/`unknown` → `waiting_project`; `failed` → new row. A live name search runs first |

If V2/V3 rule out every mode, the trial cannot start (G2).

**Payload (one per line).** `customfield_id` values come from V1 (e.g. `cf_order_received_from` = `4892105000000168001`, SOJ:278-279).

```json
POST /salesorders?organization_id=843825512
{
  "customer_id": "4892105000000168085",
  "date": "<today Colombo>",
  "shipment_date": "<required_by>",
  "reference_number": "<Job No text>",
  "notes": "<'End customer: <name>' if placeholder (P4); then line notes>",
  "custom_fields": [
    {"customfield_id": "<cf_order_received_from>", "value": "<contact id or placeholder 4892105000000168085>"},
    {"customfield_id": "<cf_material_to_be_used>", "value": "<item id>"},
    {"customfield_id": "<cf_additional_other_material_t>", "value": "<item id>"},   // only if set
    {"customfield_id": "<cf_sh_sales_order_ref>", "value": "<SH SO ref or ''>"},
    {"customfield_id": "<cf_job_no>", "value": "<project id>"},                    // omitted in mode 'later'
    {"customfield_id": "<cf_order_type>", "value": "<exact option>"},
    {"customfield_id": "<cf_manufacturing_division>", "value": "<exact option>"},
    {"customfield_id": "<cf_job_nature>", "value": "<exact option>"},
    {"customfield_id": "<cf_artwork_availablility>", "value": "<exact option>"},
    {"customfield_id": "<cf_dye_cutter_availablity>", "value": "<exact option>"},
    {"customfield_id": "<cf_screen_plate_availability_2>", "value": "<exact option>"},
    {"customfield_id": "<cf_portal_ref>", "value": "<PORTAL_INSTANCE>-<line uuid>"}
  ],
  "line_items": [{
    "item_id": "<id>", "quantity": <qty>, "rate": <job-order rate>,
    "warehouse_id": "4892105000000201016",
    "project_id": "<project id>",                                                  // omitted in mode 'later'
    "tags": [{"tag_id": "4892105000000000333", "tag_option_id": "<division option>"}]
  }]
}
```
Not sent: `salesorder_number`, `salesperson_name`, `delivery_method`, `cf_clickup_link`.

### 6.10 Weekly review report (S6)
- **Week:** Monday 00:00 to Sunday 23:59:59, Colombo time.
- **Snapshot:** taken Monday 06:00 (`ON CONFLICT DO NOTHING`); a missed week is generated once at startup.
- **Sections:**
  - job orders created;
  - send-backs and declines;
  - price changes with their basis;
  - new items;
  - new end customers;
  - SH requests;
  - missing images;
  - failures, unknowns and drafts;
  - "Job No to add";
  - `restore_reconcile` events.
- **Scope:** IT only, with no finance items.
- **Format:** page + CSV + print view (OQ12). No SMTP.
- **Footer:** "Prepared by Abdul Hadhee | IT Executive".

---

## 7. Write safety

### 7.1 Ledger and refs
- **`zoho_writes`:**
  - `kind ∈ {so_create, so_confirm, project_create (S1b), item_create (S3), contact_create (S4), item_image (S5)}`;
  - `entity_type`, `entity_id`, `idem_key`, `marker`, `payload_json`;
  - `state ∈ {pending, in_flight, done, failed, unknown}`;
  - `zoho_id`, `http_status`, `zoho_code`, `error_text`, `attempts`, `approved_by`, timestamps;
  - `UNIQUE(idem_key) WHERE state <> 'failed'`.
- **idem_key formats:** `so_create:<line>:<version>`, `so_confirm:<line>:<n>`, `project_create:<lower(trim(name))>`, `item_create:<req>:<version>`, `contact_create:<req>:<version>`, `item_image:<file>`.
- **Ref** = `PORTAL_INSTANCE-<line_uuid>`, stored in `cf_portal_ref` (created at G1).
  - The UUID is made once per line, so one line maps to at most one job order.
  - `PORTAL_INSTANCE` differs between dev, test and live.
  - A new Zoho field is needed because `reference_number` holds the Job No (SOJ:30 = :364) and `cf_sh_sales_order_ref` holds the SH SO number.
  - The detail sync stores `cf_portal_ref` and `status` in `sps_so_lines`.

### 7.2 Write sequence
**1. Pre-checks.** Each is a live read counted in the write reserve. If any check fails, nothing is written and the reason is shown.

- **`so_create`:**
  - The item, contact/placeholder and materials are active.
  - The project exists (`pick`/`api`).
  - **Ref check:**
    - **(a) Forced delta.** Wait at most **30 s** for `sps_sync_lease`. If the wait times out: "Zoho sync busy, retry", no write row, the line stays `accepted`, and nothing is sent. Once the lease is held: list job orders by `last_modified_time` back to the line's last attempt − 2 min (or 24 h if there was none), and fetch details for listed job orders that the mirror does not have at that `last_modified_time`.
    - **(b)** Search the mirror's `cf_portal_ref`.
    - **(c)** Only if V8 shows a filter exists: one live filter call.
    - **If found → L28**: the status rule applies and nothing is POSTed.
    - **V8-negative:** (a) and (b) are the whole check. Any remaining gap is covered by the reconciler for `unknown` writes.
- **`so_confirm`:** a GET by id. If the status ≠ draft → `done`, no POST.
- **`project_create` (S1b):** a live name search.
- **`item_create` / `contact_create`:** a duplicate check; components must be active.
- **`item_image`:** item active; PNG/JPEG within the Zoho limit (V4).
- **Every write:** `ZOHO_WRITES_ENABLED=true` **and** `restore_pending` not set; the write token is configured; budget remains.

**2. Insert the row** as `pending` (or reuse it on an `idem_key` clash) and move the entity to its writing state, in one transaction.

**3. Commit `in_flight`** before the network call.

**4. POST**, classify the result (§7.3), and update the row and the entity in one transaction.

**At startup (before any scheduler runs):**
- Non-confirm rows still `pending` → `failed (never_sent)`, and the entity goes back (L24/L20r).
- `so_confirm` rows still `pending` → re-queued.
- `in_flight` rows → `unknown`.

**Order of writes:** `project_create` (S1b) → `so_create` → `so_confirm`. An image failure never affects the item or the job order. Zoho ids are stored only when they come from Zoho or are verified by a GET.

### 7.3 Outcome classification

| Answer | State |
|---|---|
| 2xx with id | `done` |
| 4xx with a Zoho `code` (incl. 429) | `failed`; entity goes back; re-approval uses the same ref |
| 401 after one refresh | `failed (auth)`; writes pause; banner |
| timeout / network / 5xx / non-JSON | `unknown`; **never resent automatically** |

### 7.4 Reconciliation (every 5 min)
- **`so_create`:**
  - Forced delta back to `attempted_at − 2 min`, with the same 30 s lease wait (on timeout, try again next cycle).
  - Then a mirror lookup, plus a live filter if V8 allows.
  - Found → status rule (L26). Absent in two reads ≥10 min after the attempt → `failed (reconciled_absent)` and the line goes to `accepted`.
  - V8-negative: the forced delta plus the mirror is the only method. If the delta cannot complete, the row stays `unknown`. There is no customer filter, because every customer is Standard Holdings.
- **`so_confirm`:** §7.6.
- **Others:** exact search by marker.
- Two `unknown` outcomes in a row → approval is disabled until an admin acts.

### 7.5 After any DB restore: mandatory runbook
`shdeploy rollback` does **not** restore the DB (`shdeploy:209`). Restoring a DB backup is a manual human step.

**The portal does not detect restores by itself**, so the runbook below is mandatory. It is printed in `docs/RESTORE-RUNBOOK.md` and on the Admin screen.

**Why the ref check alone is not enough after a restore.** The restored DB has lost ledger rows. A line that already has a job order can be back in `accepted` with no record of its last attempt. Its forced delta then looks back only 24 h (§7.2.1a) against an older mirror, so an earlier job order could be missed and a **duplicate** created on re-approval.

**`restore_pending` (admin toggle, in `settings`):**
- While it is set, every write is refused at the pre-check **whatever `ZOHO_WRITES_ENABLED` says**.
- It survives restarts.
- It is shown in health and as a red banner.
- It can be cleared **only** by an admin, and only after a Reconcile refs run that started after the toggle was set has completed.
- Setting and clearing it are audited.

**Runbook, in this order:**
1. **Before starting the service on the restored DB**, do one of these (both is best):
   - run `npm run restore-pending -- on`. This offline CLI opens the DB file directly with the service stopped, sets `restore_pending=1` with an audit row, and refuses to run if the service is running (it checks the PM2 process / port 4800);
   - set `ZOHO_WRITES_ENABLED=false` in `.env`.

   Then start the service.
2. **Reconcile refs (admin):**
   - Forced delta back to the backup's time. There is no 24 h limit; it may take several cycles within budget.
   - Every mirrored job order whose `cf_portal_ref` starts with `PORTAL_INSTANCE` and that was modified since then is matched to its line by `line_uuid`:
     - a non-terminal line → **L29** (status rule, `restore_reconcile`, O8 in the same transaction);
     - a line that is `declined`, `cancelled` or `stock` → listed for the human, not moved;
     - a ref with no line → listed.
   - The run is "completed" only when the delta has covered the whole period.
3. **Clear** `restore_pending` (admin), set `ZOHO_WRITES_ENABLED=true` if it was turned off, and restart.

Who restores and how they follow this runbook is OQ24.

### 7.6 Status rule and `so_confirm`
**Status rule.** Whenever the portal learns that a job order exists, it reads its status. This applies at L21, L28, L26, L15 and L29.
- `draft` → `so_created_draft`, and an `so_confirm` is queued as `pending`. It is sent only while writes are allowed and `restore_pending` is not set.
- Any other status → `so_created`.

**`so_confirm`** (endpoint and scope from V2; implemented by the fake):

| Situation | Handling |
|---|---|
| `pending` (incl. at startup) | GET first; if status ≠ draft → `done` with no POST; otherwise POST confirm |
| 2xx | GET shows status ≠ draft → `done` → L23 |
| 4xx / 401 | `failed`; the line stays `so_created_draft`; Retry confirm (L27); banner "Draft in Zoho: not on the Production Dashboard until confirmed" |
| timeout / 5xx / non-JSON | `unknown` → GET by id: status ≠ draft → `done`; still draft in two reads ≥10 min apart → `failed` |

A line never goes back to `accepted` because of a confirm problem.

### 7.7 Audit
- Append-only `audit_log`.
- Logged: logins, transitions, approvals, write attempts and outcomes, uploads, admin changes (including `restore_pending` set and clear, from the UI and the CLI), and the kill-switch state at startup.
- The actor is recorded, plus the acting person on the shared login.
- Never logged: tokens, secrets, passwords or file contents.

---

## 8. Reads

### 8.1 SPS budget (7,500/day per org)

| Consumer | Cap/day | Source |
|---|---|---|
| production-dashboard | **≤ 4,500** (lower its default of 7,500) | `config.js:83`; OQ11, needed **before the portal's first live read** |
| inventory-system | 500 | `/root/CLAUDE.md` §2 |
| order-portal | **2,000** (range 250–2,000) | this spec |
| headroom | ≥ 500 | |

**Inside the portal's 2,000:**

| Use | Budget |
|---|---|
| Steady reads | ~1,060 (three list deltas every 5 min = 864; ~100 details; project delta every 15 min = 96) |
| Write reserve | **300**. About 9 calls per job order, so **about 33 job orders a day**. `WRITE_RESERVE` can go up to 1,000 |
| Images | ≤ 100 |
| History load | Only what is left: `cap − reserve − images_used − steady_so_far − projected_steady_rest_of_day` (≤ 0 means none that day) |

- Throttle: ≤ **50 SPS calls/min** in total.
- Reads stop at `cap − reserve`; writes stop at `cap`.
- Counters reset at midnight Colombo time.

### 8.2 SPS sync
- One cycle at a time, under `sps_sync_lease` (`zoho-sync.js:72-74`). A tick while the lease is held is skipped and logged as `cycle_skipped_busy`.
- Deltas run newest first and stop at `watermark − 2 min`. The watermark advances only after an `ok` run (`zoho-sync.js:166-196`).
- The detail sync stores `cf_portal_ref` and `status`.
- Items gone from Zoho or inactive there are marked inactive.
- The read token is GET-only. Only the write module can reach the write token.
- Forced deltas wait **at most 30 s** for the lease; on timeout: "Zoho sync busy, retry", and nothing is written.

### 8.3 SH browser reader (S2)
- **Adapters:** the `ShReader` interface, with `cdp` and `off` only. No `api` adapter code yet.
- **Lease and order:** its own `sh_sync_lease`. Stock is read first (≤20 per cycle, cached 5 min), then the lists.
- **`cdp` rules:**
  - `127.0.0.1:9333` only, on a robots.txt tab that passes the `1+1` probe (`zget.mjs:9-24`);
  - the fetch source is fixed and uses `method:'GET'`;
  - path allow-list (`items`, `items/<id>`, `contacts`, `locations`); ids must match `^\d{1,25}$`; query keys allow-listed; values passed via `JSON.stringify` (`zget.mjs:39`);
  - ≥1,200 ms between requests (≤50/min), ≤40 per cycle, ≤6,000 per day, 60 s timeout;
  - never navigates, closes the app tab, signs in or out, or kills Chrome.
- **Combined ceiling on :9333:** ≤200/min across all tools (`zoho-inventory-browser.md:18`). No full SH pull while the reader runs (OQ20).
- **Delta sorting:** V12. If SH lists can't be sorted by change time, fall back to a nightly refresh.
- **Stop states** (persisted):
  - `login_required` (401, non-JSON, missing key, or an accounts URL) — cleared only by an admin Resume;
  - `rate_paused` for 10 min after a 429.

### 8.4 Freshness
- Normal: "updated HH:MM".
- Over 15 min since the last update: amber "stale since".
- SH `login_required`: red banner, stock shown as unknown.
- SPS `auth` failure: red banner, approvals disabled.
- `restore_pending`: red admin banner, writes off.

---

## 9. Data model changes

**New database `data/order-portal.db`** (SQLite, WAL). Justification: a new service by user decision, holding new data. The alternative (the dashboard's DB) was rejected because it couples the two deploys.

- **People:** `users`, `sessions`, `team_members`, `divisions`, `division_people`, `division_fields`.
- **Mirror:**
  - `sps_items`, `sps_contacts`, `sps_projects`;
  - `sps_so_lines` (with `cf_portal_ref` indexed, and `status`);
  - `sps_field_options`;
  - `sh_customers`, `sh_items`, `sh_stock`, `item_links`, `customer_links`;
  - `sync_runs`, `api_calls_daily`.
- **Work:**
  - `orders(…, state CHECK IN ('draft','submitted','returned_to_sales','stock','in_production','done','cancelled'), done_at, version, UNIQUE(salesperson_id, client_token))`;
  - `order_lines(id, line_uuid UNIQUE NOT NULL, …, last_rate, last_rate_basis CHECK IN ('customer','item','none'), price_changed, …, job_no, project_id, job_no_to_add, state, version, sps_so_id, sps_so_number, sps_status, CHECK (sps_item_id IS NOT NULL OR item_request_id IS NOT NULL))`;
  - `order_events` and `line_events` (append-only), `item_requests`, `customer_requests`, `files` (soft delete), `zoho_writes` (partial unique index), `audit_log` (append-only), `weekly_reports`;
  - `settings` (leases, `sh_state`, `sh_pause_until`, **`restore_pending`** with `restore_pending_set_at` / `_by` and `reconcile_completed_at`).
- **Migrations:**
  - Forward: numbered `NNN-*.sql`, one transaction each, recorded in `schema_migrations(name, sha256, applied_at)`. The service refuses to start on a hash mismatch.
  - Idempotent: migrations already recorded are skipped.
  - Rollback: changes are additive only. `shdeploy rollback` is code-only (`shdeploy:209`), so every migration must run under the previous code. A DB restore is a manual step plus the §7.5 runbook.
- **Zoho:** a `Portal Ref` field and two refresh tokens.

---

## 10. Security
- **Exposure:** HTTPS through Traefik; binds only to `127.0.0.1` and `172.17.0.1`; `TRUSTED_PROXY_IPS` is set. Hostname: OQ10.
- **CSRF:** SameSite=Strict plus an exact `Origin` check. No CORS.
- **Input:**
  - zod on every route;
  - caps: name 200, notes 2,000, reason 500;
  - qty > 0 and ≤ 1e7; rate ≥ 0 and ≤ 1e7, 2 dp;
  - `YYYY-MM-DD` dates; required-by ≥ today;
  - every id must exist in the mirror;
  - output escaped; the dashboard's CSP.
- **Login lock-out:** 10 per user+IP per 15 min, 100 per IP. Never a global lock on a user. **P3** `FULFILMENT_ALLOWED_IPS` (OQ21).
- **Shared login:** acting person required, P2 timeout, password rotated when someone leaves, individual logins at launch.
- **Rate limits:** writes 60/min per user; approvals 30/min per manager; uploads 20/min per user.
- **Secrets:**
  - dev `.env` is gitignored; the live `/root/order-portal/.env` is created by the human;
  - keys: `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_READ_REFRESH_TOKEN`, `ZOHO_WRITE_REFRESH_TOKEN`, `ZOHO_ORG_ID_SPS=843825512`, `ZOHO_WRITES_ENABLED`, `ZOHO_DAILY_CALL_CAP`, `WRITE_RESERVE`, `PROJECT_MODE`, `PORTAL_INSTANCE`, `SH_READER`, `SH_CDP_URL`, `SH_ORG_ID=843061977`, `APP_ORIGIN`, `TRUSTED_PROXY_IPS`, `FULFILMENT_ALLOWED_IPS`, `PORT=4800`;
  - `ZOHO_FAKE_URL` is for tests only and refused in production;
  - tokens are held in memory only and never logged.
- **Tokens:** one Self Client, **two refresh tokens**:
  - read: `salesorders.READ, items.READ, compositeitems.READ, contacts.READ, settings.READ` (+ projects);
  - write: `salesorders.CREATE` (+ `.UPDATE` if confirm needs it), plus scopes for later slices;
  - exact names come from V7.
- **Kill switch:** revoke **only the write token**. Never delete the client.
- **Creator:** Zoho shows the token owner (OQ22).

---

## 11. Service, port, deploy
- **Process:** `order-portal`, one PM2 process in **fork mode, `instances: 1`**. It exits if `NODE_APP_INSTANCE` is set and not `0`.
- **Paths:** live `/root/order-portal`, dev `/root/dev/order-portal`, DB `data/order-portal.db`, health `http://127.0.0.1:4800/api/health`.
- **Port 4800:**
  - not in the in-use list (22, 3000, 3001, 3005, 4100, 4199, 4200, 4310, 4500, 4601, 4710, 4711, 5001, 6969, 8080, 8765, 9333–9336, 19930–19940);
  - not reserved (4300, 4400);
  - follows the round-hundred pattern.
  - The human checks it with `ss -ltn | grep :4800`.
- **shdeploy row** (added by the human):
  `order-portal |/root/order-portal |order-portal |data/order-portal.db |http://127.0.0.1:4800/api/health |docs/`
- **Health:** `{ok, db, sps:{lastOkAt, stale}, sh:{state, lastOkAt}, writesEnabled, restorePending, projectMode, budget:{used, cap}, draftsAwaitingConfirm}`.

---

## 12. Testing approach and the fake Zoho
- **Fake Zoho:** a local Node `http` server on a random port (`ZOHO_FAKE_URL`).
  - Read fixtures come from real exports (SOJ, `items.json`).
  - Write responses are hand-written: 201 confirmed or draft, 4xx with a code, a delay, a timeout, 5xx, non-JSON.
  - The `cf_portal_ref` filter can be switched on or off.
  - It records every request.
- **Fake CDP:** stands in for `:9333`.
- **Test lease holder:** for AC33c.
- **After G3:** the real responses replace the hand-written ones.

---

## 13. Acceptance criteria

**Auth and roles**
- AC1: Given no session, when any `/api/*` route except login/health is called, then 401 and no write.
- AC2: Given a sales user, when they open another salesperson's order, then 404.
- AC3: Given a non-GET with the wrong `Origin`, then 403.
- AC4: Given 10 failures for U from IP A, then the 11th attempt from A gets 429, and U from IP B can still log in.
- AC5: Given the shared login with no acting person, then 400.
- AC6: Given a fulfilment login from an IP outside the allowed list, then 403 and an audit row.
- AC7: Given admin+manager on one user, then 400.
- AC8: Given a coordinator approves, then 403 and no ledger row.
- AC8b: Given a user of division X acts on division Y, then 403 and nothing written.

**Order entry and Rizwan's decision**
- AC9: Given a past order for item I with customer C, when I then C are picked, then pre-fill comes from the newest such line (`basis=customer`).
- AC10: Given I was ordered only by D, then pre-fill comes from I's newest line, "New Order", `basis=item`.
- AC10b: Given the placeholder is picked and I's newest line is on the placeholder at 5.00, then I's newest line is used, "New Order", `last_rate=5.00`, `basis=item`. A real customer with no lines → `basis=item`. An item with no lines → `basis=none` and `price_changed=1`.
- AC11: Given last 4.27 and entered 4.50, then `price_changed=1`. AC12: equal at 2 dp → 0.
- AC13: Given the same `client_token` twice, then one order.
- AC14: Given an inactive item, then 422.
- AC15: Given bad dates, qty, rate or notes, then 422 and nothing stored.
- AC16: Given Stock chosen on a 3-line order, then the order is `stock` with a snapshot per line and the acting person recorded.
- AC17: Given an order with an item request, when Stock is chosen, then 409 `new_item_not_in_stock`.
- AC18: Given Production chosen, then every line is `to_production`, each only in its own division's queue.
- AC19: Given a send-back reason of 4 chars, then 422. Given ≥5 chars, then `returned_to_sales` and the reason is visible.
- AC20: Given two decisions on the same version, then one succeeds and the other gets 409.
- AC21: Given O7, then the lines are `to_production`.
- AC22: Given sales cancels an `in_production` order, then 409. Given a `submitted` order, then `cancelled`.
- AC22b: Given the last line goes terminal, then the order is `done` in the same transaction and moves to the Done tab. Given a `so_created_draft` line, then the order is not done.

**Production**
- AC23: Accept → `accepted`.
- AC24: Reassign X→Y moves the line between queues.
- AC25: Decline without a reason → 422. With a reason → `declined`; later transitions → 409.
- AC26: A full state × action matrix. Unlisted pairs → 409 with nothing written. L28 and L29 are allowed (matching AC33/33b/46/46b). Reconcile refs on `declined`/`cancelled`/`stock`/`so_created`/`so_created_draft` changes nothing (AC46c).
- AC26b: A rejected request blocks O1, L5 and O3 with `request_rejected` (item and customer). A request becoming `created` sets its id on linked lines in every state.
- AC27: Picking an existing item on a returned line clears `item_request_id` and leaves the request unchanged.

**Job-order write (S1)**
- AC28: Given writes are disabled, when approving, then 409 and no requests.
- AC29: Given the hand-written fixture `test/fixtures/expected/so-create-basic.json`, when `test/fixtures/lines/basic.json` is approved, then exactly one POST whose body deep-equals the fixture.
- AC30: Given 201 confirmed, then `so_created` and `done`.
- AC30b: `so_created` never has status draft. Given 201 draft, then draft → confirm → `so_created`.
- AC30c: Given the confirm returns 400, then the line stays draft and Retry confirm is offered; on success, `so_created`.
- AC30d: Given the confirm times out, then `unknown` → GET settles it either way.
- AC30e: Given a confirm `pending` at restart, then it is re-queued, the line stays draft, and if the GET shows confirmed, no POST is sent.
- AC31: Given two concurrent approvals of the same version (fake delayed 500 ms), then exactly one POST and the same write id for both.
- AC32: Given the item is inactive at pre-check, then no POST.
- AC33 (L28): Given the ref is found with confirmed, then no row, no POST, `so_created`, and O8 is checked.
- AC33b (L28): Given the ref is found with draft, then `so_created_draft` plus a confirm. Holds with the filter off and on (exactly one filter call when on).
- AC33c: Given the lease is held for 35 s, then after ~30 s "Zoho sync busy, retry", no row, `accepted`, and 0 requests. Given it is freed at 20 s, then the write proceeds.
- AC34: Given 400, then `failed`, `accepted`; re-approval keeps the same ref.
- AC35: Given a timeout, then `unknown` and no second POST.
- AC36: Given the reconciler finds the ref (confirmed), then `so_created` and still one POST. AC36b: draft → `so_created_draft` plus a confirm.
- AC37: Given the ref is absent twice, ≥10 min apart, then `failed` and `accepted`.
- AC38: Given restart recovery, then `pending` → `never_sent`/`accepted` and `in_flight` → `unknown`/`so_unknown`, before any scheduler runs.
- AC39: Given L15 with a GET of a different ref, then 409. A matching ref (confirmed) → `so_created`. AC39b: a matching ref (draft) → draft plus a confirm.
- AC40: Given L16 while the ref is found, then 409. If absent with a reason ≥10, then `accepted`.
- AC41: Given an item request not yet created, then 409 `prerequisite_pending`.
- AC43 (`pick`): Given an unknown typed Job No, then 409.
- AC44 (`later`): Given a typed Job No, then no project fields, `reference_number` = Job No, and the flag is set; it clears later.
- AC45 (P4): Given a placeholder line, then the payload has the placeholder and the "End customer:" note.
- AC46 (toggle, L29):
  - Given a DB restored to before a `done` write (the line is back in `accepted`) and `npm run restore-pending -- on` run with the service stopped:
    - then on startup with `ZOHO_WRITES_ENABLED=true`, health shows `restorePending=true`;
    - an approval → 409 `restore_pending` with 0 requests to Zoho write paths.
  - The CLI, run while the service is up → it refuses and exits non-zero.
  - Clearing the toggle before a completed Reconcile refs (started after it was set) → 409.
  - Reconcile refs → the line becomes `so_created` (`restore_reconcile`), and O8 is checked in the same transaction.
  - The admin clears the toggle → writes allowed again.
  - Re-approving that line → 409 `already_created`.
  - Setting and clearing the toggle (UI and CLI) each leave one audit row.
  - The toggle survives a restart while it is set.
- AC46b: Same as AC46, but the job order is draft → `so_created_draft` plus a confirm, which is sent only after the toggle is cleared.
- AC46c: Reconcile refs matching a `declined`/`cancelled`/`stock` line → unchanged and listed with the job-order number. A ref with no line → listed.

**Project create (S1b)**
- AC42: The project is created before the job order. A failed project write → no job order, L20r. An existing "opdtest1 " is reused with no POST.
- AC42b: Two concurrent approvals of " OPDTest2" and "opdtest2" → one project POST. Both lines are `waiting_project`, then both `so_created` with the same `project_id`. On timeout, both stay waiting until reconciled.

**Budget and sync**
- AC47: Reads at cap − reserve → 0 read calls, while writes still work.
- AC48: At cap → writes get 409.
- AC49: History budget ≤ 0 → 0 history calls.
- AC50: ≤ 50 SPS requests per 60 s.
- AC51: A tick while the lease is held → skipped and logged.
- AC52: Paging stops correctly; the watermark advances only after `ok`.
- AC53: Banner at 16 min, none at 14 min.
- AC54: At the image cap → 0 more fetches.
- AC54b: `cf_portal_ref` and status are stored by the detail sync.

**SH reader (S2)**
- AC55: HTML response → `login_required`, 0 further requests, and the state persists across a restart until Resume.
- AC56: 429 → a 10-min pause that persists across a restart.
- AC57: Through the vm stub fetch, every call is GET and allow-listed; bad ids or paths are refused before any CDP message.
- AC58: ≤40 per cycle, ≥1,200 ms apart, stock before lists.
- AC59: A slow SH cycle does not delay SPS.
- AC60: `off` works; `cdp` passes the contract suite.
- AC61: Stock older than 31 min → shown as unknown.

**New item, customer, images, report**
- AC62 (S3): Copy request → pre-filled recipe; approval → one composite POST, then R5 and L11.
- AC63 (S3): A name match → link existing; a rejection → L12.
- AC64 (S4): Duplicate blocked; approval → one contact POST, R5, L14a; a rejection → L14b.
- AC65 (S4): An SH request stays local; the CSV has no credit or terms; an exact-name match auto-links.
- AC66 (S5): Uploads are typed by their bytes; size and type limits enforced.
- AC67 (S5): One image call per attach; a failure leaves everything else unchanged.
- AC68 (S5): An unauthorised download → 404.
- AC69 (S6): One snapshot per week, unchanged by a restart; price rows match the flags, with basis.
- AC70 (S6): No finance words; a sales user gets 403.

**Audit and process**
- AC71: Append-only tables abort an update or delete.
- AC72: A fault injected after a state update → nothing kept.
- AC73: No secrets in logs.
- AC74: `NODE_APP_INSTANCE=1` → the process exits before it binds.

---

## 14. Slices and gates

| Slice | Content | Done when | Blocked by |
|---|---|---|---|
| **S0 Foundation** | repo, config, migrations, auth/roles, admin data, fake Zoho, SPS read sync incl. `cf_portal_ref`, budget, freshness, health, audit, **`restore_pending` toggle + offline CLI** | AC1–AC8b, AC47–AC54b, AC71–AC74 | **Nothing** |
| **S1 Trial core** | order → per-order decision → production → approval (`pick`/`later`) → `so_create` + `so_confirm`, ref check (L28), status rule, reconciliation, Reconcile refs (L29), kill switch, restart rules, price basis, order `done`, `docs/RESTORE-RUNBOOK.md` | AC9–AC41, AC43–AC46c | **Nothing for building.** The trial needs G1–G3 |
| **S1b Project create** | mode `api` | AC42, AC42b | V3 |
| **S2 SH reader** | `cdp`/`off`, mapping, stock, stop states | AC55–AC61 | OQ5, OQ20, V9–V12 |
| **S3 New item** | | AC62–AC63 | OQ7, OQ19, V5 |
| **S4 New customer** | | AC64–AC65 | OQ8, OQ9, V6 |
| **S5 Images** | | AC66–AC68 | OQ18, V4 |
| **S6 Weekly report** | | AC69–AC70 | OQ12 |

### Pre-trial gates (with the user; none block the build)

**G1. Zoho setup (the user):**
1. At https://api-console.zoho.com/ as the SPS admin (US DC), open the existing Self Client, or ADD CLIENT → Self Client.
2. Read code: read scopes (§10), 10 min, Inventory, **SmartPack**.
3. Run the `curl` from `zoho-self-client-setup.md:49-55` and put the result in `ZOHO_READ_REFRESH_TOKEN` in `/root/order-portal/.env`.
4. Write code: the same with the write scopes → `ZOHO_WRITE_REFRESH_TOKEN`.
5. Record how many refresh tokens the client now has. The cap of about 20 is unverified, so keep well below it.
6. Add an SPS job-order custom field **Portal Ref** (Text) and note its API name.
7. Set the dashboard cap to ≤4,500 (OQ11) before the portal's first live read.
8. Keep writes off until G3. Never paste a secret anywhere.

**G2. Read-only checks** (IT, ≤40 calls; results in `docs/zoho-api-findings.md`):

| V | Question |
|---|---|
| V1 | Custom-field ids and option lists |
| V3 | Can projects be read and created? Which scopes? Is matching case-sensitive? |
| V7 | Scope names; can one token be revoked on its own? |
| V8 | Do list rows include `cf_*`? Is there a `cf_portal_ref` filter? Search and sort behaviour |
| V9 | SH stock per location; the Kohalwila ids |
| V10 | What a dead SH session returns (observed naturally) |
| V11 | The SH Salesperson field |
| V12 | Can SH lists be sorted by change time? |
| V13 | The SPS per-minute limit (published figure or one observed 429; never flood) |

**G3. Live TEST write** (the user is told first; at a quiet hour):
1. Turn writes on for the test.
2. Create a TEST project (the coordinator does it; or the portal, if S1b is built).
3. Create one TEST job order marked "TEST – do not produce" and record **V2**: payload accepted? status? approval? confirm endpoint? can it be created without a project? are salesperson/delivery needed? the real 201 body. V4–V6 only if their slices are built.
4. Delete the TEST records by hand.
5. Dashboard check: deleted job orders stay on the dashboard until its not-found code is recorded (`client.js:6-7`, `zoho-sync.js:380-381`, `line-jobs.js:134`). Run G3 before the dashboard goes live, or after that code is recorded.
6. Turn writes off until the trial.

---

## 15. Non-goals
- N1: No writes to SH Zoho.
- N2: No SH sales orders, picklists or packages.
- N3: No edits after `so_created`.
- N4: No automatic routing.
- N5: No pricing, finance, payables or overdues.
- N6: No SH sign-in automation.
- N7: No messaging.
- N8: No dashboard code changes.
- N9: No item variants.
- N10: No mobile app.
- N11: No ClickUp link.
- N12: No individual fulfilment logins during the trial.
- N13: No SH `api` adapter code.
- N14: No changes to the :9333 tools.
- N15: No `api` project mode in S1.
- N16: **No automatic restore detection.** Restore safety relies on the §7.5 runbook and the `restore_pending` toggle.

---

## 16. Failure modes and required handling

| failure | detection | system response |
|---|---|---|
| Double submit or approve | unique keys | one order, one write |
| Same new Job No twice (S1b) | name key | one project |
| Restart: create `pending` | startup | `never_sent`; entity goes back |
| Restart: confirm `pending` | startup | re-queued |
| Restart: `in_flight` | startup | `unknown` → reconcile |
| **DB restored** | **none automatic**: the human follows the §7.5 runbook | `restore_pending` (CLI before start) and/or env writes off → Reconcile refs (L29, whole window) → admin clears. The ref check is not relied on by itself |
| Ref already in Zoho before POST | forced delta + mirror | L28 |
| Lease busy | 30 s wait | "sync busy, retry"; no write |
| Job order lands as draft | status rule | confirm |
| Confirm fails | 4xx | stays draft; retry |
| Write timeout / 5xx | exception | `unknown` |
| Write 4xx | code | `failed`; same ref on retry |
| Project write fails (S1b) | ledger | `accepted` |
| Item inactive | pre-check | no write |
| Request rejected | manager | L12/L14b; `request_rejected` |
| Concurrent decisions | version | 409 |
| SPS 401 | client | approvals off |
| Caps reached | counters | reads stop, then writes stop |
| Per-minute 429 | status | cycle stops; write `failed` |
| Malformed reply | shape | run failed |
| SH stop states | §8.3 | persisted |
| Bad upload / disk full | | 415 / 507 |
| SQLITE_BUSY | | 503 |
| Weekly job missed | startup | generated once |
| Write token revoked | 401 | `failed (auth)`; reads unaffected |

---

## 17. Observability
- **Logs:** `sync_cycle`, `cycle_skipped_busy`, `forced_delta {reason, calls, waited_ms, outcome}`, `zoho_write`, `status_rule`, `ref_found_before_post`, `restore_pending_set {by, via: ui|cli}`, `restore_pending_cleared`, `restore_reconcile {matched, moved, listed}`, `sh_state_change`, `budget` (hourly), `login`, `upload_rejected`, `startup_recovery`.
- **Admin screen:** runs, counters, ledger, drafts, restore toggle and the reconcile report, SH state, mode.
- **A human confirms it worked by:**
  1. the job order in SPS shows the correct fields, Job No and Portal Ref, and its status is not Draft;
  2. it appears on the dashboard (once the dashboard is live);
  3. health is OK, with `restorePending=false` and `draftsAwaitingConfirm=0`;
  4. it appears in the weekly report.

---

## 18. Rollback plan
1. **Stop writes:** revoke the write token, or set writes off in the env and restart (human).
2. **Stop the portal:** the admin exports `open-lines.csv`, then the human runs `pm2 stop order-portal`. The WhatsApp group keeps running in parallel the whole time.
3. **Bad release:** `shdeploy rollback order-portal` restores code only (`shdeploy:209`), so migrations must be additive. A DB restore is a separate manual step, and the **§7.5 runbook is mandatory**: `restore_pending` on (CLI, before start) and/or writes off → Reconcile refs → clear.
4. **Zoho records** stay. Export the `done` writes for review. The portal never deletes anything in Zoho.
5. Nothing else needs reverting.

---

## 19. Assumptions and risks
**Assumptions:**
- Custom fields can be set by `customfield_id` with lookup ids (V2).
- About 100 changed details a day.
- SH stock per location is visible (V9).
- Salespeople work outside the office (OQ10).
- The 2,706 figure is unverified (`PLAN.md:40`).
- A single token can be revoked (V7); otherwise use env plus restart.

**Risks:**
- **Per-minute rate:** the portal (≤50/min) plus the dashboard (≤100/min, `client.js:9`) is about 150/min against an unknown org limit (V13). If V13 is lower, lower the portal throttle to keep the total ≤80%. The first live read waits for V13.
- **Write reserve:** about 33 job orders a day. Watch the `budget` log.
- **Refresh-token cap:** unverified (G1 step 5).
- **Restore runbook:** depends on a human following §7.5. If someone restores the DB and starts the service with writes on and no toggle, a re-approval could create a duplicate job order. This is mitigated by OQ24 (only named people restore), the printed runbook, and the pre-POST ref check, which still catches anything inside its 24 h window.

---

## 20. Open questions (suggested answer → what it blocks)
- **OQ5:** Which SH locations count as Kohalwila stock? → *The ones Rizwan's team picks from; V9 lists them.* **S2.**
- **OQ20:** Pause full SH pulls while the reader runs? → *Yes.* **S2.**
- **OQ7:** What do SP-/CP- mean? → *An admin list seeded with SP, CP.* **S3.**
- **OQ19:** Which field holds the cost? → *`purchase_rate`; no item rate.* **S3.**
- **OQ8:** Who creates SH customers? → *The customer-master owner; Rizwan's team until one is named.* **S4.**
- **OQ9:** Should the portal create SPS contacts? → *Yes, name only.* **S4.**
- **OQ18:** More artwork formats? → *Not in the trial.* **S5.**
- **OQ12:** Report format? → *Page + CSV + print-to-PDF.* **S6.**
- **OQ11:** Dashboard cap ≤4,500? → *Yes.* **G1.**
- **OQ22:** Who owns the write token? → *The user's SPS admin login.* **G1.**
- **OQ6:** Is the division field rule right? → *Confirm with the managers.* **Trial start.**
- **OQ10:** Hostname? → *`orders.standard-holdings.lk`.* **Trial start.**
- **OQ13:** People lists? → *The user supplies them.* **Trial start.**
- **OQ21 (P3):** Office fixed IP? → *Restrict to it if one exists.* **Trial start.**
- **OQ24:** Who may restore the portal DB, and how is the §7.5 runbook enforced? → *Only the user restores. The runbook goes into the shdeploy restore notes and `docs/RESTORE-RUNBOOK.md`. Step 1 (CLI toggle and/or env writes off) always comes before the first start on a restored DB.* **Trial start** (procedure only).
- **OQ23:** P1, P2, P4 → *accept.* Not blocking.
- **OQ17:** Does sales still create the SH SO? → *Yes during the trial.* Not blocking.

VERDICT: READY. **S0 and S1 have no open blocker** for building and testing against the fake Zoho. S1b waits on V3. The trial waits on G1–G3 and on OQ6, OQ10, OQ11, OQ13, OQ21, OQ22 and OQ24. S2–S6 each start once their listed questions are answered.
