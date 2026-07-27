"""Deterministic extraction of explicitly listed vacancy requirements."""

from __future__ import annotations

import re

from gradpath_api.domain.analysis import JobRequirement, RequirementPriority

_LIST_ITEM = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+(?P<text>.+?)\s*$")


class RequirementExtractionError(ValueError):
    """Raised when no explicit vacancy requirements can be extracted."""


def extract_requirements(job_description: str) -> list[JobRequirement]:
    """Extract listed requirements and classify them from nearby headings."""

    priority = RequirementPriority.UNCLEAR
    extracted: list[JobRequirement] = []

    for line in job_description.splitlines():
        normalized = line.strip().lower().lstrip("#").strip()
        if "essential" in normalized and "requirement" in normalized:
            priority = RequirementPriority.ESSENTIAL
            continue
        if "desirable" in normalized and "requirement" in normalized:
            priority = RequirementPriority.DESIRABLE
            continue
        if "requirement" in normalized and normalized.startswith("unclear"):
            priority = RequirementPriority.UNCLEAR
            continue

        match = _LIST_ITEM.match(line)
        if not match:
            continue
        source_text = match.group("text").strip()
        extracted.append(
            JobRequirement(
                requirement_id=f"req-{len(extracted) + 1:03d}",
                priority=priority,
                source_text=source_text,
            )
        )

    if not extracted:
        raise RequirementExtractionError(
            "No numbered or bulleted job requirements were found."
        )
    return extracted
