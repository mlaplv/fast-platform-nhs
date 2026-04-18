<!-- MobileBannerCarousel.svelte -->
<!-- Hero banner với autoplay, dot indicators và Mall Day badge -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  import type { Product, Banner as BannerType } from '$lib/types';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { Gift, Package, TrendingUp, Star } from 'lucide-svelte';

  interface Props {
    banners: BannerType[];
    products: Product[];
  }

  let { banners, products }: Props = $props();

  // Elite V3.1: Hiển thị toàn bộ banner tại vị trí home_main dưới dạng Carousel
  const homeBanners = $derived(banners?.filter(b => b.position === 'home_main') || []);
  
  // Elite 2026: Mapping Banner with Product Data
  const bannerData = $derived(homeBanners.map(banner => {
    // Tìm sản phẩm dựa trên slug trong link_url
    const slug = banner.link_url?.replace(/^\//, '') || '';
    const product = products.find(p => p.slug === slug || p.id === slug);
    
    if (!product) return { banner, product: null };

    // Lấy variant đầu tiên hoặc mặc định để lấy combo/gifts
    const variant = product.variants?.[0];
    const comboQty = variant?.attributes?.combo_qty || variant?.attributes?.comboQty || 0;
    const gifts = variant?.attributes?.gifts || [];
    
    return {
      banner,
      product,
      comboQty,
      gifts,
      price: product.discountPrice || product.price,
      oldPrice: product.discountPrice ? product.price : null,
      rating: product.metadata?.rating || '5.0',
      soldText: product.order_count_text || 'Đang hot'
    };
  }));

  let currentIndex = $state(0);
  let carouselRef: HTMLElement | undefined = $state();

  // Autoplay Logic (Elite 2026 Smooth Transition)
  onMount(() => {
    if (!browser || homeBanners.length <= 1) return;

    const interval = setInterval(() => {
      if (!carouselRef) return;
      const next = (currentIndex + 1) % homeBanners.length;
      const scrollLeft = next * carouselRef.offsetWidth;
      carouselRef.scrollTo({ left: scrollLeft, behavior: 'smooth' });
    }, 5000); // Tăng lên 5s để sếp kịp nhìn combo xịn

    return () => clearInterval(interval);
  });

  function handleScroll(e: Event) {
    if (!carouselRef) return;
    const scrollLeft = (e.target as HTMLElement).scrollLeft;
    const width = carouselRef.offsetWidth;
    currentIndex = Math.round(scrollLeft / width);
  }

  function getProductLink(url?: string | null) {
    if (!url) return '#';
    if (url.startsWith('http') || url.startsWith('/')) return url;
    return `/${url}`;
  }

  const today = new Date();
  const dateStr = `${today.getDate()} Tháng ${today.getMonth() + 1}`;
</script>

<div class="banner-carousel-root shadow-sm">
  <div 
    class="banner-track scroll-smooth" 
    bind:this={carouselRef}
    onscroll={handleScroll}
  >
    {#each bannerData as item, i}
      <a href={getProductLink(item.banner.link_url)} class="banner-slide">
        <img
          src={item.banner.image_url}
          alt={item.banner.title || "Banner"}
          class="w-full h-full object-cover select-none"
          loading={i === 0 ? "eager" : "lazy"}
        />

        <!-- VIRAL 2026: LIQUID GLASS OVERLAY -->
        {#if item.product}
          <div class="banner-overlay-content">
            <!-- Top Badges -->
            <div class="overlay-top-row">
              <div class="badge-fomo badge-viewing">
                <span class="dot-pulse"></span>
                {Math.floor(Math.random() * 500) + 100} ĐANG XEM
              </div>
              <div class="badge-fomo badge-scarcity">🔥 HÀNG SẮP HẾT</div>
            </div>

            <div class="spacer"></div>

            <!-- Bottom Info Card -->
            <div class="info-glass-card">
              <div class="price-row">
                <span class="currency">₫</span>
                <span class="price-value">{item.price?.toLocaleString('vi-VN')}</span>
                {#if item.oldPrice}
                  <span class="old-price">₫{item.oldPrice.toLocaleString('vi-VN')}</span>
                {/if}
              </div>

              <h3 class="banner-product-title">{item.banner.title || item.product.name}</h3>

              <!-- Combo & Rating Row -->
              <div class="meta-row">
                <div class="rating-box">
                  <Star size={10} fill="currentColor" />
                  <span>{item.rating}</span>
                  <span class="sep">|</span>
                  <span>{item.soldText}</span>
                </div>
                
                {#if item.comboQty > 1}
                  <div class="combo-pill">
                    <Package size={10} />
                    COMBO X{item.comboQty}
                  </div>
                {/if}
              </div>

              <!-- Gifts (Mini horizontal list) -->
              {#if item.gifts.length > 0}
                <div class="gifts-preview">
                  <div class="gift-icon-wrap">
                    <Gift size={12} class="text-[#ee4d2d]" />
                  </div>
                  <div class="gifts-tags">
                    {#each item.gifts.slice(0, 2) as gift}
                      <span class="gift-tag">+{gift.name}</span>
                    {/each}
                    {#if item.gifts.length > 2}
                      <span class="gift-tag">+{item.gifts.length - 2} quà khác</span>
                    {/if}
                  </div>
                </div>
              {/if}

              <!-- CTA -->
              <div class="cta-mini-row">
                <div class="cta-button">
                  XEM CHI TIẾT
                  <TrendingUp size={12} class="ml-1" />
                </div>
                <div class="cta-shipping">⚡ FREESHIP HỎA TỐC</div>
              </div>
            </div>
          </div>
        {/if}
      </a>
    {/each}

    {#if homeBanners.length === 0}
      <div class="banner-slide bg-gray-100 flex items-center justify-center">
        <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Đang cập nhật khuyến mãi...</span>
      </div>
    {/if}
  </div>

  <!-- Mall Day badge (Top Left fixed if needed, or inside slide) -->
  {#if homeBanners.length > 0}
    <div class="banner-badge-row">
      <div class="badge-mall-day">Ngày Hội Mall ⚡</div>
      <div class="badge-date">{dateStr}</div>
    </div>

    <!-- Dot Indicators -->
    <div class="banner-dots">
      {#each homeBanners as _, i}
        <div class="banner-dot {currentIndex === i ? 'banner-dot--active' : ''}"></div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .banner-carousel-root {
    position: relative;
    width: 100%;
    height: 400px; /* Tăng chiều cao để hiển thị Premium Banner Content */
    overflow: hidden;
    background: #000;
  }

  .banner-track {
    display: flex;
    width: 100%;
    height: 100%;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .banner-track::-webkit-scrollbar {
    display: none;
  }

  .banner-slide {
    position: relative;
    flex: 0 0 100%;
    width: 100%;
    height: 100%;
    scroll-snap-align: start;
    display: block;
    outline: none;
  }

  /* LIQUID GLASS OVERLAY CSS */
  .banner-overlay-content {
    position: absolute;
    inset: 0;
    padding: 60px 16px 40px 16px;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.4) 100%);
    pointer-events: none;
  }

  .spacer { flex: 1; }

  .overlay-top-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    z-index: 5;
  }

  .badge-fomo {
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 900;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    gap: 6px;
    letter-spacing: 0.5px;
  }

  .badge-viewing {
    background: rgba(0, 0, 0, 0.5);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .badge-scarcity {
    background: rgba(255, 215, 0, 0.85);
    color: #d0011b;
    box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
  }

  .dot-pulse {
    width: 6px;
    height: 6px;
    background: #ff4d4d;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
  }

  @keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.5; }
    100% { transform: scale(1); opacity: 1; }
  }

  .info-glass-card {
    background: rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border-radius: 16px;
    padding: 16px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    transform: translateY(10px);
    animation: fadeInUp 0.5s forwards ease-out;
  }

  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .price-row {
    display: flex;
    align-items: baseline;
    gap: 4px;
    color: #fff;
    margin-bottom: 2px;
  }

  .currency { font-size: 16px; font-weight: 900; text-decoration: underline; }
  .price-value { font-size: 32px; font-weight: 900; letter-spacing: -1px; }
  .old-price { 
    font-size: 14px; 
    color: rgba(255,255,255,0.4); 
    text-decoration: line-through;
    margin-left: 6px;
  }

  .banner-product-title {
    font-size: 20px;
    font-weight: 900;
    color: #fff;
    text-transform: uppercase;
    margin-bottom: 8px;
    line-height:1.2;
    background: linear-gradient(90deg, #fff, rgba(255,255,255,0.7));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .meta-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }

  .rating-box {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #ffb800;
    font-size: 11px;
    font-weight: 800;
  }
  .rating-box .sep { color: rgba(255,255,255,0.2); }
  .rating-box span:last-child { color: rgba(255,255,255,0.7); }

  .combo-pill {
    background: #d0011b;
    color: #fff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 900;
    display: flex;
    align-items: center;
    gap: 4px;
    box-shadow: 0 4px 10px rgba(208, 1, 27, 0.3);
  }

  .gifts-preview {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.1);
    padding: 6px 10px;
    border-radius: 8px;
    margin-bottom: 12px;
  }

  .gift-icon-wrap {
    width: 24px;
    height: 24px;
    background: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .gifts-tags { display: flex; flex-wrap: wrap; gap: 4px; }
  .gift-tag {
    font-size: 10px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    white-space: nowrap;
  }

  .cta-mini-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .cta-button {
    background: #fff;
    color: #000;
    padding: 8px 16px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 900;
    display: flex;
    align-items: center;
    pointer-events: auto;
  }

  .cta-shipping {
    font-size: 10px;
    font-weight: 900;
    color: #00ffcc;
    text-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
  }

  /* REST OF STYLES */
  .banner-badge-row {
    position: absolute;
    top: 16px;
    left: 16px;
    display: flex;
    align-items: center;
    gap: 6px;
    pointer-events: none;
    z-index: 10;
  }

  .badge-mall-day {
    background: linear-gradient(135deg, #C18F7E 0%, #E3B5A4 100%);
    color: #fff;
    font-size: 10px;
    font-weight: 900;
    padding: 3px 10px;
    border-radius: 20px;
    font-style: italic;
    box-shadow: 0 4px 12px rgba(193, 143, 126, 0.35);
    white-space: nowrap;
  }

  .badge-date {
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    white-space: nowrap;
  }

  .banner-dots {
    position: absolute;
    bottom: 12px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 5px;
    z-index: 10;
    pointer-events: none;
  }

  .banner-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.4);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .banner-dot--active {
    width: 14px;
    height: 4px;
    border-radius: 4px;
    background: #ffffff;
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
  }
</style>

