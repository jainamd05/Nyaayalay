from nyayalay.retrieval import retrieve_candidates


TESTS = [
    ("theft of a mobile phone", "criminal"),
    ("person intentionally killed another person", "criminal"),
    ("someone cheated me and took my money", "criminal"),
    ("how can a person apply for bail after arrest", "criminal_procedure"),
    ("is an electronic message admissible as evidence", "evidence"),
]

def main():
    for query, domain in TESTS:
        print("\n" + "=" * 80)
        print(f"QUERY:  {query}")
        print(f"DOMAIN: {domain}")
        print("-" * 80)

        candidates = retrieve_candidates(
            query=query,
            domain=domain,
            top_k=5,
        )

        if not candidates:
            print("NO CANDIDATES RETRIEVED")
            continue

        for rank, candidate in enumerate(candidates, start=1):
            print(f"\n#{rank}")
            print(f"Act:      {candidate.act}")
            print(f"Section:  {candidate.section}")
            print(f"Title:    {candidate.title}")
            print(f"Score:    {candidate.retrieval_score:.4f}")
            print(f"Semantic: {candidate.semantic_score:.4f}")
            print(f"Lexical:  {candidate.lexical_score:.4f}")
            print(f"Text:     {candidate.text[:500]}")


if __name__ == "__main__":
    main()