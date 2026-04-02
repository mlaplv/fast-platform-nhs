# CNS V77: Semantic Intent Anchors & Action Mappings
INTENT_TO_ACTION = {
    "revenue_query": {"intent_type": "DATA_QUERY", "target": "revenue", "action": "COUNT", "message": "Dạ sếp, đây là biểu đồ doanh thu ạ."},
    "order_query": {"intent_type": "DATA_QUERY", "target": "order", "action": "COUNT", "message": "Dạ, em đang thống kê đơn hàng cho sếp."},
    "product_query": {"intent_type": "DATA_QUERY", "target": "product", "action": "COUNT", "message": "Dạ, đây là tình hình kho hàng và sản phẩm ạ."},
    "news_create": {"intent_type": "CONTENT_CREATE", "target": "news", "action": "CONTENT_CREATE", "ui_action": "show_content_factory", "message": "Dạ sếp, em bắt đầu lên ý tưởng bài viết ngay đây."},
    "ui_navigation": {"intent_type": "UI_NAV", "target": "none", "action": "READ", "message": "Dạ, em chuyển trang cho sếp đây ạ."},
    "session_sleep": {"intent_type": "SESSION_CTRL", "target": "none", "action": "HARDWARE_SLEEP", "category": "SESSION_CTRL", "message": "Hẹn gặp lại sếp ạ."},
    "session_wake": {"intent_type": "SESSION_CTRL", "target": "none", "action": "WAKE_ROUTINE", "category": "SESSION_CTRL", "message": "Dạ, em nghe đây sếp."},
    "learn_command": {"intent_type": "LEARN_COMMAND", "target": "none", "action": "MUTATE", "message": ""}
}

SEMANTIC_ANCHORS = {
    "revenue_query": ["doanh thu hôm nay", "báo cáo tài chính", "tiền về bao nhiêu", "doanh số", "biểu đồ tăng trưởng"],
    "order_query": ["có bao nhiêu đơn hàng", "kiểm tra đơn mới", "hóa đơn", "vận chuyển", "bill hôm nay"],
    "product_query": ["hàng trong kho", "sản phẩm bán chạy", "tồn kho", "danh sách sản phẩm"],
    "news_create": ["viết bài báo", "sáng tác nội dung", "tạo bài viết mới", "lên content", "viết bài facebook"],
    "ui_navigation": [
        "mở cài đặt", "vào trang chủ", "xem danh mục", "đi tới quản trị", "vào phần báo cáo", 
        "mở helen", "cấu hình hệ thống", "mở cấu hình", "mở lịch hẹn", "mở banner", 
        "mở đánh giá", "mở thư viện ảnh", "biểu đồ doanh thu", "quản lý đơn hàng",
        "quản lý sản phẩm", "quản lý người dùng", "quản lý tin tức"
    ],
    "session_sleep": ["cút đi", "ngủ đi", "tạm biệt", "hẹn gặp lại", "tắt máy"],
    "session_wake": ["xohi ơi", "dậy đi", "alo xohi", "nghe này", "làm việc"],
    "learn_command": ["học lệnh", "dạy em khi nói", "nhớ nhé sếp bảo", "dạy xohi học lệnh"]
}
