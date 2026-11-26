"""P0b: SH stock by location set (a, b, c), last-12-month ordered customized items. Read-only on all sources.
Usage: stock_by_location_p0b.py CACHEDIR OUTDIR   (CACHEDIR has so.pkl; OUTDIR = .../data, writes OUTDIR/stock-by-location-p0b.json)
Free-stock field: location_actual_available_for_sale_stock (routing contract); old location_available_for_sale_stock side by side.
SH-own lines dropped: nfkc/trim/collapse-space/lower(CF.Order Received from) == 'standard holdings (pvt) ltd' (spec s6 name_key).
Unit alias: pcs == nos only (case-insensitive); box/pack/pks not aliased. SH only; snapshot 28 Sep 2026."""
import sys,json,glob,csv,pickle,re,unicodedata
from collections import Counter,defaultdict
from datetime import timedelta
C,O=sys.argv[1],sys.argv[2]
RAW='/root/exports/zoho/native/2026-09-28/sh-rizwan/items/detail/batch_*.json'
A=['Southern Warehouse (Warehouse)','Central Warehouse (Warehouse)','3PL Warehouse (DWW)']; K='SPS Kohalwila Factory (Warehouse)'
SETS={'a':A,'b':A+[K],'c':[K]}
NEW,OLD='location_actual_available_for_sale_stock','location_available_for_sale_stock'
nk=lambda s:re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s or '').strip()).lower()
SHOWN=nk('Standard Holdings (Pvt) Ltd')
sh={}; ident={'rows':0,'mismatch_rows':0,'by_location':{},'max_abs_diff':0.0,'examples':[]}
for f in sorted(glob.glob(RAW)):
    for r in json.load(open(f))['records']:
        it=r['item']; sh[it['item_id']]=it
        for l in it.get('locations',[]):
            d=(l.get('location_stock_on_hand') or 0)-(l.get('location_actual_committed_stock') or 0)-(l.get(NEW) or 0)
            b=ident['by_location'].setdefault(l['location_name'],[0,0]); b[0]+=1; ident['rows']+=1
            if abs(d)>1e-9:
                b[1]+=1; ident['mismatch_rows']+=1; ident['max_abs_diff']=max(ident['max_abs_diff'],abs(d))
                if len(ident['examples'])<5: ident['examples'].append({'item':it['name'],'loc':l['location_name'],'on_hand':l.get('location_stock_on_hand'),'actual_committed':l.get('location_actual_committed_stock'),'actual_free':l.get(NEW)})
ident['by_location']={k:{'rows':v[0],'mismatch':v[1]} for k,v in ident['by_location'].items()}
for s in SETS.values():
    for n in s: assert n in ident['by_location'],n
cat={r['item_id']:r for r in csv.DictReader(open(O+'/customized-catalogue.csv'))}
st=[r for r in csv.DictReader(open(O+'/customized-stock.csv')) if int(r['lines_last12m'])>0]
ids={r['sps_item_id'] for r in st}
SO=pickle.load(open(C+'/so.pkl','rb'))
win=max(l['Order Date'] for l in SO if l['Order Date'])-timedelta(days=365)
all_l=Counter(); own_l=Counter()
for l in SO:
    i=str(l['Product ID'])
    if i in ids and l['Order Date']>win:
        all_l[i]+=1
        if nk(l['CF.Order Received from'])==SHOWN: own_l[i]+=1
assert sum(all_l.values())==3527
for r in st: assert all_l[r['sps_item_id']]==int(r['lines_last12m'])
lines_ex={i:all_l[i]-own_l[i] for i in all_l}; lines_all=dict(all_l)
basis=[r for r in st if lines_ex[r['sps_item_id']]>0]
norm=lambda s:(s or '').strip().lower()
al=lambda s:'nos' if norm(s)=='pcs' else norm(s)
def cls(r,locs,fld,alias):
    it=sh.get(r['sh_item_id'])
    if not r['sh_item_id'] or it is None: return 'UNKNOWN'
    free=sum(l.get(fld) or 0 for l in it.get('locations',[]) if l['location_name'] in locs)
    u=al if alias else norm
    if r['sps_item_id'] not in cat or u(it.get('unit'))!=u(cat[r['sps_item_id']]['unit']): return 'UNIT_MISMATCH'
    m=float(r['typical_order_qty_median'])
    return 'FULL' if free>=m else 'PARTIAL' if free>0 else 'NONE'
def run(rows,lines,locs,fld,alias):
    t=sum(lines[r['sps_item_id']] for r in rows); cl=defaultdict(lambda:[0,0])
    for r in rows:
        c=cls(r,locs,fld,alias); cl[c][0]+=lines[r['sps_item_id']]; cl[c][1]+=1
    return {c:{'lines':v[0],'pct':round(100*v[0]/t,1),'items':v[1]} for c,v in sorted(cl.items())}
out={'snapshot':'SH items 28 Sep 2026; SPS stock not used',
 'definitions':{'sh_own':"name_key == 'standard holdings (pvt) ltd'",'unit_alias':'pcs==nos only; items absent from the catalogue count as UNIT_MISMATCH','fields':{'main':NEW,'old_for_comparison':OLD},'sets':SETS},
 'basis_before_dropping_SH_own':{'lines':sum(all_l.values()),'items':len(st)},
 'sh_own_lines_dropped':sum(own_l.values()),'items_with_sh_own_lines':len(own_l),
 'basis_after':{'lines':sum(lines_ex.values()),'items':len(basis)},
 'identity_check':{'formula':'location_stock_on_hand - location_actual_committed_stock == location_actual_available_for_sale_stock (tol 1e-9), all SH location rows',**ident},'results':{}}
for k,locs in SETS.items():
    out['results'][k]={'MAIN_actual_SHown_dropped_alias_ON':run(basis,lines_ex,locs,NEW,True),
      'old_field_SHown_dropped_alias_ON':run(basis,lines_ex,locs,OLD,True),
      'actual_SHown_dropped_alias_OFF':run(basis,lines_ex,locs,NEW,False),
      'actual_SHown_KEPT_alias_ON':run(st,lines_all,locs,NEW,True)}
json.dump(out,open(O+'/stock-by-location-p0b.json','w'),indent=1)
print(json.dumps({k:out[k] for k in ('basis_before_dropping_SH_own','sh_own_lines_dropped','items_with_sh_own_lines','basis_after')}))
i=out['identity_check'];print({x:i[x] for x in i if x!='formula'})
for s,v in out['results'].items():
  for m,c in v.items():print(s,m,{k:(x['lines'],x['pct'],x['items']) for k,x in c.items()})
