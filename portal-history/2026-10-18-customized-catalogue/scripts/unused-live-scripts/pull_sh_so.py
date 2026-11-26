"""Pull SH sales-order list (GET only) back to 2026-06-01 (about 4.5 months; 12 months would need about 3 h at Zoho speed); keep only customer/salesperson/date/number fields (no finance) in ../pulls/sh_so_compact.json."""
import json,subprocess,os,time
here=os.path.dirname(os.path.abspath(__file__)); pulls=here+'/../pulls/'
raw=pulls+'_sh_raw_page.json'; outf=pulls+'sh_so_compact.json'
CUT='2026-06-01'; env={**os.environ,'PORT':'9333','ORG':'843061977','TAB':'F14FFA5CF9C42641144A8345FBB0B929'}
rows=json.load(open(outf)) if os.path.exists(outf) else {}
p=max([r['_p'] for r in rows.values()],default=0)+1
while True:
    path=f"salesorders?filter_by=Status.All&sort_column=date&sort_order=D&per_page=200&page={p}&date_start={CUT}"
    if os.path.exists(raw): os.remove(raw)
    r=subprocess.run(['node',here+'/cdpget.mjs',raw,path],env=env,capture_output=True,text=True,timeout=150)
    d=json.load(open(raw)).get(path) if os.path.exists(raw) else None
    if not d or d['st']!=200: print('STOP',p,r.stderr[:200],flush=True); break
    so=d['body']['salesorders']
    for s in so:
        rows[s['salesorder_id']]={k:s.get(k) for k in('salesorder_number','date','customer_name','customer_id','salesperson_name','location_name','cf_business_unit')}|{'_p':p}
    json.dump(rows,open(outf,'w'))
    print('page',p,len(rows),so[-1]['date'],flush=True)
    if not so or so[-1]['date']<CUT or not d['body']['page_context']['has_more_page']: print('DONE',flush=True); break
    p+=1
if os.path.exists(raw): os.remove(raw)
