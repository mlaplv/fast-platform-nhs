import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_health_check_endpoint():
    """
    R71 Test Mandate: Verify the core backend API health endpoint is accessible and returns 200 OK.
    This guarantees the Uvicorn application can assemble successfully.
    """
    # Use ASGITransport for Litestar app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "online"
