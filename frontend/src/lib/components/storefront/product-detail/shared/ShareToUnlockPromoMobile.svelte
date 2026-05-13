<script lang="ts">
  import Gift from "@lucide/svelte/icons/gift";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Check from "@lucide/svelte/icons/check";
  import Copy from "@lucide/svelte/icons/copy";
  import Loader from "@lucide/svelte/icons/loader";
  import Heart from "@lucide/svelte/icons/heart";
  import Facebook from "@lucide/svelte/icons/facebook";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Share2 from "@lucide/svelte/icons/share-2";
  import type { Product, ProductMetadata } from '$lib/types';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';

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

  const viralSuite = $derived(product.metadata?.viral_suite as (ViralSuiteMetadata | undefined) ?? null);
  
  const promoConfig = $derived(
    viralSuite?.share_promotion ?? 
    (product.metadata as ProductMetadata)?.share_promotion ?? 
    null
  );
  const isEnabled = $derived(
    promoConfig?.enabled === true && !!promoConfig?.voucher_id
  );

  const shareCount = $derived(
    viralSuite?.share_count ?? (typeof (product.metadata as ProductMetadata)?.share_count === 'number' ? (product.metadata as ProductMetadata).share_count : 0)
  );

  type Step = 'idle' | 'sharing' | 'verifying' | 'revealed' | 'error';
  let step = $state<Step>('idle');

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
  
  const initTime = Date.now();

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


  $effect(() => {
    const onVisibilityChange = () => { 
      if (document.hidden) visibilityChanges++; 
    };
    const onClick = () => interactionCount++;
    const onScroll = () => {
        const scrolled = window.scrollY;
        if (scrolled > maxScrollY) maxScrollY = scrolled;
    };

    document.addEventListener('visibilitychange', onVisibilityChange);
    document.addEventListener('click', onClick);
    window.addEventListener('scroll', onScroll, { passive: true });

    if (typeof window !== 'undefined') {
      const isCookieUnlocked = shopStore?.unlockedVoucherIds?.includes(`${product.id}_${promoConfig.voucher_id}`);
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      
      if (isCookieUnlocked) {
        // If unlocked by server cookie, find it in the store
        const existingVoucher = shopStore?.vouchers?.find(v => v.id === promoConfig.voucher_id);
        if (existingVoucher) {
            voucherCode = existingVoucher.code;
            voucherLabel = existingVoucher.label || 'Voucher đặc quyền';
            step = 'revealed';
        }
      } else if (saved) {
        try {
          const data = JSON.parse(saved);
          voucherCode = data.code;
          voucherLabel = data.label;
          step = 'revealed';
        } catch {
          localStorage.removeItem(`viral_unlocked_${product.id}`);
        }
      }
    }
    return () => {
        document.removeEventListener('visibilitychange', onVisibilityChange);
        document.removeEventListener('click', onClick);
        window.removeEventListener('scroll', onScroll);
    };
  });

  const viralActions = {
    async share() {
      if (step !== 'idle' && step !== 'error') return;
      step = 'sharing';
      
      try {
        const res = await fetch('/_viral/share-intent', {
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
            
            const popup = window.open(shareUrl, 'Share', `toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=${w}, height=${h}, top=${top}, left=${left}`);
            
            if (!popup || popup.closed || typeof popup.closed === 'undefined') {
                popupWasBlocked = true;
                // If popup blocked, let's just try to verify anyway, AI will handle
                setTimeout(() => viralActions.verify(), 2000);
            } else {
                let verifyAttempts = 0;
                let isVerifying = false;

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

                const handleFocus = () => {
                    if (step !== 'revealed') attemptVerify();
                };

                // Poll popup closure
                const pollTimer = setInterval(() => {
                    if (popup.closed) {
                        clearInterval(pollTimer);
                        const elapsed = Date.now() - shareStartTime;
                        if (elapsed < 1500) {
                            // Firefox isolation detected. Popup is actually still open.
                            // Rely strictly on focus events when they return to the main window.
                            window.addEventListener('focus', handleFocus);
                            document.addEventListener('visibilitychange', () => {
                                if (!document.hidden) handleFocus();
                            });
                        } else {
                            // Normal browser, popup legitimately closed.
                            attemptVerify();
                        }
                    }
                }, 500);
            }
        }
      } catch (e: unknown) {
        errorMsg = e instanceof Error ? e.message : 'Đã xảy ra lỗi';
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
        const res = await fetch('/_viral/verify-share', {
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
                  popup_was_blocked: popupWasBlocked
              }
          }),
        });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || errData.error || 'Hệ thống phát hiện bất thường. Vui lòng chia sẻ lại!');
        }
        const data = await res.json();
        voucherCode = data.voucher_code;
        voucherLabel = data.voucher_label;
        step = 'revealed';
        localStorage.setItem(`viral_unlocked_${product.id}`, JSON.stringify({ code: voucherCode, label: voucherLabel, unlocked_at: Date.now() }));
        if (onUnlock) onUnlock();
        triggerFlyAnimation();
        createHeartConfetti(window.innerWidth / 2, window.innerHeight / 2);
        clientUi.showToast('🎉 Đã mở khóa!', 'success');
      } catch (e: unknown) {
        errorMsg = e instanceof Error ? e.message : 'Xác minh thất bại';
        step = 'error';
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

{#if isEnabled && step !== 'revealed'}
  <div class="stu-mobile-root" class:funnel={variant === 'funnel'} class:stu-compact={compact}>
    {#if step === 'idle' || step === 'error'}
      <div class="stu-view">
        {#if variant === 'floating'}
          <div class="stu-ios-container">
            <div class="stu-ios-content">
              <h4 class="stu-ios-title">{displayRewardLabel}</h4>
              {#if subDescription}
                <span class="stu-ios-sub">{subDescription}</span>
              {/if}
            </div>
            <button class="stu-ios-btn" onclick={viralActions.share}>
               <span>{ctaText}</span>
               <ExternalLink size={12} class="ml-1.5" />
               <div class="stu-ios-btn-shimmer"></div>
            </button>
          </div>
        {:else}
          <div class="stp-funnel-wrapper">
            <div class="stp-f-social">
              <button class="stp-f-heart"><Heart size={16} class="fill-current" /><span>{formatViralCount(shareCount * 12)}</span></button>
              <div class="stp-f-divider"></div>
              <button class="stp-f-social-btn" onclick={viralActions.share} aria-label="Share on Facebook"><Facebook size={16} /></button>
              <button class="stp-f-social-btn" onclick={() => shareToPlatform('zalo', window.location.href, product.name)} aria-label="Share on Zalo"><span class="text-[9px] font-black italic">Zalo</span></button>
              <button class="stp-f-social-btn" onclick={() => shareToPlatform('tiktok', window.location.href, product.name)} aria-label="Share on TikTok"><span class="text-[9px] font-black italic">TikTok</span></button>
              <button class="stp-f-social-btn" onclick={copyCode} aria-label="Copy code"><Copy size={14} /></button>
            </div>
            <div class="stp-funnel-row">
              <div class="stp-f-msg">
                <span class="stp-f-t">{displayRewardLabel}</span>
                {#if subDescription}
                  <span class="text-[8px] text-[#ffb7c5]/60 font-medium leading-none mb-1">{subDescription}</span>
                {/if}
                <div class="stp-f-progress">
                  <div class="stp-f-bar" style="width: 50%"></div>
                </div>
              </div>
              <button class="stp-f-btn" onclick={viralActions.share}>
                <span>{ctaText}</span>
                <div class="stu-f-btn-shine"></div>
              </button>
            </div>
          </div>
        {/if}
      </div>

    {:else if step === 'sharing' || step === 'verifying'}
      <div class="stu-center">
        <Loader size={16} class="stu-spin" style="color: #ee4d2d;" />
        <span class="stu-loading-text">{step === 'sharing' ? 'Đang kết nối...' : 'AI đang xác minh...'}</span>
      </div>

    {:else if step === 'revealed' && voucherCode}
      <div class="stu-revealed-card {variant === 'floating' ? 'stu-float-card' : ''}">
        <div class="stu-voucher-info">
          <span class="stu-voucher-label">{voucherLabel}</span>
          <span class="stu-voucher-code {variant === 'floating' ? 'text-lg' : ''}">{voucherCode}</span>
        </div>
        <button class="stu-copy-btn {variant === 'floating' ? 'text-[9px] px-2' : ''}" onclick={copyCode}>
          {#if codeCopied}
            <Check size={10} /><span>Xong</span>
          {:else}
            <Copy size={10} /><span>Copy</span>
          {/if}
        </button>
      </div>
    {/if}
  </div>
{/if}

<style>
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
    padding: 8px 20px; border-radius: 6px; font-size: 11px; font-weight: 1000; border: none; cursor: pointer;
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
