from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.database.models.system import SupportKnowledge, SupportKnowledgeCategory
from backend.database.repositories import SupportKnowledgeRepository
from backend.schemas.support import (
    CreateSupportKnowledgeRequest, 
    UpdateSupportKnowledgeRequest, 
    SupportKnowledgeResponse, 
    SupportKnowledgeListResponse,
    BulkDeleteRequest,
    BulkToggleRequest
)
from backend.schemas.common import SuccessResponse

logger = logging.getLogger("api-gateway")

class SupportKnowledgeService:
    """Elite V2.2: Business Logic for Support Knowledge Base (RAG)."""

    def __init__(self, repo: SupportKnowledgeRepository):
        self.repo = repo

    async def list_knowledge(
        self,
        db_session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        category: Optional[SupportKnowledgeCategory] = None,
        search: Optional[str] = None,
    ) -> SupportKnowledgeListResponse:
        """List knowledge entries with filtering."""
        conditions = [SupportKnowledge.deleted_at == None]
        
        if category:
            conditions.append(SupportKnowledge.category == category)
            
        if search:
            # Simple keyword search for now (Elite V2.2)
            # In Phase 2, this can be upgraded to Vector Search
            conditions.append(or_(
                SupportKnowledge.question.ilike(f"%{search}%"),
                SupportKnowledge.answer.ilike(f"%{search}%")
            ))

        stmt = select(SupportKnowledge).where(and_(*conditions)).limit(limit).offset(offset).order_by(SupportKnowledge.priority.desc(), SupportKnowledge.created_at.desc())
        
        result = await db_session.execute(stmt)
        items = result.scalars().all()
        
        # Count total
        count_stmt = select(func.count(SupportKnowledge.id)).where(and_(*conditions))
        total = await db_session.scalar(count_stmt) or 0
        
        data = [
            SupportKnowledgeResponse(
                id=m.id,
                category=m.category,
                question=m.question,
                answer=m.answer,
                is_active=m.is_active,
                priority=m.priority,
                tags=list(m.tags) if m.tags else None,
                created_at=m.created_at.isoformat()
            ) for m in items
        ]
        
        return SupportKnowledgeListResponse(data=data, total=total)

    async def get_knowledge(self, db_session: AsyncSession, item_id: str) -> SupportKnowledgeResponse:
        item = await self.repo.get_one_or_none(id=item_id)
        if not item or item.deleted_at:
            raise NotFoundException(f"Knowledge item {item_id} not found")
            
        return SupportKnowledgeResponse(
            id=item.id,
            category=item.category,
            question=item.question,
            answer=item.answer,
            is_active=item.is_active,
            priority=item.priority,
            tags=list(item.tags) if item.tags else None,
            created_at=item.created_at.isoformat()
        )

    async def create_knowledge(self, db_session: AsyncSession, data: CreateSupportKnowledgeRequest) -> SuccessResponse:
        new_id = str(uuid.uuid4())
        item = SupportKnowledge(
            id=new_id,
            category=data.category,
            question=data.question,
            answer=data.answer,
            is_active=data.is_active,
            priority=data.priority,
            tags=data.tags
        )
        db_session.add(item)
        from backend.services.xohi_memory import xohi_memory
        await xohi_memory.clear_kb_cache()
        return SuccessResponse(ok=True, id=new_id)

    async def update_knowledge(self, db_session: AsyncSession, item_id: str, data: UpdateSupportKnowledgeRequest) -> SuccessResponse:
        item = await self.repo.get_one_or_none(id=item_id)
        if not item or item.deleted_at:
            raise NotFoundException(f"Knowledge item {item_id} not found")
            
        if data.category is not None: item.category = data.category
        if data.question is not None: item.question = data.question
        if data.answer is not None: item.answer = data.answer
        if data.tags is not None: item.tags = data.tags
        
        from backend.services.xohi_memory import xohi_memory
        await xohi_memory.clear_kb_cache()
        return SuccessResponse(ok=True, id=item_id)

    async def delete_knowledge(self, db_session: AsyncSession, item_id: str) -> SuccessResponse:
        item = await self.repo.get_one_or_none(id=item_id)
        if not item:
            raise NotFoundException(f"Knowledge item {item_id} not found")
            
        item.deleted_at = datetime.now(timezone.utc)
        from backend.services.xohi_memory import xohi_memory
        await xohi_memory.clear_kb_cache()
        return SuccessResponse(ok=True, id=item_id)

    async def bulk_delete(self, db_session: AsyncSession, data: BulkDeleteRequest) -> SuccessResponse:
        """Elite V2.2: Large-scale neural purge (Bulk Delete)."""
        stmt = sa.update(SupportKnowledge).where(SupportKnowledge.id.in_(data.ids)).values(deleted_at=datetime.now(timezone.utc))
        await db_session.execute(stmt)
        from backend.services.xohi_memory import xohi_memory
        await xohi_memory.clear_kb_cache()
        return SuccessResponse(ok=True)

    async def bulk_toggle_active(self, db_session: AsyncSession, data: BulkToggleRequest) -> SuccessResponse:
        """Elite V2.2: Neural Toggle (Bulk On/Off)."""
        stmt = sa.update(SupportKnowledge).where(SupportKnowledge.id.in_(data.ids)).values(is_active=data.is_active)
        await db_session.execute(stmt)
        from backend.services.xohi_memory import xohi_memory
        await xohi_memory.clear_kb_cache()
        return SuccessResponse(ok=True)

    # ══════════════════════════════════════════════════════════════
    # THREE-LAYER MEMORY ARCHITECTURE (V2.2 Standard)
    # ══════════════════════════════════════════════════════════════
    
    async def get_knowledge_index(self, db_session: AsyncSession) -> str:
        """Layer 1: Index (Short Pointers/Index). Summaries < 150 chars."""
        # R112: Neural Cache Layer (Redis)
        from backend.services.xohi_memory import xohi_memory
        
        cached = await xohi_memory.get_kb_layer1()
        if cached:
            return cached

        stmt = select(SupportKnowledge.id, SupportKnowledge.category, SupportKnowledge.question).where(
            and_(
                SupportKnowledge.deleted_at == None,
                SupportKnowledge.is_active == True
            )
        ).order_by(SupportKnowledge.priority.desc())
        
        result = await db_session.execute(stmt)
        items = result.all()
        
        if not items:
            return "Helen chưa có kiến thức nào trong mục lục."
            
        index_lines = ["[MỤC LỤC KIẾN THỨC GIẢI MÃ - LAYER 1]"]
        for row in items:
            # Question acts as the summary if it's short, else truncates
            summary = (row.question[:147] + "...") if len(row.question) > 150 else row.question
            index_lines.append(f"- ID: {row.id} | Phân loại: {row.category} | ND: {summary}")
        
        final_index = "\n".join(index_lines)
        
        # Set cache with 1h TTL (Elite V2. Standard)
        await xohi_memory.set_kb_layer1(final_index, ttl=3600)
            
        return final_index


    async def get_topic_details(self, db_session: AsyncSession, topic_id: str) -> str:
        """Layer 2: Topic Files (Detailed Subject Matter). Fetch on-demand."""
        item = await self.repo.get_one_or_none(id=topic_id)
        if not item or item.deleted_at or not item.is_active:
            return f"Không tìm thấy thông tin chi tiết cho ID: {topic_id}"
            
        return (
            f"[CHI TIẾT CHỦ ĐỀ - LAYER 2: {topic_id}]\n"
            f"Câu hỏi/Trường hợp: {item.question}\n"
            f"Phản hồi chuyên môn: {item.answer}\n"
            "---"
        )

    async def search_relevant_knowledge(self, db_session: AsyncSession, query: str, limit: int = 5) -> str:
        """
        RAG Core: Flexible keyword matching for support knowledge.
        Splits prompts by comma/newline to match against user query.
        """
        # Fetch only active, non-deleted entries
        stmt = select(SupportKnowledge.question, SupportKnowledge.answer).where(
            and_(
                SupportKnowledge.deleted_at == None,
                SupportKnowledge.is_active == True
            )
        ).order_by(SupportKnowledge.priority.desc())
        
        result = await db_session.execute(stmt)
        all_items = result.all()
        
        if not all_items:
            return ""
            
        matches = []
        q_lower = query.lower()
        
        for q_text, a_text in all_items:
            # Split triggers by comma, semicolon or newline (Elite V2.2)
            import re
            triggers = re.split(r'[,;\n]+', q_text.lower())
            triggers = [t.strip() for t in triggers if t.strip()]
            
            # Check if any trigger is contained in the query
            # OR if the query is contained in the whole prompt
            found = False
            if q_text.lower() in q_lower:
                found = True
            else:
                for t in triggers:
                    if t in q_lower:
                        found = True
                        break
            
            if found:
                matches.append((q_text, a_text))
                if len(matches) >= limit:
                    break
        
        if not matches:
            return ""
            
        context = "[THÔNG TIN TRÍ THỨC HỆ THỐNG PHÊ DUYỆT]\n"
        for q, a in matches:
            context += f"Q: {q}\nA: {a}\n---\n"
        return context

# ==========================================
# SERVICE PROVIDERS
# ==========================================

async def provide_support_kb_service(kb_repo: SupportKnowledgeRepository) -> SupportKnowledgeService:
    return SupportKnowledgeService(repo=kb_repo)
