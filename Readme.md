# CitySight

CitySight is an offline ward-demand estimator and static map demo for the Ward Pulse challenge. Phase 1 implements and tests read-only input validation, numeric/date parsing, structural geometry checks and COV-1 complaint-count aggregation. Modeling, scoring and frontend phases remain pending; no model-quality result is claimed.

## Implementation handoff

Give [MASTER-IMPLEMENTATION-PROMPT.md](MASTER-IMPLEMENTATION-PROMPT.md) to the implementation agent. For an existing checkout, read [the saved checkpoint](docs/implementation/STATUS.md) first: D0 and D1 are complete; D2 waits for a new **continue**. A fresh implementation starts with D0. Each continuation authorizes only one phase, subject to its prerequisite checks.

Read the [architecture decisions](docs/planning/00_IMPLEMENTATION_BLUEPRINT.md), [phase specification](docs/planning/01_EXECUTION_SPEC.md), [data and evaluation contracts](docs/planning/02_CONTRACTS_AND_EVALUATION.md), and [acceptance and operations](docs/planning/03_ACCEPTANCE_AND_OPERATIONS.md). The [reverification report](docs/research/10_REVERIFICATION_REPORT.md) records evidence, corrections, unknowns and document status.

The organizer requires an offline Python scoring CLI that builds predictions from the supplied public data and grid. The static frontend is the presentation interface. No web API, database or paid hosting is needed for this scope.

## Current limitations

Zero-filling and partial-month interpretation are documented local evaluation assumptions, not confirmed complete observation coverage. The available guide describes an event on 31 October 2026; its applicability to a future submission is unknown. Public redistribution rights, hidden scores, package compatibility, model quality and resource performance remain unverified. See the reverification report for what these unknowns block.

The implementation agent must replace this index with the guide's required README sections as part of packaging, retaining links to the planning documents and reporting measured results honestly.

## Run the data foundation

This phase uses only Python 3.11's standard library. From the CitySight directory, using the verified interpreter on this Windows workspace:

```powershell
$pythonExe = 'C:\Users\harsh\AppData\Local\Programs\Python\Python311\python.exe'
& $pythonExe -m unittest discover -s tests -v
$env:PYTHONPATH = 'src'
& $pythonExe -m citysight.data --data-dir ..\hack-day-lucknow-datasets\p3-ward-civic-demand --check-geometry
```

On another environment, substitute an available Python 3.11 executable and set PYTHONPATH to the repository's `src` directory for the audit command. The audit prints aggregate checks and fingerprints to stdout; it does not generate answer tables or alter source files. Invalid inputs return exit code 2 with an actionable diagnostic. The data package supports alternate/reordered grids, preserves identifier text and separates query wards from eligible labeled count aggregation.

Numeric parsing accepts international (`118,059`) and Indian (`1,18,059`) comma grouping and explicit percentage-point growth fields. COV-1 is an assumption about recorded counts in the provided extract, including partial source months. Dense expansion is capped at a configurable 2,000,000 cells to reject unexpectedly large coverage ranges before allocating the full count grid; the public data has 60,840 cells.
