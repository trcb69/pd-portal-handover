# Code review round 2: Production Dashboard joint demo v0.1 (My jobs + fix pass)

Repo `/root/dev/production-dashboard-v01`, branch `feature/joint-demo-v0.1`, diff `ed434eb..HEAD`
(275b860, c3c98e0, 6b8cda2 = My jobs; f61bc83, e293ddc, 18f2a56 = fix pass). Reviewed 25 Oct 2026 by code-reviewer.
Specs: rev4 Rev 4.8 (§2.5, §2.7, §5, R4-AC1, R4-AC7, §19 N2, §20), joint-demo §2 (line 80-82, "My jobs (reduced)"),
pd-demo-release §3 (line 101 labels) and §5.1.

Runs by the reviewer: `node --test test/build-stamp.test.js test/joint-demo-gateway.test.js test/joint-demo-setup-followups.test.js`
gave 19/19 pass. Playwright `my-jobs.spec.js` + `admin.spec.js` gave 17/17 pass. I did not run the full `npm test`; the test-runner has it.
`git ls-files node_modules` is empty, and the diff adds no symlinks.

## Verdict
APPROVE-WITH-NITS

## Critical (must fix before merge)
None.

## Warnings (fix now or file a ticket)
- [W1] `web/src/pages/MyJobs.tsx:139` — `onFocus={markSeen}` is on the card container. React's `onFocus` bubbles, so any
  focusable child counts: the Job card checkbox, "Send to …" and "Other unit". **Tabbing through the page therefore marks
  every unread card seen**, even though the user never opened any of them. Under the "New for me" filter it is worse.
  Each focus causes `onChanged` → a refetch, the focused card drops out of the list, and keyboard focus falls to `<body>`.
  That breaks the tab order (WCAG 2.4.3). I do not accept "seen by tabbing past". The click trigger is fine.
  — Fix: remove `onFocus`. Call `markSeen()` from the keyboard *actions* instead: in `ask()` (`:77`), in the checkbox
  `onChange` (`:162`) and in the "Other unit" toggle (`:95`). Keep `onClick` for pointer users. Add one e2e:
  Tab through two unread cards, then reload, and both still say "New for me".
- [W2] `web/src/lib/jobs.ts:20` — the label map is `4 Order, 7 Packed (SmarTAG), 8 Checked (Standardization),
  10 Invoiced (to SH)`. Stage ids 7/8/10 are the package / shipment / invoice detectors (`002-seed.sql:26-28`), so
  the mapping matches **pd-demo-release §3 line 101** and the test-first e2e (`test/e2e/my-jobs.spec.js:129`).
  **Rev 4.8, though, names the steps Bundled → Packed → Shipped → Invoiced** (§2.5 line 185, §20 line 491, R4-AC3
  line 307) and says "There is no 'Checked' step" (line 188). In the demo, the presenter presses **Shipped** on `/demo`
  and the dot that lights says **Checked**. The code is not wrong. The two specs disagree, and the doctrine sends that
  question to the human. Two smaller points on the same strip. Stage 5 shows the API name "Bundle", which is fine for
  the Bundled step. For OPD-family divisions the strip order is `4,6,5,7,…` (`002-seed.sql:39`), so after **Bundled**
  the amber "next" ring stays on Pick list until **Packed** sets `quantity_picked` (§20).
  — Fix: the human picks one wording. Either rename the `/demo` buttons to the dashboard labels ("Shipped → Checked"),
  or change `DEMO_LABEL[8]` to `'Shipped'` and update `my-jobs.spec.js:129`. Record the choice in rev4 §2.5.
- [W3] `LATER.md` (rows S2, S4 deleted in f61bc83). Both were only partly fixed. **S2:** an explicit `BRIDGE_HOST` is now
  refused and the skip is logged (`server/config.js:62`, `server/startup.js:8`). But a trailing-dot origin
  (`APP_ORIGIN=http://localhost.:4300`, hostname `localhost.`) is still not "local". The bridge then binds the
  default 172.17.0.1 (`config.js:57-61`). **S4:** the logout is done (`cli/demo-setup.js:48-49`). The runbook line
  (password via `read -s` + `export`, never `.env` or argv) exists nowhere: I grepped the repo and the specs.
  `cli/demo-setup.js:1` still loads `dotenv/config`. — Fix: put both rows back with only the open half, or fix
  them. For S2, strip one trailing `.` before `LOCAL_HOSTS.has(...)`. For S4, add the line to the CLI header comment
  `cli/demo-setup.js:9-10` and to the demo runbook.

## Nits (optional)
- [N1] `web/src/pages/MyJobs.tsx:196` — the greeting count ("N jobs need you today") is worked out from `list.data`,
  which is the *filtered* list. Click "Past due" and the greeting changes to the past-due count. It also shows "0 jobs"
  while the list loads. No spec fixes the rule; the Calm sample has only the sentence. — Count from an unfiltered
  `state=open` query (or a server counter), and hide the sentence until the data arrives.
- [N2] `cli/lib/demo-setup.js:101` — `retire()` renames with `/\.json$/`. A custom `--undo-file` without `.json` is
  renamed to itself, so it is never retired, and the round-1 W1 bug returns for that name. — Append
  `.<ts>.done` when the name does not end in `.json`, or refuse such a name.
- [N3] `server/zoho/client.js:23,48` — the token POST follows redirects by default. Config cannot point it off Zoho or
  loopback (verified below), so this is defence in depth only. — Add `redirect: 'error'`, the same as Rev 4.8 §20 asks
  of the gateway.
- [N4] `server/config.js:44` — `gatewayUrl` returns the raw string. A trailing slash (`…:4850/inventory/v1/`) gives `//salesorders`.
  — Return `env[key].replace(/\/+$/, '')`. Also add `DEMO_GATEWAY`, `ZOHO_API_BASE` and `ZOHO_TOKEN_URL` (commented) to `.env.example`.
- [N5] `test/joint-demo-setup-followups.test.js:15` — `ROOT = path.resolve('.')` depends on the cwd. It only reads and
  spawns, so nothing is written in the wrong place, but the file fails when run from another directory. —
  `fileURLToPath(new URL('..', import.meta.url))`.

## Round-1 findings: status
| ID | Status | Evidence |
|---|---|---|
| C1 node_modules symlink | FIXED | 05cfecf; `.gitignore:1` = `node_modules` (no slash); `git ls-files node_modules` is empty |
| W1 undo never retired | FIXED | `cli/lib/demo-setup.js:85-102` (db_path bound, checked on run *and* undo, `retire()` after success at `:188`); test `…followups.test.js:33` = run → undo → API edit → run → undo keeps the edit |
| W2 no log | FIXED | `demo-setup.js:147` (import) and `:178` (inside the undo transaction); test `:67` |
| W3 cwd-relative defaults | FIXED | `defaultWorkDir(config.dbPath)` `demo-setup.js:21`, `cli/demo-setup.js:31-32`; process-boundary test from a foreign cwd `:104` |
| W4 `cf_portal_ref` name | FILED | `LATER.md` W4 + D2 (OP G1); accepted |
| N1 bridge skip silent / bare TypeError | FIXED | `config.js:46-48,62`, `startup.js:8`; tests `gateway.test.js` N1/S2 |
| N2 displayFilter signal / `shown` name | FILED | `LATER.md` N2; accepted |
| N3 stage enum | FIXED | `admin-config.js:54`; test N3 |
| N4 CLI logout | FIXED | `cli/demo-setup.js:48-49`; test checks `sessions` count 0 |
| N5 W2DEBUG | FIXED | removed `joint-demo-sync.test.js:34` |
| N6 markAllSeen hides | FILED | `LATER.md` N6 (before S2 widening); accepted |
| S1 symlink | FIXED | as C1 |
| S2 tunnel-only backstop | PARTLY | explicit BRIDGE_HOST refused + logged; trailing dot open → W3 |
| S3 undo audit / validation / 0600 | FIXED | `demo-setup.js:160-168` checks unit + source before any write; `:96` mode 0600; tests `:80`, `:94` |
| S4 CLI session / password handling | PARTLY | logout done; runbook line missing → W3 |

## What I verified and found clean
- **Gateway config (R4-AC1, §19 N2, R4-AC7)**: without `DEMO_GATEWAY=1`, both URLs are the hard Zoho defaults. Setting
  either variable, even to `''`, stops the start (`config.js:65`). With it, each half is required and checked on its own
  (`:40-44`): `http:` only, hostname exactly `127.0.0.1` (WHATWG normalises `127.1` / `0x7f000001` to loopback; the
  `127.0.0.1:x@evil` userinfo trick and `127.0.0.1.evil.com` are refused), port required, no credentials. Only
  `makeClient` (`zoho-sync.js:52`) uses them, and the old `API_BASE`/`TOKEN_URL` exports have no other importer. Health
  and the start log say `DEMO MODE (gateway)` only in demo mode, and the log line carries no secret. NODE_ENV=production
  still works in demo mode. The tests cover all of these, including a real loopback server that sees the token POST
  and the GET.
- **Undo binding**: an old snapshot without `db_path` is refused with a clear message, and the refusal happens before
  any change. A failed undo leaves the file live, so it can be retried (the restore is idempotent). The temp-file +
  rename write is kept.
- **Audit rows**: the actor is the string `cli:demo-setup`, following the `'anon'` precedent (`routes/auth.js:31`).
  `audit_log` stays append-only.
- **My jobs API use**: `GET /jobs?state=open|all&counter=…` uses whitelisted values only (`job-queries.js:75-76`;
  `new_for_me` is in `COUNTERS`). The tick goes to `POST /jobs/:id/steps/3`, Send to `POST /jobs/:id/send` with
  `expected_unit` + a `client_token`, and seen to `POST /jobs/:id/seen` (no body; it is idempotent and readable-checked,
  `job-writes.js:117-126`). Every id goes through `encodeURIComponent`. A 409 is handled with a refresh. Admins are
  redirected and their queries are disabled. Scope matches joint-demo line 82 ("strip, Job card tick, Send next,
  Unassigned"). `/units` matches the `Unit` type.
- **XSS**: there is no `dangerouslySetInnerHTML` or `innerHTML` in `web/src` (the one hit in dist is React's own
  runtime), and no `href` is built from data. Every Zoho string is rendered as a JSX text child.
- **Unassigned page**: an admin-only route (`jobs.js:119`) with error and empty states; the existing e2e covers it.
- **e2e edits are honest**: `admin.spec.js:78`: the C1 assertion (no loop back to `/password`) is unchanged, and only
  the heading of the replaced Home page changed. `:86`: migration 006 line 90 really sets `working_weekdays` to Mon–Sat,
  so Sat is the last box, and the test was red before this diff for that reason.
- **The new "seen" e2e would fail without the change**: at 6b8cda2 `web/src` has no `/seen` call (`git grep`), so the
  tile count could not drop. It compares against a measured `before`, checks again after a reload, and passes now. It
  covers only the click path; the focus path is untested (see W1).
- **web/dist** was rebuilt, and `build-stamp.test.js` passes against the committed stamp.
- **Possible lead for the 4 unexplained unit failures**: `runDemoSetup` spawns `cli/import-routes.js` with the parent's
  *whole* `process.env` (`demo-setup.js:145`). The importer calls `loadConfig()` (`import-routes.js:74`). Since f61bc83
  a shell that exports `APP_ORIGIN=http://localhost…` together with a non-empty `BRIDGE_HOST`, or `ZOHO_API_BASE` /
  `ZOHO_TOKEN_URL` without `DEMO_GATEWAY=1`, makes every test that runs the set-up fail with "import-routes failed"
  (`joint-demo-setup-script.test.js`, `joint-demo-setup-followups.test.js`). A second, weaker lead is the
  cwd-relative paths (`build-stamp.test.js:7`, N5). I have not reproduced either.
