---
name: credit-check-rules
description: Apply the order portal's credit-check formula and gating rules consistently across the spec delta and the build (OP-08). Use when implementing, testing, or reviewing anything that touches credit limits, pending dues, "On Hold – Credit Review", or the over_by calculation. Trigger phrases — "credit check", "over the credit limit", "pending dues", "credit hold", "block or hold the order", "OP-08".
---

# Credit check rules

**Changed 25 Sep 2026:** the data-source question (Zoho Books vs Zoho Inventory) is now **DECIDED**
— Zoho Inventory, no Books access needed. Rewrote the questions list (three → two), added the exact
field/endpoint/formula, and replaced the generic `over_by` formula with the real one mapped to
Zoho's actual fields.

## Status — read this before writing any code

**The credit check is NOT in the frozen state machine yet** (spec §7.2.0 has no credit-hold state
at all). Do not add a credit gate as a bolt-on side effect of `POST /api/orders`. It needs its own
spec delta, reviewed by `plan-critic`, before any code — this is a hard pipeline gate
(`/root/.claude/CLAUDE.md` §2), not a suggestion. If you are asked to "just add the credit check,"
check first whether OP-08's spec delta has actually landed and passed `plan-critic`. If it hasn't,
stop and say so.

## The two questions that must be answered before this skill's formula can be implemented

These are **not this skill's or the developer's call** — they go to Finance (Hazeem's function)
and the COO. If you don't have written answers to both, the build step is blocked, not guessable:

1. **Block outright, or hold for a named releaser?** Changes the shape of the fix — a new
   terminal-ish `credit_hold` state, or a hard 400 at submit with a release queue.
2. **What counts as "pending dues"?** All unpaid invoices, or only overdue ones? Changes the
   formula's aggressiveness. The credit-limit research (below) recommends all-unpaid as the
   default, but this is still Finance's call to confirm.

Check `/root/Project Management/reports/2026-09-25-sps-business-plan/dev/order-portal/questions.md`
under "Finance / credit" for the current answer state before starting.

## Data source — DECIDED 25 Sep 2026, not open any more

**Zoho Inventory, not Zoho Books.** No Books access, login or integration is built. Full research,
every claim cited to a URL or our own export data:
`/root/Project Management/reports/2026-09-25-sps-business-plan/analysis/research/zoho-credit-limit.md`.

- **Field/endpoint:** `credit_limit` on the shared Zoho Contact object, returned by
  `GET /contacts/{contact_id}?organization_id={id}` (Zoho Inventory API v1) alongside
  `outstanding_receivable_amount_bcy` and `unused_credits_receivable_amount_bcy` (use the `_bcy`,
  LKR, versions). Confirmed live in our own SPS org's data
  (`/root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json`,
  `contact.credit_limit`) — currently `0`/unset for the one contact visible there, so before
  go-live someone with Zoho's "configure credit limit" permission needs to set real limits for the
  8 key customers (a data/config task, not new development).
- **SH and SPS are two separate Contact records in two separate Zoho orgs.** Check and cache each
  independently — never sum them (standing project rule).
- **Zoho already blocks/warns on this natively**, at its own API layer, not just its UI (Settings →
  Preferences → Customers and Vendors: "Restrict" or "Show a warning"). The portal's job is to
  *read* the numbers before checkout so the customer sees a clean message — it does not rebuild
  Zoho's enforcement, and Zoho remains the backstop if the portal's own check has a bug.
- **Rate limit:** 100 req/min/org — one `GET` per checkout is negligible. A ~60s per-customer cache
  is a cheap optional optimisation, not a correctness requirement.
- **Who maintains the limit:** Zoho's own permission model (admin or "configure credit limit")
  — a Finance decision made inside Zoho. The portal only ever reads `credit_limit`, never writes it.

## The formula (fixed, 21 Sep decision, now mapped to the real Zoho fields — 25 Sep 2026)

```
available_credit = credit_limit − (outstanding_receivable_amount_bcy − unused_credits_receivable_amount_bcy)
over_by = this_order_total − available_credit
```

If `over_by > 0`: show an error popup quoting the **exact LKR amount**, computed from the real
Zoho Inventory fields above — never a placeholder, never rounded for display in a way that could
disagree with the number Finance would compute by hand.

## Enum reconciliation — implement one set, not two

Two draft enum sets exist and **must not both ship**:
- 20-Sep draft (`CLAUDE.md §17.5`): requester-visible `Released / Rejected / Held until customer
  pays / Cancel / Change order`; reviewer-only `Credit Hold / Released / Rejected / On Hold / Sent
  for review`.
- The spec's actual `order_events` enum (§7.2.0), which predates the credit concept entirely and
  has no credit values at all.

The spec delta (OP-08 phase 1) must pick **one** reconciled set and write it into `order_events`
(or wherever the delta puts it) — check the delta text for which one before writing any code that
checks a status string. If both are still floating when you start building, that's a signal the
delta isn't finished; stop and flag it rather than picking one yourself.

## Visibility rule (fixed — not open)

"On Hold – Credit Review" (or whatever the delta names the state) is visible **only** to: Senuri,
the order's placer, CEO, COO, and both GMs. Nobody else — not other triage staff, not other
coordinators. Test this the same way AC1.2/AC1.6 test the rest of the visibility matrix: a
key/value scan on seeded data, not a route-by-route eyeball.

## Checklist before this ships

- [ ] Both remaining open questions (block-vs-hold; dues definition) have written answers, dated,
      with who answered. The data-source question no longer needs one — it's DECIDED.
- [ ] The spec delta exists, is merged, and has a `plan-critic: PASS`.
- [ ] Exactly one enum set is implemented (grep for both draft sets in the diff; either is fine,
      both is a defect).
- [ ] `over_by` is computed from real Zoho Inventory data (`credit_limit`,
      `outstanding_receivable_amount_bcy`, `unused_credits_receivable_amount_bcy`), never a
      placeholder, at submission time.
- [ ] No code path calls Zoho Books, requests a Books token, or references a Books OAuth scope
      anywhere in the diff.
- [ ] SH and SPS credit checks run and are cached independently — never summed.
- [ ] The visibility test covers all five permitted roles and at least one denied role.
- [ ] `security-auditor` has reviewed this diff (it touches auth/visibility) — not optional per
      spec §11.
- [ ] Hazeem's backup (continuity question 3) is named somewhere in config/docs before go-live,
      even though it doesn't block the build itself.

## Dates

Build 27 Nov – 4 Dec 2026; ships with OP-14's Release-1 go-live: IT test 21–26 Jan 2027, UAT
27 Jan – 10 Feb 2027, full release **11 Feb 2027** (`dev/01b-dated-schedule.md`, row `OP-08`).

## References

- `plans/40-order-portal-developer-brief.md` §5 (the fullest single write-up of this feature).
- `dev/order-portal/02-process-steps.md` OP-08 (the two-phase build: spec delta, then build).
- `dev/order-portal/questions.md` — "Finance / credit" section, current answer status.
- `analysis/research/zoho-credit-limit.md` — the field/endpoint/formula/rate-limit research behind
  the DECIDED data source (new 25 Sep 2026).
- `/root/Production Dashboard/CLAUDE.md` §17.2 step 3, §17.5 (the original, partly-superseded draft).
- `/root/.claude/projects/-root/memory/production-dashboard.md` (the 22-Sep decision dropping the
  Books ask — now the settled, DECIDED position).
