"""Sample screens of the production dashboard's "My jobs" page for Ranga, Ishan and Mubeena (and the GM view),
built from the 22 real SPS sales-order lines in the dev fixture (test/fixtures/zoho/sps-detail-22.json, Zoho pull
of late Sep 2026) and the rules of the manager-preview spec (Rev 11). Mockups only: the screen itself is not built yet.
Run: python3 make_mockups.py  -> <manager>.html + <manager>.png"""
import json, html, subprocess, datetime as dt
from pathlib import Path

D = Path(__file__).parent
FIX = json.load(open('/root/dev/production-dashboard/test/fixtures/zoho/sps-detail-22.json'))
TODAY = dt.date(2026, 9, 30); AS_OF = '10:05'
e = html.escape

TAG2DIV = {'Paper Straw Unit': 'PSU', 'OPD - PackPro Unit': 'PACKPRO', 'MOBA Unit': 'MOBA', 'MOBA Punching Unit': 'MOBA',
           'Screen Printing Unit': 'SHPS', 'Customized Packing Unit': 'CPU', None: 'RWU'}       # RWU lines carry no tag; header gives RWU (AC19)
DIVNAME = {'PSU': 'Paper Straw', 'PACKPRO': 'Packpro', 'MOBA': 'MOBA', 'SHPS': 'Screen Printing', 'CPU': 'Customized Packing', 'RWU': 'Rewinding', 'OPD': 'Offset'}
MANAGERS = {'Ranga': ['OPD', 'MOBA', 'FPP', 'CPU'], 'Ishan': ['PSU', 'OPD', 'PACKPRO', 'RWU'], 'Mubeena': ['SHPS']}
STAGES = {'SHPS': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 'PSU': [1, 2, 3, 4, 5, 7, 8, 9, 10, 11], 'RWU': [2, 3, 4, 5, 7, 8, 9, 10, 11]}
SNAME = {1: 'Artwork', 2: 'Item photo', 3: 'Job card', 4: 'Sales order', 5: 'Bundle', 6: 'Pick list', 7: 'Package', 8: 'Shipment', 9: 'Inv. adjustment',
         10: 'Invoice to SH', 11: 'Bill from SPS'}
# Illustrative flags (the real rules need observed timestamps the fixture does not hold): one per screen, marked as a sample.
SAMPLE_FLAG = {'JOBORDER-08589': ('Shipment missing', 'packed 105, nothing shipped for 3 working days'),
               'JOBORDER-08561': ('Package missing', 'bundled, nothing packed for 2 working days'),
               'JOBORDER-08593': ('Package missing', 'bundled, nothing packed for 2 working days')}

jobs = []
for s in FIX:
    for l in s['line_items']:
        tag = next((t['tag_option_name'] for t in l.get('tags', []) if t.get('tag_name') == 'Division'), None)
        div = TAG2DIV.get(tag, 'OTHER')
        q = l['quantity']; pk, sh, iv = l.get('quantity_packed', 0), l.get('quantity_shipped', 0), l.get('quantity_invoiced', 0)
        due = dt.date.fromisoformat(s['shipment_date'])
        jobs.append(dict(so=s['salesorder_number'], job=l.get('project_name') or '—', div=div, item=l['name'], qty=q, produced=pk, packed=pk, shipped=sh, invoiced=iv,
                         due=due, late=(TODAY - due).days if due < TODAY and sh < q else 0, bundle=pk > 0))
        if SAMPLE_FLAG.get(s['salesorder_number'], ('',))[0] == 'Package missing':     # the rule needs a full bundle first
            jobs[-1].update(bundle=True, produced=q)


def st(v, q):
    return 'done' if v >= q else 'partial' if v > 0 else 'not_done'


def strip(j):
    order = STAGES.get(j['div'], [1, 2, 3, 4, 6, 5, 7, 8, 9, 10, 11])
    out = []
    for sid in order:
        if sid in (1, 2, 3, 9, 11): s = 'not_tracked'
        elif sid == 4: s = 'done'
        elif sid == 5: s = 'detected' if j['bundle'] else 'not_detected'
        elif sid == 6: s = st(j['packed'], j['qty'])           # pick list follows packing in this sample
        else: s = st({7: j['packed'], 8: j['shipped'], 10: j['invoiced']}[sid], j['qty'])
        icon = {'done': ('✔', '#0f766e', '#ccfbf1'), 'detected': ('✔', '#0f766e', '#ccfbf1'), 'partial': ('½', '#b45309', '#fef3c7'),
                'not_done': ('✘', '#b91c1c', '#fee2e2'), 'not_detected': ('○', '#94a3b8', '#f1f5f9'), 'not_tracked': ('·', '#cbd5e1', '#f8fafc')}[s]
        out.append(f"<span class='st' title='{SNAME[sid]}: {s.replace('_', ' ')}' style='color:{icon[1]};background:{icon[2]}'>{icon[0]}</span>")
    return ''.join(out)


CSS = '''<style>
*{box-sizing:border-box;margin:0}body{font:13px/1.45 Inter,system-ui,Segoe UI,Arial;background:#f1f5f9;color:#0f172a;width:1440px}
.top{display:flex;justify-content:space-between;align-items:center;background:#0f172a;color:#e2e8f0;padding:12px 28px}
.top b{font-size:15px;color:#fff}.top .u{font-size:12px}.top .u span{background:#134e4a;color:#99f6e4;border-radius:99px;padding:2px 9px;margin-left:6px}
.wrap{padding:18px 28px}.fresh{color:#475569;font-size:12px;margin-bottom:12px}.fresh b{color:#0f766e}
.cards{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:14px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:12px 14px}.card b{display:block;font-size:26px;letter-spacing:-.02em}
.card span{color:#64748b;font-size:12px}.card.red b{color:#b91c1c}.card.amb b{color:#b45309}.card small{display:block;color:#94a3b8;font-size:11px;margin-top:2px}
.filters{display:flex;gap:8px;margin-bottom:10px}.chip{border:1px solid #cbd5e1;background:#fff;border-radius:99px;padding:4px 12px;font-size:12px;color:#334155}
.chip.on{background:#0f766e;border-color:#0f766e;color:#fff}
table{width:100%;border-collapse:separate;border-spacing:0;background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden}
th{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#64748b;text-align:left;padding:8px 10px;background:#f8fafc;border-bottom:1px solid #e2e8f0}
td{padding:8px 10px;border-bottom:1px solid #f1f5f9;vertical-align:middle}tr:last-child td{border-bottom:0}
.so{color:#0f766e;font-weight:600;text-decoration:underline}.n{text-align:right;font-variant-numeric:tabular-nums}
.strip{white-space:nowrap}.st{display:inline-flex;width:20px;height:20px;border-radius:5px;align-items:center;justify-content:center;font-size:12px;margin-right:2px;font-weight:700}
.miss{background:#fee2e2;color:#991b1b;border-radius:99px;padding:2px 8px;font-size:11px;font-weight:600;white-space:nowrap}.ck{color:#94a3b8;font-size:11px}
.div{background:#f1f5f9;border-radius:6px;padding:1px 7px;font-size:11px;color:#334155}.late{color:#b91c1c;font-weight:600}
.legend{display:flex;gap:14px;color:#64748b;font-size:11px;margin-top:10px}.note{margin-top:8px;color:#94a3b8;font-size:11px}
</style>'''


def page(user, divs, role='Production manager'):
    mine = [j for j in jobs if j['div'] in divs]
    mine.sort(key=lambda j: (-j['late'], j['due']))
    openj = [j for j in mine if j['shipped'] < j['qty']]
    c = dict(due3=sum(TODAY <= j['due'] <= TODAY + dt.timedelta(days=3) for j in openj), past=sum(j['due'] < TODAY for j in openj),
             prod=sum(j['produced'] < j['qty'] for j in openj), pns=sum(j['produced'] >= j['qty'] for j in openj),
             miss=sum(j['so'] in SAMPLE_FLAG for j in openj))
    rows = ''.join(f"""<tr><td>{e(j['job'])}</td><td style='white-space:nowrap'><span class='so'>{j['so'].replace('JOBORDER-', 'JO-')}</span></td><td>{e(j['item'][:34])}</td>
      <td><span class='div'>{DIVNAME.get(j['div'], j['div'])}</span></td><td class='n'>{j['qty']:,}</td><td class='n'>{j['produced']:,}</td><td class='n'>{j['shipped']:,}</td>
      <td class='n'>{j['invoiced']:,}</td><td style='white-space:nowrap'>{j['due'].strftime('%d %b')}</td><td class='{'late' if j['late'] else ''}'>{f"{j['late']} d" if j['late'] else '—'}</td>
      <td class='strip'>{strip(j)}</td><td>{f"<span class='miss'>{SAMPLE_FLAG[j['so']][0]}</span> <span class='ck'>checked 10:05</span>" if j['so'] in SAMPLE_FLAG and j['shipped'] < j['qty'] else ''}</td></tr>""" for j in mine)
    divchips = ''.join(f"<span class='chip'>{DIVNAME.get(d, d)}</span>" for d in divs)
    return f'''<!doctype html><html><head><meta charset="utf-8">{CSS}</head><body>
<div class="top"><b>SPS Production · My jobs</b><div class="u">{user}<span>{role}</span></div></div>
<div class="wrap"><div class="fresh">Zoho data as of <b>{AS_OF}</b> (Colombo) · refreshes every 15 min · read-only, nothing here changes Zoho</div>
<div class="cards"><div class="card amb"><b>{c['due3']}</b><span>Due in 3 days</span></div><div class="card red"><b>{c['past']}</b><span>Past due</span></div>
<div class="card"><b>{c['prod']}</b><span>In production</span></div><div class="card"><b>{c['pns']}</b><span>Produced, not shipped</span></div>
<div class="card red"><b>{c['miss']}</b><span>Documents missing</span><small>being checked: 0</small></div></div>
<div class="filters"><span class="chip on">Open</span><span class="chip">All</span><span class="chip">Documents missing only</span>{divchips}</div>
<table><thead><tr><th>Job no</th><th>SO</th><th>Item</th><th>Division</th><th class="n">Ordered</th><th class="n">Produced</th><th class="n">Shipped</th><th class="n">Invoiced</th>
<th>Due</th><th>Late</th><th>Documentation strip <span style='text-transform:none;letter-spacing:0;color:#94a3b8'>(hover a box for the step)</span></th><th>Missing</th></tr></thead><tbody>{rows or '<tr><td colspan=12>No jobs</td></tr>'}</tbody></table>
<div class="legend"><span>✔ done</span><span>½ part done</span><span>✘ not done</span><span>○ no bundle seen</span><span>· not tracked yet (artwork, photo, job card, adjustment, bill)</span></div>
<div class="note">Sample: real SPS order lines and quantities from the Zoho sample of late Sep 2026, seen as on 30 Sep. "Produced" uses packed qty, and the missing-document chips are sample values; the live screen derives both from Zoho bundles and the time each step was first seen.</div>
</div></body></html>''', len(mine)


for user, divs in list(MANAGERS.items()) + [('Samitha', sorted({j['div'] for j in jobs}))]:
    h, n = page(user, divs, 'GM · all divisions' if user == 'Samitha' else 'Production manager')
    f = D / f'{user}.html'; f.write_text(h)
    height = 400 + 62 * max(n, 1)
    subprocess.run(['google-chrome', '--headless=new', '--no-sandbox', '--hide-scrollbars', f'--window-size=1440,{height}', f'--screenshot={D / (user + ".png")}', f'file://{f}'],
                   capture_output=True, timeout=120)
    print(user, n, 'jobs')
