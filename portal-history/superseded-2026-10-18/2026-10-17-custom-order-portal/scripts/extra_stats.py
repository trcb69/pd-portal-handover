"""usage: extra_stats.py DATA_DIR  (reads catalogue + end-customers csv) -> prints extra numbers"""
import csv, sys, re
from collections import Counter
d = sys.argv[1]
cat = list(csv.DictReader(open(f"{d}/customized-catalogue.csv"))); ec = list(csv.DictReader(open(f"{d}/end-customers.csv")))
live = [c for c in cat if c['live_12m'] == 'Y']
def custs(c): return [re.sub(r' \(\d+\)$', '', x) for x in c['top3_end_customers'].split('; ') if x]
SH = 'Standard Holdings (Pvt) Ltd'
print('live items with a non-SH end customer in top3:', sum(1 for c in live if any(x != SH for x in custs(c))))
print('live items whose top1 is SH:', sum(1 for c in live if custs(c) and custs(c)[0] == SH))
print('live items w/ single end customer in top3 list (<=1 name):', sum(1 for c in live if len(custs(c)) == 1))
print('live items with name tag == top non-SH customer prefix (loose):', sum(1 for c in live if c['name_customer_tag'] and any(c['name_customer_tag'].lower()[:4] in x.lower() for x in custs(c))))
print('end customers (non-SH) with >=1 live item (top3 only):', len({x for c in live for x in custs(c) if x != SH}))
print('live items per name_kind/unit bands: median qty median', sorted(float(c['median_qty']) for c in live if c['median_qty'])[len(live)//2])
print('live items with median_price blank', sum(1 for c in live if not c['median_price']))
print('live items artwork ever NA', sum(c['artwork_ever_not_available']=='Y' for c in live), 'dye', sum(c['dye_cutter_ever_not_available']=='Y' for c in live), 'screen', sum(c['screen_plate_ever_not_available']=='Y' for c in live))
print('all items artwork ever NA', sum(c['artwork_ever_not_available']=='Y' for c in cat), 'dye', sum(c['dye_cutter_ever_not_available']=='Y' for c in cat), 'screen', sum(c['screen_plate_ever_not_available']=='Y' for c in cat))
print('live with share_reorder==1', sum(1 for c in live if c['share_reorder']=='1.0'), 'share_new_order>0', sum(1 for c in live if c['share_new_order'] not in ('','0.0')))
print('live stock>0 (16 Sep item master)', sum(1 for c in live if c['stock_on_hand_item_master_16sep'] not in ('',) and float(c['stock_on_hand_item_master_16sep'])>0), 'blank', sum(1 for c in live if c['stock_on_hand_item_master_16sep']==''))
print('SH row', [ (e['order_lines'],e['distinct_sos'],e['customized_item_lines'],e['distinct_customized_items']) for e in ec if e['end_customer']==SH])
print('ec with norm-groups:', [(e['end_customer'], e['same_after_normalising_case_punctuation']) for e in ec if e['same_after_normalising_case_punctuation']][:8])
print('ec near variants sample:'); [print('  ',e['end_customer'],'<>',e['near_variants_unmerged'][:110]) for e in ec if e['near_variants_unmerged']][:0]
for e in [e for e in ec if e['near_variants_unmerged']][:14]: print('  ',e['end_customer'],'<>',e['near_variants_unmerged'][:110])
print('ec with zero customized items:', sum(1 for e in ec if e['customized_item_lines']=='0'))
print('mfg division blank in live', sum(1 for c in live if not c['manufacturing_division']))
print('live by bu', Counter(c['cf_bu'] for c in live).most_common())
print('live names len>90', sum(len(c['name'])>90 for c in live), 'live no tag', sum(1 for c in live if not c['name_customer_tag']))
print('items with order_lines but inactive status', [(c['name'][:50],c['last_order']) for c in cat if c['status']!='Active'][:3])
