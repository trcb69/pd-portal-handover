# R1. Zoho Inventory API v1 for the custom-order portal

Prepared 17 Oct 2026. Research only: no live Zoho call, no credentials. SH and SPS figures are never summed.
Method: Zoho docs pages read through a page-summariser (WebFetch), plus web search. Several doc pages are 100k+ characters and only the first 100k were read, so "not stated" below means "not in what I read", not "does not exist". Anything marked UNVERIFIED must be checked against the docs or a sandbox before it is built on.

## 1. Answer first

1. Yes, the portal can talk to Zoho directly by API, read and write, with a normal server-side Node service (Express + SQLite house style). Read = items, contacts, sales orders, locations, per-location stock, transfer orders, packages, picklists, shipments all exist as endpoints.
2. Recommended OAuth shape: **one Self Client per Zoho org** (SPS now, SH later), refresh token stored server-side, `organization_id` fixed in config per org. Not one multi-org client: the SH and SPS orgs have different admins, so each admin authorises their own.
3. Recommended write policy: **read everywhere from day 1; write only drafts, behind a feature flag per org, and only after the SH admin consents.** SPS SO draft creation is the first write to turn on (the user is the SPS admin). SH SO creation waits for SH access.
4. Budget: Zoho's documented limit is 100 requests/minute per org and a daily cap by plan (1,000 to 10,000). The 7,500/day figure checked for SPS on 7 Oct is **not one of the documented plan tiers** (see section 5): treat the 7 Oct reading as the truth for SPS and re-check it, do not assume it for SH.
5. Push: Zoho Inventory has workflow rules with webhooks (outgoing) but only on "selective pricing plans" which Zoho does not name. Plan on **polling with `last_modified_time`** and treat webhooks as an optional later speed-up.

## 2. Earlier decisions this overrides (stated explicitly)

| Earlier decision | Source | Status under this design |
|---|---|---|
| Zoho is read-only everywhere | /root/CLAUDE.md section 1 (8 Oct: "Zoho stays read-only") and old plan | **Overridden for the portal** if the user accepts section 7: scoped writes of drafts. Production Dashboard stays read-only unless the user says otherwise. |
| SH data read through the signed-in browser session (Playwright/CDP) for now; SH API only later | /root/CLAUDE.md section 1 (7 Oct) | **Overridden in direction**: the user now wants API. The 7 Oct condition still holds in practice: SH API needs the SH admin (CEO) to create the client. Until then the SH side is a snapshot/browser read behind the same reader interface. |
| No scripts/extensions | user, 17 Oct | Honoured: only API + server. |

## 3. OAuth options

Facts (all from Zoho docs):
- Inventory API base URL, US DC: `https://www.zohoapis.com/inventory/v1`; the data centre must match the org (both SH and SPS are US DC). Source: https://www.zoho.com/inventory/api/v1/introduction/
- `organization_id` "should be sent in with every API request" (query parameter). It comes from `GET /organizations` (scope `ZohoInventory.settings.READ`) or the admin console. Source: same page.
- Token header is `Authorization: Zoho-oauthtoken {access_token}`; scopes look like `ZohoInventory.<resource>.<CREATE|READ|UPDATE|DELETE>`, comma separated with no spaces. Resource groups listed: contacts, items, compositeitems, inventoryadjustments, transferorders, settings, salesorders, packages, shipmentorders, invoices, customerpayments, salesreturns, creditnotes, purchaseorders, purchasereceives, bills. Source: https://www.zoho.com/inventory/api/v1/oauth/
- Access token life: about 1 hour ("In most general cases"). Refresh token is permanent; **max 20 refresh tokens per user, and the oldest is silently deleted past that** (so do not generate a fresh one on every deploy). Grant code valid 60 seconds on that page. `access_type=offline` is needed to receive a refresh token. Source: https://www.zoho.com/inventory/api/v1/oauth/
- Zoho lists five client types: server-based, client-based, mobile/desktop, non-browser, self client. Source: https://www.zoho.com/accounts/protocol/oauth.html
- Self Client: created in the Zoho API console; "you will be the resource owner and there will be no end-user authorization required". Two flows: authorization-code (gives access + refresh token) and client-credentials (**no refresh token**; request a new access token whenever needed). Source: https://www.zoho.com/accounts/protocol/oauth/self-client/overview.html
- Not stated in anything I read: tokens-per-minute limit on the token endpoint, access tokens per refresh token limit, whether one Self Client may span two orgs. A third-party guide says a Self Client works for one owner with several orgs since `organization_id` is passed per call, but flags it as unconfirmed (https://www.apideck.com/blog/how-to-get-your-zoho-books-api-key). UNVERIFIED.

| Option | Fit here | Verdict |
|---|---|---|
| Self Client, one per org | Backend-to-backend, no end-user consent screen, one admin authorises once. Portal users never touch Zoho login. | **Recommended.** SPS: the user creates it. SH: the SH admin creates it (or authorises a client). |
| Server-based client (auth-code redirect) | Needs a redirect URL and a consent step by a real Zoho user; designed for apps acting for many users/orgs. Zoho CRM SDK docs say server-based is for multi-org apps (CRM docs, UNVERIFIED for Inventory). | Over-built for an internal portal. |
| One client, two orgs | Would need the same Zoho user to be a member of both orgs. The user is admin of SPS only. | Not possible today. |
| Client-credentials Self Client | No refresh token to protect, simpler secret handling. | Worth testing: fewer long-lived secrets. Check it works with Inventory scopes; UNVERIFIED. |

Which Zoho user owns the token matters: API calls act with that user's role. Use a **dedicated integration user** (e.g. a "portal-svc" user) rather than a person's account, so that a staff change (note the 14 Oct IT manager dismissal) does not kill the integration, and Zoho's audit trail shows "portal" as the actor.

### Scopes (minimum sets)

Read-only set (build first): `ZohoInventory.items.READ, ZohoInventory.contacts.READ, ZohoInventory.salesorders.READ, ZohoInventory.settings.READ` (locations and organizations), `ZohoInventory.transferorders.READ, ZohoInventory.packages.READ, ZohoInventory.picklists.READ`, and `ZohoInventory.shipmentorders.READ`. Each of those scope names appears on the endpoint pages (links in section 4); `ZohoInventory.picklists.READ` and `ZohoInventory.shipmentorders.READ` confirmed on their list/retrieve rows.

Write set (add only when section 7 is approved): `ZohoInventory.salesorders.CREATE` (confirmed on create), `ZohoInventory.contacts.CREATE` (only if the portal may add a customer; probably not). Update scopes (`salesorders.UPDATE`, `transferorders.CREATE/UPDATE`) are not needed for the minimal flow. Do not request `ZohoInventory.FullAccess.all`: it appears in Zoho's own example but breaks least-privilege.

UNVERIFIED: whether the status and approval endpoints (`/salesorders/{id}/status/confirmed`, `/submit`, `/approve`) need `salesorders.CREATE` or `UPDATE`. The page excerpt did not state it. The portal should not call them in v1 anyway.

## 4. Endpoints needed

All paths are relative to `/inventory/v1` and take `organization_id`. Pagination on every list I read: `page` (default 1), `per_page` (default **200**). The response-side "more pages" flag was **not shown** in what I read (UNVERIFIED; I recall `page_context.has_more_page` but have not confirmed it here, so confirm it in a sandbox before relying on it).

| Need | Method + path | Scope | Source |
|---|---|---|---|
| Items list | `GET /items` (filters: `search_text`, `filter_by` e.g. `Status.Active`, `status`, `sku*`, `name*`, `last_modified_time`, `warehouse_id`, `location_id`, `sort_column`, `sort_order`) | `items.READ` | https://www.zoho.com/inventory/api/v1/items/ |
| Item detail | `GET /items/{item_id}` | not stated | same |
| Item custom field update | `PUT /item/{item_id}/customfields` (path is singular `/item/`) | not stated | same |
| Item create/update | `POST /items`, `PUT /items/{item_id}` | `items.CREATE`; update not stated | same |
| Per-location stock | `locations` array on items: `location_stock_on_hand`, `location_available_stock`, `location_actual_available_stock`. No `warehouse_available_stock` field on that page. | `items.READ` | same |
| Contacts | `GET /contacts` (`search_text` max 100 chars, `contact_name_contains`, `email_contains`, `company_name`, `phone`...), `GET /contacts/{id}`, `POST /contacts` | `contacts.READ`, `.CREATE` | https://www.zoho.com/inventory/api/v1/contacts/ |
| Sales orders | `POST /salesorders`, `GET /salesorders`, `GET /salesorders/{id}`, `PUT /salesorders/{id}`, `POST /salesorders/{id}/status/confirmed`, `/submit`, `/approve`, `/approve/final`, `/reject`, `/status/void` | create `salesorders.CREATE`; list `salesorders.READ`; others not stated | https://www.zoho.com/inventory/api/v1/salesorders/ |
| Locations (= warehouses) | `GET /locations`, `GET /locations/{id}`; `POST /locations` and `POST /settings/locations/enable` exist but must not be used | `settings.READ` | https://www.zoho.com/inventory/api/v1/locations/ |
| Transfer orders | `POST /transferorders`, `GET /transferorders`, `GET /transferorders/{id}`, `PUT`, `POST /transferorders/{id}/markastransferred` ("Mark as Received"), `POST /transferorders/{id}/intransit`; body `from_warehouse_id`, `to_warehouse_id`, `line_items` | `transferorders.CREATE/READ/UPDATE/DELETE` | https://www.zoho.com/inventory/api/v1/transferorders/ |
| Picklists | `GET /picklists`, `GET /picklists/{id}`, `POST /picklists`, `POST /picklists/{id}/setstatus`, `GET /picklists/searchso` | `picklists.READ/CREATE/UPDATE/DELETE` | https://www.zoho.com/inventory/api/v1/picklists/ |
| Packages | `GET/POST /packages`, `GET/PUT /packages/{id}`; can be created from a picklist | `packages.READ/CREATE/UPDATE` | https://www.zoho.com/inventory/api/v1/packages/ |
| Shipments | `POST /shipmentorders`, `GET/PUT/DELETE /shipmentorders/{id}`, `POST /shipmentorders/{id}/status/delivered`. **No list-many endpoint on that page**: shipments are found via the sales order or package. | `shipmentorders.CREATE/READ/UPDATE/DELETE` (Mark as Delivered uses CREATE) | https://www.zoho.com/inventory/api/v1/shipmentorders/ |

Caveats found while reading:
- **Sales order list filters.** The excerpt I read showed only `organization_id`, and `salesorder_ids` (max 200) as parameters, plus `page`/`per_page`. It did not show status, date or customer filters. The page was 163k characters and I read ~100k, so filters may exist further down. UNVERIFIED: if there are none, "poll for changed SOs" cannot be done by `last_modified_time` on this endpoint and the portal must track its own SO ids and fetch them by `salesorder_ids` (200 per call, which is cheap).
- **SO line location.** In SO line items the warehouse concept appears as `location_id` (top-level) and `mapped_items[].warehouse_id` (kit components only). So for a multi-location org, the line's `location_id` is what to send. UNVERIFIED which of `location_id` / `warehouse_id` the SH org (which uses multi-warehouse, per the exports) needs; test in a sandbox. The transfer order page still says `from_warehouse_id` / `to_warehouse_id` "when multi-warehouse is enabled".
- **Custom fields (CF.*).** On create/update, `custom_fields` is an array of `{customfield_id, label, value}` (salesorders page). The export column `CF.Order Received from` is the label; the API needs the `customfield_id` (a numeric id) which comes from an existing SO read or the field settings. I did not find a dedicated custom-field-definitions endpoint in the pages read. UNVERIFIED how `cf_*` keys appear on reads (the 19 Sep item export from SPS has `cf_fg_type`, which suggests `cf_<api_name>` keys on item objects; see /root/exports/zoho/native/2026-09-19/sps/items.json).
- **Customized-item flag.** SPS items carry `cf_fg_type = Customized` (02-stock-and-routing.md). The `GET /items` filters I read do not include custom-field filters, so the portal should cache the item catalogue locally (862 customized items per 01-catalogue.md) and refresh it by `last_modified_time` rather than query by custom field.
- Picklists and shipments are only needed if the portal must show fulfilment progress. They are read-only candidates.
- Zoho Books API (separate product, `books/api/v3` or `v4`): I did not read it. SH does hold a Zoho Books login in the exports notes, but the portal flow (SO, stock, transfer order, picklist, package) is Inventory territory. Do not use Books unless a gap appears. UNVERIFIED which Zoho app SH finance uses for bills.

## 5. Rate limits

From https://www.zoho.com/inventory/api/v1/introduction/ (as summarised; confirmed by a second search summary):

| Limit | Value | Error |
|---|---|---|
| Per minute | 100 requests per organization | HTTP 429, code 44 |
| Per day, Free / Standard / Professional / Premium / Enterprise | 1,000 / 2,000 / 5,000 / 10,000 / 10,000 | HTTP 429, code 45 |
| Concurrent | Free 5; paid 10 (soft limit) | HTTP 429, code 1070 |

Conflicts and gaps:
- **SPS 7,500/day (checked 7 Oct, `reports/2026-10-07-zoho-api-limit/`) is not in the table above.** Possible reasons: the Zoho org has an add-on/user-count-based allowance, an older plan, or the page differs from the admin console. I cannot resolve this from docs. Use the admin console figure for SPS and ask the SH admin for the SH figure; budget SH at the **1,000/day floor** until known.
- The doc per-minute limit is per org, so SPS and SH budgets are independent; they are not added.
- Every portal write (SO create) plus its read-back costs 2+ calls. Rough SPS arithmetic is small: the order volume is hundreds of SOs a month (see 03-patterns-and-lead-times.md for real counts), so the daily budget goes on polling, not on orders. Design: item catalogue sync hourly-by-modified-time, stock on demand with a 5 minute cache, cap the portal at a share of the daily allowance and stop (not retry) on code 45. The existing inventory design already caps each service at 500/day; keep that principle.
- Back off with jitter on 429 and distinguish the three codes.

## 6. Pushing changes out of Zoho

- Workflow rules in Inventory have event triggers (module created, edited, created or edited, deleted; edit triggers on chosen fields) and date triggers. Actions include email alerts, field updates, webhooks and custom functions (Deluge). Source: https://www.zoho.com/us/inventory/help/settings/automation.html
- Outgoing **webhooks**: path Settings > Organization Settings > Automation > Workflow Actions > Webhooks; methods POST/PUT/DELETE; default JSON payload or chosen entity parameters (max 10); custom headers/params for a token; **"available only for selective pricing plans"**, which plans are not named. Sources: https://www.zoho.com/us/inventory/help/settings/automation.html and https://www.zoho.com/us/inventory/kb/automation/create-webhook.html
- The help page warns contact details are sent to the webhook URL, so the receiving URL must be HTTPS and authenticated.
- Custom functions: "support Invoices, Sales Orders, Purchase Orders and Bills" (same automation page). Workflow alerts are capped at 500 per day (same page; the webhook share of that cap is not stated).
- Incoming webhooks bring data into Zoho; not a push out. Source: https://www.zoho.com/us/inventory/help/settings/incoming-webhooks.html
- Not stated: webhook signing/HMAC, retry behaviour, delivery guarantees. So treat a webhook as a **nudge to re-read**, never as the record.
- Webhooks need a workflow rule created by the org admin in the Zoho UI, i.e. the user for SPS and the CEO's team for SH. Their workflow rules are configuration inside Zoho, not code in our repo. Also needs the portal's public HTTPS URL: Traefik/EasyPanel owns 80/443; an extra route is an EasyPanel change.
- Recommendation: poll first; add one SO-modified webhook per org later if latency matters.

## 7. Should the portal WRITE?

What a write would be, mapped to the flow:

| Step | Write | Who needs to consent |
|---|---|---|
| Rizwan's team accepts an in-stock order | `POST /salesorders` in the SH org (draft). Possibly then transfer order for Galle/HO (`POST /transferorders`). | SH admin (CEO); not available until SH API access exists |
| Production coordinator accepts | `POST /salesorders` in the SPS org (draft, customer = SH contact, `CF.Order Received from` = end customer) | The user (SPS admin) |

Pros of writing drafts:
- Kills the double entry that is today's WhatsApp-then-retype; the end customer free-text (640 spellings today) can be picked from a controlled list and written once into the CF field.
- Customer, item, rate, location are chosen from live Zoho data, so SOs cannot reference a non-existent item.
- The Zoho SO number comes back and links portal order to SO (today's join is a ClickUp link custom field, per the 2 Oct dispatch discovery).
- Enables correct status without a human retyping.

Cons / risks:
- Reverses the standing "Zoho read-only" rule; one bug creates duplicate or wrong SOs in the books of record. Mitigation: portal-generated idempotency key stored in the SO `reference_number` (UNVERIFIED that the field is searchable via list filters), create as draft only, never call confirm/approve, a daily reconciliation read, and a kill-switch flag.
- Stock reservation side-effects: a confirmed SO commits stock; a draft should not (UNVERIFIED for this org's settings; test in a sandbox).
- Auto-number series (`ignore_auto_number_generation` exists; leave default so numbering stays Zoho's).
- Approval workflows in the org (the SO has submit/approve endpoints) may already require sign-off; the portal must respect, not bypass, them. The role of the API user decides what it can do.
- API-created records are attributed to the integration user, which is good for audit but means the CEO must consent to a new actor in SH books.
- Extra budget: about 2 calls per order, trivial against the daily allowance.
- Support load: partial failure handling (portal saved, Zoho failed) needs a retry queue and a visible "not in Zoho yet" state.

Read-only alternative: portal holds the order, staff create the SO in Zoho by hand and paste the SO number back (or the portal finds it by reference). Safe and consistent with earlier decisions, but keeps the retype, which is the user's main pain.

Recommendation (a proposal for the user to decide, not a decision):
1. Phase 1: read-only against SPS via API (user holds the keys), SH via a swappable snapshot reader. Ship the queue and acceptance without Zoho writes.
2. Phase 2: enable SPS SO draft creation (user is admin, can test in the real org and delete drafts). Needs a sandbox/test customer and a test item.
3. Phase 3: SH SO draft creation only after the CEO grants SH API access and the shown proposal earns it (7 Oct condition).
4. Never auto-confirm; never create transfer orders from the portal in v1: Rizwan's team keeps that step in Zoho.

## 8. Open points to verify before any build (all need a sandbox or admin console, no guessing)

1. SO list filters and the pagination flag name (read rest of https://www.zoho.com/inventory/api/v1/salesorders/ beyond char 100,000).
2. `location_id` versus `warehouse_id` in SO line items for multi-warehouse orgs.
3. How `cf_*` custom fields appear on SO and item reads, and how to obtain `customfield_id`.
4. Real daily limit for SPS (7,500 vs docs) and SH (unknown).
5. Whether the Zoho plan includes outgoing webhooks / custom functions (SPS and SH).
6. Draft SO behaviour on stock commitment, and approval workflow in each org.
7. Whether one Self Client can serve two orgs; irrelevant if we use one client per org as recommended.
8. Token endpoint limits (not found in docs read).
9. Self Client token type: authorization-code (refresh token) vs client-credentials.

## 9. Sources

- https://www.zoho.com/inventory/api/v1/introduction/ (org id, DCs, rate limits)
- https://www.zoho.com/inventory/api/v1/oauth/ (scopes, tokens)
- https://www.zoho.com/accounts/protocol/oauth.html (client types)
- https://www.zoho.com/accounts/protocol/oauth/self-client/overview.html
- https://www.zoho.com/inventory/api/v1/{items,contacts,salesorders,locations,transferorders,picklists,packages,shipmentorders}/
- https://www.zoho.com/us/inventory/help/settings/automation.html, .../incoming-webhooks.html, https://www.zoho.com/us/inventory/kb/automation/create-webhook.html
- https://www.apideck.com/blog/how-to-get-your-zoho-books-api-key (third party, multi-org remark)
- Local data: 02-stock-and-routing.md, 01-catalogue.md; /root/CLAUDE.md decisions table.

Prepared by Abdul Hadhee | IT Executive
