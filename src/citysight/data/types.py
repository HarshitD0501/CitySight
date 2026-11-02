"""Typed records shared by the input readers and later pipeline stages."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

CATEGORIES = (
    "electrical", "solid_waste", "roads", "trees", "animals_health", "other"
)
NUMERIC_FEATURES = (
    "population_2011", "area_sq_km", "households_census_2011",
    "road_length_kms", "lakes", "lake_area_sq_m", "parks", "park_area_sq_m",
    "playgrounds", "playground_area_sq_m", "govt_schools", "police_stations",
    "fire_stations", "bus_stops", "bmtc_ttmc", "streetlights",
    "population_density_2011_persons_sq_km",
    "decadal_popn_growth_rate_2011_2001",
    "decadal_households_growth_rate_2011_2001", "bus_routes",
    "centroid_lon", "centroid_lat",
)
PERCENT_FEATURES = frozenset((
    "decadal_popn_growth_rate_2011_2001",
    "decadal_households_growth_rate_2011_2001",
))
CountKey = tuple[str, str, str]


class DataValidationError(ValueError):
    """An input violates a documented data contract."""


@dataclass(frozen=True, slots=True)
class WardFeatures:
    ward_id: str
    attributes: Mapping[str, str | None]
    numeric: Mapping[str, float | None]


@dataclass(frozen=True, slots=True)
class GridRow:
    ward_id: str
    month: str
    category_group: str

    @property
    def key(self) -> CountKey:
        return self.ward_id, self.month, self.category_group


@dataclass(frozen=True, slots=True)
class Complaint:
    complaint_id: str
    ward_id: str
    timestamp: datetime
    category_group: str
    status: str | None


@dataclass(frozen=True, slots=True)
class CountTable:
    counts: Mapping[CountKey, int]
    observed_wards: tuple[str, ...]
    months: tuple[str, ...]
    record_count: int
    null_status_count: int
    first_timestamp: datetime
    last_timestamp: datetime
    coverage_policy: str = "COV-1"


@dataclass(frozen=True, slots=True)
class InputDataset:
    data_dir: Path
    features: Mapping[str, WardFeatures]
    grid: tuple[GridRow, ...]
    counts: CountTable
    geometry: dict[str, Any] | None
    source_hashes: Mapping[str, str]
