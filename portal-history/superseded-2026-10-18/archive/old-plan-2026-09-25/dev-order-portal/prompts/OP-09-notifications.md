# OP-09 — Notifications

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** this step's date moved later — the shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-09`):** build 22–31 Dec 2026 (**FORCED**: later start; answer deadline moves to 8 Dec 2026). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

Notify the next actor instantly on order creation or any state move — in-app + email, which are
the record. **WhatsApp is explicitly out of scope for this step and this codebase, full stop** —
see "what NOT to touch" below, this is non-negotiable.

## Files to read first

1. `/root/Production Dashboard/CLAUDE.md` §17.2 step 2.
2. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §9.
3. `/root/Production Dashboard/BUILD-ORDER-2026-09-20.md` §6 (the `notifications`-vs-`outbox`
   decision — already made: separate table).
4. `server/services/sse.js` (reuse for in-app delivery, don't duplicate).
5. `/root/.claude/projects/-root/memory/hub-whatsapp-notifications.md` (referenced by name; if you
   cannot read it directly, treat its rule as absolute from this prompt: never build WhatsApp
   sending, never build anything that resembles anti-detection for messaging automation).

## Exact scope

- The `notifications` table from OP-01/OP-02's delta.
- One sender: in-app (SSE, via the existing `server/services/sse.js`) and email (SMTP, once
  provisioned).
- A notification row per state transition from OP-03/OP-04's transition matrix, addressed to the
  correct next actor.
- Retry-then-mark-failed behaviour for email, visible in Admin — never a silent drop.
- A backup-owner config value (not code logic) for the pipeline.

## What NOT to touch

- **No WhatsApp-sending code of any kind** — no library, no browser automation, no queued message
  destined for WhatsApp. If a future WhatsApp channel is approved, it is a separate, already-paused
  project (`hub-whatsapp-notifications.md`) with its own explicit "never build anti-detection" rule
  — this step does not touch it even to prepare for it.
- Do not reuse or modify the `outbox` table — it is a held Zoho write-back queue, a different
  concern entirely; a shared table risks a Zoho write slipping through.

## Pipeline gates to follow

`test-author` → `implementer` → `test-runner` → `code-reviewer`.

## Tests to write first

- Every transition in OP-03/OP-04's tested matrix produces exactly one notification row to the
  correct actor.
- A simulated transient email failure is retried and, after a bounded number of retries, marked
  failed and visible in Admin (not silently dropped).
- A static/code-search test (or a documented manual check) confirming no WhatsApp-related import,
  string, or endpoint exists anywhere in this step's diff.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. SMTP credentials go in `.env`, never committed
(`/root/.claude/CLAUDE.md` §5, "no secrets in source").

## Definition of done

All tests above pass; a named backup owner is recorded in config before this ships (a checklist
item you flag if it's still missing at the end of this step, not something you invent).

## Stop and ask conditions

- No SMTP account exists yet — stop and ask IT (the user) to provision one before building the
  email sender; you can build and test the in-app (SSE) path first if this blocks you, but don't
  fake an SMTP integration against invented credentials.
- No backup owner is named — flag it in your PR, don't block the whole step on it, but don't mark
  the step "done" without noting it's outstanding.
