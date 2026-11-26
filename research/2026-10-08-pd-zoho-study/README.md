# SPS Zoho study for the Production Dashboard (8 Oct 2026)
Read-only. Signed-in itexe@ Chrome (CDP :9335), GET only, ~1 request / 1.2 s, about 1,050 calls (lists 600+, 309 SO details, 44 comment fetches, 3 failed URL guesses). Nothing was written to Zoho.
Org 843825512. Tags used below: **[M]** measured, **[E]** estimated/modelled.

Files: `zget.mjs`, `pager.mjs` (pull tools), `pulls/` (raw pages), `analyse_a.py`, `analyse_a2.py`, `analyse_rule.py`, `analyse_hist.py`, `analyse_b.py`, `analyse_c.py`, `daily_counts.csv`, `modelB.json`, `routes.csv`, `fact-check.md`.

## Part A - what decides a job's division
Line-level data = the 16 Sep export `/root/exports/zoho/native/2026-09-16/Sales_Order.xlsx` (16 Sep 2025 - 15 Sep 2026, 4,559 lines, 3,362 SOs; same window as the 29 Sep study, numbers reproduced exactly) plus live API for 16 Sep - 8 Oct (266 SOs, 275 lines).

**Fields that name a division/unit/person [M]**
| Where | API name / label | Fill 12 m | Values |
|---|---|---|---|
| SO header custom field | `cf_manufacturing_division` / "Manufacturing Division" | 100% every month | 11 (OPD bucket 2,029; SHPS 1,080; PCU 523; PSU 305; RWU 224; CPU 163; MOBA Punching 161; Lid 33; FPP 32; Cake 6; Plate 3). Live also shows "Digital Printing Unit (DPU)" (3 SOs recent) |
| SO line reporting tag | `tags[]` with `tag_name="Division"` (xlsx column "Division") | 92.7% (monthly range 88.3-95.7%); live 16 Sep-8 Oct 93.8% | 10 (PackPro 1,451; Screen Printing 1,078; MOBA 617; MacPro 464; PSU 217; MOBA Punching 195; CPU 163; FPP 32; RWU 9) |
| Header `tags` (reporting tags on the SO) | none used | 0 | Division exists only on lines (305 line tags, 0 header tags) |
| Salesperson | `salesperson_name` | 0% (4,559 of 4,559 blank) | useless |
| Warehouse | line `warehouse_name` | 100% | "SPS Work In Progress" 4,540 / "Finished Goods" 19: no division information |
| Job no | `cf_job_no` | 98.4% (94.9-100% monthly) | ids a job, not a unit |
| Creator | `created_by_name` (detail only) | 100% | see history below |
| Item master | `cf_bu`, `cf_fg_sub_category`, `cf_parent_category`, `cf_raw_material_category`, `cf_fg_type`, `cf_fg_nature` (all lines match an item: 0 unmatched) | 100% | `cf_bu` has 18 values |
Per-month fill table: `pulls/partA_fill.json`. Line-tag fill never dropped below 88% in any month; no trend.

**Header vs line [M]:** of 4,226 tagged lines, 4,125 (97.6%) are consistent with the header (OPD header allows PackPro/MacPro; PCU/Lid/Cake/Plate headers allow "MOBA Unit"). 101 lines (2.4%) disagree: OPD header with MOBA 59, OPD with MOBA Punching 34, PCU with MOBA Punching 4, MOBA-Punching header with MacPro 2 / MOBA 2. OPD header splits PackPro 1,451 / MacPro 462 / MOBA 59 / MOBA Punching 34 / no tag 23. Header is a bucket for OPD only; MOBA paper-cup family has four header values but one line tag (MOBA Unit). 
**333 untagged lines [M]:** RWU 215, PSU 88, OPD 23, PCU 5, SHPS 2. 310 (93%) are resolved exactly by the header (unique mapping); only the 23 OPD lines are ambiguous, by month 0-5 lines.
**Live SOs 16 Sep-8 Oct [M]:** 266 SOs, none has two different line tags; header always set; 17 RWU lines untagged (same pattern as before).

**History (A3) [M, limited]:** The Zoho comments feed (`/salesorders/{id}/comments`) for a stratified sample of 44 SOs (4 per header division, various months) holds only system lines (598 of 598): package/pick list/invoice events and "Sales Order updated." It does **not** record which field changed or its old/new value, so I cannot say who set the division field or when it was changed. What it does show: creator is recorded on every SO and maps cleanly to division (all 266 recent SOs + 44 sample, 309 detail pulls): Nimesha Lakmali 145 (OPD 87, PCU 25, MOBA Punching 11, CPU 8, Cake 4, Plate 4); Madushi Hansika 67 (SHPS 64, DPU 3); Umanda Sathsarani 61 (PSU 43, RWU 18); Nirmani Vishmi 34 (CPU 28, Lid 3, FPP 3); Ikram 1; shared login "Packpro" 1. 42 of 44 sampled SOs show later activity (packages, cancellation, template changes), but only 6 of 44 carry a generic "Sales Order updated." line; 4 with amount changes. No sampled SO shows evidence of the division being re-set after creation, but the feed cannot prove it either way. Surprise vs spec 5.3: Nirmani creates mainly CPU (28 of 34), not FPP; Nimesha also creates PCU (cups).

**Item master as predictor (A4) [M]:** `cf_bu` predicts the header division 96.6% of lines but the line tag only 92.5%. It cannot split PackPro/MacPro: PACPRO items are tagged PackPro 1,448 / MacPro 279 (84% / 16%); items with `cf_bu`=OPD go to MacPro 159 of 161 (99%). 149 of 675 OPD items appear under both tags, so MacPro vs PackPro is chosen per order, not per item. Item master is therefore a good fallback hint, not the primary key.

**Recommended rule [M numbers above]**
1. Line reporting tag `Division` (present on 92.7%), mapped through the alias table (add MacPro, Digital Printing). 
2. Else header `cf_manufacturing_division` when it maps to exactly one unit (resolves 310 of 333 untagged lines, i.e. 93%; RWU and PSU live here, so the header fallback must stay).
3. Else (OPD header, no tag; 23 lines in 12 months, ~2 per month) suggest the item's `cf_bu` (OPD-> MacPro, PACPRO -> PackPro; 17 and 6 lines) but put the job on the Unassigned list for a manager to confirm. 
4. Flag (do not auto-resolve) the 2.4% header-vs-line disagreements, mostly OPD header with MOBA/Punching tag; follow the line, show a "check" chip. Creator name is a useful tie-break for which coordinator (not manager) owns the job.
Unassigned expected: about 23 / 4,559 lines = 0.5%.

## Part B - API calls per day if "always in sync" [measured volumes, modelled calls]
Window 8 Oct 2025 - 7 Oct 2026 (Colombo times), `daily_counts.csv`. Per day, median / p95 / max [M]: SOs created 10/23/33; packages created 162/317/534 (54,989 in a year); shipments 18/30/49; invoices 19/36/66; pick lists 17/30/43; SOs "modified" 0/23/2,645. The modified series is a **lower bound**: Zoho keeps only the last modification time, and it has 4 bulk-edit days (5 May 2,645 SOs, 7 May 1,644, 16 May 821, 4 May 457; bulk edits at 00:00 / 21:00). Max SO changes in any 5-minute window 337 (15 windows over 200, so 2 list pages).
Model [E]: calls/day = list polls (x2 if the bundles delta is also polled, as spec 5.2 requires) + detail calls + 43 pages for the nightly full header read (8,571 SOs / 200). Detail calls = distinct (SO, interval) with a create/modify/package/shipment/invoice/picklist event. Variant A = additionally one call per package/shipment/invoice (owner's wording); variant B = SO detail only (what the spec does; the SO detail already carries packages/shipments/invoices). Budget = 7,500 - 500 = **7,000/day**.
| Poll | SO list only, A: median / p95 / max | SO list + bundles, B: median / p95 / max | SO list + bundles, A: median / p95 / max |
|---|---|---|---|
| 5 min | 645 / 890 / 3,476 | 728 / 794 / 3,423 | 933 / 1,178 / 3,764 |
| 2 min | 1,106 / 1,377 / 3,956 | 1,621 / 1,720 / 4,335 | 1,826 / 2,097 / 4,676 |
| 1 min | 1,864 / 2,179 / 4,741 | 3,099 / 3,246 / 5,840 | 3,304 / 3,619 / 6,181 |
Busiest 10 days (5 min, SO+bundles, B): 5 May 3,423; 7 May 2,383; 16 May 1,567; 4 May 1,225; 22 Jul 1,094; 12 May 1,020; 2 Sep 1,006; 8 May 1,002; 13 May 989; 3 Aug 981. Others in `modelB.json`.
No scenario exceeds 7,000 on any day (days over: 0 for all 12). Hybrid (fast 06-20h, hourly at night) 5 min: median 508, max 3,203; 2 min 1,041 / 3,755; 1 min 1,918 / 4,660. Spec as written (15-min day slots, hourly night, 340-400/day) [spec figures, not re-measured]. Stress check [E]: if real modifications were 3x what I can see, 5-min polling would still be about 0.7-1.3k/day typical.
**Safe interval:** 5 min is clearly safe (median ~0.7k, 10%); 2 min is safe (~1.6k median, 4.3k worst); 1 min is technically under the cap (3.1k median, 5.8k worst, 83% of budget on the worst day) but leaves no room for retries, history backfill or a bulk-edit day. Recommend 5 min by day (2 min possible), hourly at night, and a bulk-edit guard (cap detail calls per cycle; a 2,645-SO day is the real risk, not the polling interval).

## Part C - what each item goes through
Basis: 1,450 items sold in the 12 months [M], item master + BOMs + bundles of the 19 Sep export (`/root/exports/zoho/native/2026-09-19/sps/`, bundles to 18 Sep). `routes.csv`: one row per item (route, SOs, line tags, header divisions, crosses-units flag, bundles, bundle makers, adjustment lines).
- **Type [M]:** 1,442 (99.4%) are Zoho composite items, type "assembly" (no "bundle" type used); 8 plain inventory items. Item master carries `cf_bu` (18 values), `cf_fg_sub_category`, `cf_parent_category`, `cf_fg_nature`; BOMs list component items with labour/electricity as service lines.
- **Route = unit of each nested sub-assembly (BOM) then the item's own unit.** 27 distinct routes. Single-unit: PackPro 530 items, SHPS 453, MOBA-Cup 145, OPD 112, MOBA-Punch 57, CPU 21, FPP 11, RWU 8, PSU 7, others. Cross-unit [M]: 87 items (6.0%), 218 of 4,559 order lines (4.8%): PackPro>CPU 32, OPD>CPU 16, MOBA-Cup>MOBA 12, SHPS>PackPro 9, MOBA-Cup>PCU 5, PackPro>RWU 3, PackPro>SHPS 3, OPD>SHPS 3, MOBA-Cup>SHPS>OPD 2.
- **Actual bundling [M]:** 3,360 SOs have bundles, 1,367 of the sold items were bundled at least once. Only 48 SOs (1.4%) bundle more than one composite item; typical hand-offs: Madushi (screen printing "PRINTSERV-Sub" item) then Umanda (bag making) 28, Madushi then Nimesha 9, Umanda then Nimesha ("PACKSERV") 3. Bundle recorder = coordinator of the unit; shared logins "Packpro"/"MacPro" appear.
- **Adjustments/transfers carry no route [M]:** 2,910 adjustments in 12 months are 78% "Damaged goods", Stocktaking, Packaging reinstatement (no "Product Conversion" in SPS); only 47 transfer orders, all RM/FG <-> WIP; purchase receives hold no item lines in my pull.
- **Predictable from item master? Yes, mostly:** `cf_bu` plus BOM nesting gives the expected route for all 1,450 items with no manual input; the cross-unit set (87 items) can be pre-filled as "Send next". Not predicted: PackPro vs MacPro (per order) and extra steps added at order time.
- **Not done:** the item-level history/comments page (who edited the item master and when) was not opened; items.json only gives created/last-modified times, no user.
