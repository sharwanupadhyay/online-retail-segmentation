# Dataset source documentation

Source identified in the supplied brief: [Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii). Analysis used only the user-supplied workbook and brief. Local access date: 2026-10-16; this is not a claimed download date from UCI.
The source sheets contain 1,067,371 rows across 8 fields. Observation window: 2009-12-01 07:45:00 through 2011-12-09 12:50:00. Sheet overlap: 2010-12-01 08:26:00 through 2010-12-09 20:01:00.

## Schema and missingness

Year 2009-2010: 525,461 rows, 8 columns. Fields, source dtypes and missing counts:

| Field | Dtype | Missing |
| --- | --- | ---: |
| Invoice | object | 0 |
| StockCode | object | 0 |
| Description | object | 2,928 |
| Quantity | int64 | 0 |
| InvoiceDate | datetime64[us] | 0 |
| Price | float64 | 0 |
| Customer ID | float64 | 107,927 |
| Country | str | 0 |

Year 2010-2011: 541,910 rows, 8 columns. Fields, source dtypes and missing counts:

| Field | Dtype | Missing |
| --- | --- | ---: |
| Invoice | object | 0 |
| StockCode | object | 0 |
| Description | object | 1,454 |
| Quantity | int64 | 0 |
| InvoiceDate | datetime64[us] | 0 |
| Price | float64 | 0 |
| Customer ID | float64 | 135,080 |
| Country | str | 0 |

## Sequential preprocessing audit

| Before | Removed | After | Treatment |
| ---: | ---: | ---: | --- |
| 1,067,371 | 34,335 | 1,033,036 | Remove exact duplicate rows across both sheets, including their overlapping dates; no fuzzy deduplication. |
| 1,033,036 | 5,581 | 1,027,455 | Remove only original non-product code list, after uppercase and whitespace normalisation; fixed-list regression passed. |
| 1,027,455 | 237 | 1,027,218 | Extend exclusions only with documented fee, sample and gift-voucher codes; evidence is in non_product_evidence.csv. |
| 1,027,218 | 17,914 | 1,009,304 | Separate all cancellation-invoice rows into a retained cancellation table; these are not booked as sales. |
| 1,009,304 | 5,964 | 1,003,340 | Remove non-cancellation rows with nonpositive quantity or price; no price imputation. |
| 1,003,340 | 226,761 | 776,579 | Exclude missing-ID positive purchase rows from linked customer analysis; their gross merchandise value and coverage loss are reported separately. |
| 776,579 | 6,026 | 770,553 | Drop fully reversed purchase lines after chronological customer/product LIFO matching; partly reversed lines retain remaining units at original purchase prices. Unmatched cancellation units remain outside net sales. |

Original-list regression passed: {"duplicates": 34335, "nonproduct": 5581, "cancellations": 18046, "invalid": 5986, "missing_id": 226844, "purchases": 776579, "customers": 5852}. The original list was used unchanged before inspecting extended exclusions.
Extended exclusions: AMAZONFEE, GIFT_0001_10, GIFT_0001_20, GIFT_0001_30, GIFT_0001_40, GIFT_0001_50, GIFT_0001_60, GIFT_0001_70, GIFT_0001_80, GIFT_0001_90, S. Extra rows removed: 237. Evidence and retained irregular catalog codes are in non_product_evidence.csv. Descriptions are not imputed; retained missing descriptions: 0.
Missing-ID coverage loss: 226,761 valid purchase rows (22.60%), GBP 2,575,278.90 (13.11% of valid gross purchase value).
Cancellations: 15,872 matched / 127 partly matched / 1,915 unmatched, out of 17,914 retained rows. Cancelled units 467,739; reversed 450,047; unmatched 17,692 (3.78%). Matching runtime 12.78 seconds. Missing-ID cancellation rows: 328. Nonnegative cancellation rows: 0.
Gross identified purchase value GBP 17,068,582.72; reversal GBP 730,004.12; net GBP 16,338,578.60. Fully reversed lines dropped: 6,026; partly reversed lines retained: 9,677. Remaining lines: 770,553; customers with positive net purchases: 5,839.
Matching key is customer plus stock code. Only strictly earlier purchases qualify, most recent first. Purchase prices determine the net revenue reduction. No price equality is required. The lack of explicit invoice return links makes this an allocation assumption. Unmatched returns are preserved and do not create negative customer spending. Netting is retrospective to the original purchase month.

## Feature and modelling definitions

Snapshot: 2011-12-10 12:50:00. All customer features: Recency, Frequency, Monetary, AOV, Variety, CancellationRate. Fitted feature order: Recency, Frequency, Monetary. Recency uses whole days since the last retained purchase; Frequency counts retained invoices; Monetary sums retained value; AOV = Monetary / Frequency; Variety counts retained products. Distinct identified-customer cancellation invoices divided by distinct identified-customer cancellation plus valid identified-customer gross purchase invoices; merchandise codes only. Same invoice ratio as the customer profiling feature.
Outlier rule: Upper Tukey fence on log1p net customer Monetary; descriptive high-value group, not confirmed wholesale. Upper fence GBP 36,098.33, derived from log quartiles 5.817 and 7.688 using multiplier 1.5. The separate group has 40 customers and 27.54% of net value.
Selected model: rfm, k=2; silhouette 0.438, Davies-Bouldin 0.873, seed ARI 0.999. Selection: Choose the highest full-sample silhouette across feature sets and candidate k; exact ties use higher stability, lower Davies-Bouldin and lower k. Stability varies initialisation, not customers or time.

## What the data cannot tell us

- No browsing events, marketing spend, margins, acquisition dates or return reasons supplied.
- Observed cancellations are invoice events, not a complete physical-return rate.
- Single UK retailer; historical window and incomplete final month limit generalisation.
- Customer/product LIFO is an allocation assumption, not an invoice-linked return record; prices may differ.
- Net sales retrospectively attribute matched returns to original purchase months; unmatched returns are not deducted from unrelated sales.
- K-Means assumes Euclidean compact groups after transformation; clusters may overlap and are descriptive.
- RFM is backward-looking; correlations and segment associations are not causal effects.
- Outlier-Wholesale is a requested operational label; buyer type is not observed.
- Initialisation stability is not temporal or resampling stability; there is no predictive holdout target.
- Actions are hypotheses for controlled tests; no uplift or profit claims are made.

## Citation and access caveat

The requested donation year is 2019. The exact UCI author and DOI have not been checked online because the request limits factual sources to the supplied files. Verify the exact citation on the linked UCI page before submission. Software versions are recorded in results.json and pinned in requirements.txt.
