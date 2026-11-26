# OP-03 — Order submission and core lifecycle

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** this step's date moved later — the shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-03`):** build 4–16 Nov 2026 (**FORCED**: later start only, content/effort unchanged). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

This is the core of Release 1: order submission and the frozen state machine
(`submitted → questions → accepted/rejected/cancelled`), built with **no credit gate and no
company/location requirement yet** — those are OP-08 and OP-07. This step is fully unblocked by
open questions; start it as soon as OP-02 lands.

## Files to read first

1. Design spec §6.3 (`orders`, `order_lines`, `order_events`, `order_messages`), §6.4
   (`order_state`/`order_status`), §7.2.0 (state table), §7.2.1 ("Updates are not edits").
2. The Release-1 route table in
   `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §3 and the design spec's own API table.
3. `server/routes/index.js`, and any existing route file for the auth/session pattern to follow
   (e.g. `server/routes/auth.js`, `server/auth/middleware.js`).
4. AC1.1, AC1.3, AC1.7 in spec §13.

## Exact scope

- `POST /api/orders` (customer, required date, type, division hint, items, attachments; server
  sets `submitted_at`, ignores any client-sent time).
- `GET /api/orders/mine`, `GET /api/orders/:id` (thread view).
- `POST /api/orders/:id/messages` (public/internal).
- `POST /api/orders/:id/cancel-request`, `POST /api/orders/:id/decline-cancel`.
- DB triggers that abort UPDATE/DELETE on `orders`, `order_lines`, `order_events`,
  `order_messages` (the spec's **(A)** append-only tables).
- Server-side `order_status` derivation function per spec §6.4, unit-tested for every branch.

## What NOT to touch

- No credit gate of any kind (OP-08).
- No `company`/`location` requirement on submission yet (OP-07) — those columns may exist from
  OP-02 but are not required here.
- No triage actions (`accept`/`reject`/`ask`) — those are OP-04.
- No attachment upload logic beyond what's needed to accept a multipart request shape — full
  validation/magic-byte checking is OP-10.

## Pipeline gates to follow

`test-author` (transition-matrix tests, AC1.1/1.3/1.7) → `implementer` → `test-runner` →
`code-reviewer`. `security-auditor` is not required for this step alone (no auth/upload surface
change beyond existing session auth) but will review the release as a whole in OP-13.

## Tests to write first

- Every §7.2.0 transition, including every combination **not** in the table (expect 409) —
  exhaustive, not spot-checked.
- AC1.1: a client-sent `submitted_at` is ignored.
- AC1.3: an UPDATE/DELETE attempt against any append-only table fails even if a route tried it
  (test the trigger directly, not just through the API).
- AC1.7: write this test now, mark it pending/skip until OP-04's job creation exists (job creation
  is what lets a job go "back to the coordinator").

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. No new migration expected in this step (schema comes from
OP-02); if you find you need one, stop — that likely belongs in OP-02's delta instead.

## Definition of done

- The four routes work against a test DB with the append-only triggers active.
- The transition-matrix test is exhaustive and green.
- `order_status` has a unit test per branch of §6.4.

## Stop and ask conditions

- None of this step's own scope is blocked by an open question. If you hit a question not covered
  above, stop — it likely belongs to a later step (OP-04 through OP-14); check
  `02-process-steps.md` before assuming it's yours to answer.
