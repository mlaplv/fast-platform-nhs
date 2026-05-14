<script lang="ts">
    import ShoppingCart from "@lucide/svelte/icons/shopping-cart";
  import Star from "@lucide/svelte/icons/star";
  import Info from "@lucide/svelte/icons/info";
  import MessageSquare from "@lucide/svelte/icons/message-square";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import type { Product } from '$lib/types';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';

  interface Props {
    product: Product;
    onPurchase: () => void;
    onOpenDetails?: () => void;
    onChat?: () => void;
    onVerify?: () => void;
    isTikTokActive?: boolean;
    isScrollingDown?: boolean;
  }

  let {
    product,
    onPurchase,
    onOpenDetails,
    onChat,
    onVerify,
    isTikTokActive = false,
    isScrollingDown = false
  }: Props = $props();

  const metadata = $derived(product?.metadata);

  const labels = $derived({
    disk_image: metadata?.mobile_disk_image || metadata?.mobile_shop_avatar || "/favicon.svg",
    label_purchase: metadata?.mobile_label_purchase || "Mở giỏ hàng"
  });

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };
</script>

<div
  class="mobile-action-stack"
  class:HUD-hidden={isScrollingDown}
>
  <!-- 6. Tra cứu (Top-most utility) -->
  <a
    href="/track"
    class="action-btn-mini group"
    aria-label="Tra cứu đơn hàng"
  >
    <ShieldCheck class="w-6 h-6 text-white drop-shadow-xl group-active:scale-90 transition-transform" />
    <span class="btn-label-mini">Tra cứu</span>
  </a>

  <!-- 5.5 Xác thực (Elite V2.2 Scan) -->
  <button
    class="action-btn-mini group"
    onclick={() => onVerify?.()}
    aria-label="Xác thực nguồn gốc"
  >
    <div class="relative">
      <div class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-black animate-pulse"></div>
      <svg class="w-6 h-6 text-white drop-shadow-xl group-active:scale-90 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 7V5a2 2 0 0 1 2-2h2" />
        <path d="M17 3h2a2 2 0 0 1 2 2v2" />
        <path d="M21 17v2a2 2 0 0 1-2 2h-2" />
        <path d="M7 21H5a2 2 0 0 1-2-2v-2" />
        <line x1="7" y1="12" x2="17" y2="12" />
      </svg>
    </div>
    <span class="btn-label-mini">Xác thực</span>
  </button>

  <!-- 5. Chat (Viral AI Helen Integration) -->
  <button
    class="action-btn-mini group"
    onclick={() => onChat ? onChat() : supportAgent.toggle()}
    aria-label="Tư vấn AI Helen"
  >
    <div class="relative">
      <MessageSquare class="w-6 h-6 text-white drop-shadow-xl group-active:scale-90 transition-transform" />
    </div>
    <span class="btn-label-mini">{supportAgent.helenEnabled ? 'AI HELEN' : 'HỖ TRỢ'}</span>
  </button>

  <!-- 4. Chi tiết sản phẩm -->
  <button
    class="action-btn-mini group"
    onclick={() => onOpenDetails ? onOpenDetails() : scrollToSection('science')}
    aria-label="Chi tiết sản phẩm"
  >
    <Info class="w-6 h-6 text-white drop-shadow-xl group-active:scale-90 transition-transform" />
    <span class="btn-label-mini">Chi tiết</span>
  </button>

  <!-- 3. Đánh giá -->
  <button
    class="action-btn-mini group"
    onclick={() => scrollToSection('reviews')}
    aria-label="Đánh giá"
  >
    <Star class="w-6 h-6 text-white drop-shadow-xl group-active:scale-90 transition-transform" fill="white" />
    <span class="btn-label-mini">Đánh giá</span>
  </button>

  <!-- MIỄN PHÍ SHIP Badge (Centered between Star and Cart) -->
  <div class="bg-[#FFB7C5] text-slate-950 text-[7px] font-black px-2 py-0.5 rounded shadow-[0_4px_12px_rgba(255,183,197,0.4)] animate-bounce whitespace-nowrap z-surface uppercase tracking-wider relative translate-y-[8px]">
    FREESHIP
  </div>

  <!-- 1. Giỏ hàng (Mini Stack) -->
  <button
    class="relative group/buy active:scale-90 transition-all outline-none"
    onclick={onPurchase}
    aria-label={labels.label_purchase}
  >
    <div class="w-12 h-12 vinyl-spin bg-black rounded-full flex items-center justify-center border border-[#FFB7C5]/30 shadow-[0_0_20px_rgba(255,183,197,0.2)] overflow-hidden relative">
      <div
        class="w-full h-full animate-spin-slow bg-cover opacity-60 absolute inset-0"
        style:background-image="url('{labels.disk_image}')"
      ></div>
      <div class="absolute inset-0 bg-[#FFB7C5]/5"></div>
      <ShoppingCart class="w-6 h-6 text-[#FFB7C5] relative z-surface drop-shadow-lg" />
    </div>
  </button>
</div>

<style lang="postcss">
  .action-btn-mini {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 2.75rem;
    height: 2.75rem;
    transition: all 0.4s ease;
  }

  .btn-label-mini {
    position: absolute;
    bottom: -1rem;
    font-size: 8px;
    font-weight: 800;
    color: white;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.8;
    text-shadow: 0 2px 8px rgba(0,0,0,1);
    white-space: nowrap;
  }

  /* Tiktok-style Shadow for icons */
  :global(.action-btn-mini svg) {
    filter: drop-shadow(0 2px 8px rgba(0,0,0,1));
  }
  .disk-image {
    background-image: var(--disk-url);
  }
</style>
