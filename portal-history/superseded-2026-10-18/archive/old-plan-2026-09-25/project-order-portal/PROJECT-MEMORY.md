# Order portal — project memory

**Changed 25 Sep 2026:** added the credit-limit data-source decision (Zoho Inventory, no Books) to
§6 and removed it from §7's open-items list, where it had been flagged as an active conflict.
Updated the §7 credit bullet to two remaining questions. No other section touched.

**Read this file first, every session, before touching this project.** It will be linked from
this project's `CLAUDE.md`. Written by Abdul Hadhee | IT Exec | Standard-Holdings, 25 Sep 2026.

---

## 1. What this project is

The order portal is **Release 1 of the production-dashboard app**
(`/root/dev/production-dashboard`) — not a separate codebase or repo
(`plans/40-order-portal-developer-brief.md:1`). It shares the schema, auth, migrations and
pipeline Release 0 already built there. It's planned/staffed as its own project (16 steps,
OP-01…OP-16, a separately scoped body of work) but built inside the one existing repo.

**It replaces three things that fail today** (`plans/40...` §1, `CLAUDE.md:15-19`):
- A WhatsApp order group with no record of when an order really started.
- A paper job file whose physical location is the only status anyone can check.
- A monthly Excel sheet re-typed from data Zoho already holds.

**Who it serves** (spec §5.1, `plans/40...` §2): requesters (SPS/SH order-desk staff placing
orders), triage (accept/reject/ask), coordinators (Nimesha, Madushi, Nirmani, Umanda — create job
files, link SOs), managers (Mubeena, Ranga, Ishan), a Credit & Billing Reviewer (Hazeem's
function), stores (Ilham + SH's Saman/Pasindu once in scope), invoicing (Darshani), GM
(Samitha)/COO (read-only, redacted), and admin (the user).

**Sponsor:** Mr. Samitha, SmartPack GM — this is the requested build, not the user's initiative
(unlike the stock system / BI work, which is separately labelled "my initiative").

---

## 2. Current state (25 Sep 2026)

- **Release 0 (foundation) is built, tested, not deployed.** Dev repo HEAD `b0cd339`
  (`/root/dev/production-dashboard`). 136 tests green (`npm test`, verified directly against HEAD
  `b0cd339`, 25 Sep 2026 — `dashboard-state.md:2`'s "143 tests green" is a stale count), reviews
  PASS.
  Routes live: auth, `/events` SSE, `/health`, `/admin/imports`, users/teams/bulk-requesters,
  divisions/stages/processes/aliases/pairs/reason-codes/reject-reasons/order-type-aliases/
  calendar/holidays/audit (`server/routes/`: `admin-config.js`, `admin-imports.js`,
  `admin-users.js`, `auth.js`, `events.js`, `health.js`, `index.js`).
- **Schema frozen at migrations 001–004** (`server/db/migrations/`: `001-schema.sql` 366 lines,
  `002-seed.sql` 77, `003-migration-hashes.sql`, `004-migration-hashes-append-only.sql`).
- **Release 1 (the order portal itself) is NOT built.** No order-submission route, no triage
  workspace, no credit check, no `orders.company`/`.location` columns yet (`dashboard-state.md:3`).
- **The "Release 1 v2" spec delta is NOT written.** Must cover company/SH-location tagging,
  enums→lookup tables, a `notifications` table, multi-job-per-order, MFA, `customer_portal=false`
  — step **OP-01**; no Release-1 code is written before it passes `plan-critic`
  (`/root/.claude/CLAUDE.md` §2).
- **Floor Board demo is live** (pm2 `Production`, :4310) — a different, already-shipped preview,
  not this release.
- **Release order agreed 22 Sep:** Preview → R0 (done) → **R1 order portal + auto credit check** →
  R2 managers' job list → R3 stores/invoicing → R4 blockers/raw-material → R5 GM view → R6 floor
  digital. The 22-Sep "no dates" placeholder is **superseded (25 Sep 2026)** by the dated master
  schedule — **R1 (this project) goes fully live 11 Feb 2027** (`dev/dated-schedule.json` row
  `OP-14`); R2 is `PD-06`, 4 Mar 2027. See `dev/01b-dated-schedule.md` for every release's date.
- **This project's own build steps are already written**, in build order, with acceptance
  criteria, inputs and open questions per step: `dev/order-portal/02-process-steps.md` (OP-01…
  OP-16, ~12.0 developer-weeks for OP-01→OP-14). Question pack: `dev/order-portal/questions.md`.
  Read both before starting any step.

---

## 3. Stack and conventions (from the repo — cite before assuming)

Node ≥24, Express 5, **better-sqlite3** (synchronous, no async DB calls), React 19 + Vite 8 +
Tailwind 4 + shadcn-style components, TanStack Query/Table, `multer` uploads, `qrcode`, `exceljs`
for Zoho xlsx reads, `zod` validation (`package.json`). Tests: `node --test` (`npm test`),
Playwright (`npm run test:e2e`), `@axe-core/playwright`. `npm start` runs migrations
automatically at startup — **idempotent by design**, never run a migration script by hand
(`README.md`). Port 4300 (`PORT`), DB at `data/production.db` (`DB_PATH`). Git history so far is
all Release-0 foundation work — 32 commits ending `b0cd339` (`git log --oneline b0cd339 | wc -l`,
verified directly).

---

## 4. Non-negotiable rules

1. **Pipeline gates apply** (`/root/.claude/CLAUDE.md` §2): spec → plan-critic → test-author →
   implementer → test-runner → code-reviewer → security-auditor → db-migration-guard →
   release-captain. `plan-critic: BLOCK` means no code; `code-reviewer: BLOCK` means nothing
   ships. Auth/uploads/secrets/external input/new routes always go to `security-auditor`; any
   schema touch goes to `db-migration-guard`.
2. **Additive migrations only. Schema frozen at 001–004.** New work is migration `005+`.
   Forbidden: `DROP TABLE`, `DROP COLUMN`, any `RENAME`. Allowed: `DROP VIEW|TRIGGER|INDEX IF
   EXISTS` only when the same file re-creates that name (spec §6.1, `server/db/lint-migrations.js`).
3. **Dev clone only, never deploy.** Write and test in `/root/dev/production-dashboard`. Never
   write inside the live tree, never migrate/restart/push/deploy from here — the human runs
   `shdeploy production-dashboard`. `guard-live-paths` blocks live writes; a block is a finding to
   report, not an obstacle to route around.
4. **No retyping Zoho data.** Mirror tables (`zoho_*`) are read-only, written only by the shared
   upsert functions. Core tables (`orders`, `jobs`, …) are owned by the app. Never mix a Zoho
   field and an owned field in one row (spec §6.2 vs §6.3, `CLAUDE.md §2` rule 3).
5. **SH and SPS are never summed.** Separate companies, separate reports, always — "the single
   most-repeated rule across every source document" (`CLAUDE.md §17.1b`). Every new report/screen
   is checked for cross-company summing as a standing code-review item (OP-07 AC3).
6. **Job numbers are opaque strings. Never parse them.** Formats vary wildly (`OPD6700`,
   `PSU/BTN/989`, `RWU/IMP2357/QPP/00025/BIO`) — no validation/extraction/auto-numbering logic
   that assumes a shape (spec §8).
7. **Security rules are load-bearing** (spec §11): scrypt auth, hashed session id,
   `HttpOnly/Secure/SameSite=Strict`, 12h idle/7-day expiry; CSRF via required `Origin` (missing
   Origin also rejected); rate limits; roles checked server-side on every route; uploads
   allow-listed by **magic bytes** never extension (SVG/HTML/XML/script never accepted); GM/COO
   redaction (worker identity → "operator", `payload_json` never sent, ≥2-worker aggregates only).
8. **Never build any WhatsApp-sending capability.** "Never build anti-detection" is explicit and
   non-negotiable (`memory/hub-whatsapp-notifications.md`). WhatsApp is an urgent-alert channel
   only, via the separate, paused Hub WhatsApp project — never a bespoke sender built here.
9. **The portal never writes to Zoho.** `outbox` stays `held` (spec D15). A browser-only helper
   fills Senuri's Zoho form; she clicks Save. No server-side Zoho writes, ever.
10. **Never mention any COO-analyst role in any document.** Sign "Abdul Hadhee | IT Exec |
    Standard-Holdings". Stock system/BI work is "my initiative"; the order portal and production
    dashboard are the requested build (sponsor Samitha).

---

## 5. Data sources and how to read them

- **Authoritative spec:** `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md`
  (Rev 7.3, `plan-critic: PASS`). If this memory file and the spec ever disagree on something the
  spec already decided, **the spec wins** — come back and fix this file.
- **This project's brief:** `plans/40-order-portal-developer-brief.md` — everything needed before
  touching the portal, gathered from the spec + working notes + business-plan analysis, every
  fact cited to a file.
- **This project's build steps:** `dev/order-portal/02-process-steps.md` (OP-01…OP-16, effort,
  acceptance criteria, dependencies, open questions per step) and
  `dev/order-portal/questions.md` (same questions, grouped by who answers them) and
  `dev/order-portal/prompts/` (one file per step, `OP-01-...md` … `OP-16-...md`).
- **Current build/decision state:** `analysis/research/dashboard-state.md` (25 Sep survey, cites
  file:line for every claim).
- **Business context:** `analysis/BRIEF.md` (company/people/data map), `plans/11-production-plan-2027.md`
  (the MTS/buffer-stock proposal behind OP-15).
- **Zoho capability/pricing reference:** `analysis/research/market-and-zoho.md` (cite URLs for
  any Zoho-capability or pricing claim, never invent one).
- **The dev repo itself, read-only for this file's purposes:** `git log`, `CLAUDE.md`/`README.md`,
  `server/db/migrations/`, `server/routes/`, `package.json` in `/root/dev/production-dashboard`.
- **Zoho exports on disk** (read-only, never write inside `/root/exports`): see `BRIEF.md` "Data
  on disk" for the full list (SPS sales orders, SH monthly sales/purchases, 19-Sep stock/recipe
  snapshot).

---

## 6. Decisions already made

| Date | Decision | Source |
|---|---|---|
| 22 Sep | Release order: Preview → R0 → **R1 (this project)** → R2 → R3 → R4 → R5 → R6. | `dashboard-state.md:4` |
| 25 Sep | The 22-Sep "no calendar dates" placeholder is superseded — fixed dates for every step, each part gets an IT-test/UAT/(pilot) window before full release. R1 (this project) full release **11 Feb 2027**. | `dev/01b-dated-schedule.md` |
| 21 Sep | Credit check is **automatic at order placement**, not a manual Hazeem look-up. Formula: `over_by = (pending dues + this order's value) − credit limit`; error popup with exact LKR amount if `over_by > 0`. | `CLAUDE.md §17.2` step 3 |
| 20 Sep | `customer_portal` flag defaults `false`, hidden — no customer-facing route built now. | spec Q9, `CLAUDE.md §17.2` |
| 20 Sep | SH SO linking fallback until SH admin access arrives: Senuri pastes the SO number, portal validates against the mirror ("way B"). "Way C" (fuzzy match by customer/date/line) explicitly rejected. | `zoho-helper-userscript-spec.md §5b` |
| 20 Sep | Build order SPS-side first, complete; SH side (OP-16) floats until SH admin access lands. | `CLAUDE.md §4`, `BUILD-ORDER-2026-09-20.md` |
| 23 Sep | Scope is SmartPack (SPS)-mandated; SH side built only with Rizwan's agreement, as his own request. | `CLAUDE.md §17.1b` |
| 25 Sep | This project's 16-step build sequence (OP-01…OP-16) with effort estimates and acceptance criteria written. | `dev/order-portal/02-process-steps.md` |
| 25 Sep | **Credit limit is read automatically from Zoho Inventory** — `credit_limit` field on the Contact object, `GET /contacts/{id}`, confirmed live in our own SPS export data. No Zoho Books access, login or integration needed; the earlier Books ask is closed for good. | `analysis/research/zoho-credit-limit.md` |
| 25 Sep | Dated master schedule published for every OP-01…OP-16 step (build/IT-test/UAT/full-release dates) — no more "no dates" placeholder for this project. | `dev/01b-dated-schedule.md`, `dev/dated-schedule.json` |

## 7. Decisions still open (do not decide — list and route)

- **Credit check — two questions remain** (OP-08, `plans/40...` §5): (1) block outright or hold for
  a named releaser; (2) "pending dues" = all unpaid invoices or only overdue ones (the credit-limit
  research recommends all-unpaid, Finance still confirms). The third question — where the credit
  limit lives — is **DECIDED** (25 Sep 2026): Zoho Inventory, no Books access needed. That
  conflict is closed, not open any more.
- **Triage ownership** — who triages SPS orders (spec Q7, nobody proposed); who triages SH orders
  (Senuri suggested, unconfirmed).
- **Multi-job-per-order shape** — does any order really split into several jobs at once? Needs GM
  Samitha before OP-01's delta is written.
- **English-only vs Sinhala/Tamil** — not mentioned anywhere in the spec; ask GM Samitha, don't
  assume.
- **7 unconfirmed SH locations** — only Head Office, South Branch, Central Branch are seen in live
  order data; Rizwan/Abdullah confirm the rest (OP-07).
- **SH Zoho admin access** — `ithelp@` sees only 1 of 10 locations. Blocks OP-07's "verified"
  flag, OP-11's SH-side sync, and all of OP-16. Owner: CEO; Rizwan is the practical contact.
- **"Portal Order No" mandatory field** — recommended mandatory in Zoho SH SO settings (config,
  the user's Zoho admin); check with Senuri for a workflow it might break (OP-12).
- **SMTP account** for notification email — not yet provisioned (OP-09).
- **Manager/coordinator pairs missing** for PCU, PCLU, DPU, PPU, CWU (OP-04).
- **Safety-stock/MTS buffer policy** (precondition for the future call-off order type, OP-15) —
  not signed off; the paused stock-system project (Abdullah/Ilham) must resume first (COO's call).

Full per-person question pack, what each unblocks, mini-report needed or not:
`dev/order-portal/questions.md`.

---

## 8. People and roles

| Person | Role in this project |
|---|---|
| **Mr. Samitha** | SmartPack GM — sponsor; signs off manager/coordinator pairs, safety-stock policy, i18n, multi-job shape |
| **COO** | Confirms triage ownership, credit sign-off authority, redaction rules |
| **CEO** | Owns SH; grants SH Zoho admin access (blocks OP-07/OP-11/OP-16) |
| **Hazeem** | Credit & Billing Reviewer (Finance) — answers the two remaining credit-check questions (OP-08); the data-source question is DECIDED, 25 Sep 2026 |
| **Senuri** | SH Team 03 lead, creates SH sales orders; candidate SH-side triage; the "Portal Order No" workflow is hers |
| **Nimesha, Madushi, Nirmani, Umanda** | Coordinators — create/receive job files, link SOs, attachments |
| **Mubeena, Ranga, Ishan** | Managers — jobs, receive, ticks, blockers, output |
| **Ilham / Darshani** | SPS stores (shipment ref) / invoicing (ITN ref) |
| **SH Rizwan / Abdullah / Nazmi** | Runs SH Food Packaging desk / SH key-customer buffer stock (separate paused project) / SH purchasing |
| **IT / the user** | Admin: config, users, imports, audit, SPS Zoho admin actions |

---

## 9. Glossary

- **Job number / `job_no`** — an opaque string identifying a production job, e.g. `OPD6700`,
  `CPU-155`, `PSU/BTN/989`, `RWU/IMP2357/QPP/00025/BIO`. Never parsed. Nullable until a coordinator
  sets it. Different from the Zoho SO number — the two are linked only via `job_so_links`.
- **JOBORDER-…** — the SPS Zoho sales-order number prefix for customised orders (e.g.
  `JOBORDER-08338`). The customer on this SO is almost always "Standard Holdings (Pvt) Ltd" — the
  real end customer is in `CF.Order Received from`.
- **Portal Order No** — a custom field being added to the SH sales order in Zoho, written by the
  portal's `OR-000123` number so the two systems auto-link (OP-12).
- **`so_key`** — the normalised matching key for an SO number: trim, uppercase, regex
  `^([A-Z]+-\d+)(\s*-.*)?$`, group 1 is the key. `JOBORDER-08338 - C` and `joborder-08338` are the
  same SO; `JOBORDER-083381` is a different one.
- **Divisions** — the 12 SPS manufacturing units: OPD (Offset Printing), SHPS (Screen Printing),
  PCU (Paper Cup Unit), PSU (Paper Straw Unit), RWU (Rewinding), CPU (Customized Packing,
  PACKSERV items), MOBA (Punching), FPP (Food Product Processing), DPU (Digital Printing), plus
  Paper Cup Lid, Cake Wrapper, Paper Plate.
- **Stages** — the 11-item File Checklist shared across divisions (Artwork image, Item photo, Job
  card, Sales order, Bundle, Pick list, Package, Shipment, Inventory adjustment, Sales invoice to
  SH, Purchase bill from SPS). 7 are Zoho-detected automatically, 4 need a human tap; divisions
  omit some (e.g. PSU has no Pick list).
- **Time Claiming Bill** — a green pre-numbered carbon book used only by PSU (date, product,
  minutes, employees, staff count, impressions, serial). Who fills it is still open — a
  production-dashboard question, not this project's.
- **Drops** (cross-project BI term, not portal-specific) — a distinct order occasion for a
  customer/item in the trailing 12 months, used to classify demand cadence. Relevant only if the
  future call-off order type (OP-15) is ever built.
- **Ex-stock vs customised order** — ex-stock is often produced before the file is created,
  processed qty = SO qty, artwork/plate "Not Applicable". Never average the two lead times.
- **`order_status` (plain-word)** — what the requester sees: `Submitted → Accepted → In production
  → Packed → Shipped → Invoiced → Completed`, or `Question for you / Rejected / Cancelled`. Always
  derived server-side (spec §6.4), never client-side.

---

## 10. Known traps (verified against real data — don't rediscover these)

- **~29% of key-customer order lines are logged with "Standard Holdings" as the customer**
  instead of the real end customer — the exact mis-tagging the portal is designed to fix at entry
  (`BRIEF.md:48`).
- **`SubTotal`/`Total` repeat the order total on every SO line** — never sum across lines; only
  `Item Total`/`Amount` is additive.
- **Only ~17–18% of SPS orders carry a usable SH SO reference** in `CF.SH Sales Order Ref`
  (1,398/8,286 independently recomputed); the rest are blank or placeholder strings ("To be
  Received", "For SH Stock", "BTN#"). This is the core problem OP-12 fixes.
- **Straw item codes** — whether "packed"/"imported"/"SPS" paper-straw variants are one product or
  three is still an open correction before publishing any volume figure built on them.
- **Weak PSU timestamps** — PSU's creator and receiver are the same person (Umanda), so there's no
  handover event; ex-stock is often produced before the file exists. Don't trust PSU dwell-time
  data without checking this.
- **Division values need alias mapping, never hard-coded** — an unmapped Zoho division value is
  stored raw and flagged in Admin, never silently skipped.
- **A blank status cell does not mean "not done."** The Sep-2026 job sheet has 47 blank cells in
  one register alone — check qty-done and hourly checkpoints before treating a blank as negative.
- **Capture-time discipline** — every import carries `captured_at`; an older capture never
  overwrites a newer one. Carry this into any new data source, don't build a simpler rule.

---

## 11. What NOT to build (Zoho already does this)

Low-stock alerts/reorder points, composite items/kit bundling, basic reports/pivots/KPI widgets/
workflow rules/webhooks — all native to Zoho Inventory. **Sales order creation itself** — the
portal never writes to Zoho; a browser helper fills Senuri's screen, she clicks Save. True
manufacturing work orders/MRP — Zoho's own docs say it isn't supported; the production dashboard's
job/stage tracking fills that gap, don't duplicate it inside the order portal too. Full citations
(with market-and-zoho.md URLs): `plans/40-order-portal-developer-brief.md` §16.

---

## 12. Where the step prompts and questions live

- Step-by-step build plan: `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/order-portal/02-process-steps.md`
- Per-role question pack: `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/order-portal/questions.md`
- One prompt file per step: `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/order-portal/prompts/OP-01-spec-delta-release-1-v2.md`
  through `OP-16-sh-triage-fulfilment.md`
- This project's finished-product spec: `../FINISHED-PRODUCT.md` (same directory as this file)
- Custom skills for this project's development: `./skills/` (drafted, not installed)

---

Abdul Hadhee | IT Exec | Standard-Holdings
