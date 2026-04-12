<script lang="ts">
  import { ChevronLeft, ChevronRight, Zap, Bookmark } from 'lucide-svelte';
  import type { Product } from '$lib/types';
  
  interface Props {
    product: Product;
    timeLeft: { hours: number; minutes: number; seconds: number };
  }

  let { product, timeLeft }: Props = $props();

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
  
  const vouchers = $derived(
    Array.isArray((product.metadata as any)?.vouchers) && (product.metadata as any).vouchers.length > 0
      ? (product.metadata as any).vouchers 
      : [
          { id: 'freeship_30k', label: 'Miễn Phí Vận Chuyển', sub: 'Giảm tối đa 30,000đ', type: 'ship' },
          { id: 'freeship_60k', label: 'Miễn Phí Vận Chuyển', sub: 'Giảm tối đa 60,000đ', type: 'ship' },
          { id: 'disc_30k', label: 'Giảm ₫30k', sub: 'Đơn từ 150k', type: 'discount' },
          { id: 'disc_60k', label: 'Giảm ₫60k', sub: 'Đơn từ 300k', type: 'discount' }
        ]
  );

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
        <span class="scoreText">{(product.metadata as any)?.rating || '5.0'}</span>
        <div class="stars">
          {#each Array(5) as _, i}
            <svg class="w-2.5 h-2.5 {i < ((product.metadata as any)?.rating || 5) ? 'text-orange-400' : 'text-gray-300'}" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          {/each}
        </div>
      </div>
      <div class="divider"></div>
      <div class="sold-count">{(product as any).order_count_text || `Đã bán ${product.order_count || 0}`}</div>
      <div class="trust-badge">{(product.metadata as any)?.brand_type || 'Micsmo'}</div>
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

  .flash-sale-banner { background: #ff2556; color: white; display: flex; padding: 4px 8px; justify-content: space-between; align-items: center; position: relative; overflow: hidden; }
  .fs-left { flex: 1; z-index: var(--z-base); }
  .discount-percent { background: white; color: #ff2556; border: 1px solid #ff2556; width: max-content; padding: 0 4px; font-size: 11px; font-weight: 800; border-radius: 2px; }
  .freeship-fomo { background: #00bfa5; color: white; font-size: 10px; font-weight: 900; padding: 0 4px; border-radius: 2px; display: flex; align-items: center; gap: 2px; height: 16px; }
  .price-container { display: flex; align-items: center; gap: 4px; margin-top: 2px; }
  .price-label { font-size: 13px; color: white; }
  .price-value { font-size: 20px; font-weight: 800; }
  .original-price { font-size: 11px; text-decoration: line-through; color: rgba(255,255,255,0.8); }
  .fs-right { text-align: right; z-index: var(--z-base); display: flex; flex-direction: column; align-items: flex-end; }
  .fs-title { display: flex; align-items: center; gap: 4px; font-weight: 900; font-size: 16px; }
  .fs-countdown { font-size: 11px; display: flex; align-items: center; gap: 4px; }
  .time-box { display: flex; gap: 2px; }
  .time-box span { background: #333; color: white; padding: 1px 3px; border-radius: 2px; font-weight: bold; }

  .info-content { background: white; padding: 12px; }
  .vouchers-outer { position: relative; margin-bottom: 12px; }
  .vouchers-list { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; mask-image: linear-gradient(to right, black 90%, transparent); }
  .vouchers-list::-webkit-scrollbar { display: none; }
  .ticket { background: #fff5f5; border: 1px dashed #ff4d4f; color: #ff4d4f; padding: 4px 8px; border-radius: 4px; font-size: 11px; white-space: nowrap; }
  .ticket.active { background: #ff4d4f; color: white; border-style: solid; }
  .ticket-wrapper { position: relative; background: none; border: none; padding: 0; }
  .active-badge { position: absolute; top: -4px; right: -4px; background: #52c41a; color: white; border-radius: 50%; width: 12px; height: 12px; display: flex; align-items: center; justify-content: center; }
  .scroll-btn { position: absolute; top: 50%; transform: translateY(-50%); background: white; border: 1px solid #eee; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; z-index: 2; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .scroll-btn.prev { left: -8px; }
  .scroll-btn.next { right: -8px; }

  .title-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
  .product-title { font-size: 16px; font-weight: 600; line-height: 1.4; color: #222; flex: 1; margin: 0; }
  .bookmark-btn { background: none; border: none; color: #666; padding: 0; }

  .product-stats-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #888; }
  .rating-box { display: flex; align-items: center; gap: 4px; color: #222; font-weight: bold; }
  .divider { width: 1px; height: 10px; background: #eee; }
  .trust-badge { background: #f0f0f0; padding: 2px 6px; border-radius: 2px; }
</style>
