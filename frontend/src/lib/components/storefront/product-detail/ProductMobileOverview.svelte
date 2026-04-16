<script lang="ts">
  import { ChevronLeft, ChevronRight, Zap, Bookmark } from 'lucide-svelte';
  import type { Product } from '$lib/types';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  
  interface Props {
    product: Product;
    timeLeft: { hours: number; minutes: number; seconds: number };
  }

  let { product, timeLeft }: Props = $props();
  const cartStore = getCartStore();

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
      sub: v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : `Giảm ${v.value.toLocaleString()}đ`),
      type: v.type === 'SHIPPING' ? 'ship' : 'discount'
    }));
  });

  const pDiscountPrice = $derived(product.discountPrice || product.discount_price);
  const displaySalePrice = $derived(pDiscountPrice || product.price);
  const displayOriginalPrice = $derived(pDiscountPrice ? product.price : product.price * 1.5);
  const displayDiscountPercent = $derived(
    Math.round(((displayOriginalPrice - displaySalePrice) / displayOriginalPrice) * 100)
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
        <span class="price-value">{formatPrice(displaySalePrice)}đ</span>
      </div>
      <div class="original-price">{formatPrice(displayOriginalPrice)}đ</div>
    </div>
    
    <div class="fs-right">
      <div class="fs-title"><Zap size={18} fill="white" /><span>Flash Sale</span></div>
      <div class="fs-countdown">
        <span>Kết thúc sau</span>
        <div class="time-box">
          <span>{timeLeft.hours.toString().padStart(2, '0')}</span>:
          <span>{timeLeft.minutes.toString().padStart(2, '0')}</span>:
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
            <button class="ticket-wrapper" onclick={() => toggleVoucher(v.id)}>
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
    <div class="title-row">
      <h1 class="product-title">{product.name}</h1>
      <button class="bookmark-btn"><Bookmark size={22} /></button>
    </div>

    <div class="product-stats-row">
      <div class="rating-box">
        <span class="scoreText">{product.metadata?.rating || '5.0'}</span>
        <div class="stars">
          {#each Array(5) as _, i}
            <svg class="w-2.5 h-2.5 {i < (Number(product.metadata?.rating) || 5) ? 'text-luxury-copper' : 'text-gray-300'}" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          {/each}
        </div>
      </div>
      <div class="divider"></div>
      <div class="sold-count">{product.order_count_text || `Đã bán ${product.order_count || 0}`}</div>
      <div class="trust-badge text-luxury-copper font-bold bg-luxury-peach/10">{product.metadata?.brand_type || 'Micsmo Mall'}</div>
    </div>
  </section>
</section>

<style>
  .media-section { position: relative; background: white; aspect-ratio: 1/1; overflow: hidden; }
  .carousel-container { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; height: 100%; }
  .carousel-container::-webkit-scrollbar { display: none; }
  .carousel-slide { flex: 0 0 100%; height: 100%; scroll-snap-align: start; }
  .carousel-slide img { width: 100%; height: 100%; object-fit: cover; }
  .image-counter { position: absolute; bottom: 12px; right: 12px; background: rgba(0, 0, 0, 0.4); color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; }

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
  .time-box { display: flex; gap: 2px; }
  .time-box span { background: rgba(0,0,0,0.2); color: white; padding: 1px 4px; border-radius: 2px; font-weight: 900; border: 1px solid rgba(255,255,255,0.2); }

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
