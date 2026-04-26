from ..schema import PromptComponent, PromptCategory

PHARMA_MIXIN = PromptComponent(
    id="niche_pharmaceuticals",
    category=PromptCategory.NICHE,
    content="""[NICHE: PHARMACEUTICALS & HEALTH — ELITE V2.2]
1. 🩺 GIỌNG ĐIỆU: Chuyên gia, tin cậy, khách quan và điềm tĩnh.
2. 📊 BẰNG CHỨNG: Ưu tiên dẫn chứng các nghiên cứu, số liệu hoặc cơ sở khoa học.
3. ⚠️ AN TOÀN: Luôn nhấn mạnh vào sự an toàn, liều lượng và chỉ định của chuyên gia.
4. 🚫 CẤM KỴ: Không phóng đại hiệu quả. Sử dụng từ ngữ chuẩn y khoa (Medical-grade terminology).
"""
)

def register_pharma(composer_instance) -> None:
    composer_instance.register_component(PHARMA_MIXIN)
