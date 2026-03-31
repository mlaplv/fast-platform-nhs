import os
import jwt
from litestar.middleware import ASGIMiddleware
from litestar.datastructures import State
from litestar.types import ASGIApp, Receive, Scope, Send
from litestar.exceptions import NotAuthorizedException

SECRET_KEY = os.environ["ENCRYPTION_SALT"]  # MUST be set — crash on start if missing (CTO Audit V2 C2)
ALGORITHM = "HS256"

class AuthMiddleware(ASGIMiddleware):
    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await next_app(scope, receive, send)
            return

        headers = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in scope.get("headers", [])}
        
        # 1. Resolve Tenant ID (R31)
        tenant_id = headers.get("x-tenant")
        
        # WebSocket query param support (V8.2)
        from urllib.parse import parse_qs
        query_params = parse_qs(scope.get("query_string", b"").decode("utf-8"))
        if not tenant_id and "tenant" in query_params:
            tenant_id = query_params["tenant"][0]

        # Fallback to Host subdomain extraction
        if not tenant_id and "host" in headers:
            host = headers["host"]
            parts = host.split(".")
            system_subdomains = {"admin", "api", "www", "portal"}
            relevant_parts = [p for p in parts if p not in system_subdomains]
            if relevant_parts:
                tenant_id = relevant_parts[0]

        if not tenant_id or tenant_id == "localhost":
            tenant_id = "default"

        from backend.database import current_tenant_id
        token_ctx = current_tenant_id.set(tenant_id)

        # 2. Auth Logic
        auth_header = headers.get("authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        if not token and "token" in query_params:
            token = query_params["token"][0]

        if not token and "cookie" in headers:
            cookies = {c.split('=', 1)[0].strip(): c.split('=', 1)[1].strip() for c in headers["cookie"].split(';') if '=' in c}
            token = cookies.get("admin_token")

        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                if "state" not in scope:
                    scope["state"] = {}
                scope["state"]["user"] = payload
                
                jwt_tenant = payload.get("tenant_id")
                if jwt_tenant:
                    current_tenant_id.set(jwt_tenant)
            except Exception:
                pass
        
        async def send_wrapper(message: "Send") -> None:
            """Helper to inject security headers into the start message (R51)."""
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                # R51: Elite V2.2 Security Headers (Production Grade)
                sec_headers = {
                    "Content-Security-Policy": (
                        "default-src 'self'; "
                        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; " # Allowed for Svelte/Vite dev
                        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                        "font-src 'self' https://fonts.gstatic.com data:; "
                        "img-src 'self' data: blob: https://*; " # Allow CDN images
                        "connect-src 'self' https://* wss://*; " # Allow API & WS
                        "frame-ancestors 'none';"
                    ),
                    "X-Frame-Options": "DENY",
                    "X-Content-Type-Options": "nosniff",
                    "Referrer-Policy": "strict-origin-when-cross-origin",
                    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
                }
                
                for k, v in sec_headers.items():
                    headers.append((k.encode("utf-8"), v.encode("utf-8")))
                    
                message["headers"] = headers
            await send(message)

        try:
            await next_app(scope, receive, send_wrapper)
        finally:
            # Clean up context to avoid bleed across requests
            current_tenant_id.reset(token_ctx)
