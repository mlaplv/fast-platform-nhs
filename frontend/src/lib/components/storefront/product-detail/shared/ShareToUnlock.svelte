<script lang="ts">
    import Gift from "@lucide/svelte/icons/gift";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Check from "@lucide/svelte/icons/check";
  import Copy from "@lucide/svelte/icons/copy";
  import Loader from "@lucide/svelte/icons/loader";
  import Facebook from "@lucide/svelte/icons/facebook";
  
  // Types
  import type { Product } from '$lib/types';
  
  // States
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
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

  /**
   * Elite V2.2: Share promotion config from product.metadata.viral_suite
   */
  const viralSuite = $derived(product.metadata?.viral_suite ?? null);

  const promoConfig = $derived(
    viralSuite?.share_promotion ?? 
    product.metadata?.share_promotion ?? 
    null
  );
  const isEnabled = $derived(
    promoConfig?.enabled === true && !!promoConfig?.voucher_id
  );

  const shareCount = $derived(
    viralSuite?.share_count ?? (typeof product.metadata?.share_count === 'number' ? product.metadata.share_count : 0)
  );

  // ── State Machine ──────────────────────────────────────────────────────────
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
  let showFlyGhost = $state(false);

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
            voucherLabel = existingVoucher.label || 'VOUCHER ĐẶC QUYỀN';
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
        errorMsg = e instanceof Error ? e.message : String(e);
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
        onUnlock?.();
        triggerFlyAnimation();
        createHeartConfetti(window.innerWidth / 2, window.innerHeight / 2);
        clientUi.showToast('🎉 Đã mở khóa!', 'success');
      } catch (e: unknown) {
        errorMsg = e instanceof Error ? e.message : String(e);
        step = 'error';
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
  const displayRewardLabel = $derived(
    viralSuite?.share_reward_label || 
    promoConfig?.voucher_label ||
    promoConfig?.reward_label ||
    ''
  );

  const ctaText = $derived(
    viralSuite?.share_cta || 
    promoConfig?.cta_text ||
    'NHẬN'
  );
</script>

{#if showFlyGhost}
  <div class="stu-fly-ghost">
    <div class="stu-fly-content">
       <span class="text-[10px] font-black">{voucherCode}</span>
    </div>
  </div>
{/if}

{#if isEnabled && step !== 'revealed'}
  <div class="stu-desktop-root" class:stu-compact={compact}>
    {#if step === 'idle' || step === 'error'}
      <div class="stu-view-bar">
        <div class="stp-one-line">
          <div class="stp-icon-box"><Gift size={18} /></div>
          <div class="stp-msg">
            <span class="stp-t">{displayRewardLabel}</span>
            {#if promoConfig?.voucher_subtitle}
              <span class="text-[10px] text-gray-500 font-medium leading-none mt-0.5">{promoConfig.voucher_subtitle}</span>
            {/if}
            {#if errorMsg}<span class="text-[10px] text-red-500 font-bold">{errorMsg}</span>{/if}
          </div>
          <button class="stp-go" onclick={viralActions.share}>
            <span>{ctaText}</span><ExternalLink size={12} />
          </button>
        </div>
      </div>

    {:else if step === 'sharing' || step === 'verifying'}
      <div class="stu-center">
        <Loader size={16} class="stu-spin" style="color: #ee4d2d;" />
        <span class="stu-loading-text">{step === 'sharing' ? 'ĐANG KẾT NỐI...' : 'AI ĐANG XÁC MINH...'}</span>
      </div>

    {:else if step === 'revealed' && voucherCode}
      <div class="stu-revealed-card">
        <div class="stu-voucher-info">
          <span class="stu-voucher-label">{voucherLabel}</span>
          <span class="stu-voucher-code">{voucherCode}</span>
        </div>
        <button class="stu-copy-btn" onclick={copyCode}>
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
  .stu-desktop-root { position: relative; margin: 8px 0; }
  
  .stu-view-bar {
    padding: 0; background: #fff; position: relative; border-radius: 4px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05); overflow: hidden;
    border: 1px dashed #ee4d2d;
    mask-image: radial-gradient(circle at 0 50%, transparent 5px, black 6px), radial-gradient(circle at 100% 50%, transparent 5px, black 6px);
    mask-composite: intersect;
  }
  .stp-one-line { display: flex; align-items: center; gap: 10px; padding: 10px 12px; min-height: 44px; }
  .stp-icon-box { color: #ee4d2d; display: flex; align-items: center; justify-content: center; }
  .stp-msg { flex: 1; display: flex; flex-direction: column; justify-content: center; }
  .stp-t { font-size: 13px; font-weight: 1000; color: #111; text-transform: uppercase; letter-spacing: -0.01em; }
  .stp-go { 
    display: flex; align-items: center; gap: 6px; color: #fff; background: #ee4d2d;
    padding: 5px 12px; border-radius: 6px; font-size: 11px; font-weight: 1000; border: none; cursor: pointer;
    text-transform: uppercase;
  }

  .stu-center { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px; border: 1px dashed #ee4d2d; border-radius: 4px; }
  .stu-loading-text { font-size: 11px; font-weight: 800; color: #ee4d2d; text-transform: uppercase; }
  
  .stu-confirm-view { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 16px; background: #fff; border: 1.5px dashed #ee4d2d; border-radius: 4px; }
  .stu-confirm-txt { font-size: 14px; font-weight: 1000; color: #000; text-transform: uppercase; }
  .stu-confirm-btns { display: flex; gap: 8px; width: 100%; }
  .stu-btn-alt { flex: 1; height: 36px; background: #f5f5f5; color: #666; border: none; border-radius: 6px; font-size: 12px; font-weight: 800; cursor: pointer; }
  .stu-btn-prim { flex: 1; height: 36px; background: #ee4d2d; color: #fff; border: none; border-radius: 6px; font-size: 12px; font-weight: 1000; cursor: pointer; }

  .stu-revealed-card { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: #fffcfc; border: 1.5px dashed #ee4d2d; border-radius: 4px; animation: stu-reveal 0.5s ease; }
  .stu-voucher-info { display: flex; flex-direction: column; }
  .stu-voucher-label { font-size: 10px; font-weight: 800; color: #999; text-transform: uppercase; }
  .stu-voucher-code { font-size: 18px; font-weight: 1000; color: #ee4d2d; font-family: monospace; }
  .stu-copy-btn { padding: 6px 12px; background: #ee4d2d; color: #fff; border: none; border-radius: 6px; font-size: 11px; font-weight: 900; cursor: pointer; }

  @keyframes stu-reveal { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  :global(.stu-spin) { animation: stu-rotate 1s linear infinite; }
  @keyframes stu-rotate { to { transform: rotate(360deg); } }
</style>
