# Production dashboard demo (manager preview)

A clickable demo of the manager view for the office visit. Pick a person (Ranga, Ishan, Mubeena, Samitha, Hadhee) and see their jobs, five counters, the document strip per job and a drawer per job. It is read-only, has no prices, and never calls Zoho or any network (only Google Fonts).

Files: `index.html` (the page, data inlined), `preview.html` (same page with a plain skeleton for opening from disk), `page.src.html` (source, `__DATA__` placeholder), `data.json` (from `make_data.py`), `validate.py` (checks the data against the spec rules), `DESIGN.md` (design notes; sections 3.1 and the MacPro lines are superseded by this README), `final-desktop.png`, `final-phone.png`.

## Where the data comes from
- Real, from `/root/exports/zoho/native/2026-09-16/Sales_Order.xlsx`: order number, line id, customer, item, unit, quantity ordered and cancelled, creation date, due date, line division tag, header division, order type, job number. These are listed per job in `real_fields`.
- Simulated (see `demo_fields` per job): bundled, produced, shipped quantities where Zoho has no value, packed/invoiced on a few re-opened lines, event times ("seen by sync"), the missing-document flags that follow from them, and the checking and sync-problem states. The visible ribbon says this.
- "Today" is fixed at 15 Sep 2026 so numbers never drift.

## Rules used (spec Rev 11)
- Open = not (shipped >= effective and invoiced >= effective). Fully shipped but not invoiced jobs stay open, so the invoice_missing flag shows and counts under Documents missing.
- Past due, Due in 3 days, In production, Made not shipped count only open jobs with shipped < effective.
- Division comes from the line tag, else the header. A tag with no alias (for example OPD - MacPro Unit, not in 002-seed.sql) gives no division, reason `unmapped_division`, shown as "No division" to Samitha and Hadhee only.
- Counters on screen: Ranga 12/4/11/20/7, Ishan 8/2/9/13/6, Mubeena 7/1/0/8/3, Samitha and Hadhee 26/7/22/37/14 (past due, due in 3 days, in production, made not shipped, documents missing).

## Rebuild
```
cd "/root/Project Management/reports/2026-10-02-pd-manager-demo"
python3 make_data.py && python3 validate.py
python3 - <<'PY'
s=open('page.src.html').read(); d=open('data.json').read().strip()
idx=s.replace('__DATA__',d); open('index.html','w').write(idx)
open('preview.html','w').write('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+idx+'</body></html>')
PY
```

## Known gaps
- Closed short: removed. The earlier "straws ship about 95%" claim was not supported (the cancelled quantity explains the gap). Still to confirm with Ishan and Samitha: do straw orders ever ship short with no cancellation recorded? If yes the spec needs a closed-short state.
- MacPro is not a division in the seed. Whether it becomes one is a manager answer; the demo shows those 5 lines as "No division".
- Card strips hide untracked stages and show "N not tracked" (tooltip lists them); spec section 6 shows them as icons. The drawer shows all.
- validate.py's docs_missing count is a rough check and counts older (legacy) jobs; the page's numbers above are authoritative.
- The person picker is not vertically centred on very large screens.
- Not published as an artifact.
