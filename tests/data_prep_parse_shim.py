import importlib.util
import sys
from pathlib import Path

DATA_PREP = Path(__file__).resolve().parents[1] / "data-prep"
MODULE_PATH = DATA_PREP / "parse_act_pdf.py"

if str(DATA_PREP) not in sys.path:
    sys.path.insert(0, str(DATA_PREP))

spec = importlib.util.spec_from_file_location("parse_act_pdf", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
# Registered before execution so dataclasses can resolve the module.
sys.modules[spec.name] = module
spec.loader.exec_module(module)

parse_sections = module.parse_sections
