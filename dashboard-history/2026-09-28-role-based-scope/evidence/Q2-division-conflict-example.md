# Q2 evidence: the SO where the division on the header and the division on the line disagree

Written 29 Sep 2026 for spec question Q2 of
`/root/Project Management/wiki/specs/2026-09-28-pd-manager-preview.md`.
Source of every fact below: `/root/exports/zoho/native/2026-09-19/sps/salesorders_since_2026-09-15.json`
(SPS Zoho Inventory, sales-order **detail** pull, 22 SOs dated 15-18 Sep 2026, pulled 19 Sep 2026).

Saved next to this file:

- `Q2-division-conflict-JOBORDER-08597-08592.json` - just the two SOs, trimmed to the fields that matter.
- `Q2-division-lines-all.json` - all 22 SOs / 22 lines, header division next to line tag, so the pattern is visible.

---

## 1. Zoho holds the division in two different places

| Where | Zoho field | Level | Example value |
|---|---|---|---|
| On the sales order itself | custom field **CF.Manufacturing Division** (`cf_manufacturing_division`) | **header** - one per sales order | `Paper Cup Unit (PCU)` |
| On each item row of the sales order | reporting tag **Division** (`tags[].tag_name = "Division"`) | **line** - one per item | `MOBA Unit` |

A sales order with three different items can therefore carry three different line tags but only one
header value. Since one job = one sales-order line (your decision of 28 Sep), only the line tag can be
per job.

## 2. The two sales orders where they disagree

Both are dated **16 Sep 2026**, both sold to Standard Holdings (Pvt) Ltd.

| Sales order | Zoho salesorder_id | Job no (CF.Job No) | Item on the line | Header CF.Manufacturing Division | Line Division tag |
|---|---|---|---|---|---|
| **JOBORDER-08597** | 4892105000113028131 | OPD6704 | SP-12oz D/Wall White Paper Cup (TCO) | `Paper Cup Unit (PCU)` | `MOBA Unit` |
| **JOBORDER-08592** | 4892105000113028068 | OPD6705 | SH-12oz S/Wall White Paper Cup | `Paper Cup Unit (PCU)` | `MOBA Unit` |

Exact places in the export file:

| Fact | JOBORDER-08597 | JOBORDER-08592 |
|---|---|---|
| `salesorder_number` | line 2021 | line 3971 |
| line `line_item_id` | line 2075 | line 4025 |
| line tag `"tag_name": "Division"` | line 2133 | line 4083 |
| line tag value `"tag_option_name"` | line 2135 = `MOBA Unit` | line 4085 = `MOBA Unit` |
| line `project_name` (the job no on the line) | line 2165 = `OPD6704` | line 4115 = `OPD6705` |
| header `cf_job_no` | line 2527 = `OPD6704` | line 4505 = `OPD6705` |
| header `cf_manufacturing_division` | line 2533 = `Paper Cup Unit (PCU)` | line 4511 = `Paper Cup Unit (PCU)` |

**To see it in Zoho yourself:** Zoho Inventory (SPS org) > Sales Orders > search `JOBORDER-08597`.
The header field is in the order's detail panel ("Manufacturing Division"). The line tag is on the item
row - open the row's tag/reporting-tag column, or use More > Reporting Tags. The same two SOs also carry
a `cf_clickup_link`, so the ClickUp task for each is one click away and you can see which team actually
worked it.

## 3. How common is it

Of 22 sampled lines: **2 disagree** (the two above), **16 agree**, **4 have no line tag at all** - every
one of those four is a Rewinding Unit (RWU) order: JOBORDER-08589, -08571, -08560 and -08539. For
those the header is the only source there is.

The full 22 are in `Q2-division-lines-all.json`. Line tag values seen in the sample:
`Paper Straw Unit`, `OPD - PackPro Unit`, `MOBA Unit`, `MOBA Punching Unit`, `Screen Printing Unit`,
`Customized Packing Unit`.

## 4. Why I recommend the line tag wins (and the header only as fallback)

1. It is the only per-item source, and a job is one item line.
2. **If the header wins, these two jobs have no manager at all.** The manager list of 28 Sep covers
   PSU, OPD/Offset, Packpro, RWU (Ishan), Screen Printing (Mubeena), OPD, MOBA, FPP, CPU (Ranga).
   `Paper Cup Unit (PCU)` is in nobody's list, so both jobs would land on the admin "unassigned" list
   and no manager would ever see them. With the line tag they go to MOBA, which is Ranga.
3. It matches how the work is actually tracked: paper-cup work has no ClickUp list of its own - PCU
   tasks live inside MOBA's ClickUp list (ClickUp map, 25 Sep 2026).

I cannot verify which value is factually right for these two orders - the item is a paper cup (points at
PCU) but the job number is OPD-series and the tag says MOBA (points at the punching machines). Only the
floor knows. That is a data-quality question for Samitha, not a blocker for the screen.

## 5. Two things this turned up that the spec does not yet cover

- **Five seeded divisions have no manager:** PCU, PCLU (Paper Cup Lid), DPU (Digital Printing), PPU
  (Paper Plate), CWU (Cake Wrapper) - all seeded in `002-seed.sql:9-11` but absent from the 28 Sep
  manager mapping. Any job that resolves to one of them is invisible to every manager. Needs an owner
  per division, or an explicit decision that they stay on the admin list.
- **A "division conflict" marker is cheap and worth having:** route by the line tag, and also show the
  job on the admin list flagged "header says X, line says Y" so the wrong one gets corrected in Zoho
  instead of staying wrong forever.

Abdul Hadhee | IT Exec | Standard-Holdings
