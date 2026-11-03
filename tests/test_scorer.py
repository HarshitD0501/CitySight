"""Comprehensive acceptance tests for CLI scorer, train entry point, and static export."""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DATA_DIR = ROOT.parent / "hack-day-lucknow-datasets" / "p3-ward-civic-demand"


class ScorerAcceptanceTests(unittest.TestCase):
    def test_empty_grid_produces_header_only_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_grid = Path(tmpdir) / "empty_grid.csv"
            empty_grid.write_text("ward_id,month,category_group\n", encoding="utf-8")
            out_csv = Path(tmpdir) / "out.csv"

            cmd = [
                PYTHON, str(ROOT / "predict.py"),
                "--data-dir", str(DATA_DIR),
                "--grid", str(empty_grid),
                "--output", str(out_csv),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Failed on empty grid: {res.stderr}")
            self.assertTrue(out_csv.is_file())
            content = out_csv.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(content, ["ward_id,month,category_group,predicted_count"])

    def test_shuffled_and_subset_grid_preserves_order(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a 3-row grid in non-trivial order
            subset_grid = Path(tmpdir) / "subset_grid.csv"
            rows = [
                ["12", "2024-05", "trees"],
                ["5", "2024-01", "electrical"],
                ["5", "2024-02", "solid_waste"],
            ]
            with subset_grid.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ward_id", "month", "category_group"])
                writer.writerows(rows)

            out_csv = Path(tmpdir) / "out.csv"
            cmd = [
                PYTHON, str(ROOT / "predict.py"),
                "--data-dir", str(DATA_DIR),
                "--grid", str(subset_grid),
                "--output", str(out_csv),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"predict.py failed: {res.stderr}")

            with out_csv.open("r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                self.assertEqual(header, ["ward_id", "month", "category_group", "predicted_count"])
                out_rows = list(reader)
                self.assertEqual(len(out_rows), 3)
                for expected_in, actual_out in zip(rows, out_rows):
                    self.assertEqual(actual_out[:3], expected_in)
                    self.assertGreaterEqual(float(actual_out[3]), 0.0)

    def test_malformed_input_does_not_publish_partial_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_grid = Path(tmpdir) / "bad_grid.csv"
            # Invalid category
            bad_grid.write_text("ward_id,month,category_group\n5,2024-01,NONEXISTENT_CATEGORY\n", encoding="utf-8")
            out_csv = Path(tmpdir) / "out.csv"

            cmd = [
                PYTHON, str(ROOT / "predict.py"),
                "--data-dir", str(DATA_DIR),
                "--grid", str(bad_grid),
                "--output", str(out_csv),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertFalse(out_csv.exists(), "Partial output file must not be created on error")

    def test_label_mutation_changes_runtime_fit_predictions(self):
        """Verifies that predict.py dynamically fits at runtime rather than serving static answers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_data = Path(tmpdir) / "data"
            shutil.copytree(DATA_DIR, temp_data)

            small_grid = Path(tmpdir) / "grid.csv"
            small_grid.write_text("ward_id,month,category_group\n5,2024-01,electrical\n", encoding="utf-8")

            out_normal = Path(tmpdir) / "out_normal.csv"
            subprocess.run([
                PYTHON, str(ROOT / "predict.py"),
                "--data-dir", str(temp_data),
                "--grid", str(small_grid),
                "--output", str(out_normal),
            ], check=True)
            pred_normal = float(out_normal.read_text().strip().splitlines()[1].split(",")[3])

            # Mutate grievances: append thousands of electrical complaints to ward 1
            complaint_csv = temp_data / "grievances_public_wards.csv"
            with complaint_csv.open("a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for i in range(5000):
                    writer.writerow([f"mutated_{i}", "electrical", "raw", "sub", "2024-01-15 10:00:00", "1", "Closed"])

            out_mutated = Path(tmpdir) / "out_mutated.csv"
            subprocess.run([
                PYTHON, str(ROOT / "predict.py"),
                "--data-dir", str(temp_data),
                "--grid", str(small_grid),
                "--output", str(out_mutated),
            ], check=True)
            pred_mutated = float(out_mutated.read_text().strip().splitlines()[1].split(",")[3])

            self.assertNotEqual(pred_normal, pred_mutated, "Runtime fit should reflect changed grievance labels")

    def test_submission_yaml_and_requirements_format(self):
        """Check requirements.txt pins and submission.yaml fields."""
        req_file = ROOT / "requirements.txt"
        self.assertTrue(req_file.is_file())
        for line in req_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                self.assertIn("==", line, f"Requirement not pinned with ==: {line}")
                self.assertNotIn("git+", line)
                self.assertNotIn("http", line)

        sub_file = ROOT / "submission.yaml"
        self.assertTrue(sub_file.is_file())
        text = sub_file.read_text()
        self.assertIn("problem: p3", text)
        self.assertIn("predict.py", text)
        self.assertIn("train.py", text)


class ArtifactProvenanceTests(unittest.TestCase):
    def test_export_demo_provenance_and_contract(self):
        """Test export_demo creates consistent schema version 1 and matching run_id artifacts."""
        sys.path.insert(0, str(ROOT / "src"))
        from citysight.artifacts import export_artifacts

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = export_artifacts(DATA_DIR, tmpdir, run_id="test_run_123")
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["run_id"], "test_run_123")

            # Check all referenced files exist and match run_id
            for key, filename in manifest["files"].items():
                file_path = Path(tmpdir) / filename
                self.assertTrue(file_path.is_file(), f"Missing exported file {filename}")
                if filename.endswith(".json"):
                    content = json.loads(file_path.read_text(encoding="utf-8"))
                    self.assertEqual(content.get("run_id"), "test_run_123")
                    self.assertEqual(content.get("schema_version"), 1)


if __name__ == "__main__":
    unittest.main()

