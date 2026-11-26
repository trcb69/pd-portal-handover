# OP-15 — Key-customer call-off order type (wiring only — do not build the feature)

**Changed 25 Sep 2026:** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates:** not scheduled (`dev/01b-dated-schedule.md` row `PD-21 / OP-15`, "NOT SCHEDULED") — waits on the safety-stock/MTS policy sign-off and the paused key-customer stock-system project, both outside this document's control.

## Context

**This is a confirmation step, not a feature-build step.** The 2027 production plan proposes a
future "against buffer stock" order type; it is not agreed, and the stock system it depends on is a
paused, separately-scoped project. Do not build any buffer-stock logic here.

## Files to read first

1. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §11.
2. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/11-production-plan-2027.md`
   §3–4 (context only — you are not implementing this plan).
3. Your OP-01/OP-02 work — confirm `order_type` is a seeded lookup table, not a CHECK enum.

## Exact scope

- Confirm, in writing (a short note added to the spec or a comment near the `order_type` lookup
  table), that adding a future `buffer_stock` (or similarly named) value is already just a seeded
  INSERT once the policy is agreed — no migration needed beyond what OP-02 already built.
- That's it. No route, no UI, no draw-down logic.

## What NOT to touch

- Do not add a `buffer_stock` (or any new) value to the `order_type` lookup table.
- Do not build any stock-buffer draw-down logic, safety-stock calculation, or link to the paused
  stock-system project.
- Do not touch anything in the paused stock-system project's own files.

## Pipeline gates to follow

None beyond a normal `code-reviewer` glance at the confirmation note — there is no feature code to
gate.

## Tests to write first

None — nothing is built. If you want to leave a marker, a single test asserting `order_type` is
backed by a table (not a CHECK constraint) is sufficient and can live alongside OP-02's own tests.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. No migration in this step.

## Definition of done

The confirmation note exists; no feature code was written.

## Stop and ask conditions

- If you find yourself about to write a route, a UI element, or any draw-down logic for this order
  type — stop. That is out of scope until GM Samitha signs off the safety-stock policy and the COO
  confirms the paused stock-system project can resume (see `questions.md`). This step only exists
  to confirm the door is left open, not to walk through it.
