# Customized-items order portal (SH sales → Rizwan's team decides → stock or SPS production)

Prepared by Abdul Hadhee | IT Executive · 17 Oct 2026 · **Rev 3** (user answers and the user's design change of 17 Oct applied: routing is now a manual decision by Rizwan's team; P0 done; plan-critic round 1 = BLOCK, round 2 = APPROVE-WITH-CHANGES, handled in §12; **Rev 3 needs a fresh plan-critic round** because the flow changed) · Status: DRAFT, blocked on Q6 and Q10 · Verdict at the end

Shorthand used below:
- `R01`–`R05` = `/root/Project Management/reports/2026-10-17-custom-order-portal/0{1..5}-*.md` (`R05` = `05-p0-stock-by-location.md`)
- `FC` = `.../2026-10-17-custom-order-portal/fact-check.md`
- `SUM` = `.../data/stock-routing-summary.json`; `LOC` = `.../data/stock-by-location-summary.json` (P0)
- `MGR` = `wiki/specs/2026-10-08-pd-managers-full-release.md` (the managers' release: side panel + web `/jobs`)
- `DES` = `wiki/specs/2026-09-17-production-dashboard-design.md` (authoritative dashboard spec, REPO `CLAUDE.md`)
- `PM` = `reports/2026-09-25-sps-business-plan/projects/order-portal/PROJECT-MEMORY.md`
- `REPO` = `/root/dev/production-dashboard`
- `UA` = the user's answers and design change of 17 Oct 2026, quoted in §11 Decisions (summary at `/root/CLAUDE.md:38`)

Where FC reports a MISMATCH, this spec uses FC's value: 862 distinct items, not 926. The customer seed uses **640** distinct names (FC #7, CONFIRMED).

---

## 0. Readings of the request (ambiguity register)

The request: *"an Order Portal only for the customized items so Sales Team can order through it and it will be sent to Rizwan's team if the items are already in stock, if not it will be shared to the production managers."* Refined by the user (DQ5): *"the sales person creates and send the order through our portal and with the common login we give to rizwans team decides whether its in stock or send to production they click a button to send and then the production teams sees the order in queue and click a button and it will be on their Production Dashboard"*.

| # | Phrase | Possible readings | Assumed / decided | Why |
|---|---|---|---|---|
| A1 | "customized items" | (a) items with `CF.Finished Good Type` = Customized; (b) orders with `CF.Order Type` = Customized Order (R03 §2) | **(a) item flag** (assumed) | The form needs an item list, and only (a) gives one. |
| A2 | who decides "in stock" | (a) the portal, from a stock read; (b) Rizwan's team, by hand | **(b) by hand — decided, DQ5** | User's design change. P0 (§1) supports it: the stock data could cover only 3–8% of lines and cannot match 20%. |
| A3 | "Rizwan's team" | SH stock holders / pickers / Food Packaging desk (R04 C2) | **SH fulfilment team** (SH SO picklist, packing, dispatch prep), one shared login with role `sh_stores` — **decided, DQ1, DQ6** | Not the existing `stores` role, which belongs to SPS stores (Ilham, DES:154). |
| A4 | "on their Production Dashboard" | (a) a full dashboard job; (b) a visible entry in the managers' feed until an SO exists | **(b)** a "Requests (no SO yet)" section (§3.7) (assumed) | A dashboard job is one SPS SO line (`MGR:499`, `MGR:63`); a portal line has no SO yet. Needs MGR's owner to accept the change (Q10). |
| A5 | "click a button" (production) | Accept only, or Accept/Decline | **Accept**, plus "send back to Rizwan's team" with a reason and "hand to Unassigned" for a wrong unit (assumed) | Coordinator's instruction; no dead ends (round-2 finding 2.10). |
| A6 | "customer first, then items" | filter items by name text, or by order history | **by order history** (`portal_catalogue_customers`, §6), with a "show all items" fallback (assumed) | Bracket text in names is not reliable; history is data we hold. |

## 1. Problem

Today SH sales staff ask for customized items outside any system. When SH has no stock, the order is posted to the WhatsApp group "SH MANUFACTURING ORDER REQUEST", where the production managers pick it up and their coordinators raise the SPS SO in Zoho (UA). The Zoho record cannot tell who asked or for whom:
- the Zoho customer is SH on 10,594 of 10,596 lines (R01:114; FC did not re-check);
- `Sales Person` is blank on 84.7% of customized lines; `Source` and `Sales Channel` are constants (FC #24);
- the real end customer is free text with 640 spellings (FC #7).

Customized production lines wait a median of 18 days (p80 29) to first shipment (R03 §5, FC #19). Nobody can see where an order is between the WhatsApp post and the SPS SO.

**Why the stock decision stays manual (P0, R05, LOC; SH snapshot 28 Sep 2026, stale, shape only).** Basis 1,269 items / 3,527 customized lines of the 12 months to 25 Sep 2026; free stock = Σ `location_actual_available_for_sale_stock`; FULL = covers the item's typical order.

| View | FULL | UNKNOWN (no SH name match) | UNIT_MISMATCH |
|---|---|---|---|
| Set (a) Southern + Central + 3PL DWW, strict unit | 38 lines = 1.1% | 20.1% | 47.0% |
| Set (a), alias nos=pcs=piece=pieces=each | 69 = 2.0% | 20.1% | 17.7% |
| Set (b) = (a) + `SPS Kohalwila Factory (Warehouse)`, strict | 112 = 3.2% | 20.1% | 47.0% |
| Set (b), alias | 271 = 7.7% | 20.1% | 17.7% |

Rule "SH-own end customer → production" = 106 lines (3.0%); it changes set (b) alias FULL only from 271 to 264 (7.5%). The identity `stock_on_hand − actual_committed = actual_available_for_sale` holds on all 113,670 location rows. So an automatic rule would send over 90% of lines to production anyway, and could not judge one line in five. Rizwan's team knows its shelves; the portal gives them the decision and records it. A stock hint is v1.1 (§5).

**Who is harmed:** SH sales and their customers (no status, possible waits for goods that exist); production managers (work arrives by WhatsApp with no record); everyone (no one can see where an order is).

**Desired:** sales submit one form; every line lands in Rizwan's team's queue; they press "Fulfil from stock" or "Send to production"; the unit's pair accepts it and sees it on their dashboard until the coordinator links the SPS SO. The requester sees a plain-word status at every step.

## 2. Current behaviour (with file:line evidence)

**Process today (UA; `/root/CLAUDE.md:38`)**
- In stock: Rizwan's team works from the SH sales order (picklist, packing, dispatch prep). Customized stock sits mostly at SH Kohalwila; Galle and HO orders are supplied from Kohalwila by Zoho transfer order, arranged by Rizwan's team.
- Not in stock: the order goes to the WhatsApp group "SH MANUFACTURING ORDER REQUEST"; production managers add it to a job; their coordinators create the SPS SO.

**Data**
- End customer is free text in `CF.Order Received from`; SH is the value on 5,075 lines (FC #6); 640 distinct values (FC #7).
- A customized item is customer-specific: 1,186 of 1,257 live items carry the customer in brackets (R01 §2; FC #5). Top 100 items hold 25.2% of lines (FC #3).
- Customized SO volume: mean 7.7 SOs/day, p95 20, max 35; 70.2% of orders have one line; the most is 5 (FC #17, #18).
- 12.2% of last-12-month production lines resolve to PCU, which has no manager; 0.6% are unresolved (FC #14; `MGR:183`).
- `customized-catalogue.csv` gives the modal `base_material` with a count suffix (row 2: `Sub Outsourced-SP-Chicken Bucket (Keells) (30)`), and only `*_ever_not_available` flags for artwork, dye and screen.
- `end-customers.csv` holds case-only duplicates (row 238 `The brownie Station`, row 266 `The Brownie Station`). FC #7 counts 8 groups.

**Code (`REPO`)**
- `server/db/migrations/001-schema.sql:132-140`: table `orders` (`order_no` = `'OR-'||printf('%06d',id)`, `requester_id`, `team_id NOT NULL`, free-text `customer`, `order_type CHECK IN ('customised','ex_stock','internal')`, `created_via CHECK IN ('portal','on_behalf')`).
- `001-schema.sql:141-145`: `order_lines` (free-text `item_description`, `qty`, `unit`; no item id).
- `001-schema.sql:337-340`: **`orders` and `order_lines` are append-only** (triggers abort UPDATE/DELETE). This design only INSERTs into them; all state lives in `portal_line_events`.
- `001-schema.sql:280-285`: `order_events.event` has a fixed CHECK with no portal events; 001 is frozen (REPO `CLAUDE.md`).
- `001-schema.sql:93`: `users.roles` is JSON with only a `json_valid` CHECK.
- `shared/schemas.js:2`, `web/src/admin/Users.tsx:10`: `ROLES` contains `stores` (= Ilham, SPS stores, DES:154; drives SPS shipments, DES:421-425).
- `server/auth/middleware.js:83-84`: `requireRole(...roles)` → 403 `{error:'forbidden'}`; `middleware.js:76`: no session → 401; `middleware.js:21-24`: Origin check on writes (the CSRF guard); `server/auth/password.js:4-21`: scrypt hashes; `server/routes/auth.js:5,41`: login rate limiter, counted before the scrypt check.
- `server/routes/index.js:9`: every router is mounted at `/api`; routers guard sub-paths with a path-scoped `r.use('<prefix>', requireRole(...))` (e.g. `routes/admin-config.js:88`, `r.use('/admin', requireRole('admin'))`).
- `001-schema.sql:115-119`: `division_pairs(division_code, manager_user_id, coordinator_user_id, active)`.
- `001-schema.sql:4-14` + `005-line-jobs.sql:2-13`: the read-only SPS SO mirror (`zoho_so_headers`, `zoho_so_line_items` with `item_id`).
- `server/zoho/client.js:1,5`: the only Zoho client; GET-only, SPS org only, no items/stock scope.
- `server/services/line-jobs.js:44-63`: `resolveHomeUnit({tag, header, cfBu}, rules, activeUnits)` → `{home, …}`; `home` NULL for the OPD bucket with no tag (line 59).
- In-app push exists through SSE for the web app (`server/services/sweep.js:85`, `server/app.js:22`).
- `package.json:20-32`: no mail library. `package.json:24`: better-sqlite3 (synchronous). `package.json:29`: Express `^5.2.1`.
- Migrations present: 001–006 + MANIFEST.json; 007 (MFA) claimed, no file (FC #27; R04 C11).

**Managers' release (MGR, not deployed)**
- One job = one SPS SO line, `(org, line_item_id)` (`MGR:63`, `MGR:499`); the 001 `jobs` tables are not used.
- Managers work in a Chrome side panel ("My jobs" feed) and the web `/jobs` page, both built from `web/src/feed/` (`MGR:926`, §10.5 at `MGR:1006-1028`), fed by `GET /api/jobs` (`MGR:727-751`).
- No push to the add-on: the panel polls every 15 s while visible (`MGR:38`, `MGR:1026`).
- MGR §14 non-goals include "**Jobs without an SO**", "**Parallel units, accept/decline**" and "A live push channel to the add-on … and any new server event type" (`MGR:1518`, `MGR:1527`, `MGR:1529`).

## 3. Proposed behaviour

### 3.1 Shape

```
SH sales person (own login, role requester, team "SH Sales")
  │  1 pick end customer → 2 that customer's items (or "show all") → qty, date, notes, flags
  ▼
POST /api/portal/sales/orders   (one transaction; idempotent on (requester, client_token))
  ▼
RIZWAN'S TEAM queue (one shared login, role sh_stores; "your name" pick on every action)
  ├─ Fulfil from stock (SH doc ref) ─> Dispatched            [their Zoho work: SH SO, picklist, transfer order]
  ├─ Send back to sales (reason)                              [terminal]
  └─ Send to production ─> home unit resolved
          ├─ unit has an active pair ─> PRODUCTION queue of that pair
          └─ no unit / no pair ──────> UNASSIGNED (admin, gm) ─> Move to unit
PRODUCTION queue (manager + coordinator of the unit)
  ├─ Accept ─> "Requests (no SO yet)" on their Production Dashboard ─> coordinator raises SPS SO in Zoho ─> Link SO
  ├─ Send back to Rizwan's team (reason)  (also after Accept)
  └─ Hand to Unassigned (wrong unit, reason)
```

The portal writes nothing to Zoho. Galle/HO supply by transfer order is Rizwan's team's Zoho work (DQ2).

### 3.2 Module, not a new service

The portal is a module of the production-dashboard app: PM2 `production-dashboard`, port 4300 (PM:14-18; REPO `CLAUDE.md`: "Release 1 of it is the order portal"). Rejected alternative: a separate service (the inventory system, port 4400), which would need its own auth and could not share `division_pairs` or the SO mirror. Open as D11, non-blocking.

### 3.3 Order form (sales)

Header fields:

| Field | Rule | Source / default |
|---|---|---|
| End customer (picked **first**) | required. Pick from `portal_customers`, or type a new name of 2–120 chars. A typed name whose `name_key` (§6) matches an existing row reuses it; otherwise an `unreviewed` customer is created | seeded from `portal-customers.csv` |
| Required date | required, ≥ Colombo today + 1 | |
| Customer PO / reference | optional, ≤ 60 chars | |
| Deliver to | required: `sh_warehouse` or `customer` | |
| Notes | optional, ≤ 1,000 chars (e.g. the SH branch: Galle, HO) | |

Line fields (1–`portal.max_lines` lines, default 10; history maximum 5, FC #18):

| Field | Rule | Default |
|---|---|---|
| Item | after a customer is picked, the list shows that customer's items from `portal_catalogue_customers` (orderable only, newest `last_order_date` first, filtered by typed text). A "show all items" switch searches every `orderable=1` row by name; a new customer has no history, so the switch starts on. "Item not in list" takes free text, 5–300 chars. The server does not require the item to be in the customer's list | |
| Quantity | required, > 0 and ≤ 10,000,000, up to 3 decimals | `median_qty` shown as a hint only |
| Unit | read-only from the catalogue; free text ≤ 20 chars for a new item | |
| Job nature | required: Reorder / New Order / Reorder With New Design / Rework | |
| Base material | required, ≤ 200 | `default_base_material` |
| Other material | optional, ≤ 200 | `default_other_material` |
| Artwork / Dye cutter / Screen-plate | each required: Available / Not Available / Not Applicable | `default_artwork` / `default_dye_cutter` / `default_screen_plate` (unselected if NULL) |

No price is shown (`Item Price` is an SH-internal transfer price, R01 §5.10). No attachments in v1.

### 3.4 Line lifecycle (normative)

Status = the latest `portal_line_events.event` of the line.

```
submitted ─> to_stores ─┬─> stores_fulfilling ─┬─> stores_dispatched (terminal)
     ▲                  │                      └─> routed_production | routed_unassigned   ("cannot fulfil after all")
     │                  ├─> returned_to_sales (terminal)
     │                  └─> routed_production | routed_unassigned
     │                                      routed_production ─┬─> production_accepted ─┬─> so_linked (terminal)
     │                                                         │                        └─> returned_to_stores ─> to_stores
     │                                                         ├─> returned_to_stores ─> to_stores
     │                                                         └─> routed_unassigned (wrong unit)
     │                                      routed_unassigned ─> admin_moved ─> routed_production
cancelled (requester; terminal) from to_stores | routed_production | routed_unassigned
```

Every non-terminal state has an exit: `to_stores` (fulfil, send to production, send back to sales, cancel); `stores_fulfilling` (dispatched, send to production); `routed_production` (accept, send back, hand to Unassigned, cancel); `production_accepted` (link, send back); `routed_unassigned` (move, cancel).

Actions (each one DB transaction; a wrong starting state → 409 `bad_state`, nothing written):

| Action | Who | From | Writes | Input |
|---|---|---|---|---|
| Submit | requester | — | `submitted`, `to_stores` per line | form |
| Fulfil from stock | sh_stores | `to_stores` | `stores_fulfilling` | `sh_doc_ref` 1–40 chars (e.g. the SH SO no.), member |
| Dispatched | sh_stores | `stores_fulfilling` | `stores_dispatched` | member |
| Send to production | sh_stores | `to_stores`, `stores_fulfilling` | `routed_production` (`reason_code='sent_by_stores'`, `unit_code`) or `routed_unassigned` (`no_home_unit` / `no_manager`) | member |
| Send back to sales | sh_stores | `to_stores` | `returned_to_sales` | reason note ≥ 5 chars, member |
| Accept | the line's unit pair | `routed_production` | `production_accepted` | — |
| Send back to Rizwan's team | the line's unit pair | `routed_production`, `production_accepted` | `returned_to_stores` (note), then `to_stores` | reason note ≥ 5 chars |
| Hand to Unassigned | the line's unit pair | `routed_production` | `routed_unassigned` (`returned_by_production`, `unit_code` NULL, note) | reason note ≥ 5 chars |
| Link SPS SO | the line's unit pair (coordinator expected, DQ4) | `production_accepted` | `so_linked` (`so_number`) | SO number; note if item differs |
| Move to unit | gm, admin | `routed_unassigned` | `admin_moved`, then `routed_production` (`reason_code='admin_moved'`) | unit |
| Cancel | the requester (own line) | `to_stores`, `routed_production`, `routed_unassigned` | `cancelled` | — |

Rules:
- **Home unit** for Send to production = `resolveHomeUnit({tag: line_tag, header: header_division, cfBu: cf_bu}, rules, activeUnits).home`, the dashboard's function and settings. NULL → `routed_unassigned` / `no_home_unit`. A unit with no `division_pairs` row `active=1` → `routed_unassigned` / `no_manager` with `unit_code` set (PCU today, MGR:183). A new-item line has no catalogue row, so it goes to Unassigned with `no_home_unit`.
- **Link SO:** the SO number must exist in `zoho_so_headers` (org `SPS`), else 409 `so_not_in_mirror` with the mirror's last sync time. If `zoho_so_line_items` for that SO has no line with `item_id = catalogue_item_id` (or the line is a new item), the link needs a note ≥ 5 chars, stored as `item_mismatch: <note>`; without it, 409 `item_not_on_so`. One SO may link several lines.
- **"Member" (shared-login name pick, DQ6):** when `portal_team_members` has ≥ 1 active row, every sh_stores action needs `member_id` of an active row, else 400 `member_required` / `member_invalid`, nothing written. With no active rows, `member_id` is NULL. The event stores `actor_id` (the shared user) **and** `member_id`.
- v1 derives no status from the mirror after linking.

Requester labels: "With Rizwan's team", "Rizwan's team is supplying from stock (<ref>)", "Sent from SH stock (<ref>)", "Returned by Rizwan's team: <reason>", "Waiting for production – <unit>", "Accepted by production – <unit>", "Waiting for a unit", "In production (SO <no>)", "Cancelled".

### 3.5 Who can do what

| Role | Who | Can |
|---|---|---|
| `requester`, team "SH Sales" | SH sales staff, individual logins (names: Q7) | create orders; see their own orders; cancel own lines (§3.4) |
| **`sh_stores`** (new value) | **one shared account** for Rizwan's team (DQ1, DQ6) | see the `to_stores` and `stores_fulfilling` queue (with notes from production on returned lines); Fulfil, Dispatched, Send to production, Send back to sales |
| `manager` / `coordinator` | the unit's pair in `division_pairs` | see `routed_production` and `production_accepted` lines of units they are paired to; Accept, Send back, Hand to Unassigned, Link SO |
| `gm`, `admin` | GM, IT | Unassigned list; Move |
| `admin` | IT | imports (catalogue, customers, catalogue-customers); catalogue/customer edits; team-member list; portal settings; health page; open-lines CSV |

**Shared account rules (DQ6):**
- **Audit risk, stated plainly:** actions by a shared account cannot be traced to one person by authentication. The name pick is self-declared: it records who *says* they acted, not who did. Anyone who knows the password can act as the team. This is the user's decision; the name pick is the suggested mitigation, not a control.
- The account is an ordinary `users` row. **No auth rule changes for it:** same scrypt hashing (`password.js`), sessions and lifetime, Origin check (`middleware.js:21-24`), login limiter (`routes/auth.js:41`), `must_reset`. No file in `server/auth/` mentions `sh_stores` (AC15).
- A user holding `sh_stores` may hold no other role (AC15), so the shared password can never unlock admin, production or SPS stores actions.
- The admin changes the shared password when a team member leaves (§8 checklist).

**`sh_stores` is not `stores`.** Append `'sh_stores'` to `ROLES` in `shared/schemas.js:2` and `web/src/admin/Users.tsx:10` (code change; `users.roles` has only a `json_valid` CHECK). Portal routes check `sh_stores` and never `stores`.

### 3.6 Routes (normative; AC14 uses this exact list)

Five new router files, each added to `server/routes/index.js` at mount `/api`, each starting with one path-scoped guard `r.use('<prefix>', requireRole(...))` in the `admin-config.js:88` style. `:o` = `order_no`, `:l` = `line_no`.

| File | Guard (first middleware) | Routes |
|---|---|---|
| `portal-sales.js` | `r.use('/portal/sales', requireRole('requester'))` | `POST /api/portal/sales/orders`; `GET /api/portal/sales/orders`; `GET /api/portal/sales/orders/:o`; `POST /api/portal/sales/orders/:o/lines/:l/cancel`; `GET /api/portal/sales/customers`; `GET /api/portal/sales/customers/:id/items` |
| `portal-stores.js` | `r.use('/portal/stores', requireRole('sh_stores'))` | `GET /api/portal/stores/queue`; `GET /api/portal/stores/members`; `POST /api/portal/stores/lines/:o/:l/fulfil`; `POST …/dispatched`; `POST …/to-production`; `POST …/return-to-sales` |
| `portal-production.js` | `r.use('/portal/production', requireRole('manager','coordinator'))`, plus a pair check in each line handler (403 when the user is not in the line's active pair) | `GET /api/portal/production/queue`; `GET /api/portal/production/requests`; `POST /api/portal/production/lines/:o/:l/accept`; `POST …/return-to-stores`; `POST …/to-unassigned`; `POST …/link-so` |
| `portal-unassigned.js` | `r.use('/portal/unassigned', requireRole('gm','admin'))` | `GET /api/portal/unassigned`; `POST /api/portal/unassigned/lines/:o/:l/move` |
| `admin-portal.js` | `r.use('/admin/portal', requireRole('admin'))` | `POST /api/admin/portal/imports/catalogue`; `POST …/imports/customers`; `POST …/imports/catalogue-customers`; `GET`/`PUT /api/admin/portal/settings`; `PATCH /api/admin/portal/catalogue/:itemId`; `POST /api/admin/portal/catalogue/:itemId/reset`; `PATCH /api/admin/portal/customers/:id`; `GET`/`POST /api/admin/portal/members`; `PATCH /api/admin/portal/members/:id`; `GET /api/admin/portal/health`; `GET /api/admin/portal/open-lines.csv` |

No other file registers a path containing `/portal`.

### 3.7 "On their Production Dashboard": the smallest change (a change request to MGR; Q10)

- **What:** after Accept, the line appears in a **"Requests (no SO yet)"** section at the top of the managers' feed (`web/src/feed/`, so both the side panel's "My jobs" and the web `/jobs` show it). One card per `production_accepted` line of the viewer's units: order no, end customer, item, qty + unit, required date, job nature, artwork/dye/screen, notes, accepted by/at, and a **Link SO** control that calls `POST /api/portal/production/lines/:o/:l/link-so`. Hidden when empty. After linking, the card leaves; the SO's lines then appear as normal jobs through the existing sync.
- **Data:** `GET /api/portal/production/requests`, a separate read. Nothing is added to `GET /api/jobs`, JobDTO, counters, chips, Unassigned, or the job tables. It refreshes with the panel's existing 15 s poll; no push to the add-on (MGR C2 kept). It uses the same auth as `GET /api/jobs`, so the extension bearer works.
- **Conflict with MGR (not edited here):** MGR §14 lists "Jobs without an SO" and "accept/decline" as non-goals (`MGR:1527`, `MGR:1529`), and §10.5 fixes the panel's content (`MGR:1006-1028`). The section is not a job and Accept happens in the portal, but the panel does show pre-SO work. **MGR's owner must accept this change (Q10)** before AC22 is built, and MGR §10.5/§14 must then be amended in its own revision. The rest of the portal does not depend on Q10: the portal's own production page lists the same requests.

### 3.8 What is read

| Data | Source |
|---|---|
| SPS SO headers/lines (Link check only) | existing dashboard mirror, synced by the dashboard (MGR) |
| Catalogue, customers, customer↔item history | admin import of CSVs from `scripts/build_portal_import.py` (§6) |
| SH stock, SPS stock | **not read in v1** (v1.1 stock hint, §5) |

No new Zoho calls, no new OAuth scope, no write to Zoho or the mirror. SH and SPS figures are never added together.

### 3.9 Notifications (no WhatsApp)

- In-app SSE (existing web stream) `{type:'portal_line', order_no, line_no, status}` on every event except `submitted`:
  - `to_stores` → users with `sh_stores` (never `stores`);
  - `routed_production` → that unit's active manager and coordinator;
  - `routed_unassigned` → admin and gm;
  - `cancelled` → the audience of the line's state at cancel time (rules above);
  - every event → the requester.
- The side panel gets no push (MGR C2); its Requests section polls (§3.7).
- Queue badges are computed from the DB on page load, so a missed event loses nothing.
- **No email, SMS or WhatsApp sending of any kind** (no mail library, `package.json:20-32`; PM:108-111). The production queue replaces the "SH MANUFACTURING ORDER REQUEST" group; running the group in parallel during the pilot is a human practice (Q7).

## 4. Acceptance criteria

Fixture "F": requesters A and B (team "SH Sales"); U_sh = the shared account (role `sh_stores` only); U_sps (role `stores` only); active pairs SHPS = Mubeena (manager) + Madushi (coordinator), PACKPRO = Ishan + Umanda; PCU has no active pair; catalogue X (`line_tag='Screen Printing Unit'` → SHPS), X2 (resolves to PCU), X3 (OPD bucket, no tag → home NULL); customer C1 with history for X and X2; team members M1, M2 active, M3 inactive.

**Submit (sales)**
- **AC1:** Given F, when A submits C1 with X qty 400 and X2 qty 50, then 201 with `order_no` matching `^OR-\d{6}$`; each line has `submitted` then `to_stores`, written in one transaction; U_sh receives one SSE event per line; U_sps receives none.
- **AC2:** Idempotency. (a) Two POSTs from A with the same `client_token` and identical body, sequentially and with `Promise.all` → exactly one `orders` row, one 201 and one 200 with the same `order_no`, never 500; a test hook that forces `SQLITE_CONSTRAINT_UNIQUE` on `ux_orders_requester_token` gets 200 (same hash) or 409 (different hash). (b) Same token, different body → 409 `client_token_reused`, nothing written. (c) B with A's token → a new order (201, different `order_no`), nothing of A's order in the response.
- **AC3:** 400 with a field-keyed error and no rows written when: 0 lines or more than `portal.max_lines`; qty ≤ 0 or > 10,000,000; required date < Colombo today + 1; a missing artwork, dye, screen or job-nature value; `deliver_to` ∉ {sh_warehouse, customer}.
- **AC4:** A line for a catalogue row with `orderable=0` → 400 `item_not_orderable`, nothing written.
- **AC5:** A failure injected after the `order_lines` insert → no `orders`, `order_lines` or `portal_line_events` rows for it.
- **AC6:** A typed new customer "Acme Café" creates one `unreviewed` row; later orders typing "acme café", "ACME CAFÉ" or " Acme  Café " reuse it.
- **AC7:** A user without `requester` → 403 on every `/api/portal/sales/*` route, nothing written.
- **AC8 (customer first):** `GET /api/portal/sales/customers/C1/items` returns X and X2 only (orderable, newest `last_order_date` first); with `all=1&q=<text>` it returns every orderable item whose name contains the text, case-insensitive; for a customer with no history it returns `[]`. Submitting C1 with an item outside C1's list succeeds.

**Rizwan's team (shared login)**
- **AC9:** Given a `to_stores` line, U_sh Fulfil with `sh_doc_ref='SO-SH-1'` and `member_id=M1` → `stores_fulfilling` with that ref, `actor_id`=U_sh and `member_id`=M1; label "Rizwan's team is supplying from stock (SO-SH-1)". Then Dispatched → `stores_dispatched`, label "Sent from SH stock (SO-SH-1)". Fulfil with an empty or 41-char ref → 400.
- **AC10:** U_sh Send to production: X → `routed_production`, `reason_code='sent_by_stores'`, `unit_code='SHPS'`, and the SHPS pair gets SSE; X2 → `routed_unassigned`, `no_manager`, `unit_code='PCU'`; X3 and a new-item line → `routed_unassigned`, `no_home_unit`. The same works from `stores_fulfilling`.
- **AC11:** Send back to sales with a reason of ≥ 5 chars → `returned_to_sales`, terminal; requester label "Returned by Rizwan's team: <reason>". A reason of < 5 chars → 400.
- **AC12 (name pick):** With M1, M2 active, any sh_stores action without `member_id` → 400 `member_required`; with M3 (inactive) or an unknown id → 400 `member_invalid`; nothing written. After the admin deactivates M1 and M2, the same actions succeed with `member_id` NULL. `GET /api/portal/stores/members` returns active rows only.
- **AC13:** Wrong starting state → 409 `bad_state`, nothing written, for: Fulfil on `stores_fulfilling`; Dispatched on `to_stores`; Send to production on `routed_production`; Send back to sales on `stores_fulfilling`.
- **AC14 (role separation and guard completeness):**
  - (a) Each `/api/portal/stores/*` route returns 403 for U_sps, a requester, a manager, a coordinator, gm, and admin, and 401 unauthenticated; nothing is written. U_sh does not get 403.
  - (b) U_sps's SSE stream receives no `portal_line` event when a line enters `to_stores`.
  - (c) U_sh gets 403 on `POST /api/jobs/:id/send`, `POST /api/jobs/:id/move`, `GET /api/admin/imports`, and on every `/api/portal/sales/*`, `/api/portal/production/*`, `/api/portal/unassigned/*` and `/api/admin/portal/*` route.
  - (d) For each of the five portal routers, the test reads the method + path of every route registered on it (`router.stack`) and asserts that set **equals** the §3.6 list held literally in the test; then a user with none of the guard's roles gets 403 on every listed route. An unlisted new route fails the equality; a route without the guard fails the sweep.
  - (e) Source scans: fail if any `requireRole(` call lists both `'stores'` and `'sh_stores'`; fail if `/portal` appears in any `server/` file other than the five router files and `server/routes/index.js`.
- **AC15 (shared account kept narrow):** Creating or updating a user with roles `["sh_stores","admin"]`, `["sh_stores","manager"]` or `["sh_stores","stores"]` → 400 `sh_stores_exclusive`; `["sh_stores"]` → OK. A source scan fails if `sh_stores` appears in any file under `server/auth/`. U_sh's login attempts hit the existing limiter exactly as another user's do (the existing limiter test re-run with U_sh's username).

**Production**
- **AC16:** A `routed_production` SHPS line is in Mubeena's and Madushi's queue and not in PACKPRO's. Ishan's Accept, Send back, Hand to Unassigned and Link on it → 403, nothing written.
- **AC17:** Madushi Accepts → `production_accepted`; the line is in `GET /api/portal/production/requests` for Mubeena and Madushi; it is in no response of `GET /api/jobs` (every `at` scope) and changes no counter value.
- **AC18:** Send back to Rizwan's team with a note of ≥ 5 chars, from `routed_production` and separately from `production_accepted` → `returned_to_stores` (note) then `to_stores` in one transaction; U_sh gets SSE; the stores queue shows the note; the line leaves `requests`. A note < 5 chars → 400.
- **AC19:** Hand to Unassigned with note "belongs to PACKPRO" → `routed_unassigned`, `returned_by_production`, `unit_code` NULL; admin and gm get SSE; then an admin Move to PACKPRO works (AC23). From `production_accepted` → 409 `bad_state`.
- **AC20:** Link on a `production_accepted` line: SO `SO-123` in the mirror (org SPS) with a line `item_id = X` → `so_linked`, label "In production (SO-123)", the line leaves `requests`. SO not in the mirror → 409 `so_not_in_mirror` with the last sync time. SO without an X line: no note → 409 `item_not_on_so`; note ≥ 5 chars → `so_linked` with `note` starting `item_mismatch: `. Link on a `routed_production` line → 409 `bad_state`.
- **AC21:** After linking, mirror changes to SO-123 (`quantity_shipped`, `quantity_invoiced`, status `void`) leave the label "In production (SO-123)".
- **AC22 (dashboard section; built only after Q10):** a component test of `web/src/feed/` given 2 request rows renders a "Requests (no SO yet)" section with 2 cards showing order no, customer, item, qty + unit and required date, and given 0 rows renders no section. `GET /api/portal/production/requests` with Madushi's extension bearer and the allow-listed extension Origin → 200. With the panel visible, a newly accepted line appears within one 15 s refresh. A Link from the card produces the AC20 result.

**Unassigned, cancel, requester view**
- **AC23:** gm or admin Move of a `routed_unassigned` line to SHPS → `admin_moved` then `routed_production` (`unit_code='SHPS'`, `admin_moved`); the SHPS pair gets SSE. Move to a unit with no active pair → 409 `no_manager`.
- **AC24:** The requester's Cancel of an own line in `to_stores`, `routed_production` or `routed_unassigned` → `cancelled`, with SSE to U_sh (not U_sps), the SHPS pair, or admin + gm respectively. In `stores_fulfilling`, `production_accepted` or `so_linked` → 409 `bad_state`. Another requester's line → 403.
- **AC25:** A lists only A's orders; GET of B's order → 404.
- **AC26:** No `portal_line` event reaches a user outside the §3.9 audience (checked for U_sps, U_sh on a production line, a non-pair manager, another requester).
- **AC27 (closed lists):** `reason_code` takes only `sent_by_stores`, `no_home_unit`, `no_manager`, `returned_by_production`, `admin_moved`, and is NULL on every event that is not `routed_production` / `routed_unassigned`; an INSERT of `reason_code='stock_full'` or `event='routed_stores'` fails on the CHECK. Each of the 5 codes is produced by at least one test above.

**Imports and admin**
- **AC28:** Catalogue import upserts by `item_id`, sets `orderable=0` on rows absent from the file (never deletes), keeps `orderable` where `edited_at IS NOT NULL` until "reset to imported", and reports inserted / updated / unchanged / kept-edited / made-non-orderable counts.
- **AC29:** Catalogue-customers import replaces `portal_catalogue_customers` in one transaction; rows whose `name_key` has no `portal_customers` row or whose `item_id` has no catalogue row are skipped and counted; a failed import leaves the old table intact.
- **AC30:** `portal.enabled='0'` → every `/api/portal/*` and `/api/admin/portal/*` route except `open-lines.csv` returns 404; no nav entry; the Requests section is hidden.
- **AC31:** `open-lines.csv` has one row per line whose latest event is not terminal, with order_no, line_no, customer, item, qty, status, unit, member name (if any) and age in days.
- **AC32:** The migration applies on an empty DB and on a copy of a DB at 006 with fixture data; existing tests pass; two app start-ups apply it once (`schema_migrations` one row for N).
- **AC33 (customer seed, real data):** importing `portal-customers.csv` built from `end-customers.csv` gives 640 − K rows, K a literal constant in the test counted once by hand and equal to the builder's printed `customer_key_collisions`; "The brownie Station" (row 238) and "The Brownie Station" (row 266) are one row.
- **AC33b (customer seed, hand fixture):** a 5-row `end-customers.csv` written in the test — `Acme Café` (3 lines), `acme café` (5), ` Acme  Café ` (1), `ACME CAFE` (2), `Shangri-La` (1) — gives exactly (`acme café`, `acme café`, 9), (`ACME CAFE`, `acme cafe`, 2), (`Shangri-La`, `shangri-la`, 1) as (`name`, `name_key`, `order_lines`) and prints `customer_key_collisions=2`.
- **AC34 (builder, real data):** `python3.12 -I scripts/build_portal_import.py <Sales_Order.xlsx> <customized-catalogue.csv> <customized-stock.csv> <end-customers.csv> <OUTDIR>` writes `portal-catalogue.csv`, `portal-customers.csv` and `portal-catalogue-customers.csv` with exactly the §6 columns; no `default_base_material` ends in ` (<digits>)`; the defaults of item 4892105000000298629 equal literal values in the test, read once by hand from its latest SO line.
- **AC34b (builder, hand fixture):** a test-built `Sales_Order.xlsx` with item `I1` lines (2026-01-05, `SO-00010`, customer `Acme Café`, base `Kraft 250gsm`, artwork text `Available`), (2026-03-01, `SO-00020`, customer `acme café`, base `Kraft 300gsm`, artwork text empty + boolean `true`, dye text `Not Avaialble`), (2026-03-01, `SO-00019`, customer `Shangri-La`, base `Board`), and a catalogue row `I2` with no SO line and `base_material` `Kraft (12)`, gives: `I1` `default_base_material=Kraft 300gsm`, `default_artwork=Available`, `default_dye_cutter=Not Available`, `default_screen_plate` empty; `I2` `default_base_material=Kraft`; catalogue-customers rows exactly (`I1`, `acme café`, 2, 2026-03-01) and (`I1`, `shangri-la`, 1, 2026-03-01).
- **AC35:** Team members: the admin adds a member (name 2–60 chars, unique case-insensitive) and deactivates or reactivates one; there is no delete route; events keep the member's id and the queue history shows the name.

## 5. Non-goals (v1)

- **Automatic stock routing, stock snapshots, netting and the unit-alias table.** They move to v1.1 as an **optional stock hint**: SH free stock (default location `SPS Kohalwila Factory (Warehouse)`, plus set (a) if the user wants) shown beside each line in Rizwan's team's queue. It does not decide anything. Carried design for v1.1: a swappable reader (admin snapshot now, read-only SH API later, DQ3); fields `committed` ← `location_actual_committed_stock`, `free_to_promise` ← `location_actual_available_for_sale_stock`, `unit` ← item `unit`; per-location identity check on import; alias seed nos=pcs=piece=pieces=each; better SPS→SH item matching (admin item-link table; SKU alone matches only 104 of 184, R02) for the 20.1% UNKNOWN.
- Any write to Zoho (SH or SPS), including SOs, items, transfer orders and reservations; tracking transfer orders.
- Reading SH or SPS stock; a live SH API reader.
- Individual logins for Rizwan's team (the user chose one shared login, DQ6).
- Dashboard job rows, JobDTO fields or counters for portal lines; anything beyond the §3.7 section; any push to the add-on.
- Splitting a line between stock and production.
- Statuses derived from the mirror after `so_linked` (v1.1).
- Customer merge UI (v1.1, Q9); reason statistics; lead-time hint.
- Email, SMS or WhatsApp sending of any kind, including to the "SH MANUFACTURING ORDER REQUEST" group.
- Credit checks (OP-08), prices, attachments (OP-10), Portal Order No in Zoho (OP-12), SH-location tagging (OP-07), call-off (OP-15), a GM/COO redacted view, the triage workspace (OP-04).
- Importing historic orders; non-SH requesters; end-customer logins (`customer_portal` stays false, PM:154); creating catalogue items from "item not in list" lines; non-customized items.
- Changing `resolveHomeUnit`, `division_pairs`, the jobs model (MGR:499), or the existing `stores` role.

## 6. Data model changes

One migration, `server/db/migrations/<N>-custom-order-portal.sql`; N blocked on Q6. Additive only.
- **Forward step:** the columns, tables, triggers, indexes and settings below.
- **Idempotency:** the runner applies each N once (user_version + hash in `schema_migrations`, `003-migration-hashes.sql:4`; `migrate.js:51-71`); `IF NOT EXISTS` / `INSERT OR IGNORE` throughout.
- **No UPDATE or DELETE** against `orders` / `order_lines` (append-only, `001-schema.sql:337-340`).
- **Code change, not schema:** `'sh_stores'` in `ROLES` (§3.5).

**Columns added (nullable):**
- `orders`: `client_token TEXT`, `client_payload_sha256 TEXT` + `CREATE UNIQUE INDEX IF NOT EXISTS ux_orders_requester_token ON orders(requester_id, client_token) WHERE client_token IS NOT NULL`. Payload hash = sha256 of the body as JSON with keys sorted recursively and `client_token` removed. The handler looks up (requester, token); if absent it inserts; on `SQLITE_CONSTRAINT_UNIQUE` it rolls back, reads the stored row and answers as for a found row (equal hash → 200 with that order; different → 409 `client_token_reused`); never 500. Also `customer_id INTEGER REFERENCES portal_customers(id)`, `customer_ref TEXT`, `deliver_to TEXT CHECK (deliver_to IS NULL OR deliver_to IN ('sh_warehouse','customer'))`. Rows are written with `order_type='customised'`, `created_via='portal'`, `entered_by=requester_id`, `customer` = name snapshot, `team_id` = requester's team.
- `order_lines`: `catalogue_item_id TEXT`, `job_nature TEXT`, `base_material TEXT`, `other_material TEXT`, `artwork TEXT`, `dye_cutter TEXT`, `screen_plate TEXT`; `item_description` holds the item-name snapshot or the new-item text.
- Why reuse `orders`/`order_lines`: they exist for this purpose (`001-schema.sql:132-145`), nothing writes them yet (MGR:499 retires only `jobs`), and they give `OR-` numbers.

**New tables (each justified, with the rejected alternative):**

| Table | Columns (NOT NULL unless stated) | Why | Rejected alternative |
|---|---|---|---|
| `portal_customers` | `id PK`, `name`, `name_key UNIQUE`, `status CHECK IN ('reviewed','unreviewed')`, `created_at`, `created_by NULL` | 640 free-text spellings (FC #7) | free text in `orders.customer`; `COLLATE NOCASE` (ASCII only) |
| `portal_catalogue` | `item_id TEXT PK`, `name`, `unit`, `cf_bu NULL`, `line_tag NULL`, `header_division NULL`, `median_qty REAL NULL`, `default_base_material NULL`, `default_other_material NULL`, `default_artwork NULL`, `default_dye_cutter NULL`, `default_screen_plate NULL`, `last_order_date NULL`, `order_lines INTEGER`, `orderable INTEGER CHECK IN (0,1)`, `edited_at NULL`, `edited_by NULL`, `imported_at` | `zoho_items` has no customized flag or tags, and mirror tables are cli/import-only (`001-schema.sql:3, 67-71`) | admin-edited columns on `zoho_items` |
| `portal_catalogue_customers` | `item_id REFERENCES portal_catalogue`, `customer_id REFERENCES portal_customers`, `order_lines INTEGER`, `last_order_date`, PK(item_id, customer_id) | the user's "customer first, then that customer's items" (DQ5) | matching the bracket text in item names (unreliable; 6% of items have none, R01 §2) |
| `portal_team_members` | `id PK`, `name`, `name_key UNIQUE`, `active INTEGER CHECK IN (0,1)`, `created_at` | the name pick on the shared login (DQ6) | free-text name per action (typos, cannot be listed); individual logins (the user chose a shared login) |
| `portal_line_events` | `id PK`, `order_id`, `line_no`, `event CHECK IN ('submitted','to_stores','stores_fulfilling','stores_dispatched','returned_to_sales','routed_production','routed_unassigned','production_accepted','returned_to_stores','admin_moved','so_linked','cancelled')`, `reason_code NULL CHECK (reason_code IS NULL OR reason_code IN ('sent_by_stores','no_home_unit','no_manager','returned_by_production','admin_moved'))`, `unit_code NULL`, `so_number NULL`, `sh_doc_ref NULL`, `note NULL`, `member_id NULL REFERENCES portal_team_members`, `actor_id`, `at`, FK(order_id, line_no) → order_lines; append-only triggers `ao_u_/ao_d_portal_line_events` in the 001 style | lifecycle + audit | `order_events`: its frozen CHECK (`001-schema.sql:282`) lacks these events |

`name_key(s)` = `s.normalize('NFKC').trim().replace(/\s+/g,' ').toLowerCase()`, used for customers and members; the builder uses the same rule in Python. Accents and punctuation are not folded.

**Indexes:** `portal_line_events(order_id, line_no, id)`; `portal_line_events(event, unit_code)`; `portal_catalogue_customers(customer_id)`.

**Settings** (`INSERT OR IGNORE`): `portal.enabled` = `'0'`; `portal.max_lines` = `'10'`.

**Import contracts (CSV, UTF-8, header row, comma):**
- Regeneration chain from one SPS export date: `build_catalogue.py` → `scripts/stock_routing.py` → `scripts/build_portal_import.py` (FC #8, #9: the item masters must match).
- `portal-catalogue.csv`: `item_id`, `name`, `unit`, `cf_bu`, `median_qty`, `order_lines`, `last_order_date` (= `last_order`) from `customized-catalogue.csv`; `line_tag` = `customized-stock.csv.modal_line_tag`, `header_division` = `modal_header_division`; `default_*` from the item's latest SO line in `Sales_Order.xlsx` (Product ID = item_id; latest = max `Order Date`, ties → max `SalesOrder Number`, then last row): base ← `CF.Base Material to be Used`, other ← `CF.Additional Other Material...`, artwork/dye/screen by the R01 §5.7 merge rule (text field `CF.Artwork Availablility` / `CF.Dye Cutter Availablity` / `CF.Screen / Plate Availability`; if empty and the boolean `CF.Artwork Availability` / `CF.Dye Cutter Availability` / `CF.Screen / Plate Available` is `true` → `Available`; `Not Avaialble` → `Not Available`; anything else → NULL); no SO line → base from `customized-catalogue.csv.base_material` stripped by `\s\(\d+\)$`. `orderable` = 1 when `status='Active'` AND `order_lines>0` AND `product_type='goods'` (the builder prints the count).
- `portal-customers.csv`: `name,name_key,order_lines`; one row per `name_key` over `end-customers.csv`; `name` = the spelling with most lines (tie → first in file); `order_lines` = the sum; seeded rows are `reviewed`.
- `portal-catalogue-customers.csv`: `item_id,name_key,order_lines,last_order_date`; one row per (Product ID, `name_key(CF.Order Received from)`) over `Sales_Order.xlsx` lines whose Product ID is in the catalogue.

**Rollback step (schema):** none is run. Nullable columns and new tables are ignored by the previous code. No down-migration (it would destroy orders). Restoring the `shdeploy` pre-deploy backup is a last resort and loses portal orders entered since. `sh_stores` left in `ROLES` is harmless to old code.

## 7. Failure modes and required handling

| Failure | Detection | System response |
|---|---|---|
| Duplicate submit (double click, retry, two tabs) | unique (requester, token) + payload hash; UNIQUE error caught | same body → 200 with the first order; different → 409; never 500 (AC2) |
| Another user replays a token | per-requester index | a normal new order; nothing of the other order returned (AC2c) |
| Crash or restart mid-submit or mid-action | one transaction per action | full rollback; nothing partial; the client retries (AC5) |
| Two team members act on the same line at once on the shared login | state check inside the transaction | the second gets 409 `bad_state` (AC13); the queue refreshes |
| Shared password leaks or a member leaves | not detectable by the system | admin changes the password; actions remain attributed only by the self-declared name (§3.5 risk) |
| Member list empty | count of active members | actions allowed with `member_id` NULL (AC12); the health page shows "no name pick" in red |
| Rizwan's team says "in stock" but cannot supply | — | Send to production from `stores_fulfilling` (AC10) |
| Production gets a line it should not make, or a wrong unit | the pair sees it | Send back to Rizwan's team (AC18) or Hand to Unassigned (AC19) |
| Unit has no manager (PCU) or no home unit | §3.4 rule | Unassigned (AC10); gm/admin Move (AC23) |
| Requester cancels a line someone is working on | SSE `cancelled` | the audience is told (AC24); accepted or fulfilling lines cannot be cancelled |
| SPS SO not yet in the mirror | mirror lookup | 409 `so_not_in_mirror` + last sync time; retry after sync (AC20) |
| SPS SO raised on a different or new item | no matching SO line | link only with an `item_mismatch:` note (AC20) |
| Dashboard sync down | mirror last-sync time | Link works only for mirrored SOs; nothing else depends on the mirror |
| Side panel not refreshed / SSE dropped | DB-computed badges and 15 s poll | no lost work |
| Order also posted to the WhatsApp group during the pilot | not detectable | production may see it twice; the pilot rule (Q7) decides; the portal sends nothing to WhatsApp |
| New portal route without a guard | AC14(d)/(e) | the test suite fails |
| Catalogue item dropped from a new import | AC28 | `orderable=0`; existing lines keep their name snapshot |
| Case-only duplicate customers in the seed | `name_key` UNIQUE + builder fold | one row per key (AC33, AC33b) |
| Portal must be switched off | `portal.enabled='0'` | 404 except the open-lines CSV (AC30, AC31) |

## 8. Observability

**Logged** (existing `audit_log` via `audit()`, plus `portal_line_events`): every submit (order_no, line count, requester id); every action (event, actor_id, member_id, unit, reason_code); every import (type, counts, result); member-list changes. Customer names and quantities go to the DB only, never to stdout. No secrets logged.

**Admin page `/admin/portal/health`:** open lines by status and unit; lines older than 2 Colombo working days (Mon–Sat, `holidays`) in `to_stores`, `stores_fulfilling`, `routed_production`, `production_accepted` or `routed_unassigned`; last 30 days: count to stock vs to production vs returned to sales, and the share of stores actions with a member name; catalogue `imported_at` and orderable count; active member count.

**A human confirms it worked by:**
1. Submitting a test order as a sales user and seeing it in Rizwan's team's queue.
2. As the shared login, picking a name and pressing Fulfil on one line and Send to production on another.
3. Logging in as the SPS `stores` user and seeing no portal queue.
4. As Madushi, accepting the production line and seeing it under "Requests (no SO yet)" (after Q10), then linking a real SPS SO and seeing "In production (SO …)".
5. Checking the health page.
6. When a team member leaves: changing the shared password and deactivating the name.

## 9. Rollback plan

1. Admin sets `portal.enabled='0'` (immediate, no restart).
2. Admin downloads `open-lines.csv` and hands open lines to Rizwan's team and the managers (or back to the WhatsApp group).
3. Faulty code: the human runs `shdeploy rollback production-dashboard`; tables and columns stay and are ignored (§6).
4. DB backup restore only if the migration corrupted data; it loses orders entered since.

## 10. Fit with the existing plans

- **Replaces** OP-03's free-text form with the catalogue form and OP-04 triage with Rizwan's team's manual decision plus Unassigned (R04 §3.1, §4).
- **Adds** the `sh_stores` role and queue (no OP step had it).
- **Changes MGR** only by the §3.7 section, pending Q10; MGR itself is not edited here.
- **Resolves** R04 C1: no portal job rows; a dashboard job exists only once the coordinator raises and links the SPS SO (DQ4).
- **Keeps** the binding rules (R04 §6): Zoho read-only, no WhatsApp sending, SH/SPS never summed, additive migrations, module of production-dashboard, pipeline gates.
- **Depends on** the managers' release (mirror for Link; the feed for §3.7) and Q6. 005/006 are in dev, not deployed (`/root/CLAUDE.md` §3).
- **Kept beyond the bare request**, one line each: SO-item check on Link (catches a mistyped SO; the note removes the stuck case); the ageing list (the only detector for stuck lines); the name pick (the only trace on a shared login).

## 11. Decisions and open questions

**Decisions (made; do not re-ask).** User, 17 Oct 2026, quoted as given:

| ID | Question | User's words | What this spec does |
|---|---|---|---|
| DQ1 | Who is "Rizwan's team"? | "Rizwan's team is the SH SO picklist packaging and getting things ready to deploy and arranging the orders" | `sh_stores` = the SH fulfilment team, working from the SH sales order (picklist, packing, dispatch prep). Not SPS `stores`. |
| DQ-path | Today's no-stock path | "if they dont have a stock of that item, the order will be forwarded on SH MANUFACTURING ORDER REQUEST group where all the production managers sees the order and adds it to the job and they fulfill it." | The portal production queue replaces the group. Parallel running in the pilot = Q7. No WhatsApp sending is built. |
| DQ2 | Where customized stock is | "mostly all customized items are stored in kohalvila right for galle orders they send it to them through transfer orders and for HO the process is same" | Kohalwila holds most stock; Galle/HO are supplied by transfer order, which is Rizwan's team's Zoho work, not a portal write. In v1 it informs only the v1.1 stock-hint default location. The possible SH Kohalwila / SPS WIP double count (R02 §a) does not matter: the portal reads no stock. |
| DQ3 | How SH data is read | "we can connect through zoho's API so it can get the records" | **Conflict recorded** with the 7 Oct decision (`/root/CLAUDE.md:32`): SH data is read through the signed-in browser session (read-only) for now; SH API access is requested only after the production dashboard runs reliably or after the goods-gatepass proposal is shown. v1 reads no SH data, so this does not block. The v1.1 stock hint uses a swappable reader (snapshot now, API later). The human decides when SH API access is requested (Q3). |
| DQ4 | Who raises the SPS SO | "the production managers have coordinators under them they create the SO" | The unit coordinator raises the SPS SO in Zoho and links it; the pair's manager may also link (assumed, absence cover). |
| DQ5 | Routing | "the sales person creates and send the order through our portal and with the common login we give to rizwans team decides whether its in stock or send to production they click a button to send and then the production teams sees the order in queue and click a button and it will be on their Production Dashboard" | Manual routing by Rizwan's team (§3.4); production Accept; the §3.7 dashboard section. Automatic routing → v1.1 hint (§5). |
| DQ6 | Login for Rizwan's team | "with the common login we give to rizwans team" | One shared `sh_stores` account. Audit risk stated in §3.5; suggested mitigation = required name pick when the admin keeps a member list (the admin can leave it empty). No auth rule is weakened. |
| D14 | Unit alias table | (lead, from P0) | Superseded by DQ5: needed only for a stock comparison, so it moves to the v1.1 hint with the seed nos=pcs=piece=pieces=each. |

**Pre-steps:** P0 (`scripts/stock_by_location.py` → LOC) — **DONE 17 Oct**: actual free-stock field, rule 2 simulated, alias view, identity check (§1). It is now evidence for DQ5 and input to the v1.1 hint.

**Blocking:**

| # | Question | Suggested answer |
|---|---|---|
| Q6 | Migration number: 007 is claimed by MFA but has no file, and the contiguity lint fails on a gap (R04 C11); `/root/CLAUDE.md` §3 records "portal=008+" | Either MFA's 007 lands first and the portal takes 008, or the portal takes the next free number and MGR §8.1's claim table is updated in the same change. The human picks one. Blocks the whole build |
| Q10 | Does MGR's owner accept the §3.7 "Requests (no SO yet)" section in the managers' feed, against MGR §14 "Jobs without an SO" / "accept/decline" and §10.5? | Yes: it is not a job, adds nothing to `GET /api/jobs`, and keeps MGR's no-push rule. MGR gets its own revision. Blocks AC22 only; without it, managers use the portal's production page |

**Not blocking (defaults apply):**

| # | Question | Suggested answer |
|---|---|---|
| Q7 | Names of Rizwan's team members for the name list; the 2–3 pilot sales users; does the "SH MANUFACTURING ORDER REQUEST" group run in parallel during the pilot? | Rizwan gives the names; pilot with 2–3 sales users; the group runs in parallel for 2 weeks, and an order goes to the group only if the portal is down |
| Q5 | PCU manager (MGR Q-U) | PCU lines go to Unassigned until answered |
| Q3 | When is SH Zoho API access requested (DQ3 conflict)? | Per the 7 Oct rule; matters only for the v1.1 stock hint |
| Q8 | Who owns Unassigned lines? | GM; admin as fallback |
| Q9 | Who merges customer variants (8 groups, FC #7)? | v1.1; sales lead with the admin |
| D10 | Email notices? | No (needs SMTP and a mail library, a new dependency) |
| D11 | Module or the inventory service? | Module |

## 12. Review log

**plan-critic round 1 (17 Oct 2026): `"verdict":"BLOCK"`** (2 BLOCKING, 9 NON-BLOCKING, 1 INFO).

| ID | Finding (quoted, shortened) | Handling |
|---|---|---|
| B1 | "`stores` is not a new role … Two different teams would be merged into one permission." | **Applied.** `sh_stores` (§3.5); AC14, AC15. |
| B2 | "The headline evidence for the stores path does not hold under the spec's own default locations …" | **Applied as P0 (done):** 1.1–7.7% FULL (§1). Under DQ5 it is the evidence for manual routing. |
| N1 | "The netting rule … promises stock twice after a dispatch." | **Superseded** (no automatic routing in v1; v1.1 hint does not promise stock). |
| N2 | "The customer seed collides with its own UNIQUE constraint …" | **Applied.** `name_key`; AC6, AC33, AC33b. |
| N3 | "The catalogue import contract does not match the CSV." | **Applied.** §6 builder contract; AC34, AC34b. |
| N4 | "'Current snapshot' is undefined." | **Superseded** (no snapshot in v1). |
| N5 | "Cancellation is not pushed to the people working the line." | **Applied.** AC24. |
| N6 | "The lead-time hint keys do not match …" | Hint removed from v1 (§5). |
| N7 | "`client_token` is unique across all users … leaks across requesters …" | **Applied in part.** Per-requester index + hash 409; no cross-user 409 (it would be an oracle). AC2. |
| N8 | "Several figures and descriptions are imprecise or unverified." | **Applied.** |
| N9 | "Simpler alternative (scope) …" | **Applied.** Mirror statuses, merge UI, statistics → v1.1. |
| INFO | "Not verified: … whether SH unit strings match SPS units." | Answered by P0 (47.0% strict, 17.7% alias); now v1.1 only. |

**plan-critic round 2 (17 Oct 2026): `"verdict":"APPROVE-WITH-CHANGES"`** (two results, agents `ac029916…` and `afd9718d…`, both APPROVE-WITH-CHANGES). Handling under the Rev 3 flow:

| # | Finding (quoted, shortened) | Handling in Rev 3 |
|---|---|---|
| 2.1 | "Lines routed while the snapshot is stale stay in production for good." | **Superseded:** no stock-based routing. (A "re-check stock" action was drafted, then dropped with automatic routing.) |
| 2.2 | "The claim 'the design never over-promises within the portal' (§3.3) is false." | **Superseded:** the portal promises no stock; Rizwan's team decides. |
| 2.3 | "A production line can get stuck for good when the SO uses a different item." | **Applied.** Link with an `item_mismatch:` note (AC20). |
| 2.4 | "The reason_code list is not actually closed …" | **Applied.** CHECK on 5 named codes and 12 named events (§6); AC27. |
| 2.5 / 2.13 | (REQUIRED) "Part of AC40 is theatre." | **Applied.** §3.6 names every route and its guard; AC14 asserts 403 for `stores` and every other role on each `sh_stores` route, a `router.stack` equality test that fails on an unlisted route, and source scans. AC12-style "stale" assertion superseded. |
| 2.6 | "The import-builder precondition cannot be met as specified." | **Applied.** Regeneration chain (§6). |
| 2.7 | "Concurrency is not spelled out for AC2(a)." | **Applied.** UNIQUE error caught, rolled back, read back (§6); `Promise.all` + forced-error hook (AC2). |
| 2.8 | "Simpler alternative (scope against the request)." | **Applied:** lead-time hint dropped (no decision depends on it). The customer-first picker, earlier deferred, is now in v1 because the user asked for it (DQ5), with `portal_catalogue_customers` justified in §6. |
| 2.9 | "Not checked by FC and not checked by me …" | **Applied.** Unverified figures removed or labelled. |
| 2.10 | (REQUIRED) "The line lifecycle has a dead end … `stores_accepted`." | **Applied.** §3.4 lists an exit for every non-terminal state; stores can Send to production from `stores_fulfilling` ("cannot fulfil") and Send back to sales. |
| 2.11 | (REQUIRED) "P0 does not simulate routing rule 2." | **Applied:** P0 re-run: rule 2 = 106 lines (3.0%); set (b) alias FULL 271 → 264 (7.5%) (§1). |
| 2.12 | (REQUIRED) "Q2's suggested default … probably leaves out Rizwan's team's own stock." | **Resolved by the user** (DQ2: Kohalwila); now relevant only to the v1.1 hint. |
| 2.14 | "The snapshot contract (§6) needs a `committed` figure for each location row." | **Carried to v1.1** (§5) with the field mapping and the identity check (0 failures on 113,670 rows). |
| 2.15 | "Production has no path to correct a misrouted line." | **Applied.** Hand to Unassigned and Send back to Rizwan's team (AC18, AC19). |
| 2.16 | "AC42 and AC44 use oracles computed by the code under test." | **Applied.** Literal constants plus independent hand fixtures (AC33b, AC34b). |
| 2.17 | "Move the lead-time hint and the ageing list to v1.1." | Hint dropped; ageing list kept (§10). |

**Rev 3 summary:** the user's answers (DQ1–DQ4) and design change (DQ5, DQ6) recorded; automatic routing, snapshots, netting and the alias table moved to an optional v1.1 stock hint; the shared login and its audit risk recorded with a name pick; production Accept added, plus the §3.7 dashboard change request to MGR (Q10, with its conflict); the DQ3 conflict with the 7 Oct rule recorded. The flow changed, so **a fresh plan-critic round is required before tests are written.**

---

Prepared by Abdul Hadhee | IT Executive

VERDICT: NEEDS-INFO — Q6 migration number (007 claimed by MFA with no file), Q10 whether MGR's owner accepts the "Requests (no SO yet)" section in the managers' feed (blocks AC22 only). Open, not blocking: Q7 Rizwan's team member names, the 2–3 pilot sales users, and whether the WhatsApp group runs in parallel; Q5 PCU manager; Q3 SH API timing; Q8; Q9; D10; D11.
