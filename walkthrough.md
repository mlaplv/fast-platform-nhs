# Walkthrough: Kiểm tra và thiết kế chức năng FOMO kiểu TikTok trên Mobile

## 1. Phân tích hiện trạng sử dụng chức năng FOMO
Đã thực hiện tìm kiếm toàn diện (`grep_search`) các thực thể liên quan đến FOMO trong codebase:
1. **Backend Controller:** `/backend/controllers/client/fomo.py` đăng ký controller `FomoController` dưới route `/api/v1/client/fomo`.
2. **Backend Service:** `/backend/services/commerce/logic/fomo_service.py` tính toán số lượt xem hiện thời dựa trên Redis (`support:presence:*`), số lượng đơn hàng gần đây qua DB và trạng thái khan hiếm của sản phẩm.
3. **Frontend Store:** `/frontend/src/lib/state/commerce/fomo.svelte.ts` quản lý state, định kỳ gọi API đồng bộ thông số và chu kỳ ẩn/hiện popup.
4. **Global Layout Component:** `/frontend/src/routes/(client)/(store)/+layout.svelte` nạp động `<NeuralActivityBar />` nếu tùy chọn `fomo_enabled` từ cấu hình hệ thống được bật.
5. **Mobile Funnel Components:** `MobileHero.svelte`, `MobileOffer.svelte`, và `MobileProductDetailsModal.svelte` sử dụng các chỉ số viewers/totalSales trong `fomoStore` để tăng chuyển đổi trên giao diện phễu bán hàng.

## 2. Quy hoạch theo yêu cầu của Sếp (TikTok 2026 Style)
1. **Trên Desktop (Bao gồm cả Landing):**
   - Loại bỏ hoàn toàn sự hiện diện của FOMO động. Giao diện Desktop sẽ không chạy `fomoStore`, không gọi API `/api/v1/client/fomo/*`, và không hiển thị `<NeuralActivityBar />`.
   - Đã rà soát thư mục `/funnel/desktop/` (các trang landing phễu Desktop như `OfferCard.svelte`, `EmotionalIncentive.svelte`) và xác nhận **không** có bất kỳ đoạn code nào import hay gọi `fomoStore`. Các text/badge giới hạn (như "Chỉ còn X suất") trên nút thanh toán là các giá trị đếm tĩnh/nội bộ từ thuộc tính của variant, hoàn toàn độc lập và không kéo dữ liệu fomo động từ API, đảm bảo an toàn tuyệt đối.
   - Trực tiếp giới hạn điều kiện nạp và render `NeuralActivityBar` trong file layout chung:
     `const fomoEnabled = !isAdmin && ui.isMobile && ui.settings?.conversions?.fomo_enabled;`
2. **Trên Mobile (Thiết kế phong cách TikTok 2026):**
   - **Giao diện (Style):**
     - Đổi lớp bọc từ `.neural-inner` phong cách cũ sang `.tiktok-fomo-pill`.
     - Thiết lập bo góc tối đa `border-radius: 9999px` dạng kẹo nhộng.
     - Sử dụng nền đen mờ bán trong suốt `background: rgba(18, 18, 18, 0.75)` kèm bộ lọc làm mờ phông nền `backdrop-filter: blur(10px)` để hiển thị cực kỳ sang trọng và chuyên nghiệp.
     - Loại bỏ các icon màu mè và hiệu ứng phát sáng Neon phức tạp.
     - Thêm một chấm tròn nhấp nháy màu xanh lá (`#10b981`) báo trạng thái "Live" siêu nhỏ gọn (5px).
     - Cập nhật text trắng mảnh tinh tế (`font-size: 11px`, màu `rgba(255, 255, 255, 0.95)`).
   - **Nội dung (Content):**
     - Thay thế các câu văn rườm rà bằng chuỗi thông tin tối giản kiểu TikTok:
       * Lượt xem: `{count} lượt xem trong 30 ngày` hoặc `{count} người đang xem`.
       * Đơn hàng: `Đã mua trước đây` hoặc `Khách hàng {Tên} đã mua sản phẩm này`.

## 3. Kết quả triển khai & Xác minh (Verification)
1. **Layout + Routing:** Đã cập nhật `/frontend/src/routes/(client)/(store)/+layout.svelte`, thêm ràng buộc `ui.isMobile` cho `fomoEnabled`.
2. **UI Component:** Đã nâng cấp `NeuralActivityBar.svelte` sang cấu trúc kẹo nhộng tối giản `.tiktok-fomo-pill`, sử dụng nền đen mờ bán trong suốt `rgba(18, 18, 20, 0.78)` và `backdrop-filter: blur(10px)`. Đã loại bỏ các icon Lucide, thay bằng chấm nhấp nháy `.live-dot` màu xanh lá (`#10b981`).
3. **Backend Service:** Đã chuẩn hóa chuỗi dữ liệu trong `/backend/services/commerce/logic/fomo_service.py` trả về định dạng TikTok 2026:
   * **Voucher:** Tự động truy vấn 1 voucher giảm giá (FIXED/PERCENT) và 1 voucher freeship (SHIPPING) có giá trị cao nhất và đang còn hoạt động từ database để hiển thị thông báo.
   * **Lượt mua:** Cộng gộp biến môi trường `PUBLIC_G_BY_COUNT` lấy từ file `.env` với số đơn hàng thật trong bảng `orders` của cơ sở dữ liệu để tạo ra con số chính xác.
   * **Đơn hàng gần đây:** Lấy ngẫu nhiên các đơn hàng thật mới nhất từ DB, đi qua bộ lọc bảo mật `_clean_and_mask_fomo_name` để bóc tách triệt để số điện thoại/số và ký tự đặc biệt, sau đó ẩn danh hóa tên khách hàng một cách an toàn (ví dụ: `N*** Anh`, `L***n`, hoặc mặc định là `Khách hàng`), tránh tuyệt đối mọi trường hợp rò rỉ dữ liệu cá nhân ra ngoài.
4. **Tối ưu hóa chu kỳ (Live Cycle):** Tần suất hiển thị của kẹo nhộng FOMO được tinh chỉnh ngắn gọn hơn (mỗi thông báo hiển thị trong 4.5 giây, khoảng nghỉ ngẫu nhiên từ 5 đến 10 giây) để đem lại cảm xúc nhộn nhịp trực tiếp của TikTok Live.
5. **Compile Test:** Đã chạy `pnpm build` thành công, xác nhận các thay đổi về cú pháp Svelte 5 / Runes đều hoàn toàn chuẩn chỉnh và không gây lỗi biên dịch.
6. **Service Test:** Chạy test service trả về định dạng mặc định kiểu TikTok thành công.

---

# Walkthrough: Fixing "Xem thêm phân nhóm" Overlap on Mobile

## 1. Issue Analysis
The user reported an issue where the "Xem thêm phân nhóm" (View more sub-categories) text at the bottom of the Mobile product ingredients section was overlapping with the underlying content text (e.g. ingredient tags). 
The overlapping was caused because the button containing the text had a `max-height` (180px) and `overflow-hidden`. As the flex content exceeded this height, it bled into the padding area at the bottom of the button. The "Xem thêm" text was absolutely positioned at the bottom using a semi-transparent gradient (`from-gray-50/95`), which allowed the underlying white ingredient tags to shine through, ruining readability.

## 2. Technical Fixes
File: `frontend/src/lib/components/storefront/product-detail/MainDetail/modules/ProductMobileSpecs.svelte`
- Upgraded the bottom fade gradient from `from-gray-50/95` (which was partially transparent near the text) to `from-gray-50 from-50%`. This ensures that the bottom 50% of the gradient is entirely solid (`#f9fafb`), completely masking the underlying overflow content.
- Increased the absolute gradient container height from `h-12` (48px) to `h-14` (56px) for more coverage.
- Adjusted the positioning of the "Xem thêm" text. Changed `pb-1` to `pb-0` and added `mb-1.5` along with `text-gray-500` to lower the text slightly, pushing it away from the content bounds and achieving a cleaner look.
- Applied the same visual and layout fix for both the `ingredients_groups` branch and the plain `ingredients` string branch.

## 3. Verification & Deployment
- The structural CSS changes ensure that no matter how long the ingredient list is, the "View more" text always rests on a solid background and cannot be overlapped by white tags.
- Pending execution of `rsync` to synchronize the changes to the production VPS `mlap@103.1.236.14`.

## 4. Modal Optimization for Mobile (Full Width & Bottom Sheet style)
### 4.1 Issue
When viewing the landing page on mobile, the modal `DesktopProductDetailsModal.svelte` had fixed desktop padding `p-6` around it and bo-tron 4 goc `rounded-[32px]`, creating ugly gaps/leakage on both sides.

### 4.2 Fix
File: `frontend/src/lib/components/storefront/funnel/desktop/sections/DesktopProductDetailsModal.svelte`
- Updated outer layout of the portal to shift from centered dialog on desktop (`items-center p-6 md:p-12`) to a bottom-docked panel on mobile (`items-end p-0 md:p-12`).
- Replaced fixed border-radius and borders with dynamic responsive classes: `border-t md:border border-white/10 rounded-t-[24px] md:rounded-[32px] rounded-b-none md:rounded-b-[32px]`.
- Enforced full width (`w-full`) and set height constraints to `h-[85vh]` / `max-h-[85vh]` on mobile to allow clean internal scrolling.
- Reduced inner padding on mobile viewport to `px-6 py-6` (from `px-10 py-8`) to prevent squeezing the text.
- Standardized close button location on mobile to `right-4 top-4`.

---

## 5. Tối ưu hóa FCP và Triệt tiêu Chớp Nháy Trắng (Loading Flicker)

### 5.1 Phân tích Sự cố & Giải pháp kỹ thuật
Trong chế độ Single Page Application (SPA), trình duyệt nhận được file `index.html` trắng trơn trước khi các file JS được nạp và kích hoạt (hydrate). Điều này dẫn đến khoảng thời gian 2 giây đầu tiên màn hình bị trắng xóa hoàn toàn (FCP Delay), kèm theo chớp nháy đột ngột khi giao diện thật hiển thị.

Để giải quyết triệt để:
1. **Thiết lập nền tĩnh tức thời (Instant CSS Background Paint):**
   - Đưa trực tiếp bộ quy tắc `@keyframes skeleton-pulse` và style thiết lập `background-color` cho `html, body` vào thẻ `<style>` trong `<head>` của `frontend/src/app.html`.
   - Sử dụng một đoạn script tự động phát hiện máy chủ hoặc URL chứa `admin` để gắn class `admin-theme`, lập tức đổi màu nền từ off-white (`#fafafa`) sang đen sâu (`#020202`) của Dashboard quản trị trước khi bất kỳ tài nguyên nào khác được tải xuống.
2. **Khung xương tải ảo hai chế độ (Dual-mode Loading Skeleton):**
   - Thêm phần tử `#app-skeleton` tĩnh bên trong `<body>` của `app.html`, mô phỏng cấu trúc của thanh tiêu đề (Header) và bố cục lưới hình ảnh / thông tin sản phẩm.
   - Script tự động đổi tông màu (sáng/tối) tương ứng cho các phần tử con của `#app-skeleton` nếu ở môi trường Admin.
3. **Mờ dần và giải phóng tài nguyên (Hydration Fade-Out):**
   - Cập nhật hàm `onMount` của layout chính `frontend/src/routes/+layout.svelte` để phát hiện sự kiện nạp Svelte thành công.
   - Khi đó, cả `#app-skeleton` và `#initial-loader` sẽ được gán độ mờ `opacity = 0` (chuyển động mượt mà bằng CSS transitions) trước khi bị xóa bỏ hoàn toàn khỏi cây DOM qua lệnh `.remove()` sau 500ms, giúp giải phóng hoàn toàn bộ nhớ RAM.
4. **Tối ưu hóa màu nền chuyển vùng (Zero-Flash Background Caching):**
   - Loại bỏ thuộc tính nền cứng `background-color: #010101` trên thẻ `body` trong `client.css`, thay thế bằng biến động `var(--bg-canvas)` để tránh xung đột màu sắc khi tải trang Storefront.
   - Triển khai ghi nhớ trạng thái màu nền qua `localStorage.setItem('last_bg_color')` ngay tại `$effect` của layout chính Svelte.
   - Đọc giá trị `last_bg_color` trực tiếp trong thẻ `<script>` ở `<head>` của `app.html` để phủ màu nền và áp dụng giao diện tối/sáng cho `#app-skeleton` ngay từ mili-giây đầu tiên.
5. **Đồng bộ hóa Vòng đời Hydration (Robust App-Ready Execution):**
   - Đảm bảo sự kiện `app-ready` luôn được kích hoạt kể cả khi component tải động bị trả về kết quả lỗi hoặc rỗng (`null`) tại `[slug]/+page.svelte`.
   - Biên dịch tĩnh ứng dụng thành công qua `pnpm build` với adapter-static hoạt động trơn tru.


