/**
 * ELITE V2.2 - Global Shop Configuration!
 * This follows Rule R00: NO Hardcoded logic/data.
 */

export const SHOP_CONFIG = {
    pharmacy: {
        name: "Hệ Thống Phân Phối Chính Hãng",
        address: "Trung tâm Phân phối Toàn quốc",
        phone: "Hotline Hỗ trợ",
        zalo: "Zalo Official",
        license: "GPKD: Đang cập nhật | osmo"
    },
    shipping: {
        fixed_cost: 30000,
        free_threshold: 0 // In this funnel, we might have specific rules
    },
    trust_marks: [
        "GIAO HÀNG COD",
        "MIỄN PHÍ VẬN CHUYỂN",
        "Kiểm định lâm sàng",
        "Tiêu chuẩn Dược phẩm"
    ],
    default_features: [
        [
            "01 Tinh chất khử mùi Elite",
            "Hiệu quả tức thì lần đầu dùng",
            "-Miễn phí giao hàng toàn quốc" // '-' prefix for disabled/opacity
        ],
        [
            "+02 Tinh chất (Đủ liệu trình)", // '+' for bold
            "+Miễn phí vận chuyển (Freeship)",
            "Cam kết hoàn tiền ẩn danh",
            "Tặng kèm Voucher: 100k"
        ]
    ],
    checkout: {
        title: "THANH TOÁN AN TOÀN",
        trust_active: "Mã hóa Neural đang hoạt động",
        reservation_msg: "Giữ ưu đãi cho Quý khách trong:",
        reservation_time: 600, // 10 minutes
        labels: {
            phone: "Số điện thoại liên hệ",
            address: "Địa chỉ nhận hàng",
            summary: "CHI TIẾT ĐƠN HÀNG",
            total: "TỔNG THANH TOÁN",
            cta: "CHỐT ĐƠN NGAY",
            processing: "HỆ THỐNG ĐANG XỬ LÝ...",
            success_title: "ĐẶT HÀNG THÀNH CÔNG!",
            success_msg: "Đơn hàng đã được chuyển tới trung tâm hậu cần. Nhân viên hỗ trợ sẽ gọi tới Quý khách ngay!"
        },
        placeholders: {
            phone: "09xx xxx xxx",
            address: "Số nhà, tên đường, phường/xã..."
        },
        trust_badges: [
            { icon: "📦", label: "MIỄN PHÍ GIAO HÀNG", color: "text-blue-400" },
            { icon: "🛡️", label: "BẢO MẬT TUYỆT ĐỐI", color: "text-cyan-400" },
            { icon: "🚚", label: "THANH TOÁN KHI NHẬN", color: "text-emerald-400" }
        ]
    },
    default_badge_url: "/01.Badge_52ad415e46.webp"
};

export const OFFER_CONSTANTS = {
    timers: {
        default_seconds: 1800
    },
    labels: {
        activation: "Giai đoạn kích hoạt",
        full_treatment: "Liệu trình tối đa",
        expert_choice: "Chuyên gia khuyên dùng",
        scarcity: "Sắp cháy hàng",
        cta_start: "Bắt đầu trải nghiệm",
        cta_full: "Chọn liệu trình tự tin",
        voucher_viral_title: "Mã Giảm Giá Viral",
        voucher_used_label: "Lượt dùng",
        benefit_detail_title: "Chi tiết quyền lợi gói",
        sold_count_prefix: "Đã bán",
        expert_verify_label: "Bác sĩ da liễu khuyên dùng"
    }
};

export const PRIVACY_CONSTANTS = {
    title: "ĐẶC QUYỀN BẢO MẬT CAO CẤP",
    sub: "Cam kết đóng gói kín đáo & bảo mật quyền riêng tư cá nhân.",
    benefits: [
        "BẢO MẬT TÊN SẢN PHẨM",
        "KIỂM TRA HÀNG TRƯỚC NHẬN",
        "ĐÓNG GÓI KÍN ĐÁO 3 LỚP",
        "ĐỔI TRẢ 7 NGÀY"
    ]
};
