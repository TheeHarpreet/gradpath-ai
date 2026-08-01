"""Domain-level tests for ownership, transitions, and approval binding."""

from datetime import timedelta

import pytest
from gradpath_api.application.tracker_service import (
    ApplicationNotFoundError,
    ApplicationTrackerService,
    ApprovalBroker,
    ApprovalRequiredError,
    InMemoryTrackerRepository,
    InvalidStageTransitionError,
)
from gradpath_api.domain.tracker import ApplicationStage
from gradpath_mcp import DEFAULT_PROFILE_ID, fictional_applications


def _service(
    *,
    approvals: ApprovalBroker | None = None,
) -> tuple[ApplicationTrackerService, ApprovalBroker]:
    broker = approvals or ApprovalBroker()
    return (
        ApplicationTrackerService(
            repository=InMemoryTrackerRepository(fictional_applications()),
            approvals=broker,
        ),
        broker,
    )


@pytest.mark.asyncio
async def test_cross_profile_lookup_is_indistinguishable_from_missing() -> None:
    service, _ = _service()

    with pytest.raises(ApplicationNotFoundError, match="not found"):
        await service.get_application(
            candidate_profile_id=DEFAULT_PROFILE_ID,
            application_id="application-private-003",
        )


@pytest.mark.asyncio
async def test_invalid_backwards_transition_is_rejected() -> None:
    service, _ = _service()

    with pytest.raises(InvalidStageTransitionError, match="Cannot move"):
        await service.update_stage(
            candidate_profile_id=DEFAULT_PROFILE_ID,
            application_id="application-riverbank-002",
            target_stage=ApplicationStage.SAVED,
            approval_token="not-a-valid-approval-token-value",
        )


@pytest.mark.asyncio
async def test_approval_is_bound_to_the_exact_transition() -> None:
    service, approvals = _service()
    token = approvals.approve_stage_update(
        candidate_profile_id=DEFAULT_PROFILE_ID,
        application_id="application-northstar-001",
        current_stage=ApplicationStage.PREPARING,
        target_stage=ApplicationStage.APPLIED,
    )

    with pytest.raises(ApprovalRequiredError, match="valid matching approval"):
        await service.update_stage(
            candidate_profile_id=DEFAULT_PROFILE_ID,
            application_id="application-northstar-001",
            target_stage=ApplicationStage.WITHDRAWN,
            approval_token=token,
        )


@pytest.mark.asyncio
async def test_expired_approval_cannot_mutate_state() -> None:
    expired = ApprovalBroker(ttl=timedelta(seconds=-1))
    service, approvals = _service(approvals=expired)
    token = approvals.approve_stage_update(
        candidate_profile_id=DEFAULT_PROFILE_ID,
        application_id="application-northstar-001",
        current_stage=ApplicationStage.PREPARING,
        target_stage=ApplicationStage.APPLIED,
    )

    with pytest.raises(ApprovalRequiredError, match="valid matching approval"):
        await service.update_stage(
            candidate_profile_id=DEFAULT_PROFILE_ID,
            application_id="application-northstar-001",
            target_stage=ApplicationStage.APPLIED,
            approval_token=token,
        )
