# Part C: item process routes for items sold on SPS SOs, 12 months (16 Sep 2025 - 15 Sep 2026). Measured from saved pulls.
import openpyxl, collections, json, re, csv, warnings
warnings.filterwarnings('ignore')
S='/root/exports/zoho/native/2026-09-19/sps/'
items={i['item_id']:i for i in json.load(open(S+'items.json'))['rows']}
byname={i['name'].strip().lower():i for i in items.values()}
boms={b['composite_item_id']:b for b in json.load(open(S+'boms.json'))['rows']}
comp={c['composite_item_id']:c for c in json.load(open(S+'composite_items_list.json'))['rows']}
bund=[x for x in json.load(open(S+'bundles_and_recent_sos.json'))['bundles']['rows'] if x['date']>='2025-09-16']
adj=json.load(open(S+'inventory_adjustments_12m_detail.json'))['rows']
tro=json.load(open(S+'transfer_orders_detail.json'))['rows']
wb=openpyxl.load_workbook('/root/exports/zoho/native/2026-09-16/Sales_Order.xlsx',read_only=True)
ws=wb.active; it=ws.iter_rows(values_only=True); h=next(it); ix={n:i for i,n in enumerate(h)}
rows=[{k:r[i] for k,i in ix.items()} for r in it if '2025-09-16'<=str(r[ix['Order Date']])[:10]<='2026-09-15']
BU={'PACPRO':'PackPro','OPD':'OPD-Offset','MOBA':'MOBA','MOBA - PAPER CUP':'MOBA-Cup','PCU':'PCU(cup)','MOBA PUNCHING':'MOBA-Punch','SHP':'SHPS','RWU':'RWU','PSU':'PSU','FPP':'FPP','DPU':'DPU','CUSTOMIZED PACKING UNIT':'CPU','COMMON':'Common','MOBA - PAPER PLATE':'MOBA-Plate','MOBA - CAKE WRAPPER':'MOBA-Cake'}
def bu(i): return BU.get(i.get('cf_bu'), i.get('cf_bu') or '?')
def chain(cid, seen=()):
    """sub-assembly units, deepest first, then the item's own unit"""
    out=[]
    b=boms.get(cid)
    if b:
        for m in b['mapped_items']:
            if m.get('product_type')=='goods' and m['item_id'] in boms and m['item_id'] not in seen:
                out+=chain(m['item_id'],seen+(cid,))
    out.append(bu(items.get(cid,{})))
    return out
def dedup(l):
    o=[]
    for x in l:
        if not o or o[-1]!=x: o.append(x)
    return o
bund_by=collections.defaultdict(list)
for x in bund: bund_by[x['composite_item_id']].append(x)
adj_by=collections.defaultdict(lambda:[0,collections.Counter()])
for a in adj:
    for l in a['line_items']:
        adj_by[l['item_id']][0]+=1
        for t in l.get('tags',[]):
            if t['tag_name']=='Division': adj_by[l['item_id']][1][t['tag_option_name']]+=1
sold=collections.defaultdict(lambda:{'so':set(),'tags':collections.Counter(),'hdr':collections.Counter(),'lines':0})
for r in rows:
    i=items.get(str(r['Product ID'])) or byname.get(str(r['Item Name']).strip().lower())
    if not i: continue
    s=sold[i['item_id']]; s['so'].add(r['SalesOrder Number']); s['lines']+=1
    s['tags'][r['Division'] or '(none)']+=1; s['hdr'][r['CF.Manufacturing Division']]+=1
res=[]
for iid,s in sold.items():
    i=items[iid]
    typ='composite/assembly' if iid in boms else ('service' if i['product_type']=='service' else 'plain inventory item')
    if iid in boms:
        ch=dedup(chain(iid)); n_sub=sum(1 for m in boms[iid]['mapped_items'] if m['item_id'] in boms)
        depth=len(ch)-1
    else: ch=[bu(i)]; n_sub=0
    route=' > '.join(ch) if iid in boms else 'direct('+bu(i)+')'
    rm_units=set()
    if iid in boms:
        for m in boms[iid]['mapped_items']:
            if m.get('product_type')=='goods' and m['item_id'] not in boms:
                c=items.get(m['item_id'],{}).get('cf_raw_material_category') or ''
                rm_units.add(c.split()[0] if c and c!='NA' else '')
    tags=[t for t in s['tags'] if t!='(none)']
    nb=bund_by.get(iid,[])
    crossed=len(set(ch))>1
    res.append(dict(item=i['name'],item_id=iid,current_type=typ,item_master_unit=bu(i),parent_cat=i.get('cf_parent_category'),route=route,
        n_sub_assemblies=n_sub,so_count=len(s['so']),order_lines=s['lines'],line_tags=';'.join(f'{k}:{v}' for k,v in s['tags'].most_common()),
        header_divisions=';'.join(f'{k}:{v}' for k,v in s['hdr'].most_common()),
        crosses_units_in_bom='yes' if crossed else 'no', distinct_line_tags=len(tags),
        bundles_12m=len(nb),bundle_makers=';'.join(sorted({x['created_by_name'].strip() for x in nb})),adjustment_lines_12m=adj_by[iid][0] if iid in adj_by else 0))
res.sort(key=lambda r:-r['so_count'])
with open('routes.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
print('items sold',len(res))
print(collections.Counter(r['current_type'] for r in res))
rc=collections.Counter(r['route'] for r in res); print('distinct routes',len(rc))
for k,v in rc.most_common(25): print(v,k, sum(r['so_count'] for r in res if r['route']==k))
print('cross-unit BOM items',sum(r['crosses_units_in_bom']=='yes' for r in res),'SO-lines on them',sum(r['order_lines'] for r in res if r['crosses_units_in_bom']=='yes'),'of',sum(r['order_lines'] for r in res))
print('items with >1 distinct line tag',sum(r['distinct_line_tags']>1 for r in res))
print('items with bundle in 12m',sum(r['bundles_12m']>0 for r in res),' composite items w/o bundle',sum(1 for r in res if r['current_type'].startswith('comp') and r['bundles_12m']==0))
# bundle-makers per route
bm=collections.Counter(r['bundle_makers'] for r in res if r['bundles_12m']); print(bm.most_common(12))
# SO-level: same JOBORDER bundled items of different composite -> real multi-step
ref=collections.defaultdict(list)
for x in bund:
    m=re.match(r'\s*(JOBORDER-\d+)',x['reference_number'])
    if m: ref[m.group(1)].append(x)
multi=[v for v in ref.values() if len({x['composite_item_id'] for x in v})>1]
print('SOs with bundles',len(ref),'with >1 distinct composite item bundled',len(multi))
makers=collections.Counter(tuple(sorted({x['created_by_name'].strip() for x in v})) for v in multi); print(makers.most_common(8))
ex=[]
for v in multi[:400]:
    if len({x['created_by_name'] for x in v})>1: ex.append([(x['date'],x['composite_item_name'][:28],x['created_by_name'].split()[0]) for x in sorted(v,key=lambda x:x['created_time'])])
print(len(ex)); 
for e in ex[:4]: print(e)
