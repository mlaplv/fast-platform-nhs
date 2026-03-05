from typing import Awaitable, Callable
from litestar import Request
from litestar.types import ASGIApp, Message, Receive, Scope, Send
from litestar.exceptions import ClientException


class BodyLimitMiddleware:
    """
    Doomsday T5: JSON Bomb Protection.
    Limits the maximum request body size at the ASGI level BEFORE Litestar
    attempts to parse JSON/FormData into Pydantic models.
    Prevents memory exhaustion attacks (OOM).
    """

    def __init__(self, app: ASGIApp, max_size: int = 1048576) -> None:
        """
        Args:
            app: The ASGI application
            max_size: Maximum payload size in bytes (default 1MB)
        """
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive)

        request = Request(scope, receive)
        
        # Check Content-Length header first for quick rejection
        content_length_str = request.headers.get("content-length")
        if content_length_str and content_length_str.isdigit():
            if int(content_length_str) > self.max_size:
                raise ClientException(status_code=413, detail=f"Request body exceeds {self.max_size} bytes limit.")

        # Read body chunks and accumulate size (protects against missing/fake Content-Length)
        total_size = 0

        async def _receive() -> Message:
            nonlocal total_size
            message = await receive()
            if message["type"] == "http.request":
                chunk_size = len(message.get("body", b""))
                total_size += chunk_size
                if total_size > self.max_size:
                    raise ClientException(status_code=413, detail=f"Request body exceeds {self.max_size} bytes limit.")
            return message

        await self.app(scope, _receive, send)
