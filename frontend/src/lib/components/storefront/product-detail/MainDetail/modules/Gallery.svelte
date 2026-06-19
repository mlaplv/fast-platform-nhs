<script lang="ts">
  import { onMount } from 'svelte';
  import type { Product } from '$lib/types';
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import VolumeX from "@lucide/svelte/icons/volume-x";
  import ViralShareBarDesktop from '../../shared/ViralShareBarDesktop.svelte';
  import { resolveOptimizedImageUrl } from '$lib/state/utils';

  interface Props {
    product: Product;
    likeCount: number;
    isFlashSaleActive: boolean;
    productInfo: {
      salePrice: number;
      originalPrice: number;
    };
    selectedIndices: number[];
    variations: Array<{
      name: string;
      options: string[];
      images?: string[];
    }>;
    resolvedLcpUrl?: string;
  }

  let { 
    product, 
    likeCount, 
    isFlashSaleActive, 
    productInfo, 
    selectedIndices, 
    variations,
    resolvedLcpUrl
  }: Props = $props();

  // --- Gallery State ---
  let activeImageIndex = $state(0);
  let overrideImageIndex = $state<number | null>(null);

  $effect(() => {
    // Reset override when variant changes
    selectedIndices;
    overrideImageIndex = null;
  });

  let isInitialLcp = $state(true);
  onMount(() => {
    isInitialLcp = false;
  });
  
  // Detect video URL
  function isVideoUrl(url: string | undefined | null): boolean {
    if (!url) return false;
    const clean = url.split('?')[0].toLowerCase();
    return /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(clean);
  }

  let videoEl = $state<HTMLVideoElement | null>(null);
  let videoMuted = $state(true);

  const videoStartTime = $derived(
    typeof product.metadata?.video_start_time === 'number'
      ? product.metadata.video_start_time
      : 0
  );
  const videoEndTime = $derived(
    typeof product.metadata?.video_end_time === 'number'
      ? product.metadata.video_end_time
      : null
  );

  function handleTimeUpdate() {
    if (!videoEl) return;
    if (videoEndTime !== null && videoEl.currentTime >= videoEndTime) {
      videoEl.currentTime = videoStartTime;
      videoEl.play().catch(() => {});
    }
  }

  function toggleMute() {
    videoMuted = !videoMuted;
    if (videoEl) videoEl.muted = videoMuted;
  }

  const displayImages = $derived.by(() => {
    if (variations?.[0]?.images && variations[0].images.length > 0) {
      return variations[0].images;
    }
    return product.images || [];
  });

  // Derive current image based on variant selection or thumbnail index
  let currentImage = $derived.by(() => {
    const pImages = displayImages;
    if (overrideImageIndex !== null) {
      return pImages[overrideImageIndex] || pImages[0] || '/placeholder.png';
    }
    if (selectedIndices[0] >= 0 && variations?.[0]?.images?.[selectedIndices[0]]) {
      return variations[0].images[selectedIndices[0]];
    }
    return pImages[activeImageIndex] || pImages[0] || '/placeholder.png';
  });

  $effect(() => {
    if (videoEl && isVideoUrl(currentImage)) {
      videoEl.load();
      videoEl.muted = videoMuted;
      const onMeta = () => {
        if (videoEl) {
          videoEl.currentTime = videoStartTime;
          videoEl.play().catch(() => {});
        }
      };
      videoEl.addEventListener('loadedmetadata', onMeta, { once: true });
      return () => videoEl?.removeEventListener('loadedmetadata', onMeta);
    }
  });
</script>

<div class="w-full md:w-[250px] lg:w-[450px] shrink-0">
  <div class="aspect-square w-full rounded-none overflow-hidden relative border border-gray-100 flex items-center justify-center bg-white group">
    {#if isVideoUrl(currentImage)}
      <video
        bind:this={videoEl}
        src={currentImage}
        class="w-full h-full object-cover"
        autoplay
        muted={videoMuted}
        loop={videoEndTime === null}
        playsinline
        preload="auto"
        fetchpriority="high"
        ontimeupdate={handleTimeUpdate}
      ></video>
      <button
        onclick={toggleMute}
        class="absolute bottom-3 right-3 z-10 w-9 h-9 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/70 transition-all border border-white/20"
        title={videoMuted ? 'Bật âm thanh' : 'Tắt âm thanh'}
      >
        {#if videoMuted}
          <VolumeX size={16} />
        {:else}
          <Volume2 size={16} />
        {/if}
      </button>
    {:else}
      <img 
        src={(isInitialLcp && resolvedLcpUrl) ? resolvedLcpUrl : ((currentImage === displayImages[0] && resolvedLcpUrl) ? resolvedLcpUrl : resolveOptimizedImageUrl(currentImage, 800))} 
        srcset="{resolveOptimizedImageUrl(currentImage, 450)} 450w, {resolveOptimizedImageUrl(currentImage, 600)} 600w, {resolveOptimizedImageUrl(currentImage, 800)} 800w, {resolveOptimizedImageUrl(currentImage, 900)} 900w, {resolveOptimizedImageUrl(currentImage, 1200)} 1200w"
        sizes="(max-width: 1023px) 100vw, 450px"
        width="450"
        height="450"
        alt={product.name} 
        class="w-full h-full object-contain bg-white" 
        fetchpriority="high"
        decoding="sync"
      />
    {/if}
    
    {#if isFlashSaleActive}
      <div class="absolute top-0 left-0 bg-[#d12a0f] text-white px-3 py-1.5 text-[11px] font-black tracking-widest shadow-lg">
        Flash Sale
      </div>
    {/if}
 
    {#if !isVideoUrl(currentImage) && productInfo.salePrice < productInfo.originalPrice}
      <div class="absolute {isFlashSaleActive ? 'top-8' : 'top-0'} left-0 bg-[#ffe97a] px-2 py-1 text-[12px] font-black text-[#d12a0f] shadow-sm z-10">
        -{Math.round((1 - productInfo.salePrice / productInfo.originalPrice) * 100)}%
      </div>
    {/if}
  </div>
  
  <div class="mt-6 grid grid-cols-5 gap-3 px-1">
    {#each displayImages.slice(0, 5) as img, i}
      {@const isActive = activeImageIndex === i}
      <button 
        type="button"
        class="aspect-square border-2 cursor-pointer rounded-lg overflow-hidden relative group {isActive ? 'border-[#ffaa00] shadow-sm z-10' : 'border-transparent opacity-70 hover:opacity-100 hover:border-[#ffaa00]/50'} bg-gray-50 p-0"
        onclick={() => { activeImageIndex = i; overrideImageIndex = i; }}
        aria-label="Xem ảnh {i + 1}"
      >
        {#if isVideoUrl(img)}
          <video
            src={img}
            class="w-full h-full object-cover pointer-events-none"
            muted
            playsinline
            loop
            autoplay={isActive}
            preload="metadata"
          ></video>
          <div class="absolute inset-0 flex items-center justify-center bg-black/10 group-hover:bg-black/20 transition-colors">
            <div class="w-8 h-8 rounded-full bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center text-white shadow-xl">
              <svg class="w-3.5 h-3.5 fill-current ml-0.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            </div>
          </div>
          <div class="absolute top-1.5 left-1.5 bg-gradient-to-br from-[#FFD700] to-[#FFA500] text-black text-[7px] font-black px-1.5 py-0.5 rounded shadow-sm tracking-tighter">
            Viral
          </div>
        {:else}
          <img 
            src={resolveOptimizedImageUrl(img, 120)} 
            alt="{product.name} - Hình ảnh {i + 1}" 
            class="w-full h-full object-cover" 
            loading="lazy"
            decoding="async"
          />
        {/if}
      </button>
    {/each}
  </div>

  <div class="mt-8 px-2">
    <ViralShareBarDesktop 
      {product} 
      likeCount={likeCount}
      hideLikes={false}
    />
  </div>
</div>


