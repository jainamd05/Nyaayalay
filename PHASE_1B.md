# Nyayalay Phase 1B — Real Legal Corpus

## Goal

Replace the 3-record development corpus with a reproducible corpus pipeline based
on official India Code copies of BNS, BNSS, and BSA.

## Acts

- BNS — Bharatiya Nyaya Sanhita, 2023
- BNSS — Bharatiya Nagarik Suraksha Sanhita, 2023
- BSA — Bharatiya Sakshya Adhiniyam, 2023

## Commands

Install the new dependency:

```powershell
pip install -r requirements.txt
```

Download official PDFs:

```powershell
python data-prep/download_official_acts.py BNS BNSS BSA
```

Parse them:

```powershell
python data-prep/parse_act_pdf.py BNS BNSS BSA
```

Validate:

```powershell
python data-prep/validate_corpus.py BNS BNSS BSA
```

Build Chroma:

```powershell
python data-prep/build_corpus_index.py BNS BNSS BSA
```

Run tests:

```powershell
pytest
```

## Important

The downloaded PDFs and generated Chroma database are ignored by Git. The
repository stores the reproducible tooling and source URLs, not generated
artifacts.

The parser is intentionally conservative and should be validated against the
official source before treating the resulting corpus as production legal data.
