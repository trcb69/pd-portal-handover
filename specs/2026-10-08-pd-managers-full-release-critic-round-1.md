# plan-critic, round 1, on PD managers' full release, Rev 2 (8 Oct 2026)

The plan-critic had read-only tools, so the coordinator saved this report from its hand-back. The verdict and every finding are as returned. The wording is lightly condensed, with nothing removed.

## Verdict: **BLOCK**
C1 and C2 must be fixed in Rev 3 before test-author starts. N1–N5 must be fixed in the same pass. The other findings are recommended. Owner decisions D-A to D-O were treated as fixed.

## Blocking

**[C1] Send next's route model runs backwards against the real data, and §9.3 contradicts AC28** (§9.3, §1e, AC27/28/31).
- The study defines a route as "BOM sub-assembly units, then the item's own unit" (README:53). The line tag is the item's own unit, which is the **last** route step.
  - Example: every `PackPro > CPU` item is tagged "Customized Packing Unit" (routes.csv:19, 21, 38, 39, 54-56).
  - `SHPS > PackPro` is tagged PackPro/MacPro (routes.csv:64).
- §9.3 and AC28 contradict each other:
  - §9.3 ("idx from first from_unit (or home)") gives home=CPU on [PACKPRO, CPU] → idx 1 → suggests R[2] = null.
  - AC28 ("Home ≠ R[0] → suggest R[0]") suggests PACKPRO.
- §1e's list of main hand-offs (PackPro→CPU 32, OPD-Offset→CPU 16, MOBA-Cup→MOBA 12, SHPS→PackPro 9) can never be suggested under §9.3.
- Lids: route `PCU(cup)` but home PCLU (routes.csv:8). AC28 would wrongly suggest PCU, which has no manager.
- AC27/28 use a synthetic route [PSU, MOBA, CPU] with home = R[0], so they hide the problem.
- **Fix:**
  1. Ask the owner: for a two-unit item (e.g. item 4892105000110658771, `PackPro > CPU`, tagged CPU), whose list does the job appear in first?
     - (a) the first unit's: the job starts at R[0];
     - (b) the home unit's: Send next suggests R[0], then the job comes back.
  2. Write one rule that covers both "home matches a later step" and "home not on the route" (suggest null in that case).
  3. Build the ACs from real rows: routes.csv:19, 64 and 8.
  4. Correct §1e.

**[C2] The live nudge cannot work in an MV3 service worker** (§10.5, §0a, AC24, AC67).
- The worker stops after about 30 s without extension events. A `fetch()` stream is not such an event, and R0's 25 s SSE ping (`server/app.js:22`) does not keep it alive. Only WebSocket activity extends the worker's life (Chrome 116+), and adding `ws` would be a new dependency, which is a hard stop.
- Result: chips go stale, the panel falls back to 60 s, and AC24's "within 5 s" is flaky in tests and false in the field.
- **Fix:** choose one:
  - (a) Visible extension frames hold the stream with a short-lived events-only ticket. Content scripts poll `GET /api/changes?since=` through the worker every 30 s while the tab is visible.
  - (b) Drop the stream and refresh every 30 s while the tab is visible.
  - Then rewrite AC24 to ≤ 35 s, and add an E-test that idles the worker for more than 30 s first.

## Non-blocking (N1–N5 required in Rev 3)

- **[N1] No storage for the division-change trail** (§8.0b, §9.1, §9.2, AC21). Fix: in 006, add append-only `job_division_observations(org, line_item_id, raw_tag, raw_header, seen_at)`, written by the sync line handler. Name the step in the Rev 12 list.
- **[N2] V8 fallback math leaves out invoices and pick lists.** With 4 × 840 extra calls, the worst day is about 8,020, over the 7,000 cap.
  - Fix: make V8 cover all four types, and state a 5-minute fallback cadence with numbers.
  - **Coordinator note:** V8 has since been measured (`reports/2026-10-08-pd-zoho-study/v8/V8.md`). Packages 46/46, shipments 45/45 and invoice creation 14/14 bump the SO's `last_modified_time`; invoice edits do not (1/14). Pick lists were not tested. A single SO delta poll (`last_modified_time` watermark plus `sort_column=last_modified_time`) is enough. Keep a periodic full reconciliation for deletions.
- **[N3] Bulk-edit days break 1-minute freshness for real changes.** Fix: in the backlog, put SOs whose list-row signature changed first (quantity_packed, quantity_shipped, quantity_invoiced, status) and SOs where only `last_modified_time` moved last. Add an AC54 case.
- **[N4] 23 of 85 ACs are labels, not criteria:** AC14, 15, 30, 39–43, 47, 48, 50, 51, 53, 55, 56, 58–66, 68.
  - Rewrite them with inputs, action and observable result.
  - Add missing ACs: B-grade "NA" lines labelled "no job no"; no injection on `#/salesorders/<id>/edit` or `/new`; a DPU job lands on Unassigned with `no_manager`.
- **[N5] The fixture pairs DPU with Mubeena + Madushi, against D-N F2.5 and D-O.** Remove it, add a `no_manager` AC, and strike the §1d DPU row.
- **[N6] Hosts injected into Zoho's Ember-managed DOM.** The fake-SPA E-tests cannot catch Glimmer re-render breakage. Fix:
  - (a) Render chips in one overlay on `document.body`, positioned from each row's bounding rectangle.
  - (b) Use a re-rendering harness.
  - (c) Extend manual AC84 (sort, filter, page, switch layout, open/close 5 SOs, zero Zoho console errors compared with a run without the add-on).
- **[N7] `externally_connectable` is absent, so any extension may connect.** Declare `{"ids": []}`. Add a static AC that there is no `onMessageExternal` or `onConnectExternal` listener.
- **[N8] `chrome.storage.session` is readable by extension pages; only content scripts are excluded.** Restate the token-isolation claim and add a static check that the feed bundle never calls it.
- **[N9] Any `inventory.zoho.com` script can frame `block.html` and clickjack writes.** Fix:
  - The worker accepts writes only from its own frame URL **and** a `sender.tab.url` matching `#/salesorders/<same id>`.
  - Frames are registered with a one-time nonce; unregistered frames are read-only.
  - Optional: an IntersectionObserver v2 visibility check.
  - Add E-tests.
- **[N10] Identity is linked by email only, and SPS org membership is never checked.** Check ZUID/email against SPS org users at exchange time, or write the two-system offboarding rule into the runbook and audit. V5 should record whether the email is verified.
- **[N11] The 7,000 hard / 6,000 soft caps and hourly nights depart from F1.1 and F1.2 without sign-off.** 1-minute polling 24 h is 3,304 median and 6,181 max (README:45). Either follow the owner's numbers or ask him with these numbers.
- **[N12] Migration numbering collisions fail only at startup** (`migrate.js:43-68`). Add a lint for unique, contiguous numbers. Update the `/root/CLAUDE.md`, portal resequence and PD-03D notes.
- **[N13] The kill switch conflicts with R0's empty-env rule** (`config.js:24-29`). Keep the origin allowed and use `EXT_DISABLED=1` → 503 `{error:'ext_disabled'}`. Add an AC for the exact rollback command.
- **[N14]**
  - (a) Define `is_return`.
  - (b) Treat the units of earlier ticks as part of `pathUnits`.
  - (c) Add a runbook check for `TRUSTED_PROXY_IPS` and Traefik's IP.
  - (d) Use a company-owned Chrome Web Store publisher account.
  - (e) The ≈211 h estimate leaves out the preview build and Rev 12. Plan about 280–320 h and state the combined path to go-live.

## Could not verify
- `launchWebAuthFlow` on Edge (V3/V6).
- Whether Zoho's CSP allows extension iframes (V1).
- Watermark indexing lag.
- Whether `line_item_id` stays stable when an SO is edited.
- Edge support for `chrome.sidePanel`.
- V7 (session calls likely do not count: 0 API calls in 30 days on 7 Oct, despite daily UI use).

## Simpler alternative
Put every write in an extension-owned side panel. Keep the list chips as display-only overlays. This removes the in-page write iframe, both anchors and the clickjacking surface, and about 25–30% of the add-on hours. The trade-off is that ticks sit **beside** the SO page instead of inside it. This is the owner's call.
