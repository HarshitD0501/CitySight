#!/usr/bin/env python3
"""CitySight model training and rebuild entry point.

Usage:
    python train.py --data-dir {public_dir} --out {model_directory}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Enforce 2 CPU threads before importing numerical libraries
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"

# Ensure local src/ is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from citysight.data import load_inputs
from citysight.data.types import DataValidationError
from citysight.models.pipeline import fit_model


def run_train(data_dir: str, out_dir: str) -> int:
    data_p = Path(data_dir).resolve()
    out_p = Path(out_dir).resolve()

    if not data_p.is_dir():
        sys.stderr.write(f"Error: Data directory not found: {data_p}\n")
        return 1

    try:
        out_p.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        sys.stderr.write(f"Error: Cannot create output model directory {out_p}: {exc}\n")
        return 1

    # Load dataset
    try:
        dataset = load_inputs(data_p)
    except DataValidationError as exc:
        sys.stderr.write(f"Error validating input data: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"Unexpected error loading dataset: {exc}\n")
        return 1

    # Fit model on all eligible observed wards
    training_wards = dataset.counts.observed_wards
    if not training_wards:
        sys.stderr.write("Error: No observed wards found to train on\n")
        return 1

    try:
        fitted = fit_model(dataset.counts, dataset.features, training_wards)
    except Exception as exc:
        sys.stderr.write(f"Error fitting model: {exc}\n")
        return 1

    # Save rebuild metadata and configuration
    info = {
        "fit_id": fitted.fit_id,
        "model_name": fitted.model_name,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "training_wards_count": len(fitted.training_wards),
        "fitted_months_count": len(fitted.fitted_months),
        "all_missing_columns": list(fitted.all_missing_columns),
        "feature_encoder": {
            "medians": list(fitted.encoder.medians),
            "zones": list(fitted.encoder.zones),
        },
        "source_hashes": dict(dataset.source_hashes),
        "coverage_policy": dataset.counts.coverage_policy,
    }

    info_path = out_p / "model_info.json"
    temp_info = info_path.with_suffix(info_path.suffix + ".tmp")
    try:
        temp_info.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        temp_info.replace(info_path)
    except Exception as exc:
        if temp_info.is_file():
            temp_info.unlink(missing_ok=True)
        sys.stderr.write(f"Error saving model info: {exc}\n")
        return 1

    print(f"Model successfully trained. Fit ID: {fitted.fit_id}, Output: {info_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CitySight model training and rebuild entry point")
    parser.add_argument("--data-dir", required=True, help="Path to public data directory")
    parser.add_argument("--out", required=True, help="Directory to save model build metadata")
    args = parser.parse_args()

    return run_train(args.data_dir, args.out)


if __name__ == "__main__":
    sys.exit(main())

