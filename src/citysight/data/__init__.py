"""Validated read-only data interfaces for the offline CitySight pipeline."""

from .loaders import (
    aggregate_counts, file_sha256, iter_complaints, load_inputs,
    read_features, read_geometry, read_grid,
)
from .parsing import normalize_ward_id, parse_category, parse_month, parse_numeric, parse_timestamp
from .types import (
    CATEGORIES, NUMERIC_FEATURES, Complaint, CountTable, DataValidationError,
    GridRow, InputDataset, WardFeatures,
)

__all__ = [
    "CATEGORIES", "NUMERIC_FEATURES", "Complaint", "CountTable", "DataValidationError",
    "GridRow", "InputDataset", "WardFeatures", "aggregate_counts", "file_sha256",
    "iter_complaints", "load_inputs", "normalize_ward_id", "parse_category", "parse_month",
    "parse_numeric", "parse_timestamp", "read_features", "read_geometry", "read_grid",
]
