# OP-14 — End-to-end smoke test and go-live readiness

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** this step's date moved later — the shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-14`):** build 20–25 Jan 2027 (**FORCED**: later start, propagated from OP-01's ~3-week shift minus OP-11's 9-wd removal); internal IT test 26–28 Jan 2027; UAT 29 Jan – 12 Feb 2027 (2 weeks — Ishan, Umanda, Hazeem, Samitha — longer than a typical UAT window because this release includes the automated credit check, money); **full release 15 Feb 2027, Release 1 + 1b live for everyone** (2 working days after the original 11 Feb 2027 target — see `01b-dated-schedule.md` §4).

## Context

This is the last build step of Release 1's core scope (OP-01–OP-13 must all be done). It proves
the whole chain works together and produces the go-live checklist for `release-captain`.

## Files to read first

1. Design spec §13 AC1.27, §8.2/AC1.28.
2. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §14, §15.
3. `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/order-portal/02-process-steps.md`
   — every step's "questions that must be answered first" tagged "blocks go-live" (not "blocks the
   build") is what this step's checklist collects.
4. Existing Playwright config: `test/e2e/playwright.config.js`.

## Exact scope

- The AC1.27 Playwright test: requester submits → triage accepts → coordinator sets job no, links
  pending SO, attaches docs, sends to production → import+sweep resolve the SO → requester sees "In
  production," live via SSE.
- Add this test to CI (not just a local run).
- Apply the AC1.28 performance discipline (keyset-paged chunks of ≤500, no single sync DB call
  blocking the event loop over 100ms) to any new order-list endpoint added in OP-03–OP-12.
- Confirm English-only (or whatever OP-01's delta decided) and desk-first layout (no phone-first
  redesign) are actually reflected in the built UI.
- Produce a go-live checklist naming every "blocks go-live" item collected from OP-01–OP-13, each
  with an owner.

## What NOT to touch

- No new feature work — this step tests and checks readiness of what OP-01–OP-13 already built.

## Pipeline gates to follow

`test-author` (the AC1.27 test itself) → `test-runner` → `code-reviewer` for the checklist/report
artifact. `release-captain` is the next gate after this step, run by the human when ready to
deploy — this step prepares for it, does not run it.

## Tests to write first

- The AC1.27 flow, as a single Playwright test exercising every step in sequence.
- A measured (not assumed) timing check on any new order-list endpoint against the AC1.28
  discipline.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. This step explicitly does not deploy — it prepares the
readiness checklist the human uses when they choose to run `shdeploy`.

## Definition of done

AC1.27 passes in CI; the go-live checklist is written and complete (every open "blocks go-live"
item has a named owner, even if the resolution is "pending").

## Stop and ask conditions

- If AC1.27 fails because an earlier step (OP-03–OP-13) has a gap, do not patch around it inside
  this step — go back and fix the actual step, then re-run this one. This step is a checkpoint, not
  a place to paper over an earlier defect.
