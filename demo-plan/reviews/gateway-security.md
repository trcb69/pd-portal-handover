# Demo gateway — security audit (25 Oct 2026)

Branch `feature/demo-gateway`, worktree `/root/dev/order-portal-gateway`, diff `9db7c02..HEAD` (b6899d6, f3cd2db, 86b5c2a, 975e016), tests bdcb1b4. Spec Rev 4.7 §2.1–§2.7. Read-only review; nothing was run against Zoho. The URL-parsing checks were run in Node v24.18.0 in a scratch folder.

## Scope and trust boundary
- The listener binds `127.0.0.1` only (`create-gateway.js:528,533`; the host option cannot widen it). Callers: local processes on the VPS, plus viewers' browsers through an SSH tunnel. Docker containers (172.17.0.1) cannot reach it.
- No route is open without a token except `GET /health` (mode + filter_refused count only). `/oauth/v2/token` needs the demo client + secret + one of two demo refresh tokens. `/inventory/v1/*` needs a demo bearer token. `/demo` and `/demo/advance` need `DEMO_PAGE_TOKEN`.
- The real secrets (`ZOHO_CLIENT_SECRET`, `ZOHO_READ_REFRESH_TOKEN`) are used in exactly one place: the POST body to `accounts.zoho.com` (`:158-164`). The upstream access token is used in exactly one place: the Authorization header to `www.zohoapis.com/inventory/v1` (`:191`).

## Findings
- [S1] SEVERITY: medium
  - where: create-gateway.js:442 + :191 (`forward(..., url.search, ...)`); checks at :390-402
  - what an attacker does: the org and filter checks run on Node's WHATWG `URLSearchParams`, but the **raw** `url.search` string is what goes to Zoho. Any difference between how the two sides parse it gets past the allow-list. I tested this: `?organization_id=843825512&page=1;organization_id=2` passes both checks, because Node does not split on `;` and so `page` = `1;organization_id=2`, and it is forwarded verbatim. Values of the allowed list keys (`page`, `per_page`, `sort_column`, `sort_order`, `last_modified_time`) are not checked before forwarding. Whether Zoho's server splits on `;`, or decodes twice, is unknown. Nothing in the gateway rules it out. A Zoho token is user-scoped, so if the `itexe@` login belongs to any other org, a smuggled `organization_id` would read that org's data with the real token. Only a demo-token holder (a local app or process) can try this.
  - impact: the spec's "organization_id=843825512 only, anything else refused before any network call" (§2.1) depends on the two parsers agreeing, not on the gateway itself.
  - fix: build the upstream query again from the parsed values, e.g. `new URLSearchParams([['organization_id', ORG], ...validated])`. Check each value: `page`/`per_page` `^\d{1,4}$`, `sort_order` `^[AD]$`, `sort_column` from an enum, `last_modified_time` in the Zoho date format. Never forward `url.search`. Add tests for `;`, `%00` and double-encoded `%2526`.

- [S2] SEVERITY: low
  - where: create-gateway.js:158 and :191 (`fetch` with the default `redirect: 'follow'`)
  - what an attacker does: if anything on the network path, or Zoho itself, answers the token POST with a 307/308, fetch sends the same body again to the new location. That body holds the client secret and the real refresh token, and the new location can be any host. A redirect on the GET can also move the request off the `/inventory/v1/` prefix with the token attached on the same origin. undici removes Authorization only on cross-origin redirects.
  - impact: the real SPS refresh token could leak, or the host/prefix allow-list could be bypassed after the gateway's own checks.
  - fix: `redirect: 'error'` on both fetches (or `'manual'`, treating any 3xx as a 502). Add a test where the fake upstream returns a 307.

- [S3] SEVERITY: low
  - where: main.js:16-35
  - what an attacker does: nothing checks the strength or uniqueness of the demo secrets. A short `DEMO_PAGE_TOKEN`/`DEMO_CLIENT_SECRET` can be guessed by any local process: the token route has no rate limit. If `DEMO_READ_REFRESH == DEMO_WRITE_REFRESH`, the portal silently gets only read tokens (`:142` wins). If a demo value equals a real `ZOHO_*` value, the real secret ends up in an app's `.env`, which breaks §2.2 ("no real Zoho secret in either app's .env"). The pre-start check in §2.7 (ecosystem file) is not in this diff.
  - impact: weak or reused secrets; the human sees no warning.
  - fix: at start, refuse unless every DEMO_* secret is ≥32 characters, all DEMO_* values are different from each other, and none equals any ZOHO_* value. Report the variable names only, never the values.

- [S4] SEVERITY: low
  - where: create-gateway.js:174-186
  - what an attacker does: there is one global FIFO queue with no fairness between the two token tags. A portal backfill (or a local runaway loop holding the read token) keeps about 15 requests in flight, and the 10 s window fills. The dashboard then gets 429 on every request. A client that disconnects while waiting still uses its slot, and the upstream call still happens and counts against the 7,500/day SPS limit.
  - impact: one app can starve the other's sync during the demo, and calls nobody receives are wasted.
  - fix: a separate queue per tag (read and write) served in turn, or a cap on queued requests per tag. Before the upstream fetch, skip it if `req.socket.destroyed`.

- [S5] SEVERITY: low
  - where: create-gateway.js:155-170
  - what an attacker does: if the real refresh token is revoked or wrong, every paced request makes a new POST to accounts.zoho.com (up to about 90/min). Zoho throttles refresh-token use, so the token can get locked out even after the cause is fixed.
  - impact: availability (the demo stops reading) and noisy auth traffic on the SPS account.
  - fix: after a refresh failure, return 502 without calling Zoho for 60 s, and log `upstream_refresh_failed` with the status only.

- [S6] SEVERITY: low
  - where: create-gateway.js:446-465, :118-122
  - what an attacker does: the `/demo?token=` URL stays in the viewer's browser history and autocomplete. Responses set no `Cache-Control`, `Referrer-Policy`, CSP or `X-Frame-Options`, and the Host header is never checked, so DNS rebinding can reach the tunnelled port. Today rebinding only gets `/health` without a token, and the page loads nothing external (no Referer leak), so the real exposure is small.
  - impact: the token stays on viewer machines; there is no defence in depth on the one HTML page.
  - fix: on `/demo`, send `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`, and `Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; connect-src 'self'` (or a nonce). Refuse requests whose Host is not `127.0.0.1:<port>`/`localhost:<port>`. Rotate `DEMO_PAGE_TOKEN` after the demo.

- [S7] SEVERITY: low
  - where: create-gateway.js:70 (`openSync(tmp,'w')`), :88 (`mkdirSync`), build-maps.mjs:45-46
  - what an attacker does: the files get the default umask. Observed: `data/` drwxr-xr-x and `maps.json` -rw-r--r--. `sandbox.json` (customer names, rates the portal typed) and `maps.json` (111 real end-customer names, 234 items) are readable by any account on the host. `.env` was not in the dev worktree, so its mode could not be checked.
  - impact: low on a root-only VPS, but these are commercial data.
  - fix: `mkdirSync(dir, { recursive: true, mode: 0o700 })`, `openSync(tmp, 'w', 0o600)`, and the same in build-maps. The pre-start check should refuse a `.env` that is not 0600.

- [S8] SEVERITY: low
  - where: test/fixtures/maps.fixture.json (committed)
  - what an attacker does: the fixture says "SYNTHETIC … made-up names", but its contacts are real end-customer brands (TACO BELL, PIZZA HUT, Keells Super). It has no real ids beyond the placeholder and no prices.
  - impact: a small amount of customer-list information in git, which goes against §2.7 "nothing … commercial in git".
  - fix: replace them with obviously fake names (e.g. "Test Customer A").

- [N1] note: `tokens` Map (:56,127-133) grows without limit for an hour for anyone holding the demo client credentials. Prune expired tokens on every lookup and cap the map at about 1,000 entries.

## Verified clean
- Path tricks: `API_PATH` (:20) runs on the normalised `url.pathname`. I tested `%2e%2e`, `..%2f`, backslashes, `//` inside the path, `@` / `%40`, absolute URLs and `//evil.com/...` in the request line: all are rejected or ignored. The upstream host and prefix are constants (`API_BASE` :11), so neither the request host nor the Host header reaches the fetch.
- Org: exactly one `organization_id` is required and it must equal `843825512` (:391-392). Encoded-key duplicates (`organization%5fid`) are counted and refused. Client headers (e.g. `X-com-zoho-inventory-organizationid`) are never forwarded. Unknown keys get 400 + `filter_refused` (:395-402).
- Non-GET: only the two sandbox POSTs, which require a write tag and never go upstream (:411-426). HEAD, OPTIONS, PUT and DELETE get 405 (:427). A read tag cannot POST.
- Token leakage: no response, error, log line, `/health` or `/demo` HTML contains the upstream access/refresh token or the client secret. Upstream response headers are dropped except content-type. Errors log `err.code ?? err.name` only. Request logs carry pathname only, so `?token=` never reaches PM2 logs (:469,513,523). Bodies are never logged.
- Timing-safe comparison: client id, client secret, both refresh tokens and the page token use SHA-256 + `timingSafeEqual` (:33-34), which also removes the length leak. Bearer lookup is a Map lookup on a 192-bit random token (fine).
- Expiry: demo tokens last 1 h and are checked on every use (:150). The upstream token is refreshed 120 s early, a single refresh runs at a time (`refreshing ??=`), and the cache is dropped on an upstream 401 (:197).
- `/demo` page: everything it prints is `escapeHtml`'d (:452-453). It loads no external script, style or image (no Referer leak). `/demo/advance` needs the token in a header or query, so cross-site form CSRF is not possible, and ids must match the sandbox pattern.
- Portal DB: opened `{ readonly: true, fileMustExist: true }` after an `existsSync` check, with a parameterised query; the path comes only from `.env` (:213-224). It cannot create a DB or write rows. One caveat: on a WAL-mode DB, SQLite may create `-shm`/`-wal` beside it if the folder is writable (not a data write).
- Hydration input: every map lookup uses `Object.hasOwn` + type checks (no prototype pollution). Quantity and rate are checked. Bodies are capped at 1 MB (:17,503-506).
- Git hygiene: `.gitignore` (root) covers `.env`, `.env.*`, `data/`, `*.db` at any depth; `git check-ignore` confirms both `tools/demo-gateway/.env` and `data/maps.json`. `git log --all -- '*data/*' '*.env*' '*.db'` is empty. No token-looking strings appear in the diff. Fixtures hold no prices and no real ids except the documented placeholder and a stand-in `4892105000000999001`.
- Dependencies: only `better-sqlite3` and `dotenv`, both already in the lock. No new dependency.

## Accepted risk (already known and deliberately deferred)
- No gateway daily budget; each app's cap does the budgeting (spec §2.1/§2.6, 4,500 + 2,000 ≤ 7,500). A local process with a demo read token is not held by those caps and could burn up to about 129k calls/day at the 667 ms spacing. Accepted by the spec. S4's per-tag cap would also limit this.
- The allow-list is prefix-wide (`/inventory/v1/*`, spec §2.1), so a demo read token can GET anything the real token's scopes allow. The real control is the scopes the human grants on the Self Client. Recommend the narrowest list (salesorders, items, bundles READ only; not `FullAccess`/`settings`); please confirm when the token is created.
- The ecosystem file + pre-start `.env` checks (§2.7) are not in this diff; they need their own review.

VERDICT: SHIP-WITH-FOLLOWUPS (PASS-WITH-CHANGES): fix S1 and S2 before the real refresh token goes into `.env`. S3–S8 can follow before the warm-up date.
