"""Human-readable deliverables templated exclusively from the results ledger."""
import json
from common import words

def video_script(R):
    n=R['netting']; m=R['model']; miss=R['missing_id']; co=R['countries']; p=R['products']['leaders']; season=R['seasonal']; test=R['model_test']; x=test['inputs']
    paragraphs=[
      f"We selected the problem of identifying patterns in global e-commerce sales. Our aim is to turn transaction records into useful customer actions. We use the supplied Online Retail II workbook, containing {R['source']['rows']:,} rows from {R['source']['start'][:4]} to {R['source']['end'][:4]}. In this demonstration, we explain how we cleaned the records, what we learned about sales, how we grouped customers, and how the saved model handles a new example. We focus on evidence that could guide a practical business test. Our central question is which different actions are supported by different purchasing histories. We keep the assumptions visible so a reviewer can trace each conclusion back to the transactions.",
      f"We removed {R['regression']['duplicates']:,} exact duplicates, then excluded {R['regression']['nonproduct']:,} original non-product rows and {R['nonproduct']['extra_rows']:,} additional fee, sample and voucher rows. Missing customer IDs excluded {miss['rows']:,} otherwise valid purchase rows worth {miss['revenue']:,.2f} pounds. We did not guess those identities. We matched cancellations only to earlier purchases by the same customer for the same product, starting with the most recent purchase. Of the retained cancellation rows, {n['matched']:,} were fully matched, {n['partly_matched']:,} partly matched, and {n['unmatched']:,} unmatched. Reversals reduced identified merchandise value by {n['reversed_revenue']:,.2f} pounds, leaving {n['net_revenue']:,.2f} pounds. Unmatched cancelled units remain separately reported.",
      f"Our exploratory findings show why definitions matter. Complete fourth-quarter months averaged {season['q4_rest_ratio']:.2f} times the revenue of other months. We marked the incomplete final month instead of treating it as a complete sales decline. {p['revenue']['description'].title()} led product revenue at {p['revenue']['revenue']:,.0f} pounds. {p['units']['description'].title()} led units with {p['units']['units']:,.0f}, while {p['customers']['description'].title()} reached {p['customers']['customers']:,} customers. {co['leader']} led export revenue from only {co['leader_customers']:,.0f} customers. {co['highest_AOV']} averaged {co['highest_AOV_value']:,.2f} pounds per order. Large baskets and small customer bases deserve investigation, but do not prove buyer type.",
      f"Our clustering inputs are {', '.join(m['features'])}. These measure days since a purchase, distinct purchase invoices, and net spending. We use K-Means to group similar purchasing histories. We also profile AOV, meaning average order value, Variety, meaning product breadth, and CancellationRate, meaning the proportion of invoices that are cancellations. A logarithm reduces scale differences before standardisation. We compare basic and extended features across candidate cluster counts and check agreement across {m['stability_seeds']} starting seeds. We select the model using the same evaluation rule for every feature set and candidate. Highest silhouette selected {m['k']} clusters. The silhouette is {m['silhouette']:.3f}; the groups overlap, and their business usefulness still needs testing. We retain exceptional spenders separately using a fence calculated from the spending distribution.",
      ' '.join(f"{s['name']} has {s['size']:,} customers and {100*s['revenue_share']:.2f} percent of net revenue. {s['action']}" for s in R['segments'].values())+' These actions differ because the profiles differ. The outlier group label does not establish that the buyers are wholesalers. Each proposed action still needs a controlled business test before wider use.',
      f"We reload the saved pipeline to test a made-up customer. The inputs are {x['Recency']:,.0f} days of recency, {x['Frequency']:,.0f} purchase invoices, and {x['Monetary']:,.0f} pounds of net spending. Average order value is consistently {x['AOV']:,.0f} pounds. Product variety is {x['Variety']:,.0f}, and the cancellation ratio is {x['CancellationRate']:.0f}. The pipeline uses its saved feature order and predicts {test['segment_name']}. This demonstrates that the saved artifact works; it does not measure future prediction accuracy.",
      f"Our limitations shape our recommendation. Missing identities exclude {100*miss['purchase_revenue_share']:.2f} percent of valid gross purchase value, while {100*n['unmatched_unit_share']:.2f} percent of cancelled units cannot be linked. We have no browsing behaviour, marketing spend, margins or return reasons. This is a single historical retailer, and the groups describe past purchasing rather than causes. We recommend focused retention tests and individual review of major accounts, alongside better identity and return records. We would compare treated customers with an untreated group and measure net purchasing after costs. We used AI to assist coding, drafting and checks, with numerical claims verified by execution."
    ]
    script='\n\n'.join(paragraphs)+'\n'
    print('Spoken script word count:',words(script),flush=True)
    assert 650<=words(script)<=720,words(script)
    return script

def source_documentation(R):
    n=R['netting']; miss=R['missing_id']
    lines=['# Dataset source documentation','',
      f"Source identified in the supplied brief: [Online Retail II]({R['source']['url']}). Analysis used only the user-supplied workbook and brief. Local access date: {R['source']['access_date']}; this is not a claimed download date from UCI.",
      f"The source sheets contain {R['source']['rows']:,} rows across {R['source']['columns']} fields. Observation window: {R['source']['start']} through {R['source']['end']}. Sheet overlap: {R['source']['overlap_start']} through {R['source']['overlap_end']}.",'',
      '## Schema and missingness','']
    for name,s in R['sheets'].items():
        lines.append(f"{name}: {s['shape'][0]:,} rows, {s['shape'][1]} columns. Fields, source dtypes and missing counts:")
        lines+=['','| Field | Dtype | Missing |','| --- | --- | ---: |']
        lines += [f"| {col} | {dtype} | {s['nulls'][col]:,} |" for col,dtype in s['dtypes'].items()]
        lines.append('')
    lines+=['## Sequential preprocessing audit','','| Before | Removed | After | Treatment |','| ---: | ---: | ---: | --- |']
    lines += [f"| {a['before']:,} | {a['removed']:,} | {a['after']:,} | {a['reason']} |" for a in R['audit']]
    lines+=['',f"Original-list regression passed: {json.dumps(R['regression'])}. The original list was used unchanged before inspecting extended exclusions.",
      f"Extended exclusions: {', '.join(R['nonproduct']['extra'])}. Extra rows removed: {R['nonproduct']['extra_rows']:,}. Evidence and retained irregular catalog codes are in non_product_evidence.csv. Descriptions are not imputed; retained missing descriptions: {R['cleaning']['description_nulls_retained']:,}.",
      f"Missing-ID coverage loss: {miss['rows']:,} valid purchase rows ({miss['purchase_rows_share']:.2%}), GBP {miss['revenue']:,.2f} ({miss['purchase_revenue_share']:.2%} of valid gross purchase value).",
      f"Cancellations: {n['matched']:,} matched / {n['partly_matched']:,} partly matched / {n['unmatched']:,} unmatched, out of {n['cancellation_rows']:,} retained rows. Cancelled units {n['cancelled_units']:,.0f}; reversed {n['reversed_units']:,.0f}; unmatched {n['unmatched_units']:,.0f} ({n['unmatched_unit_share']:.2%}). Matching runtime {n['runtime_seconds']:.2f} seconds. Missing-ID cancellation rows: {n['cancellation_missing_id_rows']:,}. Nonnegative cancellation rows: {n['nonnegative_cancellation_rows']:,}.",
      f"Gross identified purchase value GBP {n['gross_revenue']:,.2f}; reversal GBP {n['reversed_revenue']:,.2f}; net GBP {n['net_revenue']:,.2f}. Fully reversed lines dropped: {n['lines_dropped']:,}; partly reversed lines retained: {n['lines_partly_reversed']:,}. Remaining lines: {n['net_lines']:,}; customers with positive net purchases: {n['customers']:,}.",
      'Matching key is customer plus stock code. Only strictly earlier purchases qualify, most recent first. Purchase prices determine the net revenue reduction. No price equality is required. The lack of explicit invoice return links makes this an allocation assumption. Unmatched returns are preserved and do not create negative customer spending. Netting is retrospective to the original purchase month.',
      '', '## Feature and modelling definitions','',
      f"Snapshot: {R['features']['snapshot']}. All customer features: {', '.join(R['features']['all'])}. Fitted feature order: {', '.join(R['model']['features'])}. Recency uses whole days since the last retained purchase; Frequency counts retained invoices; Monetary sums retained value; AOV = Monetary / Frequency; Variety counts retained products. {R['cancellations_monthly']['definition']}",
      f"Outlier rule: {R['outliers']['rule']} Upper fence GBP {R['outliers']['threshold_GBP']:,.2f}, derived from log quartiles {R['outliers']['q1_log']:.3f} and {R['outliers']['q3_log']:.3f} using multiplier {R['outliers']['iqr_multiplier']:.1f}. The separate group has {R['outliers']['customers']:,} customers and {R['outliers']['revenue_share']:.2%} of net value.",
      f"Selected model: {R['model']['feature_set']}, k={R['model']['k']}; silhouette {R['model']['silhouette']:.3f}, Davies-Bouldin {R['model']['davies_bouldin']:.3f}, seed ARI {R['model']['stability_ARI']:.3f}. Selection: {R['model']['selection_rule']}",
      '', '## What the data cannot tell us','']
    lines.extend('- '+fact for fact in R['limitations']['facts'])
    lines+=['','## Citation and access caveat','',
      f"The requested donation year is {R['references']['uci_year']}. The exact UCI author and DOI have not been checked online because the request limits factual sources to the supplied files. Verify the exact citation on the linked UCI page before submission. Software versions are recorded in results.json and pinned in requirements.txt."]
    return '\n'.join(lines)+'\n'

def readme(R):
    m=R['model']; n=R['netting']
    code="""import json
import joblib
import pandas as pd

R = json.load(open('outputs/results.json', encoding='utf-8'))
model = joblib.load('outputs/model/customer_segmentation.joblib')
columns = R['model']['features']
raw = R['model_test']['inputs'].copy()
assert raw['AOV'] == raw['Monetary'] / raw['Frequency']
if raw['Monetary'] > R['outliers']['threshold_GBP']:
    name = 'Outlier-Wholesale'
else:
    label = str(int(model.predict(pd.DataFrame([raw])[columns])[0]))
    name = R['segments'][label]['name']
print(columns, name)
"""

    return f"""# Identifying Patterns in Global E-Commerce Sales

Assignment Option C: reproducible transaction cleaning, chronological cancellation netting, descriptive analysis and customer segmentation. The supplied workbook and assignment brief are the only empirical sources. This is an analytical segmentation, with no forecast or supervised prediction target.

## Setup and data

Put the supplied workbook at `inputs/online_retail_II.xlsx` and the supplied brief at `inputs/Data Science Group Assignment.pdf`. The workbook is excluded from Git. To obtain the data separately, use the [UCI dataset page]({R['source']['url']}) and place its workbook at that input path; this project used the user's local copy accessed on {R['source']['access_date']}. Verify source licensing and the exact citation before redistributing the data.

Create a virtual environment with `python -m venv .venv`, activate it, and run `python -m pip install -r requirements.txt`. Use a compatible Python environment; the pinned package versions are the versions actually executed in this project. Install Poppler and place `pdftoppm` on PATH if it is not already available. The script also detects the bundled local Poppler runtime.

Run `python run_all.py --clean` from the repository root. This archives earlier generated data and outputs under `work/rebuild_backups/` and rebuilds from both source inputs. It does not overwrite the original Downloads files. All analytical stages, notebook execution, PDF rendering, artifact validation and pytest are run. Each stage records progress and makes a local Git commit, so run inside an initialised repository with Git installed and a writable Git directory. The commit identity is a local automation identity, not a claim about group authorship.

For a later validation without rebuilding, run `python src/08_verify.py` and `python -m pytest -q`. Open `outputs/notebook/retail_segmentation.ipynb` to inspect the already executed cells and figures. Re-execution recomputes the same workflow and writes its generated artifacts.

## Folder structure

`inputs/`: supplied source files. `src/`: stage implementations and shared helpers. `data/`: generated transactions, customer tables and selection metrics. `docs/`: extracted requirements and checklist. `tests/`: independent matching edge cases and artifact contracts. `outputs/figures/`: labelled figures with computed captions. `outputs/model/`: fitted pipeline, column order and names. `outputs/report/`: PDF and countable report text. `outputs/notebook/`: executed notebook. `outputs/demo/`: spoken script. `outputs/docs/`: cleaning audit, evidence, profiles, source documentation and verification. `outputs/results.json`: common numerical and naming ledger. `PROGRESS.md`: stage history and unresolved human tasks. `requirements.txt`: actual environment versions. `run_all.py`: complete rebuild entry point.

## Results

The fixed original-list regression passes. {R['regression']['duplicates']:,} exact duplicate rows were removed, followed by {R['regression']['nonproduct']:,} original non-product rows and {R['nonproduct']['extra_rows']:,} justified extended exclusions. Missing IDs exclude {R['missing_id']['rows']:,} valid purchase rows worth GBP {R['missing_id']['revenue']:,.2f}. Chronological cancellation matching reports {n['matched']:,} matched, {n['partly_matched']:,} partly matched and {n['unmatched']:,} unmatched cancellation rows. It reduces identified purchase value from GBP {n['gross_revenue']:,.2f} to GBP {n['net_revenue']:,.2f}, leaving {n['net_lines']:,} lines and {n['customers']:,} customers.

The selected {m['feature_set']} model has k={m['k']}, silhouette {m['silhouette']:.3f}, Davies-Bouldin {m['davies_bouldin']:.3f} and mean seed ARI {m['stability_ARI']:.3f}. Exact clustering column order: {', '.join(m['features'])}. It is a coarse descriptive split with overlap. All profiling features: {', '.join(R['features']['all'])}. AOV derives from Monetary/Frequency, and CancellationRate is retained for profiling rather than clustering. The upper log-IQR spending fence is GBP {R['outliers']['threshold_GBP']:,.2f}; the separate Outlier-Wholesale group contributes {R['outliers']['revenue_share']:.2%} of net value. That label is not proof of buyer type.

"""+'\n\n'.join(f"- **{s['name']}**: {s['size']:,} customers, {s['revenue_share']:.2%} of net value. {s['action']}" for s in R['segments'].values())+f"""

## Load and score

Inputs must follow the fitted feature order {', '.join(m['features'])}. The example below reads the saved order and test inputs rather than copying stale values. The separate outlier rule must be applied before the ordinary-customer pipeline. The pipeline expects raw nonnegative customer aggregates with valid positive Frequency; it handles logarithms and scaling internally.

```python
{code}```

The saved test case predicts **{R['model_test']['segment_name']}**. This reload test checks artifact integrity, not predictive generalisation.

## Definitions and limits

Net merchandise value reverses matched units at original purchase prices and assigns them to original sale dates. Cancellations are matched strictly backward in time by customer and product, most recent first; unmatched units remain separate. {R['cancellations_monthly']['definition']} Country AOV uses net value divided by retained distinct invoices. Monthly seasonal comparisons exclude the partial final month. Seed stability measures only initialisation changes. There is no observed uplift, profit, browsing data, marketing spend or return reason. Missing-ID selection, a single retailer and historical coverage constrain conclusions. Segment names and actions are held in `outputs/model/segment_names.json`; stable result keys remain unchanged by display names.

## Before submission

Fill in group names, IDs, course title and submission date. Complete the signed group Ethics and Integrity Declaration and group review. The brief's due date is {R['assignment']['due_date']}, earlier than this local access date; verify submission arrangements with the course. Record the spoken script while demonstrating the notebook and saved-model test, or give the live demo. Push the local repository to a public or shared GitHub repository. Verify the UCI citation/DOI and source access details. Read the report, rerun the notebook and confirm every group member can explain the work. No video has been recorded or uploaded, and no remote repository has been published.
"""


def assumptions_documentation(R):
    return f"""# Assumptions and interpretation boundaries

- Exact duplicate rows are treated as repeated records, including across overlapping source sheets. Legitimate identical lines cannot be distinguished without a line identifier.
- Stock codes and invoice codes are stripped and uppercased. Physical-merchandise analysis excludes the original requested administrative codes plus documented Amazon fee, sample and voucher codes. Irregular syntax alone does not justify exclusion.
- Purchase rows require positive quantity and price. Missing customer IDs are excluded from linked customer analysis rather than imputed. The missingness mechanism is unknown; representativeness is not assumed.
- Monetary value is quantity multiplied by price, expressed in GBP as required by the request. It measures merchandise value and does not establish profit, cash flow, tax treatment or total-company revenue.
- Cancellation allocation uses customer plus stock code and strictly earlier purchases, most recent eligible lines first. Equal-time purchases are ineligible. Prices need not match; reversals use original purchase prices. This is a LIFO allocation assumption, not an observed return-to-invoice link.
- Fully reversed lines are dropped, partial lines retain the remaining quantity, and unmatched cancellation units remain separately reported. Missing-ID cancellations cannot be assigned to customers. Unmatched units account for {R['netting']['unmatched_unit_share']:.2%} of cancelled units.
- Net revenue is retrospective to original sale dates. Customers with no remaining positive purchase lines leave the model population. Frequency and country AOV use retained net purchase invoices; the cancellation-rate denominator instead uses valid gross purchase invoices so fully reversed orders are still counted as purchase events.
- Customer and monthly cancellation rates both count distinct identified-customer cancellation invoices divided by cancellation plus valid identified-customer gross purchase invoices. All retained cancellation events count for identified customers, whether matched or unmatched. This is not a physical-return rate.
- Snapshot date is {R['features']['snapshot']}, the last source invoice timestamp plus a day. Recency uses whole elapsed days. AOV is Monetary divided by Frequency. Variety counts distinct retained stock codes. Customer aggregation spans the full observed window; exposure time is not normalised by acquisition date because acquisition dates are absent.
- Monthly comparisons use arithmetic means of complete monthly values or complete monthly invoice rates. The final partial month is excluded from fourth-quarter versus other-month comparisons. The observed window is not assumed to represent all future seasonal cycles.
- Export charts exclude United Kingdom by name and use the highest net-revenue countries. A country's customer count and retained-order count determine descriptive spending averages; high order value and account concentration do not prove wholesale buyer status or expansion potential.
- The conventional upper Tukey fence uses log-Monetary quartiles and multiplier {R['outliers']['iqr_multiplier']:.1f}, yielding GBP {R['outliers']['threshold_GBP']:,.2f}. It is a standard descriptive convention, not a tuned causal or profit threshold. The requested Outlier-Wholesale label does not assert buyer type.
- Clustering inputs are {', '.join(R['model']['features'])}. All fitted inputs receive log transformation and standardisation before Euclidean K-Means. AOV and CancellationRate remain profiles; the extended candidate adds Variety. These choices determine which behavioural differences are emphasised.
- Highest full-sample silhouette chooses among the evaluated candidate feature sets and cluster counts. Exact ties prefer greater seed stability, then lower Davies-Bouldin and lower k. This is internal selection, not independent validation, predictive accuracy or a global optimum.
- Initialisation stability averages pairwise adjusted Rand agreement across {R['model']['stability_seeds']} seeds. It does not measure temporal or resampling stability. Outliers are excluded from fitting but retained in profiles. Cluster IDs are reordered by descending mean net Monetary, and final ordinary-customer labels come from pipeline predictions.
- Segment names use median Recency, Frequency and Monetary compared with all-customer terciles. Tags are relative descriptions. Membership does not guarantee every individual shares the segment median behaviour.
- The synthetic demonstration combines rounded marginal medians and recalculates AOV exactly. It is not an observed customer, a holdout set or a performance estimate. A scoring wrapper must apply the outlier fence before the ordinary-customer pipeline.
- Business actions are hypotheses for controlled tests. No marketing uplift, revenue scenario, margin or return-reason estimate is invented. Associations do not establish causes.
- Access date {R['source']['access_date']} records local file access. No UCI download or external factual lookup is claimed. The requested UCI donation year is retained, while its exact author and DOI remain provisional. Software references use known project identities and installed versions. Group identities, course title and submission date remain placeholders; ethics signatures, actual collaboration, recording/live delivery and remote repository publication require the group.
"""
