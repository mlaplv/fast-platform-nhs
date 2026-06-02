# BÁO CÁO PHÂN TÍCH HIỆU NĂNG LIGHTHOUSE & PHƯƠNG ÁN TỐI ƯU HÓA HỆ THỐNG
> **ĐỐI TƯỢNG KHẢO SÁT:** Trang chi tiết sản phẩm `osmo.vn` (Micsmo Storefront)
> **THỜI GIAN ĐÁNH GIÁ:** 2026-06-02
> **QUY CHUẨN KIẾN TRÚC:** Elite V2.2 (SvelteKit 5 Runes + Caddy SPA Routing)

---

## I. TỔNG QUAN CHỈ SỐ HIỆU NĂNG & THỰC TRẠNG

Theo số liệu đo lường thực tế từ Lighthouse (biểu đồ trong ảnh đính kèm), điểm hiệu năng tổng thể của storefront đạt **42/100** – mức báo động đỏ nghiêm trọng đối với tỷ lệ chuyển đổi (CRO):

| Metric | Giá trị đo lường | Trạng thái | Ngưỡng tiêu chuẩn | Ý nghĩa |
| :--- | :--- | :--- | :--- | :--- |
| **First Contentful Paint (FCP)** | **3.3 s** | 🔴 Nguy hiểm | < 1.8 s | Thời gian màn hình bắt đầu xuất hiện những nét vẽ đầu tiên |
| **Largest Contentful Paint (LCP)** | **7.7 s** | 🔴 Nguy hiểm | < 2.5 s | Thời gian phần tử nội dung lớn nhất (ảnh đại diện sản phẩm) hiển thị |
| **Total Blocking Time (TBT)** | **1,330 ms** | 🔴 Nguy hiểm | < 200 ms | Tổng thời gian luồng chính (Main Thread) bị khóa bởi JavaScript |
| **Speed Index (SI)** | **4.3 s** | 🟡 Cảnh báo | < 3.4 s | Tốc độ load phần nhìn thấy của trang |
| **Cumulative Layout Shift (CLS)** | **0.002** | 🟢 Đạt chuẩn | < 0.1 | Mức độ dịch chuyển giao diện khi đang load |

### 🚨 Các Cảnh báo Đỏ từ Lighthouse:
1. **Render-blocking requests:** Tiết kiệm dự tính **330 - 530 ms** nếu loại bỏ tài nguyên chặn render.
2. **Forced reflow:** Phát hiện các tác vụ ép trình duyệt tính toán lại Layout ngay trong thời gian khởi tạo (Layout Thrashing).
3. **LCP request discovery:** Trình duyệt phát hiện ảnh LCP quá muộn trong chuỗi thác tải (waterfall).

---

## II. PHÂN TÍCH CHUYÊN SÂU NGUYÊN NHÂN GÂY TRÌ TRỆ 3S ĐẦU

Qua đối chiếu mã nguồn thực tế tại phân hệ Frontend (`app.html`, `+layout.svelte`, `+page.svelte`), chúng tôi xác định được **3 nút thắt cổ chai hệ thống (Performance Bottlenecks)** cốt lõi:

### 1. Hiệu ứng "Thác Tải Kép" (Double-Hop Dynamic Imports) của Trang Chi Tiết Sản Phẩm
Tại `src/routes/(client)/(store)/[slug]/+page.svelte` (dòng 130-159), để thực hiện code-splitting tối ưu dung lượng tải cho thiết bị, dự án đang áp dụng Dynamic Import thủ công trong `onMount`:
```javascript
onMount(async () => {
  if (data.isMobile) {
    const { default: ProductDetailMobile } = await import('$lib/components/storefront/product-detail/MainDetail/Mobile.svelte');
    activeComponent = ProductDetailMobile;
  } else {
    const { default: ProductDetailDesktop } = await import('$lib/components/storefront/product-detail/MainDetail/Desktop.svelte');
    activeComponent = ProductDetailDesktop;
  }
});
```
* **Hệ quả cực kỳ nghiêm trọng:**
  1. Trình duyệt tải `index.html` trắng ➔ Tải JS khởi tạo của SvelteKit.
  2. SvelteKit chạy quá trình hydration và gọi `onMount` của `+page.svelte`.
  3. Trình duyệt phát hiện ra lệnh `import()` mới, bắt đầu gửi request thứ hai để tải file chunk JS của `Desktop.svelte` hoặc `Mobile.svelte`.
  4. Sau khi chunk JS thứ hai tải xong và thực thi, Svelte mới thực sự render phần tử ảnh sản phẩm (LCP).
  * ➔ **Đây là chuỗi thác tải (Waterfall Chain) có độ trễ cực dài.** Trình duyệt hoàn toàn mù tịt về sự tồn tại của ảnh sản phẩm cho đến khi block JS thứ hai được tải và biên dịch hoàn tất, đẩy LCP lên mức **7.7 giây**.

### 2. Sự bất lực của Dynamic Preload trong Kiến trúc SPA (CSR)
Trong `+page.svelte` (dòng 210-240), mã nguồn có cố gắng tối ưu hóa LCP bằng cách chèn thẻ `<link rel="preload">` thông qua `<svelte:head>`:
```svelte
<svelte:head>
  {#if productData?.product}
    <link rel="preload" as="image" href={preloadUrl} fetchpriority="high" />
  {/if}
</svelte:head>
```
* **Tại sao không có tác dụng?** Vì hệ thống storefront đang hoạt động dưới dạng **Single-Page Application (SPA)** thuần túy (`adapter-static` với fallback `index.html`). 
* Khi người dùng truy cập trang lần đầu, Caddy chỉ trả về đúng file `index.html` tĩnh, rỗng không hề có thẻ preload này. Thẻ preload này chỉ được Svelte tiêm vào `head` thông qua JavaScript **sau khi đã tải xong đợt JS đầu tiên**. Một khi JS thực thi xong mới chèn thẻ preload, trình duyệt đã tự động bắt đầu tải các tài nguyên khác, khiến preload động mất sạch giá trị ưu tiên băng thông ban đầu.

### 3. Tải chồng chất JS & Khóa luồng chính (TBT: 1,330ms)
Trang web đang chịu tải CPU quá mức ngay tại 3 giây đầu tiên do:
* **ONNX Runtime Web (`/wasm/ort.min.js`) loaded globally:** File này (102 KB gzipped, >1 MB uncompressed) được định nghĩa là script chạy đồng bộ/hoãn (`defer`) ngay trong `app.html` (dòng 167) cho tất cả các trang, ngay cả khi người dùng chỉ xem sản phẩm mà không hề mở Chat Helen. Việc trình duyệt phải phân tích và tải bộ máy AI này tạo ra một Long Task lớn chặn luồng chính.
* **Biometric & Ads Telemetry Click Protection:** Trình bảo vệ Google Ads (`+layout.svelte` dòng 132-304) ngay khi phát hiện `gclid` sẽ đăng ký hàng loạt Listener chặn sự kiện chuột (`mousemove`, `touchmove`, `scroll`) chạy liên tục trên luồng chính, gây hiện tượng **Forced Reflow / Layout Thrashing** khi tính toán `window.scrollY` và các thông số telemetry.
* **Immediate Analytics Fetch & Third-party Injections:** `app.html` gọi `fetch('/api/v1/client/settings/primary', {cache: 'no-store'})` đồng bộ lúc phân tích HTML, sau đó ngay lập tức chèn script GTM, GA4, FB Pixel ngay trong đầu trang, tranh chấp băng thông mạng cực kỳ khốc liệt với các file CSS/JS giao diện chính.

---

## III. BIỆN LUẬN PHƯƠNG ÁN XỬ LÝ CHI TIẾT (ARCHITECTURAL OPTIONS)

Để giải quyết triệt để trì trệ 3 giây đầu tiên mà không phá vỡ quy chuẩn thiết quân luật Elite V2.2, chúng tôi đề xuất 4 giải pháp kiến trúc đồng bộ:

### 🚀 Phương án 1: Phá vỡ "Thác Tải Kép" bằng Compile-time Device Switching (KHUYÊN DÙNG CHI PHÍ THẤP)
Thay vì dynamic import lồng trong `onMount`, chúng ta cấu hình lại SvelteKit 5 để compiler có thể chuẩn bị sẵn preload cho các chunk thông qua cơ chế phân tách tầng giao diện tĩnh tại `+page.svelte`.
* **Kỹ thuật:** 
  1. Loại bỏ hoàn toàn dynamic import thủ công trong `onMount` tại `+page.svelte`.
  2. Chuyển đổi import thành static import cho cả hai phiên bản Desktop/Mobile hoặc sử dụng Svelte 5 Dynamic Component Resolver thông thường để trình đóng gói Vite đưa các file này vào danh sách `modulepreload` trực tiếp của entry point. Trình duyệt sẽ song song tải cả hai phiên bản nhẹ hơn nhiều so với việc chờ `onMount` mới đi fetch.
  3. Hoặc tận dụng cơ chế `+page.ts` load function để quyết định luồng tải trước khi render.
* **Lợi ích:** FCP và LCP sẽ giảm ngay lập tức từ **3s - 7.7s xuống dưới 1.5s - 2.5s** do toàn bộ file JS chính được kéo song song trong đợt đầu tiên.

### ⚡ Phương án 2: Tối ưu hóa tải theo nhu cầu (On-Demand Bootstrapping) cho AI & Analytics
* **Kỹ thuật:**
  1. **Trì hoãn ONNX Runtime:** Xóa hoàn toàn `<script src="/wasm/ort.min.js">` khỏi `app.html`. Chỉ thực hiện chèn thẻ script này hoặc tải động thư viện ONNX/VAD **khi và chỉ khi người dùng click vào nút FAB** để mở hộp thoại Chat với Helen lần đầu tiên (Lazy AI Loading).
  2. **Trì hoãn Telemetry Protection:** Di chuyển toàn bộ logic ghi nhận hành vi quảng cáo và telemetry từ `onMount` tức thì sang một hàm chạy trong `requestIdleCallback()` hoặc trì hoãn tối thiểu 2.5 giây sau khi trang đã ổn định FCP.
  3. **Trì hoãn Analytics Injections:** Chuyển đổi logic tiêm các mã theo dõi GTM, GA4, FB Pixel từ đồng bộ lúc parse đầu trang sang cơ chế `setTimeout(() => inject..., 1500)` để ưu tiên tuyệt đối băng thông cho CSS/JS layout của sản phẩm.
* **Lợi ích:** **Total Blocking Time (TBT) sẽ giảm từ 1.3s xuống dưới 150ms** (Mức Xanh Hoàn Hảo), trang phản hồi cực kỳ mượt mà.

### 🌐 Phương án 3: Dynamic Edge Preload Headers tại Caddy (Tối ưu hóa LCP cho SPA)
Vì chúng ta đang dùng SPA thuần phục vụ bởi Caddy, trình duyệt không thể biết URL ảnh sản phẩm LCP để tải sớm. Chúng ta có thể tận dụng chính Caddy để tiêm Header `Link` tải sớm mà không cần chạy server Node.js cồng kềnh.
* **Kỹ thuật:**
  * Tại cấu hình `Caddyfile`, đối với route chi tiết sản phẩm `/miccosmo-*`, Caddy sẽ tự động tiêm thêm HTTP Response Header:
    ```caddy
    header Link "</uploads/2026/04/...webp>; rel=preload; as=image; fetchpriority=high"
    ```
    *(Tuy nhiên, do ảnh sản phẩm là động theo database, giải pháp tối ưu hơn là backend cung cấp một API hoặc Caddy tích hợp nhẹ với một luồng kiểm tra CDN nhanh để tự động bổ sung preload header).*
* **Lợi ích:** Trình duyệt phát hiện ảnh sản phẩm ngay lập tức tại mili-giây đầu tiên khi nhận được phản hồi HTTP, giảm LCP xuống ngang bằng FCP.

### 🎨 Phương án 4: Ổn định hóa Skeleton giao diện (Layout Stability & Reflow Fix)
* **Kỹ thuật:**
  1. Thay thế skeleton xoay đơn giản bằng skeleton cấu trúc thật (chứa khung ảnh vuông sản phẩm, tiêu đề giả, nút mua giả) với chiều cao cố định (`aspect-ratio` giữ chỗ).
  2. Tránh tuyệt đối việc thay đổi kích thước phần tử DOM hoặc đọc các thuộc tính gây reflow như `element.getBoundingClientRect()` hay `window.scrollY` trong 2 giây đầu tiên trừ khi bắt buộc.
* **Lợi ích:** Loại bỏ hoàn toàn cảnh báo **Forced reflow** và đảm bảo điểm CLS tiệm cận tuyệt đối **0.000**.

---

## IV. ĐỀ XUẤT TIẾN ĐỘ THỰC THI (PROPOSAL)

Để đạt hiệu quả tối ưu nhất với chi phí vận hành an toàn cho RAM VPS (2GB), chúng tôi đề xuất thực hiện theo 2 bước:

1. **Bước 1 (Ưu tiên Cao - Fix TBT & FCP):** 
   * Trì hoãn tải ONNX Runtime và Analytics trackers sang cơ chế Lazy-load / Idle-callback.
   * Chuyển đổi Ads Protection Telemetry hoạt động ở chế độ phi chặn (Non-blocking).
2. **Bước 2 (Tối ưu hóa LCP & CRO):**
   * Refactor cấu trúc Dynamic Component tại trang chi tiết sản phẩm, gom nhóm các chunk giao diện chính để loại bỏ thác tải kép.
   * Thiết lập Kích thước Skeleton chuẩn để triệt tiêu Forced Reflow.

*Báo cáo được đệ trình lên Sếp duyệt để chuyển sang giai đoạn thực thi mã nguồn.*
