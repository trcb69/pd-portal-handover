# Order Portal S0 — security audit (21 Oct 2026): PASS-WITH-CHANGES

Repo `/root/dev/order-portal`, `feature/s0-foundation`, 04fecd8..c18b382. No critical/high. Fix S2 (at least the empty-list
start check), S5, S6 before the v0.1 deploy; S1, S3, S4 before S1 writes or the v0.3 public exposure.

- **S1 MED** Limiter memory growth without hashing: `server/auth/rate-limit.js:9` stores empty arrays; `routes/auth.js:28-29` checks per-user before per-IP. Fix: check byIp first; delete empty keys; 15-min sweep + key cap.
- **S2 MED** Office-IP rule only at login and skipped when empty: `routes/auth.js:45`, `config.js:62`, `sessions.js:16-34`. Fix: enforce per request for fulfilment sessions; refuse to start when APP_ORIGIN is https and FULFILMENT_ALLOWED_IPS is empty.
- **S3 MED** restore_pending cleared by a reconcile that started before the flag: `services/restore-pending.js:26-27`. Fix (S1): record `reconcile_started_at`; clear only if started-at > set-at and completed; test.
- **S4 LOW–MED** No test that a client cannot spoof XFF: `test/helpers/app.js:23,44`, `create-app.js:16`. Fix: test with non-loopback TRUSTED_PROXY_IPS + forged XFF (rate-limit key and fulfilment 403); refuse loopback in TRUSTED_PROXY_IPS in production. Ops: Traefik needs a fixed IP (`config.js:61` default 172.18.0.3).
- **S5 LOW** Raw typed username (maybe a password) stored in append-only audit: `routes/auth.js:32,41`. Fix: store only known usernames/ids; else a marker + length or keyed hash.
- **S6 LOW** BRIDGE_HOST defaults to 172.17.0.1 (`config.js:41`). Fix: refuse to start when APP_ORIGIN is http://localhost and BRIDGE_HOST non-empty; only private ranges allowed.
- **S7 LOW** ZOHO_FAKE_URL refused only when NODE_ENV=production (`config.js:53`). Fix: allow only when NODE_ENV=test and the URL is 127.0.0.1/localhost.
- **S8 LOW** No rate limit on password change; shared account can change its password (`routes/auth.js:74-90`). Fix: per-user limiter; refuse for is_shared.
- **Notes** N1 move requireAuth into create-app before admin/orders routers · N2 shared accounts = fulfilment only, roles locked · N3 acting person in audit() from the session · N4 narrow GET /orders/:id before S1 adds fields · N5 health: only {ok} off-loopback; log the caught error (`health.js:24`) · N6 validate Zoho SO ids `^\d+$` (`sps-sync.js:86`) · N7 CLI: print DB path, fileMustExist · N8 migration numbering contiguity · N9 old session on re-login, expired-session cleanup, Cache-Control no-store, shared login max ~12 h, S1 write/approval/upload limits · N10 __Host- cookie on http://localhost (older Safari).
- Verified clean: scrypt + dummy hash timing, login limits counted before hashing, trusted-proxy IP, server-generated hashed sessions, cookie flags, exact-Origin CSRF, headers, admin/stub authorisation, zod everywhere, no secrets in logs/errors, GET-only Zoho client, bind checks, restore_pending fail-closed, migration hash checks, append-only triggers.
