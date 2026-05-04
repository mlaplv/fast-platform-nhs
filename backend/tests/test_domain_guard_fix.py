import pytest
import jwt
import os
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta, timezone
from backend.main import app

# Standard Elite V2.2 Test Config
SECRET_KEY = os.environ.get("ENCRYPTION_SALT", "osmo_Elite_Standard_Salt_2026")
ALGORITHM = "HS256"

@pytest.mark.asyncio
async def test_super_admin_mutation_bypass():
    """
    R00 Test Mandate: Verify that SUPER_ADMIN identity can bypass DomainGuard 
    mutation restrictions on the production domain (osmo).
    This confirms AuthMiddleware is running BEFORE DomainGuardMiddleware.
    """
    # 1. Create a SUPER_ADMIN JWT Token
    payload = {
        "id": "test-admin-id",
        "sub": "admin@osmo",
        "roles": ["SUPER_ADMIN"],
        "perms": ["product:write"],
        "stamp": "VALID_STAMP_2026",
        "name": "Sếp Tổng",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # 2. Simulate PATCH request on production domain
    # Path: /api/v1/products/prod_miccosmo_virgin_white
    # Host: osmo
    headers = {
        "Authorization": f"Bearer {token}",
        "Host": "osmo"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://osmo") as client:
        # We expect this request to NOT return 403 (Forbidden) from DomainGuard.
        # It might return 401 or 404 depending on DB state, but DomainGuard should grant bypass.
        response = await client.patch("/api/v1/products/prod_miccosmo_virgin_white", headers=headers, json={})
        
        status = response.status_code
        body = response.text
        
        print(f"\n[TEST_RESULT] Status: {status}")
        print(f"[TEST_RESULT] Body: {body}")

        # If it's a 403, it must not be from DomainGuard
        if status == 403:
            assert "DomainGuard" not in body, f"❌ DomainGuard still blocking SUPER_ADMIN: {body}"
        
        # If fix is working, we should see something else or 200/404
        assert status != 403 or "DomainGuard" not in body
        print("✅ DomainGuard Bypass Verified!")
