# Project Glossary

## Applicant Tracking System (ATS)

Software employers use to store, search, manage, and sometimes screen
applications. GradPath AI may improve structural and keyword compatibility, but
it cannot guarantee that a particular ATS or employer will accept a CV.

## Agent

Software in which a model participates in a controlled multi-step process. The
agent may select tools or branches, but application code still defines limits,
state, permissions, retries, and termination.

## Acceptance criterion

A specific, testable condition that must be true for a feature to be considered
complete.

## Citation

A reference from a generated assessment back to the precise source material
that supports it.

## CV alignment

Reordering, rewriting, and clarifying a CV so that genuine candidate evidence is
presented clearly for a particular role. Alignment must not create experience
that the candidate does not possess.

## Embedding

A numeric representation of content used to find semantically similar material.
Similarity is useful for retrieval, but it is not proof that a candidate meets a
requirement.

## Entity Relationship Diagram (ERD)

A diagram showing the main kinds of data a system manages and the relationships
between them. A conceptual ERD describes business information; a physical ERD
later specifies implementation details such as database tables, keys, and
constraints.

## Evidence

Candidate-controlled information that can support a CV claim, including CV
content, project descriptions, employment records, portfolio material, and
specific details confirmed through clarification. Evidence retains its origin
so a generated claim can be traced and checked.

## Human in the loop

A design boundary at which a person reviews or approves an action rather than
allowing the system to act autonomously.

## Large language model (LLM)

A model that predicts and generates language. It can reason usefully in a
workflow, but it can also produce plausible false information.

## Managed infrastructure

A cloud service where the provider operates more of the underlying system. With
Cloud Run, for example, the developer supplies a container while the platform
handles much of the server management and scaling.

## Model Context Protocol (MCP)

An open protocol through which AI applications can discover and call
well-defined tools, access resources, and use reusable prompts. In this project,
MCP will provide a controlled interface to application-tracking capabilities.

## Non-goal

Something the project intentionally will not attempt within the defined scope.
Non-goals protect delivery time and clarify design decisions.

## Retrieval-augmented generation (RAG)

A pattern in which relevant source material is retrieved before a model
generates an answer. Good RAG still requires evaluation, source tracking, and
protection against misleading retrieved content.

## Serverless

A cloud execution model where the provider manages servers and scaling for the
user. Servers still exist; the application developer has less responsibility
for operating them.

## Unmanaged infrastructure

Infrastructure where the developer is responsible for more operational work. A
VM normally requires operating-system updates, firewall configuration, process
management, monitoring, and capacity decisions.

## User story

A short description of desired behaviour from a user's perspective, normally
expressed as who wants something, what they want, and why.

## Unsupported claim

A statement about the candidate for which the supplied and confirmed evidence
does not provide adequate support. Unsupported claims must be excluded from the
aligned CV or clearly presented as gaps rather than facts.

## Vertical slice

The smallest implementation that crosses the real layers of a system
end-to-end. It provides early evidence that the components can work together.
