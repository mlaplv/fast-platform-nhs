<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { 
    ChevronLeft, 
    Search, 
    Share2, 
    ShoppingCart, 
    MoreHorizontal,
    Zap,
    Bookmark,
    ChevronRight,
    MessageCircleMore
  } from 'lucide-svelte';
  import MobileBottomNav from '../home/MobileBottomNav.svelte';
  import type { Product } from '$lib/types';

  interface Props {
    product: Product;
  }
  let { product }: Props = $props();

  const cartStore = getCartStore();
  
  // State cho Carousel
  let activeImageIndex = $state(0);
  let carouselRef: HTMLElement | null = $state(null);
  let vouchersListRef: HTMLElement | null = $state(null);
  
  // State điều hướng Voucher
  let isAtStart = $state(true);
  let isAtEnd = $state(false);

  // State cho countdown Flash Sale (giả lập kết thúc sau 14h như hình)
  let timeLeft = $state({ hours: 14, minutes: 9, seconds: 9 });

  onMount(() => {
    const timer = setInterval(() => {
      if (timeLeft.seconds > 0) {
        timeLeft.seconds--;
      } else if (timeLeft.minutes > 0) {
        timeLeft.minutes--;
        timeLeft.seconds = 59;
      } else if (timeLeft.hours > 0) {
        timeLeft.hours--;
        timeLeft.minutes = 59;
        timeLeft.seconds = 59;
      }
    }, 1000);
    return () => clearInterval(timer);
  });

  function handleScroll(e: Event) {
    if (!carouselRef) return;
    const scrollLeft = (e.target as HTMLElement).scrollLeft;
    const width = carouselRef.offsetWidth;
    activeImageIndex = Math.round(scrollLeft / width);
  }

  function addToCart() {
    cartStore.addItem(product as any);
  }

  function buyNow() {
    cartStore.addItem(product as any);
    cartStore.closeCart();
    goto('/checkout');
  }

  const formatPrice = (p: number) => p.toLocaleString('vi-VN');
  
  // Voucher Logic (Elite V2.2: Interaction Sync)
  let selectedVouchers = $state<string[]>([]);
  const vouchers = [
    { id: 'freeship', label: 'Miễn Phí Vận Chuyển', sub: 'HẠN 15/04' },
    { id: '30k', label: 'Giảm ₫30k', sub: 'HẠN 15/04' },
    { id: '60k', label: 'Giảm ₫60k', sub: 'HẠN 15/04' },
    { id: '3pct', label: 'Giảm 3%', sub: 'HẠN 15/04' },
    { id: '5pct', label: 'Giảm 5%', sub: 'HẠN 15/04' }
  ];

  function toggleVoucher(id: string) {
    if (selectedVouchers.includes(id)) {
      selectedVouchers = selectedVouchers.filter(v => v !== id);
    } else {
      selectedVouchers = [...selectedVouchers, id];
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
  const displayImages = product.images?.length > 0 ? product.images : [product.images?.[0] || ''];
</script>

<div class="product-mobile-root">
  <!-- 1. STICKY HEADER -->
  <header class="detail-header">
    <button class="icon-btn" onclick={() => history.back()}>
      <ChevronLeft size={24} />
    </button>
    
    <div class="search-bar-wrapper">
      <Search size={16} class="search-icon" />
      <span class="placeholder">tai nghe bluet...</span>
    </div>

    <div class="header-actions">
      <button class="icon-btn">
        <Share2 size={24} />
      </button>
      <button class="icon-btn relative" onclick={() => goto('/checkout')}>
        <ShoppingCart size={24} />
        {#if cartStore.totalItems > 0}
          <span class="badge">{cartStore.totalItems}</span>
        {/if}
      </button>
      <button class="icon-btn">
        <MoreHorizontal size={24} />
      </button>
    </div>
  </header>

  <!-- 2. IMAGE CAROUSEL SECTION -->
  <section class="media-section">
    <div 
      class="carousel-container" 
      bind:this={carouselRef}
      onscroll={handleScroll}
    >
      {#each displayImages as img}
        <div class="carousel-slide">
          <img src={img} alt={product.name} />
        </div>
      {/each}
    </div>
  </section>

  <!-- 3. FLASH SALE BANNER -->
  <section class="flash-sale-banner">
    <div class="fs-left">
      <div class="flex items-center gap-1.5">
        <div class="discount-percent">-{Math.round(((product.price * 1.5 - product.price) / (product.price * 1.5)) * 100)}%</div>
        <div class="freeship-fomo">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          FREE SHIP
        </div>
      </div>
      <div class="price-container">
        <span class="price-label">Từ</span>
        <span class="price-value">{formatPrice(product.price)}đ</span>
        <img src="https://img.icons8.com/color/48/ticket.png" alt="coupon" class="w-4 h-4" />
      </div>
      <div class="flex items-center gap-2">
        <div class="original-price">{formatPrice(product.price * 1.5)}đ</div>
        <div class="today-only">Chỉ áp dụng hôm nay</div>
      </div>
    </div>
    
    <div class="fs-right">
      <div class="fs-title">
        <Zap size={18} fill="white" />
        <span>Flash Sale</span>
      </div>
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

  <!-- 4. PRODUCT INFO & VOUCHERS -->
  <section class="product-details-content">
    <!-- Voucher horizontal scroll - Desktop Style -->
    <div class="vouchers-outer">
      {#if !isAtStart}
        <button class="scroll-btn prev" onclick={() => scrollVouchers('prev')}>
          <ChevronLeft size={14} />
        </button>
      {/if}

      <div class="vouchers-container">
        <div 
          class="vouchers-list" 
          bind:this={vouchersListRef}
          onscroll={handleVoucherScroll}
        >
          {#each vouchers as v}
            {@const isApplied = selectedVouchers.includes(v.id)}
            <button 
              class="ticket-wrapper bg-transparent border-none p-0 outline-none active:scale-95 transition-transform"
              onclick={() => toggleVoucher(v.id)}
            >
              <div class="ticket" class:active={isApplied}>
                <div class="ticket-content">
                  <span class="main">{v.label}</span>
                  <span class="sub">{v.sub}</span>
                </div>
                
                {#if isApplied}
                  <div class="selected-badge">
                    <svg class="w-2 h-2 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                {/if}
              </div>
            </button>
          {/each}
        </div>
      </div>
      
      {#if !isAtEnd}
        <button class="scroll-btn next" onclick={() => scrollVouchers('next')}>
          <ChevronRight size={14} />
        </button>
      {/if}
    </div>

    <!-- Title & Bookmark -->
    <div class="title-row">
      <h1 class="product-title">{product.name}</h1>
      <button class="bookmark-btn">
        <Bookmark size={22} />
      </button>
    </div>

    <!-- Rating, Sold & Trust Badge -->
    <div class="product-stats-row">
      <div class="rating-box">
        <span class="scoreText">4.9</span>
        <div class="stars">
          {#each Array(5) as _, i}
            <svg class="w-2.5 h-2.5 {i < 4 ? 'text-orange-400' : 'text-gray-300'}" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          {/each}
        </div>
      </div>
      <div class="divider"></div>
      <div class="sold-count">
        Đã bán 29
      </div>
      <div class="trust-badge">
        Mall
      </div>
    </div>
  </section>

  <!-- 5. STICKY BOTTOM NAV -->
  <MobileBottomNav />

  <!-- Content spacing for Bottom Nav -->
  <div class="h-28"></div>
</div>

<style>
  .product-mobile-root {
    background: #f5f5f5;
    min-height: 100vh;
    width: 100%;
    font-family: 'Inter', sans-serif;
  }

  /* HEADER */
  .detail-header {
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }

  .icon-btn {
    background: transparent;
    border: none;
    color: #444;
    padding: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: #ee4d2d;
    color: white;
    font-size: 10px;
    font-weight: bold;
    min-width: 16px;
    height: 16px;
    border-radius: 999px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid white;
  }

  .search-bar-wrapper {
    flex: 1;
    background: #f0f0f0;
    height: 36px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    padding: 0 12px;
    gap: 8px;
    color: #888;
  }

  .placeholder {
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .header-actions {
    display: flex;
    gap: 4px;
  }

  /* MEDIA SECTION */
  .media-section {
    position: relative;
    background: white;
    aspect-ratio: 1/1;
    overflow: hidden;
  }

  .carousel-container {
    display: flex;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
    height: 100%;
  }

  .carousel-container::-webkit-scrollbar { display: none; }

  .carousel-slide {
    flex: 0 0 100%;
    height: 100%;
    scroll-snap-align: start;
  }

  .carousel-slide img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .badge-return {
    position: absolute;
    top: 12px;
    left: 12px;
    background: rgba(0, 0, 0, 0.6);
    color: white;
    padding: 4px 10px;
    border-radius: 99px;
    font-size: 12px;
    display: flex;
    align-items: center;
  }

  .image-counter {
    position: absolute;
    bottom: 60px;
    right: 12px;
    background: rgba(0, 0, 0, 0.4);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
  }

  .promo-overlay-tags {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    display: flex;
    align-items: flex-end;
  }

  .promo-tag {
    height: 48px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 0 10px;
    font-weight: bold;
    font-size: 11px;
    flex: 1;
  }

  .promo-tag.freeship {
    background: #00bfa5;
    color: white;
    clip-path: polygon(0 0, 90% 0, 100% 100%, 0% 100%);
  }

  .promo-tag.extra {
    background: #ee4d2d;
    color: white;
    margin-left: -5px;
    clip-path: polygon(10% 0, 90% 0, 100% 100%, 0% 100%);
  }

  .promo-tag.bonus {
    background: #ffc107;
    color: #444;
    margin-left: -5px;
    clip-path: polygon(10% 0, 100% 0, 100% 100%, 0% 100%);
  }

  .xtra { font-weight: 900; font-size: 13px; font-style: italic; }
  .extra-text { font-weight: 900; font-size: 13px; font-style: italic; }
  .bonus-label { font-weight: 900; font-size: 13px; background: black; color: white; width: max-content; padding: 0 2px; }

  .bluetooth-tag {
    position: absolute;
    right: 12px;
    bottom: 12px;
    background: rgba(255,255,255,0.8);
    border-radius: 50%;
    padding: 4px;
  }

  /* FLASH SALE */
  .flash-sale-banner {
    background: #ff2556; /* Vibrant Shopee red */
    color: white;
    display: flex;
    padding: 2px 8px; /* Heavily reduced from 6px 12px */
    justify-content: space-between;
    align-items: center;
    position: relative;
    overflow: hidden;
  }

  /* Lightning bolt decoration in background like image */
  .flash-sale-banner::after {
    content: '';
    position: absolute;
    right: 20%;
    top: -20%;
    width: 100px;
    height: 100px;
    background: white;
    opacity: 0.1;
    clip-path: polygon(40% 0%, 40% 45%, 100% 45%, 60% 100%, 60% 55%, 0% 55%);
    transform: rotate(15deg);
  }

  .fs-left { flex: 1; z-index: 1; }
  .discount-percent {
    background: white;
    color: #ff2556;
    border: 1px solid #ff2556;
    width: max-content;
    padding: 0 4px;
    font-size: 11px;
    font-weight: 800;
    border-radius: 2px;
  }

  .freeship-fomo {
    background: #00bfa5; /* Free ship green */
    color: white;
    font-size: 10px;
    font-weight: 900;
    padding: 0 4px;
    border-radius: 2px;
    display: flex;
    align-items: center;
    gap: 2px;
    height: 16px;
    line-height: normal;
  }

  .price-container {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: -2px;
  }

  .price-label { font-size: 13px; color: white; margin-right: 2px; }
  .price-value { font-size: 20px; font-weight: 800; } /* Reduced from 22px */

  .original-price {
    font-size: 11px;
    text-decoration: line-through;
    color: rgba(255,255,255,0.8);
    margin-top: -4px;
  }

  .today-only {
    font-size: 10px;
    color: #ffeb3b; /* FOMO Yellow */
    font-weight: 700;
    margin-top: -4px;
    letter-spacing: -0.2px;
  }

  .fs-right { 
    text-align: right; 
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }
  .fs-title {
    display: flex;
    align-items: center;
    gap: 4px;
    font-weight: 900;
    font-size: 16px; /* Reduced from 18px */
    margin-bottom: -2px;
  }

  .fs-countdown {
    margin-top: 0px; /* Reduced from 2px */
    font-size: 11px; /* Reduced from 12px */
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .time-box {
    display: flex;
    gap: 1px;
    font-size: 12px;
    font-weight: 400;
  }

  /* CONTENT AREA */
  .product-details-content {
    background: white;
    padding: 2px 8px; /* Heavily reduced from 10px 12px */
  }

  .paylater-bar {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 0; /* Reduced from 10px */
    font-size: 13px; /* Reduced from 13.5px */
    color: #333;
  }

  .paylater-bar .text { font-weight: 400; }
  .paylater-bar .limit { 
    color: #ee4d2d; 
    margin-left: 2px; 
    padding-left: 8px;
    border-left: 1px solid #eee;
  }

  .vouchers-outer {
    display: flex;
    align-items: center;
    position: relative;
    padding: 2px 0; /* Reduced from 4px */
    margin: 0 -8px; /* Pull to exactly match parent padding 8px */
    padding: 2px 8px;
  }

  .vouchers-container {
    flex: 1;
    overflow: hidden;
    position: relative;
  }

  .vouchers-list {
    display: flex;
    gap: 6px; 
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    scrollbar-width: none;
    padding: 2px 0;
  }
  .vouchers-list::-webkit-scrollbar { display: none; }

  .scroll-btn {
    background: rgba(255, 255, 255, 0.4); /* Light and transparent */
    backdrop-filter: blur(4px); /* Glassmorphism effect */
    -webkit-backdrop-filter: blur(4px);
    border: none; /* Remove border/outline */
    color: #444;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    z-index: 10;
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  }

  .scroll-btn.prev { left: 4px; }
  .scroll-btn.next { right: 4px; }

  .ticket-wrapper {
    filter: drop-shadow(0 1px 2px rgba(255, 37, 86, 0.03));
    flex-shrink: 0;
  }

  .ticket {
    background: #fff5f7;
    border: 0.5px solid #ffccd5;
    padding: 1px 8px; /* Reduced padding from 2px 10px */
    border-radius: 4px;
    position: relative;
    /* Create cutout holes using radial-gradient masking */
    mask-image: 
      radial-gradient(circle at 0 50%, transparent 3px, black 3.5px),
      radial-gradient(circle at 100% 50%, transparent 3px, black 4.5px);
    mask-composite: intersect;
    -webkit-mask-image: 
      radial-gradient(circle at 0 50%, transparent 3px, black 3.5px),
      radial-gradient(circle at 100% 50%, transparent 3px, black 4.5px);
    -webkit-mask-composite: source-in; 
    transition: all 0.2s ease;
  }

  /* Internal dashed line effect like image */
  .ticket::before {
    content: '';
    position: absolute;
    left: 6px; /* Reduced from 8px */
    top: 3px;
    bottom: 3px;
    width: 0.5px;
    border-left: 1px dashed #ee4d2d;
    opacity: 0.3;
  }

  .ticket-content {
    display: flex;
    flex-direction: column;
    padding-left: 2px;
  }

  .ticket-content .main {
    color: #ee4d2d;
    font-size: 11px; /* Reduced from 13px */
    font-weight: 700;
  }

  .ticket-content .sub {
    color: #758ca3;
    font-size: 8.5px; /* Reduced from 10px */
    font-weight: 500;
    text-transform: uppercase;
  }

  .ticket.active {
    border-color: #ee4d2d;
    background: #fff4f1;
  }

  .selected-badge {
    position: absolute;
    top: -3px;
    right: -3px;
    background: #ee4d2d;
    border-radius: 50%;
    width: 11px; /* Reduced from 14px */
    height: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid white;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  }

  .product-stats-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 4px;
  }

  .rating-box {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .scoreText {
    font-size: 13px;
    font-weight: 700;
    color: #ee4d2d;
    text-decoration: underline;
  }

  .stars {
    display: flex;
    gap: 1px;
  }

  .divider {
    width: 1px;
    height: 10px;
    background: #dbdbdb;
  }

  .sold-count {
    font-size: 12px;
    color: #222;
  }

  .trust-badge {
    margin-left: auto;
    background: #d0011b;
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 0 4px;
    border-radius: 2px;
    text-transform: uppercase;
  }

  .title-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-top: 0px; /* Zero top margin */
  }

  .product-title {
    font-size: 15.5px; /* Slightly smaller for density */
    font-weight: 400;
    color: #000;
    line-height: 1.25; /* Tighter line height */
    flex: 1;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .bookmark-btn {
    background: transparent;
    border: none;
    color: #000;
    padding: 0;
    display: flex;
    align-items: flex-start;
  }

  .sold-info {
    margin-top: 2px; /* Reduced from 4px */
    font-size: 11.5px; /* Slightly smaller */
    color: #666;
  }
</style>
