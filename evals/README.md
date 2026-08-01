# GradPath AI Evaluation Dataset

All people, employers, universities, and vacancies in this directory are
fictional. Do not add a real CV, email address, phone number, or employer job
description.

Case IDs are stable public identifiers. Expected results should describe facts
and safety constraints rather than require one exact writing style.

The initial case is:

- `graduate-fullstack-001`: a graduate software candidate with strong project
  evidence, limited commercial experience, partial Docker evidence, and no AWS
  or Kubernetes evidence.

## Results

- `results/step-4-rag-2026-07-30.json`: lexical, PostgreSQL hybrid, and
  reranked retrieval metrics for the first golden case. The report contains
  safe aggregate values and source IDs only—never CV text, vectors, prompts,
  model output, or credentials.
- `results/step-5-agent-workflow-2026-08-01.json`: safe summary of the live
  synthetic LangGraph, hybrid retrieval, Agents SDK, and verification path.
- `results/step-6-mcp-agent-2026-08-01.json`: safe summary of the live
  synthetic Agents SDK read and approval-gated update through local MCP.
