from __future__ import annotations

from pathlib import Path
import json
import sys

import chromadb

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
CHROMA_DIR = ROOT / "data" / "chroma"

COLLECTION_NAME = "nyayalay_legal_corpus"

# The collection is rebuilt from scratch, so by default index every act the
# app supports. Indexing a subset would silently drop the other acts.
ALL_ACTS = ["BNS", "BNSS", "BSA"]

def create_document(record: dict) -> str:
    """Searchable text; must match scripts/ingest_legal_corpus.py."""
    parts = [
        f"Act: {record.get('act_title', record.get('act', 'Unknown'))}",
        f"Section: {record.get('section', 'Unknown')}",
    ]
    if record.get("title"):
        parts.append(f"Title: {record['title']}")
    if record.get("text"):
        parts.append(f"Text: {record['text']}")
    return "\n".join(parts)

def load_records(act_code: str) -> list[dict]:
    path = PROCESSED_DIR / f"{act_code.lower()}_2023_sections.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Parse the official PDF first."
        )
    return json.loads(path.read_text(encoding="utf-8"))

def build_index(act_codes: list[str]) -> None:
    all_records = []
    for act_code in act_codes:
        all_records.extend(load_records(act_code))

    if not all_records:
        raise RuntimeError("No legal records available for indexing.")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Rebuild the collection deterministically. This avoids stale records when
    # an official source is updated and the number of sections changes.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(COLLECTION_NAME)

    ids = [record["id"] for record in all_records]
    documents = [create_document(record) for record in all_records]
    metadatas = [
        {
            "act": record["act"],
            "section": record["section"],
            "title": record["title"],
            "chapter": record.get("chapter") or "",
            "part": record.get("part") or "",
            "domain": record.get("domain") or "",
            "source_url": record["source_url"],
        }
        for record in all_records
    ]

    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

    print(
        f"Indexed {len(all_records)} legal sections across "
        f"{len(act_codes)} acts into {COLLECTION_NAME}."
    )

def main():
    acts = [arg.upper() for arg in sys.argv[1:]]
    if not acts:
        acts = ALL_ACTS

    build_index(acts)

if __name__ == "__main__":
    main()
