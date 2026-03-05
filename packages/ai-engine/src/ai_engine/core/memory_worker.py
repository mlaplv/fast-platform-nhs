# packages/ai-engine/src/ai_engine/core/memory_worker.py
try:
    from fastembed import TextEmbedding
    encoder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
except ImportError:
    encoder = None
from ai_engine.core.nanobot import NanoBot
import logging
import asyncio

logger = logging.getLogger("memory-worker")

class MemoryWorker:
    """
    Tier 2 Memory: Episodic & Semantic Summarization.
    Extracts facts from chat logs and saves to Long-term Memory (pgvector).
    Filters out "noise" words like "À, ừm, gõ nhầm" (Test Case 3).
    """
    def __init__(self, db_client=None):
        self.bot = NanoBot()
        self.db = db_client

    async def summarize_and_store(self, session_id: str, raw_messages: list):
        """
        Background Task: Extract facts and store in Vector DB.
        Runs asynchronously to avoid blocking the main API response.
        """
        if not raw_messages or not self.db:
            return

        try:
            # 1. Clean up noise (À, ừm, etc.) and extract meaningful facts
            text_to_analyze = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in raw_messages])
            
            prompt = (
                "Hãy đóng vai chuyên gia tóm tắt. "
                "Bỏ qua các từ đệm, rác vô nghĩa (À, ừm, gõ nhầm, trời đẹp...). "
                "CHỈ TRÍCH XUẤT các 'SỰ THẬT' (Facts) về sở hữu, sở thích, hoặc ý định của khách hàng. "
                "Ví dụ: 'Khách hàng thích mai vàng dáng trực, ngân sách < 10 triệu'. "
                "Nếu không có thông tin quan trọng, hãy trả về rỗng. "
                f"\n\nNội dung: {text_to_analyze}"
            )
            
            from litellm import acompletion
            import os
            
            response = await acompletion(
                model=self.bot.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            
            # Safe parsing (Director's Audit Resilience)
            if hasattr(response, "choices") and len(response.choices) > 0:
                fact = response.choices[0].message.content.strip()
            else:
                # Fallback for unexpected response structures
                fact = str(getattr(response, "content", response)).strip()
            
            if fact and len(fact) > 5:
                logger.info(f"[MemoryWorker] Extracted Fact: {fact}")
                
                # 2. Store in Long-term Memory (Vector DB)
                if not encoder:
                    logger.warning("[MemoryWorker] Encoder missing. Storing text only.")
                    vector = [0.0] * 384
                else:
                    embeddings = list(encoder.embed([fact]))
                    vector = embeddings[0].tolist() if embeddings else ([0.0] * 384)
                
                sql = """
                    INSERT INTO "ProductEmbedding" (id, content, embedding, metadata, "tenantId")
                    VALUES ($1, $2, $3::vector, $4, $5)
                """
                # Using a generic UUID and metadata for the demo
                import uuid
                await self.db.execute(
                    query=sql, 
                    values=[
                        str(uuid.uuid4()), 
                        fact, 
                        str(vector), 
                        '{"source": "episodic_memory"}',
                        'default'
                    ]
                )
        except Exception as e:
            logger.error(f"[MemoryWorker] Summarization failed: {e}")
