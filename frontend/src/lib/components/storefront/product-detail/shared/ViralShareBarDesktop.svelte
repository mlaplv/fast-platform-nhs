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

  let campaignData = $state<{ voucher_label?: string; cta_text?: string; share_text?: string; voucher_subtitle?: string; voucher_id?: string } | null>(null);
  let isCampaignLoaded = $state(false);

  $effect(() => {
    const vId = viralSuite?.share_promotion?.voucher_id;
    if (vId && !isCampaignLoaded) {
      isCampaignLoaded = true;
      fetch(`/api/v1/client/viral/campaign/${vId}`)
        .then(res => res.json())
        .then((data: { voucher_label?: string; cta_text?: string; share_text?: string; voucher_subtitle?: string; voucher_id?: string }) => { 
          campaignData = data; 
        })
        .catch(() => {});
    }
  });

  const displayRewardLabel = $derived(
    campaignData?.voucher_label || 
    viralSuite?.share_reward_label || 
    product.metadata?.share_reward_label || 
    promoConfig?.voucher_label ||
    'Ưu đãi lan tỏa'
  );

  const activationMsg = $derived(campaignData?.cta_text || promoConfig?.cta_text || 'Chia sẻ để mở khóa ưu đãi');
  const campaignDesc = $derived(campaignData?.share_text || 'Cùng cộng đồng lan tỏa để nhận mã giảm giá đặc biệt!');
  const voucherCode = $derived(shareProgress >= 100 ? (campaignData?.voucher_id || promoConfig?.voucher_id) : null);

  // Elite V2.2: Centralized Favorite Management
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const baseLikeCount = $derived(Number(viralSuite?.likes_count || product.metadata?.likes || likeCount || 0));
  const localLikeCount = $derived(baseLikeCount + (isLiked ? 1 : 0));

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

<div class="w-full font-sans">
  <div class="flex flex-col gap-4 w-full">
    
    <!-- Social & Like Row -->
    <div class="flex items-center justify-between">
      {#if !hideLikes}
        <button onclick={handleLike} class="flex items-center gap-1.5 group/like hover:scale-105 transition-all">
          <Heart size={18} class="transition-transform group-hover/like:scale-110 {isLiked ? 'fill-rose-500 text-rose-500' : 'text-slate-400'}" />
          <span class="text-xs font-bold {isLiked ? 'text-rose-600' : 'text-slate-500'}">{formatViralCount(localLikeCount)}</span>
        </button>
        <div class="w-[1px] h-4 bg-slate-200 mx-2"></div>
      {/if}
      
      <button onclick={() => share('facebook')} class="text-slate-400 hover:text-[#1877f2] transition-colors hover:scale-110" aria-label="Share Facebook"><Facebook size={18} class="fill-current" /></button>
      <button onclick={() => share('zalo')} class="text-slate-400 hover:text-[#0068ff] transition-colors hover:scale-110 font-black text-xs" aria-label="Share Zalo">Zalo</button>
      <button onclick={() => share('x')} class="text-slate-400 hover:text-black transition-colors hover:scale-110" aria-label="Share X"><Twitter size={18} class="fill-current" /></button>
      <button onclick={() => share('instagram')} class="text-slate-400 hover:text-[#e4405f] transition-colors hover:scale-110" aria-label="Share Instagram"><Instagram size={18} /></button>
      <button onclick={() => share('telegram')} class="text-slate-400 hover:text-[#229ed9] transition-colors hover:scale-110" aria-label="Share Telegram"><Send size={18} /></button>
      <button onclick={copyLink} class="text-slate-400 hover:text-slate-900 transition-colors hover:scale-110" aria-label="Copy Link"><Copy size={18} /></button>
    </div>

    <!-- Progress -->
    {#if shareTarget > 0}
      {#if shareProgress < 100}
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="flex items-center gap-1.5">
                <div class="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></div>
              </div>
              <span class="text-[11px] text-slate-500 line-clamp-1">{campaignDesc}</span>
            </div>
            <span class="text-[13px] font-black text-rose-500">{Math.round(shareProgress)}%</span>
          </div>
          <div class="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
            <div class="h-full rounded-full bg-rose-500 transition-all duration-1000" style="width: {shareProgress}%"></div>
          </div>
        </div>
      {:else}
        <!-- Reveal State Minimalist -->
        <div class="p-3 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-between">
           <div class="flex flex-col">
             <span class="text-[10px] font-bold text-rose-600 uppercase mb-0.5">Mục tiêu đã đạt 🎉</span>
             <span class="text-[11px] text-slate-600">Mọi người đều có thể dùng mã này!</span>
           </div>
           <div class="flex items-center gap-2 bg-white px-2 py-1.5 rounded border border-rose-100">
             <span class="font-bold text-rose-600 text-xs font-mono">{voucherCode}</span>
             <button onclick={() => {
               if (voucherCode) {
                 navigator.clipboard.writeText(voucherCode);
                 onShareComplete?.();
               }
             }} class="text-slate-400 hover:text-rose-500"><Copy size={12} /></button>
           </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  :global(.vsb-heart-burst) { position: fixed; pointer-events: none; z-index: 10000; transform: translate(-50%, -50%); }
  :global(.vsb-heart-particle) { position: absolute; font-size: 14px; animation: heart-fly 0.8s ease-out forwards; opacity: 0; }
  @keyframes heart-fly {
    0% { transform: translate(0,0) scale(0.5); opacity: 1; }
    100% { transform: translate(calc(cos(calc(var(--i) * 45deg)) * 60px), calc(sin(calc(var(--i) * 45deg)) * 60px)) scale(1.2); opacity: 0; }
  }
</style>
