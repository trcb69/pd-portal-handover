# Recommended rule evaluation on 12m lines (measured)
import openpyxl,collections,json,warnings
warnings.filterwarnings('ignore')
items={i['item_id']:i for i in json.load(open('/root/exports/zoho/native/2026-09-19/sps/items.json'))['rows']}
wb=openpyxl.load_workbook('/root/exports/zoho/native/2026-09-16/Sales_Order.xlsx',read_only=True); ws=wb.active
it=ws.iter_rows(values_only=True); h=next(it); ix={n:i for i,n in enumerate(h)}
rows=[{k:r[i] for k,i in ix.items()} for r in it if '2025-09-16'<=str(r[ix['Order Date']])[:10]<='2026-09-15']
allowed={'Offset Printing Division (OPD)':{'OPD - PackPro Unit','OPD - MacPro Unit'},'Paper Cup Unit (PCU)':{'MOBA Unit'},'Paper Cup Lid Unit':{'MOBA Unit'},'Cake Wrapper Unit':{'MOBA Unit'},'Paper Plate Unit':{'MOBA Unit'},
 'Screen Printing Division (SHPS)':{'Screen Printing Unit'},'Rewinding Unit (RWU)':{'Rewinding Unit'},'Paper Straw Unit (PSU)':{'Paper Straw Unit'},'Food Product Processing (FPP)':{'Food Product Processing Unit'},
 'Customized Packing Unit (CPU)':{'Customized Packing Unit'},'MOBA Punching Unit':{'MOBA Punching Unit'}}
tagged=[r for r in rows if r['Division']]
ok=sum(1 for r in tagged if r['Division'] in allowed[r['CF.Manufacturing Division']]); print('tagged',len(tagged),'consistent with header',ok,round(100*ok/len(tagged),1))
bad=collections.Counter((r['CF.Manufacturing Division'],r['Division']) for r in tagged if r['Division'] not in allowed[r['CF.Manufacturing Division']]); print(bad)
un=[r for r in rows if not r['Division']]
print('untagged',len(un),collections.Counter(r['CF.Manufacturing Division'] for r in un))
# whose header maps uniquely to one unit (fallback is exact)
uniq={k for k,v in allowed.items() if len(v)==1}
fb=[r for r in un if r['CF.Manufacturing Division'] in uniq]; print('untagged resolved by header (unique mapping)',len(fb))
amb=[r for r in un if r['CF.Manufacturing Division'] not in uniq]; print('untagged on ambiguous header (OPD)',len(amb))
pred=collections.Counter(items.get(str(r['Product ID']),{}).get('cf_bu') for r in amb); print('item cf_bu of those',pred)
# PackPro vs MacPro: item master prediction
opd=[r for r in tagged if r['Division'] in('OPD - PackPro Unit','OPD - MacPro Unit')]
c=collections.Counter(); 
for r in opd: c[(items[str(r['Product ID'])]['cf_bu'],r['Division'])]+=1
print(c)
# same item tagged both PackPro and MacPro?
im=collections.defaultdict(set)
for r in opd: im[r['Item Name']].add(r['Division'])
print('OPD items',len(im),'seen under both PackPro and MacPro',sum(1 for v in im.values() if len(v)>1))
# by month sanity: unresolved share
by=collections.defaultdict(lambda:[0,0])
for r in rows:
    m=str(r['Order Date'])[:7]; by[m][0]+=1; by[m][1]+= (1 if (not r['Division'] and r['CF.Manufacturing Division'] not in uniq) else 0)
print({m:v for m,v in sorted(by.items())})
