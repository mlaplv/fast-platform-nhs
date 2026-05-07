<script lang="ts">
  import { 
    Facebook, Copy, Heart, Zap 
  } from 'lucide-svelte';
  import type { Product } from '$lib/types';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';

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
    shareTarget > 0 ? Math.min((shareCount / shareTarget) * 100, 100) : 0
  );

  const displayRewardLabel = $derived(
    viralSuite?.share_reward_label || product.metadata.share_reward_label || 
    (viralSuite?.primary_campaign === 'VOUCHER_UNLOCK' ? 'Chiến dịch lan tỏa nhận Voucher 50K' : 'Đạt mốc để mở khóa quà tặng')
  );

  let localLikeCount = $state(likeCount);
  let isLiked = $state(false);

  function handleLike(e: MouseEvent) {
    e.preventDefault();
    isLiked = !isLiked;
    if (isLiked) {
      localLikeCount++;
      createHeartConfetti(e.clientX, e.clientY);
    } else {
      localLikeCount = Math.max(0, localLikeCount - 1);
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
      <div class="vsb-reward-panel">
        <div class="vsb-reward-header">
          <Zap size={12} class="text-amber-500 fill-current" />
          <span class="vsb-reward-text">{displayRewardLabel}</span>
        </div>
        <div class="vsb-progress-container">
          <div class="vsb-progress-track">
            <div class="vsb-progress-bar" style="width: {shareProgress}%">
              <div class="vsb-progress-glow"></div>
            </div>
          </div>
          <div class="vsb-progress-meta">
            <span class="vsb-progress-label">TIẾN TRÌNH LAN TỎA</span>
            <span class="vsb-progress-val">{Math.round(shareProgress)}%</span>
          </div>
        </div>
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
    background: linear-gradient(145deg, #ffffff, #f8fafc); border: 1px solid #e2e8f0; 
    border-radius: 12px; padding: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.03);
  }
  .vsb-reward-header { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }
  .vsb-reward-text { font-size: 11px; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 0.02em; }
  
  .vsb-progress-track { height: 6px; background: #f1f5f9; border-radius: 10px; overflow: hidden; margin-bottom: 6px; }
  .vsb-progress-bar { height: 100%; background: linear-gradient(90deg, #f59e0b, #ef4444); position: relative; border-radius: 10px; transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1); }
  .vsb-progress-glow {
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    animation: vsb-shimmer 2s infinite linear;
  }
  @keyframes vsb-shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(200%); } }

  .vsb-progress-meta { display: flex; justify-content: space-between; align-items: center; }
  .vsb-progress-label { font-size: 9px; font-weight: 800; color: #94a3b8; letter-spacing: 0.05em; }
  .vsb-progress-val { font-size: 10px; font-weight: 900; color: #ef4444; }

  :global(.vsb-heart-burst) { position: fixed; pointer-events: none; z-index: 10000; transform: translate(-50%, -50%); }
  :global(.vsb-heart-particle) { position: absolute; font-size: 14px; animation: heart-fly 0.8s ease-out forwards; opacity: 0; }
  @keyframes heart-fly {
    0% { transform: translate(0,0) scale(0.5); opacity: 1; }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 60px), calc(sin(calc(var(--i) * 45deg)) * 60px)) scale(1.2); opacity: 0; }
  }
</style>
