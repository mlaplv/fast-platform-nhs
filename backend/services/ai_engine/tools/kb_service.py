import logging
from typing import Optional
from backend.services.xohi_memory import xohi_memory
from backend.database.alchemy_config import alchemy_config
from sqlalchemy import text

logger = logging.getLogger("api-gateway")

class KBService:
    @staticmethod
    async def fetch_topic(topic_id: str) -> str:
        """
        Layer 2 Fetch: Lấy chi tiết một chủ đề kiến thức.
        """
        content = await xohi_memory.get_kb_topic(topic_id)
        if content:
            return f"--- CHỦ ĐỀ: {topic_id} ---\n{content}"
        return f"Không tìm thấy nội dung cho chủ đề '{topic_id}'."

    @staticmethod
    async def fuzzy_search_raw(query: str, limit: int = 3) -> str:
        """
        Layer 3 Search: Tìm kiếm dữ liệu thô từ Database (Raw Transcripts/Articles).
        """
        maker = alchemy_config.create_session_maker()
        try:
            async with maker() as session:
                # [THIẾT QUÂN LUẬT] Phải dùng tham số hóa để chống SQL Injection
                # Tìm kiếm trong articles hoặc chat_messages tùy ngữ cảnh. 
                # Ở đây ta ưu tiên articles (kiến thức cứng).
                result = await session.execute(
                    text("""
                        SELECT title, content 
                        FROM articles 
                        WHERE (title ILIKE :q OR content ILIKE :q)
                        AND deleted_at IS NULL
                        LIMIT :limit
                    """),
                    {"q": f"%{query}%", "limit": limit}
                )
                rows = result.fetchall()
                if not rows:
                    return f"Không tìm thấy dữ liệu thô liên quan đến '{query}'."
                
                output = [f"--- KẾT QUẢ THÔ CHO '{query}' ---"]
                for r in rows:
                    # Chỉ lấy 300 ký tự đầu của mỗi kết quả để bảo vệ RAM
                    snippet = (r[1][:297] + "...") if len(r[1]) > 300 else r[1]
                    output.append(f"Tiêu đề: {r[0]}\nNội dung: {snippet}")
                
                return "\n\n".join(output)
        except Exception as e:
            logger.error(f"[KBService] Raw search failed: {e}")
            return "Lỗi khi truy xuất dữ liệu thô."

kb_service = KBService()
