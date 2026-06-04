# Task: Tối ưu hóa Accessibility, Viewport và Triệt tiêu Cảnh báo Font/API Lỗi thời (Zero-Font & Safe-A11y)

## Objectives
1. **Chuẩn hóa Typography các Section (Diagnostics, ScienceBento, OfferGrid):**
   - Loại bỏ các CSS local ghi đè font-weight hoặc font-family cưỡng ép.
   - Sử dụng class Tailwind `font-normal` để subtitle của các section đồng bộ hoàn toàn với `VerifiedReviews.svelte` (không bị in đậm, hiển thị rõ ràng, mượt mà).
2. **Sửa lỗi Accessibility Viewport trùng lặp:**
   - Xóa bỏ thẻ `<meta name="viewport" ...>` bị trùng lặp ở `src/routes/+layout.svelte` vốn đang chặn zoom của người dùng (`maximum-scale=1, user-scalable=0`).
   - Đảm bảo thẻ viewport chuẩn WCAG ở `app.html` có hiệu lực duy nhất.
3. **Cấm tải ngoài hoàn toàn và Triệt tiêu Cảnh báo API:**
   - Cập nhật `Permissions-Policy` trong `Caddyfile` để chặn hoàn toàn `attribution-reporting=()`.
   - Triệt tiêu cảnh báo API deprecated `navigator.plugins`: Thay thế việc đọc API cũ `navigator.plugins.length` bằng giá trị tĩnh an toàn `5` trong `+layout.svelte` nhằm xóa bỏ cảnh báo Chrome deprecation trong tệp bundle JS client.
4. **[MỚI] Triệt tiêu Forced Reflow và Nghẽn Main Thread:**
   - Bọc toàn bộ các tác vụ đọc kích thước hình học DOM của hàm `sendTelemetry` trong `requestAnimationFrame` tại `+layout.svelte` để tránh cưỡng ép tính toán layout (Forced Reflow) khi tải trang.
   - Khôi phục CSP của Google Fonts trong `Caddyfile` để tránh lỗi CSP liên tục khi Google Tag Manager cố chèn font (nguyên nhân chính khiến TBT tăng vọt lên 1,620ms do trình duyệt bận xử lý block thread).
5. **Triệt tiêu tận gốc cảnh báo API AttributionReporting:**
   - Vô hiệu hóa nhận diện API trên `Request.prototype` và các phần tử HTML trên client (`HTMLAnchorElement`, `HTMLImageElement`, `HTMLScriptElement`, `HTMLAreaElement`) để các script GTM/Google Ads tự động bỏ qua.

## Checklist
- [x] Cập nhật `DiagnosticsSection.svelte` (đổi subtitle class, xóa CSS local `:global(.diagnostics-subtitle-text)`)
- [x] Cập nhật `ScienceBento.svelte` (thêm `font-normal` vào subtitle, xóa CSS local `:global(.science-section .section-description)`)
- [x] Cập nhật `OfferGrid.svelte` (thêm `font-normal` vào subtitle, xóa CSS local `:global(.offer-section .section-description)`)
- [x] Cập nhật `src/routes/+layout.svelte` (xóa thẻ `<meta name="viewport">` và `<meta charset="utf-8">` trùng lặp trong `<svelte:head>`)
- [x] Sửa lỗi API deprecated `navigator.plugins.length` thành giá trị tĩnh `5` trong `+layout.svelte`
- [x] Triệt tiêu Forced Reflow bằng cách bọc code đo đạc trong `requestAnimationFrame` ở `+layout.svelte`
- [x] Khôi phục Google Fonts trong CSP ở `Caddyfile` nhằm loại bỏ lỗi nghẽn block thread (TBT) từ GTM
- [x] Triệt tiêu tận gốc cảnh báo `AttributionReporting` bằng cách vô hiệu hóa nhận diện API trên Request/HTML Prototypes, chặn setAttribute, và loại bỏ khỏi fetch/Request options trong `app.html`
- [x] Triệt tiêu Forced Reflow của Carousel bằng cách dùng `bind:clientWidth` và bọc `scrollTo` trong `requestAnimationFrame` (`ProductMobileOverview.svelte` & `ProductMobileMedia.svelte`)
- [x] Triệt tiêu Forced Reflow trong phễu chi tiết di động (`MobileProductDetailsModal.svelte` & `vouchers-list`)
- [x] Triệt tiêu Forced Reflow `handleScroll()` trong `MobileProductDetailsModal.svelte` — bọc rAF + throttle
- [x] Triệt tiêu Forced Reflow `scrollHeight` trong `ProductMobileSpecs.svelte` — hoãn đọc bằng rAF
- [x] Triệt tiêu Forced Reflow `scrollHeight` trong `ViralFunnelLanding.svelte:verify()` — đọc an toàn
- [x] Giải quyết LCP Discovery: Thêm SSR-visible hero `<img>` vào `[slug]/+page.svelte` với `fetchpriority="high"` và z-index trên skeleton
- [x] Thực hiện kiểm tra cục bộ (`pnpm build`) để đảm bảo không lỗi biên dịch
- [x] Deploy lên VPS và chạy `/opt/fast-platform/xohi.sh clean` để dọn sạch cache

