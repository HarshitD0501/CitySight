# CitySight contracts and evaluation

Status: PROPOSED interfaces and defaults. Repository evidence and official-source sections are in the [audit report](../research/10_REVERIFICATION_REPORT.md). Decisions live in [the blueprint](00_IMPLEMENTATION_BLUEPRINT.md). No benchmark result or package compatibility is asserted here.

## Input validation and coverage

Canonical categories, in order: `electrical, solid_waste, roads, trees, animals_health, other`. A month is a valid `YYYY-MM` calendar month. Ward IDs are nonempty strings read as strings; trim surrounding whitespace, reject decimal/scientific IDs, and do not silently merge different raw identifiers. Current input IDs are integer text. Use a single normalization function across files. Required headers are selected by name, not position; tolerate unused extra columns.

- Complaints require `complaint_id, category_group, grievance_time, ward_id`; ignore status for counting. Reject duplicate complaint IDs, invalid categories, missing mandatory values or unparseable timestamps. Parse the observed naive timestamp format `%Y-%m-%d %H:%M:%S` as source-local calendar time; do not apply a timezone shift. Stream records and aggregate counts instead of retaining all complaint dictionaries.
- Features require unique `ward_id` plus columns consumed by the selected method. A missing descriptive field is allowed; missing required numeric data is represented as missing for fold-fitted imputation. Malformed nonempty numeric input is an error. Strip comma thousands separators on documented numeric fields; growth values such as `59.10%` become percentage-point numbers `59.10`, consistently. Test these parsers. Do not coerce percentage strings to missing silently.
- Geometry requires a FeatureCollection with unique matching ward IDs, finite geographic positions, closed polygon rings with at least four positions and Polygon/MultiPolygon types. Check coordinate ranges. These checks do not prove topology. Geometry is needed for demo export, not for a scorer using supplied centroids.
- Grid requires `ward_id,month,category_group`, unique keys, allowed categories and existing feature IDs. Preserve input row order. An empty valid grid produces header-only output without model fitting. Invalid inputs exit nonzero with a concise diagnostic. Prediction cannot depend on a fixed 4,320-row set.
- The guide requires runtime handling of different valid inputs. Exclude every requested grid ward ID from labeled training wards, even if it appears in complaints, so the cold-start rule remains true. Fit one method per invocation on remaining eligible wards. Fail clearly if none remain. Unknown-month behavior is defined below.

**COV-1 (PROPOSED local assumption):** count source records for observed labeled wards over every calendar month from the source's first to last timestamp and every allowed category; fill absent combinations with zero records in that extract. Never zero-fill the 40 target wards or wards 3/65 as training labels. Preserve February 2020 and June 2025 as supplied partial periods; do not scale to a full month or drop them silently. Required evaluation reports focus on January 2024–June 2025 for held-out wards and label June as potentially partial. This policy is reproducible but does not verify complete collection coverage. An organizer clarification supersedes COV-1, invalidating affected counts, metrics and artifacts until regenerated.

## Runtime interfaces

Guide-mandated scorer:

```text
python predict.py --data-dir {public_dir} --grid {grid_csv} --output {output_csv}
python train.py --data-dir {public_dir} --out {model_directory}
```

Scorer output is UTF-8 CSV with exactly `ward_id,month,category_group,predicted_count`; one row per supplied key in supplied order. Predictions are finite nonnegative decimals, not necessarily integers. No intervals in the core release. Use the standard CSV writer; do not concatenate unescaped fields. Write a temporary sibling output within the permitted output directory and atomically replace only after all validation succeeds. Failure must not publish a partial new CSV; report if a pre-existing old output remains.

`predict.py` rebuilds from public files at runtime, uses the method/configuration selected in D2, and never loads precomputed ward answers or assumes committed weights are authoritative for changed data. `train.py` uses the same fit function and saves minimal rebuild metadata plus the selected estimator if useful for auditing. Do not deserialize untrusted pickle/joblib files. Selection configuration may be committed; data-derived answer tables may not.

Proposed internal responsibilities: `load_inputs(data_dir)`, `aggregate_counts(records, coverage_policy)`, `fit(training_wards, counts, features, model_config)`, and `predict(fitted, grid, features)`. Return typed records/arrays and explicit errors. Separate input validation from fitting so empty/invalid grids fail cheaply. Expose local-only evaluation/export commands through `python -m citysight.evaluate` and `python -m citysight.export_demo`; document their arguments and source-path setup in the implementation README. Root entry points must work without undeclared installation steps.

Guide runtime: 10 minutes total, 2 CPU, 4 GB RAM, no network; read-only filesystem except `/output` and `/tmp`. Use only the requested output directory and a per-run temp directory. Set thread limits before scientific-library imports; avoid persistent caches, repo writes and pycache writes in read-only execution. No automatic retries on validation or model errors; avoid consuming the budget with repeated fits. Log stage durations and failures to stderr without dumping complaint rows or tokens.

Manifest core fields from guide p. 5: `team` (actual team slug), `problem: p3`, `entry: "python predict.py --data-dir {data_dir} --grid {grid} --output {output}"`, `python: "3.11"`, and `train_cmd: "python train.py --data-dir {data_dir} --out models/"`. No extra model downloads are needed by this design. Verify starter-specific schema when available. Required README headings, each with at least 20 words: `Problem understanding`, `Approach`, `Validation`, `Results`, `How to run`, `Use of AI tools`, `Data & licences`, `Team`. Use actual team details and explicitly unavailable evaluator results rather than invented values.

## Models and deterministic defaults

D0 resolves compatible fully pinned packages for Python 3.11; exact pins are not verified by this plan. Required baseline and candidate specification:

1. **CM:** category-by-exact-month mean count across eligible training wards, including COV-1 zeros. Missing source month uses the category mean across training ward-months. Missing/zero training category count means a legitimate zero mean when its covered cells exist; no covered training cells is an input/training error.
2. **K5:** five nearest eligible training wards by haversine distance between supplied centroid latitude/longitude in radians; equal-weight mean of their category/month counts. Use `min(5, number_of_training_wards)`; distance ties sort by normalized ward ID. Never use validation/challenge/query wards as neighbors. Missing month falls back to CM's category mean. Reject missing/out-of-range required centroids. This is a transparent guide-aligned baseline, not a claim of the guide's measured score.
3. **HGB:** one optional `HistGradientBoostingRegressor` candidate with `loss='poisson', learning_rate=0.1, max_iter=100, max_leaf_nodes=15, min_samples_leaf=50, l2_regularization=1.0, early_stopping=False, random_state=42`. These are bounded proposed defaults, not optimal or measured settings. No search loop in the core phase. Native automatic early stopping can create a row-level validation split; it is disabled to preserve ward-level evaluation.

For HGB, use category and zone one-hot encoding with unknown zones mapped to an all-zero block. Numeric columns are `population_2011, area_sq_km, households_census_2011, road_length_kms, lakes, lake_area_sq_m, parks, park_area_sq_m, playgrounds, playground_area_sq_m, govt_schools, police_stations, fire_stations, bus_stops, streetlights, bus_routes, population_density_2011_persons_sq_km, decadal_popn_growth_rate_2011_2001, decadal_households_growth_rate_2011_2001, centroid_lon, centroid_lat`. Include time index `12 * year + month - 1` and calendar month 1–12. Fit numeric medians inside each training fold; use zero only for a column wholly missing in that training fold and record it. Freeze category/zone encodings on training data; use a missing-zone sentinel. Explicitly exclude ward ID/name, constituencies, `police_stn`, raw grievance categories, status and complaint-derived ward/neighbor counts. Do not add target encoding or target-derived features in this release.

Poisson requires nonnegative target counts and positive total training target. If data cannot satisfy the candidate's objective, report it and retain a valid baseline. For an unseen source month, HGB falls back to selected baseline behavior instead of extrapolating an unvalidated time trend; record the fallback. Reject nonfinite predictions, and clamp only finite negative model outputs to zero while recording the count of clamps.

## Splits, selection and metrics

- Sort observed ward IDs; choose 12 challenge wards by the lowest SHA-256 digest of UTF-8 `citysight-challenge-v1:42:<ward_id>`, tie-break by ID. Persist IDs and algorithm before model selection. This is independent of labels, reproducible and a proxy for the official cold-start task; it does not guarantee representative geography.
- Exclude these wards from all candidate selection and preprocessing. Use five-fold `GroupKFold(shuffle=True, random_state=42)` on the remaining wards with ward ID as group. This API needs scikit-learn >=1.6; verify compatible pins in D0. Score out-of-fold predictions only for the 18 target months, while fitting on all allowed source months of training wards. Historical-period overlap is intentional for this spatial task.
- Aggregate WAPE from pooled out-of-fold absolute-error and actual totals; do not average fold ratios and call that pooled WAPE. Report each fold separately. Choose the best valid baseline by pooled WAPE; exact ties prefer CM. Accept HGB only if pooled WAPE is strictly lower than that baseline and at least three of five fold WAPEs are lower. Otherwise keep the baseline. Record failures; do not substitute a silent fallback during model selection.
- Freeze method/configuration, then evaluate the 12 reserved challenge wards once. Do not retune from that result. Demo challenge predictions come from a fit excluding all challenge labels; scoring fit uses all eligible supplied observed wards except query IDs. Record distinct fit IDs to prevent mixing provenance.
- Primary WAPE = sum absolute error / sum actual counts. Zero total actuals yields JSON `null` plus reason `zero_actual_total`, never an invented zero score. MAE = mean absolute cell error. Pooled WAPE and MAE determine no causal or full-city impact claim.
- Mean Spearman: per-category 18-month ward totals, average-rank handling of ties, Pearson correlation of the two rank vectors, average across defined categories. Constant ranks yield null and are listed; disclose that local undefined handling is a convention, not a verified evaluator implementation.
- Top-25% recall: local diagnostic uses `k=ceil(n_wards/4)` per category on 18-month totals, ties by ward ID; recall is intersection size divided by k and then mean across categories. The guide does not specify ties/rounding; report this convention. No metric computed on target wards without actual labels.
- Report category MAE/WAPE, zero/nonzero cells and ward-total signed errors; report errors for low-density wards using training-set density quartile boundaries. This is descriptive error analysis. No calibrated intervals or confidence claims without a separate validated design.

## Static artifact contract

Proposed local-only exports under `frontend/public/data/`, excluded from Git together with `artifacts/`, source data copies, model binaries and build outputs. Use a generated `manifest.json` with schema_version `1`, run_id, creation time in UTC, coverage_policy `COV-1`, source hashes, category/month lists, relative file paths and model/evaluation identifiers. Create a versioned subdirectory per run; publish the manifest last after validating all referenced files. Load one manifest snapshot per page session. Reject schema mismatch, missing files or inconsistent run IDs with an error state; never mix stale runs.

| File | Records / required fields | Provenance and errors |
|---|---|---|
| `predictions.json` | envelope `schema_version,run_id,fit_id,records`; each `ward_id,month,category_group,predicted_count` | full-fit predictions for target grid; explicit estimate labels |
| `observations.json` | same envelope, no model fit required; each `ward_id,month,category_group,observed_count` | source-extract counts for observed wards; COV-1; no target actuals |
| `wards.geojson` | supplied geometry plus normalized ID, name and `ward_status` | status enum `observed,target,unassigned`; all 198 supplied features, no invented polygons |
| `challenge.json` | envelope plus challenge fit ID and records `ward_id,month,category_group,predicted_count,actual_count` | reserved-ward fit only; labels are visible in downloaded assets |
| `metrics.json` | `schema_version,run_id`, selection, split metadata, fit IDs, metric values, undefined reasons and limitations | finite numbers or null; raw evaluation outputs stay local |

No row-level complaint IDs or descriptions reach the browser. Main map uses target estimates, observed source counts for observed wards, and null/no-data for unassigned wards. Challenge mode uses its own fit and records. Filtered error metrics must be recomputed from the same displayed challenge subset and labeled as such; full-challenge summary remains separately labeled. Manifest paths must be relative and must not escape the data directory or reference remote origins.

Artifact requests have a 10-second proposed local UI timeout, cancellation on unmount and a visible manual retry. Do not loop automatic retries. Malformed/inconsistent data disables dependent controls; valid table data can remain usable when geometry or WebGL fails. Loading failure is not an empty result or a zero count.
