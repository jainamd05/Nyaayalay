from .llm_utils import call_structured
from .schemas import IncidentFacts

def extract_facts(incident: str, domain: str) -> IncidentFacts:
    system = (
        "Extract factual information only. Do not give legal advice, name sections, "
        "classify offences, or invent facts. If intent is not supported, use null. "
        "Record important missing or uncertain facts."
    )
    prompt = f"""
Legal domain: {domain}

Incident:
{incident}

Extract structured facts for downstream retrieval and verification.
"""
    return call_structured(IncidentFacts, system, prompt)
