"""
Tests for health check endpoints
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test basic health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "databases" in data
    assert "global_kb" in data["databases"]
    assert "tenant" in data["databases"]


@pytest.mark.asyncio
async def test_liveness_check():
    """Test liveness probe"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert "version" in data
    assert data["message"] == "Salesbrain Backend API"
