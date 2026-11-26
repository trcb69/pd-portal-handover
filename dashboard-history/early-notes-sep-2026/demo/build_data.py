"""Build the demo dataset from real SmartPack Zoho exports.

Real: SO fields, readiness gates, SH SO ref, quantities, bundle/picklist/package/shipment/invoice
dates (first document per SO). Simulated (flagged in output): manual checklist stages, file
location, manager choice for OPD jobs.
"""
import json, datetime as dt, hashlib, re, collections, statistics
import openpyxl

TODAY = dt.date(2026, 9, 17)
N16 = '/root/exports/zoho/native/2026-09-16/'
N17 = '/root/exports/zoho/native/2026-09-17/sps/'
OUT = '/root/Production Dashboard/demo/data.json'

DIV = {  # Zoho division value -> (code, name, managers, coordinator per manager)
    'Offset Printing Division (OPD)': ('OPD', 'Offset Printing', ['Ranga', 'Ishan']),
    'Screen Printing Division (SHPS)': ('SHPS', 'Screen Printing', ['Mubeena']),
    'Paper Straw Unit (PSU)': ('PSU', 'Paper Straw', ['Ishan']),
    'Rewinding Unit (RWU)': ('RWU', 'Rewinding', ['Ishan']),
    'MOBA Punching Unit': ('MOBA', 'MOBA Punching', ['Ranga']),
    'Food Product Processing (FPP)': ('FPP', 'FPP', ['Ranga']),
    'Customized Packing Unit (CPU)': ('CPU', 'Customized Packing', ['Ranga']),  # user, 2026-09-17
}
COORD = {'Ranga': 'Nirmani', 'Ishan': 'Umanda', 'Mubeena': 'Madushi'}
CREATOR = {'OPD': 'Nimesha', 'MOBA': 'Nimesha', 'FPP': 'Nirmani', 'SHPS': 'Madushi', 'RWU': 'Umanda', 'PSU': 'Umanda', 'CPU': 'not specified'}

# brief §6 stage catalog; per-division order (MOBA/FPP/CPU assumed = OPD, not verified)
CAT = ['Artwork image', 'Item photo', 'Job card', 'Sales order', 'Bundle', 'Pick list', 'Package',
       'Shipment', 'Inventory adjustment', 'Sales invoice to SH', 'Purchase bill from SPS']
ORDER = {
    'OPD': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    'SHPS': [1, 2, 3, 4, 6, 5, 7, 8, 9, 10, 11],
    'PSU': [1, 2, 3, 4, 5, 7, 8, 9, 10, 11],
    'RWU': [2, 3, 4, 5, 7, 8, 9, 10, 11],
}
for c in ('MOBA', 'FPP', 'CPU'):
    ORDER[c] = ORDER['OPD']


def h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def d(v):
    if v is None or v == '':
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def clean(v):
    return (v or '').strip()


def first_dates(path, date_col, so_col):
    ws = openpyxl.load_workbook(path, read_only=True).active
    rows = ws.iter_rows(values_only=True)
    hdr = list(next(rows))
    i, j = hdr.index(date_col), hdr.index(so_col)
    out = {}
    for r in rows:
        so, dd = r[j], d(r[i])
        if so and dd and (so not in out or dd < out[so]):
            out[so] = dd
    return out


print('loading exports...')
sos = json.load(open(N17 + 'salesorders_headers.json'))
bundles = json.load(open(N17 + 'bundles.json'))
picks = json.load(open(N16 + 'parts/picklists.json'))
pkg = first_dates(N16 + 'Package_ALL.xlsx', 'Packing Date', 'SO Number')
shp = first_dates(N16 + 'Shipment_ALL.xlsx', 'Shipment Date', 'SO Number')
inv = first_dates(N16 + 'Invoice.xlsx', 'Invoice Date', 'Sales Order Number')

bun = {}
for b in bundles:
    m = re.match(r'\s*(JOBORDER-\d+)', (b.get('reference_number') or '').upper())
    dd = d(b.get('date'))
    if m and dd and b.get('status') == 'bundled':
        k = m.group(1)
        bun[k] = min(bun.get(k, dd), dd)
pck = {}
for p in picks:
    for so in (p.get('salesorder_numbers') or '').split(','):
        so, dd = so.strip(), d(p.get('date'))
        if so and dd:
            pck[so] = min(pck.get(so, dd), dd)
print('bundles', len(bun), 'picklists', len(pck), 'packages', len(pkg), 'shipments', len(shp), 'invoices', len(inv))

# ---- real dwell times, 2026 orders (all divisions in DIV), per stage transition
flow = [('Sales order', 'Bundle'), ('Bundle', 'Package'), ('Package', 'Shipment'), ('Shipment', 'Sales invoice to SH')]
dwell = {f'{a} → {b}': collections.defaultdict(list) for a, b in flow}
for s in sos:
    dv = DIV.get(s.get('cf_manufacturing_division'))
    if not dv or not (s['date'] >= '2026-01-01' and s['date'] <= '2026-09-15'):
        continue
    so = s['salesorder_number']
    dates = {'Sales order': d(s['date']), 'Bundle': bun.get(so), 'Package': pkg.get(so),
             'Shipment': shp.get(so), 'Sales invoice to SH': inv.get(so)}
    ctype = 'Ex stock' if clean(s.get('cf_order_type')) == 'Ex Stock' else 'Customised'
    for a, b in flow:
        if dates[a] and dates[b] and dates[b] >= dates[a]:
            dwell[f'{a} → {b}'][(dv[0], ctype)].append((dates[b] - dates[a]).days)


def med(xs):
    return round(statistics.median(xs), 1) if xs else None


dwell_out = []
for step, groups in dwell.items():
    for (div, ctype), xs in groups.items():
        dwell_out.append({'step': step, 'div': div, 'type': ctype, 'n': len(xs), 'median': med(xs),
                          'p90': sorted(xs)[int(0.9 * (len(xs) - 1))] if xs else None})

# ---- jobs: orders dated 1 Jul – 15 Sep 2026 in the six pilot-relevant divisions
jobs = []
for s in sos:
    dv = DIV.get(s.get('cf_manufacturing_division'))
    if not dv or not ('2026-07-01' <= s['date'] <= '2026-09-15'):
        continue
    code, dname, mgrs = dv
    so = s['salesorder_number']
    seed = h(so)
    mgr = mgrs[seed % len(mgrs)]
    otype = clean(s.get('cf_order_type'))
    customised = otype != 'Ex Stock'
    zdates = {4: d(s['date']), 5: bun.get(so), 7: pkg.get(so), 8: shp.get(so),
              10: inv.get(so)}
    order = ORDER[code]
    # simulated manual stages: ticked within 0–2 days of SO for most jobs; job card ticked once bundle/package exists
    stages = []
    so_date = zdates[4]
    for sid in order:
        st = {'id': sid, 'name': CAT[sid - 1], 'source': 'zoho' if sid >= 4 else 'manual', 'date': None, 'sim': False}
        if sid == 6:  # picklist list API carries no SO numbers -> simulated from package date
            if zdates[7]:
                st['date'] = zdates[7].isoformat()
            st['sim'] = True
        elif sid in zdates:
            st['date'] = zdates[sid].isoformat() if zdates[sid] else None
        elif sid in (1, 2):
            if (seed >> sid) % 10 < 8:
                st['date'] = (so_date + dt.timedelta(days=(seed >> (sid + 3)) % 3)).isoformat()
            st['sim'] = True
        elif sid == 3:
            if zdates[5] or zdates[7] or (seed % 10 < 5):
                st['date'] = (so_date + dt.timedelta(days=1 + (seed >> 7) % 4)).isoformat()
            st['sim'] = True
        elif sid == 9:  # inventory adjustment: cannot be linked to an SO from the export
            if zdates[8] and seed % 3:
                st['date'] = zdates[8].isoformat()
            st['sim'] = True
        elif sid == 11:  # SH side, not in this org
            if zdates[10] and seed % 2:
                st['date'] = (zdates[10] + dt.timedelta(days=(seed >> 5) % 6)).isoformat()
            st['sim'] = True
        stages.append(st)

    done = [x for x in stages if x['date']]
    last = max(done, key=lambda x: (x['date'], order.index(x['id']))) if done else None
    nxt = next((x for x in stages if not x['date']), None)

    qty = s.get('quantity') or 0
    packed = s.get('quantity_packed') or 0
    shipped = s.get('quantity_shipped') or 0
    exp_ship = d(s.get('shipment_date'))

    blockers = []
    art, dye, plate = clean(s.get('cf_artwork_availablility')), clean(s.get('cf_dye_cutter_availablity')), clean(s.get('cf_screen_plate_availability_2'))
    ref = clean(s.get('cf_sh_sales_order_ref'))
    open_job = s['shipped_status'] not in ('fulfilled', 'shipped')
    if open_job and customised:
        if art.lower().startswith('not av'):
            blockers.append('Artwork not available')
        if dye.lower().startswith('not av') and packed == 0:
            blockers.append('Dye cutter not available')
        if plate.lower().startswith('not av') and packed == 0:
            blockers.append('Screen plate not available')
    if open_job and ref.upper() == 'TO BE RECEIVED':
        blockers.append('Waiting on SH sales order')

    if s['shipped_status'] in ('fulfilled', 'shipped'):
        bucket = 'shipped'
    elif packed >= qty and qty:
        bucket = 'handoff'           # fully packed, waiting on Stores (shipment)
    elif packed > 0 or zdates[5]:
        bucket = 'production'
    else:
        received = (seed % 10) < 6   # simulated: file physically received by production
        bucket = 'production' if received else 'incoming'

    at_risk = open_job and exp_ship is not None and (exp_ship - TODAY).days <= 3 and packed < qty
    overdue = open_job and exp_ship is not None and exp_ship < TODAY

    holder = {'incoming': CREATOR[code], 'production': mgr, 'handoff': mgr, 'shipped': 'Darshani' if not zdates[10] else 'Closed'}[bucket]

    jobs.append({
        'so': so, 'job': clean(s.get('cf_job_no')) or clean(s.get('reference_number')),
        'div': code, 'divName': dname, 'manager': mgr, 'coordinator': COORD[mgr], 'creator': CREATOR[code],
        'customer': clean(s.get('cf_order_received_from')), 'material': clean(s.get('cf_material_to_be_used')),
        'type': 'Ex stock' if otype == 'Ex Stock' else ('Internal SH order' if otype == 'Internal SH Order' else 'Customised'),
        'nature': clean(s.get('cf_job_nature')), 'shRef': ref,
        'orderDate': s['date'], 'expShip': exp_ship.isoformat() if exp_ship else None,
        'qty': qty, 'packed': packed, 'shipped': shipped,
        'shippedStatus': s['shipped_status'], 'invoicedStatus': s['invoiced_status'],
        'value': s.get('total') or 0,
        'gates': {'artwork': art, 'dyeCutter': dye, 'screenPlate': plate},
        'stages': stages,
        'current': last['name'] if last else None, 'currentDate': last['date'] if last else None,
        'next': nxt['name'] if nxt else None,
        'blockers': blockers, 'bucket': bucket, 'atRisk': at_risk, 'overdue': overdue,
        'fileWith': holder, 'fileWithSim': True, 'mgrSim': code == 'OPD',
        'zohoCreated': s['created_time'][:10],
    })

# ---- COO trends, 2026: on-time (first shipment <= expected ship date) by month, shipped orders per ISO week
ontime = collections.defaultdict(lambda: [0, 0])
weekly = collections.Counter()
for s in sos:
    dv = DIV.get(s.get('cf_manufacturing_division'))
    so = s['salesorder_number']
    sd, ex = shp.get(so), d(s.get('shipment_date'))
    if not dv or not sd or sd < dt.date(2026, 1, 1) or sd > dt.date(2026, 9, 13):
        continue
    ctype = 'Ex stock' if clean(s.get('cf_order_type')) == 'Ex Stock' else 'Customised'
    wk = sd - dt.timedelta(days=sd.weekday())
    weekly[wk.isoformat()] += 1
    if ex:
        k = (sd.strftime('%Y-%m'), ctype)
        ontime[k][1] += 1
        ontime[k][0] += sd <= ex
trends = {
    'ontime': [{'month': m, 'type': t, 'on': v[0], 'n': v[1]} for (m, t), v in sorted(ontime.items())],
    'weekly': [{'week': w, 'n': n} for w, n in sorted(weekly.items())],
}

out = {'trends': trends, 'today': TODAY.isoformat(), 'snapshot': '2026-09-15/17', 'jobs': jobs, 'dwell': dwell_out,
       'stageCatalog': CAT, 'divisionOrder': ORDER}
for j in jobs:
    if j['bucket'] == 'shipped':
        j.pop('material'); j.pop('gates')
        j['stages'] = [{'id': x['id'], 'date': x['date']} for x in j['stages'] if x['id'] in (7, 8, 10)]
json.dump(out, open(OUT, 'w'), separators=(',', ':'))
print('ontime', trends['ontime'][-6:]); print('weekly', trends['weekly'][-6:])
c = collections.Counter
print('jobs', len(jobs), c(j['div'] for j in jobs), c(j['bucket'] for j in jobs))
print('blocked', sum(1 for j in jobs if j['blockers']), c(b for j in jobs for b in j['blockers']))
print('at risk', sum(j['atRisk'] for j in jobs), 'overdue', sum(j['overdue'] for j in jobs))
print('managers', c(j['manager'] for j in jobs))
for r in sorted(dwell_out, key=lambda r: (r['step'], r['div'], r['type'])):
    print(r)
