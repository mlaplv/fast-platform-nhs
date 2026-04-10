<!-- MobileFlashSale.svelte -->
<!-- Flash Sale section: title, FOMO badge, live countdown, horizontal scroll deals -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
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
    originalPrice: number;
    image: string;
    sold: number;
    isHot: boolean;
    isFreeShip: boolean;
    isBestSale: boolean;
  }

  const deals: Deal[] = Array.from({ length: 12 }).map((_, i) => ({
    id: i,
    name: `Siêu phẩm ${i + 1}`,
    price: 86621 + i * 12345,
    originalPrice: 577473 - i * 32154,
    image: `/uploads/img/micsmo${dealImages[i % dealImages.length]}`,
    sold: 40 + i * 5,
    isHot: i % 3 === 0,
    isFreeShip: true,
    isBestSale: i % 4 === 0,
  }));

  // Countdown: init 15h57m17s
  let seconds = $state(15 * 3600 + 57 * 60 + 17);
  let timer: ReturnType<typeof setInterval>;

  const hh = $derived(String(Math.floor(seconds / 3600)).padStart(2, '0'));
  const mm = $derived(String(Math.floor((seconds % 3600) / 60)).padStart(2, '0'));
  const ss = $derived(String(seconds % 60).padStart(2, '0'));

  function getDiscountPct(deal: Deal): number {
    if (!deal.originalPrice || deal.originalPrice <= deal.price) return 0;
    return Math.round((1 - deal.price / deal.originalPrice) * 100);
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
      <span class="flash-fomo-badge">Bấm Săn Deal - 70%</span>
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
      {@const discountPct = getDiscountPct(deal)}
      <button
        class="flash-deal-card"
        onclick={() => goto(`/${slugify(deal.name)}`)}
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
            <div class="progress-fill" style="width: {deal.isHot ? 88 : Math.min(85, deal.sold)}%"></div>
            <span class="progress-text {deal.isHot ? 'fomo-pulse' : ''}">
              {#if deal.isHot}
                🔥 Sắp hết
              {:else}
                Đã bán {deal.sold}
              {/if}
            </span>
          </div>
        </div>

        <!-- Prices -->
        <div class="price-info">
          <div class="current-price">
            {deal.price.toLocaleString('vi-VN')}<span class="unit">đ</span>
          </div>
          <div class="old-price">
            {deal.originalPrice.toLocaleString('vi-VN')}đ
          </div>
        </div>
      </button>
    {/each}
  </div>
</div>

<style>
  .flash-sale-wrapper {
    /* Soft gradient matching image 3 (purpleish top-left fading to cyan-blue) */
    background: linear-gradient(135deg, #eaddff 0%, #d4ebff 100%);
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
    background: #46464a; /* Dark gray */
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
    color: #333;
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
    gap: 4px; /* Tối đa hóa khoảng cách ngắn */
    padding: 0 8px 18px;
  }
  .flash-deals-track::-webkit-scrollbar { display: none; }

  .flash-deal-card {
    flex-shrink: 0;
    width: 88px; /* Tăng số lượng item hiển thị cùng lúc */
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    border-radius: 8px;
    cursor: pointer;
    padding: 0;
    padding-bottom: 6px;
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
    z-index: 3;
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
    z-index: 4;
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
    bottom: 4px;
    left: 4px;
    right: 4px;
    height: 16px;
    background: #ffdce3; /* Unfilled light pink */
    border-radius: 999px;
    overflow: hidden;
    /* Soft white outer shadow to push away from image */
    box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
    z-index: 2;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #ff2b54, #ff5778);
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
    font-weight: 700;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
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
    font-size: 13px;
    font-weight: 900;
    color: #ff2b54;
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
    font-size: 8.5px;
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
