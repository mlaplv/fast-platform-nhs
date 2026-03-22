import logging
import os
import uuid
import re
import asyncio
from datetime import datetime, timezone
from pydantic_ai import Agent

from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge, AIConfigurationError
from backend.services.xohi.creative_studio.models.schemas import TopicSeed, AgentResponse, AgentSignal, CategoryEnum
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")

# Pre-compiled Regex for Performance (V76.3)
RE_CLEAN_PREFIX = re.compile(r'^(viết bài|tạo bài|làm bài|thiết kế|viết một bài về|viết bài về|tạo bài về|viết)\s+', re.IGNORECASE)

VISION_PROMPT = """[ROLE] CHUYÊN GIA SEO CONTENT STRATEGY — Hệ thống XoHi Content Factory V63.0 Alpha

[NHIỆM VỤ]
Phân tích chủ để và KHÓA MỤC TIÊU (Intent Lock) dựa trên dữ liệu thực tế.

[QUY TRÌNH SUY LUẬN 3 BƯỚC - NEURAL GUARD]
BƯỚC 1: PHÂN BIỆT THỰC THỂ (Disambiguation)
- Đọc toàn bộ `[GROUND TRUTH]`. Liệt kê các thực thể trùng tên nhưng khác bản chất (Vd: Hồng Sơn là Thuốc/Dược, Võ thuật, hay Cây sầu riêng).

BƯỚC 2: ĐỐI CHIẾU Ý ĐỊNH (Semantic Matching)
- So khớp thực thể tìm được với động từ/từ khóa của Sếp. 
- Ví dụ: Sếp dùng "đặc trị", "bài thuốc", "chữa" -> CHỌN thực thể Dược phẩm.
- Nếu Sếp chỉ nói tên chung chung -> Ưu tiên thực thể có tính thương mại/phổ biến nhất trên Google.

BƯỚC 3: KHÓA MỤC TIÊU (Intent Lock)
- Chỉ sử dụng thông tin của thực thể đã chọn để sinh TopicSeed.
- Tuyệt đối không để lẫn lộn từ khóa của các thực thể khác (Vd: Không mang "võ thuật" vào bài "thuốc").
- Tóm tắt bối cảnh thực thể đã khóa vào trường `ground_truth`.

[YÊU CẦU ĐỊNH DẠNG]
Trả về JSON TopicSeed chính xác. KHÔNG giải thích."""

class VisionInsight:
    """
    Step 1: Analyze input and generate the Golden Thread metadata.
    [PHASE 15: DISCOVERY-FIRST REFORM]
    """
    def __init__(self, discovery_hunter=None):
        # CNS V76: Global-like semaphore for Insight tasks to protect VPS RAM
        self.insight_semaphore = asyncio.Semaphore(2)
        self.discovery_hunter = discovery_hunter
        self.agent = Agent(
            output_type=TopicSeed,
            system_prompt=VISION_PROMPT,
            retries=3
        )

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0)."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")
        
        seed = await self.analyze_input(
            raw_input=campaign.source_input,
            campaign_id=campaign.id,
            user_id=str(campaign.user_id) if campaign.user_id else "default"
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

        # Phase 15: Discovery-First Context Injection
        clean_topic = self._sanitize_topic(raw_input)
        ground_truth = ""
        
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
            if self.discovery_hunter:
                await _emit_progress("📡 Đang kết nối mạng lưới trinh sát thực tế...")
                ground_truth = await self.discovery_hunter.search(clean_topic)
                logger.info(f"[VisionInsight] Ground Truth Context acquired for: {clean_topic}")

            # Phase 77: Dynamic mode-based constraints
            mode_instruction = ""
            if content_mode == "deep_dive":
                mode_instruction = "\n[CHẾ ĐỘ: PHÂN TÍCH SÂU] Bắt buộc word_count >= 1000, max_sections >= 6, style='Hàn lâm/Chuyên gia'."
            elif content_mode == "normal":
                mode_instruction = "\n[CHẾ ĐỘ: THÔNG THƯỜNG] Bắt buộc word_count ~ 500, max_sections ~ 3, style='Chuyên nghiệp/Tin tức'."
            else:
                mode_instruction = "\n[CHẾ ĐỘ: VIRAL] Bắt buộc word_count ~ 500, max_sections ~ 3, style='Sắc sảo/Viral'."

            prompt = f"Chủ đề bài viết: {clean_topic}\n"
            if ground_truth:
                prompt += f"\n[GROUND TRUTH CONTEXT - DỮ LIỆU THỰC TẾ TỪ GOOGLE]:\n{ground_truth}\n"
            prompt += mode_instruction
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
