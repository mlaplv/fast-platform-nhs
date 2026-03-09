export const ORDER_STATUS_MAP: Record<
  string,
  { label: string; color: string; border: string }
> = {
  pending: {
    label: "CHỜ XỬ LÝ",
    color: "text-[#FFB800]",
    border: "border-[#FFB800]",
  },
  paid: {
    label: "ĐÃ THANH TOÁN",
    color: "text-[#00FFFF]",
    border: "border-[#00FFFF]",
  },
  processing: {
    label: "ĐANG XỬ LÝ",
    color: "text-[#00FFFF]",
    border: "border-[#00FFFF]",
  },
  shipped: {
    label: "ĐANG GIAO",
    color: "text-[#39FF14]",
    border: "border-[#39FF14]",
  },
  completed: {
    label: "HOÀN THÀNH",
    color: "text-[#39FF14]",
    border: "border-[#39FF14]",
  },
  delivered: {
    label: "ĐÃ GIAO",
    color: "text-[#39FF14]",
    border: "border-[#39FF14]",
  },
  cancelled: {
    label: "ĐÃ HUỶ",
    color: "text-[#FF3333]",
    border: "border-[#FF3333]",
  },
};
