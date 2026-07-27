# ADR-0004: Use PostgreSQL and pgvector

- Status: Accepted
- Date: 2026-07-27

## Context

Most project data is relational, but retrieval needs semantic similarity and
exact keyword matching. A second vector database would add operations,
authorisation duplication, and cross-store consistency problems.

## Decision

Use PostgreSQL for domain data, full-text search, workflow persistence, and
pgvector embeddings. Begin with exact vector search and add HNSW only after
evaluation demonstrates a latency need.

## Consequences

- Ownership filters and retrieval can occur in one database query boundary.
- SQL migrations and relational constraints remain central engineering skills.
- Very large corpora may eventually require specialised retrieval infrastructure.
- Retrieval quality must be evaluated rather than inferred from technology choice.

