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
        "category_id": "cat_thuoc_dong_y",
        "description": "Thảo dược chữa trị hôi nách nặng mùi lâu năm, bị từ nhỏ (bẩm sinh), phụ nữ mang thai, sau sinh, tuổi dậy thì. Giúp giảm thâm & mồ hôi nách nhiều, se nhỏ lỗ chân lông, hiệu quả rõ rệt sau 1 liệu trình. Sản phẩm dạng xịt, thẩm thấu nhanh, không gây ố vàng áo và không kích ứng da.",
        "images": [
            "https://nhathuochongson.com/uploads/images/products/thuoc-dac-tri-hoi-nach-hong-son-lo-lon-20ml.jpeg",
            "https://nhathuochongson.com/uploads/images/products/thuoc-tri-hoi-nach-hong-son-dam-dac.gif",
            "https://nhathuochongson.com/uploads/images/products/thuoc-tri-hoi-nach-hoi-chan-hong-sonlo-lon-20ml.jpg"
        ],
        "tier_variations": [
            {
                "name": "Loại thuốc",
                "options": ["Thường", "Đậm đặc"],
                "images": [
                    "https://nhathuochongson.com/uploads/images/products/thuoc-dac-tri-hoi-nach-hong-son-lo-lon-20ml.jpeg",
                    "https://nhathuochongson.com/uploads/images/products/thuoc-tri-hoi-nach-hong-son-dam-dac.gif"
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
                "discount_price": 280000,
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
