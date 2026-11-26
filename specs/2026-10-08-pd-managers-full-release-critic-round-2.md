# plan-critic, round 2, on PD managers' full release, Rev 3 (8 Oct 2026)

The critic's tools were read-only, so the coordinator saved this report from its hand-back. The verdict and the findings are as returned, condensed.

## Verdict: **APPROVE-WITH-CHANGES**
- C1 and C2 are fixed in the spec body. The critic checked the C1 rule against routes.csv rows 19, 16, 64, 8, 417, 645 and 681. For C2, the stream is gone; every refresh is a runtime message that wakes the worker, and AC24 waits through an idle worker.
- Round-1 N1–N14 are answered in the body, with the code claims re-verified.
- No blocking findings remain. N1–N4 below are required in Rev 3.1 before test-author writes the affected ACs. N5–N12 are recommended.

## Required in Rev 3.1
- **N1. Which unit's step list a job uses is undefined now that start ≠ home.** This affects the strip, `manual_missing` and the preview `missing` (§9.1, §9.4, AC15).
  - Example: a `PackPro > RWU` item starts at PACKPRO, which has Artwork, but its home RWU does not.
  - Fix: write the rule as "the union of the `division_doc_steps` of pathUnits ∪ {current}" or as "current_unit's". Add an AC on row 19, at PACKPRO and again after the job is sent to CPU. Say what the preview DTO's `division` now holds.
- **N2. Overlay chips paint over Zoho's dropdowns, modals and sticky header, and take the clicks.**
  - Fix: give the host `pointer-events:none` with only the chips set to `auto`, and a modest z-index. Hide a chip unless `elementFromPoint` at the row's number rectangle (host excluded) falls inside that row.
  - Add an E-AC: with a dropdown, a modal, or the sticky header over rows, no chip shows and the click reaches Zoho.
- **N3. The startup contiguity check breaks R0's AC0.15 tests.** These are `test/migrations.test.js:87-97` and `:112-133`, which use `900-extra.sql`, plus the note at `helpers/db.js:8`.
  - Fix (recommended, option a): `runMigrations` checks uniqueness only. Contiguity is checked by the `npm test` lint over the real migrations directory.
- **N4. Bulk-day lanes.**
  - A new SO with no mirror row → lane 1.
  - Line-only edits (tag or quantity) do not change `sig`, so on a bulk day they can lag up to the drain time (about 2 h 13 m). State this in owner note N-1, and add an AC55 case for a new SO.

## Recommended
- **N5. The 10-minute overlap re-reads about 11 minutes of changes every cycle.** A bulk day costs about 150–300 extra list calls; the total, about 6,800, still fits under 7,500.
  - Correct the "+60" sentence and the §9.5 table.
  - Add V8b and org-check calls to `listReserve`.
  - AC54 becomes "every cycle completes its delta (all pages) and the bundles delta".
- **N6. `home_at_first_move` when no observation exists.** Use the earliest observation, or show no chip. Define `raw_tag` for a line with two Division tags (sort and join them).
- **N7. 15 s polling turns off the 12 h idle timeout** (`sessions.js:28-30`). Mark background refreshes (for example `X-PD-Background: 1`) so they do not refresh `last_seen_at`, or hand this to the security-auditor as a residual risk. An optional ETag/304 would cut load.
- **N8. AC8 conflicts with R0's Origin rule** (`middleware.js:21`: GETs pass). Scope it as: non-GET with a foreign or missing Origin → 403; a bearer without an allow-listed extension Origin → 401.
- **N9. `chrome.sidePanel.open()` loses the user gesture after any `await`.** The worker must call `open({windowId})` synchronously. Add an S-check for this next to V14.
- **N10. AC102's synthetic home never occurs in the real data.** Add real row `routes.csv:645` (MOBA-Cup > MOBA, home PCU = R[0]).
- **N11. Remaining label ACs.** AC44, AC45, AC48 and AC52 need inputs and results. AC85 becomes a sign-off gate. AC71 lists the non-SPS URLs (SH org 843061977, `/app#/`).
- **N12. The estimate is optimistic.** The add-on is more like 30–35 h than 20 h, and the test-author time is light. Plan the combined path at about 340–380 h. Non-blocking.

## Unverified assumptions
- CDP `ServiceWorker.stopAllWorkers` on extension workers in Playwright.
- Playwright intercepting `launchWebAuthFlow`.
- Whether a content-script message carries the user gesture into `sidePanel.open` (V14).
- Zoho's per-minute limit (about 100/min is commonly documented; the 02:00 cycle is about 78). Record it in V13.
- V1, V7 and V15 are unchanged.

## Simpler alternative
Nothing materially smaller. Dropping the list chips (panel only) saves about 8–10 h but removes the owner's "see it on Zoho's list". That is the owner's call.
