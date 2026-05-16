import logging
import re
import json
from typing import List, Dict
from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

async def suggest_seo_logic(name: str, description: str) -> Dict[str, str]:
    """Elite V2.2: AI SEO Suggestion Logic (Isolated)."""
    agent = Agent(
        system_prompt=(
            "Bạn là chuyên gia SEO hàng đầu Việt Nam. Hãy tối ưu tiêu đề, mô tả và từ khóa SEO cho sản phẩm này. "
            "QUY TẮC TỐI CAO: Dù tên sản phẩm hoặc mô tả đầu vào là tiếng Anh, bạn BẮT BUỘC phải phản hồi nội dung hoàn toàn bằng tiếng Việt thuần 100%. "
            "Nội dung phải súc tích, hấp dẫn và chuẩn SEO. "
            "Chỉ trả về JSON hợp lệ, không có markdown: "
            "{\"title\": \"...\", \"description\": \"...\", \"keywords\": \"...\"}"
        )
    )
    prompt = f"Tên sản phẩm: {name}\nMô tả: {description}"
    
    try:
        result = await trinity_bridge.run(
            agent=agent,
            prompt=prompt,
            role="fast",
            timeout=30.0
        )
        
        if result:
            suggested_json_str = str(getattr(result, "data", getattr(result, "output", result))).strip()
            match = re.search(r'\{.*\}', suggested_json_str, re.DOTALL)
            parsed = json.loads(match.group(0)) if match else {"title": "", "description": "", "keywords": ""}
            return parsed
        
        return {"title": f"{name} Chính Hãng", "description": "Sản phẩm chính hãng", "keywords": ""}
        
    except Exception as e:
        logger.exception(f"[ProductAI] AI SEO Suggestion Failed: {e}")
        return {"title": f"{name} Chính Hãng", "description": "Mua sản phẩm chính hãng với nhiều ưu đãi", "keywords": ""}

async def suggest_faqs_logic(name: str, description: str) -> List[Dict[str, str]]:
    """Elite V2.2: XOHI Auto FAQ Generator Logic (Isolated)."""
    agent = Agent(
        system_prompt=(
            "Bạn là chuyên gia tư vấn sản phẩm. Dựa trên tên và mô tả sản phẩm, hãy tạo từ 3 đến 5 câu hỏi thường gặp và câu trả lời ngắn gọn, hữu ích bằng tiếng Việt. "
            "QUY TẮC TỐI CAO: Dù tên sản phẩm đầu vào là tiếng Anh, toàn bộ câu hỏi và câu trả lời phải là tiếng Việt thuần 100%. "
            "Chỉ trả về mảng JSON chính xác các đối tượng, không có markdown: "
            "[{\"question\": \"...\", \"answer\": \"...\"}]"
        )
    )
    prompt = f"Tên sản phẩm: {name}\nMô tả: {description}"

    try:
        result = await trinity_bridge.run(
            agent=agent,
            prompt=prompt,
            role="fast",
            timeout=45.0
        )

        if result:
            suggested_json_str = str(getattr(result, "data", getattr(result, "output", result))).strip()
            match = re.search(r'\[.*\]', suggested_json_str, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list):
                    return parsed

        return []

    except Exception as e:
        logger.exception(f"[ProductAI] AI FAQ Suggestion Failed: {e}")
        return []
