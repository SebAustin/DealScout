#!/usr/bin/env python3
"""Start Streamlit UI — works when run from inside dealscout/."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
app = Path(__file__).resolve().parent / "ui" / "app.py"

if __name__ == "__main__":
    env = {**dict(__import__("os").environ), "PYTHONPATH": str(ROOT)}
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)], env=env))
