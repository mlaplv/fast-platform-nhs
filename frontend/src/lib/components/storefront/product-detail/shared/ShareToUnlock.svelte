<script lang="ts">
  import Gift from "@lucide/svelte/icons/gift";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Check from "@lucide/svelte/icons/check";
  import Copy from "@lucide/svelte/icons/copy";
  import Loader from "@lucide/svelte/icons/loader";
  import Zap from "@lucide/svelte/icons/zap";
  import Facebook from "$lib/components/ui/icons/Facebook.svelte";
  import { fade, scale } from 'svelte/transition';
  
  // Types
  import type { Product } from '$lib/types';
  
  // States
  import { onMount, onDestroy, untrack } from 'svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';
  import { logger } from "$lib/utils/logger";

  interface Props {
    product: Product;
    compact?: boolean;
    onUnlock?: () => void;
  }

  let { product, compact = false, onUnlock }: Props = $props();
  const clientUi = getClientUi();
  const shopStore = getShopStore();
  const cartStore = getCartStore();

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

  let shareStartTime = $state<number>(0);
  let showFlyGhost = $state(false);
  let honeypotTriggered = $state(false);

  // ── Elite V2.2: Focus Listeners & Verification Controls ──────────────────────
  let hasRegisteredListeners = false;
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let popupWindow: Window | null = null;
  let verifyAttempts = 0;
  let isVerifying = false;
  let oauthMessageHandler: ((e: MessageEvent) => void) | null = null;

  const handleFocus = () => {
    const duration = Date.now() - shareStartTime;
    logger.log(`[ShareToUnlock Focus] Trang chính nhận sự kiện 'focus'. Thời gian kể từ khi mở popup: ${duration}ms.`);
    // Bỏ qua nếu thời gian quá ngắn dưới 1s (tránh focus nhầm khi vừa click mở popup)
    if (duration < 1000) {
        logger.warn(`[ShareToUnlock Focus] Bỏ qua sự kiện focus do duration quá ngắn (${duration}ms < 1000ms - có thể là focus ảo lúc mở)`);
        return;
    }
    
    cleanupFocusListeners();
    if (step !== 'revealed') {
        logger.log(`[ShareToUnlock Focus] Gọi attemptVerify() để backend kiểm tra.`);
        attemptVerify();
    }
  };

  const handleVisibilityChange = () => {
    if (!document.hidden) {
      const duration = Date.now() - shareStartTime;
      logger.log(`[ShareToUnlock Visibility] Trang chính nhận sự kiện 'visibilitychange' (visible). Thời gian kể từ khi mở popup: ${duration}ms.`);
      if (duration < 1000) {
          logger.warn(`[ShareToUnlock Visibility] Bỏ qua sự kiện visibility do duration quá ngắn (${duration}ms < 1000ms)`);
          return;
      }
      
      cleanupFocusListeners();
      if (step !== 'revealed') {
          logger.log(`[ShareToUnlock Visibility] Gọi attemptVerify() để backend kiểm tra.`);
          attemptVerify();
      }
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
    if (oauthMessageHandler) {
      window.removeEventListener('message', oauthMessageHandler);
      oauthMessageHandler = null;
    }
  }

  const attemptVerify = async () => {
    if (isVerifying || step === 'revealed' || verifyAttempts >= 3) return;
    
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
    });

    if (typeof window !== 'undefined') {
      // Dọn dẹp cache legacy không an toàn (không chứa userId)
      localStorage.removeItem(`viral_unlocked_${product.id}`);

      // CẤM: Cho phép restore trạng thái nếu chưa đăng nhập thực tế
      if (!authStore.isAuthenticated) {
        step = 'idle';
        voucherCode = null;
        voucherLabel = null;
        return;
      }

      const userId = authStore.user?.id;
      const isCookieUnlocked = promoConfig?.voucher_id && shopStore?.unlockedVoucherIds?.includes(`${product.id}_${promoConfig.voucher_id}`);
      
      // Elite V2026: Lưu cache theo user_id để cô lập lượt share giữa các tài khoản khác nhau
      const localKey = userId ? `viral_unlocked_${userId}_${product.id}` : null;
      const saved = localKey ? localStorage.getItem(localKey) : null;
      
      if (saved) {
        try {
          const data = JSON.parse(saved);
          
          if (promoConfig?.voucher_id && data.code !== promoConfig.voucher_id) {
            if (localKey) localStorage.removeItem(localKey);
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
          if (localKey) localStorage.removeItem(localKey);
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
  });

  const viralActions = {
    async share(platform: string = 'facebook') {
      if (typeof platform !== 'string') {
        platform = 'facebook';
      }
      if (step !== 'idle' && step !== 'error') return;

      // Elite V2.2: Bắt buộc login mới được kích hoạt hành động share
      if (!authStore.isAuthenticated) {
        clientUi.showToast('Vui lòng đăng nhập để tham gia nhận ưu đãi!', 'warning');
        getClientUi().openLogin();
        step = 'error';
        errorMsg = 'Bạn cần đăng nhập để tham gia chương trình.';
        return;
      }

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
        verifyAttempts = 0;

        const w = 600;
        const h = 600;
        const left = (window.innerWidth / 2) - (w / 2);
        const top = (window.innerHeight / 2) - (h / 2);
        
        const productUrl = window.location.origin + '/product/' + product.id;
        const targetUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(productUrl)}`;
        
        cleanupFocusListeners();
        
        // Đăng ký listeners cho trang cha để phát hiện người dùng quay lại trang
        window.addEventListener('focus', handleFocus);
        document.addEventListener('visibilitychange', handleVisibilityChange);
        hasRegisteredListeners = true;
        logger.log(`[ShareToUnlock Share] Mở popup. Target: Share Dialog. shareStartTime: ${shareStartTime}`);

        popupWindow = window.open(targetUrl, 'Share', `toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=${w}, height=${h}, top=${top}, left=${left}`);
        
        if (!popupWindow || popupWindow.closed || typeof popupWindow.closed === 'undefined') {
            logger.error('[ShareToUnlock Share] Popup bị chặn hoặc closed ngay lập tức. Sử dụng fallback verify sau 2s.');
            setTimeout(() => viralActions.verify(), 2000);
        } else {
            logger.log('[ShareToUnlock Share] Mở popup thành công. Bắt đầu pollTimer.');
            // Polling phát hiện khi popup đóng
            pollTimer = setInterval(() => {
                if (popupWindow) {
                    const isClosed = popupWindow.closed;
                    const duration = Date.now() - shareStartTime;
                    
                    if (isClosed) {
                        logger.log(`[ShareToUnlock Poller] Phát hiện popupWindow.closed = true. Trôi qua: ${duration}ms`);
                        cleanupFocusListeners();
                        if (step !== 'revealed') {
                            attemptVerify();
                        }
                    }
                }
            }, 800);
        }
      } catch (e: unknown) {
        errorMsg = e instanceof Error ? e.message : String(e);
        step = 'error';
        finishProgress();
      }
    },
    async verify() {
      if (!_token || !_fingerprint || !promoConfig) return;
      if (!promoConfig.voucher_id) {
        errorMsg = 'Cấu hình ưu đãi không hợp lệ. Vui lòng tải lại trang.';
        step = 'error';
        return;
      }
      if (step === 'revealed') return;
      
      step = 'verifying';
      startProgress();
      
      const verificationSteps = [
        'Đang thiết lập kênh Webhook...',
        'Xác thực chữ ký OAuth 2.0...',
        'Chờ tín hiệu từ máy chủ xã hội...',
        'Hoàn tất mở khóa ưu đãi...'
      ];
      
      let currentStepIdx = 0;
      const stepInterval = setInterval(() => {
        if (currentStepIdx < verificationSteps.length - 1) {
          currentStepIdx++;
          verificationText = verificationSteps[currentStepIdx];
        } else {
          clearInterval(stepInterval);
        }
      }, 800);

      try {
        // Wait 2 seconds for nice premium feeling
        await new Promise(r => setTimeout(r, 2000));

        const durationMs = Date.now() - shareStartTime;
        const res = await fetch('/api/v1/client/viral/verify-share', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            product_id: product.id, 
            fingerprint: _fingerprint, 
            token: _token, 
            voucher_id: promoConfig.voucher_id,
            telemetry: {
              time_on_page_ms: 0,
              share_duration_ms: durationMs,
              visibility_changes: 0,
              scroll_depth_pct: 0.0,
              interaction_count: 0,
              share_method: activePlatform || 'facebook',
              popup_was_blocked: false,
              mouse_acceleration: 0.0,
              interaction_rhythm: 0.0,
              honeypot_triggered: honeypotTriggered
            }
          }),
        });
        
        clearInterval(stepInterval);
        
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            let errMsg = 'Xác minh chia sẻ không thành công. Bạn chưa hoàn thành việc đăng bài chia sẻ.';
            if (errData) {
                if (typeof errData.errors === 'string') {
                    errMsg = errData.errors;
                } else if (Array.isArray(errData.errors) && errData.errors.length > 0) {
                    const firstErr = errData.errors[0];
                    errMsg = firstErr?.message || firstErr?.msg || JSON.stringify(firstErr);
                } else if (typeof errData.detail === 'string' && errData.detail !== 'Data validation failed') {
                    errMsg = errData.detail;
                } else if (Array.isArray(errData.detail) && errData.detail.length > 0) {
                    const firstErr = errData.detail[0];
                    errMsg = firstErr?.message || firstErr?.msg || JSON.stringify(firstErr);
                } else if (errData.detail === 'Data validation failed' && errData.errors) {
                    errMsg = typeof errData.errors === 'object' ? JSON.stringify(errData.errors) : String(errData.errors);
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
        
        const userId = authStore.user?.id;
        if (userId) {
          localStorage.setItem(`viral_unlocked_${userId}_${product.id}`, JSON.stringify({
            code: voucherCode, label: voucherLabel, unlocked_at: Date.now(),
            value: data.voucher_value, type: data.voucher_type, min_spend: data.min_spend
          }));
        }
        
        shopStore?.injectViralVoucher(
          data.voucher_code,
          data.voucher_label,
          data.voucher_value,
          data.voucher_type,
          data.min_spend
        );
        try {
          cartStore?.setVouchers(cartStore.vouchers);
        } catch (e) {
          logger.error('Failed to sync to cartStore on unlock', e);
        }
        step = 'revealed'; 
        onUnlock?.();
        triggerFlyAnimation();
        createHeartConfetti(window.innerWidth / 2, window.innerHeight / 2);
        clientUi.showToast('🎉 Đã áp mã ưu đãi!', 'success');
      } catch (e: unknown) {
        const errMsg = e instanceof Error ? e.message : String(e);
        errorMsg = errMsg;
        step = 'error';
        
        clientUi.showToast(errorMsg, 'error');
        logger.error('Xác thực lượt chia sẻ thất bại', e);
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
    clientUi.showToast(`Đã sao chép: ${voucherCode}`, 'success');
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

{#if isMounted && isEnabled}
  {#if step !== 'revealed'}
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
          <div class="stp-one-line">
            <div class="stp-icon-box">
              <Gift size={18} />
            </div>
            <div class="stp-msg">
              <span class="stp-t">{displayRewardLabel}</span>
              {#if errorMsg}
                <div class="flex flex-col gap-1 mt-0.5 items-start">
                  <span class="text-[10px] text-red-500 font-bold bg-red-50 border border-red-200/50 px-2 py-0.5 rounded-sm w-fit leading-tight">{errorMsg}</span>
                  {#if _token}
                    <button 
                      class="text-[10px] text-[#d12a0f] hover:text-[#d33b1d] font-extrabold hover:underline flex items-center gap-0.5 mt-1 transition-colors border:none bg-transparent p-0 cursor-pointer"
                      onclick={() => attemptVerify()}
                    >
                      <span>➔ Tôi đã chia sẻ xong, Xác minh ngay</span>
                    </button>
                  {/if}
                </div>
              {:else if subDescription}
                <span class="stp-sub">{subDescription}</span>
              {/if}
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
            <Zap size={28} class="viral-zap-anim text-[#d12a0f]" />
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
{/if}

<style>
  .viral-overlay {
    position: fixed;
    inset: 0;
    z-index: var(--z-modal-overlay);
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
    background: linear-gradient(90deg, #ff4e50, #d12a0f);
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
    overflow: visible;
    border: none;
    box-shadow: none;
  }

  .stp-one-line { display: flex; align-items: center; gap: 12px; padding: 0; min-height: 0; flex-wrap: wrap; }
  
  .stp-icon-box { 
    position: relative;
    color: #d12a0f; 
    display: flex; 
    align-items: center; 
    justify-content: center;
    width: 24px;
    height: 24px;
    background: transparent;
  }

  .stp-msg { flex: 1; display: flex; flex-direction: column; justify-content: center; }
  .stp-t { font-size: 13px; font-weight: 800; color: #111; letter-spacing: -0.01em; display: inline-block !important; text-transform: lowercase !important; }
  .stp-t::first-letter { text-transform: uppercase !important; }
  .stp-sub { font-size: 11px; color: #666; font-weight: 500; line-height: 1.2; margin-top: 1px; display: inline-block !important; text-transform: lowercase !important; }
  .stp-sub::first-letter { text-transform: uppercase !important; }
  
  .stp-go { 
    position: relative;
    display: flex; align-items: center; gap: 6px; color: #fff; 
    background: #d12a0f;
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
  .stu-loading-text { font-size: 12px; font-weight: 700; color: #d12a0f; }
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
  .stu-btn-prim { flex: 1; height: 36px; background: #d12a0f; color: #fff; border: none; border-radius: 6px; font-size: 12px; font-weight: 900; cursor: pointer; }

  .stu-revealed-card { 
    display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; 
    background: linear-gradient(135deg, #fffaf9, #fff);
    border-radius: 12px;
    border: 1px dashed #d12a0f;
    animation: stu-reveal 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  .stu-voucher-info { display: flex; flex-direction: column; gap: 2px; }
  .stu-voucher-label { font-size: 10px; font-weight: 700; color: #999; }
  .stu-voucher-code { font-size: 20px; font-weight: 900; color: #d12a0f; font-family: monospace; letter-spacing: 1px; }
  .stu-copy-btn { 
    display: flex; align-items: center; gap: 6px;
    padding: 8px 16px; background: #d12a0f; color: #fff; border: none; border-radius: 8px; font-size: 12px; font-weight: 900; cursor: pointer;
    box-shadow: none;
  }

  @keyframes stu-reveal { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  :global(.stu-spin) { animation: stu-rotate 1s linear infinite; }
  @keyframes stu-rotate { to { transform: rotate(360deg); } }
</style>
