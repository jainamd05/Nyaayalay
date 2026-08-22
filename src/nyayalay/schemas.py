from pydantic import BaseModel, Field

class RouteResult(BaseModel):
    domain: str
    confidence: float = Field(ge=0, le=1)
    reason: str

class IncidentFacts(BaseModel):
    summary: str
    alleged_conduct: list[str] = Field(default_factory=list)
    event_type: str | None = None
    victim: str | None = None
    accused: str | None = None
    relationship_between_parties: str | None = None
    location: str | None = None
    time_or_date: str | None = None
    intent: str | None = None
    harm: list[str] = Field(default_factory=list)
    property_or_money: bool = False
    violence_or_threat: bool = False
    deception_or_fraud: bool = False
    digital_element: bool = False
    property_items: list[str] = Field(default_factory=list)
    money_amount: str | None = None
    injuries: list[str] = Field(default_factory=list)
    weapons_or_tools: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    missing_or_uncertain_facts: list[str] = Field(default_factory=list)

class ClassificationResult(BaseModel):
    section: str | None = None
    confidence: float = Field(ge=0, le=1)
    explanation: str
    candidate_rank: int | None = Field(default=None, ge=1)
    missing_information: list[str] = Field(default_factory=list)

class VerificationResult(BaseModel):
    supported: bool
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    evidence_support: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)

EXTRACTION_SCHEMA_DESCRIPTION = "Extract facts only. Never invent facts or choose legal sections."
CLASSIFICATION_SCHEMA_DESCRIPTION = "Choose only an exact section from supplied candidates, or null."
VERIFICATION_SCHEMA_DESCRIPTION = "Verify only from supplied facts and supplied legal text; fail closed when weak."
