# OP-12 — Portal Order No field enforcement

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** this step's date moved later — the shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-12`):** build 11–13 Jan 2027 (**FORCED**: later start, but lands within 2 working days of the original 7 Jan start — removing OP-11 (9 wd) almost exactly cancels the later start). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

Only ~17–18% of SPS orders today carry a usable SH SO reference. The designed fix is a "Portal
Order No" field on the SH sales order. Part (a) below is a Zoho config change the developer
verifies, not code; part (b) is the actual build — the fallback paste-and-validate flow until SH
sync exists.

## Files to read first

1. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §7 in full.
2. `zoho-helper-userscript-spec.md` §4, §5, §5b (in `/root/Production Dashboard/` — draft, not
   approved; read only for the "way B" fallback design, do not build its other fields here).
3. Your own OP-05 work — reuse its `so_key` matching exactly, do not reimplement it.

## Exact scope

**(a) Config, verified not built:** using the user's existing SmartPack Zoho admin access, mark
"Portal Order No" mandatory in Zoho SH SO settings (today: "text, not mandatory"). This is a manual
Zoho-admin-panel action — you verify it by attempting to save a test SH SO without the field and
observing the block, then document that check. You do not write code for this part.

**(b) Build ("way B" fallback):** Senuri pastes a Zoho SO number onto the portal order; the portal
validates it exists in the mirror using OP-05's exact `so_key` matching, then links it.

## What NOT to touch

- Do not implement "way C" (guessing the link from customer + date + line match) anywhere — it is
  explicitly rejected in every source document that mentions it, because it links the wrong orders.
- Do not build the full helper page/userscript from `zoho-helper-userscript-spec.md` — that's a
  separate, unapproved, floating piece of work (part of OP-16's scope), not this step.
- Do not duplicate OP-05's `so_key` regex — import/reuse it.

## Pipeline gates to follow

`test-author` → `implementer` → `test-runner` → `code-reviewer`.

## Tests to write first

- A pasted SO number that doesn't exist in the mirror → 400 with a clear message.
- A pasted SO number that does exist → linked exactly per OP-05's matching rule.
- A code-search / review checklist item confirming no fuzzy customer+date+line matching exists
  anywhere in this diff.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. No migration expected. The Zoho-side config change in part
(a) happens in the Zoho admin panel directly — it is not a deploy of this codebase and not covered
by the `shdeploy`/live-directory restriction, but it is still the human's action to actually click
"Save" in a production Zoho org; you verify the setting exists and document it, you do not need
write access to production Zoho to develop part (b).

## Definition of done

Part (a)'s mandatory-field check is documented (screenshot or written confirmation); part (b)'s
tests pass.

## Stop and ask conditions

- Before marking the field mandatory in Zoho (part a), confirm with Senuri (via the user) that no
  current workflow genuinely lacks a portal order number at save time (see `questions.md`) — if
  there's a real gap (a walk-in, a phone order predating the portal), flag it rather than making
  the field mandatory anyway and breaking her workflow.
