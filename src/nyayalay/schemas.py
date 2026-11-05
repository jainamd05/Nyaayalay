from typing import Any, get_args, get_origin

from pydantic import BaseModel, Field, field_validator, model_validator


def _coerce_confidence(value: Any) -> Any:
    """Accept 0.85, "0.85", 85 or "85%" and normalise to the 0..1 range."""
    if isinstance(value, str):
        stripped = value.strip().rstrip("%").strip()
        try:
            value = float(stripped)
        except ValueError:
            return value
    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
    if is_number and 1 < value <= 100:
        return value / 100
    return value


class LLMModel(BaseModel):
    """
    Base for schemas filled in by the LLM.

    Models frequently return `null` for list/boolean fields, numbers where a
    string is expected (e.g. a section number), or a single string instead
    of a list. Normalise those before validation so a cosmetic deviation does
    not fail the whole analysis.
    """

    @model_validator(mode="before")
    @classmethod
    def _normalise_llm_output(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        data = dict(data)
        for name, field in cls.model_fields.items():
            if name not in data:
                continue
            value = data[name]
            annotation = field.annotation
            origin = get_origin(annotation)
            args = get_args(annotation)

            if origin is list:
                if value is None:
                    data[name] = []
                elif isinstance(value, (str, int, float)):
                    data[name] = [str(value)] if str(value).strip() else []
                elif isinstance(value, list):
                    data[name] = [
                        str(item) for item in value
                        if item is not None and str(item).strip()
                    ]
            elif annotation is bool and value is None:
                data[name] = False
            elif annotation is str or (str in args and type(None) in args):
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    data[name] = str(value)
                elif value is None and annotation is str:
                    data[name] = ""
        if "confidence" in cls.model_fields and "confidence" in data:
            data["confidence"] = _coerce_confidence(data["confidence"])
        return data


class RouteResult(LLMModel):
    domain: str
    confidence: float = Field(default=0.0, ge=0, le=1)
    reason: str = ""



class IncidentFacts(LLMModel):
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


class ClassificationResult(LLMModel):
    section: str | None = None
    confidence: float = Field(default=0.0, ge=0, le=1)
    explanation: str = ""
    candidate_rank: int | None = Field(default=None, ge=1)
    missing_information: list[str] = Field(default_factory=list)

    @field_validator("candidate_rank", mode="before")
    @classmethod
    def _ignore_invalid_rank(cls, value: Any) -> Any:
        # The pipeline computes the rank itself; never fail on a bad model value.
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            return None
        return value



class VerificationResult(LLMModel):
    supported: bool = False
    confidence: float = Field(default=0.0, ge=0, le=1)
    reasoning: str = ""
    evidence_support: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)



EXTRACTION_SCHEMA_DESCRIPTION = "Extract facts only. Never invent facts or choose legal sections."
CLASSIFICATION_SCHEMA_DESCRIPTION = "Choose only an exact section from supplied candidates, or null."
VERIFICATION_SCHEMA_DESCRIPTION = "Verify only from supplied facts and supplied legal text; fail closed when weak."
