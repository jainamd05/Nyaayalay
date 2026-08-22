from .llm_utils import call_structured, pretty_json
from .retrieval import Candidate
from .schemas import VerificationResult


def verify(facts, proposed_section: str | None, candidates: list[Candidate]) -> VerificationResult:
    if not proposed_section:
        return VerificationResult(
            supported=False,
            confidence=0.0,
            reasoning="There is no proposed section to verify.",
        )

    candidate = next(
        (c for c in candidates if c.section == proposed_section),
        None,
    )

    if candidate is None:
        return VerificationResult(
            supported=False,
            confidence=0.0,
            reasoning="The proposed section is not present in the retrieved evidence.",
            contradictions=["Section not found among retrieved candidates."],
        )

    system = (
        "You are a verification layer for a grounded legal-information system. "
        "Decide whether the supplied provision is supported by the supplied facts "
        "and candidate text. Do not use outside legal knowledge."
    )

    prompt = f"""
Facts:
{pretty_json(facts)}

Proposed provision:
Act: {candidate.act}
Section: {candidate.section}
Title: {candidate.title}
Text: {candidate.text}
"""

    return call_structured(VerificationResult, system, prompt)
