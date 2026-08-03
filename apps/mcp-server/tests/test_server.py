"""MCP protocol and permission-boundary tests."""

import json

import pytest
from gradpath_api.application.tracker_service import (
    ApplicationTrackerService,
    ApprovalBroker,
    InMemoryTrackerRepository,
)
from gradpath_api.domain.tracker import ApplicationStage
from gradpath_mcp import DEFAULT_PROFILE_ID, create_server, fictional_applications


def _server() -> tuple[object, ApprovalBroker]:
    approvals = ApprovalBroker()
    service = ApplicationTrackerService(
        repository=InMemoryTrackerRepository(fictional_applications()),
        approvals=approvals,
    )
    return (
        create_server(
            service=service,
            approvals=approvals,
            candidate_profile_id=DEFAULT_PROFILE_ID,
        ),
        approvals,
    )


def test_server_has_expected_name() -> None:
    server, _ = _server()

    assert server.name == "GradPath AI"


@pytest.mark.asyncio
async def test_tools_are_narrow_and_accurately_annotated() -> None:
    server, _ = _server()

    tools = {tool.name: tool for tool in await server.list_tools()}

    assert set(tools) == {
        "list_job_applications",
        "get_job_application",
        "update_job_application_stage",
    }
    assert tools["list_job_applications"].annotations.readOnlyHint is True
    assert tools["get_job_application"].annotations.readOnlyHint is True
    update = tools["update_job_application_stage"].annotations
    assert update.readOnlyHint is False
    assert update.openWorldHint is False


@pytest.mark.asyncio
async def test_list_tool_enforces_candidate_ownership() -> None:
    server, _ = _server()

    _, structured = await server.call_tool("list_job_applications", {})

    assert structured["count"] == 2
    assert {item["candidate_profile_id"] for item in structured["applications"]} == {
        DEFAULT_PROFILE_ID
    }
    assert "application-private-003" not in {
        item["application_id"] for item in structured["applications"]
    }


@pytest.mark.asyncio
async def test_update_tool_requires_exact_single_use_approval() -> None:
    server, approvals = _server()
    token = approvals.approve_stage_update(
        candidate_profile_id=DEFAULT_PROFILE_ID,
        application_id="application-northstar-001",
        current_stage=ApplicationStage.PREPARING,
        target_stage=ApplicationStage.APPLIED,
    )

    _, structured = await server.call_tool(
        "update_job_application_stage",
        {
            "application_id": "application-northstar-001",
            "target_stage": "applied",
            "approval_token": token,
        },
    )

    assert structured["application"]["stage"] == "applied"
    assert structured["audit_event"] == "application_stage_updated"

    with pytest.raises(Exception, match="valid matching approval"):
        await server.call_tool(
            "update_job_application_stage",
            {
                "application_id": "application-northstar-001",
                "target_stage": "applied",
                "approval_token": token,
            },
        )


@pytest.mark.asyncio
async def test_summary_resource_contains_only_safe_aggregates() -> None:
    server, _ = _server()

    result = await server.read_resource("gradpath://applications")
    payload = json.loads(next(iter(result)).content)

    assert payload["total"] == 2
    assert payload["stage_counts"]["preparing"] == 1
    assert payload["stage_counts"]["applied"] == 1
    assert "employer_name" not in payload
