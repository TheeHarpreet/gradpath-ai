"""Deterministic privacy and prompt-injection controls for untrusted text."""

from __future__ import annotations

import re
from dataclasses import dataclass

from gradpath_api.domain.analysis import AnalysisRequest

_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.IGNORECASE)
_PHONE = re.compile(
    r"(?<!\w)(?:\+44\s?\d{4}|0\d{4}|\+44\s?\d{3}|0\d{3})"
    r"(?:[\s()-]?\d){6,8}(?!\w)"
)
_UK_POSTCODE = re.compile(
    r"\b(?:GIR\s?0AA|[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})\b",
    re.IGNORECASE,
)
_INJECTION_PATTERNS = (
    re.compile(
        r"\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?\b", re.I
    ),
    re.compile(r"\bignore\s+all\s+(?:system\s+)?(?:rules|instructions)\b", re.I),
    re.compile(r"\b(?:reveal|print|show|return)\s+(?:the\s+)?system\s+prompt\b", re.I),
    re.compile(r"\byou\s+are\s+now\s+(?:a|an|the)\b", re.I),
    re.compile(r"\b(?:developer|system)\s+message\s*:", re.I),
    re.compile(r"\bdisregard\s+(?:the\s+)?(?:rules|instructions|prompt)\b", re.I),
)


class UnsafeInputError(ValueError):
    """Input contains an instruction-like payload unsafe for model processing."""


@dataclass(frozen=True)
class RedactionSummary:
    """Counts only; never includes detected personal values."""

    emails: int = 0
    phone_numbers: int = 0
    uk_postcodes: int = 0

    @property
    def total(self) -> int:
        return self.emails + self.phone_numbers + self.uk_postcodes


def detect_prompt_injection(text: str) -> bool:
    """Detect high-confidence instruction-override phrases in document data."""

    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


def redact_personal_data(text: str) -> tuple[str, RedactionSummary]:
    """Replace direct contact identifiers before text reaches model services."""

    email_count = len(_EMAIL.findall(text))
    phone_count = len(_PHONE.findall(text))
    postcode_count = len(_UK_POSTCODE.findall(text))
    redacted = _EMAIL.sub("[EMAIL REDACTED]", text)
    redacted = _PHONE.sub("[PHONE REDACTED]", redacted)
    redacted = _UK_POSTCODE.sub("[POSTCODE REDACTED]", redacted)
    return redacted, RedactionSummary(email_count, phone_count, postcode_count)


def secure_analysis_request(
    request: AnalysisRequest,
) -> tuple[AnalysisRequest, RedactionSummary]:
    """Reject malicious instructions and redact identifiers from model inputs."""

    fields = [request.candidate_cv, request.job_description]
    if request.supporting_evidence:
        fields.append(request.supporting_evidence)
    if any(detect_prompt_injection(value) for value in fields):
        raise UnsafeInputError(
            "Instruction-like content was detected in an uploaded document. "
            "Remove embedded AI instructions and try again."
        )

    cv, cv_summary = redact_personal_data(request.candidate_cv)
    job, job_summary = redact_personal_data(request.job_description)
    evidence, evidence_summary = redact_personal_data(request.supporting_evidence or "")
    summary = RedactionSummary(
        emails=cv_summary.emails + job_summary.emails + evidence_summary.emails,
        phone_numbers=(
            cv_summary.phone_numbers
            + job_summary.phone_numbers
            + evidence_summary.phone_numbers
        ),
        uk_postcodes=(
            cv_summary.uk_postcodes
            + job_summary.uk_postcodes
            + evidence_summary.uk_postcodes
        ),
    )
    return (
        request.model_copy(
            update={
                "candidate_cv": cv,
                "job_description": job,
                "supporting_evidence": evidence or None,
            }
        ),
        summary,
    )
