from nyayalay.pipeline import analyze_incident, _retrieval_query
from nyayalay.schemas import IncidentFacts

def test_pipeline_function_exists():
    assert callable(analyze_incident)

def test_retrieval_query_contains_fact_signals():
    facts = IncidentFacts(
        summary="Laptop was taken",
        alleged_conduct=["entered home", "took laptop"],
        property_or_money=True,
        property_items=["laptop"],
    )
    query = _retrieval_query(facts)
    assert "Laptop was taken" in query
    assert "laptop" in query
    assert "property or money involved" in query
