from .config import CLASSIFICATION_MIN_CONFIDENCE
from .llm_utils import call_structured, pretty_json
from .retrieval import Candidate
from .schemas import ClassificationResult

def classify(facts, candidates: list[Candidate]) -> ClassificationResult:
    if not candidates:
        return ClassificationResult(
            section=None, confidence=0.0,
            explanation="No grounded candidates were retrieved."
        )

    candidate_text = "\n\n".join(
        f"Candidate {i+1}\nAct: {c.act}\nSection: {c.section}\n"
        f"Title: {c.title}\nRetrieval score: {c.retrieval_score:.3f}\nText: {c.text}"
        for i, c in enumerate(candidates)
    )

    system = (
        "Select a provision only from supplied candidates. Never invent or rename "
        "a section. If none is supported by the facts, return section=null. "
        "Do not use outside legal knowledge."
    )
    prompt = f"""
Facts:
{pretty_json(facts)}

Retrieved candidates:
{candidate_text}

Select the single best supported candidate, or null.
"""
    result = call_structured(ClassificationResult, system, prompt)
    valid = {c.section for c in candidates}

    if result.section not in valid:
        return ClassificationResult(
            section=None, confidence=0.0,
            explanation="The model did not select an exact retrieved section.",
            missing_information=result.missing_information,
        )

    rank = next(
        i + 1 for i, c in enumerate(candidates) if c.section == result.section
    )
    return result.model_copy(update={"candidate_rank": rank})

