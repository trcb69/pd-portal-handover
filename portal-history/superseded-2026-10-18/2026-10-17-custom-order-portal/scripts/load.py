import openpyxl, pickle, sys, warnings
warnings.filterwarnings('ignore')
def rows(path, sheet=None):
    wb=openpyxl.load_workbook(path,read_only=True)
    ws=wb[sheet] if sheet else wb.worksheets[0]
    it=ws.iter_rows(values_only=True)
    h=list(next(it)); out=[]
    for r in it:
        if all(v is None or v=='' for v in r): continue
        out.append(dict(zip(h,r)))
    return h,out
if __name__=='__main__':
    out=sys.argv[1]; d={}
    for k,p,s in [('so','/root/exports/zoho/sps/2026-09-27/item1/Sales_Order.xlsx','Sales Order'),('inv','/root/exports/zoho/sps/2026-09-27/item1/Invoice.xlsx','Invoice'),('pkg','/root/exports/zoho/native/2026-09-16/Package_ALL.xlsx',None),('shp','/root/exports/zoho/native/2026-09-16/Shipment_ALL.xlsx',None),('item','/root/exports/zoho/native/2026-09-16/Item.xlsx',None)]:
        h,r=rows(p,s); d[k]=r; print(k,len(r),flush=True)
    pickle.dump(d,open(out,'wb'))
