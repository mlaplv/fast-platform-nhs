<!-- MobileBannerCarousel.svelte -->
<!-- Hero banner với autoplay, dot indicators và Mall Day badge -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  interface Banner {
    id: string;
    image_url: string;
    link_url?: string;
    title?: string;
    position?: string;
  }

  interface Props {
    banners: Banner[];
  }

  let { banners }: Props = $props();

  // Elite V3.1: Hiển thị toàn bộ banner tại vị trí home_main dưới dạng Carousel
  const homeBanners = $derived(banners?.filter(b => b.position === 'home_main') || []);
  
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
    }, 4000);

    return () => clearInterval(interval);
  });

  function handleScroll(e: Event) {
    if (!carouselRef) return;
    const scrollLeft = (e.target as HTMLElement).scrollLeft;
    const width = carouselRef.offsetWidth;
    currentIndex = Math.round(scrollLeft / width);
  }

  function getProductLink(url?: string) {
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
    {#each homeBanners as banner}
      <a href={getProductLink(banner.link_url)} class="banner-slide">
        <img
          src={banner.image_url}
          alt={banner.title || "Banner"}
          class="w-full h-full object-cover select-none"
          loading="eager"
        />
      </a>
    {/each}

    {#if homeBanners.length === 0}
      <div class="banner-slide bg-gray-100 flex items-center justify-center">
        <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Đang cập nhật khuyến mãi...</span>
      </div>
    {/if}
  </div>

  <!-- Mall Day badge (Sticky Overlay) -->
  {#if homeBanners.length > 0}
    <div class="banner-badge-row">
      <div class="badge-mall-day">Ngày Hội Mall ⚡</div>
      <div class="badge-date">{dateStr}</div>
    </div>

    <!-- Dot Indicators (Elite Minimalist) -->
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
    height: 185px;
    overflow: hidden;
    background: #f3f3f3;
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
    flex: 0 0 100%;
    width: 100%;
    height: 100%;
    scroll-snap-align: start;
    display: block;
    outline: none;
  }

  .banner-badge-row {
    position: absolute;
    top: 12px;
    left: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    pointer-events: none;
    z-index: 10;
  }

  .badge-mall-day {
    background: linear-gradient(135deg, #ee4d2d 0%, #ff7337 100%);
    color: #fff;
    font-size: 10px;
    font-weight: 900;
    padding: 3px 10px;
    border-radius: 20px;
    font-style: italic;
    box-shadow: 0 4px 12px rgba(238, 77, 45, 0.3);
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
