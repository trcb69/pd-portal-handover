# OP-16 — SH-side triage and fulfilment (floating — do not start without SH admin access)

**Changed 25 Sep 2026:** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`
only once SH Zoho admin access (all 10 locations) has actually been granted and confirmed.**

**Dates:** not scheduled (`dev/01b-dated-schedule.md` row `OP-16`, "NOT SCHEDULED") — waits on the
CEO granting SH Zoho admin access across all 10 locations.

## Context

**Do not begin any work on this step until SH admin access is confirmed.** This step is
deliberately under-specified in `02-process-steps.md` — it needs its own spec delta before real
work starts, following the same pattern as OP-01. This prompt exists to mark its place in the
sequence and to point at what must happen first, not to hand you a buildable scope today.

## Files to read first (before writing the spec delta this step actually needs)

1. `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/order-portal/02-process-steps.md`,
   step OP-16, in full.
2. `/root/Production Dashboard/LATER.md`, item L27, in full.
3. `/root/Production Dashboard/BUILD-ORDER-2026-09-20.md`, floating-builds table, "SH fulfilment"
   and "Zoho sync, SH" rows.
4. `zoho-helper-userscript-spec.md` (draft, unapproved — read for context, do not build from it
   directly without a plan-critic-approved delta first).
5. `/root/Operation Food Packaging Division — Team Structure.pdf` — **read this before scoping
   anything**; it was not read for the brief this project is based on.

## Exact scope

**None yet.** The first real task, once SH admin access is confirmed, is to write this step's own
spec delta (a `spec-writer` → `plan-critic` cycle, same as OP-01), covering: SH sync's own call
budget; the helper/userscript's actual approved field list (trimmed per Senuri's answer in
`questions.md`); "way A" linking via the Portal Order No field once sync exists (making OP-12's
"way B" fallback obsolete for new orders, while old pasted links stay as a historical fallback);
ex-stock dispatch (Saman's team, Pasindu's packaging slip). Only after that delta passes
`plan-critic` does this step get an actual numbered scope, test list, and effort estimate.

## What NOT to touch

- No code at all until the spec delta above is written and passed.
- Do not assume any detail from `zoho-helper-userscript-spec.md` is final — it is an unapproved
  draft.
- Do not touch OP-12's "way B" fallback logic — this step supplements it, doesn't replace it
  immediately (old pasted links must keep working).

## Pipeline gates to follow

`spec-writer` → `plan-critic` first, for the delta this step needs. Then the normal
`test-author` → `implementer` → `test-runner` → `code-reviewer` (+`security-auditor` since this
touches a new external-facing helper surface, +`db-migration-guard` for the SH sync tables) once
scope exists.

## Tests to write first

Not yet determinable — write these as part of the spec delta, in the same style as every other
step's ACs.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only, once started. Any new migration for SH sync tables or a
`notifications`/helper-related table is additive, never a change to earlier migrations.

## Definition of done (for this prompt, as written today)

Nothing — this prompt's "done" state is simply: SH admin access is confirmed, the spec delta is
written and passed `plan-critic`, and a follow-up prompt (OP-16a, OP-16b, etc., or a renumbered
OP-17+) exists with real scope. Do not report this step "done" by building against guessed scope.

## Stop and ask conditions

- SH Zoho admin access is not yet confirmed — stop immediately, do not proceed on any assumption
  about what access might look like once granted.
- Even with access granted, stop after reading the files above and write the spec delta first —
  do not skip straight to code because the access blocker is gone; the scope blocker (no approved
  delta) is separate and still applies.
