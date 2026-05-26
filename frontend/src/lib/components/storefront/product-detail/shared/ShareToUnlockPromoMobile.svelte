<script lang="ts">
  import Gift from "@lucide/svelte/icons/gift";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Check from "@lucide/svelte/icons/check";
  import Copy from "@lucide/svelte/icons/copy";
  import Loader from "@lucide/svelte/icons/loader";
  import Zap from "@lucide/svelte/icons/zap";
  import Heart from "@lucide/svelte/icons/heart";
  import Facebook from "@lucide/svelte/icons/facebook";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Share2 from "@lucide/svelte/icons/share-2";
  import { untrack, onMount, onDestroy } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import type { Product, ProductMetadata } from '$lib/types';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';
  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';

  interface PromoConfig {
    enabled: boolean;
    voucher_id: string;
    reward_text?: string;
  }

  interface ViralSuiteMetadata {
    share_promotion?: PromoConfig;
    share_count?: number;
    likes_count?: number;
    stats?: {
      redeemed_count?: number;
    };
  }

  interface Props {
    product: Product;
    compact?: boolean;
    variant?: 'floating' | 'funnel';
    onUnlock?: () => void;
  }

  let { product, compact = false, variant = 'floating', onUnlock }: Props = $props();
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

  const viralSuite = $derived(product.metadata?.viral_suite as (ViralSuiteMetadata | undefined) ?? null);
  
  const promoConfig = $derived(
    viralSuite?.share_promotion ?? 
    (product.metadata as ProductMetadata)?.share_promotion ?? 
    null
  );
  let campaignExists = $state(true);
  const isEnabled = $derived(
    promoConfig?.enabled === true && !!promoConfig?.voucher_id && campaignExists
  );

  const shareCount = $derived(
    viralSuite?.share_count ?? (typeof (product.metadata as ProductMetadata)?.share_count === 'number' ? (product.metadata as ProductMetadata).share_count : 0)
  );

  type Step = 'idle' | 'sharing' | 'verifying' | 'revealed' | 'error';
  let step = $state<Step>('idle');
  let verificationText = $state('AI đang xác minh...');

  let _token = $state<string | null>(null);
  let _fingerprint = $state<string | null>(null);

  let voucherCode = $state<string | null>(null);
  let voucherLabel = $state<string | null>(null);

  let codeCopied = $state(false);
  let errorMsg = $state('');

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
  
  let _lastTouchX = 0, _lastTouchY = 0, _lastTouchTime = 0;
  let _clickTimes: number[] = [];
  
  const initTime = Date.now();

  let campaignData = $state<{ voucher_label?: string; cta_text?: string; share_text?: string; voucher_subtitle?: string; voucher_id?: string } | null>(null);
  let isCampaignLoaded = $state(false);
  let isComponentMounted = true;

  $effect(() => {
    // Reset state when switching products (track ONLY product.id)
    product.id;
    untrack(() => {
      step = 'idle';
      voucherCode = null;
      voucherLabel = null;
      errorMsg = '';
      isCampaignLoaded = false;
      campaignData = null;
    });
  });

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
    'Nhận quà'
  );

  const stats = $derived(viralSuite?.stats ?? { redeemed_count: 0 });

  const isLiked = $derived(isMounted ? wishlistStore.isLiked(product.id) : false);
  const baseLikeCount = $derived(Number(viralSuite?.likes_count || (product.metadata as ProductMetadata)?.likes || shareCount * 12 || 0));
  const likeCount = $derived(baseLikeCount + (isLiked ? 1 : 0));

  function toggleLike() {
    wishlistStore.toggle(product.id);
    if (wishlistStore.isLiked(product.id)) {
      clientUi.showToast('Đã lưu sản phẩm vào mục yêu thích!', 'success');
      createHeartConfetti(window.innerWidth / 2, window.innerHeight / 2);
    }
  }


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
    const onTouchMove = (e: TouchEvent) => {
      const touch = e.touches[0];
      if (!touch) return;
      const now = Date.now();
      if (_lastTouchTime > 0) {
        const dt = (now - _lastTouchTime) / 1000;
        if (dt > 0) {
          const dx = touch.clientX - _lastTouchX;
          const dy = touch.clientY - _lastTouchY;
          const v = Math.sqrt(dx*dx + dy*dy) / dt;
          if (v > mouseAcceleration) mouseAcceleration = v;
        }
      }
      _lastTouchX = touch.clientX;
      _lastTouchY = touch.clientY;
      _lastTouchTime = now;
    };
    const onScroll = () => {
        const scrolled = window.scrollY;
        if (scrolled > maxScrollY) maxScrollY = scrolled;
    };

    document.addEventListener('visibilitychange', onVisibilityChange);
    window.addEventListener('blur', onBlur);
    document.addEventListener('click', onClick);
    window.addEventListener('touchmove', onTouchMove, { passive: true });
    window.addEventListener('scroll', onScroll, { passive: true });

    if (typeof window !== 'undefined') {
      const isCookieUnlocked = promoConfig?.voucher_id && shopStore?.unlockedVoucherIds?.includes(`${product.id}_${promoConfig.voucher_id}`);
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      
      if (saved) {
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
            shopStore?.injectViralVoucher(
              data.code,
              data.label,
              data.value ?? 0,
              data.type ?? 'FIXED',
              data.min_spend ?? 0
            );
            step = 'revealed';
          }
        } catch {
          localStorage.removeItem(`viral_unlocked_${product.id}`);
        }
      } else if (isCookieUnlocked && promoConfig?.voucher_id) {
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
        isComponentMounted = false;
        document.removeEventListener('visibilitychange', onVisibilityChange);
        window.removeEventListener('blur', onBlur);
        document.removeEventListener('click', onClick);
        window.removeEventListener('touchmove', onTouchMove);
        window.removeEventListener('scroll', onScroll);
        if (progressInterval) {
          clearInterval(progressInterval);
        }
    };
  });

  onDestroy(() => {
    if (progressInterval) {
      clearInterval(progressInterval);
    }
  });

  const viralActions = {
    async share() {
      if (step !== 'idle' && step !== 'error') return;
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
                throw err;
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
            
            const popup = window.open(shareUrl, 'Share', `toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=${w}, height=${h}, top=${top}, left=${left}`);
            
            if (!popup || popup.closed || typeof popup.closed === 'undefined') {
                popupWasBlocked = true;
                // If popup blocked, let's just try to verify anyway, AI will handle
                setTimeout(() => { if(isComponentMounted) viralActions.verify() }, 2000);
            } else {
                let verifyAttempts = 0;
                let isVerifying = false;

                const attemptVerify = async () => {
                    if (!isComponentMounted || isVerifying || step === 'revealed' || verifyAttempts >= 3) return;
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

                const handleFocus = () => {
                    if (step !== 'revealed') attemptVerify();
                };

                const handleVisibilityChange = () => {
                    if (!document.hidden) handleFocus();
                };

                // Poll popup closure
                const pollTimer = setInterval(() => {
                    if (!isComponentMounted || popup.closed) {
                        clearInterval(pollTimer);
                        window.removeEventListener('focus', handleFocus);
                        document.removeEventListener('visibilitychange', handleVisibilityChange);
                        
                        if (isComponentMounted && popup.closed) {
                            const elapsed = Date.now() - shareStartTime;
                            if (elapsed < 1500) {
                                // Firefox isolation detected. Popup is actually still open.
                                // Rely strictly on focus events when they return to the main window.
                                window.addEventListener('focus', handleFocus, { once: true });
                                document.addEventListener('visibilitychange', handleVisibilityChange, { once: true });
                            } else {
                                // Normal browser, popup legitimately closed.
                                attemptVerify();
                            }
                        }
                    }
                }, 500);
            }
        }
      } catch (e: unknown) {
        errorMsg = e instanceof Error ? e.message : 'Đã xảy ra lỗi';
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
            throw new Error(errData.detail || errData.error || 'Hệ thống phát hiện bất thường. Vui lòng chia sẻ lại!');
        }
        const data = await res.json();
        voucherCode = data.voucher_code;
        voucherLabel = data.voucher_label;
        localStorage.setItem(`viral_unlocked_${product.id}`, JSON.stringify({
          code: voucherCode, label: voucherLabel, unlocked_at: Date.now(),
          value: data.voucher_value, type: data.voucher_type, min_spend: data.min_spend
        }));
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
        step = 'revealed';
        if (onUnlock) onUnlock();
        triggerFlyAnimation();
        createHeartConfetti(window.innerWidth / 2, window.innerHeight / 2);
        clientUi.showToast('🎉 Đã áp mã ưu đãi!', 'success');
      } catch (e: unknown) {
        errorMsg = e instanceof Error ? e.message : 'Xác minh thất bại';
        step = 'error';
      } finally {
        finishProgress();
      }
    }
  };

  let showFlyGhost = $state(false);
  function triggerFlyAnimation() {
    showFlyGhost = true;
    setTimeout(() => { showFlyGhost = false; }, 1000);
  }

  async function copyCode() {
    if (!voucherCode) return;
    await copyViralLink(voucherCode);
    codeCopied = true;
    clientUi.showToast(`Đã sao chép: ${voucherCode}`, 'success');
    setTimeout(() => { codeCopied = false; }, 2000);
  }

</script>

{#if showFlyGhost}
  <div class="stu-fly-ghost">
    <div class="stu-fly-content">
       <span class="text-[10px] font-black">{voucherCode}</span>
    </div>
  </div>
{/if}

{#if isMounted && isEnabled && step !== 'revealed'}
  <!-- Canary Trap / Honeypot: Hidden from real users but bots will interact with it -->
  <input 
    class="stu-honeypot" 
    type="text"
    name="promo_code_hidden"
    autocomplete="off"
    style="position: absolute; top: -9999px; left: -9999px; opacity: 0; pointer-events: none; width: 0; height: 0;"
    aria-hidden="true" 
    tabindex="-1"
    onfocus={() => { honeypotTriggered = true; }}
    oninput={() => { honeypotTriggered = true; }}
  />
  
  <div class="stu-mobile-root" class:funnel={variant === 'funnel'} class:stu-compact={compact}>
    {#if step === 'idle' || step === 'error'}
      <div class="stu-view">
        {#if variant === 'floating'}
          <div class="stu-ios-container">
            <div class="stu-ios-content">
              <h4 class="stu-ios-title first-letter:uppercase">{displayRewardLabel}</h4>
              {#if subDescription}
                <span class="stu-ios-sub inline-block first-letter:uppercase">{subDescription}</span>
              {/if}
            </div>
            <button class="stu-ios-btn" onclick={viralActions.share}>
               <span class="inline-block first-letter:uppercase">{ctaText}</span>
               <ExternalLink size={12} class="ml-1.5" />
               <div class="stu-ios-btn-shimmer"></div>
            </button>
          </div>
        {:else}
          <div class="stp-funnel-wrapper">
            <div class="stp-f-social">
              <button class="stp-f-heart" onclick={toggleLike} aria-label="Yêu thích sản phẩm">
                <Heart size={16} class="fill-current {isLiked ? 'text-[#ff2c55]' : 'text-[#ffb7c5]'}" />
                <span>{formatViralCount(likeCount)}</span>
              </button>
              <div class="stp-f-divider"></div>
              <button class="stp-f-social-btn" onclick={viralActions.share} aria-label="Share on Facebook"><Facebook size={16} /></button>
              <button class="stp-f-social-btn" onclick={() => shareToPlatform('zalo', window.location.href, product.name)} aria-label="Share on Zalo"><span class="text-[9px] font-black italic">Zalo</span></button>
              <button class="stp-f-social-btn" onclick={() => shareToPlatform('tiktok', window.location.href, product.name)} aria-label="Share on TikTok"><span class="text-[9px] font-black italic">TikTok</span></button>
              <button class="stp-f-social-btn" onclick={copyCode} aria-label="Copy code"><Copy size={14} /></button>
            </div>
            <div class="stp-funnel-row">
              <div class="stp-f-msg">
                <span class="stp-f-t inline-block first-letter:uppercase">{displayRewardLabel}</span>
                {#if subDescription}
                  <span class="text-[8px] text-[#ffb7c5]/60 font-medium leading-none mb-1 inline-block first-letter:uppercase">{subDescription}</span>
                {/if}
                <div class="stp-f-progress">
                  <div class="stp-f-bar" style="width: 50%"></div>
                </div>
              </div>
              <button class="stp-f-btn" onclick={viralActions.share}>
                <span class="inline-block first-letter:uppercase">{ctaText}</span>
                <div class="stu-f-btn-shine"></div>
              </button>
            </div>
          </div>
        {/if}
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
          {step === 'sharing' ? 'Đang kết nối Facebook...' : 'AI đang xác minh lượt chia sẻ'}
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

  .stu-mobile-root { position: relative; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
  
  /* --- Funnel Variant --- */
  .stp-funnel-wrapper { display: flex; flex-direction: column; gap: 4px; }
  .stp-f-social { display: flex; align-items: center; gap: 8px; padding: 2px 0; }
  .stp-f-heart { display: flex; align-items: center; gap: 4px; color: #ffb7c5; background: none; border: none; font-size: 11px; font-weight: 1000; }
  .stp-f-divider { width: 1px; height: 10px; background: rgba(255,255,255,0.1); }
  .stp-f-social-btn { 
    width: 28px; height: 28px; border-radius: 50%; background: rgba(255,255,255,0.06); 
    border: 1px solid rgba(255,255,255,0.08); color: #fff; display: flex; align-items: center; justify-content: center;
    cursor: pointer; transition: all 0.2s;
  }
  .stp-f-social-btn:hover { background: rgba(255,255,255,0.2); border-color: #ffb7c5; }
  
  .stp-funnel-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-top: 1px solid rgba(255,255,255,0.1); min-height: 52px; }
  .stp-f-msg { flex: 1; display: flex; flex-direction: column; gap: 4px; }
  .stp-f-t { font-size: 9px; font-weight: 900; color: #ffb7c5; letter-spacing: 0.1em; }
  .stp-f-progress { height: 4px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden; }
  .stp-f-bar { height: 100%; background: linear-gradient(90deg, #ffb7c5, #ee4d2d); border-radius: 10px; }
  .stp-f-btn { 
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, #ee4d2d, #ff7337); color: #fff; 
    padding: 8px 10px; border-radius: 6px; font-size: 11px; font-weight: 1000; border: none; cursor: pointer;
    box-shadow: 0 4px 15px rgba(238, 77, 45, 0.25); transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    letter-spacing: 0.05em;
  }
  .stp-f-btn:active { transform: scale(0.92); }

  /* --- Floating Variant (iOS 26 x TikTok) --- */
  .stu-ios-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding-bottom: 4px;
  }
  .stu-ios-content { display: flex; flex-direction: column; gap: 0; }
  .stu-ios-title { 
    font-size: 18px; font-weight: 1000; color: #fff; 
    text-shadow: 0 2px 15px rgba(0,0,0,0.8), 0 1px 2px rgba(0,0,0,0.9);
    letter-spacing: -0.02em; line-height: 1;
  }
  .stu-ios-sub { 
    font-size: 10px; font-weight: 800; color: rgba(255, 255, 255, 0.9); 
    letter-spacing: 0.05em; margin-top: 4px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.8);
  }
  
  .stu-ios-btn { 
    position: relative; overflow: hidden;
    background: rgba(255, 45, 85, 0.85);
    color: #fff;
    height: 34px;
    padding: 0 10px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    font-size: 11px; font-weight: 1000;letter-spacing: 0.1em;
    display: flex; align-items: center; justify-content: center;
    width: fit-content;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }
  .stu-ios-btn:active { transform: scale(0.94); }
  .stu-ios-btn-shimmer {
    position: absolute; inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 45, 85, 0.4), transparent);
    transform: translateX(-100%);
    animation: stu-ios-shimmer 2.5s infinite;
  }
  @keyframes stu-ios-shimmer { 0% { transform: translateX(-100%); } 30%, 100% { transform: translateX(100%); } }
  
  .stu-f-btn-inner {
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 1000;
    letter-spacing: 0.12em;
    z-index: 2; position: relative;
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.4);
  }

  :global(.stu-f-btn-icon) { 
    filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.5)); 
    animation: stu-sparkle-pulse 2s infinite ease-in-out;
  }
  @keyframes stu-sparkle-pulse {
    0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.8; }
    50% { transform: scale(1.2) rotate(15deg); opacity: 1; }
  }

  .stu-f-btn-shine {
    position: absolute; top: 0; left: -150%; width: 60%; height: 100%;
    background: linear-gradient(90deg, 
      transparent, 
      rgba(255, 255, 255, 0.2) 20%, 
      rgba(255, 255, 255, 0.6) 50%, 
      rgba(255, 255, 255, 0.2) 80%, 
      transparent
    );
    transform: skewX(-35deg);
    animation: stu-liquid-shine 3s infinite cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 1;
  }
  @keyframes stu-liquid-shine {
    0% { left: -150%; }
    30% { left: 250%; }
    100% { left: 250%; }
  }

  .stu-center { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px; }
  .stu-loading-text { font-size: 11px; font-weight: 800; color: #ee4d2d; }
  .stu-loading-text-blue { font-size: 13px; font-weight: 1000; color: #ffffff; letter-spacing: -0.01em; }
  
  :global(.stu-spin-pulse) { animation: stu-pulse-zap 1.5s ease-in-out infinite; filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.4)); }
  @keyframes stu-pulse-zap {
    0%, 100% { transform: scale(1) rotate(0deg); opacity: 1; }
    50% { transform: scale(1.2) rotate(15deg); opacity: 0.7; }
  }
  
  .stu-confirm-view { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 16px; background: #fff; border: 1.5px dashed #ee4d2d; border-radius: 4px; }
  .stu-confirm-txt { font-size: 14px; font-weight: 1000; color: #000; }
  .stu-confirm-btns { display: flex; gap: 8px; width: 100%; }
  .stu-btn-alt { flex: 1; height: 36px; background: #f5f5f5; color: #666; border: none; border-radius: 6px; font-size: 12px; font-weight: 800; }
  .stu-btn-prim { flex: 1; height: 36px; background: #ee4d2d; color: #fff; border: none; border-radius: 6px; font-size: 12px; font-weight: 1000; }

  .stu-revealed-card { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: #fffcfc; border: 1.5px dashed #ee4d2d; border-radius: 4px; animation: stu-reveal 0.5s ease; }
  .stu-voucher-info { display: flex; flex-direction: column; }
  .stu-voucher-label { font-size: 10px; font-weight: 800; color: #999; }
  .stu-voucher-code { font-size: 18px; font-weight: 1000; color: #ee4d2d; font-family: monospace; }
  .stu-copy-btn { padding: 6px 12px; background: #ee4d2d; color: #fff; border: none; border-radius: 6px; font-size: 11px; font-weight: 900; }

  @keyframes stu-fade-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes stu-reveal { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  :global(.stu-spin) { animation: stu-rotate 1s linear infinite; }
  @keyframes stu-rotate { to { transform: rotate(360deg); } }

  .stu-fly-ghost { position: fixed; z-index: 9999; bottom: 25%; left: 50%; pointer-events: none; animation: stu-fly 1.2s ease-in forwards; }
  .stu-fly-content { background: #fff; border: 1.5px dashed #ee4d2d; padding: 6px 12px; border-radius: 4px; color: #ee4d2d; box-shadow: 0 10px 30px rgba(238, 77, 45, 0.4); }
  @keyframes stu-fly { 0% { transform: translate(-50%, 0) scale(1.5); opacity: 0; } 10% { opacity: 1; } 100% { transform: translate(-50%, -400px) scale(0.2); opacity: 0; } }
</style>
