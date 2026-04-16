from typing import TypedDict, List, Optional, Dict, Union
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

SECRET_KEY = os.environ.get("ENCRYPTION_SALT", "Micsmo_Elite_Standard_Salt_2026")  # R00: Consistent SSOT Key
ALGORITHM = "HS256"
logger = logging.getLogger("api-gateway.auth")

class AuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        token_ctx = None # Standard resource cleanup placeholder

        # ═══ MEGA-HARDEN: Try/Except to prevent 502/Crash ═══
        try:
            # CNS v2.2: Safe header extraction with errors='replace' to avoid UnicodeDecodeError (R51)
            headers: Dict[str, str] = {
                k.decode("utf-8", errors="replace").lower(): v.decode("utf-8", errors="replace") 
                for k, v in scope.get("headers", [])
            }
            
            if scope["type"] == "websocket":
                logger.debug(f"🔌 [WS-Auth] Handshake attempt for {scope['path']}")
                
            from backend.constants.tenants import DOMAIN_TENANT_MAP, DEFAULT_TENANT_ID
            
            tenant_id: Optional[str] = headers.get("x-tenant")
            
            # Elite V2.2: Dynamic Domain-to-Tenant Resolution (Rule R03)
            if not tenant_id:
                host: str = headers.get("host", "").split(":")[0].lower()
                tenant_id = DOMAIN_TENANT_MAP.get(host)

            token_ctx = current_tenant_id.set(tenant_id or DEFAULT_TENANT_ID)

            query_params: Dict[str, List[str]] = parse_qs(scope.get("query_string", b"").decode("utf-8", errors="replace"))
            if not tenant_id and "tenant" in query_params:
                tenant_id = query_params["tenant"][0]
                current_tenant_id.set(tenant_id)

            # R00: Elite Resilient Auth — Collect all token candidates
            candidates: List[Optional[str]] = []
            
            # 1. Authorization Header
            auth_header = headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                candidates.append(auth_header.split(" ")[1])
            
            # 2. Query Parameter (Real-time fallback)
            if "token" in query_params:
                candidates.append(query_params["token"][0])
            
            # 3. Cookies (Legacy/Browser fallback)
            if "cookie" in headers:
                cookies = {c.split('=', 1)[0].strip(): c.split('=', 1)[1].strip() for c in headers["cookie"].split(';') if '=' in c}
                candidates.append(cookies.get("admin_token"))
                candidates.append(cookies.get("access_token"))

            # R00: Try each candidate until success
            for token in [c for c in candidates if c]:
                try:
                    payload_raw: Dict[str, object] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # type: ignore
                    payload: UserPayload = {
                        "id": str(payload_raw.get("id", "")),
                        "sub": str(payload_raw.get("sub", "")),
                        "email": str(payload_raw.get("email", "")),
                        "roles": list(payload_raw.get("roles", [])) if isinstance(payload_raw.get("roles"), list) else [],
                        "perms": list(payload_raw.get("perms", [])) if isinstance(payload_raw.get("perms"), list) else [],
                        "tenant_id": str(payload_raw.get("tenant_id", "")) if payload_raw.get("tenant_id") else None,
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
                    
                    # R00: Success! Stop looking for other tokens
                    break
                except Exception as e:
                    logger.debug(f"🔐 [Auth] JWT Decode failed: {e}")
                    continue
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
