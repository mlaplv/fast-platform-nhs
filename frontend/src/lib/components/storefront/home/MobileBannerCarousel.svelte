<!-- MobileBannerCarousel.svelte -->
<!-- Hero banner với autoplay, dot indicators và Mall Day badge -->
<script lang="ts">
  import { onMount } from 'svelte';

  interface Banner {
    id: string;
    image_url: string;
    link_url?: string;
    title?: string;
  }

  interface Props {
    banners: Banner[];
  }

  let { banners }: Props = $props();

  // Elite V2.2: Neural Link Intelligence
  function getProductLink(url?: string) {
    if (!url) return '#';
    if (url.startsWith('http') || url.startsWith('/')) return url;
    return `/${url}`;
  }

  const displayBanners = $derived(banners && banners.length > 0 ? banners : []);

  let current = $state(0);
  let timer: ReturnType<typeof setInterval>;

  onMount(() => {
    timer = setInterval(() => {
      current = (current + 1) % displayBanners.length;
    }, 3200);
    return () => clearInterval(timer);
  });
</script>

<div class="banner-carousel">
  <!-- Slide track -->
  <div
    class="banner-track"
    style="transform: translateX(-{current * 100}%)"
  >
    {#each displayBanners as banner, i}
      <a href={getProductLink(banner.link_url)} class="banner-slide">
        <img
          src={banner.image_url}
          alt={banner.title || `Banner ${i + 1}`}
          class="w-full h-full object-cover"
          loading={i === 0 ? 'eager' : 'lazy'}
        />
      </a>
    {/each}
  </div>

  <!-- Mall Day badge (top-left) -->
  <div class="banner-badge-row">
    <span class="badge-mall-day">Ngày Hội Mall ⚡</span>
    <span class="badge-date">{new Date().getDate()} Tháng {new Date().getMonth() + 1}</span>
  </div>

  <!-- Dot indicators (bottom-center) -->
  <div class="banner-dots">
    {#each displayBanners as _, i}
      <button
        class="banner-dot {i === current ? 'banner-dot--active' : ''}"
        onclick={() => current = i}
        aria-label="Slide {i + 1}"
      ></button>
    {/each}
  </div>
</div>

<style>
  .banner-carousel {
    position: relative;
    width: 100%;
    height: 185px;
    overflow: hidden;
    background: #f0f0f0;
  }

  .banner-track {
    display: flex;
    width: 100%;
    height: 100%;
    transition: transform 0.45s ease-out;
  }

  .banner-slide {
    width: 100%;
    height: 100%;
    object-fit: cover;
    flex-shrink: 0;
  }

  .banner-badge-row {
    position: absolute;
    top: 10px;
    left: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .badge-mall-day {
    background: #ee4d2d;
    color: #fff;
    font-size: 11px;
    font-weight: 900;
    padding: 2px 8px;
    border-radius: 9999px;
    font-style: italic;
  }

  .badge-date {
    background: rgba(0,0,0,0.55);
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
  }

  .banner-dots {
    position: absolute;
    bottom: 8px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .banner-dot {
    border: none;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 9999px;
    width: 6px;
    height: 6px;
    padding: 0;
    cursor: pointer;
    transition: width 0.3s ease, background 0.3s ease;
  }

  .banner-dot--active {
    width: 16px;
    background: #ffffff;
  }
</style>
