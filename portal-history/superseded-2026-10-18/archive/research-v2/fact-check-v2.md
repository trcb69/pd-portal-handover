# Fact-check v2 of RECOMMENDATION.md and D-A / D-B / D-C

Checked 17 Oct 2026. Zoho pages fetched live (read-only page fetches, no API calls, no credentials). Business numbers against `../fact-check.md`. Prepared by Abdul Hadhee | IT Executive.

Counts: CONFIRMED 31, WRONG 4, UNVERIFIABLE 6.

## Zoho capability, limit and price claims

| # | Claim | Verdict | Source / note |
|---|---|---|---|
| 1 | 100 requests/min per org; error 44 per-minute, 45 per-day, 1070 concurrency | CONFIRMED | https://www.zoho.com/inventory/api/v1/introduction/ |
| 2 | Daily limits 1,000 / 2,000 / 5,000 / 10,000 / 10,000 by plan; concurrency 5 free, 10 paid | CONFIRMED | same page (Free/Standard/Professional/Premium/Enterprise; Elite not listed) |
| 3 | SPS 7,500/day matches no published tier | CONFIRMED | same page lists no 7,500; the 7,500 itself is the 7 Oct observation (/root/CLAUDE.md), not re-checkable |
| 4 | Scope names items/settings/contacts/transferorders READ, salesorders.CREATE | CONFIRMED | https://www.zoho.com/inventory/api/v1/oauth/ and .../salesorders/ |
| 5 | 20 refresh tokens per user, oldest deleted; access token about 1 h | CONFIRMED | oauth page |
| 6 | Token refresh capped at 10 per 10 min | CONFIRMED | https://www.zoho.com/accounts/protocol/oauth/web-apps/access-token-expiry.html |
| 7 | Self Client: no end-user consent | CONFIRMED | https://www.zoho.com/accounts/protocol/oauth/self-client/overview.html |
| 8 | Sign in with Zoho via OAuth/OIDC exists | CONFIRMED | https://www.zoho.com/accounts/protocol/oauth/sign-in-using-zoho.html |
| 9 | `POST /salesorders` accepts `custom_fields` (customfield_id, value) | CONFIRMED | salesorders docs |
| 10 | List SOs by `salesorder_ids`, up to 200 ids per call | CONFIRMED | salesorders docs (page also marks the param required; filters beyond that not seen, page truncated) |
| 11 | Confirm and void endpoints exist; their scopes UNVERIFIED | CONFIRMED | endpoints listed, scopes not shown |
| 12 | Items list supports `last_modified_time`, per_page default 200 | CONFIRMED | items docs (maximum not stated) |
| 13 | Stock per location comes from the items list (D-C s3.2 `z_item_stock`, 24 x 13-page sweep) | UNVERIFIABLE / doubtful | items docs show `location_*` stock fields in retrieve and bulk-fetch, not in the list response example. Note added to RECOMMENDATION |
| 14 | "Draft" SPS SO created by the API | UNVERIFIABLE | create docs do not say what status a new SO receives. Wording softened in RECOMMENDATION |
| 15 | Creator limits: external calls 100/250/500 per user/day; connections 10/50/100; permission sets 10/50/250; records 25k/100k/250k per user; apps 1/unlimited | CONFIRMED | https://www.zoho.com/creator/pricing-comparison.html (French page; Developer API 250/500/1000 also matches) |
| 16 | Creator USD 8 / 20 / 25 per user per month, annual | CONFIRMED on the preview host only | https://prezohoweb.zoho.com/creator/pricing.html?src=hdd; the main pricing page shows no amounts. Keep "shaky" tag |
| 17 | Inventory plans USD 29 / 79 / 129 / 249 per org per month annual; 2 users on Standard to Premium | CONFIRMED | https://www.zoho.com/inventory/pricing/ (Enterprise includes 7 users). No API charge or API limit stated on the page |
| 18 | Creator connection to Inventory with sales-order scope; per-user vs pooled external-call cap; Creator scheduled export; extra Inventory seat price; SH daily limit | UNVERIFIABLE | the designs already tag these UNKNOWN; I agree |
| 19 | Rizwan-team licensing wording ("each unique person") | UNVERIFIABLE | help.zoho.com KB page not fetched; designs mark it a licence question |

## API-calls-per-day arithmetic

| # | Calculation | Verdict | Note |
|---|---|---|---|
| 20 | D-C SPS: 312+12+1+96+40+48+14 = 523; worst 673; 7.0% / 9.0% of 7,500; hourly sweep saves 156 | CONFIRMED | recomputed |
| 21 | D-C SH: N=3,000 -> 177 (241); N=10,000 -> 387 (451); with inventory cap 677 to 951 | CONFIRMED | recomputed |
| 22 | D-C SPS shared total 415+500+673 = 1,588 = 21% | CONFIRMED | |
| 23 | D-A SH worst 155 (15.5%), average 75; SPS 314 (4.2% / 31%); sum 469 for Creator sizing | CONFIRMED | 862/200 = 5 pages ok |
| 24 | D-B dashboard line: 2 calls x 120 refreshes = 480 | WRONG | = 240. Typical SPS total is then 377 (not 650; the table's own rows sum to 617 with 480), worst 587 (not 830). Corrected in RECOMMENDATION (sections 3 and 4). D-B file itself not edited (scope) |
| 25 | D-B Case B: 120 x 40 = 4,800; 120 x 10 = 1,200; D-B other rows | CONFIRMED | |
| 26 | D-B "35 SOs, about 49 lines" worst day | WRONG | worst day is 35 SOs / 51 lines (../fact-check.md #17). Stock hint worst = 102, not 98. Not quoted in RECOMMENDATION |
| 27 | D-A status follower "about 160 SOs = 1 call" | WRONG | open linked SOs are 217 (../fact-check.md #22; 229 lines is the line count). 217 ids at 200 per call = 2 calls, so 96 not 48, and D-A's SPS total is 362, not 314 (4.8% of 7,500). Not quoted in RECOMMENDATION; D-A not edited |
| 28 | D-B SH: 22 / 62 / ~100 stock reads; totals about 60 and 150 | CONFIRMED (roughly) | 22+10+24 = 56 typical; worst 100+10+24 = 134, "about 150" is a rounded-up allowance |
| 29 | Cost: 31 users 2,976 / 7,440 / 9,300; 20 users 1,920 / 4,800 / 6,000; 40 users 3,840 / 9,600 / 12,000; 5 seats x 20 x 12 = 1,200; LKR at 300 = 0.89 m / 2.23 m / 2.79 m | CONFIRMED | |
| 30 | Effort sums: D-A 9.5, D-B 15.0, D-C 17.25 ("about 17") | CONFIRMED | |
| 31 | Score totals 19 / 29 / 25 | CONFIRMED | |

## Business numbers (against ../fact-check.md)

| # | Claim | Verdict | Note |
|---|---|---|---|
| 32 | 862 customized items | CONFIRMED | #B 01 s4 (926 is names) |
| 33 | 640 end-customer spellings | CONFIRMED with note | 640 over the whole file; 638 on customized lines. Wording corrected in RECOMMENDATION |
| 34 | 7.7 SOs and 11.0 lines per working day; worst 35 SOs | CONFIRMED | #17 |
| 35 | 2,537 catalogue (13 pages) | CONFIRMED | #1; ceil(2537/200) = 13 |
| 36 | 217 open SOs / 229 lines | CONFIRMED | #22 |
| 37 | Snapshots 19 and 28 Sep, about 3 weeks old | CONFIRMED | 19 and 29 days at 17 Oct (19 Sep is nearer 4 weeks) |
| 38 | Dashboard about 415/day, inventory cap 500/day, SPS 7,500 observed, 3-person IT, Y1 300 h | CONFIRMED | /root/CLAUDE.md |
| 39 | "About 9 in 10 lines go to production" (R3) | UNVERIFIABLE | not in ../fact-check.md as stated; routing simulation classes (#13) were only arithmetic-checked, SH stock classes not rebuilt |
| 40 | 31 Oct demo belongs to the goods gatepass | CONFIRMED | /root/CLAUDE.md, 7 Oct |
| 41 | SH and SPS never summed | CONFIRMED | the only sums are per org; D-A's 469 is labelled sizing-only |

## Corrections applied to RECOMMENDATION.md

1. Section 3, D-B: typical SPS load about 650 -> about 380 (worst about 590) (corrected by fact-check).
2. Section 4, D-B dashboard refresh: 480 -> 240 calls/day (corrected by fact-check).
3. Section 3, D-C: added that the 523/day assumes per-location stock in the items list, which the docs do not show (note added by fact-check).
4. Section 6 decision 1: "draft" is UNVERIFIED until the spike (note added by fact-check).
5. Section 5: 640 end-customer spellings qualified (640 file-wide, 638 on customized lines) (corrected by fact-check).

Not fixed (outside the file I may edit): D-B 49 -> 51 lines; D-A 160 -> 217 SOs and its totals. Neither changes the recommendation (D-B still far under 7,500; D-A still scores lowest on cost).
