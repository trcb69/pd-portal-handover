"""Continue the SPS item list (sorted last_modified desc) to the end, to learn every current item_id (detects items deleted since the 19 Sep snapshot). GET only."""
import json,subprocess,os
here=os.path.dirname(os.path.abspath(__file__)); out=here+'/../pulls/sps_items_rest.json'
p=6
while True:
    path=f"items?filter_by=Status.All&sort_column=last_modified_time&sort_order=D&per_page=200&page={p}"
    subprocess.run(['node',here+'/cdpget.mjs',out,path],env={**os.environ,'PORT':'9335','ORG':'843825512'},capture_output=True,text=True,timeout=150)
    d=json.load(open(out)).get(path)
    if not d or d['st']!=200: print('STOP',p,flush=True); break
    print('page',p,flush=True)
    if not d['body']['page_context']['has_more_page']: print('DONE',flush=True); break
    p+=1
