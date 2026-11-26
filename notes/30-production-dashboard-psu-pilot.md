# Production dashboard rollout plan — PSU as the first pilot

Prepared by Abdul Hadhee | IT Exec | Standard-Holdings, 25 Sep 2026.

**Changed 25 Sep 2026 (January plan + ClickUp):** §5's rollout table rewritten — RWU, PCU and CPU
now go live **together** on 28 Jan 2027 (was RWU alone), OPD moves to 10 Feb 2027 (was 23 Feb),
and MOBA/FPP/remaining small divisions go live together on 17 Mar 2027 (was 19 Apr) — batched to
meet the "most departments in January 2027" requirement instead of rolling out one division every
4–8 weeks. §6's milestone dates updated to match. Full detail and the PCU/OPD flags:
`dev/01b-dated-schedule.md` §3b. Each division's rollout also cuts over that division's ClickUp
list (pending the user's decision on the transition option) — see `dev/01b-dated-schedule.md` §6b.

**Changed 25 Sep 2026 (December dashboard plan, earlier):** the user made a later decision the same day —
**PSU and Screen Printing must both be live by December 2026, managers only.** This changes: (1)
the PSU pilot window from ≥4 weeks (§4/§5/§6 below) to **≥3 weeks**, and Screen Printing's own
pilot from ≥2 weeks unchanged but now starting **before** PSU's bar formally clears — a flagged
deviation, not the normal move-on rule (§5); (2) the GM tile (§3) ships **trimmed** for December
(job/blocked counts only, no straw-output-vs-plan comparison) rather than the full version
described below; (3) §6's dated schedule is fully superseded again — PSU's full release is now
**8 Dec 2026** (was 5 Apr 2027), Screen Printing's **21 Dec 2026** (was 21 May 2027), see
`dev/01b-dated-schedule.md` (rewritten same day, later) for the current dates. Full technical
basis: `dev/01c-dashboard-december-feasibility.md`. RWU (§5) and everything after keeps the
original ≥2-week convention and the normal "wait for the bar" rule — only PSU→SHPS is compressed.

**Changed 25 Sep 2026 (user decisions, same day, earlier):** (1) PSU-first is now **DECIDED (user, 25 Sep
2026)** — reason: smallest department — not a proposal any more; §2.5's COO wording is unchanged
advice, the decision itself is final. (2) §5's rollout order after PSU is corrected: **Screen
Printing (SHPS) is now second, RWU third** (was RWU second, SHPS third) — same correction applied
to §5's floor-tablet order and §6's week-numbered plan. (3) §6's week-numbered "W1…" plan is now
superseded by a dated master schedule with fixed calendar dates and testing windows —
`dev/01b-dated-schedule.md` / `dev/dated-schedule.json`; this file's week numbers stay as the
underlying effort reasoning but are no longer the schedule of record. Credit-check and
customer-name items in the original decision batch don't touch this file's content.

**This plan changes the pilot division.** On 23–24 Sep the COO was told, and a talk script was
prepared, to pilot the production dashboard in **Screen Printing (SHPS)** first
(`/root/Production Dashboard/CLAUDE.md:325`: "highest pain, only 59 jobs"; COO notes and talk
script dated 23–24 Sep). The user has now asked to pilot **PSU (Paper Straw Unit) first
instead.** Section 2 below states that reversal plainly, with the honest trade-offs, and what
needs to be said to the COO so this doesn't look like the plan changing direction for no reason.

Every number in this plan cites the file it came from. Sources: `research/dashboard-state.md`
(25 Sep survey of what's built and agreed), `/root/Production Dashboard/CLAUDE.md` (the original
brief), the production-dashboard design spec
(`/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md`, Rev 7.3), and
this report set's `04-jobs-in-production.md` / `open_jobs.csv`.

---

## 1. Where the build actually stands today

| Layer | State | Source |
|---|---|---|
| **Release 0 — Foundation** | Built and tested (143 tests green, reviews PASS). **Not deployed, not pushed to GitHub.** Dev repo `/root/dev/production-dashboard`, HEAD `b0cd339`. Auth, SSE, admin config screens, schema (migrations 001–004, additive only) are all in place. `config/forms/` is empty. | `dashboard-state.md:2` |
| **Floor Board demo** | Running live for demo purposes only, `pm2 'Production'`, port 4310. Not the production deployment. | `dashboard-state.md:2` |
| **Releases 1–6** | Specified at a high level; **not built**. Design spec Rev 7.3 (17 Sep) defines Releases 0–5 in detail (§13). Management agreed a slightly different release numbering on 22 Sep (below) — that agreement is the current plan; the two numbering schemes don't map 1:1 and the newer one governs. | `dashboard-state.md:4`; spec §13 |
| **Release 1 v2 spec delta** (credit check, multi-job, notifications, company+SH location, MFA) | **Not written.** | `dashboard-state.md:3` |
| **Release 1b Zoho-sync addendum** | **Not written.** Until it exists, Zoho data freshness depends on the manual daily header pull (spec §14.2). | `dashboard-state.md:3`; spec §14.2 |

**The release order agreed with management on 22 Sep** (this supersedes the spec's R0–R5 labels
where the two disagree):

```
Preview (Floor Board demo, Samitha + managers)
  → R0 Foundation (done, not deployed)
  → R1 Order portal + auto credit check (everyone, all divisions at once)
  → R2 Managers' job list (everyone, all divisions at once)
  → R3 File location + QR (piloted in one division first)
  → R4 Blockers + advisory raw-material check (piloted in one division first)
  → R5 Samitha's GM view (after 4 weeks of data)
  → DECISION: floor tablets, yes/no
  → R6 Job file goes fully digital on the floor (per-division rollout)
  → later, one at a time: stores + invoicing, COO reports, key-customer stock tool
```
Source: `dashboard-state.md:4`.

**What "PSU first" actually changes:** R1 and R2 already roll out to every division at once —
there's no pilot division to choose there. The division choice only matters for **R3, R4, and
the R6 floor order**. That's the choice this plan reverses.

**Correction (25 Sep, after checking the dev repo):** today nothing in the built app limits R3/R4
to one division. Migration 002 seeds all 14 divisions at once and `reason_codes` is global; the
only per-division switch is `floor_live`, which belongs to the R6 floor decision
(`dev/production-dashboard/02-process-steps.md`, "overclaims" note). So "pilot in PSU" for R3/R4
is an **operating choice** (IT trains and supports PSU first, and only PSU is asked to use the
screens), not a technical lock. If the COO wants other managers to be unable to open R3/R4 until
their turn, that is a new feature (an activation flag next to `floor_live`) needing its own spec
change. Don't tell the COO the system restricts it until that exists.

---

## 2. The reversal: Screen Printing was recommended, PSU is now asked for

### 2.1 State it plainly

The COO was told on 23–24 Sep that Screen Printing (SHPS) would pilot first. This plan now
recommends PSU instead. Nothing about the underlying system design changes — R3 and R4 are the
same features either way. What changes is **which division absorbs the risk of the first live
data-entry cycle**, and **which manager and jobs the GM sees on screen first.**

### 2.2 Why Screen Printing was picked originally

- **Highest pain**: the file-location problem and raw-material shortages are worst there. 31% of
  Screen Printing jobs were blocked on "R/M Not available" (18 of 59) in the dataset the brief
  was built from. `/root/Production Dashboard/CLAUDE.md:217`
- **Small and tractable**: "only 59 jobs" — small enough that IT could hand-key two weeks of data
  so no manager carries dual entry while edge cases surface. `CLAUDE.md:325`
- **No verified full-cycle example exists yet.** An SHPS pizza-box job (order 3 Aug, to production
  11 Aug, produced in 7 hours) was previously cited as taking "roughly four months from order to
  shipment" (`CLAUDE.md:300-306`), but this report's own research notes explicitly caution against
  using it (`dashboard-state.md:10`: "don't use the '7 hours / 4 months' example"). The example's
  own timeline also doesn't support the claim: it quotes a shipment of "~9 Dec", which is more than
  two months after this report's 25-Sep-2026 date — the shipment had not happened when this plan
  was written, so "four months from order to shipment" was never an observed fact, only a forecast
  dressed up as one. What *is* verified: SHPS's SO-to-first-bundle lead time over the last 12
  months is a median of 10 days (p80 20 days) — faster than OPD's 20/30 (`05-capacity.md:142`) —
  but no verified, completed order-to-shipment cycle time exists for SHPS today. That gap is itself
  a reason to build the dashboard: right now nobody can answer "how long does a SHPS job actually
  take end to end" with real data.

### 2.3 The honest trade-offs, PSU vs Screen Printing

| | PSU (proposed) | Screen Printing / SHPS (recommended 23–24 Sep) |
|---|---|---|
| Order type | Ex-stock for SH — simpler order flow, no artwork/plate approval step. `dashboard-state.md:6` | Customised, artwork/plate involved — more steps in principle, but no verified full-cycle timing exists to quantify how much longer or more variable it is (§2.2). |
| Process flow | 3 processes: forming, cutting, packing. `dashboard-state.md:6` | More steps, more handoffs; the division management called "highest pain". |
| Manager | Ishan (also covers Offset, Packpro, RWU — not a dedicated PSU manager). `dashboard-state.md:6`, `CLAUDE.md:99-108` | Mubeena → coordinator Madushi, a Screen-Printing-specific pair. |
| Creator = receiver (weak handover timestamps) | **Yes** — Umanda creates and receives. `dashboard-state.md:6` | **Also yes** — Madushi creates and receives. This is *not* a PSU-specific weakness; SHPS, RWU and PSU all lack a handover event. `CLAUDE.md:118` |
| Existing job-sheet baseline to validate against | **None.** PSU has no dedicated job-sheet tab; it appears only in the daily shop-floor trackers. Confirmed here: `open_jobs.csv` (228 open jobs from the Sep job sheet) has **zero PSU rows** — its division breakdown is OPD (Customized) 111, OPD (SH-Stock) 53, Screen Printing 26, CPU 20, FPP 13, Screen Printing (cups) 5. | Screen Printing has two dedicated job-sheet tabs (46 + 65 rows) and appears in `open_jobs.csv` — an existing baseline to cross-check the dashboard's derived stages against. |
| Demonstrated cycle speed | Fast: 221 PSU ex-stock SOs moved SO → bundle → package → ship → invoice in **0–2 days** in the demo run. `dashboard-state.md:6` | Slow and highly variable (weeks to months), which is exactly why it was chosen to expose "where does time go" — but also means the pilot takes longer to show a clean before/after story. |
| Growth story for the GM | Paper Straw White 8mm×20cm SPS is a top-10 growth item, +45%, planned at 139,000 units Oct–Dec. `dashboard-state.md:6` (cross-checked against the Oct–Dec plan in `04-jobs-in-production.md`) | No equivalent growth story; the story there is pain reduction, not growth. |
| Known open data problems | Job number format is inconsistent (`PSU/BTN/989`-style, two batches split 11 Sep / 16 Sep — `dashboard-state.md:6`); open question on whether packed/imported/SPS-made straws are one item or three (§8 below); who fills the Time Claiming Bill is unanswered (Q6, `CLAUDE.md:348`); **no machine register exists** for PSU. | Also has open problems, but they're the ones the original brief already scoped around (R/M shortage tracking, file-location tracking) — better understood going in. |
| "Highest pain" signal | Not established — no R/M-blocked-rate figure exists for PSU in the data used for this report. Flagged as unknown, not zero. | Established: 31% R/M-blocked (`CLAUDE.md:217`). |

### 2.4 Why PSU anyway — the case for reversing

- **Lower risk to prove the mechanics first.** PSU's flow is genuinely simpler (3 processes,
  ex-stock, no artwork approval), so the first two weeks of hand-keyed data are more likely to
  expose *dashboard* bugs than *process-complexity* bugs the dashboard can't help with anyway.
- **A visible win, not just a pain reduction.** A 0–2 day order-to-invoice cycle that the GM can
  watch happen live, on a growth item, is something to point to in week 2. Screen Printing has no
  verified full-cycle example to point to at all yet (§2.2) — only a slower, more variable process
  in principle, which by definition takes longer to show a clean before/after story once the
  dashboard starts measuring it for real.
- **It closes a real blind spot.** PSU currently has no job-sheet tab and no machine register —
  it is the division management can see *least* of today. Piloting there turns an invisible
  division into a tracked one, which Screen Printing (already partially visible on the job sheet)
  does not need as urgently.
- **The honest cost:** PSU does not carry the "highest pain" evidence Screen Printing does, so
  this pilot proves the *system works*, not that it *fixes the worst problem first*. If the GM's
  main question is "where is our worst bottleneck," Screen Printing still answers that better.

### 2.5 What must be said to the COO

Say this directly, don't bury it:

> "We told you Screen Printing would go first because it's the highest-pain division. We're now
> proposing PSU first instead — not because Screen Printing stopped being the priority, but
> because PSU is the faster, lower-risk way to prove the system works before we put it in front
> of the division that's actually hurting. Screen Printing is still next in line after PSU (see
> §5), and the plan doesn't lose any time versus telling you a specific pilot date, because we
> hadn't committed to one."

Two things this message must not do: (1) it must not claim Screen Printing's pain went away — it
didn't; and (2) it must not promise the reversal saves time — it's a risk trade, not a schedule
optimisation. Section 6 below gives the actual week-numbered schedule, and it happens to be
similar either way.

---

## 3. What the PSU pilot must include (unavoidable) vs what's dropped

**Correction: the design spec does not already define R3/R4 as feature sets — this needs stating
plainly as a gap, not a citation to fix.** "Advisory raw-material check" exists only as a two-word
label in the 22-Sep management roadmap note (`dashboard-state.md:4`); a full-text search of the
1,262-line design spec for "advisory", "RM check" and "raw-material check" returns zero matches
(the only near-hit is an unrelated "Reorder" trim example at spec line 868). There is no data
model, screen or acceptance criteria behind "advisory raw-material check" anywhere in the spec.
"File location + QR" is only partially specified, and not as its own release: QR check-in is part
of Release 1's cover sheet (spec AC1.21, `§7.2.3`), and file-location fields appear in the job
Overview shown across Releases 0–3 (spec `§7.2`, line 444) — not a self-contained feature set the
way the spec's own Release 3 (Stores/Invoicing, `§7.4`) is. Spec `§7.3` is the Manager workspace
(Release 2), not R3 or R4 either. **So before R4 can be built or estimated, someone still has to
write what "advisory" means** — what triggers the warning, against what stock data, shown where —
and that spec work doesn't exist yet. This is a real gap to close, separate from the scheduling
question below: **R5 (Samitha's GM view) is scheduled for "after 4 weeks of data"**
(`dashboard-state.md:4`). A pilot that gives the GM nothing to look at for a month risks losing his
attention before R5 even ships. So this plan adds one deliberate scope decision: **pull forward a
minimal, PSU-only GM summary into the pilot itself**, rather than making Samitha wait for the full
R5 build.

| Feature | In the PSU pilot | Moves to next version | Why |
|---|---|---|---|
| PSU job/order status (file location, current stage) | **Yes** | — | This is R3's core purpose; without it there's nothing to pilot. |
| QR-based check-in for Ishan/Umanda | **Yes** | — | R3 as specified (`dashboard-state.md:2` names "file location + QR"); avoids adding typing burden that would bias the pilot's adoption numbers. |
| Blocker flag + reason code | **Yes** | — | R4's core purpose; without it the pilot can't test "readiness vs capacity" (the original Phase-1 question, `CLAUDE.md:306`). |
| Advisory raw-material check | **Yes, advisory only** | Automated PO trigger stays out | Spec scopes R4 as advisory (a warning, not an action); an automatic reorder trigger is a bigger, riskier feature that hasn't been specified. |
| A minimal GM tile (today's job count, in-production count, blocked count) | **Yes — new, scoped here. CHANGED 25 Sep, December dashboard plan: trimmed for December** — drops on-time count and the straw-output-vs-plan comparison (needs PD-07's item-code answer, no longer a December requirement); extends to PSU+SHPS on 22 Dec 2026 (`PD-10D2`), the December demo milestone. | The full metric set (on-time count, straw output vs plan) and the full cross-division GM view (R5) | Gives Samitha a reason to open the dashboard daily during the months before R5, without building all of R5 early. Small: one screen, no new tables — it reads the same job/blocker data R3/R4 already capture. |
| Credit-check automation nuances (partial payment terms, Books integration) | No | Full R1/R1 v2 scope, all divisions | R1 already ships to everyone before the PSU pilot starts (§1); PSU's ex-stock-to-SH flow is the simplest credit case, so edge cases surface elsewhere first, not in this pilot. |
| Floor tablet, EPF login, digital job file on the shop floor | No | R6, after the tablets DECISION gate | R6 needs the Employee Master read-only token (P1), which has its own spec, review and deploy (`spec §0` P1; `dashboard-state.md:9` "L18"). PSU jumping the R3/R4 pilot queue does not pull R6 or P1 forward. |
| Machine register for PSU | No | Not yet scoped anywhere | No machine register exists for PSU today (`dashboard-state.md:6`); building one is out of scope for a job-tracking pilot and would need its own spec. |
| Fixing the job-number format and straw item-code ambiguity | Data-cleanup task, not a feature | — | See §8 — this has to happen *before* or *during* the pilot as data prep, not as a dashboard feature. |

---

## 4. Pilot success metrics and feedback loop

The pilot needs a stop/go read before it becomes the template for every other division. Proposed
metrics (all computable from the dashboard's own tables once R3/R4 are live — none of these
require new instrumentation):

| Metric | Target to call it "working" | Why this one |
|---|---|---|
| Jobs entered same-day vs backfilled | ≥ 80% same-day by week 3 (still valid — CHANGED 25 Sep, December dashboard plan: the pilot window itself is now ≥3 weeks, not ≥4, so "by week 3" is the last full week, not the middle of the window) | Backfilled entries defeat the whole point of live timestamps (the batch-entry risk already flagged in `LATER.md` L10). |
| Blocker reason-code fill rate | ≥ 90% of blocked jobs have a reason code, not left blank | An empty reason code is a blocker nobody can act on. |
| SO match rate for PSU jobs entered | ≥ 90% link to a real Zoho SO | Mirrors the SO-match problem already found in `04-jobs-in-production.md` (102 of 228 open jobs across all divisions had no SO-lines match) — PSU starts with no baseline, so this has to be watched from day one. |
| Ishan/Umanda using QR check-in vs manual entry | Trending up, not flat | Confirms the QR feature is actually reducing friction, not being ignored. |
| Samitha opens the GM tile | At least a few times a week by week 3 | Direct read on whether the "unavoidable" GM feature in §3 is doing its job. |
| Divergence: dashboard stage vs Zoho status | Shrinking week over week | Spec's own operational check for approving anything further (`spec §14`, "Divergence"). |

**Feedback loop:** weekly 15-minute check-in with Ishan and Umanda during the pilot (they are
both the creator and the coordinator for PSU, so they see every problem first); IT reviews the
five metrics above every Friday and logs anything that needs a fix before the next division
starts. No metric here needs new dashboard code — they're all queries against tables R3/R4
already create.

---

## 5. Per-department rollout schedule after PSU

R1 and R2 already cover every division at once (§1). What follows PSU is the R3/R4 pilot order
for the *other* divisions, and — once the tablets DECISION is made — the R6 floor order.

**Move-on criteria** (same threshold for every division, not just PSU): 2–4 weeks of stable use
(**CHANGED 25 Sep, December dashboard plan: PSU's own window is ≥3 weeks, not 2–4, for December
only** — the harness's tighter December minimum; every division from RWU onward keeps the
original 2–4 week convention), same-day entry ≥ 80%, blocker reason-code fill ≥ 90%, and no open
critical bug. A division does not start until the previous one clears this bar — this is the same
gate PSU has to clear in §4 — **except Screen Printing below, which is a flagged, one-time
exception for December.**

**Rewritten 25 Sep 2026, January plan: the table below now batches divisions instead of rolling
out one at a time**, to meet the separate requirement that most departments go live together in
January 2027. Waves 3–5 below are new; waves 1–2 (PSU, Screen Printing) are unchanged.

| Order | Division(s) | Why here | Depends on |
|---|---|---|---|
| 1 | **PSU** (pilot) | §2.4 | — |
| 2 | **Screen Printing (SHPS)** — **moved up from 3rd, DECIDED (user, 25 Sep 2026)** | The originally-recommended division. Going straight after PSU means R4's blocker-tracking reaches the division with the actual 31% R/M-blocked pain (`CLAUDE.md:217`) sooner, once PSU has proven the weak-timestamp handling (shared with PSU/RWU/SHPS) works. | **CHANGED 25 Sep, December dashboard plan: does NOT wait for PSU's move-on bar to clear** — starts 21 Dec 2026, 7 working days before PSU's bar clears (30 Dec), gated instead on SHPS's own IT-test/UAT plus a lightweight 14 Dec checkpoint. A flagged, accepted deviation to hit "both live by Dec 2026" — see `dev/01b-dated-schedule.md` §6.1. |
| 3 | **RWU + PCU + CPU together** — **CHANGED 25 Sep 2026, January plan: batched, was RWU alone then PCU/CPU as a separate wave 5** | All three reuse R3/R4 exactly as built for PSU and SHPS — no new code, only new division configs. RWU shares PSU's manager/coordinator pair (Ishan/Umanda), same creator=receiver limitation, so PSU's/SHPS's pilot lessons transfer directly. RWU is second-largest division by revenue share (26.3% of SPS revenue full-window, `01-business-history.md`). PCU has an established lead-time baseline (`05-capacity.md`); CPU is growing fast (Keells/Spar cutlery move, Jul 2026 on) but only has 2 months of bundle history — worth tracking sooner rather than later precisely because it's thin on data. **PCU is flagged, not a rubber-stamp addition:** `LATER.md` L20 lists it as one of five divisions with manager/coordinator/stage order genuinely unset (unlike RWU or CPU) — needs Samitha's answer by 17 Dec 2026 or it's held back from this wave. | SHPS clears the bar |
| 4 | **OPD (Offset)** | Largest division (50.3% of SPS revenue, `01-business-history.md`) and the most complex routing (manager is a runtime choice between Ranga and Ishan, `CLAUDE.md:114,346` — an open question). Deliberately last among the big single divisions: mistakes here are the most expensive, so it goes once the process is proven. | Wave 3 clears the bar, and the shared developer's one dashboard build slot (occupied by wave 3's build first) — this is why OPD's pilot lands 10 Feb 2027, not "late January" as first asked for (flagged, `dev/01b-dated-schedule.md` §3b) |
| 5 | **MOBA, FPP, remaining small divisions (DPU, Paper Cup Lid, Cake Wrapper, Paper Plate) together** — **CHANGED 25 Sep 2026, January plan: FPP folded in here rather than given its own later step** | FPP specifically needs care: it has 12 real open jobs (a 13th job-sheet row is blank, not a job) and every one of the 12 is overdue, two dating to 2025 (`04-jobs-in-production.md`) — a chronic backlog, not a dashboard problem. By this point (March 2027) five other divisions have been live for weeks, so the earlier "onboard FPP once managers are used to acting on blocker flags" caution is already satisfied. The others are small enough to batch with MOBA. | OPD clears the bar (2 Mar 2027) — satisfies "February 2027 or later" since it lands in March |

**Floor tablets (R6), once the DECISION gate is passed:** apply the same PSU-first logic — the
spec's original floor order was SHPS → RWU → PSU (`spec §13`, Release 5); this plan recommends
reversing that to **PSU → SHPS → RWU**, matching the desk-side order above (corrected 25 Sep 2026
to put SHPS second), so the division with the most practice by then also gets tablets first. This
is a recommendation to revisit at the DECISION gate itself, not a commitment made now.

---

## 6. Build time plan (weeks, not calendar dates)

**Superseded for scheduling purposes, 25 Sep 2026: fixed calendar dates now exist for every step**
(`dev/01b-dated-schedule.md`, `dev/dated-schedule.json`), per the user's decision that day —
because each step below has its own dev plan and agentic-coder prompt, dates can be committed, not
just estimated in weeks, and every user-facing release now carries an IT-test → UAT →
(division rollouts) pilot window before its full-release date. **This section's week numbers stay
as the underlying effort-sizing reasoning (AC counts, relative size) that the dated schedule was
built from — they are no longer the schedule of record; read the dated schedule for the actual
commitment.** **CHANGED 25 Sep 2026 (December dashboard plan, later same day): the dated schedule
below was rebuilt again, the same day, per the user's December-demo decision — PSU and Screen
Printing must both be live by December 2026.** The current dated schedule's PSU pilot full release
is **8 Dec 2026** (pilot window to 30 Dec); Screen Printing's is **21 Dec 2026** (pilot to
6 Jan 2027, starting before PSU's own bar clears — see §5's flagged deviation). **CHANGED 25 Sep
2026, January plan (same day, later still): RWU + PCU + CPU together, 28 Jan 2027** (was RWU
alone, 18 Jan 2027); **OPD, 10 Feb 2027** (was 23 Feb 2027); **MOBA + FPP + small divisions
together, 17 Mar 2027** (was PCU/CPU 24 Mar 2027 then remaining divisions 19 Apr 2027) — rewritten
to meet the "most departments in January 2027" requirement, see §5 above and
`dev/01b-dated-schedule.md` §3b. These reflect §5's corrected order (SHPS second, the batched
waves third onward), the added testing time, and the harness's own December pilot minimums (PSU
≥3 weeks, SHPS ≥2 weeks) — see `dev/01b-dated-schedule.md` for the full rebuilt schedule; the
"W1…" week numbers in the table below are the underlying effort-sizing reasoning only, not
calendar dates for any of these steps any more.

What follows is the original week-numbered milestones from a start week — kept for the effort
reasoning, **not a calendar promise any more.** It's built from the relative size of each release,
using the number of acceptance criteria (ACs) already written for each one as a proxy for effort.

**Correction: the previous version of this table miscounted the ACs and mis-sized R3/R4/R5.** It
used `grep -c "AC0\."`-style commands, which count every textual occurrence of an AC's ID string
(including cross-references in prose and the plan-critic appendices at the bottom of the spec),
not the number of distinct acceptance criteria. Recounted as distinct AC table rows per release
section:

| Release | ACs specified (spec file) | Relative size |
|---|---:|---|
| R0 Foundation (done) | 27 | Largest — already built |
| R1 Order portal + credit check | 31 | Largest release not yet built |
| R1b Zoho sync | not yet specified (addendum pending) | Unknown — addendum must be written first |
| R2 Managers' job list | 13 | Medium |
| R3 File location + QR | No AC count exists — not its own release in the spec (§3) | Unknown — can't be sized from the spec today |
| R4 Blockers + advisory RM check | No AC count exists — the feature isn't specified at all (§3) | Unknown — can't be sized until it's specified |
| R5 GM view (Samitha's) | No AC count exists — the spec's own "Release 5" (17 ACs) is Floor stations, a different feature, not Samitha's GM view | Unknown — can't be sized from the spec today |

Source: distinct AC table rows counted per release section against
`/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` §13 (`awk` over
each `### Release N` heading, counting rows starting `| N.` — not a text-mention grep). **R0, R1
and R2 correspond 1:1 between this plan's numbering and the spec's** (same features, same order),
so those three counts are reliable size proxies. **R3, R4 and R5 do not** — this plan's R3 (file
location + QR), R4 (blockers + advisory RM check) and R5 (Samitha's GM view) are a different,
smaller-scoped feature set than the spec's differently-numbered Release 3 (Stores/Invoicing),
Release 4 (GM/COO/Analyst) and Release 5 (Floor stations) — confirmed in §3 above. There is
currently no acceptance-criteria basis to size R3/R4/R5 at all; the week estimates below that
depend on them are judgement calls, flagged as such, not AC-based estimates.

| Week | Milestone |
|---|---|
| **W1** | Deploy Release 0 (human runs `shdeploy production-dashboard` once the runbook's Part A is done). Write the Release 1 v2 spec delta and the Release 1b sync addendum — both currently missing (§1) and both block work after this week. |
| **W2–W5** | Build R1 (order portal + auto credit check) and R1b (Zoho read-only sync) in parallel where the addenda allow. R1 is now the largest not-yet-built release (31 ACs, more than Release 0's own 27) — budget an extra week versus the earlier estimate. |
| **W6** | R1/R1b go live for everyone. Build R2 (managers' job list, 13 ACs — more than double the earlier 6-AC estimate, but still the smallest built-to-date release; budget accordingly). |
| **W7** | R2 live for everyone. Start data prep for the PSU pilot (§8) — this must be done *before* R3/R4 land in PSU, not during. |
| **W8–W9** | Write what R3 (file location + QR) and R4 (blockers + advisory RM check) actually mean as acceptance criteria — this doesn't exist yet (§3) — then build and pilot them in PSU. **No AC-based size estimate exists for this window** (see correction above); the two-week figure is a placeholder carried over from the original brief's estimate for hand-keying data in one division (`CLAUDE.md:325`), applied to PSU instead of Screen Printing, not a sized estimate for the R3/R4 build itself. |
| **W10–W13** | Pilot observation window — the 2–4 week move-on criteria in §5 run their course. GM tile (§3) live throughout. |
| **W14** | If PSU clears the bar: roll R3/R4 out to **Screen Printing (SHPS)** (moved up to 2nd, 25 Sep 2026). If not: fix and re-run the pilot window — do not move to SHPS on a failed metric. |
| **W17** | SHPS clears the bar (assuming a clean run) → **RWU + PCU + CPU together** start (CHANGED 25 Sep 2026, January plan — batched, was RWU alone). |
| **W21** | The RWU/PCU/CPU wave clears the bar → **OPD** starts (the largest, most complex — budget extra buffer here; not compressed into the same 3-week rhythm as the smaller divisions). |
| **~W25 onward** | R5 (Samitha's GM view) — start once at least PSU + SHPS have 4 weeks of clean data behind them, per the "after 4 weeks of data" rule already agreed (`dashboard-state.md:4`). No AC count exists for R5 (see the correction above), so this has no sized duration either. **CHANGED 25 Sep 2026, January plan:** OPD and the MOBA/FPP/small-divisions wave continue in parallel on the R3/R4 track, the latter gated on OPD's own bar (§5). |
| **After R5 + tablets DECISION** | R6 floor rollout, PSU → SHPS → RWU → remainder (§5, corrected order). |

**Caveat stated plainly — stronger than the earlier version of this plan said.** The earlier
version said "treat W1–W8 as the only numbers worth holding anyone to." That's no longer accurate:
W8–W9 (the R3/R4 build) has **no AC-based sizing behind it at all**, not just untested downstream
risk — R3 and R4 aren't specified as their own release in the spec (§3, and the correction above).
**Only W1–W7 have a real sizing basis** — Release 0's actual build time, plus AC counts (27/31/13)
that correspond to what's actually being built (R0, R1, R2). Everything from W8 onward — the PSU
pilot build itself, the observation window, and every division after PSU in §5 — rests on an
estimate that was never sized to begin with, and needs re-doing once R3/R4 are actually specified
(§3) and once R1's real build time is known. Treat W8 onward as a placeholder schedule, not a
commitment.

---

## 7. Data that needs fine-tuning before or during the PSU pilot

These are data-quality problems, not dashboard features — fixing them is a precondition for R3/R4
to produce trustworthy PSU numbers, not a task for the dashboard team to build. (Success metrics
and the feedback loop for the pilot itself are in §4.)

- **Time Claiming Bill**: a green pre-numbered carbon book (date, product, minutes, employees,
  staff count, impressions, serial number) used on the floor. **Who fills it out is still an open
  question** (Q6, `CLAUDE.md:348`; also listed open in `dashboard-state.md:6`). This has to be
  answered before the dashboard can treat its data as a reliable source for labour-minutes —
  matches the wider finding in `05-capacity.md` that BOM labour-service quantities are flat
  (non-informative) for PSU and several other divisions, so the Time Claiming Bill may be the
  *only* real labour data PSU has.
- **Job number format**: PSU jobs use a `PSU/BTN/989`-style number, and the September run was
  split into two batches (7,724 lines on 11 Sep, 7,816 lines on 16 Sep) — `dashboard-state.md:6`.
  The dashboard's job-number parsing (already a stated non-goal to build generically,
  `spec §3` "Parsing job numbers") needs a PSU-specific rule confirmed with Ishan/Umanda before
  R3 can reliably match a PSU job to a Zoho SO.
- **Straw item codes**: open correction flagged in the research — is "packed straw", "imported
  straw" and "SPS-made straw" one product or three separate item codes in Zoho?
  (`dashboard-state.md:6`). This has to be resolved before the GM tile's "straw output vs the
  139,000-unit Oct–Dec plan" metric (§3) means anything — right now it's not known whether that
  plan figure and PSU's bundle output are counting the same thing. **CHANGED 25 Sep, December
  dashboard plan: no longer December-blocking** — the trimmed December tile (§3) drops this
  metric; it can be resolved at a relaxed pace and only feeds the full GM view later.
- **No machine register**: confirmed nowhere in Zoho or the job sheet (`dashboard-state.md:6`).
  Out of scope for this pilot (§3), but worth flagging now so nobody expects machine-level output
  data from the PSU pilot.

---

## Files

- `30-production-dashboard-psu-pilot.md` — this report
- Sources (not duplicated here): `research/dashboard-state.md`,
  `/root/Production Dashboard/CLAUDE.md`,
  `/root/Project Management/wiki/specs/2026-09-17-production-dashboard-design.md` (Rev 7.3),
  `analysis/04-jobs-in-production.md`, `analysis/open_jobs.csv`, `analysis/05-capacity.md`,
  `analysis/01-business-history.md`
