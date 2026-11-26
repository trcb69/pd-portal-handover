# plan-critic round 6 — PD manager preview (29 Sep 2026)

Reviewed: `2026-09-28-pd-manager-preview.md` body (Rev 5), against Release 0 HEAD `b0cd339` and the
19 Sep SPS Zoho samples. All line numbers are that spec file unless another path is given.

**VERDICT: BLOCK**

**Framing note.** The spec file *already contains* an appended `## Plan-critic round 5` (`:1166-1244`,
VERDICT BLOCK, B1+B2+N1-N6) written by another pass, while the body still says "Rev 5 has not yet had a
plan-critic round" (`:3`) and there is no "Revision 6 changes" table. The body is therefore unrevised
against **two** critic rounds. Round 6 reviewed the body independently; where it reaches the same
conclusion as the appended round 5 it says "confirmed".

## What Rev 5 got right (checked, not findings)

Level 1 (`:181-187`) reads only `zoho_import_runs` — no queue, no per-SO state, no `captured_at` — and
AC34's last sentence (`:521`) tests exactly that. Level 2 (`:189-202`) is per-SO and its `checking` rule
is consistent with refresh reason (b) and with `upsertGuarded`'s skip-if-unchanged behaviour
(`cli/import/upsert.js:18-21`), so an unchanged header does not spuriously flip a job to "checking".
`flag_backlog` is gone from the whole body; the only occurrences left are in the Rev 3/4/5 change tables
and the archived critic text. `flag_status` is consistent across §2 (`:141`), §4 (`:189-202`), §6 JobDTO
(`:427`), AC28 (`:509`) and the UI (`:437`). The §5.5 budget arithmetic is internally correct:
66+38+43+80+20+30+3 = 280 weekday / 340 Sunday (`:390-398`), and 400 − 147 − 130 − 60 = 63 at 00:00
(`:365`) reproduces. No N-series finding from rounds 1-4 was silently dropped. Migration 005 is additive,
passes `server/db/lint-migrations.js:68-84`, is `user_version`-guarded and idempotent on the tenth
restart; its four `INSERT OR IGNORE` alias rows collide with nothing in `002-seed.sql:43-55`. AC37's
rollback assertions are sound.

## Blocking findings

**[B1] (confirmed, round-5 B1) The sync-problem exile is irreversible at 2am.** `detail_fail_count`
survives a code rollback; the only exits are a 24 h night-only retry capped at 10/day (`:320`) or a
`not_found`; Non-goals forbid any admin reset (`:571`). A 45-minute detail-only blip counts one failure
per slot against each queued SO, and the in-cycle outage guard (`:318`) almost never fires because a day
slot has 1-2 queued SOs. **Required:** make the failure counter self-healing (per-SO backoff, or count a
failure only in a cycle that also saw an `ok` detail response, and extend the guard across cycles), plus
one env-driven, idempotent reset lever that needs no DB write.

**[B2] (confirmed, round-5 B2) §3 and the failure table claim a missed change "cannot produce a false
flag"; if V4 fails, they can.** `:167`, `:670`, against V4's "no change is needed either" (`:718`).
**Required:** either make "`last_modified_time` does not move" a return-to-spec-writer outcome of V4, or
state the ~20 h false-`missing` window in §3 and in the failure table and delete the "never false" wording.

**[B3] The 18 new line columns have no field mapping, no type conversion and no shape rules — and §5.2
asserts that no such mapping exists.** `:257` says "There is no second mapping in the sync code… The only
mapping change is one new entry in the `bundles` section", but `:326` writes 18 line fields into a new
table with no map. Three certain consequences:
1. `is_combo_product INTEGER NOT NULL DEFAULT 0` (`:588`) is written by `upsertGuarded`, which lists the
   column explicitly and binds `rec[c] ?? null` on INSERT and UPDATE (`upsert.js:12,21`), so the
   `DEFAULT 0` can never apply: any line whose response omits the key aborts the whole SO transaction
   with a NOT NULL violation.
2. The real payload carries a JSON boolean (`/root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json:90`
   `"is_combo_product": true`). better-sqlite3 refuses to bind a JavaScript boolean, so this throws
   unless the value goes through `mapRow`'s `bool` type (`cli/import/columns.js:26`) — which only exists
   if a column-map section is defined.
3. `division_tag` (`:591`) is not a key lookup: it must be extracted from `line_items[].tags[]` where
   `tag_name='Division'` (`salesorders_since_2026-09-15.json:127-135`). Nothing says how, or what to do
   with a line carrying two Division tags.
And the §5.2 outcome table (`:311-316`) has no class for "the handler threw": a line that reliably throws
leaves `detail_fetched_at` NULL, so refresh reason (a) persists, the SO is re-requested every cycle
forever, `detail_fail_count` never rises, and its jobs sit at "checking" permanently — the very class
Rev 5 set out to close. **Required:** add a `so_line_items` section to `config/zoho-columns.json` with
explicit types (`bool` for `is_combo_product`, `number` for quantities, `raw` for `line_item_id`/`item_id`),
specify the Division-tag extraction, make `is_combo_product` nullable (or guarantee `?? 0`), and add a
fifth outcome class `handler_error` counted exactly like `bad_shape`.

**[B4] Night P1 is unbounded and can eat the entire day's live detail reserve; §5.3 claims otherwise.**
`:365` says "Night P0–P2 are the only detail work not limited by `day_reserve_left`, and they are bounded
by the flags that fall due (P0) and `RECONFIRM_DAILY_MAX` (P2)" — P1 is in neither bound, and `:358`
bounds the night live lane only by `min(live_available, 250 − list calls)`, which at 00:00 is
400 − 0 − 147 − 60 = 193. The trigger is the design's own nightly event: the 02:00 full list rewrites the
header row of every SO whose fields changed, which moves `captured_at` (`upsert.js:18-21`) and is refresh
reason (b) (`:284`); every flag-eligible one lands in **P1**, not P3. Rev 5's answer to round-4
non-blocking 4 capped night **P3** only (`:358`, AC71 `:465`). Effect: one 02:00 slot can spend ~190 calls,
leaving `live_available ≈ 0` at 06:00 for the whole working day. **Required:** bound the night live lane
by `day_reserve_left` as well (or give night P1 its own per-cycle max), fix the §5.3 guarantee text, and
add an AC71-shaped case for P1.

**[B5] The 02:00 header full list is a single point of failure for the whole screen, with no retry, no
first-cycle trigger and no operator lever.** Level 1 requires an `ok` `full_list=1` `so_headers` run within
50 h (`:182-183`); that run happens once a day at 02:00 (`:342`), and any of `rate_limited` (`:647`),
`auth` (`:653`), `upstream` (`:655`), `daily_cap_reached` (`:648`) or `suspect_short_list` (`:660`) kills
it for that day with nothing retrying. Two consecutive misses → `full_list_old` → every counter `null`,
every flag hidden, for every user (`:187`, `:220`, `:232`), with no admin action permitted (`:571`). Two
further inconsistencies in the same place: the **bundles** full list has a "first cycle if none exists"
trigger (`:275`, AC45) but the header full list does not, so a go-live deploy at 10:00 shows
`no_full_header` until 02:00 next morning — even though the first header delta already pages the entire
list (`:264`) but records `full_list=0` (`:272`), so those ~43 calls earn no credit and are spent twice;
and that 43-page first delta breaks day-one `list_reserve`, which budgets 1 call per header-delta slot
(`:349`), a case AC40 never exercises because it specifies "1 page per delta" (`:456`). **Required:** give
the header full list the same first-cycle trigger; credit `full_list=1` when the first delta completes all
pages and passes the 95% rule; retry a non-`ok` full list in the next night slot of the same day; add an
AC for a failed 02:00 full list.

**[B6] (round-5 N1, elevated to blocking) One malformed list row permanently blanks the screen for
everyone, recoverable only by a deploy.** A row without an id or missing a `required` key fails the whole
page and the whole run (`:659`); `W` moves only on an `ok` run (`:262`, `:265`); level 1 needs an `ok`
delta within 45 min (`:184`). The bad row sits inside every later delta window forever: permanent
`delta_stale`, then `full_list_old`, then the banner and `null` counters for every user, with no lever
(`:571`). This contradicts `:367` ("No single SO can hide the screen or another SO's flags") and the lead
decision at `:9`. The spec also defers the required-key check to "as today (`run.js:88`)" (`:257`) without
noticing that `cli/import/run.js:87-88` checks only the **first** row's key names. **Required:** quarantine
the offending row (skip it, record it in the run's `warnings` and a counted metric) and still end the run
**`ok`** so `W` moves — a `warning` status is not enough, because `:262` and `:184` both demand `ok`. Keep
page-level failure only for a missing array or missing `page_context`. Add an AC: a 200-row page with one
malformed row → run `ok`, 199 rows written, `W` moves, `fresh=true`.

## Non-blocking findings

- **[N1] The list path still nulls header fields; only the detail path was fixed.** `:325` makes the
  detail write "only fields whose source key is present"; the delta/full-list path keeps writing
  `rec[c] ?? null` for all of `HEADER_FIELDS_PULL` (`upsert.js:25-29`, `:19-21`). The evidence that the
  list carries flattened `cf_*` keys comes from the **browser internal** endpoint
  (`bundles_and_recent_sos.json:261819-261836`, `tools/zoho-pull-snippet.js:28`), not from
  `zohoapis.com/inventory/v1`. If the OAuth list omits them, every delta silently blanks `cf_job_no`,
  `cf_manufacturing_division` and `cf_order_received_from` estate-wide. Apply the "present source keys
  only" rule to list rows too.
- **[N2] AC8 contradicts the existing meaning of `rows_upserted`.** AC8 (`:468`) asserts
  `rows_upserted = 0` on a repeat run, but `cli/import/run.js:80` sets `upserted += rows.length` — rows
  processed, not changed. Restate AC8 as "no row's `captured_at` changes", or state the differing meaning.
- **[N3] `zoho_import_runs.captured_at` is NOT NULL (`001-schema.sql:79`) and the spec never says what a
  sync run writes there.** Also: a sync `full_list=1` run does move `shippedFresh` and `bundlesDataAge`
  for SPS (`server/services/freshness.js:3-4,22-25`) though the preview no longer reads them — say this is
  intended and harmless.
- **[N4] `composite_item_id` is added to the `bundles` handler unconditionally** (`:257`), unlike
  `sync_state`, which is scoped to `ctx.source==='sync'` (`:259`). A pull bundles import whose rows lack
  the key would null a stored value. Scope it the same way; add an AC that an **SH** bundles import is
  never refused by the `sync_active` guard (`:378` is SPS-only; AC46 does not test SH).
- **[N5] Draft SOs become visible jobs and nobody decided that.** R11 keeps post-cutoff drafts in scope
  (`:25`) and §2's `state` rule (`:139`) makes a draft line `open`. State the intent; exclude or label.
- **[N6] Slot alignment is unspecified.** `:336` says "a `setTimeout` chain"; the whole budget and AC40
  assume alignment to the wall-clock grid (`:340-341`, `:390-391`). Say that the chain aligns to
  :00/:15/:30/:45 and what the first cycle does after a restart at 06:07. Round-5 N6 stands: the 02:30
  Sunday bundles list (`:343`) is not on the hourly night grid.
- **[N7] Missing ACs:** `PROBLEM_RETRY_DAILY_MAX` has none (11 problem SOs → exactly 10 retry calls, none
  in a day slot) while `RECONFIRM_DAILY_MAX` got AC58; `zoho_sync_throttled` (`:647`) has none;
  `zoho_detail_outage` after 3 consecutive `detail_outage` cycles (`:665`) has none (AC69 tests one
  cycle); `counters_complete=true` after the history load has none (AC49 only tests `false`);
  `flags_since` (`:418`) is never asserted.
- **[N8] `:325` understates what the detail object lacks, and `:669` understates the ping-pong cost.**
  The real detail has **no** header `quantity`, `quantity_packed`, `quantity_shipped` or
  `quantity_invoiced` at all — only `total_quantity` (`salesorders_since_2026-09-15.json:70`; compare
  `bundles_and_recent_sos.json:261800-261803`). Extend AC70 to all four. It follows that `detail_sig` is
  permanently list-derived for quantities and detail-derived for the three status fields, so a
  disagreement is systematic: one extra detail fetch for *every* in-scope SO every night, not "at most 1
  per such SO". Make V3(b) sample more than 3 SOs.
- **[N9] Round-5 N2–N5 are still unanswered in the body and round 6 confirms all four:** "History
  loading" never finishes while any never-loaded SO is a sync problem (`:233` vs `:702`);
  `flag_status='checking'` applies to pre-cutoff jobs that can never have chips, and P3 refreshes of the
  ~1,400 old open SOs are not in the §5.5 table; the header-quantity claim at `:120` is backwards (real
  rows include cancelled units in `quantity_shipped`/`quantity_invoiced`,
  `bundles_and_recent_sos.json:261800-261803` vs `salesorders_since_2026-09-15.json:143-149`, so cancelled
  units make an SO look *more* closed); and it is still unsaid whether the sync inherits the 2024 record
  cutoff at `cli/import/run.js:8,99`.
- **[N10] Two one-liners.** `division_source` is undefined when `division_code` is NULL (`:126`, `:425`) —
  say `null`. AC7 (`:455`) covers log output only; the status route returns the raw run `error` string
  (`:421`), which per `run.js:116` is `err.message` — assert that no token, secret or response body can
  reach that column.

## Assumptions the critic could not verify

- Whether the OAuth list endpoint returns flattened `cf_*` keys and whether its default filter returns
  every status — both sampled only from the browser internal endpoint (N1). The second decides whether
  the 95% `suspect_short_list` rule (`:273`) fails every night, which is B5's most likely trigger.
- Whether every line of every SPS SO carries `is_combo_product` (22/22 sampled do).
- Zoho's detail-404 body code (V3a), the full `status` vocabulary (V1), whether `last_modified_time` moves
  on package/shipment/invoice (V4), the org-wide daily quota (Q1b) — all already open.
- How many of the ~1,400+ pre-cutoff open SOs change per day, which decides whether B4 and round-5 N3 bite.

## Simpler alternative considered

**Take the daily header full list off the critical path.** Level 1 currently hard-depends on an `ok` full
list within 50 h (`:182-183`), which creates B5, drives the nightly `captured_at`/signature churn behind
B4 and N8, and costs 43 of the 280 daily calls. Instead: derive level 1 from the deltas only; run the
header full list **weekly** (alongside the bundles one) purely for deletion reconcile; and when the
reconcile is overdue, show that on the admin sync screen, never as a screen-wide blank. That deletes one
blocking finding outright, shrinks two others, removes ~43 calls/day (weekday steady 280 → 237, giving
Sunday real headroom instead of landing exactly on the cap), and loses only the nightly refresh of header
quantities for changes that do not move `last_modified_time` — a case the P0 confirmation rule (`:177`,
AC51) already prevents from producing a false flag.

The two alternatives the appended round 5 offers still stand and are compatible: replace the exile
mechanism with a single `detail_next_try_at` backoff column (fixes B1, deletes three columns, a module, a
constant and four ACs), and drop P2 re-confirmation (deletes `RECONFIRM_DAILY_MAX`, AC57, AC58 and 30
calls/day).

**Status of the simplification: NOT adopted — it is a lead decision waiting on Abdul Hadhee.**
