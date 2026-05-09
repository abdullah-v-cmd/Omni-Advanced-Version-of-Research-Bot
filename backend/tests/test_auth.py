"""
OmniSynth - Authentication Tests
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_register():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "Test@1234",
            "full_name": "Test User"
        })
        assert response.status_code in [201, 400]


@pytest.mark.asyncio
async def test_login_invalid():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "OmniSynth"


@pytest.mark.asyncio
async def test_protected_without_token():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403
