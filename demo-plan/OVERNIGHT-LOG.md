# Overnight log — joint demo v0.1 build (21→22 Oct 2026)

The owner is asleep and asked for everything up to the point that needs the SPS read key. Decisions taken
without him are listed here with the reason; each can be reversed in the morning.

## Decisions parked for the owner (taken provisionally)

| # | Question | Provisional choice | Why | Reverse by |
|---|---|---|---|---|
| N1 | P-AC86: a sync module whose run fails with `too_many_bad_rows` — stop retrying for the rest of the day (preview spec line 371) or keep retrying and log once? | **Keep retrying; log the error once per Colombo day** (recorded as an override in the joint demo spec §12b; the preview spec file itself is not in this branch and was not edited) | At a 1–2 minute cadence a day-long freeze of the sales-order delta would leave the screens a day stale. **Cost:** each retry re-reads every page changed since the last ok run, so on a bad day list calls grow and squeeze detail fetches under the 4,500 cap | Tell me "freeze for the day" |
| N2 | P-AC97e: retries in cycle 6 with 200 other orders queued | **Change the test fixture** to match spec line 460 ("a retry can wait", retries go last) | The spec text is explicit; reserving slots adds code | Tell me "reserve retry slots" |
| N3 | The 15 "Sign in with Zoho / add-on" tests (`test/release-auth.test.js`) | **Skipped with a written reason** (out of v0.1; the website sign-in is migration 008, v0.3) | Not built and replaced by the approved plan | — |
| N4 | History fetches run only 21:00–06:00 (`zoho-sync.js:334`) vs the FR non-goal "no night mode" (FR line 1520) | **Left as is for v0.1, noted** | No failing test; changing it alters the call budget; decide with the live numbers | Tell me to change it |

## Progress
- 21 Oct 02:3x — joint demo spec Rev 3.1 APPROVED; PDF final (`out/Joint-Demo-Plan-2026-10-21.pdf`).
- Dashboard clean copy: `/root/dev/production-dashboard-v01` (branch `feature/joint-demo-v0.1` from `aa4837b`); the main clone's uncommitted Sign in with Zoho work untouched.
- Root cause of the 31 failing tests: `/root/.claude/jobs/61c1b69c/tmp/rcd/REPORT.md` — 15 not-built sign-in, 12 stale/wrong/flaky tests, 3 real gaps (P-AC46 ×2 import guard, P-AC86), 1 spec contradiction (P-AC97e).
- SPS Self Client created under itexe@ (21 Oct, empty, no code generated). Generating the code and storing the secret was blocked for Claude ("credential leakage") — the owner does it in the morning.
- Portal: `/root/dev/order-portal` **already existed** (branch `feature/s0-foundation`, uncommitted tests dated 18 Oct from an earlier session). test-author adopted them, fixed 3 test bugs, pinned dependency versions to the dashboard's lock, added 4 files, first commit `04fecd8`: 120 tests, 114 failing for the right reason. Spec points the tests pinned (acting person in the login body, AC6 at login, AC4 per user+IP, AC49 history rule, admin paths) are listed in that commit's test headers.
- Dashboard: implementer fixing the failing-test slice in `production-dashboard-v01` (decisions N1–N3).
- Portal S0 **built: 120/120 tests, three clean runs** (`a5e00ff`, `5f1f1f2`, `c18b382` on `feature/s0-foundation`; no test edited, no dependency added). 17 interpretation points listed in the implementer's report (login order: IP check → acting person → session; stub routes 501; history allowance; APP_ORIGIN placeholder `https://orders.standard-holdings.lk` until the hostname is chosen). Not yet: write/approval rate limits, last-admin guard (S1). Code review + security audit running.
- Portal S0 security audit: **PASS-WITH-CHANGES** (S1–S8; `reviews/portal-S0-security.md`). Before the v0.1 deploy: S2 (office-IP rule), S5 (no raw usernames in audit), S6 (refuse bridge listener when tunnel-only).
- Dashboard test slice: `npm test` **0 failures twice** (374 pass, 43 skipped = 15 sign-in + 28 older, 9 todo), commits `c0392e2`…`30ce763`. e2e: 1 failure `admin.spec.js:81` (working-days alert), untouched path; baseline check in the code review. 234 stale `/tmp/pdrun-*` folders deleted.
- UI: 5 sample directions published on the canvas and as `out/UI-Directions-2026-10-21.pdf`.
- UI (earlier): 5 sample directions being drawn by a Fable agent on canvas https://claude.ai/artifact/BXwgGYJ4exMTpEBCMMNqX3 (private).
