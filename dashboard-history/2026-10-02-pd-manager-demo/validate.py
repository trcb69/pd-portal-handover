#!/usr/bin/env python3
"""Independent check of data.json against the spec rules (recomputes flags from the strip/quantities where possible)."""
import json, datetime as dt, collections, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data.json'))); T = json.load(open(os.path.join(HERE, 'data.timers.json')))
today = dt.date.fromisoformat(D['today']); err = []
divs = {d['code']: d for d in D['divisions']}; stages = {s['id'] for s in D['stages']}
assert len(stages) == 11
wd = lambda d: d.weekday() < 5
def wdays_between(a, b):            # working days d with a < d <= b
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1); n += wd(d)
    return n
KEYS = {'id','so','job_no','division','division_source','division_conflict','order_type','customer','item','unit','qty_ordered','qty_cancelled','qty_effective','qty_bundled','qty_produced','qty_packed','qty_shipped','qty_invoiced','created','due_date','strip','missing','flag_status','unassigned_reasons','real_fields','demo_fields'}
ids = set()
for j in D['jobs']:
    p = j['so']
    if set(j) != KEYS: err.append((p, 'keys', set(j) ^ KEYS))
    if j['id'] in ids: err.append((p, 'dup id'))
    ids.add(j['id'])
    if j['division'] and j['division'] not in divs: err.append((p, 'division missing from divisions', j['division']))
    if j['qty_effective'] != j['qty_ordered'] - j['qty_cancelled']: err.append((p, 'eff'))
    if not (0 <= j['qty_invoiced'] <= j['qty_shipped'] <= j['qty_packed'] <= j['qty_effective']): err.append((p, 'qty chain'))
    if j['qty_produced'] != max(j['qty_bundled'], j['qty_packed']): err.append((p, 'produced'))
    if j['qty_bundled'] > j['qty_effective']: err.append((p, 'bundled > eff'))
    if j['qty_shipped'] >= j['qty_effective'] and j['qty_invoiced'] >= j['qty_effective']: err.append((p, 'closed job in demo'))
    order = divs[j['division']]['stages'] if j['division'] else [1,2,3,4,6,5,7,8,9,10,11]
    if [s['stage_id'] for s in j['strip']] != order: err.append((p, 'strip order'))
    created = dt.date.fromisoformat(j['created'])
    if created > today: err.append((p, 'created in future'))
    q = {7: j['qty_packed'], 8: j['qty_shipped'], 10: j['qty_invoiced']}
    for s in j['strip']:
        sid, st = s['stage_id'], s['state']
        if sid in (1,2,3,9,11) and st != 'not_tracked': err.append((p, 'tracked state', sid))
        if sid in q:
            exp = 'done' if q[sid] >= j['qty_effective'] else 'partial' if q[sid] > 0 else 'not_done'
            if st != exp: err.append((p, 'strip state', sid, st, exp))
        if sid == 5 and st != ('detected' if j['qty_bundled'] > 0 else 'not_detected'): err.append((p, 'bundle state'))
        if s['at'] and dt.datetime.fromisoformat(s['at']) > dt.datetime.fromisoformat(D['as_of']): err.append((p, 'at in future', sid))
        if s['at'] and dt.datetime.fromisoformat(s['at']).date() < created: err.append((p, 'at before created', sid))
    ats = [dt.datetime.fromisoformat(s['at']) for s in j['strip'] if s['at'] and s['stage_id'] in (4,5,7,8,10)]
    if ats != sorted(ats): err.append((p, 'strip times out of order'))
    legacy = (today - created).days > 180
    if j['flag_status'] != 'current' and j['missing']: err.append((p, 'flags shown while not current'))
    if legacy and j['missing']: err.append((p, 'flag on legacy'))
    at = {s['stage_id']: s['at'] for s in j['strip']}
    for m in j['missing']:
        since = dt.date.fromisoformat(m['since']); c = m['code']
        k = {'package_missing': 2, 'shipment_missing': 3, 'invoice_missing': 2}[c]
        cond = {'package_missing': j['qty_bundled'] >= j['qty_effective'] and j['qty_packed'] == 0,
                'shipment_missing': j['qty_packed'] > j['qty_shipped'],
                'invoice_missing': j['qty_shipped'] > j['qty_invoiced']}[c]
        if not cond: err.append((p, c, 'condition false'))
        if m['stage_id'] != {'package_missing': 7, 'shipment_missing': 8, 'invoice_missing': 10}[c]: err.append((p, c, 'stage'))
        if since > today: err.append((p, c, 'threshold in future'))
        if not wd(since): err.append((p, c, 'since not a working day'))
        t = T[j['id']]; x = dt.date.fromisoformat({'package_missing': t['bundle'], 'shipment_missing': t['pack'], 'invoice_missing': t['ship']}[c])
        if wdays_between(x, since) != k: err.append((p, c, 'since is not x + k working days', x, since))
        if wdays_between(x, today) < k: err.append((p, c, 'flag raised before threshold'))
    # reverse check: a job meeting a rule's condition at/after its threshold must carry the flag unless hidden or legacy
    t = T[j['id']]
    if j['flag_status'] == 'current' and not legacy:
        for c, cond, x in (('package_missing', j['qty_bundled'] >= j['qty_effective'] and j['qty_packed'] == 0, t['bundle']),
                           ('shipment_missing', j['qty_packed'] > j['qty_shipped'], t['pack']),
                           ('invoice_missing', j['qty_shipped'] > j['qty_invoiced'], t['ship'])):
            due_flag = cond and x and wdays_between(dt.date.fromisoformat(x), today) >= {'package_missing': 2, 'shipment_missing': 3, 'invoice_missing': 2}[c]
            if bool(due_flag) != any(m['code'] == c for m in j['missing']): err.append((p, c, 'flag presence wrong', due_flag))
    # unassigned reasons consistent
    r = set(j['unassigned_reasons'])
    if (j['division'] is None) != bool(r & {'no_division', 'unmapped_division'}): err.append((p, 'reason/division'))
    if j['division_conflict'] != ('division_conflict' in r): err.append((p, 'conflict reason'))
    if j['division'] and not divs[j['division']]['managers'] != ('no_manager' in r): err.append((p, 'no_manager reason'))
    if (j['job_no'] is None) != ('no_job_no' in r): err.append((p, 'no_job_no'))
    # no money keys
    if re.search(r'price|amount|total|rate|cents|balance', ' '.join(j.keys())): err.append((p, 'money key'))
    if set(j['real_fields']) & set(j['demo_fields']): err.append((p, 'real/demo overlap', set(j['real_fields']) & set(j['demo_fields'])))
for dv in D['divisions']:
    if set(dv['stages']) - stages: err.append(('division', dv['code']))
print('ERRORS:', len(err)); [print(' ', e) for e in err[:40]]
# ---------- summary ----------
J = D['jobs']; P = D['people']
def vis(pr): return [j for j in J if pr['divisions'] == 'all' or j['division'] in pr['divisions']]
def legacy(j): return (today - dt.date.fromisoformat(j['created'])).days > 180
def counters(js):
    js = [j for j in js if j['qty_shipped'] < j['qty_effective'] and not legacy(j)]
    dd = lambda j: dt.date.fromisoformat(j['due_date']) if j['due_date'] else None
    return {'open': len(js),
            'due3': sum(1 for j in js if dd(j) and today <= dd(j) <= today + dt.timedelta(days=3)),
            'past_due': sum(1 for j in js if dd(j) and dd(j) < today),
            'in_production': sum(1 for j in js if j['qty_produced'] < j['qty_effective']),
            'produced_not_shipped': sum(1 for j in js if j['qty_produced'] >= j['qty_effective']),
            'docs_missing': sum(1 for j in js if j['missing'])}
for pr in P: print(pr['id'], 'jobs', len(vis(pr)), counters(vis(pr)))
print('by division', dict(collections.Counter(j['division'] for j in J)))
print('flags', dict(collections.Counter(m['code'] for j in J for m in j['missing'])), 'flag_status', dict(collections.Counter(j['flag_status'] for j in J)))
print('reasons', dict(collections.Counter(r for j in J for r in j['unassigned_reasons'])), 'unassigned jobs', sum(1 for j in J if j['unassigned_reasons']))
print('source', dict(collections.Counter(j['division_source'] for j in J)), 'null due', sum(1 for j in J if not j['due_date']), 'legacy', sum(map(legacy, J)))
short = [j for j in J if 0.9 <= j['qty_shipped'] / j['qty_effective'] < 1 and j['qty_shipped'] == j['qty_invoiced']]
print('closed-short candidates', len(short), collections.Counter(j['division'] for j in short))
print('total', len(J), 'size', os.path.getsize(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')))
sys.exit(1 if err else 0)
