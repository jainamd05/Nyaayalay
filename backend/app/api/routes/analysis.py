import logging

from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.legal_service import analyze

router = APIRouter(prefix="/analysis", tags=["Legal Analysis"])
logger = logging.getLogger(__name__)


@router.post("", response_model=AnalysisResponse)
def analyze_incident(request: AnalysisRequest):
    from nyayalay.llm_utils import LLMError

    try:
        return analyze(request.incident)
    except LLMError as exc:
        logger.warning("LLM failure: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        # Return a JSON error (which keeps CORS headers) instead of letting the
        # server crash the request, which browsers report as "Failed to fetch".
        logger.exception("Analysis failed")
        raise HTTPException(
            status_code=500,
            detail="The analysis failed due to an internal error. Please try again.",
        ) from exc
