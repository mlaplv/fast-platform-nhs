import pytest
import jwt
import os
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta, timezone
from backend.main import app
from backend.database import async_session_maker, engine
from backend.database.models import User
from sqlalchemy import select

SECRET_KEY = os.environ.get("ENCRYPTION_SALT", "osmo_Elite_Standard_Salt_2026")
ALGORITHM = "HS256"

@pytest.fixture(autouse=True)
async def cleanup_database_pool():
    yield
    # Dispose the connection pool after each test to prevent event loop conflicts
    await engine.dispose()

async def get_real_user_credentials():
    """Helper to fetch an active user from DB to satisfy the V3 security stamp check."""
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.status == "ACTIVE").limit(1)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user.id, user.security_stamp
    except Exception:
        pass
    return "test-user-id", "VALID_STAMP_2026"

def generate_token(roles=None, perms=None, user_id="test-user-id", stamp="VALID_STAMP_2026"):
    payload = {
        "id": user_id,
        "sub": "user@osmo.vn",
        "roles": roles or [],
        "perms": perms or [],
        "stamp": stamp,
        "name": "Test User",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@pytest.mark.asyncio
async def test_chat_endpoints_unauthorized():
    """Verify that ChatController endpoints reject unauthenticated/unauthorized requests."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://admin.osmo.vn") as client:
        # 1. No token
        res = await client.get("/api/v1/chat/sessions/account/messages")
        assert res.status_code in (401, 403)

        # 2. Token without sys:admin permission
        token = generate_token(roles=["USER"], perms=["product:read"])
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.get("/api/v1/chat/sessions/account/messages", headers=headers)
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_chat_endpoints_authorized():
    """Verify that ChatController allows authorized requests (SUPER_ADMIN or sys:admin perms)."""
    user_id, stamp = await get_real_user_credentials()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://admin.osmo.vn") as client:
        # SUPER_ADMIN token
        token = generate_token(roles=["SUPER_ADMIN"], user_id=user_id, stamp=stamp)
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.get("/api/v1/chat/sessions/account/messages", headers=headers)
        # Should bypass guards
        assert res.status_code not in (401, 403)

        # Token with sys:admin permission
        token_sys = generate_token(perms=["sys:admin"], user_id=user_id, stamp=stamp)
        headers_sys = {"Authorization": f"Bearer {token_sys}"}
        res_sys = await client.get("/api/v1/chat/sessions/account/messages", headers=headers_sys)
        assert res_sys.status_code not in (401, 403)

@pytest.mark.asyncio
async def test_admin_ctv_unauthorized():
    """Verify that AdminCtvController endpoints reject unauthorized access."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://admin.osmo.vn") as client:
        # 1. No token
        res = await client.get("/api/v1/admin/ctv/stats")
        assert res.status_code in (401, 403)

        # 2. Token without user:manage permission
        token = generate_token(roles=["USER"], perms=["product:read"])
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.get("/api/v1/admin/ctv/stats", headers=headers)
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_admin_ctv_authorized():
    """Verify that AdminCtvController allows access to users with user:manage or SUPER_ADMIN."""
    user_id, stamp = await get_real_user_credentials()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://admin.osmo.vn") as client:
        token = generate_token(perms=["user:manage"], user_id=user_id, stamp=stamp)
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.get("/api/v1/admin/ctv/stats", headers=headers)
        # Should bypass guards
        assert res.status_code not in (401, 403)

@pytest.mark.asyncio
async def test_ads_protection_endpoints():
    """Verify that AdsProtectionController secures sensitive routes but keeps validate-click public."""
    # Test validate-click from a public domain (osmo.vn)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://osmo.vn") as client_public:
        res = await client_public.post("/api/v1/ads-protection/validate-click", json={
            "gclid": "test_gclid",
            "session_fingerprint": "test_fp",
            "user_agent": "Mozilla/5.0",
            "referrer": "google.com",
            "landing_page_url": "https://osmo.vn/product-1"
        })
        # Should NOT be blocked by DomainGuard or PermissionGuard (status 200/400/500, but not 401/403)
        assert res.status_code not in (401, 403)

    user_id, stamp = await get_real_user_credentials()
    # Test admin endpoints from admin domain
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://admin.osmo.vn") as client_admin:
        # /summary should be protected
        res_summary = await client_admin.get("/api/v1/ads-protection/summary")
        assert res_summary.status_code in (401, 403)

        # Token with sys:admin can access /summary
        token = generate_token(perms=["sys:admin"], user_id=user_id, stamp=stamp)
        headers = {"Authorization": f"Bearer {token}"}
        res_summary_auth = await client_admin.get("/api/v1/ads-protection/summary", headers=headers)
        assert res_summary_auth.status_code not in (401, 403)

@pytest.mark.asyncio
async def test_video_script_endpoints():
    """Verify that VideoScriptController requires content:write permission."""
    user_id, stamp = await get_real_user_credentials()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://admin.osmo.vn") as client:
        # 1. No token -> Blocked
        res = await client.post("/api/v1/video/script/generate", json={})
        assert res.status_code in (401, 403)

        # 2. Token with content:write -> Allowed
        token = generate_token(perms=["content:write"], user_id=user_id, stamp=stamp)
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.post("/api/v1/video/script/generate", headers=headers, json={})
        # Should bypass guards
        assert res.status_code not in (401, 403)
