import importlib.util
import sys
from pathlib import Path

DATA_PREP = Path(__file__).resolve().parents[1] / "data-prep"
if str(DATA_PREP) not in sys.path:
    sys.path.insert(0, str(DATA_PREP))
spec = importlib.util.spec_from_file_location("apply_reference_headings", DATA_PREP / "apply_reference_headings.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
find_heading = module.find_heading


def test_exact_match_returns_act_wording():
    region = "... of the original. Facts admitted need not be proved. Proof of facts by oral evidence."
    assert find_heading("Facts admitted need not be proved.", region) == ("Facts admitted need not be proved.", 1.0)


def test_fuzzy_match_uses_act_wording_not_reference():
    region = "relevant fact. Facts which are occasion, cause or effect of facts in issue or relevant facts. Motive."
    heading, ratio = find_heading("Facts which are the occasion, cause or effect of facts in issue or relevant facts.", region)
    assert heading == "Facts which are occasion, cause or effect of facts in issue or relevant facts."
    assert 0.88 <= ratio < 1


def test_body_phrases_and_chapter_names_are_not_headings():
    # Lowercase start = phrase inside the body; all caps = chapter name.
    assert find_heading("Admissibility of electronic or digital record.",
                        "shall apply to deny the admissibility of an electronic or digital record in the evidence.")[0] is None
    assert find_heading("Burden of proof.", "CHAPTER VII OF THE BURDEN OF PROOF. Whoever desires") [0] is None


def test_heading_stops_at_its_full_stop_and_keeps_section_number():
    region = "Cases in which statement of relevant fact by person who is dead or cannot be found, etc., is relevant. (e) when."
    assert find_heading(
        "Cases in which statement of facts in issue or relevant fact by person who is dead or cannot be found, etc., is relevant.",
        region,
    )[0] == "Cases in which statement of relevant fact by person who is dead or cannot be found, etc., is relevant."
    region = "Testimony to facts stated in document mentioned in section 162. Refreshing memory."
    assert find_heading("Testimony to facts stated in document mentioned in section159.", region)[0] == (
        "Testimony to facts stated in document mentioned in section 162."
    )
