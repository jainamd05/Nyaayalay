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

## Setup (local)

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
pip install -r requirements.txt -r backend/requirements.txt
```

### 3. Configure the API key

Copy `.env.example` to `.env` in the project root and set `GROQ_API_KEY`
(a `backend/.env` file is also picked up).

### 4. Legal index

The Chroma index for BNS, BNSS and BSA is already committed under `data/chroma/`.
To rebuild it from `data/processed/*.json`:

```bash
python scripts/ingest_legal_corpus.py
```

### 5. Run tests

```bash
pytest
```

The tests do not call the LLM, so they run without `GROQ_API_KEY`.

### 6. Run the app

Backend (http://127.0.0.1:8000, docs at `/docs`):

```bash
uvicorn app.main:app --app-dir backend --reload
```

Frontend (http://localhost:5173), in a second terminal:

```bash
cd frontend && npm install && npm run dev
```

The frontend calls `http://127.0.0.1:8000` in development unless
`VITE_API_BASE_URL` is set (see `frontend/.env.example`).

Or run both with Docker: `docker compose up --build`.

## Deployment

### Backend on Render

- Build command: `pip install -r requirements.txt -r backend/requirements.txt`
- Start command: `bash start.sh`
- Health check path: `/api/health`
- Environment variables:
  - `GROQ_API_KEY` — required
  - `LLM_MODEL` — optional, defaults to `openai/gpt-oss-20b`
  - `FRONTEND_URL` — your Vercel URL, e.g. `https://your-app.vercel.app`
    (comma-separate several; a trailing `/` is fine)
  - `FRONTEND_URL_REGEX` — optional, e.g. `https://your-app-.*\.vercel\.app`
    to also allow Vercel preview deployments

`GET /api/health` reports whether the LLM key is configured and whether the
retrieval index has finished loading.

### Frontend on Vercel

- Root directory: `frontend`
- Environment variable: `VITE_API_BASE_URL` = your Render URL, e.g.
  `https://your-api.onrender.com` (the older name `VITE_API_URL` is still
  accepted). Vite bakes this in at build time, so **redeploy** after changing it.

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

Nyayalay calls [Groq](https://console.groq.com) through its OpenAI-compatible
API using the `openai` Python SDK. The default model is `openai/gpt-oss-20b`;
change it without touching code:

```env
LLM_MODEL=your-model-name
```

Every LLM step (routing, fact extraction, classification, verification) asks for
JSON matching a Pydantic schema. Responses are validated, common formatting
quirks are normalised, and an invalid reply is retried once before failing.
