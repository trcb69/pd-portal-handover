# Item kinds and flows: research for the joint Order Portal + Production Dashboard demo (21 Oct 2026)

Prepared by Abdul Hadhee | IT Executive. Research only; no Zoho call was made. Scripts: `/root/.claude/jobs/61c1b69c/tmp/research/` (`a3.py` classifies SH lines, `b1.py` counts SPS job orders). No payables, overdues or payment status appear here.

## 0. Short answer

1. The three-kind hypothesis holds, but the kinds are very unequal. In the 19 Sep to 17 Oct SH order lines (7,923 lines, 2,617 SOs), **about 69% of lines are traded goods** (about 64% of lines if you look only at the Packaging business unit), **about 12 to 17% are customized**, and **about 8% are standard goods that SPS makes**. Customized is the smallest of the three by lines but the only one that needs the production dashboard end to end.
2. On the SPS side (8,571 most recently touched job orders) **68% are "Customized Order"**, **25% "Ex Stock"**, **6% "Internal SH Order"** and 0.4% "Make to Order". So SPS production is mostly customized work, and "Ex Stock" is mostly straws (PSU) and cling-film rolls (RWU).
3. Easiest demo that is still real: **one customized order walked from the portal to the dashboard to dispatch (main path)**, one **standard "Ex Stock" order shown as a branch** (it skips the portal's production queue and the dashboard job), and one **traded order shown as a branch** (stock check only, no production). Do not build separate flows for traded goods in the first demo.

---

## A. How SH sales order lines split across the three kinds

### A.1 Source and method

- Lines: `/root/exports/zoho/native/2026-10-18/sh/SH_Sales_Order_2026-09-19_2026-10-18.xlsx`, sheet "Sales Order", 7,923 lines, 2,617 distinct `SalesOrder Number` (column D), 1,657 distinct `Product ID` (column X). Status mix (column E): invoiced 5,411, partially_invoiced 1,914, confirmed 437, draft 126, void 35 lines. I kept draft and void lines in all counts below (they are 161 lines, 2%).
- Each line was joined on `Product ID` to the SH item master `/root/exports/zoho/native/2026-09-19/sh/items_all.json` (12,006 items). 100 lines (85 items) have no master row because the item was created after 19 Sep: reported as "not matched".
- Item kind rules, applied in this order (the first that fires wins):

| Rule | Field and value | Kind |
|---|---|---|
| 1 | `cf_division` = SD (chemicals) | Traded (chemicals), shown apart |
| 2 | `cf_sub_category` or `cf_parent_category` contains "Customized" (OPD / SHP / PCU Customized) | **Customized** (firm) |
| 3 | Name (normalised, with or without SP-/CP- prefix) equals an SPS item with `cf_fg_type` = Customized (`/root/exports/zoho/native/2026-09-19/sps/items.json`) | **Customized (grey)**, see A.4 |
| 4 | `cf_division` in SERVICE, CONSUMPTION, COMMON, FINANCE, DISPOSABLE ASSETS, or `product_type` = service | Service / not stock |
| 5 | `cf_division` = GD | Traded (other division, general) |
| 6 | `packaging_group` from `/root/Project Management/reports/2026-09-27-sps-sh-inventory-analysis/item-classification/classification.csv`: "SPS-made (bought from SPS)" | **Standard SPS-made** |
| 7 | same file: "Both SPS and outside supplier" | Standard, also bought outside (counted with SPS-made) |
| 8 | same file: "Outside supplier" | **Traded** |
| 9 | same file: "Unknown source" (no PO or SPS-bill history) | Unknown (mostly traded by `cf_operation_nature` = General Trading / Ex-Stock) |

The classification file's own rules (vendor history from the 8,402 PO lines plus 12,320 SPS-internal bill lines) are in `item-classification/NOTES.md`. SPS-made = the item was only ever bought from the vendor "Smart Pack Internal Purchase".

### A.2 Result (all lines)

| Kind | Lines | % of lines | Distinct items | Distinct SOs | Item Total (LKR, column AX "Item Total") | % of total |
|---|---|---|---|---|---|---|
| Traded (outside supplier 3,952 + SD chemicals 1,384 + GD 127 + raw material sold to SPS 17) | 5,480 | 69.2% | 1,088 | 2,173 | 42.55 M | 62.6% |
| Customized (firm 927 + grey 419) | 1,346 | 17.0% | 292 | 732 | 9.37 M | 13.8% |
| Standard SPS-made (SPS-only 134 + both 490) | 624 | 7.9% | 64 | 512 | 8.91 M | 13.1% |
| Unknown source (mostly General Trading / Ex-Stock) | 264 | 3.3% | 112 | 106 | 6.67 M | 9.8% |
| Service / not stock | 109 | 1.4% | 16 | 53 | 0.18 M | 0.3% |
| Not matched to the item master | 100 | 1.3% | 85 | 40 | 0.33 M | 0.5% |
| **Total** | **7,923** | 100% | 1,657 | 2,617 | 68.01 M | |

Sub-rows behind it: customized firm 927 lines / 268 items / 7.81 M; customized grey 419 lines / 24 items / 1.56 M; outside supplier 3,952 lines / 444 items / 37.18 M; chemicals 1,384 lines / 591 items / 0.21 M; "both" 490 lines / 24 items / 7.06 M; SPS-only 134 lines / 40 items / 1.85 M.

### A.3 Result (Packaging business unit only)

Filter: column `CF.Business Unit` = Packaging (6,071 lines, total 60.32 M). This removes chemicals (Specialities, 1,420 lines) and most of General.

| Kind | Lines | % | Items | SOs | Value % |
|---|---|---|---|---|---|
| Traded | 3,876 | 63.8% | 512 | 1,401 | 59.1% |
| Customized | 1,232 | 20.3% | 248 | 680 | 14.5% |
| Standard SPS-made | 618 | 10.2% | 64 | 508 | 14.7% |
| Unknown | 252 | 4.2% | 100 | 102 | 11.0% |
| Service | 70 | 1.2% | 13 | 39 | 0.3% |
| Not matched | 23 | 0.4% | 20 | 19 | 0.4% |

A mixed SO is normal: of 2,617 SOs, 1,431 are traded-only, 202 customized-only, 110 standard-only, and 317 carry customized plus traded lines (`a5.py` output). So the portal's "stock or production" decision is per line in practice, even though the spec decides it per order (spec §2 row A1).

### A.4 How confident is the split

| Point | Confidence | Why |
|---|---|---|
| Customized (firm) = 927 lines | High | 900 of 927 lines also have `cf_operation_nature` = Manufactured; 296 carry SP-, 69 CP-, 121 SH-, 31 FP- prefixes and 409 no prefix (so the prefix is not a safe test; open question OQ7 in the order-portal spec §20). 443 of the 927 match an SPS item with `cf_fg_type` = Customized by name, 319 match a "Non Customized" SPS item, 150 have no name match. So the SH tag and the SPS tag disagree on about 1 in 3 lines. |
| Customized (grey) = 419 lines | Low | 24 items that SPS tags Customized but SH treats as `cf_operation_nature` = General Trading (414 of 419). Examples: "Lid For 450ml AF Container - 8342" (111 lines, value near 4,000), "8oz Kraft Double Wall Cup" (34 lines). These look like standard products with a wrong SPS type. I count them as Customized in the table only to give a maximum; the minimum is 927 lines (11.7%). |
| Standard SPS-made | Medium | Evidence is the vendor "Smart Pack Internal Purchase" on SPS-internal bills. Bill lines were pulled only for SPS bills, so outside-vendor evidence is PO lines only (`NOTES.md`). 1,879 SH items (15.6%) have no source history at all ("Unknown source"). |
| Traded | High for the 444 outside-supplier items; Medium for the Unknown group | Items such as Wooden Spoon 16cm (261 lines), Aluminium Lava Cake Cup (192), 450ml AF Container (112), Chefs Choice BP 45cm x 100m (76) are bought from outside vendors. |
| The "both" group (490 lines) | Medium | Items such as Paper White Straw 6mm x 20cm (Packed) (128 lines), Chefs Choice Cling Film (112), ST-Cling Film (89) are made by SPS (PSU, RWU) but also bought from outside suppliers at times (e.g. "Paper White Straw 6mm Imported" appears in `routes.csv` row 5). |
| Value shares | Low | 3,041 of 7,923 lines (38%) have `Item Total` = 0 (traded 2,142; customized 612 of 1,346; standard 89). Many are lids, samples or no-charge lines. Use line and item counts, not value, in any claim. |

### A.5 Other cuts that help the demo

- **Where lines are picked from** (`Line Item Location Name`, column AM): SPS Kohalwila Factory (Warehouse) 4,171 (53%), Southern Warehouse 1,967, SH Ranaviru Warehouse 1,302, Central Warehouse 345, Freeport 132. Customized lines: Kohalwila 638, Southern 253, Central 34. So customized stock is mostly but not only at Kohalwila (69%); the South picks 27% directly (the "Galle supplied by transfer" statement in `/root/CLAUDE.md` 17 Oct is not the whole picture; lines still pick from the Southern warehouse).
- **Order pick type** (`CF.Order Pick Type`, column CP): customized lines are Bulk 928, Retail 336, MTO 75, Key Customer 7. Only 235 lines in all are MTO.
- **Sales people on customized lines**: Safraz Jiffry 366, Nimal Devaraj 142, Maradana Retail Chain 109, Adnan Iqbal 74, Thariq Safraz 59 (column BI "Sales Person"). Matches the catalogue sheets (`SPS-Customized-Items-Catalogue-2026-10-18.xlsx`: Maradana Retail Chain 351 items, Safraz Jiffry 319, Nimal Devaraj 315, Thariq Safraz 186).
- **Catalogue** (`README.md` in `/root/Project Management/reports/2026-10-18-customized-catalogue/`): 2,708 SPS items with `cf_fg_type` = Customized; 2,179 are composite (have a recipe), 529 are not (these include 204 PRINTSERV-/service lines). Prefix counts of those 2,708 names: SP- 1,161, CP- 630, PRINTSERV 204, SH- 41, none 638. 1,104 have no sales person assigned.
- **SPS item master** (`sps/items.json`, 3,928 items): `cf_fg_type` Customized 2,708, Non Customized 304, NA 901 (raw material, services), blank 15.
- **SH item master** (12,006 items): `cf_operation_nature` Ex-Stock 5,368, Manufactured 3,424, General Trading 1,876; `cf_sub_category` OPD Customized 1,693, SHP Customized 1,324, PCU Customized 212. In SH, "Manufactured" = SPS-made customized, "General Trading" = bought in (from SPS or elsewhere), and standard SPS-made items are mostly tagged General Trading (104 of 134 lines), so **SH's own tag cannot separate standard-from-SPS from traded**; only the vendor history can.

---

## B. SPS job orders by order type and division

### B.1 Source and filter

Source: `/root/Project Management/reports/2026-10-08-pd-zoho-study/pulls/so_modified_p*.json` (43 pages), `so_created_p*.json` (19 pages) and `v8/list.json`, field `cf_order_type` and `cf_manufacturing_division` on the SO header. I walked every JSON object that has `salesorder_number` and de-duplicated by that number: **8,571 distinct SPS job orders** (the raw files repeat records; 8,571 is after dedup). These are the most recently modified SOs at 8 Oct, so they are not the whole register: order dates run 2023-03-18 to a future due date 2026-10-28 (2023: 4, 2024: 2,414, 2025: 3,484, 2026: 2,669). Statuses: shipped 3,988, fulfilled 2,690, partially_shipped 1,096, confirmed 797.

### B.2 Per order type

| Order type | All 8,571 | Last 12 months (9 Oct 2025 to 8 Oct 2026, 3,442) | Last 3 months (1 Jul to 8 Oct 2026, 1,047) |
|---|---|---|---|
| Customized Order | 5,856 (68.3%) | 2,478 (72.0%) | 768 (73.4%) |
| Ex Stock | 2,173 (25.4%) | 570 (16.6%) | 179 (17.1%) |
| Internal SH Order | 504 (5.9%) | 387 (11.2%) | 99 (9.5%) |
| Make to Order (MTO) | 38 (0.4%) | 7 (0.2%) | 1 (0.1%) |

(The 12-month and 3-month columns use `date` of each SO; two future-dated SOs fall outside, so the totals are 8,569 for the all-dates check.) `cf_order_type` is filled on every record (0 blank).

### B.3 Per division and order type (all 8,571)

| Division (`cf_manufacturing_division`) | Total | Customized | Ex Stock | Internal SH | MTO |
|---|---|---|---|---|---|
| Offset Printing Division (OPD) | 3,887 | 2,772 | 732 | 352 | 31 |
| Screen Printing Division (SHPS) | 2,378 | 2,378 | 0 | 0 | 0 |
| Paper Straw Unit (PSU) | 778 | 0 | 775 | 3 | 0 |
| Rewinding Unit (RWU) | 566 | 0 | 565 | 1 | 0 |
| Paper Cup Unit (PCU) | 506 | 416 | 15 | 75 | 0 |
| Customized Packing Unit (CPU) | 188 | 148 | 1 | 39 | 0 |
| MOBA Punching Unit | 105 | 105 | 0 | 0 | 0 |
| Paper Cup Lid Unit | 81 | 2 | 55 | 23 | 1 |
| Food Product Processing (FPP) | 44 | 13 | 25 | 0 | 6 |
| Digital Printing Unit (DPU) | 22 | 22 | 0 | 0 | 0 |
| Paper Plate Unit | 9 | 0 | 2 | 7 | 0 |
| Cake Wrapper Unit | 7 | 0 | 3 | 4 | 0 |

Reading: **SHPS (screen printing) is 100% customized; PSU and RWU are 99.7% Ex Stock**; OPD is the mixed one (71% customized, 19% ex stock, 9% internal). Cups, lids, plates and wrappers are small-volume "Internal SH Order" and "Ex Stock". My reading of "Internal SH Order" (SH's own use or SH-internal stock build) is **not verified**: no file defines the value. The 21 Oct demo spec lists MOBA and cup units under pairs but does not define order types either.

Note the "Ex Stock" meaning at SPS (the job is a make-for-stock run that SH then buys into stock) fits the data (PSU 775 of 778), but the SPS job order carries no SH SO link for it; the SH side sees it only as a bill from "Smart Pack Internal Purchase" (`work/scout-sh.md:176`).

---

## C. End-to-end flow per kind, as it works today

Evidence for each step is in the file named in the last column. Zoho documents are in **bold**.

### C.1 Kind 1: customized item (SH customer -> SPS makes -> SH delivers)

| # | Step | System and document | Who | Source |
|---|---|---|---|---|
| 1 | Sales person posts the request in the "SH MANUFACTURING ORDER REQUEST" group; stock vs production is not recorded | WhatsApp / ClickUp | Sales, Rizwan's team | `/root/CLAUDE.md` 17 Oct row; spec `wiki/specs/2026-10-18-order-portal-spec.md:56-62` |
| 2 | Production manager adds it to a job; coordinator retypes it as an SPS **sales order = job order** (`JOBORDER-nnnnn`, Job No = a Zoho **project**, 11 header custom fields, one line per job) | SPS Zoho | Coordinator | spec §0 F1 to F7 (lines 40-54) |
| 3 | SPS Work-in-Progress stock is fed: Stores issues material with an **RM Issue Note (transfer order RMTO-)**, linked to the job order | SPS Zoho | Stores | `/root/Project Management/reports/2026-10-20-new-production-flows/build/report.html` (step 4) |
| 4 | Units make it in a route (e.g. MacPro -> Stripping -> PacPro). Paper forms: line clearance, requisition, inline inspection. **SmarTAG** (TAGTrace#) label per pack | Paper + SPS Zoho | Operators, QC, Operation team | same report, steps 1 to 6 |
| 5 | Stores checks finished goods: **Standardization Checklist (FG QC # SPSSHP-)** | SPS Zoho | Stores | same, step 7 |
| 6 | SPS raises the **Internal Sale Invoice SPS -> SH**; SH records it as a **bill from "Smart Pack Internal Purchase"** (no PO, no receive; 12,147 such bills) | SPS + SH Zoho | SPS billing, SH | same, step 8; `work/scout-sh.md:176` |
| 7 | SH sales order is raised in SH Zoho (`HTXSO`, `HNTSO`, `ATXSO`...), **picklist** completed 7 min after the SO, **package** with QC fields 1.7 h later, **shipment** ("shipped" = packed, median 6 min after packing) with route and carton count | SH Zoho | Order desk, Stores, dispatch clerk | `/root/Project Management/reports/2026-10-18-shipment-to-gatepass-flow/KOHALWILA-SHIPMENT-TO-GATEPASS-FLOW.md` §2 steps 2 to 5 |
| 8 | **Invoice** to the SH customer 28 min after "shipped" | SH Zoho | Billing | same, step 6 |
| 9 | Gate pass = a ClickUp trip task (median 23 h after "shipped"); guard check not recorded; delivery closed "in one sitting" 68 h after "shipped" | ClickUp | Logistics planner, "Delivery" login | same, steps 7 to 10 |
| 10 | Branch supply: **transfer order** Kohalwila -> Southern / Central (2,680 and 662 of 4,903 transfers) | SH Zoho | Branch staff | `/root/Project Management/reports/2026-09-25-sh-inventory-plan/data/facts.txt` ("TRANSFERS 4903 ... routes") |

**Key gap in the data:** the SH SO line and the SPS job order are linked only by people and by the free-text SPS field "Order Received from" and the job number. I found no stored key from SH SO to SPS job order on disk. That link is exactly what the portal would create (field `cf_portal_ref`, spec G1 step 6).

### C.2 Kind 2: standard manufactured item (SPS makes for stock, SH sells ex-stock)

| # | Step | Document | Source |
|---|---|---|---|
| 1 | SPS raises a job order with `cf_order_type` = Ex Stock for a unit like PSU or RWU (straws: 126 SOs, 140 lines in the study window; cling film 85 and 77 SOs) | SPS **sales order** | `2026-10-08-pd-zoho-study/routes.csv` rows 2 to 5 |
| 2 | Production: PSU makes, dries (up to 2 days), counts, wraps; RWU rewinds. Material comes straight from Stores. Recorded as **bundle (assembly)**: 129 bundles for Paper White Straw 6mm x 20cm (Packed) | SPS **bundle** | `routes.csv`; `new-production-flows/build/report.html` |
| 3 | Finished goods to SH: Internal Sale Invoice / SH bill from "Smart Pack Internal Purchase", stock lands in SH Kohalwila | SPS invoice, SH **bill** | `work/scout-sh.md:176` |
| 4 | SH sells from stock: SO, picklist, package, shipment, invoice, gate pass, as C.1 steps 7 to 9 | SH documents | Kohalwila flow |
| 5 | Replenishment today is by hand; the planned reorder screen decides **MAKE** (internal request to SPS manufacturing) vs BUY by item | PDF per decision | `/root/Project Management/reports/2026-10-02-reorder/REQ-reorder-screen-and-pdf.md` |

### C.3 Kind 3: traded item (SH buys bulk import or local, resells)

| # | Step | Document | Source |
|---|---|---|---|
| 1 | Reorder decision (RED / YELLOW / GREY signs); Abdullah approves; a PDF per supplier goes to purchasing | PDF | `REQ-reorder-screen-and-pdf.md` decisions |
| 2 | Purchasing raises the Zoho **purchase order** (COO approval in Zoho); imports add import-charge-only POs (customs, freight): in Sep 2026, 380 POs = 130 goods, 38 import-charge-only, 212 service/consumption | SH **PO** | `/root/Project Management/reports/2026-09-monthly-report/README.md` |
| 3 | Goods arrive: **purchase receive (GRN)**, then **bill** ("Pending Bill" is a real state: 14 GRNs to sign on 1 Oct) | SH **receive**, **bill** | `/root/CLAUDE.md` (1 Oct report line); monthly report |
| 4 | Lead times: local median 8 days (p80 21, n = 2,542), import median 37 days (p80 69, n = 707); 8,402 POs / 23,721 lines, 3,185 distinct items, 825 vendors | -- | `2026-09-25-sh-inventory-plan/data/facts.txt` ("SUPPLIER LEAD TIME" block) |
| 5 | Sale from stock to customer, then C.1 steps 7 to 10 (SO, picklist, package, shipment, invoice, gate pass, transfer to branch) | SH documents | Kohalwila flow |
| 6 | Known mess: 1,876 posted "Product Conversion" adjustments; 11,556 SOs stuck at "shipped" | -- | `facts.txt` ("RECHECK" block) |

### C.4 What is the same for all three

Steps 7 to 10 of C.1 (SO -> picklist -> package -> shipment -> invoice -> gate pass -> delivered, plus branch transfer) are identical for every item. That block is the only part of the flow common to all three kinds, and it is already documented by the 18 Oct work.

---

## D. Where the Order Portal design stands

**Spec**: `/root/Project Management/wiki/specs/2026-10-18-order-portal-spec.md`, Rev 3.2, closing line "VERDICT: READY" for S0 and S1 (line 990). Rev 3.2 followed plan-critic round 4 (change log, lines 6-34). Dev repo `/root/dev/order-portal` and service port 4800 are named but **do not exist yet** (line 6, 7 of the spec).

**Round-1 BLOCK B1 to B4**: I could not find the round-1 critic file. There is no critic file next to the spec (`ls wiki/specs | grep -i portal` returns only the spec), and the spec's change log says only "round-1 BLOCK fixes B1-B4, N1-N12" (line 35). **I cannot summarise B1 to B4 individually; unverified.** What I can say is that Rev 2 to Rev 3.2 record fixes for critic rounds 2 to 4: status rule and `so_confirm` (R1), project create keyed by name (R2), customer placeholder (R3), `cf_portal_ref` mirror (R4), request ids (R5), one write per line (F1), write ledger, reconciliation every 5 min, and the `restore_pending` toggle.

**Design in one table**

| Item | State |
|---|---|
| Flow | Salesperson -> Rizwan's team decides stock / production / send back per order -> production accepts -> manager approves with a Job No -> portal POSTs one SPS job order per line -> dashboard sync picks it up (spec §4.1, lines 151-170) |
| Reads | SPS by API every 5 min (7,500 calls/day; dashboard cap to be set <= 4,500); SH by signed-in browser, swappable (spec §8) |
| Writes | SPS job order only in the first slice; items, customers and images are later slices S3 to S5; weekly report S6 |
| Slices | S0 foundation, S1 trial core (no blocker for building); S1b project create waits on V3; S2 SH reader (stock) waits on OQ5, OQ20, V9 to V12 |
| Pre-trial gates | G1 Zoho self client and `Portal Ref` field (the user), G2 read-only checks V1 to V13, G3 live TEST job order (spec lines 809-843) |
| Open for the trial | OQ6, OQ10, OQ11, OQ13, OQ21, OQ22, OQ24 (line 990) |
| Not decided | OQ7 what SP- / CP- mean (`catalogue` names show 1,161 SP, 630 CP, so no rule is derivable from names alone) |

**Demo already built** (`/root/Project Management/reports/2026-10-18-customized-catalogue/portal-demo/Customized-Order-Portal-Demo.html`, 2.0 MB, `PLAN.md`): type-ahead item then customer, pre-fill of quantity, price, job nature, artwork / dye cutter / screen from the last order, variant cards, "Add line", "Send to production", a production manager screen with the exact Zoho payload and "Create SO in Zoho", plus new-customer and new-item request flows. It uses local data to 16 Sep and real prices, is internal and not published. It does **not** include Rizwan's team stock/production decision (spec §0 of CLAUDE.md row: "the 18 Oct demo skips this step") and has no stock figures.

---

## E. Where the Production Dashboard stands (touch points only)

Source: `/root/Project Management/.claude/worktrees/pd-demo-plan/wiki/specs/2026-10-21-pd-demo-release.md` §0 to §3.

- The demo is the managers' view of **open SPS job orders**: "My jobs", a strip that ticks from Zoho (job order, **Packed (SmarTAG)** = package, **Checked (Standardization)** = shipment, **Invoiced (to SH)**) and ready-to-run chips from three SO header fields (artwork, die cutter, screen/plate; spec §3.3). The only hand tick kept is **Job card**; **Send next** hands the job to the next unit (spec §0, §1). Zoho stays read-only.
- Touch point 1, order -> job: the dashboard syncs SPS sales orders every minute (spec §1 diagram). A portal-created job order appears there once it exists in SPS Zoho; **status matters** because the dashboard hides drafts (order-portal spec F6, citing `job-queries.js:18`). So the portal's `so_confirm` step is on the demo's critical path.
- Touch point 2, job -> stock -> dispatch: the dashboard ends at "shipped + invoiced in full" (spec §1). It does not show the SH side (SH SO, picklist, gate pass). The jump from "Invoiced (to SH)" to SH stock to SH dispatch is a **gap**; today it is the Internal Sale Invoice / SH bill step, with no key between the two organisations.
- Units in the demo: STRIP added as a new unit, PCU kept, MacPro prefixed on offset routes (spec §3.1, §3.2).

---

## F. Recommendation: the easiest demo that still shows the real business

### F.1 Scope decision

| Question | Recommendation | Reason |
|---|---|---|
| Customized packaging unit only, or whole production, or the traded part? | **Show all three kinds, but build the full path only for customized.** Treat standard and traded as branches that end at the same dispatch block. | Customized is 68% of SPS job orders and 12 to 17% of SH lines; it is the only kind that needs the portal's production queue and a dashboard job. Standard Ex Stock is 25% of SPS jobs (almost all PSU / RWU) and traded is 64 to 69% of SH lines, but neither needs a person to approve a recipe or a Job No. |
| Units | **OPD (MacPro -> PackPro)** for the main path; **PSU** for the standard branch; **SHPS (screen printing)** only if there is time. | OPD holds 3,887 of 8,571 job orders (45%); the route MacPro -> PackPro is in the spec's defaults (spec §3.2). PSU is 775 of 778 Ex Stock. SHPS is 100% customized but a second route to build. |
| Locations | **SH Kohalwila (Head Office, location "SPS Kohalwila Factory (Warehouse)") as the only picking location**; South and Central shown as one line "branch transfer" on the walk-through. | 53% of all lines and 69% of customized lines pick at Kohalwila; the spec's stock reader (S2) targets Kohalwila. |
| Sales people | One real salesperson with customized items, e.g. Safraz Jiffry (366 customized lines). | Strong mapping in the catalogue. |

### F.2 One sample order of each kind (real items; check the quantities live before the demo)

| Kind | Sample | What the screen walks through |
|---|---|---|
| Customized | `SP-Kraft Paper Bag with Rope Handle 32x25x11cm (Bayside Breeze)` (catalogue, Division OPD, FG PACPRO, last ordered 2026-03-12, median qty 275, 2 lines all-time) or any of the 927 firm lines with an OPD customer | Portal: sales line pre-filled -> Rizwan's team picks Production -> manager picks Job No and approves -> job order created (use the fake Zoho or the one TEST job order of gate G3) -> Dashboard: job appears at MacPro, strip chips (artwork / die cutter) -> Send next to PackPro -> Packed (SmarTAG) -> Checked -> Invoiced (to SH) -> SH dispatch block (SO, picklist, package, shipment, gate pass) |
| Standard (Ex Stock) | `Paper White Straw 6mm x 20cm (Packed)` (PSU, 126 SOs / 140 lines in `routes.csv`, 128 SH lines in the SH export) | Portal: Rizwan's team sees stock "as of HH:MM" at Kohalwila; if enough, picks Stock and the order ends there (no production). If short, an **Ex Stock job order** is created by planning, not by a salesperson, and shows on the dashboard at PSU. Branch only. |
| Traded | `Wooden Spoon 16cm` (outside supplier, 261 SH lines, 2,425 outside-supplier lines picked at Kohalwila) | Portal: stock check only, decision = Stock. If short: show the reorder sign (RED / YELLOW) and "PDF to purchasing" from `REQ-reorder-screen-and-pdf.md`, ending at "PO raised by purchasing". No production, no dashboard. |

### F.3 What each system reads and writes in the demo

| System | Reads | Writes |
|---|---|---|
| Order Portal | SPS items and last orders (API, 5 min); SH stock at Kohalwila (browser pull; or a saved snapshot labelled with its time); SPS job-order custom field options | One SPS job order (plus project) per customized line, via the fake Zoho or one TEST job order; its own database for orders, decisions and events |
| Production Dashboard | SPS job orders, packages, shipments, invoices (read-only sync, 1 min) | Its own database only: Job card tick, Send next events. Nothing to Zoho |
| Reorder screen (traded branch) | SH items, POs, stock | A PDF only |

### F.4 What can stay manual or paper for the demo

- SH SO, picklist, package, shipment, invoice and the ClickUp gate pass (C.1 steps 7 to 9): show as a slide or the existing flow diagram (`2026-10-18-shipment-to-gatepass-flow/out/Kohalwila-Dispatch-Flow.pdf`), not as a screen. The common block is the same for all three kinds.
- New item, new customer, image upload, weekly report (slices S3 to S6): skip.
- Paper forms (line clearance, requisition, inline inspection, waste note): skip, as `new-production-flows/build/report.html` already suggests.
- Branch transfer orders: one line on a slide.
- Rizwan's team decision on stock vs production: build it (it is the one new decision the portal adds), but with a shared login and the stock figure possibly from a snapshot.

### F.5 Data gaps and things I could not verify

1. Round-1 critic findings B1 to B4 of the order-portal spec: no file on disk.
2. The meaning of `cf_order_type` = "Internal SH Order" (504 SOs) and "Make to Order (MTO)": inferred only.
3. The SPS "Ex Stock" job to SH stock link: no key exists; SH sees a bill with no item-level data (`stock_docs_bills.json` has no item rows).
4. 15.6% of SH items (1,879) have no purchase source history: the traded/standard line between them is unknown. Their lines (264, 3.3%) are put in "Unknown".
5. 38% of SH lines have a zero `Item Total`: value shares are weak.
6. The SPS job-order population is the 8,571 most recently modified, not all; the 12-month slice is 3,442, the 3-month 1,047.
7. SH and SPS item tags disagree on about a third of customized lines (443 / 319 / 150 split in A.4).
8. Customer-level and location-level splits of SPS jobs are not available (the SO has Standard Holdings as customer; the real customer is the free-text "Order Received from").
9. Imports vs local PO split for Kohalwila in the traded branch: I used the lead-time counts (local n = 2,542, import n = 707 in `facts.txt`) and did not recount the September POs by currency.
10. Nothing here used live Zoho; all files were 19 Sep to 18 Oct snapshots, so item and stock figures must be re-read before a live demo.
