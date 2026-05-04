<script lang="ts">
  import { ChevronLeft, ChevronRight, Zap, Bookmark, Gift, Sparkles, Package } from 'lucide-svelte';
  import type { Product } from '$lib/types';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { formatCurrency } from '$lib/utils/format';
  
  interface Props {
    product: Product;
    timeLeft: { hours: number; minutes: number; seconds: number };
    selectedVariant?: ProductVariant | null;
    selectedQty?: number;
    onOpenSelector?: () => void;
    stats?: import('$lib/types').ReviewStats | null;
  }

  let { product, timeLeft, selectedVariant, selectedQty = 1, onOpenSelector, stats }: Props = $props();
  const cartStore = getCartStore();

  const pVariants = $derived(product.variants || []);
  const variations = $derived(product.tier_variations || product.tierVariations || product.attributes?.tier_variations || product.metadata?.tier_variations || []);

  // Carousel State
  let activeImageIndex = $state(0);
  let carouselRef: HTMLElement | null = $state(null);
  
  // Voucher State
  let vouchersListRef: HTMLElement | null = $state(null);
  let isAtStart = $state(true);
  let isAtEnd = $state(false);
  let selectedVouchers = $state<string[]>([]);

  const formatPrice = (p: number) => p.toLocaleString('vi-VN');
  
  const displayImages = $derived(product.images?.length > 0 ? product.images : [product.images?.[0] || '']);
  
  const vouchers = $derived.by(() => {
    // 1. Check if product has specific override vouchers
    if (Array.isArray(product.metadata?.vouchers) && product.metadata.vouchers.length > 0) {
      return product.metadata.vouchers;
    }
    
    // 2. Fallback to global active vouchers from CartStore (Elite V2.2)
    return cartStore.vouchers.map(v => ({
      id: v.id,
      label: v.title || v.id,
      sub: v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : `Giảm ${formatCurrency(v.value)}`),
      type: (v.type === 'SHIPPING' || v.type === 'ship') ? 'ship' : 'discount'
    }));
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
  <!-- MEDIA CAROUSEL -->
  <section class="media-section">
    <div class="carousel-container" bind:this={carouselRef} onscroll={handleCarouselScroll}>
      {#each displayImages as img}
        <div class="carousel-slide">
          <img src={img} alt={product.name} />
        </div>
      {/each}
    </div>
    <div class="image-counter">{activeImageIndex + 1}/{displayImages.length}</div>

    <!-- Thumbnails (Hình thuib) -->
    <div class="thumbnails-track mt-2 px-4 flex gap-2 overflow-x-auto no-scrollbar">
      {#each displayImages as img, i}
        <button 
          type="button"
          class="w-12 h-12 rounded-sm border-2 overflow-hidden shrink-0 transition-all {activeImageIndex === i ? 'border-[#ee4d2d]' : 'border-transparent opacity-60'} p-0"
          onclick={() => {
            activeImageIndex = i;
            carouselRef?.scrollTo({ left: i * carouselRef.clientWidth, behavior: 'smooth' });
          }}
          aria-label="Xem ảnh nhỏ {i + 1}"
        >
          <img src={img} alt="thumb" class="w-full h-full object-cover" />
        </button>
      {/each}
    </div>
  </section>

  <!-- FLASH SALE BANNER -->
  <section class="flash-sale-banner">
    <div class="fs-left">
      <div class="flex items-center gap-1.5">
        <div class="discount-percent">-{displayDiscountPercent}%</div>
        <div class="freeship-fomo">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          FREE SHIP
        </div>
      </div>
      <div class="price-container">
        <span class="price-label">Từ</span>
        <span class="price-value">{formatCurrency(displaySalePrice)}</span>
      </div>
      <div class="original-price">{formatCurrency(displayOriginalPrice)}</div>
    </div>
    
    <div class="fs-right">
      <div class="fs-title"><Zap size={18} fill="white" /><span>Flash Sale</span></div>
      <div class="fs-countdown">
        <span>Kết thúc sau</span>
        <div class="time-box font-mono tabular-nums">
          <span>{timeLeft.hours.toString().padStart(2, '0')}</span>
          <span class="separator">:</span>
          <span>{timeLeft.minutes.toString().padStart(2, '0')}</span>
          <span class="separator">:</span>
          <span>{timeLeft.seconds.toString().padStart(2, '0')}</span>
        </div>
      </div>
    </div>
  </section>

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
               <span class="text-[11px] font-black uppercase text-gray-800 tracking-wider">Quà tặng đi kèm</span>
            </div>
            {#if activeComboQty > 1}
               <div class="bg-[#ee4d2d]/10 text-[#ee4d2d] text-[9px] font-black px-2 py-0.5 rounded-full border border-[#ee4d2d]/20 flex items-center gap-1">
                  <Package size={10} /> COMBO X{activeComboQty}
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
      <div class="sold-count">{product.order_count_text || `Đã bán ${product.orderCount || 0}`}</div>
      <div class="trust-badge text-luxury-copper font-bold bg-luxury-peach/10">{product.metadata?.brand_type || 'osmo Mall'}</div>
    </div>
  </section>
</section>

<style>
  .media-section { position: relative; background: white; aspect-ratio: 1/1; overflow: hidden; }
  .carousel-container { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; height: 100%; }
  .carousel-container::-webkit-scrollbar { display: none; }
  .carousel-slide { flex: 0 0 100%; height: 100%; scroll-snap-align: start; }
  .carousel-slide img { width: 100%; height: 100%; object-fit: cover; }
  .image-counter { position: absolute; bottom: 64px; right: 12px; background: rgba(0, 0, 0, 0.4); color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
  .thumbnails-track { scrollbar-width: none; -ms-overflow-style: none; }
  .thumbnails-track::-webkit-scrollbar { display: none; }

  .flash-sale-banner { background: var(--color-luxury-copper, #C18F7E); color: white; display: flex; padding: 4px 8px; justify-content: space-between; align-items: center; position: relative; overflow: hidden; }
  .fs-left { flex: 1; z-index: var(--z-base); }
  .discount-percent { background: white; color: var(--color-luxury-copper, #C18F7E); border: 1px solid white; width: max-content; padding: 0 4px; font-size: 11px; font-weight: 900; border-radius: 2px; }
  .freeship-fomo { background: var(--color-luxury-peach, #E3B5A4); color: white; font-size: 10px; font-weight: 900; padding: 0 4px; border-radius: 2px; display: flex; align-items: center; gap: 2px; height: 16px; }
  .price-container { display: flex; align-items: center; gap: 4px; margin-top: 2px; }
  .price-label { font-size: 13px; color: white; opacity: 0.9; }
  .price-value { font-size: 20px; font-weight: 900; letter-spacing: -0.5px; }
  .original-price { font-size: 11px; text-decoration: line-through; color: rgba(255,255,255,0.7); }
  .fs-right { text-align: right; z-index: var(--z-base); display: flex; flex-direction: column; align-items: flex-end; }
  .fs-title { display: flex; align-items: center; gap: 4px; font-weight: 900; font-size: 16px; text-transform: uppercase; font-style: italic; }
  .fs-countdown { font-size: 11px; display: flex; align-items: center; gap: 4px; font-weight: 700; }
  .time-box { display: flex; gap: 2px; align-items: center; }
  .time-box span { background: rgba(0,0,0,0.2); color: white; padding: 1px 4px; border-radius: 2px; font-weight: 900; border: 1px solid rgba(255,255,255,0.2); min-width: 24px; text-align: center; }
  .time-box .separator { background: none; border: none; padding: 0; min-width: 8px; opacity: 0.6; text-align: center; }

  .info-content { background: white; padding: 12px; }
  .vouchers-outer { position: relative; margin-bottom: 12px; margin-left: -12px; margin-right: -12px; }
  .vouchers-list {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    scrollbar-width: none;
    padding: 0 24px;
    scroll-padding: 0 24px;
  }
  .vouchers-list::-webkit-scrollbar { display: none; }
  .ticket { background: #fffaf9; border: 1px dashed var(--color-luxury-copper, #C18F7E); color: var(--color-luxury-copper, #C18F7E); padding: 4px 10px; border-radius: 4px; font-size: 11px; white-space: nowrap; font-weight: 700; }
  .ticket.active { background: var(--color-luxury-copper, #C18F7E); color: white; border-style: solid; }
  .ticket-wrapper { position: relative; background: none; border: none; padding: 0; }
  .active-badge { position: absolute; top: -4px; right: -4px; background: var(--color-luxury-peach, #E3B5A4); color: white; border-radius: 50%; width: 14px; height: 14px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .scroll-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    color: var(--color-luxury-copper, #C18F7E);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    -webkit-tap-highlight-color: transparent;
  }
  .scroll-btn:active {
    scale: 0.85;
    background: white;
  }
  .scroll-btn.prev { left: 4px; }
  .scroll-btn.next { right: 4px; }

  .title-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
  .product-title { font-size: 16px; font-weight: 800; line-height: 1.4; color: #222; flex: 1; margin: 0; text-transform: capitalize; }
  .bookmark-btn { background: none; border: none; color: #666; padding: 0; transition: color 0.3s; }
  .bookmark-btn:active { color: var(--color-luxury-copper, #C18F7E); }

  .product-stats-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #888; }
  .rating-box { display: flex; align-items: center; gap: 4px; color: #222; font-weight: 900; }
  .stars { display: flex; align-items: center; gap: 1px; }
  .divider { width: 1px; height: 10px; background: #eee; }
  .trust-badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
</style>
