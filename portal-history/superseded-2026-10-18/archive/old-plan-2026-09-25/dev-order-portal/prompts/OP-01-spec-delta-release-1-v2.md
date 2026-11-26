# OP-01 — Spec delta "Release 1 v2" (non-credit, **non-MFA**) + plan-critic pass

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** **MFA is removed from this
delta's scope** (item 5 below) — it moves to the December dashboard track's own spec delta
(`PD-02D`) and migration (`PD-03D`), since it's a "going public" gate needed for the December
managers-only release, not portal-specific content. Dates below also move ~3 weeks later.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published
dated master schedule (below); updated the OP-08 cross-reference below — its credit-limit
data-source question is now DECIDED (Zoho Inventory), so OP-08 has two open business questions, not
three.

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-01`):** build 22–23 Oct 2026 (**FORCED, 25 Sep 2026 later the same day**: ~3 weeks later than originally scoped — the shared developer works the December dashboard track first, `01b-dated-schedule.md` §0.5). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

You are extending the production-dashboard app's frozen design spec, not writing code yet. This is
`BUILD-ORDER-2026-09-20.md` row 2. The spec at
`/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` (Rev 7.3) is
approved and frozen for schema 001–004; Release 1 (the order portal) needs several decisions folded
into it before any migration or route is written. The credit check is **explicitly out of scope
here** — it has its own step (OP-08) because it has two unresolved business questions that would
otherwise block everything else (a third, where the credit limit lives, was DECIDED 25 Sep 2026:
Zoho Inventory, no Books access needed).

## Files to read first

1. `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` — read fully,
   especially §6.1 (migration rules), §6.3 (`orders` table + append-only tables), §7.2.0 (state
   machine), §13 (Release 1 ACs), Q2/Q4/Q7–Q10 (open questions list near the end).
2. `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/order-portal/02-process-steps.md`,
   step OP-01, for exactly what this delta must cover.
3. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §5, §6, §9, §11 (background for why each item is needed).
4. `/root/Production Dashboard/BUILD-ORDER-2026-09-20.md` row 2 and §6 (the notifications-table
   decision).
5. `/root/Production Dashboard/LATER.md` lines for L31 (items D6, D7 — lookup-table conversion
   requirements).

## Exact scope

Write a spec delta (as an amendment to the design-spec file, or a dated companion file the spec
then points to) covering exactly these items, no more:
- `orders.company` (`SPS`/`SH`) and `orders.location` for SH — shape only, not the seed location
  list (that's OP-07's job once SH locations are confirmed).
- Enums that will grow (`order_type`, `order_events.event`, `reject_reasons`-style) converted to
  seeded lookup tables, each with its exact seed rows named in the delta text.
- A `notifications` table, separate from `outbox` (which stays the held Zoho write-back queue).
- The shape for several child jobs per one accepted order (confirm with the ingredient/question in
  the process-steps file before assuming multi-job is even needed for Release 1).
- `customer_portal` as a stored flag, defaulting `false`.

**Do not include MFA in this delta** — it moved to the December dashboard track's own spec delta
(`PD-02D`)/migration (`PD-03D`), 25 Sep 2026.

Each item needs its own numbered, falsifiable acceptance criterion in the spec's existing style
(a criterion sentence + check type T/E/C), added to §13 or a new delta-specific AC block the spec
references.

## What NOT to touch

- Do not write any migration file. This step produces a spec-delta document only.
- Do not touch the credit check, company/location's actual seed data, or anything else assigned to
  a later OP step.
- Do not edit `001-schema.sql` through `004-migration-hashes-append-only.sql` — they are frozen.

## Pipeline gates to follow

`spec-writer` drafts the delta → `plan-critic` reviews it. No `test-author`/`implementer` in this
step — there is no code yet. Do not proceed past a `plan-critic: BLOCK` verdict; fix the finding or
escalate it to the user with the finding quoted, per `/root/.claude/CLAUDE.md` §2.

## Acceptance criteria

1. `plan-critic` returns `PASS`.
2. Every item in "exact scope" above has ≥1 numbered, falsifiable AC in the delta text.
3. Every new lookup table has its exact seed rows and FK shape named in the delta (so OP-02 needs
   no further design decisions).
4. The delta explicitly states the credit check is out of its scope, pointing to OP-08.

## Tests to write first

None — this step produces no code. (OP-02 is where test-first work begins, against this delta.)

## Dev clone only, additive migrations only, never deploy

Work only in `/root/dev/production-dashboard`. This step touches no live directory, runs no
migration, and makes no deploy/push. The human runs `shdeploy` — you never do.

## Definition of done

The spec delta is written, `plan-critic: PASS` is recorded, and OP-02 can start without asking any
further design question about schema shape.

## Stop and ask conditions

Stop and ask the user (do not guess) if:
- Whether the multi-job-per-order shape is actually needed for Release 1 go-live is unclear from
  any file you've read — ask GM Samitha via the user, don't assume yes or no.
- Any lookup-table seed value is ambiguous.
- The delta would require touching `001-schema.sql`–`004-...sql` to express — it shouldn't; if it
  seems to, you've scoped something wrong, stop and ask rather than edit the frozen files.
