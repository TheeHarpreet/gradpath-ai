# Product Diagrams

## Purpose

The diagrams in the main README demonstrate requirements-first planning before
implementation. They are stored as Mermaid source so GitHub can render them
directly and every change remains visible in version control.

## Diagram types

### Planned user journey

This flowchart describes the user's end-to-end outcome: provide evidence,
analyse a vacancy, review changes, obtain an aligned CV, and apply independently.
It is a product requirement rather than a claim about the implementation.

### Evidence and safety workflow

This flowchart expresses the central safety rule: no important candidate claim
may enter the approved CV without supporting evidence and user control. It also
shows how partial, missing, and clarified evidence are treated differently.

### Preliminary conceptual ERD

The Entity Relationship Diagram identifies the information GradPath AI is
expected to manage. It is intentionally conceptual during Step 1.

Step 2 must validate:

- whether candidate profiles and applications need separate ownership models;
- how source documents and extracted evidence are retained or deleted;
- how citations are represented;
- whether CV versions are immutable;
- how change decisions and audit events are recorded;
- which data belongs in PostgreSQL, object storage, and a vector index;
- privacy, encryption, deletion, and retention requirements;
- primary keys, foreign keys, unique constraints, and indexes.

## Diagrams planned for Step 2

The architecture stage will add:

1. System context diagram - users and external systems around GradPath AI.
2. Container diagram - web UI, API, agent service, MCP server, workers, data
   stores, model providers, and document storage.
3. Component diagram - internal backend and agent modules.
4. Agent state diagram - nodes, branches, retries, approvals, and termination.
5. RAG sequence diagram - ingestion, retrieval, reranking, generation, and
   citation verification.
6. Trust-boundary and data-flow diagram - personal data and security controls.
7. Deployment diagram - local Docker and managed cloud environments.
8. Physical ERD - implementation-ready database tables and constraints.

Detailed architecture diagrams are intentionally deferred until technology
choices have been compared and recorded as architecture decisions.
