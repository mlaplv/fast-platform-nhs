import logging
import json
import asyncio
from typing import Optional

logger = logging.getLogger("vector_memory")

# V56.0: Use shared encoder singleton (merges 3 instances → 1)
from ai_engine.core.encoder_singleton import get_shared_encoder


def get_encoder():
    """Compatibility wrapper — delegates to shared singleton."""
    return get_shared_encoder()

class VectorMemory:
    """
    RAG Logic Core - Tra cứu trí nhớ và tri thức cửa hàng (R16).
    Hỗ trợ:
    1. Trí nhớ người dùng (Facts)
    2. Tri thức sản phẩm (Products)
    3. Tri thức bài viết/chính sách (Articles)
    """
    
    @staticmethod
    async def search(query_text: str, db_client, context_type: str = "product", limit: int = 3) -> str:
        """
        Tìm kiếm ngữ cảnh liên quan nhất bằng pgvector (Cosine Distance).
        R30: Luôn áp dụng tenant_id từ contextvars.
        """
        try:
            encoder = get_encoder()
            if not encoder:
                return "Hệ thống vector hóa đang bảo trì."
            
            # 1. Vector hóa query
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, lambda: list(encoder.embed([query_text])))
            vector_str = "[" + ",".join(map(str, embeddings[0].tolist())) + "]"
            
            # 2. Lấy tenant_id từ context
            from src.database import current_tenant_id
            tenant = current_tenant_id.get() or "default"
            
            # 3. Phân loại bảng và query
            if context_type == "product":
                sql = f"""
                    SELECT p.name, p.price, e.embedding <=> '{vector_str}'::vector AS dist
                    FROM "product_bases" p
                    JOIN "product_embeddings" e ON p.id = e."productBaseId"
                    WHERE p.tenant_id = $1 AND p.deleted_at IS NULL
                    ORDER BY dist ASC LIMIT {limit}
                """
                results = await db_client.query_raw(sql, tenant)
                if not results: return "Không thấy sản phẩm phù hợp."
                return "\n".join([f"- {r['name']} (Giá: {r['price']})" for r in results])
            
            elif context_type == "article":
                sql = f"""
                    SELECT a.title, a.content, e.embedding <=> '{vector_str}'::vector AS dist
                    FROM "articles" a
                    JOIN "article_embeddings" e ON a.id = e.article_id
                    WHERE a.tenant_id = $1 AND a.deleted_at IS NULL
                    ORDER BY dist ASC LIMIT {limit}
                """
                results = await db_client.query_raw(sql, tenant)
                if not results: return "Không thấy chính sách/tin tức phù hợp."
                # Cắt bớt content nếu quá dài để tiết kiệm token
                return "\n".join([f"### {r['title']}\n{r['content'][:300]}..." for r in results])
            
            else:
                # Mặc định là facts hoặc các loại khác nếu có
                return ""

        except Exception as e:
            logger.error(f"[VectorMemory] Search failed for {context_type}: {e}")
            return f"Lỗi truy xuất tri thức ({context_type})."
