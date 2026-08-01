"""Exercise read and approval-gated write tools through an Agents SDK MCP run."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import sys

from agents import Agent, ModelSettings, OpenAIProvider, RunConfig, Runner
from agents.mcp import MCPServerStdio
from gradpath_api.core.config import Settings
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict


class TrackerSmokeResult(BaseModel):
    """Stable output contract for the synthetic integration smoke test."""

    model_config = ConfigDict(extra="forbid")

    listed_count: int
    updated_application_id: str
    final_stage: str


async def run() -> None:
    """Run one model-driven read/update cycle with explicit app approval."""

    settings = Settings()
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    approval_token = secrets.token_urlsafe(32)
    child_env = {
        "GRADPATH_MCP_CANDIDATE_PROFILE_ID": "profile-demo-001",
        "GRADPATH_MCP_APPROVAL_TOKEN": approval_token,
        "GRADPATH_MCP_APPROVAL_APPLICATION_ID": "application-northstar-001",
        "GRADPATH_MCP_APPROVAL_CURRENT_STAGE": "preparing",
        "GRADPATH_MCP_APPROVAL_TARGET_STAGE": "applied",
        "PYTHONIOENCODING": "utf-8",
    }
    for name in ("PATH", "SYSTEMROOT", "WINDIR"):
        value = os.getenv(name)
        if value:
            child_env[name] = value

    async with MCPServerStdio(
        name="GradPath application tracker",
        params={
            "command": sys.executable,
            "args": ["-c", "from gradpath_mcp import main; main()"],
            "env": child_env,
        },
        cache_tools_list=True,
        use_structured_content=True,
        require_approval={"update_job_application_stage": "always"},
    ) as server:
        agent: Agent[None] = Agent(
            name="GradPath tracker specialist",
            instructions=(
                "Use only the GradPath MCP tools. First list the authenticated "
                "candidate's applications. Then update application-northstar-001 "
                "from preparing to applied with the approval token supplied by "
                "the user. Never invent records, tokens, or employer actions."
            ),
            model=settings.openai_model,
            model_settings=ModelSettings(
                reasoning={"effort": "low"},
                store=False,
            ),
            mcp_servers=[server],
            output_type=TrackerSmokeResult,
        )
        run_config = RunConfig(
            model_provider=OpenAIProvider(
                openai_client=AsyncOpenAI(
                    api_key=settings.openai_api_key.get_secret_value()
                )
            ),
            tracing_disabled=True,
            trace_include_sensitive_data=False,
            workflow_name="GradPath MCP integration smoke",
        )
        result = await Runner.run(
            agent,
            (
                "Use this one-time approval token for the exact requested update: "
                f"{approval_token}"
            ),
            run_config=run_config,
            max_turns=8,
        )
        interruption_count = len(result.interruptions)
        if interruption_count != 1:
            raise RuntimeError("Expected exactly one write approval interruption.")
        state = result.to_state()
        for interruption in result.interruptions:
            state.approve(interruption)
        completed = await Runner.run(
            agent,
            state,
            run_config=run_config,
            max_turns=8,
        )
        output = completed.final_output
        if not isinstance(output, TrackerSmokeResult):
            raise RuntimeError("Agent returned no structured tracker result.")

    print(
        json.dumps(
            {
                **output.model_dump(),
                "approval_interruptions": interruption_count,
                "approval_token_recorded": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(run())
