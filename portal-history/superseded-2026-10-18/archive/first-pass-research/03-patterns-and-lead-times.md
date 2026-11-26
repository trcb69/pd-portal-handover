# 03 - Order patterns and lead times (SPS customized orders)

Prepared by Abdul Hadhee | IT Executive. All numbers come from `scripts/patterns.py` and `scripts/lt_extra.py` (run 17 Oct 2026); full output in `data/results.json`. Read-only on `/root/exports`. SH and SPS numbers are never summed: everything here is SPS (SmartPack) Zoho.

## 1. Headlines (what the portal designer needs)

| Question | Answer | Source |
|---|---|---|
| Customized-order volume, last 12 full months (Sep 2025 - Aug 2026) | 2,414 sales orders, 3,449 lines (about 201 SOs and 287 lines a month) | `data/monthly-volume.csv`, order_type = Customized Order |
| Portal load per working day (Mon-Sat) | mean 7.7 SOs / 11.0 lines; median 6 SOs; 95th percentile 20 SOs / 31 lines; worst day 35 SOs / 51 lines (18 Feb 2026) | `results.json` perday |
| Lines per customized SO | 70.2% single-line, mean 1.31, 95th percentile 2, max 5 | lines_per_so |
| Customized lead time, order date to first shipment (orders in 2026) | median 18 days, p80 29 days | `data/lead-times-by-year.csv` |
| Customized orders shipped within the stated expected date | about 45% (orders from Aug 2025 on), median 2 days late | `data/lead-times.csv` |
| Open backlog (status "confirmed") | 361 lines in total, of which 229 lines / 217 SOs are Customized Order; 90 of the 229 are older than 180 days | section 6 |
| Order entry today | No sales-person, no source/channel: those fields carry no information (section 7) | channel |

## 2. Scope and definitions

- Customized = `CF.Order Type` = "Customized Order" on the SO header (Sales_Order.xlsx, column `CF.Order Type`): 7,523 lines / 5,762 SOs of 10,596 lines / 8,427 SOs (2023-03-18 to 2026-09-25). The other types: Ex Stock 2,328 lines, Internal SH Order 703, MTO 42. Order type is identical on every line of an SO (checked: 0 mixed SOs), as are division, order date, expected date and status.
- Cross-check with the item master (Item.xlsx `CF.Finished Good Type`, joined on SO `Product ID` = item `Item ID`, 10,570 of 10,596 lines match): 7,399 of the 7,523 Customized Order lines sit on items flagged Customized; 94 are on Non Customized items, 5 NA, 25 not in the item master. The reverse is the bigger gap: 254 Ex Stock lines and 125 Internal SH lines are on Customized items. So order type is the better flag for "ordered as custom"; the item flag is the better flag for "may be ordered through the portal" (what the catalogue should contain). Both are reported, neither is silently chosen.
- Division = `CF.Manufacturing Division` (header). Customized orders only appear in 8 divisions: OPD, SHPS (screen), PCU (paper cup), MOBA Punching, CPU (Customized Packing), DPU, FPP, Paper Cup Lid. Straws (PSU) and Rewinding (RWU) are never ordered as Customized Order in this data: they are Ex Stock.
- Months: Oct 2024 - Sep 2026; Sep 2026 is partial (data stops 25 Sep).
- Working day = Monday-Saturday (Saturday half day). No holiday calendar was available, so public holidays count as working days and the per-day means are slightly low. Sunday orders (28 lines in the whole file) are excluded from the per-day figures.

## 3. Monthly volume (customized, last 24 months)

Lines / SOs per month (from `data/monthly-volume.csv`, rows with order_type = Customized Order and division = ALL):

| 2024 | Oct 192/174 | Nov 210/171 | Dec 192/170 | | |
|---|---|---|---|---|---|
| 2025 | Jan 300/245 | Feb 243/180 | Mar 272/210 | Apr 205/148 | May 282/195 |
| | Jun 196/134 | Jul 265/180 | **Aug 423/313** | Sep 242/185 | Oct 248/204 |
| | Nov 265/192 | Dec 309/218 | | | |
| 2026 | Jan 369/251 | Feb 306/224 | Mar 309/198 | Apr 264/163 | May 236/140 |
| | Jun 270/168 | Jul 321/231 | Aug 310/240 | Sep (to 25th) 222/203 | |

Customized lines by division over the 24 months (lines / SOs): OPD 3,331 / 2,149; SHPS 2,087 / 1,955; PCU 697 / 380; MOBA Punching 173 / 96; CPU 133 / 128; DPU 15 / 15; FPP 14 / 13; Paper Cup Lid 1 / 1. OPD and SHPS are 84% of the load (5,418 of 6,451 lines). Volume is flat-to-rising (about 198 lines a month in Oct-Dec 2024, about 287 in the last 12 full months), with spikes in Aug 2025 and Jan 2026. The csv also has the same grid for Ex Stock, Internal SH and MTO, and an ALL row, so the portal's share of total SO volume can be read off.

Repeat behaviour (relevant to a catalogue): 2,074 distinct items were ordered as Customized lines; 1,336 of them more than once, and those account for 6,785 of the 7,523 lines (90%). Job nature on customized SOs: Reorder 4,252, New Order 1,352, Reorder With New Design 25, Rework 1, blank 132. Median ordered quantity per line 500 (p20 130, p80 2,000, p95 10,000). 637 distinct "Order Received from" names; the top 15 are 41% of lines, and the biggest (2,034 lines) is "Standard Holdings (Pvt) Ltd" itself.

## 4. Lines per SO

Customized: 5,762 SOs, 70.2% single-line, median 1, p80 2, p95 2, max 5. By division: SHPS 93.7% single-line (mean 1.07); OPD 57.2% (mean 1.44); PCU 22.0% (mean 1.78, almost always 2 lines); MOBA 23.0% (mean 1.77, almost always 2). PCU and MOBA appear to order cup + lid / body + blank pairs; the portal's basket must allow more than one line, but two is the practical norm.

## 5. Lead times and promise-vs-actual

Method: per SO, days from `Order Date` to the first (and last) Packing Date, Shipment Date and Invoice Date. Cohort = orders 2024-04-01 to 2026-07-31 (7,840 SOs); the package/shipment exports start 2024-04-01 and end 2026-09-15, and orders after July are excluded so they have had time to ship. Customized-order rows are in `data/lead-times.csv` (also Ex Stock, Internal SH, MTO; per division and "ALL"; two cohorts: all-time and orders from 2025-08-01). Coverage: of the cohort, 98.1% of customized SOs have a shipment row (92.6% package, 92.1% shipment, 97.4% invoice across all types).

**Important: the all-time figures are biased low and must not be used as the promise.** In 2024 most orders were keyed into Zoho at or after dispatch: 68% of 2024 customized SOs show a first shipment on the order date itself (SHPS 98%, DPU and PCU about 100%). By 2026 that is 0.8%, so the order date has become a true order date. `data/lead-times-by-year.csv`, customized, order date to first shipment:

| Division | 2024 median / p80 | 2025 | 2026 (orders to Jul) |
|---|---|---|---|
| All customized | 0 / 16 | 8 / 21 | **18 / 29** |
| OPD | 8 / 25 | 12 / 24 | **21 / 31** |
| SHPS (screen) | 0 / 0 | 5 / 16 | **14 / 25** |
| PCU (paper cup) | 0 / 0 | 11 / 23 | **21 / 26** |
| MOBA Punching | - | - | 20 / 25 |
| CPU | - | - | 7 / 19 |

(Cells with fewer than 20 shipped SOs are omitted. The 2026 figures are right-censored: only orders already shipped by 15 Sep count, so a slow tail is missing and the real p80 is probably a few days higher.) Median first-package, first-shipment and first-invoice are within 1 day of each other in every division, so one "ready to dispatch" date describes all three. Last shipment is a further 2-4 days later in the 2025-08 cohort (all customized median first 18 / last 20; OPD 21 / 25; SHPS 14 / 15), reflecting multi-shipment orders: 20.8% of shipped customized SOs have more than one shipment (223 have 5 or more).

Ex Stock for comparison (all years, shipped SOs): median 1 day, p80 5 days; Rewinding 0/1, Paper Straw 1/2, Paper Cup Lid 1/2. Internal SH orders behave like custom work (median 11, p80 35.6 days). The gap between about 1 day (stock) and about 18 days (custom) is what the portal's stock check must exploit.

Promised vs actual (customized, `Expected Shipment Date` vs first shipment, orders from 2025-08-01, 2,201 SOs): median 2 days late, p80 12 days late, 45.3% on or before the expected date (OPD 34.5%, PCU 37.3%, MOBA 31.5%, SHPS 59.3%). Planned lead (expected date minus order date) is a median 16 days (14 for SHPS) against an actual median of 18, so the standard promise is about right at the median but wrong for a half of orders. Expected-date fill rate on customized SOs: 100% in 2023, 57.6% in 2024, 38.9% in 2025, 99.3% in 2026, so earlier on-time rates rest on a minority of orders; this is why the 2025-08 cohort is the one to quote. The portal should require the date.

## 6. Cancellations, partials and the open backlog

Line level, customized (7,523 lines): 1,385 lines (18.4%) have a cancelled quantity, but cancelled quantity is only 1.1% of ordered quantity and only 203 lines (2.7%) are fully cancelled, so most are small short-shipment cancels, not lost orders. By division: PCU 37.2% of lines (3.6% of qty), MOBA 32.8%, OPD 21.8% (1.1% of qty), SHPS 7.8% (0.3% of qty), CPU 2.3%. The share of customized lines with a cancel rises by year: 11.8% (2024), 17.1% (2025), 24.3% (2026). 1,226 lines (16.3%) have status partially_invoiced (PCU 36.2%, MOBA 36.7%, OPD 21.8%, SHPS 1.4%). No invoiced line is short of ordered-minus-cancelled quantity, so a closed SO is a complete SO. (Ex Stock: 25.6% of lines have a cancel, 2.5% of quantity.)

Open backlog: 361 lines have status "confirmed" in total (Ex Stock 67, MTO 11, Internal SH 54, Customized 229). Customized only: 229 lines on 217 SOs, 977,059 units ordered, 65,788 packed, 0 invoiced.
- By division (lines / SOs): OPD 138 / 126; SHPS 48 / 48; PCU 22 / 22; CPU 11 / 11; MOBA 10 / 10.
- Age at 25 Sep 2026 (days since order date): 0-14 d 69; 15-30 d 46; 31-60 d 12; 61-90 d 7; 91-180 d 5; 181-365 d 36; over 365 d 54 (oldest 905 days; median 24). By order year: 2026 157, 2025 38, 2024 34.
- 208 of the 229 have an expected date; 121 of those are already past it. Only 13 lines have any quantity packed.
- 90 lines (39%) are older than 180 days. I cannot tell from the exports whether these are live orders or SOs that were never closed or cancelled in Zoho; this needs Rizwan's team or the managers to confirm before the portal imports any history.

## 7. Who and what places orders today

- `Sales Person`: blank on 6,374 of 7,523 customized lines; the only value is "Internal for  SH" (1,149 lines). By year the fill rate is 60.9% (2024), 4.1% (2025), 0.0% (2026). It cannot identify the SH salesperson.
- `Source`: the constant "1" on all 10,596 lines. `Sales Channel`: the constant "direct_sales". Neither tells us how the order arrived.
- `Customer Name`: "Standard Holdings (Pvt) Ltd" on 10,594 of 10,596 lines (two stray lines: Spar SL, Banana Arugambay). The real customer is the free-text `CF.Order Received from` (100% filled, 637 distinct spellings for customized lines), so the portal needs a managed customer list.
- `Template Name`: "JOB WORK ORDER" 5,302 and "Standard Template" 2,221 customized lines. The template flipped: 2024 almost all Job Work Order (1,661 of 1,663), 2025 75% JWO, 2026 54% Standard Template (1,417 of 2,607). Someone changed how orders are keyed in 2025/26; I do not know the reason.
- `CF.SH Sales Order Ref`: 100% filled, but it is the SPS job number not an SH sales-order number: it equals `CF.Job No` on 51.0% of customized lines (53.1% equal the `PurchaseOrder` field) and the sample values are job codes such as OPD2446F and OPD2563 A. A true SH sales-order reference therefore does not exist as a field today. `CF.Job No` is filled 99.9%. The job number carries a letter-suffix revision style (OPD2563 A, C), so it is not a clean key.
- `CF.Clickup Link`: 15.4% of customized lines overall; 0.1% in 2024-2025 but 44.3% in 2026 (ClickUp linking has started recently).
- Other custom fields (customized lines): Order Received from 100%, Base Material 99.9%, Additional Material 5.3%, Artwork / Dye-cutter / Screen availability 100% (after merging the misspelled duplicate columns), Job Nature 98.2%, Notes 0%. These are the fields a portal form should replace, with Base Material and the three availability flags as required inputs.

## 8. Join keys and match rates

| Link | Key | Match |
|---|---|---|
| SO line -> item master | SO `Product ID` = Item.xlsx `Item ID` | 10,570 / 10,596 lines (99.8%); 26 unmatched (25 on Customized Order) |
| Package -> SO | Package_ALL `SO Number` = SO `SalesOrder Number` | 67,039 / 67,039 rows carry an SO number and all 7,603 distinct SO numbers exist in the SO file |
| Shipment -> SO | Shipment_ALL `SO Number` = SO `SalesOrder Number` | 65,957 / 65,957 rows; 7,559 distinct SOs all match |
| Shipment -> Package | `Packing Number` | all 65,957 shipment rows match a package number (pkg: 66,144 distinct numbers, so about 187 packs have no shipment yet) |
| Invoice -> SO | Invoice `Sales Order Number` (not `PurchaseOrder`, though the two are equal on 13,928 rows) | 13,942 / 13,990 rows carry the key, all 8,083 distinct SOs match; 48 invoice rows have no SO number |

Join is at SO level, not line level: packages carry item name and qty but no SO line ID, so first/last dates are per SO. Each SO has a single division and order type, so this is safe for the lead-time grouping. Coverage of SOs with packages: of SOs ordered from 2024-04-01, 93.3% of invoiced SOs have a package row (6,500 of 6,969), 96.8% of partially invoiced ones and 7% of confirmed. I did not investigate the 469 invoiced SOs that have no package row, so I cannot say what they are.

## 9. Limits of this analysis (what I could not determine)

- Packages and shipments are the 16 Sep snapshot (to 15 Sep 2026) and begin 1 Apr 2024; the 19 SOs before then, and any SO shipped after 15 Sep, have no shipment data. The SO and invoice exports are 27 Sep (to 25 Sep).
- Lead time is order date to first shipment. It includes SH-side waiting time before the order was keyed, which the data cannot show. Delivery to the end customer (Shipment `Delivery Date`) was not analysed.
- I cannot see stock at order time, so the share of customized orders that could have been served from stock is not here; that belongs to the stock-check analysis.
- Order Date meaning changed over time (back-keyed in 2024); I inferred this from same-day shipment rates, not from any documentation.
- Public holidays are not excluded from working-day counts.

## Files

- `data/monthly-volume.csv`, `data/lead-times.csv`, `data/lead-times-by-year.csv`, `data/results.json`
- `scripts/load.py`, `scripts/patterns.py`, `scripts/lt_extra.py`. Run: `python3.12 -I scripts/patterns.py <Sales_Order.xlsx> <Invoice.xlsx> <Package_ALL.xlsx> <Shipment_ALL.xlsx> <Item.xlsx> data [cache.pkl]` then `python3.12 -I scripts/lt_extra.py <cache.pkl> data`.
