<script lang="ts">
  import type { Banner } from '$lib/types';
  import { resolveOptimizedImageUrl } from '$lib/state/utils';

  interface Props {
    banners: Banner[];
    resolvedLcpUrl?: string;
  }
  let { banners, resolvedLcpUrl }: Props = $props();

  // Elite V2.2: Neural Link Intelligence
  // Chuẩn hóa link: Mọi slug đều được coi là sản phẩm hoặc danh mục cấp cao (Root-level)
  function getProductLink(url?: string) {
    if (!url) return '#';
    if (url.startsWith('http') || url.startsWith('/')) return url;
    return `/${url}`;
  }

  // Elite V2.2: Carousel Logic with Runes
  const mainBanners = $derived(banners.filter(b => b.position === 'home_main'));
  let sideBanners = $derived(banners.filter(b => b.position === 'home_side'));

  let currentIndex = $state(0);
  let isHovered = $state(false);

  function nextSlide() {
    currentIndex = (currentIndex + 1) % mainBanners.length;
  }

  function prevSlide() {
    currentIndex = (currentIndex - 1 + mainBanners.length) % mainBanners.length;
  }

  function setSlide(index: number) {
    currentIndex = index;
  }

  $effect(() => {
    if (mainBanners.length <= 1 || isHovered) return;
    
    const timer = setInterval(() => {
      nextSlide();
    }, 6000); // 6s per slide for Elite V2.2
    
    return () => clearInterval(timer);
  });
</script>

<!-- Desktop Layout: osmo Hero Premium 2026 -->
<!-- Tách bạch giao diện: Xóa hoàn toàn Mobile Layout ẩn giấu (tránh vi phạm SEO "Ẩn Link") -->
<div class="grid grid-cols-3 gap-[5px] w-full" style="aspect-ratio: 1200 / 235;">
  <!-- Main Banner (Carousel) -->
  <div 
    class="col-span-2 relative h-full rounded-[2px] overflow-hidden group bg-[#eee]"
    onmouseenter={() => isHovered = true}
    onmouseleave={() => isHovered = false}
    role="region"
    aria-label="banner-carousel"
  >
    {#if mainBanners.length > 0}
      <div 
        class="w-full h-full flex transition-transform duration-700 ease-in-out" 
        style="transform: translateX(-{currentIndex * 100}%)"
      >
        {#each mainBanners as banner, i}
          {#if banner.link_url && banner.link_url !== '#'}
            <a href={getProductLink(banner.link_url)} class="w-full h-full shrink-0 block">
              <img src={i === 0 && resolvedLcpUrl ? resolvedLcpUrl : resolveOptimizedImageUrl(banner.image_url, 800)} alt={banner.title || "Main Banner"} class="w-full h-full object-cover block" loading={i === 0 ? "eager" : "lazy"} fetchpriority={i === 0 ? "high" : "auto"} />
            </a>
          {:else}
            <div class="w-full h-full shrink-0 block">
              <img src={i === 0 && resolvedLcpUrl ? resolvedLcpUrl : resolveOptimizedImageUrl(banner.image_url, 800)} alt={banner.title || "Main Banner"} class="w-full h-full object-cover block" loading={i === 0 ? "eager" : "lazy"} fetchpriority={i === 0 ? "high" : "auto"} />
            </div>
          {/if}
        {/each}
      </div>

      {#if mainBanners.length > 1}
        <!-- Navigation Arrows -->
        <button 
          class="absolute left-0 top-1/2 -translate-y-1/2 bg-black/10 hover:bg-black/30 text-white w-9 h-14 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          onclick={prevSlide}
          aria-label="Previous Slide"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>

        <button 
          class="absolute right-0 top-1/2 -translate-y-1/2 bg-black/10 hover:bg-black/30 text-white w-9 h-14 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          onclick={nextSlide}
          aria-label="Next Slide"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
        </button>

        <!-- Dots Indicators -->
        <div class="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2 items-center">
          {#each mainBanners as _, i}
            <button 
              class="rounded-full transition-all {i === currentIndex ? 'w-[9px] h-[9px] bg-white border border-black/10 ring-1 ring-white/50' : 'w-[7px] h-[7px] bg-white/40 border border-white/20 hover:bg-white/60'}"
              onclick={() => setSlide(i)}
              aria-label="Go to slide {i + 1}"
            ></button>
          {/each}
        </div>
      {/if}
    {/if}
  </div>

  <!-- Side Banners -->
  <div class="flex flex-col gap-[5px] h-full">
    {#each sideBanners as banner}
      {#if banner.link_url && banner.link_url !== '#'}
        <a href={getProductLink(banner.link_url)} class="flex-1 relative rounded-[2px] overflow-hidden group block bg-[#eee]">
          <img src={resolveOptimizedImageUrl(banner.image_url, 400)} alt={banner.title || "Side Banner"} class="w-full h-full object-cover transition-opacity duration-300 hover:opacity-95 active:opacity-90 block" loading="lazy" decoding="async" />
        </a>
      {:else}
        <div class="flex-1 relative rounded-[2px] overflow-hidden group block bg-[#eee]">
          <img src={resolveOptimizedImageUrl(banner.image_url, 400)} alt={banner.title || "Side Banner"} class="w-full h-full object-cover transition-opacity duration-300 hover:opacity-95 active:opacity-90 block" loading="lazy" decoding="async" />
        </div>
      {/if}
    {/each}
  </div>
</div>
