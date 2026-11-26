---
name: order-lifecycle-fixtures
description: Generate and validate test fixtures/seed data for the order portal's state machine (orders, order_lines, order_events, jobs) against the frozen spec. Use when writing tests for OP-03 (order submission/lifecycle), OP-04 (triage), OP-05 (SO linking), OP-06 (job number), or any test that needs a realistic order/job in a given state. Trigger phrases — "seed an order in state X", "fixture for triage", "test the accept race", "build a test order", "fixture for cancel_pending", "transition matrix test".
---

# Order lifecycle fixtures

## What this is for

The order portal's core state machine (spec §7.2.0) has a small, exact set of legal transitions
and several append-only tables that must never be updated in place. Every test that touches an
order needs a fixture in a *specific, legal* state — not a hand-rolled INSERT that happens to look
right. This skill builds those fixtures consistently, so tests don't quietly drift from the spec's
own state machine as the release grows.

## Before you use this skill

Read `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` §6.3 (core
tables), §7.2.0 (state machine), §7.2.1 ("Updates are not edits"). Read
`/root/Project Management/reports/2026-09-25-sps-business-plan/projects/order-portal/PROJECT-MEMORY.md`
§4 rule 2 (append-only tables) and §9 (glossary) first if you haven't already this session.

## The state machine to build fixtures against (spec §7.2.0)

```
submitted → (triage: ask) → questions → (requester replies) → submitted
submitted / questions → (triage: accept) → accepted → job created
submitted / questions → (triage: reject, reason required) → rejected  [terminal]
submitted / questions → (triage: cancel, only while cancel_pending) → cancelled  [terminal]
```

`cancel_pending` is a flag, not a state, and can be true at any point before a terminal state.

## How to build a fixture

1. **Decide the target state** from the table above, and whether `cancel_pending` should be set.
2. **Insert in this exact order**, matching the append-only chain (spec §6.3):
   - `orders` row (immutable after insert — never UPDATE it in a fixture either; if the test needs
     a different order, insert a new row).
   - `order_lines` row(s) — written once, at submit.
   - `order_events` rows, one per transition, in id order (id order is what "latest" means, not
     the `at` timestamp — spec §6.3 ordering rule, review 2 B1). Don't backdate `at` and expect
     "latest" to follow it.
   - If the target state is `accepted`: also insert a `jobs` row with `order_id` set to this
     order's id (partial-unique — an order can never produce two jobs; don't try to fixture two
     jobs off one order, the DB will reject it and that's correct).
3. **Never fake immutability** by inserting then updating. If a test needs to prove immutability
   is enforced, that's the test — insert once, then attempt the forbidden UPDATE/DELETE and assert
   it's aborted by the trigger (AC1.3), don't work around the trigger in setup.
4. **For a race-condition test (AC1.4)**: fixture a single `submitted` order, then fire two
   concurrent `accept` calls in the test itself — don't pre-fixture two "simultaneous" states,
   that isn't what the AC is testing.
5. **For an Enter-on-behalf fixture** (spec Rev 4 N10): set `created_via = 'on_behalf'`,
   `submitted_at` to the typed WhatsApp receipt time (must be in the past, within 60 days),
   `entered_at` to now, and add the audit row — this is a materially different fixture from a
   normal portal submission, not just a flag flip.

## Checklist before trusting a fixture

- [ ] Every append-only table's rows were only ever INSERTed, never UPDATEd, in the fixture code.
- [ ] `order_events` rows are in ascending id order matching the real transition sequence, not
      just the right `at` timestamps.
- [ ] If the fixture reaches `accepted`, exactly one `jobs` row exists, `order_id` FK set.
- [ ] The fixture doesn't invent an `order_events.event` value outside the seeded enum
      (`submitted / asked / answered / accepted / rejected / cancel_requested / cancel_declined /
      cancel_resolved / cancelled`) — check `server/db/migrations/001-schema.sql` for the current
      CHECK/lookup, and OP-02's new migration if the delta converts it to a lookup table.
- [ ] A rejected fixture has a `reject_reason_code` from the seeded `reject_reasons` table, never
      free text in that column.
- [ ] The fixture's `org` (SPS/SH, once OP-07 lands) matches what the test claims — a same-numbered
      SO on the wrong org must never match a job of the other org (AC1.20, org isolation).

## Files to know

- `/root/dev/production-dashboard/server/db/migrations/001-schema.sql` — the frozen schema, read
  for exact column names and constraints before writing any INSERT.
- `/root/dev/production-dashboard/test/` — existing Release-0 test fixtures; match their style
  (`node --test`, `better-sqlite3` synchronous calls) rather than inventing a new pattern.
- Spec acceptance criteria to fixture against: AC1.1, AC1.3, AC1.4, AC1.7, AC1.8, AC1.12, AC1.20
  (`.../wiki/specs/2026-09-17-production-dashboard-design.md` §13).

## References

- Spec §6.3 (core tables, append-only markers), §7.2.0 (state table), §13 (AC1.1–AC1.31).
- `dev/order-portal/02-process-steps.md` OP-03, OP-04, OP-05, OP-06 — each step's own acceptance
  criteria list, which this skill's fixtures exist to make testable.
- `PROJECT-MEMORY.md` §4 (non-negotiable rules), §9 (glossary — job number, so_key).
