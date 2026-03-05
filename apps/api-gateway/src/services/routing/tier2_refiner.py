import os
import asyncio
import logging
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from typing import Optional, Tuple
from litellm import RateLimitError, AuthenticationError, ServiceUnavailableError, Timeout as LiteLLMTimeout
from ai_engine.core.key_rotator import SmartKeyRotator

logger = logging.getLogger("api-gateway")

@dataclass
class Tier2RefinerDeps:
    """Dependencies for Tier 2 NLG Refiner."""
    raw_data: str
    target: str
    transcript: str

REFINER_PROMPT = """[ROLE] XO HI — TRỢ LÝ PHÂN TÍCH NHANH — admin.smartshop.test
Bạn là Xô Hi. Nhiệm vụ của bạn là đọc số liệu thô từ Database và chuyển thành một câu báo cáo bằng giọng nói tự nhiên, ngắn gọn và "có hồn" cho sếp.

[QUY TẮC BÁO CÁO]
- Danh xưng: Xưng "em", gọi "Sếp" hoặc "Dạ sếp".
- Giọng điệu: Tự tin, thanh lịch, mang phong thái báo cáo kinh doanh thực thụ.
- Format: BẮT BUỘC một hoặc hai câu ngắn gọn, tối đa 15-25 từ. Viết theo ngôn ngữ nói (không dùng Markdown, in đậm, gạch đầu dòng do hệ thống sẽ đọc ra tiếng).
- Xử lý số liệu: BẮT BUỘC làm tròn số tiền và quy đổi đơn vị lớn cho dễ đọc. (VD: "15.000.000đ" -> "15 triệu đồng", "1.250.000đ" -> "hơn 1 triệu 2").
- Linh hoạt ngữ cảnh: Nếu thấy "series_data" (là biểu đồ), hãy báo cáo: "Dạ thưa sếp, tổng là [Số tiền], em đã mở biểu đồ chi tiết trên màn hình rồi ạ."
- Xử lý mảng rỗng: Nếu dữ liệu là None hoặc 0 -> "Dạ sếp, hiện chưa có dữ liệu mới ạ."

[TIÊU CHUẨN MẪU TỰ NHIÊN]
- OK: "Dạ thưa sếp, doanh thu hôm nay đạt hơn 20 triệu đồng ạ."
- OK: "Dạ sếp, trong hệ thống đang quản lý tổng cộng 135 sản phẩm."
- OK: "Sếp ơi, em lọc ra được 5 đơn hàng đang chờ xử lý."
"""

class Tier2Refiner:
    def __init__(self):
        self.primary_model = os.getenv("TIER2_MODEL", "gemini/gemini-1.5-flash")
        self.fallback_model = os.getenv("TIER2_FALLBACK_MODEL", "gemini/gemini-2.0-flash")
        self.rotator = SmartKeyRotator()
        
        # [THIẾT QUÂN LUẬT] PydanticAI Agent for NLG
        self.agent = Agent(
            model=self.primary_model,
            deps_type=Tier2RefinerDeps,
            system_prompt=REFINER_PROMPT
        )

        @self.agent.system_prompt
        def add_data_context(ctx: RunContext[Tier2RefinerDeps]) -> str:
            return f"\n[DỮ LIỆU THÔ]: {ctx.deps.raw_data}\n[MỤC TIÊU SẾP HỎI]: {ctx.deps.transcript}"

    async def refine(self, transcript: str, target: str, raw_data: str) -> Tuple[str, int]:
        all_keys = self.rotator.get_all_keys()
        max_tries = min(len(all_keys), 3)
        model_names = [self.primary_model, self.fallback_model]
        
        deps = Tier2RefinerDeps(raw_data=raw_data, target=target, transcript=transcript)

        for model_name in model_names:
            for attempt in range(max_tries):
                api_key = self.rotator.get_next_key()
                os.environ["GEMINI_API_KEY"] = api_key
                os.environ.pop("GOOGLE_API_KEY", None) # R1.4 SSOT: Prevent LiteLLM conflict
                
                try:
                    result = await self.agent.run(
                        f"Hãy báo cáo số liệu {raw_data} này cho sếp.",
                        model=model_name,
                        deps=deps
                    )
                    # PydanticAI wraps result.data based on output_type. Here it's str (default).
                    return result.data.strip(), 0 

                except (ServiceUnavailableError, RateLimitError, LiteLLMTimeout, AuthenticationError) as e:
                    logger.warning(f"[NLG Refiner] {model_name} attempt {attempt+1} failed. Rotating...")
                    if attempt < max_tries - 1:
                        await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                except Exception as e:
                    logger.warning(f"[NLG Refiner] Unexpected error: {e}")
                    continue

        # 🛡️ HARD FALLBACK (Rule 3.3)
        target_vn = {
            "order": "đơn hàng", 
            "revenue": "doanh thu", 
            "product": "sản phẩm", 
            "user": "khách hàng"
        }.get(target, "dữ liệu")
        
        return f"Dạ sếp, hiện tại hệ thống ghi nhận có {raw_data} {target_vn}.", 0

