ROUTABLE_DOMAINS = {
    "criminal": {
        "label": "Criminal Law",
        "acts": ["BNS", "BNSS", "BSA"],
        "status": "partial",
        "description": "Offences, criminal procedure, and evidence.",
    },
}

def get_domain(name: str):
    return ROUTABLE_DOMAINS.get(name)

def supported_domains():
    return list(ROUTABLE_DOMAINS.keys())

def acts_for_domain(domain: str):
    entry = get_domain(domain)
    return entry["acts"] if entry else []
