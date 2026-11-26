# OP-07 — Company (SPS/SH) and SH-location tagging on orders

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** this step's date moved later — the shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-07`):** build 9–11 Dec 2026 (**FORCED**: later start; answer deadline moves to 25 Nov 2026). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

"Never sum SPS and SH" must be structurally enforced, not just a reporting convention. This step
wires the `orders.company`/`.location` columns OP-02 added into the submission form and API, and
puts a visible flag on SH locations that aren't yet confirmed by a live sync.

## Files to read first

1. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §6 in full.
2. Design spec D4 (the `org` pattern already used on every mirror row) — extend the same
   convention, do not invent a second one.
3. `zoho-helper-userscript-spec.md:42` (or wherever it now lives in
   `/root/Production Dashboard/`) for the 10 known SH location names and the 3 confirmed from live
   order data (Head Office 55,874, South Branch 13,873, Central Branch 2,235 — figures as of the
   brief; re-verify against current data if available).
4. Your own OP-02 migration for the exact `orders.company`/`.location` schema shape.

## Exact scope

- Require `company` on `POST /api/orders`; require `location` when `company = SH`.
- Seed `orders.location` as a free-choice list of all 10 known SH locations, with the 7 unconfirmed
  ones (i.e. not yet seen in live sales-order data) flagged "unverified" in Admin and in the
  picker.
- Add a code-review checklist note (in your PR description, and ideally a comment near any
  aggregate query) that no report/query anywhere in Release 1 sums values across `company` without
  an explicit, named exception.

## What NOT to touch

- Do not hard-code Head Office as the only SH location option — the sync gap is real, not a UI
  question to route around.
- Do not build the actual SH sync (OP-11 covers SPS only; SH sync is OP-16, blocked on SH admin).

## Pipeline gates to follow

`test-author` → `implementer` → `test-runner` → `code-reviewer` (specifically checking the
no-cross-company-sum rule across this step's diff).

## Tests to write first

- `POST /api/orders` without `company` → 400.
- `company = SH` without `location` → 400.
- A grep/lint-style test (or a documented manual check in the PR) confirming no query in the
  Release-1 diff sums `orders.value` or any derived total across `company` values.
- The 7 unconfirmed SH locations render with an "unverified" flag wherever they appear.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. Schema comes from OP-02; if you find you need a new column
here, that belongs in a fresh additive migration, not a change to OP-02's.

## Definition of done

All tests above pass; the "unverified" flag is visible in the actual UI, not just in a data field
nobody renders.

## Stop and ask conditions

- The names/existence of the other 7 SH locations are not confirmed anywhere you can read — use
  the `zoho-helper-userscript-spec.md` list as a starting seed, flag every one of them
  "unverified" by default, and note in your PR that SH Rizwan/Abdullah still need to confirm the
  full list (see `questions.md`). Do not silently narrow the list to only the 3 confirmed ones —
  that would hide the other 7 rather than flag them.
