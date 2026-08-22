from .llm_utils import call_structured
from .schemas import IncidentFacts


def extract_facts(incident: str, domain: str) -> IncidentFacts:
    system = (
        "You extract factual information from legal incident descriptions. "
        "Do not give legal advice and do not choose a section. "
        "Do not invent facts."
    )

    prompt = f"""
Legal domain: {domain}

{incident}

Extract the structured facts needed for downstream retrieval.
"""

    return call_structured(IncidentFacts, system, prompt)
