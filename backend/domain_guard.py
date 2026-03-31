import os
from litestar.middleware import ASGIMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send
from litestar.exceptions import PermissionDeniedException

class DomainGuardMiddleware(ASGIMiddleware):
    """
    Elite Domain Guard (V2.2): Cô lập Admin/Client và chặn truy cập chéo.
    Bảo vệ các endpoint nhạy cảm chỉ được phép gọi từ domain quản trị.
    """
    def __init__(self) -> None:
        self.admin_url = os.getenv("ADMIN_URL", "admin.smartshop.test").replace("https://", "").replace("http://", "")
        self.api_url = os.getenv("API_URL", "api.smartshop.test").replace("https://", "").replace("http://", "")
        self.app_url = os.getenv("APP_URL", "smartshop.test").replace("https://", "").replace("http://", "")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

    async def handle(self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await next_app(scope, receive, send)
            return

        # 1. Trích xuất Host/Origin
        headers = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in scope.get("headers", [])}
        host = headers.get("host", "").split(":")[0]  # Bỏ port nếu có
        x_forwarded_host = headers.get("x-forwarded-host", "").split(":")[0]

        current_host = x_forwarded_host or host

        # 2. Bỏ qua kiểm tra nếu là môi trường Local hoặc Mạng nội bộ (Private Network)
        import ipaddress
        is_internal = False
        try:
            ip_obj = ipaddress.ip_address(current_host)
            is_internal = ip_obj.is_private or ip_obj.is_loopback
        except ValueError:
            # Nếu current_host là tên (như 'api' hoặc 'localhost')
            is_internal = current_host in ["localhost", "127.0.0.1", "api"]

        if is_internal or self.debug:
            await next_app(scope, receive, send)
            return

        path = scope["path"]
        method = scope["method"]

        # 3. Định nghĩa các vùng cấm (Restricted Zones) - Elite V2.2
        # Các controller/đường dẫn chỉ dành cho Admin, tuyệt đối không cho phép từ Client domain.
        admin_only_prefixes = [
            "/api/v1/users", "/api/v1/settings", "/api/v1/notifications",
            "/api/v1/auditor", "/api/v1/ai", "/api/v1/mcp", "/api/v1/scheduler",
            "/api/v1/banner", "/api/v1/chat", "/api/v1/auth",
            "/api/v1/pulse", "/api/v1/intent", "/api/v1/voice", "/api/v1/content", "/api/v1/media",
            "/api/v1/orders",    # Chặn prefix order chung của Admin (Dùng CheckoutController cho Client)
            "/ws/stt",           # WebSocket voice
        ]

        # 4. Logic chặn (Elite Blocking Rules)
        is_admin_domain = current_host == self.admin_url or current_host == self.api_url

        # Quy tắc 1: Nếu gọi vào Admin Zone mà không phải từ Admin Domain -> CHẶN
        if any(path.startswith(prefix) for prefix in admin_only_prefixes):
            if not is_admin_domain:
                raise PermissionDeniedException(f"Domain '{current_host}' is NOT authorized to access Admin API: {path}")

        # Quy tắc 2: Đối với các tài nguyên chung (Sản phẩm, Bài viết, Danh mục):
        # Chỉ Admin Domain mới được phép Mutation (POST, PATCH, PUT, DELETE)
        mutation_methods = ["POST", "PATCH", "PUT", "DELETE"]
        shared_resource_prefixes = ["/api/v1/products", "/api/v1/categories", "/api/v1/articles"]

        if method in mutation_methods and any(path.startswith(prefix) for prefix in shared_resource_prefixes):
            if not is_admin_domain:
                raise PermissionDeniedException(f"Domain '{current_host}' is RESTRICTED from mutation on {path}")

        await next_app(scope, receive, send)
