from pathlib import Path

from data_prep_parse_shim import parse_sections


def test_section_parser_handles_numbered_sections():
    pages = [
        """
        CHAPTER I
        PRELIMINARY
        1. Short title, commencement and application.—This Act applies here.
        2. Definitions.—(1) In this Act, definitions are given.
        """
    ]

    records = parse_sections(pages)

    assert [record["section"] for record in records] == ["1", "2"]
    assert records[0]["title"] == "Short title, commencement and application."
    assert records[1]["title"] == "Definitions."


def test_section_parser_recovers_side_note_titles_from_arrangement():
    pages = [
        """
        ARRANGEMENT OF SECTIONS
        35. When police may arrest without
        warrant.
        36. Procedure of arrest and duties of officer making arrest.
        """,
        """
        CHAPTER V
        35. (1) Any police officer may without an order from a Magistrate and without a
        warrant, arrest any person who commits a cognizable offence in the presence
        of a police officer, or against whom a reasonable complaint has been made.
        36. Every police officer while making an arrest shall bear an accurate,
        visible and clear identification of his name which will facilitate easy identification.
        """,
    ]

    records = {record["section"]: record for record in parse_sections(pages)}

    assert records["35"]["title"] == "When police may arrest without warrant."
    assert records["35"]["text"].startswith("(1) Any police officer may without an order")
    assert records["36"]["title"] == "Procedure of arrest and duties of officer making arrest."
    assert records["36"]["text"].startswith("Every police officer while making an arrest")
