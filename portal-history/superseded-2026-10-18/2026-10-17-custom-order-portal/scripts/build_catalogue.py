"""usage: build_catalogue.py SO.xlsx ITEM.xlsx OUTDIR  -> catalogue csv, end-customers csv, stats.json (read-only on inputs)"""
import sys, os, csv, json, re, statistics as st, difflib
from datetime import datetime
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import openpyxl, warnings
warnings.filterwarnings("ignore")
def rows(path, sheet):
    ws = openpyxl.load_workbook(path, read_only=True)[sheet]
    it = ws.iter_rows(values_only=True); h = list(next(it))
    for r in it:
        if all(v is None or v == '' for v in r): continue
        yield dict(zip(h, r)), h
so_p, item_p, out = sys.argv[1:4]
items = {}
dup_items = []
for r, _ in rows(item_p, "Item"):
    if r['Item ID'] in items: dup_items.append(r['Item ID'])
    items.setdefault(r['Item ID'], r)
so = [r for r, _ in rows(so_p, "Sales Order")]
END = max(r['Order Date'] for r in so)
def months_back(d, m):
    y, mo = d.year, d.month - m
    while mo < 1: mo += 12; y -= 1
    return d.replace(year=y, month=mo)
C24, C12 = months_back(END, 24), months_back(END, 12)
S = lambda v: (str(v).strip() if v is not None else '')
def merged(txt, boo):
    t = S(txt)
    if t: return t
    return 'Available' if S(boo).lower() == 'true' else ''   # bool false is the unfilled default -> unknown
for r in so:
    r['_art'] = merged(r['CF.Artwork Availablility'], r['CF.Artwork Availability'])
    r['_dye'] = merged(r['CF.Dye Cutter Availablity'], r['CF.Dye Cutter Availability'])
    r['_scr'] = merged(r['CF.Screen / Plate Availability'], r['CF.Screen / Plate Available'])
    r['_cust'] = S(r['CF.Order Received from'])
    r['_nature'] = S(r['CF.Job Nature'])
by_item = defaultdict(list)
for r in so: by_item[r['Product ID']].append(r)
def med(x): return round(st.median(x), 2) if x else ''
def top(c, n=1): return '; '.join(f"{k} ({v})" for k, v in c.most_common(n))
def kind(n):
    for pre, k in (('Service','SERVICE'),('RTP','RTP'),('PRINTSERV','PRINTSERV'),('PACKSERV','PACKSERV'),('SP-','SP'),('CP-','CP'),('Sub','SUB'),('SH-','SH'),('DP-','DP')):
        if n.strip().startswith(pre): return k
    return 'OTHER'
def tag(n):
    m = re.findall(r'\(([^()]*)\)\s*$', n.strip()); return m[-1].strip() if m else ''
cat = []
for iid, it in items.items():
    if it['CF.Finished Good Type'] != 'Customized': continue
    L = sorted(by_item.get(iid, []), key=lambda r: r['Order Date'])
    last = L[-1]['Order Date'] if L else None
    active = it['Status'] == 'Active'
    if not (active or (last and last >= C24)): continue
    pr = [r['Item Price'] for r in L if isinstance(r['Item Price'], (int, float))]
    q = [r['QuantityOrdered'] for r in L if isinstance(r['QuantityOrdered'], (int, float))]
    nat = Counter(r['_nature'] for r in L if r['_nature'])
    natt = sum(nat.values())
    def flag(k): return sum(1 for r in L if r[k].lower().startswith('not av'))
    cu = Counter(r['_cust'] for r in L if r['_cust'])
    unit = Counter(S(r['Usage unit']) for r in L if S(r['Usage unit'])).most_common(1)
    cat.append({
        'item_id': iid, 'name': it['Item Name'], 'sku': S(it['SKU']),
        'unit': unit[0][0] if unit else S(it['Unit']), 'unit_source': 'SO usage unit' if unit else 'item master Unit',
        'name_kind': kind(it['Item Name']), 'name_customer_tag': tag(it['Item Name']), 'product_type': S(it['Product Type']),
        'cf_bu': S(it['CF.BU']), 'item_division': S(it['Division']),
        'manufacturing_division': top(Counter(S(r['CF.Manufacturing Division']) for r in L if S(r['CF.Manufacturing Division']))).rsplit(' (', 1)[0] if L else '',
        'status': it['Status'], 'finished_good_nature': S(it['CF.Finished Good Nature']), 'finished_good_category': S(it['CF.Finished Good Category']),
        'stock_on_hand_item_master_16sep': it['Stock On Hand'] if it['Stock On Hand'] is not None else '',
        'order_lines': len(L), 'order_lines_customized_type': sum(1 for r in L if r['CF.Order Type'] == 'Customized Order'),
        'distinct_sos': len({r['SalesOrder Number'] for r in L}),
        'first_order': L[0]['Order Date'].date().isoformat() if L else '', 'last_order': last.date().isoformat() if last else '',
        'last_price': pr and L[-1]['Item Price'] if pr else '', 'median_price': med(pr),
        'median_qty': med(q), 'min_qty': min(q) if q else '', 'max_qty': max(q) if q else '',
        'top3_end_customers': '; '.join(f"{k} ({v})" for k, v in cu.most_common(3)),
        'base_material': top(Counter(S(r['CF.Base Material to be Used']) for r in L if S(r['CF.Base Material to be Used']))),
        'other_material': top(Counter(S(r['CF.Additional Other Material to be Used (If any)']) for r in L if S(r['CF.Additional Other Material to be Used (If any)']))),
        'job_nature_filled_lines': natt, 'share_reorder': round(nat['Reorder'] / natt, 3) if natt else '',
        'share_new_order': round(nat['New Order'] / natt, 3) if natt else '',
        'artwork_ever_not_available': 'Y' if flag('_art') else 'N', 'dye_cutter_ever_not_available': 'Y' if flag('_dye') else 'N',
        'screen_plate_ever_not_available': 'Y' if flag('_scr') else 'N',
        'artwork_not_available_lines': flag('_art'), 'dye_not_available_lines': flag('_dye'), 'screen_not_available_lines': flag('_scr'),
        'live_12m': 'Y' if last and last >= C12 else 'N',
    })
cat.sort(key=lambda d: (-d['order_lines'], d['name']))
os.makedirs(out, exist_ok=True)
with open(f"{out}/customized-catalogue.csv", "w", newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, cat[0].keys()); w.writeheader(); w.writerows(cat)

# ---- end customers (all SO lines on catalogued Customized items' type? -> lines whose item is Customized in master)
cust_ids = {iid for iid, it in items.items() if it['CF.Finished Good Type'] == 'Customized'}
cl = defaultdict(list)
for r in so:
    if r['_cust']: cl[r['_cust']].append(r)
def norm(s): return re.sub(r'[^a-z0-9]+', '', s.lower())
groups = defaultdict(list)
for n in cl: groups[norm(n)].append(n)
names = sorted(cl)
near = defaultdict(set)
blocks = defaultdict(list)
for n in names: blocks[norm(n)[:3]].append(n)
for b in blocks.values():
    for i, a in enumerate(b):
        for c in b[i+1:]:
            na, nc = norm(a), norm(c)
            if na == nc: continue
            if difflib.SequenceMatcher(None, na, nc).ratio() >= 0.88 or (min(len(na), len(nc)) >= 6 and (na.startswith(nc) or nc.startswith(na))):
                near[a].add(c); near[c].add(a)
ec = []
for n, L in cl.items():
    L.sort(key=lambda r: r['Order Date'])
    ic = Counter(r['Item Name'] for r in L if r['Product ID'] in cust_ids)
    ec.append({'end_customer': n, 'order_lines': len(L), 'distinct_sos': len({r['SalesOrder Number'] for r in L}),
        'customized_item_lines': sum(ic.values()), 'distinct_customized_items': len(ic),
        'first_order': L[0]['Order Date'].date().isoformat(), 'last_order': L[-1]['Order Date'].date().isoformat(),
        'top5_items': '; '.join(f"{k} ({v})" for k, v in ic.most_common(5)),
        'same_after_normalising_case_punctuation': ' | '.join(x for x in groups[norm(n)] if x != n),
        'near_variants_unmerged': ' | '.join(sorted(near[n]))})
ec.sort(key=lambda d: (-d['order_lines'], d['end_customer']))
with open(f"{out}/end-customers.csv", "w", newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, ec[0].keys()); w.writeheader(); w.writerows(ec)

# ---- stats
cs = [d for d in cat]; N = len(cs)
ordered = [d for d in cs if d['order_lines']]
sd = {}
sd['dates'] = {'last_order_in_file': END.date().isoformat(), 'cut24': C24.date().isoformat(), 'cut12': C12.date().isoformat()}
sd['item_master'] = {'rows': len(items) + len(dup_items), 'unique_ids': len(items), 'dup_ids': dup_items,
    'type': Counter(it['CF.Finished Good Type'] for it in items.values()),
    'customized_active': sum(1 for it in items.values() if it['CF.Finished Good Type'] == 'Customized' and it['Status'] == 'Active'),
    'customized_inactive': sum(1 for it in items.values() if it['CF.Finished Good Type'] == 'Customized' and it['Status'] != 'Active')}
sd['catalogue'] = {'items': N, 'active': sum(d['status'] == 'Active' for d in cs), 'inactive_but_ordered_24m': sum(d['status'] != 'Active' for d in cs),
    'active_never_ordered': sum(d['status'] == 'Active' and d['order_lines'] == 0 for d in cs),
    'active_not_ordered_24m_but_ordered_before': sum(d['status'] == 'Active' and d['order_lines'] > 0 and d['last_order'] < C24.date().isoformat() for d in cs),
    'live_12m': sum(d['live_12m'] == 'Y' for d in cs), 'ordered_24m_not_12m': sum(d['live_12m'] == 'N' and d['last_order'] >= C24.date().isoformat() for d in cs),
    'ordered_once_lines': sum(d['order_lines'] == 1 for d in cs), 'ordered_once_ever_items_with_1_so': sum(d['distinct_sos'] == 1 for d in cs),
    'ge10_lines': sum(d['order_lines'] >= 10 for d in cs), 'ge25_lines': sum(d['order_lines'] >= 25 for d in cs),
    'lines_total': sum(d['order_lines'] for d in cs)}
ls = sorted((d['order_lines'] for d in cs), reverse=True); tot = sum(ls)
for k in (10, 20, 50, 100, 200):
    sd['catalogue'][f'top{k}_share_lines'] = round(sum(ls[:k]) / tot, 3)
live = [d for d in cs if d['live_12m'] == 'Y']
sd['kind_all'] = Counter(d['name_kind'] for d in cs); sd['kind_live'] = Counter(d['name_kind'] for d in live)
sd['product_type'] = Counter(d['product_type'] for d in cs); sd['product_type_live'] = Counter(d['product_type'] for d in live)
sd['service_with_orders'] = sum(1 for d in cs if d['product_type']=='service' and d['order_lines'])
sd['tag_present_live'] = sum(1 for d in live if d['name_customer_tag'])
sd['live_goods'] = sum(1 for d in live if d['product_type']=='goods')
sd['live_by_division'] = Counter(d['manufacturing_division'] for d in live)
sd['cat_by_bu'] = Counter(d['cf_bu'] for d in cs)
sd['missing'] = {k: sum(1 for d in cs if d[k] in ('', None)) for k in ('sku', 'unit', 'cf_bu', 'item_division', 'manufacturing_division', 'base_material', 'finished_good_nature', 'finished_good_category')}
sd['missing_live'] = {k: sum(1 for d in live if d[k] in ('', None)) for k in ('sku', 'unit', 'cf_bu', 'item_division', 'manufacturing_division', 'base_material')}
sd['live_units'] = Counter(d['unit'] for d in live)
sd['mfg_div_conflicts'] = sum(1 for iid in cust_ids if len({S(r['CF.Manufacturing Division']) for r in by_item.get(iid, []) if S(r['CF.Manufacturing Division'])}) > 1)
nm = Counter(d['name'].strip().lower() for d in cs); sd['dup_names_in_catalogue'] = [k for k, v in nm.items() if v > 1]
sd['name_prefix'] = Counter(re.match(r'^[A-Za-z]+-?', d['name']).group(0) if re.match(r'^[A-Za-z]+-?', d['name']) else '(none)' for d in cs).most_common(12)
sd['name_oddities'] = {'leading_trailing_space': sum(d['name'] != d['name'].strip() for d in cs), 'double_space': sum('  ' in d['name'] for d in cs), 'len_gt_90': sum(len(d['name']) > 90 for d in cs)}
# SO line level
lines = [r for r in so]
item_type = lambda r: items[r['Product ID']]['CF.Finished Good Type'] if r['Product ID'] in items else 'NOT IN MASTER'
sd['lines'] = {'total': len(so), 'by_item_type': Counter(item_type(r) for r in so),
    'order_type_x_item_type': dict(Counter(r['CF.Order Type']+' | '+item_type(r) for r in so))}
sd['lines']['not_in_master_names'] = Counter(r['Item Name'] for r in so if r['Product ID'] not in items).most_common(30)
sd['lines']['customized_cancelled_lines'] = sum(1 for r in so if r['Product ID'] in cust_ids and (r['QuantityCancelled'] or 0) > 0)
sd['lines']['customized_lines'] = sum(1 for r in so if r['Product ID'] in cust_ids)
# customized item ordered as non-custom type
sd['lines']['custom_item_exstock_lines'] = sum(1 for r in so if r['Product ID'] in cust_ids and r['CF.Order Type'] == 'Ex Stock')
# fill rates over lines on catalogued/customized items (lines whose item is Customized in master)
cl_lines = [r for r in so if r['Product ID'] in cust_ids]
def fr(f, L):
    n = len(L); k = sum(1 for r in L if f(r)); return [k, n, round(100 * k / n, 1) if n else None]
fields = {
 'Item (Product ID)': lambda r: S(r['Product ID']), 'Quantity ordered': lambda r: isinstance(r['QuantityOrdered'], (int, float)) and r['QuantityOrdered'] > 0,
 'Usage unit': lambda r: S(r['Usage unit']), 'Expected Shipment Date': lambda r: r['Expected Shipment Date'],
 'Expected ship date differs from order date': lambda r: r['Expected Shipment Date'] and r['Expected Shipment Date'] != r['Order Date'],
 'CF.Order Received from (end customer)': lambda r: r['_cust'], 'CF.Base Material to be Used': lambda r: S(r['CF.Base Material to be Used']),
 'CF.Additional Other Material': lambda r: S(r['CF.Additional Other Material to be Used (If any)']),
 'CF.SH Sales Order Ref': lambda r: S(r['CF.SH Sales Order Ref']), 'CF.Job No': lambda r: S(r['CF.Job No']),
 'CF.Order Type': lambda r: S(r['CF.Order Type']), 'CF.Manufacturing Division': lambda r: S(r['CF.Manufacturing Division']),
 'CF.Clickup Link': lambda r: S(r['CF.Clickup Link']), 'Artwork (merged old bool + new text)': lambda r: r['_art'],
 'Dye cutter (merged)': lambda r: r['_dye'], 'Screen/plate (merged)': lambda r: r['_scr'], 'CF.Job Nature': lambda r: r['_nature'],
 'Division (SO line)': lambda r: S(r['Division']), 'PurchaseOrder (customer PO ref)': lambda r: S(r['PurchaseOrder']),
 'Sales Person': lambda r: S(r['Sales Person']), 'Notes': lambda r: S(r['Notes']), 'Item Desc': lambda r: S(r['Item Desc']),
 'Delivery Method': lambda r: S(r['Delivery Method']), 'Sales Channel': lambda r: S(r['Sales Channel']), 'Shipping Address': lambda r: S(r['Shipping Address']),
 'Item Price': lambda r: isinstance(r['Item Price'], (int, float)) and r['Item Price'] > 0,
}
sd['fill_all'] = {k: fr(f, cl_lines) for k, f in fields.items()}
y26 = [r for r in cl_lines if r['Order Date'] >= datetime(2026, 1, 1)]
sd['fill_2026'] = {k: fr(f, y26) for k, f in fields.items()}
ct = [r for r in cl_lines if r['CF.Order Type'] == 'Customized Order']
sd['fill_custtype'] = {k: fr(f, ct) for k, f in fields.items()}
sd['values'] = {k: Counter(S(r[k]) for r in cl_lines).most_common(15) for k in ('_art', '_dye', '_scr', '_nature', 'CF.Order Type', 'Sales Person', 'Delivery Method', 'Sales Channel', 'Status', 'Warehouse Name')}
sd['values']['artwork_bool_true_text_empty'] = sum(1 for r in cl_lines if S(r['CF.Artwork Availability']).lower() == 'true' and not S(r['CF.Artwork Availablility']))
sd['values']['text_empty_rows_by_year'] = Counter(r['Order Date'].year for r in cl_lines if not S(r['CF.Job Nature']))
sd['values']['rows_by_year'] = Counter(r['Order Date'].year for r in cl_lines)
sd['values']['qty_unit_mismatch'] = sum(1 for d in cs if d['unit'] and items[d['item_id']]['Unit'] and d['unit'].lower() != S(items[d['item_id']]['Unit']).lower() and d['order_lines'])
# end customers
sd['end_customers'] = {'distinct': len(ec), 'lines_with_value': sum(e['order_lines'] for e in ec), 'normalised_groups_gt1': sum(1 for g in groups.values() if len(g) > 1),
    'names_in_normalised_groups': sum(len(g) for g in groups.values() if len(g) > 1), 'names_with_near_variants': sum(1 for n in near if near[n]),
    'single_order': sum(e['order_lines'] == 1 for e in ec), 'ge10_lines': sum(e['order_lines'] >= 10 for e in ec),
    'top10_share': round(sum(e['order_lines'] for e in ec[:10]) / sum(e['order_lines'] for e in ec), 3),
    'active_12m': sum(e['last_order'] >= C12.date().isoformat() for e in ec),
    'top10': [(e['end_customer'], e['order_lines']) for e in ec[:10]],
    'top_custom_share': {}}
cust_lines_total = sum(1 for r in so if r['_cust']); sd['end_customers']['lines_total_all_types'] = len(so)
sd['end_customers']['customer_name_is_SH_lines'] = sum(1 for r in so if 'standard holdings' in S(r['Customer Name']).lower())
sd['end_customers']['by_order_type_filled'] = {t: fr(lambda r: r['_cust'], [r for r in so if r['CF.Order Type'] == t]) for t in ('Customized Order', 'Ex Stock', 'Internal SH Order', 'Make to Order (MTO)')}
sd['end_customers']['blank_on_customized_lines'] = sum(1 for r in cl_lines if not r['_cust'])
json.dump(sd, open(f"{out}/stats.json", "w"), indent=1, default=str, ensure_ascii=False)
print("ok", N)
