# SPS customized-items catalogue (18 Oct 2026)

Output: `SPS-Customized-Items-Catalogue-2026-10-18.xlsx` (Cover, one sheet per sales person, All Items, Unassigned, Check).
Item list as of 19 Sep 2026 (saved export). Sales-person evidence also from SH order lines 19 Sep to 17 Oct (Zoho native export). No live Zoho calls in the final build.

Sources
- Items: `/root/exports/zoho/native/2026-09-19/sps/items.json`, every item with `cf_fg_type` = Customized (2,708).
- Order stats (last ordered, median qty, 12/24-month flags, end customers): `/root/Project Management/reports/2026-10-17-custom-order-portal/data/customized-catalogue.csv` (order history to 25 Sep).
- SH order lines: `/root/exports/zoho/native/2026-10-18/sh/SH_Sales_Order_2026-09-19_2026-10-18.xlsx` (7,923 lines, 2,617 SOs). An SPS item is linked to lines by normalised item name, then SKU; the sales person is the most frequent on those lines (beats the name match; disagreements in `salesperson-disagreements.csv`). Column 'Source of salesperson' = order lines / customer-name match / none.
- Sales person per customer (fallback): `/root/exports/zoho/native/2026-09-19/sh_full/salesorders.json` (SH order headers). Last 12 months to 19 Sep; if a customer has no real sales person there, 24 months, then all time. Most frequent sales person; ties noted in `pulls/rows_final.json` (`sp_note`). Dates before 2020 are ignored.
- Customer tag: last bracket in the item name, else most frequent non-SH end customer. Matched to SH customer names by words (exact = High, tag inside the SH name = Medium, close spelling or ambiguous = Low).

Rebuild
    python3 scripts/merge_items.py     # -> pulls/items_merged.json, check_items.json
    python3 scripts/build_xlsx.py      # -> the xlsx (about 1 min)

`pulls/unused-live/` and `scripts/unused-live-scripts/` hold a partial live pull (SPS items changed since 19 Sep, partial SH orders) that was stopped on request and is NOT used.

`SPS-Customized-Items-Catalogue-2026-10-18-v1-headers-only.xlsx` = previous version (customer-name match only).

v3 (tag on order lines): bracket tags in SH order-line item names -> SH customer -> sales person, used for items still unassigned. Source of salesperson = tag on order lines. Previous version: `...-v2-lines.xlsx`.
