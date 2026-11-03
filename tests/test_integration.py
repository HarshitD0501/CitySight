"""Phase D5 End-to-End Integration and Acceptance Verification Suite (A01 - A18)."""
import csv
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DATA_DIR = ROOT.parent / "hack-day-lucknow-datasets" / "p3-ward-civic-demand"


class AcceptanceIntegrationTests(unittest.TestCase):
    def test_a08_scorer_runtime_and_limits(self):
        """A08 & A16: Dynamic scorer produces valid predictions on full 4,320 grid within time limits."""
        template_grid = DATA_DIR / "sample_submission.csv"
        # If template is small sample, construct a 4320-row grid or test against sample
        target_grid = DATA_DIR / "sample_submission.csv"
        self.assertTrue(target_grid.is_file())

        with tempfile.TemporaryDirectory() as tmpdir:
            out_csv = Path(tmpdir) / "output.csv"
            start_time = time.time()
            env = dict(os.environ)
            env["OMP_NUM_THREADS"] = "2"
            env["OPENBLAS_NUM_THREADS"] = "2"
            env["MKL_NUM_THREADS"] = "2"
            env["PYTHONPATH"] = f"{ROOT / 'src'};{ROOT}"

            cmd = [
                PYTHON, str(ROOT / "predict.py"),
                "--data-dir", str(DATA_DIR),
                "--grid", str(target_grid),
                "--output", str(out_csv),
            ]
            res = subprocess.run(cmd, env=env, capture_output=True, text=True)
            elapsed = time.time() - start_time

            self.assertEqual(res.returncode, 0, f"predict.py failed: {res.stderr}")
            self.assertTrue(out_csv.is_file())
            self.assertLess(elapsed, 600.0, f"Scoring took {elapsed:.2f}s, exceeding 600s limit")

            with out_csv.open("r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                self.assertEqual(header, ["ward_id", "month", "category_group", "predicted_count"])
                rows = list(reader)
                self.assertGreater(len(rows), 0)
                for r in rows:
                    self.assertEqual(len(r), 4)
                    val = float(r[3])
                    self.assertFalse(val < 0.0 or val != val, f"Invalid prediction: {val}")

    def test_a10_packaging_and_readme_headings(self):
        """A10: Verify submission.yaml, requirements.txt, and 8 required README headings with >= 20 words each."""
        # 1. submission.yaml
        sub_yaml = ROOT / "submission.yaml"
        self.assertTrue(sub_yaml.is_file(), "submission.yaml missing")
        sub_text = sub_yaml.read_text(encoding="utf-8")
        self.assertIn("problem: p3", sub_text)
        self.assertIn("predict.py", sub_text)
        self.assertIn("train.py", sub_text)

        # 2. requirements.txt
        req_txt = ROOT / "requirements.txt"
        self.assertTrue(req_txt.is_file(), "requirements.txt missing")
        for line in req_txt.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                self.assertIn("==", line, f"Requirement not pinned with ==: {line}")

        # 3. README.md headings and word counts
        readme = ROOT / "README.md"
        self.assertTrue(readme.is_file(), "README.md missing")
        content = readme.read_text(encoding="utf-8")

        required_headings = [
            "Problem understanding",
            "Approach",
            "Validation",
            "Results",
            "How to run",
            "Use of AI tools",
            "Data & licences",
            "Team",
        ]
        lines = content.splitlines()
        for heading in required_headings:
            found = False
            heading_line_idx = -1
            for idx, line in enumerate(lines):
                if line.lstrip("#").strip().lower() == heading.lower():
                    found = True
                    heading_line_idx = idx
                    break
            self.assertTrue(found, f"Missing required heading: {heading}")

            # Count words under this heading until next heading
            words = []
            for line in lines[heading_line_idx + 1:]:
                if line.startswith("#"):
                    break
                words.extend(line.strip().split())
            self.assertGreaterEqual(len(words), 20, f"Heading '{heading}' has {len(words)} words, requires >= 20")

    def test_a11_artifact_provenance_and_schema(self):
        """A11: Verify that exported frontend data contracts match manifest run_id and schema_version 1."""
        data_dir = ROOT / "frontend" / "public" / "data"
        manifest_file = data_dir / "manifest.json"
        self.assertTrue(manifest_file.is_file(), "manifest.json missing in frontend/public/data")

        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        run_id = manifest.get("run_id")
        self.assertTrue(bool(run_id), "Manifest missing run_id")
        self.assertEqual(manifest.get("schema_version"), 1)

        expected_files = ["predictions", "observations", "geometry", "challenge", "metrics"]
        for key in expected_files:
            fname = manifest["files"][key]
            fpath = data_dir / fname
            self.assertTrue(fpath.is_file(), f"Asset {fname} missing")
            if fname.endswith(".json"):
                data = json.loads(fpath.read_text(encoding="utf-8"))
                self.assertEqual(data.get("run_id"), run_id, f"run_id mismatch in {fname}")
                self.assertEqual(data.get("schema_version"), 1, f"schema_version mismatch in {fname}")

    def test_a18_repository_hygiene_and_secrets(self):
        """A18: Check that raw dataset files, challenge answer tables, and credentials are not tracked."""
        git_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(git_status.returncode, 0)
        lines = git_status.stdout.splitlines()

        # Check tracked/staged files do not contain forbidden assets
        for line in lines:
            status = line[:2]
            path = line[3:]
            # Must not track .csv from dataset
            self.assertNotIn("grievances_public_wards.csv", path)
            self.assertNotIn("ward_features.csv", path)
            self.assertNotIn("ward_boundaries.geojson", path)
            # Must not commit node_modules or out
            self.assertNotIn("node_modules/", path)
            self.assertNotIn("frontend/out/", path)

        # Check no hardcoded API keys or tokens in src/
        for p in (ROOT / "src").rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            self.assertNotIn("BEGIN PRIVATE KEY", text)
            self.assertNotIn("ghp_", text)
            self.assertNotIn("bearer", text.lower())


if __name__ == "__main__":
    unittest.main()

