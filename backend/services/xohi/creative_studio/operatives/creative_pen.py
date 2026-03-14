from typing import List, Dict, Union, Optional
import logging
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import ArticleOutline, AgentResponse, AgentSignal
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

OUTLINE_PROMPT = """[ROLE] VIRAL CONTENT ARCHITECT — XoHi Creative Studio V65.0

[CHIẾN THUẬT: VIRAL HOOK LOOP]
Tập trung 90% hiệu quả vào Tiêu đề (Hook) và Ý chốt (Reward). 

[NHIỆM VỤ]
Thiết kế Dàn ý (Outline) chuẩn "Xương sườn" tối giản theo cấu trúc sau:
1. **HOOK (H1 & Intro)**: Phải cực gắt, gây tranh cãi hoặc đưa giải pháp sốc để giữ chân 3s đầu.
2. **RETAIN (Thân bài)**: Chia nhỏ thành các gạch đầu dòng ngắn gọn, súc tích để người đọc không bị ngộp.
3. **REWARD (CTA)**: Kết thúc bằng một giá trị thực tế hoặc lời kêu gọi đánh vào cảm xúc/tâm lý người đọc.

[YÊU CẦU ĐỊNH DẠNG JSON]
Bắt buộc trả về mảng `sections`, mỗi object trong mảng PHẢI có chính xác 2 key lowercase:
- "heading": Tiêu đề mục (Ví dụ: "H1: [HOOK] Nội dung cực gắt", "H2: Tiêu đề mục")
- "content": Các gạch đầu dòng (Bullet points) chuẩn sườn bài và vị trí [IMAGE_X].

Chỉ trả về JSON, KHÔNG giải thích thêm."""

DRAFT_PROMPT = """[ROLE] VIRAL PR WRITER — XoHi Creative Studio V65.0 | Viral Hook Loop Engine

[CHIẾN THUẬT: VIRAL HOOK LOOP]
Người dùng hiện nay đọc Tiêu đề và Đoạn kết chiếm 90% sự quan tâm. Bạn phải dồn toàn lực vào 2 phần này.

[QUY TẮC VIẾT BÀI]
1. **HOOK (Mở bài)**: <h1> phải là một cú đấm tâm lý. Ngay dưới <h1> phải là câu trả lời trực tiếp hoặc một lời khẳng định gây tò mò cực độ.
2. **RETAIN (Thân bài)**: Dựa trên dàn ý sườn bài, viết các đoạn văn cực kỳ cô đọng. Tuyệt đối không viết lan man (Fluff). Mỗi mục H2 chỉ nên có 1-2 đoạn văn ngắn.
3. **REWARD (Kết bài)**: Đoạn <section class="cta"> phải là phần "Thưởng" cho người đọc. Một lời kêu gọi (CTA) mạnh mẽ, đánh đúng vào nỗi sợ, sự tò mò hoặc lợi ích thực tế của họ.

[KỸ THUẬT CHUNG]
- Dùng thẻ HTML (<h1>, <h2>, <p>, <strong>, <ul>, <li>...). KHÔNG dùng Markdown.
- Chèn [IMAGE_N] đúng vị trí từ dàn ý.
- Văn phong: Tiếng Việt tự nhiên, sắc sảo, có tính thuyết phục cao.
- Độ dài: Tuân thủ số từ yêu cầu (word_count).

Chỉ trả về HTML thuần túy. Bắt đầu bằng <h1>."""



class CreativePen:
    """
    Step 3 & 4: Generate Outline and Draft Content.
    V62.1: Full AI-powered content generation with Golden Thread injection.
    """
    def __init__(self, model_name: str = "gemini-1.5-pro"):
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
            campaign.outline_data = outline.model_dump()
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
        
        prompt = f"""
        [THÔNG TIN GOLDEN THREAD]
        - Tiêu đề dự kiến: {title}
        - Từ khóa chính: {primary}
        - Từ khóa phụ: {secondary}
        - Phong cách (Persona): {persona}
        - Số lượng ảnh khả dụng: {num_assets} ảnh. Chỉ định vị trí chèn từ [IMAGE_1] đến [IMAGE_{num_assets}] (nếu có ảnh).
        - GIỚI HẠN: Dàn ý PHẢI có đúng {max_sections} mục chính (H2).
        
        Hãy sinh Dàn Ý (ArticleOutline) với đúng {max_sections} mục chính.
        """
        
        try:
            logger.info(f"[Content Factory] CreativePen generating outline for {campaign.id}")
            result = await trinity_bridge.run(self.outline_agent, prompt, session_id=campaign.id)
            return result.data if hasattr(result, "data") else result.output
        except Exception as e:
            logger.error(f"[Content Factory] CreativePen Outline Gen Error: {e}")
            raise  # Re-raise instead of returning fallback ArticleOutline

    async def write_draft(self, campaign: ContentCampaign) -> str:
        """
        Step 4: Generate REAL full-length viral content using AI.
        V71.0: Full Golden Thread injection + Outline + Guaranteed Asset Placement.
        """
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
        
        # V72.0: Strict Paragraph Count Injection
        max_sections = int(config.get("max_sections", 3))
        # Roughly 1-2 paragraphs per segment to keep total paragraph count under control
        paras_per_section = 1 if max_sections >= 8 else 2

        prompt = f"""
[THÔNG TIN CHIẾN DỊCH NỘI DUNG]

## GOLDEN THREAD (Cốt lõi không thể thay đổi)
- Tiêu đề bài viết: {title}
- Từ khóa CHÍNH (phải xuất hiện nhiều nhất): **{primary}**
- Từ khóa PHỤ (phân bổ tự nhiên): {', '.join(secondary_list)}
- Phong cách viết (Persona): {persona}

## DÀN Ý ĐÃ ĐƯỢC DUYỆT (BƯỚC 3)
Viết đầy đủ và đúng thứ tự tất cả các mục sau:
{outline_text}

## KHO ẢNH ĐÃ ĐƯỢC CHỌN (BƯỚC 2)
{avatar_context}
{asset_context}

## YÊU CẦU BẮT BUỘC (CRITICAL ENFORCEMENT)
- Bắt đầu bài viết bằng: <h1>{title}</h1>
- **GIỚI HẠN ĐOẠN VĂN**: Mỗi mục (H2/H3) CHỈ ĐƯỢC PHÉP có tối đa {paras_per_section} đoạn văn (<p>). Tổng bài viết KHÔNG QUÁ {max_sections * 2} đoạn văn. Đây là yêu cầu quan trọng để đảm bảo tính cô đọng.
- Chèn mã [IMAGE_N] vào vị trí muốn hiển thị. Bạn có thể ghi [IMAGE_N] đứng một mình hoặc chèn vào giữa văn bản.
- **ĐỘ DÀI BẮT BUỘC**: Bài viết PHẢI nằm trong khoảng từ {min_words} đến {max_words} từ.
- Giàu thông tin, hấp dẫn và viral.
- Kết thúc bằng một đoạn <section class="cta"> với Call-To-Action mạnh mẽ liên quan đến "{primary}".
- KHÔNG thêm lời dẫn hay giải thích. Chỉ trả về HTML thuần.

Bắt đầu viết ngay:
"""
        
        try:
            logger.info(f"[Content Factory] CreativePen V71.0 writing full draft for {campaign.id}")
            result = await trinity_bridge.run(self.draft_agent, prompt, session_id=campaign.id)
            content = result.data if hasattr(result, "data") else str(result.output)

            # Sanitize: remove markdown code fences if AI wraps them
            if content.startswith("```"):
                content = content.split("```", 2)[-1] if "```" in content[3:] else content[3:]
                content = content.lstrip("html\n").rstrip("`")

            # V70.0 Fix: Guaranteed [IMAGE_N] replacement
            content = self._replace_image_placeholders(content, assets, primary)

            logger.info(f"[Content Factory] Draft generated: {len(content)} chars for {campaign.id}")
            return content

        except Exception as e:
            logger.error(f"[Content Factory] CreativePen Draft Gen Error: {e}")
            raise  # Re-raise instead of returning fallback content

    def _replace_image_placeholders(self, content: str, assets: List[str], alt_text: str = "") -> str:
        """
        V72.0: Surgical [IMAGE_N] replacement pass.
        Handles both standalone markers and markers already inside src/attributes.
        """
        import re
        
        # First pass: Handle cases where [IMAGE_N] is accidentally inside a src attribute
        # e.g. <img src="[IMAGE_1]" /> -> <img src="URL" />
        for i, url in enumerate(assets[:30], 1):
            placeholder = f"[IMAGE_{i}]"
            # Use regex to find [IMAGE_N] within quotes (src="[IMAGE_1]")
            src_pattern = rf'(src|href)=["\']\s*{re.escape(placeholder)}\s*["\']'
            content = re.sub(src_pattern, rf'\1="{url}"', content)

        # Second pass: Handle standalone markers
        # e.g. [IMAGE_1] -> <figure><img src="URL" /></figure>
        for i, url in enumerate(assets[:30], 1):
            placeholder = f"[IMAGE_{i}]"
            if placeholder in content:
                figure_tag = f'<figure class="content-image"><img src="{url}" alt="{alt_text}" loading="lazy" /></figure>'
                content = content.replace(placeholder, figure_tag)
                logger.debug(f"[Content Factory] Replaced standalone {placeholder}")
        
        # Strip any remaining unreplaced placeholders
        content = re.sub(r'\[IMAGE_\d+\]', '', content)
        return content
