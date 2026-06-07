<script lang="ts">
  import { fetchViralCampaign } from '$lib/utils/viralCampaignCache';
  import Heart from "@lucide/svelte/icons/heart";
  import Instagram from "@lucide/svelte/icons/instagram";
  import Send from "@lucide/svelte/icons/send";
  import Twitter from "@lucide/svelte/icons/twitter";
  import Facebook from "@lucide/svelte/icons/facebook";
  import Copy from "@lucide/svelte/icons/copy";
  import Zap from "@lucide/svelte/icons/zap";
  import type { Product } from '$lib/types';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti, getProductLikeCount,
    getProductShareCount, getProductShareTarget, getProductShareProgress
  } from '$lib/utils/commerce/viral';
  import { formatCurrency } from '$lib/utils/format';
  import { fade, scale } from 'svelte/transition';
  import { SHOP_CONFIG } from '$lib/constants/shop';

  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { checkinStore } from '$lib/state/commerce/checkin.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { apiClient } from '$lib/utils/apiClient';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';

  interface Props {
    product: Product;
    variant?: 'mobile' | 'funnel';
    likeCount?: number;
    hideLikes?: boolean;
    scrolled?: boolean;
    forceHidden?: boolean;
    scrollRatio?: number;
    hideRatio?: number;
    dark?: boolean;
    onShareComplete?: () => void;
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

  const activationMsg = $derived(campaignData?.cta_text || 'Cùng nhau chia sẻ!');
  const campaignDesc = $derived(campaignData?.share_text || 'Cùng cộng đồng lan tỏa để nhận mã giảm giá đặc biệt!');
  const displayRewardLabel = $derived(campaignData?.voucher_label || 'Ưu đãi lan tỏa');
  const voucherCode = $derived(shareProgress >= 100 ? (campaignData?.voucher_id || 'OPEN') : null);

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
    if (browser) {
      checkinStore.fetchStatus().catch(() => {});
    }
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

{#if (campaignExists && promoConfig?.voucher_id) || isCtv || variant === 'inline'}
<div class="w-full font-sans relative group z-10" class:opacity-60={isCollapsed && variant !== 'inline'} class:opacity-0={isHidden && variant !== 'inline'} class:pointer-events-none={isHidden && variant !== 'inline'}>
  {#if variant === 'inline'}
    <!-- Inline Clean Style for White Background (Elite V2.2) -->
    <div class="flex flex-col w-full relative z-10">
      <div class="flex items-center justify-between gap-3">
        {#if !hideLikes}
          <button onclick={handleLike} class="flex items-center gap-1.5 group/like hover:scale-105 active:scale-95 transition-all">
            <Heart size={16} class="transition-transform {isLiked ? 'fill-rose-500 text-rose-500' : 'text-slate-400'}" />
            <span class="text-[11px] font-bold {isLiked ? 'text-rose-600' : 'text-slate-500'}">{formatViralCount(localLikeCount)}</span>
          </button>
          <div class="w-[1px] h-3.5 bg-slate-200 shrink-0"></div>
        {/if}

        <!-- Social Icons Group -->
        <button onclick={() => share('facebook')} class="text-slate-400 hover:text-[#1877f2] active:scale-90 transition-all" aria-label="Share Facebook"><Facebook size={16} class="fill-current" /></button>
        <button onclick={() => share('zalo')} class="text-slate-400 hover:text-[#0068ff] active:scale-90 transition-all font-black text-[10px]" aria-label="Share Zalo">Zalo</button>
        <button onclick={() => share('x')} class="text-slate-400 hover:text-black active:scale-90 transition-all" aria-label="Share X"><Twitter size={16} class="fill-current" /></button>
        <button onclick={() => share('instagram')} class="text-slate-400 hover:text-[#e4405f] active:scale-90 transition-all" aria-label="Share Instagram"><Instagram size={16} /></button>

        <div class="w-[1px] h-3.5 bg-slate-200 shrink-0"></div>

        <!-- Dynamic CTV Button (Personalized for status) -->
        {#if isCtv}
          <button 
            onclick={(e) => {
              e.preventDefault();
              showCtvPopover = true;
            }} 
            class="px-2 py-1 bg-gradient-to-r from-amber-500 to-luxury-copper text-stone-950 hover:from-amber-600 hover:to-amber-500 active:scale-95 transition-all rounded-lg font-black text-[8px] tracking-wider uppercase shrink-0 flex items-center gap-1 shadow-sm shadow-luxury-copper/20 relative overflow-hidden group" 
            aria-label="Copy CTV"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -translate-x-full group-hover:animate-shimmer-fast"></div>
            <Zap size={9} class="fill-stone-950 text-stone-950 animate-pulse" /> Kênh CTV - {activeRatePercent}
          </button>
        {:else}
          <button 
            onclick={(e) => {
              e.preventDefault();
              if (!authStore.isAuthenticated) {
                getClientUi().showToast('Vui lòng đăng nhập để tham gia CTV!', 'info');
                getClientUi().openLogin();
              } else {
                goto('/user/ctv');
              }
            }} 
            class="px-2 py-1 bg-amber-50 text-amber-800 border border-amber-200/60 active:scale-95 transition-all rounded-lg font-black text-[8px] tracking-wider uppercase shrink-0 flex items-center gap-1"
            aria-label="Đăng ký CTV"
          >
            🔥 Nhận {activeRatePercent}
          </button>
        {/if}

        <button onclick={copyLink} class="text-slate-400 hover:text-slate-900 active:scale-90 transition-all" aria-label="Copy Link"><Copy size={16} /></button>
      </div>

      <!-- FOMO Progress (Inline Light Style) -->
      {#if shareTarget > 0 && campaignExists && promoConfig?.voucher_id}
        {#if shareProgress < 100}
          <div class="mt-3 space-y-1.5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5 min-w-0">
                <div class="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse shrink-0"></div>
                <span class="text-[10px] text-slate-500 font-medium truncate leading-none">
                  {campaignDesc}
                </span>
              </div>
              <span class="text-[11px] font-black text-rose-500 shrink-0">{Math.round(shareProgress)}%</span>
            </div>
            <div class="relative w-full pt-1 pb-1.5 overflow-visible">
              <div class="h-1.5 w-full bg-slate-100 rounded-full relative">
                <div 
                  class="absolute top-0 left-0 h-full rounded-full blur-[2px] opacity-40 transition-all duration-1000" 
                  style="width: {shareProgress}%; background: linear-gradient(90deg, #ff2d55 0%, #d12a0f 50%, rgba(209, 42, 15, 0) 100%);"
                ></div>
                <div 
                  class="absolute top-0 left-0 h-full rounded-full overflow-hidden transition-all duration-1000" 
                  style="width: {shareProgress}%; background: linear-gradient(90deg, #ff2d55 0%, #d12a0f 75%, rgba(209, 42, 15, 0.15) 100%);"
                >
                  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-viral-flow"></div>
                </div>
                <div 
                  class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 transition-all duration-1000 pointer-events-none" 
                  style="left: {shareProgress}%"
                >
                  <span class="relative flex h-2.5 w-2.5">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500 shadow-[0_0_6px_#ff2d55]"></span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        {:else}
          <div class="mt-3 p-2.5 rounded-xl bg-rose-50/50 border border-rose-100/50 flex items-center justify-between">
            <div class="flex flex-col min-w-0">
              <span class="text-[9px] font-black text-rose-600 mb-0.5 tracking-wider uppercase">ĐÃ ĐẠT MỤC TIÊU 🎉</span>
              <span class="text-[10px] text-slate-500 truncate">Sử dụng mã giảm giá độc quyền ngay:</span>
            </div>
            <div class="flex items-center gap-1.5 bg-white px-2 py-1 rounded-lg border border-rose-100 shadow-sm shrink-0">
              <span class="font-bold text-rose-600 text-xs font-mono">{voucherCode}</span>
              <button onclick={() => voucherCode && navigator.clipboard.writeText(voucherCode)} class="text-slate-400 hover:text-rose-500 active:scale-90 transition-transform"><Copy size={11} /></button>
            </div>
          </div>
        {/if}
      {/if}
    </div>
  {:else if variant === 'funnel'}
    <div class="flex flex-col w-full relative z-10 transition-all duration-300">
      <!-- Actions Row (Premium Glass) -->
      <div class="relative z-10 flex items-center justify-between gap-2 mt-3 mb-2">
        <!-- Like Pill -->
        <button onclick={handleLike} class="flex items-center gap-1.5 px-4 py-2 rounded-xl transition-all active:scale-95 shrink-0 backdrop-blur-md {isLiked ? 'bg-rose-700 text-white shadow-lg shadow-rose-500/20' : 'bg-white/10 text-white/90 border border-white/10'}">
          <Heart size={14} class={isLiked ? 'fill-current' : ''} />
          <span class="text-xs font-bold">{formatViralCount(localLikeCount)}</span>
        </button>
 
        <!-- Social Icons Group (Liquid Glass) -->
        <div class="flex-1 flex items-center justify-around gap-2 px-3 py-2 bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl overflow-x-auto scrollbar-hide">
          <button onclick={() => share('facebook')} class="text-white/80 hover:text-white transition-all active:scale-90" aria-label="FB"><Facebook size={18} class="fill-current" /></button>
          <button onclick={() => share('zalo')} class="text-white/80 hover:text-white transition-all active:scale-90 font-bold text-[12px]" aria-label="Zalo">Zalo</button>
          <button onclick={() => share('x')} class="text-white/80 hover:text-white transition-all active:scale-90" aria-label="X"><Twitter size={18} class="fill-current" /></button>
          <button onclick={() => share('instagram')} class="text-white/80 hover:text-white transition-all active:scale-90" aria-label="IG"><Instagram size={18} /></button>
          
          {#if isCtv}
            <button 
              onclick={(e) => {
                e.preventDefault();
                showCtvPopover = true;
              }} 
              class="px-2 py-1 bg-gradient-to-r from-amber-500 to-luxury-copper text-stone-950 hover:from-amber-600 hover:to-amber-500 rounded-lg transition-all active:scale-95 font-black text-[9px] tracking-wider uppercase shrink-0 flex items-center gap-1 shadow-sm shadow-luxury-copper/20 relative overflow-hidden group" 
              aria-label="Copy CTV"
            >
              <!-- Shimmer light sweep -->
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -translate-x-full group-hover:animate-shimmer-fast"></div>
              <Zap size={10} class="fill-stone-950 text-stone-950 animate-pulse" /> Kênh CTV - {activeRatePercent}
            </button>
          {/if}

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
            <div class="relative w-full pt-1 pb-2 overflow-visible">
              <div class="h-1.5 w-full bg-white/10 rounded-full relative backdrop-blur-sm">
                <!-- Glow shadow layer under the progress bar -->
                <div 
                  class="absolute top-0 left-0 h-full rounded-full blur-[3px] opacity-60 transition-all duration-1000" 
                  style="width: {shareProgress}%; background: linear-gradient(90deg, #ff2d55 0%, #d12a0f 50%, rgba(209, 42, 15, 0) 100%);"
                ></div>
                <!-- Main filled progress bar with a comet fade-out tail -->
                <div 
                  class="absolute top-0 left-0 h-full rounded-full overflow-hidden transition-all duration-1000" 
                  style="width: {shareProgress}%; background: linear-gradient(90deg, #ff2d55 0%, #d12a0f 75%, rgba(209, 42, 15, 0.15) 100%);"
                >
                  <!-- Liquid light sweep animation -->
                  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-viral-flow"></div>
                </div>
                <!-- Glowing neon active beacon at the progress tip -->
                <div 
                  class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 transition-all duration-1000 pointer-events-none" 
                  style="left: {shareProgress}%"
                >
                  <span class="relative flex h-3.5 w-3.5">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-3.5 w-3.5 bg-rose-500 shadow-[0_0_8px_#ff2d55]"></span>
                  </span>
                </div>
              </div>
            </div>
          {:else}
            <div class="text-center bg-white/5 backdrop-blur-md p-3 rounded-xl border border-rose-500/30 animate-bounce-subtle">
              <div class="text-[11px] font-black text-rose-400 mb-2 tracking-widest">🎉 Mục tiêu đã đạt!</div>
              <div class="flex items-center justify-between bg-black/20 rounded-lg px-3 py-2 border border-white/10">
                <span class="font-mono text-lg font-black text-white tracking-wider">{voucherCode}</span>
                <button onclick={() => voucherCode && navigator.clipboard.writeText(voucherCode)} class="text-[10px] font-black bg-rose-700 text-white px-3 py-1.5 rounded-md shadow-lg active:scale-95 transition-transform">Copy</button>
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {:else}
    <!-- TikTok Vertical Floating Style -->
    <div 
      class="fixed right-3 top-[92px] z-[1000] flex flex-col items-center gap-3 transition-all duration-300" 
      style="
        opacity: {1 - hideRatio}; 
        transform: 
          translateX({scrollRatio * 16}px) 
          translateY({hideRatio * 50}px) 
          scale({1 - scrollRatio * 0.1 - hideRatio * 0.2});
        pointer-events: {hideRatio > 0.8 ? 'none' : 'auto'};
      "
    >
      {#if checkinStore.status?.is_event_enabled !== false}
        {@const hasCheckedIn = checkinStore.status?.is_checked_in_today ?? false}
        <button
          onclick={() => checkinStore.openPopup()}
          class="w-8 h-8 flex items-center justify-center relative active:scale-95 transition-all focus:outline-none group shrink-0"
          aria-label="Điểm danh nhận quà"
        >
          {#if !hasCheckedIn}
            <!-- Outer gold pulse rings (Only shown if NOT checked in yet today) -->
            <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-40 animate-ping"></div>
            <div class="absolute inset-0 rounded-full bg-[#FFD700] opacity-25 animate-ping" style="animation-delay: 0.5s"></div>
          {/if}

          <!-- Liquid gradient/glass gift circle -->
          <div
            class="relative w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg
              {hasCheckedIn 
                ? 'bg-white/30 border border-white/50 backdrop-blur-md' 
                : 'bg-gradient-to-br from-[#FFD700] to-[#F7B731] border border-[#FFD700]/30 shadow-[0_4px_10px_rgba(255,215,0,0.3)]'}"
          >
            <!-- Standard Gift Icon -->
            <svg class="w-5 h-5 {hasCheckedIn ? 'text-white drop-shadow-md' : 'text-white drop-shadow-[0_1.5px_3px_rgba(229,169,60,0.4)] animate-bounce-subtle'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 12v10H4V12" />
              <path d="M12 22V7" />
              <path d="M2 12h20" />
              <path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z" />
              <path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z" />
            </svg>
          </div>

          <!-- Badges -->
          {#if !hasCheckedIn}
            <span class="absolute -top-0.5 -right-0.5 px-1 py-0.5 bg-[#f44336] text-white rounded-full font-black text-[6.5px] scale-90 border border-white/20 shadow-md whitespace-nowrap animate-pulse">
              NHẬN
            </span>
          {:else}
            <!-- Checked in: Green checkmark badge on top right -->
            <div class="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 rounded-full flex items-center justify-center border border-white/50 shadow-md">
              <svg class="w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
          {/if}
        </button>
      {/if}

      <button aria-label="Chứng nhận" class="w-8 h-8 flex items-center justify-center relative active:scale-90 transition-transform drop-shadow-lg focus:outline-none" onclick={triggerVerify}>
        <img src={product?.metadata?.verified_badge_url || SHOP_CONFIG.default_badge_url} alt="Verified Badge" class="w-full h-full object-contain" />
      </button>
  
      <button aria-label="Thích" class="flex flex-col items-center gap-1 drop-shadow-lg active:scale-90 transition-transform" onclick={handleLike}>
        <div class="w-8 h-8 rounded-full flex items-center justify-center backdrop-blur-md transition-colors {isLiked ? 'bg-rose-500 shadow-[0_0_12px_rgba(244,63,94,0.4)]' : 'bg-white/30 border border-white/50'}">
           <Heart size={16} class={isLiked ? 'fill-white text-white' : 'text-white drop-shadow-md'} />
        </div>
        <span class="text-[10px] font-bold text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]">{formatViralCount(localLikeCount)}</span>
      </button>
  
      <div class="flex flex-col gap-2">
        <button aria-label="Chia sẻ Facebook" class="active:scale-90 transition-transform" onclick={() => share('facebook')}>
          <div class="w-8 h-8 rounded-full bg-white/30 backdrop-blur-md border border-white/50 flex items-center justify-center shadow-lg"><Facebook size={14} class="fill-white text-white drop-shadow-md" /></div>
        </button>
        <button aria-label="Chia sẻ Zalo" class="active:scale-90 transition-transform" onclick={() => share('zalo')}>
          <div class="w-8 h-8 rounded-full bg-white/30 backdrop-blur-md border border-white/50 flex items-center justify-center shadow-lg"><span class="text-[9px] font-black italic text-white drop-shadow-md tracking-tighter">Zalo</span></div>
        </button>
        
        {#if isCtv}
          <button 
            class="active:scale-95 transition-transform relative group" 
            onclick={(e) => {
              e.preventDefault();
              showCtvPopover = true;
            }} 
            title="Kênh Tiếp Thị CTV"
          >
            <div class="w-8 h-8 rounded-full bg-white/30 backdrop-blur-md border border-white/50 flex items-center justify-center shadow-lg relative overflow-hidden">
              <span class="text-[9.5px] font-black text-white drop-shadow-md tracking-wider">CTV</span>
            </div>
            <!-- Dynamic small badge showing % on floating bubble -->
            <span class="absolute -top-0.5 -right-1.5 px-1 py-0.5 bg-rose-700 text-white rounded-full font-black text-[6.5px] scale-90 shadow-md whitespace-nowrap">
              {activeRatePercent}
            </span>
          </button>
        {:else}
          <button 
            class="active:scale-95 transition-transform relative group" 
            onclick={(e) => {
              e.preventDefault();
              if (!authStore.isAuthenticated) {
                getClientUi().showToast('Vui lòng đăng nhập để tham gia CTV!', 'info');
                getClientUi().openLogin();
              } else {
                goto('/user/ctv');
              }
            }} 
            title="Đăng ký CTV - Nhận hoa hồng"
          >
            <div class="w-8 h-8 rounded-full bg-white/30 backdrop-blur-md border border-white/50 flex items-center justify-center shadow-lg relative overflow-hidden">
              <span class="text-[9.5px] font-black text-white drop-shadow-md tracking-wider">CTV</span>
            </div>
            <!-- Dynamic small badge showing % on floating bubble -->
            <span class="absolute -top-0.5 -right-1.5 px-1 py-0.5 bg-rose-700 text-white rounded-full font-black text-[6.5px] scale-90 shadow-md whitespace-nowrap">
              +{activeRatePercent}
            </span>
          </button>
        {/if}
 
        <button aria-label="Sao chép liên kết" class="active:scale-90 transition-transform" onclick={copyLink}>
          <div class="w-8 h-8 rounded-full bg-white/30 backdrop-blur-md border border-white/50 flex items-center justify-center shadow-lg"><Copy size={14} class="text-white drop-shadow-md" /></div>
        </button>
      </div>
    </div>
  {/if}
 
  <!-- Premium Centered Popover Modal for Mobile QR Code Sharing -->
  {#if showCtvPopover}
    <!-- Blurred overlay backdrop -->
    <div 
      onclick={() => showCtvPopover = false}
      class="fixed inset-0 bg-black/70 backdrop-blur-md z-[9999] flex items-center justify-center p-4 transition-all"
      transition:fade
    >
      <!-- Premium Glass Modal Box -->
      <div 
        onclick={(e) => e.stopPropagation()}
        class="w-full max-w-xs bg-stone-950 border border-stone-850 rounded-2xl p-5 shadow-2xl flex flex-col items-center text-center gap-4 relative overflow-hidden"
        transition:scale={{ duration: 250, start: 0.95 }}
      >
        <!-- Liquid color glow spheres in background -->
        <div class="absolute -top-16 -left-16 w-32 h-32 bg-amber-500/10 rounded-full blur-3xl"></div>
        <div class="absolute -bottom-16 -right-16 w-32 h-32 bg-luxury-copper/10 rounded-full blur-3xl"></div>

        <div class="flex flex-col items-center">
          <span class="text-[10px] tracking-[3px] font-black text-luxury-copper uppercase">KÊNH TIẾP THỊ CTV</span>
          <span class="text-[9px] text-stone-400 mt-1.5 px-2 leading-relaxed">Chia sẻ liên kết hoặc quét mã để tích lũy hoa hồng!</span>
        </div>

        <!-- Dynamic Commission Card (Premium TikTok/Shopee style) -->
        <div class="w-full p-2.5 bg-stone-900/50 border border-amber-500/20 rounded-xl flex flex-col gap-1 items-center">
          <span class="text-[9px] font-bold text-stone-400">Hoa hồng của bạn</span>
          <span class="text-sm font-black text-amber-400">{activeRatePercent}</span>
          <span class="text-[9px] font-medium text-stone-300">~{formatCurrency(estimatedCommission)} / sản phẩm</span>
        </div>

        <!-- QR Code Container with amber tones -->
        <div class="p-2 bg-white rounded-xl border border-amber-500/25 shadow-xl relative">
          <img 
            src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&color=78350f&data={encodeURIComponent(window.location.origin + window.location.pathname + '?ctv=' + ctvCode)}" 
            alt="CTV QR Code"
            class="w-36 h-36 object-contain rounded-lg"
          />
        </div>

        <div class="flex flex-col gap-2 w-full mt-1">
          <button 
            onclick={(e) => {
              copyCtvLink(e);
              showCtvPopover = false;
            }}
            class="w-full py-2.5 bg-gradient-to-r from-amber-500 to-luxury-copper text-stone-950 rounded-xl font-black text-[10px] tracking-[2px] uppercase shadow-lg active:scale-95 transition-all flex items-center justify-center gap-1.5"
          >
            <Copy size={12} class="fill-stone-950" /> SAO CHÉP LIÊN KẾT
          </button>
          <button 
            onclick={() => showCtvPopover = false}
            class="w-full py-2 bg-stone-900 hover:bg-stone-850 text-stone-400 border border-stone-800 rounded-xl text-[9px] font-bold tracking-[2px] uppercase transition-colors"
          >
            ĐÓNG
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
{/if}

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
</style>
