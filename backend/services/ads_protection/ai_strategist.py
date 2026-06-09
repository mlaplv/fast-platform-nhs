"""
AI Strategist — Xohi Strategic Engine for Google Ads 2026
Thực hiện trinh sát đối thủ, đối soát luật Google và đưa ra gợi ý tối ưu.
"""
from __future__ import annotations
import logging
import httpx
from typing import Optional

from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.google_search import google_search_service
from backend.services.ads_protection.schemas import (
    AISuggestionRequest,
    AISuggestionResponse,
    CompetitorAnalysisRequest,
    CompetitorAnalysisResponse,
    PMaxAssetGroupResponse,
)

logger = logging.getLogger("ads_protection.ai_strategist")

class AIStrategist:
    """
    Hệ thống trí tuệ chiến lược cho Google Ads.
    Tích hợp trinh sát web và kiến thức chính sách Google 2026.
    """

    SYSTEM_PROMPT = (
        "Bạn là Xohi — Trợ lý AI Chiến lược cho Google Ads Elite V2.6.\n"
        "Nhiệm vụ của bạn là phân tích đối thủ và đưa ra gợi ý chiến dịch quảng cáo tối ưu nhất.\n\n"
        "QUY TẮC CỐT LÕI 2026 (SGE & SEO):\n"
        "1. SGE Compliance: Nội dung phải trả lời trực tiếp câu hỏi của người dùng, có cấu trúc dữ liệu (Schema.org) rõ ràng.\n"
        "2. Ads Quality Score: Landing Page phải khớp 100% với Keyword chủ đạo. H1 phải chứa Keyword.\n"
        "3. Tốc độ & LCP: Phải dưới 2.5s để không bị đánh tụt điểm.\n"
        "4. Google Ads AI Max: Yêu cầu tối thiểu 8-15 headlines và 4 descriptions.\n"
        "5. Thị trường VN 2026: Ưu tiên nội dung 'Mộc', chân thực, Brand-led Commerce.\n\n"
        "Khi nhận dữ liệu trinh sát đối thủ hoặc Landing Page, hãy tìm ra kẽ hở hoặc điểm cần tối ưu để Sếp thắng thế."
    )

    def __init__(self) -> None:
        self._agent = Agent(
            output_type=AISuggestionResponse,
            retries=2
        )
        self._pmax_agent = Agent(
            output_type=PMaxAssetGroupResponse,
            retries=2
        )

    async def _fetch_page(self, url: str) -> str:
        """Trinh sát nội dung Landing Page và phân tích SEO chuyên sâu."""
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Xohi-Neural-Scout/1.0"
                })
                if resp.status_code == 200:
                    from lxml import html
                    import json
                    import re
                    
                    content_bytes = resp.content
                    tree = html.fromstring(content_bytes)
                    
                    # 1. Title
                    title_list = tree.xpath("//title/text()")
                    title = title_list[0].strip() if title_list else ""
                    title_len = len(title)
                    
                    # 2. Meta Description
                    desc_list = tree.xpath("//meta[@name='description']/@content") or tree.xpath("//meta[@property='og:description']/@content")
                    meta_desc = desc_list[0].strip() if desc_list else ""
                    meta_desc_len = len(meta_desc)
                    
                    # 3. Canonical URL
                    canonical_list = tree.xpath("//link[@rel='canonical']/@href")
                    canonical_url = canonical_list[0].strip() if canonical_list else ""
                    
                    # 4. H1
                    h1_nodes = tree.xpath("//h1")
                    h1_count = len(h1_nodes)
                    h1_contents = [node.text_content().strip() for node in h1_nodes if node.text_content().strip()]
                    
                    # 5. Image Alt
                    img_nodes = tree.xpath("//img")
                    img_total = len(img_nodes)
                    img_missing_alt = 0
                    for img in img_nodes:
                        alt = img.get("alt")
                        if alt is None or not alt.strip():
                            img_missing_alt += 1
                            
                    # 6. Page Structure (Tables & Lists)
                    tables_count = len(tree.xpath("//table"))
                    lists_count = len(tree.xpath("//ul | //ol | //dl"))
                    
                    # 7. OG Image
                    og_img_list = tree.xpath("//meta[@property='og:image']/@content")
                    og_image = og_img_list[0].strip() if og_img_list else ""
                    
                    # 8. Author
                    author_list = tree.xpath("//meta[@name='author']/@content") or tree.xpath("//meta[@property='article:author']/@content")
                    author = author_list[0].strip() if author_list else ""
                    
                    # 9. JSON-LD Schema & Content JSON Extraction
                    schema_types = []
                    json_data_texts = []
                    
                    def extract_text_from_json(obj):
                        text_parts = []
                        if isinstance(obj, str):
                            s = obj.strip()
                            if s and not s.startswith("http") and not any(s.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]):
                                if "<" in s and ">" in s:
                                    try:
                                        sub_tree = html.fromstring(s)
                                        t = sub_tree.text_content().strip()
                                        if t:
                                            text_parts.append(t)
                                    except Exception:
                                        cleaned = re.sub(r'<[^>]+>', ' ', s)
                                        text_parts.append(cleaned)
                                else:
                                    text_parts.append(s)
                        elif isinstance(obj, dict):
                            for k, v in obj.items():
                                if k in ['id', 'status', 'statusText', 'headers', 'type', 'sku', 'image', 'images', 'thumbnail', 'url', 'href', 'class', 'style', 'color', 'background', 'logo']:
                                    continue
                                text_parts.extend(extract_text_from_json(v))
                        elif isinstance(obj, list):
                            for item in obj:
                                text_parts.extend(extract_text_from_json(item))
                        return text_parts

                    json_ld_nodes = tree.xpath("//script[@type='application/ld+json']")
                    for node in json_ld_nodes:
                        try:
                            js_text = node.text_content().strip()
                            if js_text:
                                data = json.loads(js_text)
                                def extract_types(obj):
                                    t_list = []
                                    if isinstance(obj, dict):
                                        if "@type" in obj:
                                            t = obj["@type"]
                                            if isinstance(t, list):
                                                t_list.extend(t)
                                            else:
                                                t_list.append(str(t))
                                        if "@graph" in obj and isinstance(obj["@graph"], list):
                                            for item in obj["@graph"]:
                                                t_list.extend(extract_types(item))
                                        for k, v in obj.items():
                                            if isinstance(v, (dict, list)):
                                                t_list.extend(extract_types(v))
                                    elif isinstance(obj, list):
                                        for item in obj:
                                            t_list.extend(extract_types(item))
                                    return t_list
                                
                                schema_types.extend(extract_types(data))
                                # Also extract text for SGE content analysis
                                json_data_texts.extend(extract_text_from_json(data))
                        except Exception as je:
                            logger.warning(f"Error parsing JSON-LD in _fetch_page: {je}")
                    
                    schema_types = sorted(list(set(schema_types)))

                    # Extract regular JSON scripts containing page data/reviews/faqs
                    json_nodes = tree.xpath("//script[@type='application/json']")
                    for node in json_nodes:
                        try:
                            js_text = node.text_content().strip()
                            if js_text:
                                data = json.loads(js_text)
                                if isinstance(data, dict) and 'body' in data:
                                    try:
                                        body_data = json.loads(data['body'])
                                        if isinstance(body_data, dict):
                                            if any(k in body_data for k in ['description', 'metadata', 'reviews', 'items', 'blocks', 'faqs']):
                                                json_data_texts.extend(extract_text_from_json(body_data))
                                    except Exception:
                                        pass
                                else:
                                    if isinstance(data, dict) and any(k in data for k in ['description', 'metadata', 'reviews', 'items', 'blocks', 'faqs']):
                                        json_data_texts.extend(extract_text_from_json(data))
                        except Exception as je:
                            logger.warning(f"Error parsing application/json in _fetch_page: {je}")

                    # 10. Clean body text for word count and content preview
                    for s in tree.xpath("//script|//style|//noscript|//iframe|//header|//footer|//nav"):
                        try:
                            s.getparent().remove(s)
                        except Exception:
                            pass
                            
                    # Strip common boilerplate classes and IDs to prevent noise in the SGE analysis
                    for el in list(tree.iter()):
                        if el.getparent() is None:
                            continue
                        
                        classes = [c.strip().lower() for c in el.get("class", "").split() if c.strip()]
                        el_id = el.get("id", "").strip().lower()
                        
                        remove_el = False
                        
                        # Match boilerplate identifiers (with substring matching)
                        for token in ['header', 'footer', 'menu', 'nav', 'sidebar']:
                            if any(token in c for c in classes) or token in el_id:
                                remove_el = True
                                break
                        
                        # Also target common compound boilerplate wrappers
                        for bp_class in ['site-header', 'site-footer', 'global-header', 'global-footer', 'main-nav', 'navbar', 'main-menu', 'sidebar-container', 'widget-area', 'social-links', 'footer-links', 'header-links', 'site-navigation']:
                            if bp_class in classes or bp_class in el_id:
                                remove_el = True
                                break
                                
                        # Do not remove if it looks like main product/content section
                        if remove_el:
                            protect_keywords = ['product', 'content', 'article', 'main', 'detail', 'body', 'page-title', 'description', 'review', 'comment']
                            if any(any(pk in c for pk in protect_keywords) for c in classes) or any(pk in el_id for pk in protect_keywords):
                                remove_el = False
                        
                        if remove_el:
                            try:
                                el.getparent().remove(el)
                            except Exception:
                                pass
                    
                    static_text = tree.text_content()
                    
                    # Deduplicate and combine all text parts to construct the full page representation
                    all_text_parts = [static_text] + json_data_texts
                    seen = set()
                    unique_text_parts = []
                    for part in all_text_parts:
                        part_clean = " ".join(part.split())
                        if part_clean and part_clean not in seen:
                            seen.add(part_clean)
                            unique_text_parts.append(part)
                            
                    body_text = "\n\n".join(unique_text_parts)
                    words = re.findall(r'\b\w+\b', body_text)
                    word_count = len(words)
                    
                    preview_text = " ".join(body_text.split())[:25000]
                    
                    audit_report = (
                        f"=== ON-PAGE SEO & SGE REAL-TIME AUDIT ===\n"
                        f"Target URL: {url}\n"
                        f"Title: \"{title}\" (Length: {title_len} chars)\n"
                        f"Meta Description: \"{meta_desc}\" (Length: {meta_desc_len} chars)\n"
                        f"Canonical Link: \"{canonical_url}\"\n"
                        f"H1 Count: {h1_count} (H1 Contents: {h1_contents})\n"
                        f"Images Count: {img_total} (Missing Alt Tags: {img_missing_alt})\n"
                        f"Page Structure: {tables_count} Tables, {lists_count} Lists\n"
                        f"OG Image: \"{og_image}\"\n"
                        f"Author: \"{author}\"\n"
                        f"Word Count: ~{word_count} words\n"
                        f"Detected JSON-LD Schemas ({len(schema_types)} total): {', '.join(schema_types)}\n"
                        f"=== LANDING PAGE CONTENT PREVIEW ===\n"
                        f"{preview_text}\n"
                        f"====================================="
                    )
                    return audit_report
                return f"Lỗi truy cập Landing Page (Status: {resp.status_code})"
        except Exception as e:
            return f"Lỗi kết nối trinh sát: {str(e)}"

    async def suggest(self, req: AISuggestionRequest) -> AISuggestionResponse:
        """Thực hiện trinh sát và đưa ra gợi ý."""
        logger.info("ai_suggest task=%s context=%s", req.task, req.context[:50])

        target_url = ""
        page_content = ""

        # Nếu task là AUDIT hoặc có URL trong context, thực hiện trinh sát URL
        if req.task == "AUDIT_LANDING_PAGE" or "http" in req.context:
            import re
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', req.context)
            if urls:
                target_url = urls[0]
                page_content = await self._fetch_page(target_url)

        # 1. Trinh sát đối thủ (Competitor Research)
        search_query = f"quảng cáo google {req.context} đối thủ cạnh tranh việt nam 2026"
        search_results = await google_search_service.search(search_query, num=3)
        
        competitor_context = ""
        if search_results:
            competitor_context = "\n".join([
                f"- {r.get('title')}: {r.get('snippet')}" for r in search_results
            ])
        else:
            competitor_context = "Không tìm thấy dữ liệu trinh sát trực tiếp."

        # 1.5 Lấy danh sách từ khóa hiện có của Ad Group
        keywords_context = ""
        if req.keywords:
            keywords_context = f"\nTỪ KHÓA MỤC TIÊU CỦA AD GROUP:\n" + "\n".join([f"- {k}" for k in req.keywords])

        # 2. Xây dựng Prompt Chiến thuật (Elite V2.6 Standard)
        task_directives = ""
        if req.task == "RSA":
            task_directives = """
            YÊU CẦU ĐẶC BIỆT CHO TÁC VỤ RSA (RESPONSIVE SEARCH AD):
            - BẮT BUỘC sinh đúng ĐỦ 15 tiêu đề (headlines) trong trường 'headlines'. Mỗi tiêu đề dài từ 10 đến TỐI ĐA 30 ký tự. KHÔNG được vượt quá 30 ký tự!
            - BẮT BUỘC sinh đúng ĐỦ 4 mô tả (descriptions) trong trường 'descriptions'. Mỗi mô tả dài từ 50 đến TỐI ĐA 90 ký tự. KHÔNG được vượt quá 90 ký tự!
            - BẮT BUỘC sinh 2 đường dẫn hiển thị ngắn gọn (display_path1 và display_path2) có liên quan đến sản phẩm/chiến dịch, dài tối đa 15 ký tự mỗi đường dẫn, không dấu, viết thường, ngăn cách bởi dấu gạch ngang (ví dụ: 'beppin-body', 'tri-tham').
            - BẮT BUỘC thực hiện chấm điểm độ mạnh quảng cáo (ad_strength) theo các tiêu chuẩn Google Ads:
                * headline_count_ok: True nếu sinh đủ 15 tiêu đề.
                * keyword_coverage_ok: True nếu có ít nhất 4 tiêu đề chứa chính xác các từ khóa mục tiêu đã cung cấp.
                * headline_uniqueness_ok: True nếu các tiêu đề có ý nghĩa và từ vựng độc đáo, không bị lặp lại ngữ nghĩa.
                * description_uniqueness_ok: True nếu 4 mô tả đa dạng, không trùng lặp câu chữ.
                * has_sitelinks: True (luôn khuyến nghị sếp cấu hình sitelink).
                * overall_strength: Đánh giá tổng thể ("POOR" | "AVERAGE" | "GOOD" | "EXCELLENT"). Nếu tất cả ok thì là "EXCELLENT".
            - Tự kiểm tra các tiêu đề và mô tả: KHÔNG chứa dấu chấm...). KHÔNG chứa dấu chấm thế giới (!) hoặc các từ cấm ('bảo đảm 100%', 'miễn phí hoàn toàn', 'tốt nhất thế giới').
            - Phân bổ 15 tiêu đề theo tỷ lệ vàng:
                * 3-5 tiêu đề chứa chính xác hoặc sát nghĩa từ khóa mục tiêu được cấp.
                * 3 tiêu đề chứa Tên thương hiệu/Thương hiệu dòng sản phẩm (ví dụ: "Beppin Body Nhật Bản").
                * 3 tiêu đề về Lợi ích nổi bật/USP của sản phẩm (ví dụ: "Mờ Thâm Nách Bẹn Mông").
                * 3 tiêu đề Kêu gọi hành động (CTA) (ví dụ: "Mua Ngay Nhận Ưu Đãi").
                * 1-2 tiêu đề khác biệt/Ưu đãi độc quyền.
            
            CÁC TIÊU CHÍ BẮT BUỘC ĐẢM BẢO KHI TẠO QUẢNG CÁO:
            1. Sử dụng các từ khóa phổ biến trong dòng tiêu đề của bạn: Hãy chèn các từ khóa mục tiêu được cung cấp vào dòng tiêu đề một cách tự nhiên và chính xác nhất có thể.
            2. Sử dụng dòng tiêu đề độc đáo hơn: Các dòng tiêu đề phải đa dạng về mặt ngữ nghĩa, góc tiếp cận khác biệt (như lợi ích, tính năng, cảm xúc, uy tín, CTA) để tránh trùng lặp.
            3. Sử dụng nội dung mô tả độc đáo hơn: Tránh viết các mô tả tương tự nhau. Mỗi dòng mô tả phải tập trung vào một giá trị duy nhất (Ví dụ: Mô tả 1 tập trung vào Giải pháp & Lợi ích, Mô tả 2 tập trung vào Uy tín/Chứng nhận, Mô tả 3 tập trung vào Khuyến mãi độc quyền, Mô tả 4 là Lời kêu gọi hành động quyết liệt).
            4. Thêm đường liên kết khác của trang web (Sitelinks): Hãy luôn cấu hình `has_sitelinks = True` và trong trường `message` hãy gợi ý sếp thêm 2-4 sitelinks (liên kết trang web phụ) phù hợp với sản phẩm.
            """
        elif req.task == "NEGATIVE_KEYWORDS":
            task_directives = """
            YÊU CẦU ĐẶC BIỆT CHO TÁC VỤ NEGATIVE_KEYWORDS (TỪ KHÓA PHỦ ĐỊNH):
            - Hãy phân tích landing page được cào (nếu có URL trong context) hoặc thông tin campaign để biết dòng sản phẩm gì.
            - BẮT BUỘC sinh ra đúng và đủ từ 8 đến 12 từ khóa phủ định (ví dụ: cụm từ rác như 'miễn phí', 'giá rẻ', 'crack', 'tự làm', 'tuyển dụng', 'việc làm', 'đối thủ', cụm từ không liên quan tới phân khúc cao cấp của shop).
            - Đưa danh sách các từ khóa phủ định này vào trường 'negative_keywords' của JSON response dưới dạng danh sách chuỗi (viết thường).
            - Tại trường 'message', hãy giải thích chi tiết bằng tiếng Việt chiến thuật tại sao phủ định các từ này (chia theo nhóm từ khóa như nhóm tìm thông tin free, nhóm so sánh giá rẻ, nhóm tìm tuyển dụng/việc làm).
            """
        elif req.task == "CAMPAIGN":
            task_directives = """
            YÊU CẦU ĐẶC BIỆT CHO TÁC VỤ CAMPAIGN (TỐI ƯU THÔNG SỐ KHỞI TẠO):
            - Gợi ý các thông số khởi tạo chiến dịch tối ưu:
                * campaign_name: Tên campaign gợi ý (ví dụ: 'Search_Brand_[Dòng Sản Phẩm]_[Vùng miền]')
                * daily_budget_vnd: Ngân sách ngày khuyến khích cho thị trường Việt Nam 2026 (tối thiểu 50000).
                * bidding_strategy: BẮT BUỘC chọn một trong ('MAXIMIZE_CLICKS', 'MAXIMIZE_CONVERSIONS', 'TARGET_CPA').
            - Điền các trường tương ứng trong JSON response.
            - Giải thích chiến thuật đấu thầu và ngân sách gợi ý trong trường 'message' bằng tiếng Việt chuyên nghiệp.
            """

        prompt = f"""
        BÁO CÁO TRINH SÁT TÁC CHIẾN - THỰC THI NHIỆM VỤ: {req.task}
        ĐỐI TƯỢNG PHÂN TÍCH: {req.context}
        {keywords_context}
        
        {f"URL TRANG ĐÍCH: {target_url}" if target_url else ""}
        {f"DỮ LIỆU NỘI DUNG:\n{page_content}" if target_url else ""}

        DỮ LIỆU ĐỐI THỦ CẠNH TRANH:
        {competitor_context}
        
        {task_directives}
        
        CHỈ THỊ TỪ SẾP:
        Bạn phải trả về kết quả dưới định dạng JSON (AISuggestionResponse) với các yêu cầu sau:
        1. THIẾT LẬP success = True (Trừ khi gặp lỗi kỹ thuật không thể phân tích).
        2. QUẢN LÝ ĐIỂM SỐ (BẮT BUỘC): Điền giá trị từ 0-100 vào các trường: 
           - seo_score: Đánh giá tối ưu công cụ tìm kiếm truyền thống.
           - sge_score: Đánh giá khả năng hiển thị trên Google AI (SGE) 2026.
           - quality_score: Đánh giá sự đồng bộ giữa quảng cáo và trang đích (0-10).
           - ad_strength: Cấu trúc dữ liệu AdStrengthDetails chứa kết quả tự đánh giá.
        3. THÔNG ĐIỆP CHIẾN THUẬT (message): 
           - KHÔNG dùng tiền tố 'INTERNAL_ERROR' hay 'SUCCESS'.
           - Đưa ra các bước hành động cụ thể, ngắn gọn, quyết liệt để Sếp tối ưu ngay.
           - Phân tích ngắn gọn kẽ hở của đối thủ so với trang của mình.
        """

        # 3. Gọi Trinity Bridge để thực hiện suy luận
        try:
            result = await trinity_bridge.run(
                self._agent, 
                prompt, 
                system_prompt=self.SYSTEM_PROMPT,
                role="pro",
                timeout=120.0
            )
            return result
        except Exception as e:
            logger.error("ai_strategist_failed: %s", e)
            return AISuggestionResponse(
                success=False,
                message=f"Xohi đang bận suy nghĩ (Lỗi: {str(e)}). Sếp vui lòng thử lại sau giây lát ạ!"
            )

    async def competitor_research(self, req: CompetitorAnalysisRequest) -> CompetitorAnalysisResponse:
        """Phân tích đối thủ, gợi ý từ khóa và chiến lược từ URL landing page."""
        logger.info("competitor_research url=%s", req.url)

        # 1. Trinh sát trang đích
        page_content = await self._fetch_page(req.url)
        import re
        domain = re.sub(r'^https?://', '', req.url).split('/')[0]

        # 2. Tìm kiếm đối thủ cạnh tranh cùng ngành
        search_query = f'site:{domain} OR "{domain}" quảng cáo google ads tiêu đề mô tả'
        competitor_query = f'quảng cáo google "{domain}" đối thủ việt nam 2026'
        kw_query = f'từ khóa mua hàng site:{domain} {domain}'

        results, competitor_results = await __import__('asyncio').gather(
            google_search_service.search(kw_query, num=10),
            google_search_service.search(competitor_query, num=8),
        )

        competitor_snippets = "\n".join([
            f"- [{r.get('displayLink')}] {r.get('title')}: {r.get('snippet')}"
            for r in (results + competitor_results)
        ])

        # 3. Build prompt phân tích
        _agent: Agent[None, CompetitorAnalysisResponse] = Agent(output_type=CompetitorAnalysisResponse, retries=2)  # type: ignore

        prompt = f"""PHÂN TÍCH ĐỐI THỦ VÀ KẾ HOẠCH TỪ KHÓA CHO: {req.url}

DỮ LIỆU TRANG ĐÍCH:
{page_content}

DỮ LIỆU TỪ KHÓA & ĐỐI THỦ TỪ GOOGLE SEARCH:
{competitor_snippets}

YÊU CẦU PHÂN TÍCH (trả về CompetitorAnalysisResponse):
1. page_title: Tiêu đề chính của trang.
2. page_summary: Tóm tắt sản phẩm/dịch vụ và điểm mạnh/yếu trong 2-3 câu.
3. keyword_suggestions: Gợi ý 15-20 từ khóa tìm kiếm mua hàng thực tế chất lượng cao, người dùng VN hay dùng.
   - Mỗi từ khóa cần: intent (BẮT BUỘC phải là COMMERCIAL), match_type (EXACT/PHRASE/BROAD),
     relevance (BẮT BUỘC phải là HIGH), estimated_cpc_vnd (ước tính CPC theo VNĐ), estimated_volume.
   - BẮT BUỘC LOẠI BỎ các từ khóa có lượt tìm kiếm quá thấp (dưới 100 lượt/tháng). Giá trị estimated_volume chỉ được phép chọn trong ('100-1K', '1K-10K', '> 10K'). CẤM chọn '< 100'.
   - Chỉ chọn từ khóa có ý định mua hàng rõ ràng (như tìm kiếm sản phẩm, tìm kiếm giải pháp điều trị, so sánh giá), loại bỏ các từ khóa mang tính chất tìm thông tin chung chung, tìm việc làm, hoặc chứa tên các đối thủ cạnh tranh khác không phù hợp.
4. competitor_headlines: Trích xuất 8-10 tiêu đề/mô tả quảng cáo thực tế từ dữ liệu đối thủ tìm được.
   - CHÚ Ý: Tuyệt đối LOẠI BỎ tên miền {domain} (website của chính mình) ra khỏi danh sách đối thủ này. Chỉ được lấy tiêu đề từ các domain của các đối thủ cạnh tranh khác.
5. negative_keyword_suggestions: 5-8 từ khóa phủ định nên thêm để tránh click ảo (ví dụ: "miễn phí", "tự làm", "công thức").
6. recommended_display_path1 và display_path2: Gợi ý 2 đường dẫn hiển thị tối ưu (không dấu, viết thường, tối đa 15 ký tự).
7. seo_gaps: Phân tích kẽ hở SEO/Ads mà trang này đang bỏ lỡ so với đối thủ (2-3 gạch đầu dòng).
8. message: Tóm tắt chiến thuật 1 câu.
"""
        try:
            result = await trinity_bridge.run(
                _agent,
                prompt,
                system_prompt=self.SYSTEM_PROMPT,
                role="pro",
                timeout=120.0
            )
            if result.success and result.keyword_suggestions:
                try:
                    from backend.services.ads_protection.campaign_manager import CampaignManager
                    _campaign_mgr = CampaignManager()
                    seeds = [item.keyword for item in result.keyword_suggestions]
                    real_suggestions = await _campaign_mgr.get_keyword_suggestions(seeds)
                    real_map = {rs.keyword.lower().strip(): rs for rs in real_suggestions} if real_suggestions else {}
                    
                    for item in result.keyword_suggestions:
                        key = item.keyword.lower().strip()
                        if key in real_map:
                            rs = real_map[key]
                            vol = rs.avg_monthly_searches
                            if vol is not None:
                                try:
                                    vol_val = int(vol)
                                except (TypeError, ValueError):
                                    vol_val = 0
                                if vol_val < 100:
                                    item.estimated_volume = "< 100"
                                elif vol_val < 1000:
                                    item.estimated_volume = "100-1K"
                                elif vol_val < 10000:
                                    item.estimated_volume = "1K-10K"
                                else:
                                    item.estimated_volume = "> 10K"
                            else:
                                item.estimated_volume = "< 100"
                            if rs.avg_cpc_vnd is not None:
                                item.estimated_cpc_vnd = rs.avg_cpc_vnd
                        else:
                            item.estimated_volume = "< 100"
                            
                    # Lọc bỏ các từ khóa có lượng tìm kiếm dưới 100 (Google Ads 2026 compliance)
                    result.keyword_suggestions = [
                        item for item in result.keyword_suggestions 
                        if item.estimated_volume != "< 100"
                    ]
                except Exception as enrich_err:
                    logger.error("Failed to enrich keyword suggestions with Google Ads API: %s", enrich_err)
            return result
        except Exception as e:
            logger.error("competitor_research_failed: %s", e)
            return CompetitorAnalysisResponse(
                success=False,
                message=f"Phân tích thất bại: {str(e)}"
            )

    async def generate_pmax_assets(self, landing_page_url: str) -> PMaxAssetGroupResponse:
        """Tự động sinh Asset Group và Search Themes cho chiến dịch PMax từ trang đích."""
        logger.info("generate_pmax_assets url=%s", landing_page_url)
        
        # Scrape image candidates first
        marketing_imgs = []
        square_imgs = []
        logo_imgs = []

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                resp = await client.get(landing_page_url, headers=headers)
                if resp.status_code == 200:
                    from lxml import html
                    from urllib.parse import urljoin
                    tree = html.fromstring(resp.content)
                    
                    # 1. Get og:image
                    og = tree.xpath("//meta[@property='og:image']/@content")
                    if og:
                        full_og = urljoin(landing_page_url, og[0])
                        marketing_imgs.append(full_og)
                        square_imgs.append(full_og)

                    # 2. Get all images and classify by priority
                    all_img_elements = tree.xpath("//img")
                    priority_imgs = []
                    other_imgs = []
                    
                    exclude_keywords = [
                        "icon", "svg", "tracker", "sprite", "favicon", "badge", "trust", 
                        "payment", "card", "shield", "star", "arrow", "next", "prev", 
                        "close", "menu", "cart", "search", "avatar", "user", "author", 
                        "comment", "facebook", "zalo", "youtube", "tiktok", "instagram", 
                        "messenger", "pinterest", "thumb", "thumbnail", "small", "mini", 
                        "button", "gif", "banner", "slider", "slide", "bg", "background",
                        "policy", "chinh-sach", "cam-ket", "shipping", "delivery"
                    ]

                    for img in all_img_elements:
                        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or img.get("data-original")
                        if not src:
                            continue
                        
                        full_src = urljoin(landing_page_url, src)
                        src_lower = src.lower()
                        class_lower = (img.get("class") or "").lower()
                        id_lower = (img.get("id") or "").lower()
                        alt_lower = (img.get("alt") or "").lower()
                        
                        # Check for logo
                        if "logo" in src_lower or "logo" in class_lower or "logo" in id_lower:
                            if full_src not in logo_imgs:
                                logo_imgs.append(full_src)
                            continue
                            
                        # Exclude icons, UI decorations, etc.
                        if any(x in src_lower or x in class_lower or x in id_lower or x in alt_lower for x in exclude_keywords):
                            continue
                            
                        # Detect priority product images
                        is_priority = any(
                            x in src_lower or x in class_lower or x in id_lower or x in alt_lower 
                            for x in ["product", "prod", "main", "detail", "gallery", "featured", "item"]
                        )
                        
                        if is_priority:
                            if full_src not in priority_imgs:
                                priority_imgs.append(full_src)
                        else:
                            if full_src not in other_imgs:
                                other_imgs.append(full_src)
                    
                    # Combine: priority product images first, then other valid images
                    for img_url in priority_imgs:
                        if img_url not in marketing_imgs:
                            marketing_imgs.append(img_url)
                        if img_url not in square_imgs:
                            square_imgs.append(img_url)
                            
                    for img_url in other_imgs:
                        if img_url not in marketing_imgs:
                            marketing_imgs.append(img_url)
                        if img_url not in square_imgs:
                            square_imgs.append(img_url)
        except Exception as img_err:
            logger.warning(f"Error scraping images in generate_pmax_assets: {img_err}")

        # Limit sizes and enforce high quality fallbacks
        marketing_imgs = marketing_imgs[:10]
        square_imgs = square_imgs[:10]
        logo_imgs = logo_imgs[:3]

        if not marketing_imgs:
            marketing_imgs = ["/v65_assets/cache/t_800_75_e2dedb54-cabe-4c49-a81f-a6b988e7efbe.webp?w=1200&h=628&fit=crop"]
        if not square_imgs:
            square_imgs = ["/v65_assets/cache/t_800_75_b2e65771-e14e-4ec1-a95b-ffd577e7cc6b.webp?w=1200&h=1200&fit=crop"]
        if not logo_imgs:
            logo_imgs = ["/v65_assets/cache/t_800_75_553d62fa-3e54-4544-9739-839920617e75.webp?w=512&h=512&fit=crop"]

        page_content = ""
        try:
            page_content = await self._fetch_page(landing_page_url)
        except Exception as e:
            logger.error("Failed to fetch landing page in generate_pmax_assets: %s", e)
            page_content = "Không thể lấy nội dung trang đích. Hãy sử dụng kiến thức chung."

        prompt = f"""
        NỘI DUNG TRANG ĐÍCH CỦA SẾP:
        {page_content[:20000]}
        
        URL Trang Đích: {landing_page_url}
 
        YÊU CẦU:
        Hãy phân tích nội dung trang đích trên và tự động tạo Asset Group và Search Themes tối ưu cho chiến dịch Google Ads Performance Max (AI Max):
        1. headlines: Sinh đúng ĐỦ 5 tiêu đề ngắn, mỗi tiêu đề dài TỐI ĐA 30 ký tự.
        2. descriptions: Sinh đúng ĐỦ 5 mô tả, mỗi mô tả dài TỐI ĐA 90 ký tự.
        3. search_themes: Sinh đúng ĐỦ 10 chủ đề tìm kiếm (Search Themes) dưới dạng hội thoại ngữ cảnh hoặc từ khóa dài (đại diện cho hành vi tìm kiếm AI Mode), mỗi chủ đề dài từ 3 đến 7 từ.
        4. landing_page_url: Trả về chính xác URL trang đích được cung cấp.

        Chú ý: Tuyệt đối tuân thủ độ dài ký tự! Không chứa các từ cam kết quá mức hoặc hoạt chất nhạy cảm bị cấm y tế.
        """

        try:
            result = await trinity_bridge.run(
                self._pmax_agent,
                prompt,
                system_prompt=self.SYSTEM_PROMPT,
                role="pro",
                timeout=120.0
            )
            result.marketing_images = marketing_imgs
            result.square_marketing_images = square_imgs
            result.logo_images = logo_imgs
            return result
        except Exception as e:
            logger.error("generate_pmax_assets_failed: %s", e)
            # Trả về giá trị fallback hợp lệ để không bị crash
            return PMaxAssetGroupResponse(
                headlines=[
                    "Kem Dưỡng Da Xohi",
                    "Phục Hồi Sáng Da Toàn Thân",
                    "Mỹ Phẩm Lành Tính Tự Nhiên",
                    "Dưỡng Ẩm Chuyên Sâu",
                    "Ưu Đãi Hôm Nay"
                ],
                descriptions=[
                    "Kem dưỡng sáng da toàn thân từ thảo duyệt thiên nhiên Nhật Bản an toàn cho mọi loại da.",
                    "Sản phẩm dưỡng ẩm chuyên sâu giúp da mềm mịn tự nhiên không kích ứng da nhạy cảm.",
                    "Mua ngay hôm nay để nhận ưu đãi giảm giá đặc biệt và miễn phí vận chuyển toàn quốc.",
                    "Giải pháp phục hồi làn da xỉn màu hư tổn mang lại vẻ rạng rỡ tự nhiên cho bạn.",
                    "Được kiểm nghiệm da liễu an toàn và hiệu quả nhanh chóng cho phụ nữ sau sinh."
                ],
                search_themes=[
                    "kem dưỡng sáng da toàn thân loại nào tốt",
                    "kem phục hồi da lành tính sau sinh",
                    "mỹ phẩm dưỡng ẩm sâu tự nhiên",
                    "cách làm sáng da nách bẹn mông an toàn",
                    "review kem dưỡng trắng da tốt nhất",
                    "kem dưỡng ẩm cho da nhạy cảm",
                    "sản phẩm chăm sóc da thương hiệu xohi",
                    "kem bôi làm mờ vết thâm sạm",
                    "kem dưỡng sáng da chính hãng",
                    "bí quyết phục hồi làn da xỉn màu"
                ],
                landing_page_url=landing_page_url,
                marketing_images=marketing_imgs,
                square_marketing_images=square_imgs,
                logo_images=logo_imgs
            )


ai_strategist: AIStrategist = AIStrategist()
