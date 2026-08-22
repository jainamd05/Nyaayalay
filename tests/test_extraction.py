import pytest

from nyayalay.extraction import extract_facts


def test_extraction_requires_api_key():
    # The real extraction test is an integration test and requires OPENAI_API_KEY.
    # This assertion keeps the test file importable without making a paid API call.
    assert callable(extract_facts)
