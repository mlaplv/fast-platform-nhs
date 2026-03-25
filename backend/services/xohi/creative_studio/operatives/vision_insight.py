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

# Pre-compiled Regex for Performance (V85.1)
RE_CLEAN_PREFIX = re.compile(r'^(adm\s+)?(viết bài|tạo bài|làm bài|thiết kế|viết một bài về|viết bài về|tạo bài về|viết|tạo sản phẩm|san pham:?)\s+', re.IGNORECASE)

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
            repo=repo,
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

    async def analyze_input(self, raw_input: str, campaign_id: str, repo: ContentCampaignRepository, user_id: str = "default", content_mode: str = "viral") -> TopicSeed:
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
            campaign = await repo.get(c_id)
            if not campaign:
                raise ValueError(f"Campaign {c_id} not found")

            # Extract target entity from metadata
            gold_meta = campaign.gold_metadata or {}
            target_entity = gold_meta.get("target_entity", "article")

            if self.discovery_hunter:
                await _emit_progress("📡 Đang kết nối mạng lưới trinh sát thực tế...")
                ground_truth = await self.discovery_hunter.search(clean_topic)
                
                # Phase 15.4: Live Intelligence (Ground Truth reporting)
                snippet = ground_truth[:120].replace("\n", " ") + "..."
                await _emit_progress(f"🔍 Trinh sát thực tế: {snippet}")
                logger.info(f"[VisionInsight] Ground Truth Context acquired for: {clean_topic}")

            # Phase 77: Dynamic mode-based constraints
            mode_instruction = ""
            if content_mode == "deep_dive":
                mode_instruction = "\n[CHẾ ĐỘ: PHÂN TÍCH SÂU] Bắt buộc word_count >= 1000, max_sections >= 6, style='Hàn lâm/Chuyên gia'."
            elif content_mode == "normal":
                mode_instruction = "\n[CHẾ ĐỘ: THÔNG THƯỜNG] Bắt buộc word_count ~ 500, max_sections ~ 3, style='Chuyên nghiệp/Tin tức'."
            else:
                mode_instruction = "\n[CHẾ ĐỘ: VIRAL] Bắt buộc word_count ~ 500, max_sections ~ 3, style='Sắc sảo/Viral'."

            # Inject entity hint for AI
            entity_hint = f"\n[ENTITY TYPE]: {target_entity.upper()}"
            if target_entity == "product":
                entity_hint += "\n[REQUIREMENT]: Đọc kỹ thông tin sản phẩm và phân loại category = 'Sản phẩm'."

            prompt = f"Chủ đề: {clean_topic}\n"
            prompt += entity_hint
            if ground_truth:
                prompt += f"\n[GROUND TRUTH CONTEXT - DỮ LIỆU THỰC TẾ TỪ GOOGLE]:\n{ground_truth}\n"
            prompt += mode_instruction
            await _emit_progress("🧠 Đang kích hoạt lõi phân tích SEO Content...")

            # Phase 15.6: Category Intelligence (V85.2)
            categories_ctx = ""
            if hasattr(repo, "session"):
                from backend.database.models import Category
                from sqlalchemy import select
                try:
                    stmt = select(Category.id, Category.name).where(Category.tenant_id == campaign.tenant_id)
                    res_cat = await repo.session.execute(stmt)
                    cat_list = res_cat.all()
                    if cat_list:
                        categories_ctx = "\n[DANH MỤC HỆ THỐNG]:\n" + "\n".join([f"- ID: {c.id} | Name: {c.name}" for c in cat_list])
                        prompt += f"\n{categories_ctx}\n[BẮT BUỘC]: Chọn ID danh mục phù hợp nhất từ danh sách trên và điền vào trường `category_id`."
                except Exception as e:
                    logger.warning(f"[VisionInsight] Failed to fetch categories: {e}")

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
                seed: TopicSeed = result.data if hasattr(result, "data") else result.output

                # CNS V85.1: Enforce Category based on intent or AI detection
                if target_entity == "product":
                    seed.category = CategoryEnum.SAN_PHAM
                elif target_entity == "article":
                    seed.category = CategoryEnum.TIN_TUC

                return seed
        except AIConfigurationError:
            # R109: Re-raise config errors so Orchestrator can report model/key status to sếp
            raise
        except Exception as e:
            logger.error(f"[VisionInsight] AI failed (Campaign: {c_id}): {e}", exc_info=True)
            # Fallback: Tạo keywords từ transcript đã gọt râu ria (Graceful Degradation R103)
            if not clean_topic:
                clean_topic = "Nội dung Sáng tạo"
            
            # Fetch target_entity for fallback
            try:
                temp_campaign = await repo.get(c_id)
                target_entity = (temp_campaign.gold_metadata or {}).get("target_entity", "article") if temp_campaign else "article"
            except: target_entity = "article"

            return TopicSeed(
                title=f"Khám phá {clean_topic}",
                primary_keyword=clean_topic[:50],
                secondary_keywords=[clean_topic[:50], f"{clean_topic} mới nhất", "Xohi AI Strategy"],
                persona="Chuyên gia, giọng văn thân thiện và chuyên nghiệp",
                description=f"Khám phá kiến thức chuyên sâu về {clean_topic} để tối ưu hóa hiệu quả công việc và cuộc sống.",
                category=CategoryEnum.SAN_PHAM if target_entity == "product" else CategoryEnum.TIN_TUC
            )
