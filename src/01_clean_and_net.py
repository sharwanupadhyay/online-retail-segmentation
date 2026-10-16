"""Read source, run fixed regression checks, then chronologically reverse units."""
import time
import re
import json
from collections import defaultdict
import numpy as np
import pandas as pd
from common import ROOT, start, save_results, finish

ORIGINAL = ['POST','D','M','BANK CHARGES','C2','DOT','PADS','CRUK','TEST001','TEST002','ADJUST','ADJUST2','B']
EXPECTED = dict(duplicates=34335, nonproduct=5581, cancellations=18046,
                invalid=5986, missing_id=226844, purchases=776579, customers=5852)

def net_cancellations(purchases, cancellations):
    """LIFO by customer/product; cancellation events precede equal-time purchases."""
    p = purchases.sort_values(['InvoiceDate','source_row']).reset_index(drop=True).copy()
    c = cancellations.sort_values(['InvoiceDate','source_row']).reset_index(drop=True).copy()
    remaining = p.Quantity.to_numpy(dtype=float,copy=True)
    reversed_units = np.zeros(len(c))
    keys = set(zip(c.loc[c.CustomerID.notna(),'CustomerID'],c.loc[c.CustomerID.notna(),'StockCode']))
    events = defaultdict(list)
    for i, row in enumerate(p[['CustomerID','StockCode','InvoiceDate']].itertuples(index=False,name=None)):
        customer,stock,date=row
        if (customer,stock) in keys:
            events[(customer,stock)].append((date,1,i))
    for i,row in enumerate(c[['CustomerID','StockCode','InvoiceDate']].itertuples(index=False,name=None)):
        customer,stock,date=row
        if pd.notna(customer) and c.iloc[i].Quantity < 0:
            events[(customer,stock)].append((date,0,i))
    for ev in events.values():
        stack=[]
        for _,kind,i in sorted(ev):
            if kind:
                stack.append(i)
            else:
                need = -float(c.iloc[i].Quantity)
                while need > 0 and stack:
                    j=stack[-1]
                    take=min(remaining[j],need)
                    remaining[j]-=take
                    need-=take
                    reversed_units[i]+=take
                    if remaining[j] == 0:
                        stack.pop()
    c['cancelled_units']=np.maximum(-c.Quantity.to_numpy(),0)
    c['reversed_units']=reversed_units
    c['unmatched_units']=c.cancelled_units-c.reversed_units
    c['matched_flag']=np.select([(c.cancelled_units>0)&(c.unmatched_units==0),c.reversed_units>0],['matched','partly matched'],default='unmatched')
    p['OriginalQuantity']=p.Quantity
    p['Quantity']=remaining
    p['Revenue']=p.Quantity*p.Price
    return p.loc[p.Quantity>0].copy(),c,p

def main():
    start()
    sheets=pd.read_excel(ROOT/'inputs/online_retail_II.xlsx',sheet_name=None,engine='calamine')
    assert list(sheets)==['Year 2009-2010','Year 2010-2011']
    R={'source':{'file':'online_retail_II.xlsx','access_date':'2026-10-16',
       'url':'https://archive.ics.uci.edu/dataset/502/online+retail+ii','reader':'pandas calamine engine'},'sheets':{},'audit':[]}
    R['assignment']=json.loads((ROOT/'docs/brief_metadata.json').read_text())
    for name,df in sheets.items():
        R['sheets'][name]={'shape':df.shape,'dtypes':df.dtypes.astype(str).to_dict(),
                          'nulls':df.isna().sum().to_dict(),'start':df.InvoiceDate.min(),'end':df.InvoiceDate.max()}
    raw=pd.concat(sheets.values(),ignore_index=True)
    R['source'].update(rows=len(raw),columns=raw.shape[1],start=raw.InvoiceDate.min(),end=raw.InvoiceDate.max())
    R['source']['overlap_start']=max(x.InvoiceDate.min() for x in sheets.values())
    R['source']['overlap_end']=min(x.InvoiceDate.max() for x in sheets.values())
    def audit(before,after,reason):
        R['audit'].append(dict(before=int(before),removed=int(before-after),after=int(after),reason=reason))
    df=raw.drop_duplicates().copy()
    actual={'duplicates':len(raw)-len(df)}
    audit(len(raw),len(df),'Remove exact duplicate rows across both sheets, including their overlapping dates; no fuzzy deduplication.')
    df=df.rename(columns={'Customer ID':'CustomerID'})
    df['source_row']=df.index
    df['StockCode']=df.StockCode.astype(str).str.strip().str.upper()
    df['Invoice']=df.Invoice.astype(str).str.strip().str.upper()
    original=df.loc[~df.StockCode.isin(ORIGINAL)].copy()
    actual['nonproduct']=len(df)-len(original)
    c=original.loc[original.Invoice.str.startswith('C')]
    actual['cancellations']=len(c)
    p=original.loc[~original.Invoice.str.startswith('C')]
    valid=p.loc[(p.Quantity>0)&(p.Price>0)]
    actual['invalid']=len(p)-len(valid)
    actual['missing_id']=int(valid.CustomerID.isna().sum())
    valid=valid.loc[valid.CustomerID.notna()]
    actual.update(purchases=len(valid),customers=valid.CustomerID.nunique())
    print('Original-list regression:',actual,flush=True)
    assert actual==EXPECTED, (actual,EXPECTED)
    R['regression']=actual
    odd=original.loc[~original.StockCode.str.fullmatch(r'\d{5}[A-Z]*')]
    evidence=odd.groupby('StockCode').agg(rows=('Invoice','size'),descriptions=('Description',lambda s:'; '.join(s.dropna().astype(str).unique()[:8]))).reset_index()
    # Only service/fee/voucher descriptions justify an extension. Irregular product codes stay.
    extra=[code for code in evidence.StockCode if code in ['AMAZONFEE','S'] or re.fullmatch(r'GIFT_\d+_\d+',code)]
    evidence['excluded']=evidence.StockCode.isin(extra)
    evidence['justification']=evidence.StockCode.map(lambda code: 'Amazon fee, not merchandise.' if code=='AMAZONFEE' else 'SAMPLES code: non-catalog sample/accounting lines, excluded consistently from sales and cancellations.' if code=='S' else 'Gift voucher liability, excluded from physical-merchandise sales.' if code in extra else 'Irregular syntax alone is not evidence of a non-product; retained.')
    evidence.to_csv(ROOT/'outputs/docs/non_product_evidence.csv',index=False)
    R['nonproduct']={'original':ORIGINAL,'extra':extra,'extra_rows':int(original.StockCode.isin(extra).sum()),'evidence':evidence.to_dict('records')}
    full=df.loc[~df.StockCode.isin(ORIGINAL+extra)].copy()
    audit(len(df),len(original),'Remove only original non-product code list, after uppercase and whitespace normalisation; fixed-list regression passed.')
    audit(len(original),len(full),'Extend exclusions only with documented fee, sample and gift-voucher codes; evidence is in non_product_evidence.csv.')
    c=full.loc[full.Invoice.str.startswith('C')].copy()
    p=full.loc[~full.Invoice.str.startswith('C')].copy()
    audit(len(full),len(p),'Separate all cancellation-invoice rows into a retained cancellation table; these are not booked as sales.')
    valid=p.loc[(p.Quantity>0)&(p.Price>0)].copy()
    audit(len(p),len(valid),'Remove non-cancellation rows with nonpositive quantity or price; no price imputation.')
    missing=valid.loc[valid.CustomerID.isna()]
    R['missing_id']={'rows':len(missing),'revenue':(missing.Quantity*missing.Price).sum(),
                     'purchase_revenue_share':(missing.Quantity*missing.Price).sum()/(valid.Quantity*valid.Price).sum(),
                     'purchase_rows_share':len(missing)/len(valid)}
    p=valid.loc[valid.CustomerID.notna()].copy()
    audit(len(valid),len(p),'Exclude missing-ID positive purchase rows from linked customer analysis; their gross merchandise value and coverage loss are reported separately.')
    tic=time.perf_counter()
    net,c,all_lines=net_cancellations(p,c)
    runtime=time.perf_counter()-tic
    audit(len(p),len(net),'Drop fully reversed purchase lines after chronological customer/product LIFO matching; partly reversed lines retain remaining units at original purchase prices. Unmatched cancellation units remain outside net sales.')
    gross=(p.Quantity*p.Price).sum()
    R['netting']={'runtime_seconds':runtime,'cancellation_rows':len(c),
       'matched':int((c.matched_flag=='matched').sum()),'partly_matched':int((c.matched_flag=='partly matched').sum()),
       'unmatched':int((c.matched_flag=='unmatched').sum()),'cancelled_units':c.cancelled_units.sum(),
       'reversed_units':c.reversed_units.sum(),'unmatched_units':c.unmatched_units.sum(),
       'unmatched_unit_share':c.unmatched_units.sum()/c.cancelled_units.sum(),
       'gross_revenue':gross,'net_revenue':net.Revenue.sum(),'reversed_revenue':gross-net.Revenue.sum(),
       'lines_dropped':len(p)-len(net),'lines_partly_reversed':int(((all_lines.Quantity>0)&(all_lines.Quantity<all_lines.OriginalQuantity)).sum()),
       'net_lines':len(net),'customers':net.CustomerID.nunique(),'cancellation_missing_id_rows':int(c.CustomerID.isna().sum()),
       'nonnegative_cancellation_rows':int((c.Quantity>=0).sum())}
    for customer,invoice in [(16446,'581483'),(12346,'541431')]:
        assert not ((net.CustomerID==customer)&(net.Invoice==invoice)).any()
    R['cleaning']={'purchase_invoices':p.Invoice.nunique(),'net_invoices':net.Invoice.nunique(),
                   'description_nulls_retained':int(net.Description.isna().sum()),'price_matching':'Customer and product only; reverse at purchase price, not cancellation price.'}
    net.to_parquet(ROOT/'data/net_purchases.parquet',index=False)
    p.to_parquet(ROOT/'data/gross_purchases.parquet',index=False)
    c.to_parquet(ROOT/'data/cancellations.parquet',index=False)
    pd.DataFrame(R['audit']).to_csv(ROOT/'outputs/docs/cleaning_audit.csv',index=False)
    save_results(R)
    print(R['netting'],flush=True)
    finish('Cleaning and netting','Fixed regression passed. Both specified extreme purchases fully reversed; native JSON and audit saved. Strict earlier-time LIFO matching verified; missing-ID cancellations cannot be linked. Figures and downstream modelling remain unverified.')

if __name__=='__main__':
    main()
