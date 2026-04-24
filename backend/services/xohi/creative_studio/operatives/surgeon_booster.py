import logging
from datetime import datetime, timezone
from pydantic_ai import Agent
from backend.services.xohi.creative_studio.models.schemas import SurgeonBoosterReport
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, XoHiProgressMixin

logger = logging.getLogger("api-gateway")

_SURGEON_BOOST_PROMPT = """[ROLE] VIRAL EDGE SENIOR SURGEON — Neural XoHi Elite V2.2
Nhiệm vụ: Phẫu thuật nội dung để đạt Viral Edge tối đa. Tuyệt đối không viết chung chung vô giá trị.

[QUY TẮC BÁO CÁO — ELITE PROTOCOL]
1. 🚫 KHÔNG DÙNG LỜI MỞ ĐẦU/KẾT THÚC: Đi thẳng vào các thao tác phẫu thuật.
2. 🚫 KHÔNG DÙNG DẤU BA SAO (***): Sử dụng tiêu đề Markdown hoặc danh sách chuẩn.
3. 💉 INFORMATION GAIN: Mỗi patch phẫu thuật phải tăng cường EEAT (Số liệu, Trích dẫn, Thực thể).
4. 🔪 SURGICAL PRECISION: search_string phải khớp 100% bản gốc.

[YÊU CẦU ĐẦU RA — SurgeonBoosterReport]
summary: "BẢN TRÌNH BÁO PHẪU THUẬT NỘI DUNG (Elite V2.2)\\n\\n- **[LUẬN ĐIỂM CẢI TIẾN]**: Phân tích vì sao nội dung gốc đang bị 'loãng' hoặc thiếu sức nặng.\\n- **[CHỨNG CỨ PHẪU THUẬT]**: Liệt kê các đoạn đã được tiêm Information Gain.\\n- **[KẾT QUẢ KỲ VỌNG]**: Tăng khả năng lọt TOP 1 và AI Overview."
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
