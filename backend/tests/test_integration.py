import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.schemas.release import ReleaseRequest

# This requires pytest-asyncio and httpx
@pytest.mark.asyncio
async def test_analyze_release_invalid_repo():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/releases/analyze", json={
            "repository": "invalid_repo_format", 
            "release": "v1.0"
        })
    
    # Should fail validation before hitting GitHub
    assert response.status_code == 400
    assert "Invalid repository format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_analyze_release_missing_fields():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/releases/analyze", json={
            "repository": "facebook/react"
            # Missing release
        })
    
    assert response.status_code == 422 # FastAPI standard validation error

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
        
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "ReleaseShield Git Agent API is running"}
