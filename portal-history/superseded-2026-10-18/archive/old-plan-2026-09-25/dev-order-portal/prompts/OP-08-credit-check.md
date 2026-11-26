# OP-08 — Credit check (spec delta + build, gated)

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** dates below move later — the
shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated
Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** the data-source question (Zoho Books vs Zoho Inventory) is now **DECIDED**
— Zoho Inventory, no Books access needed. Rewrote Context, the file list, Phase 2's data-source
instructions, "What NOT to touch," and the stop-and-ask list to match; added the exact field,
endpoint and formula and the build's calendar dates.

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

## Context

**Do not start this step until the two questions below are answered by Finance/Hazeem and the
COO.** The credit-check mechanism is sketched (`CLAUDE.md §17.2`/§17.5) but not yet in the frozen
state machine (spec §7.2.0 has no credit-hold state). The data source is settled (Zoho Inventory,
decided 25 Sep 2026 — see below); starting this step before the two remaining questions are
answered means guessing a state shape or a formula input, which is exactly the failure mode the
house doctrine forbids.

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row
`OP-08`):** build 14–21 Dec 2026 (**FORCED**: later start; answer deadline moves to 30 Nov 2026).
Ships as part of OP-14's single Release-1 go-live: IT test 26–28 Jan 2027, UAT 29 Jan – 12 Feb 2027,
full release **15 Feb 2027** (target 11 Feb), live for everyone.

## Files to read first

1. `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/order-portal/02-process-steps.md`,
   step OP-08, in full — it has the two remaining questions, the DECIDED data-source note, and the
   two draft enum sets to reconcile.
2. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §5 in full.
3. `/root/Project Management/reports/2026-09-25-sps-business-plan/analysis/research/zoho-credit-limit.md`
   — the field/endpoint/formula/rate-limit research behind the DECIDED data source. Read this before
   writing any Zoho-facing code in Phase 2.
4. `/root/Production Dashboard/CLAUDE.md` §17.2 step 3, §17.5.
5. Design spec §7.2.0 (the current, credit-free state machine you'll be extending) and §7.2.4
   (visibility matrix pattern to follow for "On Hold – Credit Review").

## Exact scope, in two phases

**Phase 1 (spec delta):** add a credit state or gate to §7.2.0, matching whichever shape question 1
below implies (a new terminal-ish state, or a hard 400 at submit plus a release queue). Reconcile
the 20-Sep draft enums with the spec's actual `order_events` enum — implement one set only. Write
numbered ACs for the new state/gate, same style as OP-01's delta. This phase gets its own
`plan-critic` pass, same as OP-01.

**Phase 2 (build):** data source is **DECIDED: Zoho Inventory**, not Books. Call
`GET /contacts/{contact_id}?organization_id={id}` (Zoho Inventory API v1) for the logged-in
customer's org (SH and SPS are two separate Contact records in two separate orgs — check and cache
each separately, **never** sum them). Read `credit_limit`, `outstanding_receivable_amount_bcy`,
`unused_credits_receivable_amount_bcy`. Compute:

```
available_credit = credit_limit − (outstanding_receivable_amount_bcy − unused_credits_receivable_amount_bcy)
over_by = this_order_total − available_credit
```

On `over_by > 0`: block or hold per question 1's answer; error popup quoting the exact LKR amount.
Visibility of "On Hold – Credit Review" restricted to Senuri, the order's placer, CEO, COO, both
GMs. **No Zoho Books call, token, OAuth scope or login anywhere in this diff** — that data source
is closed, not deferred. A ~60-second per-customer cache on the `GET /contacts` call is a cheap
optional optimisation (Zoho's rate limit is 100 req/min/org — one call per checkout is negligible
even uncached); not required for correctness.

**Do not rebuild Zoho's own credit block/warning.** Zoho already enforces this at its own API layer
(Settings → Preferences → Customers and Vendors: "Restrict" or "Show a warning") — the portal's
pre-check exists only so the customer sees a clean message before checkout instead of a raw Zoho
error if the order is actually submitted to Zoho later; Zoho remains the real backstop.

## What NOT to touch

- Do not implement both draft enum sets — pick the one the reconciled delta specifies.
- **Do not call Zoho Books, request a Books token, or add a Books OAuth scope anywhere** — the
  data-source question is closed (Zoho Inventory), not open for a build-time choice.
- Do not build any new credit-limit-blocking logic that duplicates what Zoho's own
  Restrict/Warning preference already does — read the numbers, decide what the portal shows, don't
  reimplement Zoho's enforcement.

## Pipeline gates to follow

Phase 1: `spec-writer` → `plan-critic`. Phase 2: `test-author` → `implementer` → `test-runner` →
`code-reviewer` → `security-auditor` (this touches auth/visibility — required per spec §11) →
`db-migration-guard` if phase 1's delta needs a new migration.

## Tests to write first

- An order whose `over_by > 0` at submission is blocked or held per the answered shape; the popup
  shows the exact computed LKR amount (not a placeholder), computed from `credit_limit`,
  `outstanding_receivable_amount_bcy` and `unused_credits_receivable_amount_bcy` via the formula
  above.
- "On Hold – Credit Review" visible only to the named roles — a key/value scan on seeded data, same
  method as AC1.2/AC1.6.
- SH and SPS credit checks run and are cached independently — a test asserts one org's numbers
  never leak into or get summed with the other's.
- Every new numbered AC from phase 1's delta has a corresponding test.
- A grep/code-search test (or `code-reviewer` checklist item) confirming no Zoho Books endpoint,
  token, or OAuth scope appears anywhere in the diff.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. Never deploy, migrate live data, or push.

## Definition of done

Both `plan-critic` (phase 1) and `security-auditor` (phase 2) return PASS; the gate and its
visibility rule work against seeded test data; no Zoho Books call exists anywhere in the diff.

## Stop and ask conditions — do not start without these answered

1. Block outright, or hold for a named person to release? (Finance/Hazeem)
2. Do "pending dues" mean all unpaid invoices, or only overdue ones? (Finance/Hazeem — the
   credit-limit research recommends all-unpaid as the default, using Zoho's own
   `outstanding_receivable_amount`, but this still needs Finance's confirmation.)
3. Who is Hazeem's backup? (go-live item, doesn't block the build, but confirm before this ships)

**Not a stop condition any more:** where the credit limit lives. That's DECIDED (Zoho Inventory,
25 Sep 2026) — don't ask Finance this question again.

If either 1 or 2 is still unanswered when you're asked to start this step, stop immediately and
report back rather than picking a plausible default.
