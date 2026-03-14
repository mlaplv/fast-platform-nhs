import re
import logging

logger = logging.getLogger("api-gateway")

class TextSanitizer:
    """
    XoHi 2026 Silent Cleaner:
    Tự động dọn rác văn bản trước khi check bản quyền hoặc SEO.
    Giúp tiết kiệm Token AI và làm sạch bài viết cho SEO.
    """

    # Bắt các đoạn văn rác: <p>-</p>, <p> . </p>, <p>&nbsp;</p>
    RE_TRASH_PARAGRAPH = re.compile(r'<p[^>]*>\s*[^\wàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{0,5}\s*</p>', re.IGNORECASE)

    # Bắt dấu gạch ngang hoặc phẩy thừa ở cuối câu trước khi đóng thẻ (vd: "abc -</p>")
    RE_TRAILING_DEBRIS = re.compile(r'([,\-\s\u2013\u2014]+)(</p>|</div>|<br\s*/?>)', re.IGNORECASE)

    # Bắt khoảng trắng rác giữa các thẻ
    RE_EXCESSIVE_SPACES = re.compile(r'\s{2,}')

    def sanitize(self, html_content: str) -> str:
        if not html_content:
            return ""

        original_len = len(html_content)

        # 1. Xóa đoạn văn rác
        cleaned = self.RE_TRASH_PARAGRAPH.sub('', html_content)

        # 2. Xóa ký tự lửng lơ cuối câu (thay bằng chính thẻ đóng đó)
        cleaned = self.RE_TRAILING_DEBRIS.sub(r'\2', cleaned)

        # 3. Dọn khoảng trắng
        cleaned = self.RE_EXCESSIVE_SPACES.sub(' ', cleaned)

        new_len = len(cleaned)
        if original_len != new_len:
            logger.info(f"[TextSanitizer] Cleaned {original_len - new_len} characters of debris.")

        return cleaned.strip()
