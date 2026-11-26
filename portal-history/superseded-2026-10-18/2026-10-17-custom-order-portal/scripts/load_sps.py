"""Shared loaders. Usage: imported by the other scripts. Read-only."""
import json, openpyxl, warnings
warnings.filterwarnings('ignore')
def so_lines(path):
    ws=openpyxl.load_workbook(path,read_only=True).active
    it=ws.iter_rows(values_only=True); h=list(next(it))
    for r in it:
        if r[0] is None: continue
        yield dict(zip(h,r))
def items(path):
    return json.load(open(path))['rows']
def wh(path):
    d=json.load(open(path)); return {k:{r['item_id']:r for r in d['items_wh_'+k]['rows']} for k in ('wip','rm','fg')}
