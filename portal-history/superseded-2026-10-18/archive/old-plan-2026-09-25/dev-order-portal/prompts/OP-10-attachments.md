# OP-10 — Attachments and artwork

**Changed 25 Sep 2026 (December dashboard plan, later the same day):** this step's date moved later — the shared developer works the December dashboard track (PSU/Screen Printing) first. See the updated Dates line below.

**Changed 25 Sep 2026 (earlier the same day):** added this step's calendar dates from the published dated master schedule (below).

**Paste this whole prompt to the agentic coding assistant working in `/root/dev/production-dashboard`.**

**Dates (dated master schedule, `dev/01b-dated-schedule.md` / `dev/dated-schedule.json`, row `OP-10`):** build 1–8 Jan 2027 (**FORCED**: later start only). Sub-step — no separate release; ships as part of OP-14's single Release-1 go-live, full release **15 Feb 2027** (target 11 Feb).

## Context

Fully specced, zero open questions. Getting any rule here wrong is a security finding, not a style
choice — read spec §11 and §7.2.4 closely before writing any code.

## Files to read first

1. Design spec §11 (Security — upload rules) and §7.2.4 (`portal_visible` matrix) in full.
2. Design spec §6.3 (`upload_quota`, `attachments` table).
3. `/root/Project Management/reports/2026-09-25-sps-business-plan/plans/40-order-portal-developer-brief.md`
   §10.
4. AC1.14, AC1.30, AC1.6 in spec §13.

## Exact scope

- `POST /api/orders/:id/messages` and `POST /api/jobs/:id/attachments`, multipart upload.
- Allow-listed types checked by **magic bytes**, not file extension: PDF, PNG, JPEG, WebP, XLSX,
  DOCX, AI (PDF-based), PSD, CDR, ZIP. **Never** SVG, HTML, XML, or any script type, regardless of
  the extension on the uploaded filename.
- Only images and PDFs served inline; everything else forced `attachment` (Content-Disposition).
- 25MB/file, 20 files/request; requester daily quotas (50 files / 200MB / 100 messages per Colombo
  day) → 429 past that.
- Random stored names, stored outside the web root, served only through `GET /files/:id` after an
  auth + scope check.
- The `portal_visible` matrix exactly per spec §7.2.4: requester-uploaded or publicly-posted files
  visible to the requester; internal-note files never visible to the requester; GM/COO see public
  messages only, never internal notes or their files.

## What NOT to touch

- No route or logic outside attachments/messages — this step is upload/serve/visibility only.
- Do not serve any file via a direct static path — every read goes through `/files/:id`.

## Pipeline gates to follow

`test-author` → `implementer` → `test-runner` → `code-reviewer` → `security-auditor` (required —
this is an upload feature, per `/root/.claude/CLAUDE.md` §2's delegation table: "Auth, uploads,
secrets, external input, new route" → security-auditor).

## Tests to write first

- AC1.14: 26MB upload → 413; a renamed `.exe` → 415; an SVG or HTML file (even renamed to `.png`)
  → 415, checked by magic bytes not extension; 51st file or 101st message in a Colombo day → 429.
- AC1.6: every cell of the §7.2.4 matrix, both directions, on seeded data.
- A direct filesystem request to a stored file's on-disk path fails (outside web root, verified by
  test, not just code inspection).

## Dev clone only, additive migrations only, never deploy

`/root/dev/production-dashboard` only. The upload directory lives under the dev clone's own data
path, never inside a served static directory.

## Definition of done

All tests above pass; `security-auditor: PASS` recorded before this ships.

## Stop and ask conditions

None expected — fully specced. If Colombo-day boundary logic is unclear, use `shared/time.js`'s
`colomboDate()` (spec §6) rather than deriving "today" from the VPS clock — do not invent your own
timezone handling.
