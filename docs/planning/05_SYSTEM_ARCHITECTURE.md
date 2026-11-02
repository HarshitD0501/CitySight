# CitySight system architecture

The authoritative decisions are in [the blueprint](00_IMPLEMENTATION_BLUEPRINT.md) and interfaces in [the contracts](02_CONTRACTS_AND_EVALUATION.md). This overview replaces the previous static-only scoring proposal.

There are two execution paths: the evaluator invokes the offline Python CLI to rebuild from supplied public data and predict the supplied grid; the presenter serves a locally built static Next.js map/table from locally generated aggregate artifacts. They share model/data logic and provenance but run independently. No runtime web API, database or hosted model server is required.

Source files stay in the sibling organizer folder. Proposed Python ownership is `src/citysight/` plus root `train.py` and `predict.py`; frontend ownership is `frontend/`; tests live in `tests/`. Generated model/data/build outputs are ignored by Git. COV-1 and partial-period labels apply everywhere.

Do not implement the earlier optional FastAPI routes, use a saved ward-month answer table for scoring, or assume that UI reveal keeps downloaded actuals secret. See [the phase specification](01_EXECUTION_SPEC.md) before implementation. Phase advancement requires a new user continue after each passing phase.
