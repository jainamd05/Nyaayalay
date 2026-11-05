"""Parse the official BNS / BNSS / BSA PDFs into section records.

The three Acts are not typeset the same way:

* Inline headings (BNS): the heading sits on the section's first line and
  is separated from the body by a full stop and a dash, sometimes wrapping
  onto a second line::

      49. Punishment of abetment if act abetted is committed in consequence and where no express
      provision is made for its punishment.—Whoever abets any offence ...

* Marginal notes (BNSS, BSA, Gazette of India layout): the heading is
  printed as a short note in the page margin, level with the section's
  first line, and the body starts directly after the number::

      57. A police officer making an arrest without      Person arrested
      warrant shall, without unnecessary delay ...       not to be detained
                                                         more than twenty-
                                                         four hours.

  pypdf's plain extraction emits all of a page's marginal notes in one block
  after the page body. That block used to end up in the middle of whichever
  section was running at the time, and the first body line was taken as the
  title.

To handle both layouts, the PDF is read with positions. Lines that start in
a margin column are marginal notes; each note is matched to the section
whose first line is level with it on the same page. Sections without a
marginal note fall back to an inline heading.

Other rules:

* Parsing starts after the enacting formula ("BE it enacted by
  Parliament ..."), which skips the Gazette masthead and the Arrangement of
  Sections.
* Sections must be numbered in order, so footnotes such as
  "1. 1st day of July, 2024, ..." and numbered paragraphs of the Statement
  of Objects and Reasons are not taken for sections.
* Parsing stops at the Schedules, the Statement of Objects and Reasons or
  the signature block.
* Page headers, page numbers, chapter titles, citations in the margin
  ("21 of 2000.") and footnotes set in a smaller type are left out of the
  section text.
"""

from __future__ import annotations

import json
import math
import re
import statistics
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "raw" / "source_pdfs"
TEXT_DIR = ROOT / "data" / "raw" / "source_text"
PROCESSED_DIR = ROOT / "data" / "processed"

SECTION_RE = re.compile(r"^\s*(\d{1,3})\.\s*(.+?)\s*$")
CHAPTER_RE = re.compile(r"^\s*CHAPTER\s+([IVXLCDM]+)\s*$", re.IGNORECASE)
PART_RE = re.compile(r"^\s*PART\s+([IVXLCDM]+)\s*$", re.IGNORECASE)

# "BE it enacted by Parliament in the Seventy-fourth Year ..." (pypdf
# sometimes splits the drop-cap: "B E it enacted").
ENACTING_RE = re.compile(r"B\s*E\s+it\s+enacted\s+by\s+Parliament", re.IGNORECASE)

# Material after the last section that is not part of any section. The
# headings are matched case-sensitively so that body text such as
# "Schedule to the Constitution" does not end the Act.
END_RE = re.compile(
    r"^\s*(?:"
    r"STATEMENT\s+OF\s+OBJECTS\s+AND\s+REASONS"
    r"|(?:THE\s+)?(?:FIRST\s+|SECOND\s+|THIRD\s+)?SCHEDULE\b"
    r"|.*\b[Ss]ecretary\s+to\s+the\s+Govt\.?\s+of\s+India\b"
    r"|.*\bLegislative\s+Counsel\s+to\s+the\s+Govt\.?\s+of\s+India\b"
    r"|UPLOADED\s+BY\s+THE\s+MANAGER"
    r"|Digitally\s+signed\s+by"
    r")"
)

# Gazette running heads and similar page furniture.
PAGE_FURNITURE_RE = re.compile(
    r"GAZETTE\s+OF\s+INDIA"
    r"|^\s*_{5,}\s*$"
    r"|^\s*[—–\-\s]+$"
    r"|^\s*\d{1,4}\s*$"
    r"|^\s*(?:Sec\.\s*\d+\]|\[Part\s+II\b)"
    r"|xxxGID[A-Z]xxx",
    re.IGNORECASE,
)

# Marginal citations of other Acts, e.g. "21 of 2000." or "45 of 1860.".
CITATION_RE = re.compile(r"^\s*(?:\d{1,3}\s+of\s+\d{4}\.?\s*)+$", re.IGNORECASE)

# Inline heading terminators: "Definitions.—", "Definitions.– In",
# "... of another person—Whoever".
INLINE_TITLE_RE = re.compile(
    r"\.\s*[—–]+-?\s*"
    r"|(?<=[A-Za-z)])\s*[—–]+\s*(?=[A-Z])"
)

MAX_INLINE_TITLE_CHARS = 300
MAX_TITLE_CONTINUATION_LINES = 3
MAX_MARGIN_LINE_CHARS = 70
MAX_SECTION_NUMBER_JUMP = 3


@dataclass
class TextLine:
    """One extracted line. Positions are absent for plain-text input."""

    text: str
    x: float | None = None
    y: float | None = None
    size: float | None = None


@dataclass
class _Section:
    number: int
    chapter: str | None
    part: str | None
    page: int
    y: float | None
    heading_rest: str
    lines: list[str] = field(default_factory=list)
    note: str | None = None


def normalize_line(line: str) -> str:
    line = line.replace("­", "")
    line = line.replace("‐", "-")
    line = line.replace("‑", "-")
    line = line.replace("–", "–")
    line = line.replace("—", "—")
    line = re.sub(r"[ \t]+", " ", line)
    return line.strip()


# --------------------------------------------------------------------------
# PDF extraction
# --------------------------------------------------------------------------

def _matrix_multiply(m: Sequence[float], n: Sequence[float]) -> list[float]:
    return [
        m[0] * n[0] + m[1] * n[2],
        m[0] * n[1] + m[1] * n[3],
        m[2] * n[0] + m[3] * n[2],
        m[2] * n[1] + m[3] * n[3],
        m[4] * n[0] + m[5] * n[2] + n[4],
        m[4] * n[1] + m[5] * n[3] + n[5],
    ]


def _extract_page_lines(page) -> list[TextLine]:
    """Return a page's lines, in pypdf's order, with where each one starts."""
    lines: list[TextLine] = []
    parts: list[str] = []
    state: dict = {"pos": None, "sizes": {}}

    def flush() -> None:
        text = normalize_line("".join(parts))
        if text:
            x, y = state["pos"] if state["pos"] else (None, None)
            sizes = state["sizes"]
            size = max(sizes, key=sizes.get) if sizes else None
            lines.append(TextLine(text=text, x=x, y=y, size=size))
        parts.clear()
        state["pos"] = None
        state["sizes"] = {}

    def visitor(text, cm, tm, font_dict, font_size):
        if not text:
            return
        matrix = _matrix_multiply(tm, cm)
        x, y = matrix[4], matrix[5]
        scale = math.hypot(matrix[2], matrix[3]) or 1.0
        size = round(float(font_size or 0) * scale, 1)

        for index, piece in enumerate(text.split("\n")):
            if index > 0:
                flush()
            if piece.strip():
                if state["pos"] is None:
                    state["pos"] = (x, y)
                if size:
                    state["sizes"][size] = (
                        state["sizes"].get(size, 0) + len(piece.strip())
                    )
                parts.append(piece)
            elif piece:
                parts.append(piece)

    page.extract_text(visitor_text=visitor)
    flush()
    return lines


def extract_layout_pages(pdf) -> tuple[list[list[TextLine]], list[float]]:
    """Extract positioned lines for every page.

    ``pdf`` is a path or an open ``PdfReader``. Returns the lines of each
    page and each page's width.
    """
    reader = pdf if isinstance(pdf, PdfReader) else PdfReader(str(pdf))
    pages: list[list[TextLine]] = []
    widths: list[float] = []
    for page in reader.pages:
        pages.append(_extract_page_lines(page))
        widths.append(float(page.mediabox.width))
    return pages, widths


def extract_pages(pdf_path: Path) -> list[str]:
    """Plain text of each page (kept for the raw text dump)."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        lines = [normalize_line(line) for line in text.splitlines()]
        pages.append("\n".join(line for line in lines if line))
    return pages


# --------------------------------------------------------------------------
# Page layout analysis
# --------------------------------------------------------------------------

def _page_orientation(lines: Sequence[TextLine]) -> int:
    """+1 if y grows upwards (normal PDF space), -1 if it is flipped."""
    ys = [line.y for line in lines if line.y is not None]
    if len(ys) < 2:
        return 1
    downs = sum(1 for a, b in pairwise(ys) if b < a)
    ups = sum(1 for a, b in pairwise(ys) if b > a)
    return 1 if downs >= ups else -1


def _line_height(lines: Sequence[TextLine]) -> float:
    ys = [line.y for line in lines if line.y is not None]
    gaps = [abs(a - b) for a, b in pairwise(ys) if 2 < abs(a - b) < 40]
    return statistics.median(gaps) if gaps else 12.0


def split_margin_lines(
    lines: Sequence[TextLine], page_width: float | None
) -> tuple[list[TextLine], list[TextLine]]:
    """Separate body lines from lines printed in the left or right margin."""
    positioned = [line for line in lines if line.x is not None]
    long_xs = sorted(line.x for line in positioned if len(line.text) >= 40)
    if not page_width or len(long_xs) < 3:
        return list(lines), []

    body_left = long_xs[len(long_xs) // 10]
    right_threshold = body_left + 0.62 * (page_width - body_left)

    body: list[TextLine] = []
    margin: list[TextLine] = []
    for line in lines:
        in_margin = (
            line.x is not None
            and len(line.text) <= MAX_MARGIN_LINE_CHARS
            and (line.x < body_left - 15 or line.x > right_threshold)
        )
        (margin if in_margin else body).append(line)
    return body, margin


def group_margin_notes(
    margin_lines: Sequence[TextLine], orientation: int = 1
) -> list[TextLine]:
    """Join margin lines into notes; each note ends with a full stop."""
    lines = [
        line for line in margin_lines
        if not CITATION_RE.match(line.text)
        and not PAGE_FURNITURE_RE.search(line.text)
    ]
    if all(line.y is not None for line in lines):
        lines.sort(key=lambda line: -orientation * line.y)

    height = _line_height(lines) if lines else 12.0
    notes: list[TextLine] = []
    current: list[TextLine] = []

    def close() -> None:
        if current:
            text = _join_lines(line.text for line in current)
            notes.append(TextLine(text=text, x=current[0].x, y=current[0].y))
            current.clear()

    for line in lines:
        if current:
            previous = current[-1]
            gap = (
                abs(previous.y - line.y)
                if previous.y is not None and line.y is not None
                else 0.0
            )
            if previous.text.rstrip().endswith(".") or gap > 2.2 * height:
                close()
        current.append(line)
    close()
    return notes


FOOTNOTE_START_RE = re.compile(r"^\s*(?:\d{1,2}\.?|\*+|†)\s*\S")


def _drop_small_trailing_lines(lines: list[TextLine]) -> list[TextLine]:
    """Drop footnotes at the foot of a page.

    A footnote block is a run of lines in clearly smaller type at the end of
    the page body whose first line starts with a footnote marker ("1.",
    "*"). Illustrations, which are also set smaller but carry no marker,
    are kept.
    """
    sizes = [line.size for line in lines if line.size]
    if len(sizes) < 5:
        return lines
    body_size = statistics.median(sizes)
    cut = len(lines)
    while cut > 0 and lines[cut - 1].size and lines[cut - 1].size < 0.8 * body_size:
        cut -= 1
    if cut < len(lines) and FOOTNOTE_START_RE.match(lines[cut].text):
        return lines[:cut]
    return lines


# --------------------------------------------------------------------------
# Section assembly
# --------------------------------------------------------------------------

def _join_lines(lines: Iterable[str]) -> str:
    text = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not text:
            text = line
        elif text.endswith("-") and text[-2:-1].isalpha():
            # A compound broken at its hyphen: "sub-" + "section".
            text += line
        else:
            text += " " + line
    return text


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    # pypdf inserts stray spaces before punctuation and hyphens:
    # "currency -notes", "sub -section", "of which .—".
    text = re.sub(r"(\w) -(?=\w)", r"\1-", text)
    text = re.sub(r"\s+([.,;:])(?=[\s—–]|$)", r"\1", text)
    return text.strip()


def clean_body(text: str) -> str:
    text = clean_text(text)
    # Remove a trailing page number left over from extraction.
    text = re.sub(r"\s+\d{1,3}\s*$", "", text)
    return text.strip()


def split_title_and_body(heading_line: str) -> tuple[str, str, str]:
    """Split a one-line inline heading such as "2. Definitions.—In ..."."""
    match = SECTION_RE.match(heading_line)
    if not match:
        raise ValueError(f"Not a section heading: {heading_line}")

    number = match.group(1)
    title, body = _split_inline_title(match.group(2).strip())
    if title is None:
        return f"Section {number}", match.group(2).strip(), ""
    return f"Section {number}", title, body


def _split_inline_title(text: str) -> tuple[str | None, str]:
    """Find "Heading.—Body" at the start of ``text``.

    Returns ``(None, text)`` when there is no inline heading.
    """
    for match in INLINE_TITLE_RE.finditer(text):
        if match.start() > MAX_INLINE_TITLE_CHARS:
            break
        title = text[:match.start()].rstrip()
        if text[match.start():match.end()].lstrip().startswith("."):
            title += "."
        title = title.strip()
        # Numbered sub-sections are body text, not a heading.
        if not title or title.startswith("(") or title.endswith(","):
            return None, text
        return clean_text(title), text[match.end():].strip()
    return None, text


def _is_chapter_title(line: str) -> bool:
    letters = [char for char in line if char.isalpha()]
    return len(letters) >= 4 and all(char.isupper() for char in letters)


def _skip_body_line(line: str) -> bool:
    return bool(
        PAGE_FURNITURE_RE.search(line)
        or CITATION_RE.match(line)
        or _is_chapter_title(line)
    )


def _assign_notes(
    sections: list[_Section],
    notes_by_page: dict[int, list[TextLine]],
    line_heights: dict[int, float],
) -> None:
    """Give each section the marginal note level with its first line."""
    by_page: dict[int, list[_Section]] = {}
    for section in sections:
        if section.y is not None:
            by_page.setdefault(section.page, []).append(section)

    for page, page_sections in by_page.items():
        notes = [note for note in notes_by_page.get(page, []) if note.y is not None]
        if not notes:
            continue
        height = line_heights.get(page, 12.0)
        used: set[int] = set()
        for tolerance in (2.5 * height, 8.0 * height):
            pairs = sorted(
                (abs(note.y - section.y), n_index, s_index)
                for n_index, note in enumerate(notes)
                for s_index, section in enumerate(page_sections)
                if section.note is None and n_index not in used
            )
            for distance, n_index, s_index in pairs:
                section = page_sections[s_index]
                if distance > tolerance or n_index in used or section.note:
                    continue
                section.note = notes[n_index].text
                used.add(n_index)


def _finish(section: _Section) -> dict:
    first = section.heading_rest
    if section.note:
        title = clean_text(section.note)
        body = _join_lines([first, *section.lines])
    else:
        title = None
        body = _join_lines([first, *section.lines])
        # The heading may wrap onto the next line(s): try the first line,
        # then the first two, and so on.
        for extra in range(MAX_TITLE_CONTINUATION_LINES + 1):
            candidate = _join_lines([first, *section.lines[:extra]])
            found, rest = _split_inline_title(candidate)
            if found is not None:
                title = found
                body = _join_lines([rest, *section.lines[extra:]])
                break
        if title is None:
            title = ""

    return {
        "section": str(section.number),
        "title": title,
        "chapter": section.chapter,
        "part": section.part,
        "text": clean_body(body),
    }


def parse_layout(
    pages: Sequence[Sequence[TextLine]],
    page_widths: Sequence[float | None] | None = None,
) -> list[dict]:
    """Build section records from positioned (or plain) page lines."""
    widths = list(page_widths or [None] * len(pages))

    body_pages: list[list[TextLine]] = []
    notes_by_page: dict[int, list[TextLine]] = {}
    line_heights: dict[int, float] = {}
    orientations: list[int] = []
    for index, lines in enumerate(pages):
        body, margin = split_margin_lines(lines, widths[index])
        orientation = _page_orientation(body)
        orientations.append(orientation)
        line_heights[index] = _line_height(body)
        body_pages.append(_drop_small_trailing_lines(body))
        if margin:
            notes_by_page[index] = group_margin_notes(margin, orientation)

    # Start after the enacting formula. Anything on that page printed above
    # it (the Gazette masthead, emitted late by pypdf) is dropped as well.
    start_page, start_line = 0, 0
    found_enacting_formula = False
    for page_index, lines in enumerate(body_pages):
        for line_index, line in enumerate(lines):
            if ENACTING_RE.search(line.text):
                start_page, start_line = page_index, line_index + 1
                break
        else:
            continue
        found_enacting_formula = True
        marker = lines[line_index]
        if marker.y is not None:
            sign = orientations[page_index]
            kept = [
                line for line in lines[start_line:]
                if line.y is None or sign * line.y <= sign * marker.y + 1
            ]
            body_pages[page_index] = (
                body_pages[page_index][:start_line] + kept
            )
        break

    sections: list[_Section] = []
    current: _Section | None = None
    chapter: str | None = None
    part: str | None = None
    expected = 1

    finished = False
    for page_index in range(start_page, len(body_pages)):
        if finished:
            break
        lines = body_pages[page_index]
        first = start_line if page_index == start_page else 0
        for line in lines[first:]:
            text = normalize_line(line.text)
            if not text:
                continue

            if sections and END_RE.match(text):
                finished = True
                break

            part_match = PART_RE.match(text)
            if part_match:
                part = f"Part {part_match.group(1)}"
                continue

            chapter_match = CHAPTER_RE.match(text)
            if chapter_match:
                chapter = f"Chapter {chapter_match.group(1)}"
                continue

            if _skip_body_line(text):
                continue

            heading = SECTION_RE.match(text)
            if heading:
                number = int(heading.group(1))
                in_sequence = expected <= number <= expected + MAX_SECTION_NUMBER_JUMP
                # Without an enacting formula the Arrangement of Sections is
                # parsed first; start over when the real section 1 appears.
                restart = (
                    number == 1
                    and not found_enacting_formula
                    and sections
                    and statistics.mean(
                        len(" ".join(s.lines)) for s in sections
                    ) < 120
                )
                if in_sequence or restart:
                    if restart:
                        sections.clear()
                    current = _Section(
                        number=number,
                        chapter=chapter,
                        part=part,
                        page=page_index,
                        y=line.y,
                        heading_rest=heading.group(2).strip(),
                    )
                    sections.append(current)
                    expected = number + 1
                    continue

            if current is not None:
                current.lines.append(text)

    _assign_notes(sections, notes_by_page, line_heights)
    return [_finish(section) for section in sections]


def parse_sections(pages: Iterable[str]) -> list[dict]:
    """Parse plain-text pages (no layout information)."""
    plain_pages = [
        [TextLine(text=line) for line in page.splitlines() if line.strip()]
        for page in pages
    ]
    return parse_layout(plain_pages)


def parse_pdf(pdf) -> list[dict]:
    pages, widths = extract_layout_pages(pdf)
    return parse_layout(pages, widths)


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

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

    raw_text = "\n\n".join(extract_pages(pdf_path))
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    (TEXT_DIR / f"{act_code.lower()}_2023.txt").write_text(
        raw_text, encoding="utf-8"
    )

    sections = parse_pdf(pdf_path)

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
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    untitled = [r["section"] for r in records if not r["title"]]
    unusual = [
        r["section"] for r in records
        if r["title"] and not r["title"].endswith((".", "—"))
    ]
    print(f"{act_code}: parsed {len(records)} sections")
    if untitled:
        print(f"  {len(untitled)} without a title: {untitled[:20]}")
    if unusual:
        print(f"  {len(unusual)} titles not ending in '.' or '—': {unusual[:20]}")
    print(f"Output: {output}")
    return output


def main():
    from act_sources import ACT_SOURCES

    requested = sys.argv[1:] or list(ACT_SOURCES.keys())
    for act_code in requested:
        parse_act(act_code)


if __name__ == "__main__":
    main()
