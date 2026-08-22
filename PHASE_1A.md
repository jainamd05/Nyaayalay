# Nyayalay Phase 1A — Core AI Engine Hardening

Phase 1A makes the existing pipeline safer and more retrieval-grounded.

## Changes

- Router rejects unknown and low-confidence domains.
- Fact extraction captures richer factual signals and missing information.
- Retrieval uses a larger semantic pool, domain/Act filtering, and lightweight lexical reranking.
- Classification can select only an exact retrieved section and records its candidate rank.
- Verification is a final fail-closed evidence gate.
- Pipeline builds a richer retrieval query and exposes retrieval evidence for debugging/UI.

## Important

The current corpus is still development sample data. These changes improve the engine architecture; they do not make sample text authoritative legal material.
