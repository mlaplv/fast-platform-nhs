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

SECRET_KEY = os.environ.get("ENCRYPTION_SALT")
if not SECRET_KEY:
    if os.environ.get("ENVIRONMENT") == "production":
        import sys
        logger.critical("🚨 [CRITICAL_CONFIG_ERROR] ENCRYPTION_SALT is missing in Production environment! Absolute security shutdown.")
        sys.exit("CRITICAL CONFIGURATION ERROR: ENCRYPTION_SALT MUST BE CONFIGURED IN PRODUCTION.")
    else:
        SECRET_KEY = "osmo_Elite_Standard_Salt_2026"  # Dev fallback thưa Sếp!
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
        
        # [THIẾT QUÂN LUẬT] Kiểm tra IP Blacklist (R00)
        try:
            client_ip = scope.get("client", ("0.0.0.0", 0))[0]
            from backend.services.ai_engine.core.key_rotator import key_rotator
            if key_rotator._use_redis and key_rotator.client:
                # Elite V2.2: Fast path for security check
                is_blacklisted = await key_rotator.client.get(f"security:blacklist:ip:{client_ip}")
                if is_blacklisted:
                    logger.error(f"🚫 [SECURITY_BLOCK] Connection denied for blacklisted IP: {client_ip}")
                    raise NotAuthorizedException("Địa chỉ IP của bạn đã bị khóa do vi phạm an ninh.")
        except NotAuthorizedException as e:
            raise e
        except Exception:
            pass # Fail open for connectivity issues to avoid total lockout

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
            tenant_source = "header"
            
            # Elite V2.2: Dynamic Domain-to-Tenant Resolution (Rule R03)
            if not tenant_id:
                host: str = headers.get("host", "").split(":")[0].lower()
                tenant_id = DOMAIN_TENANT_MAP.get(host)
                tenant_source = "host_map"

            final_tenant = tenant_id or DEFAULT_TENANT_ID
            if not tenant_id:
                tenant_source = "default"
                
            logger.info(f"🌐 [Tenant] Identified: {final_tenant} via {tenant_source} (Host: {headers.get('host')})")
            token_ctx = current_tenant_id.set(final_tenant)

            query_params: Dict[str, List[str]] = parse_qs(scope.get("query_string", b"").decode("utf-8", errors="replace"))
            if not tenant_id and "tenant" in query_params:
                tenant_id = query_params["tenant"][0]
                current_tenant_id.set(tenant_id)
                logger.info(f"🌐 [Tenant] Overridden by query: {tenant_id}")

            # Check for AI Agent API Key
            agent_api_key = headers.get("x-agent-api-key")
            auth_header = headers.get("authorization")
            if auth_header and auth_header.startswith("ApiKey "):
                agent_api_key = auth_header.split(" ")[1]

            if agent_api_key:
                import hashlib
                valid_keys = [k.strip() for k in os.getenv("AGENT_API_KEYS", "").split(",") if k.strip()]
                valid_hashes = [h.strip().lower() for h in os.getenv("AGENT_API_KEY_HASHES", "").split(",") if h.strip()]
                
                # Compute SHA-256 hex hash of the received key
                hashed_key = hashlib.sha256(agent_api_key.encode("utf-8")).hexdigest().lower()
                
                # Verify key directly or by hash
                if (agent_api_key in valid_keys) or (hashed_key in valid_hashes):
                    if "state" not in scope:
                        scope["state"] = {}
                    scope["state"]["is_agent"] = True
                    scope["state"]["agent_key"] = agent_api_key
                    logger.info(f"🔑 [Auth-Agent] Verified AI Agent cryptographically (Key Prefix: {agent_api_key[:4]}...).")

            # Military-Grade Replay Attack Protection
            agent_timestamp = headers.get("x-agent-timestamp")
            if agent_timestamp and scope.get("state", {}).get("is_agent"):
                try:
                    import time
                    request_time = float(agent_timestamp)
                    current_time = time.time()
                    if abs(current_time - request_time) > 300: # 5 minutes window
                        ip = headers.get("x-real-ip") or scope.get("client", [None])[0] or "unknown"
                        
                        # Trigger infraction async
                        import asyncio
                        from backend.services.commerce.security.input_guard import input_guard
                        asyncio.create_task(input_guard.record_security_infraction(ip))
                        
                        from litestar.exceptions import PermissionDeniedException
                        raise PermissionDeniedException("Phiên yêu cầu đã hết hạn. Suspected replay attack.")
                except PermissionDeniedException:
                    raise
                except Exception as e:
                    logger.warning(f"Failed to validate agent timestamp in middleware: {e}")

            # Parse Google/OpenAI A2A (Agent-to-Agent) Context Header
            a2a_header = headers.get("x-a2a-context")
            if a2a_header:
                import base64
                import json
                try:
                    decoded = None
                    try:
                        decoded = base64.b64decode(a2a_header).decode("utf-8")
                    except Exception:
                        decoded = a2a_header  # Fallback to raw JSON string

                    a2a_data = json.loads(decoded)
                    if "state" not in scope:
                        scope["state"] = {}
                    scope["state"]["a2a_context"] = a2a_data
                    logger.info(f"🤝 [A2A-Context] Injected A2A Context: {a2a_data.get('referring_agent', 'unknown')}")
                except Exception as e:
                    logger.warning(f"Failed to parse X-A2A-Context header: {e}")


            # R00: Elite Resilient Auth — Collect all token candidates
            candidates: List[Optional[str]] = []

            
            # 0. User Delegation Header (X-User-Delegation-Token)
            user_delegation_token = headers.get("x-user-delegation-token")
            if user_delegation_token:
                candidates.append(user_delegation_token)

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
                    
                    # [THIẾT QUÂN LUẬT] Kiểm tra Device Fingerprint (dfp)
                    jwt_dfp = payload_raw.get("dfp")
                    client_dfp = headers.get("x-device-fingerprint")
                    
                    is_admin = any(role in ["ADMIN", "SUPER_ADMIN", "OPERATIVE"] for role in payload.get("roles", []))
                    
                    if jwt_dfp and client_dfp and str(jwt_dfp) != str(client_dfp):
                        logger.warning(f"🚨 [SECURITY] Fingerprint Mismatch! User: {payload.get('sub')}")
                        if is_admin:
                            if os.environ.get("ENVIRONMENT") != "development":
                                raise NotAuthorizedException("Thiết bị không hợp lệ (Security Fingerprint Mismatch).")

                    # [THIẾT QUÂN LUẬT] Kiểm tra Session Revocation (Security Stamp)
                    if is_admin:
                        token_stamp = payload.get("stamp")
                        # Chỉ check nếu token có stamp (để hỗ trợ chuyển đổi từ legacy token)
                        if token_stamp and token_stamp != "MISSING":
                            # R03: Fast path — Redis cache stamp (TTL 5 phút)
                            # Tránh 1 DB query trên MỌI admin request → giảm latency ~10ms/req
                            stamp_key = f"security:stamp:{payload['id']}"
                            cached_val: Optional[str] = None
                            db_stamp: Optional[str] = None
                            db_status: Optional[str] = None
                            try:
                                if key_rotator._use_redis and key_rotator.client:
                                    raw = await key_rotator.client.get(stamp_key)
                                    if raw:
                                        cached_val = raw.decode() if isinstance(raw, bytes) else str(raw)
                                        if cached_val and ":" in cached_val:
                                            db_stamp, db_status = cached_val.split(":", 1)
                            except Exception:
                                pass

                            if not db_stamp:
                                # Cache miss: query DB một lần, write-through cache
                                from backend.database import async_session_maker
                                from sqlalchemy import select
                                from backend.database.models import User
                                async with async_session_maker() as session:
                                    user_res = await session.execute(
                                        select(User.security_stamp, User.status).where(User.id == payload["id"])
                                    )
                                    row = user_res.first()
                                    if row:
                                        db_stamp, db_status = row[0], row[1]
                                try:
                                    if key_rotator._use_redis and key_rotator.client and db_stamp:
                                        await key_rotator.client.set(stamp_key, f"{db_stamp}:{db_status or 'ACTIVE'}", ex=300)
                                except Exception:
                                    pass

                            if db_status and db_status != "ACTIVE":
                                logger.error(f"🚫 [MARTIAL_LAW] Admin Account Suspended for {payload['sub']}. Status: {db_status}")
                                raise NotAuthorizedException("Tài khoản của bạn đã bị khóa hoặc ngừng hoạt động.")

                            if db_stamp and str(db_stamp) != str(token_stamp):
                                logger.error(f"🚫 [MARTIAL_LAW] Session Revoked for {payload['sub']}. Stamp mismatch.")
                                raise NotAuthorizedException("Phiên làm việc đã hết hạn hoặc bị thu hồi.")

                    if "state" not in scope:
                        scope["state"] = {} # type: ignore
                    scope["state"]["user"] = payload # type: ignore
                    
                    if scope["type"] == "websocket":
                        logger.info(f"✅ [WS-Auth] Identified: {payload.get('email', 'unknown')}")
                    
                    jwt_tenant = payload.get("tenant_id")
                    if jwt_tenant:
                        current_tenant_id.set(jwt_tenant)
                    
                    return await self.app(scope, receive, send)

                except jwt.ExpiredSignatureError:
                    continue
                except jwt.InvalidTokenError:
                    continue
                except NotAuthorizedException as e:
                    # Elite V2.2: Ngắt kết nối ngay nếu vi phạm an ninh
                    logger.error(f"🛡️ [SECURITY_DENIED] {e.detail}")
                    raise e
                except Exception as e:
                    logger.error(f"🚨 [Auth-Critical] Unexpected failure: {e}", exc_info=True)
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
