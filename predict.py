#!/usr/bin/env python3
"""CitySight offline prediction entry point.

Usage:
    python predict.py --data-dir {public_dir} --grid {grid_csv} --output {output_csv}
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
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

from citysight.data import load_inputs, read_grid
from citysight.data.types import DataValidationError
from citysight.models.pipeline import fit_model, predict_model


def run_predict(data_dir: str, grid_path: str, output_path: str) -> int:
    grid_p = Path(grid_path).resolve()
    out_p = Path(output_path).resolve()
    data_p = Path(data_dir).resolve()

    if not grid_p.is_file():
        sys.stderr.write(f"Error: Grid file not found: {grid_p}\n")
        return 1

    if not data_p.is_dir():
        sys.stderr.write(f"Error: Data directory not found: {data_p}\n")
        return 1

    # Ensure output directory exists or can be written to
    out_dir = out_p.parent
    if not out_dir.is_dir():
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            sys.stderr.write(f"Error: Cannot create output directory {out_dir}: {exc}\n")
            return 1

    # Load and validate grid
    try:
        raw_grid = read_grid(grid_p)
    except DataValidationError as exc:
        sys.stderr.write(f"Error validating grid: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"Unexpected error reading grid: {exc}\n")
        return 1

    # Fast path for empty grid: write header-only output without fitting
    if not raw_grid:
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile("w", dir=out_dir, delete=False, suffix=".tmp", encoding="utf-8", newline="") as tf:
                temp_file = Path(tf.name)
                writer = csv.writer(tf)
                writer.writerow(["ward_id", "month", "category_group", "predicted_count"])
            os.replace(temp_file, out_p)
            return 0
        except Exception as exc:
            if temp_file and temp_file.is_file():
                temp_file.unlink(missing_ok=True)
            sys.stderr.write(f"Error writing empty grid output: {exc}\n")
            return 1

    # Ingest data from data_dir and exclude grid wards from training counts
    try:
        dataset = load_inputs(data_p, grid_path=grid_p)
    except DataValidationError as exc:
        sys.stderr.write(f"Error validating input data: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"Unexpected error loading dataset: {exc}\n")
        return 1

    # Verify that grid ward IDs exist in features
    for row in dataset.grid:
        if row.ward_id not in dataset.features:
            sys.stderr.write(f"Error: Grid ward {row.ward_id} not found in ward features\n")
            return 1

    # Fit model on all eligible observed wards (wards not in grid)
    training_wards = dataset.counts.observed_wards
    if not training_wards:
        sys.stderr.write("Error: No training wards remaining after excluding grid wards\n")
        return 1

    try:
        fitted = fit_model(dataset.counts, dataset.features, training_wards)
    except Exception as exc:
        sys.stderr.write(f"Error fitting model: {exc}\n")
        return 1

    # Predict in exact supplied grid row order
    requests = [(row.ward_id, row.month, row.category_group) for row in dataset.grid]
    try:
        predictions = predict_model(fitted, dataset.features, requests)
    except Exception as exc:
        sys.stderr.write(f"Error generating predictions: {exc}\n")
        return 1

    # Write output atomically: write to temp file first, then os.replace
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=out_dir, delete=False, suffix=".tmp", encoding="utf-8", newline="") as tf:
            temp_file = Path(tf.name)
            writer = csv.writer(tf)
            writer.writerow(["ward_id", "month", "category_group", "predicted_count"])
            for req, pred in zip(requests, predictions):
                writer.writerow([req[0], req[1], req[2], f"{pred:.4f}"])
        os.replace(temp_file, out_p)
    except Exception as exc:
        if temp_file and temp_file.is_file():
            temp_file.unlink(missing_ok=True)
        sys.stderr.write(f"Error writing output CSV: {exc}\n")
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CitySight offline Ward Pulse demand predictor")
    parser.add_argument("--data-dir", required=True, help="Path to public data directory")
    parser.add_argument("--grid", required=True, help="Path to prediction grid CSV")
    parser.add_argument("--output", required=True, help="Path for output prediction CSV")
    args = parser.parse_args()

    return run_predict(args.data_dir, args.grid, args.output)


if __name__ == "__main__":
    sys.exit(main())

