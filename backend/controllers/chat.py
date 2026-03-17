from typing import Optional, List, Dict, Union
import logging
from litestar import Controller, get, post, delete, Request
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.chat_service import chat_service
from backend.schemas.chat import ChatHistoryResponse, CreateChatMessageRequest

logger = logging.getLogger("api-gateway")

# Security Rate Limits
chat_sync_limit = RateLimitConfig(rate_limit=("minute", 200), store="memory_store")
chat_clear_limit = RateLimitConfig(rate_limit=("minute", 50), store="memory_store")


class ChatController(Controller):
    path = "/api/v1/chat"

    @post(
        "/sessions/{session_id:str}/messages",
        status_code=201,
        summary="Persist a single chat message from frontend",
        middleware=[chat_sync_limit.middleware]
    )
    async def save_message(self, db_session: AsyncSession, session_id: str, request: Request, data: CreateChatMessageRequest) -> dict:
        """Save a chat message via ChatService (Elite V2.2)."""
        user_state = getattr(request.state, "user", {})
        user_id = user_state.get("id")

        msg_id = await chat_service.save_message(
            session=db_session,
            session_id=session_id,
            role=data.role,
            content=data.content,
            user_id=user_id,
            modality=data.modality or "text"
        )
        # Explicit commit for standalone save
        await db_session.commit()

        return {"status": "success", "id": msg_id}

    @get(
        "/sessions/{session_id:str}/messages",
        summary="Fetch raw chat logs with Cursor Pagination (Zalo Standard)",
        middleware=[chat_sync_limit.middleware]
    )
    async def get_chat_history(
        self,
        db_session: AsyncSession,
        session_id: str,
        request: Request,
        cursor: Optional[str] = None,
        limit: int = 20,
        user_id_query: Optional[str] = None,
        since_id: Optional[str] = None
    ) -> ChatHistoryResponse:
        """
        Retrieves messages for a session or user via ChatService.
        """
        user_state = getattr(request.state, "user", {})
        user_id = user_state.get("id")
        user_roles = user_state.get("roles", [])

        return await chat_service.get_chat_history(
            session=db_session,
            session_id=session_id,
            user_id=user_id,
            user_roles=user_roles,
            cursor=cursor,
            limit=limit,
            user_id_query=user_id_query,
            since_id=since_id
        )

    @delete(
        "/sessions/{session_id:str}/messages",
        status_code=200,
        summary="Permanently CLEAR all chat logs for a session",
        middleware=[chat_clear_limit.middleware]
    )
    async def delete_chat_history(self, db_session: AsyncSession, session_id: str, request: Request) -> dict:
        """Hard deletes all messages for a session or account via ChatService."""
        user_state = getattr(request.state, "user", {})
        user_email = user_state.get("sub")
        user_roles = user_state.get("roles", [])

        result = await chat_service.delete_chat_history(
            session=db_session,
            session_id=session_id,
            user_email=user_email,
            user_roles=user_roles
        )
        await db_session.commit()

        return result
