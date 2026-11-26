# D-C. Full standalone app on the VPS (own Zoho mirror + portal + queues + dashboard, optional write-back)

Prepared 17 Oct 2026. Design proposal only: no live Zoho call, no credentials, nothing built. Inputs: R1-R4 in this folder and the data files in `../` (01, 02, 03, 05, fact-check). SH (org 843061977) and SPS (org 843825512) figures are never summed; each org has its own budget.
Zoho facts below carry the URL R1/R2 got them from. Where R1/R2 could not confirm something it is marked UNVERIFIED and the design does not depend on it.
Old OP-01..16, the dashboard's Zoho add-on, extension, userscripts and the tunnel-only password login are not used.

## 0. Answer in eight lines

1. Build one new Node service, `order-portal` (Express + better-sqlite3, PM2, same stack as `/root/dev/IT_Utilities_Backend/package.json`), that keeps a local SQLite **mirror** of the Zoho data it needs, and runs the sales, Stores, production and admin screens plus the production dashboard on top of that mirror.
2. The mirror is filled by **scheduled polling** of the Zoho Inventory API (one connection per org). Webhooks are an optional nudge only, because Zoho limits them to unnamed "selective pricing plans" (https://www.zoho.com/us/inventory/help/settings/automation.html).
3. Screens never call Zoho while a person waits: they read the mirror and show its age. A stale mirror removes a hint, it never blocks a decision (R3 6.3).
4. Write-back is optional and phased: SPS sales-order **draft** creation first (the user is SPS admin), SH writes only after the CEO grants SH API access. No auto-confirm, no portal transfer orders in v1 (R1 section 7).
5. API arithmetic: SPS about 520 calls on a mean day (worst plausible about 670) against 7,500/day; SH about 300 against an assumed 1,000/day floor. SH is the tight one once the other SH-reading services are counted (section 3.5).
6. Cost: about USD 0 extra hosting and no Zoho licence for portal users. Open money items are the integration-user seat in each Zoho org (price not found) and an off-server backup target. Zoho Creator, the nearest native alternative, is roughly USD 160-1,000 a month for 20-40 users (R2, shaky pricing).
7. Effort: about 17 developer-weeks for everything (range 14-22); about 11 for a read-only first release; a clickable demo on real SPS data in about 4-5 weeks.
8. Biggest dependencies: the user creates the SPS Self Client; the CEO decides SH API access; the user approves the write exception and two new dependencies (TOTP, SMTP).

## 1. Earlier decisions this overrides (stated explicitly)

| Earlier decision | Source | Under this design |
|---|---|---|
| Zoho read-only everywhere | /root/CLAUDE.md section 1 (8 Oct) | Overridden for this service only, narrowly: create (and later void) SPS sales-order drafts. Production Dashboard (port 4300) and the inventory system stay read-only. Needs the user's explicit yes. |
| SH data via signed-in browser session (7 Oct) | /root/CLAUDE.md section 1 | Direction changed to API (user, 17 Oct). It still holds in practice until the CEO grants access: the SH reader is a swappable interface, snapshot now, API later. |
| "No scripts or extensions" | user, 17 Oct | Honoured. Server-side API calls only. Webhooks, if used, are one Zoho workflow rule per org (configuration, not our code). |
| Auto-route by stock (02 cases 1-7) | 02-stock-and-routing.md | Replaced by Stores' decision; stock is a hint (R3). |

## 2. Components

```
 Browser (sales / Stores / managers / coordinators / admin)
        | HTTPS
 Traefik (EasyPanel, :80/:443) -- own subdomain, rate-limit + HSTS middleware (R4)
        | http://172.17.0.1:<port>   (port chosen at build time after `ss -ltn`; 4300 and 4400 are claimed)
 +--------------------------- order-portal (one PM2 process) ---------------------------+
 |  web/API layer      sessions, roles, TOTP, CSRF, audit log, rate limits              |
 |  screens            sales | Stores triage | production queue | dashboard A/B | admin |
 |  domain             request -> line state machine (R3 3.1), splits, cancels         |
 |  notifier           in-app rows + email outbox (no WhatsApp, ever)                   |
 |  ----------------------------------- mirror ---------------------------------------- |
 |  zoho-client x2     token cache, call limiter, daily ledger, 429/44/45/1070 handling |
 |  sync jobs          items+stock, locations, SO status, packages, transfer orders     |
 |  reader interface   SPS: API reader.   SH: snapshot reader now, API reader later     |
 |  write-back queue   SPS SO create (idempotent), retry, reconcile, kill switch        |
 |  webhook receiver   optional /hooks/zoho/<org>: marks a record "re-read now"         |
 +---------------------------------- SQLite (WAL) data/portal.db -----------------------+
        | HTTPS (outbound only)                    nightly .backup -> encrypted off-server copy
 Zoho Inventory API  https://www.zohoapis.com/inventory/v1   (US DC; both orgs)
   org 843825512 SPS (connection A)     org 843061977 SH (connection B, when granted)
```

**Mirror tables** (all carry `org`, `synced_at`, `zoho_modified_time`): `z_items` (name, unit, `cf_bu` division tag, `cf_fg_type`, status), `z_item_stock` (item x location: stock on hand, available, actual available, from the `locations` array on items, https://www.zoho.com/inventory/api/v1/items/), `z_locations`, `z_salesorders` + `z_so_lines` (only SOs the portal created or linked, plus the 217 open customized SOs for linking), `z_packages`, `z_transferorders`, `sync_runs`, `api_ledger` (one row per call: org, endpoint, status, caller).
**Portal-owned tables** (R3 6.1): `requests`, `lines`, `line_events` (append-only audit), `end_customers` + aliases, `item_map` (SPS item to SH item), `division_rules`, `manager_coordinator_pairs`, `hand_ticks`, `notifications`, `outbox`, `users`, `sessions`, `holidays`.

**Why a mirror at all**, given the cheaper "call Zoho on demand" alternative: (a) the Stores screen and dashboard stay up and fast when Zoho is slow, rate-limited or the SH access is only a snapshot; (b) one place records every call, so the budget is visible and enforceable; (c) the same item/stock mirror can later serve the stock hint, other items and the inventory system without a second sync. Cost of the mirror: staleness (always shown), sync code to maintain, and a second copy of data that can drift. The drift risk is bounded by a daily reconciliation count against Zoho.

**Boundaries kept from R3:** Zoho owns items, stock, SOs, packages, shipments, invoices. The portal owns requests, decisions, customers list, mapping, audit. The only Zoho writes are SPS SO create / void and the new portal-ref custom field.

## 3. Zoho connection

### 3.1 Orgs, auth, scopes (R1, R4)
- One **Self Client per org**, each owned by a dedicated integration user (not a person's account, because staff change; see the 14 Oct dismissal). Self Client is created in the Zoho API console and needs no end-user consent screen (https://www.zoho.com/accounts/protocol/oauth/self-client/overview.html). SPS: the user creates it. SH: the SH admin (CEO) must. Can a non-admin register a client? UNVERIFIED.
- Base URL `https://www.zohoapis.com/inventory/v1`, `organization_id` on every call, header `Authorization: Zoho-oauthtoken <token>` (https://www.zoho.com/inventory/api/v1/introduction/ and /oauth/).
- Token handling: access token about 1 hour, cached in memory per org, refreshed on expiry only (refresh is capped at 10 per 10 minutes, https://www.zoho.com/accounts/protocol/oauth/web-apps/access-token-expiry.html). At most 20 refresh tokens per user and the oldest is silently dropped, so generate once, never per deploy (https://www.zoho.com/inventory/api/v1/oauth/). Refresh token and client secret encrypted at rest (AES-256-GCM), key in env, backed up separately (R4). Test whether the client-credentials flow (no refresh token) works with Inventory scopes: UNVERIFIED.
- **Scopes, read set (phase 1):** `ZohoInventory.items.READ`, `ZohoInventory.contacts.READ`, `ZohoInventory.salesorders.READ`, `ZohoInventory.settings.READ`, `ZohoInventory.transferorders.READ`, `ZohoInventory.packages.READ`, `ZohoInventory.picklists.READ` (optional), `ZohoInventory.shipmentorders.READ` (https://www.zoho.com/inventory/api/v1/oauth/ and the per-resource pages).
- **Write set (phase 2, SPS only):** `ZohoInventory.salesorders.CREATE` (confirmed on https://www.zoho.com/inventory/api/v1/salesorders/). Void needs a scope the page excerpt did not state: UNVERIFIED, so void stays a manual step until checked. Do not request `FullAccess.all`.
- SH and SPS clients never share a token, queue or ledger row.

### 3.2 Endpoints used (all from R1 section 4)
`GET /items` (filters include `last_modified_time`, `warehouse_id`, `location_id`; stock in `locations` array), `GET /locations`, `GET /salesorders` (documented parameters seen: `salesorder_ids` up to 200, `page`, `per_page`; status/date filters UNVERIFIED), `GET /salesorders/{id}`, `POST /salesorders` (`custom_fields` array of `{customfield_id, label, value}`), `GET /packages`, `GET /transferorders`, `GET /contacts`. Pagination `page`/`per_page`, default 200; the "more pages" flag name is UNVERIFIED, so the sync stops on a short page rather than on a flag. Shipments have no list endpoint on the documented page (https://www.zoho.com/inventory/api/v1/shipmentorders/): shipment state is reached through the SO or package.

### 3.3 Limits (https://www.zoho.com/inventory/api/v1/introduction/ via R1)
100 requests/minute per org (HTTP 429, code 44); daily by plan 1,000 / 2,000 / 5,000 / 10,000 / 10,000 for Free to Enterprise (code 45); concurrency 5 free, 10 paid (code 1070). SPS reads 7,500/day (checked 7 Oct, `reports/2026-10-07-zoho-api-limit/`), which is **not** a documented tier, so it must be re-read in the admin console. SH is unknown: budget at the 1,000 floor. In the app: a token-bucket limiter at 60/min per org (headroom for other services), concurrency 3, and a hard stop (not retry) on code 45 with a banner.

### 3.4 Sync schedule and arithmetic (SPS, per working day, 12 hours 07:00-19:00)
Inputs: SPS catalogue 2,537 items (01-catalogue.md) = ceil(2537/200) = 13 pages. Open linked SOs 217 (03 s6). Load: mean 7.7 SOs / 11 lines a day, p95 20 SOs / 31 lines, worst day 35 SOs (03 s1). About 9 in 10 lines go to production (R3), so roughly 7 SPS SOs mean, 18 p95, 32 worst.

| Job | Rule | Calls/day |
|---|---|---|
| Item + stock sweep (stock is in the items list; I do not know that a stock movement bumps `last_modified_time`, UNVERIFIED, so sweep instead of incremental) | full list every 30 min = 24 sweeps x 13 pages | 312 |
| Item master incremental | `last_modified_time` filter, hourly, 1 call each | 12 |
| Locations | 1/day | 1 |
| SO status for open linked SOs | list by `salesorder_ids` (217 ids = 2 calls) every 15 min = 48 cycles | 96 |
| SO detail for SOs whose list summary changed | assume 40/day | 40 |
| Packages incremental | every 15 min | 48 |
| Write-back, mean day | 7 SOs x (create + read-back) | 14 |
| **Subtotal, mean day** | | **523** |
| Write-back, p95 day | 18 x 2 | 36 |
| Write-back, worst day | 32 x 2 | 64 |
| Retries / reconcile / manual "refresh now" allowance | +100 | 100 |
| **Worst plausible** | 312+12+1+96+40+48+64+100 | **673** |

Headroom: mean 523 is 7.0% of 7,500; worst 673 is 9.0%. If the 30-minute sweep is relaxed to hourly: 12 x 13 = 156, saving 156. Per-minute check: a 13-page sweep is a burst of 13 calls; the limiter spaces it (60/min), so a sweep takes about 13 seconds, well inside 100/min. 
SH (assumed floor 1,000/day; catalogue size N unknown, so pages = ceil(N/200)):

| Job | Rule | Calls/day |
|---|---|---|
| Stock sweep | every 2 h, 6 sweeps x pages | 6 x ceil(N/200) |
| Locations | 1/day | 1 |
| On-demand stock refresh when Stores opens a line | 31 lines p95 x 2 reads | 62 |
| Transfer orders being watched | about 10 open, every 30 min, 24 cycles x 1 list call | 24 |
| Later, SH SO drafts (phase 3) | 32 x 2 | 64 |

N = 3,000 gives 15 pages: 90 + 1 + 62 + 24 = 177 (241 with phase 3). N = 10,000 gives 50 pages: 300 + 87 = 387 (451). So the portal alone fits a 1,000 limit, but see 3.5. Until the CEO grants access the SH reader is a snapshot and costs 0 calls.

### 3.5 Shared-budget warning
Other planned services also read the same orgs: production dashboard about 415/day against SPS, inventory system capped at 500/day per org (HUMAN-DECISIONS / INV notes in /root/CLAUDE.md). SPS total: 415 + 500 + 673 = 1,588 of 7,500 (21%): fine. **SH: 500 (inventory cap) + 177 to 451 (portal) = 677 to 951 of an assumed 1,000**: too tight, and zero headroom if SH also runs the dashboard. Mitigation in this design: one shared `api_ledger` per org across services (or a single mirror service feeding the others, section 8), a hard portal cap of 400/day on SH, and the first action once SH access exists is to read the real SH daily limit. This is the strongest argument for deciding the mirror's owner once, not three times.

### 3.6 Webhooks (optional)
Zoho outgoing webhooks come from workflow rules (Settings > Automation > Workflow Actions > Webhooks), POST/PUT/DELETE, JSON payload, custom headers allowed, "available only for selective pricing plans", plan not named; no signing or retry behaviour stated (https://www.zoho.com/us/inventory/help/settings/automation.html, https://www.zoho.com/us/inventory/kb/automation/create-webhook.html). Plan: the receiver at `/hooks/zoho/<org>` checks a long random value in a custom header, accepts only the record id, and enqueues a re-read. It never trusts the payload as data. It needs a public HTTPS route (an EasyPanel/Traefik change by the human) and a workflow rule created by each org's admin. Whether the SPS plan includes it: unknown; check Settings > Automation. Without webhooks nothing breaks: polling is the design.

### 3.7 Write-back design (SPS, phase 2)
Coordinator clicks **Create SPS SO** on an accepted line. Steps: (1) portal writes a `write_jobs` row with a UUID idempotency key and the exact payload; (2) before POST it searches for an SO carrying that key (needs a searchable field: `reference_number` searchability is UNVERIFIED, so also store the key in the new portal-ref custom field and match by reading back); (3) `POST /salesorders` as a **draft** (customer = SH contact, `CF.Order Received from` = canonical end customer, order type, division, expected date, portal-ref); (4) read back, store SO id and number, line moves to SPS_SO_PENDING/IN_PRODUCTION; (5) on timeout the job stays "unknown" and is resolved by reading Zoho, never by blind retry. Kill switch per org in config. `CF.SH Sales Order Ref` is the job number (51% equals `CF.Job No`, 03 s7) so it is not reused. The user creates the new custom field in SPS Zoho. Draft stock-commitment behaviour and approval workflows in the org: UNVERIFIED, test in the real SPS org with a test customer before enabling.

## 4. Login (R4)
Own accounts: scrypt password hashes (pattern from IT Utilities), HttpOnly Secure SameSite cookie sessions in SQLite, login rate limiter reused from the Hub (`loginLimiter.js`), 12-character minimum, TOTP required for manager, coordinator and admin, optional for sales. Roles: `sales`, `stock_team`, `manager`, `coordinator`, `admin`. Scope (division list) stored per manager/coordinator from `manager_coordinator_pairs`. Rizwan's team: one real `stock_team` account with a hard expiry date, office-IP only (Traefik `ipAllowList` with `ipStrategy`, office public IPs needed), generated password, and a mandatory "who is acting" pick-list written to the audit log. Honest limit: that is logging, not authentication. R4 suggests individual accounts for them now; this design supports both since the roles are data. "Sign in with Zoho" is a later add-on (https://www.zoho.com/accounts/protocol/oauth/sign-in-using-zoho.html). Zoho client secrets never reach the browser.

## 5. Screens (all read from the mirror, line-level state machine from R3 3.1)

**Sales.** New order: customer picker over the managed list with aliases (640 spellings today), item search over the mirrored 862 customized items, qty + unit, required-by, job nature (New / Reorder / Reorder with new design / Rework), artwork / dye-cutter / screen flags, notes, attachments. "New item (not in catalogue)" path. My orders with per-line timeline and the SPS SO number once linked. Duplicate-submit warning (same customer + item + qty within 10 minutes).
**Rizwan's team (Stores).** Triage queue: one card per line with stock panel (SH per location, SPS separately labelled, never summed, "mirror age hh:mm / snapshot date"), hint text from the 02 cases. Buttons: Fulfil from stock, Send to production, Split, Return to sales (reason required). Bulk "send unknown/none lines to production" (R3 decision 6). Fulfil sub-screen: pick location, "transfer raised" with TO number typed in (SH Zoho read-only), watched via the mirror.
**Production.** Per-manager queue by resolved division: Accept, Return (reason), Wrong division reassign. Dashboard block A (accepted, no SPS SO yet, with age and the Create SPS SO form prefilled) and block B (SPS SO status, ordered/packed/shipped, days late, hand-ticked steps: artwork, item photo, job card). Coordinators act for their manager via `division_pairs`.
**Admin (the user).** Unassigned list (PCU, DPU, unresolved), division rules, pairs, customer merge/aliases, SPS-to-SH item map, unit alias table (nos = pcs), holidays, user management, sync status page (last run per job, calls today vs cap per org, mirror age), write-back jobs in "unknown" state, audit log search, kill switches.

## 6. Notifications
In-app bell and queue counters; email only otherwise. Table in R3 section 7 applies. Email goes through an `outbox` table drained by a sender, so a mail failure never fails a business action. Sending needs an SMTP library: `nodemailer` is not among the dependencies seen in `/root/dev/IT_Utilities_Backend/package.json` (better-sqlite3, express, multer), so it is a **new dependency needing approval**; the SMTP account to send from (Bluehost mailbox) is an owner answer. Managers get one digest per day-part, not one email per line. No WhatsApp sending, scraping or automation anywhere; the existing group stays a human channel.

## 7. Cost per year

| Item | Amount | Basis |
|---|---|---|
| VPS | LKR 0 extra | runs on the existing Contabo box (process, one SQLite file) |
| Domain / TLS | about 0 | subdomain of an existing domain via Traefik; DNS record needed |
| Zoho licences for portal users | USD 0 | users never log in to Zoho; the portal uses the API |
| Zoho integration user (one per org) | not priced | extra Inventory seat price not retrieved (R2). SPS: possibly an existing seat. SH: CEO's call |
| Zoho API | USD 0 | within the existing plan limits |
| Off-server backup | not priced | R4 requires it; target not chosen; existing mail-storage costings might host it |
| Email sending | about 0 | existing Bluehost mailbox, if SMTP is permitted |
| Developer time | the user's own | 17 dev-weeks (section 9) |
| **Comparison: Zoho Creator route** | about USD 160-320 /month Standard, 400-800 Professional, 500-1,000 Enterprise for 20-40 users on annual billing = about USD 1,900-12,000 a year, plus extra Inventory seats | R2, from the preview-host pricing page; pricing is shaky, re-check on live pages |

Hidden costs: maintenance time (about 0.25 day a week once live, my estimate), the restore test, and SH/SPS Zoho changes breaking a sync.

## 8. Growth
- **Stock hint to smarter hint**: the mirror already holds item x location stock, so ATP-style hints, "2 other open lines want this item", and later a suggested route (never auto) need no new Zoho calls.
- **Other items**: the mirror holds the full catalogue (2,537 SPS items); widening the order form from customized to standard items is a filter change plus the item map. SH's own catalogue needs the CEO's access.
- **One mirror, several apps**: the production dashboard (4300) and the inventory system (4400) both need Zoho mirrors. If this app's mirror exposes a read-only internal API, they could read it instead of syncing again. That would cut SH usage per 3.5 but couples three services, so it is a decision for later, not part of this build.
- **Goods gatepass**: its Zoho reader is meant to be swappable (7 Oct); this reader interface could be it.
- **Webhooks** later reduce polling; **SH SO drafts** (phase 3); **transfer orders** only if Stores asks and the CEO agrees.

## 9. Effort (one developer, test-first, reviews per step per house rules)

| Block | Dev-weeks |
|---|---|
| Foundation: app skeleton, users/roles/TOTP, sessions, audit, backup job, hosting config | 2.0 |
| Zoho client x2: OAuth, token cache, limiter, ledger, reader interface (API + snapshot) | 1.5 |
| Mirror sync jobs, freshness, sync status page, reconcile | 2.0 |
| Sales screens + managed customer list | 1.5 |
| Stores triage, stock panel, split, fulfil path | 2.0 |
| Production queue, dashboard A/B, hand ticks | 2.5 |
| SPS SO write-back: idempotency, retry/unknown state, reconcile | 1.5 |
| Admin screens | 1.5 |
| Notifications + outbox | 0.75 |
| Review, security audit, UAT, deploy pack, docs | 2.0 |
| **Total** | **17.25 (range 14-22)** |

Read-only first release (everything except write-back, with the SO created in Zoho by hand and its number pasted back): about 11 weeks. These are working weeks of one developer on this alone. The user also carries other builds (dashboard, inventory notes, gatepass), so at 50% availability the calendar roughly doubles.
**Time to a working demo:** about 4-5 weeks: foundation, SPS connector and mirror, sales form, Stores queue, production queue, with SH stock from the 28 Sep snapshot (three weeks old today; label it) and write-back faked ("would create SO"). That demo uses real SPS data only if the user has created the Self Client; otherwise it runs on the existing exports. The 31 Oct demo date belongs to the goods gatepass, not to this portal; do not promise both.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Largest build of the options (17 weeks, mirror plus portal plus dashboard) | schedule | phase it; read-only release first; compare with lighter angles before committing |
| Mirror drift | wrong hints | always show age, daily count reconcile, never decide on mirror data alone |
| Unverified API details (SO filters, pagination flag, `location_id` vs `warehouse_id`, `cf_*` shape, `customfield_id`, scopes for void/confirm) | rework | one sandbox day against SPS first, record in a findings doc |
| Duplicate or wrong SO from write-back | books of record | drafts only, idempotency key, unknown-state resolution, kill switch |
| SH access not granted or limit 1,000 | SH side stays a snapshot | swappable reader; cap 400/day; ask CEO early |
| Shared SH budget with other services | 429s | shared ledger, section 3.5 |
| Refresh token + key theft | persistent Zoho write | encrypt at rest, key off the DB, separate backup, least scope |
| Existing services bind 0.0.0.0, ufw inactive (R4) | bypass of Traefik | bind to docker bridge; human decides firewall |
| No scheduled DB backups today (ARCHITECTURE.md:154 per R4) | data loss | nightly `.backup`, off-server encrypted copy, restore test |
| Shared Stores login | no per-person audit | initials pick-list now, individual accounts at launch (or earlier) |
| Two new dependencies (TOTP lib, SMTP lib) | hard stop | user approves each, library chosen and checked then |
| Stale snapshot data (19/28 Sep) and possible SH Kohalwila vs SPS WIP double counting | bad hints | panels show them separately, labelled |

## 11. What this needs from the user / CEO

**User (this week):** (1) approve the narrow SPS write exception; (2) create the SPS Self Client and integration user, with the read scopes in 3.1, and create the portal-ref custom field; (3) read the real SPS daily limit and plan features (webhooks, custom functions) in the admin console; (4) approve or reject the two new dependencies; (5) answer R3's open questions (PCU manager, Stores acting on SPS stock, which SH locations Stores dispatch from, email addresses, cancel authority); (6) subdomain, port at build time, backup target.
**CEO / SH admin:** SH API access for an integration user with read scopes; SH daily API limit; consent to a portal actor in SH books before any phase-3 write. The 7 Oct rule (the proposal's UI quality unlocks SH access) still describes the order of asks.
**Human-executed, per the hard stops:** Traefik `custom.yaml` edit and DNS, `shdeploy`, any restart, any push.

## 12. Recommendation on this angle
This is the most capable option and the most work. It is right if the portal will also become the platform for stock hints, other items and the dashboard. If the real need is the order hand-off alone, a smaller design (on-demand reads, no mirror, SPS write only) would cut roughly 4-5 of the 17 weeks, and I would compare it before committing. A decision for the user, not made here.

## 13. Sources
- https://www.zoho.com/inventory/api/v1/introduction/ , /oauth/ , /items/ , /contacts/ , /salesorders/ , /locations/ , /transferorders/ , /picklists/ , /packages/ , /shipmentorders/
- https://www.zoho.com/accounts/protocol/oauth/self-client/overview.html , https://www.zoho.com/accounts/protocol/oauth/web-apps/access-token-expiry.html , https://www.zoho.com/accounts/protocol/oauth/sign-in-using-zoho.html
- https://www.zoho.com/us/inventory/help/settings/automation.html , https://www.zoho.com/us/inventory/kb/automation/create-webhook.html
- R2 for Creator pricing (preview-host figures, unverified). Local: 01, 02, 03, 05 in `../`; `/root/dev/IT_Utilities_Backend/package.json`; `/root/CLAUDE.md`.

Prepared by Abdul Hadhee | IT Executive
