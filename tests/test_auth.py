"""
Tests for authentication endpoints
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_login_success():
    """Test successful login with valid credentials"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "email": "admin@test.com",
                "password": "password123"
            }
        )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data
    assert "organization_id" in data
    assert "role" in data
    assert data["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_login_invalid_email():
    """Test login with non-existent email"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "password123"
            }
        )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_login_invalid_password():
    """Test login with wrong password"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "email": "admin@test.com",
                "password": "wrongpassword"
            }
        )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_current_user():
    """Test getting current user info with valid token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First login to get token
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "admin@test.com",
                "password": "password123"
            }
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Get current user info
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    data = response.json()

    assert "user_id" in data
    assert "organization_id" in data
    assert "role" in data
    assert data["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_get_current_user_no_token():
    """Test accessing protected endpoint without token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/auth/me")

    assert response.status_code == 403  # Forbidden without token


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test accessing protected endpoint with invalid token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_logout():
    """Test logout endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/auth/logout")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
