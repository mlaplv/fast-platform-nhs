# Viral Share-To-Unlock UI Stabilization

- [x] Analyze `ShareToUnlock.svelte` để tìm lý do box share biến mất sau khi chia sẻ.
- [x] Lần đầu: Xóa `&& step !== 'revealed'` khỏi wrapper ngoài (fix sai — tạo revealed card dead code).
- [x] Lần 2: Fix lại sang dạng sibling `{#if} {:else if}` — wrapper ngoài giữ `&& step !== 'revealed'`, revealed card là một nhánh riêng biệt ở ngoài `{:else if isEnabled && step === 'revealed' && voucherCode}`.
- [x] Apply cùng fix cho `ShareToUnlockPromoMobile.svelte`.
- [x] Wrap `{#key product.id}` tại tất cả các điểm mount: `LandingPage/Info`, `MainDetail/Info`, `ProductMobileMedia`, `MobileOffer`.
- [x] **Root Cause cuối cùng được xác nhận:** Template cũ có `{#if isEnabled && step !== 'revealed'}` bao ngoài `{:else if step === 'revealed'}` bên trong → dead code, hai điều kiện triệt tiêu nhau. Box share không hiện do inner revealed branch không thể đạt được. Fix: Tách revealed card ra thành nhánh `{:else if}` độc lập ở cấp wrapper.

# Storefront Hydration Error Stabilization for Admin Accounts
- [x] Phân tích Root Cause lỗi hydration (`root.svelte:44:41`) khi tài khoản có role ADMIN truy cập storefront.
- [x] Nhận diện nguyên nhân: Sự chênh lệch trạng thái phân quyền giữa Server-Side (khách vãng lai, `liveEditStore.isAdmin = false`) và Client-Side (đã giải mã token trước lúc hydrate, `liveEditStore.isAdmin = true`) kích hoạt nỗ lực mount Admin JIT components không đồng nhất.
- [x] Khai báo trạng thái `$state` rune `isMounted = false` trong `[slug]-funnel/+page.svelte`.
- [x] Phát hiện hiện tượng chạy đồng bộ của `isMounted = true` trong `onMount` vẫn có thể bị cuốn vào chu kỳ hydration gốc của Svelte 5.
- [x] Refactor sang cơ chế **Deferred Gate Guard (Trì hoãn bằng setTimeout 150ms)** để đẩy tác vụ render Admin HUD sang luồng event loop tiếp theo, khi Svelte đã hoàn thành 100% root hydration, đặt cờ `hydrating = false` và ổn định hoàn toàn cấu trúc DOM storefront.
- [x] Đăng ký hàm hủy `clearTimeout` tại sự kiện hủy component trong `onMount` (Resource Discipline).
- [x] Kiểm tra cú pháp và hoàn thành kiểm định.

# Viral Progress Bar Visual Upgrade & Optimization
- [x] Phân tích và nâng cấp hiệu ứng thẩm mỹ cho thanh tiến trình chia sẻ trong `ViralShareBarDesktop.svelte` (vệt sao chổi mờ dần + neon beacon).
- [x] Phân tích và nâng cấp hiệu ứng thẩm mỹ cho thanh tiến trình chia sẻ trong `ViralShareBarMobile.svelte` (vệt sao chổi mờ dần + neon beacon).
- [x] Phân tích và nâng cấp hiệu ứng thẩm mỹ cho thanh tiến trình chia sẻ trong `ViralFunnelLanding.svelte` (vệt sao chổi mờ dần + neon beacon).
- [x] Tự kiểm thức và chạy kiểm tra cú pháp biên dịch dự án.

# XOHI Auto Featured Ingredients Extraction Integration
- [x] Định nghĩa Pydantic schema `FeaturedIngredientItem` trong [backend/schemas/product.py](file:///home/lv/Desktop/fast-platform-core/backend/schemas/product.py).
- [x] Xây dựng logic AI Agent `suggest_ingredients_logic` trong [backend/services/commerce/logic/product_ai.py](file:///home/lv/Desktop/fast-platform-core/backend/services/commerce/logic/product_ai.py).
- [x] Tích hợp Service delegate `suggest_ingredients` trong [backend/services/commerce/product.py](file:///home/lv/Desktop/fast-platform-core/backend/services/commerce/product.py).
- [x] Khai báo API Endpoint `POST /api/v1/products/ingredients-suggest` trong [backend/controllers/product.py](file:///home/lv/Desktop/fast-platform-core/backend/controllers/product.py).
- [x] Phát triển hàm `handleAiSuggestIngredients` và thiết kế nút bấm **XOHI AUTO** trong [ProductFormMetadata.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductFormMetadata.svelte).
- [x] Kiểm thức syntax compile toàn bộ codebase thành công.

# XOHI Auto Specifications (Thông số kỹ thuật) Extraction Integration
- [x] Triển khai logic AI Agent `suggest_specs_logic` trong [backend/services/commerce/logic/product_ai.py](file:///home/lv/Desktop/fast-platform-core/backend/services/commerce/logic/product_ai.py).
- [x] Đăng ký Service delegate `suggest_specs` trong [backend/services/commerce/product.py](file:///home/lv/Desktop/fast-platform-core/backend/services/commerce/product.py).
- [x] Thiết lập POST route `/specs-suggest` trong [backend/controllers/product.py](file:///home/lv/Desktop/fast-platform-core/backend/controllers/product.py).
- [x] Tích hợp panel QUICK SPECS INPUT (XOHI Auto) và hàm `handleExtractSpecs` trong [ProductFormSpecs.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductFormSpecs.svelte).
- [x] Chạy biên dịch toàn bộ Python service & Svelte frontend thành công.

# Mobile Product Details Modal Visual Refinements
- [x] Sửa lỗi thiếu Header cho "Bảng thành phần" trong file [MobileProductDetailsModal.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/mobile/MobileProductDetailsModal.svelte).
- [x] Loại bỏ viền kép (double border) thừa dưới cùng của khung thông tin trong file [MobileProductDetailsModal.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/mobile/MobileProductDetailsModal.svelte).
- [x] Kiểm thức syntax compile toàn bộ codebase thành công.

# HeroBanner Visual Sizing & Spacing Refinements
- [x] Phân tích cấu trúc giao diện `HeroBanner.svelte` và CSS tương ứng trong `HeroBanner.css`.
- [x] Lập báo cáo chi tiết cách fix (propose plan) gửi Sếp duyệt trước khi triển khai.
- [x] Nâng cấp phụ đề trong `HeroBanner.css` (.hero-description): mở rộng `max-width` lên `82ch !important` (giảm tải chiều dọc), tăng font chữ lên `1.1rem !important` (Desktop), `1.02rem` (Tablet), `0.92rem` (Mobile) và áp dụng font `'Be Vietnam Pro'` với `font-weight: 400`.
- [x] Đảm bảo cấu trúc SEO thẻ `h1` bọc từ khóa không bị thay đổi và kế thừa hoàn hảo kích thước phụ đề mới.
- [x] Tinh chỉnh `.metrics-arc-container` trong `HeroBanner.css` bằng cách giảm `gap` từ `1.25rem` xuống `0.5rem`.
- [x] Giảm padding trên/dưới của `.hud-metric-segment` trong `HeroBanner.svelte` từ `pt-5 pb-5` xuống `pt-3 pb-3`.
- [x] Tự kiểm thức và kiểm tra biên dịch frontend thành công.

# Conditional Diagnostics Disclaimer SGE Stabilization (Bản 2.0)
- [x] Phân tích vị trí render Disclaimer y tế và Phác đồ điều trị trong `ClinicalQuiz.svelte` và `DiagnosticsSection.svelte`.
- [x] Lập kế hoạch chi tiết Bản 2.0 tích hợp Disclaimer y tế vào lòng kết quả và in hoa tiêu đề gửi Sếp duyệt.
- [x] Chuyển đổi tiêu đề chính thành chữ IN HOA **`PHÁC ĐỒ ĐIỀU TRỊ`** sử dụng class `uppercase` trong [ClinicalQuiz.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/client/ClinicalQuiz.svelte).
- [x] Nhúng trực tiếp dòng Disclaimer y tế *"AI có thể mắc sai sót. Vì vậy, hãy xác minh thông tin này với bác sĩ"* vào chính giữa nút CTA "Xem liệu trình" và "Làm lại chẩn đoán" của [ClinicalQuiz.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/client/ClinicalQuiz.svelte).
- [x] Dọn dẹp hoàn toàn Disclaimer cũ ở [DiagnosticsSection.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/client/slug/DiagnosticsSection.svelte) để tối ưu hóa trải nghiệm thị giác và tránh lặp chữ.
- [x] Khắc phục triệt để lỗi ép chữ thường do class `.sentence-case-target` trong [MobileDiagnostics.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/mobile/sections/MobileDiagnostics.svelte) bằng cách chuyển thành `uppercase` và in hoa cứng **`PHÁC ĐỒ ĐIỀU TRỊ`**.
- [x] Nhúng đồng bộ dòng Disclaimer y tế *"AI có thể mắc sai sót. Vì vậy, hãy xác minh thông tin này với bác sĩ"* vào chính giữa vùng điều khiển dưới nút CTA "Xem liệu trình" của [MobileDiagnostics.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/mobile/sections/MobileDiagnostics.svelte).
- [x] Khắc phục lỗi lowercase tiêu đề phụ bằng cách gỡ bỏ class `sentence-case-target` tại h4 "Phân tích chuyên sâu" trong [MobileDiagnostics.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/mobile/sections/MobileDiagnostics.svelte), khôi phục viết hoa chữ cái đầu.
- [x] Chuyển đổi text tĩnh "AI osmo 2026" thành dòng đếm lượt chẩn đoán động "đã chẩn đoán cho {lượt} người" trong [MobileDiagnostics.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/mobile/sections/MobileDiagnostics.svelte) để tạo độ tin cậy vượt trội.
- [x] Khắc phục lỗi lowercase nhãn hiệu lực góc phải bằng cách gỡ bỏ class `sentence-case-target` tại span "An toàn tuyệt đối" và "Hiệu lực" trong [MobileDiagnostics.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/mobile/sections/MobileDiagnostics.svelte), khôi phục viết hoa chữ cái đầu.
- [x] Khắc phục lỗi lowercase nút bấm CTA chính bằng cách gỡ bỏ class `sentence-case-target` ở span "Xem liệu trình" trong [MobileDiagnostics.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/mobile/sections/MobileDiagnostics.svelte), khôi phục viết hoa chữ cái đầu.
- [x] Chuẩn hóa viết hoa chữ cái đầu cho nhãn trạng thái hoạt động của chatbot Helen thành "Đang hoạt động" và "Chuyên viên trực" trên cả [SupportChatMobile.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/client/support/SupportChatMobile.svelte) và [SupportChatDesktop.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/client/support/SupportChatDesktop.svelte).
- [x] Tự kiểm thức và kiểm tra biên dịch thành công trên cả Desktop và Mobile.

# Storefront Product Detail Chi tiết Heading Color Synchronization
- [x] Phân tích và truy vết màu sắc `.prose-osmo h2, .prose-osmo h3` bị ghi đè màu sắc đậm (đen) lệch tông thị giác trên giao diện chi tiết.
- [x] Chuyển đổi màu sắc của h2/h3 thành màu xám dịu nhẹ (#6b7280 !important) và áp dụng Sentence Case (chỉ viết hoa ký tự đầu) tại [MainDetail/Desktop.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/Desktop.svelte) để hòa sắc hoàn hảo với văn bản thường.
- [x] Chuyển đổi màu sắc của h2/h3 thành màu xám dịu nhẹ (#6b7280 !important) và áp dụng Sentence Case (chỉ viết hoa ký tự đầu) tại [MainDetail/modules/Sections.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/modules/Sections.svelte) để giữ tính đồng nhất trên giao diện chi tiết chính.
- [x] Chuyển đổi màu sắc của h2/h3 thành màu xám dịu nhẹ (#6b7280 !important), áp dụng Sentence Case (chỉ viết hoa ký tự đầu), thu gọn line-height (1.3 !important) và margin-bottom để tối ưu khoảng cách dòng trên Mobile View tại [MainDetail/modules/ProductMobileSpecs.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/modules/ProductMobileSpecs.svelte).
- [x] Chuyển đổi màu sắc của h2/h3 thành màu xám dịu nhẹ (#6b7280 !important) và áp dụng Sentence Case (chỉ viết hoa ký tự đầu) tại [LandingPage/Desktop.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingPage/Desktop.svelte) cho view Landing Page Desktop.
- [x] Chuyển đổi màu sắc của h2 thành màu xám dịu nhẹ (#6b7280 !important) và áp dụng Sentence Case (chỉ viết hoa ký tự đầu) tại [LandingPage/modules/Description.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingPage/modules/Description.svelte) cho module Description Landing Page.
- [x] Chạy kiểm thức biên dịch dự án đảm bảo không phát sinh lỗi cú pháp nào.

# Bulk Select All & Discount Percent Upgrade (Elite V2.2)
- [x] Bổ sung `isAllSelected` derived state và truyền props vào ProductToolbar tại [ProductManagement.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductManagement.svelte).
- [x] Tích hợp nút SELECT_ALL sang trọng tại [ProductToolbar.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductToolbar.svelte).
- [x] Nâng cấp hàm `bulkDiscount()` thành form đa trường hỗ trợ 3 hình thức: Giảm theo %, Nhập giá trực tiếp, Xoá KM tại [ProductManagement.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductManagement.svelte).
- [x] Kiểm thức biên dịch frontend thành công (0 lỗi mới phát sinh từ các file đã sửa).

# Home Product Grid Dynamic Load More on Scroll & Button (Elite V2.2)
- [x] Phân tích `HomeProductGrid.svelte` và thiết kế giải pháp tải động sản phẩm.
- [x] Khai báo các trạng thái `$state` cho `visibleLimit`, `autoLoaded`, và `triggerEl` trong `HomeProductGrid.svelte`.
- [x] Tối ưu hóa `extendedCatalog` bằng cách chỉ tăng slice cho tab đang hoạt động để tiết kiệm RAM.
- [x] Dựng `IntersectionObserver` tự giải phóng tài nguyên ngay sau khi scroll load lần đầu.
- [x] Tích hợp phần tử trigger và bọc nút "Xem thêm" theo đúng logic: scroll load lần đầu, hiện nút từ lần 2.
- [x] Tự kiểm thức và kiểm tra biên dịch frontend thành công.

# Home Mobile Product Feed Dynamic Load More on Scroll & Button (Elite V2.2)
- [x] Phân tích `MobileProductFeed.svelte` và cấu hình giải pháp tải động.
- [x] Khai báo biến `$state` cho `visibleLimit`, `autoLoaded`, và `triggerEl` trên mobile.
- [x] Lọc động danh sách hiển thị `displayedProducts` bằng slice để tối ưu hóa bộ nhớ.
- [x] Tích hợp `IntersectionObserver` tự hủy ngầm ngay khi scroll-load lần đầu.
- [x] Thêm trigger element và nút "Xem thêm" sang trọng chân trang mobile.
- [x] Tự kiểm thức và kiểm tra biên dịch frontend thành công.

# Storefront Desktop Product Grid Sizing & Grid Wrapping Upgrade
- [x] Phân tích lý do các sản phẩm tải thêm bị ẩn sang rìa bên phải trên Desktop do layout hàng ngang trượt `flex overflow-x-auto`.
- [x] Cải tạo danh sách sản phẩm thành lưới dọc tự xuống dòng chuẩn `grid grid-cols-2 md:grid-cols-4 gap-4 pb-10`.
- [x] Tinh chỉnh chiều rộng thẻ sản phẩm từ phép tính cứng sang tự thích ứng `w-full`.
- [x] Loại bỏ toàn bộ event listener cuộn ngang không còn cần thiết.
- [x] Đồng bộ code biên dịch và nạp thành công 100% trên trang storefront.

# Admin AI Recommendations Filter (admin.osmo.vn)
- [x] Khai báo tham số truy vấn `featured_only: bool` trong endpoint `GET /api/v1/products` của `ProductController` tại [backend/controllers/product.py](file:///home/lv/Desktop/fast-platform-core/backend/controllers/product.py) và đẩy xuống ProductService.
- [x] Khai báo cờ trạng thái phản ứng `$state` rune `isAiFeaturedOnly` trong [ProductManagement.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductManagement.svelte).
- [x] Đăng ký Reactive Trigger trong `$effect` để tự động kích hoạt tải lại bảng sản phẩm khi check/uncheck bộ lọc AI.
- [x] Thiết kế nút bộ lọc **AI_RECOMMENDED** sang trọng với tông màu Cyan Neon `#00FFFF` và biểu tượng **Sparkles nhấp nháy** trong [ProductToolbar.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductToolbar.svelte).
- [x] Thực hiện biên dịch type-check thành công tuyệt đối (svelte-check exit code 0).

# Storefront Product Card Wide Layout & Compact Padding Refinement
- [x] Thu hẹp padding của vùng nội dung phía dưới hình ảnh từ `p-6` (24px) xuống còn `p-[5px]` (5px) trong [HomeProductGrid.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/home/HomeProductGrid.svelte) theo yêu cầu của Sếp.
- [x] Tinh chỉnh khoảng cách lề dưới của tiêu đề sản phẩm `h3` từ `mb-5` xuống còn `mb-2` để bố cục cân đối.
- [x] Gom gọn padding phần thông số/giá khuyến mại phía dưới: chuyển `pt-4` thành `pt-2`, và `space-y-3` thành `space-y-2`.
- [x] Đồng bộ kích thước font chữ và các tag nhãn (`CHÁY HÀNG`, giá bán) sang dạng thắt chặt, giúp nội dung sản phẩm trải rộng và hiển thị tối đa diện tích hữu ích trên cả Desktop & Tablet.
- [x] Chạy biên dịch svelte-check thành công tuyệt đối 100%.

# Storefront Homepage Flash Deal Card Compact Padding Refinement
- [x] Thu hẹp padding của toàn bộ thẻ sản phẩm Flashdeal `.deal-item` từ `padding: 1rem;` (16px) xuống còn **`padding: 5px;`** (5px) trong [HomeFlashDeal.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/home/HomeFlashDeal.svelte).
- [x] Gom gọn lề dưới của ảnh `.item-media` từ `margin-bottom: 1rem;` về **`margin-bottom: 0.5rem;`** (8px).
- [x] Điều chỉnh khoảng cách các thành phần chữ `.item-info` từ `gap: 0.75rem;` xuống **`gap: 0.4rem;`** (6px) và thêm khoảng lề đệm an toàn `padding: 0 0.15rem;`.
- [x] Rút nhỏ kích thước font chữ của giá tiền từ `text-2xl` (`1.4rem`) về **`text-xl`** (`1.25rem`) giúp hạn chế tối đa hiện tượng tràn chữ, xuống dòng ngoài ý muốn.
- [x] Thực hiện biên dịch svelte-check thành công tuyệt đối 100%.


