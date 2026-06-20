<script lang="ts">
  import Gift from "@lucide/svelte/icons/gift";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Check from "@lucide/svelte/icons/check";
  import Copy from "@lucide/svelte/icons/copy";
  import Loader from "@lucide/svelte/icons/loader";
  import Zap from "@lucide/svelte/icons/zap";
  import Heart from "@lucide/svelte/icons/heart";
  import Facebook from "$lib/components/ui/icons/Facebook.svelte";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Share2 from "@lucide/svelte/icons/share-2";
  import { untrack, onMount, onDestroy } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import type { Product, ProductMetadata } from '$lib/types';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti, getProductLikeCount
  } from '$lib/utils/commerce/viral';
  import { logger } from "$lib/utils/logger";
  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';
  import { authStore } from '$lib/state/authStore.svelte';

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
  let activePlatform = $state<string>('facebook');

  let shareStartTime = $state<number>(0);
  let honeypotTriggered = $state(false);

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
  const likeCount = $derived(getProductLikeCount(product, isLiked));

  function toggleLike() {
    wishlistStore.toggle(product.id);
    if (wishlistStore.isLiked(product.id)) {
      clientUi.showToast('Đã lưu sản phẩm vào mục yêu thích!', 'success');
      createHeartConfetti(window.innerWidth / 2, window.innerHeight / 2);
    }
  }

  // ── Elite V2.2: Focus Listeners & Verification Controls ──────────────────────
  let hasRegisteredListeners = false;
  let pollTimer: ReturnType<typeof setInterval> | null = null;
  let popupWindow: Window | null = null;
  let verifyAttempts = 0;
  let isVerifying = false;
  let oauthMessageHandler: ((e: MessageEvent) => void) | null = null;

  const handleFocus = () => {
    const duration = Date.now() - shareStartTime;
    logger.log(`[ShareToUnlockMobile Focus] Trang chính nhận sự kiện 'focus'. Thời gian kể từ khi mở popup: ${duration}ms.`);
    // Bỏ qua nếu thời gian quá ngắn dưới 1s (tránh focus nhầm khi vừa click mở popup)
    if (duration < 1000) {
        logger.warn(`[ShareToUnlockMobile Focus] Bỏ qua sự kiện focus do duration quá ngắn (${duration}ms < 1000ms - có thể là focus ảo lúc mở)`);
        return;
    }
    
    cleanupFocusListeners();
    if (step !== 'revealed') {
        logger.log(`[ShareToUnlockMobile Focus] Gọi attemptVerify() để backend kiểm tra.`);
        attemptVerify();
    }
  };

  const handleVisibilityChange = () => {
    if (!document.hidden) {
      const duration = Date.now() - shareStartTime;
      logger.log(`[ShareToUnlockMobile Visibility] Trang chính nhận sự kiện 'visibilitychange' (visible). Thời gian kể từ khi mở popup: ${duration}ms.`);
      if (duration < 1000) {
          logger.warn(`[ShareToUnlockMobile Visibility] Bỏ qua sự kiện visibility do duration quá ngắn (${duration}ms < 1000ms)`);
          return;
      }
      
      cleanupFocusListeners();
      if (step !== 'revealed') {
          logger.log(`[ShareToUnlockMobile Visibility] Gọi attemptVerify() để backend kiểm tra.`);
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
    if (!isComponentMounted || isVerifying || step === 'revealed' || verifyAttempts >= 3) return;
    
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

  $effect(() => {
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
    return () => {
        isComponentMounted = false;
        cleanupFocusListeners();
    };
  });

  onDestroy(() => {
    cleanupFocusListeners();
    if (progressInterval) {
      clearInterval(progressInterval);
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
        logger.log(`[ShareToUnlockMobile Share] Mở popup. Target: Share Dialog. shareStartTime: ${shareStartTime}`);

        popupWindow = window.open(targetUrl, 'Share', `toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=no, resizable=no, copyhistory=no, width=${w}, height=${h}, top=${top}, left=${left}`);
        
        if (!popupWindow || popupWindow.closed || typeof popupWindow.closed === 'undefined') {
            logger.error('[ShareToUnlockMobile Share] Popup bị chặn hoặc closed ngay lập tức. Sử dụng fallback verify sau 2s.');
            setTimeout(() => { if (isComponentMounted) viralActions.verify(); }, 2000);
        } else {
            logger.log('[ShareToUnlockMobile Share] Mở popup thành công. Bắt đầu pollTimer.');
            // Polling phát hiện khi popup đóng
            pollTimer = setInterval(() => {
                if (!isComponentMounted) {
                    cleanupFocusListeners();
                    return;
                }
                if (popupWindow) {
                    const isClosed = popupWindow.closed;
                    const duration = Date.now() - shareStartTime;
                    
                    if (isClosed) {
                        logger.log(`[ShareToUnlockMobile Poller] Phát hiện popupWindow.closed = true. Trôi qua: ${duration}ms`);
                        cleanupFocusListeners();
                        if (isComponentMounted && step !== 'revealed') {
                            attemptVerify();
                        }
                    }
                }
            }, 800);
        }
      } catch (e: unknown) {
        errorMsg = e instanceof Error ? e.message : 'Đã xảy ra lỗi';
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
        if (onUnlock) onUnlock();
        triggerFlyAnimation();
        createHeartConfetti(window.innerWidth / 2, window.innerHeight / 2);
        clientUi.showToast('🎉 Đã áp mã ưu đãi!', 'success');
      } catch (e: unknown) {
        const errMsg = e instanceof Error ? e.message : 'Xác minh thất bại';
        errorMsg = errMsg;
        step = 'error';
        clientUi.showToast(errorMsg, 'error');
        logger.error('Xác thực lượt chia sẻ trên Mobile thất bại', e);
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

{#if isMounted && isEnabled}
  {#if step !== 'revealed'}
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
                {#if errorMsg}
                  <div class="flex flex-col gap-1.5 mt-1 items-start">
                    <span class="text-[9px] text-red-400 font-bold bg-red-950/40 border border-red-500/20 px-2 py-0.5 rounded-sm w-fit">{errorMsg}</span>
                    {#if _token}
                      <button 
                        class="text-[9px] text-[#ffb7c5] hover:text-white font-extrabold hover:underline flex items-center gap-0.5 mt-0.5 transition-colors border:none bg-transparent p-0 cursor-pointer"
                        onclick={() => attemptVerify()}
                      >
                        <span>➔ Tôi đã chia sẻ xong, Xác minh ngay</span>
                      </button>
                    {/if}
                  </div>
                {:else if subDescription}
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
                <button class="stp-f-social-btn" onclick={() => viralActions.share('facebook')} aria-label="Share on Facebook"><Facebook size={16} /></button>
                <button class="stp-f-social-btn" onclick={() => viralActions.share('zalo')} aria-label="Share on Zalo"><span class="text-[9px] font-black italic">Zalo</span></button>
                <button class="stp-f-social-btn" onclick={() => viralActions.share('tiktok')} aria-label="Share on TikTok"><span class="text-[9px] font-black italic">TikTok</span></button>
                <button class="stp-f-social-btn" onclick={copyCode} aria-label="Copy code"><Copy size={14} /></button>
              </div>
              <div class="stp-funnel-row">
                <div class="stp-f-msg">
                  <span class="stp-f-t inline-block first-letter:uppercase">{displayRewardLabel}</span>
                  {#if errorMsg}
                    <div class="flex flex-col gap-1 items-start mt-0.5">
                      <span class="text-[9px] text-red-400 font-bold leading-none mb-1 inline-block first-letter:uppercase">{errorMsg}</span>
                      {#if _token}
                        <button 
                          class="text-[9px] text-[#ffb7c5] hover:text-white font-extrabold hover:underline flex items-center gap-0.5 mb-1 transition-colors border:none bg-transparent p-0 cursor-pointer"
                          onclick={() => attemptVerify()}
                        >
                          <span>➔ Tôi đã chia sẻ xong, Xác minh ngay</span>
                        </button>
                      {/if}
                    </div>
                  {:else if subDescription}
                    <span class="text-[8px] text-[#ffb7c5] font-medium leading-none mb-1 inline-block first-letter:uppercase">{subDescription}</span>
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
  .stp-f-bar { height: 100%; background: linear-gradient(90deg, #ffb7c5, #d12a0f); border-radius: 10px; }
  .stp-f-btn { 
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, #d12a0f, #eb3c1a); color: #fff; 
    padding: 8px 10px; border-radius: 6px; font-size: 11px; font-weight: 1000; border: none; cursor: pointer;
    box-shadow: 0 4px 15px rgba(209, 42, 15, 0.25); transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    letter-spacing: 0.05em;
  }
  .stp-f-btn:active { transform: scale(0.92); }

  /* --- Floating Variant (iOS 26 x TikTok) --- */
  .stu-ios-container {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 8px 12px;
    background: #111827; /* Solid dark color for accessibility contrast */
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  }
  .stu-ios-content { display: flex; flex-direction: column; gap: 0; }
  .stu-ios-title { 
    font-size: 18px; font-weight: 1000; color: #ffffff; 
    text-shadow: 0 2px 15px rgba(0,0,0,0.8), 0 1px 2px rgba(0,0,0,0.9);
    letter-spacing: -0.02em; line-height: 1;
  }
  .stu-ios-sub { 
    font-size: 10px; font-weight: 800; color: #e5e7eb; /* Solid gray color to guarantee contrast ratio */
    letter-spacing: 0.05em; margin-top: 2px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.8);
  }
  
  .stu-ios-btn { 
    position: relative; overflow: hidden;
    background: #C8102E;
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
  .stu-loading-text { font-size: 11px; font-weight: 800; color: #d12a0f; }
  .stu-loading-text-blue { font-size: 13px; font-weight: 1000; color: #ffffff; letter-spacing: -0.01em; }
  
  :global(.stu-spin-pulse) { animation: stu-pulse-zap 1.5s ease-in-out infinite; filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.4)); }
  @keyframes stu-pulse-zap {
    0%, 100% { transform: scale(1) rotate(0deg); opacity: 1; }
    50% { transform: scale(1.2) rotate(15deg); opacity: 0.7; }
  }
  
  .stu-confirm-view { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 16px; background: #fff; border: 1.5px dashed #d12a0f; border-radius: 4px; }
  .stu-confirm-txt { font-size: 14px; font-weight: 1000; color: #000; }
  .stu-confirm-btns { display: flex; gap: 8px; width: 100%; }
  .stu-btn-alt { flex: 1; height: 36px; background: #f5f5f5; color: #666; border: none; border-radius: 6px; font-size: 12px; font-weight: 800; }
  .stu-btn-prim { flex: 1; height: 36px; background: #d12a0f; color: #fff; border: none; border-radius: 6px; font-size: 12px; font-weight: 1000; }

  .stu-revealed-card { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: #fffcfc; border: 1.5px dashed #d12a0f; border-radius: 4px; animation: stu-reveal 0.5s ease; }
  .stu-voucher-info { display: flex; flex-direction: column; }
  .stu-voucher-label { font-size: 10px; font-weight: 800; color: #999; }
  .stu-voucher-code { font-size: 18px; font-weight: 1000; color: #d12a0f; font-family: monospace; }
  .stu-copy-btn { padding: 6px 12px; background: #d12a0f; color: #fff; border: none; border-radius: 6px; font-size: 11px; font-weight: 900; }

  @keyframes stu-fade-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes stu-reveal { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  :global(.stu-spin) { animation: stu-rotate 1s linear infinite; }
  @keyframes stu-rotate { to { transform: rotate(360deg); } }

  .stu-fly-ghost { position: fixed; z-index: 9999; bottom: 25%; left: 50%; pointer-events: none; animation: stu-fly 1.2s ease-in forwards; }
  .stu-fly-content { background: #fff; border: 1.5px dashed #d12a0f; padding: 6px 12px; border-radius: 4px; color: #d12a0f; box-shadow: 0 10px 30px rgba(209, 42, 15, 0.4); }
  @keyframes stu-fly { 0% { transform: translate(-50%, 0) scale(1.5); opacity: 0; } 10% { opacity: 1; } 100% { transform: translate(-50%, -400px) scale(0.2); opacity: 0; } }
</style>
