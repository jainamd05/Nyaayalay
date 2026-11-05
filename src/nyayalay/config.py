from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables from the project root `.env` and, for people who
# followed `backend/.env.example`, from `backend/.env` as well. Variables that
# are already set in the real environment (e.g. on Render) always win.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env")

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CHROMA_DIR = DATA_DIR / "chroma"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip() or "openai/gpt-oss-20b"
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

CHROMA_COLLECTION = "nyayalay_legal_corpus"

TOP_K = 5
RETRIEVAL_POOL_SIZE = 25

ROUTER_MIN_CONFIDENCE = 0.70
CLASSIFICATION_MIN_CONFIDENCE = 0.65
VERIFICATION_MIN_CONFIDENCE = 0.70

SEMANTIC_WEIGHT = 0.70
LEXICAL_WEIGHT = 0.30

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
