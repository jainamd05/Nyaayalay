# Nyayalay — System Architecture

## 1. Goal

Nyayalay converts a natural-language incident into a **grounded legal-information result**.

It does not ask the LLM to directly guess a section.

Instead:

```text
Incident
  -> domain
  -> structured facts
  -> candidate provisions
  -> best candidate
  -> verification
  -> answer
```

## 2. Layered design

### Layer A — Configuration

`config.py`

Owns environment variables, model configuration, and data paths.

### Layer B — Domain registry

`domains.py`

Defines which legal domains are supported and which Acts belong to each domain.

### Layer C — LLM boundary

`llm_utils.py`

Contains the common LLM call mechanism. Individual pipeline stages should not duplicate client setup.

### Layer D — Reasoning stages

- `router.py`
- `extraction.py`
- `classification.py`
- `verification.py`

Each stage has one job.

### Layer E — Retrieval

`retrieval.py`

Searches Chroma and applies the domain's Act filter before returning candidates.

### Layer F — Orchestration

`pipeline.py`

Controls the order and error handling of the stages.

### Layer G — Data preparation

`data-prep/`

Prepares and indexes the legal corpus. It is deliberately outside the application package.

## 3. Why `src/`?

The `src/nyayalay` layout is a standard Python package layout.

It prevents accidental imports from the repository root and makes the package behave like a real installable project.

## 4. Why tests are separate?

Tests validate behavior without mixing test code into application code.

Each test file maps to one pipeline stage.

## 5. Why data is separate?

Legal source material and generated vector indexes are data, not application code.

Generated indexes should not be committed to Git.

## 6. Adding consumer/civil law later

The intended change is:

1. Add `consumer` to the domain registry.
2. Add its extraction schema.
3. Add the corresponding corpus.
4. Rebuild the vector index.
5. Add tests.

The router and pipeline orchestration do not need to be rewritten.

## 7. Safety boundary

If:

- the domain is unsupported,
- retrieval returns no candidates,
- classification confidence is too low, or
- verification fails,

the system should decline to produce a confident section recommendation.

That behavior is a feature, not an error.

# 8. Full product architecture

The repository is intentionally split into **frontend**, **backend**, **AI engine**, **data preparation**, **data**, and **tests**.

```text
NYAYALAY/
│
├── frontend/                    # What the user sees
│   ├── src/
│   │   ├── components/          # Reusable UI pieces
│   │   ├── pages/               # Screens
│   │   ├── services/            # API calls
│   │   ├── types/               # TypeScript contracts
│   │   └── styles/              # Global/page styles
│   └── package.json
│
├── backend/                     # HTTP/API application
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/          # HTTP endpoints
│   │   ├── schemas/             # Request/response validation
│   │   ├── services/            # Application-level services
│   │   └── core/                # API configuration
│   └── requirements.txt
│
├── src/nyayalay/                # AI/legal reasoning engine
│   ├── router.py
│   ├── extraction.py
│   ├── retrieval.py
│   ├── classification.py
│   ├── verification.py
│   └── pipeline.py
│
├── data-prep/                   # Corpus acquisition/indexing
├── data/
│   ├── raw/                     # Source corpus
│   └── chroma/                  # Generated vector index
│
├── tests/                       # Core engine tests
├── pyproject.toml
├── docker-compose.yml
└── README.md
```

## 9. Request lifecycle

```text
Browser
  │
  │ POST /api/analysis
  ▼
FastAPI Route
  │
  ▼
Analysis Service
  │
  ▼
Nyayalay Pipeline
  │
  ├── 1. Domain Router
  │       │
  │       └── unsupported → safe response
  │
  ├── 2. Fact Extraction
  │       │
  │       └── Gemini structured output
  │
  ├── 3. Retrieval
  │       │
  │       └── Chroma + domain metadata filter
  │
  ├── 4. Classification
  │       │
  │       └── Gemini chooses only retrieved candidates
  │
  └── 5. Verification
          │
          └── Gemini checks result against evidence
  │
  ▼
FastAPI JSON response
  │
  ▼
React result UI
```

## 10. Why this separation matters

### Frontend
Should know **what the user wants to do**, not how legal retrieval works.

### Backend
Should know **how to expose Nyayalay as an API**, not how the React UI is styled.

### Core engine
Should know **how legal analysis works**, not how HTTP requests or browser components work.

### Data preparation
Should know **how the corpus is prepared**, not how a user submits an incident.

This makes each layer independently replaceable.

## 11. Future expansion

The architecture leaves room for:

```text
backend/app/
├── api/routes/
│   ├── analysis.py
│   ├── auth.py
│   ├── history.py
│   └── documents.py
│
├── services/
│   ├── legal_service.py
│   ├── history_service.py
│   └── document_service.py
│
└── repositories/
    └── ...
```

and:

```text
frontend/src/
├── components/
│   ├── ChatInput.tsx
│   ├── EvidenceCard.tsx
│   ├── SectionCard.tsx
│   ├── ConfidenceBadge.tsx
│   └── SourceCitation.tsx
│
├── pages/
│   ├── Home.tsx
│   ├── Analysis.tsx
│   ├── History.tsx
│   └── About.tsx
│
└── services/
    ├── api.ts
    └── analysis.ts
```

Authentication, history, document upload, and user accounts should be added only after the legal-analysis API is stable.
