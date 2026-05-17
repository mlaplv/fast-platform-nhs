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

async def suggest_ingredients_logic(name: str, ingredients: str) -> List[Dict[str, str]]:
    """Elite V2.2: XOHI Auto Ingredients Extractor Logic (Isolated)."""
    agent = Agent(
        system_prompt=(
            "Bạn là chuyên gia da liễu và mỹ phẩm hàng đầu. Dựa trên tên sản phẩm và bảng thành phần đầy đủ, "
            "hãy phân tích và trích xuất chính xác đúng 4 thành phần quan trọng nhất, nổi bật nhất của sản phẩm.\n"
            "YÊU CẦU CẤU TRÚC JSON PHẢN HỒI:\n"
            "- 'name': Tên thành phần (ví dụ: 'Hyaluronic Acid', 'Ceramide', 'Chiết xuất rau má', ...)\n"
            "- 'benefit': Công dụng/lợi ích nổi bật, ngắn gọn của thành phần đó trong sản phẩm (dưới 15 từ)\n"
            "- 'icon': Emoji đại diện phù hợp nhất cho thành phần đó theo nội dung (ví dụ: 💧 cho HA, 🧬 cho Ceramide/Collagen, 🌱 cho rau má, 🌿 cho trà xanh, 🛡️ cho Niacinamide, ✨ cho làm sáng, ...)\n"
            "QUY TẮC TỐI CAO: Toàn bộ thông tin tên thành phần, công dụng phải là tiếng Việt thuần 100%.\n"
            "Chỉ trả về mảng JSON chính xác các đối tượng, không có markdown hoặc bất kỳ văn bản nào khác ngoài JSON:\n"
            "[{\"name\": \"...\", \"benefit\": \"...\", \"icon\": \"...\"}]"
        )
    )
    prompt = f"Tên sản phẩm: {name}\nBảng thành phần: {ingredients}"

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
                    return parsed[:4]

        return []

    except Exception as e:
        logger.exception(f"[ProductAI] AI Ingredients Suggestion Failed: {e}")
        return []

async def suggest_specs_logic(raw_text: str) -> Dict[str, str]:
    """Elite V2.2: XOHI Auto Specifications Extractor Logic (Isolated)."""
    agent = Agent(
        system_prompt=(
            "Bạn là trợ lý AI chuyên nghiệp. Hãy phân tích đoạn văn bản thô mô tả thông số kỹ thuật của sản phẩm "
            "và trích xuất chúng thành các cặp khóa-giá trị (Key-Value) dưới dạng JSON.\n"
            "QUY TẮC:\n"
            "1. Chuẩn hóa tên khóa sang tiếng Việt chuyên nghiệp nếu có thể (ví dụ: 'Thương hiệu', 'Xuất xứ', 'Quy cách', 'Hạn sử dụng', 'Dung tích', 'Khối lượng').\n"
            "2. Giá trị phải được giữ nguyên hoặc làm sạch nhẹ nhàng để hiển thị trên website.\n"
            "3. Chỉ trả về đối tượng JSON phẳng duy nhất, không có markdown hoặc bất kỳ văn bản nào khác ngoài JSON:\n"
            "{\"Khóa 1\": \"Giá trị 1\", \"Khóa 2\": \"Giá trị 2\"}"
        )
    )
    prompt = f"Thông số kỹ thuật thô:\n{raw_text}"

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
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return {str(k): str(v) for k, v in parsed.items()}

        return {}

    except Exception as e:
        logger.exception(f"[ProductAI] AI Specs Extraction Failed: {e}")
        return {}
