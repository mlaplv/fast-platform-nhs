<script lang="ts">
  import type { Product } from '$lib/types';
  import MobileActionStack from './MobileActionStack.svelte';
  import MobileBottomSheet from './MobileBottomSheet.svelte';
  import { Music } from 'lucide-svelte';
  import { Z_INDEX } from '$lib/core/constants/zIndex';
  import './mobile.css';

  let { product }: { product: Product } = $props();

  let showBottomSheet = $state(false);
  const metadata = $derived(product?.metadata || {});
  const images = $derived(product?.images || []);

  const handle = $derived(metadata.mobile_handle || '@elitestore_official');
  const hashtags = $derived(metadata.mobile_hashtags || '#xuhuong #thinhhanh');
  const musicLabel = $derived(metadata.mobile_music_label || 'Nhạc nền gốc - Elite Storefront Bản Quyền');
  const loadingText = $derived(metadata.mobile_loading_text || 'Loading Media...');
</script>

<div
  class="mobile-snap-container bg-black min-h-screen text-white relative"
  style="--z-content: {Z_INDEX.BASE}; --z-overlay: {Z_INDEX.SURFACE}"
>
  <MobileActionStack {product} onPurchase={() => showBottomSheet = true} />

  {#if images.length > 0}
    {#each images as img, i}
      <div class="mobile-snap-slide relative overflow-hidden">
         <img
           src={img}
           alt={`${product?.name} | Frame ${i + 1}`}
           loading={i === 0 ? "eager" : "lazy"}
           fetchpriority={i === 0 ? "high" : "auto"}
           decoding="async"
           class="w-full h-full object-cover select-none pointer-events-none will-change-transform"
           style="aspect-ratio: 9/16;"
         />

         <!-- Gradient Overlay: GPU Accelerated -->
         <div class="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/90 via-black/20 to-transparent pointer-events-none will-change-[opacity]"></div>

         <div
           class="absolute bottom-6 left-3 right-16 text-white tiktok-shadow mb-[env(safe-area-inset-bottom)]"
           style="z-index: var(--z-overlay)"
         >
           <p class="font-bold text-base mb-1 tracking-tight opacity-90">{handle}</p>
           <h1 class="text-[15px] font-normal line-clamp-2 leading-tight mb-2">
             {product?.name}
             <span class="font-bold text-white/80 ml-1">{hashtags}</span>
           </h1>
           <div class="px-2 py-[2px] bg-white/20 backdrop-blur-md rounded border border-white/30 inline-flex items-center">
             <span class="text-[13px] font-bold text-yellow-400">🔥 {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(product?.price || 0)}</span>
           </div>

           <div class="flex items-center gap-2 mt-3 text-[13px] text-white/90">
             <Music class="w-4 h-4 animate-pulse" />
             <div class="music-marquee-container">
                <span class="music-ticker text-[13px]">{musicLabel}</span>
             </div>
           </div>
         </div>
      </div>
    {/each}
  {:else}
      <div class="mobile-snap-slide bg-gray-900 text-white flex flex-col items-center justify-center">
        <div class="animate-pulse flex flex-col items-center">
          <div class="w-12 h-12 border-4 border-white/20 border-t-white rounded-full animate-spin"></div>
          <p class="mt-4 font-bold tracking-widest text-sm uppercase text-white/50">{loadingText}</p>
        </div>
      </div>
  {/if}

  <MobileBottomSheet bind:active={showBottomSheet} {product} />
</div>
