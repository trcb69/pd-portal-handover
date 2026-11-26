"""Build the catalogue xlsx. Run merge_items.py first, then: python3 build_xlsx.py  (reads ../pulls/*, writes ../SPS-Customized-Items-Catalogue-2026-10-18.xlsx)"""
import json,re,os,collections,difflib,csv
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.utils import get_column_letter
here=os.path.dirname(os.path.abspath(__file__)); P=here+'/../pulls/'; OUT=here+'/../SPS-Customized-Items-Catalogue-2026-10-18.xlsx'
items=json.load(open(P+'items_merged.json')); check=json.load(open(P+'check_items.json')); stats=json.load(open(P+'merge_stats.json'))
_all=json.load(open('/root/exports/zoho/native/2026-09-19/sh_full/salesorders.json'))['rows']
_good=[r for r in _all if r.get('date','')>='2020' and r['date']<='2026-09-19' and r.get('customer_name')]
_end='2026-09-19'
so12=[r for r in _good if r['date']>'2025-09-19']; so24=[r for r in _good if r['date']>'2024-09-19']
so=so12
PSEUDO={'','Internal','Maradana Retail Chain','Inventory Loan','Central Retail Showroom'}
STOP={'pvt','ltd','private','limited','the','co','lanka','sl','sri','and','of','plc','company','inc','llc','pty'}
def toks(s): return [t for t in re.sub(r'[^a-z0-9 ]+',' ',s.lower().replace('&',' and ')).split() if t not in STOP]
# --- SH customers -> sales persons
cust=collections.defaultdict(collections.Counter); basis12=set(); alltime=set()
for r in so12: cust[r['customer_name']][r['salesperson_name'] or '']+=1
for n,c in cust.items():
    if not [k for k in c if k not in PSEUDO]: pass
c24=collections.defaultdict(collections.Counter)
for r in so24: c24[r['customer_name']][r['salesperson_name'] or '']+=1
for n,c in c24.items():
    if n not in cust or not [k for k in cust[n] if k]:
        cust[n]=c; basis12.add(n)   # fall back to 24 months
call=collections.defaultdict(collections.Counter)
for r in _good: call[r['customer_name']][r['salesperson_name'] or '']+=1
for n,c in call.items():
    if n not in cust or not [k for k in cust[n] if k]:
        cust[n]=c; basis12.add(n); alltime.add(n)
cinfo={}
for n,c in cust.items():
    real=collections.Counter({k:v for k,v in c.items() if k not in PSEUDO}) or collections.Counter({k:v for k,v in c.items() if k})
    top=real.most_common(1)[0][0] if real else ''
    tie=len(real)>1 and real.most_common(2)[0][1]==real.most_common(2)[1][1]
    others='; '.join(f'{k} ({v})' for k,v in real.most_common() if k!=top)
    cinfo[n]={'toks':set(toks(n)),'joined':' '.join(sorted(toks(n))),'sp':top,'n':sum(c.values()),'tie':tie,'others':others,'real_n':sum(real.values()),'span':('all-time' if n in alltime else '24 months') if n in basis12 else '12 months'}
_mc={}
def match(tag):
    if tag in _mc: return _mc[tag]
    _mc[tag]=_match(tag); return _mc[tag]
def _match(tag):
    T=set(toks(tag)); 
    if not T: return None
    tj=' '.join(sorted(T)); ex=[];sub=[];fz=[]
    for n,i in cinfo.items():
        if i['toks']==T: ex.append(n)
        elif T<=i['toks'] and (len(T)>1 or len(tj)>=4) : sub.append(n)
        elif len(tj)>=5 and abs(len(tj)-len(i['joined']))<=3 and difflib.SequenceMatcher(None,tj,i['joined']).ratio()>=0.9: fz.append(n)
    for lst,lvl in ((ex,'High'),(sub,'Medium'),(fz,'Low')):
        if lst:
            lst.sort(key=lambda n:(-(cinfo[n]['sp']!=''),-cinfo[n]['n']) if lvl!='Medium' else (len(cinfo[n]['toks']),-cinfo[n]['n']))
            best=lst[0]; sps={cinfo[n]['sp'] for n in lst if cinfo[n]['sp']}
            if lvl!='High' and len(sps)>1: lvl='Low'
            return best,lvl,len(lst)
    return None
JUNK=re.compile(r'(pcs|packing|inch|^\d|\bmm\b|\bcm\b|ml$|\boz\b|^l$|^m$|^s$|^xl)',re.I)
def tags_of(name): return [t.strip() for t in re.findall(r'\(([^()]*)\)',name)]
def kind(n):
    for pre,k in (('Service','SERVICE'),('RTP','RTP'),('PRINTSERV','PRINTSERV'),('PACKSERV','PACKSERV'),('SP','SP'),('CP','CP'),('Sub','SUB'),('SH','SH'),('DP','DP')):
        if re.match(r'^'+pre+r'\s*-',n.strip()) or (pre in('Service','RTP') and n.strip().startswith(pre)): return k
    return 'OTHER'
rows=[]
for it in items:
    tl=[t for t in tags_of(it['name']) if t and not JUNK.search(t)]
    cand=[('name tag',t) for t in reversed(tl)]
    te=[x.rsplit(' (',1)[0].strip() for x in it['top_end'].split(';') if x.strip()]
    cand+=[('order history',t) for t in te if 'standard holdings' not in t.lower()]
    m=None; used=None
    for how,t in cand:
        r=match(t)
        if r: m=r; used=(how,t); break
    tagshown=tl[-1] if tl else (te[0] if te else '')
    it=dict(it); it['type']=kind(it['name'])
    if m:
        best,lvl,nc=m; ci=cinfo[best]
        how,t=used
        if how=='order history' and lvl=='High': lvl='Medium'
        it.update(customer=best,tag=t,conf=lvl,basis=how+(f' ({nc} candidate names)' if nc>1 else ''),sp=ci['sp'],sp_note=('tie; ' if ci['tie'] else '')+('' if ci['span']=='12 months' else ci['span']+' basis; ')+('also: '+ci['others'] if ci['others'] else ''))
        if not ci['sp']: it.update(sp='',reason='customer found in SH orders but no sales person on them')
    else:
        it.update(customer=tagshown or '(no customer in item name)',tag=tagshown,conf='',basis='no match' if tagshown else 'no tag',sp='',sp_note='',reason=('end customer is Standard Holdings itself' if 'standard holdings' in tagshown.lower() else 'tag not found among SH customer names') if tagshown else 'no customer tag in name')
    it['new']={'new':'New','updated':'Updated'}.get(it['src'],'')
    it['ord24']='Y' if it['last_order']>='2024-09-25' else 'N'
    rows.append(it)

# ---- SH order-line evidence (19 Sep - 18 Oct), pulled 18 Oct
import warnings; warnings.filterwarnings('ignore')
from openpyxl import load_workbook
XL='/root/exports/zoho/native/2026-10-18/sh/SH_Sales_Order_2026-09-19_2026-10-18.xlsx'
nm=lambda s:' '.join(re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).split())
_tl=[]; by_name=collections.defaultdict(list); by_sku=collections.defaultdict(list); sos=set(); nlines=0; failed=0; nosp=0
_it=load_workbook(XL,read_only=True).worksheets[0].iter_rows(values_only=True); _h=list(next(_it)); _ix={k:_h.index(k) for k in('SalesOrder Number','Customer Name','Item Name','SKU','Sales Person')}
for _r in _it:
    if not _r[_ix['SalesOrder Number']]: continue
    sos.add(_r[_ix['SalesOrder Number']]); nlines+=1
    sp=(_r[_ix['Sales Person']] or '').strip()
    if not sp: nosp+=1
    rec=(sp,(_r[_ix['Customer Name']] or '').strip())
    _tl.append((rec,_r[_ix['Item Name']] or ''))
    by_name[nm(_r[_ix['Item Name']])].append(rec)
    if _r[_ix['SKU']]: by_sku[str(_r[_ix['SKU']]).strip().lower()].append(rec)
nso=len(sos)
LINES={'sos':nso,'lines':nlines,'failed':failed,'lines_without_salesperson':nosp}
dis=[]; meth=collections.Counter()
for d in rows:
    d['sp_name_match']=d['sp']; d['sp_src']='customer-name match' if d['sp'] else 'none'
    ev=by_name.get(nm(d['name'])); how='exact/normalised name'
    if not ev and d['sku']: ev=by_sku.get(d['sku'].strip().lower()); how='SKU'
    if ev:
        meth[how]+=1
        c=collections.Counter(sp for sp,_ in ev if sp)
        real=collections.Counter({k:v for k,v in c.items() if k not in PSEUDO}) or c
        if real:
            top,n=real.most_common(1)[0]
            tie=[k for k,v in real.items() if v==n and k!=top]
            cc=collections.Counter(cu for sp,cu in ev if sp==top).most_common(1)[0][0]
            if d['sp'] and d['sp']!=top: dis.append((d['name'],d['sp_name_match'],d['customer'],top,cc,dict(real)))
            if not d['sp'] or d['sp']!=top: d['customer']=cc if (not d['sp'] or d['sp']!=top) else d['customer']
            d['sp']=top; d['sp_src']='order lines'; d['conf']=d['conf'] if d['sp_name_match']==top else 'Order lines'
            d['sp_note']=(('tie with '+', '.join(tie)+'; ') if tie else '')+f'{sum(real.values())} SH order lines'
            d.pop('reason',None)
    d['linked']=bool(ev)
json.dump(rows,open(P+'rows_final.json','w'))
with open(here+'/../salesperson-disagreements.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['item','sales person (customer-name match)','customer (name match)','sales person (order lines)','customer (order lines)','lines per sales person'])
    for r in dis: w.writerow(list(r[:5])+[json.dumps(r[5])])

# ---- tag on order lines: bracket tag in SH item names -> SH customer -> sales person (local export only)
tagmap=collections.defaultdict(lambda:{'sp':collections.Counter(),'cu':collections.defaultdict(collections.Counter),'n':0,'bad':0})
for (sp,cu),iname in _tl:
    for t in {x for x in tags_of(iname) if x and not JUNK.search(x)}:
        k=' '.join(sorted(toks(t)))
        if not k: continue
        e=tagmap[k]; e['n']+=1
        if not sp or sp=='Internal' or 'standard holdings' in cu.lower(): e['bad']+=1; continue
        e['sp'][sp]+=1; e['cu'][sp][cu]+=1
tagmap={k:e for k,e in tagmap.items() if e['sp'] and e['bad']*2<=e['n']}
tagkeys=list(tagmap)
tagnew=collections.defaultdict(lambda:[0,None])
for d in rows:
    if d['sp_src']!='none': continue
    best=None
    for t in reversed([x for x in tags_of(d['name']) if x and not JUNK.search(x)]):
        k=' '.join(sorted(toks(t)))
        if not k: continue
        if k in tagmap: best=(k,'exact',t); break
        if len(k)>=5:
            for kk in tagkeys:
                if abs(len(kk)-len(k))<=2 and difflib.SequenceMatcher(None,k,kk).ratio()>=0.92: best=(kk,'fuzzy',t); break
        if best: break
    if not best: continue
    kk,how,t=best; e=tagmap[kk]; (top,n),=e['sp'].most_common(1); runner=[f'{s} ({v})' for s,v in e['sp'].most_common()[1:]]
    cu=e['cu'][top].most_common(1)[0][0]
    d['sp']=top; d['customer']=cu; d['sp_src']='tag on order lines'
    d['conf']='High' if how=='exact' and not runner else ('Medium' if how=='exact' else 'Low')
    d['sp_note']=('also: '+', '.join(runner)+'; ' if runner else '')+f'{sum(e["sp"].values())} SH lines with this tag'; d.pop('reason',None)
    tagnew[(t,cu,top)][0]+=1; tagnew[(t,cu,top)][1]=how
json.dump(rows,open(P+'rows_final.json','w'))
tn=sorted(tagnew.items(),key=lambda x:-x[1][0])
print('TAG-NEW',sum(v[0] for k,v in tn),'top10',[(k,v[0]) for k,v in tn[:10]])
print('LINES',LINES,dict(meth),'linked',sum(d['linked'] for d in rows),'disagree',len(dis))
# ---- workbook
NAVY='1F3A5F';TEAL='1B7F8C';ZEB='EAF4F5';WHITE='FFFFFF'
fnt=lambda **k:Font(name='Calibri',**k)
thin=Side(style='thin',color='BFD0D6');thick=Side(style='medium',color=TEAL)
COLS=[('Customer',30),('Item name',52),('SKU',12),('Type',8),('Unit',8),('Division',24),('Category',16),('Status',9),('Ordered in last 24 months',11),('Ordered in last 12 months',11),('Last ordered',12),('Usual order qty (median)',12),('Order lines (all time)',10),('New / updated since 19 Sep',11),('Customer match',10),('Source of salesperson',16),('Zoho item ID',21)]
def rowvals(r): 
    return [r['customer'],r['name'],r['sku'],r['type'],r['unit'],r['division'],r['category'],r['status'],r['ord24'],r['live_12m'],r['last_order'],float(r['median_qty']) if r['median_qty'] not in('',None) else None,r['order_lines'],r['new'],r['conf'] or '-',r['sp_src'],r['item_id']]
def sheet(ws,title,sub,data,extra_first=None):
    cols=([extra_first] if extra_first else [])+COLS
    ws.sheet_view.showGridLines=False
    ws['A1']=title; ws['A1'].font=fnt(size=16,bold=True,color=NAVY)
    ws['A2']=sub; ws['A2'].font=fnt(size=10,italic=True,color='555555')
    hr=4
    for j,(h,w) in enumerate(cols,1):
        c=ws.cell(hr,j,h); c.font=fnt(bold=True,color=WHITE); c.fill=PatternFill('solid',fgColor=NAVY if j%2 else TEAL)
        c.alignment=Alignment(wrap_text=True,vertical='center',horizontal='center'); ws.column_dimensions[get_column_letter(j)].width=w
    ws.row_dimensions[hr].height=42
    prev=None; band=False; r=hr
    for d in data:
        r+=1; key=(d.get('sp') if extra_first else None,d['customer'])
        first=key!=prev
        if first: band=not band
        prev=key
        vals=([d['sp'] or 'Unassigned'] if extra_first else [])+rowvals(d)
        for j,v in enumerate(vals,1):
            c=ws.cell(r,j,v); c.font=fnt(size=10,bold=(first and cols[j-1][0]=='Customer')); c.alignment=Alignment(wrap_text=True,vertical='top',horizontal='center' if cols[j-1][1]<=12 or cols[j-1][0] in('Status','Type') else 'left')
            c.border=Border(top=thick if first else thin,bottom=thin,left=thin,right=thin)
            if band: c.fill=PatternFill('solid',fgColor=ZEB)
        ws.cell(r,len(vals)).number_format='@'
        fq=[j for j,(h,w) in enumerate(cols,1) if h.startswith('Usual')][0]; ws.cell(r,fq).number_format='#,##0.##'
        if d['status']=='Inactive': ws.cell(r,[j for j,(h,w) in enumerate(cols,1) if h=='Status'][0]).font=fnt(size=10,color='B03A2E',bold=True)
    last=max(r,hr+1)
    ws.auto_filter.ref=f"A{hr}:{get_column_letter(len(cols))}{last}"
    ws.freeze_panes=ws.cell(hr+1,3 if not extra_first else 4)
    ws.page_setup.orientation='landscape'; ws.page_setup.paperSize=9; ws.page_setup.fitToWidth=1; ws.page_setup.fitToHeight=0
    ws.sheet_properties.pageSetUpPr.fitToPage=True; ws.print_title_rows=f'{hr}:{hr}'
    ws.oddFooter.center.text='Page &P of &N'; ws.oddFooter.left.text='SPS customized items catalogue'
    ws.print_options.horizontalCentered=True
    return last-hr
srt=lambda L:sorted(L,key=lambda d:(d['customer'].lower(),0 if d['status']=='Active' else 1,0 if d['ord24']=='Y' else 1,d['name'].lower()))
bysp=collections.defaultdict(list); unas=[]
for d in rows:
    (bysp[d['sp']] if d['sp'] else unas).append(d)
wb=Workbook(); cv=wb.active; cv.title='Cover'
names=sorted(bysp,key=lambda k:-len(bysp[k]))
used=set(); cnt={}
def safe(n):
    s=re.sub(r'[\[\]\*\?/\\:]','',n)[:31]; b=s;i=2
    while s.lower() in used or s.lower() in('cover','all items','unassigned','check'): s=b[:28]+f' {i}';i+=1
    used.add(s.lower()); return s
sheetnames={}
asof='Item list as of 19 Sep 2026 (saved Zoho export; items changed after that are not included). Sales-person evidence from SH order lines 19 Sep to 17 Oct 2026.'
for n in names:
    ws=wb.create_sheet(safe(n)); sheetnames[n]=ws.title
    cnt[n]=sheet(ws,f'{n}  |  customized items by customer',f'{len(bysp[n])} items, {len({d["customer"] for d in bysp[n]})} customers.  Filter any column; the customer name is on every row.',srt(bysp[n]))
ws=wb.create_sheet('All Items')
allr=sorted(rows,key=lambda d:((d['sp'] or 'zzz').lower(),d['customer'].lower(),0 if d['status']=='Active' else 1,d['name'].lower()))
sheet(ws,'All customized items (flat list)',f'{len(rows)} items. Filter by Sales Person, Customer, Type, Status or Ordered in last 24 months.',allr,extra_first=('Sales Person',20))
ws=wb.create_sheet('Unassigned')
ur=sorted(unas,key=lambda d:(d['customer'].lower(),d['name'].lower()))
sheet(ws,'Unassigned: no sales person could be found',f'{len(unas)} items. Grouped by the customer tag in the item name. Reason is in the last column.',ur)
ws2=ws; col=len(COLS)+1
ws2.cell(4,col,'Why unassigned').font=fnt(bold=True,color=WHITE); ws2.cell(4,col).fill=PatternFill('solid',fgColor=NAVY); ws2.cell(4,col).alignment=Alignment(horizontal='center',vertical='center',wrap_text=True); ws2.column_dimensions[get_column_letter(col)].width=34
for i,d in enumerate(ur,5): ws2.cell(i,col,d.get('reason','')).font=fnt(size=10); ws2.cell(i,col).alignment=Alignment(wrap_text=True,vertical='top')
ws2.auto_filter.ref=f"A4:{get_column_letter(col)}{max(4+len(ur),5)}"
ws=wb.create_sheet('Check')
ws['A1']='Check: names that look customized but the Zoho field is not Customized'; ws['A1'].font=fnt(size=16,bold=True,color=NAVY)
ws['A2']='Not included in the catalogue. Item name starts SP- or CP- and ends with a (customer) tag, but Finished Good Type is not Customized. Worth a look in Zoho.'; ws['A2'].font=fnt(size=10,italic=True,color='555555')
H=[('Item name',56),('Finished Good Type',18),('Status',10),('BU',8),('Last modified',13),('Zoho item ID',22)]
for j,(h,w) in enumerate(H,1):
    c=ws.cell(4,j,h); c.font=fnt(bold=True,color=WHITE); c.fill=PatternFill('solid',fgColor=NAVY if j%2 else TEAL); c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True); ws.column_dimensions[get_column_letter(j)].width=w
for i,c in enumerate(sorted(check,key=lambda x:x['name'].lower()),5):
    for j,v in enumerate([c['name'],c['cf_fg_type'],c['status'].title(),c['bu'],c['modified'],c['item_id']],1):
        x=ws.cell(i,j,v); x.font=fnt(size=10); x.alignment=Alignment(vertical='top',wrap_text=True); x.border=Border(bottom=thin)
        if i%2: x.fill=PatternFill('solid',fgColor=ZEB)
ws.auto_filter.ref=f"A4:F{max(4+len(check),5)}"; ws.freeze_panes='A5'
ws.page_setup.orientation='landscape'; ws.page_setup.fitToWidth=1; ws.page_setup.fitToHeight=0; ws.sheet_properties.pageSetUpPr.fitToPage=True; ws.print_title_rows='4:4'
# ---- cover
cv.sheet_view.showGridLines=False
cv.column_dimensions['A'].width=3; cv.column_dimensions['B'].width=34; cv.column_dimensions['C'].width=14; cv.column_dimensions['D'].width=14;cv.column_dimensions['E'].width=60
def put(r,c,v,**k):
    x=cv.cell(r,c,v); x.font=fnt(**k); return x
for c in range(1,6): cv.cell(1,c).fill=PatternFill('solid',fgColor=NAVY); cv.cell(2,c).fill=PatternFill('solid',fgColor=NAVY)
put(1,2,'SmartPack customized items catalogue',size=22,bold=True,color=WHITE); put(2,2,'Customized items grouped by sales person, then customer',size=11,color='CFE8EC')
put(4,2,'Prepared by Abdul Hadhee | IT Executive',size=11,bold=True,color=NAVY); put(5,2,'Date: 18 October 2026',size=10)
put(6,2,asof,size=10,italic=True,color='555555')
put(8,2,'How to use',size=13,bold=True,color=TEAL)
tips=['Open the sheet with your name. Each customer is a block; the first row of a block has a heavier top line and the customer name in bold.',
 'Every sheet has filter arrows on the header row. The customer name is repeated on every row, so filtering by customer or item always works.',
 'To hide old items: filter "Ordered in last 24 months" = Y, or Status = Active.',
 '"All Items" lists everything with a Sales Person column. "Unassigned" holds items no sales person could be linked to. "Check" lists names that look customized but are not marked Customized in Zoho.',
 'Quantities are the usual (median) order quantity from past orders. No prices or finance figures are included.']
for i,t in enumerate(tips): c=put(9+i,2,'•  '+t,size=10); cv.merge_cells(start_row=9+i,start_column=2,end_row=9+i,end_column=5); c.alignment=Alignment(wrap_text=True,vertical='top'); cv.row_dimensions[9+i].height=30
r=15; put(r,2,'Items per sales person',size=13,bold=True,color=TEAL)
r+=1
for j,h in enumerate(['Sales person','Items','Customers','Sheet'],2):
    c=put(r,j,h,bold=True,color=WHITE,size=10); c.fill=PatternFill('solid',fgColor=NAVY)
for n in names:
    r+=1; put(r,2,n,size=10); put(r,3,len(bysp[n]),size=10); put(r,4,len({d['customer'] for d in bysp[n]}),size=10)
    c=put(r,5,sheetnames[n],size=10,color='0563C1'); c.hyperlink=f"#'{sheetnames[n]}'!A1"
r+=1; put(r,2,'Unassigned',size=10); put(r,3,len(unas),size=10); put(r,4,len({d['customer'] for d in unas}),size=10); c=put(r,5,'Unassigned',size=10,color='0563C1'); c.hyperlink="#'Unassigned'!A1"
r+=1; put(r,2,'Total customized items',size=10,bold=True); put(r,3,len(rows),size=10,bold=True)
r+=2; put(r,2,'Which items are included',size=13,bold=True,color=TEAL)
inc=[f'Every SPS item whose Zoho field Finished Good Type = Customized: {len(rows)} items ({sum(d["status"]=="Active" for d in rows)} active, {sum(d["status"]=="Inactive" for d in rows)} inactive).',
 f'Rule: nothing is dropped. Use the Status and "Ordered in last 24 months" columns to filter old items out ({sum(d["ord24"]=="Y" for d in rows)} were ordered in the last 24 months).',
 'Items created or changed in Zoho after 19 Sep 2026 are not in this file (no live Zoho calls were made for it). The New / updated column is therefore empty.']
for i,t in enumerate(inc): c=put(r+1+i,2,'•  '+t,size=10); cv.merge_cells(start_row=r+1+i,start_column=2,end_row=r+1+i,end_column=5); c.alignment=Alignment(wrap_text=True,vertical='top'); cv.row_dimensions[r+1+i].height=30
r+=len(inc)+2; put(r,2,'How sales person was found',size=13,bold=True,color=TEAL)
conf=collections.Counter(d['conf'] or 'none' for d in rows)
srcc=collections.Counter(d['sp_src'] for d in rows)
mp=[f'1. Order lines ({srcc["order lines"]} items): the item was found on SH sales-order lines dated 19 Sep to 17 Oct 2026 (Zoho native sales-order export; {LINES["sos"]:,} orders, {LINES["lines"]:,} lines, matched by item name, then SKU). The sales person is the one on most of those lines; this beats the other methods when they differ.',
 f'2. Tag on order lines ({srcc["tag on order lines"]} items): the customer (bracket) tag in the item name also appears in the item names on those SH order lines (for example a Coffee Manor cup sold to C M Partners). The sales person is the most frequent on lines with that tag (runner-up noted in the file); tags mostly sold to Standard Holdings or Internal are ignored; Customer match = High (one sales person), Medium (several), Low (close spelling only).',
 f'3. Customer-name match ({srcc["customer-name match"]} items): otherwise the customer is the (bracket) tag in the item name, matched to an SH customer name; the sales person is the most frequent one on that customer\'s SH orders in the last 12 months to 19 Sep 2026 ({len(so12):,} orders), falling back to 24 months, then all time. Customer match column: High = same name, Medium = tag is part of the SH name, Low = approximate (check these).',
 f'4. None ({srcc["none"]} items): no sales person could be found; they are on the Unassigned sheet. Internal and Maradana Retail Chain are sales-person values in Zoho and have their own sheets where their customers map to them.',
 'Order quantities, last-ordered dates and the 12/24-month flags come from the SPS sales orders to 25 Sep 2026 (17 Oct catalogue).']
for i,t in enumerate(mp): c=put(r+1+i,2,'•  '+t,size=10); cv.merge_cells(start_row=r+1+i,start_column=2,end_row=r+1+i,end_column=5); c.alignment=Alignment(wrap_text=True,vertical='top'); cv.row_dimensions[r+1+i].height=58
cv.page_setup.orientation='portrait'; cv.page_setup.fitToWidth=1; cv.page_setup.fitToHeight=0; cv.sheet_properties.pageSetUpPr.fitToPage=True
wb.save(OUT)
print('saved',OUT); print({n:len(bysp[n]) for n in names},'unassigned',len(unas),'check',len(check),'total',len(rows),dict(conf))
