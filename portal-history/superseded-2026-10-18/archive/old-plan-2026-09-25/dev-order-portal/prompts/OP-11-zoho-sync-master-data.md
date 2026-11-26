# ~~OP-11~~ — Zoho read-only sync (SPS) + master-data import — **REMOVED, December dashboard plan, 25 Sep 2026, later the same day**

**Do not paste this prompt to a coding assistant — this step no longer exists in the order-portal
track.** Its content ships ~10 weeks earlier, as `PD-05D` in the December dashboard track, because
the December-live divisions (PSU, SHPS) need live SPS Sales-Order data too, not just the portal
(`dev/01b-dated-schedule.md` §0.5, §4). Use `PD-05D`'s own prompt/spec in the production-dashboard
project instead. The SH-side sync half is unaffected and stays under `OP-16`. Everything below is
kept for reference only.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below — now superseded, see the removal notice above).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates:** none — removed. Its content is `PD-05D`, build 28 Sep – 13 Oct 2026 (`01b-dated-schedule.md` §3).

## Context

Replaces the Release-0 manual-run import CLI with a scheduled, budget-respecting sync, and imports
customer/item master data so the order-submission form's pickers are backed by real data. **SPS
only** — SH sync is a separate, floating step (OP-16), blocked on SH admin access.

## Files to read first

1. `/root/Production Dashboard/BUILD-ORDER-2026-09-20.md` rows 3–4.
2. `server/services/facts.js`, `server/services/freshness.js`, `server/services/mirror-report.js`
   — read before extending; reuse the existing `captured_at` / freshness discipline, do not build a
   second, simpler one.
3. The existing import CLI (`cli/` directory) — the shared upsert functions this sync must reuse,
   not duplicate.
4. `/root/exports/zoho/native/2026-09-19/sh_full/` and `/sps/` (read-only; these are the 19-Sep
   snapshot files feeding item master data until a live SH sync exists).
5. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §17, last bullet (capture-time discipline).

## Exact scope

- A scheduled sync (SPS only) extending the existing shared upsert functions, with its own SPS API
  call budget (config value).
- Customer master-data import: distinct `CF.Order Received from` values from the SPS mirror.
- Item master-data import: from the 19-Sep SH snapshot files (read-only source), flagged as a
  point-in-time snapshot, not a live sync.
- Lookup tables the order-submission form's pickers read from.
- A freshness/"as of [date]" indicator wherever snapshot-sourced data is shown.

## What NOT to touch

- No SH sync — that's OP-16, blocked on SH admin access covering all 10 locations (today only Head
  Office is visible).
- Do not write to any mirror table from a portal route — only the shared upsert functions write
  mirror tables, per spec's mirror/core-table separation rule.
- Do not read or write inside `/root/exports/zoho/` beyond reading the snapshot files listed above
  (read-only, never write there).

## Pipeline gates to follow

`test-author` → `implementer` → `test-runner` → `code-reviewer` → `db-migration-guard` (if any new
mirror table is added).

## Tests to write first

- The sync never exceeds its configured call budget in a single run (tested with a mock API client
  that counts calls).
- Every mirror row written carries `captured_at`, and an older capture never overwrites a newer one
  — tested directly against the shared upsert functions.
- The order form's customer/item pickers are backed by the imported lookup tables, with a visible
  "as of [snapshot date]" flag on snapshot-sourced data.

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. Any new mirror table is a fresh additive migration.

## Definition of done

All tests above pass; `db-migration-guard: PASS` if schema changed.

## Stop and ask conditions

- If the SPS self-client's read-scope list (provisioned by IT/the user, who holds SPS Zoho admin)
  doesn't cover sales orders, customers, or items, stop and ask before building against a scope
  that doesn't exist yet.
