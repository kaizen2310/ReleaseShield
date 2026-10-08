import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.github.client import github_client

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# Add more mocked tests later
