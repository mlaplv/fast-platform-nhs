# SSOT Seed Data (V72.0)
GEMINI_KEYS = [
    "AIzaSyCmplBB4YGaQRUF0dDm_C_10JEf-Ih2T3Y",
    "AIzaSyBUDTtODvWg1vUL2gjsHM8UDBU9228r8ew",
    "AIzaSyAsl3t1zInuOo8tskrz1_FzO9o8GOPrk4A",
    "AIzaSyAdWxvdliDJCdRTRc3wDjPqMbBuQWTpRmI",
    "AIzaSyBUwokbBFhIcaZR9PQ0mlb7W9awGN0odsk",
    "AIzaSyAMEVZrNziQi1zPINg09iURV5LEtqcI7bo",
    "AIzaSyBYYrrjd61yL98W61owDVbkH6MCchXLHj8"
]

CATEGORY_DEFS = [
    {"name": "Thuốc đông y", "slug": "thuoc-dong-y", "id": "cat_thuoc_dong_y"},
]

SUB_CATEGORY_DEFS = []

PRODUCT_DEFS = [
    {
        "id": "prod_hoi_nach_hong_son",
        "name": "Thuốc Đặc Trị Hôi Nách Hồng Sơn",
        "slug": "thuoc-dac-tri-hoi-nach-hong-son",
        "sku": "HS-HN-BASE",
        "price": 299000, # Base price
        "discount_price": 249000,
        "short_description": "Sáng mai, cầm lọ tinh chất trên tay, hãy lắc nhẹ 2 nhịp. Một làn sương mát lạnh chạm vào da, khô tắp lự sau 3 giây. Giờ thì... thoải mái diện chiếc sơ mi trắng yêu thích và tự tin bước ra cửa.",
        "category_id": "cat_thuoc_dong_y",
        "description": "Thảo dược chữa trị hôi nách nặng mùi lâu năm, bị từ nhỏ (bẩm sinh), phụ nữ mang thai, sau sinh, tuổi dậy thì. Giúp giảm thâm & mồ hôi nách nhiều, se nhỏ lỗ chân lông, hiệu quả rõ rệt sau 1 liệu trình. Sản phẩm dạng xịt, thẩm thấu nhanh, không gây ố vàng áo và không kích ứng da.",
        "product_metadata": {
            "landing_type": "tiktok",
            "video_url": "/static/video/HN_TikTok.mp4",
            "quiz_questions": [
                {
                    "id": "q1",
                    "title": "Mức độ mùi cơ thể?",
                    "subtitle": "Hãy chọn mức độ biểu hiện gần nhất với bạn",
                    "options": [
                        {"label": "NHẸ (THOẢNG QUA)", "value": "light", "icon": "😊"},
                        {"label": "TRUNG BÌNH (RÕ RỆT)", "value": "medium", "icon": "😐"},
                        {"label": "NẶNG (LÂU NĂM)", "value": "heavy", "icon": "😰"}
                    ]
                },
                {
                    "id": "q2",
                    "title": "Thời gian bị tình trạng này?",
                    "subtitle": "Thông tin này giúp AI tính toán liều lượng",
                    "options": [
                        {"label": "DƯỚI 1 NĂM", "value": "recent", "icon": "🕒"},
                        {"label": "TRÊN 1 NĂM", "value": "chronic", "icon": "📅"},
                        {"label": "BẨM SINH", "value": "genetic", "icon": "🧬"}
                    ]
                },
                {
                    "id": "q3",
                    "title": "Trải nghiệm trước đó?",
                    "subtitle": "Bạn đã từng thử các phương pháp khác chưa?",
                    "options": [
                        {"label": "CHƯA TỪNG DÙNG", "value": "none", "icon": "🆕"},
                        {"label": "DÙNG NHƯNG KHÔNG ĐỠ", "value": "failed", "icon": "❌"}
                    ]
                }
            ],
            "science_mechanism_image": "/uploads/2026/04/81a1dedc-cc87-457b-8fc5-a8037ae76921.webp",
            "science_mechanism_label": "QUY TRÌNH // PHÒNG NGỰ PHÂN TỬ",
            "science_claims": [
                {
                    "label": "PHỨC HỢP DƯỢC LIỆU SINH HỌC",
                    "content": "Vô hiệu hóa quá trình phân hủy axit béo của vi khuẩn, sát trùng triệt để và ngăn chặn mùi hôi ngay từ gốc.",
                    "image": "/uploads/2026/04/7e019c82-cc72-4e43-8753-54e85a3c6e90.webp"
                },
                {
                    "label": "AN TOÀN // LÀNH TÍNH",
                    "content": "100% thảo dược tự nhiên, cam kết không thâm nách, không ố vàng áo, an toàn cho cả mẹ bầu và trẻ nhỏ."
                }
            ],
            "science_stats": {
                "value": "72",
                "unit": "H",
                "label": "KHÔ THOÁNG TUYỆT ĐỐI",
                "description": "Ức chế Acetylcholine để điều tiết tuyến mồ hôi chủ động. Sạch mùi, tự tin suốt 3 ngày dài."
            },
            "science_guarantee": {
                "icon": "💎",
                "label": "BẢO CHỨNG",
                "description": "Hoàn 100% trong 3 ngày. <br/> <span class=\"text-cyan-400 font-bold tracking-widest\">KHÔNG CẦN TRẢ VỎ</span>."
            },
            "reviews_headline": "99.8% Tìm lại sự tự do. <br/> <span class=\"text-emerald-400 font-black italic\">KHÔNG CÒN NHỮNG KHOẢNG CÁCH NGẬP NGỪNG.</span>",
            "reviews_trust_score": "4.9/5",
            "reviews_count_text": "2,140+ LƯỢT MUA",
            "reviews": [
                {
                    "id": 1,
                    "name": "T.M. (090882) - TP.HCM*",
                    "phone": "090****882",
                    "location": "TP. Hồ Chí Minh",
                    "rating": 5,
                    "content": "Ám ảnh 5 năm không dám mặc sơ mi trắng vì ố vàng và ướt sũng. Hôm qua thử xịt đúng 1 lần buổi sáng, lúc lắc nhẹ thấy sương rất mịn mát. Đi làm cả ngày trời 40 độ mà tối về nách áo vẫn khô ron, không một mùi lạ. Thực sự là chân ái!",
                    "initial": "T"
                },
                {
                    "id": 2,
                    "name": "P.T. (093441) - Đà Nẵng*",
                    "phone": "093****441",
                    "location": "Đà Nẵng",
                    "rating": 5,
                    "content": "Cơ địa nội tiết mình ra mồ hôi như tắm, dùng đủ loại lăn ngoại nhập đều bó tay. Bác sĩ da liễu khuyên dùng thử cái này vì cơ chế kép. Khó tin thật, 2 ngày chưa tắm lại mà vẫn không hề có mùi bục ra. Đáng từng xu.",
                    "initial": "P"
                },
                {
                    "id": 3,
                    "name": "H.A. (091215) - Hà Nội*",
                    "phone": "091****215",
                    "location": "Hà Nội",
                    "rating": 5,
                    "content": "Mình ngại nhất khoản đi nhận hàng. Nhưng shop đóng hộp trơn bọc kín bưng, che tên sản phẩm hoàn toàn. Bạn shipper giao đến chỉ bảo 'có gói mỹ phẩm'. 10 điểm cho sự tế nhị và bảo mật thông tin.",
                    "initial": "H"
                }
            ],
            "active_deals": [
                {
                    "id": "deal_m2t1",
                    "label": "Mua 2 Tặng 1",
                    "buy_qty": 2,
                    "get_qty": 1,
                    "fixed_price": 498000,
                    "description": "Tiết kiệm 249k"
                },
                {
                    "id": "deal_m4t2",
                    "label": "Mua 4 Tặng 2",
                    "buy_qty": 4,
                    "get_qty": 2,
                    "fixed_price": 996000,
                    "description": "Tiết kiệm 498k - Phác đồ Nặng"
                }
            ]
        },
        "images": [
            "/uploads/2026/04/81a1dedc-cc87-457b-8fc5-a8037ae76921.webp",
            "/uploads/2026/04/d880a1f5-1be1-4a6a-9542-c705f0b1890a.webp",
            "/uploads/2026/04/7e019c82-cc72-4e43-8753-54e85a3c6e90.webp"
        ],
        "tier_variations": [
            {
                "name": "Loại thuốc",
                "options": ["Thường", "Đậm đặc", "Hôi chân"],
                "images": [
                    "/uploads/2026/04/81a1dedc-cc87-457b-8fc5-a8037ae76921.webp",
                    "/uploads/2026/04/d880a1f5-1be1-4a6a-9542-c705f0b1890a.webp",
                    "/uploads/2026/04/7e019c82-cc72-4e43-8753-54e85a3c6e90.webp"
                ]
            }
        ],
        "variants": [
            {
                "id": "var_hn_thuong",
                "tier_index": [0],
                "sku": "HS-HN-20ML-REG",
                "price": 299000,
                "discount_price": 249000,
                "stock": 100
            },
            {
                "id": "var_hn_dam_dac",
                "tier_index": [1],
                "sku": "HS-HN-20ML-CONC",
                "price": 320000,
                "discount_price": 290000,
                "stock": 50
            },
            {
                "id": "var_hn_hc",
                "tier_index": [2],
                "sku": "HS-HN-20ML-CONCC",
                "price": 320000,
                "discount_price": 289000,
                "stock": 50
            }
        ]
    }
]

PRODUCT_NAMES = ["Thuốc Đặc Trị Hôi Nách Hồng Sơn"]

ARTICLE_TITLES = [
    "Cách chữa hôi nách vĩnh viễn tại nhà",
    "Review thuốc trị hôi nách Hồng Sơn",
    "Nguyên nhân gây mùi cơ thể và cách khắc phục",
]
