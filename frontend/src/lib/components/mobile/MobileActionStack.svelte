<script lang="ts">
  import { ShoppingCart, Star, Info, MessageSquare, ShieldCheck, Heart, Share2 } from 'lucide-svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { onMount } from 'svelte';
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

  // --- Like & Share Logic (Elite V2.2) ---
  let isLiked = $state(false);
  let localLikeCount = $state(Number(product?.metadata?.likes || 0));
  let localShareCount = $state(Number(product?.metadata?.share_count || 0));

  onMount(() => {
    isLiked = !!localStorage.getItem(`liked_${product.id}`);
  });

  const handleLike = () => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) navigator.vibrate(10);
    isLiked = !isLiked;
    if (isLiked) {
      localLikeCount++;
      localStorage.setItem(`liked_${product.id}`, 'true');
    } else {
      localLikeCount--;
      localStorage.removeItem(`liked_${product.id}`);
    }
  };

  const handleShare = async () => {
    if (typeof navigator !== 'undefined' && navigator.share) {
      try {
        await navigator.share({
          title: product.name,
          text: product.shortDescription,
          url: window.location.href
        });
        localShareCount++;
      } catch (e) {
        // Fallback or ignore
      }
    } else {
      // Copy link fallback
      try {
        await navigator.clipboard.writeText(window.location.href);
        alert('Đã sao chép liên kết!');
        localShareCount++;
      } catch (e) {
        // Ignore
      }
    }
  };
</script>

<div
  class="mobile-action-stack"
  class:HUD-hidden={isScrollingDown}
>
  <!-- 5. Like (Elite Viral Integration) -->
  <button
    class="action-btn-mini group"
    onclick={handleLike}
    aria-label="Thích sản phẩm"
  >
    <Heart 
      class="w-6 h-6 drop-shadow-xl group-active:scale-90 transition-all {isLiked ? 'text-red-500 fill-red-500' : 'text-white'}" 
    />
    <span class="btn-stat-mini">{localLikeCount}</span>
    <span class="btn-label-mini">Thích</span>
  </button>

  <!-- 4. Share (Elite Viral Integration) -->
  <button
    class="action-btn-mini group"
    onclick={handleShare}
    aria-label="Chia sẻ sản phẩm"
  >
    <Share2 class="w-6 h-6 text-white drop-shadow-xl group-active:scale-90 transition-transform" />
    <span class="btn-stat-mini">{localShareCount}</span>
    <span class="btn-label-mini">Chia sẻ</span>
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

  <!-- 1. Giỏ hàng (Mini Stack) -->
  <button
    class="relative group/buy active:scale-90 transition-all outline-none mt-2"
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
  .mobile-action-stack {
    position: fixed;
    right: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 32px; /* Increased gap for breathability */
    transition: all 0.7s cubic-bezier(0.23, 1, 0.32, 1);
    padding-bottom: 32px;
    z-index: var(--z-surface);
    bottom: calc(var(--mobile-bottom-space) + env(safe-area-inset-bottom, 20px));
  }

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

  .btn-stat-mini {
    font-size: 10px;
    font-weight: 900;
    color: white;
    margin-top: 1px;
    text-shadow: 0 2px 8px rgba(0,0,0,1);
  }

  /* Tiktok-style Shadow for icons */
  :global(.action-btn-mini svg) {
    filter: drop-shadow(0 2px 8px rgba(0,0,0,1));
  }
  .disk-image {
    background-image: var(--disk-url);
  }
</style>
