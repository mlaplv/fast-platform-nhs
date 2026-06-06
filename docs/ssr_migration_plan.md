# Kế hoạch chuyển đổi SPA → SSR (SvelteKit & adapter-node)

Tài liệu này lưu trữ toàn bộ kế hoạch, đánh giá kỹ thuật và các bước thực hiện chi tiết để chuyển đổi storefront của hệ thống từ Single Page Application (SPA) hiện tại sang Server-Side Rendering (SSR).

---

## 1. Đánh giá hiện trạng & Lý do tối ưu

### Kiến trúc hiện tại (SPA + Python seo-render)
*   **Cấu trúc**: Sử dụng `@sveltejs/adapter-static` để build ra các file tĩnh (`dist/`), được phục vụ trực tiếp qua Caddy Server.
*   **SEO cho Bot**: Caddy phát hiện crawler (Googlebot, Facebook, Zalo,...) thông qua User-Agent và chuyển hướng qua `/seo-render` (Python backend) để render HTML tĩnh có cấu trúc metadata và JSON-LD.
*   **Trải nghiệm người dùng**: Người dùng thật nhận về HTML trống, chờ tải JS bundle về client rồi mới hydrate nội dung.

### Nhược điểm của kiến trúc hiện tại cần khắc phục bằng SSR
1.  **Chỉ số Google CrUX (Chrome User Experience Report)**: Google đo tốc độ LCP/FCP từ trải nghiệm thực tế của người dùng Chrome. SPA tải chậm hơn ở FCP/LCP trên thiết bị di động của người dùng thật → ảnh hưởng gián tiếp đến xếp hạng SEO.
2.  **LCP Discovery Delay**: Trình duyệt của người dùng không thể biết trước ảnh LCP (hero image) để tải sớm (preload) cho đến khi Svelte hoàn tất mount phần tử `<img>`.
3.  **Tốn tài nguyên render 2 đầu**: Duy trì cả code Svelte storefront và code render HTML (Jinja2/Python) ở backend gây trùng lặp logic metadata/SEO.

---

## 2. Kế hoạch triển khai chi tiết (6 Phases)

### Phase 1: Thay đổi Hạ tầng (adapter-static → adapter-node)

#### 1. Thay đổi SvelteKit adapter
Trong file [svelte.config.js](file:///media/lv/data/fast-platform-core/frontend/svelte.config.js):
```javascript
import adapter from '@sveltejs/adapter-node'; // Thay thế adapter-static
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const config = {
    preprocess: vitePreprocess(),
    kit: {
        inlineStyleThreshold: 1048576,
        adapter: adapter({
            out: 'build', // Thư mục output build cho Node
            precompress: true // Nén sẵn gzip/brotli
        })
    }
};

export default config;
```

#### 2. Cập nhật `package.json`
*   Xóa: `"@sveltejs/adapter-static"`
*   Thêm: `"@sveltejs/adapter-node": "^3.0.0"` (hoặc phiên bản tương thích SvelteKit hiện tại)

#### 3. Điều chỉnh Caddyfile
Thay thế việc phục vụ file tĩnh bằng reverse proxy tới Node.js app:
```caddy
# Trước đây:
# root * /app/frontend/dist
# file_server { precompressed br gzip }
# try_files {path} /index.html

# Sau khi chuyển đổi sang SSR:
@frontend_host host {$APP_DOMAIN}
handle @frontend_host {
    # 1. Vẫn cho phép serve trực tiếp static assets từ SvelteKit build để tối ưu hiệu năng
    @static_assets path /_app/* /favicon.svg /manifest.json
    handle @static_assets {
        root * /app/frontend/build/client
        file_server {
            precompressed br gzip
        }
    }

    # 2. Reverse proxy tất cả request route động tới Node.js SSR process
    handle {
        reverse_proxy localhost:3000
    }
}
```

---

### Phase 2: Cấu hình per-route (Bật SSR storefront, giữ SPA admin)

Để tránh rủi ro phá vỡ trang quản trị Admin (vốn chứa nhiều logic phức tạp phụ thuộc vào browser API):

1.  **Xóa `export const ssr = false`** khỏi root [+layout.ts](file:///media/lv/data/fast-platform-core/frontend/src/routes/+layout.ts). SvelteKit mặc định sẽ hiểu là `ssr = true`.
2.  **Khóa cứng chế độ SPA cho Admin** bằng cách chỉnh sửa hoặc tạo file [(admin)/+layout.ts](file:///media/lv/data/fast-platform-core/frontend/src/routes/(admin)/+layout.ts):
    ```typescript
    export const ssr = false;
    export const prerender = false;
    ```

---

### Phase 3: Xử lý dữ liệu động & Browser API Guard

Khi chạy SSR, toàn bộ route loader (`+page.ts`, `+layout.ts`) sẽ chạy song song trên cả Server và Client. Các lỗi crash thường gặp là do truy cập trực tiếp vào biến môi trường trình duyệt.

#### 1. Tránh truy cập trực tiếp `window`, `document`, `localStorage`, `sessionStorage`
Các logic đọc cache từ client phải được trì hoãn đến khi mount, hoặc bọc trong block kiểm tra:
```typescript
import { browser } from '$app/environment';

if (browser) {
    const cached = sessionStorage.getItem('primary_config');
}
```

#### 2. Tách loader sang `*.server.ts` khi cần
Nếu logic lấy dữ liệu phụ thuộc vào Cookies (ví dụ: xác thực, lấy thông tin user), chuyển đổi từ `+layout.ts` sang `+layout.server.ts` để đọc trực tiếp từ `locals` đã được phân tích bởi `hooks.server.ts`.

Ví dụ: Tạo [+layout.server.ts](file:///media/lv/data/fast-platform-core/frontend/src/routes/+layout.server.ts):
```typescript
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = ({ locals }) => {
    return {
        isMobile: locals.isMobile ?? false,
        tenant: locals.tenant ?? 'storefront',
        user: locals.user ?? null
    };
};
```

---

### Phase 4: Dọn dẹp mã nguồn dư thừa (Code Cleanup)

Khi có SSR, cấu trúc DOM được tạo sẵn ở server, các giải pháp "đắp vá" của SPA trước đây cần được loại bỏ để tối ưu hiệu năng:

#### 1. Xóa logic Skeleton loading tĩnh & Spinner toàn trang
*   Xóa phần tử `#initial-loader` và skeleton loader trong [app.html](file:///media/lv/data/fast-platform-core/frontend/src/app.html).
*   Xóa hàm `hideSkeleton()` và sự kiện `app-ready` trong root [+layout.svelte](file:///media/lv/data/fast-platform-core/frontend/src/routes/+layout.svelte).

#### 2. Loại bỏ lazy-import của các core components
Trong root [+page.svelte](file:///media/lv/data/fast-platform-core/frontend/src/routes/+page.svelte), thay vì dùng dynamic import trong `onMount`:
```typescript
// Trước đây:
// onMount(async () => {
//    storefrontComponent = (await import('$lib/components/storefront/StorefrontHome.svelte')).default;
// })

// Đổi thành static import trực tiếp:
import StorefrontHome from '$lib/components/storefront/StorefrontHome.svelte';
import SeoHead from '$lib/components/storefront/seo/SeoHead.svelte';
```
Điều này giúp server có thể render được HTML đầy đủ ngay lập tức khi người dùng truy cập.

---

### Phase 5: Tối ưu hóa LCP (Preload hoạt động gốc)

Khi SSR chạy, trình duyệt nhận được thẻ preload ngay trong document đầu tiên. Giữ nguyên đoạn mã sau trong `+page.svelte` của chi tiết sản phẩm:
```html
<svelte:head>
    {#if data.isMobile}
        <link 
            rel="preload" 
            as="image" 
            imagesrcset="{src412} 1x, {src600} 1.5x, {src800} 2x" 
            fetchpriority="high" 
        />
    {:else}
        <link 
            rel="preload" 
            as="image" 
            href={preloadUrl} 
            fetchpriority="high" 
        />
    {/if}
</svelte:head>
```
Lighthouse sẽ tự động ghi nhận đạt điểm tối đa cho phần phát hiện ảnh LCP.

---

## 3. Quy trình xác thực và kiểm thử (Verification)

Sau khi hoàn tất cài đặt Node.js SSR trên môi trường phát triển:

1.  **Build thử nghiệm**:
    ```bash
    npm run build
    ```
    Đảm bảo quá trình biên dịch không gặp lỗi "window is not defined".
2.  **Khởi chạy server cục bộ (để test trước khi deploy)**:
    ```bash
    PORT=3000 node build/index.js
    ```
3.  **Kiểm tra mã nguồn HTML**:
    *   **Khi kiểm tra ở local (máy dev):**
        ```bash
        curl -s http://localhost:3000/san-pham-vi-du | grep -i "preload"
        ```
    *   **Khi kiểm tra trực tiếp trên production (osmo.vn) sau khi deploy:**
        ```bash
        curl -s https://osmo.vn/san-pham-vi-du | grep -i "preload"
        ```
    HTML trả về bắt buộc phải chứa thẻ `<link rel="preload" ...>` và các thẻ SEO `<title>`, `<meta>`.
4.  **Kiểm tra trang Admin**:
    Truy cập thử các link admin để đảm bảo SPA vẫn hoạt động bình thường, không bị ảnh hưởng bởi môi trường SSR của storefront.

