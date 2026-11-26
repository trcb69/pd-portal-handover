# Part B: per-day Zoho change volume (measured) and modelled API calls for continuous sync (modelled). SPS, window 2025-10-08 .. 2026-10-07
import json,glob,collections,statistics,datetime as dt,csv
def load(prefix,key,idk):
    out={}
    for f in sorted(glob.glob(f'pulls/{prefix}_p*.json')):
        for r in json.load(open(f))[key]: out[r[idk]]=r
    return out
def ts(v):
    if isinstance(v,(int,float)) or (isinstance(v,str) and v.isdigit()):
        return dt.datetime.fromtimestamp(int(v)/1000,dt.timezone(dt.timedelta(hours=5,minutes=30))).replace(tzinfo=None)
    return dt.datetime.strptime(v[:19],'%Y-%m-%dT%H:%M:%S')
so=load('so_created','salesorders','salesorder_id')
for f in sorted(glob.glob('pulls/so_modified_p*.json')):
    for r in json.load(open(f))['salesorders']: so.setdefault(r['salesorder_id'],r)
pk=load('pkg','packages','package_id'); sh=load('ship','shipmentorders','shipment_id'); iv=load('inv','invoices','invoice_id'); pl=load('pick','picklists','picklist_id')
soid_by_num={r['salesorder_number']:k for k,r in so.items()}
D0,D1=dt.datetime(2025,10,8),dt.datetime(2026,10,8)
inwin=lambda t:D0<=t<D1
ev=[]  # (time, kind, so_key, doc_key)
for k,r in so.items():
    c=ts(r['created_time']); m=ts(r['last_modified_time'])
    ev.append((c,'so_created',k,None))
    if m>c+dt.timedelta(seconds=30): ev.append((m,'so_modified',k,None))
for k,r in pk.items(): ev.append((ts(r['created_time']),'pkg_created',r.get('salesorder_id'),('pkg',k)))
for k,r in sh.items(): ev.append((ts(r['created_time']),'ship_created',r.get('salesorder_id'),('ship',k)))
for k,r in iv.items():
    ref=soid_by_num.get((r.get('reference_number') or '').strip())
    ev.append((ts(r['created_time']),'inv_created',ref,('inv',k)))
for k,r in pl.items():
    nums=r.get('salesorder_numbers') or []
    nums=nums if isinstance(nums,list) else [nums]
    ev.append((ts(r['created_time']),'pick_created',soid_by_num.get(nums[0]) if nums else None,('pick',k)))
ev=[e for e in ev if inwin(e[0])]
days=[(D0+dt.timedelta(days=i)).date() for i in range(365)]
cnt=collections.defaultdict(collections.Counter)
for t,kind,_,_ in ev: cnt[t.date()][kind]+=1
kinds=['so_created','so_modified','pkg_created','ship_created','inv_created','pick_created']
print('per-day counts (median / p95 / max):')
def pct(v,p): v=sorted(v); return v[min(len(v)-1,int(round(p*(len(v)-1))))]
summ={}
for k in kinds:
    v=[cnt[d][k] for d in days]; summ[k]=(statistics.median(v),pct(v,.95),max(v),sum(v)); print(' ',k,summ[k])
invmatch=sum(1 for e in ev if e[1]=='inv_created' and e[2]); print('invoices mapped to SO via reference_number',invmatch,'of',sum(1 for e in ev if e[1]=='inv_created'))
with open('daily_counts.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['date']+kinds)
    for d in days: w.writerow([d]+[cnt[d][k] for k in kinds])
# model
BUDGET=7500-500
PAGES_FULL=-(-8571//200)  # 43
res={}
for P in (5,2,1):
    polls=24*60//P
    perday_A=[];perday_B=[]; det_only=[]
    byday=collections.defaultdict(list)
    for t,kind,sk,dk in ev: byday[t.date()].append((t,kind,sk,dk))
    for d in days:
        a=set();b=set()
        for t,kind,sk,dk in byday[d]:
            bucket=(t.hour*60+t.minute)//P
            if kind in('so_created','so_modified'): a.add(('so',sk,bucket)); b.add((sk,bucket))
            else:
                a.add((dk,bucket)); b.add((sk if sk else dk,bucket))
                if sk: a.add(('so',sk,bucket))
        det_only.append(len(b)); perday_A.append(len(a))
    for name,lst_mult in (('so_list_only',1),('so+bundles_list',2)):
        for dn,det in (('A_owner(SO+doc details)',perday_A),('B_SO_detail_only',det_only)):
            tot=[polls*lst_mult+x+PAGES_FULL for x in det]
            res[(P,name,dn)]=tot
rows=[]
print('\nMODEL  (calls/day = polls + details + 43-page nightly full header read)')
for (P,name,dn),tot in res.items():
    over=sum(1 for x in tot if x>BUDGET)
    top=sorted(zip(tot,days),reverse=True)[:10]
    row=dict(interval_min=P,lists=name,detail_model=dn,median=int(statistics.median(tot)),p95=pct(tot,.95),max=max(tot),days_over_7000=over,busiest=';'.join(f'{d}:{t}' for t,d in top))
    rows.append(row); print(row)
json.dump(rows,open('modelB.json','w'),indent=1)
# spec as written: 66 hdr slots + 38 bundle slots + 43 full + ~133 live details + history, cap 400
# hourly fraction of change events (busy hours)
hr=collections.Counter(e[0].hour for e in ev); print('events by hour',sorted(hr.items()))
# changed-SO per poll, to check list pages stay at 1
for P in (5,):
    c=collections.Counter()
    for t,kind,sk,dk in ev:
        if kind.startswith('so_'): c[(t.date(),(t.hour*60+t.minute)//P)]+=1
    print('max SO list changes in a 5-min window',max(c.values()),'; windows with >200:',sum(1 for v in c.values() if v>200))

# hybrid: P-min polling 06:00-20:00, hourly otherwise; SO list + bundles list; B detail model
print('\nHYBRID (P-min 06-20h, hourly 21-05h), SO list + bundles list, details B-model, + 43-page full read')
byday=collections.defaultdict(list)
for t,kind,sk,dk in ev: byday[t.date()].append((t,kind,sk,dk))
for P in (5,2,1):
    polls=14*60//P+10
    tot=[]
    for d in days:
        b=set()
        for t,kind,sk,dk in byday[d]:
            h=t.hour
            bucket=(h*60+t.minute)//P if 6<=h<20 else ('n',h)
            b.add((sk if sk else dk,bucket))
        tot.append(polls*2+len(b)+PAGES_FULL)
    print(P,'min:',dict(polls=polls*2,median=int(statistics.median(tot)),p95=pct(tot,.95),max=max(tot)))
# what happened at hour 0 / 21 and the big days
big=collections.Counter(e[0].date() for e in ev if e[1]=='so_modified'); print(big.most_common(5))
h0=collections.Counter((e[1]) for e in ev if e[0].hour in(0,21)); print('hour 0/21 kinds',h0)
