# Identifying Patterns in Global E-Commerce Sales

Assignment Option C: reproducible transaction cleaning, chronological cancellation netting, descriptive analysis and customer segmentation. The supplied workbook and assignment brief are the only empirical sources. This is an analytical segmentation, with no forecast or supervised prediction target.

## Setup and data

Put the supplied workbook at `inputs/online_retail_II.xlsx` and the supplied brief at `inputs/Data Science Group Assignment.pdf`. The workbook is excluded from Git. To obtain the data separately, use the [UCI dataset page](https://archive.ics.uci.edu/dataset/502/online+retail+ii) and place its workbook at that input path; this project used the user's local copy accessed on 2026-10-16. Verify source licensing and the exact citation before redistributing the data.

Create a virtual environment with `python -m venv .venv`, activate it, and run `python -m pip install -r requirements.txt`. Use a compatible Python environment; the pinned package versions are the versions actually executed in this project. Install Poppler and place `pdftoppm` on PATH if it is not already available. The script also detects the bundled local Poppler runtime.

Run `python run_all.py --clean` from the repository root. This archives earlier generated data and outputs under `work/rebuild_backups/` and rebuilds from both source inputs. It does not overwrite the original Downloads files. All analytical stages, notebook execution, PDF rendering, artifact validation and pytest are run. Each stage records progress and makes a local Git commit, so run inside an initialised repository with Git installed and a writable Git directory. The commit identity is a local automation identity, not a claim about group authorship.

For a later validation without rebuilding, run `python src/08_verify.py` and `python -m pytest -q`. Open `outputs/notebook/retail_segmentation.ipynb` to inspect the already executed cells and figures. Re-execution recomputes the same workflow and writes its generated artifacts.

## Folder structure

`inputs/`: supplied source files. `src/`: stage implementations and shared helpers. `data/`: generated transactions, customer tables and selection metrics. `docs/`: extracted requirements and checklist. `tests/`: independent matching edge cases and artifact contracts. `outputs/figures/`: labelled figures with computed captions. `outputs/model/`: fitted pipeline, column order and names. `outputs/report/`: PDF and countable report text. `outputs/notebook/`: executed notebook. `outputs/demo/`: spoken script. `outputs/docs/`: cleaning audit, evidence, profiles, source documentation and verification. `outputs/results.json`: common numerical and naming ledger. `PROGRESS.md`: stage history and unresolved human tasks. `requirements.txt`: actual environment versions. `run_all.py`: complete rebuild entry point.

## Results

The fixed original-list regression passes. 34,335 exact duplicate rows were removed, followed by 5,581 original non-product rows and 237 justified extended exclusions. Missing IDs exclude 226,761 valid purchase rows worth GBP 2,575,278.90. Chronological cancellation matching reports 15,872 matched, 127 partly matched and 1,915 unmatched cancellation rows. It reduces identified purchase value from GBP 17,068,582.72 to GBP 16,338,578.60, leaving 770,553 lines and 5,839 customers.

The selected rfm model has k=2, silhouette 0.438, Davies-Bouldin 0.873 and mean seed ARI 0.999. Exact clustering column order: Recency, Frequency, Monetary. It is a coarse descriptive split with overlap. All profiling features: Recency, Frequency, Monetary, AOV, Variety, CancellationRate. AOV derives from Monetary/Frequency, and CancellationRate is retained for profiling rather than clustering. The upper log-IQR spending fence is GBP 36,098.33; the separate Outlier-Wholesale group contributes 27.54% of net value. That label is not proof of buyer type.

- **Loyal champions**: 2,347 customers, 60.35% of net value. Offer early access to relevant products and test a replenishment reminder against a holdout group.

- **Dormant occasional buyers**: 3,452 customers, 12.10% of net value. Test a low-cost reminder using their last product category before committing a wider recovery budget.

- **Outlier-Wholesale**: 40 customers, 27.54% of net value. Review major accounts individually, confirm buyer needs and set stock reservations against their observed repeat orders.

## Load and score

Inputs must follow the fitted feature order Recency, Frequency, Monetary. The example below reads the saved order and test inputs rather than copying stale values. The separate outlier rule must be applied before the ordinary-customer pipeline. The pipeline expects raw nonnegative customer aggregates with valid positive Frequency; it handles logarithms and scaling internally.

```python
import json
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
```

The saved test case predicts **Dormant occasional buyers**. This reload test checks artifact integrity, not predictive generalisation.

## Definitions and limits

Net merchandise value reverses matched units at original purchase prices and assigns them to original sale dates. Cancellations are matched strictly backward in time by customer and product, most recent first; unmatched units remain separate. Distinct identified-customer cancellation invoices divided by distinct identified-customer cancellation plus valid identified-customer gross purchase invoices; merchandise codes only. Same invoice ratio as the customer profiling feature. Country AOV uses net value divided by retained distinct invoices. Monthly seasonal comparisons exclude the partial final month. Seed stability measures only initialisation changes. There is no observed uplift, profit, browsing data, marketing spend or return reason. Missing-ID selection, a single retailer and historical coverage constrain conclusions. Segment names and actions are held in `outputs/model/segment_names.json`; stable result keys remain unchanged by display names.
