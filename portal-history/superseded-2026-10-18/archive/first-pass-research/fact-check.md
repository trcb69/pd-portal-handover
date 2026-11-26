# Fact-check of 01-04 (independent recompute)

Prepared by Abdul Hadhee | IT Executive. Checked 17 Oct 2026 with my own fresh scripts (not the ones in `scripts/`), read-only on `/root/exports`. Raw sources: SPS `Sales_Order.xlsx` and `Invoice.xlsx` (27 Sep), `Item.xlsx`, `Package_ALL.xlsx`, `Shipment_ALL.xlsx` (16 Sep), and for the stock-routing claims `items.json` and `stock_by_warehouse.json` (19 Sep). My scripts live in the scratchpad, not in this folder.

Result: 27 of the 28 listed claims CONFIRMED (some with a definition note), 1 partly CONFIRMED / CANNOT CHECK in full. 4 small MISMATCHES found among the extra spot-checks (below). None changes a conclusion.

## A. The listed claims

| # | Claim | Verdict | My value / note |
|---|---|---|---|
| 1 | Catalogue 2,537 (2,519 Active + 18 Inactive ordered since 2024-09-25) | CONFIRMED | 2,537; 18 inactive ordered. |
| 2 | Live (ordered since 2025-09-25) 1,257 | CONFIRMED | 1,257. |
| 3 | 684 one-line items; 187 with 10+; top 100 = 25.2% | CONFIRMED | 684 / 187 / 25.15% of 7,765 catalogue lines. |
| 4 | 486 Active never ordered (228 service, 121 RTP) | CONFIRMED | 486 (258 goods + 228 service); 121 names contain "RTP". |
| 5 | 1,186 of 1,257 live items end in a bracket (94%) | CONFIRMED | 1,186 end with `( ... )`. |
| 6 | SH as "Order Received from" 5,075 of 10,596 (48%) | CONFIRMED | 5,075. |
| 7 | 640 distinct end customers; 8 case/punctuation groups; 42 near variants | CONFIRMED for 640 and 8; 42 CANNOT CHECK | 640 distinct. With letters and digits only (case, punctuation, spaces ignored) I get 8 groups. 42 depends on the similarity rule, which I did not rebuild. |
| 8 | 26 SO lines with items missing from the master, 2026-08-24..09-24 | CONFIRMED | 26 (25 Customized Order, 1 Internal SH). |
| 9 | Last 12 m customized-item lines Ex Stock: 1 of 3,527 (3,422 Customized Order) | CONFIRMED, with a note | Needs the **19 Sep `items.json`** item master (3,527 / 3,422 / 1). With the 16 Sep `Item.xlsx` I get 3,514 / 3,410 / 1 (window `> 2025-09-25`). 01 uses 16 Sep Item.xlsx, 02 uses 19 Sep items.json (2,708 Customized items vs 2,695), so the two files quote slightly different item counts. The doc says so only partly. |
| 10 | Customized Order lines packed within 1 day: 2026 2.4%, median 17 d; 2024 66.4%; 2025 23.5% | CONFIRMED | Share is of lines that have a package: 2026 2.36% (of all lines 2.14%), 2025 23.5% (23.2%), 2024 66.4% (65.1%); medians 0 / 8 / 17. The denominator is "packed lines" and should be stated. |
| 11 | 594 items / 1,506,078 units positive in WIP; FG 0; 2,480 tracked; 10,577 of 10,596 lines WIP | CONFIRMED | 594 / 1,506,077.6 / FG 0 / 2,480 tracked / 10,577 WIP lines (19 FG). RM warehouse has 1 item with 1,760. |
| 12 | SPS to SH match 1,638 of 2,708 (60%); last 12 m 1,026 of 1,269 (81%) | CONFIRMED (arithmetic from the CSV) | 1,413 + 225 = 1,638; 945 + 81 = 1,026. I did not re-do the name matching against the SH item file. |
| 13 | Routing simulation 10.6 / 1.3 / 30.6 / 42.8 / 14.7 | CONFIRMED (arithmetic from the CSV) | I recomputed the five buckets from `customized-stock.csv` classes. The classes themselves (SH stock) are not independently rebuilt. |
| 14 | No-manager lines PCU 12.2% + unresolved 0.6% = 12.9% | CONFIRMED | 440 of 3,423 = 12.85%, shown as 12.9 (12.2 + 0.6 on the table = 12.8; rounding). Unit counts for tags that map 1:1 (PackPro 1,191, MacPro 313, CPU 133, FPP 9, blank 25) match my count of the `Division` tag. The PCU-from-MOBA-tag split depends on the 8.0b header rule and is not rebuilt. |
| 15 | Ex Stock lines on customized items: 254, median 0, 59.8% same day, 36.5% over 3 d | CONFIRMED | 254; 249 packed; median 0; 59.8%; 36.5% (of packed). |
| 16 | 2,414 SOs / 3,449 lines, 201 / 287 a month | CONFIRMED | 2,414 / 3,449. |
| 17 | Per working day mean 7.7, median 6, p95 20, max 35; lines mean 11.0, p95 31 | CONFIRMED | 7.71 / 6 / 20 / 35; 11.02 / 31.4 (Mon-Sat, 313 days, no holiday calendar). Worst day 18 Feb 2026, 35 SOs / 51 lines. |
| 18 | 70.2% single-line, mean 1.31, p95 2, max 5 (5,762 SOs) | CONFIRMED | 70.2% / 1.306 / 2 / 5. |
| 19 | Lead time 2026 median 18, p80 29 (OPD 21/31, SHPS 14/25, PCU 21/26, MOBA 20/25, CPU 7/19) | CONFIRMED, with a note | Holds only for orders 2024-04-01..2026-07-31 (the 03 doc states this window; the claim text does not). On the full file to 25 Sep I get 17 / 27. |
| 20 | Ex Stock median 1 d, p80 5 d | CONFIRMED | 1 / 5 (n = 1,569, same window). |
| 21 | On time 45.3%, median 2 d late, p80 12 d late, n = 2,201 | CONFIRMED | 45.3% / 2 / 12 / 2,201 (orders 2025-08-01..2026-07-31). |
| 22 | Backlog 229 lines / 217 SOs of 361 confirmed; 90 older than 180 d; oldest 905; 121 of 208 past expected | CONFIRMED | 229 / 217 / 361 / 90 / 905 / 121 of 208 (strictly before 25 Sep; 136 if "on or before"). |
| 23 | 18.4% of lines have a cancel, 1.1% of qty; 16.3% partially invoiced; 20.8% multi-shipment | CONFIRMED | 18.41% / 1.11% / 16.3% (1,226 of 7,523). Multi-shipment 20.76% on the 2024-04..2026-07 cohort (20.3% on all years). |
| 24 | Source constant '1', channel direct_sales, Sales Person blank 85%; Ref 100% filled, equals Job No on 51% | CONFIRMED | 7,523 of 7,523 / 7,523 / 84.7% / 100% / 51.0%. |
| 25 | Join rates | CONFIRMED | Package, shipment, invoice SO numbers all in the SO file (0 missing); shipment Packing Numbers all in packages (0 missing); SO to master 10,570 of 10,596 (10,583 using the 19 Sep items.json). |
| 26 | OP-01 22 Oct 2026; OP-14 25 Jan 2027; full release 15 Feb 2027 | CONFIRMED, with a wording note | `dev/01b-dated-schedule.md` line 288 (OP-01 start 2026-10-22) and line 301 (OP-14 2027-01-20 to 2027-01-25; full release 2027-02-15, target 11 Feb). Note: 25 Jan is the end of OP-14's build step; IT test and UAT follow and everyone-live is 15 Feb. "OP-14 go-live 25 Jan" is the wording the dev notes themselves use, but 15 Feb is when it is live for everyone. |
| 27 | Migrations 001-006 exist; 007 has no file | CONFIRMED | `ls` of `/root/dev/production-dashboard/server/db/migrations` = 001..006 + MANIFEST.json (six hashes). That a portal migration at 008 "leaves a gap" is the doc's reading of the numbering lint; I did not run the lint. |
| 28 | Old plan about 10.5 developer-weeks for OP-01..14; OP-15/16 unscheduled | CONFIRMED | `order-portal/02-process-steps.md` lines 54-58: "~10.5 developer-weeks now" and "directional, not re-verified"; OP-15/16 (~1.75 weeks) deferred. Copied, not recomputed, as the claim says. |

## B. Further spot-checks (16 numbers from 01-04)

| Source | Number | Verdict | My value |
|---|---|---|---|
| 01 s1 | Active, ordered earlier, not in last 24 m: 220; ordered 12-24 m ago only: 574 | CONFIRMED | 220 / 574 |
| 01 s1 | 7,765 catalogue lines; 7,806 lines on Customized items | CONFIRMED | 7,765 / 7,806 |
| 01 s1 | 7,399 / 254 / 125 / 28 order types on Customized items | CONFIRMED | same |
| 01 s1 | Live BU table (SHP 456, PACPRO 445, ...) | CONFIRMED | all nine rows match |
| 01 s1 | Prefix table | CONFIRMED within 2 | I get PRINTSERV- 185 / 152 live vs doc 187 / 154, and Other 76 / 19 vs 74 / 17. Three names are written `PRINTSERV -` / `Printserv-`; it is only a prefix-rule difference. |
| 01 s2 | Top 10 / 50 / 100 / 200 = 4.7 / 15.6 / 25.2 / 38.8%; 19 items with 25+ lines; 1,022 one-SO items | CONFIRMED | same |
| 01 s2 | 1,892 New Order of 7,806; 258 blank Job Nature (all 2024) | CONFIRMED | 1,892 (value is `New Order ` with a trailing space); 258, all 2024 |
| 01 s4 | 4,098 SOs where SH is the end customer | CONFIRMED | 4,098 |
| 01 s4 | **926 distinct Customized items** for those lines | **MISMATCH** | 862 by `Product ID` (843 inside the catalogue). 926 is the count of distinct item **names** (some items were renamed). |
| 01 s4 | 116 customers once, 166 with 10+, 487 in last 12 m | CONFIRMED | 116 / 166 / 487 |
| 01 s5 | SKU blank on 2,417 (live 1,216); 94 Customized Order on Non Customized, 5 NA | CONFIRMED | same |
| 01 s5 | Item Price positive on 97.2% of lines | CONFIRMED | 97.2% on Customized-item lines (96.4% on all lines; the doc should say which) |
| 01 s5 | 1,429 Customized-item lines with a cancel; live items with stock above 0: 364 | CONFIRMED | 1,429 / 364 |
| 03 | 2,074 distinct items, 1,336 reordered, 6,785 lines; median qty 500 (130 / 2,000 / 10,000) | CONFIRMED | same |
| 03 | Job nature on customized SOs: 4,252 / 1,352 / 25 / 1 / 132 | CONFIRMED | same (SO level) |
| 03 | Monthly volume grid Oct 2024 - Sep 2026 and division lines (OPD 3,331 / 2,149, ...) | CONFIRMED | every month and all eight divisions match |
| 03 | OPD 57.2% / SHPS 93.7% / PCU 22.0% single-line | CONFIRMED | same |
| 03 | Cohort 7,840 SOs; 98.1% of customized SOs have a shipment; 28 Sunday lines | CONFIRMED | 7,840 / 98.1% / 28 |
| 03, 04 | **637 distinct "Order Received from" names for customized lines** | **MISMATCH (by 1)** | 638 on Customized Order lines (640 across the whole file). |
| 04 | HEAD is `aa4837b`; 005/006 exist | CONFIRMED | `git log` top commit `aa4837b` |

## C. Mismatches to fix (all small)

1. 01 section 4: "926 distinct Customized items" should be 862 (distinct `Product ID`); 926 counts item names.
2. 03 section 3 and 04 section 2: "637" distinct names for customized lines should be 638.
3. Make explicit which item master each file uses. 01 and 03 use `Item.xlsx` 16 Sep (2,695 Customized items); 02 uses `items.json` 19 Sep (2,708). The 3,527 / 3,422 figures hold only on the 19 Sep master.
4. Say that the 2.4% / 66.4% / 23.5% "packed within a day" shares are over lines that have a package (about 1 to 2 points lower over all lines), and that the 18 / 29 lead time is for orders up to 31 Jul 2026.

## D. What I could not determine

- The 42 near-variant customer names (depends on the similarity rule).
- SH stock classes (FULL / PARTIAL / NONE / UNKNOWN) and the SH name matching: the SH item files were not rebuilt; I only checked the arithmetic on top of `customized-stock.csv`.
- The PCU versus MOBA split inside the "MOBA Unit" tag (needs the spec 8.0b header rule).
- Whether a portal migration at 008 breaks the numbering lint (I did not run `npm test`).
