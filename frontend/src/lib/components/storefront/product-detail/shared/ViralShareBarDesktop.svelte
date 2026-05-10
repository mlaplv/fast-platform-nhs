<script lang="ts">
  import Instagram from "@lucide/svelte/icons/instagram";
  import Send from "@lucide/svelte/icons/send";
  import Twitter from "@lucide/svelte/icons/twitter";
  import Facebook from "@lucide/svelte/icons/facebook";
  import Copy from "@lucide/svelte/icons/copy";
  import Heart from "@lucide/svelte/icons/heart";
  import Zap from "@lucide/svelte/icons/zap";
  import type { Product } from '$lib/types';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';

  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';

  interface Props {
    product: Product;
    onShareComplete?: () => void;
    likeCount?: number;
    hideLikes?: boolean;
    dark?: boolean;
  }

  let { 
    product, 
    onShareComplete, 
    likeCount = 0, 
    hideLikes = false,
    dark = false
  }: Props = $props();

  const viralSuite = $derived(product.metadata?.viral_suite ?? null);
  
  const shareCount = $derived(
    viralSuite?.share_count ?? (typeof product.metadata.share_count === 'number' ? product.metadata.share_count : 0)
  );

  const shareTarget = $derived(
    viralSuite?.share_target ?? (typeof product.metadata.share_target === 'number' ? product.metadata.share_target : 0)
  );

  const shareProgress = $derived(
    shareTarget > 0 ? Math.max(80, Math.min((shareCount / shareTarget) * 100, 100)) : 80
  );
  
  const promoConfig = $derived(
    viralSuite?.share_promotion ?? 
    product.metadata?.share_promotion ?? 
    null
  );

  let campaignData = $state<any>(null);
  let isCampaignLoaded = $state(false);

  $effect(() => {
    const vId = viralSuite?.share_promotion?.voucher_id;
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
    product.metadata?.share_reward_label || 
    promoConfig?.voucher_label ||
    'ƯU ĐÃI LAN TỎA'
  );

  const activationMsg = $derived(campaignData?.cta_text || promoConfig?.cta_text || 'Chia sẻ để mở khóa ưu đãi');
  const campaignDesc = $derived(campaignData?.share_text || 'Cùng cộng đồng lan tỏa để nhận mã giảm giá đặc biệt!');
  const voucherCode = $derived(shareProgress >= 100 ? (campaignData?.voucher_id || promoConfig?.voucher_id) : null);

  // Elite V2.2: Centralized Favorite Management
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const localLikeCount = $derived(likeCount + (isLiked ? 1 : 0));

  function handleLike(e: MouseEvent) {
    e.preventDefault();
    if (!product?.id) return;
    
    const wasLiked = isLiked;
    wishlistStore.toggle(product.id);
    
    if (!wasLiked) {
      createHeartConfetti(e.clientX, e.clientY);
    }
  }

  async function share(platform: string) {
    await shareToPlatform(platform, window.location.href, product.name, onShareComplete);
  }

  async function copyLink() {
    await copyViralLink(window.location.href);
    onShareComplete?.();
  }
</script>

<div class="vsb-desktop-root" class:vsb-dark={dark}>
  <div class="vsb-container">
    <div class="vsb-actions">
      <div class="vsb-social-group">
        <button onclick={() => share('facebook')} class="vsb-social-btn fb" aria-label="Share on Facebook">
          <Facebook size={14} fill="currentColor" />
        </button>
        <button onclick={() => share('zalo')} class="vsb-social-btn zalo" aria-label="Share on Zalo">
          <span class="text-[10px] font-black italic">Zalo</span>
        </button>
        <button onclick={() => share('x')} class="vsb-social-btn x" aria-label="Share on X">
          <Twitter size={14} fill="currentColor" />
        </button>
        <button onclick={() => share('instagram')} class="vsb-social-btn instagram" aria-label="Share on Instagram">
          <Instagram size={14} />
        </button>
        <button onclick={() => share('telegram')} class="vsb-social-btn telegram" aria-label="Share on Telegram">
          <Send size={14} />
        </button>
        <button onclick={copyLink} class="vsb-social-btn copy" aria-label="Copy link">
          <Copy size={14} />
        </button>
      </div>

      {#if !hideLikes}
        <button onclick={handleLike} class="vsb-like-pill" class:liked={isLiked}>
          <div class="vsb-heart-icon" class:pulse={isLiked}>
            <Heart size={18} fill={isLiked ? '#e11d48' : 'none'} color={isLiked ? '#e11d48' : '#64748b'} />
          </div>
          <span class="vsb-like-count">{formatViralCount(localLikeCount)}</span>
        </button>
      {/if}
    </div>

    {#if shareTarget > 0}
      <div class="vsb-reward-panel" class:achieved={shareProgress >= 100}>
        {#if shareProgress < 100}
          <div class="vsb-progress-section">
            <div class="vsb-meta-msg">
              <div class="vsb-act-badge"><Zap size={10} fill="currentColor" /> ACTIVE</div>
              <span class="vsb-act-t">{activationMsg}</span>
            </div>
            
            <div class="vsb-progress-container">
              <div class="vsb-progress-info">
                <span class="vsb-reward-text">Cùng cộng đồng lan tỏa để nhận mã giảm giá đặc biệt!</span>
                <span class="vsb-progress-val">{Math.round(shareProgress)}%</span>
              </div>
              <div class="vsb-progress-track">
                <div class="vsb-progress-bar" style="width: {shareProgress}%">
                  <div class="vsb-liquid-glow"></div>
                </div>
              </div>
            </div>
          </div>
        {:else}
          <div class="vsb-reveal-panel">
            <div class="vsb-reveal-header">
              <div class="vsb-confetti-icon">🎊</div>
              <div class="vsb-reveal-title">MỤC TIÊU ĐÃ ĐẠT!</div>
            </div>
            <div class="vsb-code-card">
              <div class="vsb-code-val">{voucherCode}</div>
              <button class="vsb-copy-cta" onclick={() => {
                if (voucherCode) {
                  navigator.clipboard.writeText(voucherCode);
                  onShareComplete?.();
                }
              }}>
                <Copy size={12} /> SAO CHÉP
              </button>
            </div>
            <div class="vsb-reveal-note">Mọi khách hàng đều có thể áp dụng mã này ngay bây giờ!</div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .vsb-desktop-root { width: 100%; font-family: 'Inter', sans-serif; }
  .vsb-container { display: flex; flex-direction: column; gap: 12px; }
  .vsb-actions { display: flex; align-items: center; justify-content: space-between; }
  
  .vsb-social-group { display: flex; align-items: center; gap: 8px; }
  .vsb-social-btn {
    width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    border: 1px solid #eee; background: #fff; cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
  }
  .vsb-social-btn:hover { transform: translateY(-2px); border-color: #ddd; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
  .vsb-social-btn.fb { color: #1877f2; }
  .vsb-social-btn.zalo { color: #0068ff; }
  .vsb-social-btn.x { color: #000; }
  .vsb-social-btn.instagram { color: #e4405f; }
  .vsb-social-btn.telegram { color: #229ed9; }
  .vsb-social-btn.copy { color: #64748b; }

  .vsb-like-pill {
    display: flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #fee2e2;
    padding: 6px 14px; border-radius: 100px; cursor: pointer; transition: all 0.3s;
    box-shadow: 0 2px 8px rgba(244, 63, 94, 0.05);
  }
  .vsb-like-pill.liked { background: #fff1f2; border-color: #fecaca; }
  .vsb-like-pill:hover { transform: scale(1.02); border-color: #fca5a5; }
  
  .vsb-heart-icon.pulse { animation: vsb-heartbeat 1.5s infinite; }
  @keyframes vsb-heartbeat {
    0% { transform: scale(1); }
    14% { transform: scale(1.3); }
    28% { transform: scale(1); }
    42% { transform: scale(1.3); }
    70% { transform: scale(1); }
  }

  .vsb-like-count { font-size: 14px; font-weight: 800; color: #1e293b; }

  .vsb-reward-panel { 
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 16px; padding: 14px;
    transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .vsb-reward-panel.achieved {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.05), rgba(245, 158, 11, 0.05));
    border-color: rgba(236, 72, 153, 0.2);
    box-shadow: 0 10px 30px rgba(236, 72, 153, 0.1);
  }
  
  .vsb-meta-msg { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
  .vsb-act-badge { background: #ef4444; color: #fff; font-size: 8px; font-weight: 900; padding: 2px 6px; border-radius: 4px; display: flex; align-items: center; gap: 4px; letter-spacing: 0.05em; }
  .vsb-act-t { font-size: 11px; font-weight: 700; color: #1e293b; }
  .vsb-meta-desc { font-size: 9px; color: #64748b; line-height: 1.4; margin-top: 10px; font-weight: 500; }

  .vsb-progress-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
  .vsb-reward-text { font-size: 11px; font-weight: 500; color: #475569; font-style: italic; }
  .vsb-progress-val { font-size: 12px; font-weight: 1000; color: #ef4444; font-family: 'JetBrains Mono', monospace; }

  .vsb-progress-track { 
    height: 6px; 
    background: rgba(0, 0, 0, 0.03); 
    border-radius: 100px; 
    overflow: hidden; 
    position: relative;
    border: 1px solid rgba(0, 0, 0, 0.02);
  }
  .vsb-progress-bar { 
    height: 100%; 
    background: linear-gradient(90deg, #f59e0b, #ec4899); 
    position: relative; 
    border-radius: 100px; 
    transition: width 1.5s cubic-bezier(0.34, 1.56, 0.64, 1); 
  }
  .vsb-liquid-glow {
    position: absolute; inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent);
    animation: vsb-liquid-move 1.5s infinite linear;
  }
  @keyframes vsb-liquid-move { 0% { transform: translateX(-100%); } 100% { transform: translateX(150%); } }

  /* REVEAL PANEL STYLES */
  .vsb-reveal-panel { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 10px; padding: 4px 0; }
  .vsb-reveal-header { display: flex; align-items: center; gap: 8px; }
  .vsb-reveal-title { font-size: 11px; font-weight: 900; color: #ec4899; tracking-widest: 0.1em; }
  .vsb-code-card { 
    width: 100%; display: flex; align-items: center; justify-content: space-between; 
    background: #000; border-radius: 12px; padding: 6px 6px 6px 16px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  }
  .vsb-code-val { font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 900; color: #fff; letter-spacing: 0.1em; }
  .vsb-copy-cta { 
    background: #fff; color: #000; border: none; padding: 8px 16px; border-radius: 8px;
    font-size: 10px; font-weight: 900; cursor: pointer; display: flex; align-items: center; gap: 6px;
    transition: all 0.2s;
  }
  .vsb-copy-cta:hover { background: #fdf2f8; transform: scale(1.05); }
  .vsb-reveal-note { font-size: 9px; font-weight: 600; color: #64748b; }

  :global(.vsb-heart-burst) { position: fixed; pointer-events: none; z-index: 10000; transform: translate(-50%, -50%); }
  :global(.vsb-heart-particle) { position: absolute; font-size: 14px; animation: heart-fly 0.8s ease-out forwards; opacity: 0; }
  @keyframes heart-fly {
    0% { transform: translate(0,0) scale(0.5); opacity: 1; }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 60px), calc(sin(calc(var(--i) * 45deg)) * 60px)) scale(1.2); opacity: 0; }
  }
</style>
