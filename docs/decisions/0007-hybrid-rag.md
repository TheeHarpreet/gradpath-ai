# ADR-0007: Use measured hybrid retrieval with provider-neutral embeddings

- Status: Accepted
- Date: 2026-07-30

## Context

The Step 3 lexical baseline is transparent but misses evidence when a job
requirement and candidate source use different vocabulary. On the first golden
case its top-three Hit Rate is 60%, Recall is 44.44%, and Mean Reciprocal Rank
is 0.60. Dense retrieval can recover semantic matches, but vector similarity
alone can miss exact technologies, acronyms, and negation. Adding a separate
vector database would duplicate operational and authorization boundaries.

GradPath AI also needs reproducible tests that do not call a paid provider and
must not treat retrieval scores as proof that a candidate meets a requirement.

## Decision

1. Keep PostgreSQL as the retrieval system of record and use the open-source
   `pgvector` extension selected by ADR-0004.
2. Use PostgreSQL full-text ranking for lexical candidates and exact pgvector
   cosine search for semantic candidates.
3. Use Reciprocal Rank Fusion (RRF) to combine rank positions. Do not directly
   add lexical and cosine scores because their scales have different meanings.
4. Start with exact vector search. Add HNSW only after corpus-size and latency
   measurements justify an approximate index.
5. Define an embedding-provider port. Use OpenAI `text-embedding-3-small` with
   its default 1,536 dimensions in the first real adapter and deterministic
   embeddings in automated tests.
6. Define a reranker port. Compare fused retrieval with a deterministic
   evidence-aware reranker before adopting a local or hosted cross-encoder.
7. Preserve source IDs and original text through every stage. Retrieval returns
   evidence candidates; independent validation still decides whether a citation
   is genuine.
8. Record the embedding model and dimensions with stored vectors. Changing
   either requires re-embedding rather than mixing incompatible vector spaces.

## Alternatives considered

### Lexical search only

Rejected as the final approach because the measured baseline misses semantic
matches such as CI/CD versus GitHub Actions. It remains the control system and
one half of hybrid retrieval.

### Vector search only

Rejected because exact skill names, acronyms, versions, and negative evidence
benefit from lexical matching. Semantic similarity is not factual entailment.

### A specialised vector database

Deferred. The candidate corpus is small, PostgreSQL is already required, and a
second store would duplicate access control, deletion, backup, and consistency
work without measured benefit.

### Local Sentence Transformers for all embeddings

Deferred. This can reduce provider dependency and is a useful later comparison,
but introduces model downloads, larger containers, CPU and memory requirements,
and Python ML runtime compatibility. The provider port keeps this option open.

### Cross-encoder reranking immediately

Deferred until evaluation. Cross-encoders often improve ranking but add model
weight, latency, and per-query computation. Step 4 will measure whether the
current corpus benefits before accepting that cost.

## Consequences

- The project demonstrates SQL, full-text search, vector search, fusion,
  provider abstraction, and evaluation rather than hiding retrieval in a
  framework.
- Tests remain deterministic and free of network calls.
- Live ingestion has a small embedding cost and sends candidate-controlled text
  to the configured embedding provider.
- Exact search is intentionally simple and accurate for small per-candidate
  corpora but will not be the lowest-latency option at very large scale.
- Embeddings are derived candidate data and must be deleted with their source.

## Validation result

On 30 July 2026, the first ten-query fictional evaluation improved from a
lexical Hit Rate@3 of 0.60, Recall@3 of 0.4444, and MRR of 0.60 to a hybrid and
reranked Hit Rate@3 of 1.00, Recall@3 of 0.8333, and MRR of 0.8167. This result
accepts the deterministic evidence-aware reranker for the current stage while
continuing to defer a cross-encoder. The decision must be revisited as the
evaluation dataset expands.
