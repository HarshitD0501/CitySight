"""Scalar boundary validation, independent of model or third-party packages."""

from datetime import date, datetime
import math
import re

from .types import CATEGORIES, NUMERIC_FEATURES, PERCENT_FEATURES, DataValidationError

_INTEGER = re.compile(r"[0-9]+\Z")
_MONTH = re.compile(r"[0-9]{4}-(?:0[1-9]|1[0-2])\Z")
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")
_GROUPED = re.compile(r"[+-]?[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?\Z")
_INDIAN_GROUPED = re.compile(r"[+-]?[0-9]{1,2}(?:,[0-9]{2})+,[0-9]{3}(?:\.[0-9]+)?\Z")


def normalize_ward_id(value: str | int | None) -> str:
    """Preserve integer text, including leading zeros; never coerce floats."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise DataValidationError("ward_id must be integer text")
    result = str(value).strip()
    if not _INTEGER.fullmatch(result):
        raise DataValidationError("ward_id must be nonempty ASCII integer text")
    return result


def parse_month(value: str) -> str:
    result = value.strip()
    if not _MONTH.fullmatch(result):
        raise DataValidationError("month must use YYYY-MM")
    try:
        date(int(result[:4]), int(result[5:]), 1)
    except ValueError as exc:
        raise DataValidationError("month must be a valid calendar month") from exc
    return result


def parse_timestamp(value: str) -> datetime:
    text = value.strip()
    try:
        result = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise DataValidationError("grievance_time must use YYYY-MM-DD HH:MM:SS") from exc
    # strptime accepts some non-zero-padded fields; the source contract does not.
    if result.isoformat(sep=" ", timespec="seconds") != text:
        raise DataValidationError("grievance_time must use zero-padded calendar fields")
    return result


def parse_category(value: str) -> str:
    result = value.strip()
    if result not in CATEGORIES:
        raise DataValidationError("category_group is not an allowed category")
    return result


def parse_numeric(value: str | None, field: str) -> float | None:
    if field not in NUMERIC_FEATURES:
        raise DataValidationError("unrecognized numeric feature field")
    if value is None or not value.strip():
        return None
    text = value.strip()
    if field in PERCENT_FEATURES and text.endswith("%"):
        text = text[:-1].strip()
    if "," in text:
        if not (_GROUPED.fullmatch(text) or _INDIAN_GROUPED.fullmatch(text)):
            raise DataValidationError(f"{field} has invalid thousands separators")
        text = text.replace(",", "")
    if not _NUMBER.fullmatch(text):
        raise DataValidationError(f"{field} must be a finite numeric value")
    result = float(text)
    if not math.isfinite(result):
        raise DataValidationError(f"{field} must be finite")
    if field == "centroid_lon":
        if not -180 <= result <= 180:
            raise DataValidationError("centroid_lon is outside geographic bounds")
    elif field == "centroid_lat":
        if not -90 <= result <= 90:
            raise DataValidationError("centroid_lat is outside geographic bounds")
    elif field not in PERCENT_FEATURES and result < 0:
        raise DataValidationError(f"{field} cannot be negative")
    return result
