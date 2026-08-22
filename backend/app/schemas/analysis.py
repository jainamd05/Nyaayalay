from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    incident: str = Field(min_length=10, max_length=10000)


class AnalysisResponse(BaseModel):
    status: str
    message: str | None = None
    route: dict | None = None
    facts: dict | None = None
    candidates: list[dict] | None = None
    classification: dict | None = None
    verification: dict | None = None
    result: dict | None = None
