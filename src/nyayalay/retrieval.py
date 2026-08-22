from dataclasses import dataclass
import chromadb

from .config import CHROMA_COLLECTION, CHROMA_DIR, TOP_K
from .domains import acts_for_domain


@dataclass
class Candidate:
    act: str
    section: str
    title: str
    text: str
    distance: float | None = None


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(CHROMA_COLLECTION)


def retrieve_candidates(query: str, domain: str, top_k: int = TOP_K) -> list[Candidate]:
    acts = acts_for_domain(domain)
    if not acts:
        return []

    collection = get_collection()
    if collection.count() == 0:
        return []

    result = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        where={"act": {"$in": acts}},
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    candidates = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        candidates.append(
            Candidate(
                act=metadata.get("act", "UNKNOWN"),
                section=metadata.get("section", "UNKNOWN"),
                title=metadata.get("title", ""),
                text=document,
                distance=distance,
            )
        )

    return candidates
