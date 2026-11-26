# Part A.3 + live line check: from detail pulls (266 SOs created 16 Sep-8 Oct; 44 stratified sample SOs with comments) -- measured
import json,collections,datetime as dt
d=json.load(open('pulls/details.json'))
sos={k.split('/')[-1]:v['body']['salesorder'] for k,v in d.items() if v['st']==200 and 'comments' not in k and 'salesorder' in v['body']}
cms={k.split('/')[-2]:v['body']['comments'] for k,v in d.items() if k.endswith('/comments') and v['st']==200}
sample=json.load(open('pulls/sample_ids.json')); sid={s[0] for s in sample}
print('details',len(sos),'comments',len(cms))
# creators
cr=collections.Counter(); crdiv=collections.defaultdict(collections.Counter)
for i,s in sos.items():
    h=s['custom_field_hash'].get('cf_manufacturing_division')
    cr[s.get('created_by_name')]+=1; crdiv[s.get('created_by_name')][h]+=1
print('creators',cr.most_common())
for k,c in crdiv.items(): print(' ',k,dict(c.most_common(6)))
# live line tags vs header (SOs created since 16 Sep)
recent=[s for i,s in sos.items() if i not in sid or s['created_time']>='2026-09-16']
recent=[s for s in recent if s['created_time']>='2026-09-16']
print('recent SOs',len(recent))
tot=tag=0; agree=collections.Counter(); hdrset=0; crossline=0
for s in recent:
    h=s['custom_field_hash'].get('cf_manufacturing_division'); hdrset+= bool(h)
    tags=set()
    for l in s['line_items']:
        tot+=1
        t=[x['tag_option_name'] for x in l.get('tags',[]) if x['tag_name']=='Division']
        if t: tag+=1; tags.add(t[0]); agree[(h,t[0])]+=1
        else: agree[(h,'(none)')]+=1
    if len(tags)>1: crossline+=1
print('lines',tot,'with Division tag',tag,round(100*tag/max(tot,1),1),'%; header set',hdrset,'of',len(recent),'; SOs with >1 distinct line tags',crossline)
for k,v in sorted(agree.items(),key=lambda x:-x[1])[:20]: print(' ',k,v)
# other reporting-tag names on SO header / lines
tn=collections.Counter()
for s in sos.values():
    for t in s.get('tags',[]) or []: tn[('hdr',t.get('tag_name'))]+=1
    for l in s['line_items']:
        for t in l.get('tags',[]): tn[('line',t['tag_name'])]+=1
print('tag names',tn)
print('SO header keys of interest',[k for k in next(iter(sos.values())) if any(w in k for w in('sales','location','warehouse','created_by','branch','custom_field','tag'))])
# edits after creation (from list rows we know last_modified); in sample: compare created vs last_modified and 'Sales Order updated' comments
rows=[]
for sidv,num,div,cr_t in sample:
    s=sos.get(sidv); cl=cms.get(sidv,[])
    if not s: continue
    upd=[c for c in cl if c['transaction_type']=='salesorder' and c['operation_type']=='Updated']
    created=[c for c in cl if c['transaction_type']=='salesorder' and c['operation_type']=='Added']
    rows.append(dict(so=num,div=div,created_by=s.get('created_by_name'),created=s['created_time'][:16],last_mod=s['last_modified_time'][:16],last_mod_by=s.get('last_modified_by_id'),n_so_updates=len(upd),updaters=sorted({c['commented_by'] for c in upd}),upd_desc=[c['description'][:70] for c in upd][:3],n_comments=len(cl)))
print('sample',len(rows))
print('creators in sample',collections.Counter(r['created_by'] for r in rows))
print('SOs edited after creation (last_modified > created+5min):',sum(1 for r in rows if dt.datetime.fromisoformat(r['last_mod'])>dt.datetime.fromisoformat(r['created'])+dt.timedelta(minutes=5)),'of',len(rows))
print('with SO "Updated" comment:',sum(1 for r in rows if r['n_so_updates']),'; descriptions',collections.Counter(x for r in rows for x in r['upd_desc']).most_common(6))
print('updaters',collections.Counter(u for r in rows for u in r['updaters']))
# who commented anything on the SO, by transaction type
print('actors',collections.Counter((c['commented_by'],c['transaction_type']) for l in cms.values() for c in l).most_common(14))
# header division changed? line tags vs header on sample
mis=0
for sidv,num,div,_ in sample:
    s=sos.get(sidv)
    if not s: continue
    h=s['custom_field_hash'].get('cf_manufacturing_division')
    t={x['tag_option_name'] for l in s['line_items'] for x in l.get('tags',[]) if x['tag_name']=='Division'}
    rows_=(h,sorted(t))
json.dump(rows,open('pulls/history_sample.json','w'),indent=1,default=str)
