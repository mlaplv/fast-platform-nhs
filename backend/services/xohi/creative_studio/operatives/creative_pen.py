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

[YÊU CẦU CHẤT LƯỢNG]
1. Cấu trúc rõ ràng: Bao gồm các thẻ H2, H3 mạch lạc.
2. Tiêu đề mục (Heading): Hấp dẫn, chứa từ khóa một cách tự nhiên. Bắt đầu bằng 'H2:' hoặc 'H3:'.
3. Mô tả nội dung (Content): Tóm tắt chi tiết 2-3 câu về những gì sẽ viết trong mục này. Tông giọng phải khớp với Persona.
4. Chèn Ảnh (Image Placement): Dựa vào số lượng ảnh được cung cấp, hãy chỉ định vị trí chèn ảnh bằng tag [IMAGE_1], [IMAGE_2]... vào cuối phần 'Content' của mục phù hợp nhất (thường là H2 quan trọng). KHÔNG vượt quá số lượng ảnh đang có.
5. Từ khóa: Phân bổ rải rác Từ khóa phụ vào các H2/H3.

[ĐẦU RA]
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
6. Theo sát DÀN Ý đã được duyệt — viết đầy đủ tất cả các mục. Mỗi đoạn H2 tối thiểu 150 từ, H3 tối thiểu 80 từ. Bài viết tổng thể tối thiểu 1000 từ.
7. [BẢN QUYỀN 100% ORIGINAL] Tránh copy-paste rập khuôn từ dữ liệu huấn luyện. Dùng cấu trúc N-gram đa dạng, từ khóa phụ rải ngẫu nhiên tự nhiên để chống AI Detectors.
8. Chèn ảnh đúng vị trí [IMAGE_N] đã được định vị trong dàn ý bằng thẻ <figure>. KHÔNG tạo thêm IMAGE placeholder nào.
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
        self.outline_agent = Agent(
            output_type=ArticleOutline,
            system_prompt=OUTLINE_PROMPT
        )

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
                data={"content_preview": content[:200]}
            )
        
        return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message=f"Invalid step {step} for CreativePen")

    async def generate_outline(self, campaign: ContentCampaign) -> ArticleOutline:
        """
        Step 3: Generate a technical outline based on Golden Thread.
        """
        gold = campaign.gold_metadata or {}
        primary = gold.get("primary_keyword", "N/A")
        secondary = ", ".join(gold.get("secondary_keywords", []))
        title = gold.get("title", "Bài viết mới")
        persona = gold.get("persona", "Chuyên gia")
        
        assets = campaign.assets_data or []
        num_assets = len(assets)
        
        prompt = f"""
        [THÔNG TIN GOLDEN THREAD]
        - Tiêu đề dự kiến: {title}
        - Từ khóa chính: {primary}
        - Từ khóa phụ: {secondary}
        - Phong cách (Persona): {persona}
        - Số lượng ảnh khả dụng: {num_assets} ảnh. Chỉ định vị trí chèn từ [IMAGE_1] đến [IMAGE_{num_assets}] (nếu có ảnh).
        
        Hãy sinh Dàn Ý (ArticleOutline).
        """
        
        try:
            logger.info(f"[Content Factory] CreativePen generating outline for {campaign.id}")
            result = await trinity_bridge.run(self.outline_agent, prompt)
            return result.data if hasattr(result, "data") else result.output
        except Exception as e:
            logger.error(f"[Content Factory] CreativePen Outline Gen Error: {e}")
            return ArticleOutline(sections=[
                {"heading": f"H2: {title}", "content": f"Giới thiệu tổng quan về {primary} theo phong cách {persona}."},
                {"heading": f"H2: Tại sao nên chọn {primary}", "content": "Phân tích lợi ích chuyên sâu. " + ("[IMAGE_1]" if num_assets > 0 else "")},
                {"heading": "H2: Kết luận", "content": "Tóm tắt và kêu gọi hành động."}
            ])

    async def write_draft(self, campaign: ContentCampaign) -> str:
        """
        Step 4: Generate REAL full-length viral content using AI.
        V62.1: Full Golden Thread injection + Outline + Asset placement.
        """
        gold = campaign.gold_metadata or {}
        outline_data = campaign.outline_data or {}
        assets = campaign.assets_data or []
        
        # --- BUILD FULL CONTEXT ---
        primary = gold.get("primary_keyword", "chủ đề chính")
        secondary_list = gold.get("secondary_keywords", [])
        title = gold.get("title", primary)
        persona = gold.get("persona", "Chuyên gia")
        
        # Format outline for the AI
        sections = outline_data.get("sections", [])
        outline_text = "\n".join([
            f"  - {s.get('heading', '')}: {s.get('content', '')}"
            for s in sections
        ]) if sections else f"  - H2: {title}: Giới thiệu tổng quan.\n  - H2: Chi tiết: Nội dung chuyên sâu.\n  - H2: Kết luận: Tổng kết và CTA."
        
        # Format asset list with descriptions
        asset_lines = []
        for i, url in enumerate(assets[:8], 1):  # Max 8 images
            asset_lines.append(f"  [IMAGE_{i}]: {url}")
        asset_context = "\n".join(asset_lines) if asset_lines else "  (Không có ảnh)"
        
        # Avatar context
        avatar_url = gold.get("avatar", assets[0] if assets else None)
        avatar_context = f"  Ảnh đại diện (thumbnail): {avatar_url}" if avatar_url else "  (Chưa có ảnh đại diện)"
        
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

## YÊU CẦU
- Bắt đầu bài viết bằng: <h1>{title}</h1>
- Chèn các IMAGE_N đúng vị trí đã chỉ định trong dàn ý bằng cú pháp: <figure><img src="[IMAGE_N]" alt="{primary}" /></figure>
- Bài viết tối thiểu 1200 từ, giàu thông tin, hấp dẫn và viral.
- Kết thúc bằng một đoạn <section class="cta"> với Call-To-Action mạnh mẽ liên quan đến "{primary}".
- KHÔNG thêm lời dẫn hay giải thích. Chỉ trả về HTML thuần.

Bắt đầu viết ngay:
"""
        
        try:
            logger.info(f"[Content Factory] CreativePen V62.1 writing full draft for {campaign.id}")
            # Use a simple text agent (no structured output needed)
            draft_agent = Agent(system_prompt=DRAFT_PROMPT)
            result = await trinity_bridge.run(draft_agent, prompt)
            content = result.data if hasattr(result, "data") else str(result.output)
            
            # Sanitize: remove markdown code fences if AI wraps them
            if content.startswith("```"):
                content = content.split("```", 2)[-1] if "```" in content[3:] else content[3:]
                content = content.lstrip("html\n").rstrip("`")
            
            logger.info(f"[Content Factory] Draft generated: {len(content)} chars for {campaign.id}")
            return content
            
        except Exception as e:
            logger.error(f"[Content Factory] CreativePen Draft Gen Error: {e}")
            # Graceful fallback with real structure
            sections_html = ""
            for i, section in enumerate(sections):
                heading_raw = section.get("heading", "")
                tag = "h2" if heading_raw.upper().startswith("H2") else "h3"
                heading_text = heading_raw.replace("H2:", "").replace("H3:", "").replace("h2:", "").replace("h3:", "").strip()
                content_text = section.get("content", "")
                # Replace [IMAGE_N] placeholders with figure tags
                for j, url in enumerate(assets[:8], 1):
                    content_text = content_text.replace(
                        f"[IMAGE_{j}]",
                        f'<figure><img src="{url}" alt="{primary}" class="content-image" /></figure>'
                    )
                sections_html += f"<{tag}>{heading_text}</{tag}>\n<p>{content_text}</p>\n"
            
            return f"""<h1>{title}</h1>
<p>Bài viết chuyên sâu về <strong>{primary}</strong> theo phong cách {persona}.</p>
{sections_html}
<section class="cta">
  <h2>Kết luận</h2>
  <p>Hy vọng bài viết này giúp bạn hiểu rõ hơn về <strong>{primary}</strong>. Hãy để lại bình luận hoặc liên hệ với chúng tôi để được tư vấn thêm!</p>
</section>"""
