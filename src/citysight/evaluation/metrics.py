"""Metrics with explicit edge-case semantics from the project contract."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence


def regression_metrics(actual: Sequence[float], predicted: Sequence[float]) -> dict[str, object]:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("actual and predicted must have the same nonzero length")
    if any(not math.isfinite(float(x)) or float(x) < 0 for x in actual):
        raise ValueError("actual values must be finite and nonnegative")
    if any(not math.isfinite(float(x)) or float(x) < 0 for x in predicted):
        raise ValueError("predictions must be finite and nonnegative")
    absolute = sum(abs(float(a) - float(p)) for a, p in zip(actual, predicted))
    total = sum(float(a) for a in actual)
    return {
        "wape": absolute / total if total else None,
        "wape_undefined_reason": "zero_actual_total" if total == 0 else None,
        "mae": absolute / len(actual),
    }


def _average_ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: (values[i], i))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        rank = ((cursor + 1) + end) / 2.0
        for position in order[cursor:end]:
            ranks[position] = rank
        cursor = end
    return ranks


def _correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) < 2:
        return None
    mx, my = sum(left) / len(left), sum(right) / len(right)
    dx, dy = [x - mx for x in left], [y - my for y in right]
    sx, sy = sum(x*x for x in dx), sum(y*y for y in dy)
    if sx == 0 or sy == 0:
        return None
    return sum(x*y for x, y in zip(dx, dy)) / math.sqrt(sx * sy)


def ranking_metrics(
    actual_by_ward: Mapping[str, float], predicted_by_ward: Mapping[str, float],
) -> dict[str, object]:
    wards = sorted(set(actual_by_ward) | set(predicted_by_ward))
    if not wards or set(actual_by_ward) != set(predicted_by_ward):
        raise ValueError("actual and predicted ward sets must match and be nonempty")
    actual = [float(actual_by_ward[w]) for w in wards]
    predicted = [float(predicted_by_ward[w]) for w in wards]
    if any(not math.isfinite(x) or x < 0 for x in actual + predicted):
        raise ValueError("ward totals must be finite and nonnegative")
    rho = _correlation(_average_ranks(actual), _average_ranks(predicted))
    k = math.ceil(len(wards) / 4)
    actual_top = set(sorted(wards, key=lambda w: (-actual_by_ward[w], w))[:k])
    predicted_top = set(sorted(wards, key=lambda w: (-predicted_by_ward[w], w))[:k])
    return {"spearman": rho, "spearman_undefined_reason": "constant_rank_vector" if rho is None else None,
            "top_quarter_recall": len(actual_top & predicted_top) / k, "top_k": k}


def category_ranking_metrics(
    actual_by_category: Mapping[str, Mapping[str, float]],
    predicted_by_category: Mapping[str, Mapping[str, float]],
) -> dict[str, object]:
    """Rank ward totals within each category, then average defined category scores."""
    if not actual_by_category or set(actual_by_category) != set(predicted_by_category):
        raise ValueError("actual and predicted category sets must match and be nonempty")
    per_category = {
        category: ranking_metrics(actual_by_category[category], predicted_by_category[category])
        for category in sorted(actual_by_category)
    }
    defined = [result["spearman"] for result in per_category.values() if result["spearman"] is not None]
    recalls = [result["top_quarter_recall"] for result in per_category.values()]
    ks = {result["top_k"] for result in per_category.values()}
    return {
        "spearman": sum(defined) / len(defined) if defined else None,
        "spearman_undefined_reason": None if defined else "all_categories_constant",
        "spearman_undefined_categories": [category for category, result in per_category.items() if result["spearman"] is None],
        "top_quarter_recall": sum(recalls) / len(recalls),
        "top_k": next(iter(ks)) if len(ks) == 1 else None,
        "ranking_by_category": per_category,
    }
