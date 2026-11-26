# Rev 4.3 plan-critic round 4 (24–25 Oct 2026): BLOCK (one point)

Saved by the main session (the critic had no write tool). Condensed.

- Round 3: all resolved (B1 via projects from the map, N1–N6, round-2 N6).
- **B1** End customer has no source: dashboard shows `cf_order_received_from` (`line-jobs.js:482`,
  `zoho-columns.json:112`), a contact lookup (~110 ids in `details.json`); OP payload sends a contact id (OP:380);
  the map held "1 customer"; no `sps_contacts` in the portal. **Fix:** contacts source for the portal; id → name pairs
  in the map; placeholder name from the `End customer:` note (OP:378); R4-AC3 with a real key customer.
- N1 projects row shape/paging (`sps-sync.js:93-97`). N2 filter fixture must be regenerated from S1 code and cover
  every list path; a 400 is a quiet `upstream` error (`sps-sync.js:43`) → log loudly. N3 `cf_job_no` id vs name rule
  conflict (OP:384). N4 L15 onto a draft strands it (OP:273,276; `line-jobs.js:139`). N5 SQLite needs
  `better-sqlite3` (in the lock), readonly + fileMustExist, not `openDb` (`open.js:13-16`). N6 20 s wait + Zoho time
  can pass the 30 s timeout. N7 `sps_items.raw_json` is the list row (`sps-sync.js:213`), likely without `combo_type`
  → only mapped items work.
