<script lang="ts">
  import { goto } from "$app/navigation";
  import { slugify, formatCurrency, trimProductName } from "$lib/utils/format";
  import { onMount, onDestroy } from "svelte";
  import { fly, fade, scale } from "svelte/transition";
  import { backOut } from "svelte/easing";
  import type { ReviewStats, Product as RealProduct } from "$lib/types";
  import VerificationCenter from "../product-detail/shared/VerificationCenter.svelte";
  import { portal } from "$lib/core/actions/portal";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import X from "@lucide/svelte/icons/x";

  interface Product extends Partial<RealProduct> {
    id: string;
    name: string;
    price: number;
    image: string;
    sales?: number;
    originalPrice?: number;
  }

  interface Props {
    product: Product | null;
  }

  let { product = null }: Props = $props();
  let stats = $state<ReviewStats | null>(null);
  let showVerificationModal = $state(false);

  // Countdown Logic (Elite V2.2: Flow from metadata if available)
  let seconds = $state(
    Number(product?.metadata?.flash_sale_seconds) || 15 * 3600 + 54 * 60 + 16,
  );
  let timer: ReturnType<typeof setInterval>;

  const hh = $derived(String(Math.floor(seconds / 3600)).padStart(2, "0"));
  const mm = $derived(
    String(Math.floor((seconds % 3600) / 60)).padStart(2, "0"),
  );
  const ss = $derived(String(seconds % 60).padStart(2, "0"));

  // Derived Product Data (Elite V2.2: Sanitized & Calculated)
  const displayProduct = $derived(() => {
    if (!product) return null;

    // Support proper DB schema: price is the OLD price if there's a discount.
    // Fallback: If originalPrice is passed from parent or is equal to current price, make it viral.
    const currentPrice =
      product.discountPrice || product.discount_price || product.price;
    let originalPrice = product.originalPrice || product.price;

    if (originalPrice <= currentPrice) {
      originalPrice = currentPrice * 1.55;
    }

    const discountPercent = Math.round(
      ((originalPrice - currentPrice) / originalPrice) * 100,
    );

    return {
      ...product,
      name: trimProductName(product.name),
      price: currentPrice,
      originalPrice,
      discountPercent,
      sales: product.orderCount || product.sales || 0,
      metadata: product.metadata || {},
    };
  });

  const specs = $derived(() => {
    const p = displayProduct();
    if (!p) return [];

    return [
      {
        label: "Đánh Giá AI",
        value: stats
          ? `${stats.average_rating.toFixed(1)}/5`
          : p.metadata?.reviews_trust_score || "4.9/5",
        color: "#f97316",
      },
      {
        label: "Đã Xác Thực",
        value: p.metadata?.offer_trust_verified_by || "Chính hãng",
        color: "#3b82f6",
        isVerification: true,
      },
      {
        label: "Tình Trạng",
        value: p.metadata?.brand_type || "Loại A++",
        color: "#10b981",
      },
    ];
  });

  onMount(async () => {
    if (product?.id) {
      try {
        const res = await fetch(
          `/api/v1/client/reviews/stats?entity_type=PRODUCT&entity_id=${product.id}`,
        );
        if (res.ok) stats = await res.json();
      } catch (e) {
        console.error("Failed to load banner stats:", e);
      }
    }

    timer = setInterval(() => {
      if (seconds > 0) seconds--;
    }, 1000);
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });
</script>

{#snippet countdownUnit(value: string)}
  <div class="countdown-box tabular-nums">
    {value}
  </div>
{/snippet}

{#snippet flashSaleBadge()}
  <div class="viral-badge-group">
    <!-- Text Part -->
    <div class="viral-text-container">
      <span>F</span>
      <svg class="lightning-svg" viewBox="0 0 24 24">
        <path d="M13 2L4 14h7l-1 8 9-12h-7z" />
      </svg>
      <span>ASH SALE</span>
    </div>

    <!-- Timer Part -->
    <div class="flex items-center gap-1.5">
      {@render countdownUnit(hh)}
      <span class="countdown-separator">:</span>
      {@render countdownUnit(mm)}
      <span class="countdown-separator">:</span>
      {@render countdownUnit(ss)}
    </div>

    <div class="divider-v"></div>
    <span class="status-label">Hàng hiếm có sẵn</span>
  </div>
{/snippet}

{#if displayProduct()}
  {@const slide = displayProduct()!}
  <div
    class="category-banner relative h-[400px] md:h-[450px] overflow-hidden bg-white/50 backdrop-blur-3xl border-b border-black/[0.03]"
  >
    <!-- Background Elements -->
    <div class="bg-glow-blur"></div>
    <div class="bg-gradient-overlay"></div>

    <div
      in:fade={{ duration: 800 }}
      class="absolute inset-0 flex items-center justify-between px-8 md:px-[76px] z-10"
    >
      <!-- Content Left -->
      <div class="relative z-10 flex flex-col gap-4 max-w-[55%] ml-[-20px]">
        <div in:fly={{ y: 20, duration: 1000, delay: 200 }}>
          {@render flashSaleBadge()}
        </div>

        <div in:fade={{ duration: 800, delay: 300 }} class="flex flex-col">
          <h2 class="product-title italic">
            {slide.name}
          </h2>
        </div>

        <div
          in:fly={{ y: 30, duration: 1000, delay: 500 }}
          class="flex items-center gap-8"
        >
          <div class="flex flex-col">
            <div class="flex items-center gap-3 mb-1">
              <span class="original-price tabular-nums">
                {formatCurrency(Math.round(slide.originalPrice!))}
              </span>
              <span class="discount-tag animate-pulse"
                >−{slide.discountPercent}%</span
              >
            </div>
            <span class="current-price tabular-nums">
              {formatCurrency(slide.price)}
            </span>
          </div>
          <div class="w-px h-8 bg-black/5"></div>
          <div class="flex flex-col">
            <span class="sold-label">Đã tin dùng</span>
            <span class="sold-count italic"
              >+{slide.sales?.toLocaleString()}</span
            >
          </div>
        </div>

        <div
          in:fly={{ y: 40, duration: 1000, delay: 700 }}
          class="flex flex-col gap-3"
        >
          <button
            onclick={() => goto(`/${slugify(slide.name)}`)}
            class="cta-button group/btn shadow-xl"
          >
            <span class="relative z-10">Xem chi tiết</span>
            <div class="cta-overlay group-hover/btn:translate-y-0"></div>
          </button>
        </div>
      </div>

      <!-- Content Right -->
      <div
        class="absolute right-0 top-0 w-[45%] h-full flex items-center justify-center pointer-events-none"
      >
        <div
          in:scale={{ duration: 1500, start: 0.9, easing: backOut, delay: 400 }}
          class="relative h-[85%] w-[85%] flex items-center justify-center"
        >
          <div class="image-bg-glow"></div>

          {#each specs() as spec, idx}
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
              in:fly={{ x: 30, duration: 1000, delay: 800 + idx * 200 }}
              class="spec-badge shadow-xl animate-float-spec {spec.isVerification
                ? 'cursor-pointer hover:scale-105 transition-transform'
                : ''}"
              style="top: {20 + idx * 20}%; right: {5 +
                (idx % 2) * 8}%; animation-delay: {idx * 1.5}s"
              onclick={() =>
                spec.isVerification && (showVerificationModal = true)}
            >
              <span
                style="font-size: 7px; font-weight: 900; letter-spacing: 0.1em; color: rgba(0,0,0,0.4)"
                >{spec.label}</span
              >
              <span
                style="font-size: 9px; font-weight: 900;"
                style:color={spec.color}>{spec.value}</span
              >
            </div>
          {/each}

          <div
            in:fly={{ x: -30, duration: 1000, delay: 1200 }}
            class="origin-badge shadow-xl"
          >
            <div class="origin-dot"></div>
            <span class="origin-text">
              {slide.metadata?.brand || slide.metadata?.origin || "Chính hãng"}
            </span>
          </div>

          <img
            src={slide.image}
            alt={slide.name}
            class="product-image filter drop-shadow-2xl animate-float-3d"
          />
        </div>
      </div>
    </div>
  </div>
{:else}
  <div
    class="category-banner relative h-[400px] md:h-[450px] overflow-hidden bg-white/50 backdrop-blur-3xl border-b border-black/[0.03] flex items-center justify-center"
  >
    <!-- Mặc định không có dữ liệu nội dung : osmo.vn -->
    <div
      class="absolute inset-0 bg-gradient-to-br from-[#C18F7E]/5 via-white to-white pointer-events-none"
    ></div>
    <div
      class="relative z-10 flex flex-col items-center justify-center opacity-20 select-none"
      in:fade={{ duration: 800 }}
    >
      <h2
        class="text-6xl md:text-8xl font-black italic tracking-tighter text-gray-500 bg-gradient-to-br from-gray-400 to-gray-200 bg-clip-text text-transparent"
      >
        osmo.vn
      </h2>
    </div>
  </div>
{/if}

{#if showVerificationModal && displayProduct()}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    use:portal
    transition:fade={{ duration: 200 }}
    class="fixed inset-0 flex items-center justify-center p-4 sm:p-8 bg-black/80 backdrop-blur-xl"
    style:z-index={Z_INDEX_CLIENT.MODAL + 50}
    onclick={() => (showVerificationModal = false)}
  >
    <div
      transition:scale={{ duration: 300, start: 0.95 }}
      class="relative max-w-5xl w-full h-auto max-h-[90vh] overflow-y-auto bg-[#0a0a0a] border border-white/10 shadow-[0_20px_100px_rgba(0,0,0,1)] rounded-xl no-scrollbar"
      onclick={(e) => e.stopPropagation()}
    >
      <button
        onclick={() => (showVerificationModal = false)}
        class="absolute top-4 right-4 w-8 h-8 flex items-center justify-center text-white/40 hover:text-white hover:bg-white/10 transition-all z-[100002] rounded-full"
      >
        <X size={18} />
      </button>
      <div class="p-0 sm:p-6">
        <VerificationCenter product={displayProduct()!} />
      </div>
    </div>
  </div>
{/if}

<style>
  @reference "tailwindcss";

  /* Base Layout */
  .bg-glow-blur {
    @apply absolute -top-24 -left-20 w-[400px] h-[400px] bg-[#ee4d2d]/5 rounded-full blur-[100px] animate-pulse pointer-events-none;
  }
  .bg-gradient-overlay {
    @apply absolute inset-0 bg-gradient-to-br from-[#C18F7E]/5 via-white to-white pointer-events-none;
  }

  /* Viral Badge Styles */
  .viral-badge-group {
    @apply flex items-center gap-4;
  }
  .viral-text-container {
    @apply flex items-center font-black text-[28px] tracking-tight text-[#f05133];
  }
  .lightning-svg {
    @apply w-5 h-7 fill-[#f05133];
    margin: 0 -2px;
  }

  /* Countdown Styles */
  .countdown-box {
    @apply flex items-center justify-center bg-gradient-to-br from-[#ee4d2d] to-[#ff6a00] text-white w-9 h-9 rounded-lg font-black text-lg;
    box-shadow: 0 4px 12px rgba(238, 77, 45, 0.3);
  }
  .countdown-separator {
    @apply font-black text-[#ee4d2d] text-xl;
  }

  .divider-v {
    @apply h-px w-6 bg-black/5;
  }
  .status-label {
    @apply text-black/30 text-[8px] font-black tracking-[0.2em] whitespace-nowrap;
  }

  /* Typography */
  .product-title {
    @apply text-2xl md:text-4xl font-black leading-tight tracking-tight line-clamp-2 bg-gradient-to-br from-black via-gray-700 to-[#C18F7E] bg-clip-text text-transparent;
  }
  .original-price {
    @apply text-sm font-bold text-gray-300 line-through decoration-gray-400/20;
  }
  .discount-tag {
    @apply text-[9px] text-[#ee4d2d] font-black tracking-widest;
  }
  .current-price {
    @apply text-[#ee4d2d] text-3xl font-black tracking-tighter flex items-end gap-1;
  }
  .sold-label {
    @apply text-[8px] font-black tracking-[0.2em] text-black/20 mb-1;
  }
  .sold-count {
    @apply text-black text-lg font-black;
  }

  /* Button */
  .cta-button {
    @apply relative w-fit px-12 py-4 bg-black text-white text-[10px] font-black tracking-[0.3em] overflow-hidden transition-all active:scale-95;
  }
  .cta-overlay {
    @apply absolute inset-0 bg-[#C18F7E] translate-y-full transition-transform duration-500 ease-out;
  }

  /* Badges & Right Image */
  .image-bg-glow {
    @apply absolute inset-0 bg-[#ee4d2d]/5 blur-[80px] rounded-full animate-pulse;
  }
  .spec-badge {
    @apply absolute z-20 px-3 py-1.5 bg-white/90 backdrop-blur-xl border border-white flex flex-col gap-0.5;
  }

  .origin-badge {
    @apply absolute z-20 bottom-[20%] left-[8%] px-3 py-2 bg-black text-white flex items-center gap-2;
  }
  .origin-dot {
    @apply h-1.5 w-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)];
  }
  .origin-text {
    @apply text-[8px] font-black tracking-[0.2em];
  }

  .product-image {
    @apply relative z-10 max-h-full object-contain filter;
  }

  /* Animations */
  @keyframes float3d {
    0%,
    100% {
      transform: translateY(0) rotate(0deg);
    }
    50% {
      transform: translateY(-15px) rotate(2deg);
    }
  }
  .animate-float-3d {
    animation: float3d 6s infinite ease-in-out;
  }

  @keyframes floatSpec {
    0%,
    100% {
      transform: translate(0, 0);
    }
    50% {
      transform: translate(5px, -10px);
    }
  }
  .animate-float-spec {
    animation: floatSpec 5s infinite ease-in-out;
  }
</style>
