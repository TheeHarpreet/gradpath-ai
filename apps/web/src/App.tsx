import { useMemo, useState } from "react";
import type { FormEvent } from "react";

import "./App.css";
import type { ChangeSuggestion, WorkflowResponse } from "./api";
import {
  deleteWorkflow,
  downloadExport,
  downloadMarkdown,
  extractFile,
  startWorkflow,
  submitClarifications,
  submitReview,
  setDemoAccessToken,
} from "./api";

type InputName = "candidate_cv" | "job_description" | "supporting_evidence";
type Decision = { action: "accept" | "edit" | "reject"; edited_text?: string };

const stageLabels = ["Evidence", "Analysis", "Review", "Export"];
const statusLabels = {
  supported: "Supported",
  partially_supported: "Partly supported",
  unsupported: "Gap",
  uncertain: "Needs clarification",
};

function App() {
  const [inputs, setInputs] = useState<Record<InputName, string>>({
    candidate_cv: "",
    job_description: "",
    supporting_evidence: "",
  });
  const [filenames, setFilenames] = useState<
    Partial<Record<InputName, string>>
  >({});
  const [workflow, setWorkflow] = useState<WorkflowResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [decisions, setDecisions] = useState<Record<string, Decision>>({});
  const [approvedCv, setApprovedCv] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [demoToken, setDemoToken] = useState("");

  const stage =
    workflow?.status === "completed"
      ? 4
      : workflow?.status === "awaiting_review"
        ? 3
        : workflow
          ? 2
          : 1;
  const counts = useMemo(() => {
    const requirements = workflow?.analysis?.requirements ?? [];
    return Object.fromEntries(
      Object.keys(statusLabels).map((status) => [
        status,
        requirements.filter((item) => item.status === status).length,
      ]),
    );
  }, [workflow]);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Something went wrong.",
      );
      document.querySelector<HTMLElement>("#error-summary")?.focus();
    } finally {
      setBusy(false);
    }
  }

  async function handleFile(name: InputName, file?: File) {
    if (!file) return;
    await run(async () => {
      const text = await extractFile(file);
      setInputs((current) => ({ ...current, [name]: text }));
      setFilenames((current) => ({ ...current, [name]: file.name }));
    });
  }

  function initialiseReview(next: WorkflowResponse) {
    setWorkflow(next);
    if (next.analysis) {
      setApprovedCv(next.analysis.aligned_cv_markdown);
      setDecisions(
        Object.fromEntries(
          next.analysis.changes.map((change) => [
            change.change_id,
            { action: "accept" },
          ]),
        ),
      );
    }
  }

  function analyse(event: FormEvent) {
    event.preventDefault();
    if (inputs.candidate_cv.length < 50 || inputs.job_description.length < 50) {
      setError(
        "Add at least 50 characters to both the CV and job description.",
      );
      return;
    }
    void run(async () => {
      const result = await startWorkflow({
        candidate_cv: inputs.candidate_cv,
        job_description: inputs.job_description,
        supporting_evidence: inputs.supporting_evidence || undefined,
      });
      initialiseReview(result);
    });
  }

  function clarify(event: FormEvent) {
    event.preventDefault();
    if (!workflow) return;
    void run(async () => {
      const result = await submitClarifications(
        workflow.workflow_id,
        workflow.clarification_questions.map((question) => ({
          requirement_id: question.requirement_id,
          answer: answers[question.requirement_id]?.trim() || null,
        })),
      );
      initialiseReview(result);
    });
  }

  function review(event: FormEvent) {
    event.preventDefault();
    if (!workflow?.analysis) return;
    const invalidEdit = Object.values(decisions).some(
      (decision) => decision.action === "edit" && !decision.edited_text?.trim(),
    );
    if (invalidEdit) {
      setError("Add replacement wording for every change marked Edit.");
      return;
    }
    void run(async () => {
      const result = await submitReview(
        workflow.workflow_id,
        workflow.analysis!.changes.map((change) => ({
          change_id: change.change_id,
          ...decisions[change.change_id],
        })),
        approvedCv,
      );
      setWorkflow(result);
    });
  }

  function resetLocal() {
    setInputs({
      candidate_cv: "",
      job_description: "",
      supporting_evidence: "",
    });
    setFilenames({});
    setWorkflow(null);
    setAnswers({});
    setDecisions({});
    setApprovedCv("");
    setError("");
  }

  function clearSession() {
    void run(async () => {
      if (workflow) await deleteWorkflow(workflow.workflow_id);
      resetLocal();
    });
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <header className="site-header">
        <a className="brand" href="/" aria-label="GradPath AI home">
          <span className="brand-mark" aria-hidden="true">
            GP
          </span>
          <span>GradPath AI</span>
        </a>
        <div className="header-controls">
          <span className="privacy-note">
            Private by design · You approve every change
          </span>
          <details className="access-control">
            <summary>Demo access</summary>
            <label htmlFor="demo-token">Access token</label>
            <input
              id="demo-token"
              type="password"
              value={demoToken}
              autoComplete="off"
              onChange={(event) => {
                setDemoToken(event.target.value);
                setDemoAccessToken(event.target.value);
              }}
            />
            <small>Kept in memory only; never saved by this page.</small>
          </details>
        </div>
      </header>

      <main id="main-content">
        <section className="product-intro">
          <div>
            <p className="eyebrow">Evidence-grounded CV alignment</p>
            <h1>Turn your real experience into a role-ready CV.</h1>
            <p className="lede">
              Compare your CV with a job description, inspect every evidence
              link, and decide what reaches the final document.
            </p>
          </div>
          <aside className="trust-card" aria-label="Important product boundary">
            <strong>No invented experience.</strong>
            <p>
              GradPath AI highlights honest gaps. It does not apply for jobs or
              make decisions for employers.
            </p>
          </aside>
        </section>

        <nav aria-label="Alignment progress" className="progress-nav">
          <ol>
            {stageLabels.map((label, index) => (
              <li key={label} className={stage >= index + 1 ? "active" : ""}>
                <span>{index + 1}</span>
                {label}
              </li>
            ))}
          </ol>
        </nav>

        {error && (
          <div
            id="error-summary"
            className="error-summary"
            role="alert"
            tabIndex={-1}
          >
            <strong>We could not continue.</strong>
            <span>{error}</span>
          </div>
        )}
        {busy && (
          <p className="working" role="status">
            Working securely… this can take a moment.
          </p>
        )}

        {workflow && workflow.privacy_redactions > 0 && (
          <div className="privacy-result" role="status">
            <strong>Privacy protection applied.</strong>
            <span>
              {workflow.privacy_redactions} direct contact identifier
              {workflow.privacy_redactions === 1 ? " was" : "s were"} replaced
              before AI processing. Add verified contact details back during
              final review if needed.
            </span>
          </div>
        )}

        {!workflow && (
          <EvidenceForm
            inputs={inputs}
            filenames={filenames}
            busy={busy}
            onText={(name, value) =>
              setInputs((current) => ({ ...current, [name]: value }))
            }
            onFile={handleFile}
            onSubmit={analyse}
          />
        )}

        {workflow?.status === "awaiting_clarification" && (
          <section className="workspace" aria-labelledby="clarification-title">
            <div className="section-copy">
              <p className="eyebrow">Your knowledge, not a guess</p>
              <h2 id="clarification-title">Clarify uncertain evidence</h2>
              <p>
                Leave an answer blank if you do not have evidence. The
                requirement will remain a visible gap.
              </p>
            </div>
            <form className="clarification-form" onSubmit={clarify}>
              {workflow.clarification_questions.map((question) => (
                <label key={question.requirement_id}>
                  {question.question}
                  <textarea
                    value={answers[question.requirement_id] ?? ""}
                    onChange={(event) =>
                      setAnswers((current) => ({
                        ...current,
                        [question.requirement_id]: event.target.value,
                      }))
                    }
                    rows={4}
                    maxLength={5000}
                  />
                  <small>
                    Optional · Use only facts you can explain in an interview.
                  </small>
                </label>
              ))}
              <button className="primary-button" disabled={busy}>
                Continue analysis
              </button>
            </form>
          </section>
        )}

        {workflow?.analysis && workflow.status === "awaiting_review" && (
          <AnalysisReview
            workflow={workflow}
            counts={counts}
            decisions={decisions}
            approvedCv={approvedCv}
            busy={busy}
            onDecision={(id, decision) =>
              setDecisions((current) => ({ ...current, [id]: decision }))
            }
            onCv={setApprovedCv}
            onSubmit={review}
          />
        )}

        {workflow?.status === "completed" && (
          <ExportPanel
            approvedCv={workflow.approved_cv_markdown ?? approvedCv}
            busy={busy}
            onDownload={(format) =>
              void run(async () =>
                format === "md"
                  ? downloadMarkdown(
                      workflow.approved_cv_markdown ?? approvedCv,
                    )
                  : downloadExport(
                      format,
                      workflow.approved_cv_markdown ?? approvedCv,
                    ),
              )
            }
            onClear={clearSession}
          />
        )}
      </main>
      <footer>
        <p>
          GradPath AI · Evidence before claims · Candidate approval before
          export
        </p>
      </footer>
    </div>
  );
}

function EvidenceForm({
  inputs,
  filenames,
  busy,
  onText,
  onFile,
  onSubmit,
}: {
  inputs: Record<InputName, string>;
  filenames: Partial<Record<InputName, string>>;
  busy: boolean;
  onText: (name: InputName, value: string) => void;
  onFile: (name: InputName, file?: File) => void;
  onSubmit: (event: FormEvent) => void;
}) {
  const fields: Array<{
    name: InputName;
    title: string;
    help: string;
    required: boolean;
  }> = [
    {
      name: "candidate_cv",
      title: "Your current CV",
      help: "Paste text or upload TXT, Markdown, DOCX, or a text-based PDF.",
      required: true,
    },
    {
      name: "job_description",
      title: "Job description",
      help: "Include responsibilities and essential/desirable requirements.",
      required: true,
    },
    {
      name: "supporting_evidence",
      title: "Extra evidence",
      help: "Optional projects, portfolio notes, achievements, or course details.",
      required: false,
    },
  ];
  return (
    <section className="workspace" aria-labelledby="evidence-title">
      <div className="section-copy">
        <p className="eyebrow">Step 1 of 4</p>
        <h2 id="evidence-title">Bring the evidence</h2>
        <p>
          Email addresses, phone numbers, and UK postcodes are replaced before
          AI processing. Still remove references and unnecessary sensitive
          details. Files are converted to text in memory.
        </p>
      </div>
      <form className="evidence-form" onSubmit={onSubmit}>
        {fields.map((field) => (
          <div className="input-card" key={field.name}>
            <div className="input-heading">
              <div>
                <label htmlFor={field.name}>
                  {field.title}
                  {field.required && <span aria-hidden="true"> *</span>}
                </label>
                <p>{field.help}</p>
              </div>
              <span>{inputs[field.name].length.toLocaleString()} / 50,000</span>
            </div>
            <input
              className="file-input"
              id={`${field.name}-file`}
              type="file"
              accept=".txt,.md,.docx,.pdf"
              onChange={(event) =>
                void onFile(field.name, event.target.files?.[0])
              }
            />
            <label className="file-button" htmlFor={`${field.name}-file`}>
              {filenames[field.name]
                ? `Loaded: ${filenames[field.name]}`
                : "Choose a file"}
            </label>
            <span className="or-divider">or paste below</span>
            <textarea
              id={field.name}
              required={field.required}
              minLength={field.required ? 50 : undefined}
              maxLength={50000}
              rows={field.name === "supporting_evidence" ? 5 : 10}
              value={inputs[field.name]}
              onChange={(event) => onText(field.name, event.target.value)}
            />
          </div>
        ))}
        <div className="submit-row">
          <p>
            <strong>You stay in control.</strong> Nothing is exported until you
            approve the full CV.
          </p>
          <button className="primary-button" disabled={busy}>
            Analyse my evidence <span aria-hidden="true">→</span>
          </button>
        </div>
      </form>
    </section>
  );
}

function AnalysisReview({
  workflow,
  counts,
  decisions,
  approvedCv,
  busy,
  onDecision,
  onCv,
  onSubmit,
}: {
  workflow: WorkflowResponse;
  counts: Record<string, number>;
  decisions: Record<string, Decision>;
  approvedCv: string;
  busy: boolean;
  onDecision: (id: string, decision: Decision) => void;
  onCv: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
}) {
  const analysis = workflow.analysis!;
  return (
    <form onSubmit={onSubmit}>
      <section className="workspace" aria-labelledby="analysis-title">
        <div className="section-copy">
          <p className="eyebrow">Step 2 of 4</p>
          <h2 id="analysis-title">See the evidence map</h2>
          <p>
            A supported label always links back to wording you supplied. A gap
            stays a gap.
          </p>
        </div>
        <div className="score-grid">
          {Object.entries(statusLabels).map(([key, label]) => (
            <div key={key} className={`score ${key}`}>
              <strong>{counts[key] ?? 0}</strong>
              <span>{label}</span>
            </div>
          ))}
        </div>
        <div className="requirement-list">
          {analysis.requirements.map((item) => (
            <article
              className="requirement-card"
              key={item.requirement.requirement_id}
            >
              <div className="card-meta">
                <span>{item.requirement.priority}</span>
                <span className={`status ${item.status}`}>
                  {statusLabels[item.status]}
                </span>
              </div>
              <h3>{item.requirement.source_text}</h3>
              <p>{item.rationale}</p>
              {item.citations.map((citation) => (
                <blockquote key={`${citation.source_id}-${citation.quote}`}>
                  “{citation.quote}”
                  <cite>
                    {citation.source_kind === "candidate_cv"
                      ? "Your CV"
                      : "Supporting evidence"}
                  </cite>
                </blockquote>
              ))}
            </article>
          ))}
        </div>
      </section>
      <section
        className="workspace review-section"
        aria-labelledby="review-title"
      >
        <div className="section-copy">
          <p className="eyebrow">Step 3 of 4</p>
          <h2 id="review-title">Decide every change</h2>
          <p>
            Accept the suggestion, edit its wording, or reject it. These
            controls record your decision; the full CV remains editable below.
          </p>
        </div>
        {analysis.unsupported_claim_warnings.length > 0 && (
          <div className="warning-box">
            <strong>Claims to avoid</strong>
            <ul>
              {analysis.unsupported_claim_warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="change-list">
          {analysis.changes.map((change) => (
            <ChangeCard
              key={change.change_id}
              change={change}
              decision={decisions[change.change_id] ?? { action: "accept" }}
              onChange={(decision) => onDecision(change.change_id, decision)}
            />
          ))}
        </div>
        <div className="final-editor">
          <label htmlFor="approved-cv">Final CV — exact text to approve</label>
          <p>
            Check names, dates, qualifications, technologies, and every claim.
            Edit anything that is not accurate.
          </p>
          <textarea
            id="approved-cv"
            value={approvedCv}
            onChange={(event) => onCv(event.target.value)}
            minLength={1}
            maxLength={100000}
            rows={24}
            required
          />
        </div>
        <div className="approval-box">
          <label>
            <input type="checkbox" required /> I have checked this CV and
            approve this exact text for export.
          </label>
          <button className="primary-button" disabled={busy}>
            Approve final CV
          </button>
        </div>
      </section>
    </form>
  );
}

function ChangeCard({
  change,
  decision,
  onChange,
}: {
  change: ChangeSuggestion;
  decision: Decision;
  onChange: (decision: Decision) => void;
}) {
  return (
    <article className="change-card">
      <div className="card-meta">
        <span>{change.target}</span>
        <span>{Math.round(change.confidence * 100)}% confidence</span>
      </div>
      <h3>
        {change.decision.charAt(0).toUpperCase() + change.decision.slice(1)}{" "}
        suggestion
      </h3>
      {change.suggested_text && (
        <p className="suggested-text">{change.suggested_text}</p>
      )}
      <p>{change.reason}</p>
      <fieldset>
        <legend>Your decision</legend>
        {(["accept", "edit", "reject"] as const).map((action) => (
          <label key={action}>
            <input
              type="radio"
              name={change.change_id}
              value={action}
              checked={decision.action === action}
              onChange={() =>
                onChange({
                  action,
                  edited_text:
                    action === "edit"
                      ? (change.suggested_text ?? "")
                      : undefined,
                })
              }
            />{" "}
            {action.charAt(0).toUpperCase() + action.slice(1)}
          </label>
        ))}
      </fieldset>
      {decision.action === "edit" && (
        <label className="edit-label">
          Your replacement wording
          <textarea
            rows={4}
            required
            value={decision.edited_text ?? ""}
            onChange={(event) =>
              onChange({ action: "edit", edited_text: event.target.value })
            }
          />
        </label>
      )}
    </article>
  );
}

function ExportPanel({
  approvedCv,
  busy,
  onDownload,
  onClear,
}: {
  approvedCv: string;
  busy: boolean;
  onDownload: (format: "md" | "docx" | "pdf") => void;
  onClear: () => void;
}) {
  return (
    <section className="workspace export-panel" aria-labelledby="export-title">
      <div className="completion-mark" aria-hidden="true">
        ✓
      </div>
      <p className="eyebrow">Step 4 of 4 · Complete</p>
      <h2 id="export-title">Your approved CV is ready.</h2>
      <p>
        The content is identical in every format. DOCX is editable; PDF
        preserves layout; Markdown keeps a portable source copy.
      </p>
      <div className="download-grid">
        <button
          type="button"
          onClick={() => onDownload("docx")}
          disabled={busy}
        >
          <strong>DOCX</strong>
          <span>Edit in Word or Google Docs</span>
        </button>
        <button type="button" onClick={() => onDownload("pdf")} disabled={busy}>
          <strong>PDF</strong>
          <span>Review the fixed application layout</span>
        </button>
        <button type="button" onClick={() => onDownload("md")} disabled={busy}>
          <strong>Markdown</strong>
          <span>Keep the exact source text</span>
        </button>
      </div>
      <details>
        <summary>Preview approved text</summary>
        <pre>{approvedCv}</pre>
      </details>
      <div className="delete-panel">
        <div>
          <strong>Finished with this session?</strong>
          <p>Delete the active workflow and clear all text from this page.</p>
        </div>
        <button
          className="danger-button"
          type="button"
          onClick={onClear}
          disabled={busy}
        >
          Delete my session
        </button>
      </div>
    </section>
  );
}

export default App;
