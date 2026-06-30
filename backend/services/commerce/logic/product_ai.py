import logging
import re
import json
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")


def _apply_mandatory_terms(text: str) -> str:
    """SGE Shield V3.0: Apply mandatory fixed-term replacements (e.g. nhau thai → Placenta)."""
    from backend.services.lexical_sanitizer import _COMPILED_FIXED_TERMS
    for pattern, replacement in _COMPILED_FIXED_TERMS:
        text = pattern.sub(replacement, text)
    return text


# ══════════════════════════════════════════════════════════════
# PydanticAI V2 Structured Output Models
# ══════════════════════════════════════════════════════════════

class ProductSEOResponse(BaseModel):
    title: str = Field(..., description="Tiêu đề SEO sản phẩm")
    description: str = Field(..., description="Mô tả SEO sản phẩm")
    keywords: str = Field(..., description="Từ khóa SEO cách nhau bởi dấu phẩy")


class FAQItem(BaseModel):
    question: str = Field(..., description="Câu hỏi thường gặp")
    answer: str = Field(..., description="Câu trả lời ngắn gọn")


class ProductFAQResponse(BaseModel):
    faqs: List[FAQItem] = Field(..., description="Danh sách câu hỏi thường gặp")


class IngredientItem(BaseModel):
    name: str = Field(..., description="Tên thành phần")
    benefit: str = Field(..., description="Công dụng ngắn gọn")
    icon: str = Field(..., description="Emoji đại diện")


class IngredientListResponse(BaseModel):
    ingredients: List[IngredientItem] = Field(..., description="Danh sách 4 thành phần nổi bật")


class IngredientGroupItem(BaseModel):
    group: str = Field(..., description="Tên nhóm chức năng")
    priority: int = Field(..., description="Mức ưu tiên (1=cao nhất)")
    items: List[str] = Field(..., description="Danh sách tên INCI")


class IngredientGroupResponse(BaseModel):
    groups: List[IngredientGroupItem] = Field(..., description="Danh sách nhóm thành phần")


# ══════════════════════════════════════════════════════════════
# AI Logic Functions (PydanticAI V2 Structured Output)
# ══════════════════════════════════════════════════════════════

async def suggest_seo_logic(name: str, description: str) -> Dict[str, str]:
    """Elite V2.2: AI SEO Suggestion Logic (Structured Output)."""
    agent = Agent(
        system_prompt=(
            "Bạn là chuyên gia SEO hàng đầu Việt Nam. Hãy tối ưu tiêu đề, mô tả và từ khóa SEO cho sản phẩm này. "
            "QUY TẮC TỐI CAO: Dù tên sản phẩm hoặc mô tả đầu vào là tiếng Anh, bạn BẮT BUỘC phải phản hồi nội dung hoàn toàn bằng tiếng Việt thuần 100%. "
            "Nội dung phải súc tích, hấp dẫn và chuẩn SEO. "
            "Các câu trong phần mô tả (description) bắt buộc phải là câu hoàn chỉnh (đầy đủ chủ ngữ và vị ngữ), tuyệt đối không ngắt dòng giữa chừng và viết ngắn gọn ngay từ đầu."
        ),
        output_type=ProductSEOResponse,
    )
    prompt = f"Tên sản phẩm: {name}\nMô tả: {description}"

    try:
        result = await trinity_bridge.run(
            agent=agent, prompt=prompt, role="fast", timeout=30.0
        )

        if result:
            seo_data = getattr(result, "data", result)
            if isinstance(seo_data, ProductSEOResponse):
                parsed = seo_data.model_dump()
            elif hasattr(seo_data, "title"):
                parsed = {"title": seo_data.title, "description": seo_data.description, "keywords": seo_data.keywords}
            else:
                parsed = {"title": "", "description": "", "keywords": ""}

            from backend.utils.text import validate_vietnamese_sentence, sanitize_sentence_linebreaks
            if parsed.get("description"):
                try:
                    parsed["description"] = sanitize_sentence_linebreaks(parsed["description"])
                    parsed["description"] = validate_vietnamese_sentence(parsed["description"])
                except Exception as ve:
                    logger.warning(f"[ProductAI] SEO description validation failed: {ve}")
            # SGE Shield V3.0: enforce mandatory term replacements on all string fields
            for field in ("title", "description", "keywords"):
                if field in parsed:
                    parsed[field] = _apply_mandatory_terms(parsed[field])
            return parsed

        return {"title": f"{name} Chính Hãng", "description": "Sản phẩm chính hãng", "keywords": ""}

    except Exception as e:
        logger.exception(f"[ProductAI] AI SEO Suggestion Failed: {e}")
        return {"title": f"{name} Chính Hãng", "description": "Mua sản phẩm chính hãng với nhiều ưu đãi", "keywords": ""}

async def suggest_faqs_logic(name: str, description: str) -> List[Dict[str, str]]:
    """Elite V2.2: XOHI Auto FAQ Generator Logic (Structured Output)."""
    agent = Agent(
        system_prompt=(
            "Bạn là chuyên gia tư vấn sản phẩm và chuyên gia SEO chuyên tối ưu hóa dữ liệu Hỏi & Đáp (Q&A/FAQ Blocks) để hiển thị trên Google SGE (Search Generative Experience) và AI Overviews.\n"
            "Dựa trên tên và mô tả sản phẩm, hãy tạo từ 3 đến 5 câu hỏi thường gặp và câu trả lời ngắn gọn, hữu ích bằng tiếng Việt.\n\n"
            "YÊU CẦU CỰC KỲ QUAN TRỌNG ĐỂ ĐẠT MỤC TIÊU SGE/AI OVERVIEWS:\n"
            "1. Tiêu đề câu hỏi (question) bắt buộc phải viết dưới dạng các câu hỏi tìm kiếm tự nhiên của người dùng, sử dụng các từ nghi vấn rõ ràng như: 'Là gì', 'Làm thế nào', 'Có tốt không', 'Cách sử dụng như thế nào', 'Thành phần gồm những gì', 'Mua ở đâu chính hãng', 'Bao nhiêu tuổi dùng được', 'Có tác dụng phụ không'.\n"
            "2. Ví dụ về câu hỏi chuẩn SGE: 'Kem dưỡng mắt White Label có tác dụng gì?', 'Cách sử dụng kem mắt White Label hiệu quả nhất?', 'Kem mắt White Label có tốt không và phù hợp với loại da nào?'.\n"
            "3. Tránh các câu hỏi chung chung, mơ hồ như 'Thông tin sản phẩm' hay 'Tại sao nên mua sản phẩm này?'.\n"
            "4. Câu trả lời (answer) phải ngắn gọn, súc tích (dưới 80 từ), đi thẳng vào câu hỏi, cung cấp thông tin hữu ích và chính xác dựa trên mô tả sản phẩm.\n"
            "5. Các câu trả lời (answer) bắt buộc phải là một câu hoàn chỉnh về mặt ngữ nghĩa (có đầy đủ chủ ngữ + vị ngữ), tuyệt đối không ngắt dòng khi chưa viết hết câu, và hãy chủ động viết ngắn gọn ngay từ đầu.\n"
            "6. QUY TẮC TỐI CAO: Bất kể ngôn ngữ đầu vào là gì, đầu ra phải là tiếng Việt thuần 100%.\n"
            "7. TUYỆT ĐỐI không chứa bất kỳ thẻ liên kết <a>, đường dẫn (URL) nào trong câu hỏi hoặc câu trả lời."
        ),
        output_type=ProductFAQResponse,
    )
    prompt = f"Tên sản phẩm: {name}\nMô tả: {description}"

    try:
        result = await trinity_bridge.run(
            agent=agent, prompt=prompt, role="fast", timeout=45.0
        )

        if result:
            faq_data = getattr(result, "data", result)
            if isinstance(faq_data, ProductFAQResponse):
                faqs = faq_data.faqs
            elif hasattr(faq_data, "faqs"):
                faqs = faq_data.faqs
            else:
                faqs = []

            from backend.utils.text import validate_vietnamese_sentence, sanitize_sentence_linebreaks
            result_list: List[Dict[str, str]] = []
            for item in faqs:
                q = str(item.question).strip()
                a = str(item.answer).strip()
                try:
                    q = validate_vietnamese_sentence(q, mode="light")
                except Exception as ve:
                    logger.warning(f"[ProductAI] FAQ question validation failed: {ve}")
                try:
                    a = sanitize_sentence_linebreaks(a)
                    a = validate_vietnamese_sentence(a, mode="standard")
                except Exception as ve:
                    logger.warning(f"[ProductAI] FAQ answer validation failed: {ve}")
                # SGE Shield V3.0: enforce mandatory term replacements
                q = _apply_mandatory_terms(q)
                a = _apply_mandatory_terms(a)
                result_list.append({"question": q, "answer": a})
            return result_list

        return []

    except Exception as e:
        logger.exception(f"[ProductAI] AI FAQ Suggestion Failed: {e}")
        return []

async def suggest_ingredients_logic(name: str, ingredients: str) -> List[Dict[str, str]]:
    """Elite V2.2: XOHI Auto Ingredients Extractor Logic (Structured Output)."""
    agent = Agent(
        system_prompt=(
            "Bạn là chuyên gia da liễu và mỹ phẩm hàng đầu. Dựa trên tên sản phẩm và bảng thành phần đầy đủ, "
            "hãy phân tích và trích xuất chính xác đúng 4 thành phần quan trọng nhất, nổi bật nhất của sản phẩm.\n"
            "YÊU CẦU:\n"
            "- 'name': Tên thành phần (ví dụ: 'Hyaluronic Acid', 'Ceramide', 'Chiết xuất rau má', ...)\n"
            "- 'benefit': Công dụng/lợi ích nổi bật, ngắn gọn của thành phần đó trong sản phẩm (dưới 15 từ)\n"
            "- 'icon': Emoji đại diện phù hợp nhất cho thành phần đó theo nội dung (ví dụ: 💧 cho HA, 🧬 cho Ceramide/Collagen, 🌱 cho rau má, 🌿 cho trà xanh, 🛡️ cho Niacinamide, ✨ cho làm sáng, ...)\n"
            "QUY TẮC TỐI CAO: Toàn bộ thông tin tên thành phần, công dụng phải là tiếng Việt thuần 100%.\n"
            "Các câu mô tả công dụng (benefit) bắt buộc phải là câu hoàn chỉnh về mặt ngữ nghĩa (có đầy đủ chủ ngữ + vị ngữ), tuyệt đối không ngắt dòng khi chưa viết hết câu, và viết ngắn gọn ngay từ đầu."
        ),
        output_type=IngredientListResponse,
    )
    prompt = f"Tên sản phẩm: {name}\nBảng thành phần: {ingredients}"

    try:
        result = await trinity_bridge.run(
            agent=agent, prompt=prompt, role="fast", timeout=45.0
        )

        if result:
            ing_data = getattr(result, "data", result)
            if isinstance(ing_data, IngredientListResponse):
                items = ing_data.ingredients
            elif hasattr(ing_data, "ingredients"):
                items = ing_data.ingredients
            else:
                items = []

            from backend.utils.text import validate_vietnamese_sentence, sanitize_sentence_linebreaks
            result_list: List[Dict[str, str]] = []
            for item in items:
                item_dict: Dict[str, str] = {"name": str(item.name), "benefit": str(item.benefit), "icon": str(item.icon)}
                try:
                    item_dict["benefit"] = sanitize_sentence_linebreaks(item_dict["benefit"])
                    item_dict["benefit"] = validate_vietnamese_sentence(item_dict["benefit"])
                except Exception as ve:
                    logger.warning(f"[ProductAI] Ingredient benefit validation failed: {ve}")
                # SGE Shield V3.0: enforce mandatory term replacements
                for field in ("name", "benefit"):
                    item_dict[field] = _apply_mandatory_terms(item_dict[field])
                result_list.append(item_dict)
            return result_list[:4]

        return []

    except Exception as e:
        logger.exception(f"[ProductAI] AI Ingredients Suggestion Failed: {e}")
        return []

async def suggest_specs_logic(raw_text: str) -> Dict[str, str]:
    """Elite V2.2: XOHI Auto Specifications Extractor Logic (Structured Output)."""
    agent = Agent(
        system_prompt=(
            "Bạn là trợ lý AI chuyên nghiệp. Hãy phân tích đoạn văn bản thô mô tả thông số kỹ thuật của sản phẩm "
            "và trích xuất chúng thành các cặp khóa-giá trị (Key-Value).\n"
            "QUY TẮC:\n"
            "1. Chuẩn hóa tên khóa sang tiếng Việt chuyên nghiệp nếu có thể (ví dụ: 'Thương hiệu', 'Xuất xứ', 'Quy cách', 'Hạn sử dụng', 'Dung tích', 'Khối lượng').\n"
            "2. Giá trị phải được giữ nguyên hoặc làm sạch nhẹ nhàng để hiển thị trên website."
        ),
        output_type=Dict[str, str],
    )
    prompt = f"Thông số kỹ thuật thô:\n{raw_text}"

    try:
        result = await trinity_bridge.run(
            agent=agent, prompt=prompt, role="fast", timeout=30.0
        )

        if result:
            specs_data = getattr(result, "data", result)
            if isinstance(specs_data, dict):
                return {str(k): str(v) for k, v in specs_data.items()}

        return {}

    except Exception as e:
        logger.exception(f"[ProductAI] AI Specs Extraction Failed: {e}")
        return {}

async def suggest_semantic_logic(name: str, description: str, seo_description: Optional[str] = None) -> str:
    """GEO 2026: XOHI Auto Semantic SGE Highlights Generator Logic (Isolated)."""
    agent = Agent(
        system_prompt=(
            "Bạn là chuyên gia tối ưu cấu trúc dữ liệu Semantic HTML cho Google SGE AI bóc tách thông tin.\n"
            "Nhiệm vụ của bạn là tạo ra một đoạn HTML hoàn chỉnh, tối ưu chuẩn SEO Semantic theo cấu trúc chính xác sau:\n"
            "<h2>{Tên sản phẩm}:</h2>\n"
            "<ul class=\"product-highlights\">\n"
            "    <li>[Mô tả công nghệ/thành phần then chốt đột phá]</li>\n"
            "    <li>[Kết cấu, độ lành tính, cảm giác trên da hoặc tính năng vượt trội tiện dụng]</li>\n"
            "</ul>\n\n"
            "QUY TẮC BẮT BUỘC (VI PHẠM SẼ BỊ PHẠT NẶNG):\n"
            "1. Nội dung phải hoàn toàn bằng tiếng Việt thuần 100%.\n"
            "2. BẮT BUỘC DỰA TRÊN MÔ TẢ SEO (SEO Description) ĐỂ TÓM TẮT. Chỉ khi Mô tả SEO trống hoặc thiếu thông tin mới được dùng Mô tả sản phẩm làm dự phòng.\n"
            "3. TUYỆT ĐỐI KHÔNG sử dụng ký tự đánh số dạng '1. ...', '2. ...', hoặc ký tự gạch đầu dòng, dấu chấm tròn bên trong các thẻ <li>.\n"
            "4. CÁC CÂU BẮT BUỘC PHẢI LÀ MỘT CÂU HOÀN CHỈNH VỀ MẶT NGỮ NGHĨA (Có đầy đủ chủ ngữ + vị ngữ).\n"
            "5. TUYỆT ĐỐI KHÔNG ĐƯỢC NGẮT DÒNG khi chưa viết hết câu (không sử dụng phím Enter xuống dòng, không dùng ký tự xuống dòng như \\n hoặc <br> trong từng thẻ <li>).\n"
            "6. HÃY CHỦ ĐỘNG VIẾT NGẮN GỌN NGAY TỪ ĐẦU (Mỗi thẻ <li> tối đa 20 từ và là một câu đơn/câu ghép ngắn hoàn chỉnh, không rườm rà).\n"
            "7. Không trả về bất kỳ giải thích nào khác ngoài chuỗi HTML thô bắt đầu bằng <h2> và kết thúc bằng </ul>."
        ),
        output_type=str,
    )
    prompt = (
        f"Tên sản phẩm: {name}\n"
        f"Mô tả SEO: {seo_description or ''}\n"
        f"Mô tả sản phẩm: {description}"
    )

    try:
        result = await trinity_bridge.run(
            agent=agent, prompt=prompt, role="fast", timeout=30.0
        )

        if result:
            html_res = str(getattr(result, "data", getattr(result, "output", result))).strip()
            # Clean possible ```html blocks if generated
            html_res = re.sub(r"^```html\s*", "", html_res, flags=re.IGNORECASE)
            html_res = re.sub(r"\s*```$", "", html_res)

            # Clean numbered lists, bullet points from <li> tags
            html_res = re.sub(r"<li>\s*(?:\d+[\.)\-:]\s*|-|•)\s*", "<li>", html_res)

            # Clean internal line breaks and extra spaces within each <li> content
            def clean_li_content(match: re.Match[str]) -> str:
                li_inner: str = match.group(1)
                # Remove newlines, tabs, carriage returns and reduce multiple spaces to one
                li_inner = re.sub(r"\s+", " ", li_inner).strip()
                # Clean leading numbers/bullets again just in case of spaces
                li_inner = re.sub(r"^(?:\d+[\.)\-:]\s*|-|•)\s*", "", li_inner)
                from backend.utils.text import validate_vietnamese_sentence, sanitize_sentence_linebreaks
                try:
                    li_inner = sanitize_sentence_linebreaks(li_inner)
                    li_inner = validate_vietnamese_sentence(li_inner)
                except Exception as ve:
                    logger.warning(f"[ProductAI] Semantic highlight line validation failed: {ve}")
                return f"<li>{li_inner}</li>"

            html_res = re.sub(r"<li>(.*?)</li>", clean_li_content, html_res, flags=re.DOTALL)
            # SGE Shield V3.0: enforce mandatory term replacements on full HTML output
            html_res = _apply_mandatory_terms(html_res)
            return html_res.strip()

        return ""

    except Exception as e:
        logger.exception(f"[ProductAI] AI Semantic Suggestion Failed: {e}")
        return ""


async def suggest_ingredients_grouped_logic(ingredients_text: str) -> List[Dict[str, object]]:
    """GEO 2026: XOHI Ingredients Grouper — phân nhóm thành phần theo danh mục, sort mức độ quan trọng cao→thấp."""
    agent = Agent(
        system_prompt=(
            "Bạn là chuyên gia phân tích thành phần mỹ phẩm / dược phẩm hàng đầu.\n"
            "Nhiệm vụ: Đọc bảng thành phần INCI đầu vào và phân loại vào các nhóm chức năng.\n\n"
            "Các nhóm được phép phân loại (tên tiếng Việt ngắn gọn):\n"
            "- Hoạt chất chủ lực\n"
            "- Phục hồi và tái tạo\n"
            "- Chống oxy hoá & Làm sáng\n"
            "- Dưỡng ẩm & Emollient\n"
            "- Chất nhũ hoá & Cấu trúc\n"
            "- Thành phần khác\n\n"
            "QUY TẮC CỰC KỲ QUAN TRỌNG (ĐỘ UY TÍN THƯƠNG HIỆU):\n"
            "1. CẤM TUYỆT ĐỐI tạo ra các nhóm riêng biệt liên quan đến chất bảo quan, bảo quản, hương liệu hoặc màu sắc (như 'Chất bảo quản', 'Hương liệu & Màu sắc', 'Hương liệu', 'Màu sắc'). Việc này làm giảm lòng tin của khách hàng về độ lành tính của sản phẩm.\n"
            "2. BẮT BUỘC: Gộp toàn bộ các thành phần như chất bảo quản (preservatives), hương liệu (fragrance/perfume), chất tạo màu (colorants), dung môi (solvents), chất điều chỉnh (ph adjusters), và các tá dược/chất phụ trợ khác vào một nhóm duy nhất mang tên 'Thành phần khác'.\n"
            "3. priority: Số nguyên từ 1 (cao nhất = Hoạt chất chủ lực) đến 8 (thấp nhất = Thành phần khác). Chỉ dùng mỗi số 1 lần. Nhóm 'Thành phần khác' phải luôn có priority là 8.\n"
            "4. items: Mảng tên INCI nguyên gốc, giữ nguyên chính tả gốc, TỐI ĐA 8 thành phần mỗi nhóm.\n"
            "5. Bỏ qua các nhóm rỗng (không có thành phần nào)."
        ),
        output_type=IngredientGroupResponse,
    )
    prompt = f"Bảng thành phần:\n{ingredients_text[:3000]}"

    try:
        result = await trinity_bridge.run(
            agent=agent, prompt=prompt, role="fast", timeout=45.0
        )

        if result:
            group_data = getattr(result, "data", result)
            if isinstance(group_data, IngredientGroupResponse):
                groups = group_data.groups
            elif hasattr(group_data, "groups"):
                groups = group_data.groups
            else:
                groups = []

            parsed: List[Dict[str, object]] = []
            for g in groups:
                parsed.append({
                    "group": str(g.group),
                    "priority": int(g.priority),
                    "items": [str(i) for i in g.items]
                })
            # Sort by priority ascending (1 = highest importance)
            parsed.sort(key=lambda x: int(x.get("priority", 99)))
            return parsed

        return []

    except Exception as e:
        logger.exception(f"[ProductAI] AI Ingredients Grouping Failed: {e}")
        return []
