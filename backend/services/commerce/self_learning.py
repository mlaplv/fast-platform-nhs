import logging
import asyncio
from typing import List, Dict, Optional, cast
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.system import SupportKnowledge, SupportChatHistory, SupportKnowledgeCategory, SystemSetting
from backend.services.commerce.knowledge_vector import knowledge_vector_service
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.uid import new_id

logger = logging.getLogger("arq.worker")

class ExtractedKnowledgeItem(BaseModel):
    model_config = ConfigDict(strict=True)
    question: str = Field(..., description="Generalized representative customer question. Must be in Vietnamese.")
    answer: str = Field(..., description="High-quality, helpful, accurate, and structured answer to the question in Vietnamese.")
    category: str = Field(..., description="GENERAL, POLICY, SHIPPING, PRODUCT, PROMO, INFO_INGREDIENTS, INFO_ADDRESS, INFO_HOTLINE, PRICE_QUERY, INFO_SHIPPING")
    reasoning: str = Field(..., description="Brief rationale explaining why this is a unique and high-quality Q&A worth learning.")

class ExtractedKnowledgeResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    items: List[ExtractedKnowledgeItem] = Field(default_factory=list)

# Specialist Self-Learning Distillation Agent
_learning_agent: Agent[None, ExtractedKnowledgeResponse] = Agent(
    output_type=ExtractedKnowledgeResponse,
    system_prompt=(
        "You are an Elite AI Knowledge Synthesis Officer (Helen Self-Learning Core).\n"
        "Your task is to analyze real chat transcripts between customers and our assistant/operator.\n"
        "Identify high-quality, verified, and valuable Q&A exchanges, general brand policies, or product-specific details.\n"
        "For each identified high-quality exchange, generalize the question so it represents a common user query, "
        "and clean up the answer so it is polite, complete, professional, and structured in Vietnamese.\n"
        "Avoid duplicates, irrelevant chat chatter (like simple 'ok', 'yes', 'no'), or unresolved questions."
    )
)

class HelenSelfLearningService:
    """
    Elite V3.5 Helen AI Self-Learning Pipeline.
    Closed-loop knowledge discovery, deduplication, and sandbox curation system.
    """

    async def run_auto_learning(self, db: AsyncSession, limit_sessions: int = 50) -> Dict[str, int]:
        """
        Scans recent chat history, synthesizes new candidate Q&As,
        runs pgvector similarity deduplication, and persists them into the review sandbox.
        """
        logger.info("🧪 [Helen Self-Learning] Starting automated learning run...")
        
        # 1. Fetch recent successful sessions from chat history
        # We group by session_id, and look for sessions with at least one user message
        stmt = (
            select(SupportChatHistory)
            .where(SupportChatHistory.deleted_at.is_(None))
            .order_by(SupportChatHistory.session_id, SupportChatHistory.created_at.asc())
        )
        res = await db.execute(stmt)
        all_messages = res.scalars().all()
        
        # Group messages by session_id
        session_groups: Dict[str, List[SupportChatHistory]] = {}
        for m in all_messages:
            session_groups.setdefault(m.session_id, []).append(m)
            
        logger.info(f"🧪 [Helen Self-Learning] Loaded {len(session_groups)} chat sessions for analysis.")
        
        # Filter sessions to analyze (e.g., limit_sessions, with > 3 messages)
        active_sessions = [
            (sid, msgs) for sid, msgs in session_groups.items()
            if len(msgs) >= 3 and any(m.role == "user" for m in msgs)
        ][:limit_sessions]
        
        if not active_sessions:
            logger.info("🧪 [Helen Self-Learning] No qualified sessions for learning today.")
            return {"scanned": 0, "synthesized": 0, "persisted_to_sandbox": 0}

        # 2. Load Admin Learning Seed Templates / Guidelines
        # Admin can store seed templates under "system:settings:learning_templates"
        learning_guidelines = ""
        try:
            raw_setting = await db.execute(
                select(SystemSetting).where(SystemSetting.key == "helen_learning_seed_templates")
            )
            setting_row = raw_setting.scalar_one_or_none()
            if setting_row and setting_row.value:
                learning_guidelines = f"\n[ADMIN SEED TEMPLATES & INSTRUCTIONS]:\n{setting_row.value}\n"
        except Exception as e:
            logger.warning(f"🧪 [Helen Self-Learning] Failed to load admin seed templates: {e}")

        scanned_count = 0
        synthesized_count = 0
        persisted_count = 0

        # Process each session transcript
        for session_id, msgs in active_sessions:
            scanned_count += 1
            
            # Reconstruct transcript
            transcript_lines = []
            product_slug = None
            customer_name = "Khách hàng"
            
            session_tenant = msgs[0].tenant_id if msgs else "default"
            
            for m in msgs:
                role_label = "Customer" if m.role == "user" else "Helen (Assistant)"
                transcript_lines.append(f"{role_label}: {m.content}")
                if m.product_slug:
                    product_slug = m.product_slug
                if m.customer_name and m.customer_name != "Khách ẩn danh":
                    customer_name = m.customer_name
                    
            transcript = "\n".join(transcript_lines)
            
            # Call AI Distillation Agent via Trinity Bridge
            prompt = (
                f"{learning_guidelines}\n"
                f"[CHAT TRANSCRIPT | Session ID: {session_id} | Product Slug: {product_slug or 'N/A'}]\n"
                f"Customer Name: {customer_name}\n"
                f"----------------------------------------\n"
                f"{transcript}\n"
                f"----------------------------------------\n"
                f"Extract unique, verified, and structured Q&As from this conversation."
            )
            
            try:
                ai_res = await trinity_bridge.run(
                    agent=_learning_agent,
                    prompt=prompt,
                    role="brain",
                    safety_none=True,
                    timeout=15.0
                )
                
                res_data = cast(Optional[ExtractedKnowledgeResponse], ai_res)
                if not res_data or not res_data.items:
                    continue
                    
                for item in res_data.items:
                    synthesized_count += 1
                    
                    # 3. Deduplication Check (pgvector Hybrid Scan)
                    # We check if a highly similar question/answer exists in our DB already
                    similar_matches = await knowledge_vector_service.search_semantic(
                        db_session=db,
                        query=item.question,
                        tenant_id=session_tenant,
                        limit=1
                    )
                    
                    # If similarity score exceeds 0.88, we consider it a duplicate and skip to avoid clutter!
                    if similar_matches and similar_matches[0]["match_score"] > 0.88:
                        logger.info(
                            f"🧪 [Self-Learning Deduplication] Skipped item due to high similarity "
                            f"({similar_matches[0]['match_score']}): '{item.question}'"
                        )
                        continue
                        
                    # 4. Sandbox Curation (Persist with is_active=False for Admin review)
                    cat_val = SupportKnowledgeCategory.GENERAL
                    try:
                        cat_val = SupportKnowledgeCategory(item.category)
                    except ValueError:
                        pass
                        
                    new_knowledge = SupportKnowledge(
                        id=new_id(),
                        category=cat_val,
                        question=item.question.strip(),
                        answer=item.answer.strip(),
                        is_active=False, # 🛡️ Sandboxed! Admin must review and approve first.
                        source_type="AUTO_LEARNED",
                        source_url=f"chat_session:{session_id}",
                        tags={
                            "source": "self_learning",
                            "status": "PENDING_REVIEW",
                            "reasoning": item.reasoning,
                            "session_id": session_id,
                            "product_slug": product_slug
                        },
                        priority=0,
                        tenant_id=session_tenant
                    )
                    
                    db.add(new_knowledge)
                    persisted_count += 1
                    logger.info(f"✨ [Self-Learning Sandbox] Synthesized new candidate Q&A: '{item.question[:60]}...' (Session: {session_id})")
                    
                # Commit after processing each session to maintain database transaction safety
                await db.commit()
                
            except Exception as ex:
                logger.error(f"❌ [Helen Self-Learning] Failed to process session {session_id}: {ex}")
                await db.rollback()

        return {
            "scanned": scanned_count,
            "synthesized": synthesized_count,
            "persisted_to_sandbox": persisted_count
        }

    async def approve_sandbox_item(self, db: AsyncSession, knowledge_id: str) -> bool:
        """
        Admin action to approve a sandboxed auto-learned item.
        Sets is_active=True, updates tags status, and programmatically trigger pgvector re-indexing.
        """
        stmt = select(SupportKnowledge).where(
            and_(
                SupportKnowledge.id == knowledge_id,
                SupportKnowledge.deleted_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        item = res.scalar_one_or_none()
        
        if not item:
            logger.warning(f"❌ [Self-Learning Approve] Item {knowledge_id} not found.")
            return False
            
        item.is_active = True
        
        # Update metadata tags
        tags = dict(item.tags or {})
        tags["status"] = "APPROVED"
        item.tags = tags
        
        # Save to database
        db.add(item)
        await db.flush()
        
        # Trigger atomic vector upsert to make it instantly active in fast-path semantic search
        logger.info(f"⚡ [Self-Learning Approve] Generating pgvector embeddings for approved item: {knowledge_id}")
        await knowledge_vector_service.upsert_embedding(
            db_session=db,
            knowledge_id=item.id,
            content=f"{item.question} {item.answer}",
            tenant_id=item.tenant_id or "default"
        )
        
        await db.commit()
        logger.info(f"✅ [Self-Learning Approve] Item {knowledge_id} approved and indexed successfully.")
        return True

    async def reject_sandbox_item(self, db: AsyncSession, knowledge_id: str) -> bool:
        """
        Admin action to decline/reject a sandboxed item.
        Marks the item as deleted to clear it from sandbox review.
        """
        from datetime import datetime, timezone
        stmt = select(SupportKnowledge).where(
            and_(
                SupportKnowledge.id == knowledge_id,
                SupportKnowledge.deleted_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        item = res.scalar_one_or_none()
        
        if not item:
            return False
            
        item.deleted_at = datetime.now(timezone.utc)
        tags = dict(item.tags or {})
        tags["status"] = "REJECTED"
        item.tags = tags
        
        db.add(item)
        await db.commit()
        logger.info(f"❌ [Self-Learning Reject] Item {knowledge_id} rejected and soft-deleted.")
        return True

helen_self_learning = HelenSelfLearningService()
