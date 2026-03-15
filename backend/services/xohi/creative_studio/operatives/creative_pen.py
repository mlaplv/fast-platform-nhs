import logging
import re
from typing import List, Dict, Union, Optional
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import ArticleOutline, AgentResponse, AgentSignal
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner

logger = logging.getLogger("api-gateway")

OUTLINE_PROMPT = """[ROLE] CHIEF EDITOR — Journalism Excellence V76.5
[CHIẾN THUẬT: THÁP NGƯỢC (INVERTED PYRAMID)]
1. **SAPÔ (LEAD)**: Tóm tắt 1 câu đắt giá nhất, phản ánh mục tiêu cốt lõi của bài viết.
2. **CẤU TRÚC PHÂN CẤP**:
   - H2 phải là các câu khẳng định giá trị hoặc đặt vấn đề trực diện.
   - Nội dung (Content) chỉ liệt kê 3-5 Ý CHỐN (Key Points) hoặc số liệu, không viết mô tả rườm rà.
3. **NGÔN NGỮ CHUYÊN GIA**: Tuyệt đối không dùng từ giật gân rẻ tiền. Văn phong khoa học, tin cậy.

[NHIỆM VỤ]
Thiết kế Dàn ý (Outline) chuẩn quy trình tòa soạn:
1. **SAPÔ**: Viết vào mục đầu tiên của dàn ý.
2. **BODY**: Chia thành các mục H2/H3 hợp lý theo luồng logic.
3. **ASSETS**: Chỉ định [IMAGE_X] tại các đoạn cần minh họa dữ liệu.

[YÊU CẦU ĐỊNH DẠNG JSON]
Bắt đầu bằng mảng `sections`, mỗi object PHẢI có:
- "heading": Tiêu đề mục (Ví dụ: "H2: Phân tích thực trạng X", "Sapô: ...")
- "content": Danh sách các Key Points (gạch đầu dòng) và [IMAGE_X].

Chỉ trả về JSON, KHÔNG giải thích thêm."""

DRAFT_PROMPT = """[ROLE] SENIOR INVESTIGATIVE JOURNALIST — XoHi Press V76.5
[CHIẾN THUẬT: MỞ RỘNG & TINH LỌC (EXPANSION & REFINEMENT)]
1. **DẪN NHẬP (LEAD)**: Viết Sapô lôi cuốn, tóm lược vấn đề cốt lõi ngay 2 câu đầu.
2. **TRIỂN KHAI PHÂN TÍCH**:
   - Mỗi mục H2 phải là một luận điểm vững chắc.
   - Sử dụng các cụm từ nối chuyên nghiệp: "Đáng chú ý...", "Trên thực tế...", "Tuy nhiên, nhìn từ góc độ...".
3. **TRÌNH BÀY BÁO CHÍ**: Dùng thẻ HTML chuẩn (h1, h2, p, figure, section). Không dùng từ ngữ sáo rỗng.

[NHIỆM VỤ]
Viết bài báo hoàn chỉnh dựa trên Dàn ý đã duyệt. 
- **FACT-CHECK**: Đảm bảo thông tin chính xác, logic.
- **ASSET INTEGRATION**: Chèn [IMAGE_X] vào các vị trí hỗ trợ trực quan cho thông tin.

[YÊU CẦU HTML]
- Trả về mã HTML thuần. 
- KHÔNG có phần giải thích, KHÔNG dùng Markdown code fences (```html).
- Toàn bộ bài phải nằm trong luồng logic của Golden Thread."""



class CreativePen:
    """
    Step 3 & 4: Generate Outline and Draft Content.
    V62.1: Full AI-powered content generation with Golden Thread injection.
    """
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.model_name = model_name

        # Phase 42: Professional Agent Caching (Memory Discipline)
        self.outline_agent = Agent(
            output_type=ArticleOutline,
            system_prompt=OUTLINE_PROMPT,
            retries=3
        )
        self.draft_agent = Agent(system_prompt=DRAFT_PROMPT)

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0)."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")
        
        step = kwargs.get("step")
        if step == 3:
            outline = await self.generate_outline(campaign)

            # Phase 76.7: Defense against raw AgentRunResult leakage
            if hasattr(outline, "model_dump"):
                campaign.outline_data = outline.model_dump()
            elif isinstance(outline, dict):
                campaign.outline_data = outline
            elif hasattr(outline, "data"):
                # Recursive unwrapping if trinity_bridge returned the wrapper
                data = outline.data
                campaign.outline_data = data.model_dump() if hasattr(data, "model_dump") else data
            else:
                logger.error(f"[Content Factory] Outline data is un-dumpable: {type(outline)}")
                campaign.outline_data = {"error": "Invalid outline format"}

            return AgentResponse(
                signal=AgentSignal.PROCEED_NEXT,
                message="Outline generated based on Golden Thread.",
                data=campaign.outline_data
            )
        elif step == 4:
            content = await self.write_draft(campaign)
            campaign.draft_content = content
            return AgentResponse(
                signal=AgentSignal.PROCEED_NEXT,
                message="Draft content generated — Viral 2026 Edition.",
                data={"content": content}  # BUG-03 fix: engine.py reads response.data.get("content", ...)
            )
        
        return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message=f"Invalid step {step} for CreativePen")

    async def generate_outline(self, campaign: ContentCampaign) -> ArticleOutline:
        """
        Step 3: Generate a technical outline based on Golden Thread.
        Now using Standardized Golden Context Helpers.
        """
        primary = campaign.get_gold_val("primary_keyword", "N/A")
        secondary = ", ".join(campaign.get_gold_val("secondary_keywords", []))
        title = campaign.get_gold_val("title", "Bài viết mới")
        persona = campaign.get_gold_val("persona", "Chuyên gia")
        
        assets = campaign.assets_data or []
        num_assets = len(assets)
        
        # Phase 71: Strict Section Control
        config = campaign.get_gold_config()
        max_sections = config.get("max_sections", 3)
        
        instruction = f"""
        Hãy sinh Dàn Ý (ArticleOutline) với đúng {max_sections} mục chính. Trả về đúng schema JSON. 
        Mục đầu tiên PHẢI là "Sapô" tóm tắt toàn bài.
        """
        
        # Phase 76.5: Context De-noising before AI injection
        title_clean = await noise_cleaner.clean(title, mode="standard")
        primary_clean = await noise_cleaner.clean(primary, mode="standard")
        
        prompt = f"""
        [THÔNG TIN GOLDEN THREAD - ĐÃ KHỬ NHIỄU]
        - Tiêu đề tiêu điểm: {title_clean}
        - Từ khóa CHỦ CHỐT: {primary_clean}
        - Từ khóa bổ trợ: {secondary}
        - Phong cách (Persona): {persona}
        - Số lượng ảnh: {num_assets} ảnh.
        - GIỚI HẠN: {max_sections} mục H2.
        
        Cần một dàn ý BÁO CHÍ chuẩn mực, tập trung vào giá trị thông tin.
        """
        
        try:
            logger.info(f"[Content Factory] CreativePen generating outline for {campaign.id} using {self.model_name}")
            result = await trinity_bridge.run(self.outline_agent, f"{instruction}\n{prompt}", session_id=campaign.id, model=self.model_name)

            # Phase 76.9: Universal Unwrapper (Extreme Robustness)
            raw_data = None
            if hasattr(result, "data"):
                raw_data = result.data
            elif hasattr(result, "result") and hasattr(result.result, "data"):
                # Recursive unwrapping if trinity_bridge returned another wrapper
                inner = result.result
                raw_data = inner.data if hasattr(inner, "data") else inner
            else:
                raw_data = result

            # Extra check: if raw_data is still an AgentRunResult (leakage protection)
            if type(raw_data).__name__ == "AgentRunResult":
                if hasattr(raw_data, "data"):
                    raw_data = raw_data.data

            # Validation and Conversion
            if isinstance(raw_data, ArticleOutline):
                return raw_data
            if isinstance(raw_data, dict):
                # Ensure it has the expected structure
                if "sections" in raw_data:
                    return ArticleOutline(**raw_data)
                return raw_data

            # Final Fallback for raw objects
            if hasattr(raw_data, "model_dump"):
                return raw_data.model_dump()

            logger.warning(f"[Content Factory] Unexpected outline format: {type(raw_data)}. Returning as-is.")
            return raw_data

            # Fallback for different pydantic-ai versions
            logger.warning(f"[Content Factory] AgentRunResult missing .data, attempting fallback. Result type: {type(result)}")
            return result
        except Exception as e:
            logger.error(f"[Content Factory] CreativePen Outline Gen Error: {e}")
            raise

    async def write_draft(self, campaign: ContentCampaign) -> str:
        """
        Step 4: Generate REAL full-length viral content using AI.
        V71.0: Full Golden Thread injection + Outline + Guaranteed Asset Placement.
        """
        prompt, assets, primary = await self._build_draft_prompt(campaign)

        try:
            logger.info(f"[Content Factory] CreativePen Draft Writing Phase 76.5 for {campaign.id}")
            result = await trinity_bridge.run(self.draft_agent, prompt, session_id=campaign.id, model=self.model_name)

            # Phase 76.9: Universal Text Unwrapper
            content = ""
            if hasattr(result, "data"):
                content = str(result.data)
            elif hasattr(result, "result") and hasattr(result.result, "data"):
                content = str(result.result.data)
            else:
                content = str(result)

            return await self._process_draft_content(content, assets, primary, campaign.id)

        except Exception as e:
            logger.error(f"[Content Factory] CreativePen Draft Gen Error: {e}")
            raise  # Re-raise instead of returning fallback content

    async def stream_draft(self, campaign: ContentCampaign):
        """
        V76.5: Neural Streaming Version of draft generation.
        Yields text chunks and eventually the final processed HTML.
        """
        prompt, assets, primary = await self._build_draft_prompt(campaign)

        try:
            logger.info(f"[Content Factory] CreativePen Neural Streaming Draft for {campaign.id}")
            full_raw_content = ""

            async with trinity_bridge.run_stream(self.draft_agent, prompt, session_id=campaign.id, model=self.model_name) as stream:
                async for chunk in stream:
                    # pydantic-ai stream yields chunks
                    text = chunk.delta
                    if text:
                        full_raw_content += text
                        yield {"type": "chunk", "text": text}

            # Final processing (Sanitize, Replace Images, Noise Cleaning)
            final_content = await self._process_draft_content(full_raw_content, assets, primary, campaign.id)
            yield {"type": "final", "content": final_content}

        except Exception as e:
            logger.error(f"[Content Factory] CreativePen Streaming Draft Error: {e}")
            yield {"type": "error", "message": str(e)}
            raise

    async def _build_draft_prompt(self, campaign: ContentCampaign):
        """Helper to build prompt (Shared between sync and stream)."""
        outline_data = campaign.outline_data or {}
        assets = campaign.assets_data or []

        # --- BUILD FULL CONTEXT VIA GOLD HELPERS ---
        primary = campaign.get_gold_val("primary_keyword", "chủ đề chính")
        secondary_list = campaign.get_gold_val("secondary_keywords", [])
        title = campaign.get_gold_val("title", primary)
        persona = campaign.get_gold_val("persona", "Chuyên gia")

        # V71.0: Improved Outline Parsing (Handle both sections and html)
        sections = []
        outline_html = ""

        if isinstance(outline_data, dict):
            sections = outline_data.get("sections", [])
            outline_html = outline_data.get("html", "")

        # Format outline for the AI prompt
        if sections:
            outline_text = "\n".join([
                f"  - {s.get('heading', '')}: {s.get('content', '')}"
                for s in sections
            ])
        elif outline_html:
            # CMS V71.0: Extract text or just pass the HTML as context
            outline_text = f"Sử dụng nội dung từ dàn ý HTML sau đây làm căn cứ: {outline_html[:1500]}"
        else:
            outline_text = f"  - H2: {title}: Giới thiệu tổng quan.\n  - H2: Chi tiết: Nội dung chuyên sâu.\n  - H2: Kết luận: Tổng kết và CTA."

        # Format asset list with descriptions
        asset_lines = [f"  [IMAGE_{i}]: {url}" for i, url in enumerate(assets[:12], 1)]
        asset_context = "\n".join(asset_lines) if asset_lines else "  (Không có ảnh)"

        # Avatar context
        avatar_url = campaign.get_gold_val("avatar", assets[0] if assets else None)
        avatar_context = f"  Ảnh đại diện (thumbnail): {avatar_url}" if avatar_url else "  (Chưa có ảnh đại diện)"

        # Phase 71: Strict Word Count Enforcement (90% - 120% Range)
        config = campaign.get_gold_config()
        target_words = int(config.get("word_count", 500))
        min_words = int(target_words * 0.9)
        max_words = int(target_words * 1.2)

        # V76.0: Adaptive Paragraph Control (Deep Dive Support)
        max_sections = int(config.get("max_sections", 3))
        content_mode = config.get("content_mode", "viral") # default to viral

        if content_mode == "deep_dive":
            paras_per_section = 4 # Allow more depth for analytical content
            total_para_limit = max_sections * 5
            mode_instruction = "Viết chi tiết, phân tích sâu sắc, cung cấp nhiều giá trị chuyên môn."
        else:
            # Roughly 1-2 paragraphs per segment to keep total paragraph count under control
            paras_per_section = 1 if max_sections >= 8 else 2
            total_para_limit = max_sections * 2
            mode_instruction = "Viết cực kỳ cô đọng, tập trung vào tính viral và nhịp điệu nhanh (Fast-paced)."

        prompt = f"""
[THÔNG TIN CHIẾN DỊCH NỘI DUNG]

## GOLDEN THREAD (Cốt lõi không thể thay đổi)
- Tiêu đề bài viết: {title}
- Từ khóa CHÍNH (phải xuất hiện nhiều nhất): **{primary}**
- Từ khóa PHỤ (phân bổ tự nhiên): {', '.join(secondary_list)}
- Phong cách viết (Persona): {persona}
- Chế độ nội dung: {content_mode.upper()} ({mode_instruction})

## DÀN Ý ĐÃ ĐƯỢC DUYỆT (BƯỚC 3)
Viết đầy đủ và đúng thứ tự tất cả các mục sau:
{outline_text}

## KHO ẢNH ĐÃ ĐƯỢC CHỌN (BƯỚC 2)
{avatar_context}
{asset_context}

## YÊU CẦU BẮT BUỘC (CRITICAL ENFORCEMENT)
- Bắt đầu bài viết bằng: <h1>{title}</h1>
- **GIỚI HẠN ĐOẠN VĂN**: Mỗi mục (H2/H3) CHỈ ĐƯỢC PHÉP có tối đa {paras_per_section} đoạn văn (<p>). Tổng bài viết KHÔNG QUÁ {total_para_limit} đoạn văn.
- Chèn mã [IMAGE_N] vào vị trí muốn hiển thị. Bạn có thể ghi [IMAGE_N] đứng một mình hoặc chèn vào giữa văn bản.
- **ĐỘ DÀI BẮT BUỘC**: Bài viết PHẢI nằm trong khoảng từ {min_words} đến {max_words} từ.
- Giàu thông tin, hấp dẫn và viral.
- Kết thúc bằng một đoạn <section class=\"cta\"> với Call-To-Action mạnh mẽ liên quan đến \"{primary}\".
- KHÔNG thêm lời dẫn hay giải thích. Chỉ trả về HTML thuần.

Bắt đầu viết ngay:
"""
        return prompt, assets, primary

    async def _process_draft_content(self, content: str, assets: List[str], primary: str, campaign_id: str) -> str:
        """Helper to sanitize and clean content (Shared)."""
        # Sanitize: remove markdown code fences if AI wraps them
        if content.startswith("```"):
            content = content.split("```", 2)[-1] if "```" in content[3:] else content[3:]
            content = content.lstrip("html\n").rstrip("`")

        # Phase 70.0 Fix: Guaranteed [IMAGE_N] replacement
        content = self._replace_image_placeholders(content, assets, primary)

        # Phase 76.5: Hybrid Noise Shield - Draft Deep Cleaning
        content = await noise_cleaner.clean(content, mode="aggressive")

        logger.info(f"[Content Factory] Draft processed: {len(content)} chars for {campaign_id}")
        return content

    def _replace_image_placeholders(self, content: str, assets: List[str], alt_text: str = "") -> str:
        """
        V72.0: Surgical [IMAGE_N] replacement pass.
        Handles both standalone markers and markers already inside src/attributes.
        """

        # First pass: Handle cases where [IMAGE_N] is accidentally inside a src attribute
        # e.g. <img src="[IMAGE_1]" /> -> <img src="URL" />
        for i, url in enumerate(assets[:30], 1):
            placeholder = f"[IMAGE_{i}]"
            # Use regex to find [IMAGE_N] within quotes (src="[IMAGE_1]")
            src_pattern = rf'(src|href)=["\']\s*{re.escape(placeholder)}\s*["\']'
            content = re.sub(src_pattern, rf'\1="{url}"', content)

        # Second pass: Handle standalone markers
        for i, url in enumerate(assets[:30], 1):
            placeholder = f"[IMAGE_{i}]"
            if placeholder in content:
                figure_tag = f'<figure class="content-image"><img src="{str(url)}" alt="{alt_text}" loading="lazy" /></figure>'
                content = content.replace(placeholder, figure_tag)
                logger.debug(f"[Content Factory] Replaced standalone {placeholder}")
        
        # Strip any remaining unreplaced placeholders
        content = re.sub(r'\[IMAGE_\d+\]', '', content)
        return content
