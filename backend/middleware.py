import os
import jwt
from litestar.types import ASGIApp, Receive, Scope, Send
from litestar.exceptions import NotAuthorizedException

from urllib.parse import parse_qs
import logging
from backend.database import current_tenant_id

SECRET_KEY = os.environ["ENCRYPTION_SALT"]  # MUST be set — crash on start if missing (CTO Audit V2 C2)
ALGORITHM = "HS256"
logger = logging.getLogger("api-gateway.auth")

class AuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        # ═══ MEGA-HARDEN: Try/Except to prevent 502/Crash ═══
        try:
            # CNS v2.2: Safe header extraction with errors='replace' to avoid UnicodeDecodeError (R51)
            headers = {
                k.decode("utf-8", errors="replace").lower(): v.decode("utf-8", errors="replace") 
                for k, v in scope.get("headers", [])
            }
            
            if scope["type"] == "websocket":
                logger.info(f"🔌 [WS-Auth] Handshake Start: {scope['path']}")
                
            tenant_id = headers.get("x-tenant")
            current_tenant_id.set(tenant_id)
            token_ctx = current_tenant_id.set(tenant_id)

            query_params = parse_qs(scope.get("query_string", b"").decode("utf-8", errors="replace"))
            if not tenant_id and "tenant" in query_params:
                tenant_id = query_params["tenant"][0]
                current_tenant_id.set(tenant_id)

            token = headers.get("authorization")
            if token and token.startswith("Bearer "):
                token = token.split(" ")[1]

            if not token and "token" in query_params:
                token = query_params["token"][0]

            if not token and "cookie" in headers:
                cookies = {c.split('=', 1)[0].strip(): c.split('=', 1)[1].strip() for c in headers["cookie"].split(';') if '=' in c}
                token = cookies.get("admin_token") or cookies.get("access_token")

            if token:
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                    if "state" not in scope:
                        scope["state"] = {}
                    scope["state"]["user"] = payload
                    
                    if scope["type"] == "websocket":
                        logger.info(f"✅ [WS-Auth] User Identified: {payload.get('email')} (Roles={payload.get('roles')})")
                    
                    jwt_tenant = payload.get("tenant_id")
                    if jwt_tenant:
                        current_tenant_id.set(jwt_tenant)
                except Exception as e:
                    logger.warning(f"🔐 [Auth] JWT Decode failed: {e}")
                    pass
        except Exception as e:
            logger.error(f"🚨 [Auth-Critical] Middleware failure: {e}", exc_info=True)
            # Proceed even if Auth fails to let Litestar handle errors gracefully
            pass
        
        # R51: Elite V2.2 Security (Header delegation to Caddy)
        try:
            await self.app(scope, receive, send)
        finally:
            # Clean up context to avoid bleed across requests
            current_tenant_id.reset(token_ctx if 'token_ctx' in locals() else None)
