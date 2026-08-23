from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Iterable

from pypdf import PdfReader

from act_sources import ACT_SOURCES

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "raw" / "source_pdfs"
TEXT_DIR = ROOT / "data" / "raw" / "source_text"
PROCESSED_DIR = ROOT / "data" / "processed"

SECTION_RE = re.compile(r"^\s*(\d{1,3})\.\s*(.+?)\s*$")
CHAPTER_RE = re.compile(r"^\s*CHAPTER\s+([IVXLCDM]+)\s*$", re.I)
PART_RE = re.compile(r"^\s*PART\s+([IVXLCDM]+)\s*$", re.I)

def normalize_line(line: str) -> str:
    line = line.replace("\u00ad", "")
    line = line.replace("\u2010", "-")
    line = line.replace("\u2011", "-")
    line = line.replace("\u2013", "–")
    line = line.replace("\u2014", "—")
    line = re.sub(r"[ \t]+", " ", line)
    return line.strip()

def extract_pages(pdf_path: Path) -> list[str]:
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
    match = SECTION_RE.match(heading_line)
    if not match:
        raise ValueError(f"Not a section heading: {heading_line}")

    number = match.group(1)
    rest = match.group(2).strip()

    # Statutes commonly use a full stop followed by an em/en dash to
    # separate the section title from its operative text.
    dash_match = re.search(r"\.\s*[—–-]\s*", rest)
    if dash_match:
        title = rest[:dash_match.start() + 1].strip()
        body = rest[dash_match.end():].strip()
    else:
        # Some headings put the operative text on the next line.
        title = rest
        body = ""

    return f"Section {number}", title, body

def parse_sections(pages: Iterable[str]) -> list[dict]:
    lines: list[str] = []
    for page in pages:
        lines.extend(page.splitlines())

    sections: list[dict] = []
    current: dict | None = None
    current_chapter = None
    current_part = None

    for raw_line in lines:
        line = normalize_line(raw_line)
        if not line:
            continue

        part_match = PART_RE.match(line)
        if part_match:
            current_part = f"Part {part_match.group(1)}"
            continue

        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            current_chapter = f"Chapter {chapter_match.group(1)}"
            continue

        if is_section_heading(line):
            label, title, first_body = split_title_and_body(line)
            number = int(re.search(r"\d+", label).group())
            if current is not None:
                current["text"] = clean_body(current["text"])
                sections.append(current)

            current = {
                "section": str(number),
                "title": title,
                "chapter": current_chapter,
                "part": current_part,
                "text": first_body,
            }
            continue

        if current is not None:
            current["text"] += " " + line

    if current is not None:
        current["text"] = clean_body(current["text"])
        sections.append(current)

    return deduplicate_sections(sections)

def clean_body(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    # Remove common extracted page-number artifacts where possible.
    text = re.sub(r"\s+\d{1,3}\s*$", "", text)
    return text.strip()

def deduplicate_sections(sections: list[dict]) -> list[dict]:
    # A section number can appear more than once because the PDF contains
    # an Arrangement of Sections/index before the actual legal provisions.
    # Keep the occurrence with the most substantive extracted text.

    by_number: dict[str, dict] = {}

    for section in sections:
        number = section["section"]

        if number not in by_number:
            by_number[number] = section
        else:
            existing = by_number[number]

            # Prefer the version containing more actual legal text.
            if len(section.get("text", "")) > len(existing.get("text", "")):
                by_number[number] = section

    return sorted(by_number.values(), key=lambda x: int(x["section"]))

def parse_act(act_code: str) -> Path:
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
        __import__("json").dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"{act_code}: parsed {len(records)} sections")
    print(f"Output: {output}")
    return output

def main():
    requested = sys.argv[1:] or list(ACT_SOURCES.keys())
    for act_code in requested:
        parse_act(act_code)

if __name__ == "__main__":
    main()
