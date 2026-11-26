# Brief: the 3 open decisions, and the rules now built into the systems

Written 29 Sep 2026, for Abdul Hadhee before the call with the department managers.
Plain language on purpose. Nothing here needs a technical answer from the managers except item 2.

---

## Part 1 - the three things waiting on a decision

### 1. Read-only Zoho access for SmartPack (an admin action, not a discussion)

**What it is.** A "Self Client" created in Zoho's API console: a username-and-password equivalent that
lets our dashboard *read* SmartPack's sales orders and assemblies automatically, every few minutes, and
never write anything back.

**Why it matters.** Without it the managers' screen can only show a file someone exported by hand. With
it, the screen fills itself from Zoho all day. It is also the only way to answer four technical questions
the design depends on - what Zoho calls each order status, whether it can sort by "last changed", what it
returns for an order that was deleted, and what the assemblies list contains. Four settings in the sync
are guesses until those are answered.

**What to do.** Steps are written out at `/root/dev/production-dashboard/docs/zoho-self-client-setup.md`.
It is about ten minutes. Two things to watch: pick the **SmartPack** portal at the end (picking Standard
Holdings is the usual mistake - the system would then read the wrong company), and the secret goes
straight into the server file, never into a chat, a report or a commit.

**Second half, needs a look in Zoho settings.** What is SmartPack's **real** daily API call limit? We have
been planning against 1,000 calls a day and that number is unverified. Three things will share it - the
dashboard sync (400/day) and two inventory services (500/day each). If the real limit is lower, the first
load of history takes longer, and I size the sync down before it is built rather than after.

---

### 2. Which field decides who sees a job (this one is for the managers)

**The shape of it.** Every production job on the managers' screen comes from a SmartPack sales order. The
screen has to route each job to one manager. Zoho stores the division **twice**:

    Sales order  ->  "Manufacturing Division"   (one value for the whole order)
        +
    Each item row ->  "Division" reporting tag  (one value per item)

Since we agreed one job = one item line, only the tag is per job. But on 2 of the 22 orders I sampled the
two disagree, and the disagreement is not harmless.

**The real example.** Orders JOBORDER-08597 and JOBORDER-08592, both 16 Sep 2026, both 12oz paper cups:
the order header says **Paper Cup Unit (PCU)**, the item row says **MOBA Unit**. The job numbers are
OPD-series (OPD6704, OPD6705). Full evidence, with where to find both fields in Zoho, is in
`evidence/Q2-division-conflict-example.md` in this same folder.

**What I recommend.** The item tag decides; the order header is used only when the item has no tag (the
Rewinding Unit orders have none). Two reasons: it is the only per-item source, and if the header won,
those two jobs would have **no manager at all** - see the next point.

**What only the managers can answer:**
1. For paper cups like these, is the work MOBA's (punching machines) or PCU's? The tag and the header
   disagree and only the floor knows which is right.
2. **Five units have no manager named:** Paper Cup Unit, Paper Cup Lid Unit, Digital Printing Unit,
   Paper Plate Unit, Cake Wrapper Unit. Today's mapping covers PSU, Offset, PackPro, Rewinding (Ishan),
   Screen Printing (Mubeena), OPD, MOBA, Food Product Processing, Customized Packing (Ranga). Any job that
   lands in one of the five is invisible to everybody. Who owns each?
3. Who corrects a wrong division tag in Zoho when the screen flags a conflict?

---

### 3. Refresh design: one nightly full sweep, or continuous with a weekly sweep (a yes/no for you)

**How it works today in the design.** Every night at 2am the system re-reads the entire order list from
Zoho. That nightly sweep is what tells the screen "my data is trustworthy". During the day it only reads
what changed.

**The problem the review found.** If that one 2am run fails - Zoho rate-limits us, the token expires, the
connection drops - nothing retries it. Two failed nights in a row and **every manager's screen goes
blank**: no counters, no flags, just a grey "data is stale" banner, with no button anyone can press at
2am to fix it. It also costs 43 of our 400 daily calls, and it creates knock-on work that can eat the
next day's budget.

**The alternative I recommend.** Judge freshness from the small continuous updates instead, and run the
full sweep **weekly**, only to catch deleted orders. If the weekly sweep is overdue, that shows as a line
on my admin screen - never as a blank screen for a manager.

**What it buys:** removes one of the six must-fix findings outright, shrinks two more, and frees ~43 calls
a day (280 down to 237), which turns a budget that currently lands exactly on the cap into one with room.
**What it costs:** header quantities refresh continuously rather than being re-swept nightly - a case the
design already protects against producing a false alarm.

This is a build decision, not a business one. I need your yes or no; the managers do not need to hear it.

---

## Part 2 - rules now built in, that you should know before the call

These were decided across the specs. If any one of them is wrong, it is much cheaper to know now.

**The managers' screen**
- **One job = one item line on a SmartPack sales order**, not one whole order. An order with three items
  is three jobs and can reach three different managers.
- **The screen never writes to Zoho.** Every action is a read. The only thing we ever send is the login
  handshake.
- **Managers see only their own divisions.** The GM sees all of them, as a viewer.
- **Only jobs created from go-live day onward raise "document missing" flags.** Everything older is shown
  as history, so nobody opens the screen on day one to a thousand red marks.
- **Orders older than 180 days are "legacy"** - visible behind a filter, kept out of the counters, loaded
  last. Roughly 1,400 orders are open right now and 170 of them are from 2024.
- **When the data is stale, flags are hidden rather than shown.** The rule is: never show a red mark we
  are not sure of. A stale screen says so at the top.
- **A missing bundle is shown but not flagged** in the first version - we have not yet proved how often a
  bundle is genuinely absent versus simply recorded late.
- **Thresholds, changeable in settings, not code:** package missing after 2 working days, shipment after
  3, invoice after 2. Working days come from the calendar screen, currently Mon-Fri.
- **Jobs that cannot be routed** (no division, or a division with no manager) go to an admin list - mine -
  rather than disappearing.

**The order portal (later release, same system, same login)**
- Everyone who orders or updates uses it; it replaces the WhatsApp order group.
- The credit check reads the customer's credit limit from **Zoho Inventory** - no Zoho Books access needed.
- Customers get no access at all.

**The inventory decision system**
- **Zoho owns the data; our system owns the decisions.** Reads only, with one exception that is gated and
  not in this phase (writing a reorder level back).
- **An LLM may only propose a rule. A different person approves it.** Approver cannot be the creator -
  the database itself refuses it.
- **Rule precedence:** item+customer beats customer, beats item, beats category, beats the company
  default. "Never stock this" beats every cover rule.
- **Always show a shortage, even when we are unsure** - marked "unverified" rather than hidden.
- **Honest warning, now decision 7:** in phase 1 the availability calculation will **under-count** work in
  progress, because the job list only starts filling from 28 Sep with no back-entry of the ~228 open jobs.
  Either somebody re-enters that backlog before January, or phase 1 ships knowing this part is half-blind.
  That is a real business call and it now has an owner line waiting for a name.

**Across everything**
- **SmartPack and Standard Holdings are separate companies. Their sales are never added together** in any
  report. (SmartPack sells about 99.9% to Standard Holdings, so a combined figure would be double counting.)
- **I never deploy, restart, migrate or push.** I produce the commands; you run them.
- **Nothing is built until its design passes an independent review.** Both designs were reviewed this
  morning and both were blocked - 6 findings on the dashboard, 10 on the inventory notes. Those are being
  fixed now, then re-reviewed. This is the gate doing its job: every one of those would have been found
  after the build instead of before.

---

## Part 3 - what I would ask the managers while you have them

1. The five units with no manager - who owns each? (PCU, PCLU, DPU, PPU, CWU)
2. Paper cups: MOBA or PCU?
3. Does SmartPack pack, ship or invoice on **Saturdays**? If yes it is a settings change, not a code
   change - but the late-counting is wrong until it is set.
4. Are the 2/3/2 working-day thresholds for "package/shipment/invoice missing" about right, or too tight?
5. Of the ~1,400 open orders, how many are genuinely still live? 170 date from 2024.
6. Who fixes a wrong division tag in Zoho once the screen flags it?
7. Shall I create the coordinator accounts for Nirmani, Umanda and Madushi now? They will see a holding
   page until their release, but the manager-to-division mapping needs them to exist.

Abdul Hadhee | IT Exec | Standard-Holdings
