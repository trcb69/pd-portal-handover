# Rev 4.2 plan-critic round 3 (24 Oct 2026): BLOCK (one point)

Saved by the main session (the critic had no write tool). Condensed.

- **B1** `pick` hydrates via `GET projects/<id>` under `/inventory/v1/`, but V3 (OP:826) is open and the portal has
  no `sps_projects`/`sps_contacts` (`sps-sync.js:218-225`); `later` gives `jobNo=null` → Unassigned `no_job_no`
  (`line-jobs.js:261,322`, `job-queries.js:114`), failing R4-AC3. **Fix:** serve projects from the offline map
  (pairs in `details.json`), or run V3 first with (a) as fallback.
- Round 2: B1 resolved for hydration; N1–N5, N7–N9 resolved; N6 partly (L16 does not link — that is L15/L26).
- N1 POST lookups uncounted (up to 5 per order). N2 lookups can outlast the portal's 30 s timeout → `so_unknown`;
  pacing must be even spacing ≥667 ms. N3 confirm must bump `last_modified_time` (`sps-sync.js:179`). N4 unknown
  list filters must be refused (400), not ignored. N5 `later` and 30-day history side effects for the presenter.
  N6 `combo_type` seen on SO lines only.
- Simpler alternative: projects, contacts, tag/custom-field names from the offline map + the portal's item mirror;
  POST makes zero upstream calls.
- Unverified: `/inventory/v1/projects`; item detail fields; not-started status values; ~390 orders/month;
  `last_modified_time` filter inclusivity.
