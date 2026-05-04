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
# ═══════════════════════════════════════════════════════════════════════════════

TONE_SEEDS: list[dict[str, str]] = [
    {
        "id": "dermatologist",
        "label": "Chuyên gia da liễu",
        "instruction": (
            "Viết với giọng của một bác sĩ da liễu giàu kinh nghiệm. "
            "Sử dụng thuật ngữ chuyên ngành một cách tự nhiên, "
            "giải thích cơ chế tác dụng và bằng chứng khoa học. "
            "Giọng điệu chuyên nghiệp nhưng gần gũi."
        ),
    },
    {
        "id": "pharmacist",
        "label": "Dược sĩ tận tâm",
        "instruction": (
            "Viết với giọng của dược sĩ lâm sàng. "
            "Tập trung vào hướng dẫn sử dụng, liều lượng, "
            "tương tác thuốc và lưu ý an toàn. "
            "Giọng điệu tận tâm, cẩn thận và đáng tin cậy."
        ),
    },
    {
        "id": "health_blogger",
        "label": "Beauty blogger",
        "instruction": (
            "Viết với phong cách beauty/health blogger trẻ trung. "
            "Chia sẻ trải nghiệm cá nhân, dùng ngôn ngữ đời thường, "
            "xen kẽ mẹo vặt thực tế. "
            "Giọng điệu thân thiện, năng động, dễ tiếp cận cho Gen-Z."
        ),
    },
    {
        "id": "science_writer",
        "label": "Nhà khoa học phân tích",
        "instruction": (
            "Viết với giọng phân tích khoa học chặt chẽ. "
            "Trích dẫn nghiên cứu, so sánh dữ liệu, "
            "sử dụng cấu trúc logic nhân-quả. "
            "Giọng điệu khách quan, tỉ mỉ và có hệ thống."
        ),
    },
    {
        "id": "mom_expert",
        "label": "Mẹ Việt Nam chia sẻ",
        "instruction": (
            "Viết với giọng của một bà mẹ Việt Nam có kinh nghiệm. "
            "Chia sẻ góc nhìn thực tế từ cuộc sống gia đình, "
            "so sánh giữa các sản phẩm đã dùng. "
            "Giọng điệu chân thành, gần gũi và thực tiễn."
        ),
    },
    {
        "id": "customer_advocate",
        "label": "Khách hàng trải nghiệm",
        "instruction": (
            "Viết từ góc nhìn người tiêu dùng thông thái. "
            "Đánh giá sản phẩm dựa trên trải nghiệm thực tế, "
            "so sánh giá cả và chất lượng. "
            "Giọng điệu trung thực, khách quan và có chính kiến."
        ),
    },
    {
        "id": "wellness_coach",
        "label": "Coach sức khỏe",
        "instruction": (
            "Viết với giọng huấn luyện viên sức khỏe tổng thể. "
            "Kết hợp lối sống lành mạnh với sản phẩm hỗ trợ, "
            "động viên người đọc thay đổi thói quen tích cực. "
            "Giọng điệu năng lượng, truyền cảm hứng."
        ),
    },
    {
        "id": "traditional_medicine",
        "label": "Bác sĩ Y học cổ truyền",
        "instruction": (
            "Viết với giọng của chuyên gia Y học cổ truyền. "
            "Kết hợp triết lý Đông y với kiến thức Tây y hiện đại, "
            "giải thích cơ chế từ góc nhìn âm dương, ngũ hành. "
            "Giọng điệu sâu sắc, uyên bác và trầm ổn."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURE SEEDS — Cấu trúc viết bài khác nhau
# Mỗi seed chỉ dẫn AI tổ chức nội dung theo format khác nhau.
# ═══════════════════════════════════════════════════════════════════════════════

STRUCTURE_SEEDS: list[dict[str, str]] = [
    {
        "id": "hook_first",
        "label": "Mở đầu gây tò mò",
        "instruction": (
            "Bắt đầu bằng một câu hỏi hoặc sự thật gây bất ngờ. "
            "Sau đó triển khai nội dung chính, kết thúc bằng lời khuyên thực tế."
        ),
    },
    {
        "id": "problem_solution",
        "label": "Vấn đề → Giải pháp",
        "instruction": (
            "Mở đầu bằng việc nêu rõ vấn đề mà người đọc đang gặp. "
            "Phân tích nguyên nhân, sau đó đưa ra giải pháp cụ thể và kết luận."
        ),
    },
    {
        "id": "story_driven",
        "label": "Kể chuyện trải nghiệm",
        "instruction": (
            "Kể một câu chuyện ngắn liên quan đến chủ đề. "
            "Rút ra bài học và liên kết với nội dung chính."
        ),
    },
    {
        "id": "listicle",
        "label": "Danh sách đánh số",
        "instruction": (
            "Trình bày nội dung dưới dạng danh sách đánh số rõ ràng. "
            "Mỗi mục ngắn gọn, đi thẳng vào trọng tâm."
        ),
    },
    {
        "id": "comparison",
        "label": "So sánh trước/sau",
        "instruction": (
            "So sánh tình trạng trước và sau khi sử dụng sản phẩm/phương pháp. "
            "Dùng dữ liệu cụ thể hoặc mô tả chi tiết sự khác biệt."
        ),
    },
    {
        "id": "question_answer",
        "label": "Hỏi đáp xen kẽ",
        "instruction": (
            "Viết nội dung theo dạng hỏi-đáp. "
            "Xen kẽ câu hỏi thường gặp với câu trả lời chi tiết."
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
