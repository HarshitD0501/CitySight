"""Deterministic ward-grouped model selection and one-time challenge evaluation."""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from citysight.data.types import CATEGORIES, CountTable, InputDataset
from citysight.evaluation.metrics import category_ranking_metrics, regression_metrics
from citysight.models.baselines import category_month_means, fit_k5

TARGET_MONTHS = tuple(f"{year:04d}-{month:02d}" for year in (2024, 2025)
                      for month in range(1, 13) if (year, month) <= (2025, 6))


def challenge_split(wards: tuple[str, ...] | list[str], n: int = 12) -> tuple[str, ...]:
    if n <= 0 or n >= len(set(wards)):
        raise ValueError("challenge size must be positive and smaller than ward count")
    unique = set(wards)
    return tuple(sorted(sorted(unique, key=lambda w: (
        hashlib.sha256(f"citysight-challenge-v1:42:{w}".encode("utf-8")).digest(), w))[:n]))


def _scores(actual: list[float], predicted: list[float]) -> dict[str, object]:
    return regression_metrics(actual, predicted)


def _fit_predict_hgb(dataset: InputDataset, train: tuple[str, ...], requests: list[tuple[str, str, str]]):
    from citysight.models.poisson_hgb import fit_hgb, predict_hgb
    fitted_months = tuple(m for m in dataset.counts.months if m in TARGET_MONTHS or m not in TARGET_MONTHS)
    estimator, encoder, all_missing = fit_hgb(
        dataset.counts, train, dataset.features, dataset.counts.months, CATEGORIES,
    )
    exact, category = category_month_means(dataset.counts, train)
    fallback = dict(exact)
    fallback.update({(cat, "__category__"): value for cat, value in category.items()})
    values, clamps = predict_hgb(estimator, encoder, dataset.features, requests, fitted_months, fallback)
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("HGB produced a nonfinite or negative prediction")
    return values, {"all_missing_columns": list(all_missing), "negative_prediction_clamps": clamps}


def _evaluate_candidate(dataset: InputDataset, folds: list[tuple[tuple[str, ...], tuple[str, ...]]], method: str):
    from citysight.models.baselines import category_month_means
    actual_all: list[float] = []
    predicted_all: list[float] = []
    fold_results = []
    failures = []
    for fold_index, (train, valid) in enumerate(folds, 1):
        req = [(w, m, c) for w in valid for m in TARGET_MONTHS for c in CATEGORIES
               if (w, m, c) in dataset.counts.counts]
        actual = [float(dataset.counts.counts[key]) for key in req]
        try:
            if method == "cm":
                exact, category = category_month_means(dataset.counts, train)
                pred = [exact.get((c, m), category.get(c, 0.0)) for _, m, c in req]
            elif method == "k5":
                k5 = fit_k5(dataset.counts, train, dataset.features)
                pred = [k5(w, m, c) for w, m, c in req]
            else:
                pred, _ = _fit_predict_hgb(dataset, train, req)
            actual_all.extend(actual)
            predicted_all.extend(pred)
            fold_results.append({"fold": fold_index, "validation_wards": len(valid), **_scores(actual, pred)})
        except Exception as exc:  # candidate failure is reported, never silently replaced
            failures.append({"fold": fold_index, "error": f"{type(exc).__name__}: {exc}"})
            fold_results.append({"fold": fold_index, "validation_wards": len(valid), "status": "FAILED"})
    if failures:
        return {"status": "FAILED", "folds": fold_results, "failures": failures,
                "pooled": None, "pooled_wape": None}
    pooled = _scores(actual_all, predicted_all)
    return {"status": "PASS", "folds": fold_results, "pooled": pooled,
            "pooled_wape": pooled["wape"]}


def evaluate_dataset(dataset: InputDataset, *, challenge_size: int = 12, include_hgb: bool = True) -> dict[str, Any]:
    from sklearn.model_selection import GroupKFold

    wards = tuple(dataset.counts.observed_wards)
    challenge = challenge_split(wards, challenge_size)
    development = tuple(w for w in wards if w not in set(challenge))
    splitter = GroupKFold(n_splits=5, shuffle=True, random_state=42)
    folds = []
    # Dummy X is deliberately ward-level: group split is independent of labels and row counts.
    for train_idx, valid_idx in splitter.split(development, groups=development):
        folds.append((tuple(development[i] for i in train_idx), tuple(development[i] for i in valid_idx)))
    results = {name: _evaluate_candidate(dataset, folds, name) for name in ("cm", "k5")}
    if include_hgb:
        results["hgb"] = _evaluate_candidate(dataset, folds, "hgb")
    valid_baselines = [(r["pooled_wape"], name) for name, r in results.items()
                       if name in ("cm", "k5") and r["status"] == "PASS" and r["pooled_wape"] is not None]
    if not valid_baselines:
        raise RuntimeError("all baseline candidates failed; see candidate errors")
    baseline_score, selected = min(valid_baselines, key=lambda x: (x[0], x[1] != "cm"))
    hgb = results.get("hgb")
    if hgb and hgb["status"] == "PASS" and hgb["pooled_wape"] is not None:
        wins = sum((fold.get("wape") is not None and results[selected]["folds"][i].get("wape") is not None
                    and fold["wape"] < results[selected]["folds"][i]["wape"])
                   for i, fold in enumerate(hgb["folds"]))
        if hgb["pooled_wape"] < baseline_score and wins >= 3:
            selected = "hgb"
    # Freeze selection before touching challenge labels for metric computation.
    challenge_requests = [(w, m, c) for w in challenge for m in TARGET_MONTHS for c in CATEGORIES
                          if (w, m, c) in dataset.counts.counts]
    train_all = development
    if selected == "cm":
        exact, category = category_month_means(dataset.counts, train_all)
        challenge_pred = [exact.get((c, m), category.get(c, 0.0)) for _, m, c in challenge_requests]
    elif selected == "k5":
        k5 = fit_k5(dataset.counts, train_all, dataset.features)
        challenge_pred = [k5(w, m, c) for w, m, c in challenge_requests]
    else:
        challenge_pred, _ = _fit_predict_hgb(dataset, train_all, challenge_requests)
    challenge_actual = [float(dataset.counts.counts[key]) for key in challenge_requests]
    per_cat = {}
    for cat in CATEGORIES:
        ids = [i for i, key in enumerate(challenge_requests) if key[2] == cat]
        per_cat[cat] = regression_metrics([challenge_actual[i] for i in ids], [challenge_pred[i] for i in ids])
    totals_a: dict[str, dict[str, float]] = {cat: defaultdict(float) for cat in CATEGORIES}
    totals_p: dict[str, dict[str, float]] = {cat: defaultdict(float) for cat in CATEGORIES}
    for (ward, _, category), actual, pred in zip(challenge_requests, challenge_actual, challenge_pred):
        totals_a[category][ward] += actual
        totals_p[category][ward] += pred
    overall = regression_metrics(challenge_actual, challenge_pred)
    overall.update(category_ranking_metrics(totals_a, totals_p))
    return {
        "schema_version": 1,
        "protocol": {"coverage_policy": dataset.counts.coverage_policy,
                     "challenge_algorithm": "sha256:citysight-challenge-v1:42:<ward_id>",
                     "challenge_wards": list(challenge), "development_wards": len(development),
                     "folds": 5, "seed": 42, "target_months": list(TARGET_MONTHS),
                     "source_hashes": dict(dataset.source_hashes)},
        "selection": {"selected_method": selected, "baseline_method": min(valid_baselines)[1],
                      "candidate_rule": "lower pooled WAPE and wins at least 3/5 folds",
                      "candidate_results": results},
        "challenge": {"fit_wards": len(development), "evaluated_once": True,
                      "metrics": overall, "category_metrics": per_cat,
                      "predictions": [{"ward_id": w, "month": m, "category_group": c,
                                       "actual_count": a, "predicted_count": p}
                                      for (w, m, c), a, p in zip(challenge_requests, challenge_actual, challenge_pred)]},
    }


def main() -> int:
    import argparse
    from citysight.data import load_inputs
    parser = argparse.ArgumentParser(description="Run local ward-held-out model evaluation")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output", default="artifacts/evaluation.json")
    parser.add_argument("--skip-hgb", action="store_true", help="run baselines only")
    args = parser.parse_args()
    dataset = load_inputs(args.data_dir)
    result = evaluate_dataset(dataset, include_hgb=not args.skip_hgb)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temp.replace(path)
    print(f"selected={result['selection']['selected_method']} challenge_wape={result['challenge']['metrics']['wape']} output={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
