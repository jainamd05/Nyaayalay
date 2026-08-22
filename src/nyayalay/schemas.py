from typing import Literal
from pydantic import BaseModel, Field


class RouteResult(BaseModel):
    domain: str
    confidence: float = Field(ge=0, le=1)
    reason: str


class IncidentFacts(BaseModel):
    summary: str
    alleged_conduct: list[str] = []
    victim: str | None = None
    accused: str | None = None
    intent: str | None = None
    harm: list[str] = []
    property_or_money: bool = False
    violence_or_threat: bool = False
    deception_or_fraud: bool = False
    digital_element: bool = False
    evidence: list[str] = []


class ClassificationResult(BaseModel):
    section: str | None
    confidence: float = Field(ge=0, le=1)
    explanation: str


class VerificationResult(BaseModel):
    supported: bool
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    contradictions: list[str] = []


EXTRACTION_SCHEMA_DESCRIPTION = """
Return structured facts from an incident. Do not decide the legal section.
Only extract facts explicitly stated or strongly implied by the incident.
"""


CLASSIFICATION_SCHEMA_DESCRIPTION = """
Choose the best candidate provision only from the supplied candidates.
Never invent a section that is not in the candidate list.
If none fits, return section=null.
"""


VERIFICATION_SCHEMA_DESCRIPTION = """
Check whether the proposed provision is actually supported by the incident facts
and the supplied authoritative candidate text. Do not rely on outside memory.
"""
