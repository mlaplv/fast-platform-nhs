<script lang="ts">
  import { Gift, ExternalLink, Check, Copy, Loader, Shield, Heart, Facebook } from 'lucide-svelte';
  
  // Types
  import type { Product } from '$lib/types';
  
  // States
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  interface Props {
    product: Product;
    compact?: boolean;
    variant?: 'bar' | 'floating' | 'funnel';
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

  function formatCount(count: number): string {
    if (count >= 1000) return (count / 1000).toFixed(1).replace('.0', '') + 'k';
    return count.toString();
  }

  // --- Logic Suite (Decoupled) ---
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
        
        if (typeof navigator !== 'undefined' && navigator.share) {
          await navigator.share({ title: product.name, url: window.location.href });
        } else {
          window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}`, '_blank', 'width=600,height=400');
        }
        shareStartTime = Date.now();
        windowLostFocus = false;
        step = 'awaiting_confirm';
      } catch (e: any) {
        errorMsg = e.message;
        step = 'error';
      }
    },
    async verify() {
      if (!_token || !_fingerprint) return;
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
          body: JSON.stringify({ product_id: product.id, fingerprint: _fingerprint, token: _token, voucher_id: promoConfig.voucher_id }),
        });
        if (!res.ok) throw new Error('Xác minh thất bại');
        const data = await res.json();
        voucherCode = data.voucher_code;
        voucherLabel = data.voucher_label;
        step = 'revealed';
        localStorage.setItem(`viral_unlocked_${product.id}`, JSON.stringify({ code: voucherCode, label: voucherLabel, unlocked_at: Date.now() }));
        if (onUnlock) onUnlock();
        triggerFlyAnimation();
        clientUi.showToast('🎉 Đã mở khóa!', 'success');
      } catch (e: any) {
        errorMsg = e.message;
        step = 'error';
      }
    }
  };

  // --- Helpers ---
  let showFlyGhost = $state(false);
  function triggerFlyAnimation() {
    showFlyGhost = true;
    setTimeout(() => { showFlyGhost = false; }, 1000);
  }

  async function copyCode() {
    if (!voucherCode || !navigator.clipboard) return;
    await navigator.clipboard.writeText(voucherCode);
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
</script>

{#if showFlyGhost}
  <div class="stu-fly-ghost">
    <div class="stu-fly-content">
       <span class="text-[10px] font-black">{voucherCode}</span>
    </div>
  </div>
{/if}

{#if isEnabled && step !== 'revealed'}
  <div class="stu-root {variant}" class:stu-compact={compact}>
    {#if step === 'idle' || step === 'error'}
      <div class="stu-view-{variant}">
        {#if variant === 'floating'}
          <div class="stu-f-content">
            <h4 class="stu-f-title">CHIA SẺ NHẬN 50K</h4>
            <div class="stu-f-fomo">🔥 {formatCount(shareCount)}+ ĐÃ NHẬN</div>
            <button class="stu-f-btn" onclick={viralActions.share}>NHẬN</button>
          </div>
        {:else if variant === 'funnel'}
          <div class="stp-funnel-wrapper">
            <!-- Row 1: Unified Social Actions -->
            <div class="stp-f-social">
              <button class="stp-f-heart"><Heart size={16} class="fill-current" /><span>{formatCount(shareCount * 12)}</span></button>
              <div class="stp-f-divider"></div>
              <button class="stp-f-social-btn" onclick={viralActions.share}><Facebook size={16} /></button>
              <button class="stp-f-social-btn" onclick={viralActions.share}><span class="text-[9px] font-black italic">Zalo</span></button>
              <button class="stp-f-social-btn" onclick={viralActions.share}><span class="text-[9px] font-black italic">TikTok</span></button>
              <button class="stp-f-social-btn" onclick={copyCode}><Copy size={14} /></button>
            </div>
            <!-- Row 2: Campaign Progress -->
            <div class="stp-funnel-row">
              <div class="stp-f-msg">
                <span class="stp-f-t">CHIẾN DỊCH LAN TỎA NHẬN VOUCHER 50K</span>
                <div class="stp-f-progress">
                  <div class="stp-f-bar" style="width: 50%"></div>
                </div>
              </div>
              <button class="stp-f-btn" onclick={viralActions.share}>
                <span>NHẬN NGAY</span>
              </button>
            </div>
          </div>
        {:else}
          <div class="stp-one-line">
            <div class="stp-icon-box"><Gift size={18} /></div>
            <div class="stp-msg">
              <span class="stp-t">CHIA SẺ NHẬN 50K</span>
            </div>
            <button class="stp-go" onclick={viralActions.share}>
              <span>NHẬN</span><ExternalLink size={12} />
            </button>
          </div>
        {/if}
      </div>

    <!-- ── STEP: sharing / verifying ── -->
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
  .stu-root { position: relative; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
  
  /* --- Bar Variant (Single Line Viral) --- */
  .stu-view-bar {
    padding: 0; background: #fff; position: relative; border-radius: 4px; margin: 6px 0;
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

  /* --- Funnel Variant (Optimized Header) --- */
  .stu-view-funnel { width: 100%; padding: 0; }
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
  
  .stp-funnel-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-top: 1px solid rgba(255,255,255,0.1); }
  .stp-f-msg { flex: 1; display: flex; flex-direction: column; gap: 4px; }
  .stp-f-t { font-size: 9px; font-weight: 900; color: #ffb7c5; text-transform: uppercase; letter-spacing: 0.1em; }
  .stp-f-progress { height: 4px; background: rgba(255,255,255,0.05); border-radius: 10px; overflow: hidden; }
  .stp-f-bar { height: 100%; background: linear-gradient(90deg, #ffb7c5, #ee4d2d); border-radius: 10px; }
  .stp-f-btn { 
    background: #ee4d2d; color: #fff; padding: 6px 16px; border-radius: 4px; font-size: 11px; font-weight: 1000; border: none; cursor: pointer;
    box-shadow: 0 4px 12px rgba(238, 77, 45, 0.2); transition: all 0.2s;
  }
  .stp-f-btn:hover { transform: translateY(-1px); filter: brightness(1.1); }

  /* --- Floating Variant (Storefront Optimized) --- */
  .stu-view-floating { position: relative; max-width: 200px; animation: stu-fade-in 0.6s ease; }
  .stu-f-content { display: flex; flex-direction: column; gap: 4px; color: #fff; }
  .stu-f-title { font-size: 18px; font-weight: 1000; -webkit-text-stroke: 1px rgba(0,0,0,0.5); text-shadow: 0 2px 10px rgba(0,0,0,0.5); }
  .stu-f-fomo { font-size: 12px; font-weight: 900; color: #ff9500; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
  .stu-f-btn { 
    margin-top: 10px; background: linear-gradient(180deg, #ff453a, #ff3b30); color: #fff;
    padding: 8px 24px; border-radius: 100px; font-size: 13px; font-weight: 1000; border: none;
    box-shadow: 0 4px 15px rgba(255, 59, 48, 0.4); cursor: pointer;
  }

  /* --- Universal States --- */
  .stu-center { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px; }
  .stu-loading-text { font-size: 11px; font-weight: 800; color: #ee4d2d; text-transform: uppercase; }
  
  .stu-confirm-view { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 16px; background: #fff; border: 1.5px dashed #ee4d2d; border-radius: 4px; }
  .stu-confirm-txt { font-size: 14px; font-weight: 1000; color: #000; text-transform: uppercase; }
  .stu-confirm-btns { display: flex; gap: 8px; width: 100%; }
  .stu-btn-alt { flex: 1; height: 36px; background: #f5f5f5; color: #666; border: none; border-radius: 6px; font-size: 12px; font-weight: 800; }
  .stu-btn-prim { flex: 1; height: 36px; background: #ee4d2d; color: #fff; border: none; border-radius: 6px; font-size: 12px; font-weight: 1000; }

  .stu-revealed-card { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: #fffcfc; border: 1.5px dashed #ee4d2d; border-radius: 4px; animation: stu-reveal 0.5s ease; }
  .stu-voucher-info { display: flex; flex-direction: column; }
  .stu-voucher-label { font-size: 10px; font-weight: 800; color: #999; text-transform: uppercase; }
  .stu-voucher-code { font-size: 18px; font-weight: 1000; color: #ee4d2d; font-family: monospace; }
  .stu-copy-btn { padding: 6px 12px; background: #ee4d2d; color: #fff; border: none; border-radius: 6px; font-size: 11px; font-weight: 900; }

  /* --- Animations --- */
  @keyframes stu-fade-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes stu-reveal { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  :global(.stu-spin) { animation: stu-rotate 1s linear infinite; }
  @keyframes stu-rotate { to { transform: rotate(360deg); } }

  .stu-fly-ghost { position: fixed; z-index: 9999; bottom: 25%; left: 50%; pointer-events: none; animation: stu-fly 1.2s ease-in forwards; }
  .stu-fly-content { background: #fff; border: 1.5px dashed #ee4d2d; padding: 6px 12px; border-radius: 4px; color: #ee4d2d; box-shadow: 0 10px 30px rgba(238, 77, 45, 0.4); }
  @keyframes stu-fly { 0% { transform: translate(-50%, 0) scale(1.5); opacity: 0; } 10% { opacity: 1; } 100% { transform: translate(-50%, -400px) scale(0.2); opacity: 0; } }
</style>
