"""Slim the SH item detail pull (28 Sep, rizwan login) to a pickle. Usage: cache_sh_items.py OUT.pkl"""
import sys,json,glob,pickle
rows=[]
for f in sorted(glob.glob('/root/exports/zoho/native/2026-09-28/sh-rizwan/items/detail/batch_*.json')):
    for r in json.load(open(f))['records']:
        it=r['item']
        rows.append({k:it.get(k) for k in ('item_id','name','sku','status','item_type','track_inventory','stock_on_hand','available_stock','actual_available_stock','committed_stock','available_for_sale_stock','actual_committed_stock','actual_available_for_sale_stock','cf_division','cf_operation_nature','cf_parent_category','cf_sub_category','last_modified_time','reorder_level')}
          | {'locs':[(l['location_name'],l.get('location_stock_on_hand'),l.get('location_available_stock')) for l in it.get('locations',[])]})
pickle.dump(rows,open(sys.argv[1],'wb')); print(len(rows))
