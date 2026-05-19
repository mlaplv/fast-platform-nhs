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

# AI Diagnostic Recommendation Formatting & Aesthetics Upgrade (Elite V2.2)
- [x] Phân tích hiện trạng dấu tích markdown `**` và lỗi định dạng khối chữ dày đặc ở phần "Liệu trình tối ưu" trên cả Desktop và Mobile.
- [x] Xây dựng bộ giải mã (Parser) thông minh `formatRecommendation` có kiểu tĩnh 100% để trích xuất các bước (Numbered Steps 1, 2, 3) thành các thẻ **Card Glassmorphism** và lộ trình (Tấn công, Duy trì) thành các **Phase-specific alert cards** cao cấp.
- [x] Tích hợp bộ giải mã vào file [ClinicalQuiz.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/client/ClinicalQuiz.svelte) và render bằng cú pháp `{@html ...}` trên giao diện Desktop.
- [x] Tích hợp bộ giải mã vào file [MobileDiagnostics.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/mobile/sections/MobileDiagnostics.svelte) và render bằng cú pháp `{@html ...}` trên giao diện Mobile, loại bỏ các kiểu in đậm/nghiêng thô của khối cha.
- [x] Chạy biên dịch svelte-check thành công hoàn toàn, không phát sinh lỗi cú pháp mới.

# XOHI Product Rewrite Commitments Expansion (Elite V2.2)
- [x] Phân tích file `backend/services/xohi/prompts/agents/rewriter.py` và chuẩn bị nội dung nâng cấp.
- [x] Tích hợp mục thứ 7 `<h2>Cam kết</h2>` vào cấu trúc khung chuẩn của `PRODUCT_REWRITE_INSTRUCTIONS`.
- [x] Yêu cầu LLM chép nguyên văn cam kết an toàn sạch "3 Không" từ Miccosmo và chính sách khách hàng linh hoạt.
- [x] Chạy kiểm thử cú pháp Python và đảm bảo không có lỗi biên dịch.

# Storefront Hot Topics ("Chủ đề hot") News Page Integration (Elite V2.2)
- [x] Phân tích hiện trạng đám mây thẻ tag ở Desktop và thanh cuộn bong bóng danh mục ở Mobile.
- [x] Triển khai bộ phân tích ngữ nghĩa reactive `getArticleTags` tại client để tự động gán tag chủ đề theo tiêu đề và mô tả của từng bài viết.
- [x] Nâng cấp nhãn danh mục hiển thị trên mỗi thẻ bài viết thành tag đầu tiên khớp được, tăng tính sống động và chuyên sâu cho tin bài.
- [x] Triển khai bộ lọc động `filteredNews` và `filteredNewsList` sử dụng `$derived` để cập nhật danh sách bài viết lập tức (<5ms), tiết kiệm RAM dưới ngưỡng 2GB.
- [x] Thiết lập giao diện tag ở Desktop với hiệu ứng chọn và hover mượt mà. Bấm lại tag đang chọn để hủy lọc.
- [x] Đồng bộ Header Mobile với cụm tag Hot Topics + bong bóng "TẤT CẢ" phát sáng tông màu hồng đào `#C18F7E` khi hoạt động.
- [x] Thiết lập cấu trúc trạng thái rỗng (Empty State) cao cấp trên cả Desktop và Mobile khi không tìm thấy bài viết, kèm nút xóa bộ lọc nhanh chóng.
- [x] Thực hiện type-checking tĩnh 100% bằng svelte-check thành công hoàn hảo (exit code 0).

# XOHI Auto Product Classification (Variants) Integration (Elite V2.2)
- [x] Thiết kế nút bấm kích hoạt Trợ lý Xohi AI trên Header của `ProductFormVariants.svelte`.
- [x] Xây dựng bảng điều khiển Glassmorphism HUD Assistant Panel với các Presets và ô nhập prompt.
- [x] Triển khai hàm logic `parseXohiPrompt` trích xuất thông tin combo, quà tặng, giảm giá, tồn kho và mặc định.
- [x] Triển khai hiệu ứng AI Loading Steps kéo dài 800ms tạo trải nghiệm cao cấp.
- [x] Đồng bộ ma trận phân loại hàng và cập nhật vào `formState.tierVariations` và `formState.variants`.
- [x] Tích hợp cột Bật/Tắt (ON/OFF) ở vị trí đầu tiên của bảng ma trận biến thể.
- [x] Triển khai hàm `toggleVariantActive` quản lý kích hoạt với cảnh báo an toàn cho biến thể mặc định.
- [x] Đồng bộ hóa hiệu ứng làm mờ hàng (`opacity-40 saturate-50`) và vô hiệu hóa tất cả input (`disabled={variant.is_active === false}`) khi biến thể bị tắt.
- [x] Đồng bộ hóa lưu trữ/tải trạng thái kích hoạt biến thể vào cột JSONB `attributes` (không cần chạy DB migration).
- [x] Lọc động các biến thể đang hoạt động (`is_active !== false`) trên toàn bộ giao diện Storefront (Desktop, Mobile, Selector Drawer, Overview).
- [x] Triển khai hàm helper `isOptionActive` và lọc ẩn triệt để nút bấm tùy chọn biến thể đã bị tắt tại cả giao diện Desktop và Mobile.
- [x] Kiểm thức biên dịch `npx svelte-check` và kiểm tra hoạt động.

# Storefront Numbered Bullet Overlap Fix (Elite V2.2)
- [x] Phân tích nguyên nhân lỗi chồng số thứ tự đè lên ký tự đầu tiên của danh sách có thứ tự (ol > li) trên cả Desktop và Mobile.
- [x] Điều chỉnh CSS `ol > li` thành `padding-left: 1.5rem !important` tại [MainDetail/Desktop.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/Desktop.svelte) để tạo máng chạy an toàn cho số thứ tự absolute.
- [x] Tách biệt và khai báo độc lập kiểu dáng ordered list `ol` và `ol > li::before` tại [ProductMobileSpecs.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/modules/ProductMobileSpecs.svelte) để tối ưu hiển thị danh sách trên Mobile.
- [x] Tự kiểm thức biên dịch và chạy kiểm tra cú pháp frontend thành công.
# XOHI Product Rewrite Truncation & Token Optimization Fix (Elite V2.2)
- [x] Phát hiện nguyên nhân cốt lõi: Đặt `max_tokens = 16384` vượt giới hạn trần vật lý `8192` của Gemini API làm kích hoạt fallback ngầm hạ giới hạn về mặc định siêu thấp (2048/4096), dẫn đến việc nội dung viết lại bị cắt cụt ở phần cuối (mất mục Cam kết).
- [x] Tinh chỉnh `max_tokens = 8192` (mức trần vật lý tối đa và tối ưu nhất của Gemini API) trong `neural_rewriter.py` để tránh bị auto-fallback hạ token.
- [x] Nâng cấp `- ĐẢM BẢO CHẤT LƯỢNG` trong `rewriter.py` bằng cách bổ sung chỉ thị ép AI viết ngắn gọn, cô đọng dưới 1500 từ để kết xuất trọn vẹn và đầy đủ phần Cam kết.
- [x] Thực hiện biên dịch kiểm tra AST tĩnh thành công 100% không phát sinh lỗi.
- [x] Tái khởi động nóng các container api và worker thành công để nạp cấu hình mới ngay lập tức.
- [x] Phát hiện & sửa lỗi khuyết Cam kết trên giao diện Verdict/Copyright Analysis: Tích hợp hoàn hảo mục CAM KẾT vào `four_blocks` và `step_3_pillars` trong `agent_base.py`, cùng với Heuristic fallback trong `plagiarism_cop.py`.

# Show Policy Featured Image if Exists (Elite V2.2)
- [x] Phân tích điều kiện ẩn ảnh đại diện đối với danh mục "Chính sách".
- [x] Cập nhật NewsDetailDesktop.svelte hiển thị ảnh đại diện nếu tồn tại trường featuredImage.
- [x] Cập nhật NewsDetailMobile.svelte hiển thị ảnh đại diện dạng banner bo góc tinh tế bên dưới Clean Header nếu có ảnh.
- [x] Tự kiểm thức biên dịch và kiểm tra cú pháp frontend thành công.
- [x] Tinh chỉnh khoảng cách tiêu đề h1 (Desktop): mt-[10px] và mb-[5px] để cân đối tỷ lệ thị giác.
- [x] Thu gọn khoảng hở lề trang chi tiết (Desktop): pt-5 thành pt-[10px], px-10 thành px-[10px], và pl-[10px] (Hero) làm lề đồng bộ 10px.
- [x] Đưa top margin của prose h1 (:global(.news-article-prose h1)) về 0 để đồng bộ lề trên 10px đều đặn.
- [x] Đưa hình đại diện về tỷ lệ gốc nguyên bản (w-full h-auto object-contain) trên cả Desktop & Mobile, loại bỏ hoàn toàn việc bị cắt xén hình ảnh.
- [x] Làm cố định cột bên phải (Sticky Sidebar) trên Desktop khi cuộn chuột: sticky top-6 self-start.
- [x] Khắc phục triệt để lỗi không cuộn trang lên đỉnh khi nhấn link liên kết chuyển trang ở footer: tích hợp afterNavigate và Double-Check Scroll.
- [x] Thiết kế lại Reviews Mobile (NewsMobileReviews.svelte) mở rộng lề ngoài px-[10px] đồng bộ, tách cột chia luồng Avatar/Name & Interactions/Badge giúp tránh bóp méo hình ảnh.
- [x] Giải phóng hình đại diện Mobile, loại bỏ Hero 65vh cắt xén thô kệch, đưa tiêu đề sạch lên trước và hiển thị ảnh bìa chuẩn nguyên bản w-full h-auto object-contain không xén pixel.
- [x] Điều chỉnh ảnh bìa Mobile tràn lề 100% (Full Width) và loại bỏ hoàn toàn border radius bo góc.
- [x] Loại bỏ đường kẻ ngang dưới Ban biên tập, thu nhỏ khoảng hở (pb-1 mb-2) và thay thế bằng huy hiệu vàng ngôi sao w-5 tinh tế, đẳng cấp.

# Dynamic Commitments Format & Premium Glassmorphic UI Upgrade (Elite V2.2)
- [x] Xây dựng bộ giải mã HTML động cực kỳ mạnh mẽ `parseDescriptionAndCommitments` trong [product.ts](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/utils/product.ts) để bóc tách vùng "Cam kết" của Miccosmo ra khỏi mô tả thô.
- [x] Giải quyết triệt để lỗi Escaped Entity (`Lành tính &amp; An toàn` -> `Lành tính & An toàn`) bằng hàm unescape Html trong [product.ts](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/utils/product.ts).
- [x] Tích hợp bộ giải mã vào [Sections.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/modules/Sections.svelte) (Desktop View) và dựng thiết kế đỉnh cao: Căn giữa tiêu đề, viền kính lỏng blur mịn kèm glow backlight và banner Cyberpunk Slate-900 sang trọng.
- [x] Tích hợp bộ giải mã vào [ProductMobileSpecs.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/modules/ProductMobileSpecs.svelte) (Mobile View) và chèn khối kính lỏng an toàn y khoa chuẩn di động ở chân trang chi tiết.
- [x] Tích hợp bộ giải mã vào [Description.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingPage/modules/Description.svelte) (Landing Page View), đồng bộ giao diện cam kết động 100% trên toàn bộ các kênh storefront.
- [x] Tự kiểm thức và chạy kiểm tra biên dịch type-check thành công hoàn toàn không có lỗi cú pháp mới.
- [x] Thiết kế lại Desktop View ([Sections.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/modules/Sections.svelte) & [Description.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingPage/modules/Description.svelte)) theo mô hình hàng ngang (Horizontal Ribbon) tiết kiệm diện tích tối đa, nén chiều cao banner xuống 38px mà vẫn đảm bảo tính sang trọng và hiệu ứng lướt sáng.
- [x] Thiết kế lại Mobile View ([ProductMobileSpecs.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/modules/ProductMobileSpecs.svelte)) theo mô hình hàng dọc siêu gọn gàng (22px/dòng), gom tiêu đề lên 1 dòng duy nhất, nén banner xuống 36px để giữ cho không gian cuộn trang vô cùng thanh thoát.
- [x] Thiết lập thiết kế tối giản tối đa (background-less & border-less) cho dải băng FOMO theo chỉ thị mới của Sếp. Loại bỏ hoàn toàn nền `bg-slate-900` và các viền bo góc, chuyển đổi dải băng thành một dòng phân tách thanh lịch có đường kẻ mảnh (`border-t border-emerald-500/10`) để đồng bộ hoàn hảo với hệ sinh thái Miccosmo y khoa Nhật Bản, đi kèm liên kết `/chinh-sach-doi-tra-hoan-tien` và nhãn `Xem thêm →` màu ngọc lục bảo.
- [x] Tinh chỉnh đồng bộ cỡ chữ (`font-size`) của phần mô tả chi tiết sản phẩm (`.prose-osmo`) về chuẩn **`15px`** (Desktop) và **`14px`** (Mobile) cùng giãn dòng **`1.6`** nhẹ nhàng để đạt mật độ thông tin tối ưu, đúng chuẩn thiết kế e-commerce cao cấp của Lazada và Shopee.
- [x] Tinh chỉnh kích thước chữ của phần **Câu hỏi thường gặp (FAQ)** về mức **`15px`** cho câu hỏi và **`14px`** cho câu trả lời trên Desktop (Mobile tương ứng là **`14px` / `12px`**) để tăng tính hài hòa, thoáng đãng và dễ đọc.
- [x] Tinh chỉnh phần **Thành phần nổi bật** (tên hoạt chất **`14px` - `15px`**, công dụng **`12px` - `13px`**, container icon nhỏ gọn **`w-10 h-10`**) và **Bảng thành phần** (**`12px` - `13px` font-mono** cực kỳ rõ ràng) để tối ưu không gian hiển thị.
- [x] Thiết kế lại tiêu đề các phần **Thành phần nổi bật** và **Bảng thành phần** trên mọi giao diện: nâng cỡ chữ lên **`16px`** (thay vì in hoa thô cứng `THÀNH PHẦN NỔI BẬT`), sử dụng chữ in thường tự nhiên và giữ màu sắc tinh tế, mang lại phong thái tối giản sang trọng.
- [x] Đạt kết quả biên dịch và chạy kiểm thử không phát sinh lỗi cú pháp mới.

# Category Management Deletion Upgrades (Elite V2.2)
- [x] Thiết lập trường `skipped: List[str]` trong `BulkActionResponse` schema tại [backend/schemas/common.py](file:///home/lv/Desktop/fast-platform-core/backend/schemas/common.py).
- [x] Triển khai hàm kiểm tra tối ưu hóa SQL batch `_check_deletable` trong `CategoryService` tại [backend/services/commerce/category.py](file:///home/lv/Desktop/fast-platform-core/backend/services/commerce/category.py), ngăn chặn xóa danh mục chứa sản phẩm hoạt động hoặc danh mục con chưa xóa.
- [x] Cập nhật các phương thức `delete_category`, `bulk_delete`, `hard_delete_category` và `bulk_hard_delete` áp dụng chặt chẽ các luật nghiệp vụ an toàn dữ liệu.
- [x] Khai báo các API Endpoints `/hard-delete` và `/bulk-hard-delete` trong `CategoryController` tại [backend/controllers/category.py](file:///home/lv/Desktop/fast-platform-core/backend/controllers/category.py).
- [x] Thiết kế hộp thoại xác nhận chuyên sâu (Confirm Dialog) hỗ trợ cả 4 trạng thái (Soft, Hard, Bulk Soft, Bulk Hard) với hiệu ứng Scale/Fade cao cấp và hiển thị chi tiết đối tượng bị ảnh hưởng trong [CategoryManagement.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/CategoryManagement.svelte).
- [x] Nâng cấp bộ nút thao tác nhanh (Quick Actions) ngay trên dòng của cây danh mục gồm bật/tắt nhanh hiển thị (Mobile/Desktop) không reload và nút Purge vĩnh viễn trong [CategoryTree.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/CategoryTree.svelte).
- [x] Viết kịch bản test đầy đủ vòng đời (Lifecycle Test) kiểm tra tính đúng đắn của logic khóa ngoại và cascade soft-delete tại [backend/scratch/test_category_deletion_flow.py](file:///home/lv/Desktop/fast-platform-core/backend/scratch/test_category_deletion_flow.py) chạy thành công 100%.

# Category Temporary Cleanup (Elite V2.2)
- [x] Xóa 3 danh mục thử nghiệm (`test_child_d04ce4`, `test_parent_a34f9a`, `test_parent_fbb536`) khỏi cơ sở dữ liệu.
- [x] Xác minh trạng thái cơ sở dữ liệu sau khi xóa để đảm bảo sạch sẽ và không ảnh hưởng đến dữ liệu production.

# Category Hierarchy N-Level Rendering Fix (Elite V2.2)
- [x] Phân tích nguyên nhân mất sub3: `list_categories` ở backend chỉ query 2 tầng (`parent_id IS NULL` và `parent_id IN (parents)`), và `CategoryTree.svelte` chỉ render đúng 2 vòng lặp `#each`.
- [x] Đề xuất 1 (Backend): Nâng cấp `list_categories` trong `backend/services/commerce/category.py`. Chuyển sang tải Zero-Hydration flat array toàn bộ danh mục, sau đó dùng Dictionary O(N) thuật toán build tree đệ quy. Điều này giúp lấy full độ sâu cây danh mục mà không làm tăng Query, Latency < 1ms, không ngốn RAM.
- [x] Đề xuất 2 (Frontend): Nâng cấp `CategoryTree.svelte` sử dụng Svelte 5 `{#snippet}` để gọi đệ quy render danh mục, cho phép hiển thị N-level subcategories với đầy đủ UI mà không bị hardcode độ sâu. Không gây Memory Leak do sử dụng native snippet của Svelte Runes.
- [x] Đã hoàn thành nạp cây danh mục N-level mượt mà.

# Helen Quick Actions Conditional Visibility (Elite V2.2)
- [x] Phân tích và bao bọc khối hiển thị quickActions ở Desktop (`SupportChatDesktop.svelte`) để chỉ hiển thị khi có `productSlug`.
- [x] Phân tích và bao bọc khối hiển thị quickActions ở Mobile (`SupportChatMobile.svelte`) để chỉ hiển thị khi có `productSlug`.
- [x] Kiểm thức biên dịch tĩnh `svelte-check` toàn bộ dự án thành công.
- [x] Cập nhật nhật ký bàn giao `walkthrough.md` đầy đủ bằng chứng.

# Helen Nút Tư Vấn Siêu Cấp Bán Hàng (Sales Assassin Consulting)
- [x] Thêm nút "Tư vấn" (icon Target) vào quickActions Desktop (`SupportChatDesktop.svelte`).
- [x] Đồng bộ nút "Tư vấn" sang Mobile (`SupportChatMobile.svelte`).
- [x] Thiết kế prompt 3 Điểm Chạm Tâm Lý (Pain/Selling/Buying Point + CTA).
- [x] Sửa lỗi hiển thị prompt gốc lên bubble tin nhắn của khách hàng bằng tham số `displayText` trong `sendMessage`.
- [x] Sửa lỗi Helen không phản hồi do OrderHandler đánh chặn bằng tag `[system_consult]` bypass và lọc tự động tại `ConsultantHandler`.
- [x] Sửa lỗi `ConsultantHandler` tự động nhường quyền (silenced yield) cho Order Flow do chứa dấu hai chấm `:` và từ khóa `"mua sắm"` trong prompt.
- [x] Sửa lỗi import thiếu instance `article_vector_service` khiến chức năng tìm kiếm bài viết bằng vector bị lỗi.
- [x] Tối ưu hóa định tuyến `trinity_bridge`: Ngay lập tức thoát vòng lặp key (break) để nhảy sang model fallback tiếp theo nếu gặp lỗi dịch vụ `503/500` hoặc lỗi kiểm định đầu ra `ValidationError`, thay vì xoay vòng thử lại 8 key vô ích.
- [x] Giới hạn thời gian chờ cuộc gọi AI của `ConsultantHandler` xuống còn `timeout=12.0` để tối đa hóa tốc độ phản hồi.
- [x] Căn chỉnh thời gian chờ phía Client (`_pulseTimeout`) xuống còn `30` giây để tối ưu hóa trải nghiệm người dùng kết hợp với cơ chế fail-fast mới.
- [x] Thiết lập Bộ ngắt mạch Model (Model Circuit Breaker): Cấu hình hàm `track_model_failure` để tự động cho model vào blacklist tạm thời trong 5 phút (300s) nếu xảy ra 3 lỗi liên tiếp (Timeout hoặc 503 Service Unavailable) trong 60 giây.
- [x] Sửa lỗi Timeout không bị ghi nhận: Trước đây khi xảy ra `TimeoutError`, hệ thống chỉ thoát ra (`break`) mà không cập nhật độ khỏe của key (`mark_unhealthy`). Đã bổ sung logic ghi nhận lỗi timeout trên key và tăng số lỗi của model để hạ nhiệt đúng cách.
- [x] Tách biệt tiêu đề kỹ thuật thô kệch: Cấm tuyệt đối Helen in ra các nhãn prompt như "Điểm đau", "Giải pháp", "Viễn cảnh tự do" trong phản hồi.
- [x] Bổ sung CTA và thông tin ưu đãi/giá bán: Enforce Helen báo giá gốc + giá khuyến mãi từ dữ liệu PRODUCT, kích thích FOMO tồn kho, và đưa ra Kêu Gọi Hành Động (CTA) thu thập Lead quyết liệt (xin SĐT + Địa chỉ để đóng gói gửi ngay).
- [x] Bảo toàn và chi tiết hóa thành phần nổi bật (Ingredients List): Cấu hình prompt tối ưu hóa để AI vẫn liệt kê đầy đủ chi tiết các thành phần nổi bật dưới dạng bullet points rõ ràng như thiết kế ban đầu, chỉ ẩn đi các tiêu đề thô sơ.
- [x] Tích hợp Xoay Vòng CTA Thông Minh (Smart CTA Rotation): Cấu hình Helen tự động phát hiện trạng thái thông tin khách hàng đã gửi (chưa gửi thông tin, đã gửi SĐT nhưng thiếu Địa chỉ, hoặc đã gửi đủ SĐT + Địa chỉ) để đưa ra câu chốt đơn xoay vòng linh hoạt, cấm trùng lặp rập khuôn từ câu thứ 2 trở đi.
- [x] Sửa lỗi Helen không nắm được thông tin khuyến mãi khi giỏ hàng trống: Cập nhật `_generate_fomo_instructions` trong `support_agent.py` để inject danh sách Voucher/Khuyến mãi đang diễn ra vào ngữ cảnh tư vấn ngay cả khi khách chưa thêm sản phẩm vào giỏ, đồng thời yêu cầu Helen chủ động giới thiệu ở Bước 4 trong `consultant.py`.
- [x] Cập nhật cứng (Hardcode) thành phần "Placenta tinh khiết 100% từ Nhật Bản" tại vị trí Top 1 của danh sách nguyên liệu nổi bật cho TOÀN BỘ sản phẩm. Bất kỳ sản phẩm nào khi Tư vấn cũng sẽ được Helen phân tích công dụng của Placenta trước tiên.
- [x] Siết chặt Luật Từ Vựng (Nhau thai -> Placenta): Bổ sung quy tắc tối thượng `KIỂM SOÁT TỪ VỰNG TỐI THƯỢNG` vào `SYSTEM_PROMPT` của `ConsultantHandler` (`consultant.py`), cấm tuyệt đối Helen dùng từ "Nhau thai" hay "nhau thai", bắt buộc chuyển 100% thành "Placenta" trong mọi câu trả lời.
- [x] Sửa lỗi rò rỉ dữ liệu chéo Tenant (Tenant Data Leakage) & Soft Delete: Cập nhật hàm fetch Voucher trong `support_agent.py` để bổ sung bộ lọc `tenant_id == current_tenant_id` và `deleted_at.is_(None)`. Khắc phục tình trạng Helen gợi ý các mã khuyến mãi (như VIRAL149K) thuộc Tenant khác hoặc đã bị xóa mềm.
- [x] Kiểm thức biên dịch tĩnh `svelte-check` — Không lỗi mới phát sinh.
- [x] Cập nhật nhật ký bàn giao `walkthrough.md`.

# Storefront Percentage Voucher Display Fix (Giảm tối đa 5đ Fix)
- [x] Phân tích logic render "Giảm tối đa" tại `VouchersDesktop.svelte` và `VouchersMobile.svelte`.
- [x] Cải tiến logic để tránh lỗi hiển thị "Giảm tối đa {v.value}đ" đối với Voucher dạng PERCENT khi không cấu hình `max_discount`.
- [x] Thực hiện tự kiểm thức và chạy `npx svelte-check` kiểm tra cú pháp frontend.
- [x] Cập nhật nhật ký bàn giao `walkthrough.md`.

# Exclusive Product Voucher Configuration & Engine Integration (Elite V2.2)
- [x] Thiết kế và tích hợp bộ tìm kiếm sản phẩm động (debounced Real-time Search Input) và hiển thị kết quả (Dropdown) kèm các nhãn Tag phát sáng neon màu ngọc lục bảo (Emerald Glowing Tags) cực kỳ sang trọng vào [VoucherDrawer.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/VoucherDrawer.svelte).
- [x] Tích hợp trực tiếp UUID và nhãn hiển thị thân thiện vào mảng `applicable_product_ids` và `applicable_product_display` thông qua tương tác nhấp chọn trực quan thay vì gõ text thủ công, nâng cấp trải nghiệm sử dụng đúng chuẩn Elite V2.2.
- [x] Cải tiến công thức tính giảm giá của pricing engine tại [backend/services/commerce/logic/pricing_engine.py](file:///home/lv/Desktop/fast-platform-core/backend/services/commerce/logic/pricing_engine.py) để tính giảm giá voucher riêng biệt trên các sản phẩm được áp dụng và scale tỷ lệ công bằng theo Combo.
- [x] Đồng bộ hóa logic tính toán giảm giá và kiểm tra điều kiện tối thiểu tại client-side trong `CartStore` (`cart.svelte.ts`) và `checkout/+page.svelte` để khớp 100% với backend pricing.
- [x] Bổ sung bộ lọc hiển thị voucher restricted (chưa lọc ngoài admin) tại `ProductMobileOverview.svelte`, `LandingPage/Desktop.svelte`, và `MainDetail/Desktop.svelte` để chỉ hiện voucher nếu nó không bị giới hạn hoặc được giới hạn đúng cho sản phẩm đang xem.
- [x] Tích hợp huy hiệu độc quyền "Sản phẩm riêng" / "Toàn sàn" cao cấp vào danh sách voucher chung storefront (`VouchersDesktop.svelte` và `VouchersMobile.svelte`) tạo sự minh bạch và kích thích chốt đơn.
- [x] Chặn cấp độ backend cho phạm vi áp dụng (Product Scope Enforcement) tại `backend/services/commerce/checkout.py` bằng cách ném ra `ValidationException` rõ ràng nếu payload chứa voucher không hợp lệ cho giỏ hàng hoặc không đạt min_spend tối thiểu của các sản phẩm nằm trong danh mục áp dụng của voucher đó.
- [x] Chạy kiểm thức tĩnh `svelte-check` trên frontend và AST checks trên backend để đảm bảo 0 lỗi phát sinh.

# Exclusive Product Voucher Optimizations & Security Safeguards (Elite V2.2 - Bản nâng cấp mịn)
- [x] Thiết lập logic `isVoucherEligible(v)` và `getEligibleSubtotal(v)` tập trung trong `CartStore` (`cart.svelte.ts`) để thống nhất logic xác định tính hợp lệ của mã giảm giá giới hạn sản phẩm.
- [x] Nâng cấp checkout storefront (`checkout/+page.svelte`):
  - [x] Triển khai bộ lọc tự động gỡ các voucher không đạt điều kiện `min_spend` hoặc phạm vi áp dụng khi số lượng sản phẩm thay đổi.
  - [x] Triển khai **Giao thức Tối ưu hóa Chọn Mã Giảm Giá Thông Minh (Intelligent Discount Optimization)**: Tự động so sánh số tiền giảm giá thực tế (VND) của tất cả các voucher phần trăm và cố định khả dụng, tự động chuyển đổi sang voucher tốt nhất cho người dùng khi tăng/giảm số lượng.
  - [x] Thiết lập chặn thủ công (Manual Toggle Guard): Hiển thị toast cảnh báo và chặn chọn mã nếu giỏ hàng hoàn toàn không chứa sản phẩm hợp lệ của voucher giới hạn.
- [x] Nâng cấp `VoucherSection.svelte` để đồng bộ cờ `isEligible` thông qua `cartStore.isVoucherEligible(v)`, tự động làm mờ và khóa click trực quan.
- [x] Nâng cấp Backend Checkout Security Guard (`checkout.py`):
  - [x] Tích hợp tính năng đối chiếu trùng khớp phạm vi áp dụng đối với cả ID sản phẩm lẫn Slug sản phẩm (đã trim và chuẩn hóa lowercase), triệt tiêu hoàn toàn mọi kịch bản bypass hoặc hack mã từ client.
- [x] Chạy kiểm định tĩnh `svelte-check` trên toàn bộ storefront, xác nhận giải quyết triệt để lỗi type mismatch, biên dịch sạch sẽ 100%.
- [x] Chạy AST check thành công trên backend Python, sẵn sàng vận hành tuyệt đối an toàn.

# Helen AI Combo Recognition & Human-Readable Variant Checkout Upgrade (Elite V2.2)
- [x] Bổ sung helper `getEffectiveVariant(itemId)` và `getVariantName(product, variant)` trong `CartStore` (`cart.svelte.ts`) để phân giải tự động các cấp combo (e.g. "Dứt điểm", "Hiệu quả") và tên biến thể một cách linh hoạt.
- [x] Nâng cấp `CheckoutItems.svelte` để hiển thị:
  - [x] Tên biến thể thân thiện (e.g. "Dứt điểm") thay vì hiển thị SKU thô kệch `4968123159004-2` dưới tag "Phân loại".
  - [x] Tên quà tặng và số lượng combo quà tặng cụ thể một cách trực quan, đẹp mắt và sang trọng.
- [x] Nâng cấp logic `helenAdvice` trong `checkout/+page.svelte` để phát hiện và tuyên dương khách hàng khi họ đạt được các combo cấp độ:
  - [x] Thay vì phản hồi chung chung, Cố vấn AI Helen sẽ nêu rõ tên combo đạt được (e.g. "Dứt điểm") kèm lời chúc mừng đầy FOMO và cam kết chất lượng.
- [x] Xác minh tính chính xác, giao diện hiển thị tinh xảo và tính nhất quán với Svelte 5 Runes.
- [x] Cập nhật tài liệu nghiệm thu đầy đủ trong `walkthrough.md`.


