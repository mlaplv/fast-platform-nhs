export const CAMPAIGN_STATUS_MAP: Record<
  string,
  { label: string; color: string; border: string }
> = {
  PENDING: {
    label: "CHỜ KHỞI TẠO",
    color: "text-[#FFB800]",
    border: "border-[#FFB800]",
  },
  PROCESSING: {
    label: "ĐANG XỬ LÝ AI",
    color: "text-[#00FFFF]",
    border: "border-[#00FFFF]",
  },
  WAITING_FOR_REVIEW: {
    label: "CHỜ DUYỆT NỘI DUNG",
    color: "text-[#8A2BE2]", // Purple for review emphasis
    border: "border-[#8A2BE2]",
  },
  COMPLETED: {
    label: "HOÀN TẤT & ĐĂNG TẢI",
    color: "text-[#39FF14]",
    border: "border-[#39FF14]",
  },
  FAILED: {
    label: "LỖI HỆ THỐNG",
    color: "text-[#FF3333]",
    border: "border-[#FF3333]",
  },
  REJECTED: {
    label: "ĐÃ HỦY/TỪ CHỐI",
    color: "text-gray-500",
    border: "border-gray-500",
  },
};

export const CAMPAIGN_CATEGORY_MAP: Record<
  string,
  { label: string; icon?: any }
> = {
  all: { label: "TẤT CẢ" },
  CREATIVE_CONTENT: { label: "SÁNG TẠO NỘI DUNG" },
  AD_MANAGEMENT: { label: "QUẢN TRỊ QUẢNG CÁO" },
};
