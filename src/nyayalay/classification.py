import re

from .llm_utils import call_structured, pretty_json
from .retrieval import Candidate
from .schemas import ClassificationResult

_ACT_OR_LABEL_RE = re.compile(
    r"\b(?:bns|bnss|bsa|bharatiya\s+\w+\s+\w+)\b(?:\s*,?\s*20\d\d\b)?"
    r"|\b(?:section|sec|s)\b\.?",
    re.IGNORECASE,
)
_CANDIDATE_RE = re.compile(r"^\s*candidate\s*#?\s*(\d+)\s*$", re.IGNORECASE)


def _normalise_section(value: str) -> str:
    value = _ACT_OR_LABEL_RE.sub(" ", value)
    value = value.replace("§", " ")
    value = re.sub(r"[\s,:;]+", "", value)
    return value.strip(".-").lower()


def match_candidate_section(raw: str | None, candidates: list[Candidate]) -> str | None:
    """
    Map the section string returned by the LLM onto the exact section
    identifier of one of the retrieved candidates, or None if there is none.

    Accepts forms such as "309", "Section 309", "BNS 309", "s. 309",
    "309(1)" (sub-section of 309) and "Candidate 2".
    """
    if raw is None:
        return None
    raw = str(raw).strip()
    if not raw:
        return None

    sections = [c.section for c in candidates]
    if raw in sections:
        return raw

    by_rank = _CANDIDATE_RE.match(raw)
    if by_rank:
        index = int(by_rank.group(1)) - 1
        return sections[index] if 0 <= index < len(sections) else None

    normalised = {_normalise_section(s): s for s in sections}
    wanted = _normalise_section(raw)
    if wanted in normalised:
        return normalised[wanted]

    # "309(1)" -> "309": the model named a sub-section of a retrieved section.
    base = re.sub(r"\(.*$", "", wanted)
    if base and base in normalised:
        return normalised[base]

    return None


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
        "Do not use outside legal knowledge. In the `section` field return only "
        "the section number exactly as written after 'Section:' (for example \"309\")."
    )
    prompt = f"""
Facts:
{pretty_json(facts)}

Retrieved candidates:
{candidate_text}

Select the single best supported candidate, or null.
"""
    result = call_structured(ClassificationResult, system, prompt)

    if result.section is None:
        return result.model_copy(update={"candidate_rank": None})

    section = match_candidate_section(result.section, candidates)
    if section is None:
        return ClassificationResult(
            section=None, confidence=0.0,
            explanation="The model did not select an exact retrieved section.",
            missing_information=result.missing_information,
        )

    rank = next(i + 1 for i, c in enumerate(candidates) if c.section == section)
    return result.model_copy(update={"section": section, "candidate_rank": rank})
