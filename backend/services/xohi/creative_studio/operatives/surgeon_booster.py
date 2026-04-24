import logging
from datetime import datetime, timezone
from pydantic_ai import Agent
from backend.services.xohi.creative_studio.models.schemas import (
    SurgeonBoosterReport, ContentPatch
)
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, XoHiProgressMixin

logger = logging.getLogger("api-gateway")

_SURGEON_BOOST_PROMPT = """[ROLE] VIRAL EDGE SURGEON BOOSTER — XoHi 2026
Nhiệm vụ: Phân tích bài viết và trả về danh sách các thao tác "phẫu thuật" CỤ THỂ để nâng cấp nội dung.

[8 TIÊU CHÍ CẦN PHẪU THUẬT]
1. Xóa câu "fluff" (Không thể phủ nhận, Trong thời đại 4.0...)
2. Thêm số liệu cụ thể vào các tuyên bỏ mơ hồ
3. Tăng EEAT: thêm dẫn chứng thực tế, trích dẫn
4. Tăng Featured Snippet: cấu trúc câu trả lời ≤40 từ sau H2
5. Tối ưu Topic Sentence mỗi đoạn
6. Loại bỏ nội dung trùng lặp trong bài
7. Tăng Entity Density (tên riêng, số liệu, thuật ngữ)
8. Cải thiện cấu trúc bullet/table để AI dễ trích dẫn

[QUY TẮC BẮT BUỘC]
- search_string: PHẢI là đoạn text tồn tại THỰC SỰ trong bài (copy nguyên văn ≤200 chars)
- replacement_string: Đoạn text cải thiện (không được dài hơn 2x gốc)
- Tối thiểu 3 patches, tối đa 10 patches
- Không sửa HTML tags, chỉ sửa text bên trong tags
- Không thêm nội dung không có trong bài gốc trừ khi cần thêm số liệu

[YÊU CẦU ĐẦU RA — SurgeonBoosterReport]
Trả về patches: List[ContentPatch] và summary tóm tắt những gì đã cải thiện.
"""

class SurgeonBooster(BaseAgentOperative, XoHiProgressMixin):
    """
    CNS V87.0: Surgeon Booster Operative.
    Performs ad-hoc content enrichment and phẫu thuật.
    """
    agent_id_class = "surgeon_booster"

    def __init__(self, **kwargs: object):
        super().__init__(agent_id="surgeon_booster")
        self._agent = Agent(
            output_type=SurgeonBoosterReport,
            system_prompt=_SURGEON_BOOST_PROMPT,
            retries=2
        )

    async def chat(self, request: object, **kwargs: object) -> SurgeonBoosterReport:
        """Standard Heritage Entry."""
        content = str(getattr(request, "draft_content", "")) or str(kwargs.get("content", ""))
        topic = str(getattr(request, "topic", "")) or str(kwargs.get("topic", ""))
        campaign_id = getattr(request, "id", str(kwargs.get("campaign_id", "adhoc")))
        
        logs: list[str] = [
            f"🚀 Surgeon Booster khởi động tại {datetime.now(timezone.utc).strftime('%H:%M:%S')}...",
        ]
        await self._emit_progress(campaign_id, logs[-1])

        if not content or len(content.strip()) < 50:
            return SurgeonBoosterReport(
                patches=[],
                summary="Nội dung quá ngắn để phẫu thuật.",
                logs=logs
            )

        topic_prefix = f"[CHỦ ĐỀ]: {topic}\n\n" if topic else ""
        prompt = f"{topic_prefix}[NỘI DUNG CẦN PHẪU THUẬT]:\n{content[:10000]}"

        try:
            logs.append("🧠 Đang phân tích cấu trúc & tìm kiếm cơ hội tối ưu EEAT...")
            await self._emit_progress(campaign_id, logs[-1])
            
            logs.append("🔪 Đang thực hiện phẫu thuật nội dung bằng Neural Booster...")
            await self._emit_progress(campaign_id, logs[-1])
            
            result = await trinity_bridge.run(self._agent, prompt, role="pro", timeout=90.0)
            
            logs.append(f"✅ Hoàn tất! {len(result.patches)} thao tác phẫu thuật sẵn sàng.")
            await self._emit_progress(campaign_id, logs[-1], status="DONE")
            
            result.logs = logs
            return result
        except Exception as exc:
            logger.error(f"[SurgeonBooster] Lỗi phẫu thuật: {exc}", exc_info=True)
            err_msg = f"❌ Lỗi phẫu thuật: {str(exc)[:100]}"
            await self._emit_progress(campaign_id, err_msg, status="FAILED")
            return SurgeonBoosterReport(
                patches=[],
                summary=f"Phẫu thuật thất bại: {str(exc)[:100]}",
                logs=[*logs, err_msg]
            )

# Heritage Backdoor for legacy calls
async def run_surgeon_boost(content: str, topic: str = "") -> SurgeonBoosterReport:
    booster = SurgeonBooster()
    return await booster.chat(None, content=content, topic=topic)
