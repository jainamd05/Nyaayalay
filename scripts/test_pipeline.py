from pprint import pprint

from nyayalay.pipeline import analyze_incident


incident = (
    "A person threatened me and forcefully took away "
    "my mobile phone and wallet."
)

result = analyze_incident(incident)

pprint(result, width=120)