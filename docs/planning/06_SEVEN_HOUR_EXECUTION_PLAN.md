# CitySight phase checkpoints

The filename is retained for existing links. Earlier seven-hour/three-hour schedules and commit instructions are superseded. The guide schedules its 31 October 2026 hacking window from 10:00 to 16:30; a future event's schedule is unverified. There is no current user-approved three-hour execution deadline.

Use [D0–D5 in the execution specification](01_EXECUTION_SPEC.md). The initial handoff authorizes D0 only. After each phase, save status/issues and end the turn. A new user continue authorizes at most one phase; a failed gate keeps the same phase active.

Dependency order: environment/contracts → validated data → model evaluation → scoring CLI/artifacts → frontend → final integration. No UI work bypasses unverified data/scoring contracts. No optional feature displaces a failed core gate.

Scope cuts: retain a verified baseline if the candidate loses or fails its documented optional gate; retain a usable table when WebGL fails; omit 3D, intervals, allocation and external services. Record all errors, rejected experiments and unverified checks in the visible phase report. No automatic commits, pushes or deployments are authorized by this document.
