ROUTABLE_DOMAINS = {
    "criminal": {
        "label": "Criminal offences",
        "description": (
            "Substantive criminal conduct such as theft, hurt, assault, "
            "sexual offences, offences against property, and related offences."
        ),
        "acts": ["BNS"],
    },
    "criminal_procedure": {
        "label": "Criminal procedure",
        "description": (
            "Procedure after or around an alleged offence, including arrest, "
            "investigation, bail, trial procedure, summons, warrants, and related procedure."
        ),
        "acts": ["BNSS"],
    },
    "evidence": {
        "label": "Evidence",
        "description": (
            "Questions about admissibility, relevance, documentary/electronic evidence, "
            "witnesses, proof, burden of proof, and related evidence rules."
        ),
        "acts": ["BSA"],
    },
}

def acts_for_domain(domain: str) -> list[str]:
    entry = ROUTABLE_DOMAINS.get(domain)
    if not entry:
        return []
    return list(entry["acts"])
