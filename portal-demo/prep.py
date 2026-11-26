import warnings,json,collections,re,datetime,statistics as st; warnings.filterwarnings('ignore')
from openpyxl import load_workbook
S='/root/exports/zoho/native/2026-09-16/'
def rows(f,s):
    ws=load_workbook(S+f,read_only=True)[s]; it=ws.iter_rows(values_only=True); h=list(next(it))
    for r in it:
        if any(v not in(None,'') for v in r): yield dict(zip(h,r))
cat={r['item_id']:r for r in __import__('csv').DictReader(open('/root/Project Management/reports/2026-10-17-custom-order-portal/data/customized-catalogue.csv'))}
rf={r['item_id']:r for r in json.load(open('../pulls/rows_final.json'))}
L=[r for r in rows('Sales_Order.xlsx','Sales Order') if r['Product ID'] in rf]
end=max(r['Order Date'] for r in L); cut=end.replace(year=end.year-1)
def clean(v): return str(v).strip() if v not in(None,False,True,'') else ''
def av(r,ks):
    for k in ks:
        v=clean(r.get(k))
        if v and v.lower() not in('false','true'): return v
    return ''
by=collections.defaultdict(list)
for r in L:
    if r['Order Date']>=cut: by[r['Product ID']].append(r)
items=[]
for iid,ls in by.items():
    ls.sort(key=lambda r:r['Order Date']); last=ls[-1]; i=rf[iid]
    def snap(r): return {'d':r['Order Date'].date().isoformat(),'q':r['QuantityOrdered'],'p':r['Item Price'],'base':clean(r['CF.Base Material to be Used']),'oth':clean(r['CF.Additional Other Material to be Used (If any)']),
      'art':av(r,['CF.Artwork Availability','CF.Artwork Availablility']),'dye':av(r,['CF.Dye Cutter Availability','CF.Dye Cutter Availablity']),'scr':av(r,['CF.Screen / Plate Available','CF.Screen / Plate Availability']),
      'nat':clean(r['CF.Job Nature']),'typ':clean(r['CF.Order Type']),'mdiv':clean(r['CF.Manufacturing Division']),'div':clean(r['Division']),'unit':clean(r['Usage unit'])}
    byc=collections.defaultdict(list)
    for r in ls:
        c=clean(r['CF.Order Received from'])
        if c and 'standard holdings' not in c.lower(): byc[c].append(r)
    cust={c:{**snap(l[-1]),'n':len(l)} for c,l in byc.items()}
    items.append({'id':iid,'n':i['name'],'sku':i['sku'],'sp':i['sp'],'cu':i['customer'],'unit':i['unit'] or snap(last)['unit'],'stat':i['status'],'lines':len(ls),'last':snap(last),'cust':cust,
      'medq':st.median([r['QuantityOrdered'] for r in ls if isinstance(r['QuantityOrdered'],(int,float))] or [0])})
print(len(items)); json.dump(items,open('items_raw.json','w'))
# which meaningful fields per manufacturing division
d=collections.defaultdict(lambda:collections.defaultdict(collections.Counter))
for it in items:
    l=it['last']; 
    for k in('art','dye','scr','nat'): d[l['mdiv']][k][l[k] or '-']+=1
for m,x in d.items(): print(m,{k:dict(v.most_common(4)) for k,v in x.items()})
