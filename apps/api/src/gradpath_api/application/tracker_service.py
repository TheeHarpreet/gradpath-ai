"""Candidate-scoped tracker service with out-of-band write approvals."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Protocol

from gradpath_api.domain.tracker import (
    ApplicationStage,
    TrackedApplication,
    can_transition,
)


class TrackerError(RuntimeError):
    """Base error safe for translation at HTTP or MCP boundaries."""


class ApplicationNotFoundError(TrackerError):
    """No application exists in the caller's ownership scope."""


class InvalidStageTransitionError(TrackerError):
    """The requested lifecycle transition is not permitted."""


class ApprovalRequiredError(TrackerError):
    """A mutation lacks a valid, matching, single-use approval."""


class TrackerRepository(Protocol):
    """Storage operations that always include candidate ownership."""

    async def list_for_candidate(
        self,
        candidate_profile_id: str,
    ) -> list[TrackedApplication]:
        """Return only records owned by one candidate profile."""
        ...

    async def get_for_candidate(
        self,
        candidate_profile_id: str,
        application_id: str,
    ) -> TrackedApplication:
        """Load an owned record without revealing cross-profile existence."""
        ...

    async def save(self, application: TrackedApplication) -> None:
        """Persist a complete application record."""
        ...


class InMemoryTrackerRepository:
    """Deterministic development repository used by local MCP and tests."""

    def __init__(self, applications: list[TrackedApplication] | None = None) -> None:
        self._applications = {
            item.application_id: deepcopy(item) for item in applications or []
        }

    async def list_for_candidate(
        self,
        candidate_profile_id: str,
    ) -> list[TrackedApplication]:
        return sorted(
            [
                deepcopy(item)
                for item in self._applications.values()
                if item.candidate_profile_id == candidate_profile_id
            ],
            key=lambda item: (item.updated_at, item.application_id),
            reverse=True,
        )

    async def get_for_candidate(
        self,
        candidate_profile_id: str,
        application_id: str,
    ) -> TrackedApplication:
        item = self._applications.get(application_id)
        if item is None or item.candidate_profile_id != candidate_profile_id:
            raise ApplicationNotFoundError("Application was not found.")
        return deepcopy(item)

    async def save(self, application: TrackedApplication) -> None:
        self._applications[application.application_id] = deepcopy(application)


@dataclass(frozen=True)
class PendingApproval:
    """A write approval bound to one user, record, transition, and expiry."""

    token: str
    candidate_profile_id: str
    application_id: str
    current_stage: ApplicationStage
    target_stage: ApplicationStage
    expires_at: datetime


class ApprovalBroker:
    """Create out-of-band tokens and consume them exactly once."""

    def __init__(self, *, ttl: timedelta = timedelta(minutes=10)) -> None:
        self._ttl = ttl
        self._pending: dict[str, PendingApproval] = {}

    def approve_stage_update(
        self,
        *,
        candidate_profile_id: str,
        application_id: str,
        current_stage: ApplicationStage,
        target_stage: ApplicationStage,
    ) -> str:
        """Represent a human approval that occurs outside the model tool loop."""

        token = token_urlsafe(32)
        self.register_stage_update_approval(
            token=token,
            candidate_profile_id=candidate_profile_id,
            application_id=application_id,
            current_stage=current_stage,
            target_stage=target_stage,
        )
        return token

    def register_stage_update_approval(
        self,
        *,
        token: str,
        candidate_profile_id: str,
        application_id: str,
        current_stage: ApplicationStage,
        target_stage: ApplicationStage,
    ) -> None:
        """Register a token minted by a trusted application approval surface."""

        if len(token) < 32:
            raise ValueError("approval tokens must contain at least 32 characters")
        self._pending[token] = PendingApproval(
            token=token,
            candidate_profile_id=candidate_profile_id,
            application_id=application_id,
            current_stage=current_stage,
            target_stage=target_stage,
            expires_at=datetime.now(UTC) + self._ttl,
        )

    def consume(
        self,
        *,
        token: str,
        candidate_profile_id: str,
        application_id: str,
        current_stage: ApplicationStage,
        target_stage: ApplicationStage,
    ) -> None:
        """Validate the complete approval binding and invalidate the token."""

        approval = self._pending.pop(token, None)
        expected = (
            candidate_profile_id,
            application_id,
            current_stage,
            target_stage,
        )
        received = (
            (
                approval.candidate_profile_id,
                approval.application_id,
                approval.current_stage,
                approval.target_stage,
            )
            if approval
            else None
        )
        if (
            approval is None
            or approval.expires_at <= datetime.now(UTC)
            or received != expected
        ):
            raise ApprovalRequiredError("A valid matching approval is required.")


class ApplicationTrackerService:
    """Enforce candidate ownership, transitions, and approval-gated writes."""

    def __init__(
        self,
        *,
        repository: TrackerRepository,
        approvals: ApprovalBroker,
    ) -> None:
        self._repository = repository
        self._approvals = approvals

    async def list_applications(
        self,
        *,
        candidate_profile_id: str,
        stage: ApplicationStage | None = None,
    ) -> list[TrackedApplication]:
        applications = await self._repository.list_for_candidate(candidate_profile_id)
        if stage is None:
            return applications
        return [item for item in applications if item.stage is stage]

    async def get_application(
        self,
        *,
        candidate_profile_id: str,
        application_id: str,
    ) -> TrackedApplication:
        return await self._repository.get_for_candidate(
            candidate_profile_id,
            application_id,
        )

    async def update_stage(
        self,
        *,
        candidate_profile_id: str,
        application_id: str,
        target_stage: ApplicationStage,
        approval_token: str,
    ) -> TrackedApplication:
        application = await self.get_application(
            candidate_profile_id=candidate_profile_id,
            application_id=application_id,
        )
        if not can_transition(application.stage, target_stage):
            raise InvalidStageTransitionError(
                f"Cannot move from {application.stage} to {target_stage}."
            )
        self._approvals.consume(
            token=approval_token,
            candidate_profile_id=candidate_profile_id,
            application_id=application_id,
            current_stage=application.stage,
            target_stage=target_stage,
        )
        updated = application.model_copy(
            update={"stage": target_stage, "updated_at": datetime.now(UTC)}
        )
        await self._repository.save(updated)
        return updated
