import pytest
from litestar.testing import AsyncTestClient
from backend.main import app

@pytest.mark.asyncio
async def test_minimal_ping():
    async with AsyncTestClient(app=app) as client:
        response = await client.get("/health")
        assert response.status_code == 200
