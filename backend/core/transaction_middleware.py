import logging
from typing import Optional
from litestar.types import ASGIApp, Receive, Scope, Send, Message
from advanced_alchemy.extensions.litestar._utils import get_aa_scope_state
from backend.database.alchemy_config import alchemy_config

logger = logging.getLogger("api-gateway")

class TransactionMiddleware:
    """
    Elite V2.2 ASGI Transaction Middleware.
    Automatically commits database sessions for successful write requests (POST/PUT/PATCH/DELETE)
    and rolls back on errors (HTTP >= 400 or raised exceptions).
    """
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        is_write_request = method in ("POST", "PUT", "PATCH", "DELETE")

        if not is_write_request:
            await self.app(scope, receive, send)
            return

        session_committed = False
        response_status: Optional[int] = None

        async def transaction_send(message: Message) -> None:
            nonlocal response_status, session_committed
            if message["type"] == "http.response.start":
                response_status = message["status"]
                session_key = alchemy_config.litestar_config.session_scope_key
                session = get_aa_scope_state(scope, session_key)

                if session is not None and not session_committed:
                    if response_status is not None and response_status < 400:
                        try:
                            logger.info(f"💾 [TransactionMiddleware] Auto-committing session for {method} {scope.get('path')}")
                            await session.commit()
                            session_committed = True
                        except Exception as commit_err:
                            logger.error(f"🛑 [TransactionMiddleware] Auto-commit failed: {commit_err}", exc_info=True)
                            await session.rollback()
                            raise commit_err
                    else:
                        logger.warning(f"🔄 [TransactionMiddleware] Rolling back session due to status {response_status} for {method} {scope.get('path')}")
                        await session.rollback()
                        session_committed = True

            await send(message)

        try:
            await self.app(scope, receive, transaction_send)
        except Exception as exc:
            session_key = alchemy_config.litestar_config.session_scope_key
            session = get_aa_scope_state(scope, session_key)
            if session is not None and not session_committed:
                logger.error(f"🛑 [TransactionMiddleware] Unhandled exception. Rolling back session: {exc}")
                await session.rollback()
            raise exc
