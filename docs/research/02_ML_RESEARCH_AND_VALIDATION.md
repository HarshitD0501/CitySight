# CitySight model research and validation

The single implementation contract is [models, splits and metrics](../planning/02_CONTRACTS_AND_EVALUATION.md). References and version caveats are in [the research ledger](10_REVERIFICATION_REPORT.md).

Use two transparent baselines: category-month mean and the mean of five nearest eligible training wards. Compare at most one bounded scikit-learn histogram boosting candidate. CatBoost, LightGBM, GNNs, graphs, target encodings and automatic tuning are not approved core dependencies. This narrows the earlier research menu into an executable plan; it makes no accuracy claim.

Reserve the fixed challenge before any selection. Fit transforms and neighbor summaries inside training folds. The Poisson candidate uses nonnegative counts, fixed iterations and disabled automatic early stopping; repeated rows must not create a misleading row-level validation split. Select using pooled out-of-fold WAPE and fold consistency; do not tune from challenge metrics. A constant baseline's undefined ranking metric is reported honestly.

The historical target dates overlap other wards' records. A temporal holdout is a different stress test and is deferred; do not describe current outputs as validated future forecasts. Exposure normalization based on 2011 population is also optional future research, not assumed to improve counts. No intervals, confidence or causal explanation are included without additional held-out calibration/evidence.
