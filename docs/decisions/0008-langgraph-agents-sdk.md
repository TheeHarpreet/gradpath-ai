# ADR 0008: LangGraph control plane with one bounded Agents SDK specialist

- Status: accepted
- Date: 2026-08-01

## Context

Step 5 needs an explicit, resumable workflow with bounded retries,
clarification, deterministic evidence checks, and candidate approval. The
repository already selected LangGraph for workflow state. Step 3 used one
direct Responses API call for typed analysis.

Using a free-form multi-agent conversation would make routing, safety, cost,
and resumption harder to reason about. Using only deterministic code would
remove the model judgement needed to assess nuanced evidence and draft useful
CV wording.

## Decision

Use LangGraph as the application-owned control plane and the OpenAI Agents SDK
for one tool-less, structured-output evidence-assessment specialist.

LangGraph owns workflow state, allowed transitions, retrieval, bounded retries,
clarification and review pauses, and final completion or failure. The agent
owns only evidence assessment and draft generation. It receives a prepared JSON
evidence package, has no tools or side effects, and must return the strict
`ModelAnalysis` schema. Application code independently verifies requirements
and citations.

## Consequences

- Control flow remains inspectable and testable without model calls.
- The Agents SDK provides a standard agent loop, typed output, and optional
  privacy-controlled tracing.
- One agent is cheaper and easier to evaluate than premature specialists.
- Process-local workflow persistence is suitable only for Step 5 development;
  a PostgreSQL repository is required before production deployment.
- Additional agents are justified only when a specialist needs a materially
  different contract, policy, model, or tool surface.

## Alternatives considered

### Agents SDK handoffs between several specialists

Rejected for now because extraction, assessment, verification, and drafting do
not yet need independent conversational ownership. This would add calls and
routing uncertainty before evaluation demonstrates a benefit.

### LangGraph with direct Responses API calls only

Viable, but the Agents SDK gives the project a standard agent abstraction and
trace surface while preserving LangGraph's explicit state machine.

### Model-controlled workflow and tools

Rejected because a CV or job description is untrusted text. The model must not
choose arbitrary workflow steps or execute side effects.
