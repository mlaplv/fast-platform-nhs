from typing import Optional, List, Dict, Union
import logging
import uuid
from datetime import datetime, timezone
from litestar import Controller, get, post, delete, Request
from litestar.exceptions import NotFoundException, HTTPException
from litestar.middleware.rate_limit import RateLimitConfig
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sqlalchemy_delete, func

from backend.services.user_service import user_service
from backend.database.models import User, ChatMessage
from backend.schemas.chat import ChatHistoryResponse, ChatMessageSchema, CreateChatMessageRequest
from backend.schemas.signal import SignalSchema, SignalSeverity
from backend.services.signal_center import signal_center

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

        from backend.services.chat_service import chat_service
        msg_id = await chat_service.save_message(
            session=db_session,
            session_id=session_id,
            role=data.role,
            content=data.content,
            user_id=user_id,
            modality=data.modality or "text"
        )

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
        user_id_query: Optional[str] = None,  # New: Target user for God-Mode
        since_id: Optional[str] = None        # R82.35: Delta Polling support
    ) -> ChatHistoryResponse:
        """
        Retrieves messages for a session or user using Hybrid Redis/DB strategy.
        If session_id is 'account', it fetches by authenticated user_id.
        """
        user_state = getattr(request.state, "user", {})
        user_id = user_state.get("id")
        user_roles = user_state.get("roles", [])
        is_super_admin = "SUPER_ADMIN" in user_roles
        
        target_user_id = user_id
        
        # ═══ GOD-MODE: ADMIN OVERRIDE ═══
        if is_super_admin and user_id_query:
            target_user_id = user_id_query
            # R1.13: GHOST AUDIT — emit background event, don't block response
            from backend.services.event_bus import event_bus
            await event_bus.emit("SECURITY_AUDIT", {
                "user_id": user_id,
                "type": "SECURITY",
                "message": f"GOD-MODE ACCESS: System logs for user_id '{user_id_query}' accessed by {user_state.get('sub')}"
            })

        # ═══ CACHE BYPASS / REDIS CHECK ═══
        from backend.services.xohi_memory import xohi_memory
        if session_id == "account" and not cursor and limit <= 10 and target_user_id:
            cached = await xohi_memory.get_recent_chat(target_user_id)
            if cached:
                return ChatHistoryResponse(
                    session_id=session_id,
                    has_more=True, # Conservatively assume more exists in DB
                    next_cursor=str(cached[-1]["id"]),
                    messages=[ChatMessageSchema(**m) for m in reversed(cached)] # Redis is LPUSH (newest first)
                )

        # ═══ OWNERSHIP ENFORCEMENT ═══
        if not is_super_admin and session_id != "account" and target_user_id:
            # R1.5: Zero-Hydration — only select the user_id column
            stmt = select(ChatMessage.user_id).where(ChatMessage.session_id == session_id).limit(1)
            res = await db_session.execute(stmt)
            owner_id = res.scalar()
            if owner_id and str(owner_id) != target_user_id:
                raise HTTPException(status_code=403, detail="[SECURITY] Access Denied: Identity mismatch.")
        
        # ═══ DB QUERY: SCALAR PROJECTION (V56.0) ═══
        # We select specific columns to avoid hydrating full ORM objects (Rule 1.5)
        from sqlalchemy import text
        cols = [
            ChatMessage.id, ChatMessage.session_id, ChatMessage.user_id,
            ChatMessage.role, ChatMessage.content, ChatMessage.modality,
            ChatMessage.created_at
        ]
        stmt = select(*cols).where(ChatMessage.deleted_at == None)
        
        if session_id == "account" and target_user_id:
            stmt = stmt.where(ChatMessage.user_id == target_user_id)
        else:
            stmt = stmt.where(ChatMessage.session_id == session_id)

        # Cursor Pagination (Older messages)
        if cursor:
            cursor_stmt = select(ChatMessage.created_at).where(ChatMessage.id == cursor)
            cursor_res = await db_session.execute(cursor_stmt)
            cursor_time = cursor_res.scalar()
            if cursor_time:
                stmt = stmt.where(ChatMessage.created_at < cursor_time)
        
        # Delta Polling (Newer messages)
        if since_id:
            since_stmt = select(ChatMessage.created_at).where(ChatMessage.id == since_id)
            since_res = await db_session.execute(since_stmt)
            since_time = since_res.scalar()
            if since_time:
                stmt = stmt.where(ChatMessage.created_at > since_time)
                # When delta polling, we want newest messages first to fill the gap
                stmt = stmt.order_by(ChatMessage.created_at.asc())
            else:
                stmt = stmt.order_by(ChatMessage.created_at.desc())
        else:
            stmt = stmt.order_by(ChatMessage.created_at.desc())
        
        res = await db_session.execute(stmt)
        # Results are tuples of columns
        rows = res.all()
        
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]
        
        messages = []
        for r in rows:
            messages.append(ChatMessageSchema(
                id=str(r.id),
                session_id=r.session_id,
                user_id=str(r.user_id) if r.user_id else None,
                role=r.role,
                content=r.content,
                modality=r.modality,
                created_at=r.created_at,
                updated_at=r.created_at
            ))
            
        next_cursor = str(messages[-1].id) if messages and not since_id else None
        
        # If we were delta polling (ASC), we already have the correct order for appending to the top
        # if not, we reverse to maintain chronological order for the frontend
        if not since_id:
            messages.reverse() 

        return ChatHistoryResponse(
            session_id=session_id,
            has_more=has_more,
            next_cursor=next_cursor,
            messages=messages
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

        user = await user_service.get_user_by_email(db_session, user_email)
        user_id = str(user.id) if user else None

        # CNS V70: Security audit signal — CRITICAL        # Signal Dispatch (Audit Trail - Rule R00/R1.13)
        await signal_center.dispatch(
            user_id=str(user_id) if user_id else "system",
            signal=SignalSchema(
                message=f"SUCCESS: Chat history cleaned for session '{session_id}' by {user_email}",
                severity=SignalSeverity.INFO,
                signal_type="SECURITY"
            ),
            db_session=db_session
        )

        if session_id == "account" and user_id:
            stmt = sqlalchemy_delete(ChatMessage).where(ChatMessage.user_id == user_id)
        else:
            stmt = sqlalchemy_delete(ChatMessage).where(ChatMessage.session_id == session_id)
            
        await db_session.execute(stmt)
        await db_session.commit()
            
        return {"status": "success", "message": f"All logs for {session_id} have been purged."}
