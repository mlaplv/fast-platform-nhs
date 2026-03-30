export const ORDER_STATUS_MAP: Record<
  string,
  { label: string; color: string; border: string }
> = {
  pending: {
    label: "TIẾP NHẬN ĐƠN HÀNG",
    color: "text-[#FFB800]",
    border: "border-[#FFB800]",
  },
  packed: {
    label: "ĐÃ ĐÓNG GÓI BẢO MẬT",
    color: "text-[#00FFFF]",
    border: "border-[#00FFFF]",
  },
  shipping: {
    label: "ĐANG VẬN CHUYỂN",
    color: "text-[#39FF14]",
    border: "border-[#39FF14]",
  },
  delivered: {
    label: "GIAO THÀNH CÔNG",
    color: "text-[#39FF14]",
    border: "border-[#39FF14]",
  },
  cancelled: {
    label: "ĐÃ HUỶ",
    color: "text-[#FF3333]",
    border: "border-[#FF3333]",
  },
};

export const ORDER_TRANSITIONS: Record<string, string[]> = {
  pending: ["packed", "cancelled"],
  packed: ["shipping", "cancelled"],
  shipping: ["delivered"],
  delivered: [],
  cancelled: ["pending"], // Allow reopening
};
