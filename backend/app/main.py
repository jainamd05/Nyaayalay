import logging
import sys
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Make the core engine importable even when the package was not pip-installed.
SRC_DIR = Path(__file__).resolve().parents[2] / "src"
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.api.routes.health import router as health_router  # noqa: E402
from app.api.routes.analysis import router as analysis_router  # noqa: E402
from app.core.config import settings  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nyayalay.api")

app = FastAPI(
    title="Nyayalay API",
    version="0.1.0",
    description="API layer for the Nyayalay legal-information assistant.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Vercel production and preview deployments, e.g. https://nyayalay-git-main-x.vercel.app
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


def _warm_up() -> None:
    try:
        from nyayalay.retrieval import warm_up

        warm_up()
        logger.info("Retrieval index and embedding model are ready.")
    except Exception:  # pragma: no cover - best effort only
        logger.exception("Retrieval warm-up failed")


@app.on_event("startup")
def start_warm_up() -> None:
    # Loading Chroma and the embedding model takes a while; do it in the
    # background so the server binds its port immediately.
    threading.Thread(target=_warm_up, daemon=True).start()


@app.get("/")
def root():
    return {"name": "Nyayalay API", "status": "running"}
