from .config import VERIFICATION_MIN_CONFIDENCE
from .llm_utils import call_structured, pretty_json
from .retrieval import Candidate
from .schemas import VerificationResult

def verify(facts, proposed_section: str | None, candidates: list[Candidate]) -> VerificationResult:
    if not proposed_section:
        return VerificationResult(
            supported=False, confidence=0.0,
            reasoning="There is no proposed section to verify."
        )

    candidate = next((c for c in candidates if c.section == proposed_section), None)
    if candidate is None:
        return VerificationResult(
            supported=False, confidence=0.0,
            reasoning="The proposed section is not present in retrieved evidence.",
            contradictions=["Section not found among retrieved candidates."],
        )

    system = (
        "You are the final verification gate. Verify only from supplied facts and "
        "supplied legal text. Do not rely on outside memory. Be conservative and "
        "fail closed when material information is missing or contradictory."
    )
    prompt = f"""
Facts:
{pretty_json(facts)}

Proposed provision:
Act: {candidate.act}
Section: {candidate.section}
Title: {candidate.title}
Text: {candidate.text}

Determine whether the provision is supported by the supplied evidence.
"""
    result = call_structured(VerificationResult, system, prompt)

    if result.confidence < VERIFICATION_MIN_CONFIDENCE:
        return result.model_copy(update={"supported": False})
    return result
