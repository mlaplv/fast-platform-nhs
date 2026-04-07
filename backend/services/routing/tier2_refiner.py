import os
import logging
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from typing import Tuple
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

@dataclass
class Tier2RefinerDeps:
    """Dependencies for Tier 2 NLG Refiner."""
    raw_data: str
    target: str
    transcript: str

REFINER_PROMPT = f"""[ROLE] XO HI — TRỢ LÝ PHÂN TÍCH NHANH — {os.getenv('PUBLIC_SSOT_ADMIN_URL', 'admin.smartshop.test')}
Bạn là Xô Hi. Nhiệm vụ của bạn là đọc số liệu thô từ Database và chuyển thành một câu báo cáo bằng giọng nói tự nhiên, ngắn gọn và "có hồn" cho sếp.

[QUY TẮC BÁO CÁO]
- Danh xưng: Xưng "em", gọi "Sếp" hoặc "Dạ sếp".
- Giọng điệu: Tự tin, thanh lịch, mang phong thái báo cáo kinh doanh thực thụ.
- Format: BẮT BUỘC một hoặc hai câu ngắn gọn, tối đa 15-25 từ. Viết theo ngôn ngữ nói (không dùng Markdown, in đậm, gạch đầu dòng do hệ thống sẽ đọc ra tiếng).
- Xử lý số liệu: BẮT BUỘC làm tròn số tiền và quy đổi đơn vị lớn cho dễ đọc. (VD: "15.000.000đ" -> "15 triệu đồng", "1.250.000đ" -> "hơn 1 triệu 2").
- Xử lý mảng rỗng: Nếu dữ liệu là None hoặc 0 -> "Dạ sếp, hiện chưa có dữ liệu mới ạ."

[TIÊU CHUẨN MẪU TỰ NHIÊN]
- OK: "Dạ thưa, doanh thu hôm nay đạt hơn 20 triệu đồng ạ."
- OK: "Dạ sếp, trong hệ thống đang quản lý tổng cộng 135 sản phẩm."
- OK: "Sếp ơi, em lọc ra được 5 đơn hàng đang chờ xử lý."
"""

TARGET_VN_MAP = {
    "order": "đơn hàng",
    "revenue": "doanh thu",
    "product": "sản phẩm",
    "user": "khách hàng"
}

class Tier2Refiner:
    def __init__(self):
        self.rotator = key_rotator

        self.agent = Agent(
            deps_type=Tier2RefinerDeps,
            system_prompt=REFINER_PROMPT
        )

        @self.agent.system_prompt
        def add_data_context(ctx: RunContext[Tier2RefinerDeps]) -> str:
            return f"\n[DỮ LIỆU THÔ]: {ctx.deps.raw_data}\n[MỤC TIÊU SẾP HỎI]: {ctx.deps.transcript}"

    async def refine(self, transcript: str, target: str, raw_data: str) -> Tuple[str, int]:
        deps = Tier2RefinerDeps(raw_data=raw_data, target=target, transcript=transcript)

        try:
            result = await trinity_bridge.run(
                self.agent,
                f"Hãy báo cáo số liệu {raw_data} này cho sếp.",
                deps=deps
            )

            return result.strip() if isinstance(result, str) else str(result).strip(), 0

        except Exception as e:
            logger.error(f"[NLG Refiner] Trinity failure: {e}")

            # Hard fallback
            target_vn = TARGET_VN_MAP.get(target, "dữ liệu")

            return f"Dạ sếp, hiện tại hệ thống ghi nhận có {raw_data} {target_vn}.", 0
