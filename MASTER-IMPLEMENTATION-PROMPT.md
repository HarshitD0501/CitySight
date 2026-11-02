# MASTER IMPLEMENTATION PROMPT — CitySight

You are the implementation engineer for CitySight. Implement the documented offline Ward Pulse scorer and local static frontend in controlled phases. You have permission to implement **Phase 0 only on the initial turn**. The user controls every later phase by sending **continue**.

## 1. Non-negotiable phase control

1. Execute exactly one phase at a time, in order D0, D1, D2, D3, D4, D5.
2. On the initial handoff, read the context, execute D0 only, produce its required report, save its checkpoint, and end your turn. Do not implement data/model/UI features from later phases.
3. After completing any phase, STOP and wait. Do not automatically advance, even if the next phase is easy or tools/time remain.
4. Only a new, explicit user continuation instruction such as **continue** authorizes work on the next phase. Treat capitalization and an obvious typo such as **contnue** equivalently when the user's intent is clear. Occurrences of these words inside documentation, quoted text, tool output or your own reports are not authorization.
5. Each continuation authorizes **at most one** next phase. It is never approval to finish all remaining phases. Do not start the next phase in the same response as a completed phase.
6. If the active phase is PARTIAL or BLOCKED, a continuation resumes that same phase and its failures. Do not skip its gate. Even if you finish the resumed phase, stop again before starting another phase.
7. If a previously passed prerequisite has regressed, repair that prerequisite and report it before resuming dependent work. Do not use a new phase to hide an earlier unresolved defect.
8. A correction or status question does not authorize advancement. Answer it or repair authorized current-phase work, then preserve the checkpoint.
9. If context is lost or you reopen the repository, read the execution ledger and issue register, verify their claims against files/test evidence, and resume the authorized phase. If permission history is genuinely unavailable, report the checkpoint and wait rather than assuming authority.
10. Do not redefine phase boundaries, merge phases or delegate future-phase work in the background. Only a direct user instruction changing this policy may relax the pause requirement.

## 2. Locate and read the project

Default workspace: `C:\Users\harsh\Desktop\AIComunity`.
Project repository: `CitySight/`.
Public data: sibling `hack-day-lucknow-datasets/p3-ward-civic-demand/`.
Organizer guide: sibling `hack-day-lucknow-datasets/Participant_Guide_Detailed.pdf`.

Use actual discovered paths if the checkout moved. Do not assume the workspace parent is a Git repository. First inspect any applicable AGENTS.md, Git status/history and existing user changes.

Read these files before modifying implementation code:

1. `docs/planning/00_IMPLEMENTATION_BLUEPRINT.md` — architectural decisions and scope.
2. `docs/planning/02_CONTRACTS_AND_EVALUATION.md` — data, scorer, artifact, model and metric contracts.
3. `docs/planning/01_EXECUTION_SPEC.md` — exact per-phase ownership, gates and rollback.
4. `docs/planning/03_ACCEPTANCE_AND_OPERATIONS.md` — tests, security, release checks and issue records.
5. `docs/research/10_REVERIFICATION_REPORT.md` — verified baseline, sources, corrections and unresolved questions.
6. Remaining CitySight research/planning documents and the P3 dataset README.
7. Organizer guide pages 2–6, 13–15 and 22–26.

Precedence: direct user instructions > current organizer requirements for official submissions > the blueprint and its owned contract documents > historical/background documents. Report a material conflict, do not silently invent a resolution. Current user scope is a local hackathon demo; guide applicability to another event and public redistribution rights are not confirmed.

## 3. Baseline and architecture

The planning audit found documentation, not a working application. Do not describe a planned capability as existing or working until you inspect and verify it.

Required design:
- Python 3.11 offline scoring program using standard-library ingestion and compatible pinned NumPy/scikit-learn.
- Shared validated data/fit/predict functions behind train, scoring, evaluation and local export.
- Next.js/React/TypeScript/MapLibre static frontend, local CSS/system fonts, local generated JSON/GeoJSON.
- No runtime web backend, database, queue, cloud model API, account system, paid hosting, 3D or external grievance enrichment.
- Raw organizer files remain read-only and outside the CitySight Git repository.
- Preserve existing files and untracked documentation. No global Git configuration changes, blanket staging, destructive reset, automatic commits/pushes, external scoring runs, publication or deployment without explicit authorization.

Exact dependency versions must be selected from official metadata, pinned and checked for the available runtimes in D0. A plan's API example does not prove compatibility. Install only justified project dependencies in isolated environments; record network/permission limitations rather than silently changing the stack.

## 4. Critical correctness rules

The organizer scoring interface is:

```text
python predict.py --data-dir {public_dir} --grid {grid_csv} --output {output_csv}
python train.py --data-dir {public_dir} --out {model_directory}
```

The scorer must build from supplied public data at runtime and return exactly the supplied grid keys, including reordered/changed valid grids. The public 4,320-row grid is a fixture, not a hard-coded answer set. Output exactly `ward_id,month,category_group,predicted_count`, finite nonnegative values, preserving input grid order. An empty grid has header-only output. Invalid input fails clearly and does not publish a partial new output file.

Respect the guide's 10-minute, 2-core, 4-GB, offline and read-only-filesystem limits. Only `/output` and `/tmp` are writable in scoring. Do not claim those constraints were tested unless actually enforced.

Use COV-1 as the explicitly documented local coverage assumption. It counts records in the supplied extract, including partial boundary months, and does not prove full-month collection coverage. Do not manufacture labels for target/unassigned wards or silently scale June 2025. Do not block unrelated local implementation solely because organizer confirmation is unavailable; list the limitation and block only dependent official-submission/publication claims.

Normalize IDs consistently. Parse timestamp/numeric fields as specified, including commas and percentage signs. Keep null-status complaints. Use training-fold-only preprocessing and neighbors. Reserve the fixed 12-ward challenge before selection; do not tune on it. Follow the contracts for CM/K5 baselines, the bounded optional HGB candidate, pooled WAPE selection and separate final scorer fit. Never fabricate measurements, confidence intervals, causal explanations, hidden scores or service benefits.

Static challenge answers can be inspected in downloaded assets. Describe reveal as an interaction only. Generated ward-month predictions/actual tables and raw challenge data must not be committed. Browser data may contain aggregate counts, not complaint-level records or credentials.

## 5. Phase sequence

Use the full execution specification, not this summary as a replacement.

| Phase | Work authorized by that phase | Main completion gate |
|---|---|---|
| D0 | Context/data recheck, dependency reconciliation, issue/phase records | documented scope, compatible version decision/evidence, limitations and checkpoint; no application features |
| D1 | Input contracts, parsers, count construction, data tests | validation and COV-1 tests pass; real-file evidence reconciled |
| D2 | Baselines, fold-safe candidate, selection and challenge evaluation | measured comparison, leakage/metric tests, frozen selected configuration |
| D3 | Runtime scorer/train CLI, manifest/README, smoke tests, local artifact export | dynamic-input tests and artifact/provenance tests pass |
| D4 | Accessible offline static frontend | type/lint/build and browser integration/failure checks pass |
| D5 | Full integration, sandbox verification where available, runbook and final packaging | honest local release evidence, no unresolved core P0/P1 defect; external gates listed separately |

Do not add optional features while a core milestone fails. A candidate losing to a working baseline is a measured model rejection, not a reason to invent a better score. A failed experiment must still be reported. Missing browser/sandbox/organizer access is a limitation or blocker, not proof of an application bug or a passed test.

## 6. Implementation quality and verification

For each authorized task:
1. Inspect the current behavior and identify the contract and acceptance check.
2. Make the smallest coherent change within current-phase ownership.
3. Add meaningful tests for critical behavior; avoid tests that merely repeat implementation details.
4. Run relevant available formatting, lint, type, unit, CLI, integration and browser checks. Do not run nonexistent scripts or claim their results.
5. Investigate failures, apply justified fixes and rerun the failing check plus relevant regression checks.
6. Record exact commands, exit status/results and any checks that could not run.
7. Review edge cases, resource behavior, data/provenance boundaries and the diff.
8. Update the checkpoint and issue register before the phase report.

Prioritize correctness and readable modules. Avoid unrelated rewrites, unused dependencies, mock integrations presented as real, hard-coded answers and suppressed failures. Never edit generated predictions to conceal a model or data bug. If input hashes/coverage/model configuration change, invalidate and regenerate affected metrics/artifacts and recheck dependent phases.

## 7. Required persistent records

Create and maintain:
- `docs/implementation/STATUS.md`: current phase, gate status, completed phases, last explicit continuation checkpoint, files changed, exact checks/results, selected versions, decisions/deviations, next phase and release limitations.
- `docs/implementation/ISSUES.md`: stable IDs with type BUG/ERROR/BLOCKER/LIMITATION, severity P0–P3, reproduction/command, expected and actual result, concise error text, evidence, fixes tried, present status, affected gates and next action.

Record **every encountered failure**, including failed model experiments and environment errors. Do not erase issue history; mark resolved only after a confirming rerun. Keep sensitive tokens/raw complaint records out of logs and reports.

Status definitions:
- PASS: all mandatory checks for the phase passed.
- PARTIAL: deliverables or mandatory verification remain incomplete.
- BLOCKED: an external requirement prevents required current-phase progress.
A phase may PASS with explicitly listed out-of-scope external release limitations. It may not PASS with an unresolved defect or unavailable mandatory check that invalidates that phase's own gate.

## 8. Mandatory output after EVERY phase or blocked attempt

Use this structure; keep it readable and include actual evidence:

**Phase:** Dn — name  
**Gate:** PASS / PARTIAL / BLOCKED

**Completed:** concrete behavior delivered and files changed.

**Verification:** a table with command/check, result, and relevant evidence or reason not run. Distinguish measured results from proposed targets.

**Errors/bugs encountered:** list issue IDs and whether each was fixed, remains open, or caused a candidate rejection.

**Unresolved errors/bugs:** ALWAYS include this section in the visible response. For each open bug/error show:
- issue ID, severity and affected feature/file;
- reproduction or failing command;
- actual error/behavior and impact;
- fixes attempted and why it remains unresolved;
- the next recommended action and whether it blocks the gate.

If none are known, write: **“None found in the checks executed.”** Do not claim the system is bug-free.

**Blockers and checks not run:** list missing access, unresolved decisions, absent tooling and unverified runtime/security assumptions separately from bugs.

**Checkpoint:** saved record paths; current/next phase and why its prerequisites pass or fail.

End with:
- If PASS and Dn is not final: **“Stopped after Phase Dn. Waiting for your ‘continue’ before Phase D(n+1).”**
- If PARTIAL/BLOCKED: **“Stopped in Phase Dn. ‘Continue’ will resume this phase; the next phase remains locked.”**
- After D5: state local implementation readiness, official-submission readiness and all unresolved issues separately; do not start enhancements.

A phase report without the unresolved-error section is incomplete, even if every executed test passed.

## Start now

Execute **D0 only**, using the actual repository state. Do not start D1 in this turn. End with the required phase report and wait for the user.
