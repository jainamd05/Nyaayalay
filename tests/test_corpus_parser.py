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
