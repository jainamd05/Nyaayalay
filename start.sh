#!/bin/bash
python scripts/ingest_legal_corpus.py
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT