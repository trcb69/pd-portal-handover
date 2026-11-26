# Code review round 2 — demo gateway (`feature/demo-gateway`)

Reviewed 25 Oct 2026. Worktree `/root/dev/order-portal-gateway`, `git diff 975e016..HEAD` (11c1ecc, cd805cc, 443bf48, 38a186a).
Spec Rev 4.8 §2, §20. `npm test` re-run by me: **273/273 pass**. I rebuilt `maps.json` from the real recording (`details.json`) into a
scratch path: 309 orders, 234 items, **102 materials**. Consumers read: dashboard `/root/dev/production-dashboard-v01`
(`zoho-sync.js`, `cli/import/upsert.js`, `shared/text.js`, `line-jobs.js`, `zoho-queue.js`, `zoho/client.js`, `config/zoho-columns.json`),
portal `server/services/sps-sync.js`, `server/zoho/client.js`.

## Verdict
**BLOCK**

## Critical (must fix before merge)

- **[C1] `tools/demo-gateway/server/create-gateway.js:398` + `:441`: a DEMO bundle never reaches the order's Bundle step. W1 does
  not work end to end.**
  The dashboard does not take `so_key` from the first word of `reference_number`. It uses `soKey()` (`shared/text.js:7-11`):
  `/^([A-Z]+-\d+)(\s*-.*)?$/`. The bundle importer stores `so_key: soKey(rec.reference_number)` (`cli/import/upsert.js:137`). The
  Bundle step joins on `so_key = salesorder_number` (`line-jobs.js:163-171, 224-239, 435-438`). The re-fetch queue joins the same way
  (`zoho-queue.js:63`). The DEMO number is `DEMO-JOBORDER-<yymmdd>-<nnn>`, and the regex needs digits right after the first `-`. I ran
  it against the dashboard's own function:
  `soKey("DEMO-JOBORDER-261025-001 - F") → null` (and `soKey("JOBORDER-04512 - F") → "JOBORDER-04512"`).
  So every sandbox bundle row is stored with `so_key = NULL`. The Bundle step on a combo item stays **"not seen yet"**, which is the
  exact problem round-1 W1 was meant to fix (R4-AC3 "gains the Bundled tick"). `test/gateway-bundles.test.js:46` passes only because it
  checks the wrong rule (`split(' ')[0]`, with the comment "the dashboard derives so_key from the first word").
  **Fix (smallest diff, spec owner to approve because §2.3:164 fixes the number format):**
  (a) Change the DEMO number to one that `soKey` returns whole, keeping the `DEMO-` prefix the DEMO chip needs (§3:271). The tail
  after `DEMO-` must be digits only. Example: `DEMO-<yymmdd><nnnn>` → `DEMO-2610250001`. Do **not** use `DEMO-261025-001`: `soKey`
  would read the `-001` as a suffix and return `DEMO-261025`. Update §2.3:164 and the `create-gateway.js:398` number, and fix
  `load()`'s `seen.number` parse at `:146`, which today splits on `-`.
  (b) Replace the assertion at `gateway-bundles.test.js:46` with a contract test that runs the dashboard's regex, copied verbatim
  with a `file:line` comment, and asserts `soKey(b.reference_number) === so.salesorder_number`. Add a second assertion that the
  number matches the sandbox `load()` parse.
  Widening the dashboard's shared `soKey` instead is the riskier choice. It parses every real bundle reference, so I do not
  recommend it.

## Warnings (fix now or file a ticket)

- **[W5 from round 1, still open, expected] `test/fixtures/list-filters.json` `_note`.** The projects/contacts filter lists are still
  assumed. When S1-demo lands, also check its `sort_column`. `SORT_COLUMNS` (`create-gateway.js:19`) allows only
  `last_modified_time`/`created_time`, so S1 sync sorting projects/contacts by name would get a 400. This is the only item left open
  from round 1.

## Nits (optional)

- [N1] `create-gateway.js:233` — the comment "one app cannot starve the other" is not accurate. The dashboard and the portal's sync
  both use the **read** tag (portal `sps-sync` → `zohoReadRefreshToken`), so they share one lane. The lanes separate read from write,
  not app from app. In practice this is harmless: each app sends one upstream call at a time, so the queue never holds more than
  about two calls. Reword the comment to "a read flood cannot starve the write token".
- [N2] `create-gateway.js:635` — the Host check needs `localhost:<listening port>`. If a presenter tunnels with a different local
  port (`ssh -L 9000:127.0.0.1:4850`), the browser sends `Host: localhost:9000` and `/demo` returns 400. Add one line to the README:
  "tunnel with the same local port (`-L 4850:127.0.0.1:4850`)".

## Round-1 findings

| # | Status | Where |
|---|---|---|
| C1 materials | **FIXED** | `create-gateway.js:329-337` (items → materials → mirror `name`), `:367-369`; `build-maps.mjs:91, 115-118`. Real data: 102 materials recorded. Six-flag rule still applies to line items only (`:375`, test `gateway-materials.test.js:46`) |
| W1 bundles | **PARTLY** | Gateway side done: `:434-451` (row keys = `zoho-columns.json` bundles fields), `:506` merge, `:456` `quantity_picked` (Pick list now ticks). Join broken; see new **C1** |
| W2 timeouts | **FIXED** | `:202, 217, 277` (20 s, `redirect: 'error'`), abort mapped to 502 at `:280-283`; hung-refresh test `gateway-upstream-hardening.test.js:45` |
| W3 token before slot | **FIXED** | `:272-273`; test `:61` would fail on the old order |
| W4 monotonic bump | **FIXED** | `:425`; test `:76` (same-instant confirm) |
| W5 filter fixture | **NOT (expected)** | see Warnings |
| N1 rebuilt query | FIXED | `:531-559`, used at `:601` |
| N2 since check before upstream | FIXED | `:552-556` |
| N3 confirm only from draft | FIXED | `:582` |
| N4 shipment_date | FIXED | `:400` (an invalid value is left out, not refused; acceptable) |
| N5 counter vs sandbox | FIXED | `:143-151` (the number parse at `:146` must follow C1's new format) |
| N6 dir fsync | FIXED | `:85-95, 107` |
| N7 handler catch | FIXED | `:164-165, 700-705` |
| N8 relative paths | FIXED | `main.js:31-33`, `startup-checks.js:32` |
| N9 refresh back-off | FIXED | `:206, 225` |
| N10 recorded_at | FIXED | `build-maps.mjs:110, 131-134` (refuses to invent a date) |

## The implementer's choices

- **Per-lane queues served in turn, refusing at >10 s unless the lane is shorter (`:235-270`): accepted.** The total wait is bounded
  (each lane caps the other). Abandoned entries are skipped without spending a slot (`:249`). Pacing still runs through one
  `nextUpstreamAt`, so G-AC3 holds.
- **Global 20/min on the token route (`:642-645`): accepted.** Both apps refresh about once an hour. A 429 there becomes
  `ZohoError('auth')` (dashboard `zoho/client.js:25`, portal `:23`), which ends only that one sync cycle (`zoho-sync.js:120, 486`).
  It is not permanent.
- **`sort_column` ∈ {last_modified_time, created_time}: accepted.** Both apps send only `last_modified_time` (`zoho-sync.js:165`,
  `sps-sync.js:91`). See W5 for S1.
- **Bundled on a non-combo order bumps the time but creates no bundle: accepted.** It costs one extra detail re-fetch per click and
  causes no wrong state (test `gateway-bundles.test.js:76`).
- **Bundle row shape: matches** `zoho-columns.json` bundles (every `from` key is present, including `composite_item_id`, which the
  sync stores only when present, `upsert.js:136`). `date` is the Colombo date, so it passes the CUTOFF. The **join key** is wrong
  (C1).
- **Test-helper edits: hide nothing.** `fake-upstream.js` drops only `signal` from `everything()`, so it still serialises headers and
  bodies for the secret-leak checks. The abortable rule race copies real `fetch` abort behaviour. `harness noMkdir` is used only by
  the 0700 data-folder test. The fixture contacts were renamed to synthetic names (S8), and the assertions follow them. The materials
  test uses ids absent from `items` (`gateway-materials.test.js:20`).

## What I verified and found clean

- Correctness (materials, upstream hardening, nits): checked against real `maps.json`; no findings beyond C1.
- Data integrity: bundles are persisted in the same atomic write as the orders (`:155-160, 433`), and old sandbox files without
  `bundles` still load (`:133-135`). Re-running Bundled is idempotent (`:444`).
- Security: rebuilt query with a fixed org, `redirect: 'error'`, 0600/0700 modes, `.env` mode and secret-distinctness checks
  (names only, never values), demo-page CSP/no-store/no-referrer/DENY, Host check. No new dependency.
- Blast radius: `node_modules` is not tracked. Paths resolve from the script's location (`main.js:9`, `build-maps.mjs:99`), not
  the cwd. The working tree is clean apart from the untracked `.claude/`.
- Tests: 273/273. The W2/W3/W4/S4 tests would fail on the round-1 code.
