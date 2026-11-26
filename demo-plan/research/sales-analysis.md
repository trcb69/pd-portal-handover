# Sales analysis for the joint demo filter (Order Portal + Production Dashboard), 21 Oct 2026

Prepared by Abdul Hadhee | IT Executive. Read-only on saved data; no Zoho or other live system was called. No payables, overdues or payment status appear anywhere. No LKR values are quoted (38% of SH lines carry a zero item total, so counts and quantities are used throughout). Scripts: `/root/.claude/jobs/61c1b69c/tmp/analysis/` (`common.py` reuses the `a3.py` classification unchanged; `apimodel.py` reproduces the 8 Oct study model exactly: 5-min 933/1,178/3,764, 2-min 1,826/2,097/4,676, 1-min 3,304/3,619/6,181 for median/p95/max, variant A). Tables are in `research/data/` (file named after each table below).

## 0. Answers first

1. **The full dashboard sync already fits.** SPS limit 7,500/day. Variant A, SO list + bundles list, all SOs: 1-min polling 3,304/day median (max 6,181); 2-min 1,826 (max 4,676); 5-min 933 (max 3,764). Only the 1-min maximum breaks the 4,500 dashboard cap (OQ11), and it is a bulk-edit day (5 May 2026, 2,645 SOs modified), not normal traffic.
2. **A customer or item filter saves very little, because the list scan is the cost.** At 1-min the two list polls plus the 43-page nightly read are 2,923 calls/day, 88% of the median 3,304. Only the 381 detail calls shrink. At 5-min the fixed part is 619 of 933. The filter buys focus and protection on bulk-edit days (S1 header filter: 1-min max 6,181 down to 3,889), not necessity. The real lever is the polling interval (1 to 2 min saves about 1,480 calls/day).
3. **The 8 key customers are small in SPS and large in SH.** Header rule: 260 of 3,724 SPS job orders (7.0%, 5.0 a week) in the last 12 months; in SH 444 of 2,617 orders (17.0%) and 1,386 of 7,923 lines (17.5%) in 19 Sep to 17 Oct. One account, Gamma Pizzakraft (Pizza Hut and Taco Bell share it), is 372 of those 444 SH orders.
4. **Top-N items do not represent SPS customized work.** Customized items are a long tail (2,708 in the SPS catalogue; the best item has 14 lines in 12 months). Top-50 SPS items cover 20.6% of job orders out of sample; top-100 cover 24.6%. In SH the top-20 items cover 23.9% of lines, top-100 48.0%. Items are known only after a detail call, so an SPS item filter saves no calls unless Zoho's list accepts an item filter (not verified).
5. **What feeds the production units is the division, not the customer.** PSU and RWU have one SPS customer (Standard Holdings, i.e. SH stock builds); SHPS has 299 distinct customers (top 12 = 22%); lids, plates and cake wrappers are at least 97% SH stock builds (FPP 65%, DPU 24%). A customer list starves 9 of 12 units. Recommended filter = key customers and named feeders plus **whole divisions** (a list-row field, free): see section 7.
6. **Recommended demo filter:** stage S1 (section 7): 9 key SPS names + 6 OPD feeders + 12 SHPS feeders + 9 whole small divisions; about 34 SPS job orders a week (47% of all), SH 7 key accounts + top-20 items (576 lines and 252 orders a week, about 30% of lines). Poll every 2 min by day.

## 1. Data and coverage (what each number rests on)

| Source | What it holds | Window | Partial where |
|---|---|---|---|
| SH lines: `/root/exports/zoho/native/2026-10-18/sh/SH_Sales_Order_2026-09-19_2026-10-18.xlsx`, sheet "Sales Order" | 7,923 lines, 2,617 SOs | order dates 19 Sep to 17 Oct 2026 | Sep part = 19-30 Sep only; Oct part = 1-17 Oct only. This is the **only SH line-level data**, so every by-kind line figure covers 4 weeks |
| SH headers: `/root/exports/zoho/native/2026-09-19/sh_full/salesorders.json` | 71,982 SOs (no lines). One record dated 1831 excluded | 1 Apr 2024 to 19 Sep 2026 | Sep 2026 = 1-19 Sep. I union it with the xlsx SOs (deduplicated by SO number) to complete Sep and Oct |
| SH monthly quantity: `sh_full/sales_by_item_monthly.json` | item x month, quantity sold | Apr 2024 to 19 Sep 2026 | Sep 2026 partial. Mixed units: only items with unit nos/pcs counted (84% of quantity). I did not verify whether this Zoho report is invoice-based |
| SPS job-order headers: 8 Oct study `pulls/so_*.json` + `v8/` | 8,571 SOs (`cf_order_type`, `cf_manufacturing_division`, `cf_order_received_from`, artwork/die-cutter/screen fields) | Apr 2024 to 8 Oct 2026 (7 SOs Mar 2024, 4 in 2023) | Oct 2026 = 1-8 Oct (71). Monthly counts match the SPS `Sales_Order.xlsx` of 16 Sep within 1-3 per month, so I treat the register as complete from Apr 2024 (the earlier research called it "most recently touched"; the month-by-month match says it is the whole register) |
| SPS lines: `/root/exports/zoho/native/2026-09-16/Sales_Order.xlsx` + 266 details in `pulls/details.json` | 10,489 lines on 8,571 SOs | Apr 2024 to 8 Oct 2026 | line detail for 16 Sep to 8 Oct comes from the 266 detail pulls |
| SPS packages/shipments: `pulls/pkg_*`, `ship_*` | document times | 8 Oct 2025 to 8 Oct 2026 | |
| PO lines: `/root/exports/zoho/books/2026-09-25/sh/purchaseorders/po_line_items.csv` | import = currency not LKR (a proxy) | to 25 Sep 2026 | |

Kind rules are those of `item-flows-research.md` A.1 (a3.py). Mapping to the three kinds in this report: **customized** = firm (master tag, 927 lines) + grey (419 lines: SPS says customized, SH treats as standard); **made-for-stock** = SPS-made plus "both"; **bought-in** = outside supplier, chemicals, GD, raw material sold to SPS. Unknown source (264 lines), service (109) and unmatched (100) are shown apart. The grey group matters: "Lid For 450ml AF Container - 8342" (111 lines) and "Lid For 750ml AF Container - 8389" (91) rank 7th and 9th overall and are counted as customized here, but probably are standard products with a wrong SPS tag.

## 2. Recent trends (item 1)

### 2.1 SH order volume (orders), monthly (`sh_orders_per_month.csv`)

| Period | SH orders |
|---|---|
| Apr 2024 to Mar 2025 monthly range | 1,897 to 2,578 |
| Sep 2025 / Dec 2025 / Jan 2026 / Feb 2026 | 2,462 / 2,940 / 2,996 / 2,838 |
| Mar / Apr / May / Jun 2026 | 2,888 / 2,394 / 2,528 / 2,846 |
| Jul / Aug / Sep 2026 | 2,923 / 2,910 / 2,913 |
| Oct 2026 (1-17 Oct only, partial) | 1,658 |

Last 3 full months (Jun-Aug 2026: 8,679) vs previous 3 (Mar-May: 7,810): +11%. Jun-Aug 2026 vs Jun-Aug 2025 (6,789): +28%. By business unit the Packaging unit is about 72% of orders (e.g. Aug 2026: 2,088 of 2,910); a "Manufacturing" business unit appears from Jul 2026 (51, 92, 82 orders).

### 2.2 SH lines and quantity by kind (4-week window, `sh_lines_by_kind_window.csv`, `sh_lines_by_kind_week.csv`)

| Kind | Lines 19-30 Sep | Lines 1-17 Oct | Total | % | Quantity ordered (all units mixed) |
|---|---|---|---|---|---|
| bought-in | 1,943 | 3,537 | 5,480 | 69.2% | 4.57 M |
| customized | 494 | 852 | 1,346 | 17.0% | 0.93 M |
| made-for-stock (SPS) | 226 | 398 | 624 | 7.9% | 0.70 M |
| unknown source | 106 | 158 | 264 | 3.3% | 0.46 M |
| service / unmatched | 49 | 160 | 209 | 2.6% | |

Weekly lines (Mon-Sat; the week of 14 Sep holds only 19-20 Sep): 21 Sep 1,634; 28 Sep 2,071; 5 Oct 2,171; 12 Oct 1,905. **Average of the four full weeks: 1,945 lines a week** (bought-in 1,345, customized 332, made-for-stock 153). This matches the header-based 640 SOs a week x 3.03 lines per order.

**Longer trend, quantity only** (Zoho sales-by-item, pieces-unit items, `sh_qty_pcs_by_kind_12m_vs_prev12.csv`; last 12 full months Sep 2025-Aug 2026 vs the 12 before):

| Kind | Last 12 months (pcs) | Previous 12 | Change | Share |
|---|---|---|---|---|
| bought-in | 37.9 M | 27.7 M | +37% | 58% |
| customized | 11.8 M | 8.7 M | +35% | 18% |
| made-for-stock | 7.4 M | 7.4 M | +1% | 11% |
| unknown source | 8.1 M | 6.3 M | +28% | 12% |

Last 3 months (Jun-Aug 2026) vs the previous 3: bought-in +11%, customized +7.6%, made-for-stock +91% (a stock build in Jun-Aug after a low May: 148 k pcs in May, 807 k in Jul). Monthly series in `sh_monthly_qty_pcs_by_kind.csv`. Line counts by kind exist for 4 weeks only; I cannot give a monthly line trend by kind.

### 2.3 SPS job orders by order type and division (`sps_jobs_per_month_by_order_type.csv`, `sps_jobs_per_month_by_division.csv`, `sps_jobs_division_x_type_all.csv`)

Monthly job orders, Apr 2024 to Sep 2026 (full months): 214 to 413, typically 250-340. Selected months: Sep 2025 259, Dec 2025 288, Jan 2026 335, Jul 2026 336, Aug 2026 304, Sep 2026 338. Oct 2026 is 71 up to 8 Oct (partial).

Order type, monthly:

| Month | Customized | Ex Stock | Internal SH Order | MTO |
|---|---|---|---|---|
| Apr-Aug 2025 avg | about 194 | about 92 | about 8 | 0 |
| Sep 2025 | 185 | 37 | 37 | 0 |
| Jan 2026 | 251 | 56 | 28 | 0 |
| Jul 2026 | 231 | 57 | 48 | 0 |
| Aug 2026 | 240 | 46 | 17 | 1 |
| Sep 2026 | 262 | 46 | 30 | 0 |

Two shifts to know about: **Ex Stock halved from Sep 2025** (about 91 a month Apr 2024-Aug 2025 to about 45 since), while **Internal SH Order went from about 3 to about 32 a month** from Aug 2025. Ex Stock plus Internal is roughly constant (about 78 vs 91 a month). I suspect make-for-stock runs were partly re-labelled; unverified, no file defines "Internal SH Order". Total job orders: Jul-Sep 2026 978 vs 740 in Apr-Jun (+32%), and vs 956 in Jul-Sep 2025 (+2%).

Division, monthly: OPD 77-226 (Sep 2026: 112), SHPS 50-152 (Sep: 68), PCU 0-36 (Sep: 34), PSU 6-33 (Sep: 22). **CPU (Customized Packing Unit) was almost unused until Jul 2026** (0-3 a month), then 64, 57, 62 in Jul, Aug, Sep: these are PACKSERV pouch-packing jobs for Spar and Keells. MOBA Punching 1-18, Lid unit 0-28 (none since March 2026).

Last 8 whole weeks (10 Aug-4 Oct 2026): 72.6 job orders a week = Customized 56.9, Ex Stock 10.4, Internal SH 5.2, MTO 0.1. Last 12 months (created 9 Oct 2025-8 Oct 2026): 3,724 = 71.4 a week.

Division x type over the whole register (8,571): SHPS is 100% Customized; PSU 775 of 778 Ex Stock; RWU 565 of 566 Ex Stock; OPD 2,772 Customized / 732 Ex Stock / 352 Internal / 31 MTO.

## 3. Highest-selling lists (item 2)

Units: order lines = lines on SH SOs (or SPS job orders); quantity = ordered quantity in the item's own unit (pieces unless stated); quantity rankings use piece-unit items only (nos/pcs), because rolls, kg and packs cannot be added to pieces. Files: `sh_top_items_window.csv`, `sh_top_items_12m_qty.csv`, `sps_top_items_12m.csv`.

### 3.1 SH top 20 by order lines (19 Sep to 17 Oct 2026)

| # | Item | Kind | Lines | Qty | Unit |
|---|---|---|---|---|---|
| 1 | Wooden Spoon 16cm | bought-in | 261 | 155,050 | nos |
| 2 | Aluminium Lava Cake Cup | bought-in | 192 | 112,201 | nos |
| 3 | Paper White Straw 6mm x 20cm (Packed) | made-for-stock | 128 | 127,500 | pcs |
| 4 | Wooden Fork 16cm | bought-in | 123 | 75,250 | nos |
| 5 | Chefs Choice Cling Film 45cmX300m (21) | made-for-stock | 112 | 5,438 | rolls |
| 6 | 450ml AF Container - 8342 | bought-in | 112 | 38,000 | nos |
| 7 | Lid For 450ml AF Container - 8342 | customized (grey) | 111 | 37,000 | nos |
| 8 | 750ml AF Container - 8389 | bought-in | 95 | 56,752 | nos |
| 9 | Lid For 750ml AF Container - 8389 | customized (grey) | 91 | 55,052 | nos |
| 10 | ST-Cling Film 45cmX600m | made-for-stock | 89 | 611 | rolls |
| 11 | Chefs Choice BP 45cmX100m | bought-in | 76 | 279 | rolls |
| 12 | Screen Frame Exposing Only | bought-in (service-like) | 70 | 111 | nos |
| 13 | SH-Black (Plastic Lid - PS6) for 8oz Paper Cup (M) | customized | 61 | 48,439 | nos |
| 14 | Black Vinyl Disposable Powder Free Gloves-Large | bought-in | 59 | 882 | packs |
| 15 | Boufant Hair Net Blue | bought-in | 57 | 49,900 | pcs |
| 16 | Flat Lid for 12/16/22 Oz Plastic Cups | bought-in | 52 | 55,759 | nos |
| 17 | SP - 700ML Kraft Box (Pizza) | customized | 51 | 2,800 | nos |
| 18 | SH Kraft Box Plain 900ml (165x115x50)mm | customized | 51 | 22,680 | nos |
| 19 | 12Oz Plastic Cup (350ml) | bought-in | 51 | 26,800 | nos |
| 20 | Dome Lid for 12Oz PP Cup(350ml) | bought-in | 50 | 23,552 | nos |

Top 20 = 23.9% of lines; top 50 = 36.5%; top 100 = 48.0%; top 200 = 60.9%; 1,656 items in all. Stability: ranking items on 19 Sep-2 Oct and testing on 3-17 Oct gives 21.8% / 34.4% / 44.7% / 56.0% for N = 20 / 50 / 100 / 200, so the lists are fairly stable.

By quantity (piece-unit items): Wooden Popstick 114mm 1,008,950 (8 lines), Wooden Yogurt Spoon 306,350 (6), Cake Cup 14cm-White 250,000 (3), Cake Cup 7.5cm-Brown 206,000 (6), Flexible White Straw 6mm x 24cm 197,904 (39). Few lines carry huge quantities, so quantity and line rankings differ strongly.

**12-month quantity top 5** (sales by item, Sep 2025-Aug 2026, pcs): Wooden Popstick 114mm 3.75 M; Wooden Spoon 16cm 2.14 M; Paper White Straw 6mm x 20cm (Packed) 2.07 M; Paper White Straw 6mm x 20cm SPS 1.98 M; Flexible White Straw 6mm x 24cm 1.75 M (`sh_top_items_12m_qty.csv`, top 20 and per kind).

### 3.2 SH top 10 per kind, by lines (window)

- **Customized (10):** Lid For 450ml AF 111; Lid For 750ml AF 91; SH-Black Lid PS6 for 8oz cup 61; SP-700ML Kraft Box (Pizza) 51; SH Kraft Box Plain 900ml 51; SH Kraft Box Plain 1200ml 49; Lid For 1200ml AF 36; 8oz Kraft Double Wall Cup 34; Clear Pet Lid 500/750/1000ml 30; Lid For 1900ml AF 28. Top 10 = 40% of customized lines, top 50 = 70%, 292 items. By quantity: Lid For 750ml AF 55,052; SH-Black Lid PS6 48,439; Lid For 450ml AF 37,000; 8oz Kraft Double Wall Cup 30,026; Burger Bag Wax Coated (Street Burger) 26,000.
- **Made-for-stock (10):** Paper White Straw 6mm x 20cm (Packed) 128; Chefs Choice Cling Film 45x300m 112; ST-Cling Film 45x600m 89; 12oz Kraft Double Wall Cup 33; Paper White Straw 6mm x 20cm SPS 32; Flexible White Straw 6mm x 24cm (Packed) 16; Pizza Box 30x30x4cm 16; Paper White Straw 8mm SPS 13; ST-Cling Film 45x300m 11; Kraft Paper Bag (S) 11. Top 10 = 74%, top 20 = 84%; 64 items.
- **Bought-in (10):** Wooden Spoon 16cm 261; Aluminium Lava Cake Cup 192; Wooden Fork 16cm 123; 450ml AF Container 112; 750ml AF Container 95; Chefs Choice BP 45x100m 76; Screen Frame Exposing Only 70; Black Vinyl Gloves-Large 59; Boufant Hair Net Blue 57; Flat Lid for 12/16/22 Oz Cups 52. Top 10 = 20%, top 100 = 54%; 1,088 items. Import vs local (`bought_in_top_items_import_vs_local.csv`, share of PO lines not in LKR, a proxy): Wooden Spoon 24%, Aluminium Lava Cake Cup 57%, 450ml AF Container 59%, 750ml AF 38%, Black Vinyl Gloves 100%, Flat Lid / 12Oz Cup / Dome Lid 0% (local), overall PO lines 20%.

### 3.3 SPS top items (last 12 months, job-order lines; `sps_top_items_12m.csv`)

Top 20 overall by lines (item names merged across spelling variants; customer = the "Order received from" most often attached): Paper White Straw 6mm x 20cm (Packed) 141 lines/139 job orders (1.92 M pcs); Chefs Choice Cling Film 45x300m 96; ST-Cling Film 45x600m 83; Paper Straw White 6mm x 20cm SPS 57; Paper Straw White 8mm x 20cm SPS 41; Paper White Straw 6mm Imported (Packed) 35; Flexible White Straw 6mm x 24cm (packed) 34; SH-Black Lid PS6 for 8oz cup 18; Chefs Choice Cling Film 45x600m 17; BG - 12oz S/Wall White Paper Cup 16; then SP-Kraft Food Wrap (10x10) (Taco Bell) 14, SP-Small White Wrapper (Taco Bell) 14, SP-Kraft Food Wrap (12x12) (Taco Bell) 14, and 12 each for a Spar PACKSERV foil container, a Marriott cup and a Riff Hikkaduwa pouch. **Everything above rank 10 is Ex Stock (PSU, RWU) or SH stock builds; customized items first appear at rank 11 with 14 lines.**

Top by quantity: Paper White Straw 6mm x 20cm (Packed) 1.92 M; SH-8oz S/Wall White Paper Cup 1.10 M (7 lines); SH-White Round Cup Cake Wrapper 14cm 1.03 M (3 lines); PACKSERV Wooden Spoon 16cm (Keells) 1.01 M (7 lines); SH-Brown Cup Cake Liner 10.5cm 0.98 M.

Top items per division (top 10 each in the CSV, by lines and by quantity):

| Division | Leading items (12-month lines) |
|---|---|
| OPD | SP-Kraft Food Wrap (10x10) (Taco Bell) 14; (12x12) 14; SP-Small White Wrapper (Taco Bell) 14; SP-Chopstic pouch (Riff Hikkaduwa) 12; SH Kraft Double Cup Holder 12; SP-Chicken Bucket+Lid (Keells) 11 |
| SHPS | CP-16Oz Plastic Cup (Ceylon Coffee Club) 8; CP-12Oz Plastic Cup (Dinemore) 7; CP-12oz Plastic Cup (Blends) 7; CP-16Oz Plastic Cup (Island Tea) 7; CP-8oz D/Wall Kraft Cup (BYD) 7 (a flat tail: no item above 8) |
| PCU | BG - 12oz S/Wall White Paper Cup 16; BG - 12oz D/Wall Kraft 13; BG - 8oz D/Wall Kraft 13; BG - 8oz S/Wall White 13; SP-12oz D/Wall White Paper Cup (Marriott) 12 |
| PSU | Paper White Straw 6mm x 20cm (Packed) 141; Paper Straw White 6mm SPS 57; 8mm SPS 41; 6mm Imported (Packed) 35; Flexible 6mm x 24cm 34 |
| RWU | Chefs Choice Cling Film 45x300m 96; ST-Cling Film 45x600m 83; Chefs Choice 45x600m 17; Biodegradable 45x300 10 |
| CPU | PACKSERV - 750ml Aluminium Foil Container with Lid (10 pcs) (Spar) 12; 450ml 11; 750ml Plastic Rectangle 11; 660ml 10 (all new since Jul 2026) |
| MOBA Punching | SP-Kraft Box 1200ml (Cafe 173) 8; SP-Kraft Box 700ml (Cafe 173) 8; SP-700ml White Box (Thoma) 6 |
| Lids, plates, cake wrappers, FPP, DPU | 35, 6, 4, 26 and 21 job orders in 12 months; lids = SH-Black Lid PS6 for 8oz cup, plates = SH Paper Plate 7 / 9 inch, wrappers = SH cup cake liners |

### 3.4 Rising items (last 3 months vs previous 3)

- **SH, quantity** (Jun-Aug 2026 vs Mar-May 2026, pieces; `sh_rising_items_qty.csv`): Wooden Popstick 114mm 1.69 M vs 0.63 M (x2.7); Cake Cup 14cm-White 405 k vs 7 k (a stock build); Boufant Hair Net Blue +59%; Cake Cup 6.5cm-Brown x2.3; 80ml Transparent Container + Connected Lid +60%; Flexible White Straw 6mm x 24cm (Packed) x1.8; Paper White Straw 8mm x 20cm SPS x2.0; SP-Burger Pouch (Street Burger) x2.9; SH Kraft Box Plain 1200ml +94%; Oil Paper x3.7.
- **SPS, job-order lines** (Jul-Sep vs Apr-Jun 2026; `sps_rising_items_lines.csv`): Paper Straw White 6mm x 20cm SPS 24 vs 4 lines (x6; 158 k vs 28 k pcs) is the only established item that rises; everything else rising is **new**: nine PACKSERV pouch-packing items for Spar (750ml Aluminium Foil 12 lines, 750ml Plastic Rectangle 11, 450ml Aluminium 11, 1200ml 9, 1400ml 9, 250ml 9, 1900ml 8, 430ml 8, 700ml Kraft Lunch Box 8) and the Keells equivalents, all zero before July.

## 4. Key customers (item 3)

Names matched (unconfirmed by the owner, as in the 24 Sep memory): **SPS** field "Order received from": `PIZZA HUT`, `TACO BELL`, `Keells Super`, `Spar SL (Private ) Limited`, `Street Burger (Private) Limited`, `MARRIOTT WELIGAMA`, `Courtyard by Marriott` and `Colombo Courtyard (Pvt) Ltd`. A generic `Marriott` (29 lines: OPD 13, PCU 15) is not assigned to either Marriott customer. **SH** customer names: Pizza Hut and Taco Bell = `Gamma Pizzakraft Lanka (Pvt) Ltd` (one shared account, so they cannot be split on the SH side); Keells = `Jaykay Marketing Services (Pvt) Ltd` plus `Keells Super`; Spar and Street Burger = the same names as in SPS; Norfolk = `Norfolk Foods (Pvt) Ltd` (SH only); Marriott Weligama = `Weligama Hotel Properties Limited`; Courtyard Marriott: **no SH account found**. SPS lines logged under Standard Holdings are re-attributed to the end customer with the 24 Sep rule (item named for one customer, 90% ownership, name patterns). Files: `key_customers_summary.csv`, `key_customers_monthly.csv`, `key_customers_units_12m.csv`.

### 4.1 Summary (SPS: 9 Oct 2025-8 Oct 2026; SH: 19 Sep-17 Oct 2026 for lines, last 12 months of headers for orders)

| Customer | SPS lines / job orders (12 m) | Lines per job order | SPS units that make their items | SH orders 12 m (last 3 m vs previous 3 m) | SH lines / orders in window | SH lines per order | SH kinds (lines) |
|---|---|---|---|---|---|---|---|
| Pizza Hut | 9 / 6 | 1.5 | OPD 6, MOBA Punching 3 | shared Gamma account: 4,490 (1,273 vs 1,119) | Gamma: 1,136 / 372 | 3.05 | bought-in 670, customized 281, made-for-stock 185 |
| Taco Bell | 103 / 69 | 1.5 | OPD 103 (PackPro 83, MacPro 20) | (same Gamma account) | (same) | | |
| Keells | 46 / 39 | 1.2 | CPU 23, OPD 21, PCU 2 | 357 (57 vs 52) | 67 / 11 | 6.1 | unknown source 60, bought-in 3 |
| Spar | 108 / 98 | 1.1 | CPU 90, OPD 16, MOBA Punching 2 | 497 (130 vs 144) | 115 / 32 | 3.6 | unknown source 80, made-for-stock 17, customized 12, bought-in 6 |
| Street Burger | 49 / 38 | 1.3 | OPD 49 (PackPro 39, MacPro 10) | 105 (17 vs 25) | 35 / 9 | 3.9 | customized 22, bought-in 7, made-for-stock 4 |
| Norfolk | none | | | 34 (8 vs 5) | 5 / 3 | 1.7 | bought-in 4, customized 1 |
| Marriott Weligama | 7 / 4 | 1.75 | OPD 7 | 214 (54 vs 54) | 28 / 17 | 1.65 | bought-in 20, customized 6 |
| Courtyard Marriott | 9 / 6 | 1.5 | OPD 9 (PackPro 8, MacPro 1) | no SH account | | | |

(The "line tag" unit is PackPro or MacPro where tagged; untagged OPD lines are not in the brackets.) Keells in SH is flat over 3 months but 56% down over 6 months because of a Jan-Feb 2026 spike (56 and 167 orders).

### 4.2 Order lines a month (SPS, `key_customers_monthly.csv`) and trend

| Month 2026 | Taco Bell | Spar | Keells | Street Burger | Pizza Hut | Marriott Weligama | Courtyard |
|---|---|---|---|---|---|---|---|
| Apr | 10 | 2 | 6 | 8 | 1 | 2 | 0 |
| May | 4 | 2 | 0 | 1 | 0 | 2 | 0 |
| Jun | 12 | 0 | 0 | 4 | 1 | 0 | 0 |
| Jul | 7 | 36 | 10 | 3 | 0 | 0 | 0 |
| Aug | 5 | 38 | 0 | 0 | 0 | 0 | 2 |
| Sep | 7 | 22 | 15 | 5 | 0 | 0 | 0 |

Taco Bell: steady, 53 lines last 6 months vs 49 before (+8%). **Spar: 2 lines in the 6 months before July, 95 since** (PACKSERV pouch packing at CPU). Street Burger: 20 vs 27 (-26%). Keells: lumpy (0 to 15 a month). Pizza Hut, Marriott Weligama and Courtyard Marriott: 4 to 9 lines a year each, not enough to exercise a unit.

SH orders a month (Apr to Aug 2026): Gamma 371, 351, 411, 447, 396; Spar 41, 53, 39, 41, 49; Weligama Hotel Properties 18, 18, 16, 16, 21; Street Burger 10, 7, 7, 6, 5; Norfolk 1, 1, 1, 2, 4.

### 4.3 What they buy and top items

- **SPS top items per customer (12 m lines):** Taco Bell: Kraft Food Wrap (10x10) 14, (12x12) 14, Small White Wrapper 14 (typical job quantity 10,000-20,000). Spar: PACKSERV 750ml Plastic Rectangle 11, 750ml Aluminium 10, 660ml 9. Keells: Chicken Bucket+Lid 11, PACKSERV Wooden Spoon Pouch Packing 7, Fork 5. Street Burger: Burger Bag Wax Coated 9, Fries Pouch 8, Fries Paper Pouch 7. Pizza Hut: Fries Deal Pouch 6, 700ML Kraft Box (Pizza) 3. Marriott Weligama: Breakfast Box 7. Courtyard: Round Coaster 3.5inch 4, Panettone Box 2, Yule Log Box 2.
- **SH top items (window):** Gamma: Wooden Spoon 16cm 199 lines, Aluminium Lava Cake Cup 186, Paper White Straw 6mm x 20cm (Packed) 115; its customized lines are mostly Taco Bell / Pizza Hut wraps and boxes plus the 450ml AF lid (68 lines). Keells (Jaykay): Transparent PP Cup 450ML with Lid 6, Transparent PP Tub 80ML with Lid 6. Spar: PE Gloves 21MIC 9, White Greaseproof Paper 15x13 7. Street Burger: Hair Net Blue, Burger Bag Wax Coated, SP-Burger Pouch (3 each).
- **Gamma is the one account that buys all three kinds**: 1,136 lines in 4 weeks = bought-in 59%, customized 25%, made-for-stock 16%; 116 of its 372 orders are mixed customized + bought-in (31%). 92% of its lines are picked at Kohalwila (1,050 of 1,136).

### 4.4 Also high volume, and rising fast (each customer in one group only)

Counted in lines (SPS) or orders (SH), not LKR. Files `sps_customers_groups.csv`, `sh_customers_groups.csv`. SPS high volume = the 12 largest by 12-month lines after the key 8; rising = at least 20 lines in the last 6 months and at least 1.5x the previous 6 months, active in 3 or more of the last 6 months. SH internal accounts (Smart Pack internal and retail accounts, SH Printing, Kelaniya Warehouse, Standard Holdings Lab, Trade Receivables) and cash/staff accounts are left out.

| Group | SPS customers ("Order received from"; 12 m lines) | SH customers (12 m orders) |
|---|---|---|
| Also high volume | Kiri Kopi 83, Blends 46, Finagle Lanka 43, Skinny Tom's Deli 33, MBC 32, Double Tree Hilton 32, CAFE 173 32, RADH 31, Riff Hikkaduwa 29, Flamingo 29, Titos 29, Malu Poke 26 | Tharindu JBJ Creations 296, Shangri-La Hotels Lanka 289, Mas Active (MAS Kreeda) 284, KDU Adventures 284, Expo Industrial Engineering 266, Antler Fabric Printers 248, Screen Line 233, Welcomehotels Lanka 222, Regal Image International 212, Jk Garments 209, Hi Fashion Holdings 187, Waterfront Properties 181 |
| Rising fast | KARABU 41 (27 vs 14, x1.9), MY PIZZA 24 (22 vs 0, new in the last 6 months) | Hotel Developers Lanka 167 (109 vs 58), Mr. Burger 112 (74 vs 38), Serenia 110 (69 vs 41) |

Also noticed on the SH side: Smart Packaging Solutions - South Retail (internal retail account) went 51 to 255 orders (x5) in six months; Trade Receivables - Retail Chain went 244 to 3. Both are accounts, not customers, so I left them out.

## 5. Other things that help test the features (item 4)

**Top sales people (portal users), last 12 months of SH orders** (`sh_sales_people.csv`): Safraz Jiffry 10,094 (30.4%), Aadil Asmath 5,460 (16.4%), Nimal Devaraj 5,339 (16.1%), Thariq Safraz 2,344 (7.0%), Adnan Iqbal 1,820 (5.5%), "Internal" 1,604, Maradana Retail Chain (used as a sales-person label) 1,475, SHIRAZ 1,286, Kamal Herath 1,087, Abdul Azeez 994, Hamzeth Mohamed - Central 565; 22 values in all, 15 with 100 or more orders. 1% of orders have a blank sales person. **Customized lines in the window**: Safraz Jiffry 536, Nimal Devaraj 214, Maradana Retail Chain 140, Adnan Iqbal 96, Thariq Safraz 90, SHIRAZ 68, Hamzeth Mohamed 55 (Aadil Asmath sells almost no customized items: 4). So a demo user who creates customized orders is Safraz, Nimal or Adnan; Aadil's orders are all stock.

**Orders per day and peak days (portal load)**, SH SOs created 20 Sep 2025-19 Sep 2026: mean 104 a day (122 on weekdays), median 115, p95 169 (172 on weekdays), maximum 230 (23 Feb 2026), then 192 (3 Nov 2025), 191 (2 Jun and 3 Mar 2026). By weekday average: Mon 142, Tue 126, Wed 120, Thu 116, Fri 106, Sat 50, Sun 5. By hour: 08-18 h carries 94%; the busiest hour (09:00) is 12% of orders, about 15 on an average weekday, about 28 on the 230-order day. Last 8 weeks: 692 SOs a week; 12-month average 639. One person can create up to 122 orders in a day (p95 31).

**Lines per order (SH window)**: mean 3.03, median 2, p90 6, maximum 98; 44% of orders have one line. **Mixed orders:** 1,465 bought-in only; 330 bought-in + customized; 211 customized only; 205 bought-in + made-for-stock; 173 all three kinds; 116 made-for-stock only; 18 customized + made-for-stock; 99 other only. Customized + bought-in = 503 orders (19.2% of all orders); at least two of the three kinds = 726 orders (27.7%). (The earlier research counted 317 customized + traded orders; I count orders holding at least one customized and one bought-in line. The difference is not reconciled.) Lines per order among orders containing the kind: customized 1.84, bought-in 2.52, made-for-stock 1.22.

**Picking location split (SH lines, `sh_pick_location_by_kind.csv`)**: SPS Kohalwila Factory (Warehouse) 4,171 (52.6%): bought-in 2,540, customized 924, made-for-stock 416; Southern Warehouse 1,967 (24.8%); SH Ranaviru Warehouse 1,302 (16.4%, bought-in only); Central Warehouse 345 (4.4%); Freeport Katunayake 132. **Customized lines:** Kohalwila 924 (68.6%), Southern 359 (26.7%), Central 61 (4.5%), none from Ranaviru. Order pick types for customized: Bulk 928, Retail 336, MTO 75, Key Customer 7.

**Order to ship, as far as the data allows** (`sps_order_to_package_ship_by_type.csv`, `sps_order_to_package_by_division_type.csv`, `sh_expected_ship_gap_by_kind.csv`, `sh_progress_by_kind_orders_before_4oct.csv`):

| Measure | Result |
|---|---|
| SPS job order created to first package (days, 8 Oct 2025-8 Oct 2026; shipment follows within hours to a day) | Customized median 10.9 (p80 22.9, n = 2,531); Ex Stock 0.0 (p80 0.1, n = 565); Internal SH 7.1 (p80 32.7); MTO 0.4 (n = 6). By division, Customized: SHPS 4.2, CPU 1.8, OPD 16.9, PCU 17.3, MOBA Punching 17.2, DPU 0.0; Ex Stock: PSU 0.0, RWU 0.0 |
| SH SO created to first shipment record, all kinds (Jun-Sep 2026, n = 10,071) | median 2.8 h, p90 68 h; Bulk and Retail 2.5 h, Sample 3.2 h, MTO about 190 h, Export and Freeport about 192 h |
| SH, stock vs customized lines | **Not derivable.** The SH shipment file ends 19 Sep, the first date with line data. Proxy at export time for lines ordered up to 3 Oct: fully invoiced bought-in 90.5%, made-for-stock 90.9%, customized 83.3% (fully packed 89.3%, 90.6%, 83.0%). Expected-shipment minus order date is a median of 1 day for every kind (p90: customized 2, bought-in 1), so it does not separate them |

Note that "shipped" in SH means packed. The 10.9-day customized median is for all SPS customized orders; it is the production lead time the dashboard will show.

**SPS job orders per day per division (dashboard load)**, created 9 Oct 2025-8 Oct 2026, Mon-Sat (`sps_jobs_per_day_by_division.csv`):

| Division | Jobs in 12 m | Per week | Mean/day | p95/day | Max/day |
|---|---|---|---|---|---|
| All | 3,724 | 71.4 | 11.8 | 24 | 33 (17 Feb 2026) |
| OPD | 1,410 | 27.0 | 4.5 | 11 | 20 |
| SHPS | 1,053 | 20.2 | 3.3 | 10 | 21 |
| PCU | 326 | 6.3 | 1.0 | 4 | 9 |
| PSU | 317 | 6.1 | 1.0 | 3 | 14 |
| RWU | 233 | 4.5 | 0.7 | 2 | 4 |
| CPU | 188 | 3.6 | 0.6 | 4.4 | 12 |
| MOBA Punching | 105 | 2.0 | 0.3 | 2 | 6 |
| Lids / FPP / DPU / Plates / Cake wrappers | 35 / 26 / 21 / 6 / 4 | 0.7 / 0.5 / 0.4 / 0.1 / 0.1 | | | |

OPD splits into PackPro and MacPro by line tag: of 12-month OPD job orders, MacPro is 303 (5.8 a week, of which 28% are SH stock builds: SH-Pizza Box, greaseproof paper, plates) and PackPro the rest.

**Artwork / die cutter "Not Available" at order time** (SPS job-order header fields `cf_artwork_availablility`, `cf_dye_cutter_availablity`, `cf_screen_plate_availability_2`; 2,478 customized orders, 9 Oct 2025-8 Oct 2026, all three fields filled on 100%; `sps_customized_readiness_fields_12m.csv`, `sps_customized_not_available_by_division.csv`): artwork not available 9.0%; die cutter not available 22.1%; screen/plate not available 8.9%; at least one of the three 23.9%. By division: OPD artwork 7.1% / die cutter 30.5% / any 33.8%; SHPS die cutter 9.1% (any 9.4%); PCU about 1%; MOBA Punching 0%; **CPU 98.6%**. The CPU figure is almost certainly a default value on the PACKSERV pouch-packing jobs, not a true state; without CPU the rate is artwork 3.3%, die cutter 17.5%, any 19.2%. The monthly artwork rate jumped from about 3% to 22% in Jul 2026 only because CPU jobs started that month. Since Taco Bell die cutters read "Not Avaialble" on 28 of 35 lines of the leading wrap, the ready-to-run chip will show "die cutter missing" for many real OPD jobs: good for testing the chip, but expect it to look red. SH has no such field, so the SH share is not derivable.

## 6. The demo filter: comparison (item 5)

**How the dashboard's calls split** (README of the 8 Oct study and `apimodel.py`; variant A, polls `SO list + bundles list`, plus the 43-page nightly full header read, plus one detail call per changed (SO or document, interval)): at 1-min the fixed part is 1,440 x 2 + 43 = 2,923 calls/day; at 2-min 1,483; at 5-min 619. Details are the rest: median 381 / 343 / 314. **A filter changes only the detail part, and only if the filter fields are on the list row.** I checked that the saved list rows (`pulls/so_created_p001.json`) carry `cf_order_received_from`, `cf_manufacturing_division`, `cf_order_type`, `reference_number` and `salesperson_name`; they do not carry line items. So customer, division and order-type filters are free at list time; **item filters need a detail call per SO** (or a Zoho list filter on item, which I could not verify). In the model, events without an SO link (about 21 calls/day) disappear under any filter, which is why "no filter by item" shows 3,283, not 3,304.

Covered shares: SPS = job orders created 9 Oct 2025-8 Oct 2026 (3,724); SH = lines 19 Sep-17 Oct (7,923). Items for SPS were ranked on the same 12 months (in-sample); out-of-sample checks (rank on Oct 2025-Mar 2026, test on Apr-Sep 2026) are in `filter_item_topN_coverage_sps.csv`. Calls are variant A, SO list + bundles, 1-min and 5-min, median / p95 / max (`filter_comparison.csv`, `dashboard_api_calls_by_filter.csv`).

| Filter | SPS job orders covered (per week) | SH lines covered (per week) | Calls/day 1-min | Calls/day 5-min |
|---|---|---|---|---|
| (a) 8 key customers only (header rule) | 260 = 7.0% (5.0) | 1,386 = 17.5% (335) | 2,964 / 3,139 / 3,512 | 656 / 785 / 1,057 |
| (a2) same, also catching key-customer items logged under Standard Holdings | 263 = 7.1% | same | 3,127 / 3,389 / 5,046 (every SH-logged SO must be fetched to learn its owner) | 779 / 975 / 2,673 |
| (b) top-50 items | 825 = 22.2% in-sample, 20.6% out of sample (15.9) | 2,895 = 36.5% (699) | 3,283 / 3,585 / 6,149 (no saving: items known only after detail) | 913 / 1,145 / 3,732 |
| (b2) top-100 items | 1,119 = 30.0% (24.6% out of sample) | 3,803 = 48.0% (918) | same as (b) | same |
| (c) key customers + top-50 items | 1,001 = 26.9% (19.2) | 3,346 = 42.2% (808) | same as (b) | same |
| (c2) key customers + top-100 items | not run for SPS | 4,125 = 52.1% (996) | | |
| (d) key customers + whole PSU and RWU | 810 = 21.8% (15.6) | n/a | 3,011 / 3,203 / 3,631 | 690 / 840 / 1,296 |
| Stage S1 (section 7) | 1,763 = 47.3% (33.9) | 2,385 = 30.1% (576) | 3,073 / 3,287 / 3,889 | 745 / 906 / 1,538 |
| Full sync | 3,724 = 100% (71.6) | 7,923 (1,945) | 3,283 / 3,585 / 6,149 | 913 / 1,145 / 3,732 |

Reading it honestly:
- **The full sync fits.** Even the 1-min worst day (6,181) is under 7,500, but not under the dashboard's own 4,500 cap, and it leaves 819 once inventory's 500 is reserved. At 2-min the worst day is 4,676 and the median 1,826; at 5-min 3,764 and 933.
- **What the filter really buys:** (1) focus (fewer jobs on screen: 34 a week instead of 72); (2) protection on bulk-edit days (S1 1-min max 3,889 vs 6,181) because mass edits mostly touch jobs outside the filter; (3) a modest 7% cut in median calls at 1-min. It does not buy API room at normal volume.
- **Key customers alone are the wrong filter for production**: 5 jobs a week, no PSU, RWU, SHPS, PCU or lid traffic. The customer rule also loses almost nothing by being a header rule (260 vs 263 job orders), so the SH-logged ownership logic is not worth its call cost.
- **Item filters on the SPS side are the worst** (25% of jobs for 100 items, no call saving). They work on the SH side (portal and stock reader), where 20 items cover 24% of lines.

## 7. Four-stage month plan (new requirement)

Reading of the request: Stage 1 = demo week; the Sundays after it widen the lists (S2, S3, S4); the fourth Sunday is the month-end go / hold decision (a plan-and-test point, no new list). All stage lists are in `research/data/`: `stage-summary.csv`, `stage-sps-lists.csv`, `stage-sh-customers.csv`, `stage-items.csv`, `stage-sps-jobs-per-week-by-unit.csv`, `stage-unit-feeders.csv`, `stage-sh-coverage.csv`. SPS rule = **customer in list (list-row `cf_order_received_from`) OR division in list (list-row `cf_manufacturing_division`)**. Weekly figures = 12-month average, with the last-8-weeks average (10 Aug-4 Oct) after the slash.

### 7.1 What each stage contains

| | S1 demo week | S2 Sunday 1 | S3 Sunday 2 | S4 Sunday 3 | Sunday 4 |
|---|---|---|---|---|---|
| SPS customers | 9 key names (the 8 plus the Gamma name) + 6 OPD feeders (Kiri Kopi, Titos, KARABU, Finagle Lanka, RADH, Thai Shack) + 12 SHPS feeders (Blends, MY PIZZA, Malu Poke, Mandalas Cafe, Angel Beach Hotel, Beldon, Riff Hikkaduwa, Skinny Tom's Deli, Dinemore, Canterbury Golf Club, BYD, Araliya Unawatuna Beach Hotel) = 27 names | + 4 high-volume names not already listed (MBC, Double Tree Hilton, CAFE 173, Flamingo) = 31 (the other 10 high-volume/rising names are already S1 feeders) | + 30 more OPD customers (Chanas, Hilton Weerawila, Tasty Caterers, ITC, Sheraton, Wok to Walk, ...) = 61 | none needed (all) | hold, review |
| SPS whole divisions | PSU, RWU, PCU/MOBA cups, MOBA Punching, Lids, Plates, Cake wrappers, FPP, DPU | + SHPS, CPU | same | + OPD = everything | |
| SPS job orders a week | 33.9 / 36.2 | 51.8 / 55.9 | 57.1 / 62.2 | 71.6 / 72.6 | |
| SH customers | 7 accounts (Gamma, Jaykay, Keells Super, Spar, Street Burger, Norfolk, Weligama Hotel Properties) | + 12 high volume + 3 rising (Hotel Developers Lanka, Mr. Burger, Serenia) = 22 | + external accounts with 150+ orders a year not already in (4) = 26 | all external customers (1,166) | |
| SH items | top 20 by lines | top 50 | top 100 | top 200 | |
| SH lines a week (customers or items) | 576 (30%) | 929 (49%) | 1,132 (59%) | 1,741 (91%) | |
| SH orders a week (window; customer-only last 8 wk) | 252 (121) | 368 (196) | 431 (212) | 596 (598) | |
| Customized SH lines a week | 133 | 188 | 199 | 284 | |
| Other lists | named items for the three scenarios (section 8) | | | | |

**Items (`stage-items.csv`):** SH top-20 items are S1 (e.g. Wooden Spoon 16cm, Aluminium Lava Cake Cup, Paper White Straw 6mm x 20cm (Packed), Chefs Choice cling film, the AF containers and lids); ranks 21-50 join in S2, 51-100 in S3, 101-200 in S4. On the SPS side the 10 leading Ex Stock items (PSU straws, RWU cling film) and the top-5 items of each key customer (27 items) are S1. SPS items cannot filter calls (they follow from division and customer); they are the item list for the portal catalogue and the demo.

### 7.2 Units fed (`stage-unit-feeders.csv`, jobs a week, 12-month / last 8 weeks)

| Unit | S1 | S2 | S3 | S4 | Fed by (S1) |
|---|---|---|---|---|---|
| OPD (all) | 6.5 / 5.8 | 7.3 / 6.2 | 12.6 / 12.6 | 27.1 / 23.0 | Taco Bell 69 jobs a year, Kiri Kopi 50, Street Burger 38; Keells, Titos, KARABU, Finagle |
| of which MacPro | 1.2 | 1.4 | 2.3 | 5.4 | Taco Bell 13 a year, Kiri Kopi 13, Street Burger 9, RADH 8; 28% of MacPro jobs are SH stock builds (pizza boxes, greaseproof) that no customer list can catch |
| of which PackPro | 5.0 | 5.5 | 9.7 | 19.8 | Taco Bell wraps and wrappers, Street Burger |
| SHPS | 4.6 / 3.5 | 20.2 / 17.6 | same | same | Blends 53, MY PIZZA 24, Malu Poke 23, Mandalas Cafe 18 (299 customers, so the whole division is the realistic rule) |
| PSU | 6.1 / 4.8 | same | same | same | SH stock: Paper White Straw 6mm x 20cm (Packed) 141, Paper Straw White 6mm / 8mm SPS 57 / 41 |
| RWU | 4.5 / 5.4 | same | same | same | SH stock: Chefs Choice Cling Film 45x300m 96, ST-Cling Film 45x600m 83 |
| PCU / MOBA cups | 6.3 / 5.4 | same | same | same | SH stock (BG - 12oz and 8oz cups) + Street Barista Crew 9, Kai Coffee 8, Marriott 7 |
| CPU | 2.2 / 8.6 | 3.6 / 13.6 | same | same | Spar 84 a year (PACKSERV foil and plastic containers), Keells Super 23 |
| MOBA Punching | 2.0 / 2.4 | same | same | same | CAFE 173 13, THOMA 9, Chef Master 6 |
| Lids, FPP, DPU, Plates, Cake wrappers | 0.7, 0.5, 0.4, 0.1, 0.1 | same | same | same | SH stock lid (SH-Black Lid PS6), Montado 6 (FPP), Bohemian Quest 6 (DPU), SH plates and cake liners |

**Flags.**
- **Starved at any filter, whole division included:** Lids (0.7 a week; none in the last 8 weeks), FPP 0.5, DPU 0.4 (none in the last 8 weeks), Plates 0.1, Cake wrappers 0.1 (none in the last 8 weeks). They are admitted whole from S1 only so that the first job that arrives is visible; do not plan a weekly scenario around them. Together they are 1.9 jobs a week. Insert synthetic jobs if the COO wants them exercised.
- **Thin in S1:** CPU (2.2 a week over 12 months, 8.6 in the last 8 weeks because Spar and Keells started PACKSERV in July; the key customers carry it) and **MacPro** (1.2 a week in S1 and S2, 2.3 in S3). A MacPro-to-PackPro "Send next" will see only about one MacPro job a week until S3-S4; add Taco Bell Wings Box and the Kiri Kopi / RADH / Meraki items by name, or keep the S1 scenario to the same job entered twice.
- **Customer lists starve:** SHPS (a customer list gives 4.6 a week, a division gives 20.2), PSU, RWU, PCU and the small units (all SH-logged). That is why S1 includes whole divisions.
- **Cross-unit "Send next" from a single SO is rare:** only 16 SOs in 12 months (0.3 a week) carry line tags of two units. The handoff the dashboard shows comes from the item route (MacPro to PackPro, PackPro to CPU) rather than from SO lines, so plan scenarios, not statistics, for it.
- **Order types in S1** (last 8 weeks): Customized 25.4 a week, Ex Stock 10.4, Internal SH 0.4, MTO 0.1; all four appear by S3.

### 7.3 Dashboard API calls a day per stage (variant A; median / p95 / max) and room for the portal

| Stage | 1-min | 2-min | 5-min |
|---|---|---|---|
| S1 | 3,073 / 3,287 / 3,889 | 1,618 / 1,804 / 2,423 | 745 / 906 / 1,538 |
| S2 | 3,115 / 3,344 / 4,613 | 1,651 / 1,853 / 3,147 | 776 / 950 / 2,262 |
| S3 | 3,154 / 3,406 / 4,755 | 1,690 / 1,903 / 3,281 | 811 / 1,010 / 2,389 |
| S4 (everything) | 3,283 / 3,585 / 6,149 | 1,805 / 2,068 / 4,644 | 913 / 1,145 / 3,732 |

Room left on the SPS 7,500 after the dashboard's worst day and inventory's 500 (the portal's plan is 2,000 a day, spec 8.1): 2-min polling leaves S1 4,577, S2 3,853, S3 3,719, S4 2,356; 5-min leaves 5,462 / 4,738 / 4,611 / 3,268; 1-min leaves S1 3,111 but S2 2,387, S3 2,245 and **S4 only 851, which is below the portal's 2,000**. The spike days (5 May 2026 and a few others) come from bulk edits, so the sync needs the per-cycle detail cap the study recommended whatever the stage.

**Recommendation:** poll every 2 min in working hours and hourly at night (the study's hybrid); that keeps S1 to S3 under the 4,500 cap even on the worst day (S4 at 2-min peaks at 4,644, slightly over, and needs the bulk-edit cap) and at least 2,356 for the portal. 1-min is not worth the calls.

### 7.4 SH reader (rizwan@ browser, read-only) and what the filter needs

What the data says about SH limits:
- **Volume is small.** SH creates 640 SOs a week (692 in the last 8), at most 230 in a day. A full SH SO detail read of every order would be about 120 calls on a normal weekday and 230 on the worst day. The stage figures are 252 SO details a week in S1 (about 50 a weekday), 368 in S2, 431 in S3, about 600 in S4.
- **The spec ceilings** (order-portal spec 8.3): at least 1,200 ms between requests (50 a minute), at most 40 per cycle, at most 6,000 a day, 200 a minute across all tools on :9333. SO details fit easily. **The item list, not the customer list, sets stock freshness:** the spec reads stock for at most 20 items per cycle with a 5-minute cache, so a list of N items is refreshed every ceil(N/20) x 5 minutes: 20 items every 5 min, 50 every 15 min, 100 every 25 min, 200 every 50 min. In calls that is about 2,400 a day over a 10-hour day whatever N is (all inside the 6,000 ceiling), but the S3 and S4 lists show stock that is 25 to 50 minutes old, which is too stale for a decide screen. Keep stock reads to the S1 to S2 lists (20 to 50 items) and read others on demand.
- **Fragility, not rate:** the reader depends on a signed-in session. The 19 Sep SH document download stopped at 5,419 of 25,565 files "waiting for Rizwan's code in working hours"; the account is blocked for about 5 minutes above roughly 600 requests a minute (which locks Rizwan out too, per `zoho-inventory-browser.md`); a tab can crash while Chrome still lists it. Expect an outage or two in a month, and show "stock as of HH:MM".
- **Cheaper reading of lines:** one export call returned 30 days of SO lines on 18 Oct (7,923 lines, the xlsx used here). A daily export for the filtered customers would replace hundreds of per-SO details, if the export route is allowed for this reader (not tested here).
- **Unknown:** the SH daily API limit and whether SH lists can be sorted by change time (V12). Neither can be taken from the data.

**SPS side (itexe@):** all figures above assume the 7,500-a-day org limit holds for the itexe@ login's token. Nothing in the data contradicts it, but the data says nothing about the per-minute limit (spec V13).

## 8. Demo scenarios (item 6)

All from one real customer, **Gamma Pizzakraft Lanka (Pizza Hut and Taco Bell)**, the one account that buys all three kinds. SH sales person on 1,096 of its 1,136 window lines: Safraz Jiffry. Check stock and last order dates live before the demo; the numbers below are from the saved data.

| Scenario | Real item / order | Evidence |
|---|---|---|
| **Customized, OPD MacPro to PackPro** | **SP-Kraft Food Wrap(10 X 10 ) (Taco Bell)** (Taco Bell). Back-up with a clean ready-to-run: **SP-Burger Bag Wax Coated (Street Burger)** | SPS history 35 lines on 25 job orders, all OPD (line tag MacPro 14, PackPro 11, untagged 10), median quantity 20,000 (range 288-51,000), last ordered 12 Sep 2026, Job Nature "Reorder" on 32 of 35, artwork Available, die cutter "Not Available" on 28 of 35 (shows a red chip). SH side: 16 lines in the window under Gamma. Street Burger bag: 34 lines/25 job orders, last 5 Oct 2026, artwork and die cutter Available on 28 of 33 (a green chip). MacPro-heavy alternative: SP-Taco Bell Wings Box (4.5 x 3.2 x 1.5) |
| **Made-for-stock, PSU** | **Paper White Straw 6mm x 20cm (Packed)** | SH: 128 lines on 128 orders in the window, 115 of them from Gamma, usual line quantity about 1,000-2,000; SPS: 141 Ex Stock lines on 139 job orders in 12 months (average about 13,600 pcs per job), job ref style "PSU/BTN/1000", 100% logged under Standard Holdings; PSU makes 6.1 a week |
| **Bought-in** | **Wooden Spoon 16cm** (alternative with more imports: Aluminium Lava Cake Cup) | SH: 261 lines on 261 orders (199 Gamma), average 594 per line, picked at Kohalwila; 34 PO lines all-time, 24% in a foreign currency (local and import suppliers both); the cake cup has 57% foreign-currency PO lines |
| **Mixed order** | **SH SO ATXSO261017851**, 17 Oct 2026, Gamma Pizzakraft Lanka, Safraz Jiffry, status invoiced, all six lines picked at SPS Kohalwila | 3 customized: SP-Kraft Food Wrap (Quesadilla Pouch) (Taco Bell) 1,000; SP-Kraft Food Wrap(10 X 10 ) (Taco Bell) 500; SP-Taco Sleeve 5.4X6.7Inch (Taco Bell) 500. 2 bought-in: Wooden Spoon 16cm 1,000; Wooden Fork 16cm 200. 1 made-for-stock: Paper White Straw 6mm x 20cm (Packed) 2,000. Gamma has 116 mixed orders in 4 weeks; two shorter real ones are ATXSO261017828 (Hut Cafe cups plus straws and a lava cup, 5 lines) and ATXSO261017815 (AF container, its lid, spoon, straws, 4 lines) |

The Taco Bell wrap on SH is ordered 500 at a time (stock to customer), but its SPS job is 20,000 (a production batch). That difference is the stock-or-production decision the portal adds; use it in the script.

## 9. Confidence and gaps

- **High:** SPS job-order counts by type, division and month (headers equal the xlsx month by month); SH monthly order counts; per-day and per-week loads; the API model (it reproduces the 8 Oct study to the call).
- **Medium:** kind split (see section 1; grey customized lids); key-customer name matches (unconfirmed by the owner); attribution of SH-logged SPS lines (24 Sep rule); import share (currency proxy).
- **Low / not derivable:** SH line-level trends by kind beyond 4 weeks; SH order-to-ship by kind (shipment file ends 19 Sep, line data starts 19 Sep); SH share of "Artwork / die cutter not available"; Courtyard Marriott on the SH side (no account found); the Zoho list filter by item (unverified); the SH daily API limit; whether "Sales by Item" is invoice-based.
- The earlier research said SPS headers were "the most recently touched" 8,571. The monthly match to the full SPS export says they are the complete register from Apr 2024, so 12-month and 3-month figures here are full counts.
- The Jan 2027 reorder pilot, finance items and LKR values are out of scope and not used.
