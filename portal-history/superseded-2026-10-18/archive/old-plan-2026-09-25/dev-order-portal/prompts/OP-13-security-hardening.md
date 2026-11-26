# OP-13 — Security hardening and redaction for Release 1

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** this step's date moved later — the shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-13`):** build 15–19 Jan 2027 (**FORCED**: lands within 2 working days of the original 12 Jan start). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

This step audits and closes gaps across the whole Release-1 diff (OP-03 through OP-10) rather than
building new features. It does not rebuild Release 0's auth — it confirms Release-1 routes don't
weaken it, and applies the GM/COO redaction rule to whatever order-portal reporting this release
ships.

## Files to read first

1. Design spec §11 (Security), §5.2–5.4 (auth, rate limits, CSRF, redaction) in full.
2. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §13.
3. `/root/Production Dashboard/LATER.md` — items L24 and L32 in full (the Release-0 security
   re-audit findings, several of which touch shared middleware this release also uses).
4. `server/auth/middleware.js`, `server/auth/rate-limit.js`, `server/auth/sessions.js` — the
   existing implementations you are auditing, not rewriting from scratch.
5. AC1.2, AC1.14, AC1.30 in spec §13.

## Exact scope

- Confirm scrypt params, session cookie flags, and expiry are unchanged and still applied to every
  new Release-1 route.
- Add rate limiting to any new Release-1 route that bypasses the existing limiter.
- Enforce CSRF (`Origin` header check, including rejecting a **missing** Origin) on every new
  non-GET Release-1 route.
- Verify server-side role checks on every new route added by OP-03–OP-12 — a `requester`-only user
  must get 403 on every non-portal route.
- Apply the GM/COO redaction rule (worker identity → "operator", `payload_json` never sent, minutes
  only as ≥2-worker aggregates or "—") to whatever GM/COO order-portal view exists by this point.
- Close or explicitly defer (with a written reason) LATER.md L24 items (a)–(d).

## What NOT to touch

- Do not rewrite the existing auth system — audit and extend, don't replace.
- Do not add any new feature — if you find a missing feature (not a security gap) while auditing,
  note it, don't build it here.

## Pipeline gates to follow

`code-reviewer` and **`security-auditor` (required — this step exists specifically for the
security-auditor pass spec §11 requires before Release 1 ships)**. Run in parallel with
`code-reviewer` where they examine the same diff, per `/root/.claude/CLAUDE.md` §3.

## Tests to write first

- AC1.2: full scope-isolation test — a requester-only user gets 403 on every non-portal route; a
  key/value scan of every response a requester can see confirms no job internals, prices, worker
  fields, or internal messages leak.
- Re-run AC1.14/AC1.30 against the changes in this step to confirm they still pass.
- A test per closed L24 item confirming the fix (e.g. login-failure rows deduped, no raw password
  stored in `audit_log` from a mistyped username field).

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. Never deploy, migrate live data, or push.

## Definition of done

`security-auditor: PASS` recorded on the full Release-1 diff (not just this step's own changes).

## Stop and ask conditions

- If closing an L24/L32 item would require widening any existing security control (e.g. relaxing a
  CSRF check, widening a rate limit) — stop, this is a hard stop under
  `/root/.claude/CLAUDE.md` §4 ("a fix requires... weakening validation").
