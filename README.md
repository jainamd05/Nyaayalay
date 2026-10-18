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

Copy `.env.example` to `.env` and add your Groq API key (`GROQ_API_KEY`).

### 4. Build the local vector index

A ready-made index of the BNS, BNSS and BSA is committed in `data/chroma/`, so this step is only needed after changing the corpus:

```bash
python data-prep/download_official_acts.py   # official PDFs from India Code
python data-prep/parse_act_pdf.py            # -> data/processed/*_sections.json
python scripts/ingest_legal_corpus.py        # -> data/chroma/ (all three Acts)
```

Use `scripts/ingest_legal_corpus.py` for the index the app uses; `data-prep/build_corpus_index.py` indexes only the BNS by default.

### 5. Run tests

```bash
pytest
```

Tests that exercise the LLM require `GROQ_API_KEY`. The router and retrieval smoke tests can be run independently.

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


## LLM provider

Nyayalay calls Groq through its OpenAI-compatible API (`openai` Python SDK) and asks for JSON output validated against Pydantic schemas.

```env
GROQ_API_KEY=your_key
LLM_MODEL=openai/gpt-oss-20b
# Optional: any other OpenAI-compatible endpoint
# LLM_BASE_URL=https://api.groq.com/openai/v1
```

## Running locally

```bash
pip install -r requirements.txt
bash start.sh                     # API on http://127.0.0.1:8000 (docs at /docs)
cd frontend && npm install && npm run dev   # UI on http://localhost:5173
```

## Deployment

### Backend (Render)

`render.yaml` describes the service. If you configure it by hand:

- Root directory: repository root (not `backend/`)
- Build command: `pip install -r requirements.txt`
- Start command: `bash start.sh`
- Environment variables:
  - `GROQ_API_KEY` — required
  - `LLM_MODEL` — optional, defaults to `openai/gpt-oss-20b`
  - `FRONTEND_URL` — your Vercel URL (comma-separated for several). Any `*.vercel.app` origin is allowed by default.

`GET /api/health` reports whether the LLM key is configured. The Chroma index in `data/chroma/` is committed and used as-is; the embedding model is downloaded and loaded in the background at startup.

### Frontend (Vercel)

- Root directory: `frontend`
- Build command: `npm run build`, output directory: `dist`
- Environment variable: `VITE_API_BASE_URL=https://<your-service>.onrender.com` (`VITE_API_URL` is also accepted). Redeploy after changing it — Vite bakes it in at build time.

Render's free tier sleeps when idle, so the first request after a pause can take up to a minute; the UI wakes the backend as soon as the page loads.
