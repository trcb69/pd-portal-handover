# Gateway review round 3 (code + security follow-ups): demo gateway (`feature/demo-gateway`)

Reviewed 25 Oct 2026. Worktree `/root/dev/order-portal-gateway`, `git diff 38a186a..HEAD` (e59ea1a, 975a00f). Spec Rev 4.9 §21.
I re-ran `npm test` myself: **276/276 pass**. I did not open `.env`. The worktree is clean apart from the untracked `.claude/`.

## Verdict
**APPROVE-WITH-NITS**

## Critical (must fix before merge)
None.

## Warnings (fix now or file a ticket)
- [W5 from round 1, still open as expected] `test/fixtures/list-filters.json` `_note`: the projects/contacts filters are still assumed,
  and `SORT_COLUMNS` (`create-gateway.js:19`) does not allow sorting by name. Re-check this when S1-demo lands.

## Nits (optional)
- [N1] `create-gateway.js:150`: `Number(String(o.salesorder_number).slice(-4))` misreads any number of 10,000 or more
  (10000 → 0, 123456 → 3456). It also reads an old-format `DEMO-JOBORDER-261025-001` as −1. Numbers are **not reused** even so,
  because the counter only goes up, is persisted before the orders (`:160`, `:355`) and is never reset. At 10,000 the number simply
  gets longer: `DEMO-26102510000`. That string is still unique, the real `soKey` still returns it whole, and it still matches
  `SO_NUMBER` (`jobs.js:19`, ≤ 40 characters). The only effect is a weaker "counter behind sandbox" guard (`:153-155`) past 9,999
  orders. The demo will never get near that. Fix: parse with `/^DEMO-\d{6}(\d+)$/` and use group 1 (or `0` if it does not match).
- [N2] Spec §2.3 (`2026-10-24-joint-demo-v0-1-rev4-demo-first.md:164`) still names `DEMO-JOBORDER-<yymmdd>-<nnn>`. §21 supersedes
  it, but the stale line is a trap. Amend it inline to say "see §21". Also note that the 4-digit part is a **global** counter, not a
  daily one: the first order on 26 Oct after five on 25 Oct is `DEMO-2610260006`. That is correct under the never-reset rule, but
  the brief called it a "daily sequence".
- [N3] `create-gateway.js:654-655`: read and write tokens share one 60/min valid bucket. An app with valid credentials that loops on
  refresh could use up the bucket and lock the other app out of new tokens. Both apps are trusted local callers, so the risk is
  low. Fix: keep one valid bucket per kind (`validTokenHits.read` / `.write`).
- [N4] `test/gateway-security.test.js`: nothing tests the reverse direction, that valid requests do not eat into the failed
  allowance. Optional test: 60 valid requests, then a junk request → 400, not 429.

## Round-2 findings

| # | Status | Evidence |
|---|---|---|
| Code C1 order-number join | **FIXED** | `:402` → `DEMO-<yymmdd><nnnn>`. I imported the dashboard's **real** `soKey` (`/root/dev/production-dashboard-v01/shared/text.js:7-11`, HEAD 18f2a56) into a scratch probe and ran it on a live harness gateway: order `DEMO-2610250001`, bundle ref `DEMO-2610250001 - F`, `soKey(ref) === number` → **true**, `soKey(number) === number`. Other consumers still hold: DEMO chip `startsWith('DEMO-')` (`MyJobs.tsx:149`); `SO_NUMBER` route regex (`jobs.js:19`) matches; `upsert.js:137-138` and `zoho-queue.js` join through `soKey`; `zoho-sync.js` uses the number as an opaque key (`:349`). No sandbox file exists yet (`tools/demo-gateway/data/` holds only `maps.json`; there is no `/root/demo`), so no old-format orders need migrating. The contract test (`gateway-bundles.test.js:11-22, 59-60`) is a verbatim copy with a `file:line` pointer, and it would fail on the old format. |
| Sec R1 401 churn | **FIXED** | `:226` stamps `issuedAt`. `:289` drops the cached token on a 401 only when it is ≥ 60 s old. `forward` never retries, so nothing can loop. Concurrent in-flight 401s that carry an old token check the *current* `upstream`, so a fresh token is never thrown away. Refresh failure keeps its own 60 s back-off (`:229`). Accepted trade-off: a token revoked within 60 s of being issued gives 401s for up to 60 s. The test (`gateway-upstream-hardening.test.js:203`) gets 5 × 401 → 1 POST, then 2 POSTs after 61 s. The old code would have given 5. |
| Sec R2 global token limit | **FIXED** | `:647-657`. Two buckets. `tokenKind` (timing-safe compares) decides valid or failed **before** any limit is checked, so junk cannot touch the valid bucket. Guessing stays at 20/min. Token-map growth is bounded (≤ 60/min, pruned on expiry, `:180`). |
| S3 test rewrite | **Fair** | The old test checked "20 valid then 429, guesses too". It is replaced by: 20 failed → 400, then 429, then reset after 61 s (`gateway-security.test.js:67`); 25 junk then a valid request → 200 (`:81`); 60 valid → 429, then reset (`:93`). Together these cover both buckets and the window. Only the reverse direction is untested (N4). |
| Code N1 lane comment | FIXED | `:237` |
| Code N2 / Sec R3 tunnel port | FIXED (README) | `README.md:12`. The Host check is not relaxed. |
| /demo step labels | **FIXED** | `:31-32`, `:615`. The labels match spec §21 and the dashboard's `DEMO_LABEL` (`web/src/lib/jobs.ts:20`). The `data-step` API values are unchanged. Nothing outside the gateway's own tests clicks these buttons by their text. The test (`gateway-demo.test.js:45`) checks the exact `>label</button>`. |

## What I verified and found clean
- Correctness: C1 checked end to end against the real consumer function, not a copy. No findings beyond N1/N2.
- Data integrity: numbering stays monotonic across restarts (counter written first, never reset, `counter.json` required when orders exist, `:146`). No sandbox data needs migrating.
- Security: R1/R2 introduce no new path to a secret. Log fields are unchanged. The token route still answers only 200/400/405/429.
- Failure handling: no unawaited promise or swallowed error added.
- Blast radius: the dashboard needs no change. `soKey` was not widened, as §21 requires.
- Tests: every new or changed test would fail on the round-2 code.
