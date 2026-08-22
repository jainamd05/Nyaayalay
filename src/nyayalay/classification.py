from .config import MIN_CONFIDENCE
from .llm_utils import call_structured, pretty_json
from .retrieval import Candidate
from .schemas import ClassificationResult


def classify(facts, candidates: list[Candidate]) -> ClassificationResult:
    if not candidates:
        return ClassificationResult(
            section=None,
            confidence=0.0,
            explanation="No grounded candidates were retrieved.",
        )

    candidate_text = "\n\n".join(
        f"Candidate {i+1}\n"
        f"Act: {c.act}\n"
        f"Section: {c.section}\n"
        f"Title: {c.title}\n"
        f"Text: {c.text}"
        for i, c in enumerate(candidates)
    )

    system = (
        "You select a legal provision only from supplied candidates. "
        "Never invent a section. If no candidate is sufficiently supported, "
        "return section=null."
    )

    prompt = f"""
Facts:
{pretty_json(facts)}

Candidates:
{candidate_text}
"""

    result = call_structured(ClassificationResult, system, prompt)

    valid_sections = {c.section for c in candidates}
    if result.section not in valid_sections:
        return ClassificationResult(
            section=None,
            confidence=0.0,
            explanation="The model selected a section outside the retrieved candidates.",
        )

    if result.confidence < MIN_CONFIDENCE:
        return ClassificationResult(
            section=result.section,
            confidence=result.confidence,
            explanation=result.explanation,
        )

    return result
