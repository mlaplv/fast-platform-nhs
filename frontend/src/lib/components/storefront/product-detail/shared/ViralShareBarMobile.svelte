<script lang="ts">
  import Heart from "@lucide/svelte/icons/heart";
  import Instagram from "@lucide/svelte/icons/instagram";
  import Send from "@lucide/svelte/icons/send";
  import Twitter from "@lucide/svelte/icons/twitter";
  import Facebook from "@lucide/svelte/icons/facebook";
  import Copy from "@lucide/svelte/icons/copy";
  import Zap from "@lucide/svelte/icons/zap";
  import type { Product } from '$lib/types';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';
  import { SHOP_CONFIG } from '$lib/constants/shop';

  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';

  interface Props {
    product: Product;
    variant?: 'mobile' | 'funnel';
    likeCount?: number;
    hideLikes?: boolean;
    scrolled?: boolean;
    forceHidden?: boolean;
    scrollRatio?: number;
    hideRatio?: number;
  }

  let { 
    product, 
    variant = 'mobile', 
    likeCount = 0, 
    hideLikes = false,
    dark = false,
    onShareComplete,
    scrolled = false,
    forceHidden = false,
    scrollRatio = 0,
    hideRatio = 0
  }: Props = $props();
  
  const viralSuite = $derived(product.metadata?.viral_suite ?? null);
  
  const shareCount = $derived(
    viralSuite?.share_count ?? (typeof product.metadata.share_count === 'number' ? product.metadata.share_count : 0)
  );
  const shareTarget = $derived(
    viralSuite?.share_target ?? (typeof product.metadata.share_target === 'number' ? product.metadata.share_target : 0)
  );
  const shareProgress = $derived(
    shareTarget > 0 ? Math.max(80, Math.min((shareCount / shareTarget) * 100, 100)) : 80
  );
  
  const promoConfig = $derived(
    viralSuite?.share_promotion ?? 
    product.metadata?.share_promotion ?? 
    null
  );

  let campaignData = $state<any>(null);
  let isCampaignLoaded = $state(false);

  $effect(() => {
    const vId = viralSuite?.share_promotion?.voucher_id;
    if (vId && !isCampaignLoaded) {
      isCampaignLoaded = true;
      fetch(`/api/v1/client/viral/campaign/${vId}`)
        .then(res => res.json())
        .then(data => { campaignData = data; })
        .catch(() => {});
    }
  });

  const activationMsg = $derived(campaignData?.cta_text || 'Cùng nhau chia sẻ!');
  const campaignDesc = $derived(campaignData?.share_text || 'Cùng cộng đồng lan tỏa để nhận mã giảm giá đặc biệt!');
  const displayRewardLabel = $derived(campaignData?.voucher_label || 'Ưu đãi lan tỏa');
  const voucherCode = $derived(shareProgress >= 100 ? (campaignData?.voucher_id || 'OPEN') : null);

  // Elite V2.2: Centralized Favorite Management
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const baseLikeCount = $derived(Number(viralSuite?.likes_count || product.metadata?.likes || likeCount || 0));
  const localLikeCount = $derived(baseLikeCount + (isLiked ? 1 : 0));

  let scrollY = $state(0);
  
  const isCollapsed = $derived(scrolled || scrollRatio > 0.5 || (scrollY >= 100 && scrollY < 400));
  const isHidden = $derived(forceHidden || hideRatio >= 1 || scrollY >= 400);

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

  function triggerVerify() {
    if (typeof window !== 'undefined') window.dispatchEvent(new Event('openVerificationCenter'));
  }
</script>

<svelte:window onscroll={handleScroll} />

<div class="w-full font-sans relative group z-10" class:opacity-60={isCollapsed} class:opacity-0={isHidden} class:pointer-events-none={isHidden}>
  {#if variant === 'funnel'}
    <div class="flex flex-col w-full relative z-10 transition-all duration-300">
      <!-- Actions Row (Premium Glass) -->
      <div class="relative z-10 flex items-center justify-between gap-2 mt-3 mb-2">
        <!-- Like Pill -->
        <button onclick={handleLike} class="flex items-center gap-1.5 px-4 py-2 rounded-xl transition-all active:scale-95 shrink-0 backdrop-blur-md {isLiked ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'bg-white/10 text-white/90 border border-white/10'}">
          <Heart size={14} class={isLiked ? 'fill-current' : ''} />
          <span class="text-xs font-bold">{formatViralCount(localLikeCount)}</span>
        </button>

        <!-- Social Icons Group (Liquid Glass) -->
        <div class="flex-1 flex items-center justify-around gap-2 px-3 py-2 bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl overflow-x-auto scrollbar-hide">
          <button onclick={() => share('facebook')} class="text-white/80 hover:text-white transition-all active:scale-90" aria-label="FB"><Facebook size={18} class="fill-current" /></button>
          <button onclick={() => share('zalo')} class="text-white/80 hover:text-white transition-all active:scale-90 font-bold text-[12px]" aria-label="Zalo">Zalo</button>
          <button onclick={() => share('x')} class="text-white/80 hover:text-white transition-all active:scale-90" aria-label="X"><Twitter size={18} class="fill-current" /></button>
          <button onclick={() => share('instagram')} class="text-white/80 hover:text-white transition-all active:scale-90" aria-label="IG"><Instagram size={18} /></button>
          <button onclick={copyLink} class="text-white/80 hover:text-white transition-all active:scale-90" aria-label="Copy"><Copy size={18} /></button>
        </div>
      </div>

      <!-- FOMO Progress (Neon Standard) -->
      {#if shareTarget > 0}
        <div class="relative z-10 mt-2 px-1">
          {#if shareProgress < 100}
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full bg-rose-400 animate-pulse shadow-[0_0_10px_#fb7185]"></div>
                <span class="text-[11px] text-white/90 font-medium line-clamp-1">{campaignDesc}</span>
              </div>
              <span class="text-[12px] font-black text-rose-400">{Math.round(shareProgress)}%</span>
            </div>
            <div class="h-1.5 w-full bg-white/10 rounded-full overflow-hidden backdrop-blur-sm p-[1px]">
              <div class="h-full rounded-full bg-gradient-to-r from-rose-500 to-pink-500 transition-all duration-1000 relative" style="width: {shareProgress}%">
                <div class="absolute inset-0 bg-white/20 animate-shimmer-fast"></div>
              </div>
            </div>
          {:else}
            <div class="text-center bg-white/5 backdrop-blur-md p-3 rounded-xl border border-rose-500/30 animate-bounce-subtle">
              <div class="text-[11px] font-black text-rose-400 mb-2 tracking-widest">🎉 Mục tiêu đã đạt!</div>
              <div class="flex items-center justify-between bg-black/20 rounded-lg px-3 py-2 border border-white/10">
                <span class="font-mono text-lg font-black text-white tracking-wider">{voucherCode}</span>
                <button onclick={() => voucherCode && navigator.clipboard.writeText(voucherCode)} class="text-[10px] font-black bg-rose-500 text-white px-3 py-1.5 rounded-md shadow-lg active:scale-95 transition-transform">Copy</button>
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {:else}
    <!-- TikTok Vertical Floating Style -->
    <div 
      class="fixed right-2.5 top-[15vh] z-[1000] flex flex-col items-center gap-4 transition-all duration-300" 
      style="
        opacity: {1 - hideRatio}; 
        transform: 
          translateX({scrollRatio * 16}px) 
          translateY({hideRatio * 50}px) 
          scale({1 - scrollRatio * 0.1 - hideRatio * 0.2});
        pointer-events: {hideRatio > 0.8 ? 'none' : 'auto'};
      "
    >
      <button class="w-10 h-10 flex items-center justify-center relative active:scale-90 transition-transform drop-shadow-[0_4px_10px_rgba(0,0,0,0.1)] focus:outline-none" onclick={triggerVerify}>
        <img src={product?.metadata?.verified_badge_url || SHOP_CONFIG.default_badge_url} alt="Verified Badge" class="w-full h-full object-contain" />
      </button>

      <button class="flex flex-col items-center gap-1 drop-shadow-md active:scale-90 transition-transform" onclick={handleLike}>
        <div class="w-10 h-10 rounded-full flex items-center justify-center backdrop-blur-md transition-colors {isLiked ? 'bg-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.5)]' : 'bg-black/40 border border-white/20'}">
           <Heart size={18} class={isLiked ? 'fill-white text-white' : 'text-white'} />
        </div>
        <span class="text-[10px] font-black text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]">{formatViralCount(localLikeCount)}</span>
      </button>

      <div class="flex flex-col gap-3">
        <button class="active:scale-90 transition-transform" onclick={() => share('facebook')}>
          <div class="w-9 h-9 rounded-full bg-[#1877f2] flex items-center justify-center shadow-lg"><Facebook size={16} class="fill-white text-white" /></div>
        </button>
        <button class="active:scale-90 transition-transform" onclick={() => share('zalo')}>
          <div class="w-9 h-9 rounded-full bg-[#0068ff] flex items-center justify-center shadow-lg"><span class="text-[9px] font-black italic text-white tracking-tighter">Zalo</span></div>
        </button>
        <button class="active:scale-90 transition-transform" onclick={copyLink}>
          <div class="w-9 h-9 rounded-full bg-white/20 backdrop-blur-md border border-white/20 flex items-center justify-center shadow-lg"><Copy size={14} class="text-white" /></div>
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  @keyframes shimmer {
    100% { transform: translateX(150%); }
  }
  @keyframes shimmer-fast {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  @keyframes bounce-subtle {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
  }
  .animate-shimmer-fast { animation: shimmer-fast 1.5s linear infinite; }
  .animate-bounce-subtle { animation: bounce-subtle 3s ease-in-out infinite; }
  
  .scrollbar-hide::-webkit-scrollbar { display: none; }
  .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
  
  :global(.vsb-heart-burst) { position: fixed; pointer-events: none; z-index: 10000; transform: translate(-50%, -50%); }
  :global(.vsb-heart-particle) { position: absolute; font-size: 16px; animation: heart-fly 1s cubic-bezier(0.12, 0, 0.39, 0) forwards; opacity: 0; animation-delay: var(--delay, 0s); }
  @keyframes heart-fly {
    0% { transform: translate(0,0) scale(0); opacity: 0; }
    20% { opacity: 1; transform: translate(0,0) scale(1.2); }
    100% { transform: translate(calc(cos(calc(var(--i) * 30deg)) * 100px), calc(sin(calc(var(--i) * 30deg)) * -80px - 40px)) scale(0.8); opacity: 0; }
  }
</style>
