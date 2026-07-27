# ADR-0001: Use a modular monolith in a monorepo

- Status: Accepted
- Date: 2026-07-27

## Context

GradPath AI has distinct web, API, agent, retrieval, export, and MCP concerns,
but it is developed by one person and has no measured scaling bottleneck. Starting
with microservices would introduce network failure, distributed tracing,
multiple deployments, contract versioning, and higher cloud cost.

## Decision

Use one repository. Deploy the web application separately, while the API,
domain rules, RAG, and agent workflow form a modular Python monolith. Keep the
MCP adapter as a separate entry point that calls the application-service layer.

## Consequences

- Local development and testing remain simple.
- Domain transactions can remain atomic.
- Module boundaries must be enforced through imports and tests rather than
  network APIs.
- A module may be extracted later if scaling, ownership, or reliability evidence
  justifies it.

