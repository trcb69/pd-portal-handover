# 01 - Customized item catalogue for the SmartPack order portal

Prepared by Abdul Hadhee | IT Executive. Built 17 Oct 2026. Read-only on the Zoho exports; nothing was sent or changed.

Every number below comes from `scripts/build_catalogue.py` and `scripts/extra_stats.py` (full output in `data/stats.json`).

**Sources**
- Sales order lines: `/root/exports/zoho/sps/2026-09-27/item1/Sales_Order.xlsx`, sheet "Sales Order". It has 10,596 lines and the last order date is 25 Sep 2026.
- Item master: `/root/exports/zoho/native/2026-09-16/Item.xlsx`, sheet "Item" (modified up to 15 Sep 2026).
- "Last 24 months" means since 25 Sep 2024. "Live" means ordered since 25 Sep 2025. Both are counted back from the last order in the file, not from today.

**Outputs**
- `data/customized-catalogue.csv` has 2,537 rows.
- `data/end-customers.csv` has 640 rows.
- `data/stats.json` holds every statistic quoted here.

## 1. What the catalogue is, in numbers

| Measure | Count | Source |
|---|---|---|
| Item master rows / unique item IDs | 3,914 / 3,913 | `Item ID`. One raw material (RM-260gsm S/C White Board) is listed twice, once per warehouse. |
| Items with `CF.Finished Good Type` = Customized | 2,695 (2,519 Active, 176 Inactive) | Item.xlsx |
| **Catalogue rows** (Customized AND (Active OR ordered in the last 24 months)) | **2,537** | 2,519 Active + 18 Inactive that were ordered in the last 24 months |
| Active but never ordered | 486 | `order_lines` = 0 |
| Active, ordered earlier but not in the last 24 months | 220 | |
| **Live: ordered in the last 12 months** | **1,257** | `live_12m` = Y |
| Ordered 12 to 24 months ago only | 574 | |
| Order lines behind the catalogue | 7,765 | 41 further lines belong to Customized items outside the catalogue (inactive and old) |

**Who sold what.** Only 7,399 of the 7,806 lines on Customized items carry `CF.Order Type` = Customized Order. The rest are:
- 254 "Ex Stock"
- 125 "Internal SH Order"
- 28 "Make to Order (MTO)"

The portal order types therefore overlap with Zoho's existing order types. Section 5 explains how.

### Live items split by what the name says
The item name carries the product family as a prefix.

| Prefix | All | Live |
|---|---|---|
| `SP-` | 1,135 | 695 |
| `CP-` | 633 | 302 |
| `PRINTSERV-` | 187 | 154 |
| `PACKSERV` | 81 | 68 |
| `SH-` | 39 | 18 |
| Other | 74 | 17 |
| `Sub` | 19 | 3 |
| `DP-` | 21 | 0 |
| **`Service ...`** | **227** | **0** |
| **`RTP ...`** | **121** | **0** |

**Items to leave out of the order form.**
- All 228 items with Product Type = service have zero order lines and are all outside the live set.
- The 121 `RTP` items also have no orders.

Together with the other never-ordered Active items, that is the 486 above. Those 486 are the first thing to hide.

Live items by CF.BU:

| CF.BU | Live items |
|---|---|
| SHP | 456 |
| PACPRO | 445 |
| MOBA - PAPER CUP | 135 |
| OPD | 73 |
| CUSTOMIZED PACKING UNIT | 69 |
| MOBA PUNCHING | 57 |
| MOBA | 12 |
| FPP | 5 |
| PCU | 5 |

Live items by most common `CF.Manufacturing Division`:

| Manufacturing division | Live items |
|---|---|
| Offset Printing Division (OPD) | 554 |
| Screen Printing Division (SHPS) | 457 |
| Paper Cup Unit (PCU) | 138 |
| Customized Packing Unit (CPU) | 69 |
| MOBA Punching Unit | 34 |
| Food Product Processing (FPP) | 5 |

**Division mapping caveat.** The portal's routing to production managers must map these division names to Mubeena, Ranga and Ishan. The CF.BU values (e.g. MACPRO, PACPRO, PCU) do not line up one-to-one with the manufacturing division. Settle the mapping with the production dashboard `division_pairs`.

## 2. The most important finding: a "customized item" is a customer-specific item

Almost every customized item is one customer's product, and the customer is named in brackets at the end of the item name. Examples:
- `SP-Burger Pouch (Street Burger)`
- `CP-16Oz Plastic Cup (475ml) (Island Tea Company)`
- `PRINTSERV-8oz D/Wall Kraft Cup With Print (BYD)`

In the live set, 1,186 of 1,257 items (94%) end in such a bracket and only 71 have none.

**Consequence for the order form.** Pick the end customer first, then show that customer's items. A flat list of 1,257 items is not usable.

- The top-3 end customers on each live item include at least one name other than SH on 1,212 of 1,257 items.
- 849 live items have only one end-customer name in their top 3.
- 169 live items have SH itself as their top end customer.
- At least 497 distinct non-SH end customers have a live item. This counts top-3 only, so the true figure is higher.

**Skew of demand.** The catalogue is a long tail. The top 10 items hold 4.7% of the lines, the top 50 hold 15.6%, the top 100 hold 25.2% and the top 200 hold 38.8%. No small "best-seller" list covers the demand.

## 3. Long tail and one-offs
- Items with 1 order line: 684.
- Items with 1 distinct SO: 1,022.
- Items with 10 or more lines: 187.
- Items with 25 or more lines: 19.
- 366 of the live items have only ever been reordered. The share of New Order is greater than 0 on 885 live items, so many live items still saw a first order inside the file.
- A new design needs a "new item / new artwork" path, because it will not be in the catalogue (the same `CF.Job Nature` = New Order, 1,892 of 7,806 lines on Customized items). Whether the portal creates the Zoho item or only sends a request is a spec decision (see 02).

## 4. End customers (`data/end-customers.csv`)
- 640 distinct free-text values in `CF.Order Received from`. It is filled on 10,596 of 10,596 lines (100%).
- **SH itself is the value on 5,075 lines (48%).** Zoho Customer Name is SH on 10,594 of 10,596 lines, as already known. SH as "Order Received from" spans 4,098 SOs and 926 distinct Customized items. For these lines the real end customer is not recorded, or it is a stock order for SH's own account. I could not determine which from the export.
- Excluding SH, the top end customers by lines are:

| End customer | Lines |
|---|---|
| Spar SL (Private) Limited | 138 |
| Street Burger (Private) Limited | 117 |
| TACO BELL | 109 |
| Blends | 103 |
| Kiri Kopi | 101 |
| Keells Super | 86 |
| Malu Poke | 68 |
| GRAND BELL HOTEL | 57 |
| Flamingo | 56 |

- 116 end customers ordered exactly once.
- 166 have 10 or more lines.
- 487 ordered in the last 12 months.
- 14 end customers have no line on a Customized item.

**Name variants (not merged).**
- 8 groups differ only by case, punctuation or a non-breaking space. Examples: `Skinny Tom's Deli` / `SkinnyTom's Deli`, `Solis Hotel` / `Solis<NBSP>Hotel`, `The brownie Station` / `The Brownie Station`, `Centerbury Golf Club` / `Center bury Golf Club`.
- 42 names have a near variant by similarity or prefix. Examples:
  - spelling: `QWICK` / `QWIK`, `Muts` / `Mutts`, `Papa Jeevz` / `Pappa Jeevz`, `Eleven Resturant` / `Eleven Restaurant`, `FUSION CAFE` / `Fushion Cafe`
  - branch or legal suffix: `Marriott` / `MARRIOTT WELIGAMA`, `Rustic Roast` / `Rustic Roast Pvt Ltd`
  - group, hotel and branch hierarchy: `Shangrila`, `Shangrila Colombo`, `Shangrila Hotel Hambantota` and `Shangri-La Investments Lanka (Pvt) Ltd` all appear
- Whether a branch is the same customer is a business call. I left them separate. The portal needs a customer master, not free text. Seeding it from this list needs a person to merge, and the variants are in the CSV columns `same_after_normalising_case_punctuation` and `near_variants_unmerged`.

## 5. Data-quality problems
1. **Customer-specific items mean item count grows with every new customer.** See section 2.
2. **Item master snapshot is older than the orders.** 26 SO lines (25 Customized Order, 1 Internal SH Order, dated 24 Aug to 24 Sep 2026) point to a `Product ID` that is not in Item.xlsx. The master was exported 15 to 16 Sep. These items are missing from the catalogue; the names are in `stats.json` under `lines.not_in_master_names` and are mostly `PRINTSERV-...` and `SP-...`. Why the master lacks items that were ordered back to 24 Aug I could not determine; re-pull the item list before building.
3. **Order Type and item type disagree.** 94 Customized Order lines are on Non Customized items, 5 are on `NA`, and 254 lines for Customized items are tagged Ex Stock. The portal cannot assume that Customized Order and Customized item are the same thing.
4. **Missing fields on catalogue rows (all 2,537):**
   - SKU is blank on 2,417 (95%). On live items it is blank on 1,216 of 1,257, so the item name is the only identifier.
   - Manufacturing division is blank on 486, which are exactly the never-ordered items. All live items have it.
   - Base material is blank on 487 (live: 1).
   - Unit is blank on 12 (live: 5). I fill it from the SO usage unit first, then the master Unit.
   - Item master `Division` is blank on 181 (live: 3).
5. **Division conflicts.** 94 Customized items have more than one `CF.Manufacturing Division` across their SO lines. The catalogue uses the most common one.
6. **Names.**
   - 39 names have a double space.
   - 3 have leading or trailing spaces.
   - 60 are over 90 characters (8 live).
   - Prefixes are inconsistent: `Sub.`, `Sub-`, `SH-`, `DP-`, `Kraft ...` and others, and 74 names fit none of the known prefixes. No duplicate names within the catalogue.
   - Spelling: the dye-cutter option text is `Not Avaialble` in the data, with a typo.
7. **Duplicate and misspelled custom fields.** Artwork, dye cutter and screen/plate exist twice:
   - An older boolean field (`CF.Artwork Availability`, `CF.Dye Cutter Availability`, `CF.Screen / Plate Available`) holds `true` or `false`.
   - A newer text field (`CF.Artwork Availablility`, `CF.Dye Cutter Availablity`, `CF.Screen / Plate Availability`) holds Available / Not Available / Not Applicable.
   - The merge rule is: use the text field; if it is empty and the boolean is `true`, take Available; a `false` boolean is the unfilled default, so treat it as unknown.
   - 256 Customized-item lines hold `true` with an empty text field. Across all 10,596 lines the artwork text field is empty on 475, and every one is dated 2024.
   - The new text fields have been filled on all of 2025 and 2026 Customized lines.
8. **`CF.Job Nature` empty on 258 of 7,806 lines**, all from 2024. 100% filled for 2026.
9. **Cancelled quantity is common.** 1,429 of 7,806 Customized-item lines have `QuantityCancelled` > 0, so quantity ordered is not quantity made. Median and min/max in the catalogue use `QuantityOrdered`.
10. **Price is internal reference only.** `Item Price` is positive on 97.2% of lines. SH is the customer on 10,594 of 10,596 lines, so these are internal transfer prices to SH, not what the end customer pays. The portal should not show them to sales as a selling price unless Sales confirms.
11. **Stock figure is stale.** `stock_on_hand_item_master_16sep` is the Item.xlsx "Stock On Hand" value on 16 Sep and is a single number for the item. Of live items, 364 show more than 0. It cannot drive "in stock, send to Rizwan's team". See 02 for what the check needs (live read, warehouse-aware, never summed with SH). I did not verify which warehouses the figure covers.

## 6. Fields the order form needs, with fill rates from history

Fill rates are for the 7,806 SO lines on Customized items (all order types). The 2026 column is the 2,639 lines dated 2026. Source column is the Zoho export column name.

| Order form field | Zoho source column | Fill, all history | Fill, 2026 | Comment |
|---|---|---|---|---|
| Item (pick from catalogue) | `Product ID` / `Item Name` | 100% | 100% | |
| Quantity | `QuantityOrdered` | 100% | 100% | |
| Unit | `Usage unit` | 99.8% | 99.8% | pcs, box, nos, Pks |
| End customer | `CF.Order Received from` | 100% | 100% | free text; see 4 |
| Order type (customized / stock / internal) | `CF.Order Type` | 100% | 100% | the portal sets this |
| Reorder or new design | `CF.Job Nature` | 96.7% | 100% | Reorder / New Order / Reorder With New Design / Rework |
| Required (expected shipment) date | `Expected Shipment Date` | 65.6% | 99.4% | in 2026 it is almost always filled and differs from the order date |
| Base material | `CF.Base Material to be Used` | 99.8% | 99.9% | default from the last order |
| Other material | `CF.Additional Other Material to be Used (If any)` | 6.2% | 0.2% | optional |
| Artwork status | merged old boolean + text fields | 100% | 100% | Available / Not Available / Not Applicable |
| Dye cutter status | merged old boolean + text fields | 100% | 100% | Available / Not Available |
| Screen / plate status | merged old boolean + text fields | 100% | 100% | Available / Not Available / Not Applicable |
| Customer PO / reference | `PurchaseOrder` | 99.6% | 99.9% | |
| Division (production unit) | `CF.Manufacturing Division` | 100% | 100% | derived from the item |
| SH Sales Order ref | `CF.SH Sales Order Ref` | 100% | 100% | |
| Job number | `CF.Job No` | 99.9% | 100% | opaque, system assigned |
| ClickUp link | `CF.Clickup Link` | 15.2% | 44.8% | system assigned |

**Not worth putting on the form** (fill rates in `stats.json`):
- Notes: 0.0%
- Item description: 0.1%
- Shipping address: 0.0%
- Sales person: 0% in 2026
- Delivery method: 0% in 2026
- Sales channel: always `direct_sales`

**What the form should capture that history cannot show.** The export has no field for:
- who at SH placed the order (the portal login gives this)
- delivery destination (SH or the customer)
- in-stock vs production routing (a decision, not a field)
- artwork file upload

These are listed for the spec as new fields. I did not infer them from any column.

**Defaults the history supports.** Pre-fill base material, unit, manufacturing division and the artwork, dye cutter and screen status from the item's most recent order. Per item, artwork was ever "Not Available" on 144 live items, dye cutter on 348 and screen/plate on 149. The "Not Available" case is where production needs a prepare step before starting, so the form must make those three explicit.

## 7. What I could not determine
- Whether the 5,075 lines with SH as end customer are SH stock builds or orders whose real customer was not typed. Needs Rizwan's team or the sales team.
- Which warehouses the item-master `Stock On Hand` covers, and how current it is. A live stock read is required.
- Why 26 ordered items are missing from the item master snapshot.
- Whether branches of one customer (the Shangrila, Marriott, Sheraton type) should share one customer record.
- Whether the Customized item flag is maintained by hand; 94 + 5 Customized-Order lines sit on non-customized items, so the flag is not a perfect scope boundary.

## Rebuild
```
python3.12 -I scripts/build_catalogue.py /root/exports/zoho/sps/2026-09-27/item1/Sales_Order.xlsx /root/exports/zoho/native/2026-09-16/Item.xlsx data
python3.12 -I scripts/extra_stats.py data
```
Note: another run of the workflow wrote a different `scripts/load.py` into the same folder. `build_catalogue.py` has its own reader and does not use it.
