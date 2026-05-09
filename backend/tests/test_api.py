"""
OmniSynth - API Integration Tests
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_agents_list():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/chat/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) > 0


@pytest.mark.asyncio
async def test_citation_styles():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/citations/styles")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "OmniSynth"
