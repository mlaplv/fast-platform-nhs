<script lang="ts">
  import Gift from "@lucide/svelte/icons/gift";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Check from "@lucide/svelte/icons/check";
  import Copy from "@lucide/svelte/icons/copy";
  import Loader from "@lucide/svelte/icons/loader";
  import Zap from "@lucide/svelte/icons/zap";
  import Facebook from "@lucide/svelte/icons/facebook";
  import { fade, scale } from 'svelte/transition';
  
  // Types
  import type { Product } from '$lib/types';
  
  // States
  import { onMount, onDestroy, untrack } from 'svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';

  interface Props {
    product: Product;
    compact?: boolean;
    onUnlock?: () => void;
  }

  let { product, compact = false, onUnlock }: Props = $props();
  const clientUi = getClientUi();
  const shopStore = getShopStore();

  let isMounted = $state(false);
  onMount(() => {
    isMounted = true;
  });

  let progressPercent = $state(0);
  let progressInterval: ReturnType<typeof setInterval> | null = null;

  function startProgress() {
    if (progressInterval) clearInterval(progressInterval);
    progressPercent = 0;
    const duration = 4500;
    const intervalTime = 50;
    const stepAmount = (100 / (duration / intervalTime)) * 0.95; // run up to 95%
    progressInterval = setInterval(() => {
      if (progressPercent < 95) {
        progressPercent += stepAmount;
      }
    }, intervalTime);
  }

  function finishProgress() {
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
    progressPercent = 100;
  }

  /**
   * Elite V2.2: Share promotion config from product.metadata.viral_suite
   */
  const viralSuite = $derived(product.metadata?.viral_suite ?? null);

  const promoConfig = $derived(
    viralSuite?.share_promotion ?? 
    product.metadata?.share_promotion ?? 
    null
  );
  let campaignExists = $state(true);
  const isEnabled = $derived(
    promoConfig?.enabled === true && !!promoConfig?.voucher_id && campaignExists
  );

  const shareCount = $derived(
    viralSuite?.share_count ?? (typeof product.metadata?.share_count === 'number' ? product.metadata.share_count : 0)
  );

  // ── State Machine ──────────────────────────────────────────────────────────
  type Step = 'idle' | 'sharing' | 'verifying' | 'revealed' | 'error';
  let step = $state<Step>('idle');
  let verificationText = $state('AI đang xác minh...');

  let _token = $state<string | null>(null);
  let _fingerprint = $state<string | null>(null);

  let voucherCode = $state<string | null>(null);
  let voucherLabel = $state<string | null>(null);

  let codeCopied = $state(false);
  let errorMsg = $state('');
  let activePlatform = $state<string>('facebook');

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
  let showFlyGhost = $state(false);

  // ── Elite V2.2: Focus Listeners & Verification Controls ──────────────────────
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
    if (elapsed < 4000) {
      errorMsg = 'Vui lòng dành thêm chút thời gian để chia sẻ nhé!';
      step = 'error';
      return;
    }
    
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
    if (progressInterval) {
      clearInterval(progressInterval);
    }
  });

  $effect(() => {
    // Elite V2.2: Reset local states when product changes (track ONLY product.id)
    product.id;
    untrack(() => {
      step = 'idle';
      voucherCode = null;
      voucherLabel = null;
      errorMsg = '';
      isCampaignLoaded = false;
      campaignData = null;
    });

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
          if (v > mouseAcceleration) mouseAcceleration = v; // Track max velocity/acceleration proxy
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

    if (typeof window !== 'undefined') {
      const isCookieUnlocked = promoConfig?.voucher_id && shopStore?.unlockedVoucherIds?.includes(`${product.id}_${promoConfig.voucher_id}`);
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      
      if (saved) {
        // Priority: localStorage (most complete, has value/type/min_spend from verify)
        try {
          const data = JSON.parse(saved);
          
          // Elite V2.2: Nếu mã đã lưu khác với mã đang hoạt động được backend hydrate -> dọn sạch cache cũ để tự động chuyển dịch sang mã mới
          if (promoConfig?.voucher_id && data.code !== promoConfig.voucher_id) {
            localStorage.removeItem(`viral_unlocked_${product.id}`);
            voucherCode = null;
            voucherLabel = null;
          } else {
            voucherCode = data.code;
            voucherLabel = data.label;
            // Re-inject into store so voucher shows at top of list, auto-applied
            shopStore?.injectViralVoucher(
              data.code,
              data.label,
              data.value ?? 0,
              data.type ?? 'FIXED',
              data.min_spend ?? 0
            );
            step = 'revealed'; // Hides ShareToUnlock component completely
          }
        } catch {
          localStorage.removeItem(`viral_unlocked_${product.id}`);
        }
      } else if (isCookieUnlocked && promoConfig?.voucher_id) {
        // Cookie unlock fallback (server-side verified)
        const existingVoucher = shopStore?.vouchers?.find(v => v.id === promoConfig.voucher_id);
        if (existingVoucher) {
          shopStore?.injectViralVoucher(
            existingVoucher.id,
            existingVoucher.title || 'Voucher đặc quyền',
            existingVoucher.value ?? 0,
            existingVoucher.type ?? 'FIXED',
            existingVoucher.min_spend ?? 0
          );
          step = 'revealed';
        }
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

  const viralActions = {
    async share(platform: string = 'facebook') {
      if (step !== 'idle' && step !== 'error') return;
      activePlatform = platform;
      step = 'sharing';
      startProgress();
      
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
                if (err instanceof Error && err.name === 'AbortError') {
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
            
            const encodedUrl = encodeURIComponent(cleanUrl);
            const platforms: Record<string, string> = {
              facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
              zalo: `https://sp.zalo.me/plugins/share?url=${encodedUrl}`,
              twitter: `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodeURIComponent(product.name)}`,
              tiktok: `https://www.tiktok.com/`
            };
            const shareUrl = platforms[platform] || platforms['facebook'];
            
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
        errorMsg = e instanceof Error ? e.message : String(e);
        step = 'error';
        finishProgress();
      }
    },
    async verify() {
      if (!_token || !_fingerprint || !promoConfig) return;
      if (step === 'revealed') return;
      
      const shareDurationMs = Date.now() - shareStartTime;
      const scrollDepthPct = Math.min(100, Math.round((maxScrollY / (document.documentElement.scrollHeight - window.innerHeight || 1)) * 100));

      step = 'verifying';
      startProgress();
      
      // Elite V2.2: Simulated AI Deep Verification Sequence
      const verificationSteps = [
        'Đang phân tích Social Graph...',
        'Kiểm tra tính nhất quán Metadata...',
        'Xác thực hành vi chia sẻ...',
        'Đối chiếu Telemetry thời gian thực...'
      ];
      
      let currentStepIdx = 0;
      const stepInterval = setInterval(() => {
        if (currentStepIdx < verificationSteps.length - 1) {
          currentStepIdx++;
          verificationText = verificationSteps[currentStepIdx];
        } else {
          clearInterval(stepInterval);
        }
      }, 1200);

      try {
        // Minimum wait time for AI "thinking" effect
        await new Promise(r => setTimeout(r, 4500));

        const res = await fetch('/api/v1/client/viral/verify-share', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            product_id: product.id, 
            fingerprint: _fingerprint, 
            token: _token, 
            voucher_id: promoConfig.voucher_id,
            telemetry: {
                time_on_page_ms: Math.round(timeOnPageMs),
                share_duration_ms: Math.round(shareDurationMs),
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
        
        clearInterval(stepInterval);
        
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
        // Save locally for persistence across refreshes
        localStorage.setItem(`viral_unlocked_${product.id}`, JSON.stringify({
          code: voucherCode, label: voucherLabel, unlocked_at: Date.now(),
          value: data.voucher_value, type: data.voucher_type, min_spend: data.min_spend
        }));
        // Inject voucher into store at position #1 and auto-apply — no revealed card needed
        shopStore?.injectViralVoucher(
          data.voucher_code,
          data.voucher_label,
          data.voucher_value,
          data.voucher_type,
          data.min_spend
        );
        try {
          const cartStore = getCartStore();
          cartStore?.setVouchers(cartStore.vouchers);
        } catch (e) {
          console.error('Failed to sync to cartStore on unlock', e);
        }
        step = 'revealed'; // hides this component completely
        onUnlock?.();
        triggerFlyAnimation();
        createHeartConfetti(window.innerWidth / 2, window.innerHeight / 2);
        clientUi.showToast('🎉 Đã áp mã ưu đãi!', 'success');
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
      } finally {
        finishProgress();
      }
    }
  };

  function triggerFlyAnimation() {
    showFlyGhost = true;
    setTimeout(() => { showFlyGhost = false; }, 1000);
  }

  async function copyCode() {
    if (!voucherCode) return;
    await copyViralLink(voucherCode);
    codeCopied = true;
    setTimeout(() => { codeCopied = false; }, 2000);
  }

  function resetToIdle() {
    step = 'idle';
    errorMsg = '';
    _token = null;
    _fingerprint = null;
  }

  let campaignData = $state<{ voucher_label?: string; cta_text?: string; share_text?: string; voucher_subtitle?: string; voucher_id?: string } | null>(null);
  let isCampaignLoaded = $state(false);

  $effect(() => {
    const vId = promoConfig?.voucher_id;
    if (vId && !isCampaignLoaded) {
      isCampaignLoaded = true;
      fetch(`/api/v1/client/viral/campaign/${vId}`)
        .then(res => {
          if (!res.ok) {
            campaignExists = false;
            return null;
          }
          return res.json();
        })
        .then((data: any) => {
          if (data && data.exists !== false && data.enabled !== false) {
            campaignData = data;
            campaignExists = true;
          } else {
            campaignExists = false;
          }
        })
        .catch(() => {
          campaignExists = false;
        });
    }
  });

  const displayRewardLabel = $derived(
    campaignData?.voucher_label || 
    viralSuite?.share_reward_label || 
    promoConfig?.voucher_label ||
    promoConfig?.reward_label ||
    ''
  );

  const ctaText = $derived(
    campaignData?.cta_text || 
    viralSuite?.share_cta || 
    promoConfig?.cta_text ||
    'Nhận'
  );

  const subDescription = $derived(
    campaignData?.voucher_subtitle || 
    campaignData?.share_text || 
    promoConfig?.voucher_subtitle || 
    promoConfig?.share_text || 
    ''
  );

</script>

{#if isMounted && isEnabled && step !== 'revealed'}
  <!-- Canary Trap / Honeypot: Hidden from real users but bots will interact with it -->
  <button 
    class="stu-honeypot" 
    style="position: absolute; top: -9999px; left: -9999px; opacity: 0; pointer-events: none;" 
    aria-hidden="true" 
    tabindex="-1"
    onclick={() => { honeypotTriggered = true; }}
  >
    Share Promo
  </button>
  
  <div class="stu-desktop-root" class:stu-compact={compact}>
    {#if step === 'idle' || step === 'error'}
      <div class="stu-view-bar group">
        <div class="glass-shimmer"></div>
        <div class="stp-one-line">
          <div class="stp-icon-box">
            <div class="gift-pulse"></div>
            <Gift size={18} />
          </div>
          <div class="stp-msg">
            <span class="stp-t">{displayRewardLabel}</span>
            {#if subDescription}
              <span class="stp-sub">{subDescription}</span>
            {/if}
            {#if errorMsg}<span class="text-[10px] text-red-500 font-bold">{errorMsg}</span>{/if}
          </div>
          <button class="stp-go group/cta" onclick={viralActions.share}>
            <span>{ctaText}</span>
            <ExternalLink size={12} class="group-hover/cta:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    {/if}
  </div>

  {#if step === 'sharing' || step === 'verifying'}
    <div class="viral-overlay" transition:fade={{ duration: 250 }}>
      <div class="viral-card" transition:scale={{ duration: 300, start: 0.95 }}>
        <div class="viral-glow"></div>
        <div class="viral-icon-box">
          <Zap size={28} class="viral-zap-anim text-[#ee4d2d]" />
        </div>
        <h3 class="viral-title">
          {step === 'sharing' ? `Đang kết nối ${activePlatform === 'zalo' ? 'Zalo' : activePlatform === 'tiktok' ? 'TikTok' : 'Facebook'}...` : 'AI đang xác minh lượt chia sẻ'}
        </h3>
        <p class="viral-step">{verificationText}</p>
        
        <div class="viral-progress-track">
          <div class="viral-progress-bar" style="width: {progressPercent}%"></div>
        </div>
        
        <span class="viral-footer">Hệ thống đang đối chiếu telemetry thời gian thực. Vui lòng giữ kết nối.</span>
      </div>
    </div>
  {/if}
{/if}

<style>
  .viral-overlay {
    position: fixed;
    inset: 0;
    z-index: 99999;
    background: rgba(8, 10, 18, 0.7);
    backdrop-filter: blur(16px) saturate(180%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  .viral-card {
    position: relative;
    background: rgba(17, 24, 39, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.15);
    border-radius: 20px;
    max-width: 420px;
    width: 100%;
    padding: 32px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    overflow: hidden;
  }

  .viral-glow {
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(238, 77, 45, 0.08) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
  }

  .viral-icon-box {
    position: relative;
    z-index: 1;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: rgba(238, 77, 45, 0.1);
    border: 1px solid rgba(238, 77, 45, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
    box-shadow: 0 0 20px rgba(238, 77, 45, 0.15);
  }

  :global(.viral-zap-anim) {
    animation: viral-zap 1.5s ease-in-out infinite;
    filter: drop-shadow(0 0 8px rgba(238, 77, 45, 0.4));
  }

  @keyframes viral-zap {
    0%, 100% { transform: scale(1) rotate(0deg); opacity: 1; }
    50% { transform: scale(1.15) rotate(15deg); opacity: 0.85; }
  }

  .viral-title {
    position: relative;
    z-index: 1;
    font-size: 16px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 8px;
    letter-spacing: -0.01em;
  }

  .viral-step {
    position: relative;
    z-index: 1;
    font-size: 12px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 24px;
    min-height: 18px;
  }

  .viral-progress-track {
    position: relative;
    z-index: 1;
    width: 100%;
    height: 6px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    overflow: hidden;
    margin-bottom: 20px;
  }

  .viral-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #ff4e50, #ee4d2d);
    border-radius: 9999px;
    transition: width 0.1s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .viral-footer {
    position: relative;
    z-index: 1;
    font-size: 10px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 0.02em;
  }

  .stu-desktop-root { position: relative; margin: 0; }
  
  .stu-view-bar {
    padding: 0; 
    background: transparent; 
    position: relative;
    overflow: hidden;
    border: none;
    box-shadow: none;
  }

  .glass-shimmer {
    position: absolute;
    inset: 0;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.4),
      transparent
    );
    transform: translateX(-100%);
    animation: shimmer 3s infinite;
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    50%, 100% { transform: translateX(100%); }
  }

  .stp-one-line { display: flex; align-items: center; gap: 12px; padding: 0; min-height: 0; }
  
  .stp-icon-box { 
    position: relative;
    color: #ee4d2d; 
    display: flex; 
    align-items: center; 
    justify-content: center;
    width: 24px;
    height: 24px;
    background: transparent;
  }

  .gift-pulse {
    position: absolute;
    inset: 0;
    background: #ee4d2d;
    border-radius: 10px;
    opacity: 0.2;
    animation: icon-pulse 2s infinite;
  }

  @keyframes icon-pulse {
    0% { transform: scale(1); opacity: 0.2; }
    50% { transform: scale(1.1); opacity: 0; }
    100% { transform: scale(1); opacity: 0; }
  }

  .stp-msg { flex: 1; display: flex; flex-direction: column; justify-content: center; }
  .stp-t { font-size: 13px; font-weight: 800; color: #111; letter-spacing: -0.01em; display: inline-block !important; text-transform: lowercase !important; }
  .stp-t::first-letter { text-transform: uppercase !important; }
  .stp-sub { font-size: 11px; color: #666; font-weight: 500; line-height: 1.2; margin-top: 1px; display: inline-block !important; text-transform: lowercase !important; }
  .stp-sub::first-letter { text-transform: uppercase !important; }
  
  .stp-go { 
    position: relative;
    display: flex; align-items: center; gap: 6px; color: #fff; 
    background: #ee4d2d;
    padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: 900; 
    border: none; cursor: pointer;
    overflow: hidden;
    transition: all 0.2s;
    outline: none;
  }
  .stp-go span { display: inline-block !important; text-transform: lowercase !important; }
  .stp-go span::first-letter { text-transform: uppercase !important; }

  .stp-go:hover { transform: translateY(-1px); opacity: 0.9; }

  .stu-center { 
    display: flex; align-items: center; justify-content: center; gap: 10px; padding: 16px; 
    border-radius: 12px; background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(8px);
  }
  .stu-loading-text { font-size: 12px; font-weight: 700; color: #ee4d2d; }
  .stu-loading-text-blue { font-size: 12px; font-weight: 800; color: #ffffff; letter-spacing: -0.01em; }
  
  :global(.stu-spin-pulse) { animation: stu-pulse-zap 1.5s ease-in-out infinite; filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.4)); }
  @keyframes stu-pulse-zap {
    0%, 100% { transform: scale(1) rotate(0deg); opacity: 1; }
    50% { transform: scale(1.2) rotate(15deg); opacity: 0.7; }
  }
  
  .stu-confirm-view { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 16px; background: transparent; border: none; }
  .stu-confirm-txt { font-size: 14px; font-weight: 800; color: #000; }
  .stu-confirm-btns { display: flex; gap: 8px; width: 100%; }
  .stu-btn-alt { flex: 1; height: 36px; background: #f5f5f5; color: #666; border: none; border-radius: 6px; font-size: 12px; font-weight: 800; cursor: pointer; }
  .stu-btn-prim { flex: 1; height: 36px; background: #ee4d2d; color: #fff; border: none; border-radius: 6px; font-size: 12px; font-weight: 900; cursor: pointer; }

  .stu-revealed-card { 
    display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; 
    background: linear-gradient(135deg, #fffaf9, #fff);
    border-radius: 12px;
    border: 1px dashed #ee4d2d;
    animation: stu-reveal 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  .stu-voucher-info { display: flex; flex-direction: column; gap: 2px; }
  .stu-voucher-label { font-size: 10px; font-weight: 700; color: #999; }
  .stu-voucher-code { font-size: 20px; font-weight: 900; color: #ee4d2d; font-family: monospace; letter-spacing: 1px; }
  .stu-copy-btn { 
    display: flex; align-items: center; gap: 6px;
    padding: 8px 16px; background: #ee4d2d; color: #fff; border: none; border-radius: 8px; font-size: 12px; font-weight: 900; cursor: pointer;
    box-shadow: none;
  }

  @keyframes stu-reveal { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  :global(.stu-spin) { animation: stu-rotate 1s linear infinite; }
  @keyframes stu-rotate { to { transform: rotate(360deg); } }
</style>
