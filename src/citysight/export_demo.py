"""CLI entry point to export static artifacts for frontend demo."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure local src/ is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from citysight.artifacts import export_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Export CitySight static artifacts for local frontend demo")
    parser.add_argument("--data-dir", required=True, help="Path to public data directory")
    parser.add_argument("--out-dir", default="frontend/public/data", help="Output directory for static assets")
    parser.add_argument("--run-id", default=None, help="Optional run identifier")
    args = parser.parse_args()

    try:
        manifest = export_artifacts(args.data_dir, args.out_dir, run_id=args.run_id)
        print(f"Artifacts successfully exported to {args.out_dir}. Run ID: {manifest['run_id']}")
        return 0
    except Exception as exc:
        sys.stderr.write(f"Error exporting artifacts: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

