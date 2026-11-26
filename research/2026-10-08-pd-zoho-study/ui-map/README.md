# SPS Zoho Inventory UI map (8 Oct 2026, read-only, itexe@ browser :9335)

Captured by `map.mjs`. Navigation only, no sign-out. Screenshots: `so-list.png`, `so-detail.png`, `packages.png`, `shipments.png`, `items.png`. Raw data: `landmarks.json`.

- **App:** Ember single-page app at `https://inventory.zoho.com/app/843825512#/...`, org "Smart Packaging". Routes: `#/salesorders`, `#/salesorders/<so_id>` (detail opens beside the list), `#/packages`, `#/shipments`, `#/inventory/items`.
- **No `data-test-id` attributes.** Anchors for injection must be class or structure based, so they are fragile: Zoho shows a "we've fine-tuned Zoho Inventory, refresh" banner, so its UI changes. Use a selector health check, with the side panel as the fallback.
- **The page's own JSON calls** go to the same origin, `/api/v1/...?organization_id=<org>`:
  - `GET /api/v1/salesorders?page=1&usestate=true`, `.../salesorders/<id>?include=html`, `/packages`, `/shipmentorders`, `/items`, `/customviews`, `/customfields`.
  - Whether these session calls count against the org API limit is NOT verified.
- **SO detail layout:** header with JOBORDER-xxxxx, toolbar (Edit, Send Email, PDF/Print, Convert to Invoice, Create, ...), a "What's next" box, tabs (Packages, Picklists, Canceled Items), the backorder banner, then the SO document. Natural places for our strip: below the toolbar or above "What's next". Each list row shows customer, JOBORDER no, date, `cf_job_no` (e.g. OPD6815), amount and status.
