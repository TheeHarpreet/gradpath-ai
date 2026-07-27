# ADR-0002: Use React, TypeScript and Vite

- Status: Accepted
- Date: 2026-07-27

## Context

The product needs a rich authenticated workflow with uploads, progress, evidence
citations, and accept/edit/reject controls. Public SEO and server-rendered content
are not primary requirements.

## Decision

Use React with TypeScript and Vite as a single-page application. Communicate
with the backend through generated or validated OpenAPI contracts.

## Consequences

- The frontend has a small, explicit deployment surface.
- TypeScript, accessibility, component tests, and end-to-end tests become visible
  portfolio evidence.
- The API remains the authoritative security and domain boundary.
- If public content or SSR becomes important, this ADR must be revisited.

