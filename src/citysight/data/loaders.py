"""Read-only CSV/GeoJSON ingestion and explicit COV-1 count construction."""

from collections import Counter
from collections.abc import Collection, Iterable, Iterator
import csv
import hashlib
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .parsing import normalize_ward_id, parse_category, parse_month, parse_numeric, parse_timestamp
from .types import (
    CATEGORIES, NUMERIC_FEATURES, Complaint, CountTable, DataValidationError,
    GridRow, InputDataset, WardFeatures,
)


def _csv_rows(path: Path, required: Collection[str]) -> Iterator[tuple[int, dict[str, str]]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, strict=True)
            header = next(reader, None)
            if not header or any(not name.strip() for name in header):
                raise DataValidationError(f"{path.name}: missing or empty CSV header")
            if len(header) != len(set(header)):
                raise DataValidationError(f"{path.name}: duplicate CSV headers")
            missing = sorted(set(required) - set(header))
            if missing:
                raise DataValidationError(f"{path.name}: missing columns: {', '.join(missing)}")
            for cells in reader:
                if not cells:
                    continue
                if len(cells) != len(header):
                    raise DataValidationError(f"{path.name}: row {reader.line_num}: wrong column count")
                yield reader.line_num, dict(zip(header, cells))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DataValidationError(f"{path.name}: could not read valid UTF-8 CSV ({type(exc).__name__})") from exc


def _row_error(path: Path, number: int, exc: DataValidationError) -> DataValidationError:
    return DataValidationError(f"{path.name}: row {number}: {exc}")


def read_features(
    path: str | Path, *, required_numeric_fields: Collection[str] = (),
) -> dict[str, WardFeatures]:
    path = Path(path)
    unknown = set(required_numeric_fields) - set(NUMERIC_FEATURES)
    if unknown:
        raise DataValidationError("unrecognized required numeric feature")
    result: dict[str, WardFeatures] = {}
    for number, row in _csv_rows(path, ("ward_id", *required_numeric_fields)):
        try:
            ward_id = normalize_ward_id(row["ward_id"])
            if ward_id in result:
                raise DataValidationError("duplicate normalized ward_id")
            numeric = {field: parse_numeric(row[field], field) for field in NUMERIC_FEATURES if field in row}
            attributes = {field: value.strip() or None for field, value in row.items()}
            attributes["ward_id"] = ward_id
            result[ward_id] = WardFeatures(
                ward_id, MappingProxyType(attributes), MappingProxyType(numeric),
            )
        except DataValidationError as exc:
            raise _row_error(path, number, exc) from exc
    if not result:
        raise DataValidationError(f"{path.name}: no ward feature records")
    return result


def read_grid(
    path: str | Path, *, feature_ids: Collection[str] | None = None,
) -> tuple[GridRow, ...]:
    path = Path(path)
    known = set(feature_ids) if feature_ids is not None else None
    seen: set[tuple[str, str, str]] = set()
    result = []
    for number, row in _csv_rows(path, ("ward_id", "month", "category_group")):
        try:
            item = GridRow(normalize_ward_id(row["ward_id"]), parse_month(row["month"]), parse_category(row["category_group"]))
            if known is not None and item.ward_id not in known:
                raise DataValidationError("grid ward_id has no feature record")
            if item.key in seen:
                raise DataValidationError("duplicate grid key")
            seen.add(item.key)
            result.append(item)
        except DataValidationError as exc:
            raise _row_error(path, number, exc) from exc
    return tuple(result)


def iter_complaints(
    path: str | Path, *, feature_ids: Collection[str] | None = None,
) -> Iterator[Complaint]:
    """Stream validated rows; keep only IDs for duplicate detection, not all rows."""
    path = Path(path)
    known = set(feature_ids) if feature_ids is not None else None
    seen: set[str] = set()
    for number, row in _csv_rows(path, ("complaint_id", "ward_id", "grievance_time", "category_group")):
        try:
            complaint_id = row["complaint_id"].strip()
            if not complaint_id:
                raise DataValidationError("complaint_id is required")
            if complaint_id in seen:
                raise DataValidationError("duplicate complaint_id")
            seen.add(complaint_id)
            ward_id = normalize_ward_id(row["ward_id"])
            if known is not None and ward_id not in known:
                raise DataValidationError("complaint ward_id has no feature record")
            yield Complaint(
                complaint_id, ward_id, parse_timestamp(row["grievance_time"]),
                parse_category(row["category_group"]), row.get("status", "").strip() or None,
            )
        except DataValidationError as exc:
            raise _row_error(path, number, exc) from exc


def aggregate_counts(
    records: Iterable[Complaint], *, coverage_policy: str = "COV-1",
    excluded_wards: Collection[str] = (), max_cells: int = 2_000_000,
) -> CountTable:
    """Fill only eligible observed wards; exclude held-out rows before deriving coverage."""
    if coverage_policy != "COV-1":
        raise DataValidationError("unsupported coverage policy")
    if isinstance(max_cells, bool) or not isinstance(max_cells, int) or max_cells <= 0:
        raise DataValidationError("max_cells must be a positive integer")
    excluded = {normalize_ward_id(value) for value in excluded_wards}
    counts: Counter[tuple[str, str, str]] = Counter()
    wards: set[str] = set()
    first = last = None
    total = null_status = 0
    for record in records:
        if record.ward_id in excluded:
            continue
        month = f"{record.timestamp.year:04d}-{record.timestamp.month:02d}"
        counts[record.ward_id, month, record.category_group] += 1
        wards.add(record.ward_id)
        total += 1
        null_status += record.status is None
        first = record.timestamp if first is None else min(first, record.timestamp)
        last = record.timestamp if last is None else max(last, record.timestamp)
        if len(counts) > max_cells:
            raise DataValidationError("observed count cells exceed max_cells")
    if first is None or last is None:
        raise DataValidationError("no eligible complaint records to aggregate")
    start = first.year * 12 + first.month - 1
    end = last.year * 12 + last.month - 1
    cell_count = len(wards) * (end - start + 1) * len(CATEGORIES)
    if cell_count > max_cells:
        raise DataValidationError(f"COV-1 requires {cell_count} cells; max_cells is {max_cells}")
    months = tuple(f"{index // 12:04d}-{index % 12 + 1:02d}" for index in range(start, end + 1))
    ordered_wards = tuple(sorted(wards))
    complete = {
        (ward_id, month, category): counts.get((ward_id, month, category), 0)
        for ward_id in ordered_wards for month in months for category in CATEGORIES
    }
    return CountTable(
        MappingProxyType(complete), ordered_wards, months, total,
        null_status, first, last, coverage_policy,
    )


def _reject_json_constant(value: str) -> None:
    raise DataValidationError("GeoJSON contains a nonfinite numeric constant")


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DataValidationError("GeoJSON contains duplicate object keys")
        result[key] = value
    return result


def _validate_ring(ring: Any) -> None:
    if not isinstance(ring, list) or len(ring) < 4:
        raise DataValidationError("polygon rings require at least four positions")
    for position in ring:
        if not isinstance(position, list) or len(position) not in (2, 3):
            raise DataValidationError("positions require longitude, latitude and optional altitude")
        try:
            invalid = any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in position)
        except OverflowError:
            invalid = True
        if invalid:
            raise DataValidationError("coordinates must be finite numeric values")
        if not (-180 <= position[0] <= 180 and -90 <= position[1] <= 90):
            raise DataValidationError("coordinates are outside geographic bounds")
    if ring[0] != ring[-1]:
        raise DataValidationError("polygon ring is not closed")


def read_geometry(
    path: str | Path, *, feature_ids: Collection[str] | None = None,
) -> dict[str, Any]:
    path = Path(path)
    try:
        with path.open(encoding="utf-8-sig") as handle:
            document = json.load(handle, parse_constant=_reject_json_constant, object_pairs_hook=_json_object)
    except DataValidationError:
        raise
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise DataValidationError(f"{path.name}: could not read valid GeoJSON ({type(exc).__name__})") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise DataValidationError("GeoJSON must be a FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list) or not features:
        raise DataValidationError("GeoJSON must have nonempty features")
    seen: set[str] = set()
    for index, feature in enumerate(features):
        try:
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                raise DataValidationError("expected a GeoJSON Feature")
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                raise DataValidationError("feature properties must include ward_id")
            ward_id = normalize_ward_id(properties.get("ward_id"))
            if ward_id in seen:
                raise DataValidationError("duplicate geometry ward_id")
            seen.add(ward_id)
            properties["ward_id"] = ward_id
            geometry = feature.get("geometry")
            if not isinstance(geometry, dict) or geometry.get("type") not in ("Polygon", "MultiPolygon"):
                raise DataValidationError("geometry must be Polygon or MultiPolygon")
            coordinates = geometry.get("coordinates")
            polygons = [coordinates] if geometry["type"] == "Polygon" else coordinates
            if not isinstance(polygons, list) or not polygons:
                raise DataValidationError("geometry requires nonempty polygons")
            for polygon in polygons:
                if not isinstance(polygon, list) or not polygon:
                    raise DataValidationError("polygon requires nonempty rings")
                for ring in polygon:
                    _validate_ring(ring)
        except DataValidationError as exc:
            raise DataValidationError(f"{path.name}: feature {index}: {exc}") from exc
    if feature_ids is not None and seen != set(feature_ids):
        raise DataValidationError(f"{path.name}: geometry and feature ward ID sets differ")
    return document


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise DataValidationError(f"{Path(path).name}: could not hash input ({type(exc).__name__})") from exc
    return digest.hexdigest()


def load_inputs(
    data_dir: str | Path, *, grid_path: str | Path | None = None,
    include_geometry: bool = False, required_numeric_fields: Collection[str] = (),
) -> InputDataset:
    root = Path(data_dir).resolve()
    if not root.is_dir():
        raise DataValidationError("data directory does not exist")

    def source(name: str) -> Path:
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise DataValidationError("input path escapes the data directory")
        return path

    feature_path = source("ward_features.csv")
    complaint_path = source("grievances_public_wards.csv")
    selected_grid = Path(grid_path).resolve() if grid_path is not None else source("prediction_grid_template.csv")
    features = read_features(feature_path, required_numeric_fields=required_numeric_fields)
    grid = read_grid(selected_grid, feature_ids=features)
    counts = aggregate_counts(
        iter_complaints(complaint_path, feature_ids=features),
        excluded_wards={row.ward_id for row in grid},
    )
    paths = {"ward_features.csv": feature_path, "grievances_public_wards.csv": complaint_path, "grid": selected_grid}
    geometry = None
    if include_geometry:
        geometry_path = source("wards.geojson")
        geometry = read_geometry(geometry_path, feature_ids=features)
        paths["wards.geojson"] = geometry_path
    return InputDataset(
        root, MappingProxyType(features), grid, counts, geometry,
        MappingProxyType({name: file_sha256(path) for name, path in paths.items()}),
    )
