"""
Parse an official India Code / Gazette PDF of BNS, BNSS or BSA into section records.

Layout of these PDFs, and how the parser handles it:

1. An *Arrangement of Sections* lists every section as "N. Heading." near the
   start. This is the authoritative source for section titles.
2. The enacted text follows and numbers sections again from 1.
   - BNS puts the heading inline: "303. Theft.—(1) Whoever ...". Long
     headings wrap onto the next line.
   - BNSS and BSA have no inline heading ("3. Evidence may be given ...").
     The heading is a *margin note* that text extraction emits as a loose
     line somewhere later, sometimes batched into a later section.
3. Trailing material (Statement of Objects and Reasons, schedules) may number
   paragraphs from 1 again, and footnotes such as "1. 1st day of July ..."
   look like section headings.

So the parser splits the numbered headings into *runs* (each restart at 1
begins a new run). It takes the run with the most text as the enacted body
and the longest run before it as the arrangement. Titles come from the
arrangement, and margin notes plus page furniture are stripped from the body.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "raw" / "source_pdfs"
TEXT_DIR = ROOT / "data" / "raw" / "source_text"
PROCESSED_DIR = ROOT / "data" / "processed"

SECTION_RE = re.compile(r"^\s*(\d{1,3})\.\s*(.+?)\s*$")
CHAPTER_RE = re.compile(r"^\s*CHAPTER\s+([IVXLCDM]+)\s*$", re.I)
PART_RE = re.compile(r"^\s*PART\s+([IVXLCDM]+)\s*$", re.I)

# A heading that does not follow its predecessor by at most this much is
# treated as ordinary text (e.g. a cross-reference that wrapped to line start).
MAX_SECTION_GAP = 3
# A "1." line only starts a new run once the current run is this long;
# earlier "1." lines are footnotes on the first pages of the body.
MIN_RUN_BEFORE_RESET = 10

# Page furniture and margin citations that pypdf mixes into the text.
PAGE_ARTIFACT_PATTERNS = [
    re.compile(r"_{3,}"),
    # Odd pages: "Sec. 1] THE GAZETTE OF INDIA EXTRAORDINARY 3";
    # even pages: "4 THE GAZETTE OF INDIA EXTRAORDINARY [Part II—".
    re.compile(r"(?:\b\d{1,4}\s+)?\bTHE GAZETTE OF INDIA EXTRAORDINARY\b(?:\s*\d{1,4}\b)?"),
    re.compile(r"\[\s*Part\s+II\s*[—–-]+\s*(?:Sec\.\s*\d\s*\]?)?"),
    re.compile(r"\bSec\.\s*\d\s*\]"),
    # Margin citations of other Acts ("21 of 2000."), but not "(21 of 2000)".
    re.compile(r"(?<![(\w])\d{1,3} of (?:18|19|20)\d\d\.(?!\))"),
]
ARRANGEMENT_NOISE_RE = re.compile(
    r"^(?:SECTIONS?|ARRANGEMENT OF SECTIONS|[ivxlcdm]+|\d+)$", re.I
)
INLINE_TITLE_SPLIT_RE = re.compile(r"\.\s*[—–-]\s*")


def normalize_line(line: str) -> str:
    line = line.replace("­", "")
    line = line.replace("‐", "-")
    line = line.replace("‑", "-")
    line = line.replace("–", "–")
    line = line.replace("—", "—")
    line = re.sub(r"[ \t]+", " ", line)
    return line.strip()


def extract_pages(pdf_path: Path) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        lines = [normalize_line(line) for line in text.splitlines()]
        pages.append("\n".join(line for line in lines if line))
    return pages


def is_section_heading(line: str) -> bool:
    match = SECTION_RE.match(line)
    if not match:
        return False

    number = int(match.group(1))
    # Section numbers in these three Acts are small enough that a 1-999
    # match is useful, while avoiding ordinary numbered sub-clauses.
    return 1 <= number <= 999


def split_title_and_body(heading_line: str) -> tuple[str, str, str]:
    """Split an inline "N. Title.—Body" heading line (BNS style)."""
    match = SECTION_RE.match(heading_line)
    if not match:
        raise ValueError(f"Not a section heading: {heading_line}")

    number = match.group(1)
    rest = match.group(2).strip()

    dash_match = INLINE_TITLE_SPLIT_RE.search(rest)
    if dash_match:
        title = rest[:dash_match.start() + 1].strip()
        body = rest[dash_match.end():].strip()
    else:
        title = rest
        body = ""

    return f"Section {number}", title, body


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _is_uppercase_line(line: str) -> bool:
    letters = [c for c in line if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def remove_page_artifacts(text: str) -> str:
    for pattern in PAGE_ARTIFACT_PATTERNS:
        text = pattern.sub(" ", text)
    return text


def clean_body(text: str) -> str:
    text = remove_page_artifacts(text)
    text = re.sub(r"\s+", " ", text)
    # Remove a trailing page number left by extraction.
    text = re.sub(r"\s+\d{1,3}\s*$", "", text)
    return text.strip()


def strip_title_prefix(text: str, title: str) -> str | None:
    """
    If `text` starts with `title` (ignoring whitespace differences, e.g. a
    wrapped heading or "which .—"), return the text after it, without the
    ".—" separator. Otherwise return None.
    """
    target = _squash(title).rstrip(".")
    if not target:
        return None

    matched = 0
    index = 0
    while index < len(text) and matched < len(target):
        char = text[index]
        if not char.isspace():
            if char != target[matched]:
                return None
            matched += 1
        index += 1

    if matched < len(target):
        return None

    remainder = text[index:]
    separator = re.match(r"\s*\.?\s*[—–-]\s*", remainder)
    if separator:
        return remainder[separator.end():].strip()
    if re.match(r"\s*\.", remainder):
        return re.sub(r"^\s*\.\s*", "", remainder).strip()
    # The text only *started* with words of the title (e.g. "Theft" in
    # "Theft is ..."): not a heading.
    return None


def remove_margin_notes(text: str, titles: Iterable[str]) -> str:
    """Delete margin-note headings that extraction mixed into the body."""
    for title in titles:
        words = title.split()
        # Short titles ("Theft.") could also be ordinary sentences.
        if len(words) < 3:
            continue
        pattern = r"(?<!\w)" + r"\s+".join(map(re.escape, words)) + r"(?!\w)"
        text = re.sub(pattern, " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _split_into_runs(lines: Iterable[str]) -> list[list[dict]]:
    """Group numbered headings (plus their following lines) into runs."""
    runs: list[list[dict]] = []
    run: list[dict] | None = None
    entry: dict | None = None
    chapter = None
    part = None
    in_chapter_name = False

    for raw_line in lines:
        line = normalize_line(raw_line)
        if not line:
            continue

        part_match = PART_RE.match(line)
        if part_match:
            part = f"Part {part_match.group(1)}"
            in_chapter_name = True
            continue

        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            chapter = f"Chapter {chapter_match.group(1)}"
            in_chapter_name = True
            continue

        # Chapter/part names ("OF OFFENCES AGAINST PROPERTY") are uppercase
        # lines right after the CHAPTER line; they belong to no section.
        if in_chapter_name and _is_uppercase_line(line):
            continue
        in_chapter_name = False

        if is_section_heading(line):
            match = SECTION_RE.match(line)
            number = int(match.group(1))
            last = run[-1]["number"] if run else None

            starts_run = run is None or (
                number == 1 and len(run) >= MIN_RUN_BEFORE_RESET
            )
            continues_run = last is not None and last < number <= last + MAX_SECTION_GAP

            if starts_run or continues_run:
                if starts_run:
                    run = []
                    runs.append(run)
                entry = {
                    "number": number,
                    "rest": match.group(2).strip(),
                    "lines": [],
                    "chapter": chapter,
                    "part": part,
                }
                run.append(entry)
                continue

        if entry is not None:
            entry["lines"].append(line)

    return runs


def _run_text_length(run: list[dict]) -> int:
    return sum(len(e["rest"]) + sum(len(x) for x in e["lines"]) for e in run)


def _arrangement_titles(run: list[dict]) -> dict[int, str]:
    titles = {}
    for entry in run:
        parts = [entry["rest"]]
        for line in entry["lines"]:
            if _is_uppercase_line(line) or ARRANGEMENT_NOISE_RE.match(line):
                break
            parts.append(line)
        title = clean_body(" ".join(parts))
        title = re.sub(r"\s+([.,;:])", r"\1", title)
        if title:
            titles[entry["number"]] = title
    return titles


def parse_sections(pages: Iterable[str]) -> list[dict]:
    lines: list[str] = []
    for page in pages:
        lines.extend(page.splitlines())

    runs = _split_into_runs(lines)
    if not runs:
        return []

    body_index = max(range(len(runs)), key=lambda i: _run_text_length(runs[i]))
    body = runs[body_index]

    arrangement: dict[int, str] = {}
    earlier = runs[:body_index]
    if earlier:
        candidate = max(earlier, key=len)
        titles = _arrangement_titles(candidate)
        body_numbers = {e["number"] for e in body}
        # Only trust it if it actually lists most of the body's sections.
        if len(body_numbers & set(titles)) >= 0.5 * len(body_numbers):
            arrangement = titles

    sections: list[dict] = []
    for entry in body:
        number = entry["number"]
        joined = " ".join([entry["rest"], *entry["lines"]])
        title = arrangement.get(number)

        if title:
            text = strip_title_prefix(joined, title)
            if text is None:
                text = joined
        else:
            _, inline_title, first_body = split_title_and_body(
                f"{number}. {entry['rest']}"
            )
            if first_body:
                title = inline_title
                text = " ".join([first_body, *entry["lines"]])
            else:
                # The heading may wrap onto the next line ("... doubtful
                # of which.—In all cases ...").
                split = INLINE_TITLE_SPLIT_RE.search(joined[:300])
                if split and "(1)" not in joined[: split.start()]:
                    title = clean_body(joined[: split.start() + 1])
                    text = joined[split.end():]
                else:
                    # No reliable heading: leave it empty rather than
                    # presenting the first words of the body as a title.
                    title = ""
                    text = joined

        nearby_titles = [
            arrangement[n]
            for n in range(number - 5, number + 6)
            if n in arrangement
        ]
        text = remove_margin_notes(clean_body(text), nearby_titles)

        sections.append({
            "section": str(number),
            "title": re.sub(r"\s+([.,;:])", r"\1", clean_body(title)),
            "chapter": entry["chapter"],
            "part": entry["part"],
            "text": text,
        })

    return deduplicate_sections(sections)


def deduplicate_sections(sections: list[dict]) -> list[dict]:
    # Runs are strictly increasing, so duplicates should not occur; keep the
    # occurrence with the most text if they ever do.
    by_number: dict[str, dict] = {}

    for section in sections:
        number = section["section"]
        existing = by_number.get(number)
        if existing is None or len(section.get("text", "")) > len(existing.get("text", "")):
            by_number[number] = section

    return sorted(by_number.values(), key=lambda x: int(x["section"]))


def parse_act(act_code: str) -> Path:
    from act_sources import ACT_SOURCES

    if act_code not in ACT_SOURCES:
        raise ValueError(f"Unknown act: {act_code}")

    source = ACT_SOURCES[act_code]
    pdf_path = PDF_DIR / source["filename"]
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"{pdf_path} not found. Run: "
            f"python data-prep/download_official_acts.py {act_code}"
        )

    pages = extract_pages(pdf_path)
    raw_text = "\n\n".join(pages)

    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    (TEXT_DIR / f"{act_code.lower()}_2023.txt").write_text(
        raw_text, encoding="utf-8"
    )

    sections = parse_sections(pages)

    records = []
    for section in sections:
        records.append({
            "id": f"{act_code.lower()}-2023-section-{section['section']}",
            "act": act_code,
            "act_title": source["title"],
            "act_number": source["act_number"],
            "year": source["year"],
            "domain": source["domain"],
            "section": section["section"],
            "title": section["title"],
            "chapter": section["chapter"],
            "part": section["part"],
            "text": section["text"],
            "source_url": source["url"],
            "source_file": source["filename"],
        })

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / f"{act_code.lower()}_2023_sections.json"
    output.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"{act_code}: parsed {len(records)} sections")
    print(f"Output: {output}")
    return output


def main():
    from act_sources import ACT_SOURCES

    requested = [a.upper() for a in sys.argv[1:]] or list(ACT_SOURCES.keys())
    for act_code in requested:
        parse_act(act_code)


if __name__ == "__main__":
    main()
