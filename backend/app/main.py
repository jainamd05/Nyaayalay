import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analysis import router as analysis_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.state import warmup_state

logger = logging.getLogger("nyayalay")


def _warm_up_retrieval() -> None:
    """Load the Chroma index + embedding model without blocking startup."""
    try:
        from nyayalay.retrieval import warm_up

        warmup_state["records"] = warm_up()
        warmup_state["status"] = "ready"
        logger.info("Retrieval index ready (%s records).", warmup_state["records"])
    except Exception as exc:  # pragma: no cover - logged for operators
        warmup_state["status"] = "failed"
        warmup_state["error"] = str(exc)
        logger.exception("Retrieval warm-up failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not settings.warmup_on_startup:
        warmup_state["status"] = "disabled"
    else:
        threading.Thread(target=_warm_up_retrieval, daemon=True).start()
    yield


app = FastAPI(
    title="Nyayalay API",
    version="0.1.0",
    description="API layer for the Nyayalay legal-information assistant.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.frontend_url_regex or None,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/")
def root():
    return {"name": "Nyayalay API", "status": "running"}
