from nyayalay.pipeline import analyze_incident


def analyze(incident: str) -> dict:
    """
    Thin service boundary between HTTP and the core Nyayalay engine.

    Keeping this separate means FastAPI routes do not need to know
    how routing, extraction, retrieval, classification, or verification work.
    """
    return analyze_incident(incident)
