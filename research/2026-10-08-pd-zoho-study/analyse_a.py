# Part A: division fields over 12 months from the 16 Sep 2026 Sales_Order.xlsx (line level) -- measured
import openpyxl, collections, json, warnings, sys
warnings.filterwarnings('ignore')
wb=openpyxl.load_workbook('/root/exports/zoho/native/2026-09-16/Sales_Order.xlsx',read_only=True)
ws=wb.active; it=ws.iter_rows(values_only=True); h=next(it); ix={n:i for i,n in enumerate(h)}
rows=[]
for r in it:
    d=str(r[ix['Order Date']])[:10]
    if '2025-09-16'<=d<='2026-09-15': rows.append({k:r[i] for k,i in ix.items()})
print('lines',len(rows),'SOs',len({r['SalesOrder Number'] for r in rows}))
def blank(v): return v is None or str(v).strip() in ('','NA','N/A')
mon=lambda r:str(r['Order Date'])[:7]
fields=['Division','CF.Manufacturing Division','CF.Job No','Sales Person','Warehouse Name','CF.Order Type','CF.Job Nature']
out={}
for f in fields:
    per=collections.defaultdict(lambda:[0,0])
    for r in rows:
        per[mon(r)][0]+=1; per[mon(r)][1]+= (0 if blank(r[f]) else 1)
    out[f]={m:round(100*v[1]/v[0],1) for m,v in sorted(per.items())}
    print(f,'overall set %',round(100*sum(v[1] for v in per.values())/len(rows),1)); print('  ',out[f])
for f in ['Division','CF.Manufacturing Division','Sales Person','Warehouse Name']:
    print(f, collections.Counter(r[f] for r in rows).most_common(20))
# header vs line
def code(v):
    v=(v or '').upper()
    for k,c in [('PACKPRO','PACKPRO'),('MACPRO','MACPRO'),('MOBA','MOBA'),('PAPER STRAW','PSU'),('REWINDING','RWU'),('SCREEN','SHPS'),('FLEXIBLE','FPP'),('PAPER CUP','MOBA'),('CUSTOMIZED PACKING','CPU'),('PAPER PLATE','MOBA'),('LID','MOBA'),('CAKE','MOBA'),('DIGITAL','DPU'),('OFFSET','OPD')]:
        if k in v: return c
    return v or None
print('HEADER values',collections.Counter(r['CF.Manufacturing Division'] for r in rows).most_common(20))
agree=dis=lo=ho=both_blank=0; opd=collections.Counter(); lines_by_hdr=collections.defaultdict(collections.Counter)
for r in rows:
    H=r['CF.Manufacturing Division']; L=r['Division']
    lines_by_hdr[H][L or '(no line tag)']+=1
for H,c in lines_by_hdr.items(): print('HDR',H,dict(c))
# item-level: does one item always carry the same line tag? predictability
items=collections.defaultdict(collections.Counter)
for r in rows:
    if r['Division']: items[r['Item Name']][r['Division']]+=1
multi=sum(1 for c in items.values() if len(c)>1)
print('items with line tag',len(items),'items with >1 distinct tag',multi)
# per month conflict: line tag set but header differs materially (not just OPD bucket)
json.dump({'fill_by_month':out},open('pulls/partA_fill.json','w'),indent=1)
