# D2 model error analysis

Status: corrected D2 quantitative analysis from the regenerated local evaluation. Detailed cell-level records remain in ignored `frontend/public/data/challenge.json`; do not commit or publish them.

## Evaluation boundary

The report covers 12 reserved observed wards, January 2024–June 2025, six categories, with all challenge labels excluded from model selection and fitting. It measures error against the supplied extract under COV-1. It is not an estimate of official scoring performance or future demand.

These measured results describe the zone-aware model implemented following the resolution of ISSUE-14 (`bbmp_zone_name` one-hot encoding).

## Observed aggregate behavior (Zone-Aware Model)

- Selected model: fixed-configuration Poisson HistGradientBoostingRegressor with 8-zone one-hot encoding.
- Cross-validation HGB pooled WAPE: **0.534931** (improved from 0.540276), versus K5 **0.624587** and CM **0.746230**. HGB beat K5 in 4 of 5 folds (Fold 1: 0.576284 vs 0.661989, Fold 2: 0.460562 vs 0.610658, Fold 3: 0.497124 vs 0.624586, Fold 4: 0.480997 vs 0.665047; Fold 5: 0.692559 vs 0.553921).
- Challenge pooled WAPE: **0.531722**; MAE: **7.441239 complaints per ward-month-category cell**.
- Mean category Spearman correlation on 18-month ward totals: **0.754701**.
- Mean top-quarter recall: **0.555556**, with `k=3` out of 12 challenge wards per category (electrical 0.6667, solid_waste 0.3333, roads 0.6667, trees 0.3333, animals_health 0.6667, other 0.6667).
- Comparison with missing-zone baseline:
  - Missing-zone HGB: CV WAPE 0.540276; Challenge WAPE 0.523879, MAE 7.3315, Spearman 0.7675, Recall 0.6111.
  - Zone-aware HGB: CV WAPE 0.534931; Challenge WAPE 0.531722, MAE 7.4412, Spearman 0.7547, Recall 0.5556.
  - *Epistemological limitation:* The challenge set was already observed prior to this re-run. No tuning was done on the challenge set, but this measurement reflects post-fix re-evaluation.

## Required next diagnostic before stronger claims

Inspect per-category metrics in `frontend/public/data/metrics.json` and challenge records in `challenge.json`; add ward-total signed errors and low-density quartile summaries using boundaries computed only on the corresponding training fold. Avoid tuning against the reserved challenge split; model changes require a predeclared validation protocol.

## Errors and limitations

The previous evaluator incorrectly ranked ward totals after combining categories; the reported 0.783217 Spearman and 0.333333 recall were superseded by the corrected per-category averages above. The HGB CV WAPE changed from 0.540180 to 0.540276 on rerun; the cause is unverified. COV-1 completeness, official metric conventions and challenge applicability remain unverified.
