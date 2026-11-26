# Build order: first to last (20 Sep 2026, Rev 3)

**Rule used:** a build comes before everything that needs its code or data. Ties go to the build that is **not blocked today**. No company is preferred.
**Build under a block:** build what sits under an unanswered question, and put a safe **stub** at the blocked edge (a manual step, an editable list, an advisory-only view). A stub must never write data that has to be un-counted later.

Rev 1: **plan-critic BLOCK**. Rev 2: **plan-critic PASS (approve with changes)**. Rev 3 applies those changes (§5).

> **21 Sep update:** §8 supersedes rows 1a, 2, 2b and 1b below. The foundation deploys now, privately; the schema stays frozen and later changes are additive; MFA, S1 and X2 come before going public.

## 1. Main line (in order)

| # | Build | Needs first | Blocks the build | Blocks only go-live | Start |
|---|---|---|---|---|---|
| 1a | **Finish Release 0 (tasks 16–18)**: header-pull snippet, admin web app + E2E, runbook + dependency audit; L23 security follow-ups. **Build and test only: no deploy, no release tag, no live-install commands.** The runbook is marked "do not run until 1b"; spec §14.1 live-install steps (protected-paths entry, install, shdeploy registry, cron, backfill) move to 1b | — | — | — | **now** |
| 2 | **Spec delta "Release 1 v2" + plan-critic**, covering: <br>• one portal for both companies (company + SH location); <br>• the credit step with the exact 20 Sep enums; <br>• "On Hold – Credit Review" visibility; <br>• `customer_portal=false`; <br>• **several child jobs per order**; <br>• notifications (**decision for you**: see §6); <br>• **enum CHECKs that will grow** (order, credit and event kinds) replaced by lookup tables, so new values are an INSERT later; <br>• a written rule: after 1b, every spec delta is additive (new tables, never new stage ids or enum values); <br>• "Cancel" and "Change order" reconciled with "updates are not edits"; <br>• customer and item pickers backed by imported master data; <br>• the Q10 roles mapped onto the spec roles; <br>• MFA. <br>**The schema changes go into `001` before any production database exists** (db-migration-guard) | 1a | your OK on the Q10 list (MFA, staging, secrets store); approval of new dependencies (email sender, TOTP) | — | after 1a |
| 2b | **Build the schema delta + MFA** (test first): the `001` edit, the updated schema tests, MFA behind a flag, and the db-migration-guard items D1–D14 (LATER L31); code-reviewer + security-auditor + db-migration-guard | 2 | — | — | after 2 |
| 1b | **First deploy of the foundation** (the first release tag is cut here, on the edited `001`): <br>• off-VPS backups (L17); <br>• firewall on port 4300 (X2); <br>• the readXlsx hang fix (L26); <br>• a staging environment (if confirmed); <br>• EasyPanel 2FA (X4); <br>• security audit S1 (proxy trust by a shared header), S2 and L23/L24 (LATER L32); <br>• the spec §14.1 live-install steps | 2b | — | your deploy (`shdeploy`) | after 2b |
| 3 | **Zoho read-only sync, SPS** (Release 1b addendum, with its own call budget), plus the **master-data import** (items, customers). Sync tables built before 1b go into the `001` edit and ship with 1b; built after, they get an additive migration and their own deploy | 1a | admin action: an SPS self-client (you're admin) | — | now (addendum), build after 1a |
| 4 | **Release 1 v2 = portal + credit step + notifications + SPS triage/jobs/coordinators**, built, audited and launched **as one unit** (the ACs span both halves: spec §6.4, AC 1.4/1.7/1.8) | 2, 1b; master data (3) | — (stub: SPS customer picker from the distinct `cf_order_received_from` values; SH items from the 19 Sep snapshot; customers as free text flagged "unverified" until SH contacts are mirrored, which needs SH access) | who does triage and whether the WhatsApp group is switched off (spec-Q7/Q8); SMTP; Finance names Hazeem's backup; L24 | after 1b |
| 5 | **Managers (Release 2)** | 4 | — | day plans (spec-Q4; optional by default) | after 4 |
| 6 | **Stores + Invoicing (Release 3):** Ilham, Darshani | 5 | — | who approves the rows (spec-Q2) | after 5 |
| 7 | **GM / COO / Analyst (Release 4)** | 6; 28 days of live data for the COO weekly view | — | — | after 6 |

## 2. Floating builds (start as soon as their own inputs exist)

| Build | Needs first | Blocked by | Safe stub |
|---|---|---|---|
| **SH fulfilment** (Senuri's helper page, SO link, "Saman or his team checks and packs", "Pasindu attaches the slip", shipment/invoice detected) | 4, **its own spec delta**, an SH data feed | SH admin (sync, and the custom field A1 needs admin too); OQ-9 ship-from list | **Decided 20 Sep:** Senuri **pastes the SH SO number** on the portal order (way B, a pending link checked against the mirror) **until SH admin access arrives**. Then way A: the "Portal Order No" custom field is read by the sync, the paste step is removed, and old pastes stay as a fallback. Guessing by customer + date + lines (way C) is rejected; picklist = a manual tick (the list API has no SO number, L5); built against the 19 Sep snapshot |
| **Zoho sync, SH** | 3 | SH admin; its own budget (SH volume is several times SPS's) | interim browser import |
| **Raw-material check** (recipe × qty vs stock) | 5 (blockers are shown there); a recipe mirror table; 3 | OQ-8 (who owns a shortage); **paused stock OQ-13** (which warehouse is the truth) | **advisory only**: shortages shown, **no blocker rows opened** until OQ-8 and OQ-13 are answered; stock = the **sum of all SPS warehouses**, labelled on screen (raw material is received into WIP today) |
| **Credit data from Zoho Books** | 3 (OAuth code), 4 | Books access (Hazeem requesting) | Hazeem decides by hand (already the rule) |
| **Userscript helper** | 4 (the portal); SH fulfilment only for its fallback helper page | your approval of the spec; selectors (Zoho sign-in); A1, A2; a security review of portal sign-in from zoho.com | the helper page |
| **Floor stations (Release 5)** | 5 | build: none (Employee Master stubbed); go-live: L18 token + L2 EPF numbers | Employee Master stubbed |
| **Employee Master read-only token (L18)** | — (separate project) | — | — |
| **Stock system** (Abdullah, Ilham) | 4 (requisitions become portal orders), the SH stock mirror (SH admin), the recipe mirror | **PAUSED by you**; OQ-12–16; Abdullah's workbook | none; not started |
| **Command Centre, live** (4 seats including CEO and SH GM) | 7 + SH fulfilment; its own spec (Release 4 covers SPS only) | OQ-19 (cosmetic) | demo defaults |
| **PWA app / WhatsApp alert / ClickUp** | 4 / 4 + X1 (WAHA, paused) / a decision | — | — |

## 3. Other projects on the VPS (not in this chain)

- X1: WAHA weekly report (paused).
- X3: Hub HR board.
- Sticker engine Phase 2 (waits on QZ1, QZ2, QG).
- IT Utilities manager requirements (paused).

None of them has a dependency edge into this chain, so they can run any time.

## 4. Why SPS's chain comes first here (technical, not preference)

- **SPS jobs don't need an SH parent.** The approved design lets a job exist without a portal order (`jobs.order_id` is nullable, spec §7.2.3 "New file", CLAUDE.md §5.1). An SH-originated job hangs off the **portal order** (step 4), not off SH fulfilment.
- **Reality is often child-first.** 676 SPS orders sit at "SH Sales Order Ref: to be received".
- **SPS is unblocked and fully specced; SH isn't yet.** SPS's chain has passed plan-critic and has live data access. SH fulfilment needs SH admin and its own spec.

So "SPS first" (spec D4) is also the dependency order: there is **no rule conflict to decide**. SH fulfilment starts the moment SH admin rights arrive.

## 5. What changed

**Rev 3 (Rev 2 review):**
- M-1/M-2: 1a has no deploy and no tag.
- M-3: new row 2b.
- M-4: growing enums become lookup tables, and the additive rule after 1b.
- M-5: master data owned by step 3, with the step 4 stubs named.
- m-1: notifications are a decision for you.
- m-2: L23, L24 and X4 added.
- m-3: the stock figure is named.
- m-4: userscript edge fixed.
- m-5: sync deploy gate.

**Rev 2 (Rev 1 review):**

- **B1:** removed the false "SH before SPS" edge; SH fulfilment now floats.
- **B2:** split into 1a (build) and 1b (deploy after the spec delta), so the schema isn't frozen before the credit statuses and child jobs are designed.
- **Major findings:**
  - M1: Q10 and dependency approvals are now blockers of step 2.
  - M2: more scope for step 2, plus own spec deltas for SH fulfilment and the raw-material check.
  - M3: SH sync is its own step with its own budget.
  - M4: an SO-number paste replaces the weak match.
  - M5: raw-material check comes after managers and is advisory-only.
  - M6: portal and triage ship as one release.
  - M7: go-live prerequisites are added to 1b.
  - M8: other projects are listed.
- **Minor:** the edges were fixed and the question numbers prefixed (spec-Q = design spec §17; OQ = the open-questions README).

## 6. Decision for you: one outbox or two?

Your answer said "one outbox table, one sender" for notifications. The approved spec already has an `outbox` table: a **held queue of future Zoho write-backs** that is never sent (D15, "Zoho is never written to"). If notifications share it, a single mistake in the sender could one day dispatch a Zoho write.

**Recommended:** a separate `notifications` table with its own sender. That is still one table and one sender for all notifications, and the Zoho queue stays frozen.

## 7. Admin actions that unblock the most

1. OK the Q10 security list and the new dependencies (email, MFA) → step 2.
2. SPS self-client (read scopes) → step 3.
3. SH admin rights → SH sync, SH fulfilment, custom field A1, the stock system later.
4. SMTP account → step 4 go-live.
5. Zoho Books read-only access → the credit data.

## 8. Decisions of 21 Sep 2026

- **First deploy is PRIVATE:** the service runs on the VPS and admins reach it through an SSH tunnel. There's no Traefik router yet, so S1 (proxy trust), X2 and MFA move off the critical path to "before going public".
- **Credit check is automatic at order placement** (limit vs pending dues + this order), from Zoho Inventory data; see spec §17.2 step 3. The manual reviewer enum of 20 Sep may shrink; step 2 re-scopes it.
- **Schema after the first deploy: additive only (default).** The user didn't choose between additive and a one-time rebuild; additive is the safe default, because no live data is ever wiped. `001`–`003` are frozen from now on (manifest + test, D3), and new tables carry the credit and child-job changes.
- **The test fixture keeps its real data;** the GitHub repo must be **private**.
- **Scope (23 Sep):** SmartPack is the mandated project. Everything SH-side (SH fulfilment, SH sync, the stock system for Abdullah) is built at Rizwan's request and only with his agreement. This matches the order above: the SPS chain first, SH items floating.

