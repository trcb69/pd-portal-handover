# Production dashboard working demo: UX design

Status: design only, no code. Date 2 Oct 2026. Author: Abdul Hadhee | IT Exec | Standard-Holdings
Contract it must respect: `/root/Project Management/wiki/specs/2026-09-28-pd-manager-preview.md` (Rev 11), sections 1-4 and 6.
Delivery: one self-contained HTML page, published as a private claude.ai Artifact. Read-only, no prices, no network except Google Fonts.

## 0. What the user asked for, and the answer in one picture

User words: "make the UI more user friendly more visual not bunch of texts scattered use proper animations ui skills".
The earlier mockups failed because every fact was a sentence. The rule for this demo:

> Every fact is a shape first and a word second. A manager should know "what is late and what is stuck" from across the room, before reading anything.

```
 Phone, one column                               Laptop, two panes
 +--------------------------------+              +-----------------------------------------------+
 | DEMO ribbon (snapshot)         |              | DEMO ribbon                                   |
 | Hi Ishan        [avatar] switch|              | Hi Ishan   chips: OPD PACKPRO RWU PSU  [fresh]|
 | Zoho data as of 14:05  (o)     |              +--------------------+--------------------------+
 | [ Due 3d ][ Past due ]         |              | 5 tiles in one row | job table (compact)      |
 | [ In prod ][ Not shipped ][ Doc]|             | pipeline flow      | or cards (toggle)        |
 | pipeline: Made>Packed>Shipped>Inv|            |                    |   click row -> drawer    |
 | chips: OPD PACKPRO RWU PSU     |              | (left rail sticks) |   slides in from right   |
 | job card                       |              +--------------------+--------------------------+
 | job card ...                   |
 +--------------------------------+   Drawer on phone = bottom sheet (90% height).
```

## 1. Visual direction: "press-room, not dashboard"

Subject world: a packaging converter. Offset presses, die-cutters, carton labels, pallet tags, CMYK ink, registration marks, perforation lines, corrugated board, conveyor belts, shipping marks.

Ideas taken from that world (each carries meaning, none is decoration):

| Motif | Where it appears | What it encodes |
|---|---|---|
| Registration mark (circle with cross-hair) | Loading spinner, "checking with Zoho" state, empty states, avatar fallback ring | "being aligned / checked". It is the press operator's own symbol for "not lined up yet". |
| Carton label (die-cut notch top-right, dashed perforation under the header) | Job card shape | One job = one label on one carton. Notch holds the due-date badge. |
| Conveyor belt (a thin belt line with small cartons riding it) | Pipeline chart | Produced > Packed > Shipped > Invoiced is a physical flow. Cartons are the count. |
| Ink-strip colour bar (a 4-block CMYK-style strip) | Under the DEMO ribbon, and as the progress track skin | Brand flourish, once per screen only. |
| Station dots on a belt | Documentation stepper | Each document is a station the job passes. Skipped station = gap in the belt. |

Avoid (from the artifact-design list): cream + serif + terracotta; near-black + acid green; Inter/Space Grotesk; purple gradients; emoji as markers; rounded-lg everywhere; accent rail on rounded cards. The label shape uses a small 4px radius and a cut corner instead; no left accent rail. Icons are drawn inline SVG (stroke 1.75, 20px grid), no emoji.

Boldness goes in one place: the five counter tiles and the conveyor pipeline. Everything else is quiet.

## 2. Token plan

All colour is a token on `:root` (light), redefined for dark under `@media (prefers-color-scheme: dark)` guarded `:root:not([data-theme="light"])` and again in `:root[data-theme="dark"]`. `body` sets an explicit background. No literal colours in components.

### 2.1 Colour

Neutrals carry a cool blue-grey bias (press-sheet paper and plate steel), not cream.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | #EEF1F4 | #11161B | page ground |
| `--surface` | #FFFFFF | #1A2128 | cards, drawer |
| `--surface-2` | #E4E9EE | #232C35 | tracks, chips, tiles at rest |
| `--ink` | #14202B | #E7EDF2 | primary text |
| `--ink-2` | #46586A | #A9B7C4 | secondary text |
| `--ink-3` | #6B7C8C | #8496A6 | muted labels (still 4.5:1 on surface; validate) |
| `--line` | #CBD4DC | #34414D | hairlines, perforation |
| `--accent` (cyan ink) | #0B6F96 | #55C2E6 | selection, focus, primary action, "done" fill |
| `--accent-soft` | #D5ECF5 | #17323F | selected tile/chip ground |
| `--late` (magenta ink) | #C81E4B | #FF6B8B | past due, missing-document callouts (status colour, always with icon + word) |
| `--late-soft` | #FBE1E8 | #3D1A25 | callout ground |
| `--warn` (yellow ink) | #8A5A00 text / #F2B705 fill | #FFD34D | due in 3 days, "checking" |
| `--warn-soft` | #FFF1C7 | #3A3012 | ground |
| `--ok` | #1D7A4F | #5FD39B | closed, invoiced complete |
| `--pending` | #8A97A3 | #66747F | not tracked yet, not seen |

Rules from the dataviz skill that apply here:
- Status colours (`late`, `warn`, `ok`) are reserved. They never act as a series colour. They always ship with an icon and a word.
- The pipeline and progress bars use ONE hue (accent) light to dark. Late/missing overlays are the only second hue.
- Division identity is not colour. A division chip is its code text ("PACKPRO") plus a one-letter glyph; ten divisions cannot be told apart by hue, and managers know the codes.
- Text never wears a series or status colour except the status word inside its own callout (that is `--late` on `--late-soft`, checked at 4.5:1).
- Build step: run `validate_palette.js` (dataviz skill) on the accent / late / warn / ok set against `--surface` for both modes before publish. The GM heat bars need the late vs missing pair to pass the colour-blind separation check; if it fails, the missing series gets a diagonal hatch fill (texture), which also makes it safe in print and forced-colours.

### 2.2 Type

| Role | Family (Google Fonts) | Fallback | Use |
|---|---|---|---|
| Display | Barlow Condensed 600/700 | "Arial Narrow", Arial, sans-serif | counter numbers, screen titles, division codes. Condensed stencil-like caps match carton print. |
| Body | Barlow 400/500/600 | system-ui, sans-serif | everything else |
| Data | IBM Plex Mono 500 | ui-monospace, monospace | job numbers (SO numbers), quantities in the drawer, "seen by sync" times |

Scale (rem, phone / laptop): counter number 3 / 3.75, screen title 1.75 / 2.25, card title 1.0625, body 0.9375, label caps 0.75 with 0.06em tracking, mono 0.8125. Tabular numerals on every number. Headings `text-wrap: balance`. Minimum tap target 44px.

### 2.3 Shape, spacing, depth

- Side gutter 16px (phone) / 24px (laptop). Gaps from an 4px base: 4, 8, 12, 16, 24.
- Card radius 4px with a 14px diagonal cut on the top-right corner (CSS `clip-path` polygon; the due badge sits in the cut). Tiles radius 6px. Chips fully round.
- Depth: one soft shadow only on the drawer and the coach-mark. Cards separate by `--line` and ground contrast, not shadow.
- Perforation: a 1px dashed `--line` between card header and strip.

### 2.4 Motion tokens

```
--ease-out:   cubic-bezier(0.22, 1, 0.36, 1)      /* entrances, settle */
--ease-in-out:cubic-bezier(0.65, 0, 0.35, 1)      /* position swaps */
--ease-spring:cubic-bezier(0.34, 1.4, 0.64, 1)    /* one overshoot, tiles/pop only */
--d-micro: 120ms   --d-short: 220ms   --d-med: 360ms   --d-long: 600ms   --d-count: 900ms
--stagger: 40ms (cards) / 70ms (tiles, pipeline stations)
```

Only `transform` and `opacity` animate (plus `stroke-dashoffset` on SVG and width through `transform: scaleX`). No layout-property animation. Nothing animates forever, except the registration-mark spinner and the shimmer while data is genuinely loading.

## 3. Information model the demo needs (so the UI is honest)

Demo data is a snapshot. Sources: `/root/dev/production-dashboard/test/fixtures/zoho/sps-detail-22.json` (22 real orders with packed/shipped/invoiced per line) and `/root/exports/zoho/native/2026-09-16/Sales_Order.xlsx` (division tags, header division). Expand to about 60 jobs by sampling real lines from the export; where the export has no packed/shipped/invoiced quantities, derive them from the 22-order patterns and mark the whole data set "Snapshot, 2 Oct 2026". No prices, no amounts, no payment fields are loaded into the page at all.

Per job the page holds: `so_number, job_no, customer, item, division_code, division_source, division_conflict, qty_ordered, qty_produced, qty_packed, qty_shipped, qty_invoiced, due_date, stage states, seen_at per stage, flags[], flag_status, other_lines[]`. Same names as spec §2 so the real build can swap the data source.

Derived counters and flags use the spec rules literally (§4 table). The demo script computes them in the browser from the snapshot, with `today` fixed to the snapshot date so the numbers never drift.

### 3.1 Paper Straw "closed short" (to confirm, no rule proposed yet)

Earlier drafts said straw orders ship about 95% (14,800 of 15,500) and proposed a closed-short rule. The data does not support that. In `sps-detail-22.json` the 15,500 straw line has 700 cancelled, so effective quantity is 14,800 and 14,800 shipped closes it under the spec rule (`shipped >= qty_effective`). In `Sales_Order.xlsx`, of 530 invoiced straw lines of 10,000 units or more, 314 are fully invoiced and 216 are short but fully explained by cancelled units; none are short and uncancelled.

Question to confirm with Ishan and Samitha: do straw orders ever ship short with no cancellation recorded? Only if yes does the spec need a closed-short state (threshold, invoiced-equals-shipped condition, who confirms). The demo no longer has a closed-short rule or toggle, so its numbers equal the spec contract.

## 4. Screens and components

### 4.1 App shell (always present)

```
+------------------------------------------------------------+
| DEMO  Snapshot of Zoho data from 2 Oct 2026, 14:05. Nothing here is live.  [x? no]   <- ribbon, sticky
| ▮▮▮▮ ink strip (4 blocks, 3px)                                                         |
| Hi Ishan ▾ (avatar)       (o) Zoho data as of 14:05     [?] [sun/moon]                 |
+------------------------------------------------------------+
```

- **DEMO ribbon (item 7).** Sticky at the top. Hatched diagonal background in `--warn-soft` (warning-tape feel), text "DEMO. This is a snapshot of Zoho from 2 Oct, 14:05. Nothing you see updates." Cannot be dismissed (no close button). A second line, on tap of "What is this?", expands inline: "Real orders, no prices. Nothing you do here changes Zoho."
- **Freshness bar (item 7).** Under the header: a short pill "Zoho data as of 14:05 (Colombo)" with a 12px dot. Dot states: green "fresh", amber "older than usual", grey "not current". In the demo the state is selectable from the `?` menu ("Show what stale looks like"); stale replaces the pill with the grey banner "Zoho data is not current. Flags and counters are hidden." and every counter shows "—". This shows managers what happens when sync is down, as the spec §4 requires. Pill also shows relative age ("21 min ago") computed against the snapshot clock, which is frozen, so it reads "snapshot".
- **Theme toggle** cycles system / light / dark. Remembered per viewer (localStorage in try/catch).
- **Person chip** top-left reopens the picker as a sheet (not a page reload).

### 4.2 Screen 1: "Who's looking?" picker (item 1)

Full-screen on first load, then reachable from the chip.

```
 Who's looking?
 Pick a person to see their screen.

 ( R )  Ranga        OPD · MOBA · MOBA-P · FPP · CPU          Manager
 ( I )  Ishan        OPD · PACKPRO · RWU · PSU                Manager
 ( M )  Mubeena      SHPS                                     Manager
 ( S )  Samitha      All divisions                            GM
 ( A )  Admin        All + Unassigned + Sync                  Admin
```

- Five large rows (phone) or five tall cards in a row (laptop). Avatar = 56px circle, initial in Barlow Condensed, ring in `--line`; the ring is drawn as a registration mark (cross-hair ticks at N/E/S/W).
- No photos. Colours: avatar fill uses `--surface-2` for all; identity is the name and initial, not hue.
- Under each: the division codes as tiny chips and a role word. A "Not a real login. Demo only." line under the list.
- Selected state: on tap the row's avatar scales to 1.06 with the ring rotating 90 degrees (220ms), the other rows fade to 40% (180ms), then the home screen enters (see 5.1). Choice stored in localStorage; the next visit opens straight to that person with the chip to switch.
- Samitha and Admin rows are labelled "Sees every division". The picker has no password step and the demo says so.
- OPD is shared by Ranga and Ishan (division_pairs). Both see OPD Offset jobs; the home shows a small "Shared with Ranga" tag on OPD chip for Ishan and "Shared with Ishan" for Ranga.

### 4.3 Screen 2: "My jobs" home (item 2)

Order top to bottom on phone: ribbon, header + freshness, counter tiles, pipeline, division chips + search/sort, job list. On laptop: tiles in one row, pipeline beside or under, list below.

#### 4.3.1 Counter tiles

Five tiles, left to right in the order of urgency: **Past due**, **Due in 3 days**, **In production**, **Made, not shipped**, **Documents missing**. (Spec names kept in the tooltip; "Produced, not shipped" is shortened to "Made, not shipped" for plain words.)

```
 phone 2-col grid (5th tile spans full width)     laptop 5-col row
 +-----------+ +-----------+
 | PAST DUE  | | DUE 3 DAYS|     tile = icon (20px) + label (caps 0.75)
 |   9   (!) | |   4       |     + number (Barlow Condensed 3rem)
 | jobs      | | jobs      |     + tiny context line: "oldest 14 days" / "next: Fri"
 +-----------+ +-----------+
 +-----------------------+
 | DOCUMENTS MISSING 3   |
 | being checked: 2      |       the spec's "being checked / sync problem" note
 +-----------------------+
```

- Tiles are real `<button>`s with `aria-pressed`. Tap = filter the list to those jobs; tap again = clear. Active tile: `--accent-soft` ground, 2px `--accent` outline, check glyph at the corner. Only one tile active at a time; stage selection (4.3.2) combines with it (AND), and the active filters appear as removable chips ("Past due x") above the list, with "Clear all".
- Tile accent: Past due and Documents missing carry a 4px top edge in `--late` only when their count > 0; at 0 the tile reads calm (neutral edge, a small check, the word "none"). Due in 3 days uses `--warn`. In production and Made-not-shipped are neutral-accent.
- Count-up (see 5.1): numbers roll from 0 to value once at first view of a person, 900ms ease-out, tabular numerals. On later filter changes numbers do not re-count; only a 120ms tick (scale 1 to 1.04 to 1) if the value changed.
- Tile numbers are totals for the user's visible jobs, unaffected by the active filter (matches the spec: counters are over visible jobs). The pipeline also ignores the filter except for the division chip.
- Counter note when history is loading: "(history loading)" muted, plus a shimmer on the numbers.

#### 4.3.2 Pipeline flow (conveyor)

The only chart on this screen. Purpose: where do my open jobs sit? Answers "how many are made but not packed, packed but not shipped, shipped but not invoiced".

Stages for the chart (job-level, each open job counted once, at the furthest stage it has fully reached):
**Not made yet > Made > Packed > Shipped > Invoiced.** "Not made yet" is a quiet first box so totals add up to all open jobs; the user asked for produced, packed, shipped, invoiced, so those four are the loud ones.

```
  Not made yet     Made          Packed        Shipped       Invoiced(closed soon)
  [  18  ]  ───►  [  11  ]  ───►  [  6  ]  ───►  [  9  ]  ───►  [  4  ]
  ▇▇▇▇▇▇▇▇▇        ▇▇▇▇▇          ▇▇▇           ▇▇▇▇            ▇▇
   cartons ▫▫▫▫    ▫▫▫           ▫▫            ▫▫▫             ▫
                    ▲ 2 stuck (red notch)         ▲ 3 stuck
```

- Drawn as inline SVG: five stations on a belt line (a 2px line with chevron arrows), each station a rounded-square box with the count in Barlow Condensed, under it a bar whose length is `count / max` on one shared scale (zero-based, bars anchored at the baseline with 4px rounded ends, 2px gap), and small carton glyphs (max 8, then "+n").
- Colour: all bars `--accent` in a single hue, light to dark from first to last stage (sequential, one hue). "Stuck" overlay: the part of a stage that has a shown missing-document flag is drawn as a hatched `--late` cap on the bar, with a small "(!) 2" tag. That is the only second colour. Hatch means it is not colour-alone.
- Labels: every station has its value printed (direct labelling; there are only five). Axis lines omitted; no gridlines needed because values are printed. No legend box beyond a two-item inline key: "solid = jobs here", "hatched = a document is missing".
- Interaction: tap or arrow-key a station to filter the list to jobs at that stage; the station gets the same active style as a tile. Hover (laptop) shows a tooltip "6 jobs packed, not yet shipped. 2 are missing a document." Tooltip is also a focus-visible description for keyboard and screen readers. A "Table view" link under the chart swaps the SVG for a five-row table (accessibility and the dataviz rule that a table view exists).
- Phone: the SVG scales (viewBox 360 wide); at 400px the station boxes are 56px with 12px belt between. Labels are 12px minimum. Does not scroll horizontally.
- Empty (0 open jobs): the belt draws but boxes are dashed and empty, with the line "Nothing open right now."

#### 4.3.3 Division chips and list controls

- A row of chips from the user's divisions, each with count: `ALL 38`, `OPD 17`, `PACKPRO 12`, `RWU 6`, `PSU 3`. Single select; "ALL" default. Chips scroll horizontally inside their own container (not the page) with edge fade; 44px high.
- Shared-division mark on OPD (see 4.2).
- Sort menu (one control): Due soonest (default), Most late first, Most missing first. Search box with placeholder "Job, customer or item"; collapses to an icon on phone.
- View toggle (laptop only): Cards / Table. Phone is always cards.
- A "Closed" toggle chip at the end of the row to show closed and closed-short jobs (off by default).

### 4.4 Screen 3: job cards and the compact table (item 3)

#### 4.4.1 Card (phone default, laptop option)

```
 ┌───────────────────────────────────────╲  <- cut corner holds due badge
 │ PACKPRO · 3PL-2610-0114      [ Due Fri 3 Oct ]
 │ Ocean Gold Pvt Ltd                        
 │ Pizza box 12" kraft, 2-colour             
 ├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   (perforation)
 │  ●────●────●────◐────○────○ ... documentation strip (see 4.4.2)
 │  SO  Made Pick Pack  Ship Inv
 │ Shipped  ▇▇▇▇▇▇▇▇▇░░░░  9,200 of 15,500
 │ [(!) Package missing · 3 days]         (callout, only if flagged)
 └────────────────────────────────────────
```

- Header line: division code chip (Barlow Condensed caps), SO/job number in Plex Mono, due badge in the cut corner.
- **Due badge**: rule in text and colour and icon. `Due Fri 3 Oct` neutral; within 3 days `--warn` with clock icon "Due in 2 days"; past due `--late` solid with alert icon "5 days late". Shipped in full: green check "Shipped". No due date: grey dashed "No due date" (spec-observed: 52% of goods POs lack one, so it is a normal state).
- **Progress bar**: shipped vs ordered. Track `--surface-2`, fill `--accent`, 2px surface gap, 4px rounded end, right-aligned label "9,200 of 15,500" in Plex Mono; a faint second tick marks packed quantity (a 2px notch) so "packed but not shipped" is visible on the same bar. Never any currency. Percent shown only above 2rem text size in the drawer.
- **Callout** (missing document): a full-width pill in `--late-soft` with `--late` icon, plain words: "Nobody has packed this. Bundled 3 days ago." Max one line, two flags stack as two lines. Flag texts (copy deck in section 7).
- Two other states replace the callout line, always in the same place so cards align:
  - `checking`: "Checking with Zoho..." with the shimmer (4.4.3).
  - `sync_problem`: "Can't read this order. IT has been told." with `--warn` icon.
- Card is a button; whole card tappable (opens drawer). Focus ring 2px `--accent` offset 2px.
- Staggered entrance on first paint and on filter change (5.2).

#### 4.4.2 Documentation strip (stepper)

A belt with station dots. One station per stage of the job's division, in `division_stages` order (so PSU and RWU omit Pick list, SHPS differs; see `002-seed.sql:33-41`). Stages 1, 2, 3, 9, 11 are always "not tracked yet".

| Strip state | Dot | Connector to next | Label colour |
|---|---|---|---|
| `done` | solid `--accent` circle, white check | solid accent line | `--ink` |
| `partial` | half-filled circle (left half accent) | line accent for filled share, dashed after | `--ink` |
| `not_done` and a shown flag | `--late` ring, "!" glyph, pulses once (5.3) | dashed `--late` | `--late` word only inside callout |
| `not_done` no flag | empty ring `--line` | dashed `--line` | `--ink-3` |
| `n_a` | small dash, no dot | line passes through | hidden on phone |
| `not_tracked` | hollow dot with a dotted ring, tiny "?" | dotted | `--ink-3`, tooltip "Not tracked yet" |
| `detected` (Bundle) | solid accent diamond | accent | `--ink` |
| `not_detected` (Bundle) | grey hollow diamond with "no bundle seen" in the tooltip, never red | dashed `--line` | `--ink-3` |

- Icons per stage (20px outline, inline SVG): Artwork = image frame; Item photo = camera; Job card = clipboard; Sales order = document with lines; Bundle = stacked boxes; Pick list = checklist; Package = closed box with tape; Shipment = truck; Inventory adjustment = scales; Sales invoice = receipt; Purchase bill = receipt with arrow in. Icons sit inside the dots on laptop and the drawer; on the phone card the strip shows the dots only (11 icons do not fit in 368px), with the three stages that matter (Pack, Ship, Invoice) labelled and the rest unlabelled. Tapping a dot on the card opens the drawer scrolled to that stage.
- On the phone the card strip collapses the five "not tracked yet" stages into one grey group "5 not tracked yet" with a small count, so the belt shows only the six detected stages (SO, Bundle, Pick, Pack, Ship, Invoice) at roughly 48px each. In the drawer all stages show.
- Never colour-only: every state has a distinct dot shape (filled, half, ring+!, hollow, dotted, diamond) so it works in greyscale.

#### 4.4.3 "Checking with Zoho..." shimmer

- Used when `flag_status = checking` and while a fresh load is pending (first 600ms of the demo to let the viewer see the state; thereafter only on cards that are `checking` in the data, about 3 of 60).
- Visual: the callout line is replaced by a 14px-high skeleton bar with a diagonal ink-strip gradient sweeping left to right (1400ms linear loop, `transform: translateX`), a rotating registration-mark icon (1 turn per 1600ms), and the words "Checking with Zoho...". The strip and progress bar stay visible and still, because the spec says the strip always draws from stored data.
- It is `aria-busy` with a visually hidden "Checking with Zoho".
- Reduced motion: no sweep, no rotation; a static registration mark and a static light bar with the same words.

#### 4.4.4 Compact table (laptop only, toggle)

Columns: Division | Job / SO | Customer | Item | Due | Shipped (mini bar) | Strip (six small dots, no labels) | Flag icon. Row height 44px, sticky header, zebra none (hairlines only). Sort by clicking a header (icon shows direction). Row hover lifts background to `--accent-soft`; click or Enter opens the drawer. Wider than 900px only. Horizontal overflow, if any, scrolls inside the table container.

### 4.5 Screen 4: job / sales-order drawer (item 4)

Opens from any card or row. Laptop: 520px panel from the right with a dim scrim. Phone: bottom sheet at 92% height with a grab handle. Closing: scrim tap, Esc, swipe down (phone), X button. Focus is trapped inside while open and returned to the card on close. Background does not scroll.

```
 ┌ PACKPRO · SO-26-04412                              [x]
 │ Ocean Gold Pvt Ltd · Pizza box 12" kraft, 2-colour
 │ [ Due Fri 3 Oct ]   [ 5 days late ]  ...
 │
 │ WHAT'S MISSING AND WHO DOES IT NEXT        <- plain-language box, first thing
 │ ┌───────────────────────────────────────────────┐
 │ │ (!) Packed 15,500, shipped 9,200.               │
 │ │ Next: Ilham (Stores) records the shipment.      │
 │ │ Waiting 4 working days. Checked 14:05.          │
 │ └───────────────────────────────────────────────┘
 │
 │ DOCUMENTS                                  big stepper, vertical on phone
 │  ● Sales order ........ seen by sync  29 Sep 09:12   15,500
 │  ◆ Bundle ............. 3 Oct ...
 │  ● Package ............ seen by sync  30 Sep 11:40   15,500 of 15,500
 │  ◐ Shipment ........... seen by sync  1 Oct 15:02    9,200 of 15,500
 │  ○ Sales invoice ...... not seen yet
 │  ? Artwork, Item photo, Job card, Inventory adj., Purchase bill: not tracked yet
 │
 │ OTHER LINES IN THIS ORDER   (read-only, other divisions)
 │  line chips: RWU Label roll 5,000  |  SHPS ...   each with tiny strip, no click-through
 └
```

- Header shows the same badges as the card at a larger size.
- **"What's missing and who does it next"** is the first block, always present. For an on-track job it says "Nothing is missing. Next step: shipping." The "who" comes from the flow in `/root/Production Dashboard/CLAUDE.md` section 5.3: creator > division > manager > receiving coordinator, then coordinator > Ilham (Stores, shipment) > Darshani (invoice, ITN). Mapping used by the demo:
  - package_missing: "Receiving coordinator records the package."
  - shipment_missing: "Ilham (Stores) records the shipment."
  - invoice_missing: "Darshani records the sales invoice."
  - Nothing flagged but behind: "Waiting on production."
  The names are demo copy from CLAUDE.md 5.3 and are shown only where those roles are known; if the real build lacks a mapping the line reads "Next step: shipment (Stores)".
- **Large stepper** vertical on phone and horizontal on laptop; each row has the stage icon (24px), the name, state in words ("Done", "Partly done 9,200 of 15,500", "Not seen yet", "Not tracked yet"), the date labelled **"seen by sync"** with a small (i) explaining "The time our sync first saw it in Zoho, not the time it was done." The quantity per stage in Plex Mono.
- Stage 5 Bundle: shown in the same belt but "no bundle seen" is grey, never red.
- **Other lines**: a horizontal chip list (phone: vertical list) of every other line of the SO. Each line shows its division chip, item, ordered qty, mini strip, and a lock icon with "Read-only. Belongs to <division>." Lines of the user's own division are marked "Yours". The current line is marked "This job". Tapping another own line swaps the drawer content with a 220ms cross-slide, the other lines do nothing.
- Sync problem: the top block becomes "We can't read this order right now. IT has been told. The strip shows the last data we had." with `--warn`.
- Closed short: top block says "Closed short. Shipped 14,800 of 15,500 (700 short). Invoiced 14,800. No action needed."

### 4.6 Screen 5: GM view (item 5)

Same shell with person Samitha. Home shows all jobs. Above the five tiles (all divisions), a "Divisions at a glance" panel.

```
 Divisions at a glance             sort: Most late ▾          [ Bars | Table ]
 OPD     ▇▇▇▇▇▇▇▇▇▇▇▇ 12 late   ▨▨▨▨ 4 missing    17 open
 PACKPRO ▇▇▇▇ 4 late             ▨▨ 2 missing     12 open
 PSU     ▇ 1 late                (none)           3 open
 SHPS    ▇▇▇ 3 late              ▨ 1 missing      9 open
 MOBA ... (zero rows in grey)
 No division ... (links to Admin board, for GM only a count)
```

- Horizontal paired bars per division (late = solid `--late`, missing documents = hatched `--late` at 60% or hatched `--warn`; choose by the colour-blind check in 2.1). Shared zero baseline, one value scale across rows, value labels printed at bar ends, division code at left in Barlow Condensed, total "open" at right in `--ink-3`. Bars 12px with 4px rounded ends and a 4px gap between pair bars.
- Tap a row = filter the list to that division (same chip filter). Rows with zeros stay visible and dimmed so a division is never silently missing; this answers "is OPD quiet or just not shown?".
- Division split of shared OPD: OPD rows are shown once with a note "shared by Ranga and Ishan", not doubled.
- Divisions with unnamed manager (MACPRO per the 29 Sep finding) appear as "OPD - MacPro (no manager yet)" in italics with a link-chip "Unassigned board" visible to Admin only.
- Table view link flips to a plain 5-column table (division, open, late, missing, closed short).
- Entrance: bars grow from the baseline (5.4).
- Phone: each division becomes a two-line row (code + totals on line one; the bar pair on line two, full width).

### 4.7 Screen 6: Admin "Unassigned" board (item 6)

Admin only. Same shell; the person chip says Admin. A tab bar appears: **My jobs** | **Unassigned** | **Sync**.

```
 Unassigned jobs                      total 31
 ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
 │ No manager   │ │ Conflict     │ │ No division  │
 │     14       │ │      9       │ │      8       │
 │ Division has │ │ Line tag and │ │ Neither line │
 │ no owner     │ │ header differ│ │ nor header   │
 └──────────────┘ └──────────────┘ └──────────────┘
 (tap a column = jump to its list)
 NO MANAGER (14)
   OPD - MacPro   9 jobs  ...  [chip list of jobs]
   Paper Cup Unit  5 jobs
 CONFLICT (9)
   SO-26-04388  tag: PACKPRO | header: OPD
 NO DIVISION (8)
   ...
```

- Three kanban-style columns (laptop) or three stacked collapsible groups (phone). Each header carries the big count (Barlow Condensed) and a one-line plain definition. Cards within are compact job rows with the reason chip and, for conflicts, both values side by side ("Line says PACKPRO. Order says OPD."). Zero-count groups show a green check and "Nothing here."
- Grouping inside "No manager" is by division, with a bar showing job count per division on a single scale. The MacPro finding appears as a note: "Most of these are OPD MacPro lines. No manager owns this division yet." (taken from the 29 Sep division analysis).
- Demo only: read-only; the buttons "Assign" are absent. A muted line "Assigning a manager is done in the admin settings, not here." keeps the demo honest.
- **Sync tab** (small): the freshness line, last successful header run, bundles run, and "History loading X of Y" as a progress bar. Optional for the first demo; include if time allows, since the spec names it.

### 4.8 Screen 7: first-visit guided tour, "How to read this" (item 8)

A 20-second coach-mark overlay for first-time viewers, runs once per person and is re-openable from the `?` button ("Show the tour").

Five steps, each 3 to 4 seconds if auto-play, or tap Next. Auto-advance can be switched off by tapping anywhere on the card; progress is a thin bar at the top of the callout and a "1 of 5" counter. Skip is always visible and keyboard focused first.

| # | Target | Copy (max 12 words) |
|---|---|---|
| 1 | Counter tiles | "Five numbers tell you how today looks. Tap one to see those jobs." |
| 2 | Pipeline | "Each box is a stage. Jobs move left to right. Red hatching means a document is missing." |
| 3 | First job card | "One card is one job. The dots are the documents Zoho should have." |
| 4 | Missing callout | "Red means a step was skipped. It says what and who does it next." |
| 5 | Freshness pill + ribbon | "This is a snapshot. The real screen refreshes from Zoho by itself." |

- Overlay: dims the page to 60% with a rounded cut-out ("spotlight") around the target, a registration-mark pointer, and a callout card (surface, shadow) placed above or below the target without leaving the viewport; on phone it docks to the bottom. Spotlight transition between steps 360ms ease-in-out (position + size via transforms).
- Buttons: "Next" (primary), "Back", "Skip tour". On last step "Got it". No dialogs from `alert`; everything is DOM.
- Appears automatically 500ms after the first home render for a new person, and only if `localStorage` says not seen (try/catch; if storage is unavailable it shows once per page load). Does not trigger on the picker.
- Reduced motion: no auto-advance, no spotlight sliding (instant cut), only Next.
- Esc closes; focus trapped; screen reader announces "Step 2 of 5".

## 5. Animation spec

Everything below disables or simplifies under `prefers-reduced-motion: reduce` (section 5.7).

### 5.1 Entrances after picking a person

Sequence (total about 1.4s, nothing blocks interaction):

| t (ms) | What | Property | Duration | Easing | Stagger |
|---|---|---|---|---|---|
| 0 | Picker sheet exits | opacity 1>0, translateY 0>-8px | 180 | ease-out | none |
| 120 | Header, freshness pill | opacity 0>1, translateY 8>0 | 220 | ease-out | 40 |
| 200 | Five tiles | opacity 0>1, translateY 16>0, scale .97>1 | 360 | ease-spring (one soft overshoot) | 70 per tile, left to right |
| 200 | Tile numbers | count-up from 0 | 900 | ease-out (cubic-out) | starts with its tile |
| 520 | Pipeline belt | belt line draws left to right via `stroke-dashoffset` | 600 | ease-in-out | none |
| 560 | Pipeline boxes | scale .9>1, opacity 0>1 | 220 | ease-out | 70 per station |
| 700 | Pipeline bars | `scaleX` 0>1 from the left of each bar, transform-origin left | 360 | ease-out | 70 per station |
| 700 | Pipeline cartons | translate from belt start to slot, opacity | 200 | ease-out | 20 per carton, capped at 8 |
| 900 | Division chips | opacity, translateX 8>0 | 180 | ease-out | 30 |
| 1000 | First 8 cards | opacity 0>1, translateY 12>0 | 280 | ease-out | 40 |

Cards beyond the first 8 render at rest with no animation (never hide content behind an observer; the page must be complete at rest). Count-up numbers start from 0 only on first paint; the final value is also written into the element text and the accessible label immediately, so a screenshot still shows the right numbers.

### 5.2 Filtering and sorting

- Tile or stage or chip tap: the pressed element scales .97 for 90ms then settles (ease-out 120ms). Active outline fades in 120ms.
- List update: cards that leave fade to 0 over 120ms; remaining cards slide to new positions with FLIP (transform, 260ms ease-in-out); cards that enter fade/slide in 220ms ease-out with 30ms stagger (max 8). A "N jobs" counter above the list rolls to its new number (120ms).
- If the list becomes empty, the empty state (section 6) fades in after 160ms.

### 5.3 Missing-document callouts: pulse once

- When a flagged card first enters view (IntersectionObserver, threshold 0.5) the callout does a single attention pulse: its `--late` ring expands outward 0 to 8px and fades (box-shadow is avoided; use a pseudo-element with `transform: scale(1)>(1.12)` and `opacity .5>0`), 700ms ease-out, once. The "!" dot on the strip does the same at the same time. Never loops. It plays once per card per session (tracked in a Set); returning to the list does not replay.
- In the drawer, the "What's missing" box has no pulse; instead its icon draws in (stroke-dashoffset, 360ms).
- Content is complete at rest: the pulse is an enhancement and the callout is fully visible before and after.

### 5.4 Drawer

- Laptop open: panel `translateX(100%) > 0`, 360ms ease-out; scrim opacity 0>0.45 over 220ms. Close: 240ms ease-in-out (faster out than in).
- Phone open: bottom sheet `translateY(100%) > 0`, 360ms ease-out; swipe-down follows the finger 1:1 and settles with ease-out; releases past 30% height or fast flick closes.
- Content stagger inside the drawer, starting 120ms after the panel starts: header, missing box, stepper rows (30ms stagger per row), other lines (30ms). Stepper connectors draw in `scaleY/scaleX` 0>1, 180ms per segment, sequentially (about 700ms total), dots pop (scale .6>1, ease-spring, 160ms) as the connector reaches them.
- Switching to another line in the same order: current content slides out left 160ms, new content slides in from right 220ms.
- Focus moves to the drawer title on open and back to the opener on close.

### 5.5 GM bars and Admin board

- Division bars: grow from baseline `scaleX 0>1`, 420ms ease-out, 50ms stagger per row, hatched bar starts 60ms after its solid sibling. Value labels fade in at the bar's end when the bar stops (140ms).
- Re-sort: rows reorder by FLIP, 320ms ease-in-out.
- Admin big counts: count-up 600ms, group cards enter with 70ms stagger, 280ms ease-out.

### 5.6 Closed-short switch and stale-mode

- Switch flips: the affected cards badge swaps with a 160ms cross-fade; the tiles roll their numbers with a vertical odometer (digit column translateY, 420ms ease-in-out, 30ms stagger per digit). A one-time toast (non-blocking, bottom) reads "Past due 9 > 6. 3 Paper Straw jobs closed short." 3.5s, `role="status"`.
- Stale mode: tile numbers fade to "—" (160ms), the freshness dot changes colour with a 220ms transition, the grey banner slides down 220ms ease-out. Restoring reverses.

### 5.7 Reduced motion

`@media (prefers-reduced-motion: reduce)`:
- All entrance transitions become instant (opacity only, 1ms), no translate, no scale, no stagger.
- Count-up shows the final value at once.
- Belt draw, bar grow, connector draw, pulse, shimmer sweep, spinner rotation: removed. The spinner becomes a static registration mark; shimmer becomes a static light bar.
- Drawer and sheet appear with a 120ms opacity fade, no slide. Swipe-to-close still works (user-driven).
- Spotlight tour: no auto-advance, hard cut between steps.
- FLIP reorder: instant.
- The pulse is replaced by a permanent 2px `--late` outline on the callout (it is always visible anyway).
- Theme change and focus rings are unaffected.
- Implementation: one `matchMedia` flag read at start and on change, applied to JS-driven animations (count-up, FLIP); CSS animations are wrapped in the media query.

## 6. Empty, error and edge states

| Situation | What the viewer sees |
|---|---|
| No open jobs for this person | Registration mark drawn at centre, "No open jobs. Everything is shipped and invoiced." Tiles show 0 with a check; pipeline shows empty dashed belt. |
| Filter returns nothing | Mini belt illustration, "No jobs match." and a primary "Clear filters" button. Active filter chips remain visible. |
| Search finds nothing | "Nothing for 'xyz'. Try a job number or customer." with a clear-search button. |
| Counter is 0 | Number "0" calm style, caption "none". Not red. |
| Zoho data not current (stale mode) | Grey banner "Zoho data is not current. Flags and counters are hidden." Counters "—", callouts hidden, strip and quantities still drawn (spec 4). |
| History loading | Thin progress strip under the header "Loading older orders: 120 of 410", tile numbers marked "(so far)", cards loaded so far visible. |
| Job `checking` | Shimmer line, see 4.4.3. Not counted in Documents missing; the tile's note says "2 being checked". |
| Job `sync_problem` | Warn-coloured line "Can't read this order. IT has been told." Note on tile "1 sync problem". |
| No due date | Dashed grey badge "No due date". Never counted late or due soon. Sorted last in "Due soonest". |
| Impossible due date (for example year 9170) | Treated as "No due date" with a small warning icon and tooltip "Date looks wrong in Zoho." (September monthly report found TOS-2609121-GALLE dated 9170.) |
| Job with no division (GM/Admin only) | Division chip reads "No division" in `--ink-3` dashed outline. Managers never see these (spec 1). |
| Division conflict | Chip reads the line division with a small swap icon; drawer explains "Line says X, order says Y." |
| Quantities cancelled | Progress bar uses effective qty; drawer shows "Ordered 15,500, cancelled 500". |
| Shipped more than ordered | Bar caps at 100% with a "+200" tag; no red. |
| Closed short | Grey "Closed short 95%" badge, hidden from counters, shown under Closed filter. |
| Order with one line only | "Other lines" block reads "This order has one line." |
| Very long customer or item name | Wraps up to two lines on cards, then ellipsis; full text in the drawer. |
| 400px width | One column; chips scroll inside their container; the drawer is a bottom sheet; tile grid 2-col; no horizontal page scroll. |
| Dark mode | Own token set, hatch patterns retuned, shadows replaced by lighter surface steps. |
| No JS storage | Tour shows once per load; theme follows system. Nothing crashes. |
| Print / screenshot | Rest state already complete; no content depends on animation. |

Errors in the demo itself: the data is bundled in the page, so there is no network error state. If the embedded JSON fails to parse, show the one fallback "The demo data could not be read. Reload the page." with a reload button.

## 7. Copy deck (plain words)

- Tiles: "Past due", "Due in 3 days", "In production", "Made, not shipped", "Documents missing".
- Stage labels (short, full): Artwork, Item photo, Job card, Sales order, Made (Bundle), Pick list, Packed (Package), Shipped (Shipment), Stock adjusted (Inventory adjustment), Invoiced to SH (Sales invoice to SH), Bill from SPS.
- Flags on the card (two lines max):
  - package_missing: "Made 3 days ago, not packed yet."
  - shipment_missing: "Packed, not shipped for 4 days."
  - invoice_missing: "Shipped, not invoiced for 2 days."
- Flags in the drawer ("what's missing"): the same plus the who-next line from 4.5.
- "Seen by sync" tooltip: "When our sync first saw this in Zoho."
- Freshness: "Zoho data as of 14:05" and in the ribbon "Snapshot, not live".
- Buttons: "Show jobs", "Clear filters", "Next", "Skip tour", "Got it", "Switch person".
- Avoid: "sync_state", "quarantine", "legacy", "full list", "reconcile", any jargon from the spec. No prices, no totals in money, ever. IT scope only: nothing about payment status or overdues in invoices (an invoice stage says only "Invoiced" or "Not invoiced yet").
- Sign-off (footer, small): "Abdul Hadhee | IT Exec | Standard-Holdings".
- Author voice: first person where the page speaks about itself ("I show jobs from a snapshot"), not "we".

## 8. Accessibility and quality bar

- Contrast: text 4.5:1, large numerals and icons 3:1, in both themes; run the dataviz `validate_palette.js` on accent, late, warn, ok against `--surface` and `--bg` in light and dark and record the result in the build notes.
- Never colour alone: late = icon + word + hatch; stage states = dot shape; division = text.
- Keyboard: all tiles, stations, chips, cards, rows are tab stops with visible 2px focus ring; Enter and Space activate; Esc closes drawer, tour, picker sheet; arrow keys move among pipeline stations and between tiles.
- Screen reader: tiles announce "Past due, 9 jobs, filter, pressed/not pressed"; the pipeline has an SVG `<title>`/`<desc>` and the table alternative; the drawer is `role="dialog"` with `aria-modal`; toasts `role="status"`.
- Targets 44px; no hover-only information (tooltips duplicate in the drawer).
- No `alert`, `confirm`, `prompt`. No downloads, no print button. External resources: only Google Fonts CSS/files. Any library (none needed; hand-written SVG and CSS are enough) would load from cdnjs with a pinned version.
- Size well under 1 MB with the embedded snapshot.
- Fonts have fallback stacks so a font failure does not shift layout badly (`font-display: swap`).
- `<title>`: "Production Dashboard" (user's own name for it); the demo state lives in the description and the ribbon.

## 9. Build notes and order of work (for the next step)

1. Data: script reads the two sources above, builds `snapshot.json` (about 60 jobs, 5 people, flags, other_lines, a handful of `checking`, one `sync_problem`, three PSU closed-short candidates, two no-due-date, one conflict, four MacPro no-manager jobs) and inlines it. Compute counters in the page with the spec rules, snapshot date fixed.
2. Tokens, shell, ribbon, picker.
3. Home: tiles, pipeline SVG, chips, cards, drawer.
4. GM bars, Admin board.
5. Tour overlay, closed-short switch, stale-mode switch.
6. One preview pass at 400px and desktop, light and dark, with reduced motion emulated; one fix pass; publish private.

## 10. Open decisions for the user (the demo will make these visible)

1. Closed-short rule for Paper Straw: threshold (suggested 90% shipped, 95% tolerance, 5 working days) and whether it applies to PSU only. Needs a spec change to `state` in §2 and Rev 12; not decided here.
2. Which Zoho field decides a division (Q2): the demo uses the spec's tag-first rule with header fallback.
3. The `OPD - MacPro Unit` division has no manager, so its jobs will sit on the Admin "No manager" list until one is named.
4. Names in the "who does it next" line (Ilham, Darshani) come from `/root/Production Dashboard/CLAUDE.md` 5.3; confirm they should be shown to managers.
5. Whether "Not made yet" belongs in the pipeline chart (the spec has no such counter; it is added so the chart totals equal open jobs).

Abdul Hadhee | IT Exec | Standard-Holdings
