"""Full metric comparison, deterministic cluster IDs and a reloadable raw-input pipeline."""
from itertools import combinations
import json
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, adjusted_rand_score
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits
from common import ROOT, SEED, ALL_FEATURES, start, load_results, save_results, figure, finish

def build_pipeline(k):
    return Pipeline([('log',FunctionTransformer(np.log1p,feature_names_out='one-to-one')),
                     ('scale',StandardScaler()),('kmeans',KMeans(n_clusters=k,n_init=10,random_state=SEED))])

def main():
    start()
    R=load_results()
    f=pd.read_parquet(ROOT/'data/customer_features.parquet')
    train=f.loc[~f.Outlier]
    rows=[]
    with threadpool_limits(limits=1):
        for feature_set in ['rfm','extended']:
            cols=R['features'][feature_set]
            z=StandardScaler().fit_transform(np.log1p(train[cols]))
            for k in range(2,11):
                km=KMeans(n_clusters=k,n_init=10,random_state=SEED).fit(z)
                labels=[KMeans(n_clusters=k,n_init=10,random_state=s).fit_predict(z) for s in range(10)]
                row=dict(feature_set=feature_set,k=k,inertia=km.inertia_,silhouette=silhouette_score(z,km.labels_),
                         davies_bouldin=davies_bouldin_score(z,km.labels_),
                         stability_ARI=np.mean([adjusted_rand_score(a,b) for a,b in combinations(labels,2)]))
                rows.append(row)
                print(row,flush=True)
        table=pd.DataFrame(rows)
        table.to_csv(ROOT/'data/k_selection.csv',index=False)
        table.to_csv(ROOT/'outputs/docs/k_selection.csv',index=False)
        best=table.sort_values(['silhouette','stability_ARI','davies_bouldin','k'],ascending=[False,False,True,True]).iloc[0]
        cols=R['features'][best.feature_set]
        pipeline=build_pipeline(int(best.k)).fit(train[cols])
        raw_labels=pipeline.predict(train[cols])
        ordered=train.assign(cluster=raw_labels).groupby('cluster').Monetary.mean().sort_values(ascending=False).index.to_numpy()
        km=pipeline.named_steps['kmeans']
        km.cluster_centers_=km.cluster_centers_[ordered]
        remap={old:new for new,old in enumerate(ordered)}
        km.labels_=np.array([remap[v] for v in km.labels_])
        labels=pipeline.predict(train[cols])
    f['Segment']='Outlier-Wholesale'
    f.loc[train.index,'Segment']=labels.astype(str)
    R['model']={'features':cols,'feature_set':best.feature_set,'k':int(best.k),
       'silhouette':best.silhouette,'davies_bouldin':best.davies_bouldin,'inertia':float(best['inertia']),
       'stability_ARI':best.stability_ARI,'stability_seeds':10,'stability_pairs':len(list(combinations(range(10),2))),
       'selection_table':rows,'seed':SEED,'n_init':10,
       'selection_rule':'Choose the highest full-sample silhouette across feature sets and candidate k; exact ties use higher stability, lower Davies-Bouldin and lower k. Stability varies initialisation, not customers or time.',
       'id_rule':'Pipeline cluster centres reordered by mean raw net Monetary, descending.'}
    joblib.dump(pipeline,ROOT/'outputs/model/customer_segmentation.joblib')
    (ROOT/'outputs/model/feature_columns.json').write_text(json.dumps(cols),encoding='utf-8')
    reloaded=joblib.load(ROOT/'outputs/model/customer_segmentation.joblib')
    assert np.array_equal(reloaded.predict(train[cols]),labels)
    example={col:float(round(train[col].median())) for col in ALL_FEATURES}
    example['AOV']=example['Monetary']/example['Frequency']
    X=pd.DataFrame([example])[cols]
    predicted=str(int(reloaded.predict(X)[0]))
    R['model_test']={'inputs':example,'feature_columns':cols,'label':predicted,
                     'origin':'Synthetic combination of rounded non-outlier marginal medians; AOV recomputed exactly as Monetary/Frequency.'}
    segments={}
    for segment,g in f.groupby('Segment'):
        d={'size':len(g),'customer_share':len(g)/len(f),'revenue':g.Monetary.sum(),'revenue_share':g.Monetary.sum()/f.Monetary.sum()}
        for col in ALL_FEATURES:
            d[col.lower()+'_mean']=g[col].mean()
            d[col.lower()+'_median']=g[col].median()
        segments[str(segment)]=d
    R['segments']=segments
    f.to_parquet(ROOT/'data/customer_segments.parquet')
    pd.DataFrame(segments).T.to_csv(ROOT/'outputs/docs/segment_profiles.csv')
    fig,axes=plt.subplots(1,3,figsize=(14,5.5))
    for name,g in table.groupby('feature_set'):
        for ax,metric,label in zip(axes,['inertia','silhouette','davies_bouldin'],['Inertia (scaled squared distance)','Silhouette (higher is better)','Davies-Bouldin (lower is better)']):
            ax.plot(g.k,g[metric],marker='o',label=name)
            ax.set(xlabel='Number of clusters',ylabel=label)
            ax.legend()
    fig.suptitle('Figure 6. Feature-set and cluster-count comparison',fontweight='bold')
    figure(R,fig,'fig6_selection',f"Selected {best.feature_set}, k={int(best.k)} by highest silhouette {best.silhouette:.3f}; Davies-Bouldin {best.davies_bouldin:.3f}; mean pairwise seed ARI {best.stability_ARI:.3f}. Metrics describe this sample; they do not prove future usefulness.")
    transformed=pipeline[:-1].transform(train[cols])
    pca=PCA(n_components=2).fit(transformed)
    points=pca.transform(transformed)
    R['model']['pca_variance']=pca.explained_variance_ratio_
    fig,ax=plt.subplots(figsize=(10,7))
    for label in sorted(set(labels)):
        subset=points[labels==label]
        ax.scatter(subset[:,0],subset[:,1],s=8,alpha=.45,label=f'Segment {label}')
    ax.legend()
    ax.set(title='Figure 7. PCA view of fitted customers',xlabel=f"Principal component 1 ({pca.explained_variance_ratio_[0]:.1%} variance)",ylabel=f"Principal component 2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
    figure(R,fig,'fig7_pca',f"PCA displays {pca.explained_variance_ratio_.sum():.1%} of transformed feature variance. Colours are pipeline predictions. Projection overlap is not a separate clustering evaluation; outliers were excluded from fitting.")
    means=f.groupby('Segment')[ALL_FEATURES].mean()
    z=(means-f[ALL_FEATURES].mean())/f[ALL_FEATURES].std(ddof=0)
    fig,ax=plt.subplots(figsize=(12,6))
    sns.heatmap(z,annot=True,fmt='.2f',cmap='BrBG',center=0,ax=ax,cbar_kws={'label':'Mean difference / all-customer standard deviation'})
    ax.set_title('Figure 8. Segment means relative to all customers')
    figure(R,fig,'fig8_profiles',f"Profiles cover {len(f):,} customers and {len(segments)} groups including Outlier-Wholesale. Cells standardise raw segment means using the all-customer mean and standard deviation; the outlier label does not establish a wholesale business model.")
    save_results(R)
    print(pd.DataFrame(segments).T.to_string(),flush=True)
    finish('Modelling','Full feature/k grid and pairwise seed stability computed. Pipeline predicts deterministic IDs; save/reload predictions match exactly; synthetic internally consistent test scored. Profiles include separate high-value outliers. Interpretation and naming pending.')

if __name__=='__main__':
    main()
