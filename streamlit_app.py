"""
Streamlit Community Cloud entrypoint.
Optional: set Main file path to streamlit_app.py instead of ui/app.py
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runpy.run_path(str(ROOT / "ui" / "app.py"), run_name="__streamlit__")
