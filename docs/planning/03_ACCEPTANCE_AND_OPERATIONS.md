# CitySight acceptance, security and operations

Status: PROPOSED verification criteria. No checks here have passed merely because they are listed. Read [contracts](02_CONTRACTS_AND_EVALUATION.md) before implementing them.

## Acceptance matrix

| ID | Required scenario | Evidence / gate |
|---|---|---|
| A01 | Public-file hashes, schemas and IDs rechecked | commands/results in phase ledger; differences explained |
| A02 | Null status preserved; invalid category/time/key rejected | data tests and concise errors |
| A03 | Comma/percentage numeric fields parsed consistently | fixtures such as `3,182` and `59.10%`; malformed nonempty value rejected |
| A04 | COV-1 zeros apply only to observed source wards and covered source months | sparse synthetic fixture; no labels created for target/unassigned wards |
| A05 | Challenge excluded before CV; each fold ward-disjoint; transforms/neighbors train-only | split assertions and held-out-label mutation test |
| A06 | CM/K5/HGB selection uses the specified rule | measured pooled/fold WAPE; challenge not used for selection |
| A07 | WAPE zero denominator, Spearman ties/constants and top-k ties | small hand-computed metric fixtures; null plus reason for undefined |
| A08 | Dynamic scorer actual/shuffled/subset/empty/different data inputs | CLI tests; exact supplied keys/header/order, finite nonnegative values, repeat determinism |
| A09 | Partial-output failure, read-only data, missing output permission | failure test; nonzero exit; input hashes unchanged |
| A10 | Guide packaging | pinned requirements, manifest, entry points, smoke test and exact README headings |
| A11 | Artifact validation/provenance | all file run IDs/schema versions/fit IDs agree; stale mixed files rejected |
| A12 | Main map, table and selection agree for same filters | actual browser verification with observed/estimate/no-data labels |
| A13 | Challenge reveal/full versus filtered metrics | recompute displayed values from same artifact records; no secrecy claim |
| A14 | Keyboard, contrast, small screen and no-data/error states | manual keyboard pass and browser checks; color not sole indicator |
| A15 | Cold local load with network disabled; forced WebGL failure | no remote assets required; table accessible |
| A16 | Sandbox limits | enforced 2 CPU, 4 GB, no network, permitted writes and <600-second runtime or explicit UNVERIFIED |
| A17 | Rebuild and model provenance | same inputs/config/environment reproduce predictions; actual version and hashes recorded |
| A18 | Repository hygiene and honest handoff | no raw challenge data or answer tables committed; open issue register shown in final report |

A candidate model is optional. A P0 evaluator/data/leakage failure cannot be waived by a phase continuation. A user-approved deferred enhancement must be removed from claimed acceptance scope; do not relabel broken core behavior as optional. If checks cannot run, name the command, reason and effect on readiness.

## Security and privacy boundaries

Inputs are local files, not uploads or user sessions. Parse as data only: no eval, shell interpolation, untrusted pickle loading, remote manifest paths or injected HTML. React displays feature names as text; MapLibre popups must use text nodes or escaped content. Render no complaint-level records in browser artifacts. Model parameters, logs and generated artifacts contain no team token or credential. Use least-privilege local paths and avoid modifying raw files.

All data/artifact/manifest paths resolve under intended input/output roots. Do not write to input folders, traverse manifest paths out of `data/`, or fetch runtime remote code. Package downloads belong to an explicit setup/build step with trusted registries and pinned compatible versions. Do not delete other work, reset Git or change global safe-directory settings. User changes/untracked docs are preserved.

There is no auth system for the local static demo. Adding authentication would require a changed scope, not automatically improve this release. Public redistribution and hosted publication are gated by data rights. Do not infer an MIT data license from a proposed code license or organizer encouragement to open-source code.

## Runtime and resource behavior

The scorer validates early, aggregates complaints in a streaming pass, uses one final selected fit per invocation, limits numerical-library threads to two and writes only approved output/temp paths. Fixed model iteration limits avoid unlimited tuning. Logs contain stage, elapsed time and error class; no raw records. No retry loops for deterministic errors. Failing model fitting or nonfinite output exits nonzero rather than silently substituting fake values.

A frontend artifact request has a visible loading state and 10-second timeout; users can retry manually. Geometry/WebGL failure preserves validated table data. All artifact metadata is versioned; old and new run data cannot be combined. No background workers, service worker, mutable server cache or database backup is needed. Store source hashes/configuration and keep known-good local builds for recovery.

## Local build and recovery

D3 documents training/scoring/export commands. D4 documents locked frontend install, lint/type/build and serving its exported `out/` directory over localhost HTTP (not `file://`). Bind the demo server to loopback by default. Under the corrected 2026-11-04 ADR-03/08 amendment, Cesium renders a default 3D globe and Leaflet is the 2D fallback. The pinned Cesium CDN script, stylesheet and engine workers/assets require internet for uncached startup; integrity/download/WebGL failures select Leaflet. Street tiles require internet; Leaflet Streets off and tile failure retain local polygons and values. In 3D, imagery failure retains the globe and local overlays. Keep OSM attribution visible on both renderers, preserve browser caching/Referer and never prefetch tiles for offline use. Verify both renderers against shared filters, selection and challenge values. The local table remains available throughout 3D startup/recovery.

Retain the last verified exported build and its manifest locally. If new assets fail schema or hash checks, retain the old build, fix the exporter, then regenerate the complete run. Do not manually edit prediction JSON to hide a bug. Rebuild after model/data/coverage changes. A screen recording is accepted as a fallback by the guide, but does not establish new runtime verification.

No hosting provider or paid service is selected. No database migration, TLS configuration or live deployment is part of these phases. Public hosting requires a new plan covering dataset redistribution permission, access needs, TLS/security headers, immutable asset deployment, logging/privacy, budget and rollback. Document local-only readiness separately from official submission eligibility and public production readiness.

## Required issue and phase records

Implementation creates `docs/implementation/STATUS.md` and `docs/implementation/ISSUES.md`. The former records active/completed phase, gate status, authorization checkpoint, exact commands/results, files changed, versions and next dependency-ready phase. The latter uses stable issue IDs and columns: type (BUG/ERROR/BLOCKER/LIMITATION), severity, phase, reproduction, expected/actual, evidence, attempted fixes, current status, affected gates and recommended next action. Never mark an issue fixed without a rerun result.

Every phase response includes **Unresolved errors/bugs**, even when the answer is “None found in the checks executed.” List blockers and checks not run separately so missing access is not mistaken for a software defect. If a bug cannot be fixed within the current phase, explain the attempted fixes, leave it open and set the affected gate to PARTIAL or BLOCKED. The user must see this without opening a log file.
