# ADR-0003: Use FastAPI and LangGraph

- Status: Accepted
- Date: 2026-07-27

## Context

Document parsing, embeddings, RAG evaluation, and agent tooling have strong
Python ecosystems. The alignment workflow must pause for clarification and
review, resume safely, expose progress, and bound retries.

## Decision

Use FastAPI for HTTP/OpenAPI and LangGraph for the explicit persisted workflow.
Keep domain rules and claim verification independent of framework code.

## Consequences

- API schemas and documentation are generated from typed Python models.
- LangGraph checkpoints support interruptions and resumability.
- Framework abstractions must not replace deterministic policy checks.
- Provider calls remain behind ports so tests can use deterministic fakes.

