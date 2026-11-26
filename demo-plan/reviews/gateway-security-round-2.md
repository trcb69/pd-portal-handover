# Demo gateway: security audit, round 2 (25 Oct 2026)

Branch `feature/demo-gateway`, worktree `/root/dev/order-portal-gateway`, diff `975e016..HEAD` (11c1ecc, cd805cc, 443bf48, 38a186a). Round 1: `gateway-security.md` (S1–S8, N1). Spec Rev 4.8 §2 and §20.
This was a read-only review. I sent nothing to Zoho. The gateway test suite passed, 101/101 (`node --test tools/demo-gateway/test/*.test.js`). I also ran my own probe with the real `createGateway` on an ephemeral loopback port, using a fake `fetch` that records every URL. The probe and its data lived in a scratch folder, and I made no repo changes.
Line numbers below refer to `tools/demo-gateway/server/create-gateway.js` unless I name another file.

## Scope and trust boundary
The boundary has not changed since round 1. The gateway listens on 127.0.0.1 only (:698, :709). Callers are local processes and viewers who come in through an SSH tunnel.
`GET /health` is the only route that needs no credentials, and every route now passes the Host check first (:635). The real secrets are used in exactly one place, the token POST (:210-218). The upstream access token is used only in the GET to `www.zohoapis.com/inventory/v1` (:276-278).

## Round-1 findings: status

| id | status | evidence |
|---|---|---|
| S1 query smuggling | **FIXED** | `checkFilters` :531-560 rebuilds the query from validated pairs with `organization_id` fixed (:540), and `forward` sends only that string (:276). `url.search` is no longer read anywhere on the upstream path. |
| S2 redirects / timeout | **FIXED** | Both fetches use `redirect: 'error'` and `AbortSignal.timeout(20 s)`: the token POST at :216-217 and the GET at :277. The signal also covers `res.json()` and `up.text()`. My probe saw only `redirect=error` with a signal on every upstream call. |
| S3 secret strength / start checks | **FIXED, with two gaps** | `startup-checks.js:61-79` (required values, `.env` 0600, DEMO_* ≥ 24 characters, pairwise different, none equal to a ZOHO_* value, names only in messages), called from `main.js:22-26`. Gaps: (a) the minimum is 24 characters, not the 32 I suggested, and nothing checks that the value is random (`aaaa…` passes); (b) the 20/min token limit is global and counts failed attempts. See R2. |
| S4 fairness | **FIXED** | One queue per token type, served in turn (:71, :235-265). A lane is admitted past the 10 s cap while it is shorter than the other lane, which bounds the queue at about 2 × the cap. Requests from clients that have disconnected are skipped before they take a slot (:249) and before the fetch (:275). The token is fetched before the slot is taken (:272-273). |
| S5 refresh back-off | **FIXED, with a new hole** | After a refresh failure the gateway waits 60 s (`refreshBlockedUntil`, :206, :225) and logs only the status or error name (:226). New hole: an upstream **401** still drops the cached token (:285), so each 401 forces a fresh refresh. See R1. |
| S6 headers + Host | **FIXED** | `/demo*` sends `no-store`, `no-referrer`, `DENY` and a CSP with `frame-ancestors 'none'` (:629-634). The Host check runs before every route, including `/health` and the token route (:635). Probe: `evil.com:<port>`, `127.0.0.1` with no port, `127.0.0.1:<port>.evil.com` and `LOCALHOST:<port>` all get 400. Only `127.0.0.1:<port>` and `localhost:<port>` get through. A bad Host can reach no route. The body (≤ 1 MB) is read before the Host check (:685), which is harmless. |
| S7 file modes | **FIXED** | Data folder 0700 (:120), temp files 0600 and then renamed (:101), `build-maps.mjs:56-58` writes 0700/0600 plus a chmod, and `.env` is refused unless it is 0600 (`startup-checks.js:65`, `main.js:22`). Observed in the dev worktree: `data/` drwx------, `maps.json` -rw-------. |
| S8 fixture names | **FIXED in HEAD** | `test/fixtures/maps.fixture.json` now uses "Test Customer A/B/C" and "Test Hotel One". The real brand names are still in local history (bdcb1b4). There is no remote yet, so see N-c. |
| N1 token map | **FIXED** | Expired tokens are pruned on each issue (:176). Growth is now bounded by the rate limit (≤ 1,200 tokens/h). |

## S1 adversarial probe (real gateway, fake upstream recording the URL)
Each of these got **400 with no upstream call**:
- `page=1;organization_id=2`, `page=1%00`, `page=1%2526organization_id%253D2`, repeated `page`
- Arabic-Indic `%D9%A1` and fullwidth `%EF%BC%91` digits in `page` (`\d` without the `u` flag is ASCII only)
- `per_page=99999999` and `per_page=201`
- `last_modified_time` as a bare date, month 13, hour 99, or with a trailing `%0A` (JS `$` does not match before a newline without `m`)
- `Organization_id`, `ORGANIZATION_ID`, `0843825512`, `843825512%00`, `organization_id%00`, a duplicate `organization%5fid`, an empty second `organization_id`, `sort_column=name`, `sort_order=D%20`, `=x`, a bare `page`

Each of these got 200, and the upstream query was rebuilt as shown:
- `last_modified_time=…+0530`, `…%2B0530` and `…-0530` all go out as `…T00%3A00%3A00%2B0530` (or `-0530`)
- `organization%5Fid=843825512` goes out as `organization_id=843825512` (canonical)
- `&&&` and `#frag&organization_id=2` both go out as `organization_id=843825512` only (the fragment never reaches the server)

Paths: `/inventory/v1/items/1/../../settings` is normalised to `settings` and forwarded. That stays inside the accepted prefix-wide risk. `%2e%2e/crm` gets 404. A detail path takes `organization_id` only, so `salesorders/123?…&page=1` gets 400.
**Conclusion: the raw query string never reaches Zoho. Only `[A-Za-z0-9_-]` path segments and a query the gateway built itself do.**

## New findings
- [R1] SEVERITY: low (fix before the warm-up, not a blocker for the key)
  - where: create-gateway.js:285 (`if (up.status === 401) upstream = null;`) together with :204-231
  - what an attacker does: anyone holding a demo read token (or the dashboard by mistake) sends GETs to an endpoint that the READ-scoped key is not allowed to read, for example `settings/...` or `invoices`. Zoho answers 401 (code 57). Each 401 throws away a valid upstream token, so the next request makes a new refresh POST. The probe confirmed it: 5 consecutive 401s gave 4 refresh POSTs. The 60 s back-off starts only after a refresh *fails*. Zoho limits how many access tokens one refresh token may mint in a short window, so this churn can make Zoho refuse refreshes, and then both apps stop reading. Nothing leaks.
  - impact: the demo can lose its reads, and the SPS account sees noisy auth traffic.
  - fix: drop the cached token on 401 only when it is old (for example, issued more than 60 s ago). Alternatively, allow at most one refresh per 60 s unless the token has actually expired. Add a test: 10 upstream 401s → ≤ 1 refresh POST.
- [R2] SEVERITY: low
  - where: create-gateway.js:642-645 (`tokenHits` is one global window and counts attempts before they are checked)
  - what an attacker does: any local process, with no credentials, sends 20 junk POSTs a minute to `/oauth/v2/token`. The probe confirmed it: after 25 bad POSTs, a **valid** write-token request got 429. To the question asked: **yes**, one app (or any local process) can lock the other app out of new tokens. Tokens already issued keep working for up to 1 h, so the effect appears at an app restart or when its hourly token runs out.
  - impact: both apps fail to authenticate while the flood lasts.
  - fix: count only *failed* attempts against the 20/min limit, and let valid credentials through, with a separate generous cap such as 60/min. Alternatively, keep a separate bucket per demo refresh token plus one for failures.
- [R3] note (works as coded, but affects how the demo is run): the Host check needs the browser's port to be the gateway's port. A viewer who tunnels `-L 9000:127.0.0.1:4850` sends `Host: localhost:9000` and gets 400 on `/demo`. The README tells viewers to tunnel as `-L 4850:127.0.0.1:4850`. Do **not** relax the check to fix this.

## Nits
- N-a `last_modified_time=2026-02-31T…` passes, because `Date.parse` rolls it over, and is forwarded. It is harmless: the characters are fixed, so nothing can be smuggled. It may give a Zoho 400.
- N-b `mkdirSync(..., {mode: 0o700})` (:120, build-maps:56) does not tighten a folder that already exists, and the mode of `maps.json` is not checked at start. In the pinned `/root/demo/...` checkout, a hand-copied `maps.json` could be 0644. Check its mode at start the same way `.env` is checked, or `chmod` it.
- N-c Commit bdcb1b4 still holds the old fixture with real brand names. There is no remote yet. Before the first push, rewrite that commit or accept this.
- N-d The ecosystem file and the pre-start `.env` checks for the two apps (§2.7) are still not in this diff. This is carried from round 1 and needs its own review.
- N-e `DEMO_*` minimum is 24 characters. Generate the values with `openssl rand -hex 24` (48 characters). The check cannot prove a value is random.

## Verified clean (new code in this diff)
- Materials and bundles (11c1ecc, cd805cc): lookups use `Object.hasOwn` + type checks (:329-337). `mirrorRow` interpolates only an internal column constant (:306), and `id` is bound. Bundle rows are built from hydrated order data, never from client keys. `/demo/advance` steps come from an enum, and ids must match the sandbox pattern (:660-661). Sandbox state goes through the same atomic 0600 write.
- No secret is logged or returned. New log events carry only a status or an error code/name (:226, :282, :275). No response echoes upstream headers except content-type.
- `startup-checks.js` names variables, never values. `main.js` exits before binding if any check fails.
- No new dependency. The tests contain only obvious placeholder secrets.

## Accepted risk (already known and deliberately deferred)
- The allow-list covers the whole `/inventory/v1/*` prefix. The real control is the set of scopes on the Self Client. Create the key with the narrowest read scopes (salesorders, items, bundles, and whatever else the two apps read; **not** `FullAccess` or `settings`).
- The gateway keeps no daily budget of its own (spec §2.1/§2.6).
- `?token=` on `/demo` stays in viewers' browser history. Rotate `DEMO_PAGE_TOKEN` after the demo.

## Is it safe to put the real READ refresh token into `.env` now?
**Yes.** S1 and S2, the two gates named in spec §20, are fixed and verified. R1 and R2 affect availability only. They cannot leak the token or widen what it can reach. Conditions:
1. `chmod 0600 tools/demo-gateway/.env` (the gateway refuses to start otherwise).
2. The Self Client uses read scopes only, as narrow as possible.
3. The human types the value in, not Claude.
4. Fix R1 and R2 before the warm-up on Fri 30 Oct.

VERDICT: SHIP-WITH-FOLLOWUPS (PASS-WITH-CHANGES). S1–S8 and N1 are fixed. R1 and R2 are new low findings, to fix before the warm-up.
