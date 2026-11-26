# Order Portal S0: code review, round 3 (25 Oct 2026): APPROVE-WITH-NITS

Repo `/root/dev/order-portal`, branch `feature/s0-foundation`, diff `191adcb..1254c78` (bc1d22c, be0ed4b, 1254c78).
I re-ran `npm test` myself: 172/172. Scratch probes and a mutation copy live outside the repo, in
`/tmp/claude-0/-root/d7fbbc68-754b-4b84-b54a-5ec257db2d21/scratchpad/r3/` (`probe.test.mjs`, `mut/`). No source was edited.

## Verdict
APPROVE-WITH-NITS. C1, C2 and C3 are fixed, and so are W-a, W-b, W-c (the case it named), W-d (as an S1 AC) and W-e. The mutation
copy shows the C2 tests are real: with the verifying pass and the sweep upsert removed, both deletion tests fail. Five warnings are
left. W1 and W2 are small, and I suggest fixing them before the demo warm-up. Nothing blocks the merge.

## Status of round-2 findings

| ID | Status | Evidence |
|---|---|---|
| C1 | **FIXED** for runs with more than 5 orders. A residual gap for small steady runs is W1 | `run.failures` is held (`sps-sync.js:145`). `commitFailures` runs only on an ok steady run (`:247`), on history completion (`:282`) or on a pause (`:291`). Tests `sync-review2.test.js:20-59` |
| C2 | **FIXED** | Verifying re-pass from page 1 until a pass finds nothing (`sps-sync.js:267-277`). The sweep upserts unseen items (`:349-353`). Mutation check: with `break` forced and `unseen = []`, both deletion tests fail |
| C3 | **FIXED** | `LATER.md` has W9 (owner + "before S1 routes merge"). W3: `server/env.js` (repo-root `.env`). W4: `openExistingDb` (`db/open.js:20-33`). W5: `cli/create-admin.js` + npm script. Tests `cli-hardening.test.js:27-135` |
| W-a | FIXED | `routes/health.js:8-14,28-29` |
| W-b | FIXED | `KEEPS_POSITION` (`sps-sync.js:27,299`). Only `bad_shape` resets (`:300`). Side effect: see W2 |
| W-c | FIXED for the 404-on-fetch case | `commitFailures` `:153-160`. Test `sync-review2.test.js:146-158`. The wider gap is W5 |
| W-d | LOGGED as an S1 AC | `LATER.md` R7 |
| W-e | FIXED | `sps-sync.js:323-325`. Test `sync-review2.test.js:162-173` |
| nits | FIXED | null line → `bad_shape` (`:109`). Resume skips held orders (`:264`). NODE_ENV list (`config.js:58-60`). N6 helper path (`test/helpers/db.js:7`) |

## Judging the implementer's choices
- **C1 failures held in the run, committed on a clean end, and put back at the front of `pending` on a keep-position error:**
  correct. No duplicates are possible, because `pending` is filtered against `run.failures` (`:276`) and a failure is always already
  shifted out. A failed steady run discards its failures safely, because the watermark does not move and the next delta offers them
  again. The guard is only as good as `MAX_BAD_PER_RUN`, though (W1).
- **C2 verifying pass:** correct, and it terminates. See "Budget and loop analysis" below. `found` is broader than it needs to be (W4).
- **`honourListFilter = true` in the C2 tests:** right. With the filter off, the fake returns the whole list to the steady delta,
  and the steady lane would quietly repair the loss, which would mask the bug. Real Zoho filters.
- **W-b (`upstream` keeps the position and does not stop the cycle):** right for a transient 5xx. For a 5xx that persists on one
  order, it wedges the backfill (W2). The old behaviour (reset to page 1) wedged too, so this is not a regression.
- **W-c (404 → `missing_in_zoho` at commit time):** right, and it is applied only when the run ends well. A 404 on an order the
  mirror does **not** hold still goes to quarantine (W3).
- **W4 `openExistingDb` for CLIs only:** right. The server keeps `openDb`. It checks migration names, not SHAs. That is acceptable
  because the server's sha guard runs at start.
- **W5 `create-admin` (password via stdin only):** right. The CLI refuses a second admin without `--force-additional`, sets
  `must_reset=1` and writes an audit row. Nit below for a TTY.
- **The four changed existing tests:** none of them hides a regression.
  - AC52 and AC49 (3→6 list calls) and B1 (`[...pass, ...pass]`) only add the verifying pass. They still assert the page order and
    the detail count (5).
  - The AC52 failed-first-run test now asserts `['2','3','1','2','3']`. That is the intended W-b behaviour, and run 1 still asserts no
    ok run.
  - The health `deepEqual` only gains the new keys.
  - One weakening: `sync-backfill.test.js:40` skips the "cursor never goes back" check for the **whole** verifying pass, not just at
    the flip to page 1. See Nits.

## Budget and loop analysis (demo: `ZOHO_DAILY_CALL_CAP=2000`, `SPS_HISTORY_DAYS=30`)
- **It cannot loop without bound.** A pass ends the backfill when it finds nothing (`:269`).
  - **Stubborn bad orders:** a bad order counts as `found` at most until its hits reach 3. After that, `planSo` skips it (`:181`).
    Inside one run it is filtered out and subtracted (`:276-277`).
  - **Modifications:** these make the extra passes geometric. A pass repeats only if Zoho modified an order between two page-1 reads
    of the same run. Probe P3 had 300 orders, 30 pages and one modification per virtual minute. It needed 4 passes (120 list calls),
    finished inside one cycle and mirrored 300/300.
  - **Budget stops:** every pass also stops at `historyAllowance() <= floor` (`history_paused`).
- **It cannot starve the steady lane.**
  - `historyAllowance` already subtracts the projected 1,060 steady calls (`budget.js:22-24`).
  - The steady lane runs on every cycle where `page > 1` or the allowance is at or below `floor` (`sps-sync.js:325`).
  - The only cycle that skips it is one that starts at page 1 with allowance left. That happens only after a pause exactly at the
    flip, and page 1 of the full list then covers the same changes.
- **Cost:**
  - With 30 days (about 390 orders, 2 pages of 200), a pass costs about 2 list calls. The verifying pass adds about 2–8 calls in
    total, which is negligible against about 540 history calls a day.
  - Note: `SPS_HISTORY_DAYS` does **not exist yet** (grep finds no use in `server/`). Until R4-AC5 lands, the backfill and the
    verifying pass read the **whole** SPS list. That is about 1 call per 200 orders per pass, done once.
  - When R4-AC5 adds the cutoff, it must end the verifying pass at the same cutoff (set `state.last` from the cutoff, not only from
    `has_more_page`). Otherwise the check pass reads past 30 days.

## Critical (must fix before merge)
None.

## Warnings (fix now or file a ticket)
- **[W1] `server/services/sps-sync.js:143-145` with `:247`.** In a small steady run, a detail-only outage still quarantines orders
  for good. `MAX_BAD_PER_RUN = 5` only recognises an outage when the run has more than 5 orders, and a typical 5-minute delta has
  1–3. Probe P1: 2 orders changed, details returned maintenance HTML for 4 cycles while the list worked, then recovery. Result: 5 of
  7 orders mirrored, 2 at `hits=3`, and they are skipped until Zoho modifies them again. The loss is now visible as
  `/health.sps.quarantined` (W-a), which is why this is not Critical. (A full outage also breaks the list call, so the run fails
  and commits nothing.) **Fix:** count successful detail fetches in the run (`run.okDetails`). In `commitFailures`, add no hits when
  `run.okDetails === 0 && run.failures.size > 0` (no success means it cannot be told apart from an outage). Add test P1.
- **[W2] `server/services/sps-sync.js:47` and `:299`.** One order whose detail answers 5xx on every try wedges the backfill at that
  order for good, because `upstream` keeps the position and `pending[0]` is the same order every cycle. Probe P2: 30 orders and one
  persistent 503. After 30 cycles the backfill was still at page 3 with 12 of 30 orders mirrored, and every history run was
  `failed`. If that order is ever modified, it also fails every steady run (`upstream` throws out of `workSo`), so the watermark
  freezes and health goes stale. **Fix:** in `workSo`, treat an `upstream_5xx` on a **detail** call as per-order. This is now safe:
  it counts toward `run.bad`, more than 5 fails the run, nothing is committed on a failed run, and W1 adds the no-success guard. A
  list 5xx keeps today's behaviour.
- **[W3] `server/services/sps-sync.js:153-161`.** An order the mirror never held, deleted between the list and its detail call, 404s
  into quarantine. `retryQuarantined` pushes it to `hits=3`, and `/health.sps.quarantined` then reports 1 forever. That is a
  permanent false alarm (probe P5). **Fix:** for `notFound` with `heldAt === undefined`, delete any quarantine row and log
  `so_gone_before_mirrored` instead of counting a hit.
- **[W4] `server/services/sps-sync.js:184` and `:277`.** `added` counts every listed order the mirror does not hold *at that modified
  time*, including ordinary edits to held orders. The steady lane catches those edits anyway. Under load, the result is the extra
  passes measured in P3. The deletion shift can only hide ids the mirror does not hold at all. **Fix:** have `planSo` return
  `added = work.filter((w) => heldAt(w.id) === undefined).length`. The edited orders are still fetched, but they do not trigger
  another pass.
- **[W5] `server/services/sps-sync.js:151-160` (scope of W-c).** `missing_in_zoho` is set only when a held order is fetched again and
  answers 404. That happens only if Zoho modifies it and then deletes it, or if it is in quarantine. A held order deleted with no
  modification is never fetched again and stays live in the mirror. The verifying pass compares list → mirror, not mirror → list.
  **Fix:** log a LATER.md row with an owner and the condition "before S1 uses `sps_salesorders` for routing". It needs an id
  reconcile (all list ids vs held ids at the end of the verifying pass, then a 404 check on the difference, distrusted above N, the
  same as the item sweep `:354-367`).

## Nits (optional)
- `server/routes/health.js:6` copies `QUARANTINE_AFTER = 3`. Export it from `sps-sync.js` so the two cannot drift.
- `test/sync-backfill.test.js:40` turns off the monotonic-cursor check for the whole verifying pass. Reset `page` at the flip and keep
  asserting within the pass.
- `cli/create-admin.js:22`: on an interactive terminal, `readFileSync(0)` echoes the password and waits for EOF. Refuse when
  `process.stdin.isTTY`, with the `printf … |` usage line.
- `test/sync-review2.test.js:108` builds SQL with `'?'.replace(...)`. Use a bound parameter (test only).

## What I verified and found clean
- Correctness: C1/C2/C3 and W-a…W-e were each mapped to file:line. 172/172 tests pass, re-run by me. The mutation check proves the
  C2 tests fail without the fix.
- Data integrity: no hit count changes on a failed run. 404 marking runs in one transaction with the header, the lines and the
  quarantine. Resume after a crash skips held orders. The `missing_in_zoho` status is not blocked by a CHECK constraint (`001-schema.sql:38,43`).
- Security: no new route. The CLI takes the password on stdin only, enforces the 10-character minimum (`password.js:8`), refuses a
  taken username or a second admin, and audits. No secrets, no SQL concatenation in server code, and `nonGets()` stays at 0.
- Blast radius: `.env` is resolved from the module location (`server/env.js:6`). The CLIs never create a DB. The test helper path is
  absolute. `NODE_ENV=development` now runs the production checks (intended, R2). The demo uses `test` (LATER R1).
- Budget: the verifying pass terminates and does not starve the steady lane (analysis above).
