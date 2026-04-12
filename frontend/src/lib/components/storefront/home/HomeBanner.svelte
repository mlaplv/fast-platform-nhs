<script lang="ts">
  import type { Banner } from '$lib/types';

  interface Props {
    banners: Banner[];
  }
  let { banners }: Props = $props();

  // Elite V2.2: Neural Link Intelligence
  // Tự động chuẩn hóa link: Nếu chỉ là slug -> /product/slug, nếu là full url -> giữ nguyên
  function getProductLink(url?: string) {
    if (!url) return '#';
    if (url.startsWith('http') || url.startsWith('/')) return url;
    return `/${url}`; // Mặc định là slug sản phẩm vì đã bỏ tiền tố /product ở route
  }

  let mainBanners = $derived(banners.filter(b => b.position === 'home_main'));
  let sideBanners = $derived(banners.filter(b => b.position === 'home_side'));

  let currentSlide = $state(0);
  let timer: ReturnType<typeof setInterval>;

  function startTimer() {
    if (mainBanners.length > 1) {
      timer = setInterval(() => {
        nextSlide();
      }, 9000);
    }
  }

  function clearTimer() {
    if (timer) clearInterval(timer);
  }

  function nextSlide() {
    currentSlide = (currentSlide + 1) % mainBanners.length;
  }

  function prevSlide() {
    currentSlide = (currentSlide - 1 + mainBanners.length) % mainBanners.length;
  }

  function setSlide(index: number) {
    currentSlide = index;
  }

  $effect(() => {
    startTimer();
    return () => clearTimer();
  });
</script>

<!-- Desktop Layout: Micsmo Hero Premium 2026 -->
<div class="hidden md:grid grid-cols-3 gap-[5px] w-full" style="aspect-ratio: 1200 / 235;">
  <!-- Main Banner (Carousel) -->
  <div 
    class="col-span-2 relative h-full rounded-[2px] overflow-hidden group bg-[#eee]"
    onmouseenter={clearTimer}
    onmouseleave={startTimer}
    role="region"
    aria-label="banner-carousel"
  >
    {#if mainBanners.length > 0}
      <div class="w-full h-full flex transition-transform duration-1000 ease-out" style="transform: translateX(-{currentSlide * 100}%)">
        {#each mainBanners as banner}
          <a href={getProductLink(banner.link_url)} class="w-full h-full shrink-0">
             <img src={banner.image_url} alt={banner.title || "Main Banner"} class="w-full h-full object-cover" />
          </a>
        {/each}
      </div>

      <!-- Left Arrow -->
      {#if mainBanners.length > 1}
        <button 
          class="absolute left-0 top-1/2 -translate-y-1/2 bg-black/10 hover:bg-black/30 text-white w-9 h-14 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          onclick={prevSlide}
          aria-label="Previous Slide"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>

        <!-- Right Arrow -->
        <button 
          class="absolute right-0 top-1/2 -translate-y-1/2 bg-black/10 hover:bg-black/30 text-white w-9 h-14 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          onclick={nextSlide}
          aria-label="Next Slide"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
        </button>
      {/if}

      <!-- Dots Pagination - Micsmo Crystal Style -->
      {#if mainBanners.length > 1}
        <div class="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2 items-center">
          {#each mainBanners as _, i}
            <button 
              class="rounded-full transition-all {i === currentSlide ? 'w-[9px] h-[9px] bg-white border border-black/10 ring-1 ring-white/50' : 'w-[7px] h-[7px] bg-white/40 border border-white/20 hover:bg-white/60'}"
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
      <!-- Micsmo style hover effect -->
      <a href={getProductLink(banner.link_url)} class="flex-1 relative rounded-[2px] overflow-hidden group block bg-[#eee]">
        <img src={banner.image_url} alt={banner.title || "Side Banner"} class="w-full h-full object-cover transition-opacity duration-300 hover:opacity-95 active:opacity-90" />
      </a>
    {/each}
  </div>
</div>

<!-- Mobile Layout: Immersive Full-Width -->
<div class="md:hidden relative h-[90px] w-full mb-4 rounded-none overflow-hidden bg-white shadow-sm">
  {#if mainBanners.length > 0}
    <!-- Simple Carousel For Mobile -->
    <div class="w-full h-full flex transition-transform duration-1000" style="transform: translateX(-{currentSlide * 100}%)">
      {#each mainBanners as banner}
        <a href={getProductLink(banner.link_url)} class="w-full h-full shrink-0">
          <img src={banner.image_url} alt={banner.title || "Banner"} class="w-full h-full object-cover" />
        </a>
      {/each}
    </div>
    
    <!-- Dots for mobile -->
    {#if mainBanners.length > 1}
      <div class="absolute bottom-1 left-1/2 -translate-x-1/2 flex gap-1.5">
        {#each mainBanners as _, i}
          <div class="h-1 rounded-full transition-all {i === currentSlide ? 'w-3 bg-white' : 'w-1.5 bg-white/50'}"></div>
        {/each}
      </div>
    {/if}
  {/if}
</div>
