# Product Brief

## Working title

GradPath AI - an evidence-grounded CV analysis and alignment platform for UK
graduates and early-career technology candidates.

## Problem

Job descriptions are often long, inconsistent, and divided into essential and
desirable requirements. Candidates may undersell relevant evidence, overlook
genuine gaps, or use generic AI tools that produce unsupported claims.

The problem is not simply generating more application text. The problem is
helping a candidate reason from verifiable evidence to a truthful,
role-specific CV and understand every important change before using it.

## Primary user

A UK-based graduate or junior technology candidate who has a CV, project or
employment evidence, and a job description, and wants to tailor a truthful
application.

The initial product is useful across software engineering, full-stack,
frontend, backend, data, and adjacent technology roles; it is not limited to AI
developer vacancies.

## Value proposition

GradPath AI maps job requirements to cited evidence from a
candidate-controlled knowledge base, identifies supported and unsupported
requirements, asks focused clarification questions, and prepares a complete
job-aligned CV whose changes the candidate can review.

## One-sentence product promise

Given a candidate's CV, optional supporting evidence, and a job description,
GradPath AI analyses strengths and gaps and produces a truthful, job-aligned CV
with cited, explainable changes for the candidate to accept, edit, reject, and
download.

## Core workflow

1. The user supplies a fictional or redacted CV and a job description.
2. The user may also supply project, portfolio, education, or employment
   evidence.
3. The system extracts candidate evidence while retaining source references.
4. The system extracts essential, desirable, and unclear job requirements.
5. Retrieval finds the best candidate evidence for each requirement.
6. The agent classifies each requirement as supported, partially supported,
   unsupported, or uncertain.
7. Where the candidate may have omitted genuine experience, the system asks a
   focused clarification question.
8. A verification step rejects or flags claims that lack valid evidence.
9. The system prepares a requirement report and complete aligned CV.
10. Each significant change includes its reason, evidence, and confidence.
11. The user accepts, edits, or rejects suggested changes.
12. The system assembles the approved CV for copying or download.
13. The user performs a final review and applies to the job independently.

## What CV alignment may do

Alignment may:

- rewrite unclear statements using evidence already supplied;
- reorder skills, projects, and experience by relevance;
- make genuinely used technologies and responsibilities explicit;
- tailor the professional summary to the role;
- remove repetition and reduce irrelevant detail;
- use job-description terminology naturally when the evidence supports it;
- improve readability, grammar, structure, and ATS compatibility;
- propose measurable wording only when a real measurement is supplied;
- ask the user for missing details that may be genuine.

Alignment must not:

- invent employment, projects, qualifications, certifications, or education;
- invent technologies, responsibilities, dates, employers, or clients;
- manufacture numerical achievements or performance claims;
- exaggerate learning or interest into professional experience;
- change right-to-work, security-clearance, or personal-status information;
- hide uncertainty or represent a partial match as a strong match;
- optimise for keywords at the expense of truth or readability;
- submit an application without the candidate's action.

## First usable version

### Inputs

- CV pasted as text.
- Job description pasted as text.
- Optional supporting evidence pasted as text.

### Outputs

- structured job requirements;
- requirement-by-requirement evidence coverage;
- strengths, partial matches, gaps, and clarification prompts;
- a complete aligned CV in structured text or Markdown;
- a change report;
- unsupported-claim warnings.

PDF/DOCX parsing, interactive editing, persistent accounts, and document export
will follow after the text-based vertical slice proves the core reasoning.

## User stories

### US-01: Add candidate evidence

As a graduate candidate, I want to paste or upload my CV and supporting evidence
so that the system can reason from information I control.

Acceptance criteria:

- The system accepts supported text or document input.
- Each extracted evidence item retains a reference to its source.
- Invalid and empty inputs produce a useful error.
- Original content is not placed in application logs.

### US-02: Analyse a job description

As a candidate, I want the system to separate essential, desirable, and unclear
requirements so that I can prioritise my application effort.

Acceptance criteria:

- Requirements are returned as structured data.
- The output distinguishes essential, desirable, and unclear requirements.
- Every requirement retains its source text from the job description.

### US-03: Match requirements to evidence

As a candidate, I want each job requirement mapped to my strongest relevant
evidence so that I can see why the system assessed my fit.

Acceptance criteria:

- Every supported assessment cites candidate evidence.
- Assessments use supported, partially supported, unsupported, or uncertain.
- Keyword overlap alone is not treated as proof of competence.
- Conflicting evidence is surfaced rather than silently resolved.

### US-04: Identify truthful gaps

As a candidate, I want unsupported requirements clearly identified so that I
can decide whether to learn, provide more evidence, or avoid making the claim.

Acceptance criteria:

- Missing evidence is reported explicitly.
- The system does not fabricate projects, employment, metrics, or qualifications.
- Learning suggestions are distinguished from claims suitable for today's CV.

### US-05: Clarify omitted experience

As a candidate, I want the system to ask focused questions where I may possess
relevant but undocumented experience so that genuine evidence can be considered.

Acceptance criteria:

- A clarification question identifies the unsupported requirement.
- The system does not convert a vague "yes" into a strong claim.
- Confirmed details retain their user-provided origin.
- The user can decline or mark a requirement unsupported.

### US-06: Generate a complete aligned CV

As a candidate, I want a complete role-specific CV generated from verified
evidence so that I do not have to assemble isolated suggestions manually.

Acceptance criteria:

- The output contains the expected CV sections in a coherent order.
- Significant factual statements cite or trace to verified evidence.
- Unsupported requirements are not added as candidate claims.
- Original dates, qualifications, employers, and contact details are preserved
  unless the user explicitly corrects them.
- The generated CV remains readable rather than becoming a keyword list.

### US-07: Understand and control changes

As a candidate, I want to see what changed and why and accept, edit, or reject
each significant suggestion so that I retain control of my application.

Acceptance criteria:

- Each significant suggestion shows original text, suggested text, reason,
  evidence, and confidence.
- Rejected changes do not appear in the approved CV.
- Edited changes use the user's final wording.
- The system does not label the CV final until review is complete.

### US-08: Export an approved CV

As a candidate, I want to copy or download the approved CV so that I can perform
a final review and apply independently.

Acceptance criteria:

- The first version supports copying structured text or Markdown.
- Later document export supports an editable DOCX and viewable PDF.
- Export only uses accepted or user-edited suggestions.
- The application does not automatically submit the CV to an employer.

## Non-goals for the first version

1. Automatically submitting job applications.
2. Scraping job boards in ways that breach their terms or access controls.
3. Sending email, calendar invitations, or messages without explicit approval.
4. Ranking candidates for employers or making hiring decisions.
5. Claiming that an LLM score predicts whether a person will be hired.
6. Supporting every CV format, language, job board, and model provider.
7. Running a production Kubernetes cluster merely to advertise Kubernetes use.
8. Storing real personal data before privacy and deletion controls are ready.
9. Guaranteeing ATS acceptance, interviews, or employment outcomes.
10. Replacing the candidate's final factual and editorial review.

## Success criteria for the portfolio milestone

The project is portfolio-ready when:

- a public, privacy-safe demo is deployed to a cloud platform;
- the complete system runs from documented setup instructions;
- RAG returns source-linked candidate evidence;
- at least one original MCP server exposes useful, permission-controlled tools;
- the agent has an explicit workflow, validation, bounded retries, and human
  approval boundaries;
- the system produces a coherent aligned CV from accepted evidence;
- users can inspect and decide on significant changes;
- automated tests and a minimum 20-case evaluation suite run in CI;
- evaluation reports citation correctness, unsupported-claim rate, retrieval
  quality, requirement extraction, tool-call success, task completion, latency,
  and estimated cost;
- the repository includes architecture, deployment, security, evaluation, and
  AI-assisted-development documentation;
- secrets and real personal data are absent from Git history;
- a short demo shows the deployed product, review workflow, and limitations.

## Risks to address

- Prompt injection hidden inside uploaded documents.
- Incorrect parsing or retrieval leading to misleading evidence.
- Hallucinated candidate claims.
- A candidate accepting inaccurate AI-generated wording without reading it.
- Exposure of CV or contact information through logs or model providers.
- Model-provider outages, changing free tiers, and rate limits.
- Bias introduced by treating model output as an objective employability score.
- Formatting changes that reduce ATS readability.
- Generated claims that the candidate cannot defend in an interview.
- Unexpected cloud costs.

## Decisions recorded in this step

- Build one deep product instead of several shallow agents.
- Optimise for candidate assistance, not employer-side screening.
- Support a broad range of technology roles rather than only AI roles.
- Produce a complete aligned CV as well as an evidence report.
- Make evidence, citations, explainability, and user decisions central.
- Use human approval before finalising changes.
- Leave job submission entirely to the candidate.
- Begin with synthetic or redacted data.
- Treat the proposed technology stack and ERD as provisional until Step 2.
