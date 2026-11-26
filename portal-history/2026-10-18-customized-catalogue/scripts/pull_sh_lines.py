"""Detached, GET-only. 1) list SH SOs dated 2026-09-19..2026-10-18 (list pages) 2) fetch each SO detail in batches. Resumable.
Saves pulls/sh-so-lines-2026-09-19_2026-10-18/{list.json, batch_NNNN.json (raw detail), slim.json}."""
import json,subprocess,os,sys
here=os.path.dirname(os.path.abspath(__file__)); D=here+'/../pulls/sh-so-lines-2026-09-19_2026-10-18/'
env={**os.environ,'PORT':'9333','ORG':'843061977','TAB':'F14FFA5CF9C42641144A8345FBB0B929'}
def run(f,paths):
    r=subprocess.run(['node',here+'/cdpget.mjs',f]+paths,env=env,capture_output=True,text=True,timeout=1500)
    if r.stderr.strip(): print(r.stderr.strip()[:300],flush=True)
    return json.load(open(f)) if os.path.exists(f) else {}
LF=D+'list.json'; ids=D+'ids.json'
if not os.path.exists(ids):
    allso={}; p=1
    while True:
        path=f"salesorders?filter_by=Status.All&sort_column=date&sort_order=D&per_page=200&page={p}&date_start=2026-09-19&date_end=2026-10-18"
        d=run(LF,[path]).get(path)
        if not d or d['st']!=200: print('LIST STOP',p,d and d['st'],flush=True); sys.exit(1)
        so=d['body']['salesorders']
        for s in so: allso[s['salesorder_id']]={k:s.get(k) for k in('salesorder_number','date','customer_name','salesperson_name')}
        print('list page',p,len(allso),so[-1]['date'] if so else '',flush=True)
        if not d['body']['page_context']['has_more_page'] or not so: break
        p+=1
    allso={k:v for k,v in allso.items() if '2026-09-19'<=v['date']<='2026-10-18'}
    json.dump(allso,open(ids,'w')); os.remove(LF)
allso=json.load(open(ids)); L=list(allso); print('SOs',len(L),flush=True)
B=100
for b in range(0,len(L),B):
    f=D+f'batch_{b//B:04d}.json'
    chunk=L[b:b+B]; paths=[f'salesorders/{i}' for i in chunk]
    d=run(f,paths)
    ok=sum(1 for p in paths if d.get(p,{}).get('st')==200); bad=[(p,d[p]['st']) for p in paths if p in d and d[p]['st']!=200]
    print('batch',b//B,ok,'/',len(chunk),bad[:3],flush=True)
    if len(d)<len(chunk) and not ok==len(chunk): print('STOP (incomplete batch: login/429/timeout?)',flush=True); sys.exit(2)
print('DONE',flush=True)
