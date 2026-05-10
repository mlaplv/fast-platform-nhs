<script lang="ts">
    import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import Zap from "@lucide/svelte/icons/zap";
  import Bookmark from "@lucide/svelte/icons/bookmark";
  import Gift from "@lucide/svelte/icons/gift";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Package from "@lucide/svelte/icons/package";
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import VolumeX from "@lucide/svelte/icons/volume-x";
  import Heart from "@lucide/svelte/icons/heart";
  
  import { wishlistStore } from '$lib/state/commerce/wishlist.svelte';
  
  // Types
  import type { Product, ProductVariant, ReviewStats } from '$lib/types';
  
  // State & Stores
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  
  // Utils
  import { resolveMediaUrl } from '$lib/state/utils';
  import { formatCurrency, formatNumber } from '$lib/utils/format';
  
  // Components
  import ViralShareBarMobile from '../../shared/ViralShareBarMobile.svelte';
  import ShareToUnlockPromoMobile from '../../shared/ShareToUnlockPromoMobile.svelte';
  import ProductMobileMedia from './ProductMobileMedia.svelte';
  import ProductMobileFlashSale from './ProductMobileFlashSale.svelte';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  /** Detect video URL: mp4, webm, mov, ogg … (mirrored from Desktop) */
  function isVideoUrl(url: string | undefined | null): boolean {
    if (!url) return false;
    const clean = url.split('?')[0].toLowerCase();
    return /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(clean);
  }
  
  interface Props {
    product: Product;
    timeLeft: { hours: number; minutes: number; seconds: number };
    selectedVariant?: ProductVariant | null;
    selectedQty?: number;
    onOpenSelector?: () => void;
    stats?: import('$lib/types').ReviewStats | null;
    isViralUnlocked?: boolean;
  }

  let { product, timeLeft, selectedVariant, selectedQty = 1, onOpenSelector, stats, isViralUnlocked = $bindable() }: Props = $props();
  const cartStore = getCartStore();
  const clientUi = getClientUi();

  // --- LIKE / BOOKMARK STATE ---
  let likeAnimating = $state(false);
  const isLiked = $derived(wishlistStore.isLiked(product.id));
  const baseLikeCount = $derived(Number(product.metadata?.viral_suite?.likes_count || product.metadata?.likes || 0));
  const likeCount = $derived(baseLikeCount + (isLiked ? 1 : 0));

  function toggleLike() {
    const wasLiked = isLiked;
    wishlistStore.toggle(product.id);
    
    if (!wasLiked) {
      clientUi.showToast('Đã thêm sản phẩm vào mục Yêu thích', 'success');
      likeAnimating = true;
      setTimeout(() => { likeAnimating = false; }, 300);
    }
  }

  // --- FLASH SALE CONDITIONAL ---
  const flashSaleEnd = $derived(
    product.metadata?.flash_sale_end
      ? new Date(product.metadata.flash_sale_end).getTime()
      : null
  );
  const isFlashSaleActive = $derived(
    flashSaleEnd !== null && flashSaleEnd > Date.now()
  );

  const pVariants = $derived(product.variants || []);
  const variations = $derived(product.tier_variations || product.tierVariations || product.attributes?.tier_variations || product.metadata?.tier_variations || []);

  // Carousel State
  let activeImageIndex = $state(0);
  let carouselRef: HTMLElement | null = $state(null);

  // ─── Shopee-style Video State (Mobile) ───────────────────────────
  let videoEl = $state<HTMLVideoElement | null>(null);
  let videoMuted = $state(true);

  const videoStartTime = $derived(
    typeof product.metadata?.video_start_time === 'number'
      ? product.metadata.video_start_time
      : 0
  );
  const videoEndTime = $derived(
    typeof product.metadata?.video_end_time === 'number'
      ? product.metadata.video_end_time
      : null
  );

  function handleTimeUpdate() {
    if (!videoEl) return;
    if (videoEndTime !== null && videoEl.currentTime >= videoEndTime) {
      videoEl.currentTime = videoStartTime;
      videoEl.play().catch(() => {});
    }
  }

  /** Auto-play video when carousel scrolls to a video slide */
  $effect(() => {
    const currentUrl = displayImages[activeImageIndex];
    if (videoEl && isVideoUrl(currentUrl)) {
      videoEl.load();
      videoEl.muted = videoMuted;
      const onMeta = () => {
        if (videoEl) {
          videoEl.currentTime = videoStartTime;
          videoEl.play().catch(() => {});
        }
      };
      videoEl.addEventListener('loadedmetadata', onMeta, { once: true });
      return () => videoEl?.removeEventListener('loadedmetadata', onMeta);
    }
  });

  function toggleMute() {
    videoMuted = !videoMuted;
    if (videoEl) videoEl.muted = videoMuted;
  }
  
  // Voucher State
  let vouchersListRef: HTMLElement | null = $state(null);
  let isAtStart = $state(true);
  let isAtEnd = $state(false);
  let selectedVouchers = $state<string[]>([]);
  
  // Elite V2.2: Removed local state to use root-elevated prop

  function triggerViralFly() {
    isViralUnlocked = true;
  }

  function formatCount(count: number): string {
    if (count >= 1000) return (count / 1000).toFixed(1).replace('.0', '') + 'k';
    return count.toString();
  }

  const formatPrice = (p: number) => p.toLocaleString('vi-VN');
  
  const displayImages = $derived(product.images?.length > 0 ? product.images : [product.images?.[0] || '']);
  
  const vouchers = $derived.by(() => {
    const list: Array<{ id: string; label: string; sub: string; type: string }> = 
      Array.isArray(product.metadata?.vouchers) && product.metadata.vouchers.length > 0
        ? product.metadata.vouchers
        : cartStore.vouchers.map(v => ({
            id: v.id,
            label: v.title || v.id,
            sub: v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : `Giảm ${formatCurrency(v.value)}`),
            type: (v.type === 'SHIPPING' || v.type === 'ship') ? 'ship' : 'discount'
          }));

    /**
     * Elite V2.2: Intelligent Filtering for Mobile
     */
    const vouchersList = list.filter((v: { id: string; label?: string }) => {
      const promoVId = product.metadata?.viral_suite?.share_promotion?.voucher_id || (product.metadata as any)?.share_promotion?.voucher_id;
      const isViral = v.id.includes('VIRAL') || 
                      (v.label || '').toUpperCase().includes('VIRAL') || 
                      (v.label || '').toUpperCase().includes('LAN TỎA') ||
                      (promoVId && v.id === promoVId);
      return !isViral || isViralUnlocked;
    });

    // Elite V2.2 Re-injection: Nếu đã mở khóa, đảm bảo voucher xuất hiện dù backend đã lọc
    if (typeof window !== 'undefined' && isViralUnlocked) {
      const saved = localStorage.getItem(`viral_unlocked_${product.id}`);
      if (saved) {
        try {
          const data = JSON.parse(saved);
          const exists = vouchersList.find(v => v.id === data.code);
          if (!exists) {
             vouchersList.push({
               id: data.code,
               label: data.label || 'VOUCHER LAN TỎA',
               sub: 'Đã mở khóa từ chiến dịch',
               type: 'discount'
             });
          }
        } catch (e) {}
      }
    }
    return vouchersList;
  });

  const activeVariant = $derived(selectedVariant || pVariants?.[0]);
  
  const effectiveUnitPrice = $derived.by(() => {
    const v = activeVariant;
    if (!v) return product.discountPrice || product.discount_price || product.price || 0;
    
    // Tier Resolution logic
    const comboVariants = pVariants.filter(cv => cv.attributes && cv.attributes.combo_qty);
    const qty = selectedQty;
    
    if (comboVariants.length > 0) {
      const sortedTiers = [...comboVariants].sort((a, b) => Number(b.attributes.combo_qty) - Number(a.attributes.combo_qty));
      const bestTier = sortedTiers.find(t => Number(t.attributes.combo_qty) <= qty);
      const finalV = bestTier || v;
      return finalV.discountPrice || finalV.discount_price || finalV.price;
    }
    return v.discountPrice || v.discount_price || v.price;
  });

  const displaySalePrice = $derived(effectiveUnitPrice);
  const displayOriginalPrice = $derived(activeVariant?.price || product.price || 0);
  const displayDiscountPercent = $derived(
    displayOriginalPrice > displaySalePrice 
      ? Math.round(((displayOriginalPrice - displaySalePrice) / displayOriginalPrice) * 100)
      : 0
  );

  function handleCarouselScroll(e: Event) {
    if (!carouselRef) return;
    const scrollLeft = (e.target as HTMLElement).scrollLeft;
    const width = carouselRef.offsetWidth;
    activeImageIndex = Math.round(scrollLeft / width);
  }

  function toggleVoucher(id: string) {
    const voucher = vouchers.find(v => v.id === id);
    if (!voucher) return;
    if (selectedVouchers.includes(id)) {
      selectedVouchers = selectedVouchers.filter(v => v !== id);
    } else {
      const groupIds = vouchers.filter(v => v.type === voucher.type).map(v => v.id);
      selectedVouchers = [...selectedVouchers.filter(v => !groupIds.includes(v)), id];
    }
  }

  function scrollVouchers(direction: 'next' | 'prev') {
    if (vouchersListRef) {
      const amount = direction === 'next' ? 140 : -140;
      vouchersListRef.scrollBy({ left: amount, behavior: 'smooth' });
    }
  }

  function handleVoucherScroll() {
    if (!vouchersListRef) return;
    const { scrollLeft, scrollWidth, clientWidth } = vouchersListRef;
    isAtStart = scrollLeft <= 5;
    isAtEnd = scrollLeft + clientWidth >= scrollWidth - 5;
  }

  const activeComboQty = $derived((selectedVariant || pVariants?.[0])?.attributes?.combo_qty || (selectedVariant || pVariants?.[0])?.attributes?.comboQty || product.metadata?.combo_qty || 0);
  const activeGifts = $derived((selectedVariant || pVariants?.[0])?.attributes?.gifts || product.metadata?.gifts || []);
</script>

<section id="overview" class="overview-section">
  <!-- MEDIA SECTION (Extracted) -->
  <ProductMobileMedia
    {product}
    {displayImages}
    {activeImageIndex}
    bind:videoEl
    {videoMuted}
    {videoEndTime}
    {handleTimeUpdate}
    {toggleMute}
    {handleCarouselScroll}
    {triggerViralFly}
    onThumbClick={(i) => {
      activeImageIndex = i;
      carouselRef?.scrollTo({ left: i * carouselRef.clientWidth, behavior: 'smooth' });
    }}
    bind:carouselRef
    {isVideoUrl}
  />

  <!-- FLASH SALE BANNER (Extracted) -->
  <ProductMobileFlashSale
    {isFlashSaleActive}
    {displayDiscountPercent}
    {displaySalePrice}
    {displayOriginalPrice}
    {timeLeft}
  />



  <!-- INFO SECTION -->
  <section class="info-content">
    <!-- Vouchers -->
    <div class="vouchers-outer">
      {#if !isAtStart}<button class="scroll-btn prev" onclick={() => scrollVouchers('prev')}><ChevronLeft size={14} /></button>{/if}
      <div class="vouchers-container">
        <div class="vouchers-list" bind:this={vouchersListRef} onscroll={handleVoucherScroll}>
          {#each vouchers as v}
            {@const isApplied = selectedVouchers.includes(v.id)}
            <button type="button" class="ticket-wrapper" onclick={() => toggleVoucher(v.id)}>
              <div class="ticket" class:active={isApplied}>
                <div class="ticket-content">
                   <span class="main">{v.label}</span>
                   <span class="sub">{v.sub || ''}</span>
                </div>
              </div>
              {#if isApplied}
                <div class="active-badge">
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </div>
              {/if}
            </button>
          {/each}
        </div>
      </div>
      {#if !isAtEnd}<button class="scroll-btn next" onclick={() => scrollVouchers('next')}><ChevronRight size={14} /></button>{/if}
    </div>

    <!-- Title & Stats -->
    <div class="title-row mt-2">
      <h1 class="product-title">{product.name.replace(/40gr/g, '40g')}</h1>

    </div>

    <!-- Selection Row (Shopee Viral Style) -->
    {#if variations.length > 0}
      <button 
        onclick={onOpenSelector}
        class="w-full flex items-center justify-between py-4 border-y border-gray-50 my-2 active:bg-gray-50 transition-colors"
      >
        <div class="flex items-center gap-4">
          <span class="text-[13px] text-gray-500 w-[80px] text-left">Phân loại</span>
          <span class="text-[13px] font-bold text-gray-900">
            {#if selectedVariant}
              {selectedVariant.tierIndex.map((idx, i) => variations?.[i]?.options?.[idx] || '').filter(Boolean).join(', ')}
            {:else}
              Chọn màu sắc, kích cỡ, combo...
            {/if}
          </span>
        </div>
        <ChevronRight size={16} class="text-gray-400" />
      </button>
    {/if}

    <!-- COMBO & GIFTS MINI (Viral 2026) -->
    {#if activeComboQty > 1 || activeGifts.length > 0}
      <div class="mb-4 bg-gradient-to-br from-[#fdf2f2] to-white p-3 rounded-xl border border-[#ee4d2d]/10">
         <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
               <Gift size={16} class="text-[#ee4d2d]" />
               <span class="text-[11px] font-black text-gray-800 tracking-wider">Quà tặng đi kèm</span>
            </div>
            {#if activeComboQty > 1}
               <div class="bg-[#ee4d2d]/10 text-[#ee4d2d] text-[9px] font-black px-2 py-0.5 rounded-full border border-[#ee4d2d]/20 flex items-center gap-1">
                  <Package size={10} /> Combo x{activeComboQty}
               </div>
            {/if}
         </div>
         
         {#if activeGifts.length > 0}
            <div class="flex flex-col gap-2">
               {#each activeGifts as gift}
                  <div class="flex items-center gap-3">
                     <div class="w-10 h-10 rounded-lg overflow-hidden bg-white border border-gray-100 shrink-0 shadow-sm">
                        {#if gift.image}
                           <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                        {:else}
                           <div class="w-full h-full flex items-center justify-center text-gray-200"><Sparkles size={14} /></div>
                        {/if}
                     </div>
                     <div class="flex flex-col">
                        <span class="text-[12px] font-bold text-gray-900 leading-tight">{gift.name}</span>
                        <span class="text-[10px] text-[#ee4d2d] font-black italic">Tặng kèm x{gift.qty}</span>
                     </div>
                  </div>
               {/each}
            </div>
         {/if}
      </div>
    {/if}




    <!-- VIRAL SHARE BAR (Mobile Floating) -->
    <ViralShareBarMobile 
      {product} 
      variant="mobile" 
      likeCount={baseLikeCount}
    />

    <div class="product-stats-row">
      <div class="rating-box">
        <span class="scoreText">{stats?.average_rating || product.metadata?.rating || '5.0'}</span>
        <div class="stars">
          {#each Array(5) as _, i}
            <svg class="w-2.5 h-2.5 {i < Math.floor(stats?.average_rating || Number(product.metadata?.rating) || 5) ? 'text-luxury-copper' : 'text-gray-300'}" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          {/each}
        </div>
      </div>
      <div class="divider"></div>
      <div class="sold-count">{product.order_count_text || `Đã bán ${formatNumber(product.orderCount) || 0}`}</div>
    </div>
  </section>
</section>

<style>
  .info-content { background: white; padding: 10px 6px; }
  .vouchers-outer { position: relative; margin-bottom: 12px; margin-left: -12px; margin-right: -12px; }
  .vouchers-list {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    scrollbar-width: none;
    padding: 0 12px;
    scroll-padding: 0 12px;
  }
  .vouchers-list::-webkit-scrollbar { display: none; }
  .ticket { background: #fffaf9; border: 1px dashed var(--color-luxury-copper, #C18F7E); color: var(--color-luxury-copper, #C18F7E); padding: 4px 10px; border-radius: 4px; font-size: 11px; white-space: nowrap; font-weight: 700; }
  .ticket.active { background: var(--color-luxury-copper, #C18F7E); color: white; border-style: solid; }
  .ticket-wrapper { position: relative; background: none; border: none; padding: 0; }
  .active-badge { position: absolute; top: -4px; right: -4px; background: var(--color-luxury-peach, #E3B5A4); color: white; border-radius: 50%; width: 14px; height: 14px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .scroll-btn {
    position: absolute; top: 50%; transform: translateY(-50%); background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 0, 0, 0.05); border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; z-index: 10;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1); color: var(--color-luxury-copper, #C18F7E); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); -webkit-tap-highlight-color: transparent;
  }
  .scroll-btn:active { scale: 0.85; background: white; }
  .scroll-btn.prev { left: 4px; }
  .scroll-btn.next { right: 4px; }

  .title-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
  .product-title { font-size: 16px; font-weight: 800; line-height: 1.4; color: #222; flex: 1; margin: 0; }
  .bookmark-btn { background: none; border: none; color: #666; padding: 0; transition: color 0.3s; }
  .bookmark-active { color: #ff424f !important; }

  .product-stats-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #888; }
  .rating-box { display: flex; align-items: center; gap: 4px; color: #222; font-weight: 900; }
  .stars { display: flex; align-items: center; gap: 1px; }
  .divider { width: 1px; height: 10px; background: #eee; }
  .trust-badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; letter-spacing: 0.05em; }

  /* CSS Variables for global sync */
  .overview-section { --z-media-promo: var(--z-index-media-promo, 10); }
</style>
