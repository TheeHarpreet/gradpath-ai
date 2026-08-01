"""Persistence boundary for resumable workflow snapshots."""

from __future__ import annotations

from copy import deepcopy
from typing import Protocol

from gradpath_api.domain.workflow import WorkflowState


class WorkflowNotFoundError(LookupError):
    """A requested workflow identifier does not exist."""


class WorkflowRepository(Protocol):
    """Storage contract independent of the eventual PostgreSQL adapter."""

    async def get(self, workflow_id: str) -> WorkflowState:
        """Load one workflow snapshot or raise WorkflowNotFoundError."""
        ...

    async def save(self, state: WorkflowState) -> None:
        """Persist a complete workflow snapshot."""
        ...


class InMemoryWorkflowRepository:
    """Process-local development adapter; not suitable for production."""

    def __init__(self) -> None:
        self._states: dict[str, WorkflowState] = {}

    async def get(self, workflow_id: str) -> WorkflowState:
        try:
            return deepcopy(self._states[workflow_id])
        except KeyError as exc:
            raise WorkflowNotFoundError(workflow_id) from exc

    async def save(self, state: WorkflowState) -> None:
        self._states[state.workflow_id] = deepcopy(state)
