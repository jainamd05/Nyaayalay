import re

from .llm_utils import call_structured, pretty_json
from .retrieval import Candidate
from .schemas import ClassificationResult


def _section_key(value: str | None) -> str:
    """Normalise "Section 303", "BNS s. 303", "303." etc. to "303"."""
    if not value:
        return ""
    key = value.strip().lower()
    key = re.sub(r"^(?:(?:bns|bnss|bsa)\b[\s,.:-]*)?", "", key)
    key = re.sub(r"^(?:section|sec\.?|s\.)\s*", "", key)
    return key.strip(" .:-").replace(" ", "")


def match_candidate(section: str | None, candidates: list[Candidate]) -> Candidate | None:
    key = _section_key(section)
    if not key:
        return None
    return next((c for c in candidates if _section_key(c.section) == key), None)

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
In the "section" field return only the exact Section value shown for the
chosen candidate (for example "303"), without the Act name or the word "Section".
"""
    result = call_structured(ClassificationResult, system, prompt)
    selected = match_candidate(result.section, candidates)

    if selected is None:
        return ClassificationResult(
            section=None, confidence=0.0,
            explanation=(
                result.explanation
                if result.section is None
                else "The model did not select an exact retrieved section."
            ),
            missing_information=result.missing_information,
        )

    rank = candidates.index(selected) + 1
    return result.model_copy(
        update={"section": selected.section, "candidate_rank": rank}
    )

