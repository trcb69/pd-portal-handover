# Plan-critic round 1: joint demo v0.1 (Rev 1, 21 Oct 2026) — verdict BLOCK

Saved by the lead from the critic's hand-back.

## Blocking
- **C1** The "free" filter needs OAuth list rows to carry `cf_*`; only the browser endpoint was seen to (`test/helpers/fake-zoho.js:54`, `test/fixtures/zoho/sps-list-templates.json:2,22`, 8 Oct study via :9335). Without them, list writes leave the cf columns NULL (`zoho-sync.js:144`) and the filter hides every new job. Make V1/V8 a precondition, or a display-only filter.
- **C2** No detail fetch ≠ not shown: jobs are built from existing lines (`line-jobs.js:125-134,240`); the filter only touches the queue (`zoho-queue.js:48-56,78-101`); backfilled SOs (`runbook-release-0.md:52-57`) would show stale, "checking" forever (`line-jobs.js:265-270`), shipped as open (`:247-248`). Display filter on the read path incl. counters, Unassigned, SSE, sweep; define narrowing.
- **C3** Portal-made jobs use the SH placeholder customer (OP `:89,:380`; 11/22 samples) and OPD is not whole until S4, so the TEST job never shows. The portal sync must never be filtered (OP §7.2.1, §7.4). Admit `cf_portal_ref` jobs; use the TACO BELL contact.
- **C4** Bought-in lines have no source in v0.1 (SH items; OP CHECK `:613`, O3 `:229`, O1 `:227`; no kind rule; no owner decision).
- **C5** Per-line decision announced, not specified (OP `:220,223`; breaks OP AC16–AC22b, AC26; O8 `:234`).
- **C6** Demo write mode inconsistent with OP §7 (ledger states `:429-431`, idem clash `:457`, recovery `:463-466`, L20 `:264`), kill switch = token revoke (`:646`), token cap (`:817`), G3 is discovery (`:838`) and must precede a live dashboard (`:840`).
- **C7** 12 Nov is the upper end (day 17.5); v0.2 1.5 days after; v0.3 depends on blocked PDD §4, DD-5, P2, P3 and an unspecified portal sign-in; v0.4 on OQ5, OQ20, V9–V12 and Q0–Q14; v0.5 on OQ7, OQ19, V5, OQ8, OQ9, V6, OQ18, V4, OQ12; v1.0's reorder screen is INV-05 (Jan 2027).

## Notes
N1 day/night polling is code (`config.js:28,55-56`, `zoho-sync.js:53,61-69,244-245,334,359`, `zoho-queue.js:33-40`); no generic settings route (`admin-config.js:419,514,539`) · N2 matching rule (codes vs full names; contact id) · N3 dashboard cap default 7,500 (`config.js:83`) vs ≤4,500; projects scope; per-instance counting (`zoho-queue.js:20-24`) · N4 practice jobs break the full list (`zoho-sync.js:216-219`) · N5 tunnel-only settings exist for the dashboard (`runbook-release-0.md:24-36`); portal override; "not bound" · N6 tests that cannot fail (J-AC3, J-AC6) · N7 widening bursts vs 4,500 cap · N8 demo data in the live portal DB → separate instance · N9 D4 vs `/root/CLAUDE.md` 7 Oct and PDD §9 · N10 TEST job never ticks packed/checked/invoiced · N11 first-deploy work missing from track C.

## Simpler alternative (adopted in Rev 2)
Dashboard: sync everything at a flat 2 min with cap 4,500; stage lists as a display-only filter admitting `cf_portal_ref` jobs. Portal: OP S0+S1 as written, writes off with the existing payload preview, G3 at the rehearsal; per-line decisions and bought-in lines to v0.2.
