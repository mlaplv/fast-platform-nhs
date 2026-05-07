<script lang="ts">
  import type { Product } from '$lib/types';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';

  interface Props {
    product: Product;
    /** 'desktop' = full bar with labels, 'mobile' = compact inline */
    variant?: 'desktop' | 'mobile';
    onShareComplete?: () => void;
    likeCount?: number;
    hideLikes?: boolean;
  }

  let { product, variant = 'desktop', onShareComplete, likeCount = 0, hideLikes = false }: Props = $props();
  const clientUi = getClientUi();

  // --- Elite V2.2: Unified Viral Suite ---
  const viralSuite = $derived(product.metadata?.viral_suite ?? null);

  const shareCount = $derived(
    viralSuite?.share_count ?? (typeof product.metadata?.share_count === 'number' ? product.metadata.share_count : 0)
  );

  const shareTarget = $derived(
    viralSuite?.share_target ?? (typeof product.metadata?.share_target === 'number' ? product.metadata.share_target : 0)
  );

  const shareProgress = $derived(
    shareTarget > 0 ? Math.min((shareCount / shareTarget) * 100, 100) : 0
  );

  const shareRewardLabel = $derived(
    viralSuite?.share_reward_label || product.metadata?.share_reward_label || ''
  );

  const showProgressBar = $derived(shareTarget > 0);
  
  const displayRewardLabel = $derived(
    shareRewardLabel || (viralSuite?.primary_campaign === 'VOUCHER_UNLOCK' ? 'Chiến dịch lan tỏa nhận Voucher 50K' : 'Đạt mốc để mở khóa quà tặng')
  );

  const showLikes = $derived(!hideLikes);

  // --- Animation state ---
  let justShared = $state(false);

  function formatCount(count: number): string {
    if (count >= 1000) {
      return (count / 1000).toFixed(1).replace('.0', '') + 'k';
    }
    return count.toString();
  }

  // --- Elite V2.2: Interaction Logic ---
  let localLikeCount = $state(likeCount);
  let isLiked = $state(false);

  function handleLike(e: MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    
    isLiked = !isLiked;
    if (isLiked) {
      localLikeCount = localLikeCount + 1;
      clientUi.showToast('Đã thêm vào yêu thích', 'success');
      
      // Elite V2.2 Heart Burst Effect
      createHeartConfetti(e);
      triggerShareFeedback(); 
    } else {
      localLikeCount = Math.max(0, localLikeCount - 1);
    }
  }

  function createHeartConfetti(e: MouseEvent) {
    const container = document.createElement('div');
    container.className = 'vsb-heart-burst';
    container.style.left = `${e.clientX}px`;
    container.style.top = `${e.clientY}px`;
    document.body.appendChild(container);

    for (let i = 0; i < 8; i++) {
      const p = document.createElement('div');
      p.className = 'vsb-heart-particle';
      p.style.setProperty('--i', i.toString());
      p.innerHTML = '❤️';
      container.appendChild(p);
    }
    setTimeout(() => container.remove(), 1000);
  }

  async function share(platform: string) {
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
      case 'telegram':
        shareUrl = `https://t.me/share/url?url=${url}&text=${text}`;
        break;
      case 'whatsapp':
        shareUrl = `https://api.whatsapp.com/send?text=${text}%20${url}`;
        break;
      case 'linkedin':
        shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${url}`;
        break;
      case 'tiktok':
        await copyLink();
        window.open('https://www.tiktok.com/', '_blank');
        return;
    }
    if (shareUrl) {
      window.open(shareUrl, '_blank', 'width=600,height=400');
      triggerShareFeedback();
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

  // --- Mobile Smart Scroll Logic (3 Stages) ---
  let scrollY = $state(0);
  let isFull = $derived(scrollY < 100);
  let isCollapsed = $derived(scrollY >= 100 && scrollY < 400);
  let isHidden = $derived(scrollY >= 400);

  function handleScroll() {
    if (typeof window === 'undefined') return;
    scrollY = window.scrollY;
  }

  const isDesktop = $derived(variant === 'desktop');
  
  // --- Mobile Expandable Logic ---
  let mExpanded = $state(false);
  function toggleMExpand() { mExpanded = !mExpanded; }
</script>

<svelte:window onscroll={handleScroll} />

{#if isDesktop}
  <div class="vsb-desktop">
    <div class="vsb-section">
      <div class="vsb-main-interaction">
         <div class="vsb-buttons">
            <button onclick={() => share('facebook')} class="vsb-btn vsb-fb" title="Facebook">
              <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
            </button>
            <button onclick={() => share('zalo')} class="vsb-btn vsb-zalo" title="Zalo">
               <span class="text-[10px] font-black italic">Zalo</span>
            </button>
            <button onclick={() => share('tiktok')} class="vsb-btn vsb-tiktok" title="TikTok">
               <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 fill-current"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.03 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.9-.32-1.98-.23-2.81.33-.85.51-1.44 1.43-1.58 2.41-.14.99.11 2.07.71 2.86.69.9 1.74 1.49 2.87 1.62 1.14.16 2.37-.14 3.23-.92.83-.71 1.34-1.74 1.38-2.83.05-4.1.01-8.2.02-12.3z"/></svg>
            </button>
            <button onclick={copyLink} class="vsb-tool-btn" title="Sao chép link">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
            </button>

            {#if showLikes}
               <button onclick={handleLike} class="vsb-like-pill group {isLiked ? 'vsb-liked' : ''}">
                  <div class="vsb-heart-wrap">
                     <svg class="w-5 h-5 {isLiked ? 'text-rose-600 fill-current' : 'text-rose-500'} vsb-heart-beat" viewBox="0 0 24 24">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                     </svg>
                  </div>
                  <span class="vsb-like-number">{formatCount(localLikeCount)}</span>
               </button>
            {/if}
         </div>
      </div>

      <div class="vsb-meta-row">
         <div class="vsb-stat-item {justShared ? 'vsb-pop' : ''}">
            <div class="vsb-stat-icon-wrap bg-amber-50">
               <svg class="w-3.5 h-3.5 text-amber-500 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
            </div>
            <span class="vsb-stat-value">{formatCount(shareCount)}</span>
            <span class="vsb-stat-label italic">Lượt chia sẻ</span>
         </div>
         
         {#if showProgressBar}
            <div class="vsb-progress-container">
               <div class="vsb-progress-bg">
                  <div class="vsb-progress-fill shimmer-effect" style="width: {shareProgress}%"></div>
               </div>
               <div class="vsb-progress-info">
                  <span class="vsb-progress-text">{displayRewardLabel}</span>
                  <span class="vsb-progress-percent">{Math.round(shareProgress)}%</span>
               </div>
            </div>
         {/if}
      </div>
    </div>
  </div>

{:else}
  <!-- ═══ MOBILE: TikTok Premium (Triple-State Logic) ═══ -->
  <div class="vsb-m-tiktok-wrap {isCollapsed ? 'vsb-m-scrolled' : ''} {isHidden ? 'vsb-m-hidden' : ''}">
     <div class="vsb-m-vertical-actions">
        <!-- HEART: TikTok Premium Identity -->
        <button onclick={handleLike} class="vsb-m-v-btn vsb-m-v-like-tiktok {isLiked ? 'vsb-liked-v' : ''}">
           <div class="vsb-m-v-glass-icon">
              <svg class="w-5 h-5 {isLiked ? 'text-rose-600 fill-current' : 'text-white drop-shadow-lg'} vsb-heart-beat" fill={isLiked ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
           </div>
           <span class="vsb-m-v-num-tiktok">{formatCount(localLikeCount)}</span>
        </button>

        <div class="vsb-m-share-stack">
           <!-- Circular Core Share Buttons -->
           <button onclick={() => share('zalo')} class="vsb-m-v-btn" aria-label="Zalo">
              <div class="vsb-m-v-icon-circle bg-[#0068ff] border border-white/20 shadow-lg"><span class="text-[7px] font-black italic text-white">Zalo</span></div>
           </button>
           <button onclick={() => share('tiktok')} class="vsb-m-v-btn" aria-label="TikTok">
              <div class="vsb-m-v-icon-circle bg-black border border-white/30 shadow-lg"><svg viewBox="0 0 24 24" class="w-3 h-3 fill-current text-white"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.03 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.9-.32-1.98-.23-2.81.33-.85.51-1.44 1.43-1.58 2.41-.14.99.11 2.07.71 2.86.69.9 1.74 1.49 2.87 1.62 1.14.16 2.37-.14 3.23-.92.83-.71 1.34-1.74 1.38-2.83.05-4.1.01-8.2.02-12.3z"/></svg></div>
           </button>
           <button onclick={() => share('facebook')} class="vsb-m-v-btn" aria-label="FB">
              <div class="vsb-m-v-icon-circle bg-[#1877f2] border border-white/20 shadow-lg"><svg viewBox="0 0 24 24" class="w-3 h-3 fill-current text-white"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg></div>
           </button>
           <button onclick={copyLink} class="vsb-m-v-btn" aria-label="Copy">
              <div class="vsb-m-v-icon-circle bg-white/90 backdrop-blur-sm border border-white/30 text-gray-700 shadow-lg"><svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg></div>
           </button>

           {#if mExpanded}
              <button onclick={() => share('twitter')} class="vsb-m-v-btn" aria-label="X">
                 <div class="vsb-m-v-icon-circle bg-black border border-white/20 shadow-lg text-white"><span class="text-[9px] font-black">𝕏</span></div>
              </button>
              <button onclick={() => share('pinterest')} class="vsb-m-v-btn" aria-label="Pin">
                 <div class="vsb-m-v-icon-circle bg-[#e60023] border border-white/20 shadow-lg"><svg viewBox="0 0 24 24" class="w-3 h-3 fill-current text-white"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.965 1.406-5.965s-.359-.718-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.654 2.568-.994 3.993-.283 1.194.599 2.169 1.775 2.169 2.128 0 3.765-2.244 3.765-5.482 0-2.868-2.059-4.876-5.01-4.876-3.412 0-5.413 2.561-5.413 5.202 0 1.03.396 2.133.89 2.735.098.119.112.224.083.345l-.333 1.36c-.053.22-.174.267-.402.16-1.498-.696-2.435-2.885-2.435-4.643 0-3.782 2.748-7.252 7.925-7.252 4.161 0 7.397 2.964 7.397 6.931 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"/></svg></div>
              </button>
              <button onclick={() => share('telegram')} class="vsb-m-v-btn" aria-label="Tele">
                 <div class="vsb-m-v-icon-circle bg-[#0088cc] border border-white/20 shadow-lg"><svg viewBox="0 0 24 24" class="w-3 h-3 fill-current text-white"><path d="M11.944 0C5.346 0 0 5.346 0 11.944c0 6.598 5.346 11.944 11.944 11.944 6.598 0 11.944-5.346 11.944-11.944C23.888 5.346 18.542 0 11.944 0zm5.834 8.232l-1.98 9.336c-.15.67-.546.834-1.106.522l-3.02-2.226-1.457 1.4c-.16.16-.296.296-.606.296l.216-3.078 5.604-5.06c.244-.216-.054-.336-.376-.12l-6.93 4.364-2.984-.932c-.648-.204-.66-.648.136-.958l11.66-4.492c.54-.196 1.012.13.843.898z"/></svg></div>
              </button>
           {/if}

           <button onclick={toggleMExpand} class="vsb-m-v-btn vsb-m-more" aria-label="More">
              <div class="vsb-m-v-icon-circle bg-white/80 backdrop-blur-md text-gray-800 border border-white/40 shadow-lg">
                 <span class="vsb-m-dots">•••</span>
              </div>
           </button>
        </div>
     </div>
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
  /* ═══ DESKTOP RE-ARCH ═══ */
  .vsb-desktop {
    width: 100%;
    border-top: 1px solid #f3f4f6;
    padding-top: 12px;
    margin-top: 4px;
  }

  .vsb-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .vsb-buttons {
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .vsb-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }

  .vsb-btn:hover {
    transform: translateY(-2px) scale(1.08);
    box-shadow: 0 6px 15px rgba(0,0,0,0.12);
  }

  .vsb-fb { background: #1877f2; }
  .vsb-zalo { background: #0068ff; }
  .vsb-tiktok { background: #000; box-shadow: 1px 0 0 #fe2c55, -1px 0 0 #25f4ee; }

  .vsb-tool-btn {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: #f9fafb;
    border: 1px solid #f3f4f6;
    color: #6b7280;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
    margin-left: 2px;
  }

  .vsb-tool-btn:hover { background: #fff; border-color: #ee4d2d; color: #ee4d2d; }

  /* ══ META & STATS ══ */
  .vsb-meta-row {
    display: flex;
    align-items: center;
    gap: 20px;
  }

  .vsb-stat-item {
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s;
  }

  .vsb-stat-icon-wrap {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .vsb-stat-value { font-size: 14px; font-weight: 900; color: #111; }
  .vsb-stat-label { font-size: 10px; font-weight: 700; color: #9ca3af; margin-top: 1px; }

  .vsb-pop { transform: scale(1.1); }

  /* ══ LUXURY PROGRESS ══ */
  .vsb-progress-container {
    flex: 1;
    max-width: 240px;
  }

  .vsb-progress-bg {
    width: 100%;
    height: 5px;
    background: #f3f4f6;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 6px;
  }

  .vsb-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #f59e0b, #ee4d2d);
    border-radius: 10px;
    transition: width 1s cubic-bezier(0.19, 1, 0.22, 1);
  }

  .shimmer-effect {
    position: relative;
    overflow: hidden;
  }

  .shimmer-effect::after {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 50%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    animation: shimmer 2s infinite;
  }

  @keyframes shimmer { 100% { left: 150%; } }

  .vsb-progress-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1px;
  }

  .vsb-progress-text { font-size: 10px; font-weight: 800; color: #6b7280; letter-spacing: 0.05em; }
  .vsb-progress-percent { font-size: 10px; font-weight: 900; color: #ee4d2d; }

  /* ══ INTERACTION ══ */

  .vsb-like-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #fff;
    border: 1px solid #fee2e2;
    padding: 4px 12px;
    border-radius: 50px;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 2px 10px rgba(244, 63, 94, 0.03);
  }

  .vsb-like-pill:hover {
    background: #fff1f2;
    border-color: #fecaca;
    transform: translateY(-1.5px);
    box-shadow: 0 4px 12px rgba(244, 63, 94, 0.1);
  }

  .vsb-heart-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .vsb-like-number {
    font-size: 15px;
    font-weight: 800;
    color: #111;
    font-family: 'Inter', sans-serif;
  }

  .vsb-liked {
    background: #fff1f2 !important;
    border-color: #fecaca !important;
    transform: scale(1.05);
  }

  .vsb-heart-beat { animation: heartbeat 1.8s infinite cubic-bezier(0.4, 0, 0.6, 1); }
  @keyframes heartbeat {
    0%, 100% { transform: scale(1); filter: brightness(1); }
    10%, 30% { transform: scale(1.2); filter: brightness(1.2); }
    20% { transform: scale(1.35); filter: brightness(1.3); }
  }

  /* ═══ MOBILE TIKTOK STYLE (DYNAMIC) ═══ */
  .vsb-m-tiktok-wrap {
    position: relative;
    width: 100%;
    margin-top: 10px;
  }

  .vsb-m-vertical-actions {
    position: fixed;
    right: 8px;
    top: 65px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
    z-index: 1000;
    transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    padding-top: 10px;
  }

  /* Hiệu ứng thu gọn vòng cung (Scroll 1) */
  .vsb-m-scrolled .vsb-m-vertical-actions {
    transform: translateX(22px) scale(0.9);
    filter: blur(0.5px);
    opacity: 0.7;
  }

  /* Hiệu ứng ẨN hoàn toàn (Scroll 2) */
  .vsb-m-hidden .vsb-m-vertical-actions {
    transform: translateX(80px); /* Đẩy hẳn ra ngoài màn hình */
    opacity: 0;
    pointer-events: none;
  }

  .vsb-m-scrolled .vsb-m-v-btn {
    margin-bottom: -22px; 
    transform: rotate(15deg);
  }

  /* Staggered Delay cho hiệu ứng vòng cung mượt mà */
  .vsb-m-v-btn { transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1); }
  .vsb-m-v-btn:nth-child(2) { transition-delay: 0.05s; }
  .vsb-m-v-btn:nth-child(3) { transition-delay: 0.1s; }
  .vsb-m-v-btn:nth-child(4) { transition-delay: 0.15s; }
  .vsb-m-v-btn:nth-child(5) { transition-delay: 0.2s; }

  .vsb-m-share-stack {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .vsb-m-v-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
  }

  .vsb-m-v-like-tiktok {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    background: none;
    border: none;
    padding: 0;
  }

  .vsb-m-v-glass-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.05);
    backdrop-filter: blur(4px);
    transition: all 0.3s;
  }

  .vsb-m-v-icon-circle {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    box-shadow: 0 3px 10px rgba(0,0,0,0.15);
  }

  .vsb-m-v-icon-circle:active { transform: scale(0.9); }

  .vsb-liked-v { transform: scale(1.15); filter: drop-shadow(0 0 8px rgba(244,63,92,0.6)); }

  .vsb-m-v-num-tiktok { 
    font-size: 10px; 
    font-weight: 900; 
    color: white; 
    text-shadow: 0 1px 3px rgba(0,0,0,0.8), 0 0 6px rgba(0,0,0,0.4);
    margin-top: -1px;
  }

  .vsb-m-dots {
    font-size: 13px;
    font-weight: 900;
    display: flex;
    align-items: center;
    justify-content: center;
    letter-spacing: -1px;
    line-height: 1;
  }

  /* ═══ CONFETTI ═══ */
  .vsb-confetti { position: fixed; top: 50%; left: 50%; pointer-events: none; z-index: 1000; }
  .vsb-particle {
    position: absolute; width: 8px; height: 8px; border-radius: 50%;
    background: hsl(var(--hue), 80%, 60%);
    animation: confetti-burst 0.8s ease-out forwards;
  }
  @keyframes confetti-burst {
    0% { transform: translate(0, 0) scale(1); opacity: 1; }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 100px), calc(sin(calc(var(--i) * 45deg)) * 100px)) scale(0); opacity: 0; }
  }
  /* ═══ HEART BURST ═══ */
  :global(.vsb-heart-burst) {
    position: fixed;
    pointer-events: none;
    z-index: 10000;
    transform: translate(-50%, -50%);
  }
  :global(.vsb-heart-particle) {
    position: absolute;
    font-size: 14px;
    animation: heart-fly 0.8s ease-out forwards;
    opacity: 0;
  }
  @keyframes heart-fly {
    0% { transform: translate(0,0) scale(0.5); opacity: 1; }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 60px), calc(sin(calc(var(--i) * 45deg)) * 60px)) scale(1.2); opacity: 0; }
  }
</style>
