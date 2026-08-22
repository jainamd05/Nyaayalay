# Nyayalay

Nyayalay is a retrieval-grounded legal information assistant designed around one core rule:

> **The model should not invent legal sections.**

The system first determines the legal domain, extracts structured facts from the user's incident, retrieves relevant provisions from a local legal corpus, classifies the best candidate, and verifies the result against the retrieved text.

## Current scope

The first implementation focuses on the **criminal-law pipeline** and is designed so additional domains can be added later without rewriting the pipeline.

Current status:

- Domain router: implemented
- Fact extraction: implemented
- Chroma retrieval: implemented
- Section classification: implemented
- Verification: implemented
- End-to-end pipeline: implemented
- Sample corpus: included for local smoke testing
- Full authoritative legal corpus: **not bundled**; add your legally sourced corpus under `data/raw/`

This project is an information/research tool, not a substitute for a qualified lawyer or official legal source.

## Architecture

```text
User incident
     |
     v
+----------------+
| Domain Router  |
+----------------+
     |
     +---- unsupported -> safe response
     |
     v
+----------------+
| Fact Extractor |
+----------------+
     |
     v
+------------------------+
| Domain-filtered Search |
|       (Chroma)         |
+------------------------+
     |
     v
+----------------+
| Classification |
+----------------+
     |
     v
+----------------+
| Verification   |
+----------------+
     |
     v
Grounded result
```

## Repository layout

```text
nyayalay/
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── README.md
├── pyproject.toml
├── requirements.txt
│
├── data/
│   ├── raw/
│   │   └── sample_bns.json
│   └── chroma/
│
├── data-prep/
│   ├── build_corpus_index.py
│   ├── scrape_bns_index.py
│   └── scrape_bns_sections.py
│
├── src/
│   └── nyayalay/
│       ├── __init__.py
│       ├── classification.py
│       ├── config.py
│       ├── domains.py
│       ├── extraction.py
│       ├── llm_utils.py
│       ├── pipeline.py
│       ├── retrieval.py
│       ├── router.py
│       ├── schemas.py
│       └── verification.py
│
└── tests/
    ├── test_classification.py
    ├── test_extraction.py
    ├── test_pipeline.py
    ├── test_retrieval.py
    ├── test_router.py
    └── test_verification.py
```

## Setup

### 1. Create and activate a virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Configure the API key

Copy `.env.example` to `.env` and add your Google Gemini API key.

### 4. Build the local vector index

```bash
python data-prep/build_corpus_index.py
```

The script reads JSON files from `data/raw/` and creates the Chroma database in `data/chroma/`.

### 5. Run tests

```bash
pytest
```

Tests that exercise the LLM require `GEMINI_API_KEY`. The router and retrieval smoke tests can be run independently.

### 6. Run the pipeline

```bash
python -m nyayalay.pipeline
```

## Corpus format

Put legally sourced section data into `data/raw/*.json`.

Example:

```json
[
  {
    "act": "BNS",
    "section": "example-section",
    "title": "Example title",
    "text": "Authoritative section text..."
  }
]
```

The corpus should be sourced from an authoritative or properly licensed source. Do not scrape or redistribute a website merely because it is technically accessible.

## Adding a new legal domain

Add a new entry to `src/nyayalay/domains.py`, then add its extraction schema in `schemas.py` and its corpus.

The rest of the pipeline remains domain-agnostic.

## Important design rule

Retrieval is performed with a metadata filter based on the routed domain. This prevents a criminal-law query from retrieving documents belonging to a different legal domain.

## Development sequence

1. Verify the package imports.
2. Build the sample Chroma index.
3. Run router/retrieval tests.
4. Configure the LLM.
5. Run extraction/classification/verification tests.
6. Replace the sample corpus with a properly sourced corpus.
7. Add a UI/API only after the backend pipeline is stable.


## Gemini models

Nyayalay uses Google's official `google-genai` Python SDK.

The default development model is:

```text
gemini-2.5-flash
```

You can change the model without changing application code:

```env
GEMINI_MODEL=your-model-name
```

The pipeline uses Gemini structured JSON output with Pydantic schemas for domain routing, fact extraction, classification, and verification. Google's documentation explicitly supports structured output with Pydantic schemas. See the official documentation: https://ai.google.dev/gemini-api/docs/structured-output
