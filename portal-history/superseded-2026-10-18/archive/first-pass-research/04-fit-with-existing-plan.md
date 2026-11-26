# 04 - Fit of the "customized-items order portal" request with the existing order-portal plan

Prepared by Abdul Hadhee | IT Executive. 17 Oct 2026. Read-only reconciliation: no code, no decisions made here.
No number below comes from a script; every statement is a reading of a file, cited file:line.

Short names used for paths:
- PM = `/root/Project Management/reports/2026-09-25-sps-business-plan/projects/order-portal/PROJECT-MEMORY.md`
- FP = `.../projects/order-portal/FINISHED-PRODUCT.md`
- STEPS = `.../dev/order-portal/02-process-steps.md`
- RESEQ = `.../dev/order-portal/03-resequence-after-manager-first.md`
- Q = `.../dev/order-portal/questions.md`
- SCHED = `.../dev/01b-dated-schedule.md`
- MGR = `/root/Project Management/wiki/specs/2026-10-08-pd-managers-full-release.md`
- ROOT = `/root/CLAUDE.md`; PDC = `/root/Production Dashboard/CLAUDE.md`
- Dev repo = `/root/dev/production-dashboard` (read: `git log`, `server/db/migrations/`)

## 0. The new request in one line

SH sales staff order **customized (made-to-order) SPS items** through a portal. If the item is **already in stock**, the order goes to **Rizwan's team**. If **not**, it goes to the **production managers**.

## 1. What the new request is, against the old plan

```
EXISTING PLAN (PM, STEPS)                        NEW REQUEST
requester (SPS desk / SH Food Pkg / branches)    SH sales team only
  -> submit (all order types)                      -> submit (customized items only)
  -> credit check (OP-08)                          -> (not mentioned)
  -> TRIAGE person accepts/rejects/asks (OP-04)    -> automatic split: stock? 
  -> accept creates a job + picks division           yes -> Rizwan's team
  -> coordinator links SO, job no, docs              no  -> production managers
  -> managers track in dashboard                   
```

The single biggest difference is the routing step. In the old plan a **human triage person** decides (STEPS:238-262, FP:28-35). In the new request the **stock position decides**, and there is no triage person named.

## 2. KEEPS (the new request fits as written)

| Existing element | Why it still fits | Source |
|---|---|---|
| Portal lives **inside the production-dashboard repo/service**, not a new codebase | Nothing in the request asks for a separate service | PM:14-18; dev CLAUDE.md:3; ROOT:111 (Q10: PM2 `production-dashboard`, port 4300) |
| Requester sees plain-word status, never raw state; server-set submit time | Sales team needs to see where their order is | FP:17-27, STEPS:187-200 |
| Order gets a number at once (`OR-000123`) | Same need | FP:20-21, `001-schema.sql` `orders.order_no` |
| Managers (Mubeena, Ranga, Ishan) and coordinators (Nirmani, Umanda, Madushi) receive work per division via `division_pairs` | "Shared to the production managers" is exactly this | MGR:69-99 (D-B, D-C, D-M), PM:190-203 |
| Real end customer picked at entry, not "Standard Holdings" | The data you extracted shows 10,594 of 10,596 SPS SO lines carry SH as customer (lead's brief); the old plan already targets this mis-tagging | PM:244-246 (~29% mis-tag figure; "traps" list), FP:193 |
| Zoho is read-only; the portal never writes to Zoho | Applies unchanged | PM:112-115 (rule 9), MGR:76-77 (D-E) |
| Credit check from Zoho Inventory contact (`credit_limit`, no Books) | Binding decision, if a credit check is wanted | PM:158, STEPS:439-470, Q:164-166 |
| No WhatsApp sending; in-app plus email are the record | Applies unchanged to the routing notices | PM:108-111 (rule 8), FP:95-101 |
| SH and SPS never summed | Applies; this portal is an SH-to-SPS flow, so every screen must show one company's numbers | PM:98-100 (rule 5), FP:109-111 |
| Additive migrations only; dev clone only; human deploys with `shdeploy` | Applies | PM:88-94 |
| Job numbers opaque | Applies if a job number is shown | PM:101-103 |
| `customer_portal` flag stays false | The "customers" here are SH staff, not end customers | PM:154 (decision 20 Sep) |

## 3. CHANGES (the new request alters the old plan)

1. **Routing is automatic by stock, not by a triage person.** Old: Accept/Reject/Ask by a named triage owner (STEPS:238-262; owner unnamed, PM:168-169, Q:103, 111). New: stock check decides the destination. The triage owner question may disappear for this portal, or survive as an exception queue. Not decided here.
2. **A second destination exists that the old plan does not model.** The old plan has one downstream path (triage -> job -> managers). "Rizwan's team" gets no step in OP-01..OP-14. The nearest thing is OP-16 "SH-side triage and fulfilment (Saman's team checks, Pasindu's packaging slip)", which is **unscheduled and unscoped** (STEPS:908-960; SCHED OP-16 "NOT SCHEDULED").
3. **A stock check is new.** The old portal has no finished-goods stock check. Its only stock logic is the **raw-material** check for manufactured items (PDC:566-585, "need = order qty x recipe qty vs available_stock"). FP:195 even records finished-goods stock for key-customer items as 0 and "unaffected by Release 1". The new request needs finished-goods availability per item; the source of that number is not in the old plan.
4. **Scope narrows to customized items only.** Old order types: customised / ex_stock / internal (`001-schema.sql` `orders.order_type` CHECK; PM:234-235). The Zoho data uses four values (Customized Order / Ex Stock / Internal SH Order / MTO, from the lead's brief). New portal only needs the customized slice (plus an MTO decision, below).
5. **Requester population narrows** from "SPS order desk, SH Rizwan's Food Packaging team, branches" (FP:17) to "SH Sales Team". Also, the SH-location tagging work (OP-07, STEPS:383-438) is probably unnecessary, because SH is the only requester company.
6. **The request is item-driven.** The old form takes free-text `item_description` per line (`001-schema.sql` `order_lines`). The new portal needs a pick list of customized items built from the history (the data task of this folder). That is a change from free text to a catalogue.
7. **Sequencing.** The old plan puts OP-01 start at 22 Oct 2026 and go-live 25 Jan 2027, full release 15 Feb 2027 (SCHED:288, 301). A narrower portal could move earlier, but only if the dashboard track allows it (see section 7).

## 4. DROPS (candidates to leave out of the first customized-items release)

Each is a **candidate**, not a decision; the old plan scheduled them all as required for OP-14.

| Dropped or deferred | Old step | Why it may not be needed | Source |
|---|---|---|---|
| Triage workspace (Incoming/Questions/Enter on behalf) | OP-04 | stock decides routing; Enter-on-behalf exists only for WhatsApp stragglers | STEPS:238-262 |
| SH-location tagging with 10-location list | OP-07 | SH is the only requester; the 7 unconfirmed locations (PM:174-175) stop blocking | STEPS:383-438 |
| SH Zoho admin access dependency (CEO) | OP-07/OP-11/OP-16 gate | only if the stock check reads SPS stock; see conflict C4 | PM:176-177 |
| Portal Order No enforcement in SH Zoho | OP-12 | helps linking, but not needed for a first release | STEPS:703-757 |
| Call-off / buffer-stock order type | OP-15 | explicitly "do not build yet" | STEPS:861-905 |
| GM/COO redacted view and full hardening | OP-13 | still needed for security (do not drop security-auditor), but the redaction view is a later release (R5) | FP:61-65, PM:56-60 |

Not droppable: security rules (PM:104-108), append-only audit triggers, the plan-critic/test-first gates.

## 5. CONFLICTS between sources (listed, not resolved)

| # | Conflict | Side A | Side B |
|---|---|---|---|
| C1 | **Who creates the production job.** Old plan: triage Accept creates a job row in the same transaction (STEPS:238-262; FP:135-140 "an accepted portal order creates exactly one job"). Managers' release: jobs are derived from SPS Zoho SO **lines**; "The 001 `jobs` tables are not used" and "OP-05's assumption stays wrong". | STEPS / FP:135-140 | MGR:499; RESEQ:47-61 |
| C2 | **"Rizwan's team" means different things.** Request context: SH stock/stores team. Existing files: Rizwan runs the **SH Food Packaging desk**, which is a *requester* group, and Saman/Pasindu do SH picking and packing (FP:17, PM:202, PDC:17.2 steps 6-7). SPS stores is **Ilham** (PM:201). | request / lead brief | PM:202, PM:201, `stock-system-key-customers.md:11` ("Abdullah and Ilham ... Rizwan's department") |
| C3 | **Whose stock is "in stock"?** SPS manufactures; SH sells. Stock may be on the SPS side (Ilham's stores), the SH side (Rizwan's/Abdullah's), or both. SH and SPS must never be summed (PM:98-100), and the SH side is readable only through the browser session until SH API access is granted (ROOT:32). | | |
| C4 | **SH data access.** Old plan: SH Zoho admin access blocks OP-07/OP-11-SH/OP-16 and `ithelp@` sees 1 of 10 locations (PM:176-177, Q:119). ROOT:32: SH data via Playwright/CDP read-only for now; SH API requested after the dashboard is reliable **or straight away once the goods-gatepass proposal is shown**. | PM / Q | ROOT:32 |
| C5 | **Credit check target.** Old OP-08 reads the credit limit of "the logged-in customer's org" (STEPS:464-466). In SPS data the customer is nearly always SH, so the check on SPS's side would compare SH, not the end customer; whether the sales-team portal needs any credit check at all is unstated. | STEPS:464 | lead brief (10,594 / 10,596) |
| C6 | **Credit source in older text.** PDC:17.1 line "Credit limits ... live in Zoho Books" vs the decision "Zoho Inventory, no Books". The decision (25 Sep) is later and wins; PDC §17.1 was not updated. | PDC:17.1 | PM:158 |
| C7 | **Stale "frozen schema".** PM:46 and dev CLAUDE.md:23 say 001-004 only; the repo already has `005-line-jobs.sql` and `006-line-job-workflow.sql` (MANIFEST.json, `git log` top commits eb36056, aa4837b). PM:38-40 states HEAD `b0cd339`; actual HEAD is `aa4837b`. | PM | repo |
| C8 | **Release dates.** PM:59-60: R1 live 11 Feb 2027; R2 = PD-06, 4 Mar 2027. SCHED:301: full release 15 Feb 2027 (target 11 Feb); SCHED:147: PD-04D managers' list live 5 Nov. RESEQ:20: "OP-14 go-live 25 Jan 2027". Then the 8 Oct decision folded the managers' view into one release (ROOT:35). | PM | SCHED, RESEQ, ROOT |
| C9 | **Order type vocabulary.** DB CHECK: customised / ex_stock / internal (3). Zoho "CF.Order Type": 4 values including MTO (lead brief). OP-02 plans to make it a lookup table (STEPS:82, 863-869), which would remove the mismatch, but that step is unbuilt. | `001-schema.sql` | lead brief |
| C10 | **Where the SPS sales order comes from.** The portal never writes to Zoho (PM:112-115). The old plan has the **SH** SO made by Senuri with a browser helper (PDC:17.2 step 4). I did not find, in the files read for this note, who creates the SPS `JOBORDER-` SO for a custom item, or when. A portal order that "goes to managers" needs that SO before the dashboard can see a job (MGR:499). | | |
| C11 | **Migration numbers.** Decided: 005 preview, 006 full release, 007 PD-03D MFA, 008+ portal (MGR section 8.1, ROOT:114, RESEQ:42-45). 005 and 006 now exist in the repo; **007 (MFA) has no file yet**. A portal migration at 008 would leave a gap, and the contiguity lint runs in `npm test` (MGR:522-545). | decision | repo state |
| C12 | **Zoho API budget.** SPS limit 7,500 calls/day (ROOT section 2, "Zoho API budget" bullet); the dashboard sync polls every minute 24 h/day (MGR:81-82 D-G, diagram 0a). A live stock check from the portal would add calls. SH limit unknown. | | |
| C13 | **Separate service vs module.** The portal is a module of the production dashboard (PM:14-18). The inventory system is a separate service on a different port (ROOT:30, Q8). A stock check that reuses the inventory decision panel would cross that boundary. | PM | ROOT:30 |

## 6. DECISIONS ALREADY MADE that still bind

1. **Zoho strictly read-only**, SPS Self Client for the sync; the portal writes nothing to Zoho (PM:112-115; MGR:76-77, D-E; ROOT:32).
2. **Credit limit from Zoho Inventory** `GET /contacts/{id}`, `credit_limit` and receivable fields; no Books (PM:158; STEPS:456-466). The two open sub-questions (block vs hold; all unpaid vs overdue) remain open (PM:163-167).
3. **No WhatsApp-sending capability, ever** (PM:108-111; `memory/hub-whatsapp-notifications.md`). Notice channel = in-app plus email; email needs an SMTP account not yet provisioned (PM:180).
4. **Migration claims:** 005 preview, 006 managers' full release, 007 PD-03D MFA, 008+ portal (MGR 8.1; ROOT:114). New portal migrations start at 008 (or whatever the next number is once 007 lands); the numbering lint will catch duplicates at startup and gaps in `npm test`.
5. **Portal = module of the production-dashboard app**, one repo, PM2 `production-dashboard`, port 4300, shdeploy service (PM:14-18; ROOT:111). Inventory = separate service, port 4400 (ROOT:30).
6. **Order of work, SPS side first, SH side later** (PM:155; PDC:17.2 end). SH sales team as requesters is an SH-side population, so this ordering needs a restatement by the user.
7. **SH and SPS never summed; SH data via browser session read-only until SH API access** (PM:98-100; ROOT:32). Build any SH stock reader **swappable (snapshot now, API later)** (ROOT:32).
8. **One release for managers (view + coordinator logins + ticks + Send next)**, Send next by manager or coordinator, coordinators see their manager's divisions (ROOT:35; MGR:69-99).
9. **Pipeline gates:** spec -> plan-critic -> tests first -> build -> code-reviewer; security-auditor for new routes/uploads; db-migration-guard for schema; the human deploys (global CLAUDE.md sections 2-4).
10. **Customer portal hidden, default false** (PM:154).
11. **Never mention the COO-analyst role; sign "Prepared by Abdul Hadhee | IT Executive"** (ROOT header; PM:114-116 has the older signature, superseded 3 Oct).

## 7. PEOPLE AND ROLES

| Person | In the old plan | In the new request | Open |
|---|---|---|---|
| SH sales team | partly "requesters" (FP:17) | the requesters | names and count not in the files read |
| Rizwan and his team | SH Food Packaging desk head; practical SH access contact (PM:202, Q:180) | receives in-stock orders | is "Rizwan's team" the stock holder, the picking team (Saman/Pasindu), or both? See C2 |
| Abdullah | SH key-customer stock; Kohalwila reorder pilot (PM:202; ROOT:27-30 (reorder pilot rows)) | may hold the SH stock numbers | not named in the request |
| Ilham | SPS store keeper (PM:201) | SPS-side stock | whether the SPS stock position counts as "in stock" |
| Mubeena, Ranga, Ishan | managers (PM:190-203) | receive out-of-stock orders | division mapping per item: the data study `reports/2026-10-08-pd-zoho-study/` holds item routes (`ROUTES-BY-UNIT.md`) |
| Nirmani, Umanda, Madushi (and Nimesha per PM:199) | coordinators | tick and Send next | PM lists Nimesha, MGR lists Madushi, Nirmani, Umanda; membership differs between sources (PM:199 vs MGR:99) |
| Senuri | SH SO creation; candidate SH triage (PM:198) | likely not in the loop | whether the sales team still needs her to create the SH SO |
| Hazeem | credit and billing reviewer (PM:197) | only if a credit check is wanted | |
| Samitha (SPS GM) | sponsor (PM:31, 194) | sponsor of the managers' side only | the request comes from the user; sponsor for the SH-facing flow not stated |
| User (admin) | config, imports, SPS Zoho admin (PM:203) | same | |

Note: ROOT:32 records the user is Zoho admin for SPS only; any SH-side admin action goes through the CEO.

## 8. SMALLEST FIRST RELEASE I would suggest

Aim: replace the WhatsApp ask with one form, and show each order its destination, using only what is already decided. **No Zoho writes, no new service, no new dependency.**

```
SH sales user -> picks customized item from a catalogue (built from the order history)
              -> enters quantity, required date, end customer (free text list from history), notes
              -> submit (server time, OR- number)
                    |
                    v
         stock position of the item (read-only snapshot)
              |                         |
        enough on hand            not enough / unknown
              v                         v
     "Rizwan's team" queue      "Managers" queue = division from the item's home unit
     (in-app + email)           (in-app + email; managers' dashboard shows the job
                                 after the SPS SO exists in Zoho)
```

Smallest cut, in order:
1. **Catalogue + order form + status page** (OP-03 core, minus triage, minus credit, minus attachments, minus company/location). Customer list from history. One migration at the next free number after 007.
2. **Routing by a stock snapshot**, shown to a human as a **suggestion with an override**, not a blind automatic send. Reason: C3 and C4 (stock side and access unresolved) and the "decide by hand" principle already used in the reorder screen (ROOT:27, GREY = decide by hand). Unknown stock goes to the managers' queue by default.
3. **Two queues with in-app plus email notice** (OP-09 reduced). SMTP account still needed (PM:180).
4. **Hand-over of the manager side stays inside the managers' dashboard release**: the portal order records the destination unit; the job appears there once the SPS SO exists. I would not recreate a second job table (C1).

Left for later: credit check (OP-08, needs Hazeem's two answers), attachments/artwork (OP-10), Portal Order No (OP-12), SH-location tagging (OP-07), GM/COO view, call-off type.

## 9. What must be asked before a spec (not decided here)

1. Is "Rizwan's team" the SH stock holder, the SH picking team, or the SH Food Packaging desk? (C2)
2. Is "in stock" measured on SPS finished-goods stock, SH stock, or either? Which warehouse(s)? (C3) What quantity rule: on hand >= ordered, or available after open orders?
3. Who creates the SPS `JOBORDER-` sales order for a custom item today, and does that stay manual? (C10)
4. Are MTO items (42 lines in the history) inside "customized"? (C9)
5. Is a credit check wanted on this portal, and against whom? (C5)
6. Who names the exception owner if the stock status is unknown or the item has no home unit? (old triage question, PM:168-169)
7. Does the first release need to wait for the managers' dashboard (migrations 005-006 are in the dev repo but not deployed per ROOT:111-112), or can it ship in the same deploy train? (C7, C8, C11)
8. Which of the old plan's four requester companies/teams use the new portal, and does the WhatsApp group stay on in parallel? (Q:158-160)

## 10. What I could not determine

- Who the "SH Sales Team" members are and how many order customized items per month; no file read here lists them.
- Whether any SPS finished-goods stock exists for customized items: FP:195 says 0 for key-customer items on 19 Sep 2026, which would send nearly everything to the managers; the lead's data task should test this per item before the "in stock" path is built.
- Whether the repo's uncommitted changes (Sign in with Zoho work; `git status` shows modified auth files and `docs/zoho-self-client-setup.md`) affect portal planning; I did not read them.
- I did not open the OP prompts (`prompts/OP-01..16`) beyond their names; a skim was not needed for this reconciliation, so any detail only in them is unchecked.
