# Security audit: Production Dashboard joint-demo backend (v0.1)

Repo `/root/dev/production-dashboard-v01`, branch `feature/joint-demo-v0.1`, diff `f1a5b30..e80a46c` (5 commits). Audited read-only on 25 Oct 2026.

## Scope and trust boundary
- v0.1: the app binds 127.0.0.1 only. Viewers reach it over an SSH tunnel, so whoever can reach it already has SSH to the VPS (or is a local process or container with host networking). v0.3 adds a public address behind Traefik, reached over the 172.17.0.1 bridge listener.
- New surface: `PUT /api/admin/display-filter`; the `?counter=not_ready_to_run` feed filter; the `ready_to_run` DTO field; the `tunnelOnly` listener rule; the CLI `cli/demo-setup.js` + `cli/lib/demo-setup.js` (needs a root shell and access to the DB file); migration 007.

## Findings
- [S1] SEVERITY: medium
  - where: `node_modules` (git symlink, mode 120000, added in 28738d2) -> `/root/dev/production-dashboard/node_modules`
  - what an attacker does: nobody needs to attack anything. A fresh clone (e.g. the `/root/demo/production-dashboard` checkout in rev4 §2.7, or a later live tree) gets `node_modules` as a symlink into a dev clone. The running service then loads its code from a directory that dev work changes freely. That breaks the dev/production separation, and dependency integrity is no longer tied to the lockfile. On an existing tree that has a real `node_modules/`, the fast-forward fails instead. `.gitignore` has `node_modules/` (directory form), which does not match a symlink, so the symlink got committed.
  - impact: the demo/live service runs unreviewed or changed dependency code; deploys break.
  - fix: `git rm --cached node_modules`; change `.gitignore` to `node_modules` (no trailing slash); reword commit 28738d2 or add a follow-up commit before merge.
- [S2] SEVERITY: low
  - where: `server/config.js:65` (`tunnelOnly`), `server/app.js:19`
  - what an attacker does: the bridge-skip is silent and keys only on the exact hostnames `localhost`, `127.0.0.1` and `[::1]`. Two cases. (a) A misconfiguration such as copying the production `.env` (public APP_ORIGIN) with `BRIDGE_HOST` unset makes the app bind the default 172.17.0.1, where every Docker container (EasyPanel apps) can reach it. (b) `APP_ORIGIN=http://localhost.:4300` (trailing dot) or any non-listed loopback name has the same effect. Exposure stays limited: the session login still applies, the Origin check still applies, and with `TRUSTED_PROXY_IPS=192.0.2.1` no forwarded header is trusted. The primary control is the pre-start `.env` check (rev4 §2.7); `tunnelOnly` is the backstop, and the backstop gives no signal.
  - impact: the demo is reachable from containers on the host, against the "tunnel only" promise (J-AC10).
  - fix: log one line at start (`tunnel only: bridge listener not bound` / `bridge listener bound on <host>`). Make `tunnelOnly && BRIDGE_HOST explicitly non-empty` a startup error rather than a silent skip (the W3 test already allows a non-zero exit). Normalise a trailing dot or refuse it. Keep the pre-start `BRIDGE_HOST=` check as the main control.
- [S3] SEVERITY: low
  - where: `cli/lib/demo-setup.js:139-147` (undo route restore), and the reused `cli/import-routes.js:84-85`
  - what an attacker does: `--undo` deletes and reinserts `item_routes` rows straight in the DB and writes no `audit_log` row. It also trusts `undo.json` as written: no zod check on `unit_code` or `source`, so anyone who edits that file can insert any route rows. Every other step goes through the audited admin API.
  - impact: route changes on the demo DB with no audit trace; an edited undo file bypasses validation. Reaching it needs root plus DB access, so there is no remote abuse path.
  - fix: write one audit row (`actor: 'cli:demo-setup'`, `action: 'item_route.restore'`, item ids + row counts) in the same transaction. Check that each restored `unit_code` exists in `divisions` and that `source` is in the allowed set before inserting. Write `undo.json` with mode 0600.
- [S4] SEVERITY: low
  - where: `cli/demo-setup.js:21-24`
  - what an attacker does: the CLI's admin session is never logged out. It stays valid server-side until it expires. `import 'dotenv/config'` also invites putting `DEMO_ADMIN_PASSWORD` into the checkout's `.env` (gitignored, but it sits on disk), and an inline `DEMO_ADMIN_PASSWORD=… node …` lands in shell history.
  - impact: a leftover live admin session; the admin password stored on disk or in history.
  - fix: `POST /auth/logout` in the `finally` block. In the runbook, say to set the variables with `read -s` / `export` in the shell session, never in `.env` and never inline.

## Verified clean
- Authz on the new route: `PUT /admin/display-filter` sits under `r.use('/admin', requireRole('admin'))` (`server/routes/admin-config.js:94`). The router is mounted after the global `requireAuth` (`server/create-app.js:39-40`). The Origin check (`requireOrigin`, `server/create-app.js:35`, `server/auth/middleware.js`) covers every non-GET request, the same as the existing admin routes. Session cookie is `__Host-`, httpOnly, SameSite=Strict. Tests: J-AC3 403/401 (`test/joint-demo-display-filter.test.js:191`).
- Input validation: zod `.strict()` on the body. `stage` ≤10 chars; `customers` ≤500 × ≤300 chars; `units` ≤50, and each unit must exist in `divisions`. Body limit is 1 MB (`create-app.js:34`). The write and its audit row share one transaction, the same pattern as wait-limits and division-rules.
- Audit: the `display_filter.update` row carries the full saved object (the existing settings routes also store no before-value).
- Display filter is not an access control: it is ANDed with `inScopeOf` (`job-queries.js:111-114`), so it can only narrow what a user sees, never widen it. Failing open matches the spec (§3.2). It is skipped for `unassigned`, and the unassigned list keeps its existing access rule.
- `counter=not_ready_to_run` is whitelisted through `COUNTERS` (`job-queries.js:27,76`). `ready_to_run` puts only fixed enum states in the DTO, never raw Zoho text. `cf_portal_ref` is used only as a boolean and is not rendered.
- SQL: all new queries are static with bound parameters (`JOB_ROWS`, settings upsert, CLI snapshot and undo). No concatenation.
- CLI: credentials come only from env (not argv). The sign-in failure prints only the status code. Error messages carry API response bodies (validation fields), not secrets. `encodeURIComponent` on item ids. File args (`--routes`, `--map`, `--pairs`, `--lid-items`, `--work-dir`, `--undo-file`) are paths the operator types in a root shell, so there is no traversal boundary. Pairs go through the validated admin API. The importer is spawned with an argv array (no shell).
- J-AC10 behaviour is tested (`test/joint-demo-boundaries.test.js:115-133`), including the case where a public origin still binds the bridge.
- Migration 007: additive, nullable, no backfill; MANIFEST hash updated.
- Dependencies: no new packages (dotenv and zod already in `package.json`).

## Accepted risk (already known and deliberately deferred)
- Password sent over plain HTTP from the CLI to 127.0.0.1: it stays on loopback, so this is acceptable for v0.1.
- Display filter fails open by design (spec §3.2).
- `TRUSTED_PROXY_IPS=192.0.2.1` and `BRIDGE_HOST=` are demo values. The v0.2/v0.3 deploy package must change them (rev4 §2.7, R4-AC7). This diff does not cover that.

VERDICT: SHIP-WITH-FOLLOWUPS (= PASS-WITH-CHANGES). S1 must be fixed before any clone or deploy. S2–S4 are follow-ups.
