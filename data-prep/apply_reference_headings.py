"""
Fix section titles in an already-processed act using a reference PDF.

Use this when the official Act PDF is not available but another official
document with the same section numbering is, e.g. the Bill as introduced.

The reference is only used to *propose* each heading. A heading is accepted
only in the enacted Act's own wording: it must appear in the Act's extracted
text (where pypdf left the margin notes), either exactly or as a near
identical phrase, which is then copied from the Act text. Headings that
cannot be confirmed are left empty and reported; the reference text itself is
never copied into the corpus.

For each record the script also:
- puts back the first line of the body that the old parser stored as the
  title (BNSS/BSA layout), and
- removes margin notes, gazette page headers and margin citations from the
  text.

Usage:
    python data-prep/apply_reference_headings.py BSA path/to/reference.pdf
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

import parse_act_pdf as parser

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"

# Minimum similarity for a phrase in the Act text to count as the heading.
FUZZY_MIN_RATIO = 0.88
# Margin notes are often batched at page ends, several sections away. An
# exact match anywhere in the Act confirms the wording; fuzzy matches are
# only searched for near the section.
SEARCH_RADIUS = 10
STRIP_RADIUS = 10

# Headings the Act renamed relative to the reference, so similarity cannot
# find them. Each was read off the Act's own margin notes and is still
# checked to occur verbatim in the Act text before it is used.
MANUAL_HEADINGS = {
    # Act margin notes for 61-63: "Electronic or digital record. Special
    # provisions as to evidence relating to electronic record. Admissibility
    # of electronic records." (Bill: "Admissibility of electronic or digital
    # record.")
    "BSA": {61: "Electronic or digital record."},
}


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _words(text: str) -> list[str]:
    return text.split()


def find_heading(
    candidate: str, region: str, exact_only: bool = False
) -> tuple[str | None, float]:
    """
    Return the Act's wording of `candidate` found in `region`, and the
    similarity (1.0 for an exact match), or (None, best_ratio).
    """
    if not candidate:
        return None, 0.0

    pattern = r"(?<!\w)" + r"\s*".join(map(re.escape, _squash(candidate))) + r"(?!\w)"
    exact = re.search(pattern, region)
    if exact:
        return re.sub(r"\s+", " ", exact.group(0)).strip(), 1.0
    if exact_only:
        return None, 0.0

    target = " ".join(_words(candidate)).lower()
    words = _words(region)
    size = len(_words(candidate))
    best, best_ratio, best_span = None, 0.0, (0, 0)
    matcher = difflib.SequenceMatcher(autojunk=False)
    matcher.set_seq2(target)
    for width in range(max(1, size - 4), size + 3):
        for start in range(0, max(0, len(words) - width) + 1):
            first = words[start]
            # A margin note starts with a capital letter (a match starting
            # lowercase is a phrase inside the body text) and is not an
            # all-caps chapter name such as "BURDEN OF PROOF".
            if not first[:1].isupper():
                continue
            window = words[start:start + width]
            phrase = " ".join(window)
            if phrase.upper() == phrase:
                continue
            # A heading is one sentence: it ends at its full stop (or at the
            # word "section" before a number) and has no full stop inside.
            if candidate.endswith(".") and not (
                window[-1].endswith(".") or re.match(r"^sections?$", window[-1])
            ):
                continue
            if any(w.endswith(".") and not w.endswith("etc.") for w in window[:-1]):
                continue
            matcher.set_seq1(phrase.lower())
            if matcher.real_quick_ratio() < best_ratio or matcher.quick_ratio() < best_ratio:
                continue
            ratio = matcher.ratio()
            if ratio > best_ratio:
                best, best_ratio, best_span = phrase, ratio, (start, start + width)

    if best is not None and best_ratio >= FUZZY_MIN_RATIO:
        # "... mentioned in section" + "162." : keep a trailing section number.
        end = best_span[1]
        if re.search(r"\bsections?\.?$", best) and end < len(words) and re.match(r"^\d+\.?$", words[end]):
            best = best.rstrip(".") + " " + words[end]
        if candidate.endswith(".") and not best.endswith("."):
            best = best.rstrip(",;:") + "."
        return best, best_ratio
    return None, best_ratio


def reference_titles(pdf_path: Path) -> dict[int, str]:
    sections = parser.parse_sections(parser.extract_pages(pdf_path))
    return {int(s["section"]): s["title"] for s in sections if s["title"]}


def apply(act_code: str, reference_pdf: Path) -> dict:
    path = PROCESSED_DIR / f"{act_code.lower()}_2023_sections.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    by_number = {int(r["section"]): r for r in records}
    candidates = reference_titles(reference_pdf)

    # 1. Reassemble each section's full extracted text. The old parser split
    #    off the first line of the body as "title" unless it was a heading.
    full_text: dict[int, str] = {}
    for number, record in by_number.items():
        old_title = record.get("title") or ""
        candidate = candidates.get(number, "")
        title_was_heading = bool(old_title) and (
            find_heading(candidate, old_title)[0] is not None
        )
        parts = [record.get("text") or ""] if title_was_heading else [old_title, record.get("text") or ""]
        full_text[number] = " ".join(p for p in parts if p).strip()

    # 2. Confirm each proposed heading against the Act's own text.
    whole_act = parser.clean_body(" ".join(full_text[n] for n in sorted(full_text)))
    headings: dict[int, str] = {}
    report = {"exact": 0, "fuzzy": [], "unconfirmed": []}
    manual = MANUAL_HEADINGS.get(act_code, {})
    for number in sorted(by_number):
        candidate = manual.get(number) or candidates.get(number, "")
        # Page headers can split a margin note ("Facts admitted need not be
        # <page header> proved."), so search the text without them.
        region = parser.clean_body(" ".join(
            full_text[n]
            for n in range(number - SEARCH_RADIUS, number + SEARCH_RADIUS + 1)
            if n in full_text
        ))
        heading, ratio = find_heading(candidate, whole_act, exact_only=True)
        if heading is None:
            heading, ratio = find_heading(candidate, region)
        if heading is None:
            report["unconfirmed"].append((number, candidate, round(ratio, 2)))
        elif ratio == 1.0:
            report["exact"] += 1
            headings[number] = heading
        else:
            report["fuzzy"].append((number, candidate, heading, round(ratio, 2)))
            headings[number] = heading

    # 3. Clean the text: page furniture, then margin notes (the section's own
    #    heading always; neighbours' headings when long enough to be unambiguous).
    for number, record in by_number.items():
        text = parser.clean_body(full_text[number])
        own = headings.get(number)
        if own:
            own_pattern = r"(?<!\w)" + r"\s+".join(map(re.escape, own.split())) + r"(?!\w)"
            text = re.sub(own_pattern, " ", text)
        neighbours = [
            headings[n]
            for n in range(number - STRIP_RADIUS, number + STRIP_RADIUS + 1)
            if n in headings and n != number
        ]
        text = parser.remove_margin_notes(text, neighbours)
        record["text"] = re.sub(r"\s+", " ", text).strip()
        title = re.sub(r"\s+([.,;:])", r"\1", own or "")
        if title and not title.endswith((".", "—", ":")):
            title += "."
        record["title"] = title

    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    act_code, reference = sys.argv[1].upper(), Path(sys.argv[2])
    report = apply(act_code, reference)

    print(f"{act_code}: {report['exact']} headings confirmed exactly")
    print(f"{act_code}: {len(report['fuzzy'])} confirmed with the Act's wording differing:")
    for number, candidate, heading, ratio in report["fuzzy"]:
        print(f"  {number}: {heading!r}  (reference: {candidate!r}, {ratio})")
    print(f"{act_code}: {len(report['unconfirmed'])} not found in the Act text (title left empty):")
    for number, candidate, ratio in report["unconfirmed"]:
        print(f"  {number}: reference {candidate!r} (best similarity {ratio})")


if __name__ == "__main__":
    main()
