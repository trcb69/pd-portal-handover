# Evidence: missing, unclosed, incomplete or confusing Zoho records (SH + SPS)

Prepared by Abdul Hadhee | IT Exec | Standard-Holdings, 28 Sep 2026. Compiled from prior analyses
only — no new Zoho pull was run for this note. Quantities/counts only; no prices or finance amounts
(overdues, payment status, payables are Finance's, per `feedback-it-scope-no-finance`). Every number
cites the source file, and `file:line` where the source has stable line numbers. Grouped by process
step; each item gives what's missing/incomplete, the number(s) with year where known, who probably
should have caught it (stated plainly as inferred where it is), and the source.

---

## 1. Order entry

- **SH sales orders never progressed past "shipped" status** (customer never marked "delivered" in
  Zoho). **11,556 of 15,900 confirmed SH SOs**, all-time to 19/25 Sep 2026; of the 11,406
  invoiced-and-fully-shipped subset, South Branch carries 5,672 (a location doing only ~19% of SH's
  order volume). A second, independent re-measure on 27 Sep got 11,556 again (South Branch share
  5,708 that time — pull-to-pull noise, not reconciled).
  Likely owner: **sales/logistics staff at the branch who should mark delivery** — the plan explicitly
  flags "who is meant to mark delivery, and why it stopped" as unanswered.
  Source: `/root/Project Management/reports/2026-09-25-sh-inventory-plan/data/facts.txt:56-59,65-68`;
  `/root/Project Management/reports/2026-09-25-sh-inventory-plan/SH-inventory-build-plan.md:42,57-60`;
  `/root/Project Management/reports/2026-09-27-sps-sh-inventory-analysis/work/scout-sh.md:84-88`.

- **133 draft SH sales orders** sitting unconfirmed, 2024–2026 (22 in 2024, 34 in 2025, 77 in 2026
  YTD) — a growing count each year. Likely owner: **sales admin who opened the order and never
  confirmed it**.
  Source: `.../2026-09-25-sh-inventory-plan/data/facts.txt:50`;
  `.../2026-09-27-sps-sh-inventory-analysis/work/scout-sh.md:57-59`.

- **A sales order dated in the year 1831** (`HTXSO24040417`), an impossible date nobody caught.
  Likely owner: **sales admin who entered the order**.
  Source: `.../2026-09-25-sh-inventory-plan/data/facts.txt:69`;
  `.../SH-inventory-build-plan.md:50,83`.

- **No cancellation reason is ever captured on either side.** Of 4,862 open/partial/cancelled
  short-delivery events found across SPS and SH orders (2024–2026), **all 2,213 real
  cancel events (100%) have no usable reason** — Zoho's `reason` field only ever records "cause not
  recorded." 2,149 of those are on the SPS side (SPS cancelling SH's own orders), 64 on SH's
  customer-facing side. Likely owner: **whoever cancels/short-closes the line — SPS staff for the
  2,149, SH order-entry/customer-service for the 64** — since no reason field or process exists to
  make them record why.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/requirements/evidence/01_results.json`
  (`E_cancellations_no_reason`, `total_cancel_events: 2213`, `breakdown_by_org_reason`);
  `.../requirements/SYSTEM-REQUIREMENTS-FROM-DATA.md:111` (F5).

- **Open/short order lines that simply age instead of getting closed or chased**, across the full
  0–365+ day spectrum, with the oldest bands the biggest: SPS 2025 — 644 lines / 1,704,677 units
  aged 366+ days; SPS 2024 — 191 lines / 216,356 units aged 366+ days; SH-customer 2025 — 75 lines /
  60,158 units aged 366+ days. These are **org-wide, not yet cut down to the 11 finished-goods items**
  the phase-1 build actually watches. Likely owner: **whoever owns each open SO line — sales at SH,
  order desk at SPS** — nobody currently chases these.
  Source: `.../requirements/evidence/01_results.json` (`A_ageing_open_lines`);
  `.../requirements/SYSTEM-REQUIREMENTS-FROM-DATA.md:105-107` (F1).

- **Repeat short-deliveries to the same external customer on the same item are common but overstated
  in a first pass.** Corrected count: **183 of 684 (26.8%) SH-external-customer item×customer pairs**
  that were ever short repeat across 2+ separate sales orders (an earlier, uncorrected figure of
  35.8%/1,900 pairs wrongly folded in 1,216 intra-group SPS→SH pairs, which are the same internal
  transfer relationship counted over and over). Likely owner: **SH sales, for not flagging a
  chronic-shortage customer/item before repeating the same shortfall**.
  Source: `.../requirements/SYSTEM-REQUIREMENTS-FROM-DATA.md:108` (F2, "recomputed" citation).

- **SPS-side sales orders closing "short" (never fully delivered, shortfall cancelled rather than
  chased) is rising year over year**: 2024 — 349 of 2,243 closed SOs (15.6%); 2025 — 628 of 2,738
  (22.9%); 2026 YTD — 747 of 1,918 (38.9%). Plus **110 SOs from 2024 still sitting open
  ("partially_invoiced") as of the 16 Sep 2026 pull** — two years stale. Likely owner: **SPS order
  desk / SPS sales**, who close orders short instead of resolving the shortfall.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/work/scout-sps.md:63-83`.

## 2. Job / production

No hard numbers on shop-floor job/production records turned up in the cited analyses — the SPS→SH
work was scoped to sales orders, invoices, transfers and bills (commercial documents), not SPS's
internal production-job tracking, per `requirements/SCOPE-NOTE.md`. The DP Technologies review
(printer repairs) is closer to a "job" record and is covered under Item master/Dispatch below where
it overlaps. This is a genuine gap in the evidence base, not a claim that production records are
clean — flagged rather than asserted either way.

## 3. Stock moves and transfers

- **Transfer orders stuck mid-flight.** All-time SH transfer orders: 4,903 total; **49 stuck
  "in_transit"** (median age 7 days, oldest 60 days — `TOS-260787-GALLE`, opened 21 Jul 2026, still
  moving at the 19 Sep pull) plus **48 pending approval**. A second, later cut (as of 27 Sep) counted
  **142 transfers not yet moved**: 68 pending_approval, 50 in_transit, 24 approved (averaging 34.6
  days old, 3 over 90 days). Likely owner: **the receiving warehouse, which is supposed to confirm
  arrival** and hasn't.
  Source: `.../2026-09-25-sh-inventory-plan/data/facts.txt:42,45`;
  `.../SH-inventory-build-plan.md:46,80`;
  `.../2026-09-25-inventory-decision-system/MEETING-PACK.md:143,209,238`;
  `.../2026-09-27-sps-sh-inventory-analysis/requirements/evidence/02_results.json` (`K_transfer_leadtime_and_pending_ageing`).

- **1,876 "Product Conversion" stock adjustments posted in SH's Zoho, only 1,023 traceable to an
  actual sale/SO** (831 cite an invoice, 192 a sales order; the other 808+45 cite "other," "no
  description" or a stock loan) — i.e. over half have no clear reason on file. Plus **312 rejected and
  15 draft adjustments** sitting unresolved (of 3,911 total, Apr 2024–Sep 2026). Likely owner: **stores
  staff who post the adjustment** without filling in why.
  Source: `.../2026-09-25-sh-inventory-plan/data/facts.txt:34-40,70-71`;
  `.../SH-inventory-build-plan.md:43-44,61-63,79`.

- **Stock-take corrections are routine at every SH warehouse** — 1,500 posted (of the 3,573 posted
  adjustments), with no measure of stock accuracy attached to any of them. Likely owner: **each
  warehouse's storekeeper**, since nobody currently scores count accuracy.
  Source: `.../2026-09-25-sh-inventory-plan/data/facts.txt:70,74`; `.../SH-inventory-build-plan.md:45,66`.

- **SPS raw-material items sitting in the wrong warehouse: 266 of 423 (62.9%)** are recorded only in
  the Work-in-Progress warehouse, not Raw Material, where they should be. Likely owner: **SPS
  storekeeper/production**, who moves material without updating its Zoho warehouse location.
  Source: `.../2026-09-25-inventory-decision-system/MEETING-PACK.md:352`;
  `.../2026-09-25-inventory-decision-system/research/01-internal-digest.md:234,462`.

- **SH's own internal transfer records account for far less volume than SH's bill-line receipts from
  SPS over the same period**: transfers record only 11.7% (2024), 12.7% (2025), 13.9% (2026 YTD) of
  the units SH's bills say arrived, plus 87,442 units "not yet moved." (Flagged by the analysis's own
  review as comparing two different kinds of record — a stock move vs. a purchase document — so it
  reads as an SH-side data-completeness gap rather than proof of lost stock, but it means SH's
  Transfer Orders alone cannot be trusted as a complete "goods arrived" signal.) Likely owner: **SH
  warehouse staff, who don't log every incoming lot as a formal transfer**.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/requirements/evidence/01_results.json`
  (`F_transfers_vs_bill_inflow`); `.../requirements/SYSTEM-REQUIREMENTS-FROM-DATA.md:112` (F6).

## 4. Dispatch / shipment / delivery

- **11,556 SH sales orders never marked "delivered"** — see §1 (same fact, the dispatch/delivery side
  of the same broken step).

- **A third of SPS sales orders carry no shipment date at all** in a given year, i.e. Zoho shows no
  record of when they actually shipped: 35.0% (2024, 48 of 137 orders with dated records), 20.9%
  (2025, 192 of 918), 32.0% (2026 YTD, 1,101 of 3,436). (The analysis's own read: this looks like
  "not yet shipped" rather than a worsening hygiene trend, but it still means a third of SPS's own
  order book can't answer "did this ship" from the shipment-date field.) Likely owner: **SPS
  dispatch/logistics**, who should set the field when goods leave.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/requirements/evidence/02_results.json`
  (`J_sps_so_order_to_shipment_leadtime`); `.../requirements/SYSTEM-REQUIREMENTS-FROM-DATA.md:115` (F9).

- **SH's `delivery_date` field cannot be trusted as a delivery-promise date at all** — checked against
  24,143 SH sales orders with both a `delivery_date` and a matched package record, the package date
  is never after `delivery_date` (0 of 24,143), which only makes sense if the field is being written
  *after* the order ships rather than set as a commitment when the order is placed. Likely owner:
  **whoever fills `delivery_date` in Zoho** — currently nobody uses it as intended.
  Source: `.../2026-09-25-inventory-decision-system/research/02-data-evidence.md:202-218`.

- **8.9% of SH sales orders (2,874 of 32,335) shipped partial at least once** in the last 12 months
  measured (window ending 19 Sep 2026), with Head Office's partial-shipment rate (10.5%) roughly 3×
  Central Branch's (1.5%) and 4.5% of Head Office orders **never packaged at all** as of the pull.
  Likely owner: **branch dispatch/logistics**.
  Source: `.../2026-09-25-inventory-decision-system/research/02-data-evidence.md:194-224`.

## 5. Invoice / bill linkage

- **SPS→SH bill records carry no usable document reference at all** — `reference_number` on SH's
  SPS-internal bills was confirmed empty on every sampled row, so bills can only be matched to
  invoices by parsing job codes out of the bill number, not by a direct id. Likely owner: **whoever
  raises the bill in Zoho** (accounts) — the field exists but isn't filled in.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/requirements/evidence/02_results.json`
  (`_chain_caveat`).

- **Before a 28 Sep fix, only about half of qualifying SPS-to-SH bills could be matched to a specific
  invoice**: 6,486 of 12,260 qualifying bills (52.9%). A same-day fix (job-code matching) raised this
  to **89.5% (119 bills still unmatched)** — evidence that the gap was a Zoho/process naming problem,
  not unfixable, but it sat unresolved in the live data until this analysis built a workaround.
  Likely owner: **accounts staff who name/reference the bill** in a way that doesn't map cleanly to
  the invoice it pays.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/work/analysis/RUN-OFFICIAL.md:82-100` (table 3).

- **A third to half of item-year cells can't be reconciled between what SPS invoiced and what SH's
  bills recorded**, pre-fix: 919 of 1,910 (48.1%, 2024), 601 of 1,910 (31.5%, 2025), 657 of 1,910
  (34.4%, 2026 YTD). This is flagged in the source analysis as Finance's reconciliation job, not an
  inventory-system concern, but it is still a Zoho record-linkage gap. Likely owner: **accounts /
  Finance**, per the analysis's own routing.
  Source: `.../requirements/evidence/01_results.json` (`I_bill_invoice_matching_gaps`);
  `.../requirements/SYSTEM-REQUIREMENTS-FROM-DATA.md:114` (F8).

## 6. Item master

- **156 distinct SPS items, 5,900,051 units invoiced 2024–2026, have never been matched ("bridged")
  to any SH item** — Zoho has no shared item identity across the two orgs for these, so their flow into
  SH's stock can't be tracked at all today. Likely owner: **whoever creates new items in either
  org**, since no shared naming/SKU convention exists to stop the list growing.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/requirements/evidence/01_results.json`
  (`G_item_master_gaps.G1_unbridged_sps_items`); `.../requirements/SYSTEM-REQUIREMENTS-FROM-DATA.md:113` (F7).

- **370 distinct SH items (1,110 of 5,730 item-year rows) have a genuine unit mismatch** between how
  SH and SPS record the same item's unit (e.g. SH tracks "Pizza Box…" in `nos`, SPS in `box`) — not a
  synonym, a real conflict that breaks any quantity comparison across the two orgs. Likely owner:
  **item-master admin in each org**, who set up the unit independently.
  Source: `.../requirements/evidence/01_results.json` (`G_item_master_gaps.G2_unit_mismatch_after_synonym_fold`).

- **Only 116 of 11,297 inventory-tracked SH items have a reorder level set** — Zoho's own low-stock
  alert effectively never fires because almost nothing has a trigger value. Likely owner:
  **purchasing (Rizwan's team)**, who never populated the field.
  Source: `.../2026-09-25-sh-inventory-plan/data/facts.txt:47`; `.../SH-inventory-build-plan.md:48,67`.

- **1,879 of 5,486 SH "Operations–Packaging" items (34%) have no purchase evidence anywhere in the
  exports on disk** — never appear on a PO line or an SPS-internal bill, so where they were bought
  from can't be traced at all in Zoho's own records. A further **808 items are flagged "Review"**
  because their division tag conflicts with the evidence (name/vendor history disagrees with the
  tag), and **48 items have no division tag at all** (`cf_division` blank). Likely owner: **whoever
  tags/creates the item** (purchasing/stores admin) — tags were set once and never checked against
  actual purchase history.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/item-classification/NOTES.md:1-56,122-125`.

- **92.5% of SH's 12,006 items (11,107) have a blank `vendor_name` field** on the item master, and
  only 258 are explicitly tagged as sourced from SPS — a large undercount against the roughly 1,900+
  items actually known to come from SPS, so the field can't be used on its own to say who supplies an
  item. Likely owner: **item-master admin**, who leaves the field blank at item creation.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/work/scout-sh.md:156-169`.

- **333 of 3,331 SPS Raw Material Warehouse items (10%) can't be matched to any SH item** by SKU,
  name or fuzzy match at all, even after multiple matching passes. Likely owner: **SPS storekeeper /
  item-master admin**, naming inconsistently across the two catalogues.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/item-classification/NOTES.md:158-163`.

- **1,962 SH items carry stock on hand with zero lifetime recorded sale** — either genuine dead stock
  or (more likely for the largest ones) a data-linkage gap between how the item is bought vs. sold in
  Zoho. Likely owner: **stores/purchasing**, for items bought under one code and sold under another
  without being linked.
  Source: `.../2026-09-25-inventory-decision-system/research/02-data-evidence.md:391-401`.

- **The old toner-issue log recorded 44 cartridges issued (7 Apr–25 Aug 2026) while DP Technologies'
  Zoho purchase orders show 129 delivered in the shorter Apr–Jul 2026 window** (the tracker-build
  script's own note gives a close but not identical figure — "Zoho shows 119 cartridges from DP in
  Apr–Jul 2026 alone" — both readings agree the log undercounts by roughly 3×). The log also has no
  printer/asset link, broken sequential IDs, and one person's name spelled four different ways.
  Likely owner: **whoever hands out toner day to day** (facilities/admin staff), who logged issues
  inconsistently or not at all.
  Source: `/root/.claude/projects/-root/memory/toner-tracking.md`;
  `/root/Project Management/reports/2026-09-25-dp-technologies/data/build_tracker.py:391,394`;
  `/root/Project Management/reports/2026-09-25-dp-technologies/data/toner_log_parsed.json` (42 rows,
  sum qty 44).

- **12 of DP Technologies' 26 printer-repair POs name only the spare part, not the printer, and
  several repaired printers (a Canon MF241d, Canon LBP6030, Epson L6190, two HP 1102/1008w units) are
  not in the IT asset register at all**, so repeat faults on the same machine can't be traced.
  Likely owner: **whoever raises the repair PO** (IT), for not recording the asset.
  Source: `/root/Project Management/reports/2026-09-25-dp-technologies/data/gaps.json`.

## 7. Other (cross-cutting / structural gaps)

- **No Zoho export on either side links a customer to an item at line level.** Every SH document
  export checked (`salesorders.json`, `packages.json`, `picklists.json`, `salesreturns.json`,
  `creditnotes.json`) is header/document-level only, with no `item_id` field — so "which customer
  bought which item" cannot be answered from Zoho's own exports finer than a month-level aggregate,
  which itself keeps customer and item in two separate files that don't share a document key. Likely
  owner: **nobody's fault at the record level — this is how Zoho's standard reports are shaped**;
  fixing it needs a different export/pull, not a data-entry fix.
  Source: `.../2026-09-25-inventory-decision-system/research/02-data-evidence.md:133-167`.

- **SH sales orders have no line-item export at all on disk** — every field is an order total
  (`quantity`, `quantity_shipped`, etc.), so a single multi-item order can look "fully shipped" while
  hiding a short SPS item inside it, or vice versa. Confirmed by reading a full sample record: 25
  header fields, no `item_id`.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/work/scout-sh.md:22-24,104-131,136-153`.

- **SPS's own sales-order status field is too coarse to show real order-entry states** — only three
  values ever appear in the export (`invoiced`, `confirmed`, `partially_invoiced`); no
  `draft`/`void`/`cancelled` status string exists anywhere in 10,442 lines checked, even though
  cancellations clearly happen (tracked instead via a separate `QuantityCancelled` field). Likely
  owner: **n/a — a Zoho configuration/report-scope limitation**, not a data-entry error.
  Source: `.../2026-09-27-sps-sh-inventory-analysis/work/scout-sps.md:28-32`.

---

## Notes on evidence quality

- Two SH sales-order counts for "stuck at shipped" (11,556 both times, but South Branch's share
  differs 5,672 vs 5,708 between the 25 Sep and 27 Sep pulls) were not reconciled against each other —
  flagged, not resolved, in the source documents themselves.
- The 129-vs-119 DP-toner-purchases figure has the same kind of small internal inconsistency (two
  different window cuts in the same file set); both numbers still support the same ~3x undercount
  finding.
- Several numbers above (F1 org-wide ageing, F2 repeat shortfalls) are explicitly flagged by their own
  source as not yet cut down to the 11-item phase-1 scope — they describe the *whole* SPS/SH item
  universe, not just what any planned build will initially watch.
