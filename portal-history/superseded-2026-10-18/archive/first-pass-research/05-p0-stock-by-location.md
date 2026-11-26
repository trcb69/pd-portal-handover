# P0 - how many orders would route to SH stores, by location set

Spec step P0 (`wiki/specs/2026-10-17-custom-order-portal-spec.md` section 11). Script: `scripts/stock_by_location.py`; numbers: `data/stock-by-location-summary.json`.
Run: `python3.12 -I scripts/stock_by_location.py <Sales_Order.xlsx> data/customized-catalogue.csv data/customized-stock.csv <this folder>`.

**Snapshot caveat.** SH stock is the 28 Sep 2026 pull (raw `batch_*.json`). It is stale: read it for shape, not as a forecast. SPS stock is not used and is never summed with SH.

## Basis and method

- 1,269 items / 3,527 lines = customized items ordered in the 12 months to 25 Sep 2026 (`stock_routing.py` window; line counts match it for every item).
- SPS to SH item match (reused from `stock_routing.py`: normalised name, then punctuation-stripped name): 1,026 of 1,269 items matched (80.9%); 243 items / 708 lines (20.1%) have no SH match, so they are UNKNOWN.
- Free stock for a set = sum over the set's locations of `location_actual_available_for_sale_stock`. Other fields: `location_stock_on_hand`, `location_actual_committed_stock`. Unit = item-level `unit` (present on 11,804 of 12,081 SH items).
- Typical qty = `typical_order_qty_median` from `data/customized-stock.csv`. The catalogue CSV has no such column (it has `median_qty`, over all lines), so the stock CSV was used because `stock_routing.py` writes it.
- Locations (exact strings, all present in the data): set (a) = `Southern Warehouse (Warehouse)`, `Central Warehouse (Warehouse)`, `3PL Warehouse (DWW)`; set (b) = (a) + `SPS Kohalwila Factory (Warehouse)`.
- Class order: UNKNOWN, UNIT_MISMATCH, FULL, PARTIAL, NONE. An extra class NO_CATALOGUE_UNIT (11 items / 11 lines, 0.3%) holds matched items missing from the catalogue CSV; these have no unit to compare and would go to production anyway.
- **Identity check** stock_on_hand - actual_committed = actual_available_for_sale: 113,670 location rows checked (45,468 in the four set locations), **0 failures**, 0 rows with a missing field.
- Rule 2 (end customer `CF.Order Received from` = "Standard Holdings (Pvt) Ltd" always goes to production): 106 of 3,527 lines (3.0%). It is evaluated before the stock classes.

## Results: lines and % of 3,527, without rule 2

| Class | (a) strict | (a) alias | (b) strict | (b) alias |
|---|---|---|---|---|
| UNKNOWN | 708 (20.1%) | 708 (20.1%) | 708 (20.1%) | 708 (20.1%) |
| UNIT_MISMATCH | 1,656 (47.0%) | 624 (17.7%) | 1,656 (47.0%) | 624 (17.7%) |
| NO_CATALOGUE_UNIT | 11 (0.3%) | 11 (0.3%) | 11 (0.3%) | 11 (0.3%) |
| **FULL (to stores)** | **38 (1.1%)** | **69 (2.0%)** | **112 (3.2%)** | **271 (7.7%)** |
| PARTIAL | 49 (1.4%) | 64 (1.8%) | 273 (7.7%) | 400 (11.3%) |
| NONE | 1,065 (30.2%) | 2,051 (58.2%) | 767 (21.7%) | 1,513 (42.9%) |

"Alias" = a second view where nos, pcs, piece, pieces, each count as the same unit (lower/trim). Box and Pks/PACK stay distinct.

## With rule 2 (106 SH-own lines forced to production), % of all 3,527 lines

| Class | (a) strict | (a) alias | (b) strict | (b) alias |
|---|---|---|---|---|
| Forced to production by rule 2 | 106 (3.0%) | 106 (3.0%) | 106 (3.0%) | 106 (3.0%) |
| UNKNOWN | 670 (19.0%) | 670 (19.0%) | 670 (19.0%) | 670 (19.0%) |
| UNIT_MISMATCH | 1,601 (45.4%) | 586 (16.6%) | 1,601 (45.4%) | 586 (16.6%) |
| NO_CATALOGUE_UNIT | 11 (0.3%) | 11 (0.3%) | 11 (0.3%) | 11 (0.3%) |
| **FULL (to stores)** | **38 (1.1%)** | **69 (2.0%)** | **112 (3.2%)** | **264 (7.5%)** |
| PARTIAL | 44 (1.2%) | 56 (1.6%) | 268 (7.6%) | 395 (11.2%) |
| NONE | 1,057 (30.0%) | 2,029 (57.5%) | 759 (21.5%) | 1,495 (42.4%) |

Rule 2 barely moves the stores share: it removes only 7 FULL lines (set (b) alias 271 to 264); the other 99 SH-own lines were already production.

## (SPS unit to SH unit) pairs among strict mismatches (items, identical for both sets)

pcs to nos 210; pcs to Nos 123; box to nos 89; box to pcs 51; nos to PCS 25; Pks to PACK 19; box to Nos 16; Pks to PCS 9; pcs to box 7; nos to PACK 6; (blank) to pcs 3; (blank) to Nos 2; nos to pcs 1. Total 561 items.
Most are the nos/pcs spelling (about 360 of 561 items); the rest are real differences (box vs pcs/nos, Pks vs PACK/PCS).

## Conclusions

1. **Set (a) is inert under the strict unit rule: FULL = 1.1% of lines (38), below the 2% threshold**, with or without rule 2. Q2 should carry "With the suggested locations, almost no order would go to Rizwan's team."
2. With the nos/pcs alias, set (a) FULL is 2.0% (69 lines; 1.96% before rule 2 and after) - on the threshold, still near-inert.
3. Adding Kohalwila (set b) lifts FULL to 3.2% strict and 7.5-7.7% with the alias. Even the best view leaves over 90% of lines in production. Kohalwila is also the location in question for double-counting with SPS WIP (Q2), which this data cannot settle.
4. The unit rule is the largest single class (47.0% strict, 45.4% with rule 2). The alias table cuts it to 16.6-17.7% but most of the freed lines fall to NONE, not FULL, so D14 helps stores only slightly (set (a) +31 FULL lines, set (b) +159). Per D14's test (mismatch share larger than FULL share) the mismatch share exceeds FULL in every view.
5. Another 20% of lines are UNKNOWN (no SH item match); fixing the name match would not change the picture much, since NONE dominates matched items.

## Not determined / limits

- Stale 28 Sep snapshot: current stock could differ materially.
- Quantity is one typical median per item, not each line's real qty, so FULL is an item-level approximation per line.
- No netting (spec 3.3 `netted`) is simulated; it can only lower FULL.
- The match rate depends on name matching only (no SKU match tried).
