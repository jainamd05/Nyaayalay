from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CHROMA_DIR = DATA_DIR / "chroma"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Change this in .env without modifying Python code.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

CHROMA_COLLECTION = "nyayalay_legal_corpus"
TOP_K = 5
MIN_CONFIDENCE = 0.60

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
