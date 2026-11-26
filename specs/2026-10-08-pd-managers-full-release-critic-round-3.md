# plan-critic, round 3 (focused check), on PD managers' full release, Rev 3.1 (9 Oct 2026)

The critic's tools were read-only, so the coordinator saved this from its hand-back, condensed.

## Verdict: **APPROVE-WITH-CHANGES**. Nothing blocks.

The four items that were not mechanical edits are sound:
- **N1 strip union, ordering and `tickable`.** AC103 is falsifiable against a current-unit-only build, an ordering by id, and a `tickable` that ignores the tick unit.
- **N2 occlusion.** Hit testing works through the closed shadow root, and the cost is negligible.
- **N7 header.** The idle check at `sessions.js:23` still runs on every request. A client can only shorten its own session.
- **N11 org-path guard and `other_lines`.**

## Required small changes (before test-author writes the AC104/AC106 E-tests)
- **C1.** The hidden-chip sample point must come from the Range and the layout math, not from `getBoundingClientRect()` of a `display:none` chip, which returns 0×0. State this in §10.3 step 5b.
- **C2.** Send observer-driven `summaries` re-collects (from Zoho re-rendering by itself) with `background:true`, just like the 15 s timer. Only route changes and panel actions count as activity. Add an AC106 E-bullet: a fake list re-render with no user input sends `X-PD-Background: 1`.
- **C3.** Re-run the exact-org-path guard on every route-watch tick. If it fails, clear the overlay and stop the observers and timers. Apply the same exact-path rule to the worker's sender check (:918).

## Notes
- **N1.** Run all `elementsFromPoint` reads before any `display` writes.
- **N2.** In AC104, give at least one fake overlay a z-index below the host's 10, so that the click assertion is not vacuous.
- **N3.** Add the partial-overlap residual to §18. Optionally add `click` (capture) to the triggers.
- **N4.** §10.5: `other_lines` are rendered without the trail or seen calls, because those endpoints return 404 for them.
- **N5.** The R0 renumbering note must also update the `schema_migrations` assertion at `test/migrations.test.js:206`.
- **N6.** Compute the renumbered test files (highest+1 and highest+2) at runtime from the copied directory, not hard-coded.
- **Minor.** `division_doc_steps` has no `active` column. Write "rows whose `doc_steps.active=1`" and use the same filter for `tickable` and `manual_missing`.

## Unverified
- Whether Zoho re-renders the SO list by itself (this decides how much C2 matters).
- Whether Zoho switches org with `pushState` (C3).
- Zoho's real z-index values (V10).
- Whether `req.viaExtension` is set before `requireOrigin`'s GET early return.
