"""Pull SPS items sorted by last_modified desc until older than 2026-09-19. Writes ../pulls/sps_items_recent.json (GET only)."""
import json,subprocess,os
here=os.path.dirname(os.path.abspath(__file__)); out=here+'/../pulls/sps_items_recent.json'
CUT='2026-09-19'; p=1
while True:
    path=f"items?filter_by=Status.All&sort_column=last_modified_time&sort_order=D&per_page=200&page={p}"
    r=subprocess.run(['node',here+'/cdpget.mjs',out,path],env={**os.environ,'PORT':'9335','ORG':'843825512'},capture_output=True,text=True,timeout=150)
    print(r.stdout.strip(),r.stderr.strip()[:200],flush=True)
    d=json.load(open(out)).get(path)
    if not d or d['st']!=200: print('STOP',d and d['st']); break
    it=d['body']['items']
    print('page',p,it[-1]['last_modified_time'],flush=True)
    if it[-1]['last_modified_time'][:10]<CUT or not d['body']['page_context']['has_more_page']: print('DONE'); break
    p+=1
