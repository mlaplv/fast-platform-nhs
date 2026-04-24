"""
CNS V87.0 — Surgeon Booster: Phẫu thuật nội dung không cần Google Search.
Phân tích raw_content, trả về List[ContentPatch] để Frontend apply tuần tự.
Tuân thủ CLAUDE.md: ≤500 dòng, Pydantic V2 only, cấm any.
"""
import logging
from datetime import datetime, timezone
from pydantic_ai import Agent
from backend.services.xohi.creative_studio.models.schemas import (
    SurgeonBoosterReport, ContentPatch
)
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

_SURGEON_BOOST_PROMPT = """[ROLE] VIRAL EDGE SURGEON BOOSTER — XoHi 2026
Nhiệm vụ: Phân tích bài viết và trả về danh sách các thao tác "phẫu thuật" CỤ THỂ để nâng cấp nội dung.

[8 TIÊU CHÍ CẦN PHẪU THUẬT]
1. Xóa câu "fluff" (Không thể phủ nhận, Trong thời đại 4.0...)
2. Thêm số liệu cụ thể vào các tuyên bố mơ hồ
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

_surgeon_agent = Agent(
    output_type=SurgeonBoosterReport,
    system_prompt=_SURGEON_BOOST_PROMPT,
    retries=2
)


async def run_surgeon_boost(content: str, topic: str = "") -> SurgeonBoosterReport:
    """
    CNS V87.0: Phẫu thuật nội dung ad-hoc — không cần campaign, không cần Google Search.
    Trả về SurgeonBoosterReport với danh sách ContentPatch để Frontend apply.
    """
    logs: list[str] = [
        f"🚀 Surgeon Booster khởi động tại {datetime.now(timezone.utc).isoformat()}...",
        "🧠 Đang phân tích cấu trúc nội dung...",
    ]

    if not content or len(content.strip()) < 50:
        return SurgeonBoosterReport(
            patches=[],
            summary="Nội dung quá ngắn để phẫu thuật.",
            logs=logs
        )

    topic_prefix = f"[CHỦ ĐỀ]: {topic}\n\n" if topic else ""
    prompt = f"{topic_prefix}[NỘI DUNG CẦN PHẪU THUẬT]:\n{content[:10000]}"

    try:
        logs.append("🔪 Đang thực hiện phẫu thuật nội dung...")
        result = await trinity_bridge.run(_surgeon_agent, prompt, role="pro", timeout=90.0)
        logs.append(f"✅ Hoàn tất! {len(result.patches)} thao tác phẫu thuật sẵn sàng.")
        result.logs = logs
        return result
    except Exception as exc:
        logger.error(f"[SurgeonBooster] Lỗi phẫu thuật: {exc}", exc_info=True)
        return SurgeonBoosterReport(
            patches=[],
            summary=f"Phẫu thuật thất bại: {str(exc)[:100]}",
            logs=[*logs, f"❌ Lỗi: {str(exc)[:100]}"]
        )
