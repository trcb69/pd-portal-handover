#!/usr/bin/env python3
"""Turn an SH sales-order export (Zoho native xlsx) into sh-items.json for the portal's import-sh-items CLI.

Spec: joint demo Rev 4.10 section 22 (C1, C4). Writes id, name and SKU only: no prices, customers or quantities.
- Aborts if any Product ID cell is not text (19-digit ids would be rounded as numbers).
- Dedupes by id; the name and SKU come from the row with the latest Order Date.
- Prints counts only.

Usage: python3 -I sh-items-from-export.py <export.xlsx> <out sh-items.json>
Prepared by Abdul Hadhee | IT Executive
"""
import json
import os
import re
import sys

import openpyxl

ID_RE = re.compile(r"^\d{1,25}$")


def main(src, out):
    wb = openpyxl.load_workbook(src, read_only=True)
    rows = wb.active.iter_rows(values_only=True)
    head = list(next(rows))
    try:
        c_id, c_name, c_sku, c_date = (head.index(k) for k in ("Product ID", "Item Name", "SKU", "Order Date"))
    except ValueError as err:
        sys.exit(f"stopped: a needed column is missing ({err})")

    best = {}      # id -> (date, name, sku)
    names = {}     # id -> set of names seen
    lines = 0
    for r in rows:
        pid = r[c_id]
        if pid is None or pid == "":
            continue
        lines += 1
        if not isinstance(pid, str):
            sys.exit(f"stopped: a Product ID cell is {type(pid).__name__}, not text; nothing written")
        if not ID_RE.match(pid):
            sys.exit("stopped: a Product ID is not 1-25 digits; nothing written")
        name = (r[c_name] or "").strip()
        sku = (r[c_sku] or "").strip() if isinstance(r[c_sku], str) else ("" if r[c_sku] is None else str(r[c_sku]))
        date = str(r[c_date] or "")
        names.setdefault(pid, set()).add(name)
        if pid not in best or date >= best[pid][0]:
            best[pid] = (date, name, sku)

    items = [{"id": pid, "name": n, "sku": s or None} for pid, (_, n, s) in sorted(best.items())]
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False)
    os.chmod(tmp, 0o600)
    os.replace(tmp, out)
    print(f"lines read: {lines}")
    print(f"items written: {len(items)}")
    print(f"items with a SKU: {sum(1 for i in items if i['sku'])}")
    print(f"ids with more than one name: {sum(1 for v in names.values() if len(v) > 1)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: sh-items-from-export.py <export.xlsx> <out.json>")
    main(sys.argv[1], sys.argv[2])
