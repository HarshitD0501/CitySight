# CitySight Issue and Defect Register

**Status:** ACTIVE  
**Last Updated:** Phase D1 (2026-11-02)

| Issue ID | Type | Severity | Phase | Description | Reproduction / Command | Expected | Actual | Evidence / Error Text | Status | Affected Gates | Recommended Next Action |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **ISSUE-01** | ERROR | P2 | D0 | Default PATH `python` points to a virtual environment without pip / scientific libraries | `python -m pip list` | Execution of pip package listing | `No module named pip` | `C:\Users\harsh\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe: No module named pip` | **RESOLVED** | D0, D1 | Resolved by using Windows Python launcher `py -3.11` pointing to `C:\Users\harsh\AppData\Local\Programs\Python\Python311\python.exe` (Python 3.11.9, numpy 2.3.5, scikit-learn 1.8.0, scipy 1.17.0). |
| **ISSUE-02** | LIMITATION | P3 (local) / P0 (official) | D0 | Live organizer scoring queue access, team token, and starter schema unavailable | N/A (External service) | Official live evaluation queue access | Local-only verification environment | Guide PDF specifies live evaluator queue during event window; not present in local workspace | **OPEN** | D5 (Official release only) | Retain local-only release readiness boundary; do not block local D1–D5 implementation. |
| **ISSUE-03** | LIMITATION | P3 | D0 | Public dataset redistribution rights and unassigned wards (3 and 65) status unconfirmed | N/A | Clarification from dataset owner | Data remains local only | Raw files contain 198 wards in features/geometries, 156 in grievances, 40 in targets, 2 unassigned (3, 65) | **OPEN** | D1, D3, D5 | Strictly keep dataset out of git repository; enforce gitignore for raw and generated data tables. |
| **ISSUE-04** | LIMITATION | P2 | D0 | Potential git global configuration warning under restricted sandbox identity | `git status` | Clean status without global config warnings | Possible config warning under sandbox | Reverification report noted global config warning under sandbox runner | **OPEN** | D0–D5 | Use local command-scoped configurations where necessary; do not modify global user git config. |

---

### Resolution Notes
* **ISSUE-01:** Workaround confirmed effective. `py -3.11` executes scikit-learn 1.8.0 and numpy 2.3.5 correctly, including `GroupKFold` with `shuffle=True, random_state=42` and `HistGradientBoostingRegressor(loss='poisson')`. All future python scripts and tests will invoke `py -3.11`.

### Current sandbox follow-up

- **ISSUE-05 — ERROR / P1 / OPEN for dependency downloads:** `npm view next ...` returned EACCES; pip dry-run found no available distributions; direct PyPI HTTPS diagnosis returned WinError 10013 (socket access denied). Retrying pip with `--isolated` did not fix access. No matching public npm cache entries were found. Future frontend resolution remains unverified; this does not block standard-library D1 work. Next action: validate/install dependencies in an authorized network-enabled setup before D4; do not claim the old frontend candidate versions are security-reviewed.
- **ISSUE-06 — ERROR / P2 / RESOLVED by verified command workaround:** `py -3.11` reports `No installed Python found!` under this sandbox identity. Direct invocation of `C:\Users\harsh\AppData\Local\Programs\Python\Python311\python.exe` successfully reports the recorded Python/NumPy/scikit-learn/SciPy versions. This overrides the earlier launcher command recommendation for this sandbox only.
- **ISSUE-07 — ERROR / P2 / OPEN but unused:** repeated setup created a project `.venv/`; its offline installation was interrupted and scikit-learn is absent there. Metadata check confirmed NumPy 2.4.2, SciPy 1.17.1, joblib 1.5.3 and threadpoolctl 3.6.0, but not scikit-learn. Do not use this incomplete environment. The existing direct Python executable removes any need to repair it for D1. No destructive cleanup was performed.
- **ISSUE-04 update:** `git -c safe.directory=<CitySight-absolute-path> -c core.excludesFile= ...` successfully reads status and confirms `.venv/` and `.phase0/` are ignored, without a global-config warning or persistent configuration changes.

### Phase D1 findings

- **ISSUE-08 — BUG / P1 / RESOLVED:** the first real-input audit failed at `ward_features.csv: row 123: population_density_2011_persons_sq_km has invalid thousands separators`. The initial parser accepted international comma grouping but rejected valid Indian formatting present in the data. Expected: parse `1,18,059` as 118059 while rejecting malformed groupings. Fix: explicit Indian grouping validation alongside international grouping, with regression fixtures. Verification: final 35-test suite passed, the complete audit passed, and real-input totals/hashes were rechecked successfully. No D1 gate remains affected.
- **D1 review hardening:** added deterministic count ordering, portable zero-padded early-year handling and graceful rejection of duplicate JSON keys/extreme coordinates. These were review improvements verified by regression tests, not separately observed production bugs.
- **Open environment issues remain:** ISSUE-05 (download access restrictions) and ISSUE-07 (unused incomplete `.venv`). D1 uses the verified explicit system Python executable and needs no package downloads. No new unresolved D1 error/bug was found.

