<script lang="ts">
    import Heart from "@lucide/svelte/icons/heart";
  import Instagram from "@lucide/svelte/icons/instagram";
  import Send from "@lucide/svelte/icons/send";
  import Twitter from "@lucide/svelte/icons/twitter";
  import Facebook from "@lucide/svelte/icons/facebook";
  import Copy from "@lucide/svelte/icons/copy";
  import Zap from "@lucide/svelte/icons/zap";
  import type { Product } from '$lib/types';
  import { 
    formatViralCount, shareToPlatform, copyViralLink, createHeartConfetti 
  } from '$lib/utils/commerce/viral';

  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';

  interface Props {
    product: Product;
    variant?: 'mobile' | 'funnel';
    likeCount?: number;
    hideLikes?: boolean;
    dark?: boolean;
    onShareComplete?: () => void;
  }

  let { 
    product, 
    variant = 'mobile', 
    likeCount = 0, 
    hideLikes = false,
    dark = false,
    onShareComplete
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

  const activationMsg = $derived(campaignData?.cta_text || 'Cùng nhau chia sẻ!');
  const displayRewardLabel = $derived(campaignData?.voucher_label || 'ƯU ĐÃI LAN TỎA');
  const voucherCode = $derived(shareProgress >= 100 ? (campaignData?.voucher_id || 'OPEN') : null);

  // Elite V2.2: Centralized Favorite Management
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const localLikeCount = $derived(likeCount + (isLiked ? 1 : 0));

  let scrollY = $state(0);
  
  const isCollapsed = $derived(scrollY >= 100 && scrollY < 400);
  const isHidden = $derived(scrollY >= 400);

  function handleScroll() {
    if (typeof window !== 'undefined') scrollY = window.scrollY;
  }

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

<svelte:window onscroll={handleScroll} />

<div class="vsb-mobile-root" class:funnel={variant === 'funnel'} class:vsb-dark={dark}>
  {#if variant === 'funnel'}
    <div class="vsb-funnel">
       <div class="vsb-funnel-main">
          <button onclick={handleLike} class="vsb-funnel-pill" class:liked={isLiked}>
             <Heart size={20} class={isLiked ? 'text-rose-500 fill-current' : 'text-white/60'} />
             <span class="vsb-funnel-count">{formatViralCount(localLikeCount)}</span>
          </button>
          <button onclick={() => share('facebook')} class="vsb-funnel-icon fb" aria-label="Share on Facebook"><Facebook size={18} fill="currentColor" /></button>
          <button onclick={() => share('zalo')} class="vsb-funnel-icon zalo" aria-label="Share on Zalo"><span class="text-[9px] font-black italic">Zalo</span></button>
          <button onclick={() => share('x')} class="vsb-funnel-icon x" aria-label="Share on X"><Twitter size={16} fill="currentColor" /></button>
          <button onclick={() => share('instagram')} class="vsb-funnel-icon ins" aria-label="Share on Instagram"><Instagram size={16} /></button>
          <button onclick={() => share('telegram')} class="vsb-funnel-icon tele" aria-label="Share on Telegram"><Send size={16} /></button>
          <button onclick={copyLink} class="vsb-funnel-icon copy" aria-label="Copy link"><Copy size={16} /></button>
       </div>

       {#if shareTarget > 0}
         <div class="vsb-f-reward-box" class:achieved={shareProgress >= 100}>
            {#if shareProgress < 100}
               <div class="vsb-f-progress-wrap">
                  <div class="vsb-f-info">
                     <span class="vsb-f-label">Cùng cộng đồng lan tỏa để nhận mã giảm giá đặc biệt!</span>
                     <span class="vsb-f-val">{Math.round(shareProgress)}%</span>
                  </div>
                  <div class="vsb-f-track">
                     <div class="vsb-f-bar" style="width: {shareProgress}%">
                        <div class="vsb-f-liquid"></div>
                     </div>
                  </div>
               </div>
            {:else}
               <div class="vsb-f-reveal">
                  <div class="vsb-f-reveal-t">🎊 MỤC TIÊU ĐÃ ĐẠT!</div>
                  <div class="vsb-f-code-row">
                     <span class="vsb-f-code">{voucherCode}</span>
                     <button class="vsb-f-copy" onclick={() => {
                        if (voucherCode) navigator.clipboard.writeText(voucherCode);
                        onShareComplete?.();
                     }}>COPY</button>
                  </div>
               </div>
            {/if}
         </div>
       {/if}
    </div>
  {:else}
    <div class="vsb-tiktok-wrap" class:scrolled={isCollapsed} class:hidden={isHidden}>
       <div class="vsb-vertical-actions">
          <button class="vsb-v-btn" onclick={handleLike}>
             <div class="vsb-v-icon-circle" class:liked={isLiked}>
                <Heart size={18} fill={isLiked ? 'white' : 'none'} stroke={isLiked ? 'none' : 'white'} />
             </div>
             <span class="vsb-v-count">{formatViralCount(localLikeCount)}</span>
          </button>
          <div class="vsb-share-stack">
             <button class="vsb-v-btn" onclick={() => share('facebook')}>
                <div class="vsb-v-icon-circle fb"><Facebook size={14} fill="white" /></div>
             </button>
             <button class="vsb-v-btn" onclick={() => share('zalo')}>
                <div class="vsb-v-icon-circle zalo"><span class="text-[8px] font-black italic text-white">Zalo</span></div>
             </button>
             <button class="vsb-v-btn" onclick={copyLink}>
                <div class="vsb-v-icon-circle copy"><Copy size={14} color="white" /></div>
             </button>
          </div>
       </div>
    </div>
  {/if}
</div>

<style>
  .vsb-mobile-root { position: relative; width: 100%; }

  /* TikTok Style Vertical Actions */
  .vsb-tiktok-wrap { 
    position: fixed; right: 10px; top: 15vh; z-index: 1000;
    transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  .vsb-tiktok-wrap.scrolled { transform: translateX(20px) scale(0.85); opacity: 0.6; }
  .vsb-tiktok-wrap.hidden { transform: translateX(80px); opacity: 0; pointer-events: none; }

  .vsb-vertical-actions { display: flex; flex-direction: column; align-items: center; gap: 16px; }
  
  .vsb-v-btn { display: flex; flex-direction: column; align-items: center; gap: 4px; background: none; border: none; padding: 0; outline: none; }
  .vsb-v-icon-circle { 
    width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    background: rgba(0,0,0,0.4); backdrop-filter: blur(8px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .vsb-v-icon-circle.liked { background: #ff2d55; transform: scale(1.1); box-shadow: 0 0 15px rgba(255, 45, 85, 0.5); }
  .vsb-v-icon-circle.fb { background: #1877f2; }
  .vsb-v-icon-circle.zalo { background: #0068ff; }
  .vsb-v-icon-circle.copy { background: rgba(255,255,255,0.1); }

  .vsb-v-count { font-size: 10px; font-weight: 900; color: white; text-shadow: 0 1px 4px rgba(0,0,0,0.8); }
  .vsb-share-stack { display: flex; flex-direction: column; gap: 12px; }

  /* Funnel Variant */
  .vsb-funnel { width: 100%; padding: 12px 0; }
  .vsb-funnel-main { display: flex; align-items: center; gap: 8px; }
  .vsb-funnel-pill { 
    display: flex; align-items: center; gap: 8px; padding: 10px 18px; 
    background: rgba(255,255,255,0.08); backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12); border-radius: 100px;
    transition: all 0.3s;
  }
  .vsb-funnel-pill.liked { background: rgba(244,63,94,0.15); border-color: rgba(244,63,94,0.3); }
  .vsb-funnel-count { font-size: 13px; font-weight: 1000; italic: true; color: white; }

  .vsb-funnel-icon { 
    width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    background: rgba(255,255,255,0.08); backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.12); color: white;
    transition: all 0.2s;
  }
  .vsb-funnel-icon:active { transform: scale(0.9); background: rgba(255,255,255,0.2); }

  /* Reward Box Mobile */
  .vsb-f-reward-box { margin-top: 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 10px; transition: all 0.5s; }
  .vsb-f-reward-box.achieved { background: rgba(236, 72, 153, 0.1); border-color: rgba(236, 72, 153, 0.3); }

  .vsb-f-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
  .vsb-f-label { font-size: 10px; font-weight: 500; color: rgba(255,255,255,0.7); font-style: italic; }
  .vsb-f-val { font-size: 10px; font-weight: 900; color: #fb7185; }

  .vsb-f-track { height: 4px; background: rgba(255,255,255,0.05); border-radius: 100px; overflow: hidden; position: relative; }
  .vsb-f-bar { height: 100%; background: linear-gradient(90deg, #f59e0b, #ec4899); border-radius: 100px; position: relative; transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1); }
  .vsb-f-liquid { position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent); animation: vsb-f-liquid-anim 1.5s infinite linear; }
  @keyframes vsb-f-liquid-anim { 0% { transform: translateX(-100%); } 100% { transform: translateX(200%); } }

  .vsb-f-reveal { text-align: center; }
  .vsb-f-reveal-t { font-size: 10px; font-weight: 900; color: #f472b6; margin-bottom: 8px; }
  .vsb-f-code-row { display: flex; align-items: center; justify-content: space-between; background: #000; border-radius: 8px; padding: 4px 4px 4px 12px; }
  .vsb-f-code { font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 900; color: #fff; }
  .vsb-f-copy { background: #fff; color: #000; border: none; padding: 6px 12px; border-radius: 6px; font-size: 9px; font-weight: 900; }

  :global(.vsb-heart-burst) { position: fixed; pointer-events: none; z-index: 10000; transform: translate(-50%, -50%); }
  :global(.vsb-heart-particle) { position: absolute; font-size: 14px; animation: heart-fly 0.8s ease-out forwards; opacity: 0; }
  @keyframes heart-fly {
    0% { transform: translate(0,0) scale(0.5); opacity: 1; }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 60px), calc(sin(calc(var(--i) * 45deg)) * 60px)) scale(1.2); opacity: 0; }
  }
</style>
