from dataclasses import dataclass
import re
import chromadb
from .config import (
    CHROMA_COLLECTION, CHROMA_DIR, LEXICAL_WEIGHT,
    RETRIEVAL_POOL_SIZE, SEMANTIC_WEIGHT, TOP_K,
)
from .domains import acts_for_domain

STOPWORDS = {
    "a","an","and","are","as","at","be","been","by","for","from","had","has",
    "have","he","her","his","i","in","is","it","its","of","on","or","she",
    "that","the","their","there","they","this","to","was","were","with","you","your"
}

@dataclass
class Candidate:
    act: str
    section: str
    title: str
    text: str
    distance: float | None = None
    semantic_score: float = 0.0
    lexical_score: float = 0.0
    retrieval_score: float = 0.0

def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(CHROMA_COLLECTION)

def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,}", text.lower())
    return {w for w in words if w not in STOPWORDS}

def _semantic_score(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return 1.0 / (1.0 + max(distance, 0.0))

def _lexical_score(query: str, candidate: Candidate) -> float:
    q = _tokens(query)
    if not q:
        return 0.0
    c = _tokens(f"{candidate.title} {candidate.text} {candidate.section}")
    return len(q & c) / len(q)

def retrieve_candidates(query: str, domain: str, top_k: int = TOP_K) -> list[Candidate]:
    acts = acts_for_domain(domain)
    if not acts:
        return []

    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []

    pool_size = min(max(top_k, RETRIEVAL_POOL_SIZE), count)
    result = collection.query(
        query_texts=[query],
        n_results=pool_size,
        where={"act": {"$in": acts}},
        include=["documents", "metadatas", "distances"],
    )

    candidates = []
    for document, metadata, distance in zip(
        result.get("documents", [[]])[0],
        result.get("metadatas", [[]])[0],
        result.get("distances", [[]])[0],
    ):
        c = Candidate(
            act=metadata.get("act", "UNKNOWN"),
            section=metadata.get("section", "UNKNOWN"),
            title=metadata.get("title", ""),
            text=document,
            distance=distance,
        )
        c.semantic_score = _semantic_score(distance)
        c.lexical_score = _lexical_score(query, c)
        c.retrieval_score = (
            SEMANTIC_WEIGHT * c.semantic_score
            + LEXICAL_WEIGHT * c.lexical_score
        )
        candidates.append(c)

    candidates.sort(key=lambda c: c.retrieval_score, reverse=True)
    return candidates[:top_k]
