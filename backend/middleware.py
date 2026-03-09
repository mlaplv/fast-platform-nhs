import os
import jwt
from litestar.middleware import AbstractMiddleware
from litestar.datastructures import State
from litestar.types import ASGIApp, Receive, Scope, Send
from litestar.exceptions import NotAuthorizedException

SECRET_KEY = os.environ["ENCRYPTION_SALT"]  # MUST be set — crash on start if missing (CTO Audit V2 C2)
ALGORITHM = "HS256"

class AuthMiddleware(AbstractMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in scope.get("headers", [])}
        
        # 1. Resolve Tenant ID (R31)
        tenant_id = headers.get("x-tenant")
        
        # Fallback to Host subdomain extraction
        if not tenant_id and "host" in headers:
            host = headers["host"]
            parts = host.split(".")
            
            # System domains to ignore when extracting tenant
            system_subdomains = {"admin", "api", "www", "portal"}
            
            # Filter parts: e.g. ["admin", "smartshop", "test"] -> ["smartshop", "test"]
            relevant_parts = [p for p in parts if p not in system_subdomains]
            
            if relevant_parts:
                # The first non-system component is the tenant (e.g., "smartshop" or "store1")
                tenant_id = relevant_parts[0]

        # Final fallback
        if not tenant_id or tenant_id == "localhost":
            tenant_id = "default"

        # Set Global Context (R30)
        from backend.database import current_tenant_id
        token_ctx = current_tenant_id.set(tenant_id)

        # 2. Auth Logic
        auth_header = headers.get("authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        if not token and "cookie" in headers:
            cookies = {c.split('=', 1)[0].strip(): c.split('=', 1)[1].strip() for c in headers["cookie"].split(';') if '=' in c}
            token = cookies.get("admin_token")

        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                scope["state"]["user"] = payload
                
                # If JWT has a tenant_id, it OVERRIDES the header/host for security (prevents spoofing)
                jwt_tenant = payload.get("tenant_id")
                if jwt_tenant:
                    current_tenant_id.set(jwt_tenant)
                
            except Exception:
                pass
        
        async def send_wrapper(message: "Send") -> None:
            """Helper to inject security headers into the start message (R51)."""
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                sec_headers = {
                    "Content-Security-Policy": "default-src 'self'",
                    "X-Frame-Options": "DENY",
                    "X-Content-Type-Options": "nosniff",
                    "Referrer-Policy": "strict-origin-when-cross-origin",
                    "Permissions-Policy": "geolocation=(), microphone=()",
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
                }
                
                for k, v in sec_headers.items():
                    headers.append((k.encode("utf-8"), v.encode("utf-8")))
                    
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Clean up context to avoid bleed across requests
            current_tenant_id.reset(token_ctx)
