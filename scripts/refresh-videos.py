#!/usr/bin/env python3

from pathlib import Path
import runpy

REPO_DIR = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    runpy.run_path(str(REPO_DIR / "refresh.py"), run_name="__main__")
