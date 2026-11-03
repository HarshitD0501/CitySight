# CitySight phase execution specification

Status: PROPOSED. Follow [architecture](00_IMPLEMENTATION_BLUEPRINT.md), [contracts](02_CONTRACTS_AND_EVALUATION.md), and [acceptance](03_ACCEPTANCE_AND_OPERATIONS.md). Every phase below is a separate user-controlled step. The master prompt governs pause/resume and error reports.

## Phase 0 / D0 — Verify context and establish the foundation

**Prerequisites:** initial handoff only; do not start D1. **Ownership:** README planning index, proposed `docs/implementation/STATUS.md`, `docs/implementation/ISSUES.md`, runtime/dependency planning and project metadata.

Read all authoritative plans and guide pp. 2–6, 13–15, 22–26. Inspect current files/Git status; preserve existing changes and untracked documentation. Recheck input hashes and schemas against the audit. Confirm Python 3.11 and local Node availability; find a compatible patched Next.js/React/MapLibre/TypeScript set and scikit-learn >=1.6 with NumPy for Python 3.11. Inspect official package metadata before selecting exact pins; verify clean dependency resolution in an isolated local environment if network/access allows. Record unavailable checks and do not invent compatibility. An implementation environment may install justified project dependencies; never upgrade global tools automatically.

Create the phase/issue ledger, record selected versions and COV-1 as a local assumption. Record that current event eligibility, starter schema/team metadata and public data rights remain external questions. These do not prevent local development. Do not contact organizers, publish data, add application modules or build future-phase UI. Do not change global Git trust settings; command-scoped safe-directory handling for this known path is sufficient if necessary.

**Gate:** paths/scope, dependency decision and validation outcome, issue register and next phase are explicit; no unresolved incompatibility required by D1 is hidden. Mark PASS, PARTIAL or BLOCKED accurately. **Rollback:** remove only task-owned temporary environments if needed; preserve existing files. **Stop:** report D0 and wait for user **continue**. If blocked, a later continue resumes D0 until its gate passes.

## Phase 1 / D1 — Input validation and count construction

**Prerequisite:** D0 PASS and a new user continue. **Ownership:** `src/citysight/data/`, input types, `tests/test_data.py`, necessary import/bootstrap configuration and documented runtime/dev pins. No model search or frontend.

Implement streaming CSV validation, string ID normalization, timestamp/numeric parsers, COV-1 coverage grid, aggregations and geometry structural checks. Use the exact contracts; preserve raw input hashes. Test sparse input, zero cells, null status, duplicate keys, empty grid, nonfinite/malformed numeric values, percent/comma parsing and ward join failures. Prefer synthetic fixtures committed as small code-defined tests; do not commit copied challenge tables.

**Gate:** targeted data tests pass and real-input audit reproduces documented counts/IDs or records changed input hashes and explains differences. **Rollback:** revert only D1 edits; never alter raw files. **Stop:** required phase report and wait.

## Phase 2 / D2 — Baselines, candidate and honest evaluation

**Prerequisite:** D1 PASS and new continue. **Ownership:** `src/citysight/features/`, `models/`, `evaluation/`, local evaluation command, `tests/test_evaluation.py`, proposed `docs/decisions.md` and `docs/error_analysis.md`.

Persist challenge IDs; run CM and K5 baselines, then at most the specified HGB candidate if resources permit. Implement fold-safe transforms, shared fit/predict functions, metric edge cases and deterministic selection. Disable candidate row-level early stopping. Do not compute challenge results until selection freezes. Write local metric files ignored by Git and summarize actual results in Markdown.

**Gate:** meaningful leakage tests, split checks, metric tests and baseline comparisons pass; selected method and actual results are recorded. Tests must show that altering held-out labels does not affect corresponding training predictions. A candidate that loses can be explicitly rejected without failing the phase; a broken required baseline cannot. Baseline-only completion must be justified. **Rollback:** restore selected baseline/config and rerun affected checks. **Stop:** report results, rejected candidate errors and unresolved issues; wait.

## Phase 3 / D3 — Scoring CLI, packaging and local export

**Prerequisite:** D2 PASS and new continue. **Ownership:** root `predict.py`, `train.py`, `submission.yaml`, pinned `requirements.txt`, `tests/test_smoke.py`, scorer tests, `src/citysight/artifacts.py`, export command, artifact schema tests and generated-data ignore rules. Frontend data folder may be created; application UI waits for D4.

Implement guide-mandated entry points using the selected method and shared library. Scoring must rebuild from supplied data; no saved ward answer dependency. Provide local evaluation/export commands with documented paths. Generate all static artifact contracts, publish manifest last and validate provenance. Build a valid manifest from the guide, label starter-schema validation unavailable if starter is absent, and do not invent team/token values. Create an uppercase `README.md` via an intentional case-only rename of existing `Readme.md` for Linux evaluator compatibility; preserve planning links and supply required sections. Each required heading has at least 20 words; unknown metrics/team facts are explicitly unavailable, not fabricated.

**Gate:** scorer handles actual, shuffled, subset, empty and changed valid grids; changed labels affect applicable runtime fits; repeats are deterministic. Invalid inputs fail without publishing partial new output. Train rebuild and smoke test pass. Artifact/schema/fit-ID checks pass. Local time/memory are measured; exact sandbox verification may remain explicitly unverified until D5. **Rollback:** restore prior config or regenerate versioned artifacts; keep old valid output/build until new publication validates. **Stop:** report gate and wait.

## Phase 4 / D4 — Accessible offline frontend

**Prerequisite:** D3 PASS and new continue. **Ownership:** `frontend/app/`, `frontend/components/`, `frontend/lib/`, local CSS and frontend tests/package lock. The later explicit user request authorizes Cesium 3D under amended ADR-03/08, with Leaflet fallback. No paid basemap, web backend, account system, allocation simulator or interval feature.

Implement the static Next.js page, validated manifest loader and artifact parsing, Cesium default globe and Leaflet fallback lifecycles, month/category filters, stable selection details, searchable table and reserved-ward challenge. The 2026-11-04 corrected ADR-03/08 amendment defines the pinned online engine, optional OSM context, real tilt/top/globe cameras and fullscreen. Separate observations from estimates. Engine/WebGL failures select the 2D map; imagery failures preserve local polygons; geometry/map exceptions leave the table reachable. Use system fonts, keyboard controls, visible focus, responsive layout and reduced-motion behavior.

**Gate:** lint/types/build pass for chosen versions; browser checks cover filter/detail equality, no-data, partial coverage labels, challenge subset/full metrics, missing/corrupt artifacts, timeout/retry, no WebGL and offline cold load from local HTTP. Record commands, browser and results; if browser unavailable, do not call the UI verified. **Rollback:** revert D4 edits or retain known-good exported build. **Stop:** show unresolved UI defects and wait.

## Phase 5 / D5 — Final integration and operational handoff

**Prerequisite:** D4 PASS and new continue. **Ownership:** integration tests, local CI/check scripts if justified, docs/runbook, results and guide-required packaging. No external scoring run, push, publication or deployment is automatically authorized.

Rebuild from pinned dependencies; execute the acceptance matrix. Test the CLI in the guide's offline/read-only CPU/RAM/time conditions when the environment supports enforcement. Record unavailability as a release limitation, not a pass. Rehearse the 8-minute guide presentation (1.5-minute problem, 3.5-minute features, 3-minute Q&A) and local fallback. Record actual performance and error analysis. Scan tracked files for forbidden data/answers and secrets before any proposed release. Maintain the same verified model/configuration and provenance for all published claims.

**Gate:** mandatory tests pass; no open P0/P1 defect invalidates core demo/scoring behavior. Unavailable sandbox/organizer checks yield PARTIAL local release readiness and BLOCKED official submission readiness, not COMPLETE official release. Never use a user's continue to bypass a failed gate. **Rollback:** retain last verified build/config; regenerate affected outputs after any data/config change. **Stop:** final report with unresolved issues; do not begin optional enhancements. When all local gates pass, mark local implementation complete and list external gates separately.
