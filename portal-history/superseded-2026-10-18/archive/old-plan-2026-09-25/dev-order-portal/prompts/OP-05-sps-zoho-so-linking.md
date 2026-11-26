# OP-05 — SPS ↔ Zoho SO linking

**Changed 25 Sep 2026:** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** scope narrows to portal-accepted orders only —
direct-job linking for PSU/SHPS already shipped early in `PD-04D` (`01c-dashboard-december-feasibility.md` §4).

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-05`):** build 26 Nov – 3 Dec 2026 (**FORCED**: later start only). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

This is fully specced and frozen — no new decision needed, build exactly as written. The SPS side
of linking a portal job to its Zoho sales order, using the existing read-only mirror built in
Release 0.

## Files to read first

1. Design spec §6.2 (the `so_key` matching rule — read this closely, it's the single most-repeated
   pitfall in the whole project), §6.3 (`job_so_links`), §7.2.3.
2. `server/services/sweep.js` — the existing post-import sweep. **Extend it, do not duplicate its
   matching logic.**
3. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §7, §17 (the `so_key` pitfall section).
4. AC1.10, AC1.11, AC1.20 in spec §13.

## Exact scope

- `GET /api/so/search?q=` against the existing `zoho_*` mirror tables.
- `POST /api/jobs/:id/so` with `{action: link|link_pending|unlink, salesorder_number}`.
- The exact `so_key` regex from spec §6.2: trim, uppercase, match `^([A-Z]+-\d+)(\s*-.*)?$`, group
  1 is the key. Never a naive string compare, never fuzzy matching.
- Sweep extension: resolve a `link_pending` reference once its SO appears in a later import —
  system `link` row, SSE job event within poll interval + 5s.

## What NOT to touch

- SH-side linking or the "Portal Order No" field (OP-12).
- Do not build any customer+date+line fuzzy match ("way C") — explicitly rejected in every source
  document that mentions it.
- Do not modify the import CLI's own upsert functions beyond what the sweep extension needs.

## Pipeline gates to follow

`test-author` → `implementer` → `test-runner` → `code-reviewer`.

## Tests to write first

- AC1.10: link shows Zoho fields, stage 4 detected; unlink → stage 4 not done immediately; re-link
  same SO → done again.
- AC1.11: a pending JOBORDER link resolves after the next import (system `link` row); SSE event
  within poll interval + 5s.
- AC1.20: `JOBORDER-08338 - C` and `joborder-08338` both match `JOBORDER-08338`;
  `JOBORDER-083381` does not; an SH row with the same SO number never ticks an SPS job.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. No new migration expected — `job_so_links` already exists
from Release 0/spec §6.3.

## Definition of done

All three ACs above pass, with the regex tested against every example string in spec §6.2 and
`plans/40...` §17.

## Stop and ask conditions

None expected — this step has no open business question. If the existing mirror data doesn't
support a test case you need, say so in your PR rather than fabricating mirror rows that don't
match real Zoho export shapes.
