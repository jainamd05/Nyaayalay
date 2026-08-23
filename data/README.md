# Nyayalay Legal Corpus

Generated legal corpus data is intentionally not committed to Git.

## Flow

```text
Official India Code PDF
        ↓
data-prep/download_official_acts.py
        ↓
data/raw/source_pdfs/
        ↓
data-prep/parse_act_pdf.py
        ↓
data/processed/
        ↓
data-prep/validate_corpus.py
        ↓
data-prep/build_corpus_index.py
        ↓
data/chroma/
```

The source URLs are stored in `data-prep/act_sources.py`.

The repository contains the tooling, not downloaded legal PDFs or generated
Chroma files.
