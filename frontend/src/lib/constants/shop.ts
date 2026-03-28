/**
 * ELITE V2.2 - Global Shop Configuration thưa sếp!
 * This follows Rule R00: NO Hardcoded logic/data.
 */

export const SHOP_CONFIG = {
    pharmacy: {
        name: "Nhà Thuốc Hồng Sơn",
        address: "33 Ngô Thị Nhậm, Trung Sơn, Tam Điệp, Ninh Bình",
        phone: "097 878 5079",
        zalo: "Nhà thuốc Hồng Sơn",
        license: "GPKD: 09 B8 004018 | Ninh Bình | nhathuochongson.com"
    },
    shipping: {
        fixed_cost: 30000,
        free_threshold: 0 // In this funnel, we might have specific rules
    },
    trust_marks: [
        "COD TOÀN QUỐC",
        "FREE SHIPPING",
        "Clinical Labs VN",
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
        title: "CHECKOUT ELITE",
        trust_active: "Neural Encryption Active",
        reservation_msg: "Giữ ưu đãi cho Sếp trong:",
        reservation_time: 600, // 10 minutes
        labels: {
            phone: "Số điện thoại của Sếp",
            address: "Địa chỉ nhận hàng của Sếp",
            summary: "CHI TIẾT ĐƠN HÀNG",
            total: "TỔNG THANH TOÁN",
            cta: "CHỐT ĐƠN NGAY",
            processing: "NEURAL PROCESSING...",
            success_title: "SUCCESSFUL!",
            success_msg: "Đơn hàng đã được chuyển tới trung tâm hậu cần. Nhân viên hỗ trợ sẽ gọi tới Sếp ngay thưa sếp!"
        },
        placeholders: {
            phone: "09xx xxx xxx",
            address: "Số nhà, tên đường, khu vực sếp đang ở..."
        },
        trust_badges: [
            { icon: "📦", label: "FREE SHIPPING", color: "text-blue-400" },
            { icon: "🛡️", label: "ELITE PRIVACY", color: "text-cyan-400" },
            { icon: "🚚", label: "COD PAYMENT", color: "text-emerald-400" }
        ]
    }
};

export const OFFER_CONSTANTS = {
    timers: {
        default_seconds: 1800
    },
    labels: {
        activation: "Giai đoạn kích hoạt",
        full_treatment: "Phác đồ tối đa",
        expert_choice: "Chuyên gia khuyên dùng",
        scarcity: "Sắp cháy hàng",
        cta_start: "Bắt đầu trải nghiệm",
        cta_full: "Chọn phác đồ tự tin"
    }
};
