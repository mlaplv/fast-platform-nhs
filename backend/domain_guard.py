import os
from litestar.middleware import AbstractMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send
from litestar.exceptions import PermissionDeniedException

class DomainGuardMiddleware(AbstractMiddleware):
    """
    Elite Domain Guard (V2.2): Cô lập Admin/Client và chặn truy cập chéo.
    Bảo vệ các endpoint nhạy cảm chỉ được phép gọi từ domain quản trị.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.admin_url = os.getenv("ADMIN_URL", "admin.smartshop.test").replace("https://", "").replace("http://", "")
        self.api_url = os.getenv("API_URL", "api.smartshop.test").replace("https://", "").replace("http://", "")
        self.app_url = os.getenv("APP_URL", "smartshop.test").replace("https://", "").replace("http://", "")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
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
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        method = scope["method"]

        # 3. Định nghĩa các vùng cấm (Restricted Zones)
        # Các controller/đường dẫn chỉ dành cho Admin
        admin_only_prefixes = [
            "/users", "/settings", "/notifications",
            "/auditor", "/ai", "/mcp", "/scheduler",
            "/banner", "/chat/management"
        ]

        # 4. Logic chặn (Elite Blocking Rules)
        is_admin_domain = current_host == self.admin_url or current_host == self.api_url

        # Quy tắc 1: Nếu gọi vào Admin Zone mà không phải từ Admin Domain -> CHẶN
        if any(path.startswith(prefix) for prefix in admin_only_prefixes):
            if not is_admin_domain:
                raise PermissionDeniedException(f"Domain '{current_host}' is not authorized to access Admin Zone: {path}")

        # Quy tắc 2: Đối với các tài nguyên chung (Sản phẩm, Bài viết, Đơn hàng):
        # Chỉ Admin Domain mới được phép Mutation (POST, PATCH, PUT, DELETE)
        mutation_methods = ["POST", "PATCH", "PUT", "DELETE"]
        shared_resource_prefixes = ["/product", "/category", "/article", "/order"]

        if method in mutation_methods and any(path.startswith(prefix) for prefix in shared_resource_prefixes):
            # Ngoại lệ: Cho phép Client tạo đơn hàng (Checkout)
            if path.startswith("/order") and method == "POST":
                pass # Client được phép tạo đơn
            elif not is_admin_domain:
                raise PermissionDeniedException(f"Domain '{current_host}' is restricted from mutation on {path}")

        await self.app(scope, receive, send)
