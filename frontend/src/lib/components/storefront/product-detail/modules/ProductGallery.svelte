<script lang="ts">
  import type { Product } from '$lib/types';
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import VolumeX from "@lucide/svelte/icons/volume-x";
  import ViralShareBarDesktop from '../shared/ViralShareBarDesktop.svelte';

  interface Props {
    product: Product;
    likeCount: number;
    isFlashSaleActive: boolean;
    productInfo: {
      salePrice: number;
      originalPrice: number;
    };
    selectedIndices: number[];
    variations: any[];
  }

  let { 
    product, 
    likeCount, 
    isFlashSaleActive, 
    productInfo, 
    selectedIndices, 
    variations 
  }: Props = $props();

  // --- Gallery State ---
  let activeImageIndex = $state(0);
  
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

  // Derive current image based on variant selection or thumbnail index
  let currentImage = $derived.by(() => {
    if (selectedIndices[0] >= 0 && variations?.[0]?.images?.[selectedIndices[0]]) {
      return variations[0].images[selectedIndices[0]];
    }
    const pImages = product.images || [];
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

<div class="w-full md:w-[450px] shrink-0">
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
      <img src={currentImage} alt={product.name} class="w-full h-full object-contain transition-transform duration-700 group-hover:scale-150 bg-white" />
    {/if}
    
    {#if isFlashSaleActive}
      <div class="absolute top-0 left-0 bg-[#ee4d2d] text-white px-3 py-1.5 text-[11px] font-black uppercase tracking-widest shadow-lg">
        Flash Sale
      </div>
    {/if}

    {#if !isVideoUrl(currentImage) && productInfo.salePrice < productInfo.originalPrice}
      <div class="absolute top-2 right-2 bg-[#ffe97a] px-2 py-1 text-[12px] font-black text-[#ee4d2d] shadow-sm">
        -{Math.round((1 - productInfo.salePrice / productInfo.originalPrice) * 100)}%
      </div>
    {/if}
  </div>
  
  <div class="mt-4 grid grid-cols-5 gap-2 px-1">
    {#each (product.images || []).slice(0, 5) as img, i}
      <button 
        type="button"
        class="aspect-square border-2 cursor-pointer transition-all {activeImageIndex === i ? 'border-[#ee4d2d]' : 'border-transparent hover:border-[#ee4d2d]'} relative overflow-hidden bg-gray-50 p-0"
        onclick={() => activeImageIndex = i}
        aria-label="Xem ảnh {i + 1}"
      >
        {#if isVideoUrl(img)}
          <video
            src={img}
            class="w-full h-full object-cover pointer-events-none"
            muted
            playsinline
            preload="metadata"
          ></video>
          <div class="absolute inset-0 flex items-center justify-center bg-black/20">
            <svg class="w-4 h-4 text-white drop-shadow" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </div>
        {:else}
          <img src={img} alt="Thumb" class="w-full h-full object-cover" />
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
