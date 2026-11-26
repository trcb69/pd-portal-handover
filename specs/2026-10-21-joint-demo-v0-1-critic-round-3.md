# Plan-critic round 3: joint demo v0.1 (Rev 3, 21 Oct 2026) — APPROVE-WITH-CHANGES

Saved by the lead from the critic's hand-back. Design built correctly; three text fixes (applied in Rev 3.1).

## Must fix (applied)
- **C1** §4 step 5 impossible: a deleted order is never re-fetched (`zoho-queue.js:83-87`, p2 recheck `:71`); the client keeps no bodies (`client.js:2,68`; sync records `http_404_other`, `zoho-sync.js:381,392`). → one read-only GET by the human, record in `docs/zoho-api-findings.md`, set `client.js:7` in a reviewed commit; declare the delta to OP G3 step 5 (`order-portal-spec.md:840`).
- **C2** Demo DB: name the file; shdeploy backs up only its row's path (`/root/ops/shdeploy:147-150,182-183`; row `data/production.db`, `runbook-release-0.md:42`); tell managers pre-v0.3 work is practice; list re-entry (create-admin, users + pairs, §6 set-up, display_filter, re-sync). → v0.1 on `data/production.db`, archived with `.backup` at v0.3.
- **C3** PDD still said 007 (§4.8, `:223-225`, AC-D22 `:353`, `:376`, `:404`). → amended to 008 / v7.

## Notes (applied)
N1 round-2 items verified (C1 via `zoho-sync.js:144,277,284-286`; `migrate.js:39`; N3 `line-jobs.js:273-275`, `job-writes.js:61`) · N2 skip `shown()` when `at==='unassigned'` (`job-queries.js:96`; reasons `line-jobs.js:313-315`) · N3 unread badge `job-queries.js:107` · N4 draft/confirm fallback; 2–4 min · N5 dashboard gates straight after track B · N6 live `.env` · N7 AC48 wording, name→code mapping, MOBA_P · N8 J-AC5 labelled a guard.

Unverified: S1 names vs live `cf_order_received_from` spellings; Portal Ref hash key; re-sync duration; Poya date; track A size.
