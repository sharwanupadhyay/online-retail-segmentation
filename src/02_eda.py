"""Descriptive findings with independently ranked products and common date axes."""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator, EngFormatter
from common import ROOT, start, read_net, load_results, save_results, figure, finish

def partial(ax, date):
    ax.axvspan(date,date+pd.offsets.MonthBegin(1),color='#d17a22',alpha=.18)
    ax.text(.98,.93,'Partial final month',transform=ax.transAxes,ha='right',fontsize=9,color='#8a4800')

def main():
    start()
    R=load_results()
    p=read_net()
    p['Month']=p.InvoiceDate.dt.to_period('M').dt.to_timestamp()
    monthly=p.groupby('Month').Revenue.sum().sort_index()
    last=p.InvoiceDate.max().to_period('M').to_timestamp()
    complete=monthly.loc[monthly.index!=last]
    q4=complete.index.quarter==4
    peaks=monthly.nlargest(3)
    season={'peak_months':{x.strftime('%B %Y'):v for x,v in peaks.items()},
            'q4_mean':complete.loc[q4].mean(),'rest_mean':complete.loc[~q4].mean(),
            'q4_rest_ratio':complete.loc[q4].mean()/complete.loc[~q4].mean(),
            'partial_month':last.strftime('%B %Y'),'last_date':p.InvoiceDate.max().strftime('%d %B %Y')}
    R['seasonal']=season
    R['monthly_revenue']={d.strftime('%Y-%m'):v for d,v in monthly.items()}
    fig,ax=plt.subplots(figsize=(11,5.5))
    ax.plot(monthly.index,monthly.values,color='#236b8e',marker='o')
    ax.set(title='Figure 1. Monthly net merchandise revenue',xlabel='Invoice month',ylabel='Net revenue (GBP)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.tick_params(axis='x',rotation=40)
    partial(ax,last)
    caption=f"Peak months: {', '.join(f'{k} (GBP {v:,.0f})' for k,v in season['peak_months'].items())}. Complete-month Q4/rest mean revenue ratio: {season['q4_rest_ratio']:.2f}. {season['partial_month']} ends {season['last_date']}. Reversals are attributed to the original sale month."
    figure(R,fig,'fig1_monthly_revenue',caption)
    product=p.groupby('StockCode').agg(revenue=('Revenue','sum'),units=('Quantity','sum'),customers=('CustomerID','nunique'),orders=('Invoice','nunique'),description=('Description','first'))
    product['value_per_order']=product.revenue/product.orders
    counts=p.groupby(['StockCode','CustomerID']).Invoice.nunique()
    product['repeat_customers']=counts.gt(1).groupby(level=0).sum()
    product['repeat_customer_share']=product.repeat_customers/product.customers
    product=product.reset_index()
    product.to_csv(ROOT/'data/product_summary.csv',index=False)
    product.to_csv(ROOT/'outputs/docs/product_summary.csv',index=False)
    leaders={metric:product.loc[product[metric].idxmax()].to_dict() for metric in ['revenue','units','customers']}
    R['products']={'leaders':leaders,'same_leader':len({v['StockCode'] for v in leaders.values()})==1}
    fig,axes=plt.subplots(1,3,figsize=(14,12))
    for ax,metric,label in zip(axes,['revenue','units','customers'],['Net revenue (GBP)','Net units','Distinct customers']):
        top=product.nlargest(10,metric).sort_values(metric)
        labels=[f"{r.StockCode}\n{str(r.description)[:12]}\n{r.customers:,} customers" for r in top.itertuples()]
        ax.barh(labels,top[metric],color='#236b8e')
        ax.set(xlabel=label,title=label)
        ax.tick_params(axis='y',labelsize=14)
        ax.tick_params(axis='x',labelsize=12)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
        ax.xaxis.set_major_formatter(EngFormatter(places=0,sep=''))
    fig.suptitle('Figure 2. Products ranked separately by each measure',fontweight='bold')
    caption='; '.join(f"{m} leader: {v['description']} ({v['StockCode']}), {v[m]:,.0f} {'GBP' if m=='revenue' else m}" for m,v in leaders.items())+('. The leaders differ.' if not R['products']['same_leader'] else '. One product leads all measures.')+' Each row shows its customer count; full names are in product_summary.csv.'
    figure(R,fig,'fig2_products',caption)
    country=p.groupby('Country').agg(revenue=('Revenue','sum'),customers=('CustomerID','nunique'),orders=('Invoice','nunique'),units=('Quantity','sum'))
    country['AOV']=country.revenue/country.orders
    country['revenue_per_customer']=country.revenue/country.customers
    country['units_per_order']=country.units/country.orders
    country['orders_per_customer']=country.orders/country.customers
    country.to_csv(ROOT/'data/country_summary.csv')
    country.to_csv(ROOT/'outputs/docs/country_summary.csv')
    exports=country.drop(index='United Kingdom').nlargest(10,'revenue')
    lead=exports.iloc[0]
    high=exports.AOV.idxmax()
    R['countries']={'all':country.reset_index().to_dict('records'),'top_exports':exports.reset_index().to_dict('records'),
       'leader':exports.index[0],'leader_revenue':lead.revenue,'leader_customers':lead.customers,
       'leader_AOV':lead.AOV,'leader_units_per_order':lead.units_per_order,'highest_AOV':high,
       'highest_AOV_value':country.loc[high,'AOV'],'highest_AOV_customers':country.loc[high,'customers'],
       'highest_AOV_units_per_order':country.loc[high,'units_per_order'],'UK_AOV':country.loc['United Kingdom','AOV'],
       'UK_units_per_order':country.loc['United Kingdom','units_per_order']}
    fig,axes=plt.subplots(2,2,figsize=(12,10))
    for ax,metric,label in zip(axes.flat,['revenue','customers','AOV','revenue_per_customer'],['Net revenue (GBP)','Distinct customers','Net average order value (GBP/order)','Net revenue per customer (GBP/customer)']):
        ax.barh(exports.index[::-1],exports[metric].values[::-1],color='#236b8e')
        ax.set(xlabel=label)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
        ax.xaxis.set_major_formatter(EngFormatter(places=0,sep=''))
    fig.suptitle('Figure 3. Highest-revenue export countries (United Kingdom excluded)',fontweight='bold')
    co=R['countries']
    caption=f"{co['leader']} leads exports: GBP {co['leader_revenue']:,.0f}, {co['leader_customers']:,.0f} customers. {high} has the largest AOV in this group: GBP {co['highest_AOV_value']:,.2f}, {co['highest_AOV_units_per_order']:,.1f} units/order, {co['highest_AOV_customers']:,.0f} customers; UK: GBP {co['UK_AOV']:,.2f}, {co['UK_units_per_order']:,.1f} units/order. Basket size and customer-base size are descriptive, not proof of buyer type."
    figure(R,fig,'fig3_countries',caption)
    c=pd.read_parquet(ROOT/'data/cancellations.parquet')
    gross=pd.read_parquet(ROOT/'data/gross_purchases.parquet')
    def invoice_month(df):
        return df.assign(Month=df.InvoiceDate.dt.to_period('M').dt.to_timestamp()).groupby('Month').Invoice.nunique()
    m=pd.concat([invoice_month(c.loc[c.CustomerID.notna()]).rename('cancelled'),invoice_month(gross).rename('purchase')],axis=1).fillna(0)
    m['rate']=m.cancelled/(m.cancelled+m.purchase)
    mc=m.loc[m.index!=last]
    cq=mc.index.quarter==4
    R['cancellations_monthly']={'rows':m.reset_index().to_dict('records'),'q4_mean':mc.loc[cq,'rate'].mean(),
       'rest_mean':mc.loc[~cq,'rate'].mean(),'definition':'Distinct identified-customer cancellation invoices divided by distinct identified-customer cancellation plus valid identified-customer gross purchase invoices; merchandise codes only. Same invoice ratio as the customer profiling feature.'}
    fig,ax=plt.subplots(figsize=(11,5.5))
    ax.bar(m.index,m.cancelled,width=20,color='#236b8e',label='Cancelled invoices')
    line=ax.twinx()
    line.plot(m.index,m.rate*100,color='#c66b26',marker='o',label='Cancellation invoice rate')
    ax.set(title='Figure 4. Cancellation invoices and invoice rate',xlabel='Invoice month',ylabel='Cancelled invoices (count)')
    line.set_ylabel('Cancelled / (cancelled + purchase invoices) (%)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.tick_params(axis='x',rotation=40)
    partial(ax,last)
    cr=R['cancellations_monthly']
    caption=f"Complete-month mean invoice cancellation rate: Q4 {cr['q4_mean']:.2%}; non-Q4 {cr['rest_mean']:.2%}. "
    caption+=('No descriptive Q4 elevation is observed. ' if cr['q4_mean']<=cr['rest_mean'] else 'Q4 is descriptively higher; this is not a significance or causal test. ')
    caption+='Both invoice counts use identified customers and merchandise codes; gross purchase invoices precede netting. Final month is partial.'
    figure(R,fig,'fig4_cancellations',caption)
    save_results(R)
    print(season,{k:v for k,v in co.items() if k not in ['all','top_exports']},flush=True)
    finish('Exploratory analysis','Figures saved with computed captions; finite axis limits and annotation locations checked. Product rankings computed separately; UK excluded by name. Final month omitted from seasonal mean comparisons. Visual inspection pending.')

if __name__=='__main__':
    main()
