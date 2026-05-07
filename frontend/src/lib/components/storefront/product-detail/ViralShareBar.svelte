<script lang="ts">
  import type { Product } from '$lib/types';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  interface Props {
    product: Product;
    /** 'desktop' = full bar with labels, 'mobile' = compact inline */
    variant?: 'desktop' | 'mobile';
    onShareComplete?: () => void;
    likeCount?: number;
  }

  let { product, variant = 'desktop', onShareComplete, likeCount = 0 }: Props = $props();
  const clientUi = getClientUi();

  // --- Share count from DB ---
  const shareCount = $derived(
    typeof product.metadata?.share_count === 'number'
      ? product.metadata.share_count
      : 0
  );

  // --- Share target for gamification progress ---
  const shareTarget = $derived(
    typeof product.metadata?.share_target === 'number'
      ? product.metadata.share_target
      : 0
  );
  const shareProgress = $derived(
    shareTarget > 0 ? Math.min((shareCount / shareTarget) * 100, 100) : 0
  );
  const shareRewardLabel = $derived(
    product.metadata?.share_reward_label || ''
  );

  // --- Animation state ---
  let justShared = $state(false);

  function formatCount(count: number): string {
    if (count >= 1000) {
      return (count / 1000).toFixed(1).replace('.0', '') + 'k';
    }
    return count.toString();
  }

  function share(platform: string) {
    if (typeof window === 'undefined') return;
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(`Xem ngay: ${product.name}`);
    const media = encodeURIComponent(product.images?.[0] || '');

    let shareUrl = '';
    switch (platform) {
      case 'facebook':
        shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
        break;
      case 'zalo':
        shareUrl = `https://sp.zalo.me/plugins/share?url=${url}`;
        break;
      case 'pinterest':
        shareUrl = `https://pinterest.com/pin/create/button/?url=${url}&media=${media}&description=${text}`;
        break;
      case 'twitter':
        shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${text}`;
        break;
    }
    if (shareUrl) {
      window.open(shareUrl, '_blank', 'width=600,height=400');
      triggerShareFeedback();
    }
  }

  async function shareNative() {
    if (typeof navigator === 'undefined') return;
    if (navigator.share) {
      try {
        await navigator.share({
          title: product.name,
          text: `Xem ngay ${product.name}!`,
          url: window.location.href
        });
        triggerShareFeedback();
      } catch (_e) {
        // User cancelled share dialog
      }
    } else {
      await copyLink();
    }
  }

  async function copyLink() {
    if (typeof navigator === 'undefined' || !navigator.clipboard) return;
    await navigator.clipboard.writeText(window.location.href);
    clientUi.showToast('Đã sao chép đường dẫn', 'success');
    triggerShareFeedback();
  }

  function triggerShareFeedback() {
    justShared = true;
    setTimeout(() => { justShared = false; }, 1200);
    onShareComplete?.();
  }

  const isDesktop = $derived(variant === 'desktop');
</script>

{#if isDesktop}
  <!-- ═══ DESKTOP: Full Viral Share Bar ═══ -->
  <div class="vsb-desktop">
    <div class="vsb-row">
      <span class="vsb-label">Chia sẻ:</span>
      <div class="vsb-buttons">
        <button onclick={() => share('facebook')} class="vsb-btn vsb-fb" aria-label="Share Facebook" title="Facebook">
          <span class="vsb-btn-letter">f</span>
        </button>
        <button onclick={() => share('zalo')} class="vsb-btn vsb-zalo" aria-label="Share Zalo" title="Zalo">
          <span class="vsb-btn-letter">z</span>
        </button>
        <button onclick={() => share('pinterest')} class="vsb-btn vsb-pin" aria-label="Share Pinterest" title="Pinterest">
          <span class="vsb-btn-letter">p</span>
        </button>
        <button onclick={() => share('twitter')} class="vsb-btn vsb-x" aria-label="Share X" title="X (Twitter)">
          <span class="vsb-btn-letter">𝕏</span>
        </button>
        <button onclick={copyLink} class="vsb-btn vsb-copy" aria-label="Sao chép link" title="Sao chép link">
          <svg class="vsb-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
          </svg>
        </button>
        <button onclick={shareNative} class="vsb-btn vsb-more" aria-label="Chia sẻ thêm" title="Tùy chọn khác">
          <svg class="vsb-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
        </button>
      </div>
    </div>

    {#if shareCount > 0}
      <div class="vsb-count {justShared ? 'vsb-count--pop' : ''}">
        <svg class="vsb-count-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
        </svg>
        <span>{formatCount(shareCount)} lượt chia sẻ</span>
      </div>
    {/if}

    {#if likeCount > 0}
      <div class="vsb-count vsb-count-likes">
        <svg class="vsb-count-icon vsb-icon-heart" viewBox="0 0 24 24" fill="currentColor" stroke="none">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
        <span>{formatCount(likeCount)} người yêu thích</span>
      </div>
    {/if}

    {#if shareTarget > 0 && shareRewardLabel}
      <div class="vsb-progress-wrap">
        <div class="vsb-progress-bar">
          <div class="vsb-progress-fill" style="width: {shareProgress}%"></div>
        </div>
        <span class="vsb-progress-label">
          {#if shareProgress >= 100}
            🎉 Đã đạt mục tiêu!
          {:else}
            📢 {shareRewardLabel}
          {/if}
        </span>
      </div>
    {/if}
  </div>

{:else}
  <!-- ═══ MOBILE: Compact Inline Share ═══ -->
  <div class="vsb-mobile">
    <div class="vsb-m-row">
      <button onclick={() => share('facebook')} class="vsb-m-btn vsb-fb" aria-label="Share Facebook">f</button>
      <button onclick={() => share('zalo')} class="vsb-m-btn vsb-zalo" aria-label="Share Zalo">z</button>
      <button onclick={() => share('pinterest')} class="vsb-m-btn vsb-pin" aria-label="Share Pinterest">p</button>
      <button onclick={() => share('twitter')} class="vsb-m-btn vsb-x" aria-label="Share X">𝕏</button>
      <button onclick={shareNative} class="vsb-m-btn vsb-m-native" aria-label="Chia sẻ">
        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
        </svg>
      </button>
    </div>
    {#if shareCount > 0}
      <span class="vsb-m-count {justShared ? 'vsb-count--pop' : ''}">{formatCount(shareCount)} shares</span>
    {/if}
    {#if likeCount > 0}
      <span class="vsb-m-count vsb-m-count-likes ml-2">
        <svg class="w-2.5 h-2.5 inline mr-0.5 text-pink-500" fill="currentColor" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
        {formatCount(likeCount)}
      </span>
    {/if}
  </div>
{/if}

<!-- ═══ CONFETTI BURST (Micro-animation on share) ═══ -->
{#if justShared}
  <div class="vsb-confetti" aria-hidden="true">
    {#each Array(8) as _, i}
      <span class="vsb-particle" style="--i:{i};--hue:{i * 45}"></span>
    {/each}
  </div>
{/if}

<style>
  /* ═══ DESKTOP ═══ */
  .vsb-desktop {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 0 2px;
  }

  .vsb-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .vsb-label {
    font-size: 14px;
    font-weight: 500;
    color: #374151;
    white-space: nowrap;
  }

  .vsb-buttons {
    display: flex;
    gap: 6px;
    font-weight: 700;
  }

  .vsb-btn {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    cursor: pointer;
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s;
    position: relative;
    overflow: hidden;
  }

  .vsb-btn::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.25) 0%, transparent 50%);
    border-radius: inherit;
    pointer-events: none;
  }

  .vsb-btn:hover {
    transform: translateY(-2px) scale(1.08);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .vsb-btn:active { transform: scale(0.92); }

  .vsb-btn-letter { font-size: 11px; font-weight: 900; position: relative; z-index: 1; }

  .vsb-fb { background: #0384ff; }
  .vsb-zalo { background: #38adff; }
  .vsb-pin { background: #e60023; }
  .vsb-x { background: #000; }
  .vsb-copy { background: #f3f4f6; color: #6b7280; }
  .vsb-copy:hover { background: #e5e7eb; }
  .vsb-more { background: #f3f4f6; color: #6b7280; margin-left: 2px; }
  .vsb-more:hover { background: #e5e7eb; }

  .vsb-icon { width: 13px; height: 13px; position: relative; z-index: 1; }

  .vsb-count {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #9ca3af;
    font-weight: 600;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .vsb-count--pop { transform: scale(1.1); color: #ee4d2d; }

  .vsb-count-icon { width: 14px; height: 14px; opacity: 0.5; }
  .vsb-icon-heart { color: #f43f5e; opacity: 0.8; }
  .vsb-count-likes { color: #6b7280; font-weight: 500; }

  /* ═══ GAMIFICATION PROGRESS ═══ */
  .vsb-progress-wrap {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .vsb-progress-bar {
    width: 100%;
    height: 4px;
    background: #f3f4f6;
    border-radius: 2px;
    overflow: hidden;
  }

  .vsb-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #ee4d2d, #ff6b45);
    border-radius: 2px;
    transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .vsb-progress-label {
    font-size: 11px;
    color: #6b7280;
    font-weight: 600;
  }

  /* ═══ MOBILE ═══ */
  .vsb-mobile {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
  }

  .vsb-m-row {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  .vsb-m-btn {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 11px;
    font-weight: 900;
    cursor: pointer;
    transition: transform 0.15s ease;
    -webkit-tap-highlight-color: transparent;
  }

  .vsb-m-btn:active { transform: scale(0.85); }

  .vsb-m-native {
    background: #f3f4f6;
    color: #6b7280;
  }

  .vsb-m-count {
    font-size: 11px;
    color: #9ca3af;
    font-weight: 700;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .vsb-m-count.vsb-count--pop { transform: scale(1.15); color: #ee4d2d; }

  /* ═══ CONFETTI PARTICLES ═══ */
  .vsb-confetti {
    position: fixed;
    top: 50%;
    left: 50%;
    pointer-events: none;
    z-index: 99999;
  }

  .vsb-particle {
    position: absolute;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: hsl(var(--hue), 80%, 60%);
    animation: confetti-burst 0.8s ease-out forwards;
    animation-delay: calc(var(--i) * 0.04s);
  }

  @keyframes confetti-burst {
    0% {
      transform: translate(0, 0) scale(1);
      opacity: 1;
    }
    100% {
      transform: translate(
        calc(cos(calc(var(--i) * 45deg)) * 60px),
        calc(sin(calc(var(--i) * 45deg)) * 60px - 20px)
      ) scale(0);
      opacity: 0;
    }
  }
</style>
