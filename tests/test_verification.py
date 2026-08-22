from nyayalay.verification import verify


def test_missing_proposal_fails_closed():
    result = verify({}, None, [])
    assert result.supported is False
    assert result.confidence == 0.0
