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
  const displayRewardLabel = $derived(campaignData?.voucher_label || 'ƯU ĐÃI LAN TỎA');
  const voucherCode = $derived(shareProgress >= 100 ? (campaignData?.voucher_id || 'OPEN') : null);

  // Elite V2.2: Centralized Favorite Management
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const baseLikeCount = $derived(Number(viralSuite?.likes_count || product.metadata?.likes || likeCount || 0));
  const localLikeCount = $derived(baseLikeCount + (isLiked ? 1 : 0));

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

<div class="w-full font-sans relative group z-10" class:opacity-60={isCollapsed} class:opacity-0={isHidden} class:pointer-events-none={isHidden}>
  {#if variant === 'funnel'}
    <div class="flex flex-col w-full relative z-10 transition-all duration-300">



      <!-- Actions Row (Minimalist) -->
      <div class="relative z-10 flex items-center justify-between overflow-x-auto pb-1 mt-2 mb-2 scrollbar-hide">
        <!-- Like Pill -->
        <button onclick={handleLike} class="flex items-center gap-1.5 px-3 py-2 rounded-full transition-all active:scale-95 shrink-0 {isLiked ? 'bg-rose-500/20 text-rose-400' : 'text-white/80'}">
          <Heart size={14} class={isLiked ? 'fill-current' : ''} />
          <span class="text-xs font-black">{formatViralCount(localLikeCount)}</span>
        </button>

        <div class="w-[1px] h-4 bg-white/20 mx-2 shrink-0"></div>

        <!-- Social Icons Group (Flat) -->
        <div class="flex items-center gap-4 shrink-0 px-2">
          <button onclick={() => share('facebook')} class="text-white hover:text-white/70 transition-all active:scale-95" aria-label="FB"><Facebook size={16} class="fill-current" /></button>
          <button onclick={() => share('zalo')} class="text-white hover:text-white/70 transition-all active:scale-95 font-black text-[11px] tracking-tight" aria-label="Zalo">Zalo</button>
          <button onclick={() => share('x')} class="text-white hover:text-white/70 transition-all active:scale-95" aria-label="X"><Twitter size={16} class="fill-current" /></button>
          <button onclick={() => share('instagram')} class="text-white hover:text-white/70 transition-all active:scale-95" aria-label="IG"><Instagram size={16} /></button>
          <button onclick={() => share('telegram')} class="text-white hover:text-white/70 transition-all active:scale-95" aria-label="TG"><Send size={16} /></button>
          <button onclick={copyLink} class="text-white hover:text-white/70 transition-all active:scale-95" aria-label="Copy"><Copy size={16} /></button>
        </div>
      </div>

      <!-- FOMO Progress Minimalist -->
      {#if shareTarget > 0}
        <div class="relative z-10 mt-1">
          {#if shareProgress < 100}
            <div class="flex items-center justify-between mb-1.5">
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse shadow-[0_0_8px_rgba(251,113,133,0.8)]"></div>
                <span class="text-[10px] text-white/80 line-clamp-1">{campaignDesc}</span>
              </div>
              <span class="text-[11px] font-bold text-rose-400">{Math.round(shareProgress)}%</span>
            </div>
            <div class="h-1 w-full bg-black/60 rounded-full overflow-hidden">
              <div class="h-full rounded-full bg-rose-500 transition-all duration-1000" style="width: {shareProgress}%"></div>
            </div>
          {:else}
            <div class="text-center bg-black/20 p-2 rounded-lg border border-white/10">
              <div class="text-[10px] font-black text-pink-400 mb-2">🎉 MỤC TIÊU ĐÃ ĐẠT!</div>
              <div class="flex items-center justify-between bg-black/40 rounded px-2 py-1.5 border border-white/10">
                <span class="font-mono text-sm font-black text-white">{voucherCode}</span>
                <button onclick={() => voucherCode && navigator.clipboard.writeText(voucherCode)} class="text-[9px] font-black bg-white text-black px-2 py-1 rounded">COPY</button>
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {:else}
    <!-- TikTok Vertical Floating Style -->
    <div class="fixed right-2.5 top-[15vh] z-[1000] flex flex-col items-center gap-4 transition-all duration-500" class:translate-x-4={isCollapsed} class:scale-90={isCollapsed}>
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
  .scrollbar-hide::-webkit-scrollbar { display: none; }
  .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
  
  :global(.vsb-heart-burst) { position: fixed; pointer-events: none; z-index: 10000; transform: translate(-50%, -50%); }
  :global(.vsb-heart-particle) { position: absolute; font-size: 14px; animation: heart-fly 0.8s ease-out forwards; opacity: 0; }
  @keyframes heart-fly {
    0% { transform: translate(0,0) scale(0.5); opacity: 1; }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 60px), calc(sin(calc(var(--i) * 45deg)) * 60px)) scale(1.2); opacity: 0; }
  }
</style>
