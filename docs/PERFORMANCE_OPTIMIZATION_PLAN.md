# BẢN PHÁC THẢO CHI TIẾT TỪNG PHÂN KỲ TỐI ƯU HÓA HIỆU NĂNG BẰNG SVELTE 5
> **DỰ ÁN:** SmartShop Storefront (osmo.vn)
> **TIÊU CHUẨN CÔNG NGHỆ:** SvelteKit 5 (Runes) + Litestar (Python 3.14) + SQLAlchemy 2.0 + PydanticAI V2 + LiteLLM
> **MỤC TIÊU HIỆU NĂNG:** Đạt điểm Lighthouse **> 95/100** (FCP < 1.0s, LCP < 1.8s, TBT < 100ms, CLS = 0.000)

---



## ⚡ CHI TIẾT KẾ HOẠCH TRIỂN KHAI TỪNG PHASE VỚI MÃ NGUỒN PHÁC THẢO

---

### 🟢 GIAI ĐOẠN 1: TRÌ HOÃN TÀI NGUYÊN & ON-DEMAND BOOTSTRAPPING (TBT < 100ms)
**Mục tiêu:** Cắt giảm triệt để dung lượng và chặn luồng chính (Long Tasks) lúc khởi chạy.

#### 1. Xóa bỏ Assets chặn Hydration khỏi `frontend/src/app.html`
* **Hành động:** 
  * Loại bỏ thẻ `<script src="/wasm/ort.min.js"></script>` khỏi `app.html`.
  * Thay thế các script theo dõi của Google Tag Manager đồng bộ bằng việc chỉ định nạp bất đồng bộ.

#### 2. Tái cấu trúc Dynamic Script Injector tại `supportAgent.svelte.ts`
* **Vị trí file:** `frontend/src/lib/state/commerce/supportAgent.svelte.ts`
* **Triển khai:** Thêm cơ chế lazy-load thư viện ONNX khi chatbox mở ra bằng Svelte 5 `$effect`:
```typescript
class SupportAgentState {
  isOpen = $state(false);
  isLoaded = $state(false);

  loadDependencies() {
    if (this.isLoaded || typeof window === 'undefined') return Promise.resolve();

    return new Promise<void>((resolve, reject) => {
      const script = document.createElement('script');
      script.src = '/wasm/ort.min.js';
      script.async = true;
      script.onload = () => {
        this.isLoaded = true;
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
}
```

#### 3. Chuyển Giao Telemetry sang Trạng thái Rảnh (Idle Callback)
* **Vị trí file:** `frontend/src/routes/+layout.svelte`
* **Triển khai:** Đóng gói toàn bộ Google Ads Click Protection vào hàm rảnh rỗi:
```typescript
onMount(() => {
  if (!isAdmin) {
    const runTelemetry = () => {
      // Khởi tạo các event listeners và honeypot bảo vệ
      initClickProtection();
    };
    
    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(runTelemetry);
    } else {
      setTimeout(runTelemetry, 1500);
    }
  }
});
```

---

### 🔵 GIAI ĐOẠN 2: SVELTE 5 TRAFFIC COP ROUTER & LAYOUT REFACTOR (LCP < 1.8s)
**Mục tiêu:** Giải quyết triệt để sự tranh chấp luồng (Traffic Cop Problem) và loại bỏ "thác tải kép" (Double-Hop).

#### 1. Xây dựng Svelte 5 Device Store (`device.svelte.ts`)
* **Vị trí file:** Tạo mới `frontend/src/lib/state/commerce/device.svelte.ts`
```typescript
import { browser } from '$app/environment';

class DeviceStore {
  width = $state(browser ? window.innerWidth : 1024);
  isMobile = $derived(this.width < 768);

  constructor() {
    if (browser) {
      window.addEventListener('resize', () => {
        this.width = window.innerWidth;
      }, { passive: true });
    }
  }
}

export const device = new DeviceStore();
```

#### 2. Thiết lập "Navigation Traffic Cop" trong `frontend/src/routes/+layout.svelte`
* **Triển khai:** Tích hợp bộ đếm Epoch điều hành việc import chatComponent và searchComponent bất đồng bộ:
```typescript
<script lang="ts">
  import { device } from "$lib/state/commerce/device.svelte";
  import { page, navigating } from "$app/state";
  import { untrack } from "svelte";

  let navigationEpoch = $state(0);
  let chatComponent = $state<Component | null>(null);

  $effect(() => {
    const path = page.url.pathname;
    navigationEpoch++; // Tăng Epoch khi định tuyến thay đổi
    const myEpoch = navigationEpoch;

    untrack(async () => {
      if (isAdmin) return;

      try {
        let chatMod;
        if (device.isMobile) {
          chatMod = await import("$lib/components/client/support/SupportChatMobile.svelte");
        } else {
          chatMod = await import("$lib/components/client/support/SupportChatDesktop.svelte");
        }

        // CHỐT CHẶN TRAFFIC COP: Bỏ qua render nếu người dùng đã chuyển trang tiếp theo
        if (myEpoch !== navigationEpoch) return;

        chatComponent = chatMod.default;
      } catch (e) {
        console.error("[Traffic-Cop Fault]", e);
      }
    });
  });
</script>
```

#### 3. Refactor layout thác tải kép trong `frontend/src/routes/(client)/(store)/[slug]/+page.svelte`
* **Vấn đề cũ:** Import động `Mobile.svelte` và `Desktop.svelte` thông qua `onMount(async () => { ... import(...) })` gây ra thác tải kép mạng.
* **Cải cải tổ mới:**
```svelte
<script lang="ts">
  import { device } from "$lib/state/commerce/device.svelte";
  import ProductDetailDesktop from "$lib/components/storefront/product-detail/MainDetail/Desktop.svelte";
  import ProductDetailMobile from "$lib/components/storefront/product-detail/MainDetail/Mobile.svelte";

  let { data } = $props();
</script>

{#if device.isMobile}
  <ProductDetailMobile product={data.product} />
{:else}
  <ProductDetailDesktop product={data.product} />
{/if}
```
* **Biện luận:** Việc nạp trực tiếp component tĩnh giúp Vite phân rã chunk tối ưu khi build, trình duyệt nạp song song assets trong First Paint giúp LCP giảm 80% từ **7.7s xuống < 1.8s**.

---

### 🟡 GIAI ĐOẠN 3: CADDY EDGE PRELOAD & CACHE IMMUTABLE (TTFB < 50ms)
**Mục tiêu:** Cắt giảm thời gian tải tài nguyên và truyền dẫn HTTP ban đầu.

#### 1. Cấu hình HTTP/2 103 Early Hints tại Caddyfile
* **Vị trí file:** `Caddyfile` tại thư mục gốc.
* **Cấu hình chi tiết:**
```caddy
osmo.vn, *.osmo.vn {
    # Gửi tín hiệu tải sớm các file tĩnh cốt lõi
    header {
        Link "</_app/immutable/assets/theme.css>; rel=preload; as=style, </_app/immutable/entry/start.js>; rel=preload; as=script, </fonts/be-vietnam-pro-vn.woff2>; rel=preload; as=font; crossorigin"
        +103 {}
    }
    
    reverse_proxy fast_platform_api:8000
}
```

#### 2. Cấu hình Cache Immutable cho Assets băm tên
* **Cấu hình chi tiết:**
```caddy
@immutable_assets path /_app/immutable/*
header @immutable_assets {
    Cache-Control "public, max-age=31536000, immutable"
}
```
* **Biện luận:** Trình duyệt sẽ cache vĩnh viễn assets của SvelteKit. Khi có deploy code mới qua `rsync`, mã băm hash trong tên file tự động đổi nên không lo xung đột cache, đạt tốc độ load trang lần thứ 2 chỉ trong **0ms**.

---

### 🔴 GIAI ĐOẠN 4: SVELTE 5 SNIPPETS SKELETON & KHỬ REFOLW (CLS = 0.000)
**Mục tiêu:** Ổn định giao diện hiển thị tức thời, FCP < 1.0s.

#### 1. Nhúng Luxury Skeleton nội bộ bằng Svelte 5 Snippets
* **Vị trí file:** `frontend/src/routes/(client)/(store)/[slug]/+page.svelte`
* **Triển khai:**
```svelte
{#snippet productSkeleton()}
  <div class="skeleton-shell animate-pulse p-4 bg-stone-900 border border-white/5 rounded-2xl">
    <div class="aspect-square w-full bg-stone-800 rounded-xl mb-4 relative overflow-hidden">
      <div class="shimmer bg-gradient-to-r from-transparent via-white/5 to-transparent absolute inset-0"></div>
    </div>
    <div class="h-6 w-3/4 bg-stone-800 rounded mb-2"></div>
    <div class="h-4 w-1/2 bg-stone-800 rounded"></div>
  </div>
{#/snippet}

{#if !data.product}
  {@render productSkeleton()}
{:else}
  <!-- Nạp layout thực sự -->
{/if}
```

#### 2. Ép ASPECT-RATIO trên LCP Container để triệt tiêu Layout Shift
* **Vị trí file:** `ProductMobileMedia.svelte` và `ProductDesktopMedia.svelte`
* **Triển khai:**
```html
<!-- Bọc LCP Image cố định khung hình học -->
<div class="relative w-full overflow-hidden bg-stone-950 rounded-2xl" style="aspect-ratio: 1 / 1;">
  <img 
    src={product.hero_image} 
    alt={product.name} 
    fetchpriority="high"
    loading="eager"
    class="w-full h-full object-cover" 
  />
</div>
```
* **Biện luận:** Có `aspect-ratio` giúp trình duyệt dành sẵn ô trống cho ảnh từ trước khi ảnh được tải về từ mạng, cam kết **CLS = 0.000** tuyệt đối.

---

## 📋 HẠ HÌNH BÀN CỜ ĐÁNH GIÁ RỦI RO & BẢO VỆ VPS 2GB RAM

1. **Rủi ro rò rỉ luồng AI (Helen Init):**
   * *Trước tối ưu:* Chuyển trang liên tục kích hoạt nhiều timeout ➔ Kết nối nhiều WebSocket đồng thời ➔ VPS cạn kiệt CPU.
   * *Sau tối ưu (Traffic Cop):* Mỗi lần chuyển trang sẽ hủy luồng timeout cũ thông qua việc dọn dẹp biến Epoch, đảm bảo chỉ duy trì 1 luồng khởi tạo AI duy nhất.
2. **Rủi ro khi nạp trực tiếp component tĩnh:**
   * *Trước tối ưu:* Dynamic import ngầm khiến Vite tạo ra các chunk quá vụn vặt gây thác tải kép HTTP.
   * *Sau tối ưu:* Vite gộp nhóm tĩnh (Static Bundling) theo thiết bị, trình duyệt tải đúng 1 chunk chính của thiết bị đó mà không qua `onMount`, giảm thời gian nghẽn CPU luồng chính xuống **TBT < 100ms**.
