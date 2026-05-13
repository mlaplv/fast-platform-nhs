from ..schema import PromptComponent, PromptCategory

REVIEW_BOOSTER = PromptComponent(
    id="agent_review_booster",
    category=PromptCategory.AGENT,
    content="""Nhiệm vụ: Viết lại đánh giá cho {topic} thành ĐÚNG 1 CÂU DUY NHẤT, chân thật và giàu tính tham khảo.

CHỈ THỊ "THẬT":
1. BÁM SÁT ĐỐI TƯỢNG: Phải dùng tên hoặc loại của {topic} trong câu (ví dụ: nếu là Mặt nạ thì không được viết Serum).
2. ĐA DẠNG HÓA: Tuyệt đối không lặp lại cấu trúc "Sản phẩm tốt, thấm nhanh...". Hãy biến thiên cách mở đầu và kết thúc tùy theo dữ liệu gốc.
3. CHI TIẾT KỸ THUẬT: Đưa đúng 1 tiểu tiết vật lý thật nhất (vỏ hộp, mùi hương, cảm giác trên da, vòi xịt...).
4. KHÔNG HOA MỸ: Cấm các tính từ sáo rỗng.
5. ĐỘ DÀI: Tối đa 35 từ.

Dữ liệu gốc: {content_foundation}
"""
)

def register_review_booster(composer_instance) -> None:
    composer_instance.register_component(REVIEW_BOOSTER)
