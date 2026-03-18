# 📊 Báo Cáo Chuyên Gia: Tuân Thủ Z-Index (Elite V2.2)

Báo cáo này xác nhận tình trạng áp dụng quy tắc quản lý `z-index` tập trung trên toàn bộ hệ thống.

## 🟢 Đã Áp Dụng (100% Elite V2.2 Compliant)

Tất cả các thành phần giao diện đã được chuyển sang sử dụng hệ thống `Z_INDEX` tập trung. Không còn "magic numbers" nào tồn tại trong các file Svelte/CSS trọng yếu.

| Khu vực | File | Thành phần | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Cốt lõi** | [zIndex.ts](file:///Users/lv/Desktop/fast-platform-core/frontend/src/lib/core/constants/zIndex.ts) | Toàn hệ thống | Mở rộng thêm `SYSTEM`, `SURFACE` và `POPOVER`. |
| **VUI** | [VoiceModal.svelte](file:///Users/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/VoiceModal.svelte) | Voice Assistant | Sử dụng `Z_INDEX.OVERLAY` + [portal](file:///Users/lv/Desktop/fast-platform-core/frontend/src/lib/actions/portal.ts#1-31). |
| **Widgets** | [UniversalModal.svelte](file:///Users/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/ui/UniversalModal.svelte) | Biểu đồ & List | Sử dụng `Z_INDEX.MODAL`. |
| **Layout** | [+layout.svelte](file:///Users/lv/Desktop/fast-platform-core/frontend/src/routes/+layout.svelte) | Hệ thống Layer | Sử dụng `Z_INDEX.SYSTEM`. Tiêm CSS Variables. |
| **CSS** | [layout.css](file:///Users/lv/Desktop/fast-platform-core/frontend/src/routes/layout.css) | Global Styles | Sử dụng `var(--z-surface)` đồng bộ. |
| **Media** | [FileManager.svelte](file:///Users/lv/Desktop/fast-platform-core/frontend/src/lib/components/media/FileManager.svelte) | Library Manager | Sử dụng `Z_INDEX.POPOVER` & `SURFACE+50`. |
| **Media** | [MediaModal.svelte](file:///Users/lv/Desktop/fast-platform-core/frontend/src/lib/components/media/MediaModal.svelte) | Resource Viewer | Sử dụng `Z_INDEX.TOAST`. |
| **HUD** | [UserHud.svelte](file:///Users/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/hud/UserHud.svelte) | Admin Popup | Sử dụng `Z_INDEX.SURFACE + 40`. |
| **Chat** | [+page.svelte (Chat)](file:///Users/lv/Desktop/fast-platform-core/frontend/src/routes/chat/+page.svelte) | Command UI | Sử dụng `Z_INDEX.POPOVER`. |

---

## 🛠️ Giải pháp Kỹ thuật (Elite V2.2)

1.  **CSS Injection**: Đã tiêm `Z_INDEX` dưới dạng CSS Variables (`--z-modal`, `--z-overlay`, ...) vào `:root` thông qua [+layout.svelte](file:///Users/lv/Desktop/fast-platform-core/frontend/src/routes/+layout.svelte). Điều này cho phép các file [.css](file:///Users/lv/Desktop/fast-platform-core/frontend/src/routes/layout.css) thuần cũng có thể truy cập hệ thống hằng số mà không cần import JS.
2.  **Relative Positioning**: Sử dụng các phép toán trực tiếp như `style="z-index: {Z_INDEX.SYSTEM - 1}"` để quản lý các lớp phụ trợ liên quan mật thiết đến một cấp độ cụ thể.
3.  **Portal Decoupling**: Các thành phần nổi (VUI, Modals) đã được tách biệt khỏi stacking context cục bộ để tránh bị cắt (clipping) bởi `overflow: hidden`.

---

> [!TIP]
> **Quy tắc vàng 2026**: Khi thêm component mới, hãy luôn dùng `style="z-index: {Z_INDEX.LEVEL}"` thay vì class Tailwind `z-[...]`.
