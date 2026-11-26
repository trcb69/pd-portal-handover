"""Order patterns + lead times for SPS customized items.
usage: python3.12 -I patterns.py <so.xlsx> <invoice.xlsx> <package.xlsx> <shipment.xlsx> <item.xlsx> <outdir> [cache.pkl]
Read-only on inputs. Prints a JSON-ish results block to stdout; writes data/monthly-volume.csv, data/lead-times.csv, data/*.csv"""
import sys, os, csv, pickle, statistics as S, collections as C, datetime as dt, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load import rows
so_p, inv_p, pkg_p, shp_p, item_p, out = sys.argv[1:7]
cache = sys.argv[7] if len(sys.argv) > 7 else None
if cache and os.path.exists(cache):
    D = pickle.load(open(cache, 'rb'))
else:
    D = {'so': rows(so_p, 'Sales Order')[1], 'inv': rows(inv_p, 'Invoice')[1], 'pkg': rows(pkg_p)[1], 'shp': rows(shp_p)[1], 'item': rows(item_p)[1]}
    if cache: pickle.dump(D, open(cache, 'wb'))
so, inv, pkg, shp, item = D['so'], D['inv'], D['pkg'], D['shp'], D['item']
R = {}  # results for the report
AS_OF = dt.datetime(2026, 9, 25)
PKG_END = dt.datetime(2026, 9, 15)   # last packing/shipment date in the 16 Sep snapshot
def isdt(x): return isinstance(x, dt.datetime)
def num(x):
    try: return float(x)
    except: return 0.0
def pct(a, b): return round(100 * a / b, 1) if b else None
def med(v): return round(S.median(v), 1) if v else None
def p80(v):
    if not v: return None
    v = sorted(v); k = (len(v) - 1) * 0.8; f = int(k); c = min(f + 1, len(v) - 1)
    return round(v[f] + (v[c] - v[f]) * (k - f), 1)
DIV = {'Offset Printing Division (OPD)': 'OPD', 'Screen Printing Division (SHPS)': 'SHPS'}
def div(r): return r['CF.Manufacturing Division'] or '(blank)'
OT = lambda r: r['CF.Order Type'] or '(blank)'

# ---- SO header table (one per SalesOrder Number; header fields verified identical across lines)
hdr = {}
lines_by = C.defaultdict(list)
for r in so: lines_by[r['SalesOrder Number']].append(r)
for k, ls in lines_by.items():
    r = ls[0]
    hdr[k] = dict(so=k, order=r['Order Date'], exp=r['Expected Shipment Date'] if isdt(r['Expected Shipment Date']) else None,
                  status=r['Status'], otype=OT(r), div=div(r), nlines=len(ls), cust=r['Customer Name'],
                  end_cust=r['CF.Order Received from'], jobnature=(r['CF.Job Nature'] or '').strip() or '(blank)')
# item master flag
im = {str(r['Item ID']): r for r in item}
def fg(r): 
    i = im.get(str(r['Product ID'])); return (i or {}).get('CF.Finished Good Type') or '(not in item master)'
R['so_lines'] = len(so); R['so_count'] = len(hdr)
R['date_range'] = [str(min(h['order'] for h in hdr.values()).date()), str(max(h['order'] for h in hdr.values()).date())]
R['order_type_lines'] = C.Counter(OT(r) for r in so)
R['order_type_sos'] = C.Counter(h['otype'] for h in hdr.values())
R['fgtype_lines'] = C.Counter(fg(r) for r in so)
R['xtab_ordertype_fgtype'] = {k: dict(v) for k, v in {ot: C.Counter(fg(r) for r in so if OT(r) == ot) for ot in R['order_type_lines']}.items()}
R['item_join'] = dict(matched=sum(1 for r in so if str(r['Product ID']) in im), total=len(so))

# ---- monthly volume (customized order type) per division, last 24 months Oct-2024..Sep-2026
def ym(d): return d.strftime('%Y-%m')
months = []
y, m = 2024, 10
while (y, m) <= (2026, 9):
    months.append(f'{y}-{m:02d}'); m += 1
    if m == 13: y, m = y + 1, 1
mv = C.defaultdict(lambda: [0, set(), 0.0])
for r in so:
    h = hdr[r['SalesOrder Number']]; k = ym(r['Order Date'])
    if k not in months: continue
    for ot in (h['otype'], 'ALL'):
        for dv in (h['div'], 'ALL'):
            e = mv[(k, ot, dv)]; e[0] += 1; e[1].add(r['SalesOrder Number']); e[2] += num(r['QuantityOrdered'])
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'monthly-volume.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['month', 'order_type', 'manufacturing_division', 'so_lines', 'sales_orders', 'qty_ordered', 'note'])
    for (k, ot, dv), e in sorted(mv.items()):
        w.writerow([k, ot, dv, e[0], len(e[1]), round(e[2]), 'partial month: data to 2026-09-25' if k == '2026-09' else ''])
R['months'] = months
def mtot(ot, dv='ALL'): return {k: (mv[(k, ot, dv)][0], len(mv[(k, ot, dv)][1])) for k in months}
R['monthly_customized_all'] = mtot('Customized Order')
R['monthly_all_all'] = mtot('ALL')
cdiv = C.Counter(); cdivso = C.defaultdict(set)
for (k, ot, dv), e in mv.items():
    if ot == 'Customized Order' and dv != 'ALL': cdiv[dv] += e[0]; cdivso[dv] |= e[1]
R['custom_by_div_24m'] = {dv: (cdiv[dv], len(cdivso[dv])) for dv in cdiv}

# ---- orders per working day (customized, last 12 full months Sep-2025..Aug-2026, Mon-Sat calendar; no holiday calendar available)
def cust_so(): return [h for h in hdr.values() if h['otype'] == 'Customized Order']
win = [h for h in cust_so() if dt.datetime(2025, 9, 1) <= h['order'] <= dt.datetime(2026, 8, 31)]
perday = C.Counter(h['order'].date() for h in win)
lines_day = C.Counter(); 
for r in so:
    h = hdr[r['SalesOrder Number']]
    if h['otype'] == 'Customized Order' and dt.datetime(2025, 9, 1) <= h['order'] <= dt.datetime(2026, 8, 31): lines_day[h['order'].date()] += 1
d0 = dt.date(2025, 9, 1); alld = [d0 + dt.timedelta(i) for i in range(365)]
workdays = [d for d in alld if d.weekday() <= 5]
wd_orders = [perday.get(d, 0) for d in workdays]; wd_lines = [lines_day.get(d, 0) for d in workdays]
act = [perday[d] for d in perday if d.weekday() <= 5]
R['perday'] = dict(window='2025-09-01..2026-08-31', mon_sat_days=len(workdays), days_with_orders=len(perday), sos=len(win),
                   mean_sos_per_day=round(sum(wd_orders) / len(workdays), 2), median_sos_per_day=S.median(wd_orders), p95_sos=sorted(wd_orders)[int(.95 * (len(wd_orders) - 1))], max_sos=max(wd_orders),
                   mean_lines_per_day=round(sum(wd_lines) / len(workdays), 2), p95_lines=sorted(wd_lines)[int(.95 * (len(wd_lines) - 1))], max_lines=max(wd_lines),
                   weekday_dist=dict(C.Counter(h['order'].weekday() for h in win)),
                   busiest=[(str(d), n) for d, n in perday.most_common(3)])
# all order types too
winA = [h for h in hdr.values() if dt.datetime(2025, 9, 1) <= h['order'] <= dt.datetime(2026, 8, 31)]
R['perday']['all_types_mean_sos_per_day'] = round(len(winA) / len(workdays), 2)
# lines per SO
def dist(v): 
    v = sorted(v); return dict(n=len(v), mean=round(sum(v) / len(v), 2), median=S.median(v), p80=p80(v), p95=v[int(.95 * (len(v) - 1))], max=v[-1], single_line_pct=pct(sum(1 for x in v if x == 1), len(v)))
R['lines_per_so'] = {ot: dist([h['nlines'] for h in hdr.values() if h['otype'] == ot]) for ot in R['order_type_sos']}
R['lines_per_so_cust_by_div'] = {dv: dist([h['nlines'] for h in cust_so() if h['div'] == dv]) for dv in sorted({h['div'] for h in cust_so()})}
# job nature, qty per line
R['jobnature_cust'] = dict(C.Counter(h['jobnature'] for h in cust_so()))
q = sorted(num(r['QuantityOrdered']) for r in so if r['CF.Order Type'] == 'Customized Order')
R['qty_per_line_cust'] = dict(median=S.median(q), p20=q[int(.2 * len(q))], p80=q[int(.8 * len(q))], p95=q[int(.95 * len(q))])
R['distinct_items_cust'] = len({r['Product ID'] for r in so if r['CF.Order Type'] == 'Customized Order'})
R['distinct_endcust_cust'] = len({(r['CF.Order Received from'] or '').strip().lower() for r in so if r['CF.Order Type'] == 'Customized Order'})
# item repeat frequency (reorder share): items ordered >=2 times in customized
ic = C.Counter(r['Product ID'] for r in so if r['CF.Order Type'] == 'Customized Order')
R['items_cust_ordered_once'] = sum(1 for v in ic.values() if v == 1); R['items_cust_ordered_2plus'] = sum(1 for v in ic.values() if v >= 2)
R['cust_lines_on_items_ordered_2plus'] = sum(v for v in ic.values() if v >= 2)

# ---- date index from packages / shipments / invoices (SO-level first/last)
def agg(rowsx, key, datek, filt=None):
    first, last, n = {}, {}, C.Counter()
    for r in rowsx:
        if filt and not filt(r): continue
        k, d = r[key], r[datek]
        if not k or not isdt(d): continue
        n[k] += 1
        if k not in first or d < first[k]: first[k] = d
        if k not in last or d > last[k]: last[k] = d
    return first, last, n
pf, pl, pn = agg(pkg, 'SO Number', 'Packing Date')
sf, sl, sn = agg(shp, 'SO Number', 'Shipment Date')
inf, inl, inn = agg(inv, 'Sales Order Number', 'Invoice Date')
sonum = set(hdr)
R['joins'] = dict(
    pkg=dict(rows=len(pkg), rows_with_so=sum(1 for r in pkg if r['SO Number']), distinct_so=len(pn), matched=len(set(pn) & sonum), rows_in_so_set=sum(1 for r in pkg if r['SO Number'] in sonum), date_min=str(min(pf.values()).date()), date_max=str(max(pl.values()).date())),
    shp=dict(rows=len(shp), rows_with_so=sum(1 for r in shp if r['SO Number']), distinct_so=len(sn), matched=len(set(sn) & sonum), rows_in_so_set=sum(1 for r in shp if r['SO Number'] in sonum), date_min=str(min(sf.values()).date()), date_max=str(max(sl.values()).date())),
    inv=dict(rows=len(inv), rows_with_so=sum(1 for r in inv if r['Sales Order Number']), distinct_so=len(inn), matched=len(set(inn) & sonum), rows_in_so_set=sum(1 for r in inv if r['Sales Order Number'] in sonum), date_min=str(min(inf.values()).date()), date_max=str(max(inl.values()).date()),
             po_equals_so=sum(1 for r in inv if r['PurchaseOrder'] == r['Sales Order Number'] and r['Sales Order Number'])))
# SOs ordered on/after 2024-04-01 and up to snapshot, share having each doc
cohort = [h for h in hdr.values() if dt.datetime(2024, 4, 1) <= h['order'] <= dt.datetime(2026, 7, 31)]
R['cohort_n'] = len(cohort)
R['cohort_coverage'] = {k: pct(sum(1 for h in cohort if h['so'] in s), len(cohort)) for k, s in [('package', pn), ('shipment', sn), ('invoice', inn)]}
R['so_pre_2024_04'] = sum(1 for h in hdr.values() if h['order'] < dt.datetime(2024, 4, 1))
R['pkg_by_so_status'] = {st: dict(C.Counter(h['so'] in pn for h in hdr.values() if h['status'] == st and h['order'] >= dt.datetime(2024, 4, 1))) for st in ('invoiced', 'partially_invoiced', 'confirmed')}
# package -> shipment via Packing Number
pk_nums = {r['Packing Number'] for r in pkg if r['Packing Number']}
sh_nums = {r['Packing Number'] for r in shp if r['Packing Number']}
R['pkg_shp_join'] = dict(pkg_numbers=len(pk_nums), shp_numbers=len(sh_nums), shp_in_pkg=len(sh_nums & pk_nums), pkg_in_shp=len(pk_nums & sh_nums))
# shipment status text
R['pkg_status'] = dict(C.Counter(r['Status'] for r in pkg)); R['shp_status'] = dict(C.Counter(r['Status'] for r in shp))

# ---- lead times per SO
def days(a, b): return (b - a).days
rows_out = []
def collect(hs, getter):
    return [v for v in (getter(h) for h in hs) if v is not None and v >= 0]
LT = []  # csv rows
groups = [('Customized Order',), ('Ex Stock',), ('Internal SH Order',), ('Make to Order (MTO)',)]
def ltrow(ot, dv, hs, scope):
    d = dict(order_type=ot, manufacturing_division=dv, cohort=scope, so_n=len(hs))
    for name, fidx in [('first_package', pf), ('first_shipment', sf), ('first_invoice', inf), ('last_shipment', sl)]:
        v = [days(h['order'], fidx[h['so']]) for h in hs if h['so'] in fidx]
        neg = sum(1 for x in v if x < 0)
        v = [x for x in v if x >= 0]
        d[name + '_n'] = len(v); d[name + '_pct_of_so'] = pct(len(v), len(hs)); d[name + '_median_d'] = med(v); d[name + '_p80_d'] = p80(v); d[name + '_neg_dropped'] = neg
    # expected vs actual shipment
    e = [(h, sf[h['so']]) for h in hs if h['exp'] and h['so'] in sf]
    d['exp_date_fill_pct'] = pct(sum(1 for h in hs if h['exp']), len(hs))
    d['planned_lead_median_d'] = med([days(h['order'], h['exp']) for h in hs if h['exp'] and days(h['order'], h['exp']) >= 0])
    dl = [days(h['exp'], s) for h, s in e]
    d['first_ship_vs_expected_n'] = len(dl); d['first_ship_vs_expected_median_d'] = med(dl); d['first_ship_vs_expected_p80_d'] = p80(dl)
    d['first_ship_on_or_before_expected_pct'] = pct(sum(1 for x in dl if x <= 0), len(dl))
    el = [(h, sl[h['so']]) for h in hs if h['exp'] and h['so'] in sl and h['status'] == 'invoiced']
    dll = [days(h['exp'], s) for h, s in el]
    d['last_ship_vs_expected_n'] = len(dll); d['last_ship_vs_expected_median_d'] = med(dll); d['last_ship_on_or_before_expected_pct'] = pct(sum(1 for x in dll if x <= 0), len(dll))
    return d
cohortA = cohort
div_list = sorted({h['div'] for h in cohort})
for ot in ['Customized Order', 'Ex Stock', 'Internal SH Order', 'Make to Order (MTO)']:
    hs = [h for h in cohort if h['otype'] == ot]
    LT.append(ltrow(ot, 'ALL', hs, 'orders 2024-04-01..2026-07-31'))
    for dv in div_list:
        hh = [h for h in hs if h['div'] == dv]
        if hh: LT.append(ltrow(ot, dv, hh, 'orders 2024-04-01..2026-07-31'))
# last 12 months cohort for customised (more current)
c12 = [h for h in cohort if h['order'] >= dt.datetime(2025, 8, 1) and h['otype'] == 'Customized Order']
LT.append(ltrow('Customized Order', 'ALL', c12, 'orders 2025-08-01..2026-07-31'))
for dv in div_list:
    hh = [h for h in c12 if h['div'] == dv]
    if hh: LT.append(ltrow('Customized Order', dv, hh, 'orders 2025-08-01..2026-07-31'))
with open(os.path.join(out, 'lead-times.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(LT[0].keys())); w.writeheader(); w.writerows(LT)
R['lt_rows'] = [{k: r[k] for k in ('order_type', 'manufacturing_division', 'cohort', 'so_n', 'first_package_median_d', 'first_package_p80_d', 'first_shipment_median_d', 'first_shipment_p80_d', 'first_invoice_median_d', 'first_invoice_p80_d', 'last_shipment_median_d', 'last_shipment_p80_d', 'first_shipment_pct_of_so', 'exp_date_fill_pct', 'planned_lead_median_d', 'first_ship_vs_expected_median_d', 'first_ship_on_or_before_expected_pct', 'first_ship_vs_expected_n')} for r in LT]
# negative lead (package before order date) count
R['neg_pkg_before_order'] = sum(1 for h in cohort if h['so'] in pf and pf[h['so']] < h['order'])
# order-date vs expected date: how many SOs have expected before order
R['exp_before_order'] = sum(1 for h in hdr.values() if h['exp'] and h['exp'] < h['order'])
# expected fill by year (customized)
R['exp_fill_by_year_cust'] = {y: pct(sum(1 for h in cust_so() if h['order'].year == y and h['exp']), sum(1 for h in cust_so() if h['order'].year == y)) for y in (2023, 2024, 2025, 2026)}

# ---- cancellation / partial (line level), by order type, + customised by division
def line_stats(ls):
    n = len(ls)
    canc = [r for r in ls if num(r['QuantityCancelled']) > 0]
    fully = [r for r in canc if num(r['QuantityCancelled']) >= num(r['QuantityOrdered'])]
    done = [r for r in ls if r['Status'] in ('invoiced', 'partially_invoiced')]
    short = [r for r in ls if r['Status'] == 'invoiced' and num(r['QuantityInvoiced']) + num(r['QuantityCancelled']) < num(r['QuantityOrdered']) - 1e-9]
    over = [r for r in ls if num(r['QuantityInvoiced']) > num(r['QuantityOrdered']) + 1e-9]
    part_status = [r for r in ls if r['Status'] == 'partially_invoiced']
    qo = sum(num(r['QuantityOrdered']) for r in ls); qc = sum(num(r['QuantityCancelled']) for r in ls)
    return dict(lines=n, lines_with_cancel=len(canc), lines_with_cancel_pct=pct(len(canc), n), lines_fully_cancelled=len(fully), cancelled_qty_pct_of_ordered=pct(qc, qo),
                lines_status_partially_invoiced=len(part_status), lines_status_partially_invoiced_pct=pct(len(part_status), n),
                invoiced_lines_short_vs_ordered=len(short), over_invoiced_lines=len(over))
R['cancel_by_type'] = {ot: line_stats([r for r in so if OT(r) == ot]) for ot in R['order_type_lines']}
R['cancel_cust_by_div'] = {dv: line_stats([r for r in so if OT(r) == 'Customized Order' and div(r) == dv]) for dv in sorted({div(r) for r in so if OT(r) == 'Customized Order'})}
# SO-level partially invoiced customized, aged
R['so_status_cust'] = dict(C.Counter(h['status'] for h in cust_so()))
# cancel by year customized
R['cancel_cust_by_year'] = {y: line_stats([r for r in so if OT(r) == 'Customized Order' and r['Order Date'].year == y])['lines_with_cancel_pct'] for y in (2023, 2024, 2025, 2026)}
# partial shipments: SOs with >1 shipment dates in cohort
def multi(hs): 
    v = [h for h in hs if h['so'] in sn]
    return dict(so_shipped=len(v), so_multi_package_numbers=sum(1 for h in v if len({r for r in ()}) ) )
# distinct shipment numbers per SO
ship_per = C.defaultdict(set)
for r in shp:
    if r['SO Number']: ship_per[r['SO Number']].add(r['Shipment Number'])
R['shipments_per_so_cust'] = {k: v for k, v in C.Counter(min(len(ship_per[h['so']]), 5) for h in cohort if h['otype'] == 'Customized Order' and h['so'] in ship_per).items()}
R['multi_ship_pct_cust'] = pct(sum(1 for h in cohort if h['otype'] == 'Customized Order' and len(ship_per.get(h['so'], ())) > 1), sum(1 for h in cohort if h['otype'] == 'Customized Order' and h['so'] in ship_per))

# ---- backlog: confirmed lines (all types, then customized)
conf = [r for r in so if r['Status'] == 'confirmed']
R['confirmed_total_lines'] = len(conf); R['confirmed_by_type'] = dict(C.Counter(OT(r) for r in conf))
cc = [r for r in conf if OT(r) == 'Customized Order']
R['confirmed_cust_lines'] = len(cc); R['confirmed_cust_sos'] = len({r['SalesOrder Number'] for r in cc})
R['confirmed_cust_by_div'] = {dv: (sum(1 for r in cc if div(r) == dv), len({r['SalesOrder Number'] for r in cc if div(r) == dv})) for dv in sorted({div(r) for r in cc})}
def age(r): return (AS_OF - r['Order Date']).days
bk = [('0-14d', 0, 14), ('15-30d', 15, 30), ('31-60d', 31, 60), ('61-90d', 61, 90), ('91-180d', 91, 180), ('181-365d', 181, 365), ('>365d', 366, 99999)]
R['confirmed_cust_age'] = {n: sum(1 for r in cc if a <= age(r) <= b) for n, a, b in bk}
R['confirmed_cust_age_oldest'] = max(age(r) for r in cc); R['confirmed_cust_age_median'] = S.median(age(r) for r in cc)
R['confirmed_cust_overdue'] = dict(with_expected=sum(1 for r in cc if isdt(r['Expected Shipment Date'])), past_expected=sum(1 for r in cc if isdt(r['Expected Shipment Date']) and r['Expected Shipment Date'] < AS_OF))
R['confirmed_cust_qty'] = dict(ordered=sum(num(r['QuantityOrdered']) for r in cc), packed=sum(num(r['QuantityPacked']) for r in cc), invoiced=sum(num(r['QuantityInvoiced']) for r in cc), cancelled=sum(num(r['QuantityCancelled']) for r in cc))
R['confirmed_cust_lines_any_packed'] = sum(1 for r in cc if num(r['QuantityPacked']) > 0)
R['confirmed_cust_lines_with_package_row_by_so'] = sum(1 for r in cc if r['SalesOrder Number'] in pn)
R['confirmed_cust_by_year'] = dict(C.Counter(r['Order Date'].year for r in cc))
R['confirmed_cust_job_nature'] = dict(C.Counter((r['CF.Job Nature'] or '').strip() or '(blank)' for r in cc))
# ---- channel
def fill(ls, k, ne=''): return pct(sum(1 for r in ls if (str(r[k]).strip() if r[k] is not None else '') not in ('', ne)), len(ls))
def merged(r, a, b): return (r[a] or r[b] or '')
R['channel'] = {}
for ot in ('Customized Order', 'ALL'):
    ls = [r for r in so if ot == 'ALL' or OT(r) == ot]
    R['channel'][ot] = dict(lines=len(ls), sales_person=dict(C.Counter(r['Sales Person'] or '(blank)' for r in ls)), source=dict(C.Counter(str(r['Source']) for r in ls)), template=dict(C.Counter(r['Template Name'] for r in ls)),
        sales_channel=dict(C.Counter(r['Sales Channel'] for r in ls)), po_ref_fill=fill(ls, 'PurchaseOrder'), sh_so_ref_fill=fill(ls, 'CF.SH Sales Order Ref'), job_no_fill=fill(ls, 'CF.Job No'),
        sh_ref_equals_job=pct(sum(1 for r in ls if r['CF.SH Sales Order Ref'] and r['CF.SH Sales Order Ref'] == r['CF.Job No']), len(ls)),
        sh_ref_equals_po_field=pct(sum(1 for r in ls if r['CF.SH Sales Order Ref'] and r['CF.SH Sales Order Ref'] == r['PurchaseOrder']), len(ls)),
        received_from_fill=fill(ls, 'CF.Order Received from'), clickup_fill=fill(ls, 'CF.Clickup Link'), notes_fill=fill(ls, 'Notes'),
        base_material_fill=fill(ls, 'CF.Base Material to be Used'), addl_material_fill=fill(ls, 'CF.Additional Other Material to be Used (If any)'),
        artwork_fill=pct(sum(1 for r in ls if merged(r, 'CF.Artwork Availability', 'CF.Artwork Availablility').strip()), len(ls)),
        dye_fill=pct(sum(1 for r in ls if merged(r, 'CF.Dye Cutter Availability', 'CF.Dye Cutter Availablity').strip()), len(ls)),
        screen_fill=pct(sum(1 for r in ls if merged(r, 'CF.Screen / Plate Available', 'CF.Screen / Plate Availability').strip()), len(ls)),
        job_nature_fill=pct(sum(1 for r in ls if (r['CF.Job Nature'] or '').strip()), len(ls)),
        sample_job_no=[r['CF.Job No'] for r in ls[:3]])
cs = [r for r in so if OT(r) == 'Customized Order']
R['channel']['cust_by_year'] = {y: dict(lines=sum(1 for r in cs if r['Order Date'].year == y), template=dict(C.Counter(r['Template Name'] for r in cs if r['Order Date'].year == y)),
    sales_person_filled=pct(sum(1 for r in cs if r['Order Date'].year == y and r['Sales Person']), sum(1 for r in cs if r['Order Date'].year == y)),
    clickup_fill=fill([r for r in cs if r['Order Date'].year == y], 'CF.Clickup Link'), artwork_fill=pct(sum(1 for r in cs if r['Order Date'].year == y and merged(r, 'CF.Artwork Availability', 'CF.Artwork Availablility').strip()), sum(1 for r in cs if r['Order Date'].year == y))) for y in (2023, 2024, 2025, 2026)}
R['channel']['template_by_type'] = {ot: dict(C.Counter(r['Template Name'] for r in so if OT(r) == ot)) for ot in R['order_type_lines']}
R['channel']['customer_by_type_cust'] = dict(C.Counter(r['Customer Name'] for r in cs).most_common(4))
# Sales Person values
R['channel']['sales_person_by_type'] = {ot: dict(C.Counter(r['Sales Person'] or '(blank)' for r in so if OT(r) == ot)) for ot in R['order_type_lines']}
ec = C.Counter((r['CF.Order Received from'] or '').strip() for r in cs)
R['top_end_customers_cust'] = ec.most_common(15)
R['end_cust_top15_share'] = pct(sum(v for _, v in ec.most_common(15)), len(cs))
json.dump(R, open(os.path.join(out, 'results.json'), 'w'), indent=1, default=str)
print('OK')
