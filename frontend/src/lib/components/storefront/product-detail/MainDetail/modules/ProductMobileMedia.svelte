<script lang="ts">
  import { onMount } from 'svelte';
  import Volume2 from "@lucide/svelte/icons/volume-2";
  import VolumeX from "@lucide/svelte/icons/volume-x";
  import type { Product } from '$lib/types';
  import ShareToUnlockPromoMobile from '../../shared/ShareToUnlockPromoMobile.svelte';
  import { resolveOptimizedImageUrl } from '$lib/state/utils';

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
    carouselWidth?: number;
    isVideoUrl: (url: string | undefined | null) => boolean;
    resolvedLcpUrl?: string;
  }

  let { 
    product, displayImages, activeImageIndex, videoEl = $bindable(), 
    videoMuted, videoEndTime, handleTimeUpdate, toggleMute, 
    handleCarouselScroll, triggerViralFly, onThumbClick, carouselRef = $bindable(),
    carouselWidth = $bindable(0),
    isVideoUrl,
    resolvedLcpUrl
  }: Props = $props();

  let isInitialLcp = $state(true);
  onMount(() => {
    isInitialLcp = false;
  });
</script>

<section class="media-section">
  <div class="carousel-container" bind:this={carouselRef} bind:clientWidth={carouselWidth} onscroll={handleCarouselScroll}>
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
              fetchpriority="high"
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
          {#if i === 0}
            <img 
              src={(isInitialLcp && resolvedLcpUrl) ? resolvedLcpUrl : resolveOptimizedImageUrl(img, 600)} 
              width="412"
              height="412"
              alt={product.name} 
              class="slide-media" 
              fetchpriority="high"
              decoding="sync"
            />
          {:else}
            <img 
              src={resolveOptimizedImageUrl(img, 600)} 
              srcset="{resolveOptimizedImageUrl(img, 412)} 412w, {resolveOptimizedImageUrl(img, 600)} 600w, {resolveOptimizedImageUrl(img, 700)} 700w, {resolveOptimizedImageUrl(img, 800)} 800w"
              sizes="(max-width: 767px) 100vw, 600px"
              width="412"
              height="412"
              alt={product.name} 
              class="slide-media" 
              loading="lazy" 
              fetchpriority="low"
              decoding="async"
            />
          {/if}
        {/if}
      </div>
    {/each}
  </div>
  <div class="image-counter">{activeImageIndex + 1}/{displayImages.length}</div>

  <div class="media-promo-anchor">
     {#key product.id}
       <ShareToUnlockPromoMobile {product} variant="floating" onUnlock={triggerViralFly} />
     {/key}
  </div>
  <div class="thumbnails-track mt-[10px] px-4 flex gap-3 overflow-x-auto no-scrollbar">
    {#each displayImages as img, i}
      {@const isActive = activeImageIndex === i}
      <button 
        type="button"
        class="thumb-btn {isActive ? 'active' : 'opacity-70'}"
        onclick={() => onThumbClick(i)}
        aria-label="Xem ảnh nhỏ {i + 1}"
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
          <div class="thumb-play-overlay">
             <div class="glass-play">
                <svg class="w-3 h-3 fill-current ml-0.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
             </div>
          </div>
          <div class="viral-badge">Viral</div>
        {:else}
          <img 
            src={resolveOptimizedImageUrl(img, 120)} 
            alt="{product.name} - Thumbnail {i + 1}" 
            class="w-full h-full object-cover" 
            loading="lazy"
            decoding="async"
          />
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
  .image-counter { position: absolute; top: 12px; right: 12px; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(8px); color: white; padding: 2px 10px; border-radius: 100px; font-size: 10px; font-weight: 1000; z-index: 5; border: 1px solid rgba(255,255,255,0.1); }
  .media-promo-anchor { position: absolute; bottom: 10px; left: 10px; z-index: 10; }
  .mute-btn {
    position: absolute; bottom: 72px; left: 12px; z-index: 10; width: 32px; height: 32px; border-radius: 50%;
    background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center;
    color: white; border: 1px solid rgba(255, 255, 255, 0.2); transition: background 0.2s;
  }
  .thumbnails-track { scrollbar-width: none; -ms-overflow-style: none; }
  .thumbnails-track::-webkit-scrollbar { display: none; }
  .thumb-btn { 
    width: 56px; height: 56px; border-radius: 12px; border: 2.5px solid transparent; 
    overflow: hidden; flex-shrink: 0; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
    padding: 0; position: relative; background: #f0f0f0; 
  }
  .thumb-btn.active { 
    border-color: #ffaa00; 
    transform: scale(1.1) translateY(-2px);
    box-shadow: 0 8px 20px rgba(255, 170, 0, 0.25);
    z-index: 2;
  }
  .thumb-play-overlay { 
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; 
    background: rgba(0, 0, 0, 0.15); 
  }
  .glass-play {
    width: 28px; height: 28px; background: rgba(255, 255, 255, 0.25);
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.4); border-radius: 50%;
    display: flex; align-items: center; justify-content: center; color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  .viral-badge {
    position: absolute; top: 4px; left: 4px;
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    color: black; font-size: 7px; font-weight: 1000;
    padding: 1px 5px; border-radius: 4px;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
</style>
