# CitySight dataset forensics

The current verified counts, schemas, fingerprints, geometry limits and exact inspection methods are recorded once in [the reverification report](10_REVERIFICATION_REPORT.md). Input contracts and COV-1 are in [the contracts](../planning/02_CONTRACTS_AND_EVALUATION.md).

The dataset is spatial cold-start regression, not ordinary future forecasting: 40 target wards have no public complaint records, while their required dates overlap the other wards' history. Observed ward IDs are disjoint from target IDs; wards 3 and 65 are neither. Do not manufacture observed labels for these sets.

The local guide was successfully extracted using the PDF executable bundled with Git. Earlier claims that no extractor was available are superseded. Guide pp. 13–15 explicitly give the WAPE metric, offline runtime CLI and anti-gaming rules.

The source ends on June 19, 2025. Record presence in every observed ward that month does not prove complete coverage. Missing count combinations use the explicitly proposed COV-1 extract-count interpretation for local work. No source-data lookup or external grievance enrichment is permitted. Feature numeric formatting includes commas and percent signs; a generic coercion-to-missing step would lose valid information.

Polygon ring/finite-coordinate/ID checks passed structurally. Topology, overlap and actual browser rendering remain unverified. Supplied Census 2011 attributes are old; reporting counts are not verified incident or unmet-need counts.
