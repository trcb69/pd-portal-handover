# D-A. Architecture proposal: build it inside Zoho (Creator + Inventory + Analytics), minimal custom code

Prepared 17 Oct 2026. Design only: no live Zoho call, no credentials, nothing built.
Sources: my own R1 (Zoho API), R2 (Zoho native), R3 (flow), R4 (auth/hosting) in this folder, and the fact-checked data files `../01-catalogue.md`, `../03-patterns-and-lead-times.md`, `../05-p0-stock-by-location.md`. **I did not re-fetch any Zoho page for this document.** Every Zoho claim below carries the URL and the confidence tag it had in R1/R2: [DOC] read on an official page, [SNIPPET] seen only in a search result, [UNKNOWN] not confirmed. Where R1/R2 could not confirm something, this document does not either.
SH (org 843061977) and SPS (org 843825512) figures are never summed. Nothing here sends or automates WhatsApp.

## 1. Answer first

1. **This angle is feasible but not proven.** The whole flow (sales form, Rizwan's queue, production accept, SPS SO creation, status) fits in **Zoho Creator** with two Zoho Inventory connections. Nothing on the screens is impossible. What is not proven are three plumbing facts: a Creator connection to Inventory with sales-order scope, writing a sales order with a custom field from Deluge, and cross-org use of two connections. R2 found no official walkthrough for any of them. One 2-3 day spike settles all three (section 11).
2. **It is not "no scripts".** Creator is low-code, but the SPS-SO write, the stock hint and the status sync are Deluge scripts living inside Zoho. If your rule means "no code of any kind", this angle fails the rule. If it means "no scripts and extensions on the side, nothing to host", it passes. **You must say which.**
3. **Cost is a running licence, not a one-off:** about **USD 3,000-7,400 per year** for 31 named users (Creator Standard to Professional), USD 4,800 for 20 users on Professional, up to USD 12,000 at 40 users on Enterprise (section 8). Against that, there is no server, backup, TLS or login code to maintain.
4. **Build effort: about 9 developer-weeks (range 7-12) for one developer new to Creator.** A clickable demo with fake data in about 2 weeks; a demo that really reads SPS Zoho and creates a draft SPS SO in about 4-5 weeks (section 9).
5. **The SH side is blocked on the CEO exactly like every other angle.** Native does not remove the need for an SH admin (R2 s1). Without SH access the stock hint runs from an uploaded snapshot (section 3.3), which is the 7 Oct rule kept.
6. **Weakest points against a custom portal:** per-person licences for every manager, coordinator and salesperson; a polished 862-item catalogue search and 640-spelling end-customer picker are only as good as Creator lookup fields; plan call-limits are per user and tight (section 6.3); lock-in of logic in Deluge.

## 2. What this overrides (stated explicitly)

| Earlier decision | Effect |
|---|---|
| Zoho read-only everywhere (old plan, 8 Oct PD release spec) | Overridden, narrowly: Deluge creates a **draft SPS sales order** in the SPS org. SH Zoho stays read-only in v1. Needs your explicit OK. |
| 7 Oct: SH data via the signed-in browser session, SH API only after the proposal | Kept as the fallback. SH stock enters Creator as a snapshot upload until the CEO grants API access; then one connection replaces the upload. |
| 17 Oct: "we aren't going to build scripts or extensions" | Browser extensions, userscripts and the add-on: none. Deluge scripts inside Zoho: **yes, a few**. Decision for you (section 12, Q1). |
| Old OP-01..16 plan, Zoho add-on, tunnel-only password login | Not used. No VPS service, no port, no Traefik route. |

## 3. Components and connections

### 3.1 Architecture

```mermaid
flowchart LR
  subgraph CR[Zoho Creator app: "Custom Orders" - one app, one account]
    F1[Order form + line subform]
    F2[Stores queue + decision]
    F3[Production queue + accept]
    F4[Dashboard pages: Block A and Block B]
    T[(Tables: Orders, Lines, Customers+aliases,<br/>Item cache, Item map, Division-manager pairs,<br/>Audit log, Stock snapshot)]
    D[Deluge functions + schedules]
  end
  SHI[Zoho Inventory SH<br/>org 843061977<br/>READ only, needs CEO]
  SPI[Zoho Inventory SPS<br/>org 843825512<br/>READ + create draft SO]
  D -- "connection SH-read" --> SHI
  D -- "connection SPS-rw" --> SPI
  CSV[SH stock snapshot upload<br/>until CEO grants access] --> T
  F1 --> T --> F2 --> F3 --> D
  D --> F4
```

### 3.2 Component list

| # | Component | Lives in | Custom code? |
|---|---|---|---|
| 1 | Order form (header + line subform: item, qty, unit, required-by, job nature, artwork flags, notes) | Creator form | none; validation rules are Deluge one-liners |
| 2 | Customer + end-customer list (managed, with aliases for the 640 spellings) | Creator table + lookup field | none; seeded once from `data/*.csv` import |
| 3 | Item cache (862 customized items) and SH-to-SPS item map | Creator tables, refreshed by a schedule | 1 scheduled function (list items by `last_modified_time`) |
| 4 | Stock hint on submit and on triage | Creator table "Stock hint" with source + timestamp | 1 function: `GET /items/{id}` per line, read `locations` array |
| 5 | Stores queue: Fulfil from stock, Send to production, Split, Return | Creator report with buttons (custom actions) | small Deluge per button (set status, write audit row) |
| 6 | Production queue per division, Accept / Return | Creator report filtered by permission set + division pairs | small Deluge per button |
| 7 | **Create SPS SO** | Deluge function behind the coordinator's button | 1 function: `POST /salesorders`, customer = SH contact, `custom_fields` carries `CF.Order Received from` and a new portal-ref field |
| 8 | Status follower | scheduled function polling only the linked open SPS SOs by `salesorder_ids` (200 per call), then packages/shipments | 1 scheduled function |
| 9 | Dashboard Block A (accepted, no SPS SO) and Block B (live Zoho status), hand ticks, Send next | Creator pages/reports; ticks are checkbox fields | none for A; Block B filled by component 8 |
| 10 | Audit log | Creator table written by every button | inside 5-7 |
| 11 | Notifications | Creator/Deluge email | inside 5-7 (section 7) |
| 12 | Analytics (optional) | Zoho Analytics | none; charts only, see section 8 |

Everything above the Zoho line is configuration plus **about 8 small Deluge functions** (components 3, 4, 5, 6, 7, 8 and two helpers). There is no VPS service, no SQLite, no PM2, no port.

### 3.3 Zoho connection: orgs, OAuth, scopes

- **Mechanism.** Creator "connections" hold OAuth to another Zoho service; Deluge calls Inventory through them. Creator allows 10 / 50 / 100 connections on Standard / Professional / Enterprise (https://www.zoho.com/creator/pricing-comparison.html) [DOC]. We need two. **That a Creator connection can be authorised for Zoho Inventory sales-order scopes is [UNKNOWN]**; R2 found no official walkthrough (community threads only: https://help.zoho.com/portal/fr/community/topic/need-help-with-creating-a-sales-order-form-on-creator). Fallback: a Creator connection of the generic custom-service type pointing at the Inventory API with a Self Client refresh token (R1 s3). Either way the Inventory API contract is the same.
- **Orgs.** One connection per org, never one for both (R1 s3: one client across two orgs needs one user in both; you are SPS admin only).
  - **SPS connection** (you authorise it; you are the SPS Zoho admin): read items, read contacts, read sales orders, read settings (locations), read packages, read shipments, and `ZohoInventory.salesorders.CREATE`. Scope names: https://www.zoho.com/inventory/api/v1/oauth/ [DOC]; `salesorders.CREATE` confirmed on the create row of https://www.zoho.com/inventory/api/v1/salesorders/ [DOC]. Do not request FullAccess.
  - **SH connection** (the CEO or SH admin authorises it): **read only**: `ZohoInventory.items.READ`, `contacts.READ`, `settings.READ`, `transferorders.READ` (so Stores' transfer order number can be watched). No create scopes in v1.
- **Integration user.** Each org gets a dedicated "portal" Zoho user that owns the connection, not a person (R1 s3: the 14 Oct IT-manager dismissal is the reason). Cost of the extra Inventory seat is [UNKNOWN] (2 users included on Standard-Premium per https://www.zoho.com/inventory/pricing/ [DOC, amounts to be re-checked by eye]).
- **Until SH access exists.** A Creator form "Stock snapshot upload" takes a CSV from the browser-session pull (the 7 Oct method). The stock panel prints "snapshot of <date>", and its source switches from `snapshot` to `api` the day the SH connection is live. All stock snapshots today are 19 and 28 Sep, about 3 weeks old (R3), so a fresh pull is needed before any demo.

### 3.4 Daily API arithmetic

Inputs (from `../03`): 11.0 lines and 7.7 SOs per working day on average; worst day 35 SOs / 51 lines; about 229 open customized lines today (R3 s5, roughly 160 SOs). Limits: 100 calls/minute per org; daily cap by plan 1,000 / 2,000 / 5,000 / 10,000 / 10,000, SPS observed **7,500/day**, SH **unknown, so budget at the 1,000 floor** (https://www.zoho.com/inventory/api/v1/introduction/ [DOC]; SPS figure from the 7 Oct check).

**SH org (1,000/day floor), worst day**

| Call | Count | Calls |
|---|---|---|
| Stock hint on submit, 1 item read per line | 51 lines | 51 |
| Stock re-read at Stores triage (stock may have moved) | 51 lines | 51 |
| Item catalogue delta, hourly, 12 working hours | 12 | 12 |
| Item catalogue full refresh, 862 items at 200 per page | 5 | 5 |
| Contacts delta, hourly | 12 | 12 |
| Transfer order watch (only open ones, 1 call per 30 min) | 24 | 24 |
| **Total** | | **155 = 15.5% of 1,000** |

Average day: 11 lines gives 22 stock reads, so about 75 calls (7.5%).

**SPS org (7,500/day observed; if the real figure turns out to be the 1,000 floor, the same totals are still within it)**

| Call | Count | Calls |
|---|---|---|
| SPS free-stock read on triage, 1 per line | 51 | 51 |
| Create draft SPS SO, 1 call + 1 read-back per SO (one SO per accepted request; worst case 1 per line) | 51 | 102 |
| Catalogue delta hourly + full refresh | 12 + 5 | 17 |
| Status follower: linked open SOs fetched by `salesorder_ids` (about 160 SOs = 1 call), every 15 min over 12 h | 48 | 48 |
| Package + shipment lookups for SOs that changed (assume 2 calls per poll) | 48 x 2 | 96 |
| **Total** | | **314 = 4.2% of 7,500, or 31% of 1,000** |

Per-minute: the busiest burst is a manager accepting 10 requests in a minute, 20 calls, far under 100. Concurrency (5 free, 10 paid): Creator may run schedules in parallel, so stagger the four schedules by 5 minutes each.

**Creator-side call limits are the tighter constraint (section 6.3):** Deluge `InvokeUrl` counts as an "external call"; the plan allowance is 100 / 250 / 500 per user per day on Standard / Professional / Enterprise (https://www.zoho.com/creator/pricing-comparison.html [DOC]). Our two orgs together need about 470 `InvokeUrl` calls on a worst day (155 for SH plus 314 for SPS, added only for this Creator sizing and not as an org figure). If the allowance is pooled per account (users x allowance) that is fine; **if it is a per-user cap on the user running the schedules, Standard and Professional fail and Enterprise barely holds.** Whether it is pooled is [UNKNOWN] and is spike question S3.

## 4. Login

- Staff sign in with their **Zoho account** (Creator users are Zoho identities). Add Zoho's own MFA for managers, coordinators and admin; the exact MFA options are [UNKNOWN] here and must be read from the Zoho Accounts settings page before promising anything. No password code, no sessions, no TOTP library, no new dependency: the R4 hard-stop on a TOTP library does not arise.
- Roles are Creator **permission sets** (Standard allows 10 per app, enough for: sales, stores, manager, coordinator, admin) (https://www.zoho.com/creator/pricing-comparison.html [DOC]). Division scoping for managers and coordinators is a record-level filter on the division-pairs table (the 8 Oct rule: coordinators see their manager's divisions).
- **Shared login for Rizwan's team.** Creator licenses "each unique person" (https://help.zoho.com/portal/en/kb/creator/faqs/getting-started/articles/pricingplans [DOC]). A shared login is a licence question I cannot settle. My suggestion: give the five Stores people **named seats from day one**. It costs 5 x USD 20 x 12 = USD 1,200 a year on Professional, it removes the audit gap R3/R4 both flagged, and it makes the "initials" workaround unnecessary. If you insist on the shared login until launch, treat it as a pilot-only exception and ask Zoho support in writing.
- External users (customers or SH sales outside Zoho): not needed. Everyone in the flow is internal.
- Hosting/TLS/firewall: Zoho's. This removes R4's findings about the open port 4200, missing backups and Traefik config from this angle's scope; Creator data backup is a Zoho feature whose terms I did not read [UNKNOWN], so I would still run a weekly export (section 5).

## 5. Data and ownership

Creator holds the portal-owned records exactly as R3 s6 splits them: requests and lines, decisions, audit log, managed customer list with aliases, SH-to-SPS item map, division-manager pairs, cached Zoho status. Zoho Inventory keeps items, stock, SOs, packages, shipments and invoices. Record caps per user are 25k / 100k / 250k on Standard / Professional / Enterprise ([DOC] same page); our growth is about 3,450 lines a year plus audit rows, so no cap is near.
Exit path: keep the tables plain (no deep Deluge in the data model), and run a weekly CSV export to the VPS so a later move to a custom portal can start from the data. Whether Creator offers a scheduled export is [UNKNOWN]; the Creator API can read reports (https://www.zoho.com/creator/help/api/v2.1/api-limits.html describes its limits [DOC]).

## 6. Screens

### 6.1 Sales (about 10-20 people)

- **New order**: customer picker (managed list), line subform with item search over the cached 862 items (live items first), qty + unit, required-by (required, because only 99.3% of 2026 SOs carry one), job nature, artwork/dye-cutter/screen flags, notes, artwork file attachment. End-customer is a lookup against the alias list, with "add new" going to the Admin queue, not free text.
- **My orders**: one row per order with the least-advanced line status; Cancel while DRAFT; Request cancel after that.
- Native fit: good. A Creator form with a subform and lookups is its core use case.

### 6.2 Rizwan's team (Stores)

- **Triage queue**: one card per submitted line (item, qty, customer, required-by, sales person, age). Stock panel: SH free-to-promise per location from the stored hint, SPS free stock shown separately and labelled, "stock read at hh:mm" or "snapshot of date", the R3 hint text. Buttons: **Fulfil from stock**, **Send to production**, **Split**, **Return to sales** (reason required). Optional bulk button "send all unknown/none lines to production" (about 9 in 10 lines, R3).
- **Pick list** for stock fulfilment, with "transfer needed" for Galle and HO; Stores raises the transfer order **in SH Zoho** and types its number; a schedule watches it (read only).
- Native fit: good for queue and buttons. The stock panel is the only part that depends on the API connection.

### 6.3 Production (3 managers, 4 coordinators)

- **Production queue** per division (permission set + division pairs): item, qty, end customer, job nature, flags, required-by, Stores note, stock hint. **Accept** / **Return** (reason list).
- **Create SPS SO** on the coordinator's page: prefilled form, Edit, button calls the SPS write function, stores the SPS SO id and number, sets IN_PRODUCTION. Idempotency: the function first checks the line has no SPS SO id, then writes a portal-ref custom field; a failed call leaves the line in "Zoho write failed - retry" with the error text (R1 s7 mitigations). Draft only; no confirm call.
- **Dashboard**: Block A (accepted, no SPS SO yet, oldest first, count waiting more than 1 working day) and Block B (SPS SO status, packed/shipped quantities, expected vs today), with the hand-ticked steps (Artwork, Item photo, Job card; the steps themselves are a small admin table) and **Send next**. These are Creator checkboxes and a button, so they are native here.
- Native limit: Creator pages and reports are less flexible than the custom Production Dashboard (division filters, late flags, thresholds). The existing custom Production Dashboard (port 4300, preview spec Rev 9) is a **separate system**; under this angle either Creator replaces its portal-related blocks only, or the dashboard reads Creator records over the Creator API. I do not recommend merging them in v1.

### 6.4 Admin (you)

Unassigned list (items whose division has no manager; Paper Cup Unit today), customer alias management, item map, division-manager pairs, hand-tick step list, sync status (last run, last error, calls used), kill switch for the SPS write (a single boolean field the write function checks first), retry queue.

## 7. Notifications

Email only, plus on-screen counters on each queue. Creator can send email from Deluge and workflows; I did not read the exact feature page, so treat "Creator email" as [UNKNOWN] in detail but standard in kind. Triggers: line submitted (to Stores group), sent to production (to the division manager and coordinators), returned (to the origin), accepted (to Stores and the coordinators), SPS SO created, packed, shipped (to Stores and the sales person). Managers get a daily digest instead of per-line mail (open question R3). A push notification from the Creator mobile app is possible but [UNKNOWN]. WhatsApp: none, ever; the group "SH MANUFACTURING ORDER REQUEST" simply stops being needed.

## 8. Cost

Zoho list prices as read in R2; every figure is **excluding tax, annual billing, per user per month, and must be re-checked on the live pages** because the fetch tool dropped amounts on several Zoho pages. Creator source: https://prezohoweb.zoho.com/creator/pricing.html?src=hdd (preview host; main page https://www.zoho.com/creator/pricing.html did not show amounts) [DOC, shaky].

User count is my estimate; replace with the real list: ~15 sales, 5 Stores, 4 managers (Mubeena, Ranga, Ishan, Shihar), 4 coordinators, 3 IT/admin = **31**.

| Creator plan | per user / month | 20 users / yr | **31 users / yr** | 40 users / yr |
|---|---|---|---|---|
| Standard | 8 | USD 1,920 | **USD 2,976** | USD 3,840 |
| Professional | 20 | USD 4,800 | **USD 7,440** | USD 9,600 |
| Enterprise | 25 | USD 6,000 | **USD 9,300** | USD 12,000 |

Assumed LKR conversion for scale only: **LKR 300 per USD (my assumption, not a quote)**. 31 users: Standard about LKR 0.89 m, Professional about LKR 2.23 m, Enterprise about LKR 2.79 m a year.

Which plan: Standard allows 1 app (enough), 10 permission sets (enough), 250 developer API calls and 100 external calls per user per day (tight, section 3.4), 10 connections (enough). **I suggest Professional** (unlimited apps, 250 external calls, 50 connections) as the realistic floor and Enterprise only if spike S3 shows a per-user external-call cap. Plan-to-feature mapping beyond the limits table is [UNKNOWN].

Other lines:

| Item | Cost | Status |
|---|---|---|
| Inventory seat for the "portal" integration user, SPS and SH | each org includes 2 users on Standard-Premium; extra seat price not retrieved | [UNKNOWN] |
| Zoho Flow | not needed (Deluge in Creator calls both orgs). If used: about USD 29-49 per org per month, third-party figure | optional |
| Zoho Analytics | not needed in v1; native Creator charts suffice. If added: USD 60-145 per month plus viewer seats, and no confirmed Inventory connector | optional, [UNKNOWN] |
| Creator portal add-ons | none, all users internal | n/a |
| Server, TLS, backups, on-call | USD 0 (Zoho) | n/a |
| Build (your time) | section 9 | no cash |

**Year-1 cash for the recommended set: about USD 7,440 plus tax (about LKR 2.2 m at my assumed rate), recurring.** A custom portal on the existing VPS has no licence line but costs the same build weeks plus upkeep (R4).

## 9. Build effort and time to demo (one developer, new to Creator and Deluge)

| Work package | Dev-weeks |
|---|---|
| 0. Spike S1-S4 (section 11) and Creator account/connections | 0.5 |
| 1. Data model, roles, permission sets, seed import (customers, aliases, items, division pairs) | 1.5 |
| 2. Sales order form + validation + My orders | 1.0 |
| 3. Stores triage, stock hint function, snapshot upload, Split and Return | 1.5 |
| 4. Production queue, Accept/Return, division scoping | 1.0 |
| 5. Create SPS SO function + retry + kill switch | 1.0 |
| 6. Status follower + Block A/B pages + ticks + Send next | 1.5 |
| 7. Notifications + audit log + admin screens | 0.5 |
| 8. Testing in a real SPS test customer, UAT, fixes, docs for the team | 1.0 |
| **Total** | **9.5** (range 7-12) |

Time to demo:
- **Clickable demo, fake data, no Zoho calls: about 2 weeks** (packages 1, 2, part of 3 and 4).
- **Working demo that reads SPS Zoho and creates a draft SPS SO: about 4-5 weeks**, because the SPS write is the first thing the spike must prove and you hold the SPS keys yourself.
- **Full v1 with SH stock by API: not before the CEO grants access**; with the snapshot upload it can go live without him.
These are weeks of effort, not calendar promises; you also carry the E-Gate Pass, IT Conduit, the Production Dashboard rush and the goods-gatepass demo due end of October (/root/CLAUDE.md, 7 Oct), so calendar time will be longer.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Creator-to-Inventory sales-order write undocumented to me (R2) | The whole write path may need the generic-connection fallback or fail | Spike S1 before any other work; a draft SO with a custom field in the real SPS org |
| Per-user external-call cap (section 3.4) | Schedules stop silently after 100/250/500 calls | Spike S3; run schedules under one admin account; reduce poll rate to every 30 min (halves the status calls); Enterprise if needed |
| Deluge counts as "scripts" (user rule) | Angle disallowed | Q1 to you before any work |
| Per-person licensing, shared Stores login | Licence breach or audit gap | Named seats from day one (USD 1,200 a year) |
| Cross-org writes, one mistake creates a wrong SPS SO | Wrong books | Draft only, never confirm, idempotency check, kill switch, daily reconciliation report (portal SPS SO ids vs Zoho) |
| Draft SO may commit stock or hit an approval rule (R1 s7, [UNKNOWN]) | Stock shown reserved | Test in SPS with a test customer and item before pilot |
| Price pages disagree and some amounts failed to load | Budget off | Re-read live pricing; get a written quote from Zoho Sri Lanka/India partner |
| SH daily limit unknown and SH plan features unknown | SH reads slowed or blocked | Budget at 1,000/day; this design needs about 155 on the worst day |
| Lock-in of logic in Deluge | Rewrite cost to leave | Thin functions, plain tables, weekly CSV export |
| Zoho users for all SH sales staff may need Zoho accounts on a Zoho-identity | Onboarding friction, email-domain questions [UNKNOWN] | Confirm with spike S4 that an invited external user can open the Creator app |
| Creator account ownership: it is a separate Zoho account from both Inventory orgs; who owns it is not decided | Single point of failure (14 Oct lesson) | Owner = a company mailbox, you and one backup as super-admins |
| SH stock snapshots are 3 weeks old and SH Kohalwila and SPS WIP may be the same goods (R3) | Wrong hint | Fresh pull before demo; label sources; never sum SH and SPS |

## 11. Spike plan (before spending anything)

| # | Question | How (you are SPS admin; no CEO needed) | Pass |
|---|---|---|---|
| S1 | Can a Creator Deluge function create a draft SO with `custom_fields` in SPS? | Free or trial Creator account; a connection to SPS; one test SO for a test customer | SO appears as draft in SPS with the CF value |
| S2 | Do Workflow Rules, Custom Functions, Custom Buttons, Custom Modules exist in the SPS Settings > Automation menu? | read it in the admin console | list recorded; Inventory-only fallback judged |
| S3 | Is the Creator external-call allowance pooled across users? | Zoho documentation/support, plus a counter test | answer in writing |
| S4 | Can an invited user from another email domain open a Creator app? | invite a test user | yes/no |
| S5 | Real SPS plan and webhooks | read SPS admin console | recorded (also closes the 7,500 vs published tiers mismatch) |

If S1 fails, this angle falls back to Inventory-only hacks (custom module + approvals, R2 s3.1), which I rate weaker, or to the custom-portal angle.

## 12. What it needs from you and from the CEO

**From you (this week):**
- Q1. Does Deluge count as "scripts"? If yes, stop here.
- Q2. Approve the narrow write exception: draft SPS SO only (overrides "read-only everywhere").
- Q3. Run spike S1-S5 and read the live Creator and Inventory pricing pages by eye.
- Q4. Real user list (to fix the licence number) and named seats for Stores (or a written Zoho answer on shared logins).
- Q5. PCU with no manager: route to Ranga by an editable rule, or leave on the admin Unassigned list.
- Q6. May Stores act on SPS-side stock, or only see a hint (R3 default: hint and an "ask SPS to release" note)?

**From the CEO / SH admin:**
- C1. A dedicated "portal" integration user in SH Zoho and consent to read-only scopes (items, contacts, settings, transfer orders).
- C2. The SH daily API limit, the SH Inventory plan, and whether outgoing webhooks exist on it.
- C3. A written OK that a portal writes nothing in SH in v1 (so he sees the exposure is read-only).
Until C1 is granted, SH stock is the uploaded snapshot.

## 13. How it grows

- **Stock hint to full availability.** Today: per-location on-hand and available from `items` (`locations` array, https://www.zoho.com/inventory/api/v1/items/ [DOC]). Next: committed quantity from open SOs, transfers in transit, and an "ask SPS to release" request type.
- **Other items.** The 862-item customized catalogue is an item flag (`cf_fg_type = Customized`, R1); adding standard-stock orders is another order type on the same form, not a new app.
- **SH writes (phase 3).** After the CEO consents and the proposal is shown: draft SH SO and, only then, transfer orders (R1 s7). One more connection scope set, one more function.
- **Outgoing push.** When webhooks are confirmed on the plan, replace the 15-minute poll with an SO-modified workflow webhook (R1 s6).
- **Analytics.** If management wants trend charts (lead time median 18 days, p80 29, 45% on time from `../03`), add Zoho Analytics later; it cannot hold ticks or Send next.
- **Leaving.** If limits or licences bite, the tables export to CSV and the request/decision data seeds a custom portal; the Inventory API contract (R1) is the same either way.

## 14. Verdict

Choose this angle only if (a) Deluge is acceptable to you, (b) spike S1 and S3 pass, and (c) a running licence of about USD 7,400 a year for 31 people is acceptable. It wins on **no server to run, fastest demo, one place for logins and roles**. It loses on **licence per person, call limits per user, weaker UI control for the 862-item catalogue and the 640 end-customer spellings, and no more independence from the CEO than any other angle**. My suggestion is to run the 2-3 day spike regardless: it answers questions that every angle shares (SPS write, cf_ fields, draft SO side effects).

Prepared by Abdul Hadhee | IT Executive
