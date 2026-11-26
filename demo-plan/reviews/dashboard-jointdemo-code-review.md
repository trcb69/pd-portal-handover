# Code review — Production Dashboard joint-demo v0.1 backend

Repo `/root/dev/production-dashboard-v01`, branch `feature/joint-demo-v0.1`, diff `f1a5b30..e80a46c`
(e8af351, 28738d2, 5e35d21, 598507b, e80a46c). Reviewed 25 Oct 2026 by code-reviewer.
Spec: joint-demo v0.1 Rev 3.1 §2, §3, §7 (J-AC1–J-AC10); pd-demo-release §3, §6, AC-D1–AC-D7.

`npm test` re-run by the reviewer at e80a46c: 476 tests / 424 pass / 0 fail / 43 skipped / 9 todo (none of
the skips or todos are in `test/joint-demo-*.test.js`).

## Verdict
BLOCK

## Critical (must fix before merge)
- [C1] `node_modules` (tracked file, added in 28738d2) — the commit adds a **symlink**
  `node_modules -> /root/dev/production-dashboard/node_modules`. `.gitignore:1` ignores it now, but it is
  already tracked. Once pushed, `shdeploy production-dashboard` fast-forwards the live tree, so production
  would either load its dependencies from the dev clone (`/root/dev/...`), or the fast-forward fails on the
  live tree's real `node_modules/` directory. — Fix: `git rm --cached node_modules` in a new commit (or
  rewrite 28738d2 before pushing). Check with `git ls-files node_modules` returning nothing. Also check the
  other worktrees made the same way.

## Warnings (fix now or file a ticket)
- [W1] `cli/lib/demo-setup.js:78-83, 101, 138-157` — the undo snapshot is written once and **never retired**.
  `writeOnce` returns early if the file exists, and `undoDemoSetup` leaves the file in place. So in
  run → undo → (admin edits routes, rules or stages) → run → undo, the second undo restores the *first* run's
  snapshot. That silently reverts every interim admin edit to the five rule keys, the stages and the routes
  of every CSV item. The v0.3 re-entry (joint-demo §2: fresh `production.db`, re-run the set-up script)
  hits the same path, because the old `data/demo-setup/undo.json` is still there: the fresh database's
  undo would replay the demo database's snapshot. — Fix: bind the snapshot to the database and to one run.
  Store it in the DB as a `settings` row `demo_setup_undo` (it then travels with the DB file and dies with
  it), or store `{db_path, created_at}` in the file and refuse a mismatch. When an undo succeeds, rename
  the snapshot to `undo.<ts>.done.json` or delete the row, so the next run takes a fresh one. Add a test:
  run → undo → change a rule through the API → run → undo leaves the changed rule.
- [W2] `cli/lib/demo-setup.js:126-127, 141-148` — no log. Spec pd-demo-release §3.2 (Q2 row) and §6 say the
  script "keeps its own log and undo list" *because* `import-routes.js` writes without audit. The importer
  step and the undo's direct `DELETE`/`INSERT` on `item_routes` leave no trace in `audit_log` or anywhere
  else. — Fix: inside the undo transaction, call `audit(db, { actor: null|admin id, action:
  'demo_setup.undo_routes', entity: 'item_route', detail: { items } })`. Do the same once after the
  importer (`demo_setup.import_routes`, with the importer's stdout counts). An appended JSONL file in the
  work directory is also acceptable.
- [W3] `cli/demo-setup.js:20, 37, 45` — `--work-dir` and `--undo-file` default to **cwd-relative** paths
  (`path.resolve('data/demo-setup/...')`), while the DB path is resolved from the repo root
  (`server/config.js:47`, `path.resolve(ROOT, ...)`). The run and its `--undo` started from different
  directories look at different undo files. A run started from `/root` writes to `/root/data/demo-setup`.
  — Fix: default both to `path.join(path.dirname(config.dbPath), 'demo-setup', ...)`. (The W1 DB-row fix
  removes the undo-file half of this.)
- [W4] `config/zoho-columns.json:122` — `cf_portal_ref` is a guessed API name. Joint-demo §2 says the
  mapping comes "from the API name recorded at OP G1 step 6", and Zoho is not set up yet (OQ3). If Zoho
  names the field differently (Zoho often appends `_1` or drops underscores), detail writes store NULL
  (`zoho-sync.js:279,287` only picks present keys) and the Portal-Ref rule of `shown()` never fires. No test
  can catch that. — Fix: add a line to the v0.1 deploy runbook / G1 checklist: "confirm the API name in
  Zoho Settings › Custom fields; if it differs, edit `zoho-columns.json:122` `from`". Optionally put both
  spellings in `from`.

## Nits (optional)
- [N1] `server/config.js:65` — with `tunnelOnly` on and `BRIDGE_HOST` set, the bridge is skipped silently.
  — Add `log.warn('BRIDGE_HOST ignored: APP_ORIGIN is on localhost (tunnel only)')` next to
  `server/app.js:19` (any line except 22, which is pinned by `release-auth.test.js:397`). Also, an
  unparseable `APP_ORIGIN` now throws a bare `TypeError: Invalid URL`. Wrap it:
  `throw new Error('APP_ORIGIN must be an absolute URL')`.
- [N2] `server/services/job-queries.js:89-96, 98` — `displayFilter` fails open on an unparseable row with no
  signal. Only the validated PUT writes the row, so this is acceptable, but a one-time `console.warn` would
  stop a hand-edited row from silently disabling the filter. The module-level name `shown` also shadows
  the meaning of the existing `J.shown` (strip steps, used at `:46,141`). Rename it to `onDisplay`.
- [N3] `server/routes/admin-config.js:54` — `stage: z.string().min(1).max(10)` accepts any text. Use
  `z.enum(['S1','S2','S3','S4'])` (spec §3.3) unless free labels are wanted.
- [N4] `cli/demo-setup.js:28-30` — the CLI signs in and never calls `/auth/logout`, so a live admin session is
  left behind on each run. Log out in the `finally`.
- [N5] `test/joint-demo-sync.test.js:34` — `console.log('W2DEBUG', ...)` (from f1a5b30). Delete it.
- [N6] `server/services/job-writes.js:128-137` (unchanged) — `markAllSeen` also marks hidden jobs read. This
  matches spec §3.1 ("writes not filtered"), but a job hidden at S1 that is widened in at S2 then shows as
  already read. Mention it in the demo notes, or filter it the same way as `unread_arrivals`.

## The implementer's interpretations, judged
1. **AC48 built from `migrationsUpTo(6)`** — accepted, and better than the spec's wording: AC48 is about 006,
   and 007 has its own exact-objects test (`joint-demo-migration-007.test.js:58,87,120`), including a fresh
   start on the real folder.
2. **`tunnelOnly` skips the bridge rather than refusing to start** — accepted. J-AC10 is met, and both
   branches are tested (`joint-demo-boundaries.test.js:115-132`), including the production case still
   binding the bridge. Silence and the bare TypeError → N1.
3. **Fail open / "acted on" = any route or step event / stage 1–10 chars** — accepted. Only
   `job-writes.js:61,79` insert `job_step_events` or `job_route_events`, and only from human tick, untick,
   send and admin-move calls. No sync or sweep path writes them, so "any event" equals the spec's list.
   Fail open matches §3.2. Stage → N3.
4. **One snapshot before the first change; routes restored straight in the DB; MACPRO, STRIP, alias and pairs
   kept** — the coverage is accepted. A snapshot taken before step 1 covers a run killed at any later step.
   The direct DB restore is the only way to put `source='study'` back (`admin-config.js:499` always writes
   `admin`). Keeping the units is consistent with AC-D6 and needed, because the restored families
   reference MACPRO. **But** never retiring the snapshot → W1, and the missing log → W2.
5. **Untested CLI wrapper, password from env** — env over argv is correct. The wrapper is thin, but it holds
   the cwd-relative defaults (W3) and the leaked session (N4). A smoke test that spawns it against the
   release harness would have caught W3.
6. **`W2DEBUG`** → N5.

## What I verified and found clean
- **J-AC5 / filter placement** — `shown()`/`displayFilter()` are called only inside `listJobs`
  (`job-queries.js:89-98, 111-114, 126`). They are absent from `loadContext` (`line-jobs.js:160-196`), from
  `loadQueue`, from the single-SO reads and from the writes. The J-AC5 test compares `loadQueue` entries
  across off, S1 and an empty filter, and would fail if the filter moved into `loadContext`.
- **Correctness vs spec** — the filter covers the scoped list, the counters (`countable` derives from
  `scoped`), search and the `unread_arrivals` badge, and is skipped for `at=unassigned`. Customer matching
  uses `cmpKey` (trim, collapse, case-fold; `shared/text.js:1-6`) on both sides (J-AC6). The home unit, not
  the header, decides (J-AC7). Ready-to-run maps all AC-D1 spellings, null and empty → `not_set`; it is read
  from the header, so it is the same per SO (AC-D2). The counter is null when not fresh, like its siblings.
- **Data integrity** — 007 is a nullable `ADD COLUMN` with no backfill. It is in the MANIFEST with its hash,
  and a restart is a no-op (tested). The detail write only touches present keys, so a payload without the
  field never blanks a stored ref (tested). The xlsx import's explicit column list (`cli/import/upsert.js:27,31`)
  does not touch the column. `PUT /admin/display-filter` uses one transaction plus an audit row and checks
  units against `divisions`.
- **Security** — the new route is under `r.use('/admin', requireRole('admin'))` (`admin-config.js:94`) and the
  global origin check. zod `.strict()` validation with bounded arrays and strings. No secrets added, no SQL
  built from input (the item id in the CLI URL is `encodeURIComponent`-ed, and the DB uses bound params).
- **Restart idempotency** — a second set-up run changes nothing (409s, compare-before-PUT, the importer's
  `same` check, lid skip; tested). The undo is idempotent (tested). Migration on the tenth restart is a no-op.
- **Tests** — the joint-demo tests would fail if the features were removed. They were written first
  (f1a5b30, 49 red). The counters, the search bypass and the badge are asserted, not just the list length.
  No joint-demo test is skipped.
