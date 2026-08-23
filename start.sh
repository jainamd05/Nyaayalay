#!/bin/bash
set -e

python scripts/ingest_legal_corpus.py
exec uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port "${PORT:-8000}"