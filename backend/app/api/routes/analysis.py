import logging

import openai
from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.legal_service import analyze

logger = logging.getLogger("nyayalay")

router = APIRouter(prefix="/analysis", tags=["Legal Analysis"])


@router.post("", response_model=AnalysisResponse)
def analyze_incident(request: AnalysisRequest):
    # Every failure is converted into an HTTPException here, inside the CORS
    # middleware, so the browser receives a readable error *with* CORS headers
    # instead of an opaque "Failed to fetch".
    from nyayalay.llm_utils import LLMConfigurationError, LLMOutputError

    try:
        return analyze(request.incident)
    except LLMConfigurationError as exc:
        logger.error("LLM is not configured: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMOutputError as exc:
        logger.warning("Unusable LLM output: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="The AI model returned an unexpected response. Please try again.",
        ) from exc
    except openai.AuthenticationError as exc:
        logger.error("LLM authentication failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="The AI service rejected the server's API key (check GROQ_API_KEY).",
        ) from exc
    except openai.RateLimitError as exc:
        logger.warning("LLM rate limit: %s", exc)
        raise HTTPException(
            status_code=429,
            detail="The AI service is rate-limited right now. Please wait a minute and try again.",
        ) from exc
    except openai.NotFoundError as exc:
        logger.error("LLM model not found: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="The configured AI model was not found (check LLM_MODEL).",
        ) from exc
    except (openai.APIConnectionError, openai.APITimeoutError) as exc:
        logger.warning("LLM connection problem: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Could not reach the AI service. Please try again shortly.",
        ) from exc
    except openai.APIError as exc:
        logger.error("LLM API error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="The AI service returned an error. Please try again.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected analysis failure")
        raise HTTPException(
            status_code=500,
            detail="An unexpected server error occurred during analysis.",
        ) from exc
