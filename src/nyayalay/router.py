from .config import ROUTER_MIN_CONFIDENCE
from .domains import ROUTABLE_DOMAINS
from .llm_utils import call_structured
from .schemas import RouteResult

def route_domain(incident: str) -> RouteResult:
    incident = incident.strip()
    if len(incident) < 10:
        return RouteResult(
            domain="unsupported",
            confidence=1.0,
            reason="Incident description is too short to route safely.",
        )

    domains = "\n".join(
        f"- {name}: {entry['label']} — {entry['description']}"
        for name, entry in ROUTABLE_DOMAINS.items()
    )
    system = (
        "You are the first safety gate of a legal-information system. "
        "Choose exactly one registered domain or unsupported. "
        "Do not choose a legal section. Do not invent domains."
    )
    prompt = f"""
Supported domains:
{domains}

Allowed domains: {", ".join(ROUTABLE_DOMAINS)}, unsupported

Incident:
{incident}
"""
    result = call_structured(RouteResult, system, prompt)

    if result.domain not in ROUTABLE_DOMAINS:
        return RouteResult(
            domain="unsupported",
            confidence=0.0,
            reason="Model returned a domain that is not registered as supported.",
        )

    if result.confidence < ROUTER_MIN_CONFIDENCE:
        return RouteResult(
            domain="unsupported",
            confidence=result.confidence,
            reason="Routing confidence is below the safety threshold.",
        )
    return result
