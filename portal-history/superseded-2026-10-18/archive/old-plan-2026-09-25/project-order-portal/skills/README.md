# Order portal — custom Claude Code skills (draft, not installed)

**Changed 25 Sep 2026:** the `credit-check-rules` row and the "Why these five" intro paragraph now
say "two open business questions" (was three) — the credit-limit data-source question is DECIDED
(Zoho Inventory, no Books).

Prepared by Abdul Hadhee | IT Exec | Standard-Holdings, 25 Sep 2026.

Five draft skills for building the order portal (Release 1 of `/root/dev/production-dashboard`).
Each is a folder here with its own `SKILL.md`, in the standard format (YAML frontmatter `name` +
`description` with trigger phrases, then instructions/checklists/file paths/references). **None of
these are installed.** Review each one, then copy the folder to `~/.claude/skills/<name>/` when
ready.

## Why these five, not others

This project's build (`dev/order-portal/02-process-steps.md`, OP-01…OP-16) has a few places where
getting it wrong is expensive and easy to get wrong the same way twice: a state-machine feature
with append-only tables and race conditions (fixtures), a genuinely gated feature with two open
business questions (a third — where the credit limit lives — was DECIDED 25 Sep 2026: Zoho
Inventory, no Books) (credit), a repeated pipeline
step this project alone needs at least four times (spec deltas — OP-01, OP-08, and eventually
OP-15/OP-16), a single regex that the brief calls "the single most-repeated pitfall" if it's
reimplemented instead of reused (SO linking), and a visibility/redaction rule that spans five
different steps and has a specific, non-obvious test method (AC1.2's key/value scan, not a
route-by-route read). Each skill exists because the same mistake is one step-boundary away from
being made independently by whoever builds the next step, without it.

| Skill | Helps with | Why it helps |
|---|---|---|
| `order-lifecycle-fixtures` | OP-03, OP-04, OP-05, OP-06 | The state machine (spec §7.2.0) and its append-only tables are easy to fixture *wrong* in a way tests won't catch — an UPDATE where there should be an INSERT, an `order_events` id order that doesn't match the real sequence. This skill fixes the fixture pattern once so every later test builds on the same correct base, instead of each developer re-deriving it and one of them getting it subtly wrong. |
| `credit-check-rules` | OP-08 | This is the single most detailed, most gated feature in the whole project: two open business questions (block-vs-hold; dues definition — the data-source question, formerly a live conflict between a 22-Sep and a 24-Sep decision, was DECIDED 25 Sep 2026: Zoho Inventory, no Books) and two draft enum sets that must not both ship. A generic developer prompt won't carry all of that context every time; this skill does, and it stops code from being written before the spec delta and the two remaining questions are actually resolved. |
| `spec-delta-writer` | OP-01, OP-08 phase 1, and any future delta (OP-15 becoming real, OP-16's own delta) | This project needs a spec delta, in the frozen spec's own AC style, at least twice already and probably four times total. Without a skill, each delta risks drifting into its own format, which is exactly what makes `plan-critic` slower to review and easier to rubber-stamp incorrectly. |
| `so-link-verifier` | OP-05, OP-12 | The `so_key` regex is the exact mechanism that fixes the ~17–18%-fill-rate SH-SO-linking problem this whole feature area exists for. The brief calls it "the single most-repeated pitfall" — a plausible-looking substring match silently drops or misattributes records without ever throwing an error. This skill makes the correct regex and its three worked test cases the default, not something a developer has to remember to look up. |
| `visibility-redaction-audit` | OP-04, OP-08, OP-09, OP-10, always in OP-13 | The visibility matrix and redaction rule are tested by a specific method (a key/value scan on seeded data) precisely because a route-by-route review has a documented history of missing leaks in this spec's own review appendices. This skill turns that test method into a checklist so it's applied consistently across five different build steps, not just remembered once and then forgotten by step three. |

## What was deliberately left out

A sixth or seventh skill for things like "attachment MIME/magic-byte checking" (OP-10) or
"notification delivery retries" (OP-09) was considered and dropped — both are, per the brief
itself, fully specced with zero open questions (OP-10) or a mostly mechanical build once an SMTP
account exists (OP-09). A skill earns its place by preventing a *recurring* mistake or carrying
context across *multiple* steps; a single, already-fully-specced step doesn't need one.

## How to install (after review)

```bash
cp -r "/root/Project Management/reports/2026-09-25-sps-business-plan/projects/order-portal/skills/<name>" \
      ~/.claude/skills/<name>/
```

Do this one skill at a time, after reading its `SKILL.md` and confirming it still matches the
current state of the spec delta / build step it supports — several of these skills (especially
`credit-check-rules`) reference open questions that may be answered by the time you install them;
update the skill's text to match the answer before installing, don't install it stale.

## Files this README draws on

- `../PROJECT-MEMORY.md` — the project's own non-negotiable rules and open decisions, which every
  skill above points back to rather than restating.
- `../../dev/order-portal/02-process-steps.md` — the 16-step build plan each skill is scoped
  against.
- `../../dev/order-portal/questions.md` — current status of the open questions
  `credit-check-rules` and `spec-delta-writer` both depend on.

Abdul Hadhee | IT Exec | Standard-Holdings
