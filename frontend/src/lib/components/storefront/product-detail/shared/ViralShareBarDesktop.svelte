<script lang="ts">
  import { fetchViralCampaign } from '$lib/utils/viralCampaignCache';
  import Instagram from "$lib/components/ui/icons/Instagram.svelte";
  import Send from "@lucide/svelte/icons/send";
  import Twitter from "$lib/components/ui/icons/Twitter.svelte";
  import Facebook from "$lib/components/ui/icons/Facebook.svelte";
  import Copy from "@lucide/svelte/icons/copy";
  import Heart from "@lucide/svelte/icons/heart";
  import Zap from "@lucide/svelte/icons/zap";
  import type { Product } from '$lib/types';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti, getProductLikeCount,
    getProductShareCount, getProductShareTarget, getProductShareProgress
  } from '$lib/utils/commerce/viral';
  import { formatCurrency } from '$lib/utils/format';

  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { untrack, onMount } from 'svelte';
  import { browser } from '$app/environment';

  interface Props {
    product: Product;
    onShareComplete?: () => void;
    likeCount?: number;
    hideLikes?: boolean;
    dark?: boolean;
  }

  let { 
    product, 
    onShareComplete, 
    likeCount = 0, 
    hideLikes = false,
    dark = false
  }: Props = $props();

  // Elite V2.2: Hydration guard — delay dynamic UI until client is fully mounted
  let isMounted = $state(false);
  onMount(() => { isMounted = true; });

  const viralSuite = $derived(product.metadata?.viral_suite ?? null);
  
  const shareCount = $derived(getProductShareCount(product));
  const shareTarget = $derived(getProductShareTarget(product));
  const shareProgress = $derived(getProductShareProgress(product));
  
  const promoConfig = $derived(
    viralSuite?.share_promotion ?? 
    product.metadata?.share_promotion ?? 
    null
  );

  let campaignData = $state<{ voucher_label?: string; cta_text?: string; share_text?: string; voucher_subtitle?: string; voucher_id?: string } | null>(null);
  let isCampaignLoaded = $state(false);
  let campaignExists = $state(true); // Elite V2.2: Zero-Failure Campaign Self-Correction
  // isCampaignLoading: true khi chưa load xong (dùng cho template spinner)
  const isCampaignLoading = $derived(!isCampaignLoaded);

  $effect(() => {
    // Elite V2.2: Singleton Cache — deduplicate per voucher_id, no loop possible
    const vId = viralSuite?.share_promotion?.voucher_id || promoConfig?.voucher_id;
    if (vId && !isCampaignLoaded) {
      isCampaignLoaded = true; // Set IMMEDIATELY — prevents any re-run from triggering fetch
      fetchViralCampaign(vId).then((result) => {
        if (!result.exists || !result.enabled) {
          campaignExists = false;
          return;
        }
        campaignData = result.data as any;
      });
    }
  });

  const displayRewardLabel = $derived(
    campaignData?.voucher_label || 
    viralSuite?.share_reward_label || 
    product.metadata?.share_reward_label || 
    promoConfig?.voucher_label ||
    'Ưu đãi lan tỏa'
  );

  const activationMsg = $derived(campaignData?.cta_text || promoConfig?.cta_text || 'Chia sẻ để mở khóa ưu đãi');
  const campaignDesc = $derived(campaignData?.share_text || 'Cùng cộng đồng lan tỏa để nhận mã giảm giá đặc biệt!');
  const voucherCode = $derived(shareProgress >= 100 ? (campaignData?.voucher_id || promoConfig?.voucher_id) : null);

  // Elite V2.2: Centralized Favorite Management
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const localLikeCount = $derived(getProductLikeCount(product, isLiked));

  let isCtv = $state(false);
  let ctvCode = $state('');
  let ctvRate = $state(0.05); // Default 5%
  let showCtvPopover = $state(false);

  // Elite V2.2 Hybrid Priority Chain Commission Rate Calculation
  const activeRate = $derived.by(() => {
    const override = product.ctv_rate_override ?? product.ctvRateOverride;
    if (override !== undefined && override !== null) {
      return override;
    }
    return ctvRate;
  });

  const activeRatePercent = $derived(`${Math.round(activeRate * 100)}%`);

  const estimatedCommission = $derived.by(() => {
    const price = product.discountPrice ?? product.discount_price ?? product.price ?? 0;
    // R102 Dynamic Pricing: Deduct 3% tax from base revenue for estimated commission calculation
    const revenueNet = price * 0.97;
    return Math.round(revenueNet * activeRate);
  });

  onMount(async () => {
    isMounted = true;
    if (browser) {
      await authStore.waitForSessionVerification();
      if (authStore.isAuthenticated) {
        try {
          const ctvProfile = await apiClient.get<{ 
            ctv_code?: string; 
            encrypted_code?: string;
            tier?: { commission_rate_bps: number; commission_rate_pct: string };
          }>('/client/ctv/profile');
          if (ctvProfile) {
            isCtv = true;
            ctvCode = ctvProfile.encrypted_code || ctvProfile.ctv_code || '';
            // BPS Fix: API trả commission_rate_bps (integer), không phải commission_rate (float)
            if (ctvProfile.tier?.commission_rate_bps !== undefined) {
              ctvRate = ctvProfile.tier.commission_rate_bps / 10000;
            }
          }
        } catch (e) {
          // Not ctv, silent
        }
      }
    }
  });

  function createGoldConfetti(x: number, y: number) {
    if (typeof document === 'undefined') return;
    const burst = document.createElement('div');
    burst.className = 'vsb-gold-burst';
    burst.style.left = `${x}px`;
    burst.style.top = `${y}px`;
    document.body.appendChild(burst);

    for (let i = 0; i < 8; i++) {
      const particle = document.createElement('div');
      particle.className = 'vsb-gold-particle';
      particle.innerHTML = '✨';
      particle.style.setProperty('--i', i.toString());
      particle.style.setProperty('--delay', `${Math.random() * 0.1}s`);
      burst.appendChild(particle);
    }

    setTimeout(() => burst.remove(), 1000);
  }

  async function copyCtvLink(e: MouseEvent) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (typeof window !== 'undefined' && ctvCode) {
      const ctvLink = `${window.location.origin}${window.location.pathname}?ctv=${ctvCode}`;
      try {
        await navigator.clipboard.writeText(ctvLink);
        getClientUi().showToast('Đã copy link tiếp thị CTV độc quyền của sản phẩm này!', 'success');
        if (e) {
          createGoldConfetti(e.clientX, e.clientY);
        }
        onShareComplete?.();
      } catch (err) {
        console.error('Failed to copy CTV link:', err);
      }
    }
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

{#if (campaignExists && promoConfig?.voucher_id) || isCtv}
<div class="w-full font-sans">
  <div class="flex flex-col gap-4 w-full">
    
    <!-- Social & Like Row -->
    <div class="flex items-center justify-between">
      {#if isMounted && !hideLikes}
        <button onclick={handleLike} class="flex items-center gap-1.5 group/like">
          <Heart size={18} class="{isLiked ? 'fill-rose-500 text-rose-500' : 'text-slate-400'}" />
          <span class="text-xs font-bold {isLiked ? 'text-rose-600' : 'text-slate-500'}">{formatViralCount(localLikeCount)}</span>
        </button>
        <div class="w-[1px] h-4 bg-slate-200 mx-2"></div>
      {/if}
      
      <button onclick={() => share('facebook')} class="text-slate-400 hover:text-[#1877f2]" aria-label="Share Facebook"><Facebook size={18} class="fill-current" /></button>
      <button onclick={() => share('zalo')} class="text-slate-400 hover:text-[#0068ff] font-black text-xs" aria-label="Share Zalo">Zalo</button>
      <button onclick={() => share('x')} class="text-slate-400 hover:text-black" aria-label="Share X"><Twitter size={18} class="fill-current" /></button>
      <button onclick={() => share('instagram')} class="text-slate-400 hover:text-[#e4405f]" aria-label="Share Instagram"><Instagram size={18} /></button>
      <button onclick={() => share('telegram')} class="text-slate-400 hover:text-[#229ed9]" aria-label="Share Telegram"><Send size={18} /></button>
      
      {#if isCtv}
        <div class="relative">
          <button 
            onmouseenter={() => showCtvPopover = true}
            onmouseleave={() => showCtvPopover = false}
            onclick={(e) => copyCtvLink(e)}
            class="px-2.5 py-1 bg-gradient-to-r from-amber-500 to-luxury-copper text-stone-950 rounded-lg font-black text-[9px] tracking-wider uppercase shrink-0 flex items-center gap-1 shadow-sm shadow-luxury-copper/20 relative overflow-hidden" 
            aria-label="Copy CTV"
          >
            <!-- Continuous shimmering light sweep -->
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -translate-x-full"></div>
            <Zap size={10} class="fill-stone-950 text-stone-950" /> Kênh CTV - {activeRatePercent}
          </button>

          <!-- Premium Popover Tooltip -->
          {#if showCtvPopover}
            <div 
              onmouseenter={() => showCtvPopover = true}
              onmouseleave={() => showCtvPopover = false}
              class="absolute bottom-full right-0 mb-3 w-56 bg-stone-950/95 border border-stone-850 backdrop-blur-xl rounded-xl p-4 shadow-[0_15px_40px_rgba(0,0,0,0.5)] z-[99] flex flex-col items-center text-center gap-2.5"
            >
              <!-- Downward pointing chevron tip -->
              <div class="absolute top-full right-6 -mt-[1px] w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-stone-950/95"></div>

              <div class="flex flex-col items-center">
                <span class="text-[10px] tracking-[2px] font-black text-luxury-copper uppercase">KÊNH CTV OSMO</span>
                <span class="text-[9px] text-stone-400 mt-1">Quét mã hoặc chia sẻ để nhận hoa hồng giới thiệu</span>
              </div>

              <!-- Dynamic Commission Card (Premium TikTok/Shopee style) -->
              <div class="w-full mt-1 p-2 bg-stone-900/50 border border-amber-500/20 rounded-lg flex flex-col gap-1 items-center">
                <span class="text-[9px] font-bold text-stone-400">Hoa hồng của bạn</span>
                <span class="text-sm font-black text-amber-400">{activeRatePercent}</span>
                <span class="text-[9px] font-medium text-stone-300">~{formatCurrency(estimatedCommission)} / sản phẩm</span>
              </div>

              <!-- QR Code Container with dynamic lookup -->
              <div class="p-1.5 bg-white rounded-lg border border-amber-500/20 shadow-md">
                <img 
                  src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&color=78350f&data={encodeURIComponent(window.location.origin + window.location.pathname + '?ctv=' + ctvCode)}" 
                  alt="CTV QR Code"
                  class="w-24 h-24 object-contain"
                />
              </div>

              <button 
                onclick={(e) => copyCtvLink(e)}
                class="w-full py-2 bg-stone-900 hover:bg-stone-850 text-white border border-stone-800 rounded-lg text-[9px] font-bold tracking-[2px] uppercase transition-colors flex items-center justify-center gap-1.5 active:scale-95"
              >
                <Copy size={10} /> Sao chép Link
              </button>
            </div>
          {/if}
        </div>
      {/if}

      <button onclick={copyLink} class="text-slate-400 hover:text-slate-900" aria-label="Copy Link"><Copy size={18} /></button>
    </div>
 
    <!-- Progress: only render client-side to avoid hydration mismatch -->
    {#if isMounted && shareTarget > 0}
      {#if shareProgress < 100}
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="flex items-center gap-1.5">
                {#if isCampaignLoading}
                  <Zap size={12} class="text-blue-500 fill-blue-500/20" />
                {:else}
                  <div class="w-1.5 h-1.5 rounded-full bg-rose-500"></div>
                {/if}
              </div>
              <span class="text-[11px] {isCampaignLoading ? 'text-blue-500 font-bold' : 'text-slate-500'} line-clamp-1">
                {isCampaignLoading ? 'Đang kết nối ưu đãi...' : campaignDesc}
              </span>
            </div>
            <span class="text-[13px] font-black text-rose-500">{Math.round(shareProgress)}%</span>
          </div>
          <div class="relative w-full pt-1 pb-2 overflow-visible">
            <div class="h-1.5 w-full bg-slate-100 dark:bg-white/10 rounded-full relative">
              <!-- Glow shadow layer under the progress bar -->
              <div 
                class="absolute top-0 left-0 h-full rounded-full blur-[3px] opacity-60 transition-all duration-1000" 
                style="width: {shareProgress}%; background: linear-gradient(90deg, #ff2d55 0%, #ee4d2d 50%, rgba(238, 77, 45, 0) 100%);"
              ></div>
              <!-- Main filled progress bar with a comet fade-out tail -->
              <div 
                class="absolute top-0 left-0 h-full rounded-full overflow-hidden transition-all duration-1000" 
                style="width: {shareProgress}%; background: linear-gradient(90deg, #ff2d55 0%, #ee4d2d 75%, rgba(238, 77, 45, 0.15) 100%);"
              >
                <!-- Liquid light sweep animation removed for static display -->
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent"></div>
              </div>
              <!-- Glowing neon active beacon at the progress tip -->
              <div 
                class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 transition-all duration-1000 pointer-events-none" 
                style="left: {shareProgress}%"
              >
                <span class="relative flex h-3.5 w-3.5">
                  <span class="relative inline-flex rounded-full h-3.5 w-3.5 bg-rose-500 shadow-[0_0_8px_#ff2d55]"></span>
                </span>
              </div>
            </div>
          </div>
        </div>
      {:else}
        <!-- Reveal State Minimalist -->
        <div class="p-3 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-between">
           <div class="flex flex-col">
             <span class="text-[10px] font-bold text-rose-600 mb-0.5">Mục tiêu đã đạt 🎉</span>
             <span class="text-[11px] text-slate-600">Mọi người đều có thể dùng mã này!</span>
           </div>
           <div class="flex items-center gap-2 bg-white px-2 py-1.5 rounded border border-rose-100">
             <span class="font-bold text-rose-600 text-xs font-mono">{voucherCode}</span>
             <button onclick={() => {
               if (voucherCode) {
                 navigator.clipboard.writeText(voucherCode);
                 onShareComplete?.();
               }
             }} class="text-slate-400 hover:text-rose-500"><Copy size={12} /></button>
           </div>
        </div>
      {/if}
    {/if}
  </div>
</div>
{/if}

<style>
  :global(.vsb-heart-burst) { position: fixed; pointer-events: none; z-index: var(--z-particle); transform: translate(-50%, -50%); }
  :global(.vsb-heart-particle) { position: absolute; font-size: 14px; animation: heart-fly 0.8s ease-out forwards; opacity: 0; }
  @keyframes heart-fly {
    0% { transform: translate(0,0) scale(0.5); opacity: 1; }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 60px), calc(sin(calc(var(--i) * 45deg)) * 60px)) scale(1.2); opacity: 0; }
  }
  @keyframes viral-flow {
    0% { transform: translateX(-150%); }
    50% { transform: translateX(150%); }
    100% { transform: translateX(150%); }
  }
  .animate-viral-flow {
    animation: viral-flow 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  }

  /* Elite V2.2: Gold Glitter Confetti for CTV Success */
  :global(.vsb-gold-burst) { position: fixed; pointer-events: none; z-index: 10000; transform: translate(-50%, -50%); }
  :global(.vsb-gold-particle) { position: absolute; font-size: 16px; animation: gold-fly 1s cubic-bezier(0.12, 0, 0.39, 0) forwards; opacity: 0; animation-delay: var(--delay, 0s); }
  @keyframes gold-fly {
    0% { transform: translate(0,0) scale(0); opacity: 0; }
    20% { opacity: 1; transform: translate(0,0) scale(1.2); }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 80px), calc(sin(calc(var(--i) * 45deg)) * -60px - 20px)) scale(0.6); opacity: 0; }
  }

  /* Shimmer animations */
  @keyframes shimmer-fast {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  .animate-shimmer-fast {
    animation: shimmer-fast 1.5s linear infinite;
  }

  /* Slide Up animation for Popover */
  @keyframes slide-up {
    0% { opacity: 0; transform: translateY(8px) scale(0.95); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
  }
  .animate-slide-up {
    animation: slide-up 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }
</style>
