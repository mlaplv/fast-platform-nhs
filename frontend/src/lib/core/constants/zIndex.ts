export const Z_INDEX = {
  BASE: 0,
  SURFACE: 10, // Lối tắt cho các thành phần nổi nhẹ trên nền
  STICKY_HEADER: 100,
  OVERLAY: 500, // Lớp làm mờ nền/VUI
  MODAL: 1000, // Nội dung Modal (Product, Revenue, etc.)
  POPOVER: 1100, // Tooltip, Dropdown
  TOAST: 2000, // Thông báo khẩn cấp, Alert
  SYSTEM: 100000, // Các thành phần hệ thống (Crash, Loading toàn trang)
} as const;
