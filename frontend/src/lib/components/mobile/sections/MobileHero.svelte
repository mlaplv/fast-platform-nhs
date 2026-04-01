<script lang="ts">
  import { Music, Zap, ShieldCheck, Droplets } from 'lucide-svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { ProductVariant } from '$lib/types';

  let { product } = $props();
  const shopStore = getShopStore();
  const currentVariant = $derived(shopStore.variant);
  
  const metadata = $derived(product?.metadata || {});
  const variantOptions = $derived(product?.tierVariations?.[0]?.options || []);
  const musicLabel = $derived(metadata.mobile_music_label || 'Nhạc nền gốc - Elite Storefront');
  
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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
  };

  const iconMap: Record<string, any> = { blue: Zap, indigo: ShieldCheck, emerald: Droplets };
</script>

<div class="h-full w-full relative group">
  <div 
    class="variant-slider-container h-full" 
    bind:this={variantScroller}
    onscroll={syncVariantOnScroll}
  >
    {#each variantOptions as opt, i}
      {@const v = product?.variants?.find((varItem: ProductVariant) => varItem.tierIndex[0] === i)}
      <div class="variant-slide relative">
         <!-- Main Content Image -->
         <img
           src={product?.tierVariations[0]?.images[i] || product?.images[0]}
           alt="{product?.name} - {opt}"
           class="w-full h-full object-cover select-none"
         />

         <!-- Cinematic Smooth Gradient (Elite 2026) -->
         <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent pointer-events-none"></div>

         <!-- Product Info Overlay -->
         <div 
           class="absolute left-5 right-20 tiktok-shadow flex flex-col gap-3"
           style="bottom: calc(var(--mobile-bottom-space) + env(safe-area-inset-bottom) + 10px)"
         >
            <!-- Pricing Row -->
            <div class="flex items-end gap-3 mt-1">
               {#if v?.discountPrice}
                  <span class="text-3xl font-black text-white tracking-tighter">
                     {formatCurrency(v.discountPrice)}
                  </span>
                  <span class="text-sm text-white/40 line-through mb-1 font-bold">
                     {formatCurrency(v.price)}
                  </span>
               {:else if v}
                  <span class="text-3xl font-black text-white tracking-tighter">
                     {formatCurrency(v.price)}
                  </span>
               {/if}
            </div>

            <!-- Title & Variant -->
            <h1 class="text-2xl font-black leading-none text-white uppercase tracking-tighter italic">
              {opt} <span class="text-blue-400">.</span>
            </h1>

            <!-- Description -->
            <p class="text-[12px] text-white/90 line-clamp-3 leading-relaxed italic font-medium max-w-[90%]">
               {typeof product?.shortDescription === 'string' ? product.shortDescription.replace(/CHẤM DỨT/g, opt.toUpperCase()) : 'Phác đồ điều trị chuyên biệt cho tình trạng của bạn.'}
            </p>
            
            <!-- Metrics / USP -->
            <div class="flex flex-wrap gap-2 mt-2">
              {#each metrics.slice(0, 2) as metric}
                {@const Icon = iconMap[metric.color] || Zap}
                <div class="flex items-center gap-1.5 px-2.5 py-1 bg-white/5 backdrop-blur-xl rounded-lg border border-white/10">
                   <Icon class="w-3 h-3 text-{metric.color || 'blue'}-400" />
                   <span class="text-[8px] font-black text-white/70 uppercase tracking-tight">
                     {metric.value}
                   </span>
                </div>
              {/each}
            </div>

            <!-- Music Info -->
            <div class="flex items-center gap-2 text-white/40 mt-1">
              <Music class="w-3.5 h-3.5 animate-pulse text-white/60" />
              <div class="music-marquee-container max-w-[150px]">
                 <span class="music-ticker text-[10px] font-bold tracking-widest uppercase">{musicLabel}</span>
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
    -ms-overflow-style: none;
  }
  .variant-slider-container::-webkit-scrollbar { display: none; }
  .variant-slide {
    flex: none;
    width: 100vw;
    height: 100dvh;
    scroll-snap-align: center;
    position: relative;
  }
</style>
