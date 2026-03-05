from typing import Optional, List, Dict, Union
import logging
import uuid
from datetime import datetime, timezone
from litestar import Controller, get, post, delete, Request
from litestar.exceptions import NotFoundException, HTTPException
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sqlalchemy_delete, func

from src.database.repositories import UserRepository
from src.database.models import User, ChatMessage, Notification
from src.schemas.chat import ChatHistoryResponse, ChatMessageSchema, CreateChatMessageRequest

logger = logging.getLogger("api-gateway")

# Security Rate Limits
chat_sync_limit = RateLimitConfig(rate_limit=("minute", 30), store="memory_store")
chat_clear_limit = RateLimitConfig(rate_limit=("minute", 10), store="memory_store")


class ChatController(Controller):
    path = "/api/v1/chat"

    @post(
        "/sessions/{session_id:str}/messages",
        status_code=201,
        summary="Persist a single chat message from frontend",
        middleware=[chat_sync_limit.middleware]
    )
    async def save_message(self, db_session: AsyncSession, session_id: str, request: Request, data: CreateChatMessageRequest) -> dict:
        """Save a chat message to DB. Used by frontend for widget shortcuts and local commands."""
        user_state = getattr(request.state, "user", {})
        user_email = user_state.get("sub")

        user_id = None
        if user_email:
            user_repo = UserRepository(session=db_session)
            user = await user_repo.get_one_or_none(email=user_email)
            if user:
                user_id = str(user.id)

        if data.role not in ("user", "assistant"):
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'user' or 'assistant'.")

        try:
            msg_id = str(uuid.uuid4())
            msg = ChatMessage(
                id=msg_id,
                session_id=session_id,
                user_id=user_id,
                role=data.role,
                content=data.content,
                modality=data.modality or "text"
            )
            db_session.add(msg)
            await db_session.commit()
            return {"status": "success", "id": msg_id}
        except Exception as e:
            logger.error(f"[ChatMessage] POST save failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to persist message.")


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
        user_id_query: Optional[str] = None  # New: Target user for God-Mode
    ) -> ChatHistoryResponse:
        """
        Retrieves messages for a session or user using Cursor Pagination.
        If session_id is 'account', it fetches by authenticated user_id.
        """
        user_state = getattr(request.state, "user", {})
        user_email = user_state.get("sub")
        user_roles = user_state.get("roles", [])
        is_super_admin = "SUPER_ADMIN" in user_roles
        
        user_repo = UserRepository(session=db_session)
        current_user = None
        if user_email:
            current_user = await user_repo.get_one_or_none(email=user_email)
        
        target_user_id = str(current_user.id) if current_user else None
        
        # ═══ GOD-MODE: ADMIN OVERRIDE ═══
        if is_super_admin and user_id_query:
            target_user_id = user_id_query
            # Audit log for God-Mode access
            new_notif = Notification(
                id=str(uuid.uuid4()), # RSR: Satisfy NotNull for ID
                user_id=str(current_user.id) if current_user else None,
                type="SECURITY",
                message=f"GOD-MODE ACCESS: System logs for user_id '{user_id_query}' accessed by {user_email}"
            )
            db_session.add(new_notif)
            # We don't explicit commit here to avoid MissingGreenlet if IO is pending elsewhere
            await db_session.flush()

        # ═══ SECURITY: OWNERSHIP ENFORCEMENT ═══
        if not is_super_admin and session_id != "account":
            stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).limit(1)
            res = await db_session.execute(stmt)
            first_msg = res.scalar_one_or_none()
            if first_msg and first_msg.user_id and str(first_msg.user_id) != target_user_id:
                raise HTTPException(status_code=403, detail="[SECURITY] Access Denied: Identity mismatch for requested session.")
        
        # Build Query
        stmt = select(ChatMessage).where(ChatMessage.deleted_at == None)
        if session_id == "account" and target_user_id:
            stmt = stmt.where(ChatMessage.user_id == target_user_id)
        else:
            stmt = stmt.where(ChatMessage.session_id == session_id)

        # Cursor Pagination Logic
        if cursor:
            cursor_stmt = select(ChatMessage.created_at).where(ChatMessage.id == cursor)
            cursor_res = await db_session.execute(cursor_stmt)
            cursor_time = cursor_res.scalar_one_or_none()
            if cursor_time:
                stmt = stmt.where(ChatMessage.created_at < cursor_time)

        stmt = stmt.order_by(ChatMessage.created_at.desc()).limit(limit + 1)
        
        res = await db_session.execute(stmt)
        messages = list(res.scalars().all())
        
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]
        
        next_cursor = str(messages[-1].id) if messages else None
        messages.reverse() 

        return ChatHistoryResponse(
            session_id=session_id,
            has_more=has_more,
            next_cursor=next_cursor,
            messages=[
                ChatMessageSchema(
                    id=str(m.id),
                    session_id=m.session_id,
                    user_id=str(m.user_id) if m.user_id else None,
                    role=m.role,
                    content=m.content,
                    modality=m.modality,
                    created_at=m.created_at,
                    updated_at=getattr(m, 'updated_at', m.created_at)
                ) for m in messages
            ]
        )
    
    @delete(
        "/sessions/{session_id:str}/messages", 
        status_code=200, 
        summary="Permanently CLEAR all chat logs for a session",
        middleware=[chat_clear_limit.middleware]
    )
    async def delete_chat_history(self, db_session: AsyncSession, session_id: str, request: Request) -> dict:
        """Hard deletes all messages for a session or account."""
        user_state = getattr(request.state, "user", {})
        user_email = user_state.get("sub")
        user_roles = user_state.get("roles", [])
        
        # ═══ SECURITY: ROLE ENFORCEMENT ═══
        if "SUPER_ADMIN" not in user_roles:
            raise HTTPException(status_code=403, detail="[SECURITY] Unauthorized: Only SUPER_ADMIN can purge system logs.")

        user_repo = UserRepository(session=db_session)
        user = await user_repo.get_one_or_none(email=user_email)
        user_id = str(user.id) if user else None
        
        # ═══ SECURITY: DESTRUCTION AUDIT ═══
        new_notif = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type="SECURITY",
            message=f"DATA DESTRUCTION: Logs purged for session '{session_id}' by {user_email}"
        )
        db_session.add(new_notif)
        await db_session.flush()

        if session_id == "account" and user_id:
            stmt = sqlalchemy_delete(ChatMessage).where(ChatMessage.user_id == user_id)
        else:
            stmt = sqlalchemy_delete(ChatMessage).where(ChatMessage.session_id == session_id)
            
        await db_session.execute(stmt)
        await db_session.commit()
            
        return {"status": "success", "message": f"All logs for {session_id} have been purged."}
