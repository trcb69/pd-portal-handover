---
name: so-link-verifier
description: Implement and test SPS-Zoho sales-order linking correctly, using the spec's exact so_key matching rule, for OP-05 (SPS to Zoho SO linking) and OP-12 (Portal Order No enforcement). Use whenever code touches job_so_links, SO search/link/unlink, or the post-import sweep's pending-link resolution. Trigger phrases — "so_key", "link the SO", "link_pending", "SH sales order ref", "sweep resolves", "way B", "way C", "JOBORDER matching".
---

# SO link verifier

## The one rule that matters here

**`so_key` matching is a specific regex, never a naive string compare.** This is called out in the
brief as "the single most-repeated pitfall" for this feature area. Get it wrong and bundle-to-SO
matching silently drops or misattributes records — a defect that won't show up as an error, it'll
show up as a report that's quietly wrong.

```
trim, uppercase, then match ^([A-Z]+-\d+)(\s*-.*)?$
group 1 is the key
```

Worked examples (all real, from the spec and brief — use these as your test cases):
- `JOBORDER-08338 - C` and `joborder-08338` → both match key `JOBORDER-08338` (same SO).
- `JOBORDER-083381` → does **not** match `JOBORDER-08338` (different SO — a naive substring or
  prefix compare would wrongly merge these).
- An SH row carrying the same numeric-looking reference as an SPS job number must **never** tick
  that SPS job — org isolation is tested explicitly (AC1.20).

## Before you write or touch this code

Read `server/services/sweep.js` in the dev repo first — the post-import sweep that resolves
pending links already exists from Release 0. **Extend it, do not duplicate its matching logic.**
If you find yourself writing a second regex or a second matching function anywhere in the
codebase, that's the bug, not a feature.

## The three ways to link, and which ones are allowed

| Way | What it does | Status |
|---|---|---|
| **A** | Automatic linking via the "Portal Order No" field once SH sync exists | Future (OP-16, blocked on SH Zoho admin access) — do not build until that step is scoped |
| **B** | Senuri (or whoever) pastes the Zoho SO number onto the portal order; portal validates it exists in the mirror using the `so_key` rule above | **Build this now** (OP-12) — the current fallback, works without SH sync |
| **C** | Guess the link from customer + date + line match | **Explicitly rejected.** Never implement this. It links the wrong orders. A code-reviewer checklist item, not just a test, per OP-12's own acceptance criteria |

## What to build (OP-05)

- `GET /api/so/search?q=` and `POST /api/jobs/:id/so` (`{action: link | link_pending | unlink,
  salesorder_number}`) against the existing `zoho_*` mirror tables — read-only, already populated.
- Hook the sweep to resolve a `link_pending` reference once its SO appears in a later import,
  writing a system `link` row (`job_so_links`, actor_type = system) and broadcasting an SSE job
  event within poll interval + 5 seconds.
- Unlink must make stage 4 ("Sales order" in the checklist) go not-done immediately; re-linking
  the same SO must make it done again (AC1.10) — this is a state-derivation check, not just a
  table write; verify `server/services/derive.js`'s stage-4 detector reads the current link state,
  not a cached one.

## What to build (OP-12)

- Verify (once, manually, documented — not an automated test since it's Zoho-side config) that
  the "Portal Order No" custom field is mandatory in Zoho SH SO settings, using the user's
  existing Zoho admin access.
- Build the "way B" paste-and-validate fallback: reuse this skill's `so_key` matching, don't
  reimplement it. A pasted number that doesn't exist in the mirror → 400 with a clear message.

## Checklist before this ships

- [ ] The three worked examples above (JOBORDER-08338 with suffix, lowercase, and the
      083381-is-different case) all pass as unit tests against the actual matching function, not
      a re-derived copy of it.
- [ ] Org isolation is tested: an SH-org row and an SPS-org row with the same-looking reference
      never cross-match (AC1.20).
- [ ] No code path anywhere in the diff implements "way C" — grep the diff for any customer+date
      join used for linking purposes; if you find one, it's a defect regardless of who wrote it.
- [ ] The sweep test covers a link resolving **after** the next import, not just an immediate
      link — timing matters here (poll interval + 5s), and L21 (`LATER.md`) flags a sweep-crash
      edge case between resolving and matching to watch for in Release 3.
- [ ] Unlink → relink round-trips correctly against stage-4 derivation (AC1.10), tested, not just
      inspected.

## References

- Spec §6.2 (`so_key` rule, verbatim), §6.3 (`job_so_links` table), §7.2.3.
- `dev/order-portal/02-process-steps.md` OP-05, OP-12 — full acceptance criteria (AC1.10, AC1.11,
  AC1.20).
- `plans/40-order-portal-developer-brief.md` §7 (the ~17–18% fill-rate finding this whole feature
  exists to fix) and §17 (pitfalls, `so_key` listed first).
- `/root/dev/production-dashboard/server/services/sweep.js` — read before extending.
