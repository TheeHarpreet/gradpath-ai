"""Operational API contract tests."""

import pytest
from gradpath_api.core.config import Settings
from gradpath_api.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_liveness_endpoint() -> None:
    transport = ASGITransport(app=create_app(Settings(environment="test")))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness_endpoint() -> None:
    transport = ASGITransport(app=create_app(Settings(environment="test")))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_meta_endpoint_exposes_no_secrets() -> None:
    transport = ASGITransport(app=create_app(Settings(environment="test")))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/meta")

    assert response.status_code == 200
    assert response.json() == {
        "name": "GradPath AI API",
        "version": "0.1.0",
        "environment": "test",
    }
