from nyayalay.pipeline import analyze_incident


def _clean_candidate(candidate: dict) -> dict:
    """Return only lightweight candidate information for the API."""
    return {
        "act": candidate.get("act"),
        "section": candidate.get("section"),
        "title": candidate.get("title"),
        "retrieval_score": candidate.get("retrieval_score"),
    }


def _clean_result(result: dict) -> dict:
    """
    Convert the internal Nyayalay pipeline response into a
    frontend-friendly API response without changing the core engine.
    """
    cleaned = {
        "status": result.get("status"),
        "message": result.get("message"),
        "route": result.get("route"),
        "facts": result.get("facts"),
        "classification": result.get("classification"),
        "verification": result.get("verification"),
    }

    # Keep a lightweight candidate list for transparency/debugging.
    candidates = result.get("candidates")
    if candidates is not None:
        cleaned["candidates"] = [
            _clean_candidate(candidate)
            for candidate in candidates
        ]

    # Keep the selected provision authoritative and complete.
    selected = result.get("result")
    if selected is not None:
        cleaned["result"] = {
            "act": selected.get("act"),
            "section": selected.get("section"),
            "title": selected.get("title"),
            "text": selected.get("text"),
        }

    return cleaned


def analyze(incident: str) -> dict:
    """
    Thin service boundary between HTTP and the core Nyayalay engine.
    """
    result = analyze_incident(incident)
    return _clean_result(result)