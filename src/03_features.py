"""Customer aggregates, transformation diagnostics and a log-IQR outlier fence."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MaxNLocator, EngFormatter
from common import ROOT, ALL_FEATURES, RFM, start, read_net, load_results, save_results, figure, finish

def main():
    start()
    R=load_results()
    p=read_net()
    c=pd.read_parquet(ROOT/'data/cancellations.parquet')
    g=pd.read_parquet(ROOT/'data/gross_purchases.parquet')
    snapshot=pd.Timestamp(R['source']['end'])+pd.Timedelta(days=1)
    f=p.groupby('CustomerID').agg(last=('InvoiceDate','max'),Frequency=('Invoice','nunique'),Monetary=('Revenue','sum'),Variety=('StockCode','nunique'))
    f['Recency']=(snapshot-f['last']).dt.days
    f['AOV']=f.Monetary/f.Frequency
    cancellations=c.loc[c.CustomerID.notna()].groupby('CustomerID').Invoice.nunique().reindex(f.index,fill_value=0)
    purchases=g.groupby('CustomerID').Invoice.nunique().reindex(f.index,fill_value=0)
    f['CancellationRate']=cancellations/(cancellations+purchases)
    f=f[ALL_FEATURES]
    logm=np.log1p(f.Monetary)
    q1,q3=logm.quantile([.25,.75])
    fence=q3+1.5*(q3-q1)
    f['Outlier']=logm>fence
    skew={col:{'before':f[col].skew(),'after':np.log1p(f[col]).skew()} for col in ALL_FEATURES}
    R['features']={'all':ALL_FEATURES,'rfm':RFM,'extended':RFM+ALL_FEATURES[4:5],
       'snapshot':snapshot,'skew':skew,'cancellation_zero_share':f.CancellationRate.eq(0).mean(),
       'cancellation_decision':'Retained for profiling, excluded from clustering: zero inflation and limited log-transform change. AOV also profiles only: it is exactly Monetary divided by Frequency.',
       'customer_count':len(f),'correlation':f[ALL_FEATURES].corr().to_dict()}
    R['outliers']={'rule':'Upper Tukey fence on log1p net customer Monetary; descriptive high-value group, not confirmed wholesale.',
       'q1_log':q1,'q3_log':q3,'iqr_multiplier':1.5,'fence_log':fence,'threshold_GBP':np.expm1(fence),
       'customers':int(f.Outlier.sum()),'revenue':f.loc[f.Outlier,'Monetary'].sum(),
       'revenue_share':f.loc[f.Outlier,'Monetary'].sum()/f.Monetary.sum()}
    f.to_parquet(ROOT/'data/customer_features.parquet')
    f[ALL_FEATURES].corr().to_csv(ROOT/'data/feature_correlations.csv')
    fig,ax=plt.subplots(figsize=(9,7))
    sns.heatmap(f[ALL_FEATURES].corr(),annot=True,fmt='.2f',vmin=-1,vmax=1,cmap='BrBG',ax=ax)
    ax.set_title('Customer feature Pearson correlations (raw scale)')
    figure(R,fig,'feature_correlations',f"AOV = Monetary / Frequency. Monetary-Frequency correlation: {f.Monetary.corr(f.Frequency):.3f}. Correlation is descriptive and does not establish causality.")
    # Plot every possible model input, plus the excluded profiling features for transparency.
    fig,axes=plt.subplots(len(ALL_FEATURES),2,figsize=(10,13))
    for row,col in enumerate(ALL_FEATURES):
        for j,arr in enumerate([f[col],np.log1p(f[col])]):
            axes[row,j].hist(arr,bins='fd',color='#236b8e')
            unit={'Recency':'days','Frequency':'invoices','Monetary':'GBP','AOV':'GBP/order','Variety':'products','CancellationRate':'invoice ratio'}[col]
            axes[row,j].set(xlabel=col+(' (log1p)' if j else f' ({unit}, raw)'),ylabel='Customers',title=f"Skew {skew[col]['after' if j else 'before']:.2f}")
            axes[row,j].xaxis.set_major_locator(MaxNLocator(nbins=4))
            if not j and col in ['Monetary','AOV']:
                axes[row,j].xaxis.set_major_formatter(EngFormatter(places=0,sep=''))
    fig.suptitle('Figure 5. Raw and log-transformed customer features',fontweight='bold')
    improved=[col for col in ALL_FEATURES if abs(skew[col]['after'])<abs(skew[col]['before'])]
    R['features']['skew_improved']=improved
    caption=f"Absolute skew decreases for {', '.join(improved)}. CancellationRate is zero for {R['features']['cancellation_zero_share']:.1%} of customers; skew {skew['CancellationRate']['before']:.2f} to {skew['CancellationRate']['after']:.2f}. Histograms include outliers; model fitting excludes the upper log-Monetary fence."
    figure(R,fig,'fig5_transformations',caption)
    save_results(R)
    print(R['outliers'],R['features']['cancellation_decision'],flush=True)
    finish('Features and outliers','Net customer aggregates, correlations and all transformation histograms saved; AOV identity verified by construction. Data-derived log-IQR upper fence printed. Outlier-Wholesale is a required label, not an observed buyer classification. Model selection remains unverified.')

if __name__=='__main__':
    main()
