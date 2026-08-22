from .config import MIN_CONFIDENCE
from .extraction import extract_facts
from .classification import classify
from .retrieval import retrieve_candidates
from .router import route_domain
from .verification import verify


def analyze_incident(incident: str) -> dict:
    route = route_domain(incident)

    if route.domain == "unsupported":
        return {
            "status": "unsupported",
            "message": "This incident does not fall within a currently supported legal domain.",
            "route": route.model_dump(),
        }

    facts = extract_facts(incident, route.domain)

    query = f"{facts.summary}\n" + "\n".join(facts.alleged_conduct)
    candidates = retrieve_candidates(query, route.domain)

    if not candidates:
        return {
            "status": "no_evidence",
            "message": "No grounded legal provisions were retrieved for this domain.",
            "route": route.model_dump(),
            "facts": facts.model_dump(),
        }

    classification = classify(facts, candidates)

    if not classification.section or classification.confidence < MIN_CONFIDENCE:
        return {
            "status": "low_confidence",
            "message": "No sufficiently confident provision could be selected from the retrieved evidence.",
            "route": route.model_dump(),
            "facts": facts.model_dump(),
            "candidates": [c.__dict__ for c in candidates],
            "classification": classification.model_dump(),
        }

    verification = verify(facts, classification.section, candidates)

    if not verification.supported or verification.confidence < MIN_CONFIDENCE:
        return {
            "status": "verification_failed",
            "message": "The proposed provision could not be sufficiently verified against the retrieved evidence.",
            "route": route.model_dump(),
            "facts": facts.model_dump(),
            "classification": classification.model_dump(),
            "verification": verification.model_dump(),
        }

    selected = next(c for c in candidates if c.section == classification.section)

    return {
        "status": "ok",
        "route": route.model_dump(),
        "facts": facts.model_dump(),
        "result": {
            "act": selected.act,
            "section": selected.section,
            "title": selected.title,
            "text": selected.text,
        },
        "classification": classification.model_dump(),
        "verification": verification.model_dump(),
    }


if __name__ == "__main__":
    incident = input("Describe the incident: ").strip()
    print(analyze_incident(incident))
