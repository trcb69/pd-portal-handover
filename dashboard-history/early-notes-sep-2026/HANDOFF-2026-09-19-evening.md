# Handoff — 19 Sep 2026, evening (read this first after a compact or restart)

## 0c. UPDATE 22 Sep: READY FOR PRIVATE DEPLOY
- Dev HEAD `b0cd339` (after `9de168e` runbook). Pre-deploy fixes are done: hash guard, append-only 004 (incl. REPLACE block), manifest, linter, empty-env refusal. 136 unit + 7 e2e green.
- code-reviewer PASS and db-migration-guard PASS on the fixes (each after one BLOCK: the hash was written outside the migration transaction; fixed). 001–004 are FROZEN; schema changes from now on are additive.
- Decisions of 21 Sep: private deploy (127.0.0.1 only, SSH tunnel); automatic credit check at order placement; the GitHub repo is private and keeps the real fixture.
- **Next = the user runs `docs/runbook-release-0.md` Part A (A0–A7).** Then verify health and the first import.
- Follow-ups: LATER L34 (linter quoting, before migration 005), L35 (recursive_triggers ON before Release 2), plus L30–L33.
- The five published pages are saved as local HTML in `/root/Project Management/reports/2026-09-19-business-analysis/` (committed ed97c3e) and watched again this session.

## 0b. UPDATE 20 Sep 03:00: Release 0 COMPLETE
- `/root/dev/production-dashboard` HEAD `8886555`. Tasks 1–18 all built and committed. 128 unit tests + 7 e2e green; `tsc` clean; two builds byte-identical; `npm ci` verified on a clean clone.
- Gates: code-reviewer PASS (after one BLOCK: must_reset loop + swallowed admin errors, fixed in `d7eaf55`), security-auditor PASS (ship with follow-ups), db-migration-guard PASS (with changes).
- **Nothing deployed, pushed or tagged.** Runbook `docs/runbook-release-0.md` is marked do-not-run until build-order step 1b.
- Follow-ups: LATER L30 (pull-snippet filter check), L31 (migration items for 2b/1b), L32 (security items for 1b + anonymise the fixture before any GitHub push), L33 (admin UI gaps).
- Next: build-order step 2, the "Release 1 v2" spec delta. Blocked on the user: OK the Q10 security list, and approve an email sender + TOTP dependency.

## 0. UPDATE 20 Sep 00:30: answers received, browser signed out
- **Answers to the open questions** are in `/root/Open Questions 2026-09-19/README.md` (Q1–7, 10, 11 answered; Q8, 9, 17, 18, 19 pending until Monday; Q12–16 **paused**, so don't start the stock system). They're folded into spec §17 (`CLAUDE.md`), LATER L29 (pending items and admin actions) and L27, and memory `user-admin-context`.
- **Q7 draft for approval:** `zoho-helper-userscript-spec.md`. Selectors are TBC and get captured from the live New Sales Order page after sign-in, without saving.
- **Q1 runbook:** `/root/exports/zoho/README.md`, section "Runbook". The persistent profile is the saved state; there's no separate cookie file.
- **Documents stalled at 5,419 of 25,565.** At the compact, Claude Code restarted the browser. The old sign-in lived in the previous isolated browser, so the new persistent-profile browser is signed out. It needs **one code from Rizwan** (ask the user first). After that, restart `move_docs.py` and the bar loop (both stopped) and re-run the document downloader, skipping ids on disk.
- Another Claude process (started 22:17) also has a Playwright MCP on the same profile. Only one session should drive it.


Session: business-analysis + data-download session for Standard Holdings (SH) and SmartPack (SPS).
User = business analyst & advisor (ex IT Exec), working with the CEO, COO and both GMs.
Morning handoff (production dashboard context): `HANDOFF-2026-09-19.md` in this folder; spec in `CLAUDE.md` §17.

## 0. 22:52 update
Documents STOPPED at 5,419 of 25,565 (last file ~22:41): the Playwright browser was reset and Zoho now shows the sign-in page, so the session is lost. Needs one code from Rizwan (ask the user first). Then re-list the inbox and download only ids not already on disk. `sh_full/.docs_blocked` makes the status bar show [!]; delete it when resumed. update_bar.sh now shows speed and finish time; statusline.mjs draws a second bar for any current step with "N of M" (tests 42/42).
Why the session was lost: Rizwan's sign-in lived in the OLD browser (isolated, in-memory, from before the profile switch); it died ~22:41. The new browser uses the persistent profile but has never been signed in, so the NEXT code will survive restarts. User: don't ask Rizwan at night/weekend; wait for a normal working time. Faster plan when resumed: Node-side fetch with the browser context (6–8 parallel, backoff, write straight to documents/<type>/, skip existing), test 20 files first.
Open questions for the user's helper AI: `/root/Open Questions 2026-09-19/` (+ .tar.gz).

## 1. What is running right now (state at 20:39 +0530)

| Job | Where | State | How it saves |
|---|---|---|---|
| SH list pull — **ALL 10 LISTS COMPLETE at 21:41** (409k records; merged files in sh_full/*.json; no more drains needed) (was JS `window.__Prun`) | Playwright tab, signed in as **rizwan@standard-holdings.com**, org 843061977 | (20:44) invoices 81,866 ✓, picklists 76,855 ✓, shipmentorders 78,308 ✓, packages in progress (last drained part_0010); then packages, purchaseorders, creditnotes, salesreturns, transferorders, inventoryadjustments, purchasereceives | Rows sit in `window.__P[<module>].buf` until **drained** with browser_evaluate → `sh_full/lists_parts/part_NNNN.json` (last = part_0005). Then `python3 /root/exports/zoho/scripts/merge_parts.py` writes one de-duplicated `sh_full/<module>.json` each. Drain every ~10–12 min (tab crashed once from memory). |
| SH document download (JS `window.__DLrun`) | same tab | 1,634 of 25,565 files on disk; skips first 290 of the newest-first list | Browser download → `/root/.playwright-mcp/zdoc-<id>.<ext>` → mover moves them |
| Document mover | `python3 /root/exports/zoho/scripts/move_docs.py` (background) | running | moves to `sh_full/documents/<record type>/` using `documents_inbox.json`; writes `sh_full/documents_progress.txt` |
| Status bar | `/root/exports/zoho/scripts/update_bar.sh` | run after each drain | writes progress for session ids 9c32a6c4-… and 6cc42da7-… |

Drain command (browser_evaluate, filename = next part number):
`() => { const out = {}; for (const [k, s] of Object.entries(window.__P)) out[k] = { page: s.page, complete: s.complete, rows: s.buf.splice(0) }; return out; }`
Status command: `() => ({ log: window.__Plog.slice(-4), lists: Object.fromEntries(Object.entries(window.__P).map(([k,s]) => [k,[s.page,s.fetched,s.complete,s.buf.length]])), dl: {phase: window.__DL.phase, done: window.__DL.done, failed: window.__DL.failed.length} })`

### If Claude Code restarts / the browser resets
- Browser tool is now `/root/.config/playwright-mcp.sh` (headless, persistent profile `/root/.config/playwright-profile`). The **next** restart needs **one** code from Rizwan (sign in: email → "Sign in using email OTP" → code goes to rizwan@). After that the sign-in survives restarts.
- **Never** sign out / never call the logout URL (memory `feedback-keep-zoho-session`). Ask the user before triggering a code ("send code").
- Resume lists: re-run the list runner from the module that isn't complete (merged files show which); duplicates are removed by id in merge_parts.py. Resume documents: re-list the inbox and skip ids already in `sh_full/documents/**` and `/root/.playwright-mcp/`.
- If the tab crashes (seen once, memory): navigate to `https://inventory.zoho.com/app/843061977#/home/inventory-dashboard` — cookies survive a tab crash.
- Claude Code's safety checks **blocked**: storing session cookies to a file; editing `~/.claude.json`; entering a code for someone else's account the first time (allowed once the user explained Rizwan sends it himself). Don't work around them.

## 2. Data on disk — index `/root/exports/zoho/README.md`
- SPS (org 843825512, itexe@ — session gone): `native/2026-09-19/sps/` items + stock per warehouse, all 2,456 BOMs, adjustments (12m detail), transfers, POs, receives, bundles, top-20 raw-material workbook; `native/2026-09-16/` line-level Excel exports (SO/invoice lines to 15 Sep).
- SH (rizwan@, all 10 locations): `native/2026-09-19/sh_full/` monthly sales-by-item, purchases-by-item, sales-by-customer (Apr 2024–Sep 2026), stock summary, bills 33,694, document inbox list 25,565 with record links, salesorders 71,982, invoices 81,866, picklists 76,855, (shipments… in progress), documents/.
- Samples: `native/2026-09-19/sh_docs/` printed PDFs per doc type + sample attachments.
- Analysis: `analysis/sps_sales.json`, `analysis/sh_sales.json`, `analysis/exec_dashboard.json`, `analysis/command_centre.json` (built by `scripts/build_command_centre.py`).

## 3. Published pages (private until shared from each page's Share menu; user must share)
All copies: `/root/Project Management/reports/2026-09-19-business-analysis/` (README + 5 HTML, committed 75fe7c9; user pushes vault). Also copies in this folder.
1. SH and SmartPack in numbers — https://claude.ai/artifact/U2vTe941nxGwefa17xFNvB (scratch src `/tmp/claude-0/-root/9c32a6c4-33ea-4970-8145-92206616a329/scratchpad/exec/`)
2. How SH and SmartPack really run — https://claude.ai/artifact/8P1ihtswoaLvjftZMFvj6W (`…/scratchpad/flows/`)
3. Today vs proposed — https://claude.ai/artifact/392Bmw5p4jNxTXVcK6ULUK (`…/scratchpad/asis/`)
4. Stock flow rulebook — https://claude.ai/artifact/41cBz3eUYPsQc1oESeWcFT (`…/scratchpad/stockmap/`)
5. User's stock UI preview — file only (`stock-ui-preview.html`)
Local copies must carry `<meta charset="utf-8">` (garbled "â€"" came from missing charset; fixed and verified clean).

## 4. PUBLISHED v2 (COO shipping, routes, credit-note reasons added 21:50): "SH + SmartPack Command Centre" demo — https://claude.ai/artifact/KdM5u7vbmUgc6yGpQ1FctQ
Publish source: `/tmp/claude-0/-root/9c32a6c4-33ea-4970-8145-92206616a329/scratchpad/cc/command-centre.html` (republish same path to keep URL). Filed as `reports/2026-09-19-business-analysis/0-command-centre.html` (commit 89f00c2) and `/root/Production Dashboard/command-centre.html`.
v2 done: shipping speed (68% same day, 79% by promised date, MTO median 10 d), routes, credit notes by type (LKR 241M, 197M typed "Other"), returns 1,427. PDFs in reports/…/pdf/ (0-command-centre.pdf re-rendered). Rebuild with build_command_centre.py, reassemble template, preview once, mojibake check, republish.
- Purpose: a **static demo to hook the CEO, COO and GMs**; data to 15 Sep 2026; no daily updates; "overkill" polish; must have zero garbled text.
- Data: `/root/exports/zoho/analysis/command_centre.json` (1.06 MB) from `scripts/build_command_centre.py`.
- Template: `/root/exports/zoho/scripts/command_centre.tpl.html` (placeholder `%%DATA%%`); assembled, previewed, verified clean, published.
- Seats: CEO (group, cash), COO (stuck orders, picking heatmap by warehouse/hour, decisions outside Zoho; "arriving next": lead times + credit-note reasons once shipments/credit notes are in), SH GM (Packaging/Specialities/General toggle, items table, desks), SmartPack GM (divisions, recipe margins, end customers, warehouse discipline). Plus search, item & customer pages, All items, All customers, Where it breaks (10), What we're building.
- Rule: no individual staff productivity in GM/COO views (group by desk/warehouse/team) — brief B§2.9.
- Optional inputs asked of the user (defaults used if not sent): names/titles for the seats, logos, each exec's key number, confidentiality (default: everyone sees everything).
- Build steps left: assemble (python replace `%%DATA%%`, escape `</`), preview once with local Chrome (`/usr/bin/google-chrome` via `/root/dev/production-dashboard/node_modules/playwright`), fix, run mojibake check (`/tmp/claude-0/-root/6cc42da7-3649-40a7-bf31-2ada75a1dad6/mojicheck.mjs`), publish as a new artifact (icon "dashboard"), copy to the reports folder with charset wrapper, commit vault. Later: add COO lead times and return reasons.

## 5. Key findings (verified)
- SH 12m (Sep 25–Aug 26) sales LKR 2.17B, +11% YoY; Specialities 46%; est. GP ~LKR 796M (38%) on items with cost; 71,982 SOs; top customer MAS Kreeda LKR 106M.
- SH cash: LKR 324M open, 225M overdue at 15 Sep; median 42 days to pay; 4,775 overdue invoices.
- SH open SOs > 60 days 2,928 (LKR 230M); 869 items over-reserved, 165 negative.
- Docs: 25,565 files; 17,221 in 12m, 5,354 WhatsApp screenshots. Adjustments 91% photographed paper; items/prices approved in WhatsApp group "SPS – Approval for Item creation"; credit notes by email to Hazeem; invoice attachments = customer POs / WhatsApp orders.
- Order-number prefixes = desk + tax type (HTX/HNT Head Office, STX/SNT South, CTX/CNT Central, ATX/KTX, RTX/RNT, HSM/RSM/KSM samples, RIL/HIL loans, INT internal, FPT, EXP, SCRN, HEX). Letters A, K, R unconfirmed (asked user).
- Intercompany: SPS→SH LKR 298M ≈ SH bills 299M (12m); SH→SPS materials 143.8M; SPS retail buys from SH 71.7M; one customer payment into SPS bank filed under SH (asked user).
- SPS: 12m sales to SH LKR 298M; recipe margin ~44%; 47 transfer orders in 13 months; 23 items negative in WIP; 721 finished items in WIP vs 4 in FG; 762 recipes use an inactive component; customised on-time ~57%.
- Zoho stock mechanics: SO reserves (committed); shipment reduces physical; invoice reduces accounting; package/picklist nothing; cancelled-after-shipment breaks stock.

## 6. Open questions for the user
1. A, K, R desk letters in SH order numbers. 2. Customer payment into SPS account filed under SH — normal? 3. Command Centre optional inputs (names, logos, key numbers, confidentiality). 4. Earlier open questions (credit source, notification channel, Saman's step…) — user said they have answers; not yet sent. 5. Zoho admin: user is admin in SPS; SH admin requested (pending) — needed later for the read-only API sync (LATER L19), not for the demo.

## 7. Other state
- LATER.md: L28 (stock procedure confirmations), L19 updated (admin rights).
- Memory updated: user-role, feedback-keep-zoho-session, stock-system-key-customers (demo decision).
- Stock system (Abdullah) scope: SH key-customer buffer stock; waiting on Abdullah's full workbook; preview flaws: typed stock duplicates Zoho; suggested order ignores on-order.
- Production dashboard Release 0: tasks 1–15 committed, 127 tests pass; Task 16 WIP uncommitted (pull snippet reads cookie `zomcsr`, should be `zomcscook`); tasks 17–18 not started.
