from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    from nyayalay.config import GROQ_API_KEY, LLM_MODEL

    return {
        "status": "healthy",
        "service": "nyayalay-api",
        "llm_configured": bool(GROQ_API_KEY),
        "llm_model": LLM_MODEL,
    }
