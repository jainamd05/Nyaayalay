from .classification import classify
from .config import (
    CLASSIFICATION_MIN_CONFIDENCE,
    ROUTER_MIN_CONFIDENCE,
    VERIFICATION_MIN_CONFIDENCE,
)
from .extraction import extract_facts
from .retrieval import Candidate, retrieve_candidates
from .router import route_domain
from .verification import verify

def _candidate_dict(c: Candidate) -> dict:
    return {
        "act": c.act, "section": c.section, "title": c.title, "text": c.text,
        "distance": c.distance,
        "semantic_score": round(c.semantic_score, 4),
        "lexical_score": round(c.lexical_score, 4),
        "retrieval_score": round(c.retrieval_score, 4),
    }

def _retrieval_query(facts) -> str:
    parts = [
        facts.summary, facts.event_type or "",
        " ".join(facts.alleged_conduct),
        " ".join(facts.harm),
        " ".join(facts.property_items),
        " ".join(facts.weapons_or_tools),
        " ".join(facts.evidence),
    ]
    if facts.property_or_money:
        parts.append("property or money involved")
    if facts.violence_or_threat:
        parts.append("violence or threat involved")
    if facts.deception_or_fraud:
        parts.append("deception or fraud involved")
    if facts.digital_element:
        parts.append("digital element involved")
    return "\n".join(p for p in parts if p).strip()

def analyze_incident(incident: str) -> dict:
    route = route_domain(incident)
    if route.domain == "unsupported":
        return {
            "status": "unsupported",
            "message": "The incident could not be safely mapped to a supported legal domain.",
            "route": route.model_dump(),
        }

    facts = extract_facts(incident, route.domain)
    candidates = retrieve_candidates(_retrieval_query(facts), route.domain)

    if not candidates:
        return {
            "status": "no_evidence",
            "message": "No grounded legal provisions were retrieved for this domain.",
            "route": route.model_dump(),
            "facts": facts.model_dump(),
        }

    classification = classify(facts, candidates)
    if (
        not classification.section
        or classification.confidence < CLASSIFICATION_MIN_CONFIDENCE
    ):
        return {
            "status": "low_confidence",
            "message": "No sufficiently confident provision could be selected.",
            "route": route.model_dump(),
            "facts": facts.model_dump(),
            "candidates": [_candidate_dict(c) for c in candidates],
            "classification": classification.model_dump(),
        }

    verification = verify(facts, classification.section, candidates)
    if (
        not verification.supported
        or verification.confidence < VERIFICATION_MIN_CONFIDENCE
    ):
        return {
            "status": "verification_failed",
            "message": "The proposed provision could not be sufficiently verified.",
            "route": route.model_dump(),
            "facts": facts.model_dump(),
            "candidates": [_candidate_dict(c) for c in candidates],
            "classification": classification.model_dump(),
            "verification": verification.model_dump(),
        }

    selected = next(c for c in candidates if c.section == classification.section)
    return {
        "status": "ok",
        "message": "A provision was selected and passed verification.",
        "route": route.model_dump(),
        "facts": facts.model_dump(),
        "candidates": [_candidate_dict(c) for c in candidates],
        "result": {
            "act": selected.act,
            "section": selected.section,
            "title": selected.title,
            "text": selected.text,
        },
        "classification": classification.model_dump(),
        "verification": verification.model_dump(),
    }
