"""Data contract tests use small synthetic fixtures, never copied answer tables."""

import csv
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

# Running tests requires no editable install or third-party test dependency.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from citysight.data import (
    Complaint, DataValidationError, aggregate_counts, file_sha256,
    iter_complaints, load_inputs, normalize_ward_id, parse_category,
    parse_month, parse_numeric, parse_timestamp, read_features, read_geometry, read_grid,
)


class ParsingTests(unittest.TestCase):
    def test_ids_preserve_text_without_float_coercion(self):
        self.assertEqual(normalize_ward_id(" 001 "), "001")
        self.assertEqual(normalize_ward_id(1), "1")
        for value in (None, "", "1.0", "1e2", 1.0, True, "١", "-1"):
            with self.subTest(value=value), self.assertRaises(DataValidationError):
                normalize_ward_id(value)

    def test_months_are_valid_and_canonical(self):
        self.assertEqual(parse_month("2024-02"), "2024-02")
        for value in ("0000-01", "2024-00", "2024-13", "2024-2", "24-02", "2024-02-01"):
            with self.subTest(value=value), self.assertRaises(DataValidationError):
                parse_month(value)

    def test_source_time_preserves_naive_calendar_month(self):
        self.assertEqual(parse_timestamp("2024-02-29 00:00:00"), datetime(2024, 2, 29))
        self.assertEqual(parse_timestamp("0001-01-01 00:00:00"), datetime(1, 1, 1))
        for value in ("2023-02-29 00:00:00", "2024-2-01 00:00:00", "2024-01-01T00:00:00", ""):
            with self.subTest(value=value), self.assertRaises(DataValidationError):
                parse_timestamp(value)

    def test_categories_use_official_groups(self):
        self.assertEqual(parse_category(" electrical "), "electrical")
        with self.assertRaises(DataValidationError):
            parse_category("Electrical")

    def test_numeric_commas_and_percentage_points(self):
        self.assertEqual(parse_numeric("3,182", "population_density_2011_persons_sq_km"), 3182)
        self.assertEqual(parse_numeric("1,18,059", "population_density_2011_persons_sq_km"), 118059)
        self.assertEqual(parse_numeric("12,34,567.5", "population_2011"), 1234567.5)
        field = "decadal_popn_growth_rate_2011_2001"
        self.assertEqual(parse_numeric("59.10%", field), 59.1)
        self.assertEqual(parse_numeric("-23.9%", field), -23.9)
        self.assertIsNone(parse_numeric(" ", "population_2011"))
        self.assertIsNone(parse_numeric(None, "population_2011"))

    def test_malformed_and_nonfinite_numeric_fields_fail(self):
        for value in ("3,18", "1,234,56", "NaN", "Infinity", "-inf", "1e9999", "1_000", "1%", "oops"):
            with self.subTest(value=value), self.assertRaises(DataValidationError):
                parse_numeric(value, "population_2011")
        with self.assertRaises(DataValidationError):
            parse_numeric("-1", "population_2011")
        for field, value in (("centroid_lat", "91"), ("centroid_lon", "181")):
            with self.subTest(field=field), self.assertRaises(DataValidationError):
                parse_numeric(value, field)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def csv_file(self, name, columns, rows):
        path = self.root / name
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            writer.writerows(rows)
        return path

    def complaints(self, rows):
        return self.csv_file("complaints.csv", ["complaint_id", "ward_id", "grievance_time", "category_group", "status"], rows)

    def grid(self, rows):
        return self.csv_file("grid.csv", ["ward_id", "month", "category_group"], rows)

    def geometry(self, features=None):
        document = {"type": "FeatureCollection", "features": features if features is not None else [self.polygon()]}
        path = self.root / "wards.geojson"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    @staticmethod
    def polygon(ward_id=1):
        return {
            "type": "Feature", "properties": {"ward_id": ward_id},
            "geometry": {"type": "Polygon", "coordinates": [[[77, 12], [78, 12], [78, 13], [77, 12]]]},
        }

    def test_features_parse_missing_descriptions_without_mutation(self):
        path = self.csv_file("features.csv", ["ward_id", "police_stn", "population_2011", "decadal_popn_growth_rate_2011_2001"], [[" 1 ", "", "12,345", "59.10%"]])
        before = file_sha256(path)
        record = read_features(path)["1"]
        self.assertEqual(record.numeric["population_2011"], 12345)
        self.assertEqual(record.numeric["decadal_popn_growth_rate_2011_2001"], 59.1)
        self.assertIsNone(record.attributes["police_stn"])
        self.assertEqual(before, file_sha256(path))

    def test_missing_numeric_cells_remain_missing(self):
        path = self.csv_file("features.csv", ["ward_id", "population_2011"], [["1", ""]])
        self.assertIsNone(read_features(path)["1"].numeric["population_2011"])

    def test_duplicate_normalized_feature_ids_fail(self):
        path = self.csv_file("features.csv", ["ward_id"], [["1"], [" 1 "]])
        with self.assertRaisesRegex(DataValidationError, "row 3.*duplicate normalized"):
            read_features(path)

    def test_required_model_columns_are_explicit(self):
        path = self.csv_file("features.csv", ["ward_id"], [["1"]])
        with self.assertRaisesRegex(DataValidationError, "centroid_lat"):
            read_features(path, required_numeric_fields=("centroid_lat",))
        with self.assertRaisesRegex(DataValidationError, "unrecognized"):
            read_features(path, required_numeric_fields=("invented",))

    def test_missing_files_and_empty_files_are_actionable(self):
        with self.assertRaisesRegex(DataValidationError, "could not read"):
            read_features(self.root / "missing.csv")
        path = self.root / "empty.csv"
        path.write_text("", encoding="utf-8")
        with self.assertRaisesRegex(DataValidationError, "header"):
            read_features(path)
        path = self.csv_file("features.csv", ["ward_id"], [])
        with self.assertRaisesRegex(DataValidationError, "no ward"):
            read_features(path)

    def test_duplicate_header_and_wrong_row_width_fail(self):
        path = self.csv_file("features.csv", ["ward_id", "ward_id"], [["1", "2"]])
        with self.assertRaisesRegex(DataValidationError, "duplicate CSV headers"):
            read_features(path)
        path = self.csv_file("features.csv", ["ward_id"], [["1", "extra"]])
        with self.assertRaisesRegex(DataValidationError, "column count"):
            read_features(path)

    def test_shuffled_columns_extra_headers_and_row_order_are_supported(self):
        path = self.csv_file("grid.csv", ["category_group", "unused", "month", "ward_id"], [["roads", "x", "2024-02", "2"], ["trees", "x", "2024-01", "1"]])
        rows = read_grid(path, feature_ids={"1", "2"})
        self.assertEqual([row.key for row in rows], [("2", "2024-02", "roads"), ("1", "2024-01", "trees")])

    def test_empty_grid_is_valid(self):
        self.assertEqual(read_grid(self.grid([])), ())

    def test_duplicate_grid_keys_fail(self):
        with self.assertRaisesRegex(DataValidationError, "duplicate grid key"):
            read_grid(self.grid([["1", "2024-01", "roads"], ["1", "2024-01", "roads"]]))

    def test_missing_grid_join_and_bad_category_fail(self):
        with self.assertRaisesRegex(DataValidationError, "no feature"):
            read_grid(self.grid([["2", "2024-01", "roads"]]), feature_ids={"1"})
        with self.assertRaisesRegex(DataValidationError, "allowed category"):
            read_grid(self.grid([["1", "2024-01", "unknown"]]))

    def test_null_status_is_counted_without_filtering(self):
        path = self.complaints([["a", "1", "2024-01-01 00:00:00", "roads", ""], ["b", "1", "2024-01-02 00:00:00", "roads", "closed"]])
        result = aggregate_counts(iter_complaints(path))
        self.assertEqual(result.counts["1", "2024-01", "roads"], 2)
        self.assertEqual(result.null_status_count, 1)

    def test_duplicate_complaint_ids_fail_before_counting_twice(self):
        path = self.complaints([["a", "1", "2024-01-01 00:00:00", "roads", ""], ["a", "2", "2024-02-01 00:00:00", "trees", "closed"]])
        with self.assertRaisesRegex(DataValidationError, "row 3.*duplicate complaint_id"):
            aggregate_counts(iter_complaints(path))

    def test_malformed_or_missing_complaint_fields_fail(self):
        rows = [
            ["", "1", "2024-01-01 00:00:00", "roads", ""],
            ["a", "", "2024-01-01 00:00:00", "roads", ""],
            ["a", "1", "invalid", "roads", ""],
            ["a", "1", "2024-01-01 00:00:00", "unknown", ""],
        ]
        for row in rows:
            with self.subTest(row=row), self.assertRaises(DataValidationError):
                list(iter_complaints(self.complaints([row])))

    def test_complaint_ward_must_join_when_feature_ids_supplied(self):
        path = self.complaints([["a", "2", "2024-01-01 00:00:00", "roads", ""]])
        with self.assertRaisesRegex(DataValidationError, "no feature"):
            list(iter_complaints(path, feature_ids={"1"}))

    def test_cov1_fills_absent_combinations_and_months_for_observed_wards_only(self):
        path = self.complaints([["a", "1", "2024-01-08 00:00:00", "roads", ""], ["b", "2", "2024-03-19 00:00:00", "trees", ""]])
        result = aggregate_counts(iter_complaints(path))
        self.assertEqual(result.months, ("2024-01", "2024-02", "2024-03"))
        self.assertEqual(len(result.counts), 2 * 3 * 6)
        self.assertEqual(result.counts["1", "2024-02", "roads"], 0)
        self.assertNotIn(("3", "2024-01", "roads"), result.counts)
        self.assertEqual(result.first_timestamp.day, 8)
        self.assertEqual(result.last_timestamp.day, 19)
        self.assertEqual(sum(result.counts.values()), 2)

    def test_excluded_wards_cannot_affect_count_coverage(self):
        path = self.complaints([["a", "1", "2024-01-08 00:00:00", "roads", ""], ["b", "2", "2030-01-19 00:00:00", "trees", ""]])
        result = aggregate_counts(iter_complaints(path), excluded_wards={"2"})
        self.assertEqual(result.months, ("2024-01",))
        self.assertEqual(result.observed_wards, ("1",))
        self.assertEqual(result.record_count, 1)

    def test_empty_and_all_excluded_complaints_fail_clearly(self):
        with self.assertRaisesRegex(DataValidationError, "no eligible"):
            aggregate_counts(iter_complaints(self.complaints([])))
        path = self.complaints([["a", "1", "2024-01-01 00:00:00", "roads", ""]])
        with self.assertRaisesRegex(DataValidationError, "no eligible"):
            aggregate_counts(iter_complaints(path), excluded_wards={"1"})

    def test_count_expansion_has_an_explicit_resource_limit(self):
        row = Complaint("a", "1", datetime(2024, 1, 1), "roads", None)
        with self.assertRaisesRegex(DataValidationError, "requires 6 cells"):
            aggregate_counts([row], max_cells=5)
        with self.assertRaisesRegex(DataValidationError, "unsupported coverage"):
            aggregate_counts([row], coverage_policy="invented")

    def test_count_order_is_independent_of_complaint_order(self):
        rows = [Complaint("a", "2", datetime(2024, 2, 1), "trees", None), Complaint("b", "1", datetime(2024, 1, 1), "roads", None)]
        left = aggregate_counts(rows)
        right = aggregate_counts(reversed(rows))
        self.assertEqual(list(left.counts.items()), list(right.counts.items()))

    def test_early_calendar_year_does_not_create_mismatched_month_keys(self):
        row = Complaint("a", "1", datetime(1, 1, 1), "roads", None)
        result = aggregate_counts([row])
        self.assertEqual(result.counts["1", "0001-01", "roads"], 1)
        self.assertEqual(sum(result.counts.values()), 1)

    def test_valid_geometry_normalizes_ids_without_changing_file(self):
        path = self.geometry()
        before = file_sha256(path)
        self.assertEqual(read_geometry(path, feature_ids={"1"})["features"][0]["properties"]["ward_id"], "1")
        self.assertEqual(before, file_sha256(path))

    def test_multipolygon_and_holes_are_structurally_supported(self):
        feature = self.polygon()
        ring = feature["geometry"]["coordinates"][0]
        feature["geometry"] = {"type": "MultiPolygon", "coordinates": [[ring, ring], [ring]]}
        self.assertEqual(len(read_geometry(self.geometry([feature]))["features"]), 1)

    def test_duplicate_and_mismatched_geometry_ids_fail(self):
        with self.assertRaisesRegex(DataValidationError, "duplicate geometry"):
            read_geometry(self.geometry([self.polygon(), self.polygon()]))
        with self.assertRaisesRegex(DataValidationError, "ID sets differ"):
            read_geometry(self.geometry(), feature_ids={"2"})

    def test_open_short_empty_or_invalid_geometry_fails(self):
        for coordinates in ([], [[]], [[[77, 12], [78, 12], [78, 13], [77, 13]]], [[[77, 12], [78, 12], [77, 12]]], [[[181, 12], [78, 12], [78, 13], [181, 12]]]):
            feature = self.polygon()
            feature["geometry"]["coordinates"] = coordinates
            with self.subTest(coordinates=coordinates), self.assertRaises(DataValidationError):
                read_geometry(self.geometry([feature]))

    def test_nonfinite_and_boolean_coordinates_fail(self):
        for value in (float("nan"), float("inf"), True):
            feature = self.polygon()
            feature["geometry"]["coordinates"][0][1][0] = value
            with self.subTest(value=value), self.assertRaises(DataValidationError):
                read_geometry(self.geometry([feature]))

    def test_bad_geojson_document_and_type_fail(self):
        path = self.root / "bad.json"
        for document in ("{", "null", "[]", '{"type":"FeatureCollection","features":[]}'):
            path.write_text(document, encoding="utf-8")
            with self.subTest(document=document), self.assertRaises(DataValidationError):
                read_geometry(path)
        feature = self.polygon()
        feature["geometry"]["type"] = "Point"
        with self.assertRaisesRegex(DataValidationError, "Polygon or MultiPolygon"):
            read_geometry(self.geometry([feature]))

    def test_duplicate_json_keys_and_extreme_numbers_fail_cleanly(self):
        path = self.root / "bad.json"
        path.write_text('{"type":"FeatureCollection","type":"FeatureCollection","features":[]}', encoding="utf-8")
        with self.assertRaisesRegex(DataValidationError, "duplicate object keys"):
            read_geometry(path)
        feature = self.polygon()
        feature["geometry"]["coordinates"][0][1][0] = 10 ** 400
        with self.assertRaisesRegex(DataValidationError, "finite numeric"):
            read_geometry(self.geometry([feature]))

    def test_load_inputs_excludes_requested_ward_labels_and_hashes_inputs(self):
        self.csv_file("ward_features.csv", ["ward_id"], [["1"], ["2"], ["3"]])
        path = self.complaints([["a", "1", "2024-01-01 00:00:00", "roads", ""], ["b", "2", "2024-01-02 00:00:00", "roads", ""]])
        path.rename(self.root / "grievances_public_wards.csv")
        path = self.grid([["2", "2024-01", "roads"]])
        path.rename(self.root / "prediction_grid_template.csv")
        dataset = load_inputs(self.root)
        self.assertEqual(dataset.counts.observed_wards, ("1",))
        self.assertEqual(dataset.grid[0].ward_id, "2")
        self.assertIsNone(dataset.geometry)
        self.assertEqual(len(dataset.source_hashes), 3)
        self.assertEqual(dataset.source_hashes["ward_features.csv"], file_sha256(self.root / "ward_features.csv"))

    def test_audit_cli_invalid_input_has_nonzero_exit_and_no_traceback(self):
        import os
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
        result = subprocess.run([sys.executable, "-m", "citysight.data", "--data-dir", str(self.root / "missing")], capture_output=True, text=True, env=env, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Input validation failed", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
