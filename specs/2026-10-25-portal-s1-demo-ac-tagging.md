# Order Portal S1: acceptance-criteria tagging for v0.1 (S1-demo) and v0.5

**25 Oct 2026.** Prepared by Abdul Hadhee | IT Executive. Author: test-author. Document only: no tests and no code yet.
**Status: for plan-critic, before the S1 build starts** (Rev 4.5 §4, last bullet under "In").

Sources read:
- **Rev 4.5** = `wiki/specs/2026-10-24-joint-demo-v0-1-rev4-demo-first.md` (this worktree): §4 (in/out lists), §2.3, §2.4, §3, §6, §7.
- **OP** = `/root/Project Management/wiki/specs/2026-10-18-order-portal-spec.md` Rev 3.2: §4.3 screens, §5 state machines, §6.9, §7, §13 ACs, §14 slices (S1 = AC9-AC41, AC43-AC46c; AC42/AC42b belong to S1b).
- **J31** = `2026-10-21-joint-demo-v0-1.md` §2 (portal = OP S0+S1, writes off in J31; replaced for writes by Rev 4.5 R4-AC2 + G-AC5).
- Portal code `/root/dev/order-portal` (read-only), HEAD `be0ed4b`: S0 built.

## 0. Tag meanings

| tag | meaning |
|---|---|
| `v0.1` | AC written as in OP, test goes in the S1-demo suite |
| `v0.1-modified` | in S1-demo, but the AC text changes as stated (mostly "Zoho" becomes "the demo gateway") |
| `v0.5` | moves to the live-write update (Rev 4.5 §4 "Moved to v0.5", §7); no test in the v0.1 suite |

**Counts (OP S1 ACs, 50 rows): `v0.1` 32 · `v0.1-modified` 9 · `v0.5` 9.**
AC42 and AC42b (S1b, `api` project mode) are not S1 ACs; they stay out of v0.1 and v0.5 (V3 still open, Rev 4.5 §2.3).

## 1. State of the portal code that affects the list (checked 25 Oct)

- `server/db/migrations/001-schema.sql` has **no** `sps_projects`, `sps_contacts`, `item_requests`, `customer_requests` or `item_links`; `order_lines.item_request_id` is a plain integer (comment at line 70). So the two new syncs need a **new migration 002** (additive), and every request-based AC (AC17, AC26b, AC27, AC41) has nothing to run against until S3/S4.
- `server/services/transitions.js:7,11` moves orders only and accepts any known target state; the legal-transition table (OP §5) is entirely S1 work.
- `server/config.js:104-105`: Zoho base and token URL are hard-coded unless `ZOHO_FAKE_URL`, which `config.js:52` allows only under `NODE_ENV=test`. Rev 4.5 R4-AC2 says "no `ZOHO_FAKE_URL`", but the portal has no setting that points at the gateway (Rev 4.5 §5 defines `ZOHO_API_BASE`/`ZOHO_TOKEN_URL` for the dashboard only). See flag F1.
- Origin checks are string prefixes (`config.js:55`), rate limits exist only on login (`routes/auth.js:22-23,73`).
- `restore-pending.js:28` already refuses a clear without `reconcile_started_at`; nothing writes it until v0.5 (LATER R7).

## 2. The tagging list: OP S1 ACs

Reason column cites Rev 4.5 §4 ("In"/"Moved to v0.5"), OP section, or J31.

| AC | Summary | Tag | Reason / how the text changes |
|---|---|---|---|
| AC9 | Pre-fill from newest line with same item and customer (`basis=customer`) | `v0.1` | Screen 1 is in (Rev 4.5 §4). Fixture-based, so the 30-day history (`SPS_HISTORY_DAYS`) does not affect it |
| AC10 | Item ordered only by another customer: pre-fill from item's newest line, "New Order", `basis=item` | `v0.1` | Screen 1; OP §6.1 |
| AC10b | Placeholder never counts as customer; no-line cases give `basis=item` / `none` and `price_changed=1` | `v0.1` | Screen 1; "price flag stored" is in. Presenter note (§12): with 30 days of history many lines show the changed flag, so this path is exercised live |
| AC11 | last 4.27 vs entered 4.50 gives `price_changed=1` | `v0.1` | "price flag stored" (Rev 4.5 §4); OP §6.2 |
| AC12 | Equal at 2 dp gives 0 | `v0.1` | Same |
| AC13 | Same `client_token` twice gives one order | `v0.1` | Duplicate-submit test for a write; O1 is in |
| AC14 | Inactive item gives 422 | `v0.1` | O1 rule; screen 1 |
| AC15 | Bad dates, qty, rate or notes give 422, nothing stored | `v0.1` | Input validation at the boundary (OP §10) |
| AC16 | Stock chosen on a 3-line order: order `stock`, snapshot per line, acting person recorded | `v0.1` | Screen 3, O2 in. Snapshot may hold "unknown" stock (R4-AC4 says unmatched gives "unknown") |
| AC17 | Order with an item request: Stock gives 409 `new_item_not_in_stock` | `v0.5` | Item requests need S3 (out: "new item/customer", Rev 4.5 §4 last bullet). No `item_requests` table and no way to create one in v0.1. Guard added with S3. Safe only with new AC NP-4 (v0.1 refuses `item_request_id` input) |
| AC18 | Production chosen: all lines `to_production`, each only in its own division's queue | `v0.1` | O3/L1, screen 4 |
| AC19 | Send-back reason <5 chars 422; >=5 gives `returned_to_sales`, reason visible | `v0.1` | O4 (J31 walkthrough: the PSU coordinator returns the straw line) |
| AC20 | Two decisions on the same version: one succeeds, one 409 | `v0.1` | "`version` 409" is in (Rev 4.5 §4); concurrency test |
| AC21 | O7: lines become `to_production` | `v0.1` | Transition rules "in full up to `so_created`" |
| AC22 | Sales cancels `in_production` gives 409; `submitted` gives `cancelled` | `v0.1` | O6; transition rules |
| AC22b | Last line terminal: order `done` in the same transaction; `so_created_draft` line blocks done | `v0.1` | O8; the draft rule matters for the demo (dashboard hides drafts) |
| AC23 | Accept gives `accepted` | `v0.1` | L2, screen 4 |
| AC24 | Reassign X to Y moves the line between queues | `v0.1` | L3; screens 4 and 6 (divisions/people) |
| AC25 | Decline without reason 422; with reason `declined`; later transitions 409 | `v0.1` | L9 |
| AC26 | Full state x action matrix: unlisted pairs give 409, nothing written | `v0.1-modified` | Matrix covers only the v0.1 rows: O1-O8, L1-L9, L20, L21, L24, L25, L15, L16, L23, L27, L28. **Changes:** L10-L14b (request-driven), L20p-L20r (S1b), L26 (reconciler) and L29 (Reconcile refs) are not implemented, so they are asserted as 409 `invalid_transition` in v0.1; the "L28 and L29 are allowed" sentence becomes "L28 allowed, L29 refused until v0.5". The matrix must also give one happy-path assertion per allowed row (see gap G1) |
| AC26b | Rejected request blocks O1, L5, O3; request `created` sets id on linked lines | `v0.5` | Requests are S3/S4 |
| AC27 | Picking an existing item on a returned line clears `item_request_id` | `v0.5` | Only meaningful with item requests (S3) |
| AC28 | Writes disabled: approve gives 409, no requests | `v0.1` | Keep; combined with R4-AC2 it is the demo's main write guard |
| AC29 | Approve `basic.json`: exactly one POST, body deep-equals `so-create-basic.json` | `v0.1-modified` | **Changes:** the POST goes to the demo gateway base, not "Zoho". Body unchanged (OP §6.9). The fixture's ids (customer, warehouse, tag ids, `cf_*` values) must all exist in the gateway map or the gateway refuses them (G-AC10); `customfield_id` for Portal Ref is the stand-in `DEMO_PORTAL_REF_FIELD_ID`. Fixture is regenerated at v0.5 from G2/G3 real values (V1, V2) |
| AC30 | 201 confirmed gives `so_created` and order `done` | `v0.1` | Kept against the fake Zoho. The gateway never answers "confirmed" on create (it stores `draft`, Rev 4.5 §2.3), so this path is a fake-Zoho test only |
| AC30b | `so_created` is never draft; 201 draft goes draft, confirm, `so_created` | `v0.1` | **This is the demo's normal path** (`so_create` then `so_confirm` to the gateway) |
| AC30c | Confirm returns 400: line stays draft, Retry confirm offered; success gives `so_created` | `v0.1` | L27 is not in the out list; needed or a failed confirm leaves a job hidden from the dashboard. Retry confirm must be on the Admin screen (flag F3) |
| AC30d | Confirm times out: `unknown`, then a GET settles it either way | `v0.1-modified` | **Changes:** the settle step is the OP §7.6 confirm-row rule only (GET by id: status not draft gives `done`; still draft in two reads >=10 min apart gives `failed`), run for `so_confirm` rows. The `so_create` reconciler (§7.4, L26) stays out. The line never leaves `so_created_draft`. See flag F2 |
| AC30e | Confirm `pending` at restart is re-queued; GET first; if confirmed, no POST | `v0.1` | Restart rules; OP §7.2 startup list |
| AC31 | Two concurrent approvals of the same version (fake delayed 500 ms): one POST, same write id | `v0.1` | Mandatory concurrent-write test; ledger idem key |
| AC32 | Inactive item at pre-check: no POST | `v0.1` | OP §7.2 pre-checks "as written" |
| AC33 | L28: ref found with confirmed: no row, no POST, `so_created`, O8 checked | `v0.1` | Forced delta + ref check "against the gateway" (Rev 4.5 §4). Needs the list filter keys of the forced delta in the gateway's filter fixture (G-AC12), otherwise the gateway returns 400 |
| AC33b | L28: ref found with draft gives `so_created_draft` plus a confirm; holds with the filter off and on (one filter call when on) | `v0.1-modified` | **Changes:** "filter off" case only (V8-negative: forced delta + mirror). The "filter on, exactly one live filter call" case is v0.5: V8 is unverified and the gateway refuses unknown filter keys. Test asserts zero filter calls |
| AC33c | Lease held 35 s: after ~30 s "sync busy", no row, `accepted`, 0 requests; freed at 20 s: write proceeds | `v0.1` | Pre-check (a) as written. Uses the S0 test lease holder |
| AC34 | 400 gives `failed`, `accepted`; re-approval keeps the same ref | `v0.1` | Definite-failure path (L24); gateway can return Zoho-shape errors (G-AC10) |
| AC35 | Timeout gives `unknown`, no second POST | `v0.1` | L25, "never auto-retried"; tested on the fake (the gateway has no timeout mode) |
| AC36 | Reconciler finds ref (confirmed): `so_created`, still one POST | `v0.5` | Out: "reconciliation beyond the restart rule" |
| AC36b | Reconciler finds ref (draft): `so_created_draft` plus a confirm | `v0.5` | Same |
| AC37 | Ref absent twice >=10 min apart: `failed`, `accepted` | `v0.5` | Same (L26) |
| AC38 | Restart recovery before any scheduler: `pending` gives `never_sent`/`accepted`; `in_flight` gives `unknown`/`so_unknown` | `v0.1` | Restart rule is in. Kept **as written** (both halves); Rev 4.5 §4 names only `so_writing` to `so_unknown`. See flag F4 |
| AC39 | L15 with a GET showing a different ref: 409; matching ref (confirmed): `so_created` | `v0.1-modified` | **Changes:** "Zoho" becomes "the gateway"; the admin enters the DEMO order id (`99` + 17 digits); the GET goes to the gateway; an id the sandbox does not hold gives the gateway's not-found, line unchanged. L15 is in (Rev 4.5 §4) |
| AC39b | L15 matching ref (draft): `so_created_draft` plus a confirm | `v0.1-modified` | Same wording change. Strengthened by Rev 4.5: the `so_confirm` row is queued at once (also R4-AC8) |
| AC40 | L16 while ref found: 409; absent with reason >=10: `accepted` | `v0.1-modified` | **Changes:** the check is forced delta + mirror via the gateway; "(+ live filter if V8 allows)" is dropped. L16 is in (Rev 4.5 §4) |
| AC41 | Item request not yet created: 409 `prerequisite_pending` | `v0.5` | Needs item requests (S3) |
| AC43 | `pick`: unknown typed Job No gives 409 | `v0.1-modified` | **Changes:** "known" means present in `sps_projects`, filled by the new gateway-backed sync (272 recorded projects, G-AC11). Typing a new Job No in `pick` is refused with the OP §6.9 message; the picker is the only route |
| AC44 | `later`: typed Job No gives no project fields, `reference_number` = Job No, flag set; clears later | `v0.1` | Rev 4.5 §2.3: "`later` stays coded but is not shown in the demo". Test stays; no UI entry in v0.1. Flag clears when the portal sync sees `cf_job_no` (tested on the fake; the gateway has no way to add a project) |
| AC45 | P4: placeholder line: payload has placeholder and "End customer:" note | `v0.1` | Gateway reads the name from the note (G-AC14) |
| AC46 | `restore_pending`: toggle, CLI, approval refused, reconcile clears, re-approve gives `already_created`, audit, survives restart | `v0.1-modified` | **Keep in v0.1:** with the flag set and `ZOHO_WRITES_ENABLED=true`, approval gives 409 `restore_pending` and 0 requests to write paths; health shows `restorePending=true`; survives restart; one audit row for set; CLI refuses while the service is up; clear before a completed reconcile gives 409 (S0 code, `restore-pending.js:28`, `admin.js:150`); re-approve of a `so_created` line gives 409 `already_created`. **Moves to v0.5:** "Reconcile refs makes the line `so_created` (`restore_reconcile`)", "admin clears after the run, writes allowed again", and the audit row for clear |
| AC46b | Same as AC46 with a draft order: `so_created_draft`, confirm sent only after clear | `v0.5` | Needs Reconcile refs (L29), out |
| AC46c | Reconcile refs on `declined`/`cancelled`/`stock` lines changes nothing and lists; ref with no line listed | `v0.5` | Out (L29 Reconcile refs) |

## 3. New v0.1 ACs on the portal side (added by Rev 4.5 or LATER.md)

IDs starting `R4-` / `G-` are Rev 4.5's own; `NP-` are proposed here so each item has one test name.

| ID | Source | AC | Tag |
|---|---|---|---|
| R4-AC2 | Rev 4.5 §6 | `ZOHO_WRITES_ENABLED=true` without `DEMO_GATEWAY=1` **and** a loopback Zoho base stops the start (test both halves, and the token URL too); `DEMO_GATEWAY=1` starts with `NODE_ENV=production` and no `ZOHO_FAKE_URL`. Requires a portal setting for the gateway base (flag F1) | v0.1 (guard stays until v0.5 safety ACs pass) |
| R4-AC4 | Rev 4.5 §6, OP §8.3 | SH stock on Decide with the fake CDP: matched line shows "as of HH:MM" at the picked locations; no picked locations gives "unknown". Sub-table below | v0.1 |
| R4-AC5 | Rev 4.5 §2.6 | `SPS_HISTORY_DAYS=30`: backfill stops at orders older than 30 days and reports complete; unset keeps today's behaviour (`sps-sync.js:233`) | v0.1 |
| R4-AC7 (portal part) | Rev 4.5 §2.7 | With `DEMO_GATEWAY=1`, portal `/health` and start log say `DEMO MODE (gateway)`; without it, neither does | v0.1 |
| R4-AC8 | Rev 4.5 §6 | L15 onto a draft order queues an `so_confirm`; after it the line is `so_created`. Portal half only here (dashboard sees the job is in the R4-AC3 e2e) | v0.1 |
| NP-1 (G-AC11 portal part) | Rev 4.5 §2.3 | `sps_projects` sync through the gateway: pages by `page_context`, fills the table, each call counted by the portal budget, runs at the project cadence (`sps-sync.js:75-85`, `budget.js:17`); needs migration 002 | v0.1 |
| NP-2 (G-AC14 portal part) | Rev 4.5 §2.3, N4 | `sps_contacts` sync through the gateway, at the **project cadence** (not every 5-min cycle); the placeholder contact never appears in the picker or counts as a customer (OP §6.1); needs migration 002 | v0.1 |
| NP-3 | Rev 4.5 §4, §6 G-AC11 | Approve screen Job No picker lists `sps_projects`; Screen 1 end-customer picker lists `sps_contacts` | v0.1 |
| NP-4 | proposed | Order create/edit/resend in v0.1 refuses `item_request_id`, "new item", and any customer request (422); only an existing contact or the placeholder (P4) is accepted as end customer. This is what makes deferring AC17/26b/27/41 safe | v0.1 |
| NP-5 | proposed | Pre-check read failure (gateway 429 after a 10 s queue wait, 5xx, timeout): no write row, line stays `accepted`, reason shown (OP §7.2 "if any check fails, nothing is written"). Likely under the dashboard's polling load | v0.1 |
| NP-6 | G-AC13 portal part | After `so_confirm`, the next sync sees the bumped `last_modified_time` and the mirror shows `confirmed` | v0.1 |
| NP-7 | proposed | Gateway-backed writes count against the portal budget exactly like live ones (a POST to the gateway uses the write reserve); AC47/AC48 behaviour is unchanged | v0.1 |
| W9 | LATER.md | Rate limits on write, approval and upload routes: writes 60/min per user, approvals 30/min per manager (OP §10); uploads 20/min only when S5 exists. Test: the 61st write and 31st approval in a minute give 429; a second user is unaffected. Keyed per user, not global. **S1 entry criterion: routes may not merge without it** | v0.1 |
| R1 | LATER.md | Explicit `DEMO_GATEWAY=1` mode: loopback origin, no bridge, `NODE_ENV=production`; `TRUSTED_PROXY_IPS=192.0.2.1`; config test. Same change carries R4-AC2/R4-AC7 | v0.1, before the demo run |
| R3 | LATER.md | Origin check parses the host (127.0.0.1, `[::1]`, non-localhost http refused) instead of string prefixes (`config.js:55,82`). Test: `http://localhost.evil.example` is not treated as localhost | v0.1, before the demo run |
| N3 | LATER.md | `audit()` records the acting person from the session on the first fulfilment transition (shared login) | v0.1 (S1 entry: AC16 asserts it) |
| N4 | LATER.md | Narrow `GET /orders/:id` before S1 adds fields: only the owner and the roles with a stake see lines; AC2 re-run on the wider shape | v0.1 (S1 entry) |
| R7 | LATER.md | Reconcile writer sets `reconcile_started_at` and `completed_at` together, at completion | v0.5 (Rev 4.5 §4; S1 merge for the v0.5 branch is blocked without it) |
| R4, R5, R8, N5, N10 | LATER.md | Before v0.3 | not v0.1 |
| R6 | LATER.md | Shared-login password rotation | v0.3 unless a non-IT person uses the shared login in the rehearsal (flag F6) |

### R4-AC4 expanded (OP AC55-AC61, Rev 4.5 §3 reductions)

| AC | Tag | Note |
|---|---|---|
| AC55 HTML response gives `login_required`, 0 further requests, persists across restart until Resume | `v0.1` | as written |
| AC56 429 gives a 10-min pause that persists across a restart | `v0.1` | as written |
| AC57 every call GET and allow-listed; bad ids/paths refused before any CDP message | `v0.1-modified` | allow-list shrinks to `items/<id>` and `locations` (no SH lists, Rev 4.5 §3); `contacts` and `items` list paths must be refused |
| AC58 <=40 per cycle, >=1,200 ms apart, stock before lists | `v0.1-modified` | stock only, <=20 per cycle, cached 5 min, plus one `locations` read a day; "stock before lists" is vacuous |
| AC59 slow SH cycle does not delay SPS | `v0.1` | as written |
| AC60 `off` works; `cdp` passes the contract suite | `v0.1` | as written |
| AC61 stock older than 31 min shown unknown | `v0.1-modified` | Rev 4.5 §3 and OP §6.4 say >30 min; use 30 (see flag F7) |

## 4. Flags: unsafe to defer, wrong to include, or ambiguous

- **F1 (spec gap, blocks R4-AC2).** The portal has no way to reach the gateway without `ZOHO_FAKE_URL` (test-only, `config.js:52,104`). Rev 4.5 defines `ZOHO_API_BASE`/`ZOHO_TOKEN_URL` for the dashboard (§5, R4-AC1) but not for the portal. Proposal: same two settings, accepted only with `DEMO_GATEWAY=1` and an `http://127.0.0.1:<port>` value (R4-AC1 text, portal side). Needs one line in Rev 4.5 or the plan-critic's agreement before the config test is written.
- **F2 (unsafe to defer without the confirm settle).** AC30d: if a confirm times out, the line sits in `so_created_draft` and is hidden from the dashboard (`line-jobs.js:134`), and L27 "Retry confirm" is only offered when the latest confirm `failed` (OP:276). With "reconciliation beyond the restart rule" out, nothing resolves an `unknown` confirm. Tagged `v0.1-modified` to keep only the §7.6 confirm-row GET-by-id settle. If plan-critic disagrees, the alternative is to allow L27 on an `unknown` confirm (GET first, as the `pending` rule). Either way it cannot be dropped.
- **F3 (omission in Rev 4.5 §4).** Screen 6 is listed as "users, divisions/people, Sync view, SH locations". L15, L16 and Retry confirm (L27) are in v0.1 but live on the OP ledger view of screen 6. The in-list should say "ledger view with L15/L16/Retry confirm and the sandbox-orders-by-Portal-Ref list", otherwise AC30c/AC39/AC40 have no UI. Kill switch UI and Reconcile refs stay out.
- **F4 (ambiguity).** Rev 4.5 §4 restart rule: "a line found in `so_writing` at startup goes to `so_unknown`". OP L24/AC38 distinguishes `pending` (never sent, back to `accepted`) from `in_flight` (to `unknown`). Sending a never-sent write to `unknown` would force an admin L15/L16 for nothing. Tagged AC38 as written (both). If the intent was to drop the `pending` branch, say so and AC38 becomes `v0.1-modified`.
- **F5 (restore_pending cannot be cleared in v0.1).** With R7 and the Reconcile writer out, setting the toggle is a dead end until v0.5 (clear always gives 409 `reconcile_required`). Acceptable because the demo DB is replaced at v0.5 (Rev 4.5 §7), but the Admin UI should say so, or hide the set button in v0.1. Not unsafe: it only blocks writes.
- **F6 (conditional).** LATER R6 (no password rotation for the shared login): fine while only IT uses the demo through the SSH tunnel. If Rizwan's team tries the rehearsal on the shared login, R6 moves into v0.1.
- **F7 (nit).** OP AC61 says 31 min, OP §6.4 and Rev 4.5 §3 say 30 min. Use 30.
- **F8 (deferral safe only if NP-4 exists).** AC17, AC26b, AC27, AC41 are deferred because no request can exist in v0.1. That holds only if v0.1 rejects `item_request_id` and customer-request input (NP-4). Without NP-4 the plain integer column accepts one and the O2/O3/L5 guards are missing.
- **F9 (pre-checks run under gateway pacing).** Forced delta + ref check goes through the gateway queue at >=667 ms per upstream call, beside the dashboard's polling, and a request waiting >10 s gets 429. AC33c's 30 s lease wait and the gateway's 10 s wait are separate clocks; NP-5 pins the outcome (no write, line stays `accepted`).
- **F10 (AC29/AC33 depend on the gateway map).** A fixture id absent from the 234-item map or 111-contact map makes the gateway refuse the POST while AC29 (fake Zoho) still passes. The cross-app e2e (R4-AC3) is the only test that catches it; use mapped ids in `basic.json`.
- **Not unsafe to defer (checked):** AC36/36b/37, AC46b/46c, R7 (no write path in v0.1 reaches live Zoho because of R4-AC2 + G-AC1/G-AC2).

## 5. Coverage gaps in the AC set itself

- **G1.** OP §13 has no AC for several transitions v0.1 must implement: O5, L4, L5, L6, L7, L8, O6 (cancel before production). Only the AC26 matrix touches them. Proposal: AC26's v0.1 version asserts each allowed row once (role + division + version check + one event + one audit in one transaction, OP §5 header rules) rather than adding new AC ids.
- **G2.** OP §7.4 "two `unknown` outcomes in a row disable approval until an admin acts" has no AC and depends on the reconciler. Tag: v0.5 with the reconciler; in v0.1 one stuck `so_unknown` is handled by L15/L16 only.
- **G3.** OP §11 health fields (`draftsAwaitingConfirm`, `restorePending`, `writesEnabled`) have no AC; `draftsAwaitingConfirm` is the quickest signal for the F2 problem. Proposed as part of NP-6.
- **G4.** The 309 recorded orders do not hold `item_request` or placeholder-contact lines; AC45 needs a synthetic fixture for the `End customer:` note.
