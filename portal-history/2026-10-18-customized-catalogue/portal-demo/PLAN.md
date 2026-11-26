# Customized order portal, v1.0 beta plan (18 Oct 2026)

Demo: `Customized-Order-Portal-Demo.html` (open in a browser; local data, nothing sent to Zoho).

## Your flow, as built in the demo
1. Sales person opens the link and signs in. The item box is empty and nothing else shows.
2. They type part of an item name (size, brand tag, product). A dropdown suggests items (their own mapped items first; untick to search all).
3. After the item, the customer box suggests customers who ordered it. Choosing one fills quantity, unit price, job nature, artwork / dye cutter / screen state from the last order (marked "pre-filled").
4. Variants: Zoho item variants are not used (0 of 2,708 items). Each size or colour is its own item. The portal groups items by product name and brand tag and shows the other sizes / colours as cards; one click switches and loads that item's own history. Size, colour, wall, material and features are read from the item name.
5. "Add line", then "Send to production". The order appears at once on the production manager screen.
6. Manager checks the pre-filled division, base material, additional material and order type, then clicks "Create SO in Zoho". That is the only Zoho write: one SPS sales order (customer Standard Holdings, end customer in "Order Received from").

## What the data says (7,715 lines on customized items, 16 Sep export)
Fields always filled: item, quantity, unit, price, end customer, base material, job no, order type, manufacturing division, artwork / dye / screen state. Job nature 97%. Required-by date 65%. Additional material 6%. ClickUp link 14% (dropped).
Base material has 353 different values: it is the real "paper variant" (gsm, PE coating, board), so it is a production dropdown filled from the item's last order, not something the sales person types.
Glossy / matt finish is almost never in an item name (14 of 1,276 items); finish is not a field in Zoho today.

## Fields shown by division (rule to confirm with the production managers)
Artwork: always. Dye cutter: OPD, PCU, MOBA, CPU, FPP. Screen / plate: OPD, SHPS. Material, division, job no: production only.

## Open points
- New customers and new items: free-text customer is allowed; a new item needs a different path (not built).
- Finish (glossy / matt) and size should become real item attributes or a notes field; today they are only in the name.
- Price: confirm sales people may edit the pre-filled price.
- SH read access for the real customer list and the sales person per customer is still the CEO's decision; the demo uses the catalogue mapping (about 60% of items have a sales person).
- Zoho write: needs an SPS API write scope; the demo shows the exact payload in the manager screen.

## Data architecture (user decision, 18 Oct): write by API, read by scheduled browser pull
- Write: the portal creates the SPS sales order through the Zoho API (one call per order, so the 7,500 calls/day SPS limit is not a concern).
- Read: a script drives the already signed-in browser (raw CDP, as in `scripts/cdpget.mjs`) and pulls item, customer and recent-order data every 5 minutes by cron into the portal's own database. Browser pulls do not use the API quota.
- Things to design before building:
  - Pull incrementally (items and sales orders changed since the last run, sorted by last-modified), not the full lists. In this session one 200-row list page took 30 to 90 seconds and a full SO detail about 4 seconds, so a full refresh does not fit in 5 minutes.
  - The pull depends on a signed-in session. It dies on a sign-out or OTP, so the script must detect a login page, stop, and show "data is stale since HH:MM" in the portal (the demo has the badge).
  - One pull at a time (a lock), about 1 request per 1.2 s, GET only, as today. Playwright connectOverCDP hangs on these browsers, so use raw CDP.
  - Use the web app's own endpoints with the session cookie (not an official API). It works today but is not a supported contract and could change, and its terms of use should be checked. Keep the official API read as the fallback if a Self Client is created.
  - The portal's price and quantity suggestions are only as fresh as the last pull (up to 5 minutes old); writes should re-check the item is still active.

## New customer and new item (research 18 Oct, built in the demo)
Evidence (local exports only):
- SH customer master (2,698 active customers): about 70 new customers a month (57 to 109 since Mar 2026). Naming: 397 are "Cash - Name", 73 end in "- TC", 1,314 have Pvt/Ltd/Limited. Fields filled on 99.8% of customers: company name, VAT status, VAT and SVAT number (mostly "NA"), Salesperson, BU (FD / SD / GD). Payment terms set on all; credit limit on 67%; email 32%, phone 14%. About 12 normalised duplicate names exist.
- The SPS order does not use an SH customer: the SPS customer is always Standard Holdings; the real customer is the free-text field "Order Received from" (626 spellings, including near-duplicates such as "Kiri kopi With Boy"). So a new customer does not block creating the SPS sales order.
- New items: about 85 customized items created a month. Of 192 new SP-/CP- items since April, 190 carry a (customer) tag, 120 (62%) copy a product that already existed, and all 192 have a recipe (BOM) of 5 to 19 lines (material, ink, adhesive, labour, electricity, impressions, packing). Fields set on creation: BU, Finished Good Type = Customized, nature, sub-category (follows the BU 1:1), unit; SKU 5%, description, brand, vendor 0%.
Design:
- New customer: type-ahead with duplicate check (blocks save until the user picks the existing one or confirms "different customer"). Saves the end customer into the portal list at once. If the billing customer is not in SH Zoho, it raises a request with the Zoho fields (type, BU, salesperson pre-filled, payment type, VAT status and number, address, phone, email); credit and terms stay with finance. The customer-master team creates it in SH Zoho (no SH API write); the 5-minute pull picks it up.
- New item: two paths. Copy an existing product (pick the product, new brand tag, optional new size; name and recipe are generated and the duplicate check runs) or brand-new product (type, size, material, colours, artwork file, sample). Production reviews and creates the composite item with its recipe through the SPS API. The sales person can add the item to the order straight away; the order shows "Waiting for item" and Create SO stays disabled until production creates it. Price comes from costing, not sales.
Open: who is the customer-master team; confirm the naming prefixes (SP / CP / ...); how a recipe for a brand-new product is costed; whether artwork files are stored in the portal.
