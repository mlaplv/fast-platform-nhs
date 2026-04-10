<!-- MobileFlashSale.svelte -->
<!-- Flash Sale section: title, FOMO badge, live countdown, horizontal scroll deals -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';

  const dealImages: string[] = [
    '/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-CREAM-60g-Kem-Duong-Nhau-Thai-Lam-Sang-amp-Cap-Am-Diu-Nhe_33.1.png',
    '/Hurry-Harry-Medicated-Beauty-Wrinkle-Serum-Rich-jpeg.jpg',
    '/MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-ESSENCE-180ml-TINH-CHAT-CAP-AM-LAM-DIU-DA_. (14.1).png',
    '/-MICCOSMO-WHITE-LABEL-PREMIUM-PLACENTA-PACK-130g-Mat-na-u-duong-trang-sang-da-tu-nhau-thai_23.png',
  ];

  interface Deal {
    id: number;
    name: string;
    price: number;
    discount: number;
    image: string;
    sold: number;
    isHot: boolean;
  }

  const deals: Deal[] = Array.from({ length: 5 }).map((_, i) => ({
    id: i,
    name: `Siêu phẩm ${i + 1}`,
    price: 87888 + i * 15000,
    discount: 85 - i * 5,
    image: `/uploads/img/micsmo${dealImages[i % dealImages.length]}`,
    sold: 40 + i * 10,
    isHot: i === 0,
  }));

  // Countdown: init 17h44m43s
  let seconds = $state(17 * 3600 + 44 * 60 + 43);
  let timer: ReturnType<typeof setInterval>;

  const hh = $derived(String(Math.floor(seconds / 3600)).padStart(2, '0'));
  const mm = $derived(String(Math.floor((seconds % 3600) / 60)).padStart(2, '0'));
  const ss = $derived(String(seconds % 60).padStart(2, '0'));

  onMount(() => {
    timer = setInterval(() => {
      if (seconds > 0) seconds--;
    }, 1000);
    return () => clearInterval(timer);
  });
</script>

<div class="flash-sale-section">
  <!-- Header row -->
  <div class="flash-sale-header">
    <div class="flash-sale-title-group">
      <!-- Title text "Flash Sale" kiểu TikTok có lightning bolt -->
      <div class="flash-sale-title">
        <span class="title-f">F</span>
        <svg class="lightning" viewBox="0 0 24 24" fill="#ee4d2d">
          <path d="M13 2L4 14h7l-1 8 9-12h-7z"/>
        </svg>
        <span class="title-rest">ash Sale</span>
      </div>
      <span class="flash-fomo-badge">Bắm Săn Deal - 70%</span>
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
    {#each deals as deal}
      <button
        class="flash-deal-card"
        onclick={() => goto(`/${slugify(deal.name)}`)}
      >
        <div class="deal-img-wrap">
          {#if deal.isHot}
            <span class="deal-hot-badge">Hot</span>
          {/if}
          <div class="deal-discount-bar">{deal.discount}%</div>
          <img
            src={deal.image}
            alt={deal.name}
            class="deal-img"
            loading="lazy"
          />
        </div>
        <p class="deal-price">
          <span class="deal-price-unit">đ</span>{deal.price.toLocaleString('vi-VN')}
        </p>
        <!-- Sold progress -->
        <div class="deal-progress-wrap">
          <div class="deal-progress-bar" style="width: {Math.min(deal.sold, 90)}%"></div>
          <span class="deal-progress-label">Đã bán {deal.sold}</span>
        </div>
      </button>
    {/each}
  </div>
</div>

<style>
  .flash-sale-section {
    background: #ffffff;
    margin-top: 6px;
    overflow: hidden;
  }

  .flash-sale-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 12px 10px;
  }

  .flash-sale-title-group {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .flash-sale-title {
    display: flex;
    align-items: center;
  }

  .title-f {
    font-size: 20px;
    font-weight: 900;
    color: #ee4d2d;
    font-style: italic;
    line-height: 1;
  }

  .lightning {
    width: 14px;
    height: 14px;
    margin: 0 -1px;
    flex-shrink: 0;
  }

  .title-rest {
    font-size: 20px;
    font-weight: 900;
    color: #ee4d2d;
    font-style: italic;
    line-height: 1;
  }

  .flash-fomo-badge {
    background: #ee4d2d;
    color: #fff;
    font-size: 9px;
    font-weight: 900;
    padding: 3px 6px;
    border-radius: 3px;
    line-height: 1.2;
    white-space: nowrap;
  }

  .flash-countdown {
    display: flex;
    align-items: center;
    gap: 3px;
  }

  .time-block {
    background: #1a1a1a;
    color: #fff;
    font-size: 13px;
    font-weight: 900;
    font-family: 'Courier New', monospace;
    padding: 3px 6px;
    border-radius: 3px;
    min-width: 26px;
    text-align: center;
    line-height: 1;
  }

  .time-sep {
    color: #ee4d2d;
    font-weight: 900;
    font-size: 14px;
    line-height: 1;
  }

  /* Horizontal scroll track */
  .flash-deals-track {
    display: flex;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    gap: 8px;
    padding: 0 12px 12px;
  }
  .flash-deals-track::-webkit-scrollbar { display: none; }

  .flash-deal-card {
    flex-shrink: 0;
    width: 110px;
    display: flex;
    flex-direction: column;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    text-align: center;
  }
  .flash-deal-card:active { opacity: 0.8; }

  .deal-img-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 1 / 1;
    background: #f5f5f5;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 6px;
  }

  .deal-hot-badge {
    position: absolute;
    top: 6px;
    left: 6px;
    background: #ee4d2d;
    color: #fff;
    font-size: 9px;
    font-weight: 900;
    padding: 2px 5px;
    z-index: 2;
    border-radius: 2px;
  }

  .deal-discount-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(90deg, #ee4d2d, #ff8c00);
    color: #fff;
    font-size: 11px;
    font-weight: 900;
    text-align: center;
    padding: 2px 0;
    z-index: 2;
  }

  .deal-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.4s ease;
  }
  .flash-deal-card:hover .deal-img { transform: scale(1.05); }

  .deal-price {
    font-size: 13px;
    font-weight: 700;
    color: #ee4d2d;
    text-align: center;
    margin: 0;
  }

  .deal-price-unit {
    font-size: 10px;
  }

  .deal-progress-wrap {
    position: relative;
    width: 100%;
    height: 14px;
    background: #ffbda6;
    border-radius: 9999px;
    margin-top: 5px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .deal-progress-bar {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    background: #ee4d2d;
    border-radius: 9999px;
  }

  .deal-progress-label {
    position: relative;
    z-index: 1;
    font-size: 9px;
    font-weight: 700;
    color: #fff;
  }
</style>
