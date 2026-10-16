"""Generate the complete report from computed results, then render every page."""
import json
from importlib.metadata import version
from reportlab.platypus import PageBreak, Spacer
from common import ROOT, start, load_results, save_results, finish, words
from report_layout import para, table, image_page, build_pdf, render_pdf

def narrative(R):
    n=R['netting']; miss=R['missing_id']; model=R['model']; season=R['seasonal']; co=R['countries']
    leaders=R['products']['leaders']; cr=R['cancellations_monthly']; out=R['outliers']
    sections=[]
    def section(title,*paragraphs):
        sections.append((title,list(paragraphs)))
    section('Executive Summary',
        f"We analysed the supplied retail transactions to connect purchasing patterns with customer actions. Chronological cancellation matching leaves GBP {n['net_revenue']:,.2f} in identified-customer net merchandise value. Missing IDs exclude GBP {miss['revenue']:,.2f} of otherwise valid purchase value, so these results describe observable customers rather than the whole business. RFM with {model['k']} clusters achieves silhouette {model['silhouette']:.3f}, supporting a coarse behavioural split rather than perfectly separated customer types. The separate high-value group contributes {out['revenue_share']:.2%} of net value. We recommend differentiated retention tests and individual major-account review, supported by better customer identification and return linkage. Revenue concentration does not establish profitability or campaign effectiveness.")
    section('Introduction',
        "Option C asks how a UK online retailer can use transaction records to understand products, seasonality, countries and customers. The business question is practical: which purchasing patterns warrant a different merchandising or customer-contact decision? We use segmentation as an analytical model that organises observed behaviour. There is no supervised outcome, and forecasting is outside this project's scope.",
        f"The supplied Online Retail II workbook spans {R['source']['start']} to {R['source']['end']}. It is the sole empirical data source; the supplied assignment PDF defines the task. The UCI source is identified in the brief (Online Retail II, {R['references']['uci_year']}). We combine descriptive analysis with a reproducible scikit-learn pipeline, preserving distinctions between gross purchases, retrospective net sales and invoice cancellation rates. The output is a basis for controlled business tests, not evidence that customers will respond to a particular intervention.")
    sections[-1][1].append('The proposed business use is to allocate attention more deliberately. A merchandising team might prioritise availability for products with repeated demand, while a customer team could vary contact according to observed activity. These decisions require different evidence. We therefore keep product-level demand, country-level concentration and customer-level segmentation distinct, and link recommendations to the specific summaries that support them. Customer spending is an outcome to describe, not an explanation of motivation.')
    section('Data Description and Preprocessing',
        f"The workbook contains {R['source']['rows']:,} rows and {R['source']['columns']} columns across the source sheets. Fields identify invoices, products, descriptions, quantities, dates, prices, customers and countries. The sheet date ranges overlap from {R['source']['overlap_start']} to {R['source']['overlap_end']}. Exact deduplication removes {R['regression']['duplicates']:,} rows. Schema, null counts and date ranges are saved by sheet in the results file. We use pandas and NumPy for data handling (The pandas development team, n.d.; NumPy developers, n.d.). The complete sequential cleaning audit follows this narrative.",
        f"Before extending exclusions, the original code list passes every supplied regression check. We then remove {R['nonproduct']['extra_rows']:,} additional fee, sample and voucher rows. An evidence table preserves irregular codes and example descriptions: syntax alone never proves a code is invalid. Purchases require positive quantity and price. Missing IDs are not imputed: {miss['rows']:,} valid purchase rows, {miss['purchase_revenue_share']:.2%} of gross valid merchandise value, are excluded from customer linkage. This coverage loss may systematically distort customer and country profiles.",
        f"Cancellations reverse only strictly earlier purchases with the same customer and stock code, taking the most recent eligible units first. Remaining units keep the original purchase price. This is an explicit allocation assumption because invoice-level return links are unavailable. Of {n['cancellation_rows']:,} cancellation rows, {n['matched']:,} are matched, {n['partly_matched']:,} partly matched and {n['unmatched']:,} unmatched. We reverse {n['reversed_units']:,.0f} units and GBP {n['reversed_revenue']:,.2f}; {n['unmatched_units']:,.0f} units remain unmatched. Netting drops {n['lines_dropped']:,} fully reversed lines. Unmatched returns are reported without deducting them from unrelated purchases. Extreme purchases specified in the request are fully reversed by automated tests.")
    section('Exploratory Data Analysis',
        f"Figure 1 shows the actual peak, {next(iter(season['peak_months']))}, at GBP {next(iter(season['peak_months'].values())):,.2f}. Complete-month fourth-quarter mean revenue is {season['q4_rest_ratio']:.2f} times the other-month mean. The incomplete final month is shaded and excluded from this comparison. Matching returns to original sales means the curve describes retained purchase cohorts, not cash movements on return dates. The short window supports a descriptive seasonal pattern, not a general seasonal law. Figures use Matplotlib and seaborn (Matplotlib development team, n.d.; seaborn developers, n.d.).",
        f"Figure 2 separates value, volume and reach. {leaders['revenue']['description']} leads revenue at GBP {leaders['revenue']['revenue']:,.2f}; its product value per invoice is GBP {leaders['revenue']['value_per_order']:,.2f}, with {leaders['revenue']['repeat_customers']:,} repeat customers. {leaders['units']['description']} leads volume at {leaders['units']['units']:,.0f} units. {leaders['customers']['description']} reaches {leaders['customers']['customers']:,} customers, with {leaders['customers']['repeat_customer_share']:.1%} returning for the product. These different leaders justify distinguishing stock throughput, transaction value and repeat demand when setting priorities.",
        f"Figure 3 excludes the United Kingdom by name. {co['leader']} leads export revenue with GBP {co['leader_revenue']:,.2f} from only {co['leader_customers']:,.0f} customers. {co['highest_AOV']} averages GBP {co['highest_AOV_value']:,.2f} per order and {co['highest_AOV_units_per_order']:,.1f} units per order, versus UK values of GBP {co['UK_AOV']:,.2f} and {co['UK_units_per_order']:,.1f}. Larger observed baskets accompany high order value, while tiny customer bases limit generalisation. We cannot infer wholesale status. Figure 4 reports complete-month mean cancellation invoice rates of {cr['q4_mean']:.2%} in the fourth quarter and {cr['rest_mean']:.2%} otherwise; {'there is no descriptive fourth-quarter elevation' if cr['q4_mean']<=cr['rest_mean'] else 'the fourth quarter is descriptively higher, without a causal or significance claim'}.")
    section('Modelling Approach',
        f"Clustering inputs, in fitted order: {', '.join(model['features'])}. All customer features are {', '.join(R['features']['all'])}. Recency is whole days since the latest retained purchase, measured at {R['features']['snapshot']}; Frequency counts retained invoices; Monetary sums retained merchandise value. AOV equals Monetary divided by Frequency, Variety counts products, and CancellationRate divides distinct cancellation invoices by cancellation plus valid gross purchase invoices for identified customers. Fully reversed-only customers do not enter the positive-net customer population.",
        f"AOV is omitted from clustering because it algebraically repeats information already present. CancellationRate is zero for {R['features']['cancellation_zero_share']:.1%} of customers; its skew changes from {R['features']['skew']['CancellationRate']['before']:.2f} to {R['features']['skew']['CancellationRate']['after']:.2f} under log transformation. It remains a profiling measure. Figure 5 and the correlation heatmap show transformation behaviour and redundancy. We apply the conventional upper Tukey fence to log net Monetary, recalculated after netting: GBP {out['threshold_GBP']:,.2f}. The {out['customers']:,} customers above it remain visible in Outlier-Wholesale; that requested label is not verified buyer type.",
        f"We compare RFM with an extended set adding Variety across candidate cluster counts, recording inertia, full-sample silhouette, Davies-Bouldin and mean pairwise adjusted Rand agreement across {model['stability_seeds']} seeds. Highest silhouette determines the choice; the full table and Figure 6 expose the alternatives. The chosen {model['feature_set']} model has silhouette {model['silhouette']:.3f}, Davies-Bouldin {model['davies_bouldin']:.3f} and seed agreement {model['stability_ARI']:.3f}. More clusters may support more actions, but these results do not justify trading away separation without an operational test. The pipeline applies log transformation, standardisation and K-Means together (Pedregosa et al., {R['references']['sklearn_year']}). Cluster IDs are reordered by descending mean Monetary, and saved-model reload predictions are checked.")
    sections[-1][1].append('The evaluation measures answer different questions. Inertia records within-group squared distance and generally decreases as groups are added. Silhouette compares cohesion with distance to neighbouring groups. Davies-Bouldin summarises similarity between groups, where lower values indicate more separation. Adjusted Rand agreement compares assignments across starting seeds after allowing for relabelling. We examine these together because a visually attractive projection or falling inertia alone cannot establish a useful partition. There is no labelled ground truth against which to report classification accuracy.')
    segment_paragraphs=[]
    for s in R['segments'].values():
        segment_paragraphs.append(f"{s['name']} contains {s['size']:,} customers, {s['customer_share']:.2%} of customers and {s['revenue_share']:.2%} of net revenue (GBP {s['revenue']:,.2f}). Median recency is {s['recency_median']:,.0f} days and median frequency is {s['frequency_median']:,.0f} invoices. {s['action']}")
    section('Results and Discussion',
        f"Figure 7 projects the transformed customers into principal components, retaining {sum(model['pca_variance']):.1%} of variance. Projection overlap reinforces the need for measured language. Figure 8 standardises raw segment means against the all-customer population, including outliers. The profile tables report both means and medians to expose skew. Names use segment medians relative to all-customer terciles; automated checks reject names that contradict recency, frequency or monetary tags.",
        *segment_paragraphs,
        f"The saved pipeline classifies a synthetic median-based customer with recency {R['model_test']['inputs']['Recency']:,.0f} days, frequency {R['model_test']['inputs']['Frequency']:,.0f}, Monetary GBP {R['model_test']['inputs']['Monetary']:,.0f} and internally consistent AOV GBP {R['model_test']['inputs']['AOV']:,.0f} as {R['model_test']['segment_name']}. This checks artifact use, not predictive accuracy. A deployment wrapper must apply the separate outlier fence before calling the fitted ordinary-customer model.")
    section('Conclusion and Recommendations',
        "The main recommendation is to preserve valuable active relationships, review exceptional accounts individually, and test economical reminders for the dormant group. Group size alone should not dictate budget: revenue concentration, contact costs, margins and incremental response all matter. Product planning should likewise distinguish high-unit products from products with higher transaction value and repeated customer demand. Export decisions should examine account concentration before extrapolating a country average to a new market.",
        f"What the data cannot tell us is substantial. Missing IDs remove {miss['rows']:,} purchase rows, {miss['purchase_rows_share']:.2%} of valid purchase rows and GBP {miss['revenue']:,.2f}, or {miss['purchase_revenue_share']:.2%} of gross valid purchase value. Unmatched cancelled units account for {n['unmatched_unit_share']:.2%} of cancelled units. There are no browsing events, marketing spend, margins or return reasons. Cancellation invoices are observable, but a complete physical-return rate is not. We cannot distinguish customers who left from customers whose normal buying cycles are long, or identify the reason for inactivity.",
        "The evidence comes from a single retailer and a historical observation window with an incomplete final month. RFM is backward-looking, and different customers have different opportunities to accumulate orders. Euclidean K-Means favours compact groups after transformation; changing the observation window, fence or feature weighting could change membership. Strong seed agreement is not temporal stability or evidence of campaign uplift. Correlation is not causation, and a high-value segment need not be profitable.",
        "Before operational use, improve customer-ID capture and explicit return-to-sale links, verify the high-value accounts, and run controlled action tests with untreated comparisons. Measure incremental net purchasing after returns and costs, then revisit segment usefulness. AI assisted code generation, debugging, report drafting and verification; human group members must understand and review the work. The source citation remains provisional pending verification on the UCI page. No external retail facts were added, and no new customer response or profit estimates were invented.")
    sections[-1][1].append('A practical follow-up would track whether the proposed contact changes retained purchasing without simply subsidising orders that would have happened anyway. Contact frequency, stock availability and opt-out behaviour should also be considered before scaling. Those variables are absent here, so the report proposes a test design rather than estimating an effect. Rebuild the features consistently at later snapshots and compare segment movement before treating the current groups as permanent customer identities.')
    return sections

def references(R):
    years=R['references']; env=R['environment']
    refs=[f"Online Retail II. ({years['uci_year']}). UCI Machine Learning Repository [Data set]. {R['source']['url']} (Provisional title-first citation: verify the exact author, citation and DOI on the UCI page before submission; donation year supplied in the request.)",
      f"Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., VanderPlas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. ({years['sklearn_year']}). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, {years['journal_volume']}, {years['page_first']}-{years['page_last']}. https://jmlr.org/papers/v12/pedregosa11a.html"]
    for package,team,url in [('pandas','The pandas development team','https://pandas.pydata.org/'),('numpy','NumPy developers','https://numpy.org/'),('matplotlib','Matplotlib development team','https://matplotlib.org/'),('seaborn','seaborn developers','https://seaborn.pydata.org/')]:
        refs.append(f"{team}. (n.d.). {package} (Version {env[package]}) [Computer software]. {url}")
    refs.append('OpenAI. (n.d.). Codex [AI-assisted software authoring tool]. https://openai.com/codex/')
    refs.append('Supplied assignment brief. (n.d.). Data Science Group Assignment [Unpublished course handout; institution and course title not supplied].')
    return refs

def main():
    start()
    R=load_results()
    R.setdefault('assignment',json.loads((ROOT/'docs/brief_metadata.json').read_text()))
    packages=['pandas','numpy','scikit-learn','matplotlib','seaborn','joblib','pyarrow','nbformat','nbconvert','ipykernel','reportlab','openpyxl','pytest','pypdf','python-calamine']
    R['environment']={p:version(p) for p in packages}
    R['references']={'uci_year':2019,'sklearn_year':2011,'journal_volume':12,'page_first':2825,'page_last':2830}
    sections=narrative(R)
    story=[Spacer(1,90),para('Identifying Patterns in Global E-Commerce Sales','Title'),Spacer(1,22),
           para('Chosen problem statement: Option C'),para('Group members and student IDs: [TO BE COMPLETED]'),
           para('Course title: [TO BE COMPLETED]'),para('Submission date: [TO BE COMPLETED]'),
           Spacer(1,30),para('Transaction patterns, customer segmentation and business actions'),
           para('Ethics and Integrity Declaration: signed group form required by the brief; completion not verified.','CaptionRetail')]
    body=[]
    for title,paras in sections:
        story.extend([PageBreak(),para(title,'Heading1')])
        body.append(title)
        for p in paras:
            story.append(para(p)); body.append(p)
        if title=='Data Description and Preprocessing':
            story.append(para('Complete cleaning audit','Heading2'))
            headers=['Rows before','Removed','Rows after','Reason / treatment']
            rows=[[f"{a['before']:,}",f"{a['removed']:,}",f"{a['after']:,}",a['reason']] for a in R['audit']]
            story.append(table(headers,rows,[65,55,65,320]))
            body.extend(['Complete cleaning audit',' '.join(headers),*[' '.join(r) for r in rows]])
        if title=='Results and Discussion':
            story.extend([Spacer(1,12),para('Segment sizes and revenue','Heading2')])
            headers=['Segment','Customers','Customer share','Net value (GBP)','Revenue share']
            rows=[[s['name'],f"{s['size']:,}",f"{s['customer_share']:.2%}",f"{s['revenue']:,.2f}",f"{s['revenue_share']:.2%}"] for s in R['segments'].values()]
            story.append(table(headers,rows,[145,65,80,125,90]))
            body.extend(['Segment sizes and revenue',' '.join(headers),*[' '.join(r) for r in rows]])
    story.extend([PageBreak(),para('Raw customer profiles','Heading1')])
    headers=['Segment / units','Feature','Mean','Median']
    rows=[]
    for s in R['segments'].values():
        for col in R['features']['all']:
            key=col.lower()
            is_rate=col=='CancellationRate'
            fmt='.2%' if is_rate else ',.2f'
            unit='days' if col=='Recency' else 'GBP' if col in ['Monetary','AOV'] else 'invoice ratio' if is_rate else 'count'
            rows.append([s['name'],f'{col} ({unit})',format(s[key+'_mean'],fmt),format(s[key+'_median'],fmt)])
    story.append(table(headers,rows,[145,140,110,110]))
    body.extend(['Raw customer profiles',' '.join(headers),*[' '.join(r) for r in rows]])
    for key,info in R['figures'].items():
        image_page(story,key,info)
        body.extend([info.get('title',key),info['caption']])
    story.extend([PageBreak(),para('Full model selection results','Heading1')])
    headers=['Feature set','k','Inertia','Silhouette','Davies-Bouldin','Seed ARI']
    rows=[[v['feature_set'],str(v['k']),f"{v['inertia']:,.2f}",f"{v['silhouette']:.3f}",f"{v['davies_bouldin']:.3f}",f"{v['stability_ARI']:.3f}"] for v in R['model']['selection_table']]
    story.append(table(headers,rows,[95,30,95,90,105,90]))
    body.extend(['Full model selection results',' '.join(headers),*[' '.join(r) for r in rows]])
    bodytext='\n\n'.join(body)+'\n'
    count=words(bodytext)
    print('Report words excluding cover, references and repeated page furniture:',count,flush=True)
    assert 2300<=count<=2700,count
    story.extend([PageBreak(),para('References','Heading1')])
    # Software citations use installed-version metadata, with undated developer references.
    for ref in references(R):
        story.append(para(ref,'CaptionRetail'))
    (ROOT/'outputs/report/report_body.txt').write_text(bodytext,encoding='utf-8')
    path=ROOT/'outputs/report/Project_Report.pdf'
    pages=build_pdf(story,path)
    rendered=render_pdf(path)
    assert pages==rendered
    R['report']={'word_count_excluding_cover_references_page_furniture':count,'pages':pages,'rendered_pages':rendered,'page_numbers':list(range(1,pages+1)),
                 'count_policy':'All section prose, headings, table cells and accessible figure captions; excludes cover, bibliography and repeated page furniture.',
                 'visual_inspection':'Pending review of rendered pages; generation alone does not verify layout.'}
    save_results(R)
    finish('Report','Report body word count checked; PDF generated, reopened and every page rendered with Poppler. Visual review of the latest rendered pages is still pending. Group identity, course, date, signed declaration and exact UCI citation require human completion.')

if __name__=='__main__':
    main()
