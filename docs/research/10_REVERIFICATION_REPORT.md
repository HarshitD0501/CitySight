# CitySight reverification and corrections

Reverified 2026-11-02 against the local files and official technical references. This report records evidence; it does not claim application or model tests have passed. VERIFIED means inspected source/file output; PROPOSED means a selected design default; INFERRED means supported interpretation; UNVERIFIED means no confirming evidence; BLOCKED names the action needing external input.

## Repository and environment baseline

VERIFIED: `CitySight/` is the Git repository; its parent workspace is not. Git history has one initial commit, `7ecc874`, with an empty `Readme.md`. Planning files are untracked; do not remove them as disposable files. No application source, model files, manifests, lockfiles, tests, CI or deployment definitions were present during this audit. Accordingly, feature implementation and resource/model verification remain pending. These absences are not evidence of broken software.

VERIFIED environment outputs: Python 3.11.9, Node v22.22.3 and npm 11.11.0. Import inspection found no NumPy, SciPy, scikit-learn, pandas or Shapely in the invoked Python environment. No dependency was installed or upgraded during this planning audit. Package compatibility/patch-security checks must be executed in implementation D0.

The participant PDF was read using `C:\Program Files\Git\mingw64\bin\pdftotext.exe` with page ranges 2–6, 13–15 and 22–26. This tool was already present; older documentation saying no extractor existed was incorrect.

## Direct data findings

Method: read source CSV files as UTF-8-sig with Python 3.11 standard-library `csv.DictReader`; parse timestamps; count IDs, categories, months and aggregated keys; inspect JSON geometry structure; compute SHA-256 from bytes. These are reproducible inspections, not model benchmarks.

| Fact | Result | Status / limit |
|---|---|---|
| Complaint records | 556,561; 556,561 unique complaint IDs | VERIFIED; unique IDs also exclude exact duplicate full rows |
| Observed wards / target wards | 156 / 40, intersection empty | VERIFIED |
| Features / geometries | 198 / 198, unique equal ward-ID sets | VERIFIED; every observed and target ward joins |
| Other wards | IDs 3 and 65 | VERIFIED; not training zeros or targets |
| Target grid | 4,320 unique keys = 40 wards × 18 months × 6 categories | VERIFIED full Cartesian product |
| Target months | 2024-01 through 2025-06 | VERIFIED |
| Source time span | 2020-02-08 01:01:00 to 2025-06-19 12:59:00; 65 calendar months | VERIFIED; complete collection coverage not established |
| Invalid timestamps / duplicate complaint IDs | 0 / 0 | VERIFIED for the supplied local snapshot |
| Null status | 56; other complaint fields nonempty | VERIFIED; status is not a count filter |
| Category counts | electrical 225,303; solid_waste 137,975; roads 92,458; animals_health 40,355; other 34,689; trees 25,781 | VERIFIED |
| Raw categories / subcategories | 32 / 181 | VERIFIED; model uses the six grouped categories |
| Count-grid structure | 50,526 nonempty cells; 10,314 absent cells in 156 × 65 × 6 = 60,840 | VERIFIED combinatorics; treating absence as zero is COV-1, a PROPOSED assumption |
| Monthly coverage evidence | 155 or 156 wards have records each source month; June 2025 includes all 156 | VERIFIED presence, not proof of completeness |
| Geometry structure | 195 Polygon, 3 MultiPolygon; 204 closed rings, each at least four positions; finite positions | VERIFIED structural checks; topology/intersections not tested |
| Bounding box | lon 77.460103–77.784051; lat 12.834012–13.143666 | VERIFIED; guide says WGS84; no original-source lookup is needed |
| Features | 30 columns; only `police_stn` has empty cells (112) | VERIFIED |
| Numeric formatting | density values include commas; growth rates include percent suffixes | VERIFIED; requires explicit parsers |
| Key numeric ranges | population 21,171–95,368; area 0.3–30.5 km²; road length 13–453 km | VERIFIED descriptive ranges; no causal claim |

Source attribution as a particular city beyond the guide's undisclosed-source wording is unnecessary. Do not seek original grievance data; the guide forbids it.

### Input fingerprints

These identify this snapshot, not an immutable rule for changed evaluator inputs.

| Input | Bytes | SHA-256 |
|---|---:|---|
| `grievances_public_wards.csv` | 51,708,844 | `f2a9efb91705a0984acdafaab60b883018b210dcf06adcf15dcf09f0c59ecdec` |
| `ward_features.csv` | 42,308 | `48322fd942b66a235062dd75f6f1faefc741afcc844178a6df0459ba5c560a1c` |
| `wards.geojson` | 995,378 | `200ba14f7663c3d8992f703156e1e346b2572d63a6325c004eeed3e6d3be99e8` |
| `prediction_grid_template.csv` | 94,566 | `13bd4427ef2fb6b51476cc161b5c528418d244bf1702003cf9e07fce40364646` |
| `sample_submission.csv` | 198 | `004cf13cbab025dbc84d4919dd4fd17dfc258666a1f22b20b3452eed7a887f35` |
| `Participant_Guide_Detailed.pdf` | not used as data input | `762107c2c30c0b8fb7179274bbb7a01ee32b1cfb23eb6dce3bddd29da312752e` |

## Organizer requirements verified from the local PDF

- Pages 2–6: offline CPU sandbox, read-only except /output and /tmp, Python manifest example, pinned requirements, entry point/train/smoke-test files, exact README headings with at least 20 words each, repository limits. No challenge-data commits.
- Pages 13–15: spatial cold-start P3; dynamic `predict.py --data-dir --grid --output`; grid rows may be shuffled; 10 minutes, 2 CPU, 4 GB, no network; finite nonnegative output. Primary WAPE, secondary mean Spearman and top-25% recall; five validation runs, 20-minute cooldown; audit tolerance 0.03 WAPE.
- Page 15: external grievance data for the city is disqualifying; committed ward-month answer tables are flagged. Static demo data must therefore be locally generated and excluded from Git.
- Pages 22–26: 8-minute presentation (1.5/3.5/3-minute phases), recording fallback, rubric, no hidden-data probing, original-source-data prohibition, AI tool disclosure and event-produced-code rule.
- Page 3 schedules 31 October 2026, 10:00–16:30 hacking. The old three-hour plan is not an organizer requirement. Future event applicability is UNVERIFIED. The guide's model score bands are organizer examples/estimates; page 14 lists an excellent WAPE estimate of 0.38, while page 24's normalization anchor is 0.36. These are different contexts, neither a measured CitySight result.

Exact evaluator tie/rounding code and current starter repository were not supplied. Local diagnostic conventions are specified in the contracts and must not be presented as verified evaluator source behavior.

## Research evidence ledger

Accessed 2026-11-02. Primary sources only. Online stable documentation can change; implementation must confirm APIs against its selected pinned versions.

| Source / section | What was verified | Restriction / decision |
|---|---|---|
| [GroupKFold parameters](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html) | nonoverlapping groups; shuffle/random_state added in 1.6 | use compatible >=1.6 pin; actual install untested |
| [scikit-learn common pitfalls: leakage](https://scikit-learn.org/stable/common_pitfalls.html) | preprocessing must learn from training data; pipelines help | explicit neighbor/target aggregation boundaries still needed |
| [HistGradientBoostingRegressor: loss and early_stopping](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html) | Poisson objective and automatic early-stopping behavior | disable automatic row split; bounded optional candidate, no claimed benefit |
| [Haversine distances](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.haversine_distances.html) | angular distance input convention | latitude/longitude in radians for K5; GeoJSON coordinates remain longitude/latitude |
| [Next.js static exports](https://nextjs.org/docs/app/guides/static-exports) | output export emits static files; server-only features unsupported | frontend needs no web API; version-compatible client lifecycle required |
| [MapLibre GeoJSON source](https://maplibre.org/maplibre-gl-js/docs/API/classes/GeoJSONSource/) | GeoJSON source rendering and update API | no performance guarantee inferred |
| [MapLibre glyphs](https://maplibre.org/maplibre-style-spec/glyphs/) | style text can require referenced assets | neutral fill/line style with no remote fonts or symbols |
| [RFC 7946 §§3–4](https://datatracker.ietf.org/doc/html/rfc7946) | geographic coordinate/ring conventions | structural checks do not certify topology |
| [Python 3.11 CSV](https://docs.python.org/3.11/library/csv.html) and [os.replace](https://docs.python.org/3.11/library/os.html#os.replace) | structured CSV writing; replacement operation | use same output filesystem; handle permissions/failure |
| [WCAG 2.2 quick reference](https://www.w3.org/WAI/WCAG22/quickref/) | keyboard, focus and non-color accessibility requirements | manual/browser checks required; no conformance claim from this plan |

No current third-party globe repository/license claims are needed by the chosen architecture; unverified historical claims about such reuse were removed.

## Document audit and actual corrections

| Document | Original gap / inconsistency | Reverified action |
|---|---|---|
| `Readme.md` | initially empty; then only a redirect notice | replaced with project status, canonical reading order and limitations |
| `docs/planning/05_SYSTEM_ARCHITECTURE.md` | static-only scoring ambiguity, optional FastAPI/routes | reconciled to separate offline scorer and static frontend; removed runtime API alternative |
| `docs/planning/06_SEVEN_HOUR_EXECUTION_PLAN.md` | filename, 180-minute content and guide schedule disagree; ungrounded commit instruction | retained path as historical name, replaced schedule with D0–D5 gated sequence |
| `docs/planning/07_TESTING_AND_ACCEPTANCE.md` | fixed 4,320 row scoring rule, incomplete sandbox/error cases | now delegates to supplied-grid contracts and detailed acceptance matrix |
| `docs/planning/08_DEMO_AND_JUDGING_STRATEGY.md` | rubric called inaccessible; presentation timing incomplete | uses actual guide metric/rubric/presentation and honest result conventions |
| `docs/research/01_DATASET_FORENSICS.md` | obsolete no-extractor claim; zero reconstruction needed assumption | replaced by current verified summary and audit fingerprints, explicit COV-1 |
| `docs/research/02_ML_RESEARCH_AND_VALIDATION.md` | ambiguous candidate list/selection, challenge contamination risk, seeded split version issue | fixed two baselines/one candidate and pooled selection, separate holdout and fit IDs |
| `docs/research/03_GEOSPATIAL_AND_3D_RESEARCH.md` | unsupported upstream globe claims, external asset dependencies | focused local MapLibre and table fallback; no external code reuse |
| `docs/research/04_PRODUCT_AND_UX_STRATEGY.md` | optional scenario treated as part of demo in other docs | core estimate/observation/challenge scope, enhancements explicitly deferred |
| `docs/research/09_CRITICAL_REVIEW.md` | stale rubric and ownership findings | refreshed risk matrix and present limitations |
| `docs/planning/00_IMPLEMENTATION_BLUEPRINT.md` | broad stop rules blocked local work on unknown rights/coverage | scoped external gates; explicit reversible COV-1 assumption for local work |
| `docs/planning/01_EXECUTION_SPEC.md` | vague steps, missing empty/fallback/error and phase control | defined D0–D5 ownership, gates, rollback and mandatory pauses |
| new `docs/planning/02_CONTRACTS_AND_EVALUATION.md` | missing exact artifact/metric/model details | central contracts and deterministic defaults |
| new `docs/planning/03_ACCEPTANCE_AND_OPERATIONS.md` | distributed/partial test and failure expectations | consolidated test matrix, security and local recovery |
| `MASTER-IMPLEMENTATION-PROMPT.md` | could run all phases; failures not guaranteed visible | initial D0 only; explicit continuation per phase; mandatory visible error/bug reports |
| new `docs/research/10_REVERIFICATION_REPORT.md` | evidence and corrections lacked a consolidated record | source fingerprints, official references, actual corrections, unknowns and readiness ratings |

The second-pass review also corrected missing comma/percentage parsing, HGB's automatic row-validation risk, full-fit versus held-out artifact mixing, lack of observed-count artifacts, unclear stale-data handling, and Windows filename casing for the Linux-required README. These are planning fixes; no application bug was reproduced because no application exists yet.

## Priority matrix

| ID / type | Evidence and impact | Fix / verification | Priority / dependencies |
|---|---|---|---|
| P-01 requirement gap | no evaluator program; static data insufficient | D1–D3, dynamic grid CLI tests | P0; D0 |
| P-02 potential correctness risk | grouped rows and target-derived neighbors can leak | reserved challenge, fold-local transforms, mutation tests | P0; D1–D2 |
| P-03 modeling assumption | incomplete boundary periods, absent cells | COV-1 disclosure; organizer clarification before official claims | P1 local; official-release gate |
| P-04 input risk | numeric punctuation, null status and joins | typed parsers, sparse/invalid fixtures | P0; D1 |
| P-05 integration risk | stale/mixed artifact runs or fits | versioned manifest, fit IDs, schema validation | P1; D3 |
| P-06 runtime risk | CPU/RAM/offline/read-only constraints untested | bounded fitting and enforced sandbox test | P0 official release; D3/D5 |
| P-07 UI risk | WebGL/offline/keyboard failures | neutral local assets, accessible table and browser checks | P1; D4 |
| P-08 scope drift | 3D, intervals, allocation, backend | defer pending new scoped request | P3 |
| P-09 reporting risk | failures omitted or work advances automatically | pause protocol, persistent issues, visible unresolved errors | P0 workflow; every phase |
| P-10 enhancement | deeper spatial/temporal error analysis | only after core metrics and constraints pass | P2; D2/D5 |

No effort estimates or numeric model-quality promises are supported by measured implementation evidence.

## Material unknowns and defaults

| Unknown | Default / available choices | What is blocked |
|---|---|---|
| Complete observation coverage / partial June meaning | use disclosed COV-1 local extract-count interpretation; organizer may replace policy | verified full-month-demand claim; official scoring interpretation until confirmed |
| Guide applicability / event-produced-code rule | treat as local reconstruction/demo; check rules if entering an event | eligibility and actual external submission |
| Starter manifest, team metadata/token | derive manifest fields from guide; never invent identifiers; check starter when available | actual schema-check submission |
| Redistribution rights | keep data/generated answers local and ignored; publish code only when authorized | public data/demo-host publication |
| Compatible exact dependency pins | verify official metadata and clean resolution in D0 | claims of reproducible runnable environment until checked |
| Exact sandbox | measure locally; enforced CPU/memory/offline run in D5 when available | verified evaluator readiness if enforcement unavailable |
| Topology and browser rendering | structural geometry checks done; actual rendering and optional topology check later | verified map behavior until D4 |
| Evaluator tie and undefined-metric implementation | documented local diagnostic conventions | claim of exact secondary-metric parity |

No credential or organizer answer is required for the next agent to start local Phase 0.

## Readiness assessment

These ratings distinguish a written specification from demonstrated implementation.

| Area | Rating | Evidence / remaining work |
|---|---|---|
| Requirements | READY for local demo specification | user scope + guide contracts; official-event applicability external |
| Architecture | READY as proposed design | decisions, boundaries and no-server scope defined |
| AI/ML design | READY as proposed evaluation design | splits, baselines/candidate, selection and limitations fixed; no model trained |
| Backend/API contracts | READY for CLI/static interface specification | exact entry/output/artifact contracts; no web API needed |
| Frontend/UI | READY as behavior specification | states, labels, keyboard/table and offline failure handling; not rendered |
| Data/database | READY with disclosed COV-1 | source audit and parsers specified; no DB; coverage is not verified truth |
| Security | PARTIALLY READY | local controls specified; dependency and runtime validation pending |
| Testing/evaluation | READY as acceptance specification | A01–A18 concrete checks; implementation tests/results absent |
| Deployment | PARTIALLY READY for local execution | build/recovery specified; no sandbox/build verification and no public deployment |
| Implementation roadmap | READY | D0–D5 prerequisites, ownership, gates, pauses and visible issue reporting |

Overall: ready to start D0 locally. No claim that the system works, satisfies sandbox limits, achieves quality targets or is production-ready is supported yet.

## Final documentation checks

All 16 CitySight Markdown files were read or rewritten during this review. A read-only Python check found no broken relative Markdown links, unbalanced fenced blocks or Unicode replacement characters. The source fingerprints and geometry/feature uniqueness checks were rerun. The required phase-control and visible unresolved-error clauses were checked in the master prompt. Application tests were not run because no application exists; dependencies were not installed.

Manual control-flow review: initial handoff stops after D0; a passed phase without a new user instruction remains stopped; one continuation advances at most one phase; PARTIAL/BLOCKED continuation resumes the same phase; a quoted continue grants no permission; missing authorization history waits for clarification. These are reviewed prompt instructions, not a guarantee of another model's compliance.

Nonblocking environment warning: Git could not read the global ignore file under the sandbox identity. Read-only repository status/log inspection succeeded using a command-scoped safe-directory setting. No global setting was changed. Recheck this environment behavior in D0 if it affects staging/hygiene checks.
