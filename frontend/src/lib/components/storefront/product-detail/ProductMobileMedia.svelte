<script lang="ts">
  import { Volume2, VolumeX } from 'lucide-svelte';
  import type { Product } from '$lib/types';
  import ShareToUnlockPromoMobile from './ShareToUnlockPromoMobile.svelte';

  interface Props {
    product: Product;
    displayImages: string[];
    activeImageIndex: number;
    videoEl: HTMLVideoElement | null;
    videoMuted: boolean;
    videoEndTime: number | null;
    handleTimeUpdate: () => void;
    toggleMute: () => void;
    handleCarouselScroll: (e: Event) => void;
    triggerViralFly: () => void;
    onThumbClick: (index: number) => void;
    carouselRef: HTMLElement | null;
    isVideoUrl: (url: string | undefined | null) => boolean;
  }

  let { 
    product, displayImages, activeImageIndex, videoEl = $bindable(), 
    videoMuted, videoEndTime, handleTimeUpdate, toggleMute, 
    handleCarouselScroll, triggerViralFly, onThumbClick, carouselRef = $bindable(),
    isVideoUrl
  }: Props = $props();
</script>

<section class="media-section">
  <div class="carousel-container" bind:this={carouselRef} onscroll={handleCarouselScroll}>
    {#each displayImages as img, i}
      <div class="carousel-slide">
        {#if isVideoUrl(img)}
          {#if activeImageIndex === i}
            <video
              bind:this={videoEl}
              src={img}
              class="slide-media"
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
                <VolumeX size={14} />
              {:else}
                <Volume2 size={14} />
              {/if}
            </button>
          {:else}
            <video
              src={img}
              class="slide-media"
              muted
              playsinline
              preload="metadata"
            ></video>
          {/if}
        {:else}
          <img src={img} alt={product.name} class="slide-media" />
        {/if}
      </div>
    {/each}
  </div>
  <div class="image-counter">{activeImageIndex + 1}/{displayImages.length}</div>

  <div class="media-promo-anchor">
     <ShareToUnlockPromoMobile {product} variant="floating" onUnlock={triggerViralFly} />
  </div>

  <div class="thumbnails-track mt-2 px-2 flex gap-2 overflow-x-auto no-scrollbar">
    {#each displayImages as img, i}
      <button 
        type="button"
        class="thumb-btn {activeImageIndex === i ? 'border-[#ee4d2d]' : 'border-transparent opacity-60'}"
        onclick={() => onThumbClick(i)}
        aria-label="Xem ảnh nhỏ {i + 1}"
      >
        {#if isVideoUrl(img)}
          <video
            src={img}
            class="w-full h-full object-cover pointer-events-none"
            muted
            playsinline
            preload="metadata"
          ></video>
          <div class="thumb-play-overlay">
            <svg class="w-3.5 h-3.5 text-white drop-shadow" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </div>
        {:else}
          <img src={img} alt="thumb" class="w-full h-full object-cover" />
        {/if}
      </button>
    {/each}
  </div>
</section>

<style>
  .media-section { position: relative; background: white; aspect-ratio: 1/1; overflow: hidden; }
  .carousel-container { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; height: 100%; }
  .carousel-container::-webkit-scrollbar { display: none; }
  .carousel-slide { flex: 0 0 100%; height: 100%; scroll-snap-align: start; position: relative; }
  .slide-media { width: 100%; height: 100%; object-fit: cover; }
  .image-counter { position: absolute; top: 12px; right: 12px; background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(8px); color: white; padding: 2px 10px; border-radius: 100px; font-size: 10px; font-weight: 1000; z-index: 5; border: 1px solid rgba(255,255,255,0.1); }
  .media-promo-anchor { position: absolute; bottom: 8px; left: 8px; z-index: 10; }
  .mute-btn {
    position: absolute; bottom: 72px; left: 12px; z-index: 10; width: 32px; height: 32px; border-radius: 50%;
    background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center;
    color: white; border: 1px solid rgba(255, 255, 255, 0.2); transition: background 0.2s;
  }
  .thumbnails-track { scrollbar-width: none; -ms-overflow-style: none; }
  .thumbnails-track::-webkit-scrollbar { display: none; }
  .thumb-btn { width: 48px; height: 48px; border-radius: 2px; border: 2px solid transparent; overflow: hidden; flex-shrink: 0; transition: all 0.2s; padding: 0; position: relative; background: none; }
  .thumb-play-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.25); }
</style>
