---
name: visibility-redaction-audit
description: Check that a diff correctly enforces the order portal's visibility matrix (who sees which orders, messages, attachments) and the GM/COO redaction rule, before it ships. Use for OP-04 (triage), OP-08 (credit visibility), OP-09 (notifications), OP-10 (attachments), and always as part of OP-13 (security hardening). Trigger phrases — "who can see this", "portal_visible", "internal note", "redaction", "scope isolation", "requester sees only their own orders", "GM/COO view".
---

# Visibility and redaction audit

## What this is for

The order portal deliberately shows different people different slices of the same order — a
requester never sees job internals or prices; GM/COO see everything but redacted; internal notes
are invisible to requesters and to GM/COO alike. This is tested as one named acceptance criterion
(AC1.2, AC1.6) with a **specific test method** — a key/value scan on seeded data, not a
route-by-route eyeball — because a route-by-route check misses the case where a field leaks
through a generic serializer nobody thought to check. Use this skill whenever a diff adds a new
field, route, or view that could carry order/job data to a screen.

## The rules to check against (spec §5.1, §5.4, §7.2.4, §11)

1. **Requester scope isolation.** A requester sees only their own orders plus their team's. A
   user whose only role is `requester` gets 403 on every non-portal route. No job internals,
   prices, or worker fields leak into anything a requester can reach.
2. **`portal_visible` matrix for attachments/messages** (spec §7.2.4): a requester-uploaded file,
   or one posted with a **public** message, is visible to the requester. A file posted with an
   **internal** note is not — and neither is the note itself, even to a requester who could
   otherwise see the order.
3. **GM/COO see public messages only** — never internal notes, never their files (Rev 5 N5).
4. **GM/COO redaction rule** (spec §5.4): worker identity is replaced with "operator" everywhere;
   `payload_json` is never sent to a GM/COO view; minutes are shown only as division×process×week
   aggregates with **≥2 distinct workers**, otherwise "—" (never a number that could identify one
   worker's output).
5. **Credit-hold visibility** (once OP-08 ships, see the `credit-check-rules` skill): "On Hold –
   Credit Review" is visible only to Senuri, the order's placer, CEO, COO, and both GMs.
6. **Never sum SPS and SH values** in any view a GM/COO or anyone else sees — a data-correctness
   rule that behaves like a visibility rule here because getting it wrong on a shared screen is
   exactly the same class of leak (showing something that shouldn't be shown, just numerically
   instead of textually).

## How to audit a diff

1. **List every new route and every new field a serializer returns.** For each, ask: which roles
   can reach this route, and does the returned payload include anything §5.1/§5.4 restricts?
2. **Don't trust the UI to hide it.** Spec §10: "Scope: checked on the server for every route."
   If a field is hidden in the React component but still present in the API response JSON, that's
   a finding — the server response is the actual boundary, not the rendered screen.
3. **Run the key/value scan, not a route-by-route read.** Seed one order with a full set of
   fields (internal note, worker name, price, job internals), then for each role, fetch every
   accessible response and grep the raw JSON for every value that role should never see. This is
   what AC1.2/AC1.6 actually test — a route-by-route "looks fine" review has repeatedly missed
   leaks elsewhere in this codebase's history (see spec Appendix findings).
4. **Check the message/attachment visibility flip is audited.** `attachments.portal_visible` is
   one of the few fields allowed to change after creation — but only through an audited route
   (spec §6.3). If a diff lets it change silently, that's a finding regardless of whether the
   value ends up correct.
5. **For any GM/COO-facing view this diff adds**, explicitly check the ≥2-distinct-worker
   threshold on any aggregate — a division/process/week bucket with exactly one worker must show
   "—", not that worker's number.

## Checklist before sign-off

- [ ] Key/value scan run for every role against seeded data with a deliberately "leaky" fixture
      (internal note + worker name + price present), not just a happy-path fixture.
- [ ] Every new route checked for server-side role enforcement, not just UI hiding.
- [ ] `portal_visible` changes only via the one audited route; a test proves a direct DB write
      isn't how the app itself changes it (the app itself must use the route too).
- [ ] GM/COO serializer(s) checked line by line against §5.4 — worker identity, `payload_json`,
      the ≥2-worker aggregate rule.
- [ ] No screen or report in the diff sums SPS and SH values together.
- [ ] `security-auditor` has reviewed the diff (mandatory for anything touching auth/visibility,
      per `/root/.claude/CLAUDE.md` §2 table) — this skill's audit is a pre-check, not a
      replacement for that review.

## References

- Spec §5.1 (roles), §5.4 (redaction), §7.2.4 (visibility matrix table), §11 (security), §13
  AC1.2/AC1.6 (the exact test method).
- `dev/order-portal/02-process-steps.md` OP-04, OP-08, OP-09, OP-10, OP-13 — each references this
  matrix.
- `PROJECT-MEMORY.md` §4 rule 7 (security rules), §7 (open credit-visibility question).
