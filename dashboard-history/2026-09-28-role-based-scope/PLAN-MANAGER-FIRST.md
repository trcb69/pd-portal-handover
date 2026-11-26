# Manager dashboard first — plan (28 Sep 2026)

**User decision (28 Sep):** build and show the managers' dashboard first. It shows every production job each manager has, with its documentation part. Everything else is built on top of it, one piece at a time.

## What the managers will see (first version, view only)

- **Log in → "My jobs".** Every production job in the divisions they manage:
  - Ishan: PSU, Offset, Packpro, RWU
  - Mubeena: Screen Printing
  - Ranga: OPD, MOBA, FPP, CPU
  - Samitha (GM): all divisions, as a viewer
- **Counters at the top:** due in 3 days · past due · in production · produced but not shipped · documents missing.
- **Per job:**
  - customer (the real end customer: "Order received from" on the SPS sales order)
  - item, quantity ordered / produced / shipped / invoiced
  - due date and days late
  - a **documentation strip**: Sales order ✔ · Bundle (produced) ✔ · Pick list ✔ · Package ✔ · Shipment ✘ · Invoice ✘
- **"Documents missing" list:** jobs where a step that should exist by now is not in Zoho. For example: produced but no package after N days, shipped but not invoiced. Each row says which step is missing.
- **Data freshness line:** for example, "Zoho data as of 06:00 today". Flags are hidden when data is stale, as the spec already requires (spec:364-372).
- **Only jobs created or changed from the go-live date raise "missing" flags.** Older ones are listed as history, so managers are not flooded (critic B4).

## Why this is fastest

- Jobs come **automatically from SPS's Zoho sales orders** (one job per SPS SO / job number). Nobody has to type them in.
- The documentation strip is **detected from the Zoho documents** (bundles, pick lists, packages, shipments, invoices) we already know how to pull.
- It uses the **Release 0** code that is already built and tested (143 tests) in `/root/dev/production-dashboard` (login, roles, schema).
- It reads Zoho only and writes nothing.

## Steps (estimates, working days)

| # | Step | Estimate |
|---|---|---|
| 1 | Your 3 answers (below) + the SPS Zoho sign-in in the browser | day 0 |
| 2 | Short spec delta "PD-04D preview: auto-built job list + documentation strip" → plan-critic | 1 |
| 3 | Fresh read-only SPS pull: open + last 90 days of SOs, bundles, pick lists, packages, shipments and invoices. Batched and resumable, like the 21,700-record pull | 1 (runs alongside step 2) |
| 4 | Tests first, then build on Release 0; code review + security review | 4–6 |
| 5 | Load the snapshot, private deploy (you run the deploy command), check with you | 1 |
| 6 | Show Ishan / Mubeena / Ranga / Samitha, and collect what to add next | — |

About **8–10 working days** to a working preview on real data. That is ahead of the existing 5 Nov "managers' job list" milestone, which it replaces. This is an estimate, not a promise. The critical path is step 4.

**Next pieces after the preview, one at a time:**
1. Daily auto-refresh from Zoho
2. Blockers with reasons (PSU pilot, 8 Dec)
3. Manual ticks for the steps Zoho can't show (artwork, job card, item photo)
4. GM tile (22 Dec)
5. Then the order portal and inventory screens, on the same login

## Answers (28 Sep)
1. One job = one SPS SO line + job number, routed to that item's division manager; opening an SO shows every item on it with its own progress, also items in other divisions (read-only).
2. Mapping confirmed.
3. Automatic sync from day one → adds ~3–5 days (≈ 11–15 working days to the preview). Needs a read-only Zoho API client for the SPS org (Zoho API console, created by the Zoho admin; secrets stay in a server env file, never in chat or git).

## Questions (answered)

1. **What counts as one "job"?** Proposed: one SPS sales order line with its CF.Job No (the JOBORDER on the bundle). Alternative: one SPS sales order.
2. **Manager ↔ division list:** confirm the mapping above, including the OPD split between Ranga and Ishan.
3. **Preview data:** a snapshot refreshed once a day for the preview (fastest), with the automatic sync as the next step?

## Scope-review note

The role-based scope draft (SCOPE.md) got **plan-critic BLOCK**. Its main points, to fix when the scope is revised:

- **Owner of the "stuck at shipped" orders.** The 11,556 SH orders are SH branch staff's, not Ilham's (SPS). Our systems can't see them until SH access covers all locations.
- **Missed steps we can't detect.** "Reason recorded" and "goods received but not entered" can't be detected from Zoho without a Zoho custom field.
- **Existing access control.** Managers already see only the jobs they manage. The gap is feature switches per division, not data visibility.
- **Old backlog.** Cleaning up the old backlog is a bulk Zoho write. Instead, flag only records from the go-live date onward; the old backlog is a separate, human-run task.
- **Finished goods.** SPS phase-1 finished goods need a screen from 5 Jan.
- **No-code Zoho fixes.** Add "configure Zoho (mandatory reason field, workflow email alerts, saved views)" as an honest option for the SH record-keeping items.
- **Architecture.** The shared core is an open decision (Q8), not settled.
- **Smaller corrections:** baselines that match their targets, the 15-item cap is an open decision, and the prefill helper is still a draft.

The manager-first plan above already follows the review on the go-live cutoff and on freshness gating.
