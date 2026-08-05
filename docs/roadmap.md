# Delivery Roadmap

This roadmap is ordered by dependency. Later stages rely on decisions and tests
created earlier.

## Stage 1 — Product definition

- Define the user, problem, value proposition, user stories, non-goals, success
  criteria, risks, and shared terminology.
- Define permitted and prohibited CV-alignment behaviour.
- Define the evidence, clarification, change-review, and approval workflows.
- Create product-level diagrams and a preliminary conceptual data model.
- Exit condition: the product brief is internally consistent and gives us
  testable boundaries.

## Stage 2 — Architecture and repository engineering

- Draw the system-context, container, agent-workflow, RAG, and deployment
  diagrams.
- Compare implementation options and record architecture decisions.
- Establish the Python project, formatting, linting, tests, pre-commit checks,
  environment template, licence, contribution guide, and GitHub issue plan.
- Exit condition: a new developer can explain the proposed system and run the
  empty application/test skeleton.

## Stage 3 — Evaluation dataset and simplest vertical slice

- Create fictional candidate profiles and job descriptions.
- Define expected requirements, supporting evidence, prohibited claims, and
  aligned CV output.
- Implement one end-to-end path from pasted text to a cited match report,
  change report, and aligned CV in Markdown.
- Exit condition: one request crosses the real API, retrieval, model, and output
  boundaries, with at least one automated end-to-end test.

## Stage 4 — RAG foundation

- Implement safe document parsing, chunking, embeddings, vector storage,
  retrieval, reranking, citations, and ingestion tests.
- Compare a baseline retrieval method with the selected approach.
- Exit condition: retrieval quality is measured on the evaluation dataset.

## Stage 5 — Agentic workflow

- Implement explicit workflow state, requirement extraction, retrieval,
  assessment, clarification, CV drafting, citation verification, bounded
  retries, and human approval.
- Exit condition: the workflow handles success, uncertainty, provider failure,
  and malicious-document test cases predictably.

## Stage 6 — MCP integration

- Build an original job-application tracker MCP server.
- Expose narrow tools and resources with input validation and permission
  boundaries.
- Test the MCP server independently and through the agent.
- Exit condition: the agent can safely read and update fictional application
  records through MCP.

## Stage 7 — User interface and product controls

Status: implemented on the `codex/step-7-product-ui` branch with automated,
document-render, desktop-browser, and mobile-browser verification.

- Build the upload, analysis, requirement report, clarification, citation,
  accept/edit/reject, final-preview, export, and deletion experiences.
- Add editable DOCX and viewable PDF export after the structured-text workflow
  is reliable.
- Add accessibility and responsive-layout checks.
- Exit condition: a new user can complete the core workflow without terminal
  access.

## Stage 8 — Security, privacy, and reliability

Status: implemented on the `codex/step-8-security-reliability` branch with
abuse-case, privacy, access-control, throttling, fallback, and readiness tests.

- Add prompt-injection defences, file limits, redaction, authentication or a
  safe public-demo mode, rate limiting, structured logs, health checks, and
  provider fallbacks.
- Create a threat model and data lifecycle.
- Exit condition: documented abuse cases and failure modes have tests or
  explicit mitigations.

## Stage 9 — Containers, CI/CD, and managed cloud deployment

- Create production Docker images.
- Run linting, tests, security checks, and builds in GitHub Actions.
- Deploy to Google Cloud Run with managed secrets, least-privilege IAM,
  monitoring, budget alerts, and rollback instructions.
- Exit condition: the public demo is reproducibly deployed from a reviewed
  commit.

## Stage 10 — Infrastructure comparison

- Deploy or document the same container on an eligible Compute Engine VM.
- Compare managed Cloud Run with VM operations.
- Learn Kubernetes locally and create a minimal manifest only if it adds
  educational value.
- Exit condition: the trade-offs among managed, unmanaged, and orchestrated
  infrastructure can be explained with evidence from the project.

## Stage 11 — Evaluation and observability

- Measure retrieval quality, citation correctness, unsupported claims,
  requirement extraction, accepted-change integrity, tool-call success, task
  completion, latency, and estimated cost.
- Compare baseline RAG with reranking/corrective retrieval.
- Exit condition: a reproducible report contains results, failures, and honest
  limitations.

## Stage 12 — Portfolio and job-search presentation

- Finish the README, diagrams, architecture decisions, demo video, screenshots,
  live URL, release, and CV/LinkedIn wording.
- Practise a five-minute explanation and deeper technical questions.
- Exit condition: a recruiter can understand the problem, engineering depth,
  evidence, and live result within two minutes.
