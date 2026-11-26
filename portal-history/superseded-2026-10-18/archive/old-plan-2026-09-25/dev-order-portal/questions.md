# Order portal — questions by person

**Changed 25 Sep 2026:** "Finance / credit" question 3 (where the credit limit lives) is now
**DECIDED** — Zoho Inventory, no Zoho Books access needed — and removed from the open list below;
Hazeem's section renumbered from 4 to 3 questions. The COO section's credit item is updated to
note only the block-vs-hold authority question remains open.

Prepared by Abdul Hadhee | IT Exec | Standard-Holdings, 25 Sep 2026.

Every question below is copied from `02-process-steps.md`, grouped by who answers it. "Unblocks"
names the step(s) it gates. "Mini-report" says whether this brief recommends a short standalone
write-up before the wider planning meeting, per `plans/40-order-portal-developer-brief.md` §18.
None of these are decided here — they are listed, not answered, per this run's rules.

---

## GM Samitha

| # | Question | Unblocks | Mini-report? |
|---|---|---|---|
| 1 | Is the multi-job-per-order shape actually needed for Release 1 go-live, or can it wait? Does any current order genuinely split into several jobs at once (e.g. one order spanning two divisions)? | OP-01 | No |
| 2 | Any objection to English-only for Release 1, or should Sinhala/Tamil be scoped in now? | OP-01, OP-14 | No |
| 3 | Confirm the manager/coordinator pairs for PCU, PCLU, DPU, PPU, CWU — currently unassigned. | OP-04 | No |
| 4 | Who is triage for SPS orders? (also see COO, below — same question, either can decide) | OP-04, go-live | No |
| 5 | Sign off the safety-stock / MTS buffer policy, or say it needs more numbers first (six candidate items: SH-8oz S/Wall Paper Cup 73.6% margin, Chefs Choice Cling Film 55.5%/52.5%, ST-Cling Film 37.5%, SP-Chicken Bucket+Lid 21.6%, Taco Bell's 5 standing items, Paper White Straw 68.0%). | OP-15 (turns it from wiring into a real, numbered feature step) | **Yes** — the safety-stock policy paper itself |
| 6 | Name a backup owner for the notification pipeline (or delegate to COO). | OP-09, go-live | No |

## COO

| # | Question | Unblocks | Mini-report? |
|---|---|---|---|
| 1 | Who is triage for SPS orders, and separately, who is triage for SH orders? | OP-04, go-live | No |
| 2 | Any objection to the block-vs-hold credit decision being made by Finance/Hazeem alone, or does it need COO sign-off given it can stop a customer's order? (The credit-limit *data source* is now DECIDED — Zoho Inventory, no Books — this question is the one remaining item that needs the COO.) | OP-08 | Covered by the credit mini-report (see Finance, below) |
| 3 | Confirm the paused stock-system project (Abdullah/Ilham) is ready to resume — a precondition for the call-off order type ever becoming real. | OP-15 | Same as GM Samitha's #5 |

## CEO

| # | Question | Unblocks | Mini-report? |
|---|---|---|---|
| 1 | Grant SH Zoho admin access covering all 10 locations (SH is the CEO's company) — today the sync login sees only Head Office. This is the single access item that unblocks the most downstream work: OP-07's location verification, OP-11's SH-side sync, and all of OP-16. | OP-07, OP-11 (SH side), OP-16 | **Yes** — state the access gap and what it blocks once, since it recurs across three parts of this project |

## PSU manager Ishan

_No questions in this project directly name Ishan — PSU-specific open items live in the production
dashboard project (`dashboard-state.md:6`), not the order portal. Flagged here only so the absence
is visible, not assumed away._

## Umanda

_No questions in this project directly name Umanda — she is listed as a coordinator (job creation,
SO linking, attachments, `plans/40...` §2) but no open question in this brief is addressed to her
specifically._

## Store keeper Ilham

_No questions in this project directly name Ilham for Release 1. Ilham's stores role (shipment
reference, dispatch qty) is fully specced for Release 1 (`plans/40...` §2) with no open item; his
open items (raw-material receipt into the RM warehouse, the paused stock system) belong to the
separately-scoped, paused stock-system project (`plans/40...` §11), not this one._

## Raw-material stock manager

_No such role is currently defined anywhere read for this brief (`dashboard-state.md:9`: "No
raw-material stock-manager role defined"). This project has no question for a role that doesn't
exist yet — flagging the gap itself, not asking a question of no one._

## Sales coordinators / Senuri

| # | Question | Unblocks | Mini-report? |
|---|---|---|---|
| 1 | Willing to triage SH-side orders in the new portal, as earlier food-packaging-ops notes suggested? If not, who should? | OP-04, OP-16 | No |
| 2 | When "Portal Order No" is made mandatory on the SH sales order, any case where a portal order number genuinely won't exist yet (a walk-in, a phone order predating the portal)? | OP-12 | No |
| 3 | Which of Zoho's dropdown values (Business Unit, Order Pick Type, Invoice Type, Delivery method) does Senuri actually use day to day, so the future helper page's field list can be trimmed to what's real? | OP-16 (helper page, not yet scheduled) | No |

## Triage owner (name not yet decided)

| # | Question | Unblocks | Mini-report? |
|---|---|---|---|
| 1 | Who is triage for SPS orders, and separately, who is triage for SH orders? (same question as GM Samitha / COO above — whoever is named answers, or names themselves) | OP-04, go-live | No |
| 2 | Is the WhatsApp order group switched off on day one, or run in parallel for a transition period — and if parallel, for how long? | OP-04, OP-09 (context only — no WhatsApp code is built regardless) | No |
| 3 | Who enters orders that still arrive by WhatsApp during the transition — triage itself via Enter on behalf, or someone else? | OP-04 | No |

## Finance / credit (Hazeem's function)

**DECIDED (user, 25 Sep 2026), no longer a question for Hazeem:** the credit limit is read
automatically from Zoho Inventory (`credit_limit` field on the Contact object, confirmed live in
our own SPS export) — no Zoho Books access, login or integration is needed. Full research:
`analysis/research/zoho-credit-limit.md`.

| # | Question | Unblocks | Mini-report? |
|---|---|---|---|
| 1 | Block the order outright over the credit limit, or hold it for a named person to release? | OP-08 phase 1 (entirely) | **Yes** |
| 2 | Do "pending dues" mean every unpaid invoice, or only the overdue ones? (The credit-limit research recommends all-unpaid as the default — Finance still confirms.) | OP-08 phase 2 (formula) | **Yes** — same memo |
| 3 | Who is Hazeem's backup, so the credit-review step has continuity? | OP-08, go-live | No |

## SH Rizwan / Abdullah

| # | Question | Unblocks | Mini-report? |
|---|---|---|---|
| 1 | Confirm the names and existence of the other 7 SH locations (only Head Office, South Branch, Central Branch are confirmed from live order data today). | OP-07 seed data | No |
| 2 | (Rizwan, as SH's side) support/coordinate on the SH Zoho admin access grant — see CEO, above, who holds final authority. | OP-07, OP-11, OP-16 | Covered by the CEO's access mini-report |

## Hazeem

_See "Finance / credit," above — same person, same three questions (down from four: the
credit-limit data-source question is DECIDED, 25 Sep 2026)._

## IT (the user)

| # | Question | Unblocks | Mini-report? |
|---|---|---|---|
| 1 | Provision an SMTP account for the portal to send from (who owns it, what "From" address; a paid service may need COO budget sign-off). | OP-09 email delivery | No |
| 2 | Confirm the SPS self-client's read-scope list is sufficient for the sync (sales orders, customers, items) — a five-minute check, since the user already holds SPS Zoho admin. | OP-11 | No |
| 3 | (Verification step, not a question to decide) Mark "Portal Order No" mandatory in Zoho SH SO settings, using existing SmartPack-side Zoho admin access. | OP-12 acceptance criterion 1 | No |

---

## Questions with no clean single owner (flagged, not assigned)

- **Resolved 25 Sep 2026, kept here for the record:** the credit-limit data-source conflict (22-Sep
  memory vs 24-Sep talk script — Zoho Books vs Zoho Inventory) was a conflict between two things
  the *user* said on two different dates, not something Hazeem could resolve alone. The user has
  now decided it directly: Zoho Inventory, no Books access needed
  (`analysis/research/zoho-credit-limit.md`). It no longer needs a meeting slot.
- The SH admin access grant (CEO, above) sits between the CEO (who owns SH) and Rizwan (who runs
  SH's food-packaging desk day to day) — listed under CEO because SH-org admin rights are the CEO's
  to grant, but Rizwan is the practical point of contact for arranging it.

## Files this list draws on

`02-process-steps.md` (this project — every question here is copied from a specific step's
"questions that must be answered first" section, not re-derived); `plans/40-order-portal-developer-brief.md`
§18 (the original per-role question pack this project's questions extend); `analysis/research/dashboard-state.md`.
