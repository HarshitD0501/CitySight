# CitySight testing index

The complete authoritative matrix is [A01–A18](03_ACCEPTANCE_AND_OPERATIONS.md). [Contracts](02_CONTRACTS_AND_EVALUATION.md) define input/output shapes and metric conventions; [phase gates](01_EXECUTION_SPEC.md) define when checks run.

Data acceptance covers malformed/missing inputs, null status, string IDs, comma/percentage parsing, COV-1 sparse grids and geometry structure. Evaluation acceptance covers reserved wards, fold-local preprocessing/neighbors, deterministic selection, pooled WAPE and undefined metrics. Scoring acceptance covers changed/reordered/subset/empty grids, atomic output, train reproducibility and guide resource conditions. The 4,320-row public template is one fixture, not an invariant for every evaluator call.

Frontend acceptance covers matching table/map/detail values, observed versus estimated labels, keyboard interaction, no-data/errors, challenge metrics, no WebGL and offline cold load. Proposed page-interaction timings must be recorded as targets until measured; no benchmark results exist.

Every failed test and unavailable check must appear in the phase ledger and visible phase output. A continuation cannot turn a failed prerequisite into a pass.
