from nyayalay import classification, llm_utils
from nyayalay.classification import match_candidate
from nyayalay.retrieval import Candidate
from nyayalay.schemas import (
    ClassificationResult,
    IncidentFacts,
    RouteResult,
    VerificationResult,
)


def _candidate(section: str) -> Candidate:
    return Candidate(act="BNS", section=section, title="Theft.", text="...")


def test_section_matching_tolerates_llm_formatting():
    candidates = [_candidate("304"), _candidate("303")]
    for answer in ["303", "Section 303", "BNS Section 303", "s. 303", "303."]:
        assert match_candidate(answer, candidates).section == "303"
    assert match_candidate("999", candidates) is None
    assert match_candidate(None, candidates) is None


def test_schemas_coerce_common_llm_quirks():
    assert RouteResult(domain=" Criminal ", confidence="90%", reason="x").domain == "criminal"
    result = ClassificationResult(section=303, confidence=85, explanation="x")
    assert result.section == "303" and result.confidence == 0.85
    assert VerificationResult(supported=True, confidence=0.8, reasoning="x").confidence == 0.8

    facts = IncidentFacts.model_validate(
        {"summary": "x", "harm": None, "evidence": "CCTV", "digital_element": None}
    )
    assert facts.harm == [] and facts.evidence == ["CCTV"] and facts.digital_element is False


def test_extract_json_strips_code_fences():
    assert llm_utils._extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert llm_utils._extract_json('Here you go: {"a": 1} thanks') == '{"a": 1}'


def test_classify_returns_canonical_section(monkeypatch):
    monkeypatch.setattr(
        classification,
        "call_structured",
        lambda *a, **k: ClassificationResult(
            section="BNS Section 303", confidence=0.9, explanation="fits"
        ),
    )
    result = classification.classify(
        IncidentFacts(summary="x"), [_candidate("304"), _candidate("303")]
    )
    assert result.section == "303"
    assert result.candidate_rank == 2
