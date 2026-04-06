from typing import TypedDict, List, Optional, Dict, Union, Any
import os
import jwt
from litestar.types import ASGIApp, Receive, Scope, Send
from litestar.exceptions import NotAuthorizedException

from urllib.parse import parse_qs
import logging
from backend.database import current_tenant_id

# ═══ Elite V2.2: Typed Identity ═══
class UserPayload(TypedDict, total=False):
    id: str
    sub: str
    email: str
    roles: List[str]
    perms: List[str]
    tenant_id: Optional[str]
    stamp: str
    name: str

SECRET_KEY = os.environ["ENCRYPTION_SALT"]  # MUST be set (CTO Audit V2 C2)
ALGORITHM = "HS256"
logger = logging.getLogger("api-gateway.auth")

class AuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        token_ctx: Any = None # Standard resource cleanup placeholder

        # ═══ MEGA-HARDEN: Try/Except to prevent 502/Crash ═══
        try:
            # CNS v2.2: Safe header extraction with errors='replace' to avoid UnicodeDecodeError (R51)
            headers: Dict[str, str] = {
                k.decode("utf-8", errors="replace").lower(): v.decode("utf-8", errors="replace") 
                for k, v in scope.get("headers", [])
            }
            
            if scope["type"] == "websocket":
                logger.debug(f"🔌 [WS-Auth] Handshake attempt for {scope['path']}")
                
            tenant_id: Optional[str] = headers.get("x-tenant")
            token_ctx = current_tenant_id.set(tenant_id or "default")

            query_params: Dict[str, List[str]] = parse_qs(scope.get("query_string", b"").decode("utf-8", errors="replace"))
            if not tenant_id and "tenant" in query_params:
                tenant_id = query_params["tenant"][0]
                current_tenant_id.set(tenant_id)

            token: Optional[str] = headers.get("authorization")
            if token and token.startswith("Bearer "):
                token = token.split(" ")[1]

            if not token and "token" in query_params:
                token = query_params["token"][0]

            if not token and "cookie" in headers:
                cookies: Dict[str, str] = {
                    c.split('=', 1)[0].strip(): c.split('=', 1)[1].strip() 
                    for c in headers["cookie"].split(';') if '=' in c
                }
                token = cookies.get("admin_token") or cookies.get("access_token")

            if token:
                try:
                    payload_raw: Dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # type: ignore
                    payload: UserPayload = {
                        "id": str(payload_raw.get("id", "")),
                        "sub": str(payload_raw.get("sub", "")),
                        "email": str(payload_raw.get("email", "")),
                        "roles": list(payload_raw.get("roles", [])),
                        "perms": list(payload_raw.get("perms", [])),
                        "tenant_id": payload_raw.get("tenant_id"),
                        "stamp": str(payload_raw.get("stamp", "")),
                        "name": str(payload_raw.get("name", ""))
                    }
                    
                    if "state" not in scope:
                        scope["state"] = {} # type: ignore
                    scope["state"]["user"] = payload # type: ignore
                    
                    if scope["type"] == "websocket":
                        logger.info(f"✅ [WS-Auth] Identified: {payload.get('email', 'unknown')} (Roles={payload.get('roles', [])})")
                    
                    jwt_tenant = payload.get("tenant_id")
                    if jwt_tenant:
                        current_tenant_id.set(jwt_tenant)
                except Exception as e:
                    logger.debug(f"🔐 [Auth] JWT Decode failed: {e}")
                    pass
        except Exception as e:
            logger.error(f"🚨 [Auth-Critical] Unexpected failure: {e}", exc_info=True)
            pass
        
        # R51: Elite V2.2 Security (Header delegation to Caddy)
        try:
            await self.app(scope, receive, send)
        finally:
            # Clean up context to avoid bleed across requests
            if token_ctx:
                current_tenant_id.reset(token_ctx)
