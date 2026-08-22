from nyayalay.classification import classify


def test_empty_candidates_is_safe():
    result = classify({}, [])
    assert result.section is None
    assert result.confidence == 0.0
