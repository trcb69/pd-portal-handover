# Order Portal S0: code review, round 2 (24 Oct 2026): BLOCK

Repo `/root/dev/order-portal`, branch `feature/s0-foundation`, diff `c18b382..cbd795d` (a0595c9, af70688, 9c44fb6, cbd795d).
`npm test`: 150/150 (I re-ran it). Two scratch probes were run against the repo's own sync harness. They sit outside the repo, in
`/tmp/claude-0/-root/d7fbbc68-754b-4b84-b54a-5ec257db2d21/scratchpad/probe*.test.mjs`, and no source was edited.

## Verdict
BLOCK. B1 and B3 are fixed and B2 is fixed. The new quarantine and backfill code, though, loses orders from the mirror without any signal
(C1, C2), and the W9 deferral is not logged anywhere (C3).

## Status of round-1 findings

| ID | Status | Evidence |
|---|---|---|
| B1 | **FIXED** (the mechanism). New defects in the code are listed under C1/C2 | Resumable backfill with its cursor kept in `settings` (`sps-sync.js:59-61,225-256`). Steady lane from "now" (`:264-279`). A history stop is a deferral (`:246-250`). Items reserve (`:281-283`). Harness test `test/sync-backfill.test.js:15-48` |
| B2 | **FIXED** | `001-schema.sql` adds `sps_salesorders`, per-line `division_tag/project_id/detail_json` and `sps_items.raw_json` + sku/unit/cf_bu/image_document_id/division_tag. Writes at `sps-sync.js:113-129,176-185`, test `sync-backfill.test.js:63-87`. No DB is on disk anywhere, so editing 001 is safe |
| B3 | **FIXED** (S0 side) | `restore-pending.js:28-29` compares the start time of the completed run. Test case "started before, ended after → 409" at `test/restore-pending.test.js:103-104`. See W4 for the contract S1 must keep |
| W1 | **PARTLY** | Quarantine table and retry exist (`sps-sync.js:134-172`). However, an outage still quarantines orders for good (C1). The count only goes to a log line (`:217`), not to health (`routes/health.js:12-15`) |
| W2 | **FIXED** | Nightly sweep, where only a 404 deactivates an item and more than 25 missing means the sweep is distrusted (`sps-sync.js:289-322`). Tests `sync-backfill.test.js:146-182` |
| W3 | **NOT FIXED, not deferred** | `server/app.js:1` and `cli/restore-pending.js:3` still use `import 'dotenv/config'`, which reads `.env` from the cwd |
| W4 | **NOT FIXED, not deferred** | `cli/restore-pending.js:28` → `db/open.js:5-6` still runs `mkdirSync` and creates an empty DB, with no `fileMustExist` and no schema check |
| W5 | **NOT FIXED, not deferred** | There is still no first-admin path. `package.json` scripts have no `create-admin` |
| W6 | **FIXED** | `config.js:59-62`: required in production, no `-` allowed. Ref matching is S1 |
| W7 | **FIXED** | `startup.js:14` clears the lease at prepare, and `startup.js:32` releases it on stop. Test `sync-backfill.test.js:185-195` |
| W8 | **FIXED** | `sync-backfill.test.js:90-104` (line removal), `:106-134` (partial failure) |
| W9 | **NOT LOGGED** | The repo has no `LATER.md` (`git ls-files` shows none), no `LATER*.md` on the box mentions the order portal, and no commit mentions W9. See C3 |
| N1 | FIXED | `config.js:76-77` |
| N2 | FIXED | Every list row's modified time is checked (`sps-sync.js:93`). Test `sync-backfill.test.js:208-214` |
| N3 | FIXED | `create-app.js:35-37`, with requireAuth mounted once |
| N4 | NOT FIXED | Still one client per `makeSpsSync` (`zoho/client.js:10`, `sps-sync.js:46`). Fine for S0. Revisit when S1 adds the write client |
| N5 | NOT FIXED | `migrate.js:11` still drops non-matching `.sql` files silently |
| N6 | NOT FIXED | `test/helpers/db.js:6` still uses `path.resolve('server/db/migrations')` (cwd-relative). Commit af70688 uses the label "N6" for a different change (digit-only SO ids), so the round-1 N6 was missed |
| N7 | FIXED | `routes/auth.js:105-112` (fail counted before verify, reset on success). Shared accounts are refused |

## Critical (must fix before merge)

- **[C1] `server/services/sps-sync.js:138-146` (with `:159`, `:166-171`).** A detail outage of 15–20 minutes drops orders from the mirror
  for good. Each failing run quarantines the first 5 orders before the 6th failure shows that the problem is an outage (`:140`), and
  `retryQuarantined` then pushes those 5 to `hits = 3` over the next cycles. `planSo` skips them until Zoho modifies them again (`:159`),
  which for history orders means never. Measured with the harness:
  - Steady lane: 8 orders change, then details return maintenance HTML for 4 cycles. After recovery 8 of 13 orders are mirrored and 5
    stay quarantined.
  - History lane: 60 orders and the same outage. The backfill reports `history_complete` with 55 of 60 orders mirrored.

  Every run after recovery is recorded `ok`, and health stays green. **Fix:**
  1. Hold per-order failures in `run` and write them to `sps_so_quarantine` only after the run ends with `run.bad <= MAX_BAD_PER_RUN`. A
     failed run must change no hit counts.
  2. Show `quarantined` (the count with `hits >= 3`) in `/api/health`.
  3. Add a test: an outage of 4+ cycles, then recovery, ends with every order mirrored and the quarantine empty.

- **[C2] `server/services/sps-sync.js:230-243`.** The history pages by `last_modified_time DESC` and keeps going after Zoho deletes an
  order. A deletion on a page already read moves every row below it up by one, so one row per deletion falls into a page that has already
  been read and is never fetched. Measured: 700 orders, 5 of the newest deleted after cycle 1. The backfill "completes", and 5 live orders
  are missing from the mirror for good. No later step adds them back: the steady lane only sees modified rows, and the item sweep only
  deactivates items. The item first load (`planItems`) has the same gap. **Fix:**
  - When `state.last` is reached, run one more pass over the list only, from page 1, before declaring the backfill complete. It is cheap:
    about 43 pages, and held orders cost no detail call. Fetch any id not held, and repeat until a pass finds nothing new.
  - Or overlap pages, which is weaker.
  - Have the nightly item sweep upsert listed rows that are not in the mirror.
  - Add a harness test that deletes during the backfill and asserts that every live id is mirrored.

- **[C3] W9 deferral: no `LATER.md` in `/root/dev/order-portal`.** The handoff says W9 (write/approval/upload limits as an S1 entry
  criterion) was deferred to S1 through LATER.md. That file does not exist in the repo or anywhere else on the box for this project. W3,
  W4 and W5 were neither fixed nor deferred. **Fix:** create `LATER.md` with W9 (owner, plus the condition "before S1 merges"). Either fix
  W3, W4 and W5 or log them there too. W5 decides how the first admin logs in on a fresh database, so it needs an owner before the demo.

## Warnings (fix now or file a ticket)

- **[W-a] `server/routes/health.js:12-15`.** While a backfill of about 13 days runs, the steady lane records `ok` every cycle
  (`sps-sync.js:216`). Health therefore shows `stale: false` while the mirror holds a fraction of the orders. **Fix:** add
  `sps.backfill: { salesorders: {page, pending} | null, items: … }` to the health response, and let the banner say "history still loading".
- **[W-b] `server/services/sps-sync.js:253`.** An `upstream` error (a Zoho 5xx) resets the backfill to page 1. The comment's reason ("the
  list may have shifted") does not apply to a transient 5xx. Each 5xx costs up to about 43 list calls out of an allowance of about
  640 calls a day. **Fix:** treat `upstream` like the codes in STOPS_CYCLE (keep the position), and reset only on `bad_shape` of a list page.
- **[W-c] `server/services/sps-sync.js:136-146`.** Zoho deletes an order, so its detail returns 404 and the order is quarantined, but its
  `sps_salesorders` and `sps_so_lines` rows stay "live" for good. This is the same gap that spec line 131/840 records for the dashboard.
  **Fix:** on a 404 for an order already held, mark it `missing_in_zoho`, or delete it in the mirror transaction, and add a test. If you
  defer it, log it in LATER.md.
- **[W-d] `server/services/restore-pending.js:28`.** The S1 writer must set `reconcile_started_at` only when the run **completes**, with
  the run's start time. The key's name invites writing it at start, and that would clear the switch while Reconcile is still running.
  **Fix:** store one JSON value, `reconcile_last_completed = {started_at, completed_at}`, written once at completion. Or log the contract as
  an S1 AC in LATER.md.
- **[W-e] `server/services/sps-sync.js:275` against `:226/283`.** The steady lane is skipped when `page === 1` and the allowance is above
  0, but the history lane defers when the allowance is at or below `floor` (100 while items are pending). With the allowance between 1 and
  100 after a page-1 reset, neither lane reads, and order changes wait. They are delayed, not lost. **Fix:** skip the steady lane only when
  `historyAllowance() > floor`.

## Nits (optional)

- `sps-sync.js:24,231`: a `crashed` error (any non-Zoho exception) on `pending[0]` keeps the cursor and stops the cycle, so one
  malformed detail (for example a `null` in `line_items`, which throws a TypeError at `:105`) would block items and the sweep on every
  cycle. Guard `l` with an object check and throw `bad()`.
- `sps-sync.js:231`: on resume, filter `state.pending` against `heldAt` so a restart does not re-fetch details it already mirrored.
- `config.js:57`: any `NODE_ENV` other than `production` (for example a typo such as `prod`) turns every production check off. Accept only
  `production|test|development`.

## What I verified and found clean

- Auth chain: requireAuth is mounted once ahead of every protected router. The office-IP check runs on every request for fulfilment.
  Shared accounts are fulfilment only, their roles are locked, they cannot change their own password, and their sessions end after 12 h.
  A re-login revokes the old session. Purge runs at start and every 15 min. Clean.
- Rate limiter: memory is bounded, `undo`/`reset` behave correctly, and the IP check runs before the user check. Clean.
- Config hardening (S2, S4, S6, S7, N1, W6): the checks are correct and covered by `test/config-hardening.test.js`.
- Audit: unknown typed usernames are no longer stored raw (`routes/auth.js:16-17`).
- Restart safety: lease clear and release, migration sha guard unchanged, startup writes idempotent.
- No secrets added, no SQL built by string concatenation in server code, no non-GET Zoho calls (`fake.nonGets()` is asserted as 0).
