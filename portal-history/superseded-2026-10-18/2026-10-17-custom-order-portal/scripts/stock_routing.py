"""Customized-item stock + routing analysis. Read-only on all sources.
Usage: stock_routing.py CACHEDIR OUTDIR
CACHEDIR holds so.pkl inv.pkl pkg.pkl shitems.pkl (made by cache_sources.py / cache_sh_items.py).
SPS and SH stock are NEVER summed: they are separate columns."""
import sys,pickle,re,csv,json,statistics as st
from collections import Counter,defaultdict
from datetime import datetime,timedelta
sys.path.insert(0,__file__.rsplit('/',1)[0])
from load_sps import items,wh
C,O=sys.argv[1],sys.argv[2]
SPS='/root/exports/zoho/native/2026-09-19/sps/'
I={i['item_id']:i for i in items(SPS+'items.json')}
W=wh(SPS+'stock_by_warehouse.json')
SO=pickle.load(open(C+'/so.pkl','rb')); PK=pickle.load(open(C+'/pkg.pkl','rb')); IV=pickle.load(open(C+'/inv.pkl','rb'))
SH=pickle.load(open(C+'/shitems.pkl','rb'))
S={}  # summary numbers
def norm(s): return re.sub(r'\s+',' ',(s or '').strip()).casefold()
def norm2(s): return re.sub(r'[^0-9a-z]','',(s or '').casefold())
def med(x): return st.median(x) if x else None
def pct(x,p):
    if not x: return None
    x=sorted(x); return x[min(len(x)-1,int(round(p*(len(x)-1))))]
def num(v):
    try: return float(v)
    except: return 0.0

# ---- line tag / header -> home unit (rule: spec 2026-10-08 s8.0b; alias list = spec preview l.771 + 002-seed)
TAG={'Paper Straw Unit':'PSU','Screen Printing Unit':'SHPS','Customized Packing Unit':'CPU','MOBA Unit':'MOBA',
     'OPD - PackPro Unit':'PACKPRO','OPD - MacPro Unit':'MACPRO','MOBA Punching Unit':'MOBA',
     # not named in the spec's alias list; assumed by me from the unit name:
     'Food Product Processing Unit':'FPP','Digital Printing Unit':'DPU','Rewinding Unit':'RWU'}
ASSUMED_TAG={'Food Product Processing Unit','Digital Printing Unit','Rewinding Unit'}
HDR={'Offset Printing Division (OPD)':'OPD','Screen Printing Division (SHPS)':'SHPS','Paper Straw Unit (PSU)':'PSU','Rewinding Unit (RWU)':'RWU',
     'Paper Cup Unit (PCU)':'PCU','Customized Packing Unit (CPU)':'CPU','MOBA Punching Unit':'MOBA','Paper Cup Lid Unit':'PCLU',
     'Food Product Processing (FPP)':'FPP','Digital Printing Unit (DPU)':'DPU','Paper Plate Unit':'PPU','Cake Wrapper Unit':'CWU'}
BUCKET={'Offset Printing Division (OPD)'}
REFINE={'MOBA Unit':{'PCU','PCLU','CWU','PPU'}}
COMPAT={'OPD':{'PACKPRO','MACPRO'}}
def home(tag,hdr):
    tag=(tag or '').strip(); hdr=(hdr or '').strip()
    h=HDR.get(hdr)
    if tag:
        t=TAG.get(tag)
        if t is None: return None,'unmapped_tag'
        if tag in REFINE and h in REFINE[tag]: return h,'tag+header'
        if hdr and hdr not in BUCKET and h and h!=t and h not in COMPAT.get(h,set()) and t not in COMPAT.get(h,set()):
            return t,'tag(conflict_with_header)'
        return t,'tag'
    if hdr and hdr not in BUCKET and h: return h,'header'
    return None,'needs_unit_confirmation'

# ---- division -> people (spec 2026-10-08-pd-managers-full-release.md s1d draft + D-N F2.3/F2.5; admin data, Q-U open)
PEOPLE={'OPD':('Ranga + Ishan (first to send decides, F3.1)','Nirmani + Umanda'),'PACKPRO':('Ishan','Umanda'),'MACPRO':('Shihar','Nimesha'),
 'PSU':('Ishan','Umanda'),'RWU':('Ishan','Umanda'),'SHPS':('Mubeena','Madushi'),'CPU':('Ranga','Nirmani'),'FPP':('Ranga','Nirmani'),
 'PCLU':('Ranga','Nirmani'),'CWU':('Ranga','Nirmani'),'PPU':('Ranga','Nirmani'),'MOBA':('Ranga','Nimesha'),'PCU':('',''),'DPU':('',''),'MOBA_P':('','')}
NAMES={'OPD':'Offset Printing Division','SHPS':'Screen Printing Division','PSU':'Paper Straw Unit','RWU':'Rewinding Unit','MOBA':'MOBA Punching Unit','MOBA_P':'MOBA Punching (P)',
 'FPP':'Food Product Processing','CPU':'Customized Packing Unit','PACKPRO':'PackPro (OPD - PackPro Unit)','MACPRO':'MacPro (OPD - MacPro Unit)','PCU':'Paper Cup Unit','PCLU':'Paper Cup Lid Unit','DPU':'Digital Printing Unit','PPU':'Paper Plate Unit','CWU':'Cake Wrapper Unit'}

# ---- SO lines
maxd=max(l['Order Date'] for l in SO if l['Order Date']); win=maxd-timedelta(days=365)
S['so_lines']=len(SO); S['so_max_order_date']=str(maxd.date()); S['window_12m_start']=str(win.date())
cust_ids={k for k,i in I.items() if i.get('cf_fg_type')=='Customized'}
S['sps_items_total']=len(I); S['sps_items_customized']=len(cust_ids)
S['so_lines_unmatched_to_item_master']=sum(1 for l in SO if str(l['Product ID']) not in I)
S['so_lines_on_customized_items']=sum(1 for l in SO if str(l['Product ID']) in cust_ids)
# order type x item type
S['ordertype_x_itemtype']={f'{a} | {b}':n for (a,b),n in Counter((l['CF.Order Type'],I.get(str(l['Product ID']),{}).get('cf_fg_type','NOT_IN_MASTER')) for l in SO).items()}
# packages / invoices keyed (SO, item)
pk=defaultdict(lambda:[None,0.0])
for p in PK:
    k=(p['SO Number'],p['Item Name']); d=p['Packing Date']
    if d and (pk[k][0] is None or d<pk[k][0]): pk[k][0]=d
    pk[k][1]+=num(p['Quantity Packed'])
iv=defaultdict(lambda:[None,0.0])
for r in IV:
    k=(r['Sales Order Number'],r['Item Name']); d=r['Invoice Date']
    if d and (iv[k][0] is None or d<iv[k][0]): iv[k][0]=d
    iv[k][1]+=num(r['Quantity'])
for l in SO:
    k=(l['SalesOrder Number'],l['Item Name']); l['_pack']=pk.get(k); l['_inv']=iv.get(k)
    l['_q']=num(l['QuantityOrdered'])-num(l['QuantityCancelled'])
    l['_ct']=I.get(str(l['Product ID']),{}).get('cf_fg_type')
S['lines_with_package_match']=sum(1 for l in SO if l['_pack']); S['lines_with_invoice_match']=sum(1 for l in SO if l['_inv'])

# ---- (b) history on Customized-type items
def lag(l,key):
    v=l[key]; 
    return (v[0]-l['Order Date']).days if v and v[0] and l['Order Date'] else None
H={}
for ot in ('Customized Order','Ex Stock','Make to Order (MTO)','Internal SH Order'):
    L=[l for l in SO if l['_ct']=='Customized' and l['CF.Order Type']==ot]
    pl=[x for x in (lag(l,'_pack') for l in L) if x is not None and x>=0]; il=[x for x in (lag(l,'_inv') for l in L) if x is not None and x>=0]
    H[ot]={'lines':len(L),'orders':len({l['SalesOrder Number'] for l in L}),'items':len({l['Product ID'] for l in L}),'units':sum(l['_q'] for l in L),
      'lines_with_pack':len(pl),'pack_days_median':med(pl),'pack_days_p80':pct(pl,.8),'pack_same_day_pct':round(100*sum(1 for x in pl if x==0)/len(pl),1) if pl else None,
      'pack_le1d_pct':round(100*sum(1 for x in pl if x<=1)/len(pl),1) if pl else None,'pack_le3d_pct':round(100*sum(1 for x in pl if x<=3)/len(pl),1) if pl else None,
      'lines_with_invoice':len(il),'invoice_days_median':med(il),'invoice_days_p80':pct(il,.8),
      'invoice_le1d_pct':round(100*sum(1 for x in il if x<=1)/len(il),1) if il else None}
S['history_customized_items_by_order_type']=H
byyear=defaultdict(Counter)
for l in SO:
    if l['_ct']=='Customized' and l['CF.Order Type'] in ('Customized Order','Ex Stock'): byyear[l['Order Date'].year][l['CF.Order Type']]+=1
S['by_year_customized_items']={y:dict(c) for y,c in sorted(byyear.items())}
# all-items comparison (non-customized items sold ex stock): same lag
L=[l for l in SO if l['_ct']=='Non Customized' and l['CF.Order Type']=='Ex Stock']
pl=[x for x in (lag(l,'_pack') for l in L) if x is not None and x>=0]
S['history_noncustomized_exstock']={'lines':len(L),'pack_days_median':med(pl),'pack_same_day_pct':round(100*sum(1 for x in pl if x==0)/len(pl),1) if pl else None}
# per-item order-type mix
mix=defaultdict(Counter)
for l in SO:
    if l['_ct']=='Customized': mix[str(l['Product ID'])][l['CF.Order Type']]+=1
S['customized_items_ever_ordered']=len(mix)
S['items_only_exstock']=sum(1 for c in mix.values() if set(c)=={'Ex Stock'})
S['items_both_exstock_and_customized']=sum(1 for c in mix.values() if 'Ex Stock' in c and 'Customized Order' in c)
S['items_only_customized_order']=sum(1 for c in mix.values() if set(c)<= {'Customized Order'})
# ex-stock lines last 12m on customized items
w=[l for l in SO if l['_ct']=='Customized' and l['Order Date']>win]
S['last12m_customized_item_lines']=Counter(l['CF.Order Type'] for l in w)

# ---- SH match
shn=defaultdict(list); shn2=defaultdict(list)
for s in SH: shn[norm(s['name'])].append(s); shn2[norm2(s['name'])].append(s)
def pick(c):
    if len(c)==1: return c[0],'unique'
    a=[x for x in c if x['status']=='active']
    if len(a)==1: return a[0],'unique_active_of_%d'%len(c)
    return None,'ambiguous_%d'%len(c)
def match(name):
    c=shn.get(norm(name))
    if c: s,n=pick(c); return s,'exact_name_normalised',n
    c=shn2.get(norm2(name))
    if c: s,n=pick(c); return s,'name_punct_stripped',n
    return None,'none',''

# ---- per-item rows
by_item=defaultdict(list)
for l in SO:
    if str(l['Product ID']) in cust_ids: by_item[str(l['Product ID'])].append(l)
rows=[]
for iid in sorted(cust_ids,key=lambda k:I[k]['name']):
    it=I[iid]; L=by_item.get(iid,[])
    oc=Counter(l['CF.Order Type'] for l in L)
    recent=[l for l in L if l['Order Date']>win]
    prod=[l for l in L if l['CF.Order Type'] in ('Customized Order','Make to Order (MTO)')]
    prod_r=[l for l in prod if l['Order Date']>win] or prod
    qs=[l['_q'] for l in (prod_r or L) if l['_q']>0]
    typ=med(qs)
    # home unit: modal over production lines in window (else all lines)
    hu=Counter(); 
    for l in (prod_r or L):
        h,_=home(l['Division'],l['CF.Manufacturing Division']); hu[h or '(none)']+=1
    hu_code=hu.most_common(1)[0][0] if hu else ''
    tags=Counter((l['Division'] or '') for l in (prod_r or L)); hdrs=Counter((l['CF.Manufacturing Division'] or '') for l in (prod_r or L))
    wip=W['wip'].get(iid,{}).get('stock_on_hand'); rm=W['rm'].get(iid,{}).get('stock_on_hand'); fg=W['fg'].get(iid,{}).get('stock_on_hand')
    avail=min(it.get('stock_on_hand') or 0, it.get('available_for_sale') if it.get('available_for_sale') is not None else 0)  # free to promise, conservative
    s,mm,note=match(it['name'])
    sh_av=s['actual_available_for_sale_stock'] if s else None
    def cls(av):
        if av is None: return 'UNKNOWN'
        if typ is None: return 'FULL_UNKNOWN_QTY' if av>0 else 'NONE'
        return 'FULL' if av>=typ else ('PARTIAL' if av>0 else 'NONE')
    sps_cls=cls(avail) if it['track_inventory'] else 'UNKNOWN'
    sh_cls=cls(sh_av) if s and s['track_inventory'] and sh_av is not None else 'UNKNOWN'
    shloc=max(s['locs'],key=lambda x:(x[1] or 0))[0] if s and s['locs'] and max((x[1] or 0) for x in s['locs'])>0 else ''
    rows.append({'sps_item_id':iid,'item_name':it['name'],'sku':it['sku'],'sps_status':it['status'],'sps_tracks_inventory':it['track_inventory'],
      'cf_bu':it.get('cf_bu',''),'cf_parent_category':it.get('cf_parent_category',''),'cf_fg_nature':it.get('cf_fg_nature',''),
      'lines_all_time':len(L),'lines_last12m':len(recent),'last_order_date':str(max((l['Order Date'] for l in L)).date()) if L else '',
      'lines_customized_order':oc['Customized Order'],'lines_ex_stock':oc['Ex Stock'],'lines_internal_sh':oc['Internal SH Order'],'lines_mto':oc['Make to Order (MTO)'],
      'typical_order_qty_median':typ if typ is not None else '','units_ordered_last12m':sum(l['_q'] for l in recent),
      'home_unit_modal':hu_code,'modal_line_tag':tags.most_common(1)[0][0] if tags else '','modal_header_division':hdrs.most_common(1)[0][0] if hdrs else '',
      'sps_stock_wip_19sep':wip,'sps_stock_rm_19sep':rm,'sps_stock_fg_19sep':fg,'sps_stock_on_hand_19sep':it.get('stock_on_hand'),'sps_free_to_promise_19sep':avail,'sps_stock_class':sps_cls,
      'sh_match_method':mm,'sh_match_note':note,'sh_item_id':s['item_id'] if s else '','sh_item_name':s['name'] if s else '',
      'sh_stock_on_hand_28sep':s['stock_on_hand'] if s else '','sh_free_to_promise_28sep':sh_av if s else '','sh_committed_physical_28sep':s['actual_committed_stock'] if s else '','sh_main_location':shloc,'sh_stock_class':sh_cls,
      'route_if_sh_stock_full':'' })
    r=rows[-1]
    # tentative single-item routing for a typical order (live check is still required)
    r['route_if_sh_stock_full']=''
for r in rows: del r['route_if_sh_stock_full']
fn=O+'/data/customized-stock.csv'
with open(fn,'w',newline='') as f:
    w_=csv.DictWriter(f,fieldnames=list(rows[0])); w_.writeheader(); w_.writerows(rows)
S['csv_rows']=len(rows)
act=[r for r in rows if r['sps_status']=='active']
S['customized_active']=len(act); S['customized_tracked']=sum(1 for r in rows if r['sps_tracks_inventory'])
S['sh_match']=dict(Counter(r['sh_match_method'] for r in rows)); S['sh_match_active']=dict(Counter(r['sh_match_method'] for r in act))
S['sh_match_note']=dict(Counter(r['sh_match_note'] for r in rows if r['sh_match_method']!='none'))
ordered=[r for r in rows if r['lines_all_time']>0]; rec=[r for r in rows if r['lines_last12m']>0]
S['ordered_items']=len(ordered); S['ordered_items_last12m']=len(rec)
S['sh_match_ordered_last12m']=dict(Counter(r['sh_match_method'] for r in rec))
S['sps_class_all']=dict(Counter(r['sps_stock_class'] for r in rows)); S['sps_class_ordered12m']=dict(Counter(r['sps_stock_class'] for r in rec))
S['sh_class_all']=dict(Counter(r['sh_stock_class'] for r in rows)); S['sh_class_ordered12m']=dict(Counter(r['sh_stock_class'] for r in rec))
S['cross_sps_sh_class_ordered12m']=dict(Counter(f"SH={r['sh_stock_class']} | SPS={r['sps_stock_class']}" for r in rec))
# line-weighted: share of last-12m customized-item lines whose item has stock in SH / SPS today
tot=sum(r['lines_last12m'] for r in rec)
S['lines12m_by_sh_class_pct']={k:round(100*sum(r['lines_last12m'] for r in rec if r['sh_stock_class']==k)/tot,1) for k in set(r['sh_stock_class'] for r in rec)}
S['lines12m_by_sps_class_pct']={k:round(100*sum(r['lines_last12m'] for r in rec if r['sps_stock_class']==k)/tot,1) for k in set(r['sps_stock_class'] for r in rec)}
S['lines12m_total_customized_items']=tot
# where SPS stock sits (customized, tracked)
trk=[r for r in rows if r['sps_tracks_inventory']]
S['sps_stock_location']={k:{'items_with_positive':sum(1 for r in trk if (r[f'sps_stock_{k}_19sep'] or 0)>0),'items_negative':sum(1 for r in trk if (r[f'sps_stock_{k}_19sep'] or 0)<0),'units_positive':sum(r[f'sps_stock_{k}_19sep'] for r in trk if (r[f'sps_stock_{k}_19sep'] or 0)>0)} for k in ('wip','rm','fg')}
S['so_line_warehouse']=dict(Counter(l['Warehouse Name'] for l in SO))
# SH location of stock for matched customized items (not summed with SPS)
loc=Counter()
for r in rows:
    if r['sh_item_id']:
        s=next(x for x in SH if x['item_id']==r['sh_item_id']) if False else None
shid={s['item_id']:s for s in SH}
locu=defaultdict(float); locn=Counter()
for r in rows:
    s=shid.get(r['sh_item_id'])
    if s:
        for n,a,b in s['locs']:
            if (a or 0)>0: locu[n]+=a; locn[n]+=1
S['sh_stock_by_location_matched_customized']={n:{'items':locn[n],'units':locu[n]} for n in locu}
S['sh_matched_with_positive_stock']=sum(1 for r in rows if r['sh_item_id'] and (r['sh_stock_on_hand_28sep'] or 0)>0)
# staleness
S['sps_snapshot_date']='2026-09-19'; S['sh_snapshot_date']='2026-09-28 (last_modified max 2026-09-28T16:06)'
def _route(x):
    sh,sp=x['sh_stock_class'],x['sps_stock_class']
    if sh in('FULL','FULL_UNKNOWN_QTY'): return 'A_SH_full'
    if sp in('FULL','FULL_UNKNOWN_QTY'): return 'B_SPS_full_SH_not'
    if 'PARTIAL' in (sh,sp): return 'C_partial_somewhere'
    if sh=='UNKNOWN': return 'D_SH_unknown_SPS_none'
    return 'E_no_stock_either'
_c=Counter(); _i=Counter()
for x in rec: _c[_route(x)]+=x['lines_last12m']; _i[_route(x)]+=1
S['routing_simulation_last12m_lines']={k:{'items':_i[k],'lines':_c[k],'pct':round(100*_c[k]/tot,1)} for k in sorted(_c)}
S['unknown_sh_reason_last12m']={'no_sh_item_match':sum(1 for x in rec if x['sh_stock_class']=='UNKNOWN' and x['sh_match_method']=='none')}

# how many ex-stock customized lines are for items with 0 SPS & 0 SH stock today
# ---- division routing (customized items, production-type lines)
D=defaultdict(lambda:{'lines':0,'lines12m':0,'sos12m':set(),'items':set(),'tags':Counter(),'hdrs':Counter(),'src':Counter()})
allprod=[l for l in SO if l['_ct']=='Customized' and l['CF.Order Type'] in ('Customized Order','Make to Order (MTO)')]
for l in allprod:
    h,src=home(l['Division'],l['CF.Manufacturing Division']); k=h or '(unresolved)'
    d=D[k]; d['lines']+=1; d['items'].add(str(l['Product ID'])); d['tags'][l['Division'] or '(blank)']+=1; d['hdrs'][l['CF.Manufacturing Division'] or '(blank)']+=1; d['src'][src]+=1
    if l['Order Date']>win: d['lines12m']+=1; d['sos12m'].add(l['SalesOrder Number'])
t12=sum(d['lines12m'] for d in D.values()); tall=sum(d['lines'] for d in D.values())
out=[]
for k in sorted(set(D)|set(PEOPLE),key=lambda k:-(D[k]['lines12m'] if k in D else -1)):
    d=D.get(k); m,c=PEOPLE.get(k,('',''))
    status='NO_MANAGER' if (k in PEOPLE and not m) else ('UNRESOLVED' if k=='(unresolved)' else 'DRAFT_PAIR')
    note={'PCU':'No pair in the 8 Oct draft (spec 1d: unknown); F2.4 says MOBA-tagged cups are Ranga. Until answered the order lands on Unassigned.',
          'DPU':'Owner F2.5 (8 Oct): DPU kept with no manager; jobs go to Unassigned.','MOBA_P':'Seeded but unused; no pair.',
          'OPD':'Shared by two manager pairs; first to Send next decides (F3.1).','(unresolved)':'No usable tag and the header is the OPD bucket (or blank): admin confirms the unit (needs_unit_confirmation).',
          'MACPRO':'New manager; needs login + division_pairs row (F2.3).','MOBA':'MOBA Unit tag with a non-cup header stays MOBA.'}.get(k,'')
    out.append({'division_code':k,'division_name':NAMES.get(k,''),'manager_draft':m,'coordinator_draft':c,'pair_status':status,
      'lines_all_time':d['lines'] if d else 0,'lines_last12m':d['lines12m'] if d else 0,'share_last12m_pct':round(100*d['lines12m']/t12,1) if d else 0,
      'sales_orders_last12m':len(d['sos12m']) if d else 0,'distinct_items':len(d['items']) if d else 0,
      'top_line_tags':'; '.join(f'{a} ({b})' for a,b in d['tags'].most_common(3)) if d else '','top_header_values':'; '.join(f'{a} ({b})' for a,b in d['hdrs'].most_common(3)) if d else '',
      'resolution_source':'; '.join(f'{a} ({b})' for a,b in d['src'].most_common()) if d else '','note':note})
with open(O+'/data/division-routing.csv','w',newline='') as f:
    w_=csv.DictWriter(f,fieldnames=list(out[0])); w_.writeheader(); w_.writerows(out)
S['routing_lines_basis']={'production_type_lines_customized_items_all':tall,'last12m':t12}
S['lines12m_to_no_manager_pct']=round(100*sum(o['lines_last12m'] for o in out if o['pair_status'] in('NO_MANAGER','UNRESOLVED'))/t12,1)
S['lines12m_by_status_pct']={k:round(100*sum(o['lines_last12m'] for o in out if o['pair_status']==k)/t12,1) for k in ('DRAFT_PAIR','NO_MANAGER','UNRESOLVED')}
S['assumed_tag_aliases_lines']=sum(1 for l in allprod if (l['Division'] or '').strip() in ASSUMED_TAG)
S['tag_conflict_lines']=sum(1 for l in allprod if home(l['Division'],l['CF.Manufacturing Division'])[1]=='tag(conflict_with_header)')

# ---- extra: how many "Customized Order" lines are in practice served immediately (hidden from-stock)
def bucket(x):
    return '0 days' if x==0 else '1 day' if x==1 else '2-3 days' if x<=3 else '4-7 days' if x<=7 else '8-14 days' if x<=14 else '15-30 days' if x<=30 else '31+ days'
for tag,pred in (('all_time',lambda l:True),('last12m',lambda l:l['Order Date']>win)):
    L=[l for l in SO if l['_ct']=='Customized' and l['CF.Order Type']=='Customized Order' and pred(l)]
    b=Counter(); neg=0; nop=0
    for l in L:
        x=lag(l,'_pack')
        if x is None: nop+=1
        elif x<0: neg+=1
        else: b[bucket(x)]+=1
    S['customized_order_pack_lag_'+tag]={'lines':len(L),'no_package_found':nop,'negative_lag':neg,'buckets':dict(b)}
jn=defaultdict(lambda:[0,0])
for l in SO:
    if l['_ct']=='Customized' and l['CF.Order Type']=='Customized Order' and l['Order Date']>win:
        x=lag(l,'_pack')
        if x is not None and x>=0:
            jn[l['CF.Job Nature'] or '(blank)'][0]+=1; jn[l['CF.Job Nature'] or '(blank)'][1]+= (x<=1)
S['last12m_customized_order_packed_le1d_by_job_nature']={k:{'lines':a,'packed_le1d_pct':round(100*b/a,1)} for k,(a,b) in jn.items()}
S['psu_rwu_tag_lines_by_item_type']={t:dict(Counter(l['_ct'] for l in SO if l['Division']==t)) for t in ('Paper Straw Unit','Rewinding Unit','Digital Printing Unit')}
# units: customized-order lines packed <=1 day whose item has SPS WIP stock today (sanity: is same-day packing consistent with stock existing?)
S['quick_lines_item_has_sps_stock_today_pct']=None

yr=defaultdict(list)
for l in SO:
    if l['_ct']=='Customized' and l['CF.Order Type']=='Customized Order':
        x=lag(l,'_pack')
        if x is not None: yr[l['Order Date'].year].append(x)
S['customized_order_pack_lag_by_year']={y:{'lines':len(v),'median_days':med(v),'p80_days':pct(v,.8),'packed_le1d_pct':round(100*sum(1 for x in v if x<=1)/len(v),1)} for y,v in sorted(yr.items())}

json.dump(S,open(O+'/data/stock-routing-summary.json','w'),indent=1,default=str)
print('done')
