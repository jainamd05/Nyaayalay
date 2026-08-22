from nyayalay.pipeline import analyze_incident


def test_pipeline_function_exists():
    assert callable(analyze_incident)
