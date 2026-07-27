# ADR-0006: Deploy the API to Cloud Run

- Status: Accepted
- Date: 2026-07-27

## Context

The portfolio must demonstrate cloud deployment while remaining affordable and
operable by one developer. The API is HTTP-based and can remain stateless when
state is stored externally.

## Decision

Package the FastAPI application as a container and deploy it to Google Cloud
Run. Host compiled frontend assets separately. Use managed secrets, private
object storage, and managed PostgreSQL. Add a worker or Cloud Run job only when
measured asynchronous requirements justify it.

## Consequences

- The project demonstrates containers, managed/serverless infrastructure,
  logging, IAM, health checks, scaling, and CI/CD.
- Cold starts, request duration, database connections, and provider timeouts
  require deliberate configuration.
- Kubernetes remains an educational comparison, not a production dependency.
- The exact managed PostgreSQL provider remains a deployment-time decision.

