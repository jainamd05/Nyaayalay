# Development guide

## First run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python data-prep/build_corpus_index.py
pytest
```

## What to build next

1. Replace `sample_bns.json` with a properly sourced BNS corpus.
2. Add corpus validation and deduplication.
3. Add authoritative source metadata to every record.
4. Add better retrieval evaluation with a labelled test set.
5. Add BNSS and BSA corpora.
6. Add additional legal domains only after their corpora and schemas exist.
7. Add a FastAPI layer.
8. Add a frontend after the backend contract is stable.

## Important

Do not put API keys in Git.
Do not commit generated Chroma files.
Do not represent the development sample provisions as real law.


## Gemini setup

Create a Gemini API key and place it in `.env`:

```env
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

Do not commit `.env`.
