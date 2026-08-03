# ADR-0009: Candidate-scoped MCP with approval-gated writes

- Status: Accepted
- Date: 2026-08-01

## Context

GradPath AI needs to demonstrate MCP interoperability without allowing a model
to browse arbitrary records or perform employer-facing actions. Application
tracker data belongs to one candidate and stage updates are meaningful state
changes.

## Decision

Expose a local/private stdio MCP server with three narrow tools and two
read-only resources. Every operation is bound to one candidate profile before
the model sees the tool surface.

Read tools are automatically callable. The stage-update tool requires both:

1. an Agents SDK approval interruption at the client boundary; and
2. a short-lived, single-use server token bound to the exact candidate,
   application, current stage, and target stage.

Business rules live in the shared application service, not the MCP decorators.
The server exposes no apply, email, delete, arbitrary URL, shell, filesystem,
or SQL capability.

## Consequences

- A malicious document cannot turn MCP into a general action surface.
- Cross-profile reads return the same not-found outcome as absent records.
- Replayed, expired, or differently scoped approvals fail.
- The web API and MCP adapter can eventually share a PostgreSQL repository.
- The initial in-memory repository is suitable only for fictional local demos.
- Remote HTTP transport is deferred until authentication and deployment review.

## Alternatives considered

### Broad CRUD tools

Rejected because they expose more capability than the agent needs and increase
the cost of authorization, testing, and review.

### Client approval only

Rejected because MCP clients differ. The server must enforce its own write
authorization even when a client has no approval UI.

### Public hosted MCP

Rejected for this stage because candidate records are private and the GradPath
runtime should own connectivity, filtering, approvals, and transport policy.
