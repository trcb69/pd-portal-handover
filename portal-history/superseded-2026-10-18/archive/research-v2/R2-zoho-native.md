# R2 - Could Zoho itself do the customized-order flow better or cheaper?

Prepared 17 Oct 2026. Desk research only: public docs and search results, no live Zoho calls, no credentials.
Flow under test: SH sales submits -> Rizwan's team decides stock vs production -> production managers/coordinators accept -> Production Dashboard.
SH (org 843061977) and SPS (org 843825512) figures are never summed here.

## 1. Answer first

1. **Zoho-native can do roughly 70% of the flow, but only with the SH sales people as paid seats in Zoho.** Inventory's own customer portal cannot take orders (customers "cannot add items and place orders directly", https://www.zoho.com/inventory/help/customer-portal/). Sales staff would need an Inventory user seat or a Creator seat.
2. **The cheapest native route that fits is Zoho Creator** (a real form app with roles, approvals/blueprint-style stages, queues, Deluge writing to Inventory). At 20-40 users it costs about **USD 160-320/month (Standard) to USD 400-800/month (Professional, annual billing)**, before portal add-ons and extra Inventory seats. See section 4. That is a running cost; a Node/SQLite portal on the existing VPS has no licence cost, but costs build and upkeep time.
3. **The deciding blockers are not features:**
   - Every native route needs an **SH Zoho admin** (the CEO) to create the connection, workflow rules, custom functions or buttons in the SH org. The user is admin for SPS only, so on the SH side native is blocked on the same CEO decision as an API portal. Nothing is gained on access.
   - **The flow crosses two orgs** (SH SO, then SPS SO). I found no documented native cross-org workflow in Inventory; it needs Creator or Flow holding two OAuth connections.
   - **Production dashboard by Zoho Analytics** is plausible but unproven: I could not confirm a native Inventory connector, and the user-count rules push 20-40 viewers into the higher plans (section 6).
4. **My suggestion (not a decision):** if a Zoho-native pilot is wanted, do it in Creator, not inside Inventory. Keep it as a swappable "order intake" layer. The custom portal remains better when you need the 862-item catalogue search, 640 end-customer spellings clean-up, stock-by-location view and the Production Dashboard in one place. The final call is the user's; the CEO decides SH access.

## 2. What overrides earlier decisions (explicit)

| Earlier decision | Effect of this research |
|---|---|
| Zoho read-only everywhere (old plan) | Any native route writes to Zoho (Creator creating SOs, Inventory workflow rules, custom functions). So does the new portal direction. Overrides read-only; needs the user's explicit OK. |
| 7 Oct: SH data via browser session, SH API asked later | Native routes are not possible through a read-only browser session. They need SH admin rights now. |
| User = Zoho admin for SPS only | SPS-side native work (SPS SO creation helpers) is possible without the CEO. SH-side is not. |
| No scripts/extensions (user, 17 Oct) | Deluge custom functions and buttons are scripts inside Zoho. Creator is a low-code app, not a script on the side. The user should say whether Deluge counts as "scripts". |
| Never build WhatsApp automation | Unaffected. No Zoho option here sends WhatsApp and none is proposed. |

## 3. Capability check, product by product

Confidence tags: [DOC] stated on an official Zoho page I read; [SNIPPET] only seen in a search result; [UNKNOWN] could not confirm.

### 3.1 Zoho Inventory (the org the user already has)

| Need | Finding | Source |
|---|---|---|
| Approval on sales orders | Approvals can be set per module including Sales Orders and Custom Modules. Types: No / Simple (any admin or approver) / Multi-level (up to 10 levels). Not stated: who may submit; not stated: plan restriction. [DOC] | https://www.zoho.com/inventory/help/transaction-approval-new-flow/configure-approvals.html |
| Custom approval criteria | Listed for Zoho Books and ERP, not seen in the Inventory page. [UNKNOWN for Inventory] | https://www.zoho.com/books/help/transaction-approval/configure-approvals.html |
| Workflow rules | Community announcement: custom workflows for Sales Orders, Purchase Orders, Bills, Invoices; actions incl. field update, webhook. [SNIPPET] | https://help.zoho.com/portal/en/community/topic/introducing-workflow-automation-in-zoho-inventory |
| Custom functions (Deluge) | Created under Settings > Automation > Workflow Actions > Custom Functions, run by a workflow rule. Supported modules, timeouts and plan not stated on the page. [DOC, gaps] | https://www.zoho.com/inventory/kb/automation/custom-function.html |
| Custom buttons | Doc says custom buttons run Deluge or open links, on transactions. Whether the Sales Order detail page supports them, and plan, not confirmed by what I fetched. Community threads show users attaching Deluge buttons to Inventory records. [SNIPPET] | https://www.zoho.com/inventory/developer/extensions/extension-components.html |
| Custom modules | Support validation rules, custom buttons/links, lookup related lists, and **Blueprints** (states and transitions). Plan availability and module count not stated. [DOC, gaps] | https://zstatic.zohostatic.com/za/inventory/help/custom-modules/preferences.md |
| Incoming webhooks | A Deluge function gets a URL; a third party can call it. Plan not stated. [DOC] | https://www.zoho.com/inventory/help/settings/incoming-webhooks.html |
| Customer portal | Customers view SOs, pay invoices, track shipments. **Cannot place orders**. Needs "certain plans". [DOC] | https://www.zoho.com/inventory/help/customer-portal/ |
| Vendor portal | Accept/reject POs, invoices. Not relevant (sales and production are internal). [DOC] | https://www.zoho.com/inventory/help/vendor-portal/ |
| Org API limit | Free 1,000, Standard 2,000, Professional 5,000, Premium 10,000, Enterprise 10,000 calls/day; 100/min per org. [DOC] | https://www.zoho.com/inventory/api/v1/introduction/ |

Notes:
- **Plan mismatch to resolve.** The SPS limit checked on 7 Oct is 7,500 calls/day. That figure matches none of the tiers on the page above. The real SPS (and SH) plan or edition must be read from the admin console before any plan-based statement about them. SH's limit is still unknown.
- The pricing page I fetched (https://www.zoho.com/inventory/pricing/) shows Standard USD 29, Professional 79, Premium 129, Enterprise 249 per organisation per month billed annually, with 2 users included (7 on Enterprise), and "Customization & Automation" starting at Premium; it does **not** map workflow rules, custom functions, custom buttons, approvals or custom modules to a plan. Treat the plan-to-feature mapping as [UNKNOWN] until the "pricing comparison" page or the admin console confirms it. The fetch tool summarises pages, so also re-check the numbers by eye on the page.
- Extra Inventory user seat price: not retrieved. [UNKNOWN]

**Can Inventory alone do the flow?** Partly, with a hack: sales person (Inventory user) creates an SO in a "Pending" state; approval or a custom status/field "Production request" is set by Rizwan's team (custom button or field update); a workflow rule fires a custom function that calls the SPS org API to create a request. Gaps: sales staff need Inventory seats and the full Inventory UI (no tailored catalogue/end-customer form); a **cross-org** write needs a Deluge connection to the SPS org; the production queue and accept click would live in a custom module in the SPS org, which the managers and coordinators would also need seats for. I found no documented queue view with per-division filtering for non-admin roles. [UNKNOWN]

### 3.2 Zoho Creator

| Item | Finding | Source |
|---|---|---|
| Plans / per-user price (USD, EN pricing page) | Standard 12 monthly / **8 annual**; Professional 30 / **20**; Enterprise 37 / **25**. | https://prezohoweb.zoho.com/creator/pricing.html?src=hdd (Zoho preview host; the main page https://www.zoho.com/creator/pricing.html did not show amounts in my fetch; re-check on the live page) |
| Licensing | Per user: "licenses for each unique person who will access your applications". | https://help.zoho.com/portal/en/kb/creator/faqs/getting-started/articles/pricingplans |
| Limits per plan (Std / Pro / Ent) | Apps 1 / unlimited / unlimited; records 25k / 100k / 250k **per user**; Deluge execution instructions 10k / 20k / 50k; Developer API calls 250 / 500 / 1,000 per user per day; external calls incl. webhooks 100 / 250 / 500 per user per day; connections 10 / 50 / 100; portal permission sets 10 / 50 / 250 per app. | https://www.zoho.com/creator/pricing-comparison.html (French page; "Gratuit" column also seen) and https://www.zoho.com/creator/help/api/v2.1/api-limits.html |
| Throttle | 50 API calls per user per minute; 6 concurrent calls per account. | https://www.zoho.com/creator/help/api/v2.1/api-limits.html |
| Portal (external) users | Free plan has up to 3 portal users; more are paid add-ons by tier (250 to 100,000), amounts not retrieved. Whether internal staff in other roles need full licences or portal slots: [UNKNOWN]. | https://www.zoho.com/creator/pricing-comparison.html |
| Deluge calls count | InvokeUrl and predefined integration tasks consume "external calls", counted per execution (a loop of five = five). | https://help.zoho.com/portal/en/kb/creator/developer-guide/billing/articles/view-and-manage-billing |
| Inventory integration | Creator has Zoho-app integration on all paid plans. I found no official walkthrough of a Creator-to-Inventory sales-order connection; community threads describe building a Creator sales-order form with a subform. The usual method is a Deluge connection plus the Inventory API. Treat as feasible but not documented to me. [SNIPPET/UNKNOWN] | https://help.zoho.com/portal/fr/community/topic/need-help-with-creating-a-sales-order-form-on-creator |

Can Creator do the flow? **Yes in principle.** Sales form (customer, item, end customer free text, qty, due date) -> record in "Pending decision" -> Rizwan's team role sees a queue and clicks Stock or Send to production -> production role queue per division, click Accept -> a Deluge call creates the SO in the SPS org (second connection) and/or the transfer order in SH. Creator's own record views would also act as the queue and a basic dashboard. Weak points: stock-by-location lookup must be pulled from Inventory by API (counts against the Inventory org daily limit, which for SH is unknown); the 640 end-customer spellings need a lookup list built by us; catalogue search over 862 items is a lookup field, less polished than a purpose-built screen.

### 3.3 Zoho Flow

| Item | Finding | Source |
|---|---|---|
| Plans | Free: 100 tasks/mo, 5 flows, 15-min polling. Standard: 5k to 5M tasks (default 5k), unlimited flows, 15-min polling. Professional: 10k to 5M (default 10k), 5-min polling. Price amounts did not load in my fetch; a 2026 third-party article says USD 29 and 49 per organisation per month, which conflicts with older figures (~10 and ~25). Unverified. Pricing is per organisation, not per user. | https://www.zoho.com/flow/pricing.html ; third party: https://automationatlas.io/answers/zoho-flow-pricing-explained-2026/ |
| Task meaning | A task is a successful action execution in a flow. | https://www.zoho.com/flow/pricing.html |
| Inventory actions | Flow's "Create Sales Order" reportedly adds one line only (community report; answer not seen). [SNIPPET] | https://help.zoho.com/portal/fr/community/topic/need-help-with-creating-a-sales-order-form-on-creator |

Flow is a glue layer (trigger -> action). It has no screens for sales or production, so it cannot be the portal. It is useful only to link a Creator or Inventory event to the other org. 5-minute polling is slower than a button-driven call. Cost is small and per organisation, not per user.

### 3.4 Zoho Analytics (for the Production Dashboard)

| Item | Finding | Source |
|---|---|---|
| Plans | Free: 2 users, 10,000 rows, 5 workspaces. Paid: Standard, Premium, Enterprise (older page also lists Basic). Examples on the help page: Standard USD 60/month with 5 users, 1M rows; Premium USD 145/month. Third-party list: Basic 30, Standard 60, Premium 145, Enterprise 495-575 per month annual. Third-party figures disagree. | https://www.zoho.com/analytics/help/pricing.html ; https://coefficient.io/zoho-analytics-pricing |
| Seats | Users are licensed per account with add-on users; whether read-only dashboard viewers count as users: [UNKNOWN] (I assume they do). For 20-40 viewers the Standard 5-user base needs add-ons; add-on user price not retrieved. | https://www.zoho.com/analytics/help/pricing.html |
| Embedded / white label | Paid plans only; custom-quoted per third party. | same page |
| Inventory connector | The pricing help page lists Books and CRM connectors but I found no confirmation of a native Inventory connector or its refresh interval. A third-party connector vendor recommends 24-hour sync because of Inventory's API limits. [UNKNOWN] | https://fivetran.com/docs/connectors/applications/zoho-inventory |
| Enterprise Inventory plan | The Inventory pricing page lists "Zoho Analytics" as included at the Enterprise tier (USD 249/org/month). Scope of that bundle not stated. | https://www.zoho.com/inventory/pricing/ |

Analytics is a read-only dashboard tool. It cannot hold the "accept" click or the hand-ticked Artwork / Item photo / Job card steps (the dashboard's own writes). It would only replace the dashboard's charts and only if the data refresh is acceptable. The Production Dashboard design already includes document ticks and Send next, which Analytics cannot do. So Analytics is not a replacement for it.

## 4. Cost at 20-40 users (USD, Zoho list prices read above; re-check before quoting anyone)

Assumed users: ~10-20 sales, ~5 Rizwan's team, 3 managers + coordinators, user and IT. Annual billing. Excluding tax.

| Route | 20 users | 40 users | Not included |
|---|---|---|---|
| Creator Standard (8/user) | 160/mo | 320/mo | 1 app only; 25k records per user; Std limits (250 dev API calls/user/day) |
| Creator Professional (20/user) | 400/mo | 800/mo | portal add-ons if used |
| Creator Enterprise (25/user) | 500/mo | 1,000/mo | |
| Inventory extra user seats | [UNKNOWN] | [UNKNOWN] | 2 users included on Standard through Premium, 7 on Enterprise per the pricing page |
| Zoho Flow (org-level) | roughly 25-49/mo, unverified | same | |
| Zoho Analytics (org-level + add-on users) | 60-145+/mo plus seat add-ons, unverified | higher | |
| Custom Node/SQLite portal | 0 licence | 0 licence | build and maintenance time; VPS already paid |

Yearly range for Creator Professional: 4,800 (20 users) to 9,600 (40 users). I did not convert to LKR; the user should convert at the current rate.

Hidden cost: if Creator reaches Inventory for stock look-ups, those calls draw on the Inventory org's daily limit (SH unknown; SPS observed 7,500 with 0 used in the last 30 days, 7 Oct). A custom portal has the same exposure, so this does not favour either side.

## 5. Lock-in and limits

- **Data and logic live in Zoho** (Creator records, Deluge, Blueprints). Export is possible but the logic is rewritten from scratch elsewhere. The custom portal's SQLite is portable but Zoho data stays in Zoho either way.
- **Licensing is per unique person** and there is no cheap read-only seat found for Creator; every manager, coordinator and sales person counts. Adding the recruit and the new IT assistant raises cost.
- **Plan walls**: Standard Creator allows 1 app and 10 portal permission sets; Professional is the realistic minimum for a multi-role flow.
- **Daily call caps scale by user count** (Creator). A small number of heavy users (Rizwan's team using shared logins until launch) hit per-user caps first; shared login is a licensing question I could not settle.
- **Two-org write path** is the least documented piece. I do not claim any endpoint or scope; the exact Inventory scopes for sales orders were not on the page I fetched and must be read from the Inventory API docs for the SO endpoint before design.
- **Deluge limits** (execution instructions per month, timeouts) are tight on Standard (10,000) and are consumed by loops over line items.
- **Vendor risk**: pricing pages disagree between sources and between regional editions; re-quote before committing.

## 6. Verdict per component

| Component | Native Zoho verdict |
|---|---|
| Sales intake form (catalogue, end customer text) | Creator: possible; Inventory alone: no tailored form, needs a seat. Custom portal: better UX, zero licence. |
| Rizwan's team decision (stock / production) | Creator queue with two buttons: possible. Inventory approvals: possible but approval is yes/no, not "send to production". |
| Production accept by division | Creator role-based views: possible. Inventory: not shown to me. |
| Create SPS SO | Needs cross-org Deluge/API in both. |
| Dashboard | Analytics for charts only; the dashboard's ticks and Send next need an app. |
| WhatsApp group replacement | Not touched; no WhatsApp automation anywhere. |

## 7. Open questions the user can close in minutes

1. Which Inventory plan or edition are SH and SPS on (SPS shows 7,500 calls/day, which matches no listed tier)? Read it in each org's admin console; the SH admin must do SH.
2. Do Workflow Rules, Custom Functions, Custom Buttons and Custom Modules appear in the SPS org's Settings > Automation menu? The user is SPS admin and can check without any API.
3. Is Deluge allowed under "no scripts"?
4. Are shared logins for Rizwan's team allowed at Creator (per-unique-person licensing, per the FAQ above) for the pilot period?
5. Re-read the live Creator and Inventory pricing pages in a browser; the fetch tool dropped amounts on several pages.

## 8. Sources

- https://www.zoho.com/creator/pricing.html , https://prezohoweb.zoho.com/creator/pricing.html?src=hdd , https://www.zoho.com/creator/pricing-comparison.html
- https://help.zoho.com/portal/en/kb/creator/faqs/getting-started/articles/pricingplans
- https://www.zoho.com/creator/help/api/v2.1/api-limits.html
- https://help.zoho.com/portal/en/kb/creator/developer-guide/billing/articles/view-and-manage-billing
- https://www.zoho.com/inventory/pricing/ , https://www.zoho.com/inventory/api/v1/introduction/
- https://www.zoho.com/inventory/help/transaction-approval-new-flow/configure-approvals.html
- https://www.zoho.com/inventory/kb/automation/custom-function.html
- https://www.zoho.com/inventory/help/settings/incoming-webhooks.html
- https://www.zoho.com/inventory/help/customer-portal/ , https://www.zoho.com/inventory/help/vendor-portal/
- https://zstatic.zohostatic.com/za/inventory/help/custom-modules/preferences.md
- https://www.zoho.com/inventory/developer/extensions/extension-components.html
- https://help.zoho.com/portal/en/community/topic/introducing-workflow-automation-in-zoho-inventory
- https://www.zoho.com/flow/pricing.html , https://automationatlas.io/answers/zoho-flow-pricing-explained-2026/
- https://www.zoho.com/analytics/help/pricing.html , https://coefficient.io/zoho-analytics-pricing , https://fivetran.com/docs/connectors/applications/zoho-inventory
- https://help.zoho.com/portal/fr/community/topic/need-help-with-creating-a-sales-order-form-on-creator
