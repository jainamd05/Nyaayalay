from nyayalay.classification import classify


def test_empty_candidates_is_safe():
    result = classify({}, [])
    assert result.section is None
    assert result.confidence == 0.0


import pytest

from nyayalay.classification import match_candidate_section
from nyayalay.retrieval import Candidate


def _candidates(*sections):
    return [Candidate(act="BNS", section=s, title="", text="") for s in sections]


@pytest.mark.parametrize(
    "raw",
    ["309", " 309 ", "Section 309", "BNS 309", "BNS Section 309", "s. 309",
     "Sec. 309", "309(1)", "Section 309(4)", "Bharatiya Nyaya Sanhita, 2023, Section 309",
     "Candidate 2"],
)
def test_section_variants_match_retrieved_candidate(raw):
    assert match_candidate_section(raw, _candidates("303", "309", "311")) == "309"


@pytest.mark.parametrize("raw", [None, "", "999", "Candidate 9", "robbery"])
def test_unknown_sections_do_not_match(raw):
    assert match_candidate_section(raw, _candidates("303", "309")) is None
