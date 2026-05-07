<script lang="ts">
  import { Gift, ExternalLink, Check, Copy, Loader, Shield } from 'lucide-svelte';
  import type { Product } from '$lib/types';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  interface Props {
    product: Product;
    compact?: boolean;
  }

  let { product, compact = false }: Props = $props();
  const clientUi = getClientUi();

  /**
   * Share promotion config from product.metadata.share_promotion
   */
  const promoConfig = $derived(product.metadata?.share_promotion ?? null);
  const isEnabled = $derived(
    promoConfig?.enabled === true && !!promoConfig?.voucher_id
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
</script>

{#if isEnabled}
  <div class="stu-root" class:stu-compact={compact}>
    <!-- ── STEP: idle / error ── -->
    {#if step === 'idle' || step === 'error'}
      <div class="stu-content-row">
        <div class="stu-info">
          <div class="stu-icon-wrap"><Gift size={compact ? 14 : 16} /></div>
          <div class="stu-text-col">
            <div class="stu-title-row">
              <span class="stu-title">{promoConfig?.cta_text || 'Chia sẻ nhận mã'}</span>
            </div>
            {#if step === 'error'}
              <span class="stu-desc stu-error-text">{errorMsg}</span>
            {:else}
              <span class="stu-desc">Mở khóa ngay {promoConfig?.voucher_label || 'mã độc quyền'}</span>
            {/if}
          </div>
        </div>
        <button class="stu-share-btn" onclick={handleShare} id="btn-viral-share-{product.id}">
          <ExternalLink size={14} /><span>{step === 'error' ? 'Thử lại' : 'Chia sẻ ngay'}</span>
        </button>
      </div>

    <!-- ── STEP: sharing / verifying ── -->
    {:else if step === 'sharing' || step === 'verifying'}
      <div class="stu-content-row stu-center">
        <Loader size={16} class="stu-spin text-luxury-sakura" style="color: #ffb7c5;" />
        <span class="stu-loading-text">{step === 'sharing' ? 'Đang chuẩn bị...' : 'Đang xác minh...'}</span>
      </div>

    <!-- ── STEP: awaiting_confirm ── -->
    {:else if step === 'awaiting_confirm'}
      <div class="stu-content-row">
         <div class="stu-info">
           <span class="stu-confirm-text">Đã chia sẻ xong?</span>
         </div>
         <div class="stu-actions-row">
            <button class="stu-cancel-btn" onclick={resetToIdle}>Hủy</button>
            <button class="stu-verify-btn" onclick={handleVerify} id="btn-viral-verify-{product.id}">
              <Check size={14} /><span>Nhận mã</span>
            </button>
         </div>
      </div>

    <!-- ── STEP: revealed ── -->
    {:else if step === 'revealed' && voucherCode}
      <div class="stu-revealed-card">
        <div class="stu-voucher-info">
          <span class="stu-voucher-label">{voucherLabel}</span>
          <span class="stu-voucher-code">{voucherCode}</span>
        </div>
        <button class="stu-copy-btn" onclick={copyCode} id="btn-viral-copy-{product.id}">
          {#if codeCopied}
            <Check size={12} /><span>Đã chép</span>
          {:else}
            <Copy size={12} /><span>Sao chép</span>
          {/if}
        </button>
      </div>
    {/if}
  </div>
{/if}

<style>
  .stu-root {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 183, 197, 0.15);
    border-radius: 12px;
    padding: 12px;
    color: white;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s ease;
  }

  .stu-compact {
    padding: 8px 12px;
    border-radius: 8px;
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

  .stu-icon-wrap {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ffb7c5, #ff6b8b);
    display: flex; align-items: center; justify-content: center;
    color: #111; flex-shrink: 0;
    box-shadow: 0 0 12px rgba(255, 183, 197, 0.4);
  }
  .stu-compact .stu-icon-wrap { width: 26px; height: 26px; }

  .stu-text-col {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
  }

  .stu-title-row {
    display: flex; align-items: center; gap: 8px;
  }

  .stu-title {
    font-size: 13px; font-weight: 900;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: #fff; text-shadow: 0 2px 4px rgba(0,0,0,0.5);
  }
  .stu-compact .stu-title { font-size: 11px; }

  .stu-desc { font-size: 11px; color: rgba(255,255,255,0.6); }
  .stu-compact .stu-desc { font-size: 10px; }
  .stu-error-text { color: #ef4444; font-weight: 600; }

  .stu-share-btn {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    height: 36px; padding: 0 16px;
    background: rgba(255, 183, 197, 0.1); 
    border: 1px solid rgba(255, 183, 197, 0.3);
    color: #ffb7c5;
    font-size: 11px; font-weight: 900;
    text-transform: uppercase; letter-spacing: 0.1em;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    white-space: nowrap;
  }
  .stu-share-btn:hover {
    background: linear-gradient(135deg, #ffb7c5, #ff6b8b);
    color: #111; border-color: transparent;
    box-shadow: 0 4px 15px rgba(255, 183, 197, 0.3);
  }

  .stu-loading-text { font-size: 12px; color: rgba(255,255,255,0.7); font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;}
  :global(.stu-spin) { animation: stu-rotate 1s linear infinite; }
  @keyframes stu-rotate { to { transform: rotate(360deg); } }

  .stu-confirm-text { font-size: 13px; color: #fff; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
  
  .stu-actions-row { display: flex; gap: 8px; width: 100%; }
  @media (min-width: 768px) {
    .stu-actions-row { width: auto; }
  }

  .stu-verify-btn {
    flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
    height: 36px; padding: 0 16px;
    background: linear-gradient(135deg, #ffb7c5, #ff6b8b);
    color: #111; border: none; border-radius: 8px;
    font-size: 11px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.05em;
    cursor: pointer; transition: all 0.3s;
    white-space: nowrap;
  }
  .stu-verify-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(255, 183, 197, 0.4); }

  .stu-cancel-btn {
    padding: 0 12px; height: 36px; border-radius: 8px;
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.6); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    cursor: pointer; transition: all 0.2s;
  }
  .stu-cancel-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }

  /* ── Revealed Card ── */
  .stu-revealed-card {
    display: flex; flex-direction: column; gap: 12px;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 183, 197, 0.2);
    border-radius: 8px; padding: 10px 14px;
    animation: stu-reveal 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  @media (min-width: 768px) {
    .stu-revealed-card { flex-direction: row; align-items: center; justify-content: space-between; }
  }
  @keyframes stu-reveal {
    0% { opacity: 0; transform: scale(0.95); }
    100% { opacity: 1; transform: scale(1); }
  }

  .stu-voucher-info { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .stu-voucher-label { font-size: 12px; font-weight: 900; color: #ffb7c5; text-transform: uppercase; letter-spacing: 0.05em;}
  
  .stu-voucher-code {
    font-size: 14px; font-weight: 900;
    font-family: ui-monospace, 'Fira Code', monospace;
    letter-spacing: 0.15em; color: #fff;
    background: rgba(255,255,255,0.05); padding: 4px 10px;
    border: 1px solid rgba(255,255,255,0.1); border-radius: 6px;
  }

  .stu-copy-btn {
    display: flex; align-items: center; justify-content: center; gap: 6px;
    background: rgba(255, 183, 197, 0.15); color: #ffb7c5; 
    border: 1px solid rgba(255, 183, 197, 0.3);
    padding: 6px 12px; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
    border-radius: 6px; cursor: pointer; transition: all 0.2s; white-space: nowrap;
  }
  .stu-copy-btn:hover { background: #ffb7c5; color: #111; }
</style>
