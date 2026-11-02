# CitySight demonstration and judging

Verified local participant guide pp. 13–15 and 22–26: P3 primary metric is WAPE; mean Spearman is its first tie-break metric, with top-25% recall also reported. The guide allocates 45 points to hidden primary performance, 10 to robustness/secondary performance, 10 to automated hygiene/reproducibility, 5 to code/tests/README, 10 to decisions/error analysis and 20 to presentation. These are guide requirements, not CitySight results.

## Official guide presentation

The 8-minute presentation has 1.5 minutes of problem framing, 3.5 minutes of features and 3 minutes of Q&A. Present a frozen verified commit from the team's laptop; the guide accepts a recording fallback. Future applicability and eligibility remain unverified.

Explain spatial cold-start counts for wards lacking published complaint history. Show one month/category and ward, explicit estimated reported-count labeling, source attributes, and a reserved-ward evaluation reveal. Report actual pooled WAPE and failure slices, distinguish local from evaluator scores, and show a measured baseline comparison. State that partial periods and reporting behavior limit interpretation.

A short pitch: “CitySight estimates the reported complaint counts in wards without public complaint history. We test transfer by reserving complete wards, then show predictions and measured errors beside an offline map.”

The interface reveal is presentation only: downloaded assets include actual aggregate values. No hidden target answers exist in the supplied data. The final scorer fit and held-out demo fit have separate IDs. Do not conflate full-data fitted behavior with held-out evidence.

Use questions to explain ward grouping, fold-safe neighbors, why COV-1 does not prove coverage, which baseline won, what failed, and which checks were unavailable. No claim of optimal staffing, causal impact, guaranteed accuracy, calibrated confidence or official score without evidence. Allocation and intervals remain deferred under the current scope.
