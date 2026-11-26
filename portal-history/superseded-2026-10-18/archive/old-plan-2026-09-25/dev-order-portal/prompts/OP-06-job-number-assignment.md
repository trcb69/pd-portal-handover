# OP-06 — Job number assignment

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** this step's date moved later — the shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-06`):** build 4–8 Dec 2026 (**FORCED**: later start only). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

`jobs.job_no` is nullable until set, opaque, never parsed. Small, fully specced step.

## Files to read first

1. Design spec §6.3 (`jobs.job_no` note, the UNIQUE constraint on `(division_code, job_no)`), §8
   (job-number rules), §10 (API table, the `to_production` 400 rule).
2. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §8.
3. AC1.12 in spec §13.

## Exact scope

- `POST /api/jobs/:id/job-no` `{job_no, reason?}`.
- 409 on a duplicate within `(division_code, job_no)` — NULLs don't collide.
- `reason` required, audit row written, when changing an already-set job number.
- `to_production` returns 400 when `job_no` is still null.
- Store the string exactly as typed — no format validation, no parsing, no auto-numbering.

## What NOT to touch

- Do not add any regex, format check, or "helpful" normalization of the job number string. Real
  examples like `RWU/IMP2357/QPP/00025/BIO` must round-trip byte-for-byte.
- Do not touch SO linking (OP-05) or job creation itself (OP-04).

## Pipeline gates to follow

`test-author` → `implementer` → `test-runner` → `code-reviewer`.

## Tests to write first

- AC1.12: "No SO" requires all four `entered_*` fields; duplicate `(division, job_no)` → 409 at
  both job creation and via `POST /job-no`; an opaque string with slashes and mixed case stored and
  returned exactly as typed.
- Changing an already-set job number without `reason` → 400; with `reason` → 200 + audit row.
- `to_production` with `job_no` still null → 400.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. No migration expected.

## Definition of done

All three tests above pass; a fuzz test with several real-world-shaped job-number strings from the
spec/brief round-trips unchanged.

## Stop and ask conditions

None expected — fully specced, no open question.
