from data_prep_parse_shim import module

parse_sections = module.parse_sections
strip_title_prefix = module.strip_title_prefix

N_SECTIONS = 12
TITLES = {n: f"Heading number {n} about matter {n}." for n in range(1, N_SECTIONS + 1)}
TITLES[3] = "Evidence may be given of facts in issue and relevant facts."
TITLES[4] = "Relevancy of facts forming part of same transaction."
TITLES[5] = "Facts which are occasion, cause or effect of facts in issue or relevant facts."
TITLES[6] = "Motive, preparation and previous or subsequent conduct."
TITLES[10] = (
    "Punishment of person guilty of one of several offences, judgment stating "
    "that it is doubtful of which."
)


def _arrangement() -> str:
    lines = ["ARRANGEMENT OF SECTIONS", "CHAPTER I", "PRELIMINARY", "SECTIONS"]
    for n, title in TITLES.items():
        if n == 10:
            # Long arrangement entries wrap onto a second line.
            lines += [f"{n}. Punishment of person guilty of one of several offences, judgment",
                      "stating that it is doubtful of which."]
        else:
            lines.append(f"{n}. {title}")
        if n == 7:
            lines += ["CHAPTER II", "OF RELEVANCY OF FACTS"]
    return "\n".join(lines)


def _by_number(records):
    return {int(r["section"]): r for r in records}


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
    assert records[0]["text"] == "This Act applies here."


def test_inline_headings_use_arrangement_titles():
    """BNS layout: inline "N. Title.—Body", wrapped headings, footnote, SOR."""
    body = ["CHAPTER I", "PRELIMINARY"]
    for n, title in TITLES.items():
        if n == 10:
            body += [
                "10. Punishment of person guilty of one of several offences, judgment stating that it is doubtful",
                "of which .—In all cases in which judgment is given that a person is guilty.",
            ]
        else:
            body.append(f"{n}. {title[:-1]}.—Operative text of section {n}.")
        if n == 1:
            # India Code footnote on the first page of the body.
            body.append("1. 1st day of July, 2024, vide notification No. S.O. 850(E).")
        if n == 7:
            body += ["CHAPTER II", "OF RELEVANCY OF FACTS"]
    sor = "\n".join(
        ["STATEMENT OF OBJECTS AND REASONS"]
        + [f"{n}. Paragraph {n} of the statement with much longer explanatory prose " * 3
           for n in range(1, 6)]
    )

    records = _by_number(parse_sections([_arrangement(), "\n".join(body), sor]))

    assert sorted(records) == list(range(1, N_SECTIONS + 1))
    assert records[10]["title"] == TITLES[10]
    assert records[10]["text"] == "In all cases in which judgment is given that a person is guilty."
    assert records[2]["title"] == TITLES[2]
    assert records[2]["text"] == "Operative text of section 2."
    # Statement of Objects paragraphs must not replace real sections.
    assert "Paragraph" not in records[4]["text"]
    assert records[4]["title"] == TITLES[4]
    # The chapter name is not glued onto the previous section.
    assert "OF RELEVANCY OF FACTS" not in records[7]["text"]
    assert records[8]["chapter"] == "Chapter II"


def test_margin_note_headings_use_arrangement_titles():
    """BNSS/BSA layout: no inline heading, margin notes mixed into later text."""
    body = ["CHAPTER I", "PRELIMINARY"]
    for n in TITLES:
        if n == 3:
            body += [
                "3. Evidence may be given in any suit or proceeding of the existence or non-existence",
                "of every fact in issue and of no others.",
                "Evidence may be given of facts in issue and relevant facts.",
                "21 of 2000.",
                "Sec. 1] THE GAZETTE OF INDIA EXTRAORDINARY 3",
                "_" * 40,
            ]
        elif n == 6:
            body += [
                "6. (1) Any fact is relevant which shows or constitutes a motive or preparation for any",
                "fact in issue or relevant fact.",
                # Margin notes of sections 4-6 batched at the page end.
                "Relevancy of facts forming part of same",
                "transaction.",
                "Facts which are occasion, cause or effect of facts in issue or relevant facts.",
                "Motive, preparation and previous or subsequent conduct.",
                "5 of 1908.",
                "4 THE GAZETTE OF INDIA EXTRAORDINARY [Part II—",
                "(2) The conduct of any party is relevant.",
            ]
        else:
            body.append(f"{n}. Body text of section {n} under the Information Technology Act, 2000 (21 of 2000).")
        if n == 7:
            body += ["CHAPTER II", "OF RELEVANCY OF FACTS"]

    records = _by_number(parse_sections([_arrangement(), "\n".join(body)]))

    assert sorted(records) == list(range(1, N_SECTIONS + 1))
    for n, title in TITLES.items():
        assert records[n]["title"] == title

    assert records[3]["text"] == (
        "Evidence may be given in any suit or proceeding of the existence or "
        "non-existence of every fact in issue and of no others."
    )
    assert records[6]["text"] == (
        "(1) Any fact is relevant which shows or constitutes a motive or preparation "
        "for any fact in issue or relevant fact. (2) The conduct of any party is relevant."
    )
    # Citations inside parentheses are real text and are kept.
    assert records[2]["text"].endswith("(21 of 2000).")


def test_strip_title_prefix():
    assert strip_title_prefix("Theft.—Whoever takes", "Theft.") == "Whoever takes"
    assert strip_title_prefix("Long title wrapped\nhere .—Body", "Long title wrapped here.") == "Body"
    assert strip_title_prefix("Theft is defined", "Theft.") is None
    assert strip_title_prefix("Robbery.—x", "Theft.") is None
