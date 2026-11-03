# CitySight — Ward Pulse Demand Predictor & Civic Map

CitySight is an offline municipal demand estimator and interactive geospatial visualization tool built for the Ward Pulse (P3) civic challenge. The system enables city corporations to allocate municipal field crews, contractor resources, and maintenance budgets across newly onboarded wards before historical digital complaint records exist.

---

## Problem understanding

The civic corporation manages citizen complaints across six major infrastructure categories: electrical, solid waste, roads, trees, animal health, and other civic grievances. When onboarding 40 new municipal wards that have never recorded digitized complaints, municipal leadership faces an acute spatial cold-start problem: they must anticipate how many complaints of each type will occur month-by-month across an 18-month forward horizon (January 2024 to June 2025) without prior local history. To resolve this without guesswork, the system learns spatial, demographic, infrastructure, and temporal patterns from 156 observed wards (encompassing over 556,000 public complaints) and transfers these learned representations to the 40 target wards using their spatial geometries and census attributes.

## Approach

The modeling pipeline uses a regularized Poisson HistGradientBoostingRegressor (`HistGradientBoostingRegressor` from scikit-learn). It uses fold-local numeric preprocessing, demographic and infrastructure attributes, calendar features, category one-hot encoding, and one-hot encoding of administrative zones (`bbmp_zone_name`). For months outside the training window, predictions fall back to training category-month or global category averages. The offline scoring runtime enforces a strict two-thread limit via mathematical library environment variables, uses streaming CSV aggregation to minimize memory consumption, and performs atomic file replacement to guarantee zero partial-output artifacts.

## Validation

Validation mirrors an unseen test environment through a rigorous spatial holdout protocol rather than arbitrary random sampling or simple temporal splits. First, a reproducible 12-ward challenge holdout is reserved using SHA-256 hashes (`citysight-challenge-v1:42:<ward_id>`) and kept completely blind during model and parameter selection. Next, 5-fold `GroupKFold` grouped by unique `ward_id` is executed across the remaining 144 development wards to simulate real cold-start transfer to entirely new administrative geographies. Feature encoders, numeric median imputations, and spatial aggregations are refit exclusively on training folds, mathematically eliminating target leakage. Method selection requires superior pooled out-of-fold WAPE and wins on at least 3 of 5 folds against transparent category-month (CM) and 5-nearest-ward (K5) distance baselines.

## Results

On local 5-fold spatial cross-validation across 144 development wards (January 2024 through June 2025), the zone-aware Poisson HGB model achieved a pooled out-of-fold WAPE of 0.534931 and MAE of 7.6209 complaints per cell, beating the 5-nearest-ward baseline (K5 WAPE 0.624587) in 4 of 5 folds and substantially improving upon the category-month baseline (CM WAPE 0.746230). On the reserved 12-ward challenge split, the zone-aware model achieved pooled WAPE 0.531722, MAE 7.4412, mean Spearman rank correlation 0.754701, and mean top-quarter recall 0.555556. While hyperparameters were not tuned on the holdout, we explicitly note the epistemological limitation that the challenge set was previously inspected under the earlier unencoded-zone baseline (WAPE 0.523879, MAE 7.3315).

## How to run

The system exposes guide-mandated offline entry points that execute within standard terminal environments without external network connectivity. All scoring commands rebuild required model components dynamically from public input data, enforce a two-thread hardware constraint, and output strictly formatted predictions. Run the standard pipeline commands from the repository root:

```bash
# Train and serialize rebuild metadata from public data directory:
python train.py --data-dir ../hack-day-lucknow-datasets/p3-ward-civic-demand --out models/

# Generate offline demand predictions for an arbitrary input grid:
python predict.py --data-dir ../hack-day-lucknow-datasets/p3-ward-civic-demand --grid ../hack-day-lucknow-datasets/p3-ward-civic-demand/prediction_grid_template.csv --output output.csv

# Execute local verification and smoke tests:
python -m unittest discover -s tests -v

# Export static frontend visualization assets:
python -m citysight.export_demo --data-dir ../hack-day-lucknow-datasets/p3-ward-civic-demand --out-dir frontend/public/data
```

## Use of AI tools

Generative AI coding assistants (including Antigravity, Gemini, Codex, and Claude) were employed during project development to analyze dataset schemas, assist in drafting scikit-learn regression pipelines, generate comprehensive edge-case unit test suites, and format documentation tables. All AI-suggested code was subjected to strict verification gates, including synthetic leak-injection tests, numeric precision audits, and offline execution validation. AI tools were not permitted to fabricate validation scores, bypass spatial group splits, or access live external networks during scoring runs.

## Data & licences

The dataset consists of ward-level civic grievances, administrative attributes, and geospatial polygons supplied for the Hack Day Lucknow Ward Pulse challenge (Problem 03). The participant dataset does not disclose the source city. Ward geometries and census attributes are treated as read-only competition inputs. Data redistribution rights have not been confirmed, and no project code license file was found in this repository; do not assume permission to publish either data or code.

## Team

The CitySight engineering team consists of dedicated engineers responsible for civic analytics, ML architecture, pipeline validation, and user interface development:
- **Lead ML & Systems Engineer**: Core offline scoring CLI implementation, scikit-learn model architecture, spatial cross-validation design, and test automation.
- **Geospatial & Frontend Engineer**: MapLibre vector visualization, offline static export contracts, accessible user interface engineering, and data integrity audits.

---

## Planning and Architecture Documentation

Detailed architectural records and audit reports are maintained in the repository:
- [Implementation Blueprint](docs/planning/00_IMPLEMENTATION_BLUEPRINT.md) — Architectural decisions (ADRs) and scope boundaries.
- [Phase Execution Specification](docs/planning/01_EXECUTION_SPEC.md) — Exact phase ownership and verification gates.
- [Contracts and Evaluation](docs/planning/02_CONTRACTS_AND_EVALUATION.md) — Scorer, metric, and artifact wire contracts.
- [Acceptance and Operations](docs/planning/03_ACCEPTANCE_AND_OPERATIONS.md) — Test matrix and security boundaries.
- [Reverification Report](docs/research/10_REVERIFICATION_REPORT.md) — Direct data findings and input SHA-256 fingerprints.
- [Decisions Log](docs/decisions.md) — Model selection comparisons and frozen split parameters.
- [Error Analysis](docs/error_analysis.md) — Residual distributions, spatial variations, and ranking limitations.
- [Implementation Status](docs/implementation/STATUS.md) — Execution ledger and phase completion status.
- [Issues Register](docs/implementation/ISSUES.md) — Defect tracking and resolution evidence.
- [Frontend run and verification notes](frontend/README.md) — Offline static UI commands and outstanding dependency/browser gates.
