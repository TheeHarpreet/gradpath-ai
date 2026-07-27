# ADR-0005: Keep MCP as a narrow adapter

- Status: Accepted
- Date: 2026-07-27

## Context

The portfolio should demonstrate MCP without turning an interoperability
protocol into the application's internal architecture. Exposing broad write
tools would create unnecessary security risk.

## Decision

Build a separate MCP entry point exposing narrow application-tracker tools and
resources. It calls the same application services as the HTTP API and enforces
authentication, ownership, validation, and approval rules.

## Consequences

- MCP demonstrates real interoperability instead of cosmetic usage.
- Domain logic is not duplicated inside tool handlers.
- Initial local development can use stdio; remote transport requires explicit
  authentication and deployment review.
- Destructive or employer-facing actions remain outside initial MCP scope.

