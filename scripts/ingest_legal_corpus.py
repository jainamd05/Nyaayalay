import json
from pathlib import Path

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"

COLLECTION_NAME = "nyayalay_legal_corpus"

CORPUS_FILES = [
    PROCESSED_DIR / "bns_2023_sections.json",
    PROCESSED_DIR / "bnss_2023_sections.json",
    PROCESSED_DIR / "bsa_2023_sections.json",
]


def load_sections(file_path: Path) -> list[dict]:
    """Load one processed legal corpus JSON file."""
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"{file_path.name} must contain a JSON list, "
            f"but found {type(data).__name__}"
        )

    print(f"Loaded {len(data)} records from {file_path.name}")
    return data


def create_document(record: dict) -> str:
    """Create the searchable text stored in Chroma."""
    parts = [
        f"Act: {record.get('act_title', record.get('act', 'Unknown'))}",
        f"Section: {record.get('section', 'Unknown')}",
    ]

    if record.get("title"):
        parts.append(f"Title: {record['title']}")

    if record.get("text"):
        parts.append(f"Text: {record['text']}")

    return "\n".join(parts)


def create_metadata(record: dict) -> dict:
    """Keep useful legal fields as Chroma metadata."""
    return {
        "act": str(record.get("act", "")),
        "act_title": str(record.get("act_title", "")),
        "act_number": int(record.get("act_number", 0) or 0),
        "year": int(record.get("year", 0) or 0),
        "domain": str(record.get("domain", "")),
        "section": str(record.get("section", "")),
        "title": str(record.get("title", "")),
        "chapter": str(record.get("chapter") or ""),
        "part": str(record.get("part") or ""),
        "source_url": str(record.get("source_url", "")),
        "source_file": str(record.get("source_file", "")),
    }


def main():
    all_records = []

    for corpus_file in CORPUS_FILES:
        if not corpus_file.exists():
            raise FileNotFoundError(
                f"Processed corpus file not found: {corpus_file}"
            )

        all_records.extend(load_sections(corpus_file))

    print(f"\nTotal records to index: {len(all_records)}")

    # Basic validation before modifying Chroma.
    invalid_records = [
        record
        for record in all_records
        if not record.get("id")
        or not record.get("act")
        or not record.get("section")
        or not (record.get("text") or record.get("title"))
    ]

    if invalid_records:
        print("\nInvalid records found:")

        for record in invalid_records:
            print("-" * 60)
            print(f"ID:      {record.get('id')}")
            print(f"Act:     {record.get('act')}")
            print(f"Section: {record.get('section')}")
            print(f"Title:   {record.get('title')}")
            print(f"Text:    {repr(record.get('text'))}")

        raise ValueError(
            f"\nFound {len(invalid_records)} invalid records. "
            "Chroma was NOT modified."
        )

    print(f"Connecting to Chroma at: {CHROMA_DIR}")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Delete ONLY the old legal corpus collection.
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted old collection: {COLLECTION_NAME}")
    except Exception:
        print("No existing collection to delete. Creating a fresh one.")

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    ids = [str(record["id"]) for record in all_records]
    documents = [create_document(record) for record in all_records]
    metadatas = [create_metadata(record) for record in all_records]

    print("Adding authoritative legal records to Chroma...")

    # Add in batches to avoid problems with large requests.
    batch_size = 100

    for start in range(0, len(all_records), batch_size):
        end = min(start + batch_size, len(all_records))

        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )

        print(f"Indexed {end}/{len(all_records)} records")

    print("\nIngestion complete!")
    print(f"Final collection count: {collection.count()}")

    sample_ids = [
        "BNS::SAMPLE-01::0",
        "BNS::SAMPLE-02::1",
        "BNS::SAMPLE-03::2",
    ]

    result = collection.get(ids=sample_ids)

    if result["ids"]:
        print("\nWARNING: SAMPLE records are still present!")
        print(result["ids"])
    else:
        print("\nSUCCESS: No SAMPLE-* records found in the legal corpus.")


if __name__ == "__main__":
    main()