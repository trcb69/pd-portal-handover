#!/usr/bin/env python3
"""Deterministic demo dataset for the manager-preview production dashboard.
Backbone = real SPS sales-order lines from the 16 Sep 2026 Zoho export. Quantities the export does not
carry (bundled, shipped, picked) and all event times are generated from a hash of the line id.
No prices or amounts are ever read into the output. Run: python3 make_data.py"""
import openpyxl, warnings, json, hashlib, datetime as dt, collections, math, os, sys
warnings.simplefilter('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = '/root/exports/zoho/native/2026-09-16/Sales_Order.xlsx'
TODAY = dt.date(2026, 9, 15)                       # Tuesday, day before the export date
AS_OF = dt.datetime(2026, 9, 15, 16, 0)
LEGACY_DAYS = 180
K = {'package_missing': 2, 'shipment_missing': 3, 'invoice_missing': 2}   # spec section 3, working days

def H(*a):
    return int(hashlib.sha1('|'.join(map(str, a)).encode()).hexdigest(), 16)

# ---------- calendar (Mon-Fri, no holidays; same as seeded working_weekdays) ----------
def is_wd(d): return d.weekday() < 5
def nth_wd_after(d, k):
    n = 0
    while n < k:
        d += dt.timedelta(days=1)
        if is_wd(d): n += 1
    return d
def nth_wd_before(d, k):          # the date that is k working days before d (d itself counts as 0)
    n = 0
    while n < k:
        d -= dt.timedelta(days=1)
        if is_wd(d): n += 1
    return d

# ---------- division maps ----------
TAG = {'offset printing division (opd)': 'OPD', 'screen printing unit': 'SHPS', 'paper straw unit': 'PSU',
       'rewinding unit': 'RWU', 'moba unit': 'MOBA', 'moba punching unit': 'MOBA', 'food product processing unit': 'FPP',
       'customized packing unit': 'CPU', 'opd - packpro unit': 'PACKPRO',
       'digital printing unit': 'DPU', 'paper cup unit': 'PCU', 'paper cup lid unit': 'PCLU',
       'paper plate unit': 'PPU', 'cake wrapper unit': 'CWU'}
HEAD = {'offset printing division (opd)': 'OPD', 'screen printing division (shps)': 'SHPS', 'paper straw unit (psu)': 'PSU',
        'rewinding unit (rwu)': 'RWU', 'paper cup unit (pcu)': 'PCU', 'customized packing unit (cpu)': 'CPU',
        'moba punching unit': 'MOBA', 'paper cup lid unit': 'PCLU', 'food product processing (fpp)': 'FPP',
        'digital printing unit (dpu)': 'DPU', 'paper plate unit': 'PPU', 'cake wrapper unit': 'CWU'}
ORDER_TYPE = {'customized order': 'customised', 'ex stock': 'ex_stock', 'internal sh order': 'internal', 'make to order (mto)': 'customised'}
STAGE_ORDER = {'SHPS': [1,2,3,4,5,6,7,8,9,10,11], 'PSU': [1,2,3,4,5,7,8,9,10,11], 'RWU': [2,3,4,5,7,8,9,10,11]}
OPD_ORDER = [1,2,3,4,6,5,7,8,9,10,11]
STAGES = [(1,'Artwork image','ART'),(2,'Item photo (in system)','IMG'),(3,'Job card','JC'),(4,'Sales order','SO'),
          (5,'Bundle (produced)','BND'),(6,'Pick list','PICK'),(7,'Package','PKG'),(8,'Shipment','SHP'),
          (9,'Inventory adjustment','ADJ'),(10,'Sales invoice to SH','INV'),(11,'Purchase bill from SPS','BILL')]
NOT_TRACKED = {1,2,3,9,11}
DIVS = {'OPD': ('Offset Printing', ['ranga','ishan']), 'MOBA': ('MOBA (cups, punching)', ['ranga']),
        'FPP': ('Food Product Processing', ['ranga']), 'CPU': ('Customized Packing', ['ranga']),
        'PACKPRO': ('Packpro', ['ishan']), 'RWU': ('Rewinding', ['ishan']), 'PSU': ('Paper Straw', ['ishan']),
        'SHPS': ('Screen Printing', ['mubeena']),
        'PCU': ('Paper Cup (no manager)', []), 'DPU': ('Digital Printing (no manager)', []), 'CWU': ('Cake Wrapper (no manager)', [])}
PEOPLE = [{'id':'ranga','name':'Ranga','role':'manager','divisions':['OPD','MOBA','FPP','CPU']},
          {'id':'ishan','name':'Ishan','role':'manager','divisions':['PSU','OPD','PACKPRO','RWU']},
          {'id':'mubeena','name':'Mubeena','role':'manager','divisions':['SHPS']},
          {'id':'samitha','name':'Samitha','role':'gm','divisions':'all'},
          {'id':'admin','name':'Hadhee (IT)','role':'admin','divisions':'all'}]
QUOTA = {'SHPS':13,'MOBA':14,'CPU':10,'FPP':5,'PACKPRO':17,'RWU':6,'PSU':3,'OPD':6,'PCU':3,'DPU':1,'CWU':1}

def norm(s): return (s or '').strip().lower()
def num(x): return float(x or 0)

def load():
    ws = openpyxl.load_workbook(SRC, read_only=True).active
    it = ws.iter_rows(values_only=True); h = next(it)
    keep = ['SalesOrder ID','Order Date','Expected Shipment Date','SalesOrder Number','Status','Item Name','QuantityOrdered',
            'QuantityInvoiced','QuantityPacked','QuantityCancelled','Usage unit','Division','CF.Manufacturing Division',
            'CF.Order Type','CF.Job No','CF.Order Received from','Customer Name']   # no price / amount columns are read
    ix = {k: h.index(k) for k in keep}
    rows, seq = [], collections.Counter()
    for r in it:
        d = {k: r[i] for k, i in ix.items()}
        seq[d['SalesOrder ID']] += 1
        d['id'] = '%s-%d' % (d['SalesOrder ID'], seq[d['SalesOrder ID']])
        tag, head = norm(d['Division']), norm(d['CF.Manufacturing Division'])
        d['tag_code'] = TAG.get(tag) if tag else None
        d['head_code'] = HEAD.get(head) if head else None
        d['tag_unmapped'] = bool(tag) and d['tag_code'] is None     # includes 'opd - macpro unit': no alias in 002-seed.sql
        d['macpro'] = tag == 'opd - macpro unit'
        d['eff'] = num(d['QuantityOrdered']) - num(d['QuantityCancelled'])
        rows.append(d)
    return rows

def resolve(d):
    if d['tag_code']: return d['tag_code'], 'tag'
    if d['tag_unmapped']: return None, None
    if d['head_code']: return d['head_code'], 'header'
    return None, None

def open_real(d):
    p, i, e = num(d['QuantityPacked']), num(d['QuantityInvoiced']), d['eff']
    return d['Status'] != 'invoiced' and e > 0 and i <= p and not (p >= e and i >= e)

def select(rows):
    chosen = []                                   # (row, group)
    by = collections.defaultdict(list)
    for d in rows:
        code, _ = resolve(d)
        if code and open_real(d): by[code].append(d)
    for code, n in QUOTA.items():
        pool = sorted(by[code], key=lambda d: (d['Order Date'], d['id']), reverse=True)
        recent = [d for d in pool if (TODAY - d['Order Date'].date()).days <= LEGACY_DAYS]
        soon = [d for d in recent if hasattr(d['Expected Shipment Date'], 'date') and 0 <= (d['Expected Shipment Date'].date() - TODAY).days <= 3][:2]
        take = soon + [d for d in recent if d not in soon][:math.ceil(n * 0.7) - len(soon)]
        rest = sorted(recent[len(take):], key=lambda d: H('sel', d['id']))
        take += rest[:n - len(take)]
        if len(take) < n:
            take += sorted([d for d in pool if d not in take], key=lambda d: (d['Order Date']), reverse=True)[:n - len(take)]
        chosen += [(d, code) for d in take]
    mac = sorted([d for d in rows if d['macpro'] and open_real(d)], key=lambda d: d['Order Date'], reverse=True)[:3]       # real open, all legacy
    chosen += [(d, 'MACPRO') for d in mac]
    closed_mac = sorted([d for d in rows if d['macpro'] and d['Status'] == 'invoiced' and d['eff'] > 0],
                        key=lambda d: d['Order Date'], reverse=True)[:2]
    for d in closed_mac: d['reopened'] = True      # closed in Zoho; shown open so the demo has a live MacPro line
    chosen += [(d, 'MACPRO') for d in closed_mac]
    return chosen

# ---------- progress generation ----------
def ts(day, hour, minute=0):
    return dt.datetime.combine(day, dt.time(hour, minute))
def iso(t): return t.strftime('%Y-%m-%dT%H:%M:%S+05:30') if t else None
def clamp_day(d, lo): return max(d, lo)

def build_job(d, group, plan):
    jid = d['id']; created = d['Order Date'].date(); due = d['Expected Shipment Date'].date() if hasattr(d['Expected Shipment Date'],'date') else None
    eff = int(d['eff']); ordered = int(num(d['QuantityOrdered'])); canc = int(num(d['QuantityCancelled']))
    rp, ri = int(num(d['QuantityPacked'])), int(num(d['QuantityInvoiced']))
    reopened = d.get('reopened', False)
    age = (TODAY - created).days
    demo = set()
    prof = plan.get(jid, {})
    bundled = packed = shipped = invoiced = 0
    t_bundle = t_pack = t_ship = t_inv = None      # event DATES (latest change)
    seen = {}
    if prof.get('kind') in ('pkg_stuck','ship_stuck','inv_stuck','ship_fresh','inv_fresh','pkg_edge','ship_edge','inv_edge'):
        kind = prof['kind']; ev = prof['event']        # ev = latest-event date
        bundled = eff; demo |= {'qty_bundled','qty_packed','qty_shipped','qty_invoiced'}
        if kind.startswith('pkg'):
            t_bundle = ev
        elif kind.startswith('ship'):
            packed = eff if H('pk', jid) % 2 else max(1, int(eff * 0.6)); t_pack = ev; t_bundle = ev - dt.timedelta(days=2)
            if prof.get('part_shipped'): shipped = invoiced = max(1, packed // 3); t_ship = ev - dt.timedelta(days=1)
        else:
            packed = shipped = eff if H('pk', jid) % 2 else max(1, int(eff * 0.6)); invoiced = max(0, shipped // 2) if prof.get('part_inv') else 0
            t_ship = ev; t_pack = ev - dt.timedelta(days=1); t_bundle = ev - dt.timedelta(days=3)
            if invoiced: t_inv = ev - dt.timedelta(days=1)
    elif rp > 0 and not reopened:                  # real packed/invoiced; generate bundled and shipped only
        packed, invoiced = rp, ri; bundled = eff
        demo |= {'qty_bundled','qty_shipped'}
        stuck = H('st', jid) % 100 < 40
        mode = H('md', jid) % 2
        if packed == invoiced:
            shipped = packed; ev = TODAY - dt.timedelta(days=2 + H('e', jid) % 8)
            t_inv = ev; t_ship = ev - dt.timedelta(days=1); t_pack = t_ship
        elif mode:                                  # shipped = packed, invoice lagging
            shipped = packed
            ev = nth_wd_before(TODAY, 2 + H('e', jid) % 3) if stuck else TODAY - dt.timedelta(days=H('e', jid) % 2)
            t_ship = ev; t_pack = ev - dt.timedelta(days=1)
            if invoiced: t_inv = ev - dt.timedelta(days=1)
        else:                                       # shipped = invoiced, shipment lagging
            shipped = invoiced
            ev = nth_wd_before(TODAY, 3 + H('e', jid) % 3) if stuck else TODAY - dt.timedelta(days=H('e', jid) % 2)
            t_pack = ev
            if shipped: t_ship = t_inv = ev - dt.timedelta(days=1)
        t_bundle = (t_pack or TODAY) - dt.timedelta(days=2)
    else:                                           # nothing packed in Zoho: generate bundle progress only
        demo |= {'qty_bundled'}
        if reopened: demo |= {'qty_packed','qty_shipped','qty_invoiced'}
        x = H('prof', jid) % 100
        if age <= 2 or x < 45: pass
        elif x < 70: bundled = max(1, int(eff * (0.3 + (H('b', jid) % 5) / 10.0))); t_bundle = TODAY - dt.timedelta(days=H('e', jid) % 4)
        else: bundled = eff; t_bundle = TODAY - dt.timedelta(days=H('e', jid) % 2)
    # chain: every change date on or after creation; first-seen dates are never later than the change dates
    def fix(t): return None if t is None else min(max(t, created), TODAY)
    if invoiced and t_inv is None: t_inv = t_ship or t_pack
    t_bundle, t_pack, t_ship, t_inv = map(fix, (t_bundle, t_pack, t_ship, t_inv))
    produced = max(bundled, packed)
    picked = packed if packed > 0 else (bundled if (bundled and H('pick', jid) % 3) else 0)
    s_inv = t_inv if invoiced else None
    s_ship = (min(t_ship, s_inv) if s_inv else t_ship) if shipped else None
    s_pack = (min(t_pack, s_ship) if s_ship else t_pack) if packed else None
    s_bund = (min(t_bundle, s_pack) if s_pack else t_bundle) if bundled else None
    s_pack, s_ship, s_inv = [None if x is None else max(x, created) for x in (s_pack, s_ship, s_inv)]
    s_bund = None if s_bund is None else max(s_bund, created)
    at = {4: ts(created, 8, H('c', jid) % 60)}
    if bundled: at[5] = ts(s_bund, 9, H('m5', jid) % 60)
    if picked: at[6] = ts(s_pack or s_bund, 10, H('m6', jid) % 60)
    if packed: at[7] = ts(s_pack, 11, H('m7', jid) % 60)
    if shipped: at[8] = ts(s_ship, 13, H('m8', jid) % 60)
    if invoiced: at[10] = ts(s_inv, 15, H('m10', jid) % 50)
    def st(q): return 'done' if q >= eff else ('partial' if q > 0 else 'not_done')
    order = STAGE_ORDER.get(group, OPD_ORDER)
    strip = []
    for sid in order:
        if sid in NOT_TRACKED: strip.append({'stage_id': sid, 'state': 'not_tracked', 'at': None}); continue
        if sid == 4: s = 'done'
        elif sid == 5: s = 'detected' if bundled > 0 else 'not_detected'
        elif sid == 6: s = st(picked)
        elif sid == 7: s = st(packed)
        elif sid == 8: s = st(shipped)
        else: s = st(invoiced)
        strip.append({'stage_id': sid, 'state': s, 'at': iso(at.get(sid)) if s not in ('not_done', 'not_detected') else None})
    if picked: demo.add('strip.pick_list')
    demo.add('strip.at')
    # missing-document rules (spec section 3), measured from the generated change dates
    missing = []
    legacy = (TODAY - created).days > LEGACY_DAYS
    def chk(code, stage, cond, x):
        if cond and x is not None and not legacy:
            thr = nth_wd_after(x, K[code])
            if thr <= TODAY: missing.append({'code': code, 'stage_id': stage, 'since': thr.isoformat()})
    chk('package_missing', 7, bundled >= eff and packed == 0, t_bundle)
    chk('shipment_missing', 8, packed > shipped, t_pack)
    chk('invoice_missing', 10, shipped > invoiced, t_ship)
    code, src = resolve(d)
    conflict = bool(d['tag_code'] and d['head_code'] and d['tag_code'] != d['head_code'])
    job_no = (d['CF.Job No'] or '').strip() or None
    reasons = []
    if code is None: reasons.append('unmapped_division' if d['tag_unmapped'] else 'no_division')
    if conflict: reasons.append('division_conflict')
    if code is not None and not DIVS.get(code, ('', []))[1]: reasons.append('no_manager')
    if job_no is None: reasons.append('no_job_no')
    real = ['so','division','division_source','division_conflict','order_type','customer','item','unit','qty_ordered','created']
    if due: real.append('due_date')       # due_date is null where Zoho has none
    if job_no: real.append('job_no')
    if canc == int(num(d['QuantityCancelled'])): real.append('qty_cancelled')
    if 'qty_packed' not in demo: real.append('qty_packed')
    if 'qty_invoiced' not in demo: real.append('qty_invoiced')
    if 'qty_cancelled' not in demo: real.append('qty_effective')
    demo |= {'qty_produced', 'flag_status'}
    if 'qty_effective' not in real: demo.add('qty_effective')
    ot = ORDER_TYPE.get(norm(d['CF.Order Type']), 'customised')
    job = {'id': jid, 'so': d['SalesOrder Number'], 'job_no': job_no, 'division': code, 'division_source': src,
           'division_conflict': conflict, 'order_type': ot,
           'customer': (d['CF.Order Received from'] or d['Customer Name'] or '').strip(),
           'item': (d['Item Name'] or '').strip(), 'unit': (d['Usage unit'] or '').strip() or None,
           'qty_ordered': ordered, 'qty_cancelled': canc, 'qty_effective': eff, 'qty_bundled': bundled,
           'qty_produced': produced, 'qty_packed': packed, 'qty_shipped': shipped, 'qty_invoiced': invoiced,
           'created': created.isoformat(), 'due_date': due.isoformat() if due else None, 'strip': strip, 'missing': missing,
           'flag_status': 'current', 'unassigned_reasons': reasons,
           'real_fields': sorted(set(real)), 'demo_fields': sorted(demo)}
    job['_ev'] = {k: (v.isoformat() if v else None) for k, v in (('bundle', t_bundle), ('pack', t_pack), ('ship', t_ship))}
    return job

def make_plan(chosen):
    """Hand-pick which jobs show each problem, by deterministic hash order inside each manager's own jobs."""
    plan = {}
    def cands(groups, need_age=5):
        out = [d for d, g in chosen if g in groups and (TODAY - d['Order Date'].date()).days >= need_age
               and (TODAY - d['Order Date'].date()).days <= LEGACY_DAYS and not (num(d['QuantityPacked']) > 0)
               and not d.get('reopened')]
        return sorted(out, key=lambda d: H('plan', d['id']))
    used = set()
    def pick(groups, n, kind, **kw):
        got = 0
        for d in cands(groups):
            if d['id'] in used or any(d['SalesOrder ID'] == x['SalesOrder ID'] for x in [] ): continue
            if (kw['event'] - d['Order Date'].date()).days < 3: continue
            used.add(d['id'])
            plan[d['id']] = dict(kind=kind, **{k: v for k, v in kw.items()})
            got += 1
            if got == n: break
    R, I, M = {'MOBA','CPU','FPP','OPD'}, {'PACKPRO','RWU','PSU','OPD'}, {'SHPS'}
    pk = lambda n: nth_wd_before(TODAY, n)
    pick(R, 2, 'pkg_stuck', event=pk(4)); pick(I, 2, 'pkg_stuck', event=pk(5)); pick(M, 1, 'pkg_stuck', event=pk(3))
    pick(R, 1, 'pkg_edge', event=pk(1)); pick(I, 1, 'pkg_edge', event=pk(2))           # edge: threshold today
    pick(R, 2, 'ship_stuck', event=pk(5)); pick(I, 2, 'ship_stuck', event=pk(6), part_shipped=True)
    pick(M, 1, 'ship_stuck', event=pk(4)); pick(R, 1, 'ship_edge', event=pk(3)); pick(I, 1, 'ship_edge', event=pk(2))
    pick(R, 2, 'inv_stuck', event=pk(4)); pick(I, 2, 'inv_stuck', event=pk(3), part_inv=True)
    pick(M, 1, 'inv_stuck', event=pk(3)); pick(I, 1, 'inv_edge', event=pk(1))
    pick(R, 2, 'ship_fresh', event=TODAY - dt.timedelta(days=1)); pick(I, 2, 'ship_fresh', event=TODAY)
    pick(R | I | M, 2, 'inv_fresh', event=TODAY - dt.timedelta(days=1))
    return plan

def main():
    rows = load()
    chosen = select(rows)
    plan = make_plan(chosen)
    jobs = [build_job(d, g, plan) for d, g in chosen]
    # flag status is per SO (spec section 2): choose 3 'checking' and 1 'sync_problem' SOs
    flagged = sorted([j for j in jobs if j['missing']], key=lambda j: H('fs', j['id']))
    plain = sorted([j for j in jobs if not j['missing'] and 'legacy' != '' and (TODAY - dt.date.fromisoformat(j['created'])).days <= LEGACY_DAYS
                    and j['qty_shipped'] < j['qty_effective']], key=lambda j: H('fs2', j['id']))
    status_by_so = {}
    for j, s in [(flagged[0], 'checking'), (flagged[1], 'checking'), (plain[0], 'checking'), (flagged[2], 'sync_problem')]:
        status_by_so[j['so']] = s
    for j in jobs:
        j['flag_status'] = status_by_so.get(j['so'], 'current')
        if j['flag_status'] != 'current': j['missing'] = []      # spec: flags hidden unless 'current'
    timers = {j['id']: j.pop('_ev') for j in jobs}
    with open(os.path.join(HERE, 'data.timers.json'), 'w') as f: json.dump(timers, f, indent=0)
    jobs.sort(key=lambda j: (j['division'] or '', j['due_date'] or '9999', j['so']))
    used = {j['division'] for j in jobs if j['division']}
    divisions = []
    for c in ['OPD','SHPS','PSU','RWU','MOBA','FPP','CPU','PACKPRO','PCU','DPU','CWU']:
        if c in used:
            divisions.append({'code': c, 'name': DIVS[c][0], 'managers': DIVS[c][1], 'stages': STAGE_ORDER.get(c, OPD_ORDER)})
    out = {'as_of': iso(AS_OF), 'today': TODAY.isoformat(),
           'source_note': 'Order lines, customers, items, quantities ordered and cancelled, due dates and division tags are real rows from the 16 Sep 2026 Zoho sales-order export; bundled, shipped, picked quantities, event times and the checking / sync-problem states are generated for the demo (see each job\'s demo_fields).',
           'people': PEOPLE, 'divisions': divisions,
           'stages': [{'id': i, 'name': n, 'short': s, 'tracked': i not in NOT_TRACKED} for i, n, s in STAGES],
           'jobs': jobs}
    with open(os.path.join(HERE, 'data.json'), 'w') as f: json.dump(out, f, indent=1, ensure_ascii=False)
    print('wrote data.json,', len(jobs), 'jobs')

if __name__ == '__main__': main()
