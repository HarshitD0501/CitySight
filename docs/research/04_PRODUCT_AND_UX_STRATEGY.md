# CitySight product and UX specification

Audience: a hackathon evaluator or teammate inspecting how reported civic complaint counts transfer to wards lacking published history. Core success is an honest prediction/evaluation story and a usable offline interface.

Core view: map plus table, month/category filters and ward detail. Show observed source-extract counts for observed wards, estimates for target wards, and explicit no-data for unassigned wards. Numbers are not incidents prevented, service quality or causal risk. Use a textual legend, restrained colors, keyboard-accessible controls, visible focus, responsive layout and system fonts. Never rely on color alone.

Challenge view: explain reserved wards and the separate fit, show their estimates, then reveal source aggregates and measured errors. Static data is inspectable, so do not claim secrecy. Full versus filtered error metrics are labeled separately and derived from the same records.

Loading, empty, malformed/missing artifact, timeout, offline and WebGL-failure states must be understandable. The searchable table remains available when rendering fails. Do not substitute zeros for unavailable data.

Allocation, calibrated intervals, rate toggles, 3D and operational staffing recommendations are deferred. A future allocation scenario would require explicit assumptions and deterministic arithmetic; it is not part of the current six-phase acceptance scope. See [acceptance](../planning/03_ACCEPTANCE_AND_OPERATIONS.md) for verification.
