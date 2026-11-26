# Custom order portal: where stock sits and the routing rule

Prepared 17 Oct 2026. Every number below comes from `scripts/stock_routing.py` (output `data/stock-routing-summary.json`, `data/customized-stock.csv`, `data/division-routing.csv`). Read-only on all sources. SH and SPS numbers are never added together.

## Answer in four lines

1. The routing rule "in stock -> Rizwan's team, else -> production managers" is right in shape, but **today's history says almost nothing ships from stock**: in the last 12 months only 1 of 3,527 order lines on customized items was entered as `Ex Stock` (3,422 were `Customized Order`), and only 2.4% of 2026 `Customized Order` lines were packed within a day (median 17 days to first package).
2. On the stock snapshots I hold, a typical customized order is fully covered by SH stock for **10.6%** of last-12-month lines, by SPS stock only (not SH) for 1.3%, partly covered somewhere for 30.6%, uncovered for 42.8%, and **unknown for 14.7%** (no matching SH item).
3. SPS finished stock does not sit in the Finished Goods warehouse. It sits in **SPS Work In Progress** (594 of 2,480 stock-tracked customized items positive, 1,506,078 units); Finished Goods has 0 positive items.
4. Division to manager mapping is still the 8 Oct **draft**. 12.2% of last-12-month production lines resolve to Paper Cup Unit (PCU) which has **no manager**, and 0.6% cannot be resolved to a unit at all.

## (a) Where stock of customized items sits

### SPS side (item list and per-warehouse pull, 19 Sep 2026)

Source: `/root/exports/zoho/native/2026-09-19/sps/items.json` (`cf_fg_type = Customized`, 2,708 items; 2,480 track inventory) and `stock_by_warehouse.json` (warehouses `wip` = SPS Work In Progress, `rm` = Raw Material Warehouse, `fg` = Finished Goods).

| Warehouse | Customized items with stock > 0 | Items negative | Units (positive only) |
|---|---|---|---|
| SPS Work In Progress | 594 | 6 | 1,506,078 |
| Raw Material Warehouse | 1 | 0 | 1,760 |
| Finished Goods | 0 | 1 | 0 |

Supporting fact: of 10,596 SO lines, 10,577 have `Warehouse Name = SPS Work In Progress` and 19 have `Finished Goods` (`Sales_Order.xlsx`, column `Warehouse Name`). So SPS sells out of the WIP warehouse. A portal that reads only "Finished Goods" would see zero stock for everything.

Which stock number to trust: in `items.json`, `stock_on_hand` equals `actual_available_stock` for all 2,480 tracked customized items (physical basis), while `available_stock` differs for 50 (accounting basis). I use **free to promise = min(stock_on_hand, available_for_sale)**. The 19 Sep list has no committed-quantity field, so `available_for_sale` is Zoho's own netting of open orders and I could not verify its basis. Marked as an open point.

### SH side (item detail pull via the full-access login, 28 Sep 2026)

Source: `/root/exports/zoho/native/2026-09-28/sh-rizwan/items/detail/batch_*.json` (12,081 SH items; per-location stock for 10 locations). In that pull, `stock_on_hand` equals `actual_available_stock` for all 11,367 items with locations, and `actual_available_for_sale_stock = stock_on_hand - actual_committed_stock` (checked on batch 5, 500 of 500 items). I use **`actual_available_for_sale_stock`** as SH free to promise. Do not use SH `available_stock`: it differs from physical on 1,162 of 11,367 items (example: `SP-Kraft Box 1200ml (180x120x50)mm (Cafe 173)` has physical 0 but `available_stock` 2,062 and 2,079 committed).

### Matching SPS items to SH items

Method, in order: (1) exact name after trimming spaces and ignoring case; (2) name with all punctuation and spaces removed. No fuzzy matching. SKU matching was tested and rejected (only 184 of 2,708 SPS customized items have a SKU; 104 match).

| | Items | Exact | Punctuation-stripped | No match |
|---|---|---|---|---|
| All 2,708 customized | 2,708 | 1,413 | 225 | 1,070 |
| Ordered in last 12 months | 1,269 | 945 | 81 | 243 (19%) |

One match was ambiguous (two SH items, both active) and was left unmatched. Unmatched ordered items are mostly new designs not yet created in SH (not verified item by item). I did not check that matched pairs are physically the same product beyond the name.

### SH stock location of matched customized items (28 Sep, items with stock > 0 at that location)

| SH location | Items | Units |
|---|---|---|
| SPS Kohalwila Factory (Warehouse) | 453 | 1,595,577 |
| Southern Warehouse | 111 | 98,493 |
| 3PL Warehouse (DWW) | 11 | 246,875 |
| Central Warehouse | 40 | 30,741 |
| SPS Work in Progress WIP | 25 | 16,975 |
| SH Ranaviru Warehouse | 1 | 100 |

Open: the SH "SPS Kohalwila Factory" location (1.6M units) and the SPS WIP warehouse (1.5M units) may hold the **same physical goods** counted in two ledgers. I cannot tell from the exports, so the portal must treat them as two independent readings and never add them. Only a handful of items are positive on both sides (for example SH FULL and SPS FULL both: 5 items among last-12-month items).

### Stock class per item (`customized-stock.csv`)

`FULL` = free stock >= the item's median order quantity (median over its Customized Order and MTO lines in the last 12 months, else all lines). `PARTIAL` = above 0 but below it. `NONE` = 0 or negative. `UNKNOWN` = not stock-tracked, or no SH match. Last-12-month items (1,269):

| | SH (28 Sep) | SPS (19 Sep) |
|---|---|---|
| FULL | 96 | 17 |
| PARTIAL | 180 | 219 |
| NONE | 750 | 1,033 |
| UNKNOWN | 243 | 0 |

Weighted by last-12-month order lines (3,527 lines on customized items, all order types): SH FULL 10.6%, PARTIAL 14.0%, NONE 55.3%, UNKNOWN 20.1%; SPS FULL 1.9%, PARTIAL 17.9%, NONE 80.1%.

Both snapshots are old (19 and 28 Sep). The shares will have moved; the **shape** (most items have no covering stock) is what to rely on, not the decimals.

## (b) History: Ex Stock versus Customized Order

Source: `/root/exports/zoho/sps/2026-09-27/item1/Sales_Order.xlsx` (10,596 lines, 18 Mar 2023 to 25 Sep 2026), `CF.Order Type`, joined to the item master by `Product ID` (13 lines not in the master). First package date from `Package_ALL.xlsx` (`SO Number` + `Item Name`, 9,734 of 10,596 lines matched); first invoice date from `Invoice.xlsx` (`Sales Order Number` + `Item Name`, 10,213 matched). Lag = days from `Order Date`.

Lines on **Customized** items by order type:

| Order type | Lines | Median days to first package | Packed same day | Packed within 3 days | Median days to invoice |
|---|---|---|---|---|---|
| Customized Order | 7,411 | 10 | 24.2% | 31.5% | 12 |
| Ex Stock | 254 | 0 | 59.8% | 63.5% | 0 |
| Make to Order (MTO) | 28 | 0 | 88.9% | 94.4% | 0 |
| Internal SH Order | 126 | 21 | 5.8% | 12.6% | 21 |

Ex Stock lines on non-customized items for comparison: 2,064 lines, median 0 days, 61.7% same day.

Findings:
- **Ex Stock on customized items died out.** By year, customized-item lines are Ex Stock / Customized Order: 2024 = 213 / 1,631; 2025 = 40 / 3,207; 2026 = 1 / 2,571. Of 2,088 customized items ever ordered, 39 were only ever Ex Stock, 56 were both, 1,919 only Customized Order.
- **The 24% "same day" for Customized Order is a 2024 effect.** Same-day share by year: 2024 66.4% (median 0 days), 2025 23.5% (median 8), 2026 2.4% (median 17, p80 27). My reading is that 2024 SOs were often entered after the goods were already made; I did not verify that.
- So in 2026 the sales team never marks a customized item as in stock, and nothing in Zoho tells anyone the stock existed. The portal's stock check is **new behaviour**, not a digitised copy of today's practice.
- Ex Stock lines that were not quick: 36% took more than 3 days (p80 = 26 days), so "Ex Stock" did not always mean "on the shelf".

## (c) Division to production manager

Rule used (spec `wiki/specs/2026-10-08-pd-managers-full-release.md` section 8.0b): line tag `Division` first, with the "MOBA Unit" tag refined by a cup/lid/cake/plate header; else the header unless it is the OPD bucket; else unresolved. Tag aliases from the preview spec (`2026-09-28-pd-manager-preview.md:771`) and `002-seed.sql`. Three tag spellings are **not** in the spec and I assumed them from the unit name: `Food Product Processing Unit`, `Digital Printing Unit`, `Rewinding Unit` (42 production lines affected).

People come from the **lead's working draft** in spec section 1d plus the owner's 8 Oct answers F2.3 to F2.5. Pairs are not seeded (`002-seed.sql` header) and question Q-U (9 Oct) is still open in the spec, so every pair below is a draft.

Basis: Customized-item lines with `CF.Order Type` = Customized Order or MTO (7,439 all time, 3,423 in the last 12 months). Full table: `data/division-routing.csv`.

| Unit | Manager + coordinator (draft) | Lines last 12m | Share |
|---|---|---|---|
| PACKPRO | Ishan + Umanda | 1,191 | 34.8% |
| SHPS | Mubeena + Madushi | 1,092 | 31.9% |
| **PCU** | **none** | 419 | 12.2% |
| MACPRO | Shihar + Nimesha | 313 | 9.1% |
| MOBA | Ranga + Nimesha | 245 | 7.2% |
| CPU | Ranga + Nirmani | 133 | 3.9% |
| **(unresolved)** | admin confirms | 21 | 0.6% |
| FPP | Ranga + Nirmani | 9 | 0.3% |
| DPU, MOBA_P | none (F2.5; unused) | 0 | 0% |
| OPD, PSU, RWU, PCLU, CWU, PPU | draft pairs exist | 0 | 0% |

Divisions with no manager: **PCU** (draft says unknown; F2.4 says MOBA-tagged cups are Ranga's, which conflicts until Q-U is answered; all 672 PCU lines carry the "MOBA Unit" tag with a Paper Cup Unit header), **DPU** (kept with none by the owner; 28 lines, all before the last 12 months), **MOBA_P** (unused). OPD is shared by two pairs and the first to Send next decides (F3.1), but no customized line resolves to OPD directly. PSU and RWU have no customized lines at all: all 610 Paper Straw Unit and 17 Rewinding Unit tag lines are on Non Customized items (`Item master cf_fg_type`), so a customized-only portal never reaches Ishan through those units, only through PACKPRO.

Unresolved lines (809 all time, 21 in 12 months) have a blank tag and the OPD bucket header. 40 production lines have a tag that disagrees with the header; the tag wins (spec rule 4).

## (d) Proposed routing decision table

"Free stock" always means free to promise (physical minus committed), compared with the ordered quantity on the actual order line, not the item median.

| Case | Test, read live at submit | Goes to | Notes |
|---|---|---|---|
| 1. Full stock | SH free stock (all SH locations the owner allows, not summed with SPS) >= ordered qty | Rizwan's team | Show which location. Reserve nothing in Zoho (portal is read-only). |
| 2. Full stock, SPS only | SH below qty, SPS free stock >= qty | **Question for the owner** | 1.3% of lines. Either Rizwan's team asks SPS to release it, or the production manager confirms from the shelf. Do not auto-route. |
| 3. Partial stock | 0 < best single-ledger free stock < qty | Production managers, with the stock figure shown | Do not split the order automatically. Show "SH has N, ordered M"; the manager or Rizwan's team decides (30.6% of lines). |
| 4. No stock | both ledgers read, both <= 0 | Production managers of the resolved unit | The normal case today (42.8%). |
| 5. Unknown stock | item not stock-tracked, no SH match, or ambiguous SH match | Production managers, flagged "stock not checked" | 14.7% of lines today. Fixing item matching in SH raises case 1 and 3 hits. |
| 6. Stale or failed read | Zoho read older than the freshness limit or errored | Production managers, flagged "stock not checked", stock values hidden | Never route to Rizwan's team on stale data. |
| 7. Unit has no manager | resolved unit is PCU, DPU or unresolved | Admin Unassigned list (as the dashboard does) | PCU alone is 12.2% of lines until Q-U is answered. |

Rizwan's team routing should be a notification plus a task in the portal, not a Zoho write (Zoho stays read-only). If the owner prefers "everything goes to production managers and Rizwan's team sees stock-covered orders as a second list", the same table works with case 1 copied to both.

### What the portal must read live from Zoho, and how fresh

| Data | Source | Proposed freshness | Why |
|---|---|---|---|
| SH free-to-promise per item per location | SH item detail: `actual_available_for_sale_stock`, location rows | At order submit and again when Rizwan's team opens it; cache at most 5 minutes | Stock moves with every package and transfer |
| SPS free-to-promise per item | SPS item: `stock_on_hand`, `available_for_sale` | Same | Same |
| Item to SH item match | stored mapping table built from `customized-stock.csv`, reviewed by hand | Rebuilt weekly | Name matching misses 19% of ordered items |
| Open commitments | included in the committed fields above | Same call | Avoids double-promising the same stock |
| Item master (customized flag, unit/division tag) | SPS item `cf_fg_type`, `cf_bu` | Daily | Rarely changes |
| Stale limit | none stored | Treat as stale after 15 minutes without a successful read | My suggestion, owner to confirm |

API budget: SPS limit is 7,500 calls a day, 0 used in 30 days (`reports/2026-10-07-zoho-api-limit/`). The SH limit is still unknown and SH is read through the signed-in browser session for now (`/root/CLAUDE.md`, 7 Oct), so the SH reader must be swappable (snapshot now, API later) and case 6 will fire often until SH API access exists.

## What I could not determine

- Whether SH "SPS Kohalwila Factory" stock and SPS WIP stock are the same goods (double counting risk).
- Which SH locations Rizwan's team can actually dispatch from. All ten locations are in the data; I used none of them selectively.
- The basis of SPS `available_for_sale` (no committed field in the 19 Sep list).
- Whether the 2024 same-day packing was real fast service or after-the-fact entry.
- The confirmed manager for PCU and whether Q-U pairs changed after 9 Oct.
- Current stock: both snapshots are 19 and 28 Sep, about three weeks old on 17 Oct. A fresh read is needed before any threshold is tuned.

## Files

- `data/customized-stock.csv`: one row per customized SPS item (2,708) with both stock readings, match method, order history, modal unit.
- `data/division-routing.csv`: one row per unit with draft people, line counts and notes.
- `data/stock-routing-summary.json`: every number above.
- `scripts/stock_routing.py` (needs `scripts/cache_sources.py` and `scripts/cache_sh_items.py` run first into a scratch dir; `python3.12 -I scripts/stock_routing.py CACHEDIR OUTDIR`).
