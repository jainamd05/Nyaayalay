from nyayalay.pipeline import analyze_incident


TESTS = [
    (
        "CLEAR THEFT",
        "Someone secretly took my laptop from my room without my permission.",
    ),
    (
        "CYBER / POSSIBLY UNSUPPORTED",
        "Someone hacked my social media account and changed my password.",
    ),
    (
        "VAGUE INCIDENT",
        "Something bad happened to me and I need legal help.",
    ),
]


for name, incident in TESTS:
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)
    print("Incident:", incident)

    result = analyze_incident(incident)

    print("\nStatus:", result["status"])
    print("Message:", result["message"])

    if result["status"] == "ok":
        print(
            "Result:",
            result["result"]["act"],
            "Section",
            result["result"]["section"],
            "-",
            result["result"]["title"],
        )

    elif result["status"] == "unsupported":
        print("Route:", result["route"])

    else:
        print("Details:")
        print(result)