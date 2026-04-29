<!-- MobileFlashSale.svelte -->
<!-- Flash Sale section: title, FOMO badge, live countdown, horizontal scroll deals -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { slugify, formatCurrency } from '$lib/utils/format';

  import type { Product } from '$lib/types';

  interface Props {
    products: Product[];
  }

  let { products = [] }: Props = $props();

  // Elite 2.2: Sort and compute Max Discount for Header
  const flashDeals = $derived(
    products
      .filter(p => {
        const dPrice = p.discountPrice || 0;
        const oPrice = p.price || 0;
        return dPrice > 0 && dPrice < oPrice;
      })
      .map((p) => {
        const dPrice = p.discountPrice!;
        const oPrice = p.price;
        const discountPct = (oPrice - dPrice) / oPrice;
        
        return {
          ...p,
          finalPrice: dPrice,
          oldPrice: oPrice,
          discountPct,
          discountLabel: Math.round(discountPct * 100),
          image: p.images?.[0] || '',
          // R00 Compliance: Use boosted orderCount for real-time FOMO
          soldCount: p.orderCount || p.order_count || 0,
          soldText: p.orderCountText || p.order_count_text || p.metadata?.reviews_count_text || '0', 
          isHot: (p.metadata?.scarcity_seconds || 0) > 0 || (p.discountPrice && p.discountPrice / p.price < 0.5) || (p.orderCount || 0) > 100,
          isFreeShip: p.metadata?.is_freeship !== false,
          progress: Math.min(95, Math.max(20, (p.orderCount || 0) % 100))
        };
      })
      .sort((a, b) => b.discountPct - a.discountPct)
  );

  const maxDiscount = $derived(
    flashDeals.length > 0 ? Math.max(...flashDeals.map(d => d.discountLabel)) : 0
  );

  // Countdown: init 15h57m17s
  let seconds = $state(15 * 3600 + 57 * 60 + 17);
  let timer: ReturnType<typeof setInterval>;

  const hh = $derived(String(Math.floor(seconds / 3600)).padStart(2, '0'));
  const mm = $derived(String(Math.floor((seconds % 3600) / 60)).padStart(2, '0'));
  const ss = $derived(String(seconds % 60).padStart(2, '0'));

  function getDiscountPct(deal: Product): number {
    const dp = deal.discountPrice || 0;
    const p = deal.price || 0;
    if (!dp || !p || dp >= p) return 0;
    return Math.round((1 - dp / p) * 100);
  }

  function navigateProduct(deal: Product): void {
    goto(`/${deal.slug || deal.id}`);
  }

  onMount(() => {
    timer = setInterval(() => {
      if (seconds > 0) seconds--;
    }, 1000);
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });
</script>

<div class="flash-sale-wrapper">
  <!-- Header row -->
  <div class="flash-sale-header">
    <div class="flash-sale-title-group">
      <div class="flash-sale-title">
        <span class="title-f">F</span>
        <svg class="lightning pulse-fast" viewBox="0 0 24 24" fill="#ff2b54">
          <path d="M13 2L4 14h7l-1 8 9-12h-7z"/>
        </svg>
        <span class="title-rest">ash Sale</span>
      </div>
      {#if maxDiscount > 0}
        <span class="flash-fomo-badge fomo-pulse">Bấm Săn Deal - {maxDiscount}%</span>
      {/if}
    </div>

    <!-- Countdown -->
    <div class="flash-countdown">
      <span class="time-block">{hh}</span>
      <span class="time-sep">:</span>
      <span class="time-block">{mm}</span>
      <span class="time-sep">:</span>
      <span class="time-block">{ss}</span>
    </div>
  </div>

  <!-- Horizontal scroll deals -->
  <div class="flash-deals-track">
    {#each flashDeals as deal}
      {@const discountPct = getDiscountPct(deal)}
      <button
        class="flash-deal-card"
        onclick={() => navigateProduct(deal)}
      >
        <div class="deal-img-wrap">
          <!-- Badges -->
          {#if deal.isBestSale}
            <span class="badge-bestsale">BESTSALE</span>
          {/if}
          {#if deal.isFreeShip}
            <span class="badge-freeship">FREE SHIP</span>
          {/if}
          
          {#if discountPct > 0}
            <div class="discount-sticker">
              <span class="discount-num">-{discountPct}%</span>
            </div>
          {/if}

          <!-- Image -->
          <img
            src={deal.image}
            alt={deal.name}
            class="deal-img"
            loading="lazy"
          />

          <!-- Progress Pill Overlapping Bottom of Image -->
          <div class="progress-wrap">
            <div class="progress-fill" style="width: {deal.progress}%"></div>
            <span class="progress-text {deal.isHot ? 'fomo-pulse' : ''}">
              {#if deal.isHot && deal.progress > 80}
                🔥 Sắp cháy hàng
              {:else}
                Đã bán {deal.soldText}
              {/if}
            </span>
          </div>
        </div>

        <!-- Prices -->
        <div class="price-info">
          <span class="current-price">
            {formatCurrency(deal.finalPrice)}
          </span>
          {#if deal.oldPrice}
            <div class="old-price">
              {formatCurrency(deal.oldPrice)}
            </div>
          {/if}
        </div>
      </button>
    {/each}
  </div>
</div>

<style>
  .flash-sale-wrapper {
    background: linear-gradient(135deg, #FFF5F0 0%, #FEEAE0 100%);
    padding-top: 12px;
    margin-top: 6px;
    overflow: hidden;
  }

  .flash-sale-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 14px 10px;
  }

  .flash-sale-title-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .flash-sale-title {
    display: flex;
    align-items: center;
  }

  .title-f, .title-rest {
    font-size: 22px;
    font-weight: 900;
    color: #111;
  }

  .lightning {
    width: 15px;
    height: 15px;
    margin: 0 -2px;
    flex-shrink: 0;
    filter: drop-shadow(0 2px 4px rgba(255, 43, 84, 0.4));
  }

  .flash-fomo-badge {
    background: linear-gradient(90deg, #ff2b54, #ff5e83);
    color: #fff;
    font-size: 10px;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 999px; /* Pill shape */
    line-height: 1.4;
    white-space: nowrap;
    box-shadow: 0 3px 8px rgba(255, 43, 84, 0.25);
  }

  .flash-countdown {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .time-block {
    background: #C18F7E;
    color: #fff;
    font-size: 12px;
    font-weight: 800;
    padding: 3px 4px;
    border-radius: 4px;
    min-width: 24px;
    text-align: center;
    line-height: 1.2;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }

  .time-sep {
    color: #C18F7E;
    font-weight: 900;
    font-size: 12px;
    line-height: 1;
    margin: 0 -2px;
  }

  /* Horizontal scroll track */
  .flash-deals-track {
    display: flex;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    gap: 4px; /* Standardized high-density gap */
    padding: 0 8px 16px;
  }
  .flash-deals-track::-webkit-scrollbar { display: none; }

  .flash-deal-card {
    flex-shrink: 0;
    width: 115px; /* Increased width for airy feel */
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); /* Softer shadow */
    border-radius: 12px; /* Smoother corners */
    cursor: pointer;
    padding: 0;
    padding-bottom: 8px;
  }
  .flash-deal-card:active { opacity: 0.95; }

  .deal-img-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
    border-radius: 8px 8px 0 0;
    overflow: hidden; /* Changed from just relative */
    /* Add slight bottom padding inside wrap to make room for pill if desired, or let pill overlay */
  }

  .badge-bestsale {
    position: absolute;
    top: 6px;
    left: -4px; /* Overflow slightly or just flush */
    background: linear-gradient(135deg, #ff2b54, #ff5778);
    color: #fff;
    font-size: 8px;
    font-weight: 900;
    padding: 2px 6px;
    border-radius: 4px;
    z-index: var(--z-flash-sale);
    box-shadow: 2px 2px 6px rgba(255, 43, 84, 0.4);
  }

  .badge-freeship {
    position: absolute;
    top: 6px;
    right: -2px;
    background: #00c49a;
    color: #fff;
    font-size: 8px;
    font-weight: 900;
    padding: 2px 4px;
    border-radius: 4px 0 0 4px;
    z-index: 3;
    letter-spacing: -0.2px;
  }

  .discount-sticker {
    position: absolute;
    top: 26px; /* Below Free Ship / Bestsale if they overlap */
    right: 0;
    background: linear-gradient(135deg, #ffd839, #ffbe0b);
    color: #ff2b54;
    font-size: 10px;
    font-weight: 900;
    padding: 2px 5px;
    border-radius: 4px 0 0 4px;
    z-index: var(--z-flash-sale);
    box-shadow: -2px 2px 6px rgba(0,0,0,0.1);
  }

  .discount-num {
    display: block;
    line-height: 1;
  }

  .deal-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    background: #fff;
  }

  .progress-wrap {
    position: absolute;
    bottom: 6px;
    left: 6px;
    right: 6px;
    height: 14px;
    background: #F5E0D8;
    border-radius: 999px;
    overflow: hidden;
    /* Soft white outer shadow to push away from image */
    box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
    z-index: var(--z-base);
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #C18F7E, #E3B5A4);
    border-radius: 999px;
    transition: width 0.3s ease;
  }

  .progress-text {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 9px;
    font-weight: 800;
    white-space: nowrap;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
    pointer-events: none;
    padding: 0 4px;
    letter-spacing: -0.2px;
  }

  .price-info {
    display: flex;
    flex-direction: row;
    align-items: baseline;
    justify-content: center;
    gap: 3px;
    margin-top: 6px;
    padding: 0 4px;
  }

  .current-price {
    font-size: 15px;
    font-weight: 900;
    color: #ee4d2d;
    line-height: 1;
    letter-spacing: -0.4px;
  }

  .unit {
    font-size: 9px;
    font-weight: 800;
    margin-left: 1px;
    text-decoration: underline;
  }

  .old-price {
    font-size: 10.5px;
    font-weight: 600;
    color: #bbb;
    text-decoration: line-through;
    opacity: 0.9;
  }

  /* FOMO Animations */
  @keyframes pulse-fast {
    0%, 100% { filter: drop-shadow(0 0 2px #ff2b54); transform: scale(1); }
    50% { filter: drop-shadow(0 0 8px #ff2b54); transform: scale(1.1); }
  }
  .pulse-fast {
    animation: pulse-fast 1s infinite;
  }

  @keyframes fomo-glow {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.8; transform: scale(1.02); }
  }
  .fomo-pulse {
    animation: fomo-glow 0.8s infinite;
  }
</style>
