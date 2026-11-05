import pytest

from nyayalay.llm_utils import LLMOutputError, parse_structured
from nyayalay.schemas import (
    ClassificationResult,
    IncidentFacts,
    RouteResult,
    VerificationResult,
)


def test_parses_json_inside_code_fence():
    text = '```json\n{"domain": "criminal", "confidence": 0.9, "reason": "theft"}\n```'
    result = parse_structured(RouteResult, text)
    assert result.domain == "criminal"


def test_unwraps_single_key_wrapper():
    text = '{"RouteResult": {"domain": "evidence", "confidence": 0.8, "reason": "x"}}'
    assert parse_structured(RouteResult, text).domain == "evidence"


def test_percentage_confidence_is_normalised():
    result = parse_structured(RouteResult, '{"domain": "criminal", "confidence": 85, "reason": ""}')
    assert result.confidence == pytest.approx(0.85)
    result = parse_structured(VerificationResult, '{"supported": true, "confidence": "90%"}')
    assert result.confidence == pytest.approx(0.9)


def test_null_lists_and_booleans_become_defaults():
    text = (
        '{"summary": "Phone snatched", "alleged_conduct": null, "harm": "fear", '
        '"property_or_money": null, "money_amount": 5000, "evidence": [null, "CCTV"]}'
    )
    facts = parse_structured(IncidentFacts, text)
    assert facts.alleged_conduct == []
    assert facts.harm == ["fear"]
    assert facts.property_or_money is False
    assert facts.money_amount == "5000"
    assert facts.evidence == ["CCTV"]


def test_numeric_section_and_bad_rank_are_tolerated():
    result = parse_structured(
        ClassificationResult,
        '{"section": 309, "confidence": 0.8, "explanation": "x", "candidate_rank": 0}',
    )
    assert result.section == "309"
    assert result.candidate_rank is None


def test_missing_confidence_fails_closed():
    result = parse_structured(VerificationResult, '{"reasoning": "unclear"}')
    assert result.supported is False
    assert result.confidence == 0.0


@pytest.mark.parametrize("text", ["", "not json", "[1, 2]"])
def test_unusable_output_raises(text):
    with pytest.raises(LLMOutputError):
        parse_structured(RouteResult, text)
