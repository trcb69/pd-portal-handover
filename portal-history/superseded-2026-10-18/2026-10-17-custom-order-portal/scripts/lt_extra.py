"""Extra lead-time cuts: same-day share and lead time by order-year. usage: lt_extra.py <cache.pkl> <outdir>"""
import sys, os, pickle, csv, datetime as dt, statistics as S, collections as C
D = pickle.load(open(sys.argv[1], 'rb')); out = sys.argv[2]
so, shp = D['so'], D['shp']
hdr = {}
for r in so: hdr.setdefault(r['SalesOrder Number'], r)
sf = {}
for r in shp:
    k, d = r['SO Number'], r['Shipment Date']
    if k and isinstance(d, dt.datetime) and (k not in sf or d < sf[k]): sf[k] = d
def p80(v):
    v = sorted(v); k = (len(v) - 1) * .8; f = int(k); c = min(f + 1, len(v) - 1); return round(v[f] + (v[c] - v[f]) * (k - f), 1)
rows = []
for ot in ('Customized Order', 'Ex Stock'):
  for dv in ['ALL'] + sorted({r['CF.Manufacturing Division'] for r in hdr.values()}):
    for y in (2024, 2025, 2026, 'ALL'):
        v = [(sf[k] - r['Order Date']).days for k, r in hdr.items() if k in sf and r['CF.Order Type'] == ot and (dv == 'ALL' or r['CF.Manufacturing Division'] == dv)
             and dt.datetime(2024, 4, 1) <= r['Order Date'] <= dt.datetime(2026, 7, 31) and (y == 'ALL' or r['Order Date'].year == y)]
        if len(v) >= 20:
            rows.append([ot, dv, y, len(v), S.median(v), p80(v), round(100 * sum(1 for x in v if x == 0) / len(v), 1), round(100 * sum(1 for x in v if x <= 3) / len(v), 1)])
with open(os.path.join(out, 'lead-times-by-year.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['order_type', 'manufacturing_division', 'order_year', 'so_with_shipment', 'first_shipment_median_d', 'first_shipment_p80_d', 'same_day_pct', 'within_3d_pct']); w.writerows(rows)
for r in rows: print(r)
