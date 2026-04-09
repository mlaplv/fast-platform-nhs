# SSOT Seed Data (V72.0)
# AI Keys are NOW managed in .env via SUPPORT_GEMINI_KEYS.
GEMINI_KEYS = []

CATEGORY_DEFS = [
    {"id": "cat_serum", "name": "Serum", "slug": "serum", "icon": "💧"},
    {"id": "cat_kem_duong", "name": "Kem dưỡng", "slug": "kem-duong", "icon": "🧴"},
    {"id": "cat_mat_na", "name": "Mặt nạ", "slug": "mat-na", "icon": "🎭"},
    {"id": "cat_cham_soc_mat", "name": "Chăm sóc mắt", "slug": "cham-soc-mat", "icon": "👁️"},
    {"id": "cat_sua_rua_mat", "name": "Sữa rửa mặt", "slug": "sua-rua-mat", "icon": "🧼"},
    {"id": "cat_tinh_chat", "name": "Tinh chất", "slug": "tinh-chat", "icon": "🧪"},
    {"id": "cat_kem_mat", "name": "Kem mắt", "slug": "kem-mat", "icon": "👁️"}
]

SUB_CATEGORY_DEFS = []

PRODUCT_DEFS = [
    {
        "id": "prod_miccosmo_virgin_white",
        "name": "Miccosmo Beppin Body Virgin White Serum 30g",
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
    },
    {
        "id": "prod_miccosmo_eye_cream_gold",
        "name": "Miccosmo White Label Premium Placenta Rich Gold Eye Cream 25g – Kem mắt hỗ trợ mờ thâm, dưỡng sáng",
        "slug": "miccosmo-white-label-premium-placenta-rich-gold-eye-cream-25g",
        "sku": "4968123159010",
        "price": 600000,
        "category_id": "cat_kem_mat",
        "short_description": "Kem mắt giàu Placenta Gold hỗ trợ mờ thâm, dưỡng sáng vùng mắt.",
        "description": "Kem mắt cao cấp kết hợp vàng và nhau thai giúp làm sáng vùng da quanh mắt, giảm quầng thâm và bọng mắt.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "25g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-RICH-GOLD-EYE-CREAM-25g-Kem-Mat-Nhau-Thai-Giam-Quang-Tham_.%20(127).png?v=1756973500"
        }
    },
    {
        "id": "prod_miccosmo_placenta_pack",
        "name": "Miccosmo White Label Premium Placenta Pack 130g - Mặt nạ rửa trôi hỗ trợ dưỡng sáng",
        "slug": "miccosmo-white-label-premium-placenta-pack-130g",
        "sku": "4968123159011",
        "price": 600000,
        "category_id": "cat_mat_na",
        "short_description": "Mặt nạ rửa trôi tinh chất nhau thai giúp da trắng sáng tức thì.",
        "description": "Mặt nạ ủ trắng da chiết xuất nhau thai cao cấp, giúp loại bỏ hắc tố và cung cấp độ ẩm cho da.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "130g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-PACK-130g-Mat-na-u-duong-trang-sang-da-tu-nhau-thai_23.png?v=1754288435"
        }
    },
    {
        "id": "prod_miccosmo_placenta_wash",
        "name": "Miccosmo White Label Premium Placenta Wash 110g - Sữa rửa mặt sạch sâu, làm dịu da",
        "slug": "miccosmo-white-label-premium-placenta-wash-110g",
        "sku": "4968123159012",
        "price": 450000,
        "category_id": "cat_sua_rua_mat",
        "short_description": "Sữa rửa mặt tạo bọt mịn chiết xuất nhau thai giúp sạch sâu và dịu da.",
        "description": "Sữa rửa mặt không chứa hóa chất độc hại, bọt tuyết mịn màng lấy đi bụi bẩn mà không gây khô da.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "110g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/20250729_HOrZADYhKo.png?v=1753805579"
        }
    },
    {
        "id": "prod_miccosmo_placenta_essence",
        "name": "Miccosmo White Label Premium Placenta Essence 180ml - Tinh chất cấp ẩm, làm dịu da",
        "slug": "miccosmo-white-label-premium-placenta-essence-180ml",
        "sku": "4968123159013",
        "price": 550000,
        "category_id": "cat_tinh_chat",
        "short_description": "Tinh chất Placenta thẩm thấu nhanh giúp da căng mịn, làm dịu da.",
        "description": "Nước hoa hồng dạng tinh chất lỏng nhẹ, cấp ẩm sâu và làm sáng da hiệu quả.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "180ml",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-ESSENCE-180ml-TINH-CHAT-CAP-AM-LAM-DIU-DA_.%20(14.1).png?v=1766106546"
        }
    },
    {
        "id": "prod_miccosmo_eye_cream_basic",
        "name": "Miccosmo White Label Premium Placenta Eye Cream 30g - Kem hỗ trợ mờ thâm mắt",
        "slug": "miccosmo-white-label-premium-placenta-eye-cream-30g",
        "sku": "4968123159014",
        "price": 600000,
        "category_id": "cat_kem_mat",
        "short_description": "Kem dưỡng vùng mắt hỗ trợ xóa tan quầng thâm và nếp nhăn.",
        "description": "Kem mắt chuyên biệt với nồng độ Placenta cao, lành tính cho vùng da nhạy cảm.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "30g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/20250729_n1K6woBCCg.jpeg?v=1753804646"
        }
    },
    {
        "id": "prod_miccosmo_gold_essence_co_dac",
        "name": "Miccosmo White Label Premium Placenta Gold Essence 10ml - Tinh chất cô đặc hỗ trợ ngừa lão hóa",
        "slug": "miccosmo-white-label-premium-placenta-gold-essence-10ml",
        "sku": "4968123159015",
        "price": 690000,
        "category_id": "cat_tinh_chat",
        "short_description": "Tinh chất cô đặc Placenta Gold giúp ngăn ngừa lão hóa vượt trội.",
        "description": "Sản phẩm chứa chiết xuất vàng và nhau thai đậm đặc, thẩm thấu sâu giúp tái tạo làn da.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "10ml",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/20250729_BaDvp7EAS2.jpeg?v=1753804303"
        }
    },
    {
        "id": "prod_white_label_rich_gold_cream",
        "name": "Miccosmo White Label Placenta Rich Gold Cream 60g - Kem hỗ trợ dưỡng sáng ngừa lão hóa",
        "slug": "miccosmo-white-label-placenta-rich-gold-cream-60g",
        "sku": "4968123159016",
        "price": 790000,
        "category_id": "cat_kem_duong",
        "short_description": "Kem dưỡng cao cấp Gold Placenta dưỡng trắng và chống lão hóa.",
        "description": "Dòng kem dưỡng 'Rich Gold' với các hạt vàng nano giúp da săn chắc, trắng hồng rạng rỡ.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "60g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/-MICCOSMO-WHITE-LABEL-PLACENTA-RICH-GOLD-CREAM-60g-Kem-duong-nhau-thai-giup-da-trang-sang-cap-am-5.png?v=1754560971"
        }
    },
    {
        "id": "prod_white_label_rich_gold_essence",
        "name": "Miccosmo White Label Placenta Rich Gold Essence 180ml - Tinh chất hỗ trợ dưỡng sáng ngừa lão hóa",
        "slug": "miccosmo-white-label-placenta-rich-gold-essence-180ml",
        "sku": "4968123159017",
        "price": 600000,
        "category_id": "cat_tinh_chat",
        "short_description": "Lotion tinh chất vàng nhau thai dưỡng trắng sáng da.",
        "description": "Cung cấp độ ẩm và dưỡng chất tức thì, giúp se khít lỗ chân lông và làm mịn bề mặt da.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "180ml",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/20250729_CSBzDOM2TH.jpeg?v=1753803165"
        }
    },
    {
        "id": "prod_hurry_harry_hand_balm",
        "name": "Miccosmo Hurry Harry Premium Hand Balm 40g - Kem dưỡng da tay mềm mịn",
        "slug": "miccosmo-hurry-harry-premium-hand-balm-40g",
        "sku": "4968123159018",
        "price": 400000,
        "category_id": "cat_kem_duong",
        "short_description": "Kem dưỡng da tay cao cấp giúp đôi tay mềm mại, chống nhăn.",
        "description": "Chiết xuất thảo mộc Nhật Bản giúp phục hồi da tay khô ráp, bảo vệ da tay hiệu quả.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "40g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/20250729_Clo7Mql2nt.jpeg?v=1753785345"
        }
    },
    {
        "id": "prod_hurry_harry_golgo_shot",
        "name": "Miccosmo Hurry Harry Premium Golgo Shot 3.4g - Thỏi dưỡng hỗ trợ ngừa lão hóa",
        "slug": "miccosmo-hurry-harry-premium-golgo-shot-3-4g",
        "sku": "4968123159019",
        "price": 550000,
        "category_id": "cat_kem_duong",
        "short_description": "Thỏi dưỡng nếp nhăn vùng cười và mắt tiện lợi.",
        "description": "Giúp làm đầy rãnh cười và vết chân chim, có thể sử dụng ngay cả khi đang trang điểm.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "3.4g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/-MICCOSMO-HURRY-HARRY-PREMIUM-GOLGO-SHOT-6g-Thoi-serum-collagen-chong-nhan-vung-mat-mui-mieng_64-1.png?v=1754288804"
        }
    },
    {
        "id": "prod_white_label_whitening_cream",
        "name": "Miccosmo White Label Platinum Placenta Whitening Cream 20g - Kem dưỡng da nám",
        "slug": "miccosmo-white-label-platinum-placenta-whitening-cream-20g",
        "sku": "4968123159020",
        "price": 690000,
        "category_id": "cat_kem_duong",
        "short_description": "Kem dưỡng trắng đặc trị sạm nám và tàn nhang.",
        "description": "Sản phẩm thuốc (Medicated) chứa Placenta và hoạt chất giúp ngăn chặn sự hình thành Melanin.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "20g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/20250729_r35Vm05wZz.jpeg?v=1753782198"
        }
    },
    {
        "id": "prod_white_label_rich_gold_gel",
        "name": "Miccosmo White Label Premium Placenta Rich Gold Gel 30gr - Gel dưỡng hỗ trợ mờ thâm mắt",
        "slug": "miccosmo-white-label-premium-placenta-rich-gold-gel-30gr",
        "sku": "4968123159021",
        "price": 650000,
        "category_id": "cat_kem_mat",
        "short_description": "Gel dưỡng mắt mờ thâm với tinh chất vàng.",
        "description": "Dạng gel mỏng nhẹ, thấm nhanh, không gây bết dính cho vùng da mắt mỏng manh.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "30g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/20250729_zTkx9FSRTL.jpeg?v=1753775962"
        }
    },
    {
        "id": "prod_hurry_harry_neck_cream",
        "name": "Miccosmo Hurry Harry Premium Neck Cream Rich 40gr - Kem dưỡng sáng cổ",
        "slug": "miccosmo-hurry-harry-premium-neck-cream-rich-40gr",
        "sku": "4968123159022",
        "price": 650000,
        "category_id": "cat_kem_duong",
        "short_description": "Kem dưỡng da vùng cổ giúp mờ nếp nhăn và dưỡng sáng.",
        "description": "Cải thiện tình trạng 'vòng cổ' và da chảy xệ, giúp vùng da cổ săn chắc và sáng hơn.",
        "product_metadata": {
            "origin": "Japan",
            "weight": "40g",
            "image_url": "https://pos.nvncdn.com/3a1578-211785/ps/20250716_t2xmZQtxvN.jpeg?v=1752656410"
        }
    }
]

PRODUCT_NAMES = [
    "Miccosmo Beppin Body Virgin White Serum 30g",
    "Hurry Harry Wrinkle Serum",
    "White Label Placenta Cream",
    "Miccosmo White Label Premium Placenta Rich Gold Eye Cream 25g – Kem mắt hỗ trợ mờ thâm, dưỡng sáng",
    "Miccosmo White Label Premium Placenta Pack 130g - Mặt nạ rửa trôi hỗ trợ dưỡng sáng",
    "Miccosmo White Label Premium Placenta Wash 110g - Sữa rửa mặt sạch sâu, làm dịu da",
    "Miccosmo White Label Premium Placenta Essence 180ml - Tinh chất cấp ẩm, làm dịu da",
    "Miccosmo White Label Premium Placenta Eye Cream 30g - Kem hỗ trợ mờ thâm mắt",
    "Miccosmo White Label Premium Placenta Gold Essence 10ml - Tinh chất cô đặc hỗ trợ ngừa lão hóa",
    "Miccosmo White Label Placenta Rich Gold Cream 60g - Kem hỗ trợ dưỡng sáng ngừa lão hóa",
    "Miccosmo White Label Placenta Rich Gold Essence 180ml - Tinh chất hỗ trợ dưỡng sáng ngừa lão hóa",
    "Miccosmo Hurry Harry Premium Hand Balm 40g - Kem dưỡng da tay mềm mịn",
    "Miccosmo Hurry Harry Premium Golgo Shot 3.4g - Thỏi dưỡng hỗ trợ ngừa lão hóa",
    "Miccosmo White Label Platinum Placenta Whitening Cream 20g - Kem dưỡng da nám",
    "Miccosmo White Label Premium Placenta Rich Gold Gel 30gr - Gel dưỡng hỗ trợ mờ thâm mắt",
    "Miccosmo Hurry Harry Premium Neck Cream Rich 40gr - Kem dưỡng sáng cổ"
]

ARTICLE_DEFS = [
    {
        "id": "art_aging_strategies",
        "title": "Strategies to Combat Premature Skin Aging",
        "slug": "strategies-to-combat-premature-skin-aging",
        "content": "Lão hóa bắt đầu âm thầm sau tuổi 20. Để duy trì vẻ ngoài trẻ trung, cần tập trung vào chống nắng, cấp ẩm, ngủ đủ giấc đến bổ sung dưỡng chất chuyên sâu.",
        "image_url": "https://miccosmo.vn/images/news/aging-strategies.jpg"
    },
    {
        "id": "art_cleansing_fundamentals",
        "title": "The Fundamentals of Proper Facial Cleansing",
        "slug": "fundamentals-of-proper-facial-cleansing",
        "content": "Rửa mặt đúng cách giúp bảo vệ hàng rào da, duy trì độ ẩm và hỗ trợ hấp thụ dưỡng chất tốt hơn, đồng thời ngăn ngừa xỉn màu và mụn.",
        "image_url": "https://miccosmo.vn/images/news/cleansing.jpg"
    },
    {
        "id": "art_neck_revitalizing",
        "title": "Revitalizing the Often Forgotten Neck Area",
        "slug": "revitalizing-the-forgotten-neck-area",
        "content": "Vùng cổ lão hóa rất nhanh, cần học cách thoa kem cổ chuẩn giúp nâng cơ nhẹ nhàng, giữ da mịn màng, tránh chảy xệ và nếp nhăn sâu.",
        "image_url": "https://miccosmo.vn/images/news/neck-care.jpg"
    },
    {
        "id": "art_oily_skin_hydration",
        "title": "Why Oily Skin Still Requires Hydration",
        "slug": "why-oily-skin-requires-hydration",
        "content": "Bỏ qua kem dưỡng có thể kích thích dầu thừa. Cấp ẩm đúng cách giúp cân bằng dầu – nước, hạn chế bít tắc lỗ chân lông và giúp làn da khỏe mạnh.",
        "image_url": "https://miccosmo.vn/images/news/oily-skin.jpg"
    }
]

ARTICLE_TITLES = [article["title"] for article in ARTICLE_DEFS]

# Support Knowledge Base (Elite V2.2)
SUPPORT_KNOWLEDGE_DEFS = []