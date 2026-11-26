# Plan-critic round 1: PD demo release (Rev 1, 21 Oct 2026) — verdict BLOCK

Saved by the lead from the critic's hand-back (the critic had read-only tools).

## Blocking findings
- **C1** New `zoho` detector keys violate `doc_steps.detector_key` CHECK (`006-line-job-workflow.sql:6,9`); INSERT OR IGNORE does not skip CHECK failures; `migrate.js:61-70` aborts startup; a table rebuild is forbidden by `lint-migrations.js:71-73`. Use DTO fields instead.
- **C2** `route_unit_families = [["OPD","PACKPRO","MACPRO"]]` (`006:93`) + `resolveRoute` (`line-jobs.js:66-81`) fold a MACPRO prepend back into the home unit; printed jobs never start at MacPro. Change families to `[["OPD","PACKPRO"]]`, state the knock-on (AC28/AC31), test resolved `start_unit`.
- **C3** `cli/import-routes.js:61-68` maps one token to one unit and skips admin-edited items (`:81`): pre-fill needs a derived routes.csv with a `MacPro > ` prefix + `"MacPro":"MACPRO"` map entry; lids by `PUT /admin/item-routes/:id`; AC-D7 narrowed.
- **C4** Migrations must be contiguous (`test/release-migrations.test.js:166-170`, `lint-migrations.js:103-108`); 008 with 007 reserved fails, and a later 007 would be skipped forever (`migrate.js:53`).
- **C5** Snapshot fallback does not exist: only the live sync writes `zoho_so_line_items` (`zoho-sync.js:310`); `source='pull'` imports headers/bundles/invoices only (`cli/import/files.js:14-16`); freshness counts only `source='sync'` (`line-jobs.js:98-111`) so counters/flags hide. Make the Self Client a precondition or build a loader.
- **C6** "Missing" for availability is undefined (`job-queries.js:45`, `line-jobs.js:350-370`); AC-D4 code is `step_inactive` (`job-writes.js:48`); no admin API for `doc_steps.active` — hide steps with `PUT /admin/divisions/:code/stages` (`admin-config.js:160-179`).
- **C7** Estimate omits C1–C6, a web app from zero (`web/src/App.tsx:19-26` placeholder), the first-ever deploy (`/root/production-dashboard` absent; MACPRO + pairs only in `test/helpers/release-harness.js:59-63`), and the 17 failures measured on a tree with uncommitted auth work.

## Notes
N1 availability fields are per SO, not per line (`v8/d.json` `item_custom_fields: []`) · N2 V-D1 answered: `cf_screen_plate_availability_2` (`config/zoho-columns.json:22,121`) · N3 `JOB_ROWS` (`line-jobs.js:125-134`) and `stageEntry` (`:410-439`) don't read the columns; new chip states change the DTO · N4 attention sort and customer search not on the server (`job-queries.js:27,123`) · N5 batch send = N requests; 409 `stale` partials; 60 writes/min (`jobs.js:33`) · N6 send back needs a note (`job-writes.js:96`) · N7 route re-import moves open jobs at once (`line-jobs.js:294-301`) · N8 STRIP via `POST /admin/divisions` (`admin-config.js:151-154`); stranded jobs if deactivated · N9 Playwright ACs run under `test:e2e`, not `npm test` · N10 AC-D17 needs chip compaction · N11 no admin API for `planned` steps (`admin-config.js:459`) · N12 MOBA-Cup not in the printed-token list.

## Simpler alternative (adopted in Rev 2)
Availability as DTO fields (no migration) · steps/units by admin API · derived CSV + families change + lid edits by hand · live data only (Self Client precondition).
