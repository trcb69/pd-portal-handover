# Evidence A — what the production dashboard project already defines (28 Sep 2026)

Condensed from a read-only review. Sources: `CLAUDE.md` = `/root/Production Dashboard/CLAUDE.md`; `spec` = `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` (Rev 7.3); `PM`/`FP` = `/root/Project Management/reports/2026-09-25-sps-business-plan/projects/production-dashboard/{PROJECT-MEMORY,FINISHED-PRODUCT}.md`.

## Roles (spec §5, 144-208; screens §7, 403-693)
- **requester**: sees only their own and their team's orders; plain status Submitted→Accepted→In production→Packed→Shipped→Invoiced→Completed; never job internals, prices or other teams (spec:150,166,498,503).
- **triage** (person not yet named, Q7): incoming queue; accept / reject / ask / enter orders on someone's behalf (spec:507-521).
- **coordinator** (Nimesha, Madushi, Nirmani, Umanda): own files, link SO, attach documents, close (spec:152,525-550).
- **manager** (Mubeena, Ranga, Ishan): one "Today" screen across every division they manage. It has 9 counters: blocked, past due, due in 3 days, incoming, in production, ready to hand off, produced not shipped, waiting on stores, cancel requested (spec:153,569-596).
- **stores** (Ilham) and **invoicing** (Darshani): own tabs, plus a read-only search across all open jobs (spec:154-155,597-616).
- **approver_stores / approver_invoicing** (not yet named, Q2); **gm** (Samitha): everything, redacted; **coo**; **analyst**: full read plus export; **admin**: IT.
- **floor worker** (Release 5): enters their EPF number and sees only their own division's jobs (spec:178-197,664-692).

## Missed-step detection already specified
- An 11-stage checklist per job. Seven stages are detected automatically from Zoho documents: SO, bundle, pick list, package, shipment, invoice. Four need a human tap: artwork, item photo, job card, inventory adjustment / purchase bill (CLAUDE.md:129-156, spec §6.5).
- Freshness caveat and `force_done` override; manual ticks need a note to untick (spec:714-732).
- Blockers use fixed reason codes (CLAUDE.md:249-250). Server-side flags: overdue, at-risk, produced-not-shipped, short/over delivery. These are gated by data freshness and show "shipped: unknown" instead of a false flag (spec:364-372).
- Divergence report: where Zoho's status and the dashboard disagree (CLAUDE.md §14, spec:659).
- Notifications: the next actor is told, in-app and by email; WhatsApp alerts are optional and never the record (FP §3).

## Zoho data flow
Read-only. The outbox is permanently "held" (CLAUDE.md:26, PM:162-164). Imports today are CSV/UI exports plus a daily header pull; a live GET-only sync is Release 1b (not built). The only "write" idea is the **Zoho helper userscript**. It prefills Zoho's New Sales Order form in the user's own browser, and the user clicks Save. Status: DRAFT, not approved, nothing built (`zoho-helper-userscript-spec.md:3,18-26`; `BUILD-ORDER-2026-09-20.md:32`).

## Status and dates (PM §2, 109-127)
- Release 0 is built and tested (143 tests), but not deployed or pushed.
- PSU live 8 Dec 2026. Screen Printing 21 Dec. GM tile 22 Dec (the December demo).
- Order portal 15 Feb 2027. Inventory (separate project) 5 Jan 2027.
- Still open: triage owner, approvers, the credit-breach rule, day plans, floor tablets, and the ClickUp cut-over.

## Gaps against "each person sees only their part"
1. **Per-division containment is not built.** All 14 divisions are seeded, and `floor_live` only gates floor tablets. "PSU first" is a rollout choice, not a restriction (PM:88-98).
2. Stores and invoicing can search all open jobs (spec:154-155,599).
3. All five sections of the reference sheet are visible to every desk role, by deliberate choice (spec:447).
4. GM and COO see everything, redacted, rather than a department slice. The analyst has full read. Admin sees everything.
