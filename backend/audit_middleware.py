import time
import asyncio
from litestar.middleware import ASGIMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send
from backend.services.event_bus import event_bus
import logging

logger = logging.getLogger("api-gateway")

class AuditMiddleware(ASGIMiddleware):
    """
    R00/Elite V2.2: Centralized Audit Middleware.
    Ghi nhận log bất đồng bộ qua EventBus cho các action mutation (POST, PATCH, PUT, DELETE).
    Không chặn luồng chính (Async write), đảm nhiệm Audit cross-cutting.
    """
    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await next_app(scope, receive, send)
            return

        method = scope.get("method", "")
        # Chỉ Audit các action mutation để tránh memory leak từ Read GET requests
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Trích xuất Actor (User ID) từ scope.state
            user = scope.get("state", {}).get("user", {}) if "state" in scope else {}
            actor_id = user.get("sub", user.get("id", "ANONYMOUS"))
            
            path = scope.get("path", "")
            
            # Gửi Audit Event lên Event Bus không chờ (Async Fire and Forget)
            headers = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in scope.get("headers", [])}
            payload = {
                "actor_id": actor_id,
                "action_type": f"{method} {path}",
                "timestamp": time.time(),
                "domain": headers.get("host", "")
            }
            # Phát tín hiệu lên EventBus. Ở đầu cuối sẽ có logic bulk insert.
            asyncio.create_task(self._emit_audit(payload))

        await next_app(scope, receive, send)
        
    async def _emit_audit(self, payload: dict) -> None:
        try:
            await event_bus.emit(name="USER_ACTION_AUDIT", payload=payload)
        except Exception as e:
            logger.error(f"[AuditMiddleware] Lỗi gửi log: {e}")
