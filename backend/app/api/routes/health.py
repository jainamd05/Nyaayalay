from fastapi import APIRouter

from app.core.state import warmup_state

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    from nyayalay.config import GROQ_API_KEY

    return {
        "status": "healthy",
        "service": "nyayalay-api",
        "llm_configured": bool(GROQ_API_KEY),
        "retrieval": warmup_state["status"],
        "indexed_records": warmup_state["records"],
    }
