# Architecture

## Status

Proposed architecture for Step 2. The boundaries are approved for scaffolding,
but infrastructure providers and physical database details may evolve through
Architecture Decision Records (ADRs).

## Architectural goals

1. Keep candidate claims traceable to evidence.
2. Make agent control flow explicit, bounded, resumable, and reviewable.
3. Separate untrusted document content from executable instructions and tools.
4. Keep the first deployment understandable and affordable for one developer.
5. Preserve clean boundaries that can be extracted later without beginning with
   microservices.
6. Make local development, automated testing, and cloud deployment reproducible.

## System context

The system-context diagram shows GradPath AI as one system and identifies the
people and external systems around it.

```mermaid
flowchart LR
    Candidate["Candidate<br/>uploads evidence, reviews changes,<br/>downloads an aligned CV"]
    Maintainer["Maintainer<br/>deploys, monitors and evaluates"]

    GradPath["GradPath AI<br/>evidence-grounded CV analysis<br/>and alignment platform"]

    Identity["Identity provider<br/>authentication and account recovery"]
    Model["Model and embedding providers<br/>generation, extraction and embeddings"]
    Storage["Managed cloud services<br/>object storage, database and secrets"]
    MCPClient["MCP-compatible AI client<br/>optional application-tracker consumer"]

    Candidate -->|"CV, job description,<br/>review decisions"| GradPath
    GradPath -->|"analysis, citations,<br/>aligned CV"| Candidate
    Maintainer -->|"deploys and observes"| GradPath
    GradPath <-->|"OIDC/OAuth"| Identity
    GradPath <-->|"provider-neutral APIs"| Model
    GradPath <-->|"encrypted managed access"| Storage
    MCPClient <-->|"permission-controlled MCP tools"| GradPath
```

## Container architecture

A container here means a separately running application or data store, not only
a Docker container.

```mermaid
flowchart TB
    Browser["Web browser"]

    subgraph GradPath["GradPath AI"]
        Web["Web application<br/>React + TypeScript + Vite<br/>accessible review interface"]
        API["Application API<br/>FastAPI modular monolith<br/>REST + SSE + OpenAPI"]
        Worker["Background worker<br/>document ingestion and long tasks<br/>introduced when async work requires it"]
        MCP["MCP adapter<br/>narrow application-tracker<br/>tools and resources"]
        DB[("PostgreSQL + pgvector<br/>domain data, text search,<br/>vectors and workflow state")]
        Objects[("Object storage<br/>original uploads and exports")]
    end

    IdP["Identity provider"]
    LLM["LLM provider adapter"]
    Embed["Embedding provider adapter"]
    Secrets["Secret manager"]
    ExternalMCP["MCP client"]

    Browser -->|"HTTPS"| Web
    Web -->|"JSON REST and SSE"| API
    API -->|"SQL/TLS"| DB
    API -->|"signed/object API"| Objects
    API -->|"queued task later"| Worker
    Worker --> DB
    Worker --> Objects
    API --> LLM
    API --> Embed
    Worker --> LLM
    Worker --> Embed
    Web <-->|"OIDC"| IdP
    API --> Secrets
    Worker --> Secrets
    ExternalMCP <-->|"stdio locally;<br/>authenticated HTTP later"| MCP
    MCP -->|"application service interface"| API
```

## Backend component architecture

The backend is a modular monolith. These modules are independently testable but
ship together until operational evidence justifies extracting a service.

```mermaid
flowchart LR
    Routes["API routes<br/>HTTP validation and responses"]
    App["Application services<br/>use-case orchestration"]
    Domain["Domain model<br/>rules and state transitions"]

    Ingest["Document ingestion<br/>validation, parsing, chunking"]
    Retrieval["Retrieval<br/>full-text, vectors, fusion, reranking"]
    Workflow["Alignment workflow<br/>LangGraph state machine"]
    Verify["Claim verification<br/>citations and policy rules"]
    Export["CV export<br/>Markdown first, DOCX/PDF later"]
    Tracker["Application tracker<br/>MCP-facing use cases"]

    Ports["Provider ports<br/>LLM, embeddings, storage,<br/>identity, clock and IDs"]
    Persistence["Repositories<br/>SQLAlchemy and PostgreSQL"]

    Routes --> App
    App --> Domain
    App --> Ingest
    App --> Retrieval
    App --> Workflow
    Workflow --> Retrieval
    Workflow --> Verify
    Workflow --> Export
    App --> Tracker
    Ingest --> Ports
    Retrieval --> Ports
    Workflow --> Ports
    Export --> Ports
    App --> Persistence
    Ingest --> Persistence
    Retrieval --> Persistence
    Workflow --> Persistence
    Tracker --> Persistence
```

## Agent state machine

The agent is an explicit workflow. It cannot invent additional workflow steps
or execute arbitrary tools.

```mermaid
stateDiagram-v2
    [*] --> ValidateInput
    ValidateInput --> ExtractCandidateEvidence: valid
    ValidateInput --> Failed: invalid or unsafe input

    ExtractCandidateEvidence --> ExtractRequirements
    ExtractRequirements --> RetrieveEvidence
    RetrieveEvidence --> AssessRequirements
    AssessRequirements --> VerifyAssessments

    VerifyAssessments --> RetrieveEvidence: recoverable retrieval gap and retries remain
    VerifyAssessments --> AwaitClarification: genuine candidate detail may be missing
    VerifyAssessments --> DraftCV: evidence is sufficient or gaps are explicit

    AwaitClarification --> RetrieveEvidence: candidate supplies verified detail
    AwaitClarification --> DraftCV: candidate declines or confirms a gap

    DraftCV --> VerifyClaims
    VerifyClaims --> DraftCV: correctable unsupported wording and retries remain
    VerifyClaims --> Failed: retry limit exceeded
    VerifyClaims --> AwaitReview: draft and citations pass policy checks

    AwaitReview --> AssembleApprovedCV: candidate accepts, edits or rejects changes
    AssembleApprovedCV --> ExportReady
    ExportReady --> [*]
    Failed --> [*]
```

### Workflow invariants

- Retrieved document text is data, never an instruction source.
- Every supported assessment references one or more evidence items.
- Unsupported requirements remain gaps and never become candidate claims.
- Retry counters are bounded and stored in workflow state.
- Human interruptions are persisted before waiting for input.
- Side effects before an interrupt must be idempotent.
- Only accepted or user-edited suggestions enter the approved CV.

## RAG and alignment sequence

```mermaid
sequenceDiagram
    autonumber
    actor Candidate
    participant Web
    participant API
    participant Ingestion
    participant DB as PostgreSQL/pgvector
    participant Agent as LangGraph workflow
    participant Model as Model adapters
    participant Verifier

    Candidate->>Web: Submit CV, job description and optional evidence
    Web->>API: POST analysis request
    API->>Ingestion: Validate and parse inputs
    Ingestion->>DB: Store sources, chunks and provenance
    Ingestion->>Model: Create embeddings through adapter
    Ingestion->>DB: Store embeddings
    API->>Agent: Start persisted workflow
    Agent->>Model: Extract structured requirements
    Agent->>DB: Store requirements

    loop Each requirement
        Agent->>DB: Full-text and vector retrieval with ownership filters
        DB-->>Agent: Candidate evidence and source locations
        Agent->>Model: Assess requirement against retrieved evidence
        Agent->>Verifier: Validate label, claim and citations
        Verifier-->>Agent: Pass, retry, clarify or mark unsupported
    end

    Agent->>Model: Draft CV and structured change suggestions
    Agent->>Verifier: Check every factual claim against evidence
    Verifier-->>Agent: Verified draft or bounded correction request
    Agent-->>API: Pause for candidate review
    API-->>Web: SSE progress and review-ready event
    Candidate->>Web: Accept, edit or reject changes
    Web->>API: Submit review decisions
    API->>Agent: Resume persisted workflow
    Agent->>DB: Store approved CV version and audit decisions
    API-->>Web: Return final preview or export
```

## Retrieval design

The first implementation uses a measurable baseline before advanced retrieval:

1. Split candidate sources into provenance-preserving chunks.
2. Store raw text and metadata in PostgreSQL.
3. Start with exact vector search because each candidate corpus is small.
4. Add PostgreSQL full-text search for exact skills, names, and acronyms.
5. Fuse lexical and semantic results using rank-based fusion.
6. Apply strict `candidate_profile_id` ownership filters before ranking.
7. Add reranking only if the evaluation suite proves it improves retrieval.
8. Add HNSW only when corpus size or measured latency justifies approximate
   search.

This avoids claiming that vector similarity alone proves a requirement. The
agent receives evidence candidates; the verifier determines whether those
candidates actually support the claim.

## Trust boundaries and data flow

```mermaid
flowchart LR
    subgraph Untrusted["Untrusted zone"]
        UserInput["CVs, job descriptions,<br/>file names and user text"]
        ModelOutput["LLM and embedding<br/>provider output"]
    end

    subgraph Application["Application trust boundary"]
        Validation["File, size, type and<br/>schema validation"]
        Policy["Prompt-injection isolation,<br/>claim and tool policy"]
        AuthZ["Authentication and<br/>ownership authorization"]
        Services["Domain and application services"]
        Audit["Redacted structured audit events"]
    end

    subgraph Data["Protected data boundary"]
        DB[("PostgreSQL + pgvector")]
        Object[("Private object storage")]
        Secret[("Secret manager")]
    end

    UserInput --> Validation
    Validation --> Policy
    ModelOutput --> Policy
    Policy --> Services
    AuthZ --> Services
    Services --> DB
    Services --> Object
    Secret --> Services
    Services --> Audit
```

### Initial security controls

- Synthetic data only in public demos and committed fixtures.
- Strict file size, extension, MIME, and parser limits before persistence.
- Private object storage with short-lived signed access where required.
- Candidate ownership enforced in every repository query, not only the UI.
- Provider keys loaded from environment variables locally and a secret manager
  in cloud deployments.
- No secrets, CV contents, contact details, prompts, or model responses in
  normal application logs.
- Uploaded text is delimited and labelled as untrusted content in prompts.
- The model cannot construct or execute arbitrary MCP, database, shell, email,
  or browser actions.
- Rate limits and quotas protect public-demo resources.
- Deletion removes sources, derived chunks, embeddings, versions, and exports.

## Cloud deployment

```mermaid
flowchart TB
    Developer["Developer"] -->|"push"| GitHub["GitHub repository"]
    GitHub -->|"CI: lint, test, build and scan"| Actions["GitHub Actions"]
    Actions -->|"deploy reviewed image"| Registry["Artifact Registry"]

    Browser["Candidate browser"] -->|"HTTPS"| Static["Static web hosting<br/>Vite production assets"]
    Static -->|"HTTPS REST and SSE"| Run["Google Cloud Run<br/>FastAPI modular monolith"]

    Run --> Secret["Secret Manager"]
    Run --> DB["Managed PostgreSQL<br/>with pgvector"]
    Run --> Objects["Private object storage"]
    Run --> Models["Model and embedding providers"]
    Run --> Logs["Cloud Logging and Monitoring"]

    Scheduler["Cloud Scheduler / task queue<br/>only when async requirements arrive"] --> Worker["Cloud Run job or worker"]
    Worker --> DB
    Worker --> Objects
    Worker --> Models
```

The production backend remains stateless between requests. Durable domain and
workflow state lives in PostgreSQL. A worker is not deployed until document
processing or latency measurements show that request-bound execution is
insufficient.

## Preliminary physical ERD

This model is implementation-oriented but still subject to migrations and ADRs.
Many-to-many citation relationships are represented explicitly.

```mermaid
erDiagram
    users ||--o{ candidate_profiles : owns
    candidate_profiles ||--o{ source_documents : contains
    source_documents ||--o{ document_chunks : splits_into
    source_documents ||--o{ evidence_items : yields
    document_chunks ||--o{ evidence_items : locates

    users ||--o{ applications : creates
    candidate_profiles ||--o{ applications : used_by
    job_descriptions ||--o{ applications : targeted_by
    job_descriptions ||--|{ job_requirements : contains

    applications ||--|{ requirement_assessments : produces
    job_requirements ||--o{ requirement_assessments : evaluated_by
    requirement_assessments ||--o{ assessment_evidence : cites
    evidence_items ||--o{ assessment_evidence : supports

    applications ||--o{ clarifications : asks
    clarifications ||--o| evidence_items : may_create
    applications ||--o{ workflow_runs : executes
    applications ||--o{ cv_versions : produces
    cv_versions ||--o{ change_suggestions : contains
    change_suggestions ||--o{ suggestion_evidence : cites
    evidence_items ||--o{ suggestion_evidence : supports
    change_suggestions ||--o| change_decisions : receives
    users ||--o{ change_decisions : makes

    users {
        uuid id PK
        string external_subject UK
        string email
        timestamptz created_at
    }
    candidate_profiles {
        uuid id PK
        uuid user_id FK
        string display_name
        timestamptz created_at
        timestamptz deleted_at
    }
    source_documents {
        uuid id PK
        uuid profile_id FK
        string document_type
        string object_key
        string content_hash
        string processing_status
        timestamptz created_at
    }
    document_chunks {
        uuid id PK
        uuid document_id FK
        int chunk_index
        text content
        string source_location
        vector embedding
        tsvector search_vector
    }
    evidence_items {
        uuid id PK
        uuid document_id FK
        uuid chunk_id FK
        text evidence_text
        string evidence_type
        string verification_status
    }
    job_descriptions {
        uuid id PK
        text original_text
        string role_title
        string employer_name
        string content_hash
    }
    job_requirements {
        uuid id PK
        uuid job_description_id FK
        string category
        text requirement_text
        int source_start
        int source_end
    }
    applications {
        uuid id PK
        uuid user_id FK
        uuid profile_id FK
        uuid job_description_id FK
        string status
        timestamptz created_at
    }
    requirement_assessments {
        uuid id PK
        uuid application_id FK
        uuid requirement_id FK
        string support_level
        text explanation
        float confidence
    }
    assessment_evidence {
        uuid assessment_id PK,FK
        uuid evidence_id PK,FK
    }
    clarifications {
        uuid id PK
        uuid application_id FK
        string requirement_context
        text question
        text answer
        string status
    }
    workflow_runs {
        uuid id PK
        uuid application_id FK
        string thread_id UK
        string status
        int retry_count
    }
    cv_versions {
        uuid id PK
        uuid application_id FK
        int version_number
        string status
        text rendered_markdown
        timestamptz created_at
    }
    change_suggestions {
        uuid id PK
        uuid cv_version_id FK
        text original_text
        text suggested_text
        text reason
        float confidence
    }
    suggestion_evidence {
        uuid suggestion_id PK,FK
        uuid evidence_id PK,FK
    }
    change_decisions {
        uuid id PK
        uuid suggestion_id FK,UK
        uuid user_id FK
        string decision
        text edited_text
        timestamptz decided_at
    }
```

## Repository layout

```text
gradpath-ai/
├── apps/
│   ├── api/                 # FastAPI modular monolith
│   ├── web/                 # React + TypeScript + Vite
│   └── mcp-server/          # permission-controlled MCP adapter
├── docs/
│   ├── decisions/           # architecture decision records
│   └── architecture.md
├── infra/                   # Docker and cloud deployment definitions
├── tests/                   # cross-application and evaluation tests
├── .github/workflows/       # CI/CD
└── README.md
```

## Technology references

- [React versions](https://react.dev/versions)
- [Vite getting started](https://vite.dev/guide/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [Model Context Protocol introduction](https://modelcontextprotocol.io/docs/getting-started/intro)
- [PostgreSQL documentation](https://www.postgresql.org/docs/current/)
- [pgvector](https://github.com/pgvector/pgvector)
- [Cloud Run overview](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run)

