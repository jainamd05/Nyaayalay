"""Nyayalay FastAPI application."""

import importlib.util
import sys
from pathlib import Path

# The API depends on the `nyayalay` engine in ../src. It is normally installed
# with `pip install -e .` (see requirements.txt), but fall back to the source
# tree so the API still starts if the editable install was skipped.
if importlib.util.find_spec("nyayalay") is None:
    _src = Path(__file__).resolve().parents[2] / "src"
    if _src.is_dir():
        sys.path.insert(0, str(_src))
