<script lang="ts">
    import Heart from "@lucide/svelte/icons/heart";
  import Facebook from "@lucide/svelte/icons/facebook";
  import Copy from "@lucide/svelte/icons/copy";
  import Zap from "@lucide/svelte/icons/zap";
  import MoreHorizontal from "@lucide/svelte/icons/more-horizontal";
  import Send from "@lucide/svelte/icons/send";
  import type { Product } from '$lib/types';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';

  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';

  interface Props {
    product: Product;
    variant?: 'mobile' | 'funnel';
    likeCount?: number;
    hideLikes?: boolean;
    dark?: boolean;
    onShareComplete?: () => void;
  }

  let { 
    product, 
    variant = 'mobile', 
    likeCount = 0, 
    hideLikes = false,
    dark = false,
    onShareComplete
  }: Props = $props();
  
  const viralSuite = $derived(product.metadata?.viral_suite ?? null);
  
  // Elite V2.2: Centralized Favorite Management
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const localLikeCount = $derived(likeCount + (isLiked ? 1 : 0));

  let scrollY = $state(0);
  
  const isCollapsed = $derived(scrollY >= 100 && scrollY < 400);
  const isHidden = $derived(scrollY >= 400);

  function handleScroll() {
    if (typeof window !== 'undefined') scrollY = window.scrollY;
  }

  function handleLike(e: MouseEvent) {
    e.preventDefault();
    if (!product?.id) return;

    const wasLiked = isLiked;
    wishlistStore.toggle(product.id);
    
    if (!wasLiked) {
      createHeartConfetti(e.clientX, e.clientY);
    }
  }

  async function share(platform: string) {
    await shareToPlatform(platform, window.location.href, product.name, onShareComplete);
  }

  async function copyLink() {
    await copyViralLink(window.location.href);
    onShareComplete?.();
  }
</script>

<svelte:window onscroll={handleScroll} />

<div class="vsb-mobile-root" class:funnel={variant === 'funnel'} class:vsb-dark={dark}>
  {#if variant === 'funnel'}
    <div class="vsb-funnel">
       <div class="vsb-funnel-main">
          <button onclick={handleLike} class="vsb-funnel-pill" class:liked={isLiked}>
             <Heart size={20} class={isLiked ? 'text-rose-500 fill-current' : 'text-white/60'} />
             <span class="vsb-funnel-count">{formatViralCount(localLikeCount)}</span>
          </button>
          <button onclick={() => share('facebook')} class="vsb-funnel-icon fb" aria-label="Share on Facebook"><Facebook size={18} fill="currentColor" /></button>
          <button onclick={() => share('zalo')} class="vsb-funnel-icon zalo" aria-label="Share on Zalo"><span class="text-[9px] font-black italic">Zalo</span></button>
          <button onclick={copyLink} class="vsb-funnel-icon copy" aria-label="Copy link"><Copy size={16} /></button>
       </div>
    </div>
  {:else}
    <div class="vsb-tiktok-wrap" class:scrolled={isCollapsed} class:hidden={isHidden}>
       <div class="vsb-vertical-actions">
          <button class="vsb-v-btn" onclick={handleLike}>
             <div class="vsb-v-icon-circle" class:liked={isLiked}>
                <Heart size={18} fill={isLiked ? 'white' : 'none'} stroke={isLiked ? 'none' : 'white'} />
             </div>
             <span class="vsb-v-count">{formatViralCount(localLikeCount)}</span>
          </button>
          <div class="vsb-share-stack">
             <button class="vsb-v-btn" onclick={() => share('facebook')}>
                <div class="vsb-v-icon-circle fb"><Facebook size={14} fill="white" /></div>
             </button>
             <button class="vsb-v-btn" onclick={() => share('zalo')}>
                <div class="vsb-v-icon-circle zalo"><span class="text-[8px] font-black italic text-white">Zalo</span></div>
             </button>
             <button class="vsb-v-btn" onclick={copyLink}>
                <div class="vsb-v-icon-circle copy"><Copy size={14} color="white" /></div>
             </button>
          </div>
       </div>
    </div>
  {/if}
</div>

<style>
  .vsb-mobile-root { position: relative; width: 100%; }

  /* TikTok Style Vertical Actions */
  .vsb-tiktok-wrap { 
    position: fixed; right: 10px; top: 15vh; z-index: 1000;
    transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  .vsb-tiktok-wrap.scrolled { transform: translateX(20px) scale(0.85); opacity: 0.6; }
  .vsb-tiktok-wrap.hidden { transform: translateX(80px); opacity: 0; pointer-events: none; }

  .vsb-vertical-actions { display: flex; flex-direction: column; align-items: center; gap: 16px; }
  
  .vsb-v-btn { display: flex; flex-direction: column; align-items: center; gap: 4px; background: none; border: none; padding: 0; outline: none; }
  .vsb-v-icon-circle { 
    width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    background: rgba(0,0,0,0.4); backdrop-filter: blur(8px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .vsb-v-icon-circle.liked { background: #ff2d55; transform: scale(1.1); box-shadow: 0 0 15px rgba(255, 45, 85, 0.5); }
  .vsb-v-icon-circle.fb { background: #1877f2; }
  .vsb-v-icon-circle.zalo { background: #0068ff; }
  .vsb-v-icon-circle.copy { background: rgba(255,255,255,0.1); }

  .vsb-v-count { font-size: 10px; font-weight: 900; color: white; text-shadow: 0 1px 4px rgba(0,0,0,0.8); }
  .vsb-share-stack { display: flex; flex-direction: column; gap: 12px; }

  /* Funnel Variant */
  .vsb-funnel { width: 100%; padding: 12px 0; }
  .vsb-funnel-main { display: flex; align-items: center; gap: 8px; }
  .vsb-funnel-pill { 
    display: flex; align-items: center; gap: 8px; padding: 10px 18px; 
    background: rgba(255,255,255,0.08); backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12); border-radius: 100px;
    transition: all 0.3s;
  }
  .vsb-funnel-pill.liked { background: rgba(244,63,94,0.15); border-color: rgba(244,63,94,0.3); }
  .vsb-funnel-count { font-size: 13px; font-weight: 1000; italic: true; color: white; }

  .vsb-funnel-icon { 
    width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    background: rgba(255,255,255,0.08); backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12); color: white;
    transition: all 0.2s;
  }
  .vsb-funnel-icon:active { transform: scale(0.9); background: rgba(255,255,255,0.2); }

  :global(.vsb-heart-burst) { position: fixed; pointer-events: none; z-index: 10000; transform: translate(-50%, -50%); }
  :global(.vsb-heart-particle) { position: absolute; font-size: 14px; animation: heart-fly 0.8s ease-out forwards; opacity: 0; }
  @keyframes heart-fly {
    0% { transform: translate(0,0) scale(0.5); opacity: 1; }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 60px), calc(sin(calc(var(--i) * 45deg)) * 60px)) scale(1.2); opacity: 0; }
  }
</style>
