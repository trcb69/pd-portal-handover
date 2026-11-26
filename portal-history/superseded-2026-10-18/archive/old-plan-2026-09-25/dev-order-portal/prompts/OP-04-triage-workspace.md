# OP-04 — Triage workspace

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** this step's date moved later — the shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-04`):** build 17–25 Nov 2026 (**FORCED**: later start; answer deadline moves to 3 Nov 2026). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

Triage is where an accepted order becomes a job. Three tabs (Incoming, Questions, Enter on behalf),
three actions (Accept, Reject, Ask). Builds directly on OP-03's state machine.

## Files to read first

1. Design spec §7.2.2 (full triage rules), the route table entries for `/api/triage/orders*`.
2. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §4.
3. `/root/Production Dashboard/CLAUDE.md` line ~398 — the seeded manager/coordinator pairs and
   which divisions are missing one (PCU, PCLU, DPU, PPU, CWU as of this brief; re-check against
   current seed data, it may have changed).
4. AC1.4, AC1.5 in spec §13.
5. The code you wrote for OP-03 (`order_events`, `order_status`) — this step writes on top of it,
   never around it.

## Exact scope

- `GET /api/triage/orders` (oldest-first, cancel-pending orders on top).
- `POST /api/triage/orders/:id/accept` (division + manager/coordinator pair; creates the job in the
  same DB transaction; `order_received_at = submitted_at`; `entered_*` copied from the order's
  first line + "(+n more)"), taking `expected_state` for optimistic-concurrency safety.
- `POST /api/triage/orders/:id/reject` (reason code required, public note required).
- `POST /api/triage/orders/:id/ask` (public message; moves order to Questions).
- `POST /api/triage/orders/:id/cancel` (before acceptance, per the cancel-request rules).
- `POST /api/triage/orders` for **Enter on behalf**: receipt time must be in the past and within 60
  days; picks the requester (team copied); `created_via = on_behalf`; audit row written.

## What NOT to touch

- Job-number assignment logic beyond creating the job row (OP-06 owns `POST /api/jobs/:id/job-no`).
- SO linking (OP-05).
- Credit gating (OP-08) — accept must not check credit in this step.
- Company/location requirement (OP-07).

## Pipeline gates to follow

`test-author` → `implementer` → `test-runner` → `code-reviewer`. No `security-auditor` needed
solely for this step (reviewed with the release as a whole in OP-13), but role checks (triage-only
routes) must be server-side and tested here regardless.

## Tests to write first

- AC1.4: two simultaneous accepts on one order → exactly one 200, one 409, exactly one job created.
  Accept while `cancel_pending` → 409.
- AC1.5: reject without a reason code → 400. Every §7.2.0 combination not in the table → 409
  (extend OP-03's transition-matrix test rather than duplicating it).
- Enter on behalf: a future receipt time, and one more than 60 days in the past, both rejected.
  The resulting order is identical to a self-submitted one from the requester's view, except the
  audit trail (test both).
- Accept against a division with no manager/coordinator pair assigned → 400, no job created.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. No migration expected here.

## Definition of done

All the acceptance tests above pass; the triage UI's three tabs and three actions work against
seeded test data.

## Stop and ask conditions

- If the current seed data is missing a manager/coordinator pair for a division you need to test
  against, and no answer has arrived from GM Samitha yet (see `questions.md`), use a clearly-marked
  test fixture pair and flag in your PR description that go-live needs the real assignment — do not
  block the whole step on it, but do not silently invent a permanent pair either.
- Do not guess who "triage" is as a named person — the role and its permission check are what you
  build; the actual person assigned is a go-live question (spec Q7), not a code question.
