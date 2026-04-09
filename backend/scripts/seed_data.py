# SSOT Seed Data (V72.0)
# AI Keys are NOW managed in .env via SUPPORT_GEMINI_KEYS.
GEMINI_KEYS = []

CATEGORY_DEFS = [
    {"id": "cat_serum", "name": "Serum", "slug": "serum", "icon": "💧"},
    {"id": "cat_kem_duong", "name": "Kem dưỡng", "slug": "kem-duong", "icon": "🧴"},
    {"id": "cat_mat_na", "name": "Mặt nạ", "slug": "mat-na", "icon": "🎭"},
    {"id": "cat_cham_soc_mat", "name": "Chăm sóc mắt", "slug": "cham-soc-mat", "icon": "👁️"}
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
    },
    {
        "id": "prod_hurry_harry",
        "name": "Hurry Harry Wrinkle Serum",
        "slug": "hurry-harry-wrinkle-serum",
        "sku": "4968123159005",
        "price": 850000,
        "category_id": "cat_kem_duong",
        "short_description": "Serum xóa mờ nếp nhăn vùng mắt và khóe miệng hiệu quả.",
        "description": "Serum chuyên biệt giúp làm đầy các nếp nhăn, cung cấp Collagen và Elastin cho làn da tươi trẻ.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "20g",
            "brand": "Miccosmo"
        }
    },
    {
        "id": "prod_white_label",
        "name": "White Label Placenta Cream",
        "slug": "white-label-placenta-cream",
        "sku": "4968123159006",
        "price": 450000,
        "category_id": "cat_kem_duong",
        "short_description": "Kem dưỡng trắng da chiết xuất nhau thai giúp da trắng hồng tự nhiên.",
        "description": "Kem dưỡng trắng da, se khít lỗ chân lông và ngăn ngừa lão hóa với công thức Placenta 100%.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "60g",
            "brand": "Miccosmo"
        }
    }
]

PRODUCT_NAMES = [
    "MICCOSMO BEPPIN BODY VIRGIN WHITE SERUM 30g",
    "Hurry Harry Wrinkle Serum",
    "White Label Placenta Cream"
]

ARTICLE_TITLES = []

# Support Knowledge Base (Elite V2.2)
SUPPORT_KNOWLEDGE_DEFS = []