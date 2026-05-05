import pytest
from litestar.testing import AsyncTestClient
from backend.main import app

@pytest.mark.asyncio
async def test_urgent_support_endpoint():
    """
    Test Viral 30-Second Rule endpoint: POST /api/v1/client/support/urgent
    """
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        payload = {
            "phone": "0949901122",
            "source_url": "https://osmo.vn/bat-tong-trang-sang"
        }
        response = await client.post("/api/v1/client/support/urgent", json=payload)
        
        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert data.get("ok") is True

@pytest.mark.asyncio
async def test_urgent_support_invalid_phone():
    """
    Test validation rules for phone number
    """
    async with AsyncTestClient(app=app, base_url="http://test") as client:
        payload = {
            "phone": "123", # Too short (min_length=10)
            "source_url": "https://osmo.vn"
        }
        response = await client.post("/api/v1/client/support/urgent", json=payload)
        assert response.status_code == 400
