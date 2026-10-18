from pydantic import BaseModel, Field, field_validator, model_validator


def _normalise_confidence(value):
    """LLMs sometimes answer 85 or "85%" instead of 0.85."""
    if isinstance(value, str):
        value = value.strip().rstrip("%").strip()
        try:
            value = float(value)
        except ValueError:
            return value
    if isinstance(value, (int, float)) and 1 < value <= 100:
        return value / 100
    return value


class RouteResult(BaseModel):
    domain: str
    confidence: float = Field(ge=0, le=1)
    reason: str

    _confidence = field_validator("confidence", mode="before")(_normalise_confidence)

    @field_validator("domain", mode="before")
    @classmethod
    def _normalise_domain(cls, value):
        if isinstance(value, str):
            return value.strip().lower().replace(" ", "_").replace("-", "_")
        return value

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

    @model_validator(mode="before")
    @classmethod
    def _fill_nulls(cls, data):
        """Treat null lists/flags from the LLM as empty/false instead of failing."""
        if not isinstance(data, dict):
            return data
        for name, field in cls.model_fields.items():
            value = data.get(name)
            if field.annotation == list[str]:
                if value is None:
                    data[name] = []
                elif isinstance(value, str):
                    data[name] = [value]
            elif field.annotation is bool and value is None:
                data[name] = False
        return data

class ClassificationResult(BaseModel):
    section: str | None = None
    confidence: float = Field(ge=0, le=1)
    explanation: str
    candidate_rank: int | None = Field(default=None, ge=1)
    missing_information: list[str] = Field(default_factory=list)

    _confidence = field_validator("confidence", mode="before")(_normalise_confidence)

    @field_validator("section", mode="before")
    @classmethod
    def _section_to_str(cls, value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(int(value)) if float(value).is_integer() else str(value)
        if isinstance(value, str) and value.strip().lower() in {"", "null", "none"}:
            return None
        return value

class VerificationResult(BaseModel):
    supported: bool
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    evidence_support: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)

    _confidence = field_validator("confidence", mode="before")(_normalise_confidence)

EXTRACTION_SCHEMA_DESCRIPTION = "Extract facts only. Never invent facts or choose legal sections."
CLASSIFICATION_SCHEMA_DESCRIPTION = "Choose only an exact section from supplied candidates, or null."
VERIFICATION_SCHEMA_DESCRIPTION = "Verify only from supplied facts and supplied legal text; fail closed when weak."
