"""Deterministic fold-local tabular feature construction for HGB."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from citysight.data.types import WardFeatures

NUMERIC_COLUMNS = (
    "population_2011", "area_sq_km", "households_census_2011", "road_length_kms",
    "lakes", "lake_area_sq_m", "parks", "park_area_sq_m", "playgrounds",
    "playground_area_sq_m", "govt_schools", "police_stations", "fire_stations",
    "bus_stops", "streetlights", "bus_routes", "population_density_2011_persons_sq_km",
    "decadal_popn_growth_rate_2011_2001", "decadal_households_growth_rate_2011_2001",
    "centroid_lon", "centroid_lat",
)


@dataclass(frozen=True, slots=True)
class FeatureEncoder:
    medians: tuple[float, ...]
    all_missing: tuple[str, ...]
    zones: tuple[str, ...]


def _zone(feature: WardFeatures) -> str:
    val = feature.attributes.get("bbmp_zone_name") or feature.attributes.get("zone")
    return (val or "__MISSING__").strip() or "__MISSING__"


def fit_encoder(features: Sequence[WardFeatures]) -> FeatureEncoder:
    if not features:
        raise ValueError("cannot fit feature encoder without training wards")
    medians: list[float] = []
    all_missing: list[str] = []
    for column in NUMERIC_COLUMNS:
        values = sorted(float(f.numeric[column]) for f in features if f.numeric.get(column) is not None)
        if not values:
            medians.append(0.0)
            all_missing.append(column)
        elif len(values) % 2:
            medians.append(values[len(values)//2])
        else:
            medians.append((values[len(values)//2 - 1] + values[len(values)//2]) / 2)
    return FeatureEncoder(tuple(medians), tuple(all_missing), tuple(sorted({_zone(f) for f in features})))


def transform(feature: WardFeatures, month: str, category: str, encoder: FeatureEncoder) -> list[float]:
    year, month_num = map(int, month.split("-"))
    row = [float(feature.numeric.get(col) if feature.numeric.get(col) is not None else encoder.medians[i])
           for i, col in enumerate(NUMERIC_COLUMNS)]
    row.extend((float(12 * year + month_num - 1), float(month_num)))
    row.extend(1.0 if category == value else 0.0 for value in (
        "electrical", "solid_waste", "roads", "trees", "animals_health", "other"))
    zone = _zone(feature)
    row.extend(1.0 if zone == value else 0.0 for value in encoder.zones)
    if not all(math.isfinite(value) for value in row):
        raise ValueError("nonfinite transformed feature")
    return row
