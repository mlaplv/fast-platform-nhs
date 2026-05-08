<script lang="ts">
  import type { Product } from '$lib/types';
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import VolumeX from "@lucide/svelte/icons/volume-x";
  import ViralShareBarDesktop from '../ViralShareBarDesktop.svelte';

  interface Props {
    product: Product;
    currentImage: string;
    activeImageIndex: number;
    isFlashSaleActive: boolean;
    likeCount: number;
    productInfo: {
      salePrice: number;
      originalPrice: number;
    };
    onThumbnailClick: (index: number) => void;
  }

  let { 
    product, 
    currentImage, 
    activeImageIndex, 
    isFlashSaleActive, 
    likeCount,
    productInfo,
    onThumbnailClick 
  }: Props = $props();

  let videoEl = $state<HTMLVideoElement | null>(null);
  let videoMuted = $state(true);

  const videoStartTime = $derived(Number(product.metadata?.video_start_time || 0));
  const videoEndTime = $derived(product.metadata?.video_end_time ? Number(product.metadata.video_end_time) : null);

  function isVideoUrl(url: string | undefined | null): boolean {
    if (!url) return false;
    const clean = url.split('?')[0].toLowerCase();
    return /\.(mp4|webm|mov|ogg|ogv|avi|mkv)$/.test(clean);
  }

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

<div class="gallery-container">
  <div class="main-media group">
    {#if isVideoUrl(currentImage)}
      <video
        bind:this={videoEl}
        src={currentImage}
        class="media-content"
        autoplay
        muted={videoMuted}
        loop={videoEndTime === null}
        playsinline
        preload="auto"
        ontimeupdate={handleTimeUpdate}
      ></video>
      <button
        onclick={toggleMute}
        class="mute-btn"
        title={videoMuted ? 'Bật âm thanh' : 'Tắt âm thanh'}
      >
        {#if videoMuted}
          <VolumeX size={16} />
        {:else}
          <Volume2 size={16} />
        {/if}
      </button>
    {:else}
      <img src={currentImage} alt={product.name} class="media-content image-zoom" />
    {/if}
    
    {#if isFlashSaleActive}
      <div class="flash-sale-badge">Flash Sale</div>
    {/if}

    {#if !isVideoUrl(currentImage) && productInfo.salePrice < productInfo.originalPrice}
      <div class="discount-badge">
        -{Math.round((1 - productInfo.salePrice / productInfo.originalPrice) * 100)}%
      </div>
    {/if}
  </div>
  
  <div class="thumbnails">
    {#each (product.images || []).slice(0, 5) as img, i}
      <button 
        type="button"
        class="thumb-btn"
        class:active={activeImageIndex === i}
        onclick={() => onThumbnailClick(i)}
        aria-label="Xem ảnh {i + 1}"
      >
        {#if isVideoUrl(img)}
          <video src={img} class="thumb-video" muted playsinline preload="metadata"></video>
          <div class="play-overlay">
            <svg class="play-icon" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </div>
        {:else}
          <img src={img} alt="Thumb" class="thumb-img" />
        {/if}
      </button>
    {/each}
  </div>

  <div class="social-share">
    <ViralShareBarDesktop 
      {product} 
      likeCount={likeCount}
      hideLikes={false}
    />
  </div>
</div>

<style>
  .gallery-container {
    width: 100%;
    max-width: 450px;
    flex-shrink: 0;
  }

  .main-media {
    aspect-ratio: 1/1;
    width: 100%;
    position: relative;
    border: 1px solid #f3f4f6;
    display: flex;
    align-items: center;
    justify-content: center;
    background: white;
    overflow: hidden;
  }

  .media-content {
    width: 100%;
    height: 100%;
    object-fit: contain;
    background: white;
  }

  .image-zoom {
    transition: transform 0.7s;
  }

  .main-media:hover .image-zoom {
    transform: scale(1.5);
  }

  .mute-btn {
    position: absolute;
    bottom: 0.75rem;
    right: 0.75rem;
    z-index: 10;
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    cursor: pointer;
    transition: all 0.2s;
  }

  .mute-btn:hover {
    background: rgba(0, 0, 0, 0.7);
  }

  .flash-sale-badge {
    position: absolute;
    top: 0;
    left: 0;
    background: #ee4d2d;
    color: white;
    padding: 0.375rem 0.75rem;
    font-size: 11px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  }

  .discount-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: #ffe97a;
    padding: 0.25rem 0.5rem;
    font-size: 12px;
    font-weight: 900;
    color: #ee4d2d;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  .thumbnails {
    margin-top: 1rem;
    display: grid;
    grid-cols: 5;
    gap: 0.5rem;
    padding: 0 0.25rem;
    display: flex;
  }

  .thumb-btn {
    aspect-ratio: 1/1;
    border: 2px solid transparent;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
    background: #f9fafb;
    padding: 0;
    flex: 1;
  }

  .thumb-btn.active {
    border-color: #ee4d2d;
  }

  .thumb-btn:hover {
    border-color: rgba(238, 77, 45, 0.3);
  }

  .thumb-video, .thumb-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .play-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.2);
  }

  .play-icon {
    width: 1rem;
    height: 1rem;
    color: white;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5));
  }

  .social-share {
    margin-top: 2rem;
    padding: 0 0.5rem;
  }
</style>
