from io import BytesIO

from data_prep_parse_shim import module, parse_sections
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)

TextLine = module.TextLine
parse_layout = module.parse_layout
parse_pdf = module.parse_pdf

PAGE_WIDTH = 595.0
PAGE_HEIGHT = 842.0
BODY_X = 60.0
MARGIN_X = 470.0


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
    assert records[0]["chapter"] == "Chapter I"
    # The chapter title is not section text.
    assert "PRELIMINARY" not in records[0]["text"]


def test_inline_heading_wrapping_onto_second_line():
    pages = [
        """
        BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as follows:—
        49. Punishment of abetment if act abetted is committed in consequence and where no express
        provision is made for its punishment .—Whoever abets any offence shall, if the act
        abetted is committed in consequence of the abetment, be punished.
        50. Punishment of abetment if person abetted does act with different intention from that of
        abettor.—Whoever abets the commission of an offence shall be punished.
        """
    ]
    pages[0] = pages[0].replace("49.", "1.").replace("50.", "2.")

    records = parse_sections(pages)

    assert [r["title"] for r in records] == [
        (
            "Punishment of abetment if act abetted is committed in consequence "
            "and where no express provision is made for its punishment."
        ),
        (
            "Punishment of abetment if person abetted does act with different "
            "intention from that of abettor."
        ),
    ]
    assert records[0]["text"].startswith("Whoever abets any offence shall")
    assert records[1]["text"] == (
        "Whoever abets the commission of an offence shall be punished."
    )


def test_inline_heading_without_full_stop_before_dash():
    records = parse_sections([
        (
            "1. False information, with intent to cause public servant to use his lawful power to injury of\n"
            "another person—Whoever gives to any public servant any information.\n"
        ),
    ])

    assert records[0]["title"] == (
        "False information, with intent to cause public servant to use his "
        "lawful power to injury of another person"
    )
    assert records[0]["text"] == (
        "Whoever gives to any public servant any information."
    )


def test_masthead_arrangement_footnotes_and_statement_are_skipped():
    pages = [
        """
        THE BHARATIYA NYAYA SANHITA, 2023
        ARRANGEMENT OF SECTIONS
        1. Short title, commencement and application.
        2. Definitions.
        3. General explanations.
        """,
        """
        BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as follows:—
        CHAPTER I
        PRELIMINARY
        1. Short title, commencement and application.—(1) This Act may be called the
        Bharatiya Nyaya Sanhita, 2023.
        2. Definitions.—In this Sanhita, unless the context otherwise requires,—
        (1) "act" denotes as well a series of acts as a single act;
        1. 1st day of July, 2024, vide notification No. S.O. 850(E).
        (5) "Court" means a Judge;
        17
        3. General explanations.—Throughout this Sanhita every definition shall be understood.
        STATEMENT OF OBJECTS AND REASONS
        4. Now, it is proposed to enact a new law.
        """,
    ]

    records = parse_sections(pages)

    assert [r["section"] for r in records] == ["1", "2", "3"]
    assert records[0]["text"] == (
        "(1) This Act may be called the Bharatiya Nyaya Sanhita, 2023."
    )
    # The footnote did not start a new "section 1"; section 2 keeps the rest
    # of its definitions.
    assert '(5) "Court" means a Judge;' in records[1]["text"]
    assert "17" not in records[1]["text"].split()
    assert "Now, it is proposed" not in records[2]["text"]
    assert "STATEMENT" not in records[2]["text"]


def test_arrangement_of_sections_without_enacting_formula():
    pages = [
        "1. Short title.\n2. Definitions.\n",
        (
            "1. Short title.—This Act may be called the Test Act.\n"
            "2. Definitions.—In this Act, words have meanings.\n"
        ),
    ]

    records = parse_sections(pages)

    assert [r["text"] for r in records] == [
        "This Act may be called the Test Act.",
        "In this Act, words have meanings.",
    ]


def _line(text, y, x=BODY_X, size=10.0):
    return TextLine(text=text, x=x, y=y, size=size)


def test_marginal_notes_become_titles():
    # The order pypdf produces for a BSA page: body lines, then the
    # page's marginal notes, then marginal citations.
    page = [
        _line("4. Facts which, though not in issue, are so connected with a fact in issue or a", 700),
        _line("relevant fact as to form part of the same transaction, are relevant.", 688),
        _line("5. Facts which are the occasion, cause or effect, immediate or otherwise, of relevant", 660),
        _line("facts, or facts in issue, are relevant.", 648),
        _line("6. (1) Any fact is relevant which shows or constitutes a motive or preparation for any", 620),
        _line("fact in issue or relevant fact.", 608),
        _line("Relevancy of facts", 700, x=MARGIN_X, size=8),
        _line("forming part of same", 691, x=MARGIN_X, size=8),
        _line("transaction.", 682, x=MARGIN_X, size=8),
        _line("Facts which are", 660, x=MARGIN_X, size=8),
        _line("occasion, cause or effect", 651, x=MARGIN_X, size=8),
        _line("of facts in issue or", 642, x=MARGIN_X, size=8),
        _line("relevant facts.", 633, x=MARGIN_X, size=8),
        _line("Motive, preparation and", 620, x=MARGIN_X, size=8),
        _line("previous or subsequent", 611, x=MARGIN_X, size=8),
        _line("conduct.", 602, x=MARGIN_X, size=8),
        _line("5 of 1908.", 590, x=MARGIN_X, size=8),
    ]
    next_page = [
        _line("4 THE GAZETTE OF INDIA EXTRAORDINARY [Part II—", 800),
        _line("(2) The conduct of any party, or of any agent to any party, to any suit or proceeding,", 760),
        _line("is relevant, if such conduct influences or is influenced by any fact in issue.", 748),
        _line("7. Facts necessary to explain or introduce a fact in issue or relevant fact, are relevant", 720),
        _line("in so far as they are necessary for that purpose.", 708),
        _line("Facts necessary to", 720, x=MARGIN_X, size=8),
        _line("explain or introduce", 711, x=MARGIN_X, size=8),
        _line("relevant facts.", 702, x=MARGIN_X, size=8),
    ]
    renumber = {"4.": "1.", "5.": "2.", "6.": "3.", "7.": "4."}
    for line in page + next_page:
        head = line.text.split(" ", 1)[0]
        if head in renumber:
            line.text = renumber[head] + line.text[len(head):]

    records = parse_layout([page, next_page], [PAGE_WIDTH, PAGE_WIDTH])

    assert [r["title"] for r in records] == [
        "Relevancy of facts forming part of same transaction.",
        "Facts which are occasion, cause or effect of facts in issue or relevant facts.",
        "Motive, preparation and previous or subsequent conduct.",
        "Facts necessary to explain or introduce relevant facts.",
    ]
    assert records[0]["text"] == (
        "Facts which, though not in issue, are so connected with a fact in "
        "issue or a relevant fact as to form part of the same transaction, "
        "are relevant."
    )
    # The section keeps its opening words and its continuation on the
    # next page, without notes, citations or running heads.
    assert records[2]["text"] == (
        "(1) Any fact is relevant which shows or constitutes a motive or "
        "preparation for any fact in issue or relevant fact. (2) The conduct "
        "of any party, or of any agent to any party, to any suit or "
        "proceeding, is relevant, if such conduct influences or is "
        "influenced by any fact in issue."
    )
    for record in records:
        assert "1908" not in record["text"]
        assert "GAZETTE" not in record["text"]


def test_marginal_notes_in_left_margin():
    page = [
        _line("1. A police officer making an arrest without warrant shall, without unnecessary", 700, x=150),
        _line("delay, take or send the person arrested before a Magistrate having jurisdiction.", 688, x=150),
        _line("2. No police officer shall detain in custody a person arrested without warrant for a", 660, x=150),
        _line("longer period than under all the circumstances of the case is reasonable.", 648, x=150),
        _line("Person arrested to be", 700, x=40, size=8),
        _line("taken before Magistrate.", 691, x=40, size=8),
        _line("Person arrested not to", 660, x=40, size=8),
        _line("be detained more than", 651, x=40, size=8),
        _line("twenty-four hours.", 642, x=40, size=8),
    ]

    records = parse_layout([page], [PAGE_WIDTH])

    assert [r["title"] for r in records] == [
        "Person arrested to be taken before Magistrate.",
        "Person arrested not to be detained more than twenty-four hours.",
    ]
    assert records[0]["text"].startswith(
        "A police officer making an arrest without warrant shall, without "
        "unnecessary delay"
    )


def test_masthead_printed_above_enacting_formula_is_dropped():
    # pypdf emits the Gazette masthead after the body text of page 1.
    page = [
        _line("An Act to consolidate and to provide for general rules and principles of evidence.", 600),
        _line("BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as follows:—", 580),
        _line("1. (1) This Act may be called the Bharatiya Sakshya Adhiniyam, 2023.", 540),
        _line("(2) It applies to all judicial proceedings in or before any Court.", 528),
        _line("Short title, application", 540, x=MARGIN_X, size=8),
        _line("and commencement.", 531, x=MARGIN_X, size=8),
        _line("EXTRAORDINARY", 800),
        _line("No. 55] NEW DELHI, MONDAY, DECEMBER 25, 2023/PAUSHA 4, 1945 (SAKA)", 780),
        _line("Separate paging is given to this Part in order that it may be filed as a separate compilation.", 760),
    ]

    records = parse_layout([page], [PAGE_WIDTH])

    assert len(records) == 1
    assert records[0]["title"] == "Short title, application and commencement."
    assert records[0]["text"] == (
        "(1) This Act may be called the Bharatiya Sakshya Adhiniyam, 2023. "
        "(2) It applies to all judicial proceedings in or before any Court."
    )


def _pdf_with_lines(pages):
    """Build a PDF whose content streams draw ``(text, x, y, size)`` items in order."""
    writer = PdfWriter()
    font = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    }))
    for items in pages:
        page = writer.add_blank_page(PAGE_WIDTH, PAGE_HEIGHT)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        })
        commands = []
        for text, x, y, size in items:
            escaped = (
                text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            )
            commands.append(
                f"BT /F1 {size} Tf 1 0 0 1 {x} {y} Tm ({escaped}) Tj ET"
            )
        stream = DecodedStreamObject()
        stream.set_data("\n".join(commands).encode("cp1252"))
        page[NameObject("/Contents")] = writer._add_object(stream)

    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return PdfReader(buffer)


def test_pdf_with_marginal_notes_end_to_end():
    body, note = 10, 7
    page_one = [
        ("BE it enacted by Parliament in the Seventy-fourth Year of the Republic of India as follows:", BODY_X, 760, body),
        ("CHAPTER I", 260, 730, body),
        ("PRELIMINARY", 250, 715, body),
        ("1. (1) This Sanhita may be called the Bharatiya Nagarik Suraksha Sanhita, 2023.", BODY_X, 690, body),
        ("(2) It shall come into force on such date as the Central Government may appoint.", BODY_X, 676, body),
        ("2. (1) In this Sanhita, unless the context otherwise requires,—", BODY_X, 650, body),
        ("(a) \"bail\" means release of a person accused of or suspected of an offence;", BODY_X, 636, body),
        ("Short title, extent and", MARGIN_X, 690, note),
        ("commencement.", MARGIN_X, 681, note),
        ("Definitions.", MARGIN_X, 650, note),
        ("2 of 1974.", MARGIN_X, 600, note),
    ]
    page_two = [
        ("Sec. 1] THE GAZETTE OF INDIA EXTRAORDINARY 3", BODY_X, 810, body),
        ("(b) \"bailable offence\" means an offence shown as bailable in the First Schedule;", BODY_X, 780, body),
        ("3. A police officer making an arrest without warrant shall, without unnecessary", BODY_X, 750, body),
        ("delay and subject to the provisions herein contained as to bail, take or send the", BODY_X, 736, body),
        ("person arrested before a Magistrate having jurisdiction in the case.", BODY_X, 722, body),
        ("Person arrested to be", MARGIN_X, 750, note),
        ("taken before Magistrate", MARGIN_X, 741, note),
        ("or officer in charge of", MARGIN_X, 732, note),
        ("police station.", MARGIN_X, 723, note),
        ("THE FIRST SCHEDULE", 230, 690, body),
        ("1. Classification of offences under the Bharatiya Nyaya Sanhita, 2023.", BODY_X, 670, body),
    ]

    records = parse_pdf(_pdf_with_lines([page_one, page_two]))

    assert [(r["section"], r["title"]) for r in records] == [
        ("1", "Short title, extent and commencement."),
        ("2", "Definitions."),
        ("3", "Person arrested to be taken before Magistrate or officer in charge of police station."),
    ]
    assert records[0]["text"] == (
        "(1) This Sanhita may be called the Bharatiya Nagarik Suraksha "
        "Sanhita, 2023. (2) It shall come into force on such date as the "
        "Central Government may appoint."
    )
    assert records[1]["text"].startswith("(1) In this Sanhita")
    assert records[1]["text"].endswith(
        "(b) \"bailable offence\" means an offence shown as bailable in the "
        "First Schedule;"
    )
    assert records[2]["text"].startswith(
        "A police officer making an arrest without warrant shall"
    )
    assert records[2]["text"].endswith("having jurisdiction in the case.")
    assert all(r["chapter"] == "Chapter I" for r in records)
    for record in records:
        assert "1974" not in record["text"]
        assert "GAZETTE" not in record["text"]
        assert "Classification" not in record["text"]
