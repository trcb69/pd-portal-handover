---
name: spec-delta-writer
description: Write a numbered spec delta to the frozen production-dashboard design spec, in the spec's own style, ready for a plan-critic pass. Use for OP-01 (Release 1 v2 delta), OP-08 phase 1 (credit-check delta), and any future delta (OP-15 turning into a real feature, OP-16's own delta). Trigger phrases — "write the spec delta", "amend the spec", "plan-critic pass", "new acceptance criteria", "before any code" "T/E/C criterion".
---

# Spec delta writer

## What this is for

This project's house rule is "no code without a spec" (`/root/.claude/CLAUDE.md` §1). Several
steps in this project's build (OP-01, OP-08, and eventually OP-15/OP-16) are explicitly gated on
writing a **spec delta** — a numbered amendment to the frozen spec — and getting a `plan-critic:
PASS` before any application code. This skill keeps every delta in the same style as the spec
itself, so `plan-critic` (and the next developer) isn't reverse-engineering a new format each time.

## Where a delta lives

Either amend `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md`
directly (it already carries Appendices A–F, one per past plan-critic revision — follow that
pattern), or write a dated companion file the spec then points to. Either way: **never touch
`server/db/migrations/001-schema.sql` through `004-...sql` to reflect a delta before the delta
itself has passed plan-critic** — schema changes are a separate, later step (OP-02) that
implements an already-approved delta, not part of writing it.

## The spec's own acceptance-criterion style (copy this, don't invent a new one)

Every AC in spec §13 is: **a numbered criterion, one line, a check type**. Check types used
throughout the spec: **T** (automated test), **E** (exercised/verified manually, documented), **C**
(config/checklist item, not a test). Example, verbatim from the spec: "AC1.1: `submitted_at` is
server time; a client-sent time is ignored." Write every new AC the same shape — a falsifiable
statement, not a goal or a description of intent.

## Checklist for writing a delta

- [ ] State exactly what's changing — new table(s)/column(s), enum→lookup-table conversions,
      new state(s) in a state machine, a new feature flag. Name the migration number it will
      become (never edit 001–004; the delta text can say "migration 005" as a plan, the actual
      file is a separate step).
- [ ] For every enum converted to a lookup table: name the exact seed rows and the FK shape, so
      the implementation step (e.g. OP-02) needs **no further design decisions** — this is
      explicitly required by OP-01's own acceptance criteria.
- [ ] Every item in the delta gets **at least one** numbered, falsifiable AC, same T/E/C style as
      spec §13 — don't leave an item without one, and don't invent ad hoc criteria later at
      implementation time instead.
- [ ] If the delta reconciles two conflicting prior drafts (e.g. the credit-check status enums,
      see the `credit-check-rules` skill), say explicitly which one wins and why — don't let both
      survive into the AC list.
- [ ] If the delta depends on an unanswered business question (e.g. multi-job-per-order shape,
      i18n), either get the answer first or write the AC conditionally and name who must answer
      before the AC can be tested — never guess an answer to make the delta look finished.
- [ ] Explicitly scope out anything not covered (e.g. OP-01 explicitly excludes the credit check,
      pointing at OP-08) — one line is enough, but it must be there.

## Running the plan-critic pass

Invoke `plan-critic` on the finished delta text (not on a mix of delta + implementation code —
this is a plan review, before code exists). A `plan-critic: BLOCK` verdict means the delta is not
approved and no code may be written against it; fix the finding or escalate to the human with the
finding quoted verbatim (`/root/.claude/CLAUDE.md` §2). Only an unambiguous `PASS` — not "approve
with changes" left open — lets the next step (schema/build) start.

## Checklist before calling a delta done

- [ ] `plan-critic` returned `PASS`, recorded (date + verdict quoted) somewhere findable — this
      project's convention is to record it in the delta file itself or in
      `dev/order-portal/02-process-steps.md`'s own step entry.
- [ ] Every "what the development must do" item from the relevant OP-step has a corresponding AC.
- [ ] No schema or application code has been written yet — a delta step's output is text, not code.

## References

- `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` §13 (the AC
  style to match) and Appendices A–F (six prior plan-critic review cycles, as worked examples).
- `dev/order-portal/02-process-steps.md` OP-01 (full worked instructions for the first delta this
  project needs) and OP-08 phase 1 (the second).
- `/root/.claude/CLAUDE.md` §1 rule 1, §2 (the pipeline gate this skill exists to satisfy).
