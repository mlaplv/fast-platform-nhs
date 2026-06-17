# Phân tích kỹ thuật chuyên sâu: Forced Reflow & LCP JS Injection

Dựa theo báo cáo lỗi của hệ thống, nguyên nhân gốc rễ xuất phát từ kiến trúc "Client-Side Dynamic Router" kết hợp với vòng đời `$effect` của Svelte 5. Dưới đây là phân tích chi tiết cho 2 vấn đề:

## 1. Vấn đề Forced Reflow (52ms) tại `DExgKdPe.js`
- **Bản chất file `DExgKdPe.js`**: Đây là chunk file JS được trình biên dịch tạo ra, chứa logic của `MobileHero.svelte` (và các component Funnel).
- **Quy trình gây lỗi**: Khi Svelte mount `MobileHero`, khối `$effect` (chứa logic cuộn Variant) được kích hoạt. Svelte 5 thực thi `$effect` **ngay lập tức** sau khi cập nhật DOM (Hành động Ghi/Write). Tuy nhiên, bên trong effect lại có lệnh đọc `variantScroller.scrollLeft` (Hành động Đọc/Read).
- **Hệ quả**: Trình duyệt bị ép phải tính toán lại toàn bộ Layout đồng bộ (Synchronous Layout) ngay trong khung hình đó để trả về vị trí Scroll mới nhất thay vì được phép vẽ ra màn hình. Quá trình này gây lãng phí 52ms.
- **Trạng thái**: Đã được xử lý ở bước trước bằng cách bọc lệnh Đọc vào `requestAnimationFrame`, phá vỡ chuỗi đồng bộ Ghi ➡️ Đọc. (Đang chờ đồng bộ lên VPS).

### 2. Tabbed Inspiration & CRO Panel (`ScriptEditorWorkspace.svelte`)
*   **Unified Tab Panel**: Replaced the two separate, blocky collapsible drop components (`CompetitiveIntel` and `LandingPageMatchCard`) with an elegant, unified tabbed container to save vertical space and maintain high-density aesthetics.
*   **Neon Accent Styling**: Designed high-contrast tabs (Yellow accent for "Phân tích đối thủ", Cyan accent for "Tối ưu Landing Page") that match the design theme, with custom Svelte transition transitions (`slide` and `fade`).
*   **Bespoke Export & Delete buttons**: Replaced the entire bottom/header playback control bar with clean, dedicated `EXPORT MD` and `Delete` action buttons in the script header.
*   **Header Prompt Action**: Added a direct "Mở Prompt / Đóng Prompt" toggle button.

### 2.5. AI System Prompt Alignment (`prompts_registrar.py`)
*   **Aligned with Copywriting-First Schema**: Updated the backend system prompt component `VIDEO_SCRIPTWRITER` to remove references to the deprecated `Image Prompt` (Gợi ý tạo ảnh).
*   **Directorial Notes generation**: Instructed the Gemini model to write details for `scene_notes` (Ghi chú đạo diễn), defining camera motion instructions (e.g. Pan, Zoom, Tilt, Dolly) and acting cues instead of legacy image prompts.

## 2. Vấn đề LCP Request Discovery & "fetchpriority=high should be applied"
Báo cáo Lighthouse chỉ trích `DExgKdPe.js` là nguyên nhân chậm trễ LCP, mặc dù ta đã thiết lập Preload. Lý do cốt lõi nằm ở **kiến trúc Elite Code Splitting** trong `+page.svelte`.

- **Cơ chế SSR hiện tại**: Việc quyết định load component nào (`MobileFunnelManager` hay `Desktop`) được thực thi bên trong `$effect` của `[slug]/+page.svelte`. Vì `$effect` chỉ chạy trên trình duyệt (Client-side), máy chủ (SSR) thực chất KHÔNG render HTML của `MobileHero`. Máy chủ chỉ gửi xuống `<Skeleton>` và một thẻ `<img ssrHeroImage>` mồi.
- **Tại sao Lighthouse báo lỗi?**: Khi Svelte chạy trên Client (thông qua file `DExgKdPe.js`), nó tải `MobileHero` về, **phá hủy** thẻ `<img ssrHeroImage>` ban đầu và **bơm** thẻ `<img>` thật của MobileHero vào DOM. 
- Lighthouse truy vết phần tử lớn nhất trên màn hình (LCP node) và phát hiện nó được sinh ra động bằng JavaScript (`DExgKdPe.js`). Theo tiêu chuẩn Web Vitals, một phần tử LCP "đạt chuẩn" phải nằm sẵn trong cây HTML gốc để trình duyệt quét (Pre-parse) ngay từ byte đầu tiên. Vì ảnh của ta bị framework thay thế bằng JS, Lighthouse phạt điểm và cảnh báo "Image not discoverable from HTML".

## Hướng giải quyết tận gốc (Nếu cần xanh 100% Lighthouse)
- **Tối ưu UX/Tốc độ thực tế**: Giải pháp `<link rel="preload">` ta vừa làm đã xử lý tốt tốc độ tải thực tế (Field Data). Lỗi này chỉ là điểm trừ trên hệ thống lab test của Lighthouse do cơ chế Hydration của framework.
- **Xóa sổ cảnh báo**: Để xóa hoàn toàn lỗi này, ta bắt buộc phải thay đổi cơ chế load động trong `+page.svelte`. Thay vì dùng `$effect` (Client-only router), ta phải SSR trực tiếp component (dựa trên thông tin User-Agent từ Server) để HTML trả về chứa sẵn `MobileHero.svelte` thật. Mọi thuộc tính `fetchpriority="high"` khi đó sẽ hiển diện ngay lập tức trong HTML gốc.
