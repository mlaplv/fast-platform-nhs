import os
import ipaddress
import logging
from typing import Dict
from litestar.types import ASGIApp, Receive, Scope, Send
from litestar.exceptions import PermissionDeniedException

# Elite V2.2: Centralized security constants (Rule R00)
from backend.constants.security import (
    ADMIN_ONLY_PREFIXES,
    MUTATION_RESTRICTED_METHODS,
    SHARED_RESOURCE_PREFIXES,
)

logger: logging.Logger = logging.getLogger("api-gateway")

class DomainGuardMiddleware:
    """
    Elite Domain Guard (V2.2): Cô lập Admin/Client và chặn truy cập chéo.
    Bảo vệ các endpoint nhạy cảm chỉ được phép gọi từ domain quản trị.
    (CNS V2.2: Fixed Any types and WebSocket scope safety).
    """
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.admin_url: str = os.getenv("ADMIN_URL", "admin.smartshop.test").replace("https://", "").replace("http://", "")
        self.api_url: str = os.getenv("API_URL", "api.smartshop.test").replace("https://", "").replace("http://", "")
        self.app_url: str = os.getenv("APP_URL", "smartshop.test").replace("https://", "").replace("http://", "")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        try:
            # 1. Trích xuất Host/Origin với ép kiểu tường minh 100% (Safe decoding R51)
            headers: Dict[str, str] = {
                k.decode("utf-8", errors="replace").lower(): v.decode("utf-8", errors="replace") 
                for k, v in scope.get("headers", [])
            }
            host: str = headers.get("host", "").split(":")[0]  # Bỏ port nếu có
            x_forwarded_host: str = headers.get("x-forwarded-host", "").split(":")[0]

            current_host: str = x_forwarded_host or host

            # 2. Bỏ qua kiểm tra nếu là môi trường Local hoặc Mạng nội bộ (Private Network)
            is_internal: bool = False
            try:
                ip_obj = ipaddress.ip_address(current_host)
                is_internal = ip_obj.is_private or ip_obj.is_loopback
            except ValueError:
                # Nếu current_host là tên (như 'api' hoặc 'localhost')
                is_internal = current_host in ["localhost", "127.0.0.1", "api"]

            if is_internal or self.debug:
                await self.app(scope, receive, send)
                return

            path: str = scope["path"]
            # CNS V2.2: WebSocket scopes do not have a 'method' attribute. Get safely.
            method: str | None = scope.get("method")

            # 3. Logic chặn (Elite Blocking Rules) - Rule R00 compliance
            is_admin_domain: bool = current_host == self.admin_url or current_host == self.api_url
            
            # [DIAGNOSTIC] Whitelist /ws/stt temporarily to find truth
            if path == "/ws/stt":
                await self.app(scope, receive, send)
                return

            # Quy tắc 1: Nếu gọi vào Admin Zone mà không phải từ Admin Domain -> CHẶN
            if any(path.startswith(prefix) for prefix in ADMIN_ONLY_PREFIXES):
                if not is_admin_domain:
                    msg: str = f"⛔ DomainGuard: Access Denied to '{path}' from unauthorized host '{current_host}' (Expected={self.admin_url})"
                    logger.warning(msg)
                    raise PermissionDeniedException(msg)

            # Quy tắc 2: Đối với các tài nguyên chung (Sản phẩm, Bài viết, Danh mục):
            # Chỉ Admin Domain mới được phép Mutation (POST, PATCH, PUT, DELETE)
            if (
                method in MUTATION_RESTRICTED_METHODS 
                and any(path.startswith(prefix) for prefix in SHARED_RESOURCE_PREFIXES)
            ):
                if not is_admin_domain:
                    msg: str = f"⛔ DomainGuard: Mutation restricted on '{path}' for host '{current_host}'"
                    logger.warning(msg)
                    raise PermissionDeniedException(msg)
        except PermissionDeniedException:
            raise
        except Exception as e:
            logger.error(f"🚨 [DomainGuard-Critical] Middleware failure: {e}")
            # Continue to app if unexpected internal error occurs to avoid 502
            pass

        await self.app(scope, receive, send)
