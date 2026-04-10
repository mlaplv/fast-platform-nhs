<script lang="ts">
  import { ShoppingCart, Star, Info, MessageSquare, ShieldCheck } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import type { Product } from '$lib/types';
  import { supportAgent } from '$lib/state/commerce/supportAgent.svelte.ts';

  interface Props {
    product: Product;
    onPurchase: () => void;
    onOpenDetails?: () => void;
    onChat?: () => void;
    isTikTokActive?: boolean;
    isScrollingDown?: boolean;
  }

  let {
    product,
    onPurchase,
    onOpenDetails,
    onChat,
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
  <div class="bg-emerald-500 text-white text-[7px] font-black px-2 py-0.5 rounded shadow-lg animate-bounce whitespace-nowrap z-surface uppercase tracking-wider relative translate-y-[10px]">
    FREESHIP
  </div>

  <!-- 1. Giỏ hàng (Mini Stack) -->
  <button
    class="relative group/buy active:scale-90 transition-all outline-none"
    onclick={onPurchase}
    aria-label={labels.label_purchase}
  >
    <div class="w-12 h-12 vinyl-spin bg-black rounded-full flex items-center justify-center border border-white/20 shadow-2xl overflow-hidden relative">
      <div
        class="w-full h-full animate-spin-slow bg-cover opacity-80 absolute inset-0"
        style:background-image="url('{labels.disk_image}')"
      ></div>
      <div class="absolute inset-0 bg-black/20"></div>
      <ShoppingCart class="w-6 h-6 text-white relative z-surface drop-shadow-lg" />
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
