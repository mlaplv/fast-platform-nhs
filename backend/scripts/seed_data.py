# SSOT Seed Data (V72.0)
# AI Keys are NOW managed in .env via SUPPORT_GEMINI_KEYS.
GEMINI_KEYS = []

CATEGORY_DEFS = [
    {"id": "cat_kem_duong", "name": "Kem dưỡng", "slug": "kem-duong"}
]

SUB_CATEGORY_DEFS = []

PRODUCT_DEFS = [
    {
        "id": "prod_miccosmo_virgin_white",
        "name": "MICCOSMO BEPPIN BODY VIRGIN WHITE SERUM 30g",
        "slug": "miccosmo-beppin-body-virgin-white-serum",
        "sku": "4968123159004",
        "price": 600000,
        "category_id": "cat_kem_duong",
        "short_description": "Serum chuyên biệt cho vùng da nhạy cảm giúp hỗ trợ dưỡng hồng, giảm thâm sạm và phục hồi.",
        "description": "Serum dưỡng hồng vùng kín, nhũ hoa, nách và đùi trong với chiết xuất từ Nhật Bản.",
        "product_metadata": {
            "ingredients": "Water, Butylene Glycol, Glycerin, Vitamin C dẫn xuất & Vitamin E, Chiết xuất lá hoa anh đào.",
            "instructions": "Làm sạch và lau khô vùng da cần chăm sóc, thoa nhẹ và massage đều, ngày 2 lần.",
            "origin": "Japan",
            "weight": "30g"
        }
    }
]

PRODUCT_NAMES = ["MICCOSMO BEPPIN BODY VIRGIN WHITE SERUM 30g"]

ARTICLE_TITLES = []

# Support Knowledge Base (Elite V2.2)
SUPPORT_KNOWLEDGE_DEFS = []