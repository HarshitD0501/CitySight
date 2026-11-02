"""Read-only input audit: python -m citysight.data --data-dir PATH."""

import argparse
import json
import sys

from . import CATEGORIES, DataValidationError, load_inputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CitySight source inputs without modifying them.")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--grid", help="Optional supplied grid; defaults to the public template.")
    parser.add_argument("--check-geometry", action="store_true")
    args = parser.parse_args(argv)
    try:
        dataset = load_inputs(args.data_dir, grid_path=args.grid, include_geometry=args.check_geometry)
    except DataValidationError as exc:
        print(f"Input validation failed: {exc}", file=sys.stderr)
        return 2
    counts = dataset.counts
    targets = {row.ward_id for row in dataset.grid}
    summary = {
        "coverage_policy": counts.coverage_policy,
        "coverage_limitation": "Counts describe the supplied extract; complete monthly coverage is unverified.",
        "feature_wards": len(dataset.features),
        "eligible_observed_wards": len(counts.observed_wards),
        "grid_wards": len(targets), "grid_rows": len(dataset.grid),
        "unassigned_wards": sorted(set(dataset.features) - set(counts.observed_wards) - targets),
        "complaint_records": counts.record_count, "null_status_records": counts.null_status_count,
        "months": len(counts.months), "first_timestamp": counts.first_timestamp.isoformat(sep=" "),
        "last_timestamp": counts.last_timestamp.isoformat(sep=" "),
        "count_cells": len(counts.counts), "zero_cells": sum(value == 0 for value in counts.counts.values()),
        "category_counts": {category: sum(value for (_, _, key), value in counts.counts.items() if key == category) for category in CATEGORIES},
        "geometry_features": len(dataset.geometry["features"]) if dataset.geometry is not None else None,
        "source_hashes": dict(dataset.source_hashes),
    }
    print(json.dumps(summary, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
