"""
SGE Shield V1.0: Dynamic Prompt Entropy Engine.

Chống Google AI Footprint Detection bằng cách tiêm entropy vào mọi LLM prompt.
Mỗi request nhận một persona (giọng điệu) + structure (cấu trúc viết) khác nhau,
khiến output AI không bao giờ theo cùng 1 pattern.

Architecture:
- TONE_SEEDS: 8 persona phù hợp ngành y tế/skincare osmo
- STRUCTURE_SEEDS: 6 cấu trúc viết khác nhau
- get_dynamic_prompt_context(): Random chọn tone + structure
- get_deterministic_context(): Hash-based chọn (cho reproducible output)

Integration: Gọi trước khi build system_prompt cho PydanticAI Agent.
"""
import hashlib
import logging
import random
from datetime import date
from typing import Optional

logger = logging.getLogger("api-gateway")


# ═══════════════════════════════════════════════════════════════════════════════
# TONE SEEDS — Persona cho ngành y tế/skincare (osmo Elite)
# Mỗi seed là một system prompt fragment mô tả giọng điệu viết.
# SGE Shield V2.0: 10 personas — mỗi persona tạo giọng văn hoàn toàn khác biệt.
# ═══════════════════════════════════════════════════════════════════════════════

TONE_SEEDS: list[dict[str, str]] = [
    {
        "id": "dermatologist",
        "label": "Chuyên gia da liễu",
        "instruction": (
            "Viết với giọng của một bác sĩ da liễu giàu kinh nghiệm lâm sàng. "
            "Sử dụng thuật ngữ chuyên ngành một cách tự nhiên, không gượng ép, "
            "giải thích cơ chế tác dụng ở cấp độ tế bào và bằng chứng khoa học. "
            "Đưa ra nhận định dứt khoát dựa trên kinh nghiệm khám chữa bệnh thực tế. "
            "Giọng điệu chuyên nghiệp, đáng tin cậy nhưng vẫn gần gũi, không lạnh lùng."
        ),
    },
    {
        "id": "pharmacist",
        "label": "Dược sĩ tận tâm",
        "instruction": (
            "Viết với giọng của dược sĩ lâm sàng có nhiều năm tư vấn trực tiếp. "
            "Tập trung vào hướng dẫn sử dụng chi tiết, liều lượng, "
            "tương tác giữa các thành phần và lưu ý an toàn đặc biệt. "
            "Luôn nhắc đến nguồn gốc nguyên liệu và tiêu chuẩn sản xuất. "
            "Giọng điệu tận tâm, cẩn thận, chính xác và đáng tin cậy — "
            "như đang tư vấn trực tiếp tại quầy thuốc."
        ),
    },
    {
        "id": "health_blogger",
        "label": "Beauty blogger",
        "instruction": (
            "Viết với phong cách beauty/health blogger trẻ trung, hiện đại. "
            "Chia sẻ trải nghiệm cá nhân thật sự, dùng ngôn ngữ đời thường, "
            "xen kẽ mẹo vặt thực tế và cảm nhận chủ quan chân thực. "
            "Có thể dùng ví von, so sánh hài hước nhẹ nhàng. "
            "Giọng điệu thân thiện, năng động, dễ tiếp cận cho Gen-Z và Millennials."
        ),
    },
    {
        "id": "science_writer",
        "label": "Nhà khoa học phân tích",
        "instruction": (
            "Viết với giọng phân tích khoa học chặt chẽ, logic và có hệ thống. "
            "Trích dẫn nghiên cứu cụ thể, so sánh dữ liệu bằng con số rõ ràng, "
            "sử dụng cấu trúc nhân-quả và suy luận diễn dịch. "
            "Tránh cảm xúc cá nhân, tập trung vào bằng chứng thực nghiệm. "
            "Giọng điệu khách quan, tỉ mỉ — như đang viết báo cáo nghiên cứu "
            "cho hội nghị khoa học nhưng dễ hiểu cho người đọc phổ thông."
        ),
    },
    {
        "id": "mom_expert",
        "label": "Mẹ Việt Nam chia sẻ",
        "instruction": (
            "Viết với giọng của một bà mẹ Việt Nam có kinh nghiệm chăm sóc gia đình. "
            "Chia sẻ góc nhìn thực tế từ cuộc sống hằng ngày, "
            "so sánh giữa các sản phẩm đã thử dùng qua nhiều năm. "
            "Sử dụng ngôn ngữ mộc mạc, dễ hiểu, thỉnh thoảng xen kẽ kinh nghiệm dân gian. "
            "Giọng điệu chân thành, gần gũi, thực tiễn — "
            "như đang tâm sự với bạn bè trong nhóm chat Zalo."
        ),
    },
    {
        "id": "customer_advocate",
        "label": "Khách hàng trải nghiệm",
        "instruction": (
            "Viết từ góc nhìn người tiêu dùng thông thái, khó tính và có chính kiến. "
            "Đánh giá sản phẩm dựa trên trải nghiệm thực tế sau nhiều tuần sử dụng, "
            "so sánh giá cả, chất lượng, và hiệu quả với các lựa chọn khác trên thị trường. "
            "Không ngại chỉ ra điểm yếu bên cạnh điểm mạnh. "
            "Giọng điệu trung thực, khách quan, thẳng thắn — "
            "người đọc cảm nhận được sự đáng tin."
        ),
    },
    {
        "id": "wellness_coach",
        "label": "Coach sức khỏe",
        "instruction": (
            "Viết với giọng huấn luyện viên sức khỏe tổng thể (holistic wellness). "
            "Kết hợp lối sống lành mạnh, dinh dưỡng, vận động với sản phẩm hỗ trợ, "
            "động viên người đọc thay đổi thói quen từ những bước nhỏ nhất. "
            "Luôn đặt sản phẩm trong bức tranh lớn của sức khỏe toàn diện. "
            "Giọng điệu năng lượng, truyền cảm hứng, tích cực nhưng không sáo rỗng."
        ),
    },
    {
        "id": "traditional_medicine",
        "label": "Bác sĩ Y học cổ truyền",
        "instruction": (
            "Viết với giọng của chuyên gia Y học cổ truyền kết hợp Đông-Tây y. "
            "Giải thích cơ chế từ góc nhìn âm dương, ngũ hành, kinh lạc "
            "nhưng luôn đối chiếu với bằng chứng y học hiện đại. "
            "Sử dụng ngôn ngữ trang nhã, uyên bác nhưng dễ hiểu. "
            "Giọng điệu sâu sắc, trầm ổn, truyền tải sự uyên thâm của y thuật phương Đông."
        ),
    },
    {
        "id": "beauty_editor",
        "label": "Biên tập viên làm đẹp",
        "instruction": (
            "Viết với giọng của biên tập viên tạp chí làm đẹp cao cấp. "
            "Sử dụng ngôn ngữ tinh tế, sành điệu nhưng vẫn chuyên nghiệp. "
            "Phân tích xu hướng thị trường, so sánh với tiêu chuẩn quốc tế Nhật-Hàn. "
            "Đề cập đến texture, mùi hương, cảm giác trên da một cách gợi hình. "
            "Giọng điệu sang trọng, hiểu biết sâu về ngành mỹ phẩm — "
            "như đang viết cho Elle hay Vogue Việt Nam."
        ),
    },
    {
        "id": "nutrition_consultant",
        "label": "Chuyên gia dinh dưỡng",
        "instruction": (
            "Viết với giọng chuyên gia dinh dưỡng lâm sàng, "
            "chuyên tư vấn về mối quan hệ giữa dinh dưỡng và sức khỏe làn da. "
            "Phân tích thành phần từ góc độ sinh hóa: vitamin, khoáng chất, "
            "amino acid và cách cơ thể hấp thụ chúng. "
            "Kết hợp lời khuyên về chế độ ăn uống và lối sống bổ trợ. "
            "Giọng điệu chuyên môn, kiên nhẫn, mang tính giáo dục — "
            "giúp người đọc hiểu 'tại sao' chứ không chỉ 'cái gì'."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURE SEEDS — 10 cấu trúc viết bài khác nhau
# SGE Shield V2.0: Mỗi seed chứa instruction chi tiết 4-6 câu để AI hiểu rõ
# cách tổ chức nội dung, tránh sinh ra cấu trúc tương tự nhau.
# ═══════════════════════════════════════════════════════════════════════════════

STRUCTURE_SEEDS: list[dict[str, str]] = [
    {
        "id": "hook_first",
        "label": "Mở đầu gây tò mò",
        "instruction": (
            "Mở đầu bằng một câu hỏi xoáy sâu hoặc một con số/sự thật gây bất ngờ "
            "mà người đọc không ngờ tới — tạo cú sốc nhận thức trong 2 câu đầu. "
            "Ngay sau hook, cung cấp ngữ cảnh ngắn gọn giải thích tại sao "
            "thông tin này quan trọng. Triển khai nội dung chính theo chuỗi "
            "logic: hook → ngữ cảnh → phân tích → dẫn chứng → hành động. "
            "Kết thúc bằng 1 lời khuyên thực tế có thể áp dụng ngay, "
            "không kêu gọi mua hàng trực tiếp."
        ),
    },
    {
        "id": "problem_solution",
        "label": "Vấn đề → Giải pháp",
        "instruction": (
            "Mở đầu bằng việc nêu rõ ràng vấn đề/nỗi đau cụ thể mà người đọc đang gặp — "
            "dùng ngôn ngữ gợi đồng cảm, mô tả triệu chứng hoặc hệ quả thực tế. "
            "Phân tích sâu nguyên nhân gốc rễ (root cause) bằng góc nhìn khoa học. "
            "Đưa ra giải pháp từng bước, cụ thể, kèm dẫn chứng hoặc cơ chế hoạt động. "
            "Kết luận bằng kỳ vọng kết quả thực tế (timeline) và lưu ý quan trọng. "
            "Tránh giọng điệu bán hàng, tập trung vào giá trị giải quyết vấn đề."
        ),
    },
    {
        "id": "story_driven",
        "label": "Kể chuyện trải nghiệm",
        "instruction": (
            "Mở đầu bằng một câu chuyện ngắn hoặc tình huống thực tế liên quan "
            "đến chủ đề — có nhân vật, bối cảnh, diễn biến cụ thể. "
            "Từ câu chuyện, rút ra bài học hoặc insight quan trọng. "
            "Liên kết tự nhiên sang nội dung phân tích chuyên sâu, "
            "dùng câu chuyện như sợi dây xuyên suốt bài viết. "
            "Kết thúc bằng cách quay lại câu chuyện mở đầu — tạo cảm giác khép kín. "
            "Phù hợp cho bài viết cần tạo kết nối cảm xúc với người đọc."
        ),
    },
    {
        "id": "listicle",
        "label": "Danh sách đánh số",
        "instruction": (
            "Trình bày nội dung dưới dạng danh sách đánh số rõ ràng (3-7 mục). "
            "Mỗi mục có tiêu đề ngắn gọn kèm 2-3 câu giải thích đi thẳng trọng tâm. "
            "Sắp xếp các mục theo thứ tự quan trọng giảm dần hoặc logic tuần tự. "
            "Mở đầu bằng 1 đoạn giới thiệu ngắn (2-3 câu) nêu bối cảnh. "
            "Kết thúc bằng đoạn tổng hợp ngắn gọn, không lặp lại nội dung từng mục. "
            "Dùng gạch đầu dòng hoặc danh sách phụ bên trong nếu cần chi tiết hóa."
        ),
    },
    {
        "id": "comparison",
        "label": "So sánh trước/sau",
        "instruction": (
            "Cấu trúc bài theo lối đối chiếu trước và sau (Before/After). "
            "Mở đầu bằng mô tả tình trạng 'trước' một cách chi tiết, gợi hình. "
            "Giới thiệu bước chuyển (sản phẩm/phương pháp) với cơ chế hoạt động rõ ràng. "
            "Mô tả kết quả 'sau' bằng dữ liệu cụ thể, cảm nhận thực tế, hoặc số liệu đo lường. "
            "Tuyệt đối KHÔNG dùng bảng (table). Trình bày so sánh bằng các đoạn văn "
            "đối chiếu hoặc danh sách gạch đầu dòng song song."
        ),
    },
    {
        "id": "question_answer",
        "label": "Hỏi đáp xen kẽ",
        "instruction": (
            "Viết nội dung theo dạng hỏi-đáp (Q&A) tự nhiên. "
            "Xen kẽ câu hỏi thường gặp (dạng người đọc thật sự sẽ hỏi) "
            "với câu trả lời chi tiết, có dẫn chứng. "
            "Mỗi cặp hỏi-đáp là một tiểu mục độc lập, dễ quét nhanh. "
            "Câu hỏi viết bằng ngôn ngữ tìm kiếm tự nhiên (search query). "
            "Không mở đầu bằng đoạn giới thiệu dài — đi thẳng vào Q&A đầu tiên."
        ),
    },
    {
        "id": "qa_focused",
        "label": "Hỏi đáp tập trung",
        "instruction": (
            "Cấu trúc toàn bài tập trung vào câu hỏi và câu trả lời ngắn gọn — "
            "mỗi câu trả lời không quá 3-4 câu, đáp ứng ngay kỳ vọng người đọc. "
            "Ưu tiên các câu hỏi phổ biến nhất theo search intent. "
            "Bổ sung 1-2 câu dẫn chứng hoặc lưu ý thực tế sau mỗi câu trả lời. "
            "Tối ưu cho Google Featured Snippet và AI Overviews. "
            "Kết thúc bằng 1 câu hỏi mở để người đọc suy ngẫm."
        ),
    },
    {
        "id": "inverted_pyramid",
        "label": "Kim tự tháp ngược",
        "instruction": (
            "Áp dụng cấu trúc báo chí Kim Tự Tháp Ngược (Inverted Pyramid). "
            "Mở đầu bằng kết luận hoặc thông tin quan trọng nhất — "
            "trả lời ngay câu hỏi cốt lõi của người đọc trong 2-3 câu đầu tiên. "
            "Sau đó mở rộng với chi tiết bổ sung, bối cảnh, dẫn chứng, số liệu. "
            "Kết thúc bằng thông tin phụ trợ hoặc liên kết liên quan. "
            "Tuyệt đối KHÔNG mở bài kiểu dẫn dắt dài dòng hay hỏi câu hỏi tu từ."
        ),
    },
    {
        "id": "myth_busting",
        "label": "Bóc trần sự thật",
        "instruction": (
            "Cấu trúc bài viết theo lối bóc trần sự thật (Myth Busting). "
            "Mở đầu bằng 1-2 quan niệm sai lầm phổ biến mà nhiều người tin là đúng. "
            "Dùng heading dạng 'Sự thật #N:' hoặc 'Lầm tưởng vs Thực tế'. "
            "Phản biện từng quan niệm bằng dữ liệu khoa học, nghiên cứu thực tế, "
            "trích dẫn chuyên gia có nguồn rõ ràng. "
            "Đưa ra sự thật đúng đắn kèm lời khuyên hành động cụ thể. "
            "Giọng điệu dứt khoát, có chính kiến rõ ràng, không lưỡng lự."
        ),
    },
    {
        "id": "timeline_journey",
        "label": "Hành trình theo thời gian",
        "instruction": (
            "Trình bày nội dung theo trục thời gian hoặc các giai đoạn phát triển. "
            "Chia thành 3-5 mốc/giai đoạn rõ ràng, mỗi giai đoạn có tiêu đề riêng. "
            "Phân tích nguyên nhân và kết quả ở mỗi mốc, kết nối logic giữa các giai đoạn. "
            "Kết thúc bằng dự báo xu hướng tương lai hoặc khuyến nghị hành động. "
            "Phù hợp cho bài viết về xu hướng, lịch sử phát triển, case study, "
            "hoặc quy trình chăm sóc da theo tuần/tháng."
        ),
    },
]


def get_dynamic_prompt_context(
    product_id: Optional[str] = None,
    tone_override: Optional[str] = None,
    structure_override: Optional[str] = None,
) -> dict[str, str]:
    """
    SGE Shield: Tạo context entropy cho prompt AI.

    Nếu product_id được truyền, sử dụng deterministic hash (cùng ngày + product = cùng output).
    Nếu không, random hoàn toàn.

    Args:
        product_id: ID sản phẩm/bài viết (optional, dùng cho deterministic mode)
        tone_override: Bắt buộc dùng tone cụ thể (admin override)
        structure_override: Bắt buộc dùng structure cụ thể (admin override)

    Returns:
        Dict với keys: tone_instruction, structure_instruction, tone_id, structure_id
    """
    # Chọn Tone
    if tone_override:
        tone = next((t for t in TONE_SEEDS if t["id"] == tone_override), None)
        if not tone:
            tone = random.choice(TONE_SEEDS)
    elif product_id:
        # Deterministic: Hash(product_id + ngày) → cùng sản phẩm cùng ngày = cùng tone
        day_str = date.today().isoformat()
        tone_hash = int(hashlib.sha256(f"{product_id}:tone:{day_str}".encode()).hexdigest(), 16)
        tone = TONE_SEEDS[tone_hash % len(TONE_SEEDS)]
    else:
        tone = random.choice(TONE_SEEDS)

    # Chọn Structure
    if structure_override:
        structure = next((s for s in STRUCTURE_SEEDS if s["id"] == structure_override), None)
        if not structure:
            structure = random.choice(STRUCTURE_SEEDS)
    elif product_id:
        day_str = date.today().isoformat()
        struct_hash = int(hashlib.sha256(f"{product_id}:struct:{day_str}".encode()).hexdigest(), 16)
        structure = STRUCTURE_SEEDS[struct_hash % len(STRUCTURE_SEEDS)]
    else:
        structure = random.choice(STRUCTURE_SEEDS)

    logger.debug(
        "[SGE Shield] Entropy context: tone=%s, structure=%s",
        tone["id"], structure["id"]
    )

    return {
        "tone_instruction": tone["instruction"],
        "structure_instruction": structure["instruction"],
        "tone_id": tone["id"],
        "structure_id": structure["id"],
    }


def build_entropy_system_prompt(
    base_prompt: str,
    product_id: Optional[str] = None,
    tone_override: Optional[str] = None,
    structure_override: Optional[str] = None,
) -> str:
    """
    SGE Shield: Wrap một base system prompt với entropy layer.

    Injects tone + structure instructions vào base prompt mà không phá vỡ
    nội dung gốc. Output luôn khác nhau giữa các lần gọi.

    Args:
        base_prompt: System prompt gốc của Agent
        product_id: Dùng cho deterministic mode
        tone_override: Admin override tone
        structure_override: Admin override structure

    Returns:
        Enhanced system prompt với entropy
    """
    ctx = get_dynamic_prompt_context(
        product_id=product_id,
        tone_override=tone_override,
        structure_override=structure_override,
    )

    entropy_block = (
        f"\n\n[WRITING STYLE]\n"
        f"{ctx['tone_instruction']}\n\n"
        f"[CONTENT STRUCTURE]\n"
        f"{ctx['structure_instruction']}"
    )

    return base_prompt + entropy_block


def get_available_tones() -> list[dict[str, str]]:
    """Trả về danh sách tone seeds cho admin UI quản lý."""
    return [{"id": t["id"], "label": t["label"]} for t in TONE_SEEDS]


def get_available_structures() -> list[dict[str, str]]:
    """Trả về danh sách structure seeds cho admin UI quản lý."""
    return [{"id": s["id"], "label": s["label"]} for s in STRUCTURE_SEEDS]
