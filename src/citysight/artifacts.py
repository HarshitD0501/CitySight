"""Export deterministic static artifacts for local frontend consumption."""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from citysight.data.loaders import load_inputs
from citysight.data.types import CATEGORIES, InputDataset
from citysight.evaluation.runner import TARGET_MONTHS, challenge_split, evaluate_dataset
from citysight.models.baselines import category_month_means
from citysight.models.pipeline import fit_model, predict_model


def _atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + f".tmp.{uuid.uuid4().hex[:8]}")
    try:
        temp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temp.replace(path)
    finally:
        if temp.is_file():
            temp.unlink(missing_ok=True)


def export_artifacts(
    data_dir: str | Path,
    out_dir: str | Path,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Generate and validate all 5 static artifact contracts plus manifest.json."""
    data_path = Path(data_dir).resolve()
    out_path = Path(out_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Load full dataset including geometry
    dataset = load_inputs(data_path, include_geometry=True)

    active_run_id = run_id or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    created_at = datetime.now(timezone.utc).isoformat()

    # 2. Run evaluation to get challenge results, metrics, and challenge fit
    eval_result = evaluate_dataset(dataset, challenge_size=12, include_hgb=True)
    challenge_wards = tuple(eval_result["protocol"]["challenge_wards"])
    challenge_metrics = eval_result["challenge"]["metrics"]
    cv_metrics = eval_result["selection"]["candidate_results"]

    # Fit challenge model (excluding the 12 challenge wards)
    dev_wards = tuple(w for w in dataset.counts.observed_wards if w not in set(challenge_wards))
    challenge_fitted = fit_model(dataset.counts, dataset.features, dev_wards)
    challenge_fit_id = challenge_fitted.fit_id

    # Predict for challenge records
    challenge_requests = [
        (w, m, c) for w in challenge_wards for m in TARGET_MONTHS for c in CATEGORIES
        if (w, m, c) in dataset.counts.counts
    ]
    challenge_preds = predict_model(challenge_fitted, dataset.features, challenge_requests)
    challenge_records = [
        {
            "ward_id": req[0],
            "month": req[1],
            "category_group": req[2],
            "actual_count": float(dataset.counts.counts[req]),
            "predicted_count": float(round(pred, 4)),
        }
        for req, pred in zip(challenge_requests, challenge_preds)
    ]

    challenge_data = {
        "schema_version": 1,
        "run_id": active_run_id,
        "fit_id": challenge_fit_id,
        "challenge_wards": list(challenge_wards),
        "records": challenge_records,
    }

    # 3. Full fit for prediction grid (all observed wards used as training)
    full_fitted = fit_model(dataset.counts, dataset.features, dataset.counts.observed_wards)
    full_fit_id = full_fitted.fit_id

    grid_requests = [(row.ward_id, row.month, row.category_group) for row in dataset.grid]
    full_preds = predict_model(full_fitted, dataset.features, grid_requests)
    prediction_records = [
        {
            "ward_id": req[0],
            "month": req[1],
            "category_group": req[2],
            "predicted_count": float(round(pred, 4)),
        }
        for req, pred in zip(grid_requests, full_preds)
    ]

    predictions_data = {
        "schema_version": 1,
        "run_id": active_run_id,
        "fit_id": full_fit_id,
        "prediction_type": "model_estimate",
        "model_version": "hgb_poisson_v1",
        "records": prediction_records,
    }

    # 4. Observations data (source extract counts for observed wards, COV-1)
    observed_wards_set = set(dataset.counts.observed_wards)
    observation_records = []
    for (ward_id, month, cat), count in dataset.counts.counts.items():
        if month in TARGET_MONTHS:
            observation_records.append({
                "ward_id": ward_id,
                "month": month,
                "category_group": cat,
                "observed_count": count,
            })
    # Sort deterministically
    observation_records.sort(key=lambda r: (r["ward_id"], r["month"], r["category_group"]))

    observations_data = {
        "schema_version": 1,
        "run_id": active_run_id,
        "coverage_policy": "COV-1",
        "records": observation_records,
    }

    # 5. Metrics data
    metrics_data = {
        "schema_version": 1,
        "run_id": active_run_id,
        "selected_method": eval_result["selection"]["selected_method"],
        "full_fit_id": full_fit_id,
        "challenge_fit_id": challenge_fit_id,
        "challenge_metrics": challenge_metrics,
        "category_metrics": eval_result["challenge"]["category_metrics"],
        "cv_results": cv_metrics,
        "limitations": [
            "COV-1 local coverage policy assumes unrecorded complaints are zero counts.",
            "Evaluation focuses on January 2024 - June 2025; June 2025 is potentially partial.",
            "Challenge wards are a deterministic 12-ward proxy split.",
            "Challenge split was evaluated after prior baseline inspection (ISSUE-14 re-evaluation); measurements represent post-fix re-evaluation rather than an unexposed blind holdout.",
        ],
    }

    # 6. Wards GeoJSON data
    if dataset.geometry is None:
        raise ValueError("Geometry document missing from dataset")

    target_wards_set = {row.ward_id for row in dataset.grid}
    geojson_features = []
    for feature in dataset.geometry.get("features", []):
        ward_id = str(feature.get("properties", {}).get("ward_id"))
        feat_obj = dataset.features.get(ward_id)
        name = feat_obj.attributes.get("ward_name") if feat_obj else f"Ward {ward_id}"
        
        if ward_id in target_wards_set:
            status = "target"
        elif ward_id in observed_wards_set:
            status = "observed"
        else:
            status = "unassigned"

        props = {
            "ward_id": ward_id,
            "ward_name": name,
            "ward_status": status,
        }
        if feat_obj:
            for k, v in feat_obj.numeric.items():
                if v is not None:
                    props[k] = v
            for k, v in feat_obj.attributes.items():
                if k not in props and v is not None:
                    props[k] = v

        geojson_features.append({
            "type": "Feature",
            "properties": props,
            "geometry": feature.get("geometry"),
        })

    geojson_data = {
        "type": "FeatureCollection",
        "features": geojson_features,
    }

    # Write the 5 artifact files first
    pred_path = out_path / "predictions.json"
    obs_path = out_path / "observations.json"
    geo_path = out_path / "wards.geojson"
    chal_path = out_path / "challenge.json"
    met_path = out_path / "metrics.json"

    _atomic_write_json(pred_path, predictions_data)
    _atomic_write_json(obs_path, observations_data)
    _atomic_write_json(geo_path, geojson_data)
    _atomic_write_json(chal_path, challenge_data)
    _atomic_write_json(met_path, metrics_data)

    # Validate provenance and schema consistency before publishing manifest
    for p, expected_envelope in [
        (pred_path, predictions_data),
        (obs_path, observations_data),
        (chal_path, challenge_data),
        (met_path, metrics_data),
    ]:
        if not p.is_file():
            raise RuntimeError(f"Missing expected artifact {p.name}")
        with p.open(encoding="utf-8") as f:
            loaded = json.load(f)
            if loaded.get("run_id") != active_run_id:
                raise ValueError(f"Run ID mismatch in {p.name}")
            if loaded.get("schema_version") != 1:
                raise ValueError(f"Schema version mismatch in {p.name}")

    if not geo_path.is_file():
        raise RuntimeError("Missing expected wards.geojson")

    # 7. Write manifest.json LAST
    manifest_data = {
        "schema_version": 1,
        "run_id": active_run_id,
        "created_at": created_at,
        "coverage_policy": "COV-1",
        "source_hashes": dict(dataset.source_hashes),
        "categories": list(CATEGORIES),
        "target_months": list(TARGET_MONTHS),
        "selected_model": "hgb_poisson",
        "full_fit_id": full_fit_id,
        "challenge_fit_id": challenge_fit_id,
        "files": {
            "predictions": "predictions.json",
            "observations": "observations.json",
            "geometry": "wards.geojson",
            "challenge": "challenge.json",
            "metrics": "metrics.json",
        },
    }
    manifest_path = out_path / "manifest.json"
    _atomic_write_json(manifest_path, manifest_data)

    return manifest_data

