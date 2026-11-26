"""P0: SH stock by location set for the last-12-month ordered customized items. Read-only on all sources.
Usage: python3.12 -I stock_by_location.py SO_XLSX CATALOGUE_CSV STOCK_CSV OUTDIR [SH_BATCH_GLOB]
  SO_XLSX       /root/exports/zoho/sps/2026-09-27/item1/Sales_Order.xlsx  (SPS order lines, as stock_routing.py)
  CATALOGUE_CSV data/customized-catalogue.csv   (columns item_id, unit)
  STOCK_CSV     data/customized-stock.csv       (written by stock_routing.py: sh_item_id, sh_match_method, typical_order_qty_median)
  OUTDIR        report folder; writes OUTDIR/data/stock-by-location-summary.json
  SH_BATCH_GLOB default /root/exports/zoho/native/2026-09-28/sh-rizwan/items/detail/batch_*.json (RAW, not the slim cache)
Snapshot: SH 28 Sep 2026 (stale; shape only). SPS stock is never read. SH and SPS numbers are never summed."""
import sys,json,glob,csv,warnings,re
from collections import Counter,defaultdict
from datetime import timedelta
import openpyxl
warnings.filterwarnings('ignore')
SOX,CAT,STK,OUT=sys.argv[1:5]
RAW=sys.argv[5] if len(sys.argv)>5 else '/root/exports/zoho/native/2026-09-28/sh-rizwan/items/detail/batch_*.json'
A=['Southern Warehouse (Warehouse)','Central Warehouse (Warehouse)','3PL Warehouse (DWW)']
SETS={'a':A,'b':A+['SPS Kohalwila Factory (Warehouse)']}
F_SOH,F_COM,F_AFS='location_stock_on_hand','location_actual_committed_stock','location_actual_available_for_sale_stock'
SH_OWN='Standard Holdings (Pvt) Ltd'
ALIAS={'nos','pcs','piece','pieces','each'}

# ---- SH raw
sh={}; locnames=Counter(); keys=set()
ident={'rows':0,'fail':0,'fail_in_sets':0,'rows_in_sets':0,'examples':[],'missing_field_rows':0}
for f in sorted(glob.glob(RAW)):
    for r in json.load(open(f))['records']:
        it=r['item']; sh[it['item_id']]=it
        for l in it.get('locations',[]):
            locnames[l['location_name']]+=1; keys|=set(l)
            if any(l.get(k) is None for k in (F_SOH,F_COM,F_AFS)): ident['missing_field_rows']+=1; continue
            ident['rows']+=1; ins=l['location_name'] in SETS['b']
            ident['rows_in_sets']+=ins
            if abs(l[F_SOH]-l[F_COM]-l[F_AFS])>1e-9:
                ident['fail']+=1; ident['fail_in_sets']+=ins
                if len(ident['examples'])<5: ident['examples'].append({'item_id':it['item_id'],'loc':l['location_name'],'soh':l[F_SOH],'committed':l[F_COM],'afs':l[F_AFS]})
for s in SETS.values():
    for n in s: assert n in locnames,('location string not in data',n)

# ---- basis items
cat={r['item_id']:r for r in csv.DictReader(open(CAT))}
st={r['sps_item_id']:r for r in csv.DictReader(open(STK)) if int(r['lines_last12m'])>0}
num=lambda v:float(v) if v not in ('',None) else None
norm=lambda s:(s or '').strip().lower()
def normA(s):
    s=norm(s); return 'ALIAS' if s in ALIAS else s

# ---- lines (same window as stock_routing.py: 365 days before max order date, items from STOCK_CSV)
ws=openpyxl.load_workbook(SOX,read_only=True).active
it=ws.iter_rows(values_only=True); h=list(next(it)); ix={k:i for i,k in enumerate(h)}
rows=[r for r in it if r[0] is not None]
maxd=max(r[ix['Order Date']] for r in rows if r[ix['Order Date']]); win=maxd-timedelta(days=365)
lines=[(str(r[ix['Product ID']]),(r[ix['CF.Order Received from']] or '').strip()) for r in rows
       if r[ix['Order Date']] and r[ix['Order Date']]>win and str(r[ix['Product ID']]) in st]
tot=len(lines)
ic=Counter(i for i,_ in lines)
mismatch_items=[i for i in st if int(st[i]['lines_last12m'])!=ic[i]]
sh_lines=sum(1 for i,c in lines if c==SH_OWN)

def classify(iid,locs,alias):
    r=st[iid]; shid=r['sh_item_id']; item=sh.get(shid)
    if not shid or item is None: return 'UNKNOWN'
    cu=cat[iid]['unit'] if iid in cat else None
    if cu is None: return 'NO_CATALOGUE_UNIT'
    f=normA if alias else norm
    if f(item.get('unit'))!=f(cu): return 'UNIT_MISMATCH'
    free=sum(l.get(F_AFS) or 0 for l in item.get('locations',[]) if l['location_name'] in locs)
    m=num(r['typical_order_qty_median'])
    if m is None: return 'MEDIAN_MISSING'
    return 'FULL' if free>=m else 'PARTIAL' if free>0 else 'NONE'
ORDER=['UNKNOWN','UNIT_MISMATCH','NO_CATALOGUE_UNIT','MEDIAN_MISSING','FULL','PARTIAL','NONE']
def table(cnt,n):
    return {c:{'lines':cnt[c],'pct':round(100*cnt[c]/n,2)} for c in ORDER if cnt.get(c)}

res={}
for k,locs in SETS.items():
    for alias in (False,True):
        cls={i:classify(i,locs,alias) for i in st}
        allc=Counter(); noSH=Counter(); items_c=Counter(cls.values())
        for i,c in lines:
            allc[cls[i]]+=1
            noSH['PRODUCTION_RULE2' if c==SH_OWN else cls[i]]+=1
        # rule 2 view: SH-own lines forced to production; remaining lines by class
        n_other=tot-sh_lines
        rule2={'forced_production_lines':sh_lines,'forced_pct':round(100*sh_lines/tot,2),
               'classes_of_remaining_lines':table(Counter(cls[i] for i,c in lines if c!=SH_OWN),n_other),
               'remaining_lines':n_other,
               'sh_stores_FULL_lines_after_rule2':sum(1 for i,c in lines if c!=SH_OWN and cls[i]=='FULL'),
               'sh_stores_FULL_pct_of_all_lines_after_rule2':round(100*sum(1 for i,c in lines if c!=SH_OWN and cls[i]=='FULL')/tot,2)}
        pairs=Counter()
        if not alias:
            for i in st:
                if cls[i]=='UNIT_MISMATCH': pairs[f"{cat[i]['unit']} -> {sh[st[i]['sh_item_id']].get('unit')}"]+=1
        res[f"set_{k}_{'alias' if alias else 'strict'}"]={'items':dict(items_c),'without_rule2':table(allc,tot),'with_rule2_pct_of_all_lines':{**table(Counter({c:sum(1 for i,cu in lines if cu!=SH_OWN and cls[i]==c) for c in ORDER}),tot),'PRODUCTION_RULE2':{'lines':sh_lines,'pct':round(100*sh_lines/tot,2)}},'rule2_detail':rule2,'unit_pairs_among_mismatches_items':dict(pairs.most_common()) if not alias else None}
matchm=Counter(r['sh_match_method'] for r in st.values())
unit_present=sum(1 for x in sh.values() if x.get('unit') not in (None,''))
out={'snapshot':'SH items 28 Sep 2026 raw batch_*.json: STALE, shape only. SPS stock not used; SH and SPS never summed.',
 'basis':{'items':len(st),'lines':tot,'window':f'{win.date()} < Order Date <= {maxd.date()}','item_set_source':'customized-stock.csv rows with lines_last12m>0',
  'items_whose_line_count_differs_from_csv':len(mismatch_items),'lines_with_end_customer_SH_own':sh_lines,'end_customer_field':'CF.Order Received from','sh_own_string':SH_OWN},
 'sps_to_sh_match':{'method':'stock_routing.py match(): exact normalised name (casefold, whitespace) then punctuation-stripped name; unique or unique-active candidate only','methods_items':dict(matchm),
   'matched_items':sum(v for k,v in matchm.items() if k!='none'),'match_rate_items_pct':round(100*sum(v for k,v in matchm.items() if k!='none')/len(st),1),
   'lines_unmatched':sum(int(r['lines_last12m']) for r in st.values() if r['sh_match_method']=='none')},
 'fields':{'free_stock':F_AFS,'on_hand':F_SOH,'committed':F_COM,'unit':'item.unit (item level)','typical_qty':'customized-stock.csv typical_order_qty_median (production-type lines in window; catalogue CSV has median_qty, not this name)',
  'location_row_keys':sorted(keys),'sh_unit_present_items':f'{unit_present}/{len(sh)}'},
 'locations_in_data':dict(locnames),'sets':SETS,'alias_table':sorted(ALIAS),
 'identity_check_soh_minus_committed_eq_afs':ident,
 'results':res}
json.dump(out,open(OUT+'/data/stock-by-location-summary.json','w'),indent=1)
print(json.dumps({k:out[k] for k in ('basis','sps_to_sh_match','identity_check_soh_minus_committed_eq_afs')},indent=1))
