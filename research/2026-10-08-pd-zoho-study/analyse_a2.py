# Part A.4: does the item master (cf_bu / cf_fg_sub_category) predict the line tag / header division? -- measured on 12m xlsx lines
import openpyxl, collections, json, warnings
warnings.filterwarnings('ignore')
S='/root/exports/zoho/native/2026-09-19/sps/'
items=json.load(open(S+'items.json'))['rows']
byname={}; byid={}
for i in items: byname[i['name'].strip().lower()]=i; byid[i['item_id']]=i
wb=openpyxl.load_workbook('/root/exports/zoho/native/2026-09-16/Sales_Order.xlsx',read_only=True)
ws=wb.active; it=ws.iter_rows(values_only=True); h=next(it); ix={n:i for i,n in enumerate(h)}
rows=[{k:r[i] for k,i in ix.items()} for r in it if '2025-09-16'<=str(r[ix['Order Date']])[:10]<='2026-09-15']
miss=0; tab=collections.defaultdict(collections.Counter); tabh=collections.defaultdict(collections.Counter)
for r in rows:
    i=byid.get(str(r['Product ID'])) or byname.get(str(r['Item Name']).strip().lower())
    if not i: miss+=1; continue
    tab[i['cf_bu']][r['Division'] or '(none)']+=1
    tabh[i['cf_bu']][r['CF.Manufacturing Division']]+=1
print('lines unmatched to item master',miss,'of',len(rows))
for k,c in sorted(tab.items(),key=lambda x:-sum(x[1].values())): print('item cf_bu=',k,sum(c.values()),dict(c.most_common(6)))
# purity: majority share for tagged lines
tot=ok=0
for k,c in tab.items():
    t=sum(v for d,v in c.items() if d!='(none)'); m=max([v for d,v in c.items() if d!='(none)'] or [0]); tot+=t; ok+=m
print('item cf_bu -> line tag majority purity',round(100*ok/tot,1),'% of',tot,'tagged lines')
tot=ok=0
for k,c in tabh.items():
    t=sum(c.values()); m=max(c.values()); tot+=t; ok+=m
print('item cf_bu -> header division majority purity',round(100*ok/tot,1),'% of',tot)
# OPD lines only: item cf_bu vs line tag
for r in rows:
    pass
sub=collections.defaultdict(collections.Counter)
for r in rows:
    if r['CF.Manufacturing Division'].startswith('Offset'):
        i=byid.get(str(r['Product ID'])) or byname.get(str(r['Item Name']).strip().lower())
        sub[(i or {}).get('cf_bu','?')][r['Division'] or '(none)']+=1
print('OPD header lines: item cf_bu -> line tag'); 
for k,c in sub.items(): print(' ',k,dict(c))
