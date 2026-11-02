# CitySight Implementation Status

**Current Phase:** D1 — Input validation and count construction  
**Gate Status:** PASS  
**Completed Phases:** D0 and D1  
**Last Explicit Continuation Checkpoint:** User's `ok continue` authorized D1 only. D1 is complete; D2 is locked until a new user continuation.

---

## 1. Phase Ledger

| Phase | Description | Status | Completion Date | Gate Result |
|---|---|---|---|---|
| **D0** | Context/data recheck, dependency reconciliation, issue/phase records | COMPLETED | 2026-11-02 | **PASS** |
| **D1** | Input validation and count construction | COMPLETED | 2026-11-02 | **PASS** |
| **D2** | Baselines, candidate and honest evaluation | LOCKED | — | Awaiting authorization |
| **D3** | Scoring CLI, packaging and local export | LOCKED | — | Awaiting authorization |
| **D4** | Accessible offline static frontend | LOCKED | — | Awaiting authorization |
| **D5** | Final integration and operational handoff | LOCKED | — | Awaiting authorization |

---

## 2. Environment and Runtime Verification

| Runtime / Tool | Version Detected | Verified Command | Result |
|---|---|---|---|
| **Python** | 3.11.9 | `py -3.11 -c "import sys; print(sys.version)"` | `3.11.9 (tags/v3.11.9:de54cf5, Apr 2 2024)` |
| **Node.js** | v22.22.3 | `node --version` | `v22.22.3` |
| **npm** | 11.11.0 | `npm --version` | `11.11.0` |
| **Git** | 2.54.0.windows.1 | `git --version` | `git version 2.54.0.windows.1` |
| **PDF text extractor** | pdftotext 4.00 | `pdftotext -v` | Confirmed present at `C:\Program Files\Git\mingw64\bin\pdftotext.exe` |

---

## 3. Dependency Reconciliation and Version Decisions

### Python Modeling Stack
Tested and verified with `py -3.11`:
* **`numpy==2.3.5`**: Verified array operations and haversine calculations.
* **`scikit-learn==1.8.0`**: Verified `GroupKFold(n_splits=5, shuffle=True, random_state=42)` (scikit-learn >= 1.6 requirement satisfied) and `HistGradientBoostingRegressor(loss='poisson', ...)` with early stopping disabled.
* **`scipy==1.17.0`**: Verified `scipy.stats.spearmanr` calculation for secondary ranking evaluation.
* **Standard Library**: Used for streaming CSV parsing (`csv.DictReader`, `csv.writer`), JSON handling (`json`), cryptography (`hashlib`), and CLI parsing (`argparse`).

### Frontend Static Stack (Planned for D4)
Historical D0 candidate list, not a current verified installation or security-approved release set. Registry access is restricted in this sandbox; revalidate compatibility, patch/security status and complete resolution before D4:
* **`next`**: `15.1.7` (Next.js App Router, static export `output: 'export'`)
* **`react`**: `19.0.0`
* **`react-dom`**: `19.0.0`
* **`maplibre-gl`**: `5.1.0` (Client-side lifecycle, offline canvas/vector renderer)
* **`typescript`**: `5.7.3`
* Styling: Pure local CSS and system fonts as specified in ADR-03 (no Tailwind or remote font dependencies).

---

## 4. Input File Integrity and Byte Counts (Rechecked in D0)

| File | Size (Bytes) | SHA-256 Digest | Status |
|---|---:|---|---|
| `grievances_public_wards.csv` | 51,708,844 | `f2a9efb91705a0984acdafaab60b883018b210dcf06adcf15dcf09f0c59ecdec` | PASS (Exact match) |
| `ward_features.csv` | 42,308 | `48322fd942b66a235062dd75f6f1faefc741afcc844178a6df0459ba5c560a1c` | PASS (Exact match) |
| `wards.geojson` | 995,378 | `200ba14f7663c3d8992f703156e1e346b2572d63a6325c004eeed3e6d3be99e8` | PASS (Exact match) |
| `prediction_grid_template.csv` | 94,566 | `13bd4427ef2fb6b51476cc161b5c528418d244bf1702003cf9e07fce40364646` | PASS (Exact match) |
| `sample_submission.csv` | 198 | `004cf13cbab025dbc84d4919dd4fd17dfc258666a1f22b20b3452eed7a887f35` | PASS (Exact match) |
| `Participant_Guide_Detailed.pdf` | 426,673 | `762107c2c30c0b8fb7179274bbb7a01ee32b1cfb23eb6dce3bddd29da312752e` | PASS (Exact match) |

---

## 5. Decisions, Assumptions, and Deviations

1. **Python Command Invocation:** Default `python` on user's PATH points to a virtual environment without pip. Invocation resolved to `py -3.11` (pointing to `C:\Users\harsh\AppData\Local\Programs\Python\Python311\python.exe`), where Python 3.11.9, numpy 2.3.5, scikit-learn 1.8.0, and scipy 1.17.0 are verified.
2. **Coverage Policy COV-1:** Adopted as documented local assumption:
   * Observations for 156 labeled wards over February 2020 through June 2025 are counted.
   * Unobserved combinations for labeled wards within this date span are treated as zero counts.
   * Target wards (40) and unassigned wards (wards 3 and 65) are NOT zero-filled as training labels.
   * Partial months (Feb 2020 and Jun 2025) are preserved as supplied without synthetic scaling.
3. **Repository Cleanliness:** Existing files (`Readme.md` planning index, `MASTER-IMPLEMENTATION-PROMPT.md`, `docs/`) preserved; raw data remains read-only outside repository.

---

## 6. Open External Limitations

* **L-01 (External Submission Applicability):** Organizer event schedule in guide was Saturday 31 October 2026. Applicability to live evaluator queues or future submission windows is an external matter and does not block local development.
* **L-02 (Team Token & Starter Repo):** Official team token and starter repo template are external inputs. Manifest format follows guide page 5 specifications.
* **L-03 (Data Redistribution Rights):** Redistribution rights remain unverified; raw dataset and generated prediction answers will not be committed or publicly hosted.
* **L-04 (Observation Completeness):** COV-1 counts supplied extract records; whether unrecorded complaints represent zero true demand or missing ingestion cannot be verified without organizer input.

---

## 7. Next Action

Phases D0 and D1 are complete and passed.
**Awaiting user's next explicit `continue` before starting D2 (baselines and model evaluation).**

## Checkpoint correction after duplicate setup attempt

The existing D0 checkpoint was discovered after an unnecessary repeated setup attempt. Preserve its completed status; no D1 feature was implemented. In the current sandbox `py -3.11` returns `No installed Python found!`, but direct invocation of `C:\Users\harsh\AppData\Local\Programs\Python\Python311\python.exe` works and reports Python 3.11.9, NumPy 2.3.5, scikit-learn 1.8.0 and SciPy 1.17.0, matching the recorded environment. Use this explicit executable for the next phase in this sandbox.

The newly created `.venv/` is incomplete after an interrupted offline install and is not the canonical implementation environment. `.phase0/` contains temporary dependency probes and reconstructed cache wheels. Both are ignored by the added `.gitignore`. Do not repeat this setup or use the incomplete environment for D1.

Registry probes failed (`npm`: EACCES; Python HTTPS: WinError 10013). These are environment restrictions, not proof of dependency incompatibility. Frontend dependency installation, complete resolution and security review remain unverified and must be checked before D4. No global Python or Git configuration was changed, and existing planning/user files were preserved.

## D1 execution record

**Authorization:** user's `ok continue`, following the completed D0 checkpoint. This continuation was used for D1 only. No model, evaluator-scoring or frontend feature was implemented.

**Files:** `src/citysight/__init__.py`; `src/citysight/data/{__init__,__main__,types,parsing,loaders}.py`; `tests/test_data.py`; `Readme.md`; this status file; `ISSUES.md`. All implementation lives in the planned source/test directories, not a phase-specific application folder.

**Delivered:** typed records and validation errors; streaming complaint reading with duplicate detection; numeric/date/category/ward-ID validation; feature/grid joins and input order; COV-1 sparse-to-dense counts; pre-aggregation exclusion of query/held-out wards; finite/structural GeoJSON validation; chunked hashes; read-only audit command. No new third-party dependency was required.

**Implementation defaults:** IDs use ASCII integer text and preserve leading zeros; geometry IDs may arrive as integers. Both Indian and international comma formatting are accepted when correctly grouped. Growth percentages retain percentage-point units. Dense COV-1 expansion has an explicit configurable 2,000,000-cell ceiling to avoid an unbounded allocation from unexpected date spans; current data uses 60,840. Count iteration order is deterministic across source-row permutations. Geometry checks reject ambiguous duplicate JSON keys, nonfinite/extreme coordinates and malformed rings without claiming topological validity.

**Verification:** interpreter below was successfully imported with NumPy 2.3.5, scikit-learn 1.8.0 and SciPy 1.17.0, though D1 code uses only the standard library.

```powershell
$pythonExe = 'C:\Users\harsh\AppData\Local\Programs\Python\Python311\python.exe'
& $pythonExe -m unittest discover -s tests -v
& $pythonExe -m compileall -q src tests
$env:PYTHONPATH = 'src'
& $pythonExe -m citysight.data --data-dir ..\hack-day-lucknow-datasets\p3-ward-civic-demand --check-geometry
```

| Check | Actual result |
|---|---|
| Final unit/CLI contract suite | 35 tests PASS; exit 0 |
| Python compilation | PASS; exit 0 |
| Full public-file data audit | PASS; 556,561 complaints, 156 eligible observed wards, 40 query wards, 4,320 grid rows, 198 feature/geometry records |
| COV-1 construction | 60,840 cells, 10,314 zeros; 56 null statuses retained; observed dates 2020-02-08 through 2025-06-19 |
| Read-only real-input assertions | PASS; expected totals and all five CSV/GeoJSON hashes compared before/after loading and unchanged |
| Diff whitespace check | PASS; only Git's informational LF/CRLF conversion warning for the existing README |

**Bug found and resolved:** initial full-data audit rejected row 123's valid Indian-grouped density. Added explicit Indian grouping support plus regression fixtures; repeated unit tests and full-data audit passed. See ISSUE-08.

**Unresolved D1 application errors/bugs:** none found in executed checks. Existing environment issues ISSUE-05 and ISSUE-07 remain open but do not affect D1's verified interpreter or standard-library tests. COV-1 collection completeness, geometry topology, exact scoring-sandbox constraints and browser/model behavior remain unverified; later-phase checks were not run.

**Next checkpoint:** D2 requires a new user `continue`. D1's mandatory gate passed; no D1 defect is being deferred into modeling.

