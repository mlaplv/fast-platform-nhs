import logging
import os
import uuid
import re
import asyncio
from datetime import datetime, timezone
from pydantic_ai import Agent

from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.campaign_service import campaign_service
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge, AIConfigurationError
from backend.services.xohi.creative_studio.models.schemas import TopicSeed, AgentResponse, AgentSignal, CategoryEnum
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")

# Pre-compiled Regex for Performance (V76.3)
RE_CLEAN_PREFIX = re.compile(r'^(viết bài|tạo bài|làm bài|thiết kế|viết một bài về|viết bài về|tạo bài về|viết)\s+', re.IGNORECASE)

VISION_PROMPT = """[ROLE] CHUYÊN GIA SEO CONTENT STRATEGY — Hệ thống XoHi Content Factory V62.1

[NHIỆM VỤ]
Phân tích chủ đề sếp đưa ra và đề xuất bộ Keywords SEO cho bài viết.

[LUẬT]
1. Tiêu đề phải giật tít nhưng KHÔNG clickbait rác, KHÔNG dùng emoji.
2. Từ khóa chính phải ngắn gọn (2-4 từ), có search volume cao.
3. Từ khóa phụ bổ trợ chủ đề chính, 3-5 từ khóa.
4. Persona: Mô tả giọng văn phù hợp đối tượng mục tiêu.
5. Description: Viết 1 câu Meta Description tóm tắt bài viết chuẩn SEO (tối đa 160 ký tự).
6. Category: Phân loại danh mục bài viết. CHỈ ĐƯỢC CHỌN 1 TRONG 2 GIÁ TRỊ SAU: "Tin tức" hoặc "Chính sách".
7. creation_config: Đề xuất cấu hình (style, word_count, max_assets, max_sections). 
   Mặc định sếp yêu cầu: style="Chuyên nghiệp", word_count=500, max_assets=10, max_sections=3.
8. Trả về đúng JSON schema, KHÔNG thêm text ngoài."""

class VisionInsight:
    """
    Step 1: Analyze input (text/image) and generate the Golden Thread metadata.
    Uses PydanticAI Agent with Structured Output (TopicSeed).
    """
    def __init__(self):
        # CNS V76: Global-like semaphore for Insight tasks to protect VPS RAM
        self.insight_semaphore = asyncio.Semaphore(2)
        self.agent = Agent(
            output_type=TopicSeed,
            system_prompt=VISION_PROMPT,
            retries=3
        )

    async def execute(self, campaign_id: str, session: AsyncSession, **kwargs: object) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0)."""
        campaign = await campaign_service.get_campaign(session, campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")

        seed = await self.analyze_input(
            raw_input=campaign["source_input"],
            campaign_id=campaign["id"],
            user_id=str(campaign["user_id"]) if campaign["user_id"] else "default"
        )
        
        return AgentResponse(
            signal=AgentSignal.PROCEED_NEXT,
            message="Topic analyzed successfully.",
            data=seed.model_dump()
        )

    def _sanitize_topic(self, text: str) -> str:
        # Strip common command prefixes
        cleaned = RE_CLEAN_PREFIX.sub('', text)
        return cleaned.strip().capitalize()

    async def analyze_input(self, raw_input: str, campaign_id: str, user_id: str = "default", content_mode: str = "viral") -> TopicSeed:
        """
        Uses AI to extract structured keywords from input text.
        R85: Strict Structured Output via Pydantic.
        """
        # R109: Use direct variables to avoid 'MissingGreenlet' lazy-load error
        c_id = campaign_id
        u_id = user_id

        clean_topic = self._sanitize_topic(raw_input)

        # Phase 77: Dynamic mode-based constraints
        mode_instruction = ""
        if content_mode == "deep_dive":
            mode_instruction = "\n[CHẾ ĐỘ: PHÂN TÍCH SÂU] Bắt buộc word_count >= 1000, max_sections >= 6, style='Hàn lâm/Chuyên gia'."
        else:
            mode_instruction = "\n[CHẾ ĐỘ: VIRAL] Bắt buộc word_count ~ 500, max_sections ~ 3, style='Sắc sảo/Viral'."

        prompt = f"Chủ đề bài viết: {clean_topic}{mode_instruction}"

        async def _emit_progress(msg: str):
            await event_bus.emit("CONTENT_PROGRESS", {
                "campaign_id": c_id,
                "user_id": u_id,
                "step": 1,
                "message": msg,
                "status": "PROCESSING",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        try:
            await _emit_progress("🧠 Đang kích hoạt lõi phân tích SEO Content...")

            # CNS V76: Enforce concurrency limit for insight tasks
            async with self.insight_semaphore:
                # R101/R106: Using trinity_bridge for managed AI calls
                ai_task = asyncio.create_task(trinity_bridge.run(self.agent, prompt))

                progress_msgs = [
                    "🔍 Đang phân tích Search Intent cốt lõi...",
                    "📊 Đang truy xuất tập dữ liệu Keyword Volume...",
                    "✍️ Đang xây dựng cấu trúc Persona chiến lược...",
                    "⚙️ Đang đóng gói dữ liệu Golden Thread..."
                ]

                for msg in progress_msgs:
                    if ai_task.done():
                        break
                    # Triggers next progress message every 1.5 seconds if AI is still working
                    await asyncio.sleep(1.5)
                    if not ai_task.done():
                        await _emit_progress(msg)

                result = await ai_task

            await _emit_progress("✅ Phân tích chủ đề hoàn tất. Dữ liệu SEO đã sẵn sàng!")
            
            # result.data is the TopicSeed instance when using PydanticAI
            return result.data if hasattr(result, "data") else result.output
        except AIConfigurationError:
            # R109: Re-raise config errors so Orchestrator can report model/key status to sếp
            raise
        except Exception as e:
            logger.error(f"[VisionInsight] AI failed (Campaign: {c_id}): {e}", exc_info=True)
            # Fallback: Tạo keywords từ transcript đã gọt râu ria (Graceful Degradation R103)
            # Fix: Tránh split từng từ tiếng Việt (e.g. "Thời" "trang" "nữ") -> Giữ nguyên cụm từ hoặc fallback thông minh hơn
            if not clean_topic:
                clean_topic = "Nội dung Sáng tạo"
            
            # Thay vì split(), chúng ta dùng title làm primary và tạo secondary từ các biến thể đơn giản
            return TopicSeed(
                title=f"Khám phá {clean_topic}",
                primary_keyword=clean_topic[:50],
                secondary_keywords=[clean_topic[:50], f"{clean_topic} mới nhất", "Xohi AI Strategy"],
                persona="Chuyên gia, giọng văn thân thiện và chuyên nghiệp",
                description=f"Khám phá kiến thức chuyên sâu về {clean_topic} để tối ưu hóa hiệu quả công việc và cuộc sống.",
                category=CategoryEnum.TIN_TUC
            )
