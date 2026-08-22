from .domains import ROUTABLE_DOMAINS
from .llm_utils import call_structured
from .schemas import RouteResult


def route_domain(incident: str) -> RouteResult:
    domain_lines = "\n".join(
        f"- {name}: {entry['label']} — {entry['description']}"
        for name, entry in ROUTABLE_DOMAINS.items()
    )

    system = (
        "You are a legal-domain router. "
        "Select only a domain from the supplied supported domains. "
        "If no supported domain fits, return domain='unsupported'. "
        "Do not classify the specific legal section."
    )

    prompt = f"""
Supported domains:
{domain_lines}
- unsupported: no supported domain fits.

Incident:
{incident}
"""

    return call_structured(RouteResult, system, prompt)
