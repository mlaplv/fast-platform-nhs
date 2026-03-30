<script lang="ts">
  import { Music, Zap, ShieldCheck, Droplets } from 'lucide-svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';

  let { product } = $props();
  const shopStore = getShopStore();
  const currentVariant = $derived(shopStore.variant);
  
  const metadata = $derived(product?.metadata || {});
  const variantOptions = $derived(product?.tierVariations?.[0]?.options || []);
  const handle = $derived(metadata.mobile_handle || '@elitestore_official');
  const musicLabel = $derived(metadata.mobile_music_label || 'Nhạc nền gốc - Elite Storefront');
  const headline = $derived(metadata.hero_headline || 'CHẤM DỨT <br/> MÙI CƠ THỂ.');
  const metrics = $derived(metadata.hero_metrics || [
    { label: '[Tốc độ]', value: 'THẨM THẤU TÀNG HÌNH 3S', color: 'blue' },
    { label: '[Hiệu quả]', value: 'PHONG TỎA MÙI 48H', color: 'indigo' },
    { label: '[Thành phần]', value: 'TINH CHẤT DƯỢC LIỆU SẠCH', color: 'emerald' }
  ]);

  let variantScroller: HTMLDivElement | undefined = $state();

  function syncVariantOnScroll() {
    if (!variantScroller) return;
    const index = Math.round(variantScroller.scrollLeft / window.innerWidth);
    if (currentVariant?.tierIndex[0] !== index) {
      shopStore.selectVariantByTier([index]);
    }
  }

  $effect(() => {
    if (variantScroller && currentVariant) {
      const targetX = currentVariant.tierIndex[0] * window.innerWidth;
      if (Math.abs(variantScroller.scrollLeft - targetX) > 10) {
        variantScroller.scrollTo({ left: targetX, behavior: 'smooth' });
      }
    }
  });

  const iconMap: Record<string, any> = { blue: Zap, indigo: ShieldCheck, emerald: Droplets };
</script>

<div class="h-full w-full relative">
  <div 
    class="variant-slider-container h-full" 
    bind:this={variantScroller}
    onscroll={syncVariantOnScroll}
  >
    {#each variantOptions as opt, i}
      <div class="variant-slide relative">
         <img
           src={product?.tierVariations[0]?.images[i] || product?.images[0]}
           alt="{product?.name} - {opt}"
           class="w-full h-full object-cover select-none"
         />

         <div class="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/90 pointer-events-none"></div>

         <!-- Identity & Headline -->
         <div class="absolute bottom-32 left-5 right-20 tiktok-shadow mb-[env(safe-area-inset-bottom)]">
            <p class="font-bold text-base mb-2 drop-shadow-lg text-white">{handle}</p>
            <h1 class="text-2xl font-black leading-tight mb-2 text-white uppercase tracking-tighter italic">
              {@html headline}
            </h1>

            {#if product?.shortDescription}
               <p class="text-[11px] text-white/60 mb-4 line-clamp-2 leading-relaxed italic">
                  {@html product.shortDescription}
               </p>
            {/if}
            
            <!-- Metrics Sync -->
            <div class="flex flex-wrap gap-3 mb-6">
              {#each metrics as metric}
                {@const Icon = iconMap[metric.color] || Zap}
                <div class="flex items-center gap-1.5 px-2 py-1 bg-black/40 backdrop-blur-md rounded-lg border border-white/10">
                   <Icon class="w-3 h-3 text-{metric.color || 'blue'}-400" />
                   <span class="text-[9px] font-black text-white/90 uppercase tracking-tight">
                     {typeof metric.value === 'string' ? metric.value : (metric.label || 'Elite')}
                   </span>
                </div>
              {/each}
            </div>

            <div class="flex items-center gap-2 text-white/80">
              <Music class="w-4 h-4 animate-pulse" />
              <div class="music-marquee-container">
                 <span class="music-ticker text-[12px] font-medium">{musicLabel}</span>
              </div>
            </div>
         </div>
      </div>
    {/each}
  </div>
</div>

<style lang="postcss">
  .variant-slider-container {
    display: flex;
    overflow-x: scroll;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
  }
  .variant-slider-container::-webkit-scrollbar { display: none; }
  .variant-slide {
    flex: none;
    width: 100vw;
    height: 100dvh;
    scroll-snap-align: center;
  }
</style>
