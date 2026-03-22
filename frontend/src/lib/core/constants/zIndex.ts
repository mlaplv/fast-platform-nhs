export const Z_INDEX = {
  BASE: 0,
  SURFACE: 10, // Lối tắt cho các thành phần nổi nhẹ trên nền
  LAYOUT_HEADER: 30,
  STICKY_HEADER: 100,
  SIDEBAR: 100,
  OVERLAY: 500, // Lớp làm mờ nền/VUI
  MODAL: 1000, // Nội dung Modal (Product, Revenue, etc.)
  HUD_DROPDOWN: 1050,
  HUD_FLOATING: 1060,
  HUD_SERVICE: 1100,
  POPOVER: 1100, // Tooltip, Dropdown
  OMNI_COMMAND: 1100,
  TOAST: 2000, // Thông báo khẩn cấp, Alert
  MEDIA_OVERLAY: 99999, // Lớp phủ Media Hub (Full Screen)
  SYSTEM: 100000, // Các thành phần hệ thống (Crash, Loading toàn trang)
} as const;
