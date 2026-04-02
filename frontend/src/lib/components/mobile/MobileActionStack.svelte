<script lang="ts">
  import { ShoppingCart, Star, Info, MessageSquare, ShieldCheck } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/z_index_client';
  import type { Product } from '$lib/types';

  interface Props {
    product: Product;
    onPurchase: () => void;
    onOpenDetails?: () => void;
    isTikTokActive?: boolean;
    isScrollingDown?: boolean;
  }

  let {
    product,
    onPurchase,
    onOpenDetails,
    isTikTokActive = false,
    isScrollingDown = false
  }: Props = $props();

  const metadata = $derived(product?.metadata || {});

  const labels = $derived({
    disk_image: (metadata.mobile_disk_image as string) || (metadata.mobile_shop_avatar as string) || "/favicon.svg",
    label_purchase: (metadata.mobile_label_purchase as string) || "Mở giỏ hàng",
    zalo_link: (metadata.mobile_zalo_link as string) || "https://zalo.me/0981515545"
  });

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };
</script>

<div
  class="fixed right-2 flex flex-col items-center gap-7 transition-all duration-700 ease-[cubic-bezier(0.23,1,0.32,1)] pb-8"
  class:HUD-hidden={isScrollingDown}
  style:z-index={Z_INDEX_CLIENT.SURFACE}
  style:bottom="calc(var(--mobile-bottom-space) + env(safe-area-inset-bottom, 20px))"
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

  <!-- 5. Chat -->
  <a
    href={labels.zalo_link}
    target="_blank"
    class="action-btn-mini group"
    aria-label="Chat Zalo"
  >
    <MessageSquare class="w-6 h-6 text-white drop-shadow-xl group-active:scale-90 transition-transform" />
    <span class="btn-label-mini">Chat</span>
  </a>

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
  <div class="bg-emerald-500 text-white text-[7px] font-black px-2 py-0.5 rounded shadow-lg animate-bounce whitespace-nowrap z-30 uppercase tracking-wider relative translate-y-[10px]">
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
      <ShoppingCart class="w-6 h-6 text-white relative z-10 drop-shadow-lg" />
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

  /* Scroll Reactive State (Mini Mode) */
  .HUD-hidden {
    transform: translateX(100%) scale(0.6);
    opacity: 0.3;
    pointer-events: none;
    filter: blur(2px);
  }

  .HUD-hidden:hover {
    transform: translateX(0) scale(1);
    opacity: 1;
    pointer-events: auto;
    filter: none;
  }

  @keyframes vinyl-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .animate-spin-slow {
    animation: vinyl-spin 4s linear infinite;
  }

  /* Tiktok-style Shadow for icons */
  :global(.action-btn-mini svg) {
    filter: drop-shadow(0 2px 8px rgba(0,0,0,1));
  }
</style>
