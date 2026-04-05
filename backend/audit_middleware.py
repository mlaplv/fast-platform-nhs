import time
import json
import logging
from litestar.types import ASGIApp, Receive, Scope, Send, Message

logger = logging.getLogger("audit-trail")

class AuditMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        # Chỉ Audit các action mutation để tối ưu I/O (Read GET requests không thay đổi state)
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            start_time = time.perf_counter()
            status_code = 500  # Default fallback

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
                actor_id = str(user_dict.get("sub", user_dict.get("id", "ANONYMOUS"))) if isinstance(user_dict, dict) else "ANONYMOUS"
                
                domain = ""
                headers_list = scope.get("headers", [])
                if isinstance(headers_list, list):
                    for k, v in headers_list:
                        if k == b"host":
                            domain = v.decode("utf-8")
                            break
                
                path = str(scope.get("path", ""))
                
                # Phóng log JSON chuẩn Forensic
                audit_event = {
                    "audit": True,
                    "actor": actor_id,
                    "action": f"{method} {path}",
                    "status": int(status_code),
                    "ms": round(duration_ms, 2),
                    "domain": domain
                }
                logger.info(json.dumps(audit_event))
        else:
            await self.app(scope, receive, send)

