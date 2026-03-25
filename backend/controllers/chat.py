from __future__ import annotations
from typing import Optional, List, Dict, Union
import logging
import uuid
from datetime import datetime, timezone
from litestar import Controller, get, post, delete, Request
from litestar.exceptions import NotFoundException, HTTPException
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sqlalchemy_delete, func

from backend.schemas.chat import ChatHistoryResponse, ChatMessageSchema, CreateChatMessageRequest
from backend.schemas.common import SuccessResponse
from backend.services.chat_service import chat_service

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
    async def save_message(self, db_session: "AsyncSession", session_id: str, request: Request, data: CreateChatMessageRequest) -> SuccessResponse:
        """Save a chat message to DB with Selective Persistence and Redis Caching."""
        user_state = getattr(request.state, "user", {})
        user_id = user_state.get("id")

        res = await chat_service.persist_message(
            db_session=db_session,
            session_id=session_id,
            user_id=user_id,
            role=data.role,
            content=data.content,
            modality=data.modality
        )
        await db_session.commit()
        return res


    @get(
        "/sessions/{session_id:str}/messages",
        summary="Fetch raw chat logs with Cursor Pagination (Zalo Standard)",
        middleware=[chat_sync_limit.middleware]
    )
    async def get_chat_history(
        self,
        db_session: "AsyncSession",
        session_id: str,
        request: Request,
        cursor: Optional[str] = None,
        limit: int = 20,
        user_id_query: Optional[str] = None,
        since_id: Optional[str] = None
    ) -> ChatHistoryResponse:
        """Retrieves messages for a session or user using Hybrid Redis/DB strategy."""
        user_state = getattr(request.state, "user", {})
        return await chat_service.get_history(
            db_session=db_session,
            session_id=session_id,
            user_id=user_state.get("id"),
            roles=user_state.get("roles", []),
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
    async def delete_chat_history(
        self,
        db_session: "AsyncSession",
        session_id: str,
        request: Request,
        user_id_query: Optional[str] = None
    ) -> SuccessResponse:
        """Hard deletes all messages for a session or account."""
        user_state = getattr(request.state, "user", {})
        res = await chat_service.clear_history(
            db_session=db_session,
            session_id=session_id,
            user_id=user_state.get("id"),
            user_email=user_state.get("sub"),
            roles=user_state.get("roles", []),
            user_id_query=user_id_query
        )
        await db_session.commit()
        return res
