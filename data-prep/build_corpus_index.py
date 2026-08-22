import json
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CHROMA_DIR = ROOT / "data" / "chroma"
COLLECTION_NAME = "nyayalay_legal_corpus"


def load_records():
    records = []
    for path in sorted(RAW_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            records.extend(data)
        else:
            records.append(data)
    return records


def main():
    records = load_records()
    if not records:
        raise SystemExit("No JSON corpus files found in data/raw/.")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(COLLECTION_NAME)

    ids, documents, metadatas = [], [], []

    for i, record in enumerate(records):
        required = ["act", "section", "text"]
        missing = [key for key in required if not record.get(key)]
        if missing:
            raise ValueError(f"Record {i} is missing: {missing}")

        ids.append(f"{record['act']}::{record['section']}::{i}")
        documents.append(record["text"])
        metadatas.append(
            {
                "act": record["act"],
                "section": record["section"],
                "title": record.get("title", ""),
            }
        )

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"Indexed {len(records)} records into {COLLECTION_NAME}.")


if __name__ == "__main__":
    main()
