from nyayalay.retrieval import retrieve_candidates


def test_unknown_domain_returns_empty():
    assert retrieve_candidates("test", "unknown-domain") == []
