# Rev 4 plan-critic round 1 (24 Oct 2026): BLOCK

Saved by the main session (the critic had no write tool). Condensed; citations as given by the critic.

## Blocking
- **B1 Sandbox job order from the payload never reaches My jobs.** OP §6.9 payload has ids only (OP 371-399); the
  dashboard marks a detail `bad_shape` without `line_item_id`/`item_type`/7 qty keys (`zoho-sync.js:251-265`); jobs
  need `item_type='inventory'`, non-draft (`line-jobs.js:134`); division from line tag names (`zoho-sync.js:266-277`),
  OPD header is a bucket → Unassigned (`line-jobs.js:57-60`, `006:91`); custom fields by api_name from
  `custom_field_hash` (`zoho-sync.js:285-288`); Job No = `project_name ?? cf_job_no` (`line-jobs.js:254`); customer
  = `cf_order_received_from` text. No "Checked" step exists (detectors so/bundle/picklist/package/shipment/invoice,
  `006:6`, `002-seed.sql:26-30`); re-fetch needs a `last_modified_time` bump (`zoho-sync.js:158-167`,
  `zoho-queue.js:12,84-87`). **Fix:** hydration contract cloning a recorded real SPS detail, overlay mapped names,
  `cf_job_no`, synthetic `line_item_id`s, qty keys 0; advance sets line/header qty packed/shipped/invoiced + statuses
  + bumps modified time; rename Checked → Shipment. R4-AC3 signs in as the unit coordinator with an OPD-bucket header.
- **B2 Budget numbers and cache savings do not hold.** Different watermarks → no list cache hits
  (`zoho-sync.js:158,166-167`; `sps-sync.js:207,85-87`); details fetched by both apps; 4,500 + 2,000 > 5,000; fresh-DB
  backfills; a gateway 429 is read as a rate limit, the later app goes stale till midnight (dashboard
  `client.js:66`, `zoho-sync.js:110,494-497`; portal `client.js:59`, `sps-sync.js:24`); 90/min < 100+50/min.
  **Fix:** app caps sum ≤ gateway (e.g. 3,300 + 1,500); gateway queues over-rate requests instead of 429; drop the
  cache claims; schedule both backfills before the demo.
- **B3 Gateway runtime/topology unspecified; new service = doctrine hard stop.** Only read path for days, warm-up 3
  days (J31:103), "started by the human", no supervisor, holds the refresh token in a dev tree. Where do the apps run?
  **Fix:** P0 owner approval before track G; state runtime per app, supervisor/reboot, warm-up date.
- **B4 Snapshot mode not buildable from the 8 Oct pull** (lists since 2025-10-01, 309 details, no bundles/items/
  projects, browser API shape). **Fix:** define it fully, or drop it and say v0.1 waits for P1.

## Non-blocking
N1 token design contradicts itself; apps refuse empty secrets; portal has no write client yet · N2 gateway holds a
READ-scoped token only (G-AC) · N3 sorted insertion; never reuse sandbox numbers · N4 Portal Ref stand-in
customfield id; G1 must use api_name `cf_portal_ref` · N5 tagged S1 AC list back to plan-critic; R4-AC2 stays until
v0.5; say whether OP §7.2 pre-checks are in v0.1; restart rule for `so_writing` · N6 v0.5 "retire per division"
needs its own delta · N7 dates optimistic; warm-up unscheduled; Poya ~25/26 Oct (unverified) · N8 "Kohalwila" also
matches "SPS Kohalwila Factory" · N9 demo button adds a non-GET outbound call to the dashboard → gateway page/curl ·
N10 gateway tests outside `test/*.test.js`; cross-repo e2e harness unspecified · N11 gateway 429s counted as
dashboard calls (`client.js:56`); demo `.env` interval 2 · N12 the :9333 200/min ceiling is not enforced.

## Simpler alternative
Thin gateway: GET pass-through, sandbox (clone a recorded order), merge, loopback advance page. No shared cache, no
gateway budget; each app's tested cap set so both sum ≤ 5,000.
