<script lang="ts">
    import Facebook from "@lucide/svelte/icons/facebook";
  import Copy from "@lucide/svelte/icons/copy";
  import Heart from "@lucide/svelte/icons/heart";
  import Zap from "@lucide/svelte/icons/zap";
  import Gift from "@lucide/svelte/icons/gift";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Check from "@lucide/svelte/icons/check";
  import Loader from "@lucide/svelte/icons/loader";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import type { Product, Voucher } from '$lib/types';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';

  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';

  interface Props {
    product: Product;
    timer_prefix?: string;
    onUnlock?: () => void;
  }

  let { product, timer_prefix = "Ưu đãi đặc quyền kết thúc sau:", onUnlock }: Props = $props();
  const clientUi = getClientUi();
  const shopStore = getShopStore();
  const timeLeft = $derived(shopStore.timeLeft);

  const formatTime = (s: number): string => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const viralSuite = $derived(product.metadata?.viral_suite ?? null);
  const promoConfig = $derived(
    viralSuite?.share_promotion ?? 
    product.metadata?.share_promotion ?? 
    null
  );
  
  const shareCount = $derived(
    viralSuite?.share_count ?? (typeof product.metadata?.share_count === 'number' ? product.metadata.share_count : 0)
  );
  const shareTarget = $derived(
    viralSuite?.share_target ?? (typeof product.metadata?.share_target === 'number' ? product.metadata.share_target : 0)
  );
  const shareProgress = $derived(
    shareTarget > 0 ? Math.min((shareCount / shareTarget) * 100, 100) : (shareCount > 0 ? 100 : 0)
  );

  let campaignData = $state<any>(null);
  let isCampaignLoaded = $state(false);

  $effect(() => {
    const vId = promoConfig?.voucher_id;
    if (vId && !isCampaignLoaded) {
      isCampaignLoaded = true;
      fetch(`/api/v1/client/viral/campaign/${vId}`)
        .then(res => res.json())
        .then(data => { campaignData = data; })
        .catch(() => {});
    }
  });

  const displayRewardLabel = $derived(
    campaignData?.voucher_label || 
    viralSuite?.share_reward_label || 
    promoConfig?.voucher_label ||
    promoConfig?.reward_label ||
    'ƯU ĐÃI LAN TỎA'
  );

  const subDescription = $derived(
    campaignData?.voucher_subtitle || 
    campaignData?.share_text || 
    promoConfig?.voucher_subtitle || 
    promoConfig?.share_text || 
    ''
  );

  const ctaText = $derived(
    campaignData?.cta_text || 
    viralSuite?.share_cta || 
    promoConfig?.cta_text ||
    'NHẬN'
  );


  // ── State Machine ──────────────────────────────────────────────────────────
  type Step = 'idle' | 'sharing' | 'verifying' | 'revealed' | 'error';
  let step = $state<Step>('idle');
  let errorMsg = $state('');
  let voucherCode = $state<string | null>(null);
  let voucherLabel = $state<string | null>(null);
  let codeCopied = $state(false);

  // Elite V2.2: Centralized Favorite Management
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const baseLikeCount = $derived(Number(viralSuite?.likes_count || product.metadata?.likes || 0));
  const localLikeCount = $derived(baseLikeCount + (isLiked ? 1 : 0));

  let _token = $state<string | null>(null);
  let _fingerprint = $state<string | null>(null);
  
  // Viral 2026 Telemetry State
  let shareStartTime = $state<number>(0);
  let timeOnPageMs = $state<number>(0);
  let visibilityChanges = $state<number>(0);
  let maxScrollY = $state<number>(0);
  let interactionCount = $state<number>(0);
  let shareMethod = $state<'native' | 'popup' | 'clipboard'>('unknown');
  let popupWasBlocked = $state<boolean>(false);
  let mouseAcceleration = $state<number>(0);
  let interactionRhythm = $state<number>(0);
  let honeypotTriggered = $state<boolean>(false);
  
  let _lastMouseX = 0, _lastMouseY = 0, _lastMouseTime = 0;
  let _clickTimes: number[] = [];
  
  const initTime = Date.now();

  // ── Elite V2.2: Focus Listeners & Verification Controls ──────────────────────
  import { onDestroy } from 'svelte';
  let hasRegisteredListeners = false;
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let popupWindow: Window | null = null;
  let verifyAttempts = 0;
  let isVerifying = false;

  const handleFocus = () => {
    cleanupFocusListeners();
    if (step !== 'revealed') attemptVerify();
  };

  const handleVisibilityChange = () => {
    if (!document.hidden) {
      cleanupFocusListeners();
      if (step !== 'revealed') attemptVerify();
    }
  };

  function cleanupFocusListeners() {
    if (hasRegisteredListeners) {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      hasRegisteredListeners = false;
    }
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  const attemptVerify = async () => {
    if (isVerifying || step === 'revealed' || verifyAttempts >= 3) return;
    const elapsed = Date.now() - shareStartTime;
    if (elapsed < 4000) return; // Too fast to be a real share
    
    isVerifying = true;
    verifyAttempts++;
    try {
      await viralActions.verify();
    } catch (e) {
      // Failed, let them try again by focusing
    } finally {
      isVerifying = false;
    }
  };

  onDestroy(() => {
    cleanupFocusListeners();
  });

  const isVoucherApplied = $derived(
    promoConfig?.voucher_id && shopStore.selectedVoucherIds.includes(promoConfig.voucher_id)
  );

  // 🛡️ Military-Grade: Restore state from HTTP-Only cookie (via SSR unlockedVoucherIds)
  $effect(() => {
    const onVisibilityChange = () => { 
      if (document.hidden) visibilityChanges++; 
    };
    const onBlur = () => {
      visibilityChanges++;
    };
    const onClick = () => {
      interactionCount++;
      _clickTimes.push(Date.now());
      if (_clickTimes.length > 2) {
        const diffs = _clickTimes.slice(1).map((t, i) => t - _clickTimes[i]);
        const mean = diffs.reduce((a,b) => a+b, 0) / diffs.length;
        interactionRhythm = diffs.reduce((a,b) => a + Math.pow(b - mean, 2), 0) / diffs.length;
      }
    };
    const onMouseMove = (e: MouseEvent) => {
      const now = Date.now();
      if (_lastMouseTime > 0) {
        const dt = (now - _lastMouseTime) / 1000;
        if (dt > 0) {
          const dx = e.clientX - _lastMouseX;
          const dy = e.clientY - _lastMouseY;
          const v = Math.sqrt(dx*dx + dy*dy) / dt;
          if (v > mouseAcceleration) mouseAcceleration = v;
        }
      }
      _lastMouseX = e.clientX;
      _lastMouseY = e.clientY;
      _lastMouseTime = now;
    };
    const onScroll = () => {
        const scrolled = window.scrollY;
        if (scrolled > maxScrollY) maxScrollY = scrolled;
    };

    document.addEventListener('visibilitychange', onVisibilityChange);
    window.addEventListener('blur', onBlur);
    document.addEventListener('click', onClick);
    window.addEventListener('mousemove', onMouseMove, { passive: true });
    window.addEventListener('scroll', onScroll, { passive: true });
    
    // Check if voucher was already unlocked (cookie-backed, server-injected, bound to product)
    if (promoConfig?.voucher_id && product?.id && shopStore.unlockedVoucherIds.includes(`${product.id}_${promoConfig.voucher_id}`)) {
      const existingVoucher = shopStore.vouchers.find(v => v.id === promoConfig.voucher_id);
      if (existingVoucher) {
        voucherCode = existingVoucher.code || existingVoucher.id;
        voucherLabel = existingVoucher.title || 'MÃ QUÀ TẶNG VIRAL';
        step = 'revealed';
      }
    }
    
    return () => {
        document.removeEventListener('visibilitychange', onVisibilityChange);
        window.removeEventListener('blur', onBlur);
        document.removeEventListener('click', onClick);
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('scroll', onScroll);
    };
  });

  function handleLike(e: MouseEvent) {
    e.preventDefault();
    if (!product?.id) return;

    const wasLiked = isLiked;
    wishlistStore.toggle(product.id);

    if (!wasLiked) {
      createHeartConfetti(e.clientX, e.clientY);
    }
  }

  const viralActions = {
    async share(platform: string) {
      if (step !== 'idle' && step !== 'error') return;
      step = 'sharing';
      
      try {
        const res = await fetch('/api/v1/client/viral/share-intent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_id: product.id }),
        });
        if (!res.ok) throw new Error('Yêu cầu thất bại');
        const data = await res.json();
        _token = data.token;
        _fingerprint = data.fingerprint;
        
        shareStartTime = Date.now();
        timeOnPageMs = shareStartTime - initTime;

        // Reset verify attempts for a new share sequence
        verifyAttempts = 0;

        // Viral 2026: Auto-detect share method
        if (navigator.share && /mobile|android|iphone/i.test(navigator.userAgent)) {
            shareMethod = 'native';
            try {
                await navigator.share({
                    title: product.name,
                    text: `Xem ngay ưu đãi ${voucherLabel || ''} tại Osmo!`,
                    url: window.location.href
                });
                // Promise resolved = user picked an app. Auto verify!
                await viralActions.verify();
            } catch (err: unknown) {
                if (err.name === 'AbortError') {
                    throw new Error('Bạn đã hủy chia sẻ');
                }
                throw err; // Fallback
            }
        } else {
            shareMethod = 'popup';
            // Desktop fallback: Open popup and detect when they come back
            const w = 600;
            const h = 400;
            const left = (window.innerWidth / 2) - (w / 2);
            const top = (window.innerHeight / 2) - (h / 2);
            const cleanUrl = window.location.origin + window.location.pathname;
            const shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(cleanUrl)}`;
            
            // Clean up old listeners before creating new ones
            cleanupFocusListeners();

            popupWindow = window.open(shareUrl, 'Share', `toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=${w}, height=${h}, top=${top}, left=${left}`);
            
            if (!popupWindow || popupWindow.closed || typeof popupWindow.closed === 'undefined') {
                popupWasBlocked = true;
                // If popup blocked, let's just try to verify anyway, AI will handle
                setTimeout(() => viralActions.verify(), 2000);
            } else {
                // Poll popup closure
                pollTimer = setInterval(() => {
                    if (popupWindow && popupWindow.closed) {
                        cleanupFocusListeners();
                        const elapsed = Date.now() - shareStartTime;
                        if (elapsed < 1500) {
                            // Firefox isolation detected. Popup is actually still open.
                            // Rely strictly on focus events when they return to the main window.
                            if (!hasRegisteredListeners) {
                                hasRegisteredListeners = true;
                                window.addEventListener('focus', handleFocus);
                                document.addEventListener('visibilitychange', handleVisibilityChange);
                            }
                        } else {
                            // Normal browser, popup legitimately closed.
                            attemptVerify();
                        }
                    }
                }, 500);
            }
        }
      } catch (e: unknown) {
        errorMsg = e instanceof Error ? e.message : 'Lỗi chia sẻ';
        step = 'error';
      }
    },
    async verify() {
      if (!_token || !_fingerprint || !promoConfig) return;
      if (step === 'revealed') return;
      
      const shareDurationMs = Date.now() - shareStartTime;
      const scrollDepthPct = Math.min(100, Math.round((maxScrollY / (document.documentElement.scrollHeight - window.innerHeight || 1)) * 100));

      step = 'verifying';
      try {
        const res = await fetch('/api/v1/client/viral/verify-share', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            product_id: product.id, 
            fingerprint: _fingerprint, 
            token: _token, 
            voucher_id: promoConfig.voucher_id,
            telemetry: {
                time_on_page_ms: timeOnPageMs,
                share_duration_ms: shareDurationMs,
                visibility_changes: visibilityChanges,
                scroll_depth_pct: scrollDepthPct,
                interaction_count: interactionCount,
                share_method: shareMethod,
                popup_was_blocked: popupWasBlocked,
                mouse_acceleration: mouseAcceleration,
                interaction_rhythm: interactionRhythm,
                honeypot_triggered: honeypotTriggered
            }
          }),
        });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            let errMsg = 'Mã xác nhận không hợp lệ hoặc đã hết hạn. Vui lòng chia sẻ lại.';
            if (errData) {
                if (typeof errData.detail === 'string') {
                    errMsg = errData.detail;
                } else if (Array.isArray(errData.detail) && errData.detail[0]?.message) {
                    errMsg = errData.detail[0].message;
                } else if (typeof errData.error === 'string') {
                    errMsg = errData.error;
                } else if (typeof errData.message === 'string') {
                    errMsg = errData.message;
                }
            }
            throw new Error(errMsg);
        }
        const data = await res.json();
        voucherCode = data.voucher_code;
        voucherLabel = data.voucher_label;
        
        const newVoucher: Voucher = {
            id: promoConfig.voucher_id,
            code: voucherCode || '',
            title: voucherLabel || '',
            value: data.voucher_value,
            type: data.voucher_type,
            min_spend: data.min_spend,
            is_default: false
        };
        
        if (!shopStore.vouchers.find(v => v.id === newVoucher.id)) {
            shopStore.vouchers = [...shopStore.vouchers, newVoucher];
        }

        step = 'revealed';
        
        // 🛡️ Military-Grade: Mark as unlocked in ShopStore (cookie already set by server response)
        shopStore.unlockVoucher(newVoucher.id);
        // Re-trigger setVouchers to include the viral voucher now that it's unlocked
        shopStore.setVouchers(shopStore.vouchers);
        
        // 🔥 AUTO-APPLY TỨC THÌ
        if (!shopStore.selectedVoucherIds.includes(newVoucher.id)) {
            shopStore.toggleVoucher(newVoucher.id);
        }

        onUnlock?.();
        createHeartConfetti(window.innerWidth / 2, window.innerHeight / 2);
        clientUi.showToast(`🎉 Đã áp dụng mã ${voucherCode}!`, 'success');
      } catch (e: unknown) {
        const errMsg = e instanceof Error ? e.message : String(e);
        errorMsg = errMsg;
        step = 'error';
        
        // Elite V2.2: Professional transparent toast and clean logs
        clientUi.showToast(errMsg, 'error');
        console.groupCollapsed('⚠️ [Osmo Viral Verify] Xác thực lượt chia sẻ không thành công');
        console.warn(`Chi tiết: ${errMsg}`);
        console.warn(`Telemetry state: token=${_token ? _token.slice(0, 8) + '...' : 'none'}`);
        console.groupEnd();
      }
    }
  };

  async function copyLink() {
    await copyViralLink(window.location.href);
  }

  function applyVoucher() {
    if (!promoConfig?.voucher_id) return;
    if (!shopStore.selectedVoucherIds.includes(promoConfig.voucher_id)) {
        shopStore.toggleVoucher(promoConfig.voucher_id);
        clientUi.showToast(`🎉 Đã áp dụng mã ${voucherCode} thành công!`, 'success');
    }
  }
</script>

<div class="vfl-root">
  <!-- Canary Trap / Honeypot: Hidden from real users but bots will interact with it -->
  <input 
    class="vfl-honeypot" 
    type="text"
    name="discount_field_hidden"
    autocomplete="off"
    style="position: absolute; top: -9999px; left: -9999px; opacity: 0; pointer-events: none; width: 0; height: 0;"
    aria-hidden="true" 
    tabindex="-1"
    onfocus={() => { honeypotTriggered = true; }}
    oninput={() => { honeypotTriggered = true; }}
  />
  
  <!-- 🚀 Elite Viral Header (Master Row) -->
  <div class="vfl-master-row">
    <div class="vfl-socials">
      <button onclick={() => viralActions.share('facebook')} class="vfl-social-btn fb" title="Chia sẻ Facebook">
        <Facebook size={12} fill="currentColor" />
      </button>
      <button onclick={() => viralActions.share('zalo')} class="vfl-social-btn zalo" title="Chia sẻ Zalo">
        <span class="text-[8px] font-bold">Zalo</span>
      </button>
      <button onclick={copyLink} class="vfl-social-btn copy" title="Sao chép link">
        <Copy size={12} />
      </button>
    </div>

        <div class="vfl-progress-area">
           <div class="vfl-progress-info">
             <div class="flex flex-col">
               <span class="vfl-reward-text">{displayRewardLabel}</span>
               {#if subDescription}
                 <span class="text-[8px] text-white/40 font-bold tracking-tight">{subDescription}</span>
               {/if}
             </div>
             <span class="vfl-progress-val">{Math.round(shareProgress)}%</span>
           </div>
           <div class="vfl-progress-track">
             <div class="h-1 w-full bg-white/5 rounded-full relative">
               <!-- Glow shadow layer under the progress bar -->
               <div 
                 class="absolute top-0 left-0 h-full rounded-full blur-[2px] opacity-60 transition-all duration-1000" 
                 style="width: {shareProgress}%; background: linear-gradient(90deg, #ff2d55 0%, #ee4d2d 50%, rgba(238, 77, 45, 0) 100%);"
               ></div>
               <!-- Main filled progress bar with a comet fade-out tail -->
               <div 
                 class="absolute top-0 left-0 h-full rounded-full overflow-hidden transition-all duration-1000" 
                 style="width: {shareProgress}%; background: linear-gradient(90deg, #ff2d55 0%, #ee4d2d 75%, rgba(238, 77, 45, 0.15) 100%);"
               >
                 <!-- Liquid light sweep animation -->
                 <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-viral-flow"></div>
               </div>
               <!-- Glowing neon active beacon at the progress tip -->
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

    <button onclick={handleLike} class="vfl-like-pill" class:liked={isLiked}>
      <Heart size={12} fill={isLiked ? '#ee4d2d' : 'none'} color={isLiked ? '#ee4d2d' : '#fff'} />
      <span class="vfl-like-count">{formatViralCount(localLikeCount)}</span>
    </button>
  </div>

  <!-- 🎫 Viral Redemption Funnel -->
  <div class="vfl-redemption">
    <div class="vfl-ticket-box" class:revealed={step === 'revealed'}>
      <!-- Ticket Notches -->
      <div class="ticket-notch notch-l"></div>
      <div class="ticket-notch notch-r"></div>

      {#if step === 'idle' || step === 'error'}
        <div class="ticket-inner">
          <div class="flex flex-col gap-0.5">
            <div class="flex items-center gap-2">
              <Gift size={16} class="text-[#ee4d2d]" />
              <span class="ticket-msg">{displayRewardLabel}</span>
            </div>
            {#if subDescription}
              <span class="text-[8px] text-white/30 font-bold ml-6">{subDescription}</span>
            {/if}
          </div>
          
          <div class="flex items-center gap-3">
            <div class="vfl-timer-tag">
              <span class="font-black">{formatTime(timeLeft)}</span>
            </div>
            <button class="ticket-btn-primary" onclick={() => viralActions.share('facebook')}>
              <span>{ctaText}</span>
              <ExternalLink size={12} />
            </button>
          </div>
        </div>
        {#if errorMsg}
          <div class="vfl-error-msg">{errorMsg}</div>
        {/if}
      {:else if step === 'sharing' || step === 'verifying'}
        <div class="vfl-center py-2">
          <Loader size={14} class="animate-spin text-[#ee4d2d]" />
          <span class="vfl-status-text">{step === 'sharing' ? 'ĐANG KẾT NỐI...' : 'AI ĐANG XÁC MINH...'}</span>
        </div>
      {:else if step === 'revealed'}
        <div class="ticket-inner revealed">
          <div class="flex items-center gap-3">
            <Sparkles size={16} class="text-amber-400" />
            <div class="flex flex-col">
              <span class="text-[8px] text-white/40 font-black tracking-widest">{voucherLabel}</span>
              <span class="text-lg font-black text-[#ee4d2d] tabular-nums tracking-wider">{voucherCode}</span>
            </div>
          </div>
          <button class="vfl-apply-pill" onclick={applyVoucher} disabled={isVoucherApplied}>
            {#if isVoucherApplied}
              <Check size={14} />
              <span>ĐÃ ÁP DỤNG</span>
            {:else}
              <Zap size={14} fill="currentColor" />
              <span>SỬ DỤNG NGAY</span>
            {/if}
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .vfl-root {
    width: 100%;
    max-width: 580px;
    background: #0a0a0a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
    position: relative;
    overflow: hidden;
  }

  /* --- Master Action Row --- */
  .vfl-master-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 0 4px;
  }
  
  .vfl-socials { display: flex; gap: 6px; }
  .vfl-social-btn {
    width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.1);
    color: white; cursor: pointer; transition: all 0.2s;
  }
  .vfl-social-btn:hover { background: rgba(255, 255, 255, 0.15); transform: translateY(-1px); }
  .vfl-social-btn.fb { color: #1877f2; }
  .vfl-social-btn.zalo { color: #0068ff; }
  
  .vfl-progress-area { flex: 1; display: flex; flex-direction: column; gap: 4px; }
  .vfl-progress-info { display: flex; justify-content: space-between; align-items: center; }
  .vfl-reward-text { 
    font-size: 10px; font-weight: 700; color: rgba(255, 255, 255, 0.6); 
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
    max-width: 160px;
  }
  .vfl-progress-val { font-size: 10px; font-weight: 900; color: #ee4d2d; }
  
  .vfl-progress-track { 
    height: 12px; 
    position: relative; 
    display: flex;
    align-items: center;
    overflow: visible;
  }
  @keyframes viral-flow {
    0% { transform: translateX(-150%); }
    50% { transform: translateX(150%); }
    100% { transform: translateX(150%); }
  }
  .animate-viral-flow {
    animation: viral-flow 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  }

  .vfl-like-pill {
    display: flex; align-items: center; gap: 6px; background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1); padding: 4px 10px; border-radius: 100px;
    color: white; cursor: pointer;
  }
  .vfl-like-pill.liked { border-color: rgba(238, 77, 45, 0.4); background: rgba(238, 77, 45, 0.1); }
  .vfl-like-count { font-size: 11px; font-weight: 900; }

  /* --- Ticket Redemption Area --- */
  .vfl-ticket-box {
    width: 100%; height: 54px; position: relative; background: rgba(255, 255, 255, 0.02);
    border: 1.5px dashed rgba(238, 77, 45, 0.3); border-radius: 8px;
    display: flex; align-items: center; overflow: visible;
  }
  .vfl-ticket-box.revealed { border-style: solid; border-color: #ee4d2d; background: rgba(238, 77, 45, 0.05); }

  .ticket-notch {
    position: absolute; top: 50%; width: 12px; height: 12px; background: #000;
    border-radius: 50%; transform: translateY(-50%); z-index: 10;
    border: 1.5px dashed rgba(238, 77, 45, 0.3);
  }
  .notch-l { left: -7px; }
  .notch-r { right: -7px; }

  .ticket-inner { width: 100%; height: 100%; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; }
  .ticket-msg { font-size: 13px; font-weight: 1000; color: white; }
  
  .vfl-timer-tag {
    background: #ee4d2d; color: white; padding: 2px 8px; border-radius: 4px;
    font-size: 10px; font-weight: 900; tabular-nums: true;
    box-shadow: 0 4px 10px rgba(238, 77, 45, 0.4);
  }

  .ticket-btn-primary {
    background: #ee4d2d; color: white; padding: 6px 14px; border-radius: 6px;
    font-size: 11px; font-weight: 1000; border: none; cursor: pointer;
    display: flex; align-items: center; gap: 6px; transition: all 0.2s;
  }
  .ticket-btn-primary:active { transform: scale(0.95); }

  /* --- Revealed State --- */
  .vfl-apply-pill {
    background: #ee4d2d; color: #fff; padding: 6px 14px; border-radius: 6px;
    font-size: 10px; font-weight: 1000; display: flex; align-items: center; gap: 6px; border: none;
    cursor: pointer; transition: all 0.2s; box-shadow: 0 4px 10px rgba(238, 77, 45, 0.4);
  }
  .vfl-apply-pill:active { transform: scale(0.95); }
  .vfl-apply-pill:disabled { background: #4caf50; cursor: default; transform: none; box-shadow: none; opacity: 1; color: white; }

  /* --- Status Overlays --- */
  .vfl-center { width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px; }
  .vfl-status-text { font-size: 10px; font-weight: 900; color: #ee4d2d; letter-spacing: 0.1em; }

  .vfl-confirm-overlay { width: 100%; height: 100%; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; }
  .vfl-confirm-msg { font-size: 11px; font-weight: 1000; color: white; letter-spacing: 0.05em; }
  
  .vfl-btn-secondary { height: 28px; padding: 0 12px; background: rgba(255,255,255,0.05); color: #999; border: none; border-radius: 4px; font-size: 10px; font-weight: 800; cursor: pointer; }
  .vfl-btn-primary { height: 28px; padding: 0 12px; background: #ee4d2d; color: white; border: none; border-radius: 4px; font-size: 10px; font-weight: 1000; cursor: pointer; }

  .vfl-error-msg { position: absolute; bottom: -18px; left: 50%; transform: translateX(-50%); font-size: 8px; color: #ef4444; font-weight: 800; white-space: nowrap; }
</style>
