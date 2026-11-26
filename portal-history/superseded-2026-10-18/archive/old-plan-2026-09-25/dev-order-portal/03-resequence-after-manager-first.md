# Order portal - what the 28 Sep "managers' dashboard first" decision changes

Written 29 Sep 2026. Planning only: no OP step's content changes here and no dates are rewritten yet.
Read with `../01b-dated-schedule.md` (the dated schedule) and `../01c-dashboard-december-feasibility.md`.

## 1. Most of the re-sequencing already happened on 25 Sep

The portal was already put behind the dashboard when the dated schedule was built. For the record, so
nobody redoes it:

- **OP-11 (Zoho read-only sync + master data) was removed entirely** and ships ~10 weeks earlier inside the
  dashboard track as `PD-05D`, because the December dashboard needs it and not only the portal
  (`../01b-dated-schedule.md:298`). The SH-side half stays under `OP-16`.
- **MFA left OP-01/OP-02** and became its own dashboard-track migration, `PD-03D`, because it is a
  "going public" gate rather than a portal feature (`../01b-dated-schedule.md:61-63`).
- **OP-01 starts 22 Oct 2026** rather than early October, because the same developer works the December
  dashboard track first (`../01b-dated-schedule.md:288`). Everything after OP-11's removal lands within a
  couple of working days of its original date - removing 9 working days of OP-11 roughly cancels the
  later start (`:299-300`).
- End of the line is unchanged: **OP-14 go-live 25 Jan 2027, full release 15 Feb 2027** (`:301`).

## 2. What 28 Sep actually changes

The manager preview (spec `2026-09-28-pd-manager-preview.md`) is an earlier, narrower version of the
`PD-04D` "managers' job list" milestone that was dated 5 Nov, and it absorbs `PD-05D`'s Zoho sync into
itself. `PLAN-MANAGER-FIRST.md` states it "replaces" that milestone.

For the portal that is mostly good news - its two dependencies arrive earlier - but it creates two
concrete problems that must be settled before any OP step builds.

### 2.1 Migration 005 is claimed by three tracks at once

Migrations are forward-only and 001-004 are frozen. 005 is not written or deployed, so its content is
still open - which is exactly why all three tracks assumed they could have it:

| Claimant | What it wants in 005 | Source |
|---|---|---|
| Manager preview | the new sales-order-line table and the per-order sync failure columns | spec "Data model changes" |
| `PD-03D` | MFA schema, described as "split from migration 005" | `../01b-dated-schedule.md:146` |
| `OP-02` | the portal half: company/location, credit and notification lookup tables | `prompts/OP-02-schema-migration-mfa.md:37` |

**Decided 8 Oct 2026 (PD managers' full-release spec Rev 3 §8.1):** preview = `005`, PD managers' full
release = `006`, `PD-03D` MFA = `007`, `OP-02` portal half = `008` onward. The numbering checks (§8.1)
now catch a duplicate number at startup and a gap in `npm test`. `OP-02` is already written flexibly ("`005-...sql`, `006-...sql` if needed"), so this costs it
nothing. Fix the numbers in all three documents in one pass rather than letting an implementer pick.

### 2.2 OP-05 depends on job creation that the preview may not ship

`prompts/OP-05-sps-zoho-so-linking.md:8` scopes itself to "portal-accepted orders only", because
"direct-job linking for PSU/SHPS already shipped early in `PD-04D`". That assumption came from `PD-05D`,
which included a job-creation bootstrap ("New file (direct)").

But the manager preview is deliberately **view only** (`PLAN-MANAGER-FIRST.md`, "What the managers will
see (first version, view only)"), and its jobs are derived from Zoho rather than created by anyone. If the
preview ships without the job-creation bootstrap, OP-05's narrowed scope is wrong and the work it assumed
was already done has to come back into the portal track - or into a dashboard step between the preview and
OP-05.

**Action:** confirm against the preview spec once Rev 6 lands, then either restore the direct-linking
scope to OP-05 (re-costing it) or name the dashboard step that will carry it. Do not let OP-05 start on the
current assumption.

## 3. What is NOT changing today

- No OP step's content, order or estimate is rewritten. The two items above are dependencies to settle,
  not a re-plan.
- OP dates stay as the dated schedule has them. Re-dating now would be guessing: the preview's own scope
  is still moving (two critic rounds blocked it on 28-29 Sep and a fix pass is in progress), so any date
  derived from it today would be wrong tomorrow.
- `OP-16` (SH triage and fulfilment) still waits on SH Zoho admin access for all 10 locations, which the
  CEO owns.

## 4. Next review point

When the manager preview's Rev 6 passes `plan-critic`, re-open this file and: fix the three migration
numbers in one pass; settle OP-05's scope; and only then re-date OP-01 onward if the preview's real
finish date has moved off the dated schedule's assumption.

Abdul Hadhee | IT Exec | Standard-Holdings
