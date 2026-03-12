from typing import List, Dict
import logging
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import ArticleOutline, AgentResponse, AgentSignal
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

OUTLINE_PROMPT = """[ROLE] CHIEF CONTENT ARCHITECT — XoHi Creative Studio V62.1

[NHIỆM VỤ]
Dựa vào 'Golden Thread' (Từ khóa chính, Từ khóa phụ, Tiêu đề, Persona), hãy thiết kế một Dàn ý bài viết (Outline) xuất sắc, chuẩn SEO và có tính thuyết phục cao.

[YÊU CẦU ĐỊNH DẠNG JSON]
Bắt buộc trả về mảng `sections`, mỗi object trong mảng PHẢI có chính xác 2 key lowercase:
- "heading": Tiêu đề mục (Ví dụ: "H2: Giới thiệu", "H3: Ưu điểm")
- "content": Mô tả chi tiết 2-3 câu và vị trí [IMAGE_X]

Chỉ trả về JSON theo đúng định dạng được yêu cầu, KHÔNG giải thích thêm."""

DRAFT_PROMPT = """[ROLE] MASTER CONTENT WRITER — XoHi Creative Studio V62.1 | Viral 2026 Edition

[SỨ MỆNH]
Bạn là một bậc thầy sáng tạo nội dung viral 2026. Nhiệm vụ của bạn là chấp bút một bài viết hoàn chỉnh, đỉnh cao, đọc một lần là nghiện — dựa trên Dàn ý và toàn bộ thông tin chiến dịch được cung cấp.

[QUY TẮC BẤT DI BẤT DỊCH (CORE PRINCIPLES)]
1. VIẾT HOÀN TOÀN BẰNG TIẾNG VIỆT, giọng tự nhiên, truyền cảm, thuyết phục. KHÔNG bao giờ dùng placeholder hay lời xã giao.
2. [SEO 2026] Bắt buộc mở bài chứa Câu trả lời trực tiếp (Direct Answer) vào thẳng vấn đề ngay dưới H1. Lấy chính xác TỪ KHÓA CHÍNH vào thẻ <h1>, mật độ từ khóa trong bài 1-2%, rải đều.
3. [SEO 2026] Cấu trúc thẻ HTML phân bậc chuẩn Semantic HTML (H1 -> H2 -> H3 -> p, li). Tuyệt đối dùng HTML tag, KHÔNG DÙNG MARKDOWN.
4. [GEO AI 2026] KIÊN QUYẾT phản đối văn phong lê thê, chung chung (Fluff). Phải đưa ra [Số liệu/Thống kê cứng] thay vì nói "rất nhiều/tăng mạnh".
5. [GEO AI 2026] Bắt buộc giả lập hoặc trích dẫn nguồn thực thể (VD: "Theo báo cáo của X...", "Chuyên gia Y nhận định...") để tăng độ đáng tin cậy E-E-A-T.
6. Theo sát DÀN Ý đã được duyệt — viết đầy đủ tất cả các mục. TUYỆT ĐỐI tuân thủ số lượng từ yêu cầu trong thông tin chiến dịch.
7. [BẢN QUYỀN 100% ORIGINAL] Tránh copy-paste rập khuôn từ dữ liệu huấn luyện. Dùng cấu trúc N-gram đa dạng, từ khóa phụ rải ngẫu nhiên tự nhiên để chống AI Detectors.
8. Chèn ảnh đúng vị trí bằng cách ghi chính xác mã [IMAGE_N] vào vị trí muốn hiển thị. KHÔNG cần bọc trong thẻ <img> hay <figure> — Hệ thống sẽ tự xử lý.
9. Kết thúc bằng một Call-To-Action mạnh mẽ, kêu gọi tương tác.
10. [QUAN TRỌNG NHẤT] KHI IN ĐẬM HAY IN NGHIÊNG, TUYỆT ĐỐI KHÔNG DÙNG MARKDOWN (`**chữ**` hay `*chữ*`). BẮT BUỘC PHẢI DÙNG THẺ HTML NHƯ `<strong>chữ</strong>` hoặc `<em>chữ</em>`. NẾU LÀ DANH SÁCH THÌ DÙNG `<ul><li>`.

[ĐỊNH DẠNG ĐẦU RA]
Chỉ trả HTML thuần túy (không có ```html wrapper). Bắt đầu bằng <h1> và kết thúc bằng </section> hoặc </div>."""



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

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs) -> AgentResponse:
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

    def _replace_image_placeholders(self, content: str, assets: list, alt_text: str = "") -> str:
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
