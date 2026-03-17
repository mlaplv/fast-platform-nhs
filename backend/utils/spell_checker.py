import re
import unicodedata
from typing import List, Tuple, Set

# Phase 76.9: VN-Syllable-Sieve 2026 (Zero AI Cost)
# Dựa trên quy tắc ngữ âm học tiếng Việt chuẩn 2026

# 1. Các thành phần âm tiết
VOWELS = "aáàảãạăắằẳẵặâấầẩẫậeéèẻẽẹêếềểễệiíìỉĩịoóòỏõọôốồổỗộơớờởỡợuúùủũụưứừửữựyýỳỷỹỵ"
CONSONANTS_START = {
    "b", "c", "ch", "d", "đ", "g", "gh", "gi", "h", "k", "kh", "l", "m", "n", "ng", "ngh", "nh", "p", "ph", "qu", "r", "s", "t", "th", "tr", "v", "x"
}
CONSONANTS_END = {"p", "t", "c", "ch", "m", "n", "ng", "nh"}

# 2. Quy tắc chính tả cứng
RE_NGH = re.compile(r"ngh(?![ieêíìỉĩịếềểễệ])", re.IGNORECASE)
RE_GH = re.compile(r"gh(?![ieêíìỉĩịếềểễệ])", re.IGNORECASE)
RE_K = re.compile(r"k(?![ieêíìỉĩịếềểễệ])", re.IGNORECASE)
RE_C = re.compile(r"c(?=[ieêíìỉĩịếềểễệ])", re.IGNORECASE)
RE_NG = re.compile(r"ng(?=[ieêíìỉĩịếềểễệ])", re.IGNORECASE)
RE_G = re.compile(r"g(?=[ieêíìỉĩịếềểễệ])", re.IGNORECASE)
RE_QU = re.compile(r"q(?!u)", re.IGNORECASE)

class VNSpellChecker:
    """
    R82: Hybrid Syllable Sieve Engine V2026.
    Kiểm tra chính tả tiếng Việt thuần thuật toán, không dùng AI.
    """

    def __init__(self):
        # Tải bộ vần hợp lệ (simplified for 2026 speed)
        self.valid_rimes = self._generate_basic_rimes()

    def _generate_basic_rimes(self) -> Set[str]:
        # Trong thực tế, bộ này sẽ được load từ resource file.
        # Ở đây em định nghĩa các vần phổ biến nhất để demo logic Sieve.
        return {"oanh", "uynh", "oang", "uong", "ieng", "uoc", "uot", "ach", "ich", "anh", "inh"}

    def is_valid_syllable(self, word: str) -> bool:
        """Kiểm tra một từ đơn có phải là âm tiết tiếng Việt hợp lệ không."""
        word = unicodedata.normalize("NFC", word.lower())
        if not word or not any(c in VOWELS for c in word):
            return True # Không phải tiếng Việt hoặc từ mượn không dấu

        # 1. Check quy tắc tổ hợp phụ âm cứng
        if RE_NGH.search(word) or RE_GH.search(word) or RE_K.search(word) or \
           RE_C.search(word) or RE_NG.search(word) or RE_G.search(word) or RE_QU.search(word):
            return False

        # 2. Check dấu thanh cho phụ âm cuối (p, t, c, ch)
        # Quy tắc: kết thúc bằng p, t, c, ch chỉ đi với dấu Sắc hoặc Nặng
        if any(word.endswith(c) for c in ["p", "t", "c", "ch"]):
            # Lấy dấu thanh (NFD)
            nfd_word = unicodedata.normalize("NFD", word)
            marks = [c for c in nfd_word if unicodedata.category(c) == "Mn"]
            # Mn: \u0301 là dấu sắc, \u0323 là dấu nặng
            if marks and not any(m in ["\u0301", "\u0323"] for m in marks):
                return False

        return True

    async def check_content(self, text: str) -> List[Tuple[str, str]]:
        """
        Phân tích văn bản và trả về danh sách các từ nghi ngờ lỗi.
        Returns: List[(từ_sai, lý_do)]
        """
        # Loại bỏ HTML tags nếu có
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        words = re.findall(r'\b\w+\b', clean_text)

        errors = []
        for word in words:
            if not self.is_valid_syllable(word):
                errors.append((word, "Vi phạm quy tắc cấu tạo âm tiết tiếng Việt"))

        return errors

spell_checker = VNSpellChecker()
