import time
import json
import logging
import re
from datetime import datetime, UTC
from litestar.types import ASGIApp, Receive, Scope, Send, Message
from backend.services.ai_engine.core.security_guard import security_guard
from backend.database.models.ads import IPBlacklist
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.core.database import SYSTEM_READ_ONLY
from litestar.exceptions import PermissionDeniedException
import hmac
import hashlib
import os

SECRET_KEY = os.environ.get("ENCRYPTION_SALT", "osmo_Elite_Standard_Salt_2026")

logger = logging.getLogger("audit-trail")

# Patterns tấn công phổ biến (Elite Security Layer)
ATTACK_PATTERNS = [
    r"(?i)(union\s+select|drop\s+table|truncate\s+table|delete\s+from|--|#)", # SQL Injection
    r"(?i)(<script|alert\(|onerror=)", # XSS
]

async def auto_block_task(ip_address: str, log_entry: dict):
    """
    Background Task: Phân tích và chặn IP nếu cần.
    """
    try:
        analysis = await security_guard.analyze_log_entry(json.dumps(log_entry))
        if analysis.risk_level == "CRITICAL" and analysis.is_attack:
            logger.error(f"🚨 [AUTO_BAN] Blocking IP {ip_address}. Reason: {analysis.reason}")
            
            async with alchemy_config.create_session_maker()() as session:
                # Kiểm tra xem đã chặn chưa
                stmt = select(IPBlacklist).where(IPBlacklist.ip_address == ip_address)
                existing = await session.execute(stmt)
                if not existing.scalar():
                    new_ban = IPBlacklist(
                        ip_address=ip_address,
                        reason=f"AI Auto-Ban: {analysis.reason}",
                        fraud_score=1.0
                    )
                    session.add(new_ban)
                    await session.commit()
    except Exception as e:
        logger.error(f"Failed to auto-block IP {ip_address}: {e}")

class AuditMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = str(scope.get("path", ""))
        query = scope.get("query_string", b"").decode("utf-8")
        
        # Kiểm tra dấu hiệu tấn công ngay từ Header/Path/Query
        is_suspicious = False
        reason = None
        for pattern in ATTACK_PATTERNS:
            if re.search(pattern, path) or re.search(pattern, query):
                is_suspicious = True
                reason = "Malicious pattern in URL/Query"
                break

        # [THIẾT QUÂN LUẬT] Chặn mọi mutation nếu hệ thống đang Read-Only
        if SYSTEM_READ_ONLY and method in ["POST", "PUT", "PATCH", "DELETE"]:
            logger.error(f"🛑 [MARTIAL_LAW] Mutation Blocked: {method} {path} from {scope.get('client')}")
            raise PermissionDeniedException("Hệ thống đang trong trạng thái PHONG TỎA (Read-Only). Mọi thao tác thay đổi dữ liệu bị cấm.")

        # Chỉ Audit các action mutation hoặc các request nghi vấn
        if method in ["POST", "PUT", "PATCH", "DELETE"] or is_suspicious:
            start_time = time.perf_counter()
            status_code = 500 

            async def send_wrapper(message: Message) -> None:
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = int(message.get("status", 500))
                await send(message)

            try:
                await self.app(scope, receive, send_wrapper)
            finally:
                duration_ms = float((time.perf_counter() - start_time) * 1000.0)
                
                state_dict = scope.get("state", {})
                user_dict = state_dict.get("user", {}) if isinstance(state_dict, dict) else {}
                actor_id = str(user_dict.get("sub", user_dict.get("id", "ANONYMOUS")))
                
                # Lấy IP thật
                client = scope.get("client")
                ip_address = client[0] if client else "unknown"
                headers = dict(scope.get("headers", []))
                if b"x-forwarded-for" in headers:
                    ip_address = headers[b"x-forwarded-for"].decode("utf-8").split(",")[0]
                
                # Phóng log JSON chuẩn Forensic
                audit_event = {
                    "audit": True,
                    "actor": actor_id,
                    "ip": ip_address,
                    "action": f"{method} {path}",
                    "status": int(status_code),
                    "ms": round(duration_ms, 2),
                    "suspicious": is_suspicious,
                    "risk_reason": reason if is_suspicious else None,
                    "timestamp": datetime.now(UTC).isoformat()
                }
                
                # [THIẾT QUÂN LUẬT] Ký số vào Log để chống giả mạo
                log_content = json.dumps(audit_event, sort_keys=True)
                signature = hmac.new(
                    SECRET_KEY.encode(),
                    log_content.encode(),
                    hashlib.sha256
                ).hexdigest()
                audit_event["sig"] = signature

                if is_suspicious:
                    logger.warning(f"🛡️ [SECURITY_ALERT] {json.dumps(audit_event)}")
                    # Elite V2.2: Kích hoạt Auto-Ban Task (Chạy ngầm để không block request)
                    import asyncio
                    asyncio.create_task(auto_block_task(ip_address, audit_event))
                else:
                    logger.info(json.dumps(audit_event))
        else:
            await self.app(scope, receive, send)

