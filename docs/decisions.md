# Model evaluation decisions

Status: D2 implemented and locally evaluated on the supplied public extract. Protocol and metric choices remain subject to the contracts in [planning/02_CONTRACTS_AND_EVALUATION.md](planning/02_CONTRACTS_AND_EVALUATION.md).

## Frozen split and comparison

- Challenge wards are chosen before fitting using SHA-256 over `citysight-challenge-v1:42:<ward_id>`. The current extract reserves 12 of 156 observed wards; 144 wards remain for five-fold shuffled `GroupKFold` with seed 42.
- Cross-validation predictions are scored for January 2024 through June 2025. Each fold fits using all available COV-1 months for its training wards. Validation and challenge wards are excluded from baseline statistics, neighbor selection, and HGB preprocessing/fitting.
- CM is category-by-month mean count with category mean fallback. K5 uses up to five nearest training centroids by haversine distance and equal weights. HGB uses the fixed Poisson configuration, fold-local numeric medians, and one-hot encoded `bbmp_zone_name` (falling back to `zone` or `__MISSING__`); early stopping is disabled. ISSUE-14 was resolved by correcting the zone feature extraction.
- Selection uses pooled out-of-fold WAPE. HGB is accepted only when it improves on the best baseline and wins on at least three of five fold WAPEs. The baseline tie rule favors CM. The 12 challenge labels are evaluated only after selection freezes.

## Actual local result (2026-11-03, Zone-Aware Re-evaluation)

| Candidate | Pooled CV WAPE | Pooled MAE | Fold WAPE, 1–5 | Status |
|---|---:|---:|---|---|
| CM | 0.746230 | 10.6312 | 0.802649, 0.670630, 0.682281, 0.826154, 0.763686 | PASS |
| K5 | 0.624587 | 8.8982 | 0.661989, 0.610658, 0.624586, 0.665047, 0.553921 | PASS; best baseline |
| HGB Poisson (zone-aware) | 0.534931 | 7.6209 | 0.576284, 0.460562, 0.497124, 0.480997, 0.692559 | PASS; wins K5 on 4/5 folds |

**Selected method: HGB Poisson (zone-aware).**
Re-evaluation on reserved challenge holdout: WAPE **0.531722**, MAE **7.441239**, mean Spearman **0.754701**, top-quarter recall **0.555556** (`k=3` per category).
*Methodological limitation:* The challenge holdout was already inspected under the initial missing-zone baseline (WAPE 0.523879, MAE 7.331471, Spearman 0.767518, recall 0.611111). While hyperparameters were not tuned on the holdout, this re-evaluation is not a pristine blind test. Both sets of measurements are preserved for honesty.

The regenerated local details are in ignored `frontend/public/data/metrics.json`, `challenge.json` and `manifest.json`; do not add these files to Git or publish them. The older `artifacts/evaluation.json` predates the ranking correction and must not be used.

The earlier reported Spearman 0.783217 and recall 0.333333 ranked ward totals after combining categories; those values were mislabeled and are superseded. The regenerated report ranks wards within each category and averages the category results. Before the zone fix, HGB pooled CV WAPE was 0.540276; an earlier run produced 0.540180. The selected method was unchanged. The cause of this small run difference has not been established.

## Known interpretation limits

- COV-1 treats absent complaint rows as zero within the extract span; collection completeness is not confirmed.
- February 2020 and June 2025 are partial extract months. Evaluation focuses on the latter 18 months and retains June as supplied.
- The deterministic 12-ward holdout is small and hash-selected, not guaranteed geographically representative.
- The top-quarter metric follows the local tie and rounding convention in the contract. Official evaluator parity is unverified.
- This evaluation is offline and does not demonstrate official submission access, runtime sandbox compliance, deployment, or public-data publication permission.
