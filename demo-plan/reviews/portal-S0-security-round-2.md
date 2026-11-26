# Order Portal S0: security re-audit, round 2 (24 Oct 2026). Verdict: PASS-WITH-CHANGES

Repo `/root/dev/order-portal`, branch `feature/s0-foundation`, diff `c18b382..cbd795d`. Tests re-run: 150/150 pass.
Round 1: `portal-S0-security.md`. This round only read the code; nothing in the repo was changed.

## Scope and trust boundary
- v0.1 demo: the app listens on loopback only. `APP_ORIGIN=http://localhost:4800`, `BRIDGE_HOST` empty, and users reach it through an SSH tunnel, so every client shows up as 127.0.0.1. It may read from a local demo gateway instead of Zoho.
- v0.3: public behind Traefik, with the office-IP rule for the shared fulfilment login.

## Status of round-1 findings
| # | Status | Evidence |
|---|---|---|
| S1 limiter memory | FIXED | `server/auth/rate-limit.js:51-66`: an empty key is deleted, a sweep runs once per window, and the map is capped at 10,000 keys. `routes/auth.js:33-34` checks per-IP first and skips the per-user lookup when the IP is blocked. Test: `test/auth-hardening.test.js:13`. |
| S2 office IP per request | FIXED (one caveat, R3) | `server/auth/middleware.js:37-41` checks the office IP on every authenticated request. `config.js:82` refuses to start in production with https and no office list. Tests: `auth-hardening.test.js:30`, `config-hardening.test.js:227`. |
| S3 restore_pending | PARTLY | `services/restore-pending.js:28-29` now compares start time with the flag time. Test: `restore-pending.test.js:93`. Nothing writes `reconcile_started_at` yet (the Reconcile job comes in S1), so for now the UI clear is fail-closed (always 409). The fix depends on the future writer behaving correctly (R7). |
| S4 forged XFF | FIXED (ops part open) | Test `auth-hardening.test.js:48` covers both the limiter key and the office rule. `config.js:81` refuses a loopback trusted proxy in production. Still open: the fixed Traefik IP (default 172.18.0.3, `config.js:73`). The demo still trusts loopback in practice (R1). |
| S5 typed usernames in audit | FIXED | `routes/auth.js:16-17,37,46` store only known names, or `{username_unknown, username_length}`. Tests: `auth-hardening.test.js:63-83`. |
| S6 bridge host | FIXED (caveat, R3) | `config.js:55,57`: a localhost origin means no bridge; private IPv4 only. Test: `config-hardening.test.js:244`. |
| S7 ZOHO_FAKE_URL | FIXED | `config.js:52`: allowed only with NODE_ENV=test and an http loopback URL. Test: `config-hardening.test.js:257`. Side effect: R1. |
| S8 password change | FIXED | `routes/auth.js:92` refuses a shared account. `:94-98` counts per user before the scrypt check (no await between check and count). Tests: `auth-hardening.test.js:86-110`. New gap: R6. |
| N1 requireAuth in create-app | FIXED | `create-app.js:35-36`: only `/health` and `POST /auth/login` come before it. |
| N2 shared = fulfilment only | FIXED | `routes/admin.js:12,16` (create) and `:63,69` (roles locked). Tests: `auth-hardening.test.js:112-132`. |
| N6 Zoho id validation | FIXED | `services/sps-sync.js:155` (SO ids) and `:305` (item ids) both check `^\d{1,25}$`. |
| N9 sessions | FIXED for S0 | Re-login ends the old session (`auth.js:60`). Purge at start and every 15 min (`sessions.js:91-97`, `startup.js`). `Cache-Control: no-store` on /api (`create-app.js:32`). Shared login capped at 12 h (`sessions.js:55,62`). Write/approval/upload limits are still due in S1. |
| N3, N4, N5, N7, N10 | NOT ADDRESSED (not due yet) | `routes/health.js` still returns the full body without auth (fine on loopback, must be done before v0.3). N10 (`__Host-` cookie over http://localhost): Chrome and Firefox accept it; older Safari does not. |

## New findings
- [R1] MEDIUM for the demo
  - where: `server/config.js:52,58,78-83`; demo env in `test/demo-instance.test.js:31-34`
  - what an attacker does: Pointing the app at a local demo gateway needs `ZOHO_FAKE_URL`, and that is accepted only with `NODE_ENV=test`. With NODE_ENV=test, every production start check is off. The demo env shown in the tests also sets `TRUSTED_PROXY_IPS=127.0.0.1`. Behind an SSH tunnel every client is 127.0.0.1, so every client is a "trusted proxy" and `X-Forwarded-For` sets its IP. Anyone with the tunnel, or any local process on the VPS, can send a fresh XFF on each request. That gets past both login limiters and would get past the office rule if one were configured.
  - impact: no limit on password guessing for anyone who can reach loopback. Limited exposure in the demo (tunnel users are trusted), but the demo run quietly turns off the guards round 1 asked for.
  - fix: for the demo, set `TRUSTED_PROXY_IPS=192.0.2.1` (TEST-NET, never a real peer) and do not use loopback. Better: add an explicit demo/gateway mode (e.g. `ZOHO_GATEWAY_URL`) that is accepted only when APP_ORIGIN is loopback, BRIDGE_HOST is empty and ZOHO_WRITES_ENABLED=false, so the demo keeps NODE_ENV=production. Add a config test for the demo env.
- [R2] LOW
  - where: `config.js:58`
  - what: production checks run only when `NODE_ENV === 'production'`. Any other value (`development`, `staging`, `prod`, `Production`) skips the PORTAL_INSTANCE, loopback-proxy and office-list checks.
  - fix: `const production = nodeEnv !== 'test'`, or reject unknown NODE_ENV values.
- [R3] LOW
  - where: `config.js:55,82`
  - what: both checks match on the origin's string prefix. `APP_ORIGIN=http://127.0.0.1:4800` or `http://[::1]:4800` still binds the 172.17.0.1 bridge by default, so every EasyPanel container can reach it. A production `http://` origin that is not localhost skips the office-list check.
  - fix: parse the origin. No bridge by default when the host is loopback. Require the office list when the host is not loopback, whatever the scheme.
- [R4] LOW now, MEDIUM before v0.3 (pre-existing, not a regression)
  - where: `routes/auth.js:22-23,32`
  - what: the per-user key is `username|ip`, and no limit applies per account. 100 IPs give 1,000 guesses per 15 min against one account. IPv6 rotation inside one /64 defeats both limiters. Map eviction (`rate-limit.js:58`) needs about 10,000 fresh keys, so 100+ IPs, which already buy more guesses than an evicted counter would. **Eviction adds no real new power.**
  - fix (before v0.3): add an IP-free per-account limiter (e.g. 50 failures/hour, then a soft lock and an audit row). Key IPv6 clients by /64.
- [R5] LOW
  - where: `rate-limit.js:58,65`
  - what: when a key is evicted, it stays in `tripped` until the next sweep. If it is locked again in that window, no `auth.login_locked` audit row is written.
  - fix: `tripped.delete(evictedKey)` on eviction.
- [R6] LOW
  - where: `routes/admin.js:43`; `routes/auth.js:92`; no admin or CLI password-reset path exists (`cli/` has only `restore-pending.js`)
  - what: since S8, the shared fulfilment password cannot be changed by anyone, although the comment says "the admin sets it and rotates it". When a team member leaves or the password leaks, the only fix is to deactivate the account and create a new username.
  - fix: an admin-only `POST /api/admin/users/:id/password` that is audited and revokes that user's sessions. Or document deactivate-and-recreate as the rotation runbook.
- [R7] LOW (latent, for S1)
  - where: `services/restore-pending.js:22-29`
  - what: clearing trusts `reconcile_started_at` alone. The contract is that it is written only when a run *completes* (holding that run's start time). An S1 writer that records the start time at the *start* would let a running or failed reconcile clear the flag.
  - fix: in S1, write `reconcile_started_at` and `reconcile_completed_at` together, in one transaction, only on success. Make the clear require `completed_at >= started_at > set_at`. Add a test where started_at alone, with no completed_at, gives 409.
- [R8] INFO
  - where: `sessions.js:62,74`
  - what: the shared 12-hour cap lives only in the stored `expires_at`. `loadSession` does not re-check `created_at + SHARED_MAX_MS` for `is_shared`. Every current path sets it correctly (the password route refuses shared accounts), so this is defence in depth only.

## Checked and clean (the new code)
- Session purge (`sessions.js:91-97`): one parameterised DELETE on consistent ISO strings. Its rules match `loadSession` (expired, idle 12 h / shared 2 h, inactive user). Errors are logged, not swallowed (`startup.js`). Safe to run again on every restart.
- Re-login (`auth.js:60`): the old session is deleted only after password, IP and acting-person checks pass. The POST needs an exact Origin, so it cannot be forced cross-site.
- Office IP per request: runs before must_reset and every role route. A refused request does not destroy the session. Other roles are not tied to an address (test `:43`). A fulfilment user off-site also cannot log out; acceptable, because the session still ends after 2 h idle / 12 h total.
- XFF: Express trust is a function over the exact trusted set (`create-app.js:16`), so `req.ip` is the rightmost untrusted hop. This is correct as long as Traefik appends the client address and the trusted IP is really Traefik's (S4 ops item).
- Audit of unknown usernames: the extra lookup runs only on the failure path, so known and unknown names take about the same time. Only the typed name's length is stored.
- Password-change limiter: counted synchronously before the await, so parallel requests cannot all get past it.
- Demo: with `APP_ORIGIN=http://localhost` no bridge listener is bound. Writes are off. The Zoho client is GET-only (`zoho/client.js:48`).

VERDICT: SHIP-WITH-FOLLOWUPS (PASS-WITH-CHANGES). No critical or high findings. Before the demo: fix R1, or at least use the TEST-NET `TRUSTED_PROXY_IPS` and a demo-env config test. R2, R3 and R6 are small and should land with S1. R4, plus N5 (health), must be done before v0.3 public exposure. R7 goes into the S1 Reconcile spec.
