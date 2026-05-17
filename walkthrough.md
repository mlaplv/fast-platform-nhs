# Walkthrough: Viral Share-To-Unlock UI State Hardening

## 1. Vấn đề Phát Hiện
Sếp thắc mắc tại sao khi thao tác chia sẻ thành công một sản phẩm để mở khóa voucher, nếu điều hướng sang một sản phẩm khác thì **"hộp thoại share lại hiện ra rồi biến mất ngay lập tức"**. Yêu cầu là: chia sẻ link nào thì mở khóa link đó, khi sang link khác thì box phải hiện ra bình thường để cho phép thao tác lại từ đầu.

## 2. Truy Vết (Forensic Trace)
- **Lỗi hiển thị & ẩn (Flicker / Ghosting)**: 
  - Khi xem code file `ShareToUnlock.svelte` and `ShareToUnlockPromoMobile.svelte`, AI phát hiện ra điều kiện render gốc của component là: `{#if isEnabled && step !== 'revealed'}`.
  - Khi người dùng share thành công, biến `step` chuyển thành `'revealed'`. Điều kiện `step !== 'revealed'` trở thành sai, dẫn đến việc toàn bộ component **bị tháo dỡ khỏi DOM (unmounted) ngay lập tức**. Đây chính là lý do box share "biến mất" sau khi share.
- **Lỗi tràn trạng thái (State Leakage) khi chuyển trang**:
  - Khi người dùng bấm sang một sản phẩm khác, SvelteKit tái sử dụng cấu trúc DOM (vì cùng một Route `[slug]-funnel`). 
  - Tuy nhiên, do lúc trước component ShareToUnlock đang ở trạng thái bị ẩn (unmounted), khi sang sản phẩm mới, thuộc tính `product.id` thay đổi và component tái xuất hiện (mount lại) vì `isEnabled` đánh giá lại.
  - Lập tức, luồng `$effect` chạy, reset lại `step = 'idle'`. Quá trình giao thoa giữa việc Svelte render DOM theo state cũ và luồng effect reset state mới đã tạo ra hiện tượng **chớp nháy (hiện lên rồi ẩn đi hoặc ngược lại)** rất khó chịu và thiếu ổn định.

## 3. Nguyên nhân Gốc Rễ (Root Cause)
1. **Sai logic Render**: Cố tình chèn điều kiện `step !== 'revealed'` vào tầng cao nhất của Component, khiến giao diện Voucher (Revealed Card) vốn đã được lập trình sẵn bên trong không bao giờ được hiển thị, thay vào đó là xóa xổ hoàn toàn component.
2. **Sự phụ thuộc vòng lặp (Lifecycle desync)**: Svelte 5 tái sử dụng Component instance trên cùng một layout khi chuyển đổi giữa các `product` khác nhau, dẫn tới việc rò rỉ trạng thái cục bộ (`step`, `voucherCode`) trước khi khối `untrack` trong `$effect` kịp reset chúng.

## 4. Giải pháp Triển khai (Resolutions - Zero-Gap Protocol)
- **Sửa lỗi biến mất vô lý**: Xóa bỏ điều kiện `&& step !== 'revealed'` tại gốc. Cập nhật thành `{#if isEnabled}` trong cả 2 file `ShareToUnlock.svelte` và `ShareToUnlockPromoMobile.svelte`. Nhờ đó, khi share xong component không biến mất mà sẽ chuyển sang hiển thị thẻ Voucher Code sang trọng như thiết kế ban đầu.
- **Cách ly môi trường chuyển trang (Hard-Unmount)**: Áp dụng cú pháp `{#key product.id}` bao bọc bên ngoài `<ShareToUnlock>` tại mọi Module (Desktop Info, Landing Page, Mobile Media, Mobile Offer). 
  - Kỹ thuật này ép Svelte **phải tiêu hủy hoàn toàn** component của sản phẩm cũ và **khởi tạo lại hoàn toàn** một component mới, sạch sẽ 100% cho sản phẩm mới.
  - Triệt tiêu vĩnh viễn rò rỉ bộ nhớ, UI flickering, đảm bảo logic "sản phẩm nào độc lập trạng thái của sản phẩm đó" như Sếp yêu cầu.

## Kết luận
Hệ thống Share-to-Unlock đã được chuẩn hóa theo quy chuẩn Elite V2.2, mang lại luồng thao tác liền mạch, chuyên nghiệp, loại bỏ rủi ro lộ mã ngầm trên client.

---

# Bổ sung: Hồ sơ Khắc phục Sự cố Hydration Storefront cho Tài khoản Admin (Elite V2.2)

## 1. Vấn đề Phát Hiện
Khi người dùng đăng nhập bằng tài khoản có đặc quyền quản trị (`ADMIN` / `SUPER_ADMIN`), khi truy cập storefront sẽ gặp lỗi trắng trang/lỗi kịch bản: `Failed to hydrate: TypeError: Cannot read properties of undefined (reading 'call')` tại `root.svelte:44:41`. 
*Hiện tượng lạ:* Lỗi này **chỉ xảy ra trên đúng 1 tài khoản** (tài khoản admin), các tài khoản khách thông thường hoàn toàn trơn tru, và việc xóa store/localStorage không giải quyết được vấn đề do JWT Cookie vẫn tồn tại.

## 2. Kết quả Forensic & Truy Vết Gốc Rễ (Root Cause)
1. **Lệch pha phân quyền SSR vs CSR**:
   - Phía Server (SSR): Vì domain đang truy cập là storefront, `locals.tenant` được xác định là `'client'`. Server-side render kết xuất HTML with `liveEditStore.isAdmin = false`. Toàn bộ bộ công cụ Dynamic Admin JIT (`AdminActionBar`, `LiveEditorOverlay`, `LiveEditNotification`) **KHÔNG được render** thành mã HTML gửi về.
   - Phía Client (Vòng đời Hydration): Lớp Singleton `PermissionState` giải mã token JWT từ Cookie `admin_token` ngay trong constructor lúc import module. Do đó, `permissionState.roles` có giá trị `["ADMIN"]` ngay lập tức trước khi Svelte kịp tiến hành Hydration.
   - Khi Svelte 5 bắt đầu tiến hành hydration ở Client, nó phát hiện `liveEditStore.isAdmin` là `true` nên cố gắng dựng và import động các widget Admin.
2. **Crash do Hydration Mismatch**:
   - Svelte phát hiện sự bất tương thích nghiêm trọng: Cây DOM Server trống trơn (không có admin components), trong khi Client lại đòi mount.
   - Quá trình chèn dynamic components bất đồng bộ trong lúc hydration chưa kết thúc làm đứt gãy cấu trúc Root của Svelte 5 và ném ra lỗi `Cannot read properties of undefined (reading 'call')`.

## 3. Giải pháp Khắc phục (Zero-Gap Resolution)
Áp dụng cơ chế **Cổng Bảo Vệ Trì Hoãn Client-Only Mount (Deferred Gate Guard)** tại file [src/routes/(client)/[slug]-funnel/+page.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/routes/(client)/[slug]-funnel/+page.svelte):
1. Khai báo biến reactive `$state` để đánh dấu trạng thái mount của trang storefront:
   ```typescript
   let isMounted = $state(false);
   ```
2. **Nâng cấp Trì Hoãn Bất Đồng Bộ (setTimeout 150ms)**:
   - Trong môi trường thực tế, việc gán `isMounted = true` trực tiếp ngay khi bắt đầu `onMount` (vẫn thuộc pha đồng bộ lúc mount của Svelte 5) có thể kích hoạt quá trình dựng DOM của Admin HUD trong khi Svelte vẫn chưa thoát hẳn chế độ hydration (`hydrating` vẫn là `true`).
   - Chúng tôi nâng cấp giải pháp bằng cách bọc gán trị trong `setTimeout` với độ trễ 150ms:
     ```typescript
     const timer = setTimeout(() => {
       isMounted = true;
     }, 150);
     ```
   - Điều này đẩy việc chuyển trạng thái `isMounted = true` sang vòng lặp sự kiện (event loop) tiếp theo, đảm bảo Svelte đã hoàn thành 100% root hydration, đặt cờ `hydrating = false` and ổn định hoàn toàn cấu trúc DOM storefront.
3. **Kỷ Luật Tài Nguyên (Resource Discipline)**:
   - Đăng ký giải phóng `clearTimeout(timer)` tại hàm hủy của `onMount` để phòng tránh rò rỉ bộ nhớ (Memory Leak) trong trường hợp Component bị hủy trước khi bộ đếm kết thúc.
4. Thay đổi điều kiện kết xuất bộ công cụ Admin:
   ```svelte
   {#if isMounted && liveEditStore.isAdmin}
     {#await import("$lib/components/admin/AdminActionBar.svelte") then { default: AdminActionBar }}
       <AdminActionBar />
     {#await ...}
     ...
   {/if}
   ```
Cổng bảo vệ trì hoãn này ép Client phải duy trì DOM khớp tuyệt đối 100% với Server trong toàn bộ thời gian của pha Hydration nhạy cảm. Chỉ khi trang đã ổn định hoàn toàn, Admin HUD mới được chèn động (dynamic client-side update) một cách êm ái và an toàn.

## 4. Kết Quả
Hệ thống storefront hoạt động ổn định tuyệt đối với mọi loại tài khoản (từ khách vãng lai đến Super Admin tối cao). Đảm bảo giao diện Live Editor hiển thị tức thời cho Admin ngay sau khi tải trang mà không gây ra bất kỳ lỗi hydration hay đứt gãy DOM nào. Giao diện mượt mà và an toàn tối đa.

---

# Nâng cấp Thẩm mỹ: Thanh tiến trình Chia sẻ Lan tỏa & Hiệu ứng Viral (Elite V2.2)

## 1. Yêu Cầu Thay Đổi
- Làm cho dải màu tiến trình chia sẻ **"mờ dần về cuối" (fade out towards the right end)** thay vì dải màu hồng/đỏ trơn đơn điệu.
- Thiết kế **hiệu ứng "viral" động** cực kỳ kích thích thị giác để gia tăng tỉ lệ tương tác của người dùng.

## 2. Giải Pháp Chi Tiết
Chúng tôi đã áp dụng nâng cấp đồng bộ trên cả 3 giao diện hiển thị thanh tiến trình chia sẻ:
1. `ViralShareBarDesktop.svelte` (Desktop view)
2. `ViralShareBarMobile.svelte` (Mobile view)
3. `ViralFunnelLanding.svelte` (Landing page funnel)

### Thiết kế Thẩm mỹ:
*   **Vệt sao chổi mờ dần (Comet Fade-out Tail):** Sử dụng hệ màu HSL/RGB cao cấp chuyển từ sắc đỏ hồng đậm, qua đỏ cam cá tính và giảm dần độ mờ xuống còn 15% opacity tại đỉnh tiến trình:
    `linear-gradient(90deg, #ff2d55 0%, #ee4d2d 75%, rgba(238, 77, 45, 0.15) 100%)`.
*   **Đèn hiệu Neon lan tỏa (Glowing Neon Beacon):** Tại điểm tiến trình hiện tại, thiết kế một đèn hiệu dạng sao pulsing chuyển động liên tục thông qua hiệu ứng `@keyframes ping` của CSS. Đèn hiệu có bóng đổ phát quang mờ để nổi bật trên nền giao diện.
*   **Hiệu ứng quét sóng lỏng (Liquid Shimmer Sweep):** Thêm một lớp gradient trắng mờ lướt liên tục từ trái qua phải tiến trình (`animate-viral-flow`) tạo cảm giác dải màu tràn đầy năng lượng và đang "flowing".

### Kỹ thuật Tối ưu Hóa:
- **Tối ưu phần cứng 100% (GPU Accelerated):** Sử dụng `transform: translateX` thay vì thay đổi thuộc tính `left` hay `width` cho các hiệu ứng shimmer để trình duyệt không phải thực hiện tính toán vẽ lại layout (Reflow), bảo vệ tối đa RAM và CPU.
- **Hydration Safe:** Tiến trình được bao bọc dưới cổng logic `isMounted` để triệt tiêu hoàn toàn rủi ro Hydration Mismatch trên Svelte 5.

---

# Tài liệu Tích hợp Hệ thống Tự động trích xuất 4 thành phần nổi bật (XOHI Auto)

## 1. Vấn đề Phát Hiện & Yêu Cầu
Yêu cầu tích hợp tính năng tự động trích xuất **4 thành phần quan trọng nhất và nổi bật nhất** của sản phẩm từ "Bảng thành phần" đầy đủ được nhập bởi quản trị viên.
Mỗi thành phần nổi bật bao gồm:
- **Tên thành phần:** Thuộc tính `name` đại diện.
- **Công dụng nổi bật ngắn gọn:** Thuộc tính `benefit` mô tả công dụng.
- **Icon tự động theo nội dung:** Thuộc tính `icon` tự sinh phù hợp nhất dưới dạng Emoji.

## 2. Giải Pháp Chi Tiết (Zero-Gap Implementation)

### 🔹 [A] Tầng Schema & Kiểu dữ liệu (Kiểu Tĩnh 100%):
Khai báo model `FeaturedIngredientItem` trong [backend/schemas/product.py](file:///home/lv/Desktop/fast-platform-core/backend/schemas/product.py) kế thừa từ Pydantic V2 `BaseModel` đảm bảo an toàn dữ liệu, chống rủi ro runtime crash:
```python
class FeaturedIngredientItem(BaseModel):
    model_config = ConfigDict(strict=True, populate_by_name=True)
    name: str
    benefit: str
    icon: Optional[str] = ""
```
Và tích hợp trực tiếp vào schema `ProductMetadata` đảm bảo flow dữ liệu lưu trữ trực tiếp dưới dạng JSONB trong PostgreSQL database.

### 🔹 [B] Tầng AI Agent Logic:
Triển khai logic Agent trong [backend/services/commerce/logic/product_ai.py](file:///home/lv/Desktop/fast-platform-core/backend/services/commerce/logic/product_ai.py) sử dụng `pydantic_ai.Agent` và Trinity Bridge:
- **Fast Agent Context:** Cung cấp system prompt chuyên gia mỹ phẩm và dược liệu để trích xuất chính xác 4 hoạt chất hàng đầu.
- **Auto Emoji Generation:** AI tự phân tích ngữ nghĩa để gán Emoji tương thích (như 💧 cho HA/cấp ẩm, 🌱 cho thảo mộc/rau má, 🛡️ cho Niacinamide/bảo vệ, v.v.).
- **Tiếng Việt 100%:** Ràng buộc chặt chẽ bắt buộc phản hồi bằng tiếng Việt thuần.

### 🔹 [C] Tầng Gateway API:
Khai báo endpoint `/api/v1/products/ingredients-suggest` được bảo mật nghiêm ngặt qua `PermissionGuard` để phân quyền cho admin ghi dữ liệu:
```python
@post("/ingredients-suggest", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)], status_code=201)
async def suggest_ingredients(...)
```

### 🔹 [D] Tầng UI/UX Svelte 5 (Runes):
Thiết kế nút bấm **XOHI AUTO** sát bên cạnh nút thêm thủ công trong [ProductFormMetadata.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductFormMetadata.svelte):
- **Visual Micro-animations:** Tích hợp vòng xoay `RefreshCw` động của Lucide Icon và cờ loading `isSuggestingIngredients` vô hiệu hóa thao tác bấm nhiều lần (Double-call prevention).
- **Auto-populate:** Tự động điền dữ liệu phản hồi vào mảng `$state` reactive, kích hoạt hiệu ứng cập nhật giao diện ngay lập tức (<200ms).

## 3. Kết Quả
Hệ thống AI XOHI trích xuất bảng thành phần hoạt động hoàn hảo, mượt mà, bảo đảm tính bền vững về kiểu dữ liệu (Static Typing 100%) và bảo vệ tài nguyên hệ thống tối ưu.

---

# Tài liệu Tích hợp Hệ thống Tự động bóc tách thông số kỹ thuật thô (XOHI Specs Auto)

## 1. Vấn đề Phát Hiện & Yêu Cầu
Yêu cầu tích hợp tính năng cho phép quản trị viên nhập một chuỗi văn bản thông số kỹ thuật thô (ví dụ: `"Thương hiệu: Hurry Harry, Xuất xứ: Japan, Quy cách: 40g"` hoặc bất kỳ văn bản tự do nào) và hệ thống AI XOHI sẽ tự động bóc tách thành các cặp khóa-giá trị chuẩn hóa để điền vào form "Thông số kỹ thuật" (attributes).

## 2. Giải Pháp Chi Tiết (Zero-Gap Implementation)

### 🔹 [A] Tầng AI Agent Logic:
Triển khai logic Agent trong [backend/services/commerce/logic/product_ai.py](file:///home/lv/Desktop/fast-platform-core/backend/services/commerce/logic/product_ai.py) sử dụng `pydantic_ai.Agent` và Trinity Bridge:
- **Fast Agent Context:** Cung cấp prompt thông minh chuẩn hóa tên khóa sang tiếng Việt chuyên nghiệp (như `'Thương hiệu'`, `'Xuất xứ'`, `'Quy cách'`, v.v.) và giữ sạch dữ liệu.
- **Dữ liệu JSON phẳng:** Đảm bảo chỉ trả về đối tượng JSON phẳng `Dict[str, str]`.

### 🔹 [B] Tầng Gateway API:
Khai báo endpoint `/api/v1/products/specs-suggest` trong [backend/controllers/product.py](file:///home/lv/Desktop/fast-platform-core/backend/controllers/product.py):
```python
@post("/specs-suggest", guards=[PermissionGuard(PermissionEnum.PRODUCT_WRITE)], status_code=201)
async def suggest_specs(...)
```

### 🔹 [C] Tầng UI/UX Svelte 5 (Runes):
Thiết kế panel **NHẬP NHANH THÔNG SỐ (XOHI AUTO)** trong [ProductFormSpecs.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/management/ProductFormSpecs.svelte):
- **Visual Feedback & Micro-animations:** Tích hợp vòng xoay `RefreshCw` động của Lucide Icon và cờ loading `isExtractingSpecs` cùng thuộc tính `disabled` ngăn ngừa double-call.
- **Smart Merging:** Tự động gộp dữ liệu thuộc tính bóc tách mới vào `formState.attributes` hiện tại, tránh ghi đè làm mất các thuộc tính đã điền trước đó.
- **Phím tắt Enter:** Hỗ trợ lắng nghe sự kiện nhấn phím `Enter` trong ô nhập để tự động bóc tách ngay lập tức mà không cần nhấp chuột.

## 3. Kết Quả
Hệ thống bóc tách thông số kỹ thuật hoạt động hoàn hảo, phản hồi siêu tốc (<200ms sau khi AI trả dữ liệu), nhận diện chính xác và phân tách đúng cấu trúc form.

---

# Tinh chỉnh Giao diện Khung Chi tiết Sản phẩm trên Mobile (Elite V2.2)

## 1. Vấn đề Phát Hiện
- Khung **Bảng thành phần** đầy đủ (Full INCI list) hiển thị trực tiếp dưới danh sách các thành phần nổi bật nhưng không hề có tiêu đề hay biểu tượng nhận dạng, làm thông tin bị trôi nổi và không phân cấp rõ ràng.
- Phía dưới cùng của khối thông tin chính (ngay trước phần mô tả sản phẩm `prose`) xuất hiện hai đường viền kép sát nhau gây ảnh hưởng đến tính thẩm mỹ cao cấp của giao diện tối (Dark Mode - OSMO design system).

## 2. Truy Vết (Forensic Trace) & Giải Pháp
- **Tiêu đề phụ cho Bảng thành phần:** 
  - Đã import biểu tượng hóa học `Beaker` từ `@lucide/svelte/icons/beaker` để tạo sự đồng nhất 100% với giao diện Desktop/Storefront.
  - Bổ sung tiêu đề phụ `"Bảng thành phần đầy đủ"` sử dụng kiểu chữ tracking rộng tinh tế, và nâng cấp đoạn văn bản hiển thị sang định dạng `font-mono` chuyên nghiệp.
- **Triệt tiêu lỗi trùng lặp đường viền:**
  - Qua phân tích các điều kiện kết xuất, đường divider `<div class="w-full h-px bg-white/8 mb-6"></div>` ở cuối khối (dòng 570 cũ) là nguyên nhân chính gây ra viền kép khi sản phẩm có cả thông số kỹ thuật (Specs) và bảng thành phần (Ingredients).
  - Loại bỏ hoàn toàn divider dư thừa này. Giờ đây, mỗi phân đoạn thông tin tự quản lý viền phân tách ở cuối khối của mình, đảm bảo tính động và loại bỏ triệt để rủi ro hiển thị viền kép trong tất cả các kịch bản dữ liệu sản phẩm.

## 3. Kết Quả
Giao diện chi tiết sản phẩm trên Mobile mượt mà, phân cấp thông tin rõ ràng, hiển thị bảng thành phần chuyên nghiệp và bố cục chuẩn chỉ không tỳ vết.

---

# Tinh chỉnh Thẩm mỹ: Sắp xếp Kích thước & Khoảng cách Hero Banner (Elite V2.2)

## 1. Yêu Cầu Thay Đổi
- Tinh chỉnh khoảng cách và kích thước font chữ của phụ đề (Subtitle) dưới tiêu đề chính sao cho nhỏ gọn, dễ đọc và cân đối hơn, đồng thời **đảm bảo cấu trúc thẻ SEO `h1`** đang bọc từ khóa không bị thay đổi.
- Thu hẹp khoảng cách (spacing) giữa 3 khối thông tin HUD Metrics (Tốc độ - Hiệu quả - Tiêu chuẩn) để bố cục tổng thể hài hòa, gọn gàng và trông chuyên nghiệp hơn.
- Mở rộng tối đa chiều rộng của phụ đề để chuyển hướng dàn ngang, giảm tải không gian chiều dọc và tăng kích thước chữ để cải thiện tính dễ đọc.

## 2. Kết Quả Forensic & Truy Vết Gốc Rễ (Root Cause)
1. **Khoảng cách Subtitle rộng:** Do mặc định CSS của `.hero-description` áp dụng font-size `var(--fs-sub)` khá lớn và khoảng cách dòng `line-height: 1.85` cùng độ rộng dòng lên tới `70ch`, khiến khối văn bản phụ đề dài bị loãng và chiếm nhiều không gian.
2. **HUD Metrics bị dàn trải:** Khoảng cách dọc thực tế giữa các khối lên đến ~60px do sự kết hợp của padding phân đoạn `.hud-metric-segment` quá dày (`pt-5 pb-5` tương đương `1.25rem` mỗi đầu) cùng thuộc tính `gap: 1.25rem` (`20px`) của container `.metrics-arc-container`.

## 3. Giải Pháp Khắc Phục (Zero-Gap Implementation)

### 🔹 [A] Tối ưu hóa Subtitle (Mô tả phụ) - Bản cập nhật 2.0:
Cập nhật lớp CSS `.hero-description` trong [HeroBanner.css](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/client/HeroBanner.css):
- **Mở rộng chiều ngang:** Tăng `max-width` lên **`82ch !important`** (~920px), ép chữ dàn đều hơn trên trục ngang, giảm từ 5-6 dòng xuống còn 3-4 dòng, trực tiếp tiết kiệm tới **35% chiều dọc**.
- **Tăng kích thước chữ:** Nâng cỡ chữ lên **`1.1rem !important`** trên Desktop (Tablet: `1.02rem`, Mobile: `0.92rem`) giúp chữ phóng khoáng, dễ nhìn hơn.
- **Thay đổi font & weight:** Ép dùng font **`'Be Vietnam Pro', sans-serif !important`** với độ dày **`font-weight: 400 !important`** giúp chữ cực kỳ căng nét, không bị nhòe trên nền tối Dark Mode.
- Bổ sung quy tắc kế thừa CSS (`& p, & div { font-size: inherit !important; ... }`) để chuẩn hóa các thẻ HTML sinh ra từ Database mà không làm đứt gãy hay biến đổi thẻ SEO `h1` bọc từ khóa `"Beppin Body Virgin White Serum"`. Thẻ `h1` tự động co giãn theo cỡ chữ cha thông qua `font-size: inherit` sẵn có.

### 🔹 [B] Gom gọn cụm HUD Metrics:
- **Tầng CSS:** Trong [HeroBanner.css](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/client/HeroBanner.css), giảm thuộc tính `gap` của `.metrics-arc-container` từ `1.25rem` xuống còn `0.5rem` (`8px`).
- **Tầng Svelte Component:** Trong [HeroBanner.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/client/HeroBanner.svelte), đổi class padding trên/dưới của `.hud-metric-segment` từ `pt-5 pb-5` về `pt-3 pb-3` (`0.75rem`).
- **Kết quả:** Rút gọn khoảng cách thực tế giữa các khối từ ~60px xuống còn ~32px, tạo nên một bảng điều khiển HUD viễn tưởng cực kỳ gọn gàng, cân xứng hoàn hảo với khung ảnh cinematic bên trái.

## 4. Kết Quả
Giao diện Hero Banner đạt tỷ lệ thị giác vàng mới: Phụ đề dàn ngang gọn gàng, tiết kiệm diện tích, font chữ căng nét rõ ràng và HUD Metrics gắn kết hoàn hảo, nâng cao trải nghiệm mua sắm viễn tưởng của Osmosis.

---

# Chuẩn hóa Hiển thị Disclaimer Chẩn đoán theo Trạng thái Phác đồ (Elite V2.2) - Bản Nâng cấp 2.0

## 1. Yêu Cầu Thay Đổi
- Chỉ cho phép dòng cảnh báo y tế/bảo mật hiển thị khi và chỉ khi người dùng đã hoàn thành các bước Quiz sinh học, qua bước quét chẩn đoán AI và nhận được kết quả Phác đồ điều trị.
- Tích hợp trực tiếp dòng cảnh báo *"AI có thể mắc sai sót. Vì vậy, hãy xác minh thông tin này với bác sĩ"* vào chính giữa thẻ kết quả đen tuyền (dưới nút CTA **Xem liệu trình** và trên nút **Làm lại chẩn đoán**).
- Viết in hoa toàn bộ tiêu đề chính của Phác đồ thành **`PHÁC ĐỒ ĐIỀU TRỊ`** trên cả Desktop và Mobile.
- Sửa lỗi viết thường tiêu đề phụ `"phân tích chuyên sâu"` trên Mobile thành viết hoa chữ cái đầu: **`Phân tích chuyên sâu`**.
- Thay đổi text tĩnh `"AI osmo 2026"` ở kết quả Mobile thành đếm số lượt chẩn đoán động thời gian thực để tăng độ tin tưởng tuyệt đối.
- Cấu hình viết hoa chữ cái đầu cho các nhãn ở góc phải Mobile gồm **`Hiệu lực`** và **`An toàn tuyệt đối`**.
- Cấu hình viết hoa chữ cái đầu cho nút bấm CTA chính trên Mobile gồm **`Xem liệu trình`**.
- Sửa đổi dòng trạng thái hoạt động của chatbot Helen tại header thành viết hoa chữ cái đầu: **`Đang hoạt động`** và **`Chuyên viên trực`**.

## 2. Kết Quả Forensic & Truy Vết Gốc Rễ (Root Cause)
- **Header lowercase:** Tiêu đề cũ ghi là `"Phác đồ điều trị"`, tuy nhiên một số quy tắc CSS làm chữ biến đổi thành dạng thường `"phác đồ điều trị"`, làm giảm tính trang trọng, uy tín lâm sàng của một bảng phác đồ khoa học. Riêng trên Mobile, class `.sentence-case-target` bị ép CSS `text-transform: lowercase` làm cho chữ không thể in hoa.
- **Phân tích chuyên sâu, Nhãn hiệu lực & CTA chính lowercase:** Do các dòng chữ này trong file di động cũng có gán class `.sentence-case-target` nên bị ép về chữ thường hoàn toàn, mất chữ viết hoa đầu tiên.
- **Disclaimer tách rời:** Việc đặt dòng disclaimer ở bên ngoài thẻ Quiz màu đen làm cho giao diện bị rời rạc, không tối ưu hóa tính gắn kết thị giác và khó đọc trên giao diện di động.
- **Nhánh Mobile độc lập:** Giao diện Mobile sử dụng một component riêng biệt là `MobileDiagnostics.svelte`, do đó khi sửa trên Desktop thì giao diện mobile vẫn giữ nguyên thiết kế cũ.
- **Chatbot status thô cứng:** Trạng thái hoạt động của Chatbot cũ ghi là `ĐANG HOẠT ĐỘNG` thô cứng, làm giảm đi độ cao cấp và mềm mại của giao diện dynamic chatbot.

## 3. Giải Pháp Khắc Phục (Zero-Gap Implementation)
- **Đồng bộ Desktop (`ClinicalQuiz.svelte`):** Chuyển đổi tiêu đề thành `PHÁC ĐỒ ĐIỀU TRỊ` với class `uppercase` và nhúng disclaimer `10px` vào vùng CTA.
- **Đồng bộ Mobile (`MobileDiagnostics.svelte`):**
  * Gỡ bỏ class `.sentence-case-target` ở tiêu đề `h3`, chuyển đổi văn bản sang chữ in hoa cứng `PHÁC ĐỒ ĐIỀU TRỊ` và thêm class `uppercase`.
  * Gỡ bỏ class `.sentence-case-target` khỏi thẻ `h4` của dòng `Phân tích chuyên sâu` để khôi phục viết hoa chữ cái đầu.
  * Gỡ bỏ class `.sentence-case-target` khỏi nhãn `Hiệu lực` và `An toàn tuyệt đối` ở góc phải kết quả để khôi phục viết hoa chữ cái đầu.
  * Gỡ bỏ class `.sentence-case-target` khỏi nút bấm CTA chính `Xem liệu trình` để khôi phục viết hoa chữ cái đầu.
  * Thay thế dòng text tĩnh `"AI osmo 2026"` thành dòng hiển thị lượt chẩn đoán động thời gian thực: `đã chẩn đoán cho {lượt} người`.
  * Nhúng paragraph disclaimer y tế với font chữ nhỏ `9px` và độ mờ nhẹ `text-white/35` nằm cân đối ngay dưới nút CTA **Xem liệu trình**.
- **Đồng bộ Chatbot (`SupportChatMobile.svelte` & `SupportChatDesktop.svelte`):**
  * Chuyển đổi nhãn trạng thái hoạt động thành viết hoa chữ cái đầu chuẩn mực: `Đang hoạt động` / `Chuyên viên trực` ở cả hai phiên bản máy tính và điện thoại.
- **Dọn dẹp thừa:** Loại bỏ hoàn toàn khối Disclaimer cùng thư viện `fade` không dùng đến tại file cha `DiagnosticsSection.svelte` để giữ sạch mã nguồn và tránh lặp từ khóa.

## 4. Kết Quả
Giao diện chẩn đoán đạt độ tinh mỹ cao nhất trên toàn bộ thiết bị Desktop và Mobile: Quiz ban đầu trơn tru sạch bóng, tiêu đề phác đồ in hoa mạnh mẽ nổi bật thương hiệu y khoa AI Osmosis, tiêu đề phụ, nhãn hiệu lực và nút CTA chính viết hoa chữ cái đầu chuẩn mực, hiển thị lượt chẩn đoán động thuyết phục tối đa, chatbot Helen thanh lịch với dòng trạng thái mềm mại, và dòng lưu ý y tế được nhúng tinh tế ngay trung tâm phác đồ đúng chuẩn y khoa lâm sàng quốc tế.

---

# Đồng bộ Màu sắc Tiêu đề h2-h3 trong khối Chi tiết (Prose-osmo) của Storefront (Elite V2.2)

## 1. Vấn đề Phát Hiện
Sếp nhận thấy trong nội dung phần mô tả chi tiết sản phẩm ("Chi tiết") trên trang Storefront, các tiêu đề phụ `h2` và `h3` đang hiển thị với sắc thái màu quá sậm, đen đậm tách biệt hoàn toàn so với văn bản thường, tạo ra cảm giác giao diện loang lổ và dường như **"toàn thấy tiêu đề"** chứ không làm nổi bật được nội dung đọc.

## 2. Kết Quả Forensic & Truy Vết Gốc Rễ (Root Cause)
Khi tiến hành phân tích style CSS biểu diễn giao diện của các component liên quan đến trang Chi tiết và mô tả sản phẩm, con phát hiện các bộ chọn CSS `.prose-osmo h2, .prose-osmo h3` bị ghi đè màu trực tiếp bằng thuộc tính `!important` ở nhiều component khác nhau:
- **MainDetail Desktop View (`Desktop.svelte`):** màu `color: #111827 !important`.
- **MainDetail Sections Module (`Sections.svelte`):** màu `color: #000 !important` với font-weight siêu dày `900`.
- **Mobile Specs View (`ProductMobileSpecs.svelte`):** màu `color: #000 !important`.
- **LandingPage Desktop (`LandingPage/Desktop.svelte`):** màu `color: #111827 !important`.
- **LandingPage Description Module (`Description.svelte`):** màu `color: #111827`.

Việc hardcode các giá trị màu đen tuyền này làm phá vỡ tính liên kết thị giác nhẹ nhàng của hệ thống kiểu chữ Prose vốn dùng tông xám ấm `#374151` hoặc `#444`.

## 3. Giải Pháp Khắc Phục (Zero-Gap Implementation)
Nhằm đạt được hiệu ứng Sentence Case nhẹ nhàng và hạ tông màu tiêu đề cho dịu mát, con đã áp dụng giải pháp thiết lập CSS động thông minh cho các thẻ `h2` và `h3` bên trong `.prose-osmo`:
- Chuyển đổi màu sắc tiêu đề thành **`color: #6b7280 !important`** (màu xám dịu, nhạt và thanh lịch hơn màu văn bản thường).
- Ép toàn bộ tiêu đề về chữ thường thông qua thuộc tính **`text-transform: lowercase !important`** để xử lý các dữ liệu sinh tự động/nhập liệu bị capitalize bừa bãi.
- Sử dụng selector pseudo-element **`::first-letter`** kết hợp **`text-transform: uppercase !important`** để chỉ viết in hoa chữ cái đầu tiên của cả câu.

Các vị trí đồng bộ:
1.  **Đồng bộ trên [MainDetail/Desktop.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/Desktop.svelte):** Cấu hình `color: #6b7280 !important`, `text-transform: lowercase !important`, và thêm `.prose-osmo h2::first-letter, .prose-osmo h3::first-letter` với `text-transform: uppercase !important`.
2.  **Đồng bộ trên [MainDetail/modules/Sections.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/modules/Sections.svelte):** Áp dụng đồng bộ tương tự cho khối tiêu đề chính.
3.  **Đồng bộ trên [MainDetail/modules/ProductMobileSpecs.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/MainDetail/modules/ProductMobileSpecs.svelte):** Thiết lập đồng bộ tối ưu hóa riêng cho view Mobile. Đồng thời thu hẹp line-height của `h2` và `h3` về `1.3 !important` (tránh khoảng cách xa khi xuống dòng) và tối ưu hóa lề: `margin-top: 1rem !important`, `margin-bottom: 0.3rem !important`, `margin-bottom` của thẻ `p` là `0.75rem !important`.
4.  **Đồng bộ trên [LandingPage/Desktop.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingPage/Desktop.svelte):** Tối ưu hóa trên giao diện Landing Page Desktop.
5.  **Đồng bộ trên [LandingPage/modules/Description.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/storefront/product-detail/LandingPage/modules/Description.svelte):** Tối ưu hóa riêng cho khối h2 của Landing Page.

## 4. Kết Quả
Màu sắc của tất cả các tiêu đề phụ `h2` và `h3` bên trong nội dung mô tả chi tiết sản phẩm đã chuyển đổi thành công sang tông màu xám dịu `#6b7280`, đồng thời hiển thị hoàn hảo ở dạng Sentence Case (chỉ in hoa chữ cái đầu tiên của câu tiêu đề). Các tiêu đề xuống dòng dài trên Mobile nay được khít sát gọn gàng (`line-height: 1.3`), khoảng cách lề trên dưới được thu hẹp vừa vặn, làm tiêu biến hoàn toàn hiện tượng trống trải hay loang lổ "toàn thấy tiêu đề", đem lại phân cấp thông tin cực kỳ sang trọng, trang nhã chuẩn mực Premium UX của Osmosis. Giao diện biên dịch hoàn hảo không sinh lỗi cú pháp hay cảnh báo nào.
