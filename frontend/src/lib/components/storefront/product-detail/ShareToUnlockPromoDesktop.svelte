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

  let _token = $state<string | null>(null);
  let _fingerprint = $state<string | null>(null);

  let voucherCode = $state<string | null>(null);
  let voucherLabel = $state<string | null>(null);

  let codeCopied = $state(false);
  let errorMsg = $state('');

  let shareStartTime = $state<number>(0);
  let windowLostFocus = $state<boolean>(false);
  let showFlyGhost = $state(false);

  $effect(() => {
    const onBlur = () => { windowLostFocus = true; };
    window.addEventListener('blur', onBlur);

    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      if (saved) {
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
    return () => window.removeEventListener('blur', onBlur);
  });

  const viralActions = {
    async share() {
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
        
        await shareToPlatform('facebook', window.location.href, product.name);
        
        shareStartTime = Date.now();
        windowLostFocus = false;
        step = 'awaiting_confirm';
      } catch (e: unknown) {
        errorMsg = e instanceof Error ? e.message : String(e);
        step = 'error';
      }
    },
    async verify() {
      if (!_token || !_fingerprint || !promoConfig) return;
      if (Date.now() - shareStartTime < 3000 || !windowLostFocus) {
        errorMsg = 'Vui lòng hoàn tất chia sẻ!';
        step = 'error';
        return;
      }
      step = 'verifying';
      try {
        const res = await fetch('/api/v1/client/viral/verify-share', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            product_id: product.id, 
            fingerprint: _fingerprint, 
            token: _token, 
            voucher_id: promoConfig.voucher_id 
          }),
        });
        if (!res.ok) throw new Error('Xác minh thất bại');
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
            <span class="stp-t">CHIA SẺ NHẬN VOUCHER 50K</span>
            {#if errorMsg}<span class="text-[10px] text-red-500 font-bold">{errorMsg}</span>{/if}
          </div>
          <button class="stp-go" onclick={viralActions.share}>
            <span>NHẬN</span><ExternalLink size={12} />
          </button>
        </div>
      </div>

    {:else if step === 'sharing' || step === 'verifying'}
      <div class="stu-center">
        <Loader size={16} class="stu-spin" style="color: #ee4d2d;" />
        <span class="stu-loading-text">{step === 'sharing' ? 'ĐANG CHUẨN BỊ...' : 'ĐANG XÁC MINH...'}</span>
      </div>

    {:else if step === 'awaiting_confirm'}
      <div class="stu-confirm-view">
         <span class="stu-confirm-txt">Đã chia sẻ?</span>
         <div class="stu-confirm-btns">
            <button class="stu-btn-alt" onclick={resetToIdle}>Hủy</button>
            <button class="stu-btn-prim" onclick={viralActions.verify}>XÁC NHẬN</button>
         </div>
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
  .stp-one-line { display: flex; align-items: center; gap: 10px; padding: 8px 12px; height: 44px; }
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
