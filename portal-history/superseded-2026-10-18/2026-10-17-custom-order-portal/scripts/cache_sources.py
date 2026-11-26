"""Cache xlsx sources as pickles in a scratch dir (speed only). Usage: cache_sources.py OUTDIR"""
import sys,pickle,openpyxl,warnings; warnings.filterwarnings('ignore')
out=sys.argv[1]
S={'so':'/root/exports/zoho/sps/2026-09-27/item1/Sales_Order.xlsx','inv':'/root/exports/zoho/sps/2026-09-27/item1/Invoice.xlsx',
   'pkg':'/root/exports/zoho/native/2026-09-16/Package_ALL.xlsx'}
for k,p in S.items():
    ws=openpyxl.load_workbook(p,read_only=True).active
    it=ws.iter_rows(values_only=True); h=list(next(it))
    rows=[dict(zip(h,r)) for r in it if any(v is not None for v in r)]
    pickle.dump(rows,open(f'{out}/{k}.pkl','wb')); print(k,len(rows),h[:12])
