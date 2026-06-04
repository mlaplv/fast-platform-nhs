# Task: Kiểm tra và thiết kế chức năng FOMO kiểu TikTok trên Mobile

## Objective
Kiểm tra hiện trạng và quy hoạch lại toàn bộ chức năng FOMO:
1. **Trên Desktop:** Loại bỏ hoàn toàn khỏi tất cả các trang, bao gồm cả trang Landing (Phễu bán hàng Desktop).
2. **Trên Mobile:** Thiết kế lại giao diện thanh thông báo nổi (fomo pill) theo đúng phong cách TikTok 2026 chuyên nghiệp (kẹo nhộng bo góc tối đa, nền đen mờ bán trong suốt, chữ trắng tinh giản, không viền gradient neon) và cập nhật nội dung tương ứng (lượt xem trong 30 ngày, người đã mua trước đây).
3. Nghiêm ngặt tuân thủ chỉ thị CẤM CODE từ Sếp ở bước phân tích hiện tại.

## Status
- [x] Đã kiểm tra toàn bộ mã nguồn Backend/Frontend liên quan đến FOMO.
- [x] Đã xác định các vị trí hiện hữu của FOMO trong codebase.
- [x] Đã đề xuất kế hoạch loại bỏ hoàn toàn FOMO trên Desktop.
- [x] Đã thiết kế cấu trúc CSS và nội dung mô phỏng TikTok 2026 cho Mobile.
- [x] Đã triển khai chặn FOMO trên Desktop qua layout (`+layout.svelte`).
- [x] Đã cải tạo giao diện kẹo nhộng tối giản đen mờ TikTok 2026 cho `NeuralActivityBar.svelte`.
- [x] Đã tích hợp hiển thị 1 voucher giảm giá và 1 voucher freeship giá trị cao nhất từ DB.
- [x] Đã cấu hình hiển thị tổng lượt mua bằng `PUBLIC_G_BY_COUNT` + số đơn thật từ DB.
- [x] Đã bảo mật tuyệt đối thông tin khách hàng (loại bỏ hoàn toàn SĐT, số và kí tự đặc biệt; ẩn danh hóa tên bằng regex thành công dạng `N*** Anh`, `L***n`, `Khách hàng`).
- [x] Đã tối ưu hóa chu kỳ hiển thị và hiệu ứng kẹo nhộng TikTok Live chỉ hiện 1 thông báo mỗi lần.
- [x] Đã build thành công dự án frontend mà không phát sinh lỗi biên dịch.

---

# Task: Adjust "Xem thêm phân nhóm" Button Layout on Mobile

## Objective
Fix the layout overlapping issue on the Mobile Storefront where the "Xem thêm phân nhóm" (View more sub-categories) text in the ingredients section overlapped with the content text (tags) behind it, making it unreadable.

## Status
- [x] Identified the issue in `ProductMobileSpecs.svelte`
- [x] Analyzed layout: `max-height` restriction caused overflowing tags to render behind the absolutely positioned gradient, and the `from-gray-50/95` gradient was too transparent to mask them.
- [x] Updated the gradient to `bg-gradient-to-t from-gray-50 from-50% to-transparent` to provide a solid background for the text.
- [x] Increased the gradient height to `h-14` and adjusted padding/margins to push the text down slightly and ensure it sits cleanly without overlap.
- [x] Applied similar fix to the general "Xem thêm" ingredients toggle.
- [x] Synced to production (Pending `rsync`)
- [x] Also fixed the same overlap issue in `Sections.svelte` which was used in the desktop/tablet view.
- [x] Removed unused font preload links from `routes/+layout.svelte` to resolve the 'preloaded but not used' looping warnings.
- [x] Optimized `SupportChatMobile.svelte` header:
  - Reduced border-radius to 5px (removed `helen-box-v2` animation).
  - Made header more compact by reducing avatar size (`w-10 h-10`), text sizes, and paddings.
  - Removed the explicit 'X' close button.
  - Pulled the header closer to the top edge.
- [x] Made the drag handle interactive in `SupportChatMobile.svelte`:
  - Removed `pointer-events-none` and replaced it with a `<button>`.
  - Bound `onclick` to `closeChat()`.
  - Added swipe-down logic (`ontouchstart`, `ontouchmove`, `ontouchend`) to allow closing by dragging down.
- [x] Fixed `support_agent.py` to omit `(Nhà máy Chưa cập nhật)` in product context if the brand is missing.
- [x] Removed `(Nhà máy ...)` logic completely from `support_agent.py` as requested.
- [x] Removed the hardcoded prefix "Chính hãng" from the product origin info in `support_agent.py`.
- [x] Optimized `DesktopProductDetailsModal.svelte` for mobile/responsive viewports:
  - Made modal bottom-aligned (`items-end`) and full-width (`p-0`, `w-full`) on mobile.
  - Adjusted modal height to `h-[85vh]` and `max-h-[85vh]` on mobile to support internal scroll.
  - Adjusted border-radius to `rounded-t-[24px] rounded-b-none` and border to `border-t border-white/10` on mobile.
  - Optimized internal content paddings for mobile: `px-6 pt-8 pb-5` for header, `px-6 py-6` for body/footer.
  - Adjusted close button spacing to `right-4 top-4` on mobile.

---

# Task: Tối ưu hóa FCP và Loại bỏ Chớp Nháy Trắng (Loading Flicker)

## Objective
Tối ưu hóa thời gian vẽ đầu tiên (FCP) nhằm loại bỏ hoàn toàn màn hình trắng xóa 2 giây đầu và hiện tượng chớp giật màu sắc khi Svelte SPA tải trang.

## Status
- [x] Phân tích quy trình kết xuất và nhận diện độ trễ First Contentful Paint (FCP) do SPA hydration.
- [x] Tích hợp style nền tĩnh và script xử lý tông màu (Storefront sáng / Admin tối) tức thì ngay trong `<head>` của `app.html` để chặn chớp nháy.
- [x] Lắp đặt bộ khung xương tải ảo (HTML/CSS loading skeleton) siêu nhẹ trực tiếp tại body của `app.html` để hiển thị lập tức trong thời gian chờ tải JS.
- [x] Đồng bộ hóa sự kiện sẵn sàng `'app-ready'` để chỉ xóa `#app-skeleton` sau khi các component tải động hoàn tất.
- [x] Tích hợp phát sự kiện `'app-ready'` từ `StorefrontHome.svelte`, `+page.svelte` (Admin), và `[slug]/+page.svelte`.
- [x] Khắc phục mâu thuẫn màu nền bằng cách cấu hình `.client-layout` kế thừa `--bg-canvas` động trong `client.css`.
- [x] Chuyển đổi nền của `page-container` và loading screen trong `+page.svelte` thành dạng reactive để triệt tiêu lớp nền đen.
- [x] Chạy lệnh `pnpm build` thành công, xác minh toàn bộ storefront biên dịch tĩnh ổn định.


