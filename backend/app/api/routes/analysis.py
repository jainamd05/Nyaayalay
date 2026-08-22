from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.legal_service import analyze

router = APIRouter(prefix="/analysis", tags=["Legal Analysis"])


@router.post("", response_model=AnalysisResponse)
def analyze_incident(request: AnalysisRequest):
    try:
        result = analyze(request.incident)
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
