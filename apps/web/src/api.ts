export type CoverageStatus =
  "supported" | "partially_supported" | "unsupported" | "uncertain";

export interface Citation {
  source_id: string;
  source_kind: "candidate_cv" | "supporting_evidence";
  quote: string;
}

export interface RequirementAssessment {
  requirement: {
    requirement_id: string;
    priority: "essential" | "desirable" | "unclear";
    source_text: string;
  };
  status: CoverageStatus;
  rationale: string;
  citations: Citation[];
  clarification_question?: string | null;
}

export interface ChangeSuggestion {
  change_id: string;
  target: string;
  decision: string;
  original_text?: string | null;
  suggested_text?: string | null;
  reason: string;
  citations: Citation[];
  confidence: number;
}

export interface WorkflowResponse {
  workflow_id: string;
  status:
    | "running"
    | "awaiting_clarification"
    | "awaiting_review"
    | "completed"
    | "failed";
  clarification_questions: Array<{ requirement_id: string; question: string }>;
  analysis: {
    requirements: RequirementAssessment[];
    strengths: string[];
    gaps: string[];
    changes: ChangeSuggestion[];
    unsupported_claim_warnings: string[];
    aligned_cv_markdown: string;
  } | null;
  approved_cv_markdown: string | null;
}

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(
      body?.detail ?? "GradPath AI could not complete the request.",
    );
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function extractFile(file: File): Promise<string> {
  if (/\.(txt|md)$/i.test(file.name)) return file.text();
  const form = new FormData();
  form.append("file", file);
  const result = await request<{ text: string }>("/documents/extract", {
    method: "POST",
    body: form,
  });
  return result.text;
}

export function startWorkflow(payload: {
  candidate_cv: string;
  job_description: string;
  supporting_evidence?: string;
}) {
  return request<WorkflowResponse>("/workflows", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function submitClarifications(
  workflowId: string,
  answers: Array<{ requirement_id: string; answer: string | null }>,
) {
  return request<WorkflowResponse>(`/workflows/${workflowId}/clarifications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });
}

export function submitReview(
  workflowId: string,
  decisions: Array<{
    change_id: string;
    action: "accept" | "edit" | "reject";
    edited_text?: string;
  }>,
  approvedCvMarkdown: string,
) {
  return request<WorkflowResponse>(`/workflows/${workflowId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      decisions,
      approved_cv_markdown: approvedCvMarkdown,
    }),
  });
}

export function deleteWorkflow(workflowId: string) {
  return request<void>(`/workflows/${workflowId}`, { method: "DELETE" });
}

export async function downloadExport(
  format: "docx" | "pdf",
  approvedCvMarkdown: string,
) {
  const response = await fetch(`${API_BASE}/documents/export/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      approved_cv_markdown: approvedCvMarkdown,
      filename: "gradpath-aligned-cv",
    }),
  });
  if (!response.ok)
    throw new Error(`The ${format.toUpperCase()} export failed.`);
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `gradpath-aligned-cv.${format}`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function downloadMarkdown(markdown: string) {
  const url = URL.createObjectURL(
    new Blob([markdown], { type: "text/markdown" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "gradpath-aligned-cv.md";
  anchor.click();
  URL.revokeObjectURL(url);
}
