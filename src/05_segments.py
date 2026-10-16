"""Name and act only after inspecting computed segment profiles."""
import json
import pandas as pd
from common import ROOT, start, load_results, save_results, finish

def validate_name(name,tags):
    low=name.lower()
    if any(t in low for t in ['lapsed','dormant','at-risk']):
        assert tags['recency']=='high', (name,tags)
    if any(t in low for t in ['loyal','champion']):
        assert tags['recency']=='low' and tags['frequency']=='high', (name,tags)
    if 'low-spend' in low:
        assert tags['monetary']=='low',(name,tags)

def main():
    start()
    R=load_results()
    f=pd.read_parquet(ROOT/'data/customer_segments.parquet')
    boundaries={col.lower():f[col].quantile([1/3,2/3]).tolist() for col in ['Recency','Frequency','Monetary']}
    R['tag_boundaries']=boundaries
    names={}
    for key,s in R['segments'].items():
        tags={col:('low' if s[col+'_median']<=q[0] else 'high' if s[col+'_median']>q[1] else 'middle') for col,q in boundaries.items()}
        if key=='Outlier-Wholesale':
            name='Outlier-Wholesale'
            action='Review major accounts individually, confirm buyer needs and set stock reservations against their observed repeat orders.'
        elif tags['recency']=='low' and tags['frequency']=='high':
            name='Loyal champions'
            action='Offer early access to relevant products and test a replenishment reminder against a holdout group.'
        elif tags['recency']=='high' and tags['frequency']=='high':
            name='Lapsed repeat buyers'
            action='Run a personalised re-engagement test using previously purchased categories and retain an untreated comparison group.'
        elif tags['recency']=='high':
            name='Dormant occasional buyers'
            action='Test a low-cost reminder using their last product category before committing a wider recovery budget.'
        elif tags['monetary']=='low':
            name='Low-spend explorers'
            action='Test a relevant complementary-product recommendation after the next purchase and monitor incremental basket value.'
        else:
            name='Developing repeat buyers'
            action='Test a next-order recommendation based on prior product variety and measure repeat purchase against a holdout.'
        if name in [n['name'] for n in names.values()]:
            name+=f' group {key}'
        validate_name(name,tags)
        s.update(tags=tags,name=name,action=action)
        names[key]={'name':name,'action':action,'tags':tags}
    R['model_test']['segment_name']=names[R['model_test']['label']]['name']
    R['limitations']={'missing_id':R['missing_id'],'unmatched_unit_share':R['netting']['unmatched_unit_share'],
       'facts':['No browsing events, marketing spend, margins, acquisition dates or return reasons supplied.',
                'Observed cancellations are invoice events, not a complete physical-return rate.',
                'Single UK retailer; historical window and incomplete final month limit generalisation.',
                'Customer/product LIFO is an allocation assumption, not an invoice-linked return record; prices may differ.',
                'Net sales retrospectively attribute matched returns to original purchase months; unmatched returns are not deducted from unrelated sales.',
                'K-Means assumes Euclidean compact groups after transformation; clusters may overlap and are descriptive.',
                'RFM is backward-looking; correlations and segment associations are not causal effects.',
                'Outlier-Wholesale is a requested operational label; buyer type is not observed.',
                'Initialisation stability is not temporal or resampling stability; there is no predictive holdout target.',
                'Actions are hypotheses for controlled tests; no uplift or profit claims are made.']}
    (ROOT/'outputs/model/segment_names.json').write_text(json.dumps(names,indent=2),encoding='utf-8')
    save_results(R)
    pd.DataFrame(R['segments']).T.to_csv(ROOT/'outputs/docs/segment_profiles.csv')
    print(json.dumps(names,indent=2),flush=True)
    finish('Segment interpretation','Names validated against all-customer median tercile tags; distinct actions and limitations saved. Synthetic predicted name resolved from stable label. No marketing uplift or buyer type inferred.')

if __name__=='__main__':
    main()
