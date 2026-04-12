<script lang="ts">
  import { Music, Zap, ShieldCheck, Droplets, Eye, Clock, Flame, ArrowRight, Star, StarHalf } from 'lucide-svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import './MobileHero.css';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { ProductVariant } from '$lib/types';
  import { fomoStore } from '$lib/state/commerce/fomo.svelte.ts';

  let { product } = $props();
  const shopStore = getShopStore();
  const currentVariant = $derived(shopStore.variant);
  
  const metadata = $derived(product?.metadata || {});
  const variantOptions = $derived(product?.tierVariations?.[0]?.options || []);

  const viewers = $derived(fomoStore.viewers);
  const stockLeft = $derived(fomoStore.stockLeft);
  const totalSales = $derived(fomoStore.totalSales);
  
  let timerSeconds = $state(2 * 3600 + 45 * 60 + 12); // Flash sale count
  const formattedSales = $derived((totalSales / 1000).toFixed(1) + 'k');

  $effect(() => {
    const countdown = setInterval(() => {
      if (timerSeconds > 0) timerSeconds--;
    }, 1000);

    return () => {
      clearInterval(countdown);
    };
  });

  const formattedTime = $derived.by((): string => {
    const h = Math.floor(timerSeconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((timerSeconds % 3600) / 60).toString().padStart(2, '0');
    const s = (timerSeconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  });
  
  const metrics = $derived.by(() => {
    const raw = metadata.hero_metrics || [];
    const fallbacks = [
      { label: '[Khoa học]', value: 'LIPOSOME PHÁ GỐC THÂM', color: 'blue' },
      { label: '[Hiệu quả]', value: 'DỨT ĐIỂM HẮC SẮC TỐ', color: 'indigo' },
      { label: '[Tiêu chuẩn]', value: 'SỐ 1 DƯỢC LIỆU NHẬT', color: 'emerald' }
    ];

    return fallbacks.map((fb, i) => {
      const custom = raw[i];
      if (!custom) return fb;
      return {
        label: custom.label || fb.label,
        value: custom.value || fb.value,
        color: custom.color || fb.color
      };
    });
  });

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
      {@const mobileImg = (product?.tierVariations?.[0]?.mobile_images?.[i]) || (product?.mobileImages?.[i])}
      <div class="variant-slide relative">
         <!-- Main Content Image (Elite Adaptive Rendering) -->
         <EditableWrapper 
           path="tierVariations[0].mobile_images[{i}]" 
           type="image" 
           label="SỬA ẢNH BIẾN THỂ {i+1}"
           class="w-full h-full"
         >
           <img
             src={resolveMediaUrl(mobileImg || product?.tierVariations?.[0]?.images?.[i] || (product?.images?.length ? product.images[0] : ''))}
             alt="{product?.name} - {opt}"
             class="w-full h-full object-cover select-none"
             loading={i === 0 ? "eager" : "lazy"}
             fetchpriority={i === 0 ? "high" : "low"}
           />
         </EditableWrapper>

         <!-- Cinematic Smooth Gradient (Elite 2026 Black-Bottom) -->
         <div class="absolute inset-0 bg-gradient-to-t from-black via-black/10 to-transparent pointer-events-none"></div>

          <!-- Product Info Overlay -->
          <div class="hero-info-overlay">
            <!-- Live & Scarcity Indicator (Viral 2026) -->
            <div class="inline-flex items-center gap-2 px-2.5 py-1 bg-white/15 backdrop-blur-2xl rounded-full border border-white/20 shadow-[0_4px_24px_rgba(255,59,48,0.2)] mb-1.5 w-max">
               <div class="relative flex h-2 w-2">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ff3b30] opacity-80"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-[#ff3b30]"></span>
               </div>
               <span class="text-[10px] font-black text-white tracking-wider flex items-center gap-1">
                  {viewers} <span class="text-white/60 font-medium">BẠN ĐANG XEM</span>
               </span>
               <div class="w-[1px] h-3 bg-white/30 mx-1"></div>
               <Flame class="w-3.5 h-3.5 text-[#ffcc00] fill-[#ffcc00]" />
               <span class="text-[10px] font-black text-[#ffcc00] tracking-wide">
                  HÀNG SẮP HẾT
               </span>
            </div>

            <!-- Pricing Row -->
            <!-- Pricing Row -->
            <EditableWrapper path="price" label="SỬA GIÁ GỐC" class="block w-full pointer-events-auto">
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
            </EditableWrapper>

            <!-- Title & Variant -->
            <!-- Title & Variant -->
            <EditableWrapper path="name" label="SỬA TÊN SẢN PHẨM" class="block w-full pointer-events-auto">
              <h1 class="text-3xl font-black leading-tight text-white uppercase tracking-tight italic pr-14 drop-shadow-2xl">
                {opt} <span class="text-sakura-pink">.</span>
              </h1>
            </EditableWrapper>

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

            <EditableWrapper path="shortDescription" label="SỬA MÔ TẢ NGẮN" class="max-w-[90%] pr-14 pointer-events-auto">
               <p class="text-[12px] text-white/90 line-clamp-2 leading-relaxed italic font-medium drop-shadow-sm">
                  {product?.shortDescription || 'Phác đồ Liposome dứt điểm hắc sắc tố, tái sinh vùng da thâm sạm.'}
               </p>
            </EditableWrapper>
            
            <div class="flex flex-wrap gap-2 mt-1 pr-14">
              {#each metrics.slice(0, 3) as metric, i}
                {@const Icon = iconMap[metric.color] || Zap}
                <div class="flex items-center gap-1.5 px-2.5 py-1 bg-white/10 backdrop-blur-xl rounded-md border border-white/20 shadow-lg pointer-events-auto">
                    <Icon class="w-3 h-3 text-{metric.color || 'blue'}-400" />
                    <EditableWrapper path="metadata.hero_metrics[{i}].value" value={metric.value} label="SỬA GIÁ TRỊ {i+1}">
                      <span class="text-[9px] font-black text-white/90 uppercase tracking-tight">
                        {metric.value}
                      </span>
                    </EditableWrapper>
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
                  <div class="flex items-center gap-3 relative z-surface">
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
                  <div class="flex flex-col items-end justify-center relative z-surface mt-[1px]">
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
