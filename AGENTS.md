# NON-NEGOTIABLE RULES
Past attempts at this task (by another AI) failed in the specific ways below. Each is a rule. Violating any of them is a failure even if the output looks polished.

R1. NO HAND-TYPED NUMBERS. Every number that appears in any caption, report paragraph, README, docs file or video script must be computed by code, stored in a dict R, saved to outputs/results.json, and inserted via f-strings or templates. The only allowed typed numbers are: section/figure numbers, the random seed, the k-candidate range (2-10), the years of the dataset, and the regression-test constants in Stage 1. A previous attempt typed "£1.74M missing-ID revenue" (actual figure about £2.6M), "Netherlands AOV £2,240" (actual about £2,545), "revenue doubles Sep-Nov" (it did not), "davies-bouldin 0.91" (actual 1.26) and "~685 words" in a script of about 400 words. Do not reuse any of these. Old downstream numbers are banned entirely.

R2. NEVER WRITE INTERPRETATION BEFORE SEEING THE RESULT. Segment names, captions, "insights" and recommendations are written only after the numbers exist, and any claim ("peaks in Q4", "top product is #1 on revenue and customer reach", "skew reduced for all features", "export markets are wholesale") must be computed or must be worded neutrally. A previous attempt named a cluster "high spenders inactive 120+ days" when it was low-spend and ~360 days inactive.

R3. NO SYNTAX/TRUNCATION ERRORS. Every file must be complete. Run `python -m py_compile` on every script. After writing each file, check that it ends properly. Earlier code ended inside an unclosed triple-quoted string and never called its own functions.

R4. STABLE KEYS, NATIVE TYPES. Write one helper `save_results(R, path)` that converts numpy ints/floats/bools/arrays/Timestamps to native Python before json.dump (a previous attempt crashed on np.int64). Use stable result keys such as R["segments"]["0"]["recency_mean"], never keys built from display names (a previous attempt crashed with KeyError on 'cluster_1_at-risk_revenue').

R5. REGRESSION SELF-TEST COMES FIRST AND USES THE ORIGINAL SETTINGS. Previous code widened the non-product list before asserting expected counts, so its own assertion failed. See Stage 1.

R6. CANCELLATIONS MUST BE NETTED, CHRONOLOGICALLY. Cancelled orders counted as revenue (one customer ordered 80,995 units of "PAPER CRAFT , LITTLE BIRDIE" and cancelled minutes later; it showed up as a £168k top product). See Stage 1.

R7. NO ARBITRARY THRESHOLDS. Outlier rules and k choice must be justified from the data, and the justification printed.

R8. FIGURES MUST BE VERIFIED, NOT ASSUMED. After saving each figure, open it (view the image, or at minimum check axis limits and that annotations fall inside the axes). A previous partial-month marker sat at x=24 while the period axis ran 479-503, so it was invisible; another figure mixed bars at positions 0..n with a line on a period axis. Use real datetimes on a single shared axis.

R9. ONE DEFINITION PER CONCEPT. The feature list, segment names, k and thresholds are defined once (in results.json / config) and read everywhere. A validator (Stage 8) must confirm the code, notebook, report and video script agree.

R10. HONESTY. If something cannot be verified, say so in PROGRESS.md and the final reply. Report weak results as weak (a low silhouette is not "optimal separation"). Do not invent citations; cite only what certainly exists. Do not invent a course title.

R11. NO UNUSED IMPORTS, NO DEAD CODE, NO WARNINGS LEFT UNEXPLAINED.

