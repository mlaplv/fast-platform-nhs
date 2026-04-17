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
        "images": ["img/micsmo/virgin_white_viral_2026.png"],
        "id": "prod_miccosmo_virgin_white",
        "name": "Miccosmo Beppin Body Virgin White Serum 30g",
        "slug": "miccosmo-beppin-body-virgin-white-serum",
        "sku": "4968123159004",
        "price": 600000,
        "category_id": "cat_kem_duong",
        "short_description": "Bật tông trắng sáng cùng Beppin Body Virgin White Serum - Tinh chất dưỡng sáng hồng vùng nhạy cảm (Nách, Nhũ hoa, Bikini). Giải pháp An toàn - Hiệu quả - Không bết dính.",
        "description": "Serum dưỡng hồng vùng kín, nhũ hoa, nách và đùi trong với chiết xuất từ Nhật Bản.",
        "product_metadata": {
            "ingredients": "Water, Butylene Glycol, Glycerin, Vitamin C dẫn xuất & Vitamin E, Chiết xuất lá hoa anh đào.",
            "instructions": "Làm sạch và lau khô vùng da cần chăm sóc, thoa nhẹ và massage đều, ngày 2 lần.",
            "origin": "Japan",
            "weight": "30g",
            "diagnostics_headline": "CHẨN ĐOÁN PHỤC HỒI <span class='text-blue-500'>SẮC TỐ GỐC</span>",
            "diagnostics_subheadline": "Hệ Thống Giải Mã Chỉ Số Hắc Tố Cá Nhân Đừng Để Nỗi Tự Ti Thầm Kín Cản Trở Sự Tự Tin Quyến Rũ Ai Sẽ Thiết Lập Phác Đồ 'hồi Sinh Sắc Tố Hồng' Chuẩn Nhật Bản Bảo Mật Tuyệt Đối 100% Dữ Liệu Chẩn Đoán",
            "quiz_questions": [
                {
                    "id": "q1",
                    "title": "KHU VỰC CẦN GIẢI CỨU SẮC TỐ?",
                    "subtitle": "Chọn vùng da bạn muốn tập trung xóa bỏ hắc tố sạm màu và khôi phục sự rạng rỡ.",
                    "options": [
                        {"label": "Vùng Nách", "value": "underarm", "icon": "🛁", "desc": "Khử thâm chuyên sâu, khôi phục vẻ mịn màng"},
                        {"label": "Vùng Bikini", "value": "bikini", "icon": "👙", "desc": "Tái tạo độ hồng hào, mềm mại tự nhiên"},
                        {"label": "Vùng Nhũ Hoa", "value": "nipple", "icon": "✨", "desc": "Bật tông rạng rỡ, lấy lại sự tự tin"},
                        {"label": "Khác / Đùi trong", "value": "other", "icon": "💧", "desc": "Xử lý sạm màu thâm niên do ma sát"}
                    ]
                },
                {
                    "id": "q2",
                    "title": "TÌNH TRẠNG SẠM ĐEN THỰC TẾ?",
                    "subtitle": "Hệ thống cần xác định mật độ Melanin để tính toán liều lượng phục hồi tối ưu.",
                    "options": [
                        {"label": "Sạm nhẹ", "value": "light", "icon": "🌕", "desc": "Mới xuất hiện dấu hiệu tối màu"},
                        {"label": "Sạm trung bình", "value": "medium", "icon": "🌗", "desc": "Sạm rõ rệt, cần can thiệp để tránh lan rộng"},
                        {"label": "Sạm nặng (Báo động)", "value": "heavy", "icon": "🌑", "desc": "Thâm lâu năm, chai sạm, cần phác đồ mạnh"}
                    ]
                },
                {
                    "id": "q3",
                    "title": "KINH NGHIỆM TRỊ THÂM CỦA BẠN?",
                    "subtitle": "Để AI cân đối nồng độ dẫn xuất Vitamin C và Placenta tinh khiết cho bạn.",
                    "options": [
                        {"label": "Chưa từng dùng gì", "value": "never", "icon": "🌱", "desc": "Khởi đầu an toàn, chuẩn y khoa Nhật"},
                        {"label": "Đã dùng nhưng thất bại", "value": "failed", "icon": "🔄", "desc": "Phá vỡ cấu trúc hắc tố cũ đã lờn thuốc"},
                        {"label": "Cần cải thiện thần tốc", "value": "boost", "icon": "🚀", "desc": "Kích hoạt chế độ phục hồi tế bào tối đa"}
                    ]
                }
            ],
            "reviews": [
                {
                    "name": "suzzyy",
                    "location": "TP.HCM",
                    "rating": 5,
                    "content": "giá thành ổn áp\ncó tặng kèm quà rất oce\nvượt ngoài mong đợi\nmình dùng 1 tuần chưa thấy da sáng hơn\nnhưng có 1 số vết tàn nhang nhỏ thì mờ hẳn nha\nsp ocee nha mấy bà",
                    "attributes": {
                        "Thấm thấu": "tham nhah. k nhon rit",
                        "Da săn chắc": "da sang min và giữ ẩm tốt",
                        "Mùi thơm": "thơm dịu"
                    },
                    "attachments": [
                        {"url": "https://pub-8a62f1c8491842ec9a5789fcfc01b979.r2.dev/review_1.png", "type": "image", "duration": "0:12"},
                        {"url": "https://pub-8a62f1c8491842ec9a5789fcfc01b979.r2.dev/review_2.png", "type": "image", "duration": "0:06"},
                        {"url": "https://pub-8a62f1c8491842ec9a5789fcfc01b979.r2.dev/review_3.png", "type": "image"}
                    ],
                    "likes_count": 3
                },
                {
                    "name": "Hồng Hạnh",
                    "location": "Hà Nội",
                    "rating": 5,
                    "content": "Dùng bao nhiêu loại rồi mới thấy chân ái ở đây. Mới dùng hết nửa tuýp mà vùng bikini đã sáng hẳn lên, không còn thâm sạm như trước. Sợ hết hàng nên phải tranh thủ đặt thêm 2 tuýp nữa để dành. Chị em nào còn phân vân thì chốt ngay kẻo hối hận!"
                },
                {
                    "name": "Minh Thư",
                    "location": "TP.HCM",
                    "rating": 5,
                    "content": "Siêu phẩm thực sự! Mình mua đợt sale vừa rồi, dùng được 2 tuần là thấy hiệu quả rõ rệt nhất là ở nách. Da mềm mịn hẳn. Nhóm bạn mình ai cũng đang săn lùng em này, may mà mình chốt sớm không là lại phải đợi đặt hàng lâu. Đáng đồng tiền bát gạo lắm ạ."
                }
            ]
        },
        "tier_variations": [
            {
                "name": "Khuyến mãi",
                "options": ["1 Tuýp 30g", "Combo 2 Tặng 1", "Combo 4 Tặng 2"]
            }
        ],
        "variants": [
            {
                "id": "var_virgin_white_1",
                "tier_index": [0],
                "sku": "4968123159004-1",
                "price": 600000,
                "stock": 100,
                "attributes": {
                    "combo_qty": 1,
                    "gifts": []
                }
            },
            {
                "id": "var_virgin_white_2",
                "tier_index": [1],
                "sku": "4968123159004-2",
                "price": 1200000,
                "stock": 100,
                "attributes": {
                    "combo_qty": 2,
                    "gifts": [{"name": "Tuýp Virgin White 30g", "qty": 1}]
                }
            },
            {
                "id": "var_virgin_white_3",
                "tier_index": [2],
                "sku": "4968123159004-3",
                "price": 2400000,
                "stock": 100,
                "attributes": {
                    "combo_qty": 4,
                    "gifts": [{"name": "Tuýp Virgin White 30g", "qty": 2}]
                }
            }
        ]
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
        },
        "is_ai_featured": True,
        "variants": [
            {
                "id": "var_hurry_harry_1",
                "tier_index": [0],
                "sku": "4968123159005-1",
                "price": 850000,
                "stock": 100,
                "attributes": {"combo_qty": 1, "gifts": []}
            }
        ]
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
        },
        "is_ai_featured": True
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
SUPPORT_KNOWLEDGE_DEFS = [
    {
        "category": "POLICY",
        "question": "Quy trình xử lý đơn hàng của Micsmo diễn ra như thế nào?",
        "answer": "Sau khi Sếp đặt hàng, AI sẽ tự động xác thực và chuyển sang kho đóng gói trong vòng 30 phút. Đơn hàng sẽ được giao hỏa tốc từ 1-3 ngày làm việc.",
        "priority": 10
    },
    {
        "category": "PRODUCT",
        "question": "Dòng Beppin Body Virgin White Serum có an toàn cho da nhạy cảm không?",
        "answer": "Dạ hoàn toàn an toàn thưa Sếp! Sản phẩm được chiết xuất từ 100% thảo mộc Nhật Bản, không chứa paraben hay hương liệu nhân tạo, đã qua kiểm định khắt khe.",
        "priority": 9
    },
    {
        "category": "SHIPPING",
        "question": "Micsmo có miễn phí vận chuyển không?",
        "answer": "Dạ có thưa Sếp! Mọi đơn hàng trên 500.000 VNĐ đều được hưởng chính sách 'Neural Express' - Miễn phí vận chuyển toàn quốc.",
        "priority": 8
    },
    {
        "category": "GENERAL",
        "question": "Làm thế nào để sử dụng tính năng Chẩn đoán AI?",
        "answer": "Sếp chỉ cần truy cập trang Chi tiết sản phẩm, nhấn vào nút 'Chẩn đoán ngay'. AI của chúng em sẽ phân tích sắc tố da và thiết lập phác đồ riêng cho Sếp.",
        "priority": 7
    }
]

# Banner & Visual Suite (Elite V2.2)
BANNER_DEFS = [
    {
        "id": "banner_viral_1",
        "title": "Sát Thủ Sắc Tố - Beppin Body",
        "image_url": "/uploads/img/banner/vn-11134258-81ztc-mm7801vsbw94c6@resize_w797_nl.webp",
        "link_url": "miccosmo-beppin-body-virgin-white-serum",
        "position": "home_main",
        "order_index": 1
    },
    {
        "id": "banner_viral_2",
        "title": "Micsmo Live - Phục Hồi Chuyên Sâu",
        "image_url": "/uploads/img/banner/vn-11134258-81ztc-mmiz6tc047peb7@resize_w797_nl.webp",
        "link_url": "miccosmo-white-label-premium-placenta-pack-130g",
        "position": "home_main",
        "order_index": 2
    },
    {
        "id": "banner_viral_3",
        "title": "Combo 2 Tặng 1 - Giới Hạn",
        "image_url": "/uploads/img/banner/sg-11134258-81zu3-mmr6osj4nb41df@resize_w797_nl.webp",
        "link_url": "miccosmo-beppin-body-virgin-white-serum",
        "position": "home_main",
        "order_index": 3
    }
]

# Strategic Vouchers (Elite V2.2)
VOUCHER_DEFS = [
    {
        "code": "ELITE2026",
        "title": "MÃ QUÀ TẶNG ELITE",
        "subtitle": "Giảm ngay 50k cho đơn hàng Viral đầu tiên",
        "type": "FIXED",
        "value": 50000,
        "min_spend": 500000,
        "is_global": True
    },
    {
        "code": "FREESHIP",
        "title": "FREE SHIPPING NEURAL",
        "subtitle": "Miễn phí vận chuyển mọi miền tổ quốc",
        "type": "PERCENTAGE",
        "value": 100,
        "is_global": True
    }
]

# System Settings (Elite V2.2)
SYSTEM_SETTINGS_DEF = {
    "basic_info": {
        "site_name": "Micsmo.com",
        "description": "Hệ thống bán hàng AI thế hệ mới 2026",
        "logo_desktop": None,
        "logo_mobile": None,
        "favicon": None
    },
    "contact_info": {
        "company_name": "HKD Văn Lập",
        "tax_id": "",
        "business_license": "",
        "phone": "094990112",
        "hotline": "0978785079",
        "email": "contact@micsmo.com",
        "address": "336/28/19 Nguyễn Văn Luông, Phú Lâm, HCM",
        "working_hours": "8:00 - 22:00"
    },
    "social_media": [
        {"platform": "Facebook", "url": "https://facebook.com/micsmo", "icon_url": None},
        {"platform": "Zalo", "url": "https://zalo.me/micsmo", "icon_url": None},
        {"platform": "TikTok", "url": "https://tiktok.com/@micsmo", "icon_url": None}
    ],
    "seo_analytics": {
        "meta_title": "Micsmo.com - Mua sắm thông minh cùng AI",
        "meta_keywords": "AI, shopping, smartshop, micsmo",
        "google_analytics_id": "G-XXXXXXXXXX",
        "facebook_pixel_id": "XXXXXXXXXXXXXXX"
    },
    "google_maps": {
        "map_iframe": "",
        "api_key": ""
    },
    "maintenance": {
        "is_enabled": False,
        "message": "Hệ thống đang bảo trì để nâng cấp Core AI. Vui lòng quay lại sau."
    }
}