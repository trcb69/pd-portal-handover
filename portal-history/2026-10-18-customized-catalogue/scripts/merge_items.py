"""Items: 19 Sep SPS snapshot (cf_fg_type == Customized) + 17 Oct catalogue order stats (no live Zoho calls).
Writes ../pulls/items_merged.json (all items with cf_fg_type == Customized) and ../pulls/merge_stats.json."""
import json,csv,re,os
here=os.path.dirname(os.path.abspath(__file__)); P=here+'/../pulls/'
snap={i['item_id']:i for i in json.load(open('/root/exports/zoho/native/2026-09-19/sps/items.json'))['rows']}
live={}
for f in ():  # live refresh dropped (user decision: saved 19 Sep export only)
    if os.path.exists(P+f):
        for v in json.load(open(P+f)).values():
            if v['st']==200:
                for i in v['body']['items']: live[i['item_id']]=i
full_live = os.path.exists(P+'sps_items_rest.json') and not json.load(open(P+'sps_items_rest.json')) is None
CUT='2026-09-19'
cur={}; src={}
for iid,i in snap.items(): cur[iid]=i; src[iid]='snapshot'
changed=new=0
for iid,i in live.items():
    if i['last_modified_time'][:10]>=CUT:
        if iid not in snap: new+=1; src[iid]='new'
        else: src[iid]='updated'
        cur[iid]=i; changed+=1
# items present in snapshot but absent from a complete live list = deleted
deleted=[iid for iid in snap if live and iid not in live] if len(live)>=len(snap)*0.9 else []
for iid in deleted: src[iid]='deleted_in_zoho'
cat={r['item_id']:r for r in csv.DictReader(open('/root/Project Management/reports/2026-10-17-custom-order-portal/data/customized-catalogue.csv'))}
out=[]
for iid,i in cur.items():
    if i.get('cf_fg_type')!='Customized': continue
    c=cat.get(iid,{})
    out.append({'item_id':iid,'name':i['name'].strip(),'sku':i.get('sku') or '','unit':c.get('unit') or i.get('unit') or '',
      'status':'Active' if i.get('status')=='active' else 'Inactive','bu':i.get('cf_bu') or '','division':c.get('manufacturing_division') or c.get('item_division') or '',
      'category':c.get('finished_good_category') or i.get('cf_fg_sub_category') or '','nature':i.get('cf_fg_nature') or '',
      'src':src[iid],'created':i['created_time'][:10],'modified':i['last_modified_time'][:10],
      'order_lines':int(c['order_lines']) if c else 0,'last_order':c.get('last_order',''),'median_qty':c.get('median_qty',''),
      'live_12m':c.get('live_12m','N') if c else 'N','top_end':c.get('top3_end_customers',''),'in_catalogue':bool(c)})
chk=[]
for iid,i in cur.items():
    if i.get('cf_fg_type')!='Customized' and re.match(r'^(SP|CP)\s*-',i['name'].strip()) and re.search(r'\([^()]+\)\s*$',i['name'].strip()):
        chk.append({'item_id':iid,'name':i['name'].strip(),'cf_fg_type':i.get('cf_fg_type') or '(blank)','status':i.get('status'),'modified':i['last_modified_time'][:10],'bu':i.get('cf_bu') or ''})
json.dump(chk,open(P+'check_items.json','w'))
# was it customized in snapshot but not now (or vice versa)
stat={'snapshot_items':len(snap),'live_list_items':len(live),'changed_since_19sep':changed,'new_since_19sep':new,
 'changed_customized':sum(1 for iid,i in live.items() if i['last_modified_time'][:10]>=CUT and i.get('cf_fg_type')=='Customized'),
 'new_customized':sum(1 for iid,s in src.items() if s=='new' and cur[iid].get('cf_fg_type')=='Customized'),
 'customized_total':len(out),'deleted_in_zoho_all_types':len(deleted),
 'type_changed_to_customized':sum(1 for iid,i in live.items() if i['last_modified_time'][:10]>=CUT and i.get('cf_fg_type')=='Customized' and iid in snap and snap[iid].get('cf_fg_type')!='Customized'),
 'type_changed_from_customized':sum(1 for iid,i in live.items() if i['last_modified_time'][:10]>=CUT and i.get('cf_fg_type')!='Customized' and iid in snap and snap[iid].get('cf_fg_type')=='Customized')}
json.dump(out,open(P+'items_merged.json','w')); json.dump(stat,open(P+'merge_stats.json','w'),indent=1); json.dump(deleted,open(P+'deleted_ids.json','w'))
print(stat)
