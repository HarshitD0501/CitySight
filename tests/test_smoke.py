"""Smoke tests for guide-mandated CLI entry points predict.py and train.py."""
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DATA_DIR = ROOT.parent / "hack-day-lucknow-datasets" / "p3-ward-civic-demand"


class SmokeTests(unittest.TestCase):
    def test_predict_sample_input(self):
        """Test predict.py against sample_submission.csv as a test grid."""
        sample_grid = DATA_DIR / "sample_submission.csv"
        self.assertTrue(sample_grid.is_file(), f"Sample grid not found at {sample_grid}")

        with tempfile.TemporaryDirectory() as tmpdir:
            out_csv = Path(tmpdir) / "output.csv"
            cmd = [
                PYTHON, str(ROOT / "predict.py"),
                "--data-dir", str(DATA_DIR),
                "--grid", str(sample_grid),
                "--output", str(out_csv),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"predict.py failed: {res.stderr}")
            self.assertTrue(out_csv.is_file(), "output.csv was not created")

            with out_csv.open("r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                self.assertEqual(header, ["ward_id", "month", "category_group", "predicted_count"])
                rows = list(reader)
                self.assertEqual(len(rows), 6)  # sample_submission has 6 rows
                for row in rows:
                    self.assertEqual(len(row), 4)
                    val = float(row[3])
                    self.assertGreaterEqual(val, 0.0)

    def test_train_creates_model_info(self):
        """Test train.py against public data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_model = Path(tmpdir) / "models"
            cmd = [
                PYTHON, str(ROOT / "train.py"),
                "--data-dir", str(DATA_DIR),
                "--out", str(out_model),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"train.py failed: {res.stderr}")
            info_file = out_model / "model_info.json"
            self.assertTrue(info_file.is_file(), "model_info.json was not created")


if __name__ == "__main__":
    unittest.main()

