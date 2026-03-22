import logging
import re
import asyncio
import gc
from typing import List, Dict, Union, Optional
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import ArticleOutline, AgentResponse, AgentSignal
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner

logger = logging.getLogger("api-gateway")

OUTLINE_PROMPT = """[ROLE] TỔNG BIÊN TẬP — Điều phối nội dung XoHi 2026
[CHIẾN THUẬT "THUẦN VIỆT 100%" - R03 ELITE]
1. TRỌNG TÂM (STRICT PRIORITY):
    - Ưu tiên 1: Tiêu đề + Từ khóa chính.
    - Ưu tiên 2: Từ khóa chính + Từ khóa phụ.
    - Ưu tiên 3: Từ khóa chính + Bối cảnh từ Mô tả (Description).
2. CẤM DỊCH THUẬT: Giữ nguyên 100% tên thương hiệu và danh từ riêng bằng tiếng Việt (Vd: "Thương hiệu A" giữ nguyên).
3. ĐỊNH DẠNG SECTION:
   - 1 Câu Sapô chủ chốt dẫn dắt nội dung.
   - 1 Gạch đầu dòng duy nhất chứa ý chính của đoạn.
4. TỔNG SỐ ĐOẠN: Đúng số lượng `max_sections`.
5. TUYỆT ĐỐI: Không chèn [IMAGE_X], không viết bài báo hoàn chỉnh.

[YÊU CẦU ĐỊNH DẠNG JSON]
Trả về mảng `sections`, mỗi object:
- "heading": Tiêu đề mục (H2: ...)
- "content": [1 Câu Sapô] + [1 Gạch đầu dòng ý chính]

Chỉ trả về JSON, KHÔNG giải thích thêm.
"""

DRAFT_PROMPT = """[ROLE] KỸ SƯ NỘI ĐỘNG LỰC — XoHi Media V2026
[TIÊU CHUẨN KỸ THUẬT NỘI DUNG]
1. **MẬT ĐỘ TỪ KHÓA**: Đan xen Từ khóa chính/phụ một cách tự nhiên nhưng bền bỉ (Mật độ 1.5-2%).
2. **TÍNH NHẤT QUÁN CẤU TRÚC**: Tuyệt đối tuân thủ Dàn ý từ Bước 3. Mỗi gạch đầu dòng phải được triển khai thành các đoạn văn có chiều sâu, giàu thông tin.
3. **NHỊP ĐIỆU ĐỘNG**: Điều chỉnh độ dài đoạn văn theo Chế độ nội dung (Viral: ngắn gọn, dồn dập; Deep-dive: phân tích đa chiều).

[THUẬT TOÁN CHÈN ẢNH - CHIẾN THUẬT THUẦN VIỆT]
- Phân tích "Giá trị bối cảnh" của từng phần dựa trên Title và Mô tả.
- Chèn mã [IMAGE_X] vào vị trí có giá trị minh họa cao nhất.
- Đảm bảo bối cảnh hình ảnh (Vietnamese Context) bổ trợ trực tiếp cho luận điểm.
- CẤM DỊCH tên sản phẩm/thương hiệu sang tiếng Anh trong bài viết.

[YÊU CẦU HTML]
- Trả về mã HTML thuần (h1, h2, p, figure, section). 
- **ĐỘ SÂU NỘI DUNG**: Mỗi mục H2 phải có ít nhất 2 đoạn văn (<p>) phân tích chuyên sâu.
- KHÔNG giải thích, KHÔNG dùng Markdown code fences.
- KHÔNG trả về JSON.
"""



class CreativePen:
    """
    Step 3 & 4: Generate Outline and Draft Content.
    V62.1: Full AI-powered content generation with Golden Thread injection.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name

        # CNS V76: Global-like semaphore for Pen tasks to protect VPS RAM
        self.pen_semaphore = asyncio.Semaphore(1)

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

        async with self.pen_semaphore:
            step: Optional[int] = kwargs.get("step")
            if step == 3:
                # R110: Explicit type handling for Pydantic/Dict variants
                outline: Union[ArticleOutline, Dict[str, object], None] = await self.generate_outline(campaign)

                if isinstance(outline, ArticleOutline):
                    campaign.outline_data = outline.model_dump()
                elif isinstance(outline, dict):
                    campaign.outline_data = outline
                else:
                    logger.error(f"[Content Factory] Outline generation failed or returned invalid type: {type(outline)}")
                    campaign.outline_data = {"error": "Invalid outline format"}

                return AgentResponse(
                    signal=AgentSignal.PROCEED_NEXT,
                    message="Outline generated based on Golden Thread.",
                    data=campaign.outline_data
                )
            elif step == 4:
                logger.info(f"[CreativePen] Phase 76: Drafting full content for {campaign_id}")
                content = await self.write_draft(campaign)
                campaign.draft_content = content
                return AgentResponse(
                    signal=AgentSignal.PROCEED_NEXT,
                    message="Draft content generated — Viral 2026 Edition.",
                    data={"content": content}
                )

            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message=f"Invalid step {step} for CreativePen")

    async def generate_outline(self, campaign: ContentCampaign) -> Union[ArticleOutline, Dict[str, object], None]:
        """
        Step 3: Generate a technical outline based on Golden Thread.
        Now using Standardized Golden Context Helpers.
        """
        primary = campaign.get_gold_val("primary_keyword", "N/A")
        secondary = ", ".join(campaign.get_gold_val("secondary_keywords", []))
        description = campaign.get_gold_val("description", "")
        title = campaign.get_gold_val("title", "Bài viết mới")
        persona = campaign.get_gold_val("persona", "Chuyên gia")
        
        assets = campaign.assets_data or []
        num_assets = len(assets)
        
        # Phase 71: Strict Section Control
        config = campaign.get_gold_config()
        max_sections = config.get("max_sections", 3)
        
        instruction = f"""
        Hãy sinh Dàn Ý (ArticleOutline) với đúng {max_sections} mục chính. Trả về đúng schema JSON. 
        Mỗi mục trong `content` chỉ gồm DUY NHẤT: 01 câu Sapô chủ chốt và 01 gạch đầu dòng ý chính.
        Tuyệt đối KHÔNG chèn bất kỳ thẻ hình ảnh nào.
        """
        
        # Phase 76.5: Context De-noising before AI injection
        title_clean = await noise_cleaner.clean(title, mode="standard")
        primary_clean = await noise_cleaner.clean(primary, mode="standard")
        
        prompt = f"""
        [THUẦN VIỆT - THỨ TỰ ƯU TIÊN GOLDEN THREAD]
        1. Tiêu đề: {title_clean}
        2. Từ khóa CHÍNH: {primary_clean}
        3. Từ khóa bổ trợ: {secondary}
        4. Mô tả bối cảnh: {description}
        
        - Phong cách (Persona): {persona}
        - GIỚI HẠN: {max_sections} mục H2.
        Cần một dàn ý BÁO CHÍ thuần Việt, tập trung vào giá trị thông tin và bối cảnh Việt Nam.
        """
        
        try:
            logger.info(f"[Content Factory] CreativePen generating outline for {campaign.id} using {self.model_name}")
            result = await trinity_bridge.run(self.outline_agent, f"{instruction}\n{prompt}", session_id=campaign.id, model=self.model_name)

            if result is None:
                logger.error(f"[Content Factory] trinity_bridge.run returned None for campaign {campaign.id}")
                return None

            # Phase 76.9: Robust Unwrapper
            raw_data = None
            if hasattr(result, "data"):
                raw_data = result.data
            elif hasattr(result, "output"):
                raw_data = result.output
            else:
                raw_data = result

            if raw_data is None:
                logger.error(f"[Content Factory] raw_data is None after unwrapping result of type {type(result)}")
                return None

            # Extra check: if raw_data is still an AgentRunResult (leakage protection)
            if type(raw_data).__name__ == "AgentRunResult":
                raw_data = getattr(raw_data, "data", raw_data)

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
                return raw_data
            
            if hasattr(raw_data, "__dict__"):
                return raw_data

            logger.warning(f"[Content Factory] Unexpected outline format: {type(raw_data)}. Returning as-is.")
            return raw_data
        except Exception as e:
            logger.error(f"[Content Factory] CreativePen Outline Gen Error: {e}", exc_info=True)
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
                async for text in stream.stream_text(delta=True):
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

    async def _build_draft_prompt(self, campaign: ContentCampaign) -> tuple[str, List[str], str]:
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

        # Extract actual URL strings from mixed asset payloads
        clean_assets = []
        for a in assets:
            if isinstance(a, dict):
                clean_assets.append(a.get("file_path") or a.get("url") or str(a))
            elif hasattr(a, "file_path"):
                clean_assets.append(getattr(a, "file_path") or getattr(a, "url") or str(a))
            else:
                clean_assets.append(str(a))

        # Format asset list with descriptions
        asset_lines = [f"  [IMAGE_{i}]: {url}" for i, url in enumerate(clean_assets[:12], 1)]
        asset_context = "\n".join(asset_lines) if asset_lines else "  (Không có ảnh)"

        # Avatar context
        avatar_raw = campaign.get_gold_val("avatar", assets[0] if assets else None)
        if isinstance(avatar_raw, dict):
            avatar_url = avatar_raw.get("file_path") or avatar_raw.get("url") or ""
        elif hasattr(avatar_raw, "file_path"):
            avatar_url = getattr(avatar_raw, "file_path") or getattr(avatar_raw, "url") or ""
        else:
            avatar_url = str(avatar_raw) if avatar_raw else ""
            
        avatar_context = f"  Ảnh đại diện (thumbnail): {avatar_url}" if avatar_url else "  (Chưa có ảnh đại diện)"

        # Phase 71: Strict Word Count Enforcement (90% - 120% Range)
        config = campaign.get_gold_config()
        # R105 & Memory Shield: Clamp word count to prevent OOM/hallucinations on 2GB VPS
        raw_target = config.get("word_count", 500)
        try:
            target_words = int(raw_target)
        except (ValueError, TypeError):
            target_words = 500

        target_words = min(max(target_words, 100), 2500)
        min_words = int(target_words * 0.9)
        max_words = int(target_words * 1.2)

        # V76.0: Adaptive Paragraph Control (Deep Dive Support)
        max_sections = int(config.get("max_sections", 3))
        content_mode = config.get("content_mode", "viral") # default to viral

        if content_mode == "deep_dive":
            paras_per_section = 4 # Allow more depth for analytical content
            total_para_limit = max_sections * 5
            mode_instruction = "Viết chi tiết, phân tích sâu sắc, cung cấp nhiều giá trị chuyên môn."
        elif content_mode == "normal":
            paras_per_section = 2
            total_para_limit = max_sections * 3
            mode_instruction = "Viết theo phong cách báo chí, tin tức, khách quan và chuyên nghiệp."
        else:
            # Roughly 1-2 paragraphs per segment to keep total paragraph count under control
            paras_per_section = 1 if max_sections >= 8 else 2
            total_para_limit = max_sections * 2
            mode_instruction = "Viết cực kỳ cô đọng, tập trung vào tính viral và nhịp điệu nhanh (Fast-paced)."

        prompt = f"""
[THÔNG TIN CHIẾN DỊCH NỘI DUNG - CHIẾN THUẬT THUẦN VIỆT]

## GOLDEN THREAD (Thứ tự ưu tiên 1-2-3-4)
- **Ưu tiên 1 (Tiêu đề)**: {title}
- **Ưu tiên 2 (Từ khóa CHÍNH)**: **{primary}** (Bắt buộc giữ nguyên tên tiếng Việt, cấm dịch)
- **Ưu tiên 3 (Từ khóa PHỤ)**: {', '.join(secondary_list)}
- **Ưu tiên 4 (Mô tả)**: {campaign.get_gold_val("description", "")}

- Phong cách: {persona}
- Chế độ nội dung: {content_mode.upper()} ({mode_instruction})

## DÀN Ý ĐÃ ĐƯỢC DUYỆT (BƯỚC 3)
{outline_text}

## KHO ẢNH VIỆT NAM (BƯỚC 2)
{avatar_context}
{asset_context}

## YÊU CẦU BẮT BUỘC (CRITICAL ENFORCEMENT)
- Bắt đầu bài viết bằng: <h1>{title}</h1>
- **GIỚI HẠN ĐOẠN VĂN**: Mỗi mục (H2/H3) CHỈ ĐƯỢC PHÉP có tối đa {paras_per_section} đoạn văn (<p>). Tổng bài viết KHÔNG QUÁ {total_para_limit} đoạn văn.
- Chèn mã [IMAGE_N] vào vị trí muốn hiển thị. Bạn có thể ghi [IMAGE_N] đứng một mình hoặc chèn vào giữa văn bản.
- **ĐỘ DÀI BẮT BUỘC**: Bài viết PHẢI nằm trong khoảng từ {min_words} đến {max_words} từ.
- Giàu thông tin, hấp dẫn và mang đậm bản sắc Việt Nam. Tuyệt đối không sử dụng văn phong dịch máy.
- Kết thúc bằng một đoạn <section class=\"cta\"> với Call-To-Action mạnh mẽ liên quan đến \"{primary}\".
- KHÔNG thêm lời dẫn hay giải thích. Chỉ trả về HTML thuần.
"""
        return prompt, assets, primary

    async def _process_draft_content(self, content: str, assets: List[str], primary: str, campaign_id: str) -> str:
        """Helper to sanitize and clean content (Shared)."""
        import gc
        # Sanitize: remove markdown code fences if AI wraps them
        if content.startswith("```"):
            content = content.split("```", 2)[-1] if "```" in content[3:] else content[3:]
            content = content.lstrip("html\n").rstrip("`")

        # Phase 70.0 Fix: Guaranteed [IMAGE_N] replacement
        content = self._replace_image_placeholders(content, assets, primary)

        # Phase 76.5: Hybrid Noise Shield - Draft Deep Cleaning
        content = await noise_cleaner.clean(content, mode="aggressive")

        logger.info(f"[Content Factory] Draft processed: {len(content)} chars for {campaign_id}")

        # Memory discipline: Force GC after large string manipulations
        gc.collect()

        return content

    def _replace_image_placeholders(self, content: str, assets: List[str], alt_text: str = "") -> str:
        """
        V72.0: Surgical [IMAGE_N] replacement pass.
        Handles both standalone markers and markers already inside src/attributes.
        """
        clean_assets = []
        for a in assets:
            if isinstance(a, dict):
                clean_assets.append(a.get("file_path") or a.get("url") or str(a))
            elif hasattr(a, "file_path"):
                clean_assets.append(getattr(a, "file_path") or getattr(a, "url") or str(a))
            else:
                clean_assets.append(str(a))

        # First pass: Handle cases where [IMAGE_N] is accidentally inside a src attribute
        # e.g. <img src="[IMAGE_1]" /> -> <img src="URL" />
        for i, url in enumerate(clean_assets[:30], 1):
            placeholder = f"[IMAGE_{i}]"
            # Use regex to find [IMAGE_N] within quotes (src="[IMAGE_1]")
            src_pattern = rf'(src|href)=["\']\s*{re.escape(placeholder)}\s*["\']'
            content = re.sub(src_pattern, rf'\1="{url}"', content)

        # Second pass: Handle standalone markers
        for i, url in enumerate(clean_assets[:30], 1):
            placeholder = f"[IMAGE_{i}]"
            if placeholder in content:
                figure_tag = f'<figure class="content-image"><img src="{str(url)}" alt="{alt_text}" loading="lazy" /></figure>'
                content = content.replace(placeholder, figure_tag)
                logger.debug(f"[Content Factory] Replaced standalone {placeholder}")
        
        # Strip any remaining unreplaced placeholders
        content = re.sub(r'\[IMAGE_\d+\]', '', content)
        return content
