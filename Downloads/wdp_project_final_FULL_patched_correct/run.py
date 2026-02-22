# Unified entrypoint (root)
# This runs the consolidated app from projDraft5_abso_updated\run.py.

from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "projDraft5_abso_updated"
APP_RUN = APP_DIR / "run.py"

if __name__ == "__main__":
    sys.path.insert(0, str(APP_DIR))
    runpy.run_path(str(APP_RUN), run_name="__main__")
