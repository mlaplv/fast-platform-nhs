from ..schema import PromptComponent, PromptCategory

COSMETICS_MIXIN = PromptComponent(
    id="niche_cosmetics",
    category=PromptCategory.NICHE,
    content="""[NICHE: COSMETICS & BEAUTY — ELITE V2.2]
1. 💄 GIỌNG ĐIỆU: Sang trọng, quyến rũ, sử dụng ngôn từ gợi cảm xúc (sensory words).
2. 🔬 CÔNG NGHỆ: Nhấn mạnh vào bảng thành phần (Ingredients) và cơ chế tác động (Mechanism of Action).
3. ✨ HIỆU QUẢ: Tập trung vào sự thay đổi diện mạo và cảm giác sau khi sử dụng.
4. 🛡️ PHÁP LÝ: Tuyệt đối không dùng các từ "điều trị", "chữa khỏi" (Medical claims). Thay bằng "hỗ trợ cải thiện", "mang lại vẻ đẹp".
"""
)

def register_cosmetics(composer_instance) -> None:
    composer_instance.register_component(COSMETICS_MIXIN)
