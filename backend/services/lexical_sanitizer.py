"""
SGE Shield V1.0: Lexical Sanitizer — AI Buzzword Neutralizer.

Phát hiện và thay thế/loại bỏ các cụm từ "rập khuôn AI" (AI buzzwords)
mà Google SGE dùng để nhận diện nội dung AI-generated.

Architecture:
- AI_BUZZWORDS: Dict[pattern, List[replacement]] — pre-compiled regex
- sanitize_ai_text(): Main entry point, chạy sync (< 5ms trên text 10K)
- Deterministic replacement: Dùng seed để chọn replacement (reproducible)

Performance: Pre-compiled regex patterns, O(n) scan.
"""
import hashlib
import logging
import random
import re
from typing import Optional

logger = logging.getLogger("api-gateway")


# ═══════════════════════════════════════════════════════════════════════════════
# AI BUZZWORD REGISTRY
# Key: Regex pattern (case-insensitive Vietnamese + English)
# Value: List[str] — replacements (empty string = xóa hoàn toàn)
# ═══════════════════════════════════════════════════════════════════════════════

_BUZZWORD_MAP: dict[str, list[str]] = {
    # Vietnamese AI clichés
    r"[Tt]hật không ngoa khi nói": ["Phải nói rằng", "Nói thật", ""],
    r"[Tt]óm lại": ["Nói chung", "Cuối cùng", "Nhìn chung", ""],
    r"[Hh]ứa hẹn mang lại": ["Mang lại", "Giúp", "Hỗ trợ"],
    r"[Đđ]i sâu vào": ["Tìm hiểu", "Xem xét", "Phân tích"],
    r"[Nn]ổi bật với": ["Đặc biệt ở", "Ấn tượng bởi", "Điểm mạnh là"],
    r"[Kk]hông thể phủ nhận": ["Rõ ràng", "Hiển nhiên", "Thực tế cho thấy"],
    r"[Mm]ang đến trải nghiệm": ["Tạo cảm giác", "Cho bạn", "Giúp bạn"],
    r"[Gg]iải pháp toàn diện": ["Cách xử lý hiệu quả", "Phương pháp", "Giải pháp"],
    r"[Đđ]áng chú ý": ["Thú vị", "Hay", "Đáng xem"],
    r"[Tt]hế giới của": ["Lĩnh vực", "Ngành", ""],
    r"[Kk]hám phá ngay": ["Xem thêm", "Tìm hiểu thêm", ""],
    r"[Cc]ùng tìm hiểu": ["Hãy xem", "Xem ngay", ""],
    r"[Bb]ài viết này sẽ": ["Chúng tôi sẽ", "Bài này", ""],
    r"[Tt]rong bài viết này": ["Ở đây", "Dưới đây", ""],
    r"[Cc]hắc hẳn bạn đã": ["Có thể bạn đã", "Bạn từng", ""],
    r"[Vv]ới sự phát triển của": ["Khi", "Nhờ", ""],
    r"[Kk]hông chỉ\.\.\.mà còn": ["Vừa...vừa", "Ngoài ra còn", ""],
    r"[Tt]ừ đó giúp": ["Giúp", "Nhờ đó", ""],
    r"[Gg]iúp bạn có được": ["Cho bạn", "Giúp đạt được", "Mang lại"],
    r"[Bb]ạn có biết": ["", "Thực tế là", ""],

    # English AI clichés (cho nội dung song ngữ)
    r"[Uu]nlock the power": ["Khám phá", "Trải nghiệm", ""],
    r"[Ii]n today's world": ["Hiện nay", "Ngày nay", ""],
    r"[Ii]t's worth noting": ["Lưu ý rằng", "", "Cần biết"],
    r"[Ii]n conclusion": ["Tóm lại", "", "Cuối cùng"],
    r"[Ll]et's dive in": ["Hãy bắt đầu", "", "Cùng xem"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# PRE-COMPILED PATTERNS (Performance: compile 1 lần, dùng mãi)
# ═══════════════════════════════════════════════════════════════════════════════

_COMPILED_PATTERNS: list[tuple[re.Pattern[str], list[str]]] = [
    (re.compile(pattern, re.IGNORECASE), replacements)
    for pattern, replacements in _BUZZWORD_MAP.items()
]

# Số lượng patterns (để log)
_PATTERN_COUNT: int = len(_COMPILED_PATTERNS)

logger.info("[SGE Shield] Lexical Sanitizer initialized: %d buzzword patterns compiled", _PATTERN_COUNT)


def sanitize_ai_text(
    text: str,
    seed: Optional[str] = None,
    enabled: bool = True,
) -> str:
    """
    SGE Shield: Loại bỏ/thay thế AI buzzwords trong text.

    Scan text bằng pre-compiled regex patterns, thay thế mỗi match
    bằng một replacement ngẫu nhiên (hoặc deterministic nếu có seed).

    Args:
        text: Văn bản cần sanitize
        seed: Deterministic seed cho reproducible replacements
        enabled: Toggle on/off (admin control)

    Returns:
        Văn bản đã được sanitize (hoặc nguyên bản nếu disabled)

    Performance: < 5ms trên text 10,000 ký tự (pre-compiled regex)
    """
    if not enabled or not text or not text.strip():
        return text

    # Tạo RNG: Deterministic nếu có seed, random nếu không
    if seed:
        seed_int = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % (2 ** 32)
        rng = random.Random(seed_int)
    else:
        rng = random.Random()

    result = text
    hit_count = 0

    for pattern, replacements in _COMPILED_PATTERNS:
        if pattern.search(result):
            # Chọn replacement ngẫu nhiên (hoặc deterministic)
            replacement = rng.choice(replacements)
            result = pattern.sub(replacement, result)
            hit_count += 1

    # Dọn whitespace thừa sau replacement (tránh double spaces)
    if hit_count > 0:
        result = re.sub(r"  +", " ", result)
        result = re.sub(r"\n\s*\n\s*\n", "\n\n", result)
        logger.debug("[SGE Shield] Sanitized %d AI buzzwords", hit_count)

    return result.strip()


def get_buzzword_count() -> int:
    """Trả về số lượng buzzword patterns đang active."""
    return _PATTERN_COUNT
