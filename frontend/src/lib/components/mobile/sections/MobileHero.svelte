<script lang="ts">
  import { Music, Zap, ShieldCheck, Droplets, Eye, Clock, Flame, ArrowRight, Star, StarHalf } from 'lucide-svelte';
  import './MobileHero.css';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { ProductVariant } from '$lib/types';

  // Thao túng cảm xúc (FOMO States)
  let viewers = $state(Math.floor(Math.random() * (256 - 134) + 134));
  let stockLeft = $state(Math.floor(Math.random() * (7 - 2) + 2));
  let timerSeconds = $state(2 * 3600 + 45 * 60 + 12); // Flash sale count
  let totalSales = $state(Math.floor(Math.random() * 5000 + 12000));
  const formattedSales = $derived((totalSales / 1000).toFixed(1) + 'k');

  $effect(() => {
    const viewerInterval = setInterval(() => {
      viewers += Math.floor(Math.random() * 5) - 2;
      if (viewers < 80) viewers = 80;
    }, 4500);

    const countdown = setInterval(() => {
      if (timerSeconds > 0) timerSeconds--;
    }, 1000);

    return () => {
      clearInterval(viewerInterval);
      clearInterval(countdown);
    };
  });

  const formattedTime = $derived.by(() => {
    const h = Math.floor(timerSeconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((timerSeconds % 3600) / 60).toString().padStart(2, '0');
    const s = (timerSeconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  });

  let { product } = $props();
  const shopStore = getShopStore();
  const currentVariant = $derived(shopStore.variant);
  
  const metadata = $derived(product?.metadata || {});
  const variantOptions = $derived(product?.tierVariations?.[0]?.options || []);
  
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

  const iconMap: Record<string, import('svelte').Component> = { blue: Zap, indigo: ShieldCheck, emerald: Droplets };
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
           class="w-full h-full object-cover select-none brightness-[1.10] saturate-[1.10]"
           loading="eager"
           fetchpriority="high"
         />

         <!-- Cinematic Smooth Gradient (Ultra-Clear Elite 2026) -->
         <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent pointer-events-none"></div>

          <!-- Product Info Overlay -->
          <div class="hero-info-overlay">
            <!-- Live & Scarcity Indicator (Viral 2026) -->
            <div class="inline-flex items-center gap-2.5 px-3 py-1 bg-black/40 backdrop-blur-[25px] rounded-full border border-white/10 shadow-[0_4px_15px_rgba(0,0,0,0.2)] mb-1 w-max">
               <div class="relative flex h-1.5 w-1.5 align-middle">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ff3b30] opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#ff3b30]"></span>
               </div>
               <span class="text-[10px] font-medium text-white/80 tracking-wide mt-[1px]">
                  <strong class="font-black text-white">{viewers}</strong> đang chốt
               </span>
               <div class="w-[1px] h-3 bg-white/20 mx-0.5 mt-[1px]"></div>
               <Flame class="w-3 h-3 text-[#ff9f0a] mt-[1px]" />
               <span class="text-[10px] font-medium text-white/80 tracking-wide mt-[1px]">
                  Còn <strong class="text-[#ff9f0a] font-bold">{stockLeft}</strong> suất
               </span>
            </div>

            <!-- Pricing Row -->
            <div class="flex items-end gap-3 mt-1 pr-14">
               {#if v?.discountPrice}
                  <span class="text-3xl font-black text-white tracking-tighter drop-shadow-md">
                     {formatCurrency(v.discountPrice)}
                  </span>
                  <span class="text-sm text-white/40 line-through mb-1 font-bold">
                     {formatCurrency(v.price)}
                  </span>
               {:else if v}
                  <span class="text-3xl font-black text-white tracking-tighter drop-shadow-md">
                     {formatCurrency(v.price)}
                  </span>
               {/if}
            </div>

            <!-- Title & Variant -->
            <h1 class="text-2xl font-black leading-none text-white uppercase tracking-tighter italic pr-14">
              {opt} <span class="text-[#00f2fe]">.</span>
            </h1>

            <!-- Trust / Review Badge -->
            <div class="flex items-center gap-1.5 mt-0.5 mb-1.5 pr-14">
               <div class="flex items-center gap-[2px]">
                  <Star class="w-3.5 h-3.5 text-[#ffcc00] fill-[#ffcc00] drop-shadow-md" />
                  <Star class="w-3.5 h-3.5 text-[#ffcc00] fill-[#ffcc00] drop-shadow-md" />
                  <Star class="w-3.5 h-3.5 text-[#ffcc00] fill-[#ffcc00] drop-shadow-md" />
                  <Star class="w-3.5 h-3.5 text-[#ffcc00] fill-[#ffcc00] drop-shadow-md" />
                  <StarHalf class="w-3.5 h-3.5 text-[#ffcc00] fill-[#ffcc00] drop-shadow-md" />
               </div>
               <span class="text-[11px] font-black text-white/95 tracking-wide drop-shadow-md">4.9/5</span>
               <span class="text-[10px] text-white/70 tracking-wide font-medium ml-1">· {formattedSales} đã bán</span>
            </div>

            <!-- Description -->
            <p class="text-[12px] text-white/90 line-clamp-2 leading-relaxed italic font-medium max-w-[90%] pr-14 drop-shadow-sm">
               {typeof product?.shortDescription === 'string' ? product.shortDescription.replace(/CHẤM DỨT/g, opt.toUpperCase()) : 'Phác đồ điều trị chuyên biệt cho tình trạng của bạn.'}
            </p>
            
            <!-- Metrics / USP -->
            <div class="flex flex-wrap gap-2 mt-1 pr-14">
              {#each metrics.slice(0, 2) as metric}
                {@const Icon = iconMap[metric.color] || Zap}
                <div class="flex items-center gap-1.5 px-2.5 py-1 bg-white/10 backdrop-blur-xl rounded-md border border-white/20 shadow-lg">
                   <Icon class="w-3 h-3 text-{metric.color || 'blue'}-400" />
                   <span class="text-[9px] font-black text-white/90 uppercase tracking-tight">
                     {metric.value}
                   </span>
                </div>
              {/each}
            </div>

            <!-- CTA Button (Elite 2026 Viral Pill) -->
            <div class="mt-2.5 w-full pr-14">
               <button 
                  class="relative w-[285px] max-w-full group flex items-center justify-between p-1 pr-4 bg-white/10 backdrop-blur-[25px] border border-white/10 rounded-full shadow-[0_8px_32px_rgba(0,0,0,0.3)] active:scale-[0.98] transition-all duration-300"
                  onclick={() => window.scrollBy({ top: window.innerHeight, behavior: 'smooth' })}
               >
                  <!-- Inner Shimmer -->
                  <div class="absolute inset-0 rounded-full overflow-hidden pointer-events-none">
                     <div class="absolute top-[0%] left-[-150%] w-[50%] h-[100%] bg-gradient-to-r from-transparent via-white/10 to-transparent skew-x-[-25deg] animate-shimmer"></div>
                  </div>

                  <!-- Left: Icon & Text -->
                  <div class="flex items-center gap-3 relative z-10">
                     <div class="w-9 h-9 rounded-full bg-white text-black flex items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.3)] group-active:scale-90 transition-transform">
                        <ArrowRight class="w-4 h-4 ml-[2px]" />
                     </div>
                     <div class="flex flex-col items-start justify-center mt-[1px]">
                        <span class="text-[12px] font-black text-white uppercase tracking-wider leading-[1.1] mb-[1.5px]">XEM LIỆU TRÌNH</span>
                        <span class="text-[8px] font-bold text-[#00f2fe] tracking-widest uppercase flex items-center gap-1 leading-none drop-shadow-md">
                           <Zap class="w-2.5 h-2.5" /> FREESHIP HỎA TỐC
                        </span>
                     </div>
                  </div>
                  
                  <!-- Right: Countdown -->
                  <div class="flex flex-col items-end justify-center relative z-10 mt-[1px]">
                     <span class="text-[7.5px] font-bold text-white/50 uppercase tracking-widest mb-[1.5px]">KẾT THÚC SAU</span>
                     <span class="text-[11px] font-black text-white font-mono tracking-tighter drop-shadow-md leading-none">{formattedTime}</span>
                  </div>
               </button>
            </div>
         </div>
      </div>
    {/each}
  </div>
</div>
