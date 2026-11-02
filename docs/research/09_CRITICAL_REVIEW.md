# CitySight critical review

The full evidence and correction history is [the reverification report](10_REVERIFICATION_REPORT.md). This current review replaces the historical unknown-rubric and unavailable-extractor claims.

| Concern | Finding / action |
|---|---|
| Scoring mismatch | Guide requires dynamic offline rebuild/prediction; static-only submission is invalid |
| Small independent sample | 156 observed wards despite many complaint rows; grouped validation is mandatory |
| Coverage | June ends on the 19th; COV-1 is a disclosed local assumption, not complete monthly observation proof |
| Bias | Reported complaints reflect reporting/service access and vintage attributes; no causal need/impact claim |
| Leakage | Reserve challenge before selection, train-only neighbors/transforms, separate final/demo fits |
| Model proliferation | Two baselines, one optional bounded candidate; no framework menu left to implementer |
| Ranking edge cases | Tie/constant rules are local conventions until evaluator code is available |
| Rendering | Structural geometry checks do not establish topology or WebGL behavior; test table fallback |
| Artifact integrity | Manifest/run/fit IDs prevent stale or full-fit results from masquerading as held-out predictions |
| Anti-gaming | Do not commit answer tables, seek original grievance data or probe hidden data |
| Execution control | Every phase stops; explicit user continue is required; failed gate keeps same phase active |
| Failure disclosure | Every report includes unresolved bugs/errors, attempts and affected gates; no silent pass |
| External readiness | Event eligibility, starter/team metadata and rights affect submission/publication, not local prototyping |

No model scores, latency numbers, deployment claims or package compatibility have been measured yet. The first implementation phase must resolve its own runtime/package prerequisites and record what it cannot verify.
