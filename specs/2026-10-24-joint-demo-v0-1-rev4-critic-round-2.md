# Rev 4.1 plan-critic round 2 (24 Oct 2026): BLOCK (one point)

Saved by the main session (the critic had no write tool). Condensed.

- **B1** Cloning a recorded line leaves the template's `project_id`/`project_name` (Job No wins over `cf_job_no`,
  `line-jobs.js:261`, `zoho-columns.json:162`); `pick` puts a project id into `cf_job_no` (OP:384,396); `later` must
  not invent `cf_job_no` (OP:364); template `is_combo_product`/`combo_type`, header shipped/invoiced status, totals,
  addresses leak. **Fix:** allow-list from an empty object; Job No per mode; combo from the item; ACs check
  `job_no`, `division_source='tag'`, `customer`.
- N1 portal backfill cannot finish (≈140 history calls/day at cap 1,500) → cap 2,000 and/or 30 days, show arithmetic.
- N2 sorted merge shifts every upstream page (2 calls per page) → page 1 only, no re-paging.
- N3 list-row shape undefined (status fields come from list rows, `zoho-sync.js:279`, `zoho-queue.js:12,86`); ids
  as strings (`columns.js:18-19`).
- N4 after Invoiced the job is closed (`line-jobs.js:255`), hidden by default `state=open` (`job-queries.js:136`).
- N5 `BRIDGE_HOST` default 172.17.0.1 (`config.js:44`); `APP_ORIGIN`/`TRUSTED_PROXY_IPS` defaults; gitignore gateway
  `.env`/templates; DEMO MODE visible in health/log.
- N6 no way out of `so_unknown` named → L16 (OP:274) in or out?
- N7 atomic sandbox/counter writes before the 2xx.
- N8 v0.5 needs a fresh portal DB or a purge of `99…` ledger rows.
- N9 `shapeProblem`/`divisionTag` are closures (`zoho-sync.js:251,266`) → test via the real sync or export.
- Round 1: B2 (pacing) resolved; B3 resolved given P0; B4 resolved; most N resolved.
- Simpler alternative: offline id→name maps from the 309 recorded details + on-demand item/contact/project GETs.
- Unverified: token scope readable at start; READ endpoints for tag options / custom fields; lookup call counts;
  ports free; `/root/demo/*` vs guard hook; Poya dates (owner: Vap Poya Sun 25 Oct).
