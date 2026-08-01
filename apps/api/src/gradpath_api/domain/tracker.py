"""Domain contracts and transitions for the job-application tracker."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import Field

from gradpath_api.domain.analysis import ContractModel


class ApplicationStage(StrEnum):
    """Candidate-controlled stages in the initial tracker lifecycle."""

    SAVED = "saved"
    PREPARING = "preparing"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class TrackedApplication(ContractModel):
    """A minimal job application record without CV or contact data."""

    application_id: str = Field(pattern=r"^application-[a-z0-9-]+$")
    candidate_profile_id: str = Field(pattern=r"^profile-[a-z0-9-]+$")
    employer_name: str = Field(min_length=1, max_length=200)
    role_title: str = Field(min_length=1, max_length=200)
    vacancy_reference: str | None = Field(default=None, max_length=200)
    stage: ApplicationStage
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


_ALLOWED_TRANSITIONS: dict[ApplicationStage, set[ApplicationStage]] = {
    ApplicationStage.SAVED: {
        ApplicationStage.PREPARING,
        ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.PREPARING: {
        ApplicationStage.APPLIED,
        ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.APPLIED: {
        ApplicationStage.INTERVIEW,
        ApplicationStage.REJECTED,
        ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.INTERVIEW: {
        ApplicationStage.OFFER,
        ApplicationStage.REJECTED,
        ApplicationStage.WITHDRAWN,
    },
    ApplicationStage.OFFER: {ApplicationStage.WITHDRAWN},
    ApplicationStage.REJECTED: set(),
    ApplicationStage.WITHDRAWN: set(),
}


def can_transition(current: ApplicationStage, target: ApplicationStage) -> bool:
    """Return whether a stage update is idempotent or follows the lifecycle."""

    return current is target or target in _ALLOWED_TRANSITIONS[current]
