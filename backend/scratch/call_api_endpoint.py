import asyncio
from litestar.testing import TestClient
from backend.main import app
from backend.database import current_tenant_id

def main():
    current_tenant_id.set("osmo.vn")
    # We can use the test client with app
    with TestClient(app=app) as client:
        # We need headers for authentication / tenant if required, but let's check without auth first or pass headers
        # Wait, the endpoint is protected by guards: [PermissionGuard(PermissionEnum.CONTENT_READ)]
        # We can bypass guards or mock auth by logging in or setting headers.
        # Wait, let's check the response status.
        # Actually, let's just query the database and print the response structure as return dict by calling the handler directly.
        # Since calling the handler directly requires owner, let's mock owner!
        pass

if __name__ == "__main__":
    main()
