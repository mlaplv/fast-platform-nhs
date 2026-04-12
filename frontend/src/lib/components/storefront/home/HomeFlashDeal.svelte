<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import type { Product } from '$lib/types';
  import { ChevronLeft, ChevronRight } from 'lucide-svelte';

  interface Props {
    products: Product[];
  }

  let { products = [] }: Props = $props();

  // Elite 2.2: Actual Data Sync matching Mobile Logic
  const flashDeals = $derived(
    products
      .filter(p => !!p.discountPrice && p.discountPrice < p.price)
      .map((p, i) => {
        const dPrice = p.discountPrice!;
        const oPrice = p.price;
        const discountPct = (oPrice - dPrice) / oPrice;
        
        return {
          ...p,
          finalPrice: dPrice,
          oldPrice: oPrice,
          discountPct,
          discountLabel: Math.round(discountPct * 100),
          image: p.images?.[0] || '/images/placeholder-product.webp',
          soldCount: parseInt(p.metadata?.sold_count?.toString() || (20 + (i * 5) % 80).toString()),
          isHot: (p.metadata?.scarcity_seconds || 0) > 0 || (p.discountPrice && p.discountPrice / p.price < 0.5),
          progress: 60 + (i * 7) % 35 // High FOMO progress
        };
      })
      .sort((a, b) => b.discountPct - a.discountPct)
  );

  const isFullBanner = $derived(flashDeals.length > 0 && flashDeals.length <= 5);
  const isSlider = $derived(flashDeals.length > 5);

  // Slider controls
  let scrollContainer: HTMLDivElement;
  function scroll(direction: 'left' | 'right') {
    if (!scrollContainer) return;
    const scrollAmount = scrollContainer.clientWidth * 0.8;
    scrollContainer.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth'
    });
  }

  // Countdown: sync with mobile logic (15h57m17s base)
  let seconds = $state(15 * 3600 + 56 * 60 + 59); // Adjusted to match user screenshot state
  let timer: ReturnType<typeof setInterval>;

  const hh = $derived(String(Math.floor(seconds / 3600)).padStart(2, '0'));
  const mm = $derived(String(Math.floor((seconds % 3600) / 60)).padStart(2, '0'));
  const ss = $derived(String(seconds % 60).padStart(2, '0'));

  onMount(() => {
    timer = setInterval(() => {
      if (seconds > 0) seconds--;
    }, 1000);
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });
</script>

<div class="desktop-flash-sale bg-white rounded-sm shadow-[0_1px_4px_rgba(0,0,0,0.1)] overflow-hidden mb-6">
  <div class="flex flex-row items-center justify-between px-5 py-4 border-b border-gray-100">
    <div class="flex items-center gap-4">
      <div class="flex items-center group cursor-default">
        <h2 class="text-2xl font-black text-[#ee4d2d] italic tracking-tighter uppercase flex items-center gap-2">
          <svg class="w-6 h-6 fill-[#ee4d2d] animate-pulse drop-shadow-[0_0_8px_rgba(238,77,45,0.5)]" viewBox="0 0 24 24">
            <path d="M13 2L4 14h7l-1 8 9-12h-7z"/>
          </svg>
          <span class="drop-shadow-sm bg-gradient-to-r from-[#ee4d2d] via-[#ff6a00] to-[#ee4d2d] bg-clip-text text-transparent bg-[length:200%_auto] animate-gradient-flow">GIÁ SỐC HÔM NAY</span>
        </h2>
      </div>

      <!-- Sync Countdown Block -->
      <div class="flex items-center gap-2 ml-4">
        <div class="bg-black text-white px-2 py-1 rounded-md font-bold text-base min-w-[36px] text-center shadow-lg">{hh}</div>
        <span class="font-black text-black text-lg">:</span>
        <div class="bg-black text-white px-2 py-1 rounded-md font-bold text-base min-w-[36px] text-center shadow-lg">{mm}</div>
        <span class="font-black text-black text-lg">:</span>
        <div class="bg-black text-white px-2 py-1 rounded-md font-bold text-base min-w-[36px] text-center shadow-lg">{ss}</div>
      </div>
    </div>
    
    <a href="/deals" class="text-[#ee4d2d] font-medium text-sm hover:opacity-80 flex items-center gap-1 group transition-all">
      Xem tất cả
      <span class="text-xs group-hover:translate-x-1 transition-transform">›</span>
    </a>
  </div>

  <div class="relative group/container">
    {#if isSlider}
      <button 
        onclick={() => scroll('left')}
        class="absolute left-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 bg-white/90 border border-gray-200 rounded-full flex items-center justify-center shadow-xl opacity-0 group-hover/container:opacity-100 transition-opacity hover:bg-white text-[#ee4d2d]"
      >
        <ChevronLeft size={24} />
      </button>

      <button 
        onclick={() => scroll('right')}
        class="absolute right-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 bg-white/90 border border-gray-200 rounded-full flex items-center justify-center shadow-xl opacity-0 group-hover/container:opacity-100 transition-opacity hover:bg-white text-[#ee4d2d]"
      >
        <ChevronRight size={24} />
      </button>
    {/if}

    <div 
      bind:this={scrollContainer}
      class="flash-deals-scroller scroll-smooth no-scrollbar"
      class:is-grid={isFullBanner}
      class:is-slider={isSlider}
    >
      {#each flashDeals as deal}
        <button
          onclick={() => goto(`/${deal.slug || deal.id}`)}
          class="deal-item group {isFullBanner ? 'full-banner-item' : 'slider-item'}"
        >
          <div class="item-media">
            <!-- Discount Sticker: Premium 2-layer -->
            <div class="discount-badge">
              <div class="pct">{deal.discountLabel}%</div>
              <div class="lbl">GIẢM</div>
            </div>
            
            <img 
              src={deal.image} 
              alt={deal.name} 
              class="product-img group-hover:scale-110 transition-transform duration-700" 
              loading="lazy"
            />
            
            <div class="media-overlay"></div>
          </div>

          <div class="item-info">
            <h3 class="product-name">{deal.name}</h3>
            
            <!-- Price Block -->
            <div class="price-container">
              <p class="final-price">
                <span class="currency">₫</span>{deal.finalPrice.toLocaleString('vi-VN')}
              </p>
              {#if deal.oldPrice}
                <p class="old-price">
                  ₫{deal.oldPrice.toLocaleString('vi-VN')}
                </p>
              {/if}
            </div>

            <!-- Enhanced Sold Progress Bar -->
            <div class="sold-progress">
              <div 
                class="progress-bar" 
                style="width: {deal.progress}%"
              >
                <div class="shiver-effect"></div>
              </div>
              <span class="sold-text">
                {#if deal.progress > 85}
                  🔥 SẮP CHÁY HÀNG
                {:else}
                  ĐÃ BÁN {deal.soldCount}{deal.soldCount > 1000 ? '+' : ''}
                {/if}
              </span>
            </div>
          </div>
        </button>
      {/each}

      {#if flashDeals.length === 0}
        <div class="empty-state">
            <svg class="w-16 h-16 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span class="text-lg font-black text-gray-300 uppercase tracking-[0.2em]">Hết phiên Flash Sale</span>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

  .flash-deals-scroller {
    display: flex;
    overflow-x: auto;
    gap: 0;
  }

  .is-grid {
    display: grid;
    /* Adaptive grid: fills the row if products <= 6 */
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    overflow: hidden;
  }

  /* When precisely 5 items or in slider mode, ensure 5 columns on desktop */
  @media (min-width: 1280px) {
    .is-grid {
      grid-template-columns: repeat(5, 1fr);
    }
  }

  /* Item Styles */
  .deal-item {
    padding: 1rem;
    border-right: 1px solid #f3f4f6;
    background: white;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    text-align: left;
    position: relative;
    overflow: hidden;
  }

  .deal-item:last-child {
    border-right: none;
  }

  .deal-item:hover {
    background: rgba(238, 77, 45, 0.02);
    z-index: 10;
  }

  .slider-item {
    flex: 0 0 calc(100% / 5);
    min-width: 220px;
  }

  .full-banner-item {
    /* Auto grid takes care of this */
  }

  .item-media {
    aspect-ratio: 1/1;
    width: 100%;
    position: relative;
    margin-bottom: 1rem;
    overflow: hidden;
    background: #f8f8f8;
  }

  .product-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .media-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.05), transparent);
    opacity: 0;
    transition: opacity 0.3s;
  }

  .deal-item:hover .media-overlay {
    opacity: 1;
  }

  /* Discount Badge matching screenshot */
  .discount-badge {
    position: absolute;
    top: 0;
    right: 0;
    z-index: 10;
    background: #ffd839;
    padding: 0.25rem 0.4rem;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .discount-badge .pct {
    color: #ee4d2d;
    font-size: 0.75rem;
    font-weight: 900;
    line-height: 1;
  }

  .discount-badge .lbl {
    color: white;
    background: #ee4d2d;
    font-size: 0.55rem;
    font-weight: 700;
    padding: 0 0.25rem;
    border-radius: 1px;
    margin-top: 0.1rem;
    text-transform: uppercase;
  }

  .item-info {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .product-name {
    font-size: 0.85rem;
    color: #333;
    line-height: 1.3;
    height: 2.6rem;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    font-weight: 500;
    text-align: center;
    margin-bottom: 0.25rem;
    padding: 0 0.5rem;
    transition: color 0.3s;
  }

  .deal-item:hover .product-name {
    color: #ee4d2d;
  }

  .price-container {
    display: flex;
    flex-direction: row;
    align-items: baseline;
    justify-content: center;
    gap: 0.4rem;
  }

  .final-price {
    color: #ee4d2d;
    font-size: 1.4rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.05em;
  }

  .final-price .currency {
    font-size: 0.8rem;
    text-decoration: underline;
    margin-right: 1px;
    font-weight: 700;
  }

  .old-price {
    color: #bbb;
    font-size: 0.8rem;
    text-decoration: line-through;
    font-weight: 400;
  }

  /* Sold Progress Bar: Elite V2.2 */
  .sold-progress {
    width: 100%;
    height: 1.25rem;
    background: #ffbda6;
    border-radius: 999px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
  }

  .progress-bar {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    background: linear-gradient(90deg, #ee4d2d, #ff6a00);
    border-radius: 999px;
    transition: width 1.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .sold-text {
    position: relative;
    z-index: 10;
    color: white;
    font-size: 10px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    text-shadow: 0 1px 2px rgba(0,0,0,0.2);
  }

  .shiver-effect {
    position: absolute;
    inset: 0;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.4),
      transparent
    );
    width: 50%;
    transform: skewX(-20deg);
    animation: shiver 2.5s infinite linear;
  }

  @keyframes shiver {
    0% { transform: translateX(-150%) skewX(-20deg); }
    100% { transform: translateX(250%) skewX(-20deg); }
  }

  @keyframes gradient-flow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  .animate-gradient-flow {
    animation: gradient-flow 3s ease infinite;
  }

  .empty-state {
    width: 100%;
    padding: 5rem 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    color: #ddd;
  }

  /* Responsive Adjustments */
  @media (max-width: 1024px) {
    .is-grid {
      grid-template-columns: repeat(4, 1fr);
    }
    .slider-item {
      flex: 0 0 calc(100% / 4);
    }
  }

  @media (max-width: 768px) {
    .is-grid {
      grid-template-columns: repeat(2, 1fr);
    }
    .slider-item {
      flex: 0 0 calc(100% / 2);
    }
  }
</style>
