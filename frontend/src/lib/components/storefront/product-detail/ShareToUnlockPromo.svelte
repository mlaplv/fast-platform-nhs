<script lang="ts">
  import { Gift, ExternalLink, Check, Copy, Loader, Shield } from 'lucide-svelte';
  
  // Types
  import type { Product } from '$lib/types';
  
  // States
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  interface Props {
    product: Product;
    compact?: boolean;
    variant?: 'bar' | 'floating';
    onUnlock?: () => void;
  }

  let { product, compact = false, variant = 'bar', onUnlock }: Props = $props();
  const clientUi = getClientUi();

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
  type Step = 'idle' | 'sharing' | 'awaiting_confirm' | 'verifying' | 'revealed' | 'error';
  let step = $state<Step>('idle');

  // OTT token stored in memory ONLY — not localStorage (hack-proof)
  let _token = $state<string | null>(null);
  let _fingerprint = $state<string | null>(null);

  // Post-verify voucher data (received from server — never in page source)
  let voucherCode = $state<string | null>(null);
  let voucherLabel = $state<string | null>(null);
  let voucherType = $state<string | null>(null);
  let voucherMinSpend = $state<number>(0);

  let codeCopied = $state(false);
  let errorMsg = $state('');

  // Behavioral verification heuristics
  let shareStartTime = $state<number>(0);
  let windowLostFocus = $state<boolean>(false);

  // Monitor window focus to detect if share dialog was opened
  $effect(() => {
    const onBlur = () => { windowLostFocus = true; };
    window.addEventListener('blur', onBlur);

    // Elite V2.2: Persistence Logic (Load from localStorage)
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      if (saved) {
        try {
          const data: { code: string; label: string; type: string; min_spend: number } = JSON.parse(saved);
          voucherCode = data.code;
          voucherLabel = data.label;
          voucherType = data.type;
          voucherMinSpend = data.min_spend;
          step = 'revealed';
        } catch {
          localStorage.removeItem(`viral_unlocked_${product.id}`);
        }
      }
    }

    return () => window.removeEventListener('blur', onBlur);
  });

  // ── Step 1: Share Intent (Issue OTT) ─────────────────────────────────────
  async function handleShare() {
    if (step !== 'idle' && step !== 'error') return;
    step = 'sharing';

    try {
      // 1a. Request OTT from server
      const intentRes = await fetch('/api/v1/client/viral/share-intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: product.id }),
      });

      if (!intentRes.ok) {
        const err = await intentRes.json().catch(() => ({}));
        if (intentRes.status === 429) {
          throw new Error('Bạn đã yêu cầu chia sẻ quá nhiều lần. Thử lại sau 1 giờ.');
        }
        throw new Error(err?.detail || err?.error || 'Không thể khởi tạo yêu cầu chia sẻ.');
      }

      const intentData: { token: string; fingerprint: string; expires_at: number } =
        await intentRes.json();

      // Store token in memory (resets on page reload — intentional security)
      _token = intentData.token;
      _fingerprint = intentData.fingerprint;

      // 1b. Open native share or Facebook
      if (typeof navigator !== 'undefined' && navigator.share) {
        try {
          await navigator.share({
            title: product.name,
            text: promoConfig?.share_text || `Xem ngay ${product.name} — sản phẩm cực hot!`,
            url: window.location.href,
          });
        } catch (_e) {
          // User cancelled native share — still allow confirm step
        }
      } else {
        const url = encodeURIComponent(window.location.href);
        window.open(
          `https://www.facebook.com/sharer/sharer.php?u=${url}`,
          '_blank',
          'width=600,height=400'
        );
      }

      // Move to awaiting user confirmation
      shareStartTime = Date.now();
      windowLostFocus = false; // Reset focus state
      step = 'awaiting_confirm';
    } catch (e: unknown) {
      errorMsg = e instanceof Error ? e.message : 'Đã xảy ra lỗi. Vui lòng thử lại.';
      step = 'error';
    }
  }

  // ── Step 2: Verify & Redeem ──────────────────────────────────────────────
  async function handleVerify() {
    if (!_token || !_fingerprint || !promoConfig?.voucher_id) return;

    // Behavioral heuristic: User must spend at least 3 seconds sharing OR lose window focus
    const timeSpent = Date.now() - shareStartTime;
    if (timeSpent < 3000 || !windowLostFocus) {
      errorMsg = 'Hệ thống phát hiện bạn chưa hoàn tất việc chia sẻ. Vui lòng thực hiện chia sẻ để nhận mã!';
      step = 'error';
      return;
    }

    step = 'verifying';

    try {
      const verifyRes = await fetch('/api/v1/client/viral/verify-share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: product.id,
          fingerprint: _fingerprint,
          token: _token,
          voucher_id: promoConfig.voucher_id,
        }),
      });

      if (!verifyRes.ok) {
        const err = await verifyRes.json().catch(() => ({}));
        throw new Error(
          err?.detail || err?.error || 'Xác minh thất bại. Vui lòng chia sẻ lại.'
        );
      }

      const data = await verifyRes.json();

      // Voucher is revealed ONLY after server confirmation
      voucherCode = data.voucher_code;
      voucherLabel = data.voucher_label;
      voucherType = data.voucher_type;
      voucherMinSpend = data.min_spend ?? 0;

      // Clear token from memory
      _token = null;
      _fingerprint = null;

      step = 'revealed';

      // Elite V2.2: Persistence Logic
      localStorage.setItem(`viral_unlocked_${product.id}`, JSON.stringify({
        code: voucherCode,
        label: voucherLabel,
        type: voucherType,
        min_spend: voucherMinSpend,
        unlocked_at: Date.now()
      }));

      // Trigger Fly Effect & Parent Sync
      if (onUnlock) onUnlock();
      triggerFlyAnimation();

      clientUi.showToast('🎉 Mã giảm giá đã được mở khóa!', 'success');
    } catch (e: unknown) {
      errorMsg = e instanceof Error ? e.message : 'Xác minh thất bại. Vui lòng thử lại.';
      step = 'error';
    }
  }

  function resetToIdle() {
    step = 'idle';
    errorMsg = '';
    _token = null;
    _fingerprint = null;
  }

  // ── Copy voucher code ─────────────────────────────────────────────────────
  async function copyCode() {
    if (!voucherCode || typeof navigator === 'undefined' || !navigator.clipboard) return;
    await navigator.clipboard.writeText(voucherCode);
    codeCopied = true;
    clientUi.showToast(`Đã sao chép mã "${voucherCode}"`, 'success');
    setTimeout(() => { codeCopied = false; }, 2000);
  }
  let showFlyGhost = $state(false);
  function triggerFlyAnimation() {
    showFlyGhost = true;
    setTimeout(() => { showFlyGhost = false; }, 1000);
  }

  function formatCount(count: number): string {
    if (count >= 1000) return (count / 1000).toFixed(1).replace('.0', '') + 'k';
    return count.toString();
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
  <div class="stu-root {variant === 'floating' ? 'stu-floating' : ''}" class:stu-compact={compact}>
    <!-- ── STEP: idle / error ── -->
    {#if step === 'idle' || step === 'error'}
      <div class="stu-content-row {variant === 'floating' ? 'stu-float-minimal' : 'stp-bar'}">
        {#if variant === 'floating'}
          <div class="stu-viral-main">
            <h4 class="stu-viral-title">CHIA SẺ NHẬN 50K</h4>
            <p class="stu-viral-sub">Nhận Voucher 50.000đ ngay!</p>
            <div class="stu-viral-fomo-tag">
               <span class="stu-fomo-fire">🔥</span> {formatCount(shareCount)}+ ĐÃ NHẬN
            </div>
            <button class="stu-viral-btn-minimal" onclick={handleShare} id="btn-viral-share-{product.id}">
               <span>NHẬN</span>
            </button>
          </div>
        {:else}
          <div class="stu-info">
            <div class="stp-gift-icon"><Gift size={compact ? 20 : 24} /></div>
            <div class="stu-text-col">
              <div class="stp-info">
                <div class="stp-title-wrap flex items-center gap-1">
                  <span class="stp-title">CƠ HỘI CUỐI: CHIA SẺ NHẬN 50K</span>
                </div>
                <p class="stp-desc">Duy nhất hôm nay: Nhận Voucher osmo Mall 50.000đ khi lan tỏa sản phẩm</p>
              </div>
            </div>
          </div>
          <button class="stu-share-btn" onclick={handleShare} id="btn-viral-share-{product.id}">
            <ExternalLink size={14} /><span>{step === 'error' ? 'Thử lại' : 'Chia sẻ ngay'}</span>
          </button>
        {/if}
      </div>

    <!-- ── STEP: sharing / verifying ── -->
    {:else if step === 'sharing' || step === 'verifying'}
      <div class="stu-content-row stu-center {variant === 'floating' ? 'stu-float-card' : ''}">
        <Loader size={16} class="stu-spin text-luxury-sakura" style="color: #ffb7c5;" />
        <span class="stu-loading-text text-[10px]">{step === 'sharing' ? 'ĐANG CHUẨN BỊ...' : 'ĐANG XÁC MINH...'}</span>
      </div>

    <!-- ── STEP: awaiting_confirm ── -->
    {:else if step === 'awaiting_confirm'}
      <div class="stu-content-row {variant === 'floating' ? 'stu-float-card flex-col gap-2' : ''}">
         <div class="stu-info">
           <span class="stu-confirm-text {variant === 'floating' ? 'text-[10px]' : ''}">Đã chia sẻ?</span>
         </div>
         <div class="stu-actions-row {variant === 'floating' ? 'justify-center' : ''}">
            <button class="stu-cancel-btn {variant === 'floating' ? 'h-7 text-[9px] px-2' : ''}" onclick={resetToIdle}>Hủy</button>
            <button class="stu-verify-btn {variant === 'floating' ? 'h-7 text-[9px] px-2' : ''}" onclick={handleVerify} id="btn-viral-verify-{product.id}">
              <Check size={12} /><span>XÁC NHẬN</span>
            </button>
         </div>
      </div>

    <!-- ── STEP: revealed ── -->
    {:else if step === 'revealed' && voucherCode}
      <div class="stu-revealed-card {variant === 'floating' ? 'stu-float-card' : ''}">
        <div class="stu-voucher-info">
          <span class="stu-voucher-label">{voucherLabel}</span>
          <span class="stu-voucher-code {variant === 'floating' ? 'text-lg' : ''}">{voucherCode}</span>
        </div>
        <button class="stu-copy-btn {variant === 'floating' ? 'text-[9px] px-2' : ''}" onclick={copyCode} id="btn-viral-copy-{product.id}">
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
  .stu-root {
    position: relative;
    padding: 0;
    transition: all 0.3s ease;
  }

  .stu-compact {
    padding: 0;
  }

  .stu-content-row {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  @media (min-width: 768px) {
    .stu-content-row {
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
  }

  .stu-center {
    justify-content: center;
    flex-direction: row !important;
  }

  .stu-info {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
  }

  .stp-gift-icon {
    color: #ee4d2d;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .stu-text-col {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
  }

  .stp-title {
    font-size: 13px; font-weight: 900;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: #111;
  }

  .stp-desc { font-size: 11px; color: #666; margin: 2px 0 0; }

  .stu-desc { font-size: 11px; color: rgba(255,255,255,0.6); }
  .stu-compact .stu-desc { font-size: 10px; }
  .stu-error-text { color: #ef4444; font-weight: 600; }

  .stp-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 14px;
    position: relative;
    background: white;
    
    /* 🎟️ ELITE ZIGZAG BORDER (TINH TẾ) */
    border: 1px dashed #ee4d2d;
    border-radius: 2px;
    margin: 4px 0;
    
    /* Hiệu ứng đục lỗ 2 đầu */
    mask-image: 
      radial-gradient(circle at 0 50%, transparent 5px, black 6px),
      radial-gradient(circle at 100% 50%, transparent 5px, black 6px);
    mask-composite: intersect;
  }

  .stp-bar::after {
    display: none;
  }

  .stu-share-btn {
    display: flex; align-items: center; gap: 6px;
    color: #ee4d2d;
    font-size: 12px; font-weight: 800;
    text-transform: uppercase;
    transition: all 0.2s ease;
    white-space: nowrap;
    border: none;
    background: transparent;
    padding: 4px 8px;
  }
  .stu-share-btn:hover {
    opacity: 0.8;
    transform: translateX(3px);
  }

  .stu-loading-text { font-size: 12px; color: rgba(255,255,255,0.7); font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;}
  :global(.stu-spin) { animation: stu-rotate 1s linear infinite; }
  @keyframes stu-rotate { to { transform: rotate(360deg); } }

  .stu-confirm-text { font-size: 13px; color: #111; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
  
  .stu-actions-row { display: flex; gap: 8px; width: 100%; }
  @media (min-width: 768px) {
    .stu-actions-row { width: auto; }
  }

  .stu-verify-btn {
    flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
    height: 36px; padding: 0 16px;
    background: #ee4d2d;
    color: #fff; border: none; border-radius: 8px;
    font-size: 11px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.05em;
    cursor: pointer; transition: all 0.3s;
    white-space: nowrap;
  }
  .stu-verify-btn:hover { opacity: 0.8; transform: translateY(-1px); }

  .stu-cancel-btn {
    padding: 0 12px; height: 36px; border-radius: 8px;
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.6); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    cursor: pointer; transition: all 0.2s;
  }
  .stu-cancel-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }

  /* ═══ VIRAL 2026: WRAPPER ═══ */
  .stu-floating {
    position: relative;
    z-index: 100;
    pointer-events: auto;
    max-width: 200px;
  }

  /* ═══ TIKTOK PRO 2026: SHARP & DYNAMIC ═══ */
  .stu-float-minimal {
    display: flex;
    flex-direction: column;
    gap: 2px;
    color: white;
    padding: 0;
    pointer-events: auto;
    animation: stu-pro-entry 0.6s cubic-bezier(0.25, 1, 0.5, 1);
  }

  @keyframes stu-pro-entry {
    0% { transform: translateX(-80px) scale(0.8); opacity: 0; }
    100% { transform: translateX(0) scale(1); opacity: 1; }
  }

  .stu-viral-title {
    font-size: 18px;
    font-weight: 1000;
    margin: 0;
    color: #fff;
    /* TikTok 3D Sharp Stroke */
    -webkit-text-stroke: 1px rgba(0,0,0,0.5);
    text-shadow: 
      0 2px 10px rgba(0,0,0,0.5),
      0 0 20px rgba(0,0,0,0.2);
    letter-spacing: -0.03em;
    line-height: 1;
    text-transform: uppercase;
  }

  .stu-viral-sub {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.95);
    margin: 4px 0 0;
    font-weight: 700;
    text-shadow: 0 1px 4px rgba(0,0,0,0.8);
    letter-spacing: 0.01em;
  }

  .stu-viral-fomo-tag {
    font-size: 12px;
    font-weight: 900;
    color: #ff9500; 
    text-transform: uppercase;
    margin-top: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
    text-shadow: 0 1px 3px rgba(0,0,0,0.8);
  }

  .stu-fomo-fire {
    display: inline-block;
    animation: stu-fire-wiggle 1s infinite alternate ease-in-out;
  }

  @keyframes stu-fire-wiggle {
    from { transform: rotate(-10deg) scale(1); }
    to { transform: rotate(10deg) scale(1.2); }
  }

  .stu-viral-btn-minimal {
    margin-top: 14px;
    background: linear-gradient(180deg, #ff453a 0%, #ff3b30 100%);
    color: white;
    border: 1px solid rgba(255,255,255,0.2);
    padding: 7px 24px;
    border-radius: 100px;
    font-size: 13px;
    font-weight: 1000;
    width: max-content;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(255, 59, 48, 0.4);
    position: relative;
    overflow: hidden;
    animation: stu-btn-pulse 2s infinite;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }

  /* Liquid Glass Shine */
  .stu-viral-btn-minimal::after {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: linear-gradient(
      45deg,
      transparent 0%,
      rgba(255,255,255,0.1) 45%,
      rgba(255,255,255,0.5) 50%,
      rgba(255,255,255,0.1) 55%,
      transparent 100%
    );
    transform: rotate(45deg);
    animation: stu-liquid-shine 3s infinite;
  }

  @keyframes stu-liquid-shine {
    0% { transform: translateX(-100%) rotate(45deg); }
    100% { transform: translateX(100%) rotate(45deg); }
  }

  .stu-viral-btn-minimal:active {
    transform: scale(0.9);
    filter: brightness(1.2);
  }

  /* ── Revealed Card ── */
  .stu-revealed-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    position: relative;
    background: #fffcfc;
    
    /* 🎟️ ELITE REVEALED TICKET (ZIGZAG) */
    border: 1.5px dashed #ee4d2d;
    border-radius: 2px;
    margin: 4px 0;
    animation: stu-reveal 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);

    mask-image: 
      radial-gradient(circle at 0 50%, transparent 6px, black 7px),
      radial-gradient(circle at 100% 50%, transparent 6px, black 7px);
    mask-composite: intersect;
  }

  .stu-voucher-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .stu-voucher-label {
    font-size: 9px;
    font-weight: 800;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .stu-voucher-code {
    font-size: 20px;
    font-weight: 900;
    color: #ee4d2d;
    letter-spacing: 0.1em;
    font-family: 'Courier New', Courier, monospace;
    text-decoration: underline;
    text-decoration-style: dotted;
    text-underline-offset: 4px;
  }

  .stu-copy-btn {
    display: flex; align-items: center; justify-content: center; gap: 6px;
    background: rgba(255, 183, 197, 0.15); color: #ffb7c5; 
    border: 1px solid rgba(255, 183, 197, 0.3);
    padding: 6px 12px; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
    border-radius: 6px; cursor: pointer; transition: all 0.2s; white-space: nowrap;
  }
  .stu-copy-btn:hover { background: #ee4d2d; color: #fff; }

  /* ═══ VOUCHER FLY ANIMATION ═══ */
  .stu-fly-ghost {
    position: fixed;
    z-index: 9999;
    bottom: 25%;
    left: 50%;
    pointer-events: none;
    animation: stu-fly-trajectory 1.2s cubic-bezier(0.19, 1, 0.22, 1) forwards;
  }

  .stu-fly-content {
    background: #fff;
    border: 1.5px dashed #ee4d2d;
    padding: 6px 12px;
    border-radius: 4px;
    color: #ee4d2d;
    box-shadow: 0 10px 30px rgba(238, 77, 45, 0.4);
    animation: stu-fly-spin 1.2s ease-out forwards;
    white-space: nowrap;
  }

  @keyframes stu-fly-trajectory {
    0% { transform: translate(-50%, 0) scale(1.5); opacity: 0; }
    10% { opacity: 1; }
    100% { transform: translate(-50%, -450px) scale(0.2); opacity: 0; }
  }

  @keyframes stu-fly-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(1080deg); }
  }
</style>
