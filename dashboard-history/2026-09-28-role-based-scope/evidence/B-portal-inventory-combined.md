# B — Order portal + Inventory + Combined design: what's already defined

Pulled 28 Sep 2026 for the role-based-scope work. Every point below cites the source file and
section/line. Read-only extraction — no new decisions made here.

---

## 1. Roles / user groups per system — what they see, what they do, their screens

### 1A. Order portal (= production-dashboard Release 1)

Source: `.../projects/order-portal/PROJECT-MEMORY.md` §8 (people table), `.../projects/order-portal/FINISHED-PRODUCT.md` §1 ("A day in the life, by role") and §2 ("Screens").

| Role (exact name used) | Sees / does | Screens (FINISHED-PRODUCT §2) |
|---|---|---|
| **Requester** (SPS order desk, SH Rizwan's Food Packaging team, branches) | Places orders (customer/company/location pickers, item lines, attachments, required date); sees own/team orders with plain-word status (`Submitted → Accepted → In production → Packed → Shipped → Invoiced → Completed` / `Question for you` / `Rejected` / `Cancelled`); messages the order thread; raises cancel requests. **No job internals, no prices, no worker names** (FINISHED-PRODUCT §1, citing spec §5.1, AC1.2) | New order; My orders / Team orders; Order thread |
| **Triage** (SPS side unnamed; SH candidate Senuri) | Three tabs — Incoming, Questions, Enter on behalf; Accept (picks division + manager/coordinator pair, creates job in same transaction), Reject (reason code + required public note), Ask (public question) | Triage workspace |
| **Coordinator** (Nimesha, Madushi, Nirmani, Umanda) | Sets job number (opaque, never validated); links/unlinks Zoho SO (sweep auto-resolves); attaches production docs; sends to production; posts internal notes (never visible to requester or GM/COO) | Coordinator workspace |
| **Manager** (Mubeena, Ranga, Ishan) | Sees jobs assigned to them across every division they run (Ishan: four divisions, one dashboard) — this is Release 2's own workspace, fed by the portal | (Release 2, not built by this project) |
| **Credit & Billing Reviewer** (Hazeem's function) | Once OP-08 ships: sees "On Hold – Credit Review" orders where `pending dues + order value > credit limit`; releases or rejects. **Visible only to Senuri (placer), CEO, COO, both GMs** — "nobody else, not even other triage staff" | Credit review |
| **Stores** (Ilham, SPS) / **Invoicing** (Darshani) | Fill shipment reference / ITN reference — the two closing-checklist stages; their input flips the requester's status live (Release 3 own workspace) | (Release 3, not built by this project) |
| **GM (Samitha) / COO** | Read everything, **redacted**: worker identity → "operator," no `payload_json`, minutes only as division×process×week aggregates (≥2 workers) or "—"; public messages only, never internal notes/attachments; **never SPS+SH summed** | GM/COO view |
| **Admin** (the user) | Configures divisions, manager/coordinator pairs, reason codes, order-type aliases, calendar/holidays; manages users/roles; runs/monitors Zoho imports/sync; reads audit log; sees "unverified" flag on the 7 unconfirmed SH locations | Admin |

Sponsor: Mr. Samitha, SmartPack GM — "the requested build, not the user's initiative" (`PROJECT-MEMORY.md` §1).

### 1B. Inventory / stock system (pre-28-Sep two-login decision)

Source: `.../projects/inventory/FINISHED-PRODUCT.md` §1 ("Capabilities by role") and §2 ("Screens"); `.../projects/inventory/PROJECT-MEMORY.md` §1, §8; `INVENTORY-DECISION-SYSTEM-PLAN.md` §5.

| Role (exact name used) | Sees / does | Screen / route |
|---|---|---|
| **Store keeper (Ilham)** — daily | `GET /store-keeper/today` (INV-09): Receive/log today; Below reorder point (ATP<ROP, `flags` table); Due a physical count. Read-only, never edits Zoho | `/store-keeper/today` |
| **Raw-material stock manager** (role proposed, not yet filled) — weekly | `GET /rm-manager/weekly` (INV-10): Days-of-cover per material worst-first; Rising-item watch list (≥30% 3-month growth); Open-PO follow-up vs 5d/10d benchmark; Requisition queue. Confirms real breaches, raises requisitions (never a Zoho PO directly) | `/rm-manager/weekly` |
| **Production managers** — weekly, per division | `GET /production-manager/weekly` (INV-11), filtered to own division via dashboard's `division_pairs` — shortage-vs-plan view | `/production-manager/weekly` |
| **GM (Samitha)** — weekly | `GET /gm/weekly-summary` (INV-12): breach count, shortage count, top 2-3 LKR-value risks, accuracy roll-up; **plus a policy-review digest** (checkbox approve/reject of `pending_approval` rules) per `INVENTORY-DECISION-SYSTEM-PLAN.md` §5.4. Signs off phase transitions | `/gm/weekly-summary` |
| **SH key-customer buffer (Abdullah)** — phase 3+ only | Buffer-breach alerts routed Abdullah → Rizwan → Nazmi → COO — the existing SH purchasing chain | (phase 3+) |
| **Requisition/rule approval** (RM manager + GM/COO above threshold) | The two "act on this" moments in the system: confirm a flagged breach (→ requisition, human raises the real Zoho PO) and approve a proposed policy (`INVENTORY-DECISION-SYSTEM-PLAN.md` §5.6) | Requisition queue (part of RM manager screen); GM digest |

No screen writes to Zoho except the opt-in ROP write-back (INV-14, gated on Q9=yes) — `FINISHED-PRODUCT.md` §2.

### 1C. New 28-Sep two-login decision (supersedes/refines 1B above)

Source: `work/DECISIONS.md` line "28 Sep 2026 ... System roles (user)"; `SYSTEM-REQUIREMENTS-FROM-DATA.md` "Who uses the system" table.

| Login (exact name) | Sees | Does not see |
|---|---|---|
| **Storekeeper (SPS)** | Raw materials only | Everything else |
| **Operations–Packaging (SH)** | Every non-chemical item SH buys (from SPS or outside suppliers) and sells, plus the raw materials SH sells on to SPS | Chemicals |
| **SD (Specialities Division = chemicals)** | Outside both logins — not part of this system | — |

`SYSTEM-REQUIREMENTS-FROM-DATA.md` "Who uses the system" flags an **unresolved mapping gap** (its own item [B1], restated in §6 item 11): the GM, production-manager and RM-manager roles (INV-10/11/12, i.e. the roles in table 1B) map to **neither** Storekeeper-SPS nor Operations–Packaging-SH as the 28-Sep decision defines them — "this document does not decide that either." It also states the two-login decision "does not change" the earlier 25-Sep build-order rule (SH inventory/login builds only after SPS phase 1 signs off) "unless the user says so."

### 1D. Production dashboard (for context on the handoff chain, not this task's primary scope)

Cited from `COMBINED-SYSTEM.md` and order-portal docs where it appears as the receiving system for a job: Manager (Mubeena, Ranga, Ishan), GM/COO redacted view — see 1A above; production dashboard itself is the codebase order portal (Release 1) lives inside.

---

## 2. Where the three systems hand work to each other (order → job → stock → dispatch → invoice)

Source: `COMBINED-SYSTEM.md` §1.1 (mermaid diagram) and §1.2 (numbered integration table); `INVENTORY-DECISION-SYSTEM-PLAN.md` §7.

- **Order → job**: "An accepted portal order creates exactly one job (`orders.id` FK, partial-unique so an order can never produce two jobs)" — `order-portal/FINISHED-PRODUCT.md` §5; same fact, `COMBINED-SYSTEM.md` §1.2 row 1 (`ux_jobs_order` unique index, `server/db/migrations/001-schema.sql:155`).
- **Job → stock (WIP netting)**: dashboard's `jobs`, `job_so_links`, `zoho_bundles` are read read-only by the inventory system to net WIP against ATP — `COMBINED-SYSTEM.md` §1.2 row 4; `inventory/FINISHED-PRODUCT.md` §5; `INVENTORY-DECISION-SYSTEM-PLAN.md` §7 table row 1.
- **Stock → job (blocker)**: inventory's buffer/ATP breach data feeds the dashboard's advisory raw-material blocker, "replacing a single live Zoho-stock snapshot" — `COMBINED-SYSTEM.md` §1.2 row 6; `INVENTORY-DECISION-SYSTEM-PLAN.md` §7 table row 2. Explicitly "linked, not merged... this app only links to it, never owns its logic" (`production-dashboard/FINISHED-PRODUCT.md` §5, quoted in both).
- **Stock → purchasing (people, not a system)**: rising-item RM alerts / shortage-vs-plan alerts go to the raw-material stock manager as a notification (in-app+email; WhatsApp urgent-only) — `COMBINED-SYSTEM.md` §1.2 row 7; a human, not Zoho, then raises the PO — "the system flags, never buys" (`inventory/PROJECT-MEMORY.md` §5 rule 6, `INVENTORY-DECISION-SYSTEM-PLAN.md` §6).
- **Dispatch**: Stores (Ilham, SPS) fills the shipment reference on the order/job — this flips the requester's status to "Shipped" (`order-portal/FINISHED-PRODUCT.md` §1 "Stores/Invoicing").
- **Invoice**: Invoicing (Darshani) fills the ITN reference — flips status to "Invoiced" (`order-portal/FINISHED-PRODUCT.md` §1 same section). Order status sequence in full: `Submitted → Accepted → In production → Packed → Shipped → Invoiced → Completed` (`order-portal/FINISHED-PRODUCT.md` §1 "Requester").
- **Future call-off / buffer draw-down**: "a future call-off order type draws down an inventory-system buffer once wired" — wiring only in Release 1, `order_type` stays an extensible lookup table, no draw-down logic until the buffer policy is signed off and the paused stock project resumes (OP-15, COO's call) — `COMBINED-SYSTEM.md` §1.2 row 8; `INVENTORY-DECISION-SYSTEM-PLAN.md` §7 table row 4; `SYSTEM-REQUIREMENTS-FROM-DATA.md` "Who uses the system" (round-5 finding 3: this is "no longer the same buffer R3–R5 would populate" — R3/R5 are now parked SH-phase notes, R4b is the customer-side successor).
- **To Power BI (both dashboard+inventory)**: scheduled export only, not a live feed — no first-party Zoho→Power BI connector exists — `COMBINED-SYSTEM.md` §1.1 (diagram note), §1.2 row 9, §3.2.

---

## 3. What each system reads from Zoho / writes back

### Order portal
- **Read-only mirror only. Never writes to Zoho.** `outbox` stays `held` forever by design (spec D15) — `order-portal/PROJECT-MEMORY.md` §4 rule 9; `order-portal/FINISHED-PRODUCT.md` §5.
- Reads: SPS-side scheduled sync of SOs, bundles, packages, shipments, invoices, items, composite items (`FINISHED-PRODUCT.md` §5, `COMBINED-SYSTEM.md` §1.2 row 2); credit limit from Zoho Inventory's `credit_limit` field on the Contact object (`PROJECT-MEMORY.md` §6, 25-Sep decision).
- SH side: same read pattern once SH Zoho admin access covers all 10 locations (`FINISHED-PRODUCT.md` §5, `COMBINED-SYSTEM.md` §1.2 row 3).
- A browser-only helper fills Senuri's Zoho SO form; she clicks Save — not a server-side write (`PROJECT-MEMORY.md` §4 rule 9).

### Inventory system
- Reads (nightly): items, stock-by-warehouse, BOM/composite items (INV-02). Reads (hourly, phase-1 item set only): open SO lines, open PO lines (INV-03) — `inventory/FINISHED-PRODUCT.md` §5; `INVENTORY-DECISION-SYSTEM-PLAN.md` §6.
- **The one write, gated, optional, off by default**: computed ROP into Zoho's own `reorder_level` field (INV-14 for SPS / "decision 6" for SH) — only if Q9 (SPS) is answered **yes**; "no answer yet" = no (`inventory/PROJECT-MEMORY.md` §5 rule 5; `INVENTORY-DECISION-SYSTEM-PLAN.md` §6). One-way write, not two-way sync; OAuth scope limited to `items.UPDATE` only (`INVENTORY-DECISION-SYSTEM-PLAN.md` §6).
- "The system flags; it never buys" — POs stay a Zoho object created by people who create them today (`inventory/PROJECT-MEMORY.md` §5 rule 6; `INVENTORY-DECISION-SYSTEM-PLAN.md` §6).
- Every sync run audited in a `sync_runs` table (`inventory/FINISHED-PRODUCT.md` §5).

### Combined-system caveat
- "No live connector exists between Power BI and either the dashboard or the inventory system, or between Power BI and Zoho itself" — scheduled exports only (`COMBINED-SYSTEM.md` §1.1, §1.2 row 10).

---

## 4. Existing ideas for spotting missed or incomplete documentation

- **Stale-order / ageing exception (INV-06)**: flags open SO/PO lines past a 90-day cutoff, excludes them from ATP — `INVENTORY-DECISION-SYSTEM-PLAN.md` §4.3, cited again in `SYSTEM-REQUIREMENTS-FROM-DATA.md` R1 (day-count bands + escalation threshold proposed as a refinement).
- **Dead/slow-stock day-count bands** (`INVENTORY-DECISION-SYSTEM-PLAN.md` §4.6) — a rule specified but with **no assigned INV build step** (`SYSTEM-REQUIREMENTS-FROM-DATA.md` §3, "Dead/slow-stock day-count bands").
- **Accuracy gate / "unverified" badge** (`INVENTORY-DECISION-SYSTEM-PLAN.md` §4.7): every shortage is always shown, marked "unverified" until a real stock count backs it — never suppressed. Applied on the store-keeper screen (§5.1) and RM-manager screen (§5.2, "accuracy status by class, always-shown breach + badge, not suppressed").
- **Stuck-transfer list** (49 currently qualify) on the RM-manager weekly screen — `INVENTORY-DECISION-SYSTEM-PLAN.md` §5.2.
- **Mislocated-item exception** (WIP vs Raw Material) on the store-keeper screen — `INVENTORY-DECISION-SYSTEM-PLAN.md` §5.1.
- **Reason-code capture at cancellation/short-close (R6)**: Zoho/the portal today capture no real cancellation reason for 2,213 events; proposed as an SPS-org custom field or SPS capture-flow change, plus a separate order-portal flow for the 64 SH-customer events — `SYSTEM-REQUIREMENTS-FROM-DATA.md` §2 row R6, §5 item 3.
- **Triage's "Ask" flow**: a public question moves the order into a "Questions" tab until the requester replies — the portal's own missed-documentation prompt for orders lacking information — `order-portal/FINISHED-PRODUCT.md` §1 "Triage."
- **Zoho-native date-based workflow rules** as a possible no-code substitute for R1's escalation, not yet tested — `SYSTEM-REQUIREMENTS-FROM-DATA.md` §5 item 5.
- **Explainability rule**: "every flag carries a one-sentence deterministic explanation" — `INVENTORY-DECISION-SYSTEM-PLAN.md` §5 (house rules) and §3.4.
- **SH-side Zoho hygiene issues** flagged as no-code fixes, not system features: 11,556 SH SOs stuck at "shipped," never marked "delivered"; 1,876 unclassified "Product Conversion" adjustments — `SYSTEM-REQUIREMENTS-FROM-DATA.md` §5 items 1–2.
- **Audit trail as a documentation-completeness proxy**: order portal's append-only `audit_log` (DB-trigger enforced) and inventory's `sync_runs`/requisition audit trail both exist to make "did this step actually happen" checkable after the fact — `order-portal/FINISHED-PRODUCT.md` §6; `inventory/FINISHED-PRODUCT.md` §4, §6.

None of the above is framed in the source documents as a **per-person "you forgot to do X" prompt** distinct from a shortage/exception list — the closest existing mechanism is the exception-list pattern above plus the order portal's "Ask" / triage flow. No dedicated "missing-documentation-step reminder" screen or rule is described anywhere read for this report.

---

## 5. Dates, phase order, decisions made, what's still open

### Order portal
- Release order (22 Sep, decided): Preview → R0 (done) → **R1 order portal + auto credit check** → R2 managers' job list → R3 stores/invoicing → R4 blockers/raw-material → R5 GM view → R6 floor digital — `order-portal/PROJECT-MEMORY.md` §2, §6.
- R1 full release target: 11 Feb 2027 per the 25-Sep dated schedule, later shown as 15 Feb 2027 in the December-demo rewrite — `order-portal/PROJECT-MEMORY.md` §2; `COMBINED-SYSTEM.md` §3.1 step 1.
- Build order: SPS side first and complete; SH side (OP-16) floats until SH Zoho admin access arrives — `order-portal/PROJECT-MEMORY.md` §6 (20 Sep).
- Open: credit-check block-vs-hold and "pending dues" definition (OP-08); triage ownership (SPS unnamed, SH = Senuri unconfirmed); multi-job-per-order shape; English-only vs Sinhala/Tamil; 7 unconfirmed SH locations; SH Zoho admin access (CEO's item); "Portal Order No" mandatory-field change; SMTP account; manager/coordinator pairs missing for PCU/PCLU/DPU/PPU/CWU; safety-stock/MTS buffer policy — `order-portal/PROJECT-MEMORY.md` §7.

### Inventory system
- Phase order (25 Sep, decided): key-customer FG + their RM → all repeat items → traded non-chemical → specialities/chemicals → **SH rebuild if approved** — `inventory/PROJECT-MEMORY.md` §7; `INVENTORY-DECISION-SYSTEM-PLAN.md` §8.1.
- Dated schedule: SPS phase 1 (INV-01…13) live **5 Jan 2027**; INV-14 (optional Zoho write-back) 25 Jan 2027 (later corrected in `INVENTORY-DECISION-SYSTEM-PLAN.md` §6 to "no earlier than ~16 Feb 2027," colliding with INV-15/16 dates); phase 2 (INV-15, repeat items) 16 Feb 2027; phase 3a (INV-16, traded goods) 12 Mar 2027; phase 3b (INV-17, specialities/chemicals) 15 Apr 2027; **SH rebuild (INV-18) 16 Jul 2027** — `inventory/PROJECT-MEMORY.md` §7; `INVENTORY-DECISION-SYSTEM-PLAN.md` §8.1.
- Pause history: paused 20 Sep, **lifted 25 Sep 2026 ("lift it right now")** for both SH and SPS — `inventory/PROJECT-MEMORY.md` §2; memory `inventory-decision-system.md`; memory `stock-system-key-customers.md`.
- D11 (capacity conflict — inventory is a 3rd concurrent build track over the schedule's 2-parallel-step cap): **decided 25 Sep** — keep the dated schedule; user carries the extra track, Claude supplies per-step build notes — memory `inventory-decision-system.md`; `INVENTORY-DECISION-SYSTEM-PLAN.md` §8.2 item 1 ("RESOLVED 25 Sep 2026").
- Architecture (separate service vs module inside production-dashboard): **recommended**, not yet decided — Q8, Samitha + IT to confirm before INV-01 starts — `inventory/PROJECT-MEMORY.md` §3, §7.
- Other open questions: Q3 (RM stock manager role unfilled), Q6 (phase-2 "repeat item" definition), Q7 (requisition approval-value threshold), Q9 (Zoho ROP write-back yes/no), Q11 (Zoho plan tier/API cap), Q12/Q13 (SH approval-flow fit, per-location vs central buffer) — `inventory/PROJECT-MEMORY.md` §7.
- **28-Sep two-login decision** (Storekeeper-SPS / Operations–Packaging-SH / SD-chemicals-out-of-scope) does **not** itself change the 25-Sep SH-builds-after-SPS-phase-1-signoff rule "unless the user says so" — `SYSTEM-REQUIREMENTS-FROM-DATA.md` "Who uses the system"; and **§6 item 11 is explicitly left open**: which build step, if any inside phase 1, builds the Operations–Packaging-SH login, and which login the GM/production-manager/RM-manager roles map to.

### Combined / cross-system
- Build order rewritten 25 Sep (later the same day) for the December-demo decision: dashboard December-critical slot (PD-05D → PD-03D → PD-04D live 5 Nov 2026 → PSU pilot PD-0810D live 8 Dec 2026 → Screen Printing PD-12D live 21 Dec 2026 → GM cross-division view PD-10D2 live 22 Dec 2026) runs in parallel with, not before, the order-portal slot — `COMBINED-SYSTEM.md` §3.1 step 1.
- Inventory INV-01…04 starts Week 1 regardless of which dashboard slot is active, since its dependency (dashboard's `jobs` rows from PD-05D) is satisfied earlier than the old portal-first order assumed — `COMBINED-SYSTEM.md` §3.1 step 2.
- GM views (dashboard Release 5 / PD-17, and inventory's INV-12) should ship close together to avoid disagreeing GM views — `COMBINED-SYSTEM.md` §3.1 step 4; repeated in `INVENTORY-DECISION-SYSTEM-PLAN.md` §7 "What this plan does not change."
- Power BI export step is **not yet a scoped build step** in either project's plan — `COMBINED-SYSTEM.md` §3.1 step 5.
- ClickUp cut-over per division: Option 1 (stop new tasks at go-live, short overlap, then user archives) is the **recommended default, not yet the user's confirmed decision** — `COMBINED-SYSTEM.md` §1.4.

---

## 6. Gaps / contradictions with "each role sees only its own part"

1. **The clearest, most direct gap — explicitly stated by the source document itself.** `SYSTEM-REQUIREMENTS-FROM-DATA.md` "Who uses the system" [B1] / §6 item 11: three phase-1 requirements (R1 stale-order ageing, R4 concentrated item watchlist, R6 reason-code capture) are tagged to the **Operations–Packaging-SH** login, but "the Operations–Packaging (SH) login itself has no confirmed phase-1 build slot" — under the pre-existing 25-Sep rule, SH inventory (and, on the current record, the SH-side login) builds only after SPS phase 1 signs off. The document states plainly: "this document does not decide that either," leaving it open which of (a) building Ops-Packaging-SH inside SPS phase 1, (b) treating GM/production-manager/RM-manager as a third kind of access outside the two-login model, or (c) some other resolution is correct.

2. **The GM / production-manager / RM-manager roles do not map to either new login.** `SYSTEM-REQUIREMENTS-FROM-DATA.md` §6 item 11: "none of the three maps to either Storekeeper-SPS or Operations–Packaging-SH as the 28 Sep decision defines them." These three roles (INV-10/11/12) are pre-existing phase-1 screens (`INVENTORY-DECISION-SYSTEM-PLAN.md` §5.2–§5.4) built before the 28-Sep two-login split, and cut across both logins' data (RM + FG + production status) — a direct structural tension with a strict "each login sees only its own part" model.

3. **The store-keeper screen (INV-09) already shows a mix that the new login split would need to filter.** INV-09 shows all 79 phase-1 items — 11 FG + 68 RM — to what is now (post-28-Sep) the **Storekeeper (SPS)** login (`SYSTEM-REQUIREMENTS-FROM-DATA.md` §6 item 11, citing `.../INV-09-store-keeper-screen.md:25,36`), but the 28-Sep decision says that login should see raw materials **only**. The 11 FG items would need to be pulled out of that screen (or re-homed to Ops-Packaging-SH), which is not yet built or decided — R1 in the requirements doc is deliberately "scoped to the 11 FG items only, to keep raw-material SO lines off the Ops-Packaging-SH login," implying the reverse filtering (FG items off the Storekeeper screen) is a parallel, not-yet-specified fix.

4. **Raw materials cross the SPS/SH boundary by definition, contradicting a clean per-company split.** The 28-Sep role decision itself defines Operations–Packaging (SH) as seeing "the raw materials SH sells on to SPS" — i.e. raw material is not exclusively the Storekeeper-SPS login's domain; some raw-material items must appear on the SH side too. `work/DECISIONS.md` (28 Sep entry) and `SYSTEM-REQUIREMENTS-FROM-DATA.md` "Who uses the system" both state this, and the latter separately flags an **unverified caveat** (round-3 finding 4): "the same physical item, seen as a raw material on the SPS side and as finished packaging on the SH side" — a classification exercise (`item-classification/`) is still running to resolve which login each SKU belongs to.

5. **GM/COO redaction in the order portal is a partial, not absolute, "own part only" model.** GM/COO see a redacted **cross-division, cross-role** aggregate (worker identity hidden, minutes only as ≥2-worker aggregates) rather than a scoped slice of any one role's screen — `order-portal/FINISHED-PRODUCT.md` §1 "GM (Samitha)/COO." This is a deliberate design (oversight role), but it is architecturally different from the "each person sees only their part" principle stated for front-line roles, and the combined-system document independently warns of **"three GM views that can disagree"** if the dashboard's, inventory's, and Power BI's GM-facing views are built far apart (`COMBINED-SYSTEM.md` §2 "GM daily view" row, §3.1 step 4) — i.e. even the oversight layer risks fragmenting rather than unifying.

6. **Credit & Billing Reviewer visibility is an explicit narrow exception, already inconsistent with "own part" by design.** The credit-review order is visible only to "Senuri, the order's placer, CEO, COO and both GMs — nobody else, not even other triage staff" (`order-portal/FINISHED-PRODUCT.md` §1) — narrower than the requester/triage/coordinator role boundaries elsewhere, showing the systems already use ad hoc, per-field visibility rules rather than a single consistent "one screen per role" rule.

7. **Mobile/floor-worker access is unresolved for both systems, so per-role scoping for those layers can't yet be assessed.** Order portal: mobile "gated on an unfunded DECISION (PD-18, no unit-cost quote yet)" (`COMBINED-SYSTEM.md` §2 "Mobile" row). Inventory: "not specified in the design plan... flag as an open question" (`inventory/FINISHED-PRODUCT.md` §6). Neither system's future floor-level screen has a defined scope yet, so it's unknown whether it will follow the same-person-same-slice principle.

8. **SD (chemicals) is fully out of scope for both new logins, but the order portal and dashboard make no equivalent chemicals carve-out.** `work/DECISIONS.md` (28 Sep) and `SYSTEM-REQUIREMENTS-FROM-DATA.md` "Who uses the system" define SD as outside the inventory system entirely. No source read here defines an analogous exclusion inside the order portal or production dashboard screens — worth confirming whether chemical-item orders/jobs flow through those systems' generic screens without a role boundary.

---

Abdul Hadhee | IT Exec | Standard-Holdings (evidence pull, not a new decision)
