import warnings,json,collections,re,datetime; warnings.filterwarnings('ignore')
from openpyxl import load_workbook
S='/root/exports/zoho/native/2026-09-16/'
def rows(f,s):
    ws=load_workbook(S+f,read_only=True)[s]; it=ws.iter_rows(values_only=True); h=list(next(it))
    for r in it:
        if any(v not in(None,'') for v in r): yield dict(zip(h,r))
items={r['Item ID']:r for r in rows('Item.xlsx','Item')}
cust={i for i,r in items.items() if r['CF.Finished Good Type']=='Customized'}
L=[r for r in rows('Sales_Order.xlsx','Sales Order') if r['Product ID'] in cust]
print('lines on customized items',len(L)); 
F=['Item Desc','Usage unit','Warehouse Name','Division','CF.Order Received from','CF.Base Material to be Used','CF.Additional Other Material to be Used (If any)','CF.SH Sales Order Ref','CF.Job No','CF.Order Type','CF.Manufacturing Division','CF.Clickup Link','CF.Job Nature','Expected Shipment Date','PurchaseOrder','Notes','Sales Person','Payment Terms','Delivery Method','Customer Name','Sales Channel']
for f in F:
    v=[str(r[f]).strip() for r in L if r.get(f) not in(None,'')]
    c=collections.Counter(v)
    print(f'{f}: filled {len(v)/len(L):.0%}, distinct {len(c)}',c.most_common(6) if len(c)<=40 or f in('CF.Order Type','CF.Job Nature') else list(c.items())[:3])
for g in(('Artwork',['CF.Artwork Availability','CF.Artwork Availablility']),('Dye',['CF.Dye Cutter Availability','CF.Dye Cutter Availablity']),('Screen',['CF.Screen / Plate Available','CF.Screen / Plate Availability'])):
    c=collections.Counter(str(r[k]) for r in L for k in g[1] if r.get(k) not in(None,'')); print(g[0],c.most_common(6))
print(collections.Counter(r['CF.Manufacturing Division'] for r in L).most_common(12))
# fields by division: fill of art/dye/screen/base/other
by=collections.defaultdict(list)
for r in L: by[r['CF.Manufacturing Division'] or '(none)'].append(r)
for d,l in by.items():
    def fl(ks): return round(sum(1 for r in l if any(r.get(k) not in(None,'',False) for k in ks))/len(l),2)
    print(d,len(l),'art',fl(['CF.Artwork Availability','CF.Artwork Availablility']),'dye',fl(['CF.Dye Cutter Availability','CF.Dye Cutter Availablity']),'screen',fl(['CF.Screen / Plate Available','CF.Screen / Plate Availability']),'base',fl(['CF.Base Material to be Used']),'other',fl(['CF.Additional Other Material to be Used (If any)']),'nature',fl(['CF.Job Nature']))
print(collections.Counter(r['CF.Base Material to be Used'] for r in L).most_common(15))
print(collections.Counter(r['CF.Additional Other Material to be Used (If any)'] for r in L).most_common(10))
print(collections.Counter(r['Usage unit'] for r in L).most_common(8))
print(collections.Counter(r['CF.Order Type'] for r in L))
print('SO headers',len({r['SalesOrder Number'] for r in L}), 'cust names SPS', collections.Counter(r['Customer Name'] for r in L).most_common(4))
print('sample desc',[r['Item Desc'] for r in L if r['Item Desc']][:5])
print('item master attrs filled',sum(1 for i in cust if items[i]['AttributeName1']), 'variants group?')
