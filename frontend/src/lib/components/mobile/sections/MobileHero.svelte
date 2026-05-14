<script lang="ts">
    import Zap from "@lucide/svelte/icons/zap";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Droplets from "@lucide/svelte/icons/droplets";
  import Flame from "@lucide/svelte/icons/flame";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import Star from "@lucide/svelte/icons/star";
  import StarHalf from "@lucide/svelte/icons/star-half";
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import './MobileHero.css';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { Product, ProductVariant } from '$lib/types';
  import { fomoStore } from '$lib/state/commerce/fomo.svelte.ts';
  import MobileVariantTabs from '../MobileVariantTabs.svelte';
  import { formatCurrency } from '$lib/utils/format';

  let { product: propProduct } = $props<{ product: Product | null }>();
  const shopStore = getShopStore();
  const currentVariant = $derived(shopStore.variant);
  
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : (propProduct || shopStore.product));
  const metadata = $derived(product?.metadata || {});

  const stripTags = (h: string) => h ? h.replace(/<[^>]*>?/gm, '').trim() : '';
  const legacyParts = $derived(metadata.hero_headline?.split('<br/>') || []);
  const h1 = $derived(metadata.hero_headline_1 || stripTags(legacyParts[0]) || 'LÀN DA TRẮNG SÁNG');
  const h2 = $derived(metadata.hero_headline_2 || stripTags(legacyParts[1]) || 'CHUẨN NHẬT BẢN');
  const variantOptions = $derived(product?.tierVariations?.[0]?.options || []);

  const viewers = $derived(fomoStore.viewers);
  const stockLeft = $derived(fomoStore.stockLeft);
  const totalSales = $derived(fomoStore.totalSales);
  const formattedSales = $derived((totalSales / 1000).toFixed(1) + "k");
  
  // Elite V2.2: Dynamic Countdown logic instead of hardcode
  const flashSaleEnd = $derived(metadata.flash_sale_end ? new Date(metadata.flash_sale_end).getTime() : 0);
  let timerSeconds = $state(0);

  $effect(() => {
    const updateTimer = () => {
        const now = Date.now();
        if (flashSaleEnd > now) {
            const diff = Math.max(0, Math.floor((flashSaleEnd - now) / 1000));
            timerSeconds = diff;
        } else {
            // Fallback: Nếu không có cấu hình hoặc đã hết hạn, đếm đến cuối ngày hôm nay
            const nowDate = new Date();
            const endOfDay = new Date(nowDate.getFullYear(), nowDate.getMonth(), nowDate.getDate(), 23, 59, 59);
            timerSeconds = Math.max(0, Math.floor((endOfDay.getTime() - nowDate.getTime()) / 1000));
        }
    };
    
    updateTimer();
    const countdown = setInterval(updateTimer, 1000);

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
      { label: '[Khoa học]', value: 'LIPOSOME PHÁ GỐC THÂM', color: 'sakura' },
      { label: '[Hiệu quả]', value: 'DỨT ĐIỂM HẮC SẮC TỐ', color: 'sakura' },
      { label: '[Tiêu chuẩn]', value: 'SỐ 1 DƯỢC LIỆU NHẬT', color: 'sakura' }
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
    const width = variantScroller.clientWidth || window.innerWidth;
    const index = Math.round(variantScroller.scrollLeft / width);
    if (currentVariant?.tierIndex[0] !== index) {
      shopStore.selectVariantByTier([index]);
    }
  }

  $effect(() => {
    if (variantScroller && currentVariant) {
      const width = variantScroller.clientWidth || window.innerWidth;
      const targetX = currentVariant.tierIndex[0] * width;
      if (Math.abs(variantScroller.scrollLeft - targetX) > 10) {
        variantScroller.scrollTo({ left: targetX, behavior: 'smooth' });
      }
    }
  });

  // Elite V2.2: Gifts Interface for Static Typing
  interface GiftItem {
    name: string;
    qty: number;
    image?: string;
  }


  const iconMap: Record<string, typeof Zap> = { blue: Zap, indigo: ShieldCheck, emerald: Droplets };
  const fallbackDesc = 'Phác đồ Liposome dứt điểm hắc sắc tố, tái sinh vùng da thâm sạm.';

  function getProcessedDescription(vItem: ProductVariant | undefined) {
    let desc = vItem?.attributes?.short_description || product?.shortDescription || fallbackDesc;
    const keyword = "Beppin Body Virgin White Serum";
    
    if (desc.includes('<h1') && desc.includes(keyword)) return desc;

    if (desc.includes('<span') && desc.includes(keyword)) {
      desc = desc.replace(
        /<span([^>]*)>(.*?Beppin Body Virgin White Serum.*?)<\/span>/gi,
        '<h1 style="display:inline;font-size:inherit;font-weight:inherit;margin:0;padding:0;color:inherit">$2</h1>'
      );
      if (desc.includes('<h1')) return desc;
    }

    return desc.replace(
      new RegExp(keyword, 'gi'),
      `<h1 class="inline font-semibold" style="font-size:inherit;margin:0;padding:0;color:inherit">$&</h1>`
    );
  }
</script>

<div class="h-full w-full relative group">
  <MobileVariantTabs />
  <div 
    class="variant-slider-container h-full" 
    bind:this={variantScroller}
    onscroll={syncVariantOnScroll}
  >
    {#each variantOptions as opt, i}
      {@const v = product?.variants?.find((varItem: ProductVariant) => varItem.tierIndex[0] === i)}
      {@const mobileImg = (product?.tierVariations?.[0]?.mobile_images?.[i]) || (product?.mobileImages?.[i])}
      
      <!-- Elite V2.2: Pre-calculate dynamic content & rating for R00 compliance -->
      {@const variantH1 = v?.attributes?.hero_headline_1 || h1}
      {@const variantH2 = v?.attributes?.hero_headline_2 || h2}
      {@const rating = product?.rating || 4.9}
      {@const fullStars = Math.floor(rating)}
      {@const hasHalfStar = rating % 1 >= 0.5}

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
             alt="{product?.name || "Sản phẩm"} - {opt}"
             width="390"
             height="844"
             class="w-full h-full object-cover select-none"
             loading={i === 0 ? "eager" : "lazy"}
             fetchpriority={i === 0 ? "high" : "low"}
           />
         </EditableWrapper>

         <!-- Cinematic Smooth Gradient (Elite 2026 Black-Bottom) -->
         <div class="absolute inset-0 bg-gradient-to-t from-black via-black/10 to-transparent pointer-events-none"></div>

          <!-- Product Info Overlay -->
          <div class="hero-info-overlay container !px-2">
            <!-- Live & Scarcity Indicator (Viral 2026) -->
            <div class="elite-status-pill mb-1.5 shadow-[0_4px_24px_rgba(255,59,48,0.2)]" style="padding: 0.35rem 0.75rem; font-size: 10px;">
               <div class="elite-dot-container">
                  <span class="elite-status-dot"></span>
               </div>
               <span class="elite-status-text tracking-wider flex items-center gap-1">
                  {viewers} <span class="text-white/60 font-semibold lowercase">bạn đang xem</span>
               </span>
            </div>

            <!-- Pricing Row -->
            <EditableWrapper path="price" label="SỬA GIÁ GỐC" class="block w-full pointer-events-auto">
              <div class="flex items-end gap-3 mt-1 pr-14">
                {#if v?.discountPrice}
                    <span class="text-3xl font-extrabold text-white tracking-tighter drop-shadow-md">
                        {formatCurrency(v.discountPrice)}
                    </span>
                    <span class="text-sm text-white/40 line-through mb-1 font-bold">
                        {formatCurrency(v.price)}
                    </span>
                {:else if v}
                    <span class="text-3xl font-extrabold text-white tracking-tighter drop-shadow-md">
                        {formatCurrency(v.price)}
                    </span>
                {/if}
              </div>
            </EditableWrapper>

            <!-- Title & Variant (Elite Dynamic Content) -->
            <div class="mb-4">
              <!-- Removed slogan slot as requested -->
              
              {#if i === 0}
                <div class="hero-title text-3xl font-extrabold text-white tracking-tighter italic leading-tight bg-clip-text">
                  Miccosmo Beppin Body Virgin White Serum
                </div>
              {/if}

              <!-- Removed subtitle slot as requested -->
            </div>

            <!-- Trust / Review Badge (Elite R00 Compliant) -->
            <div class="flex items-center gap-1.5 mt-0.5 mb-1.5 pr-14">
               <div class="flex items-center gap-[2px]">
                  {#each Array(fullStars) as _}
                    <Star class="w-3.5 h-3.5 text-[#ffcc00] fill-[#ffcc00] drop-shadow-md" />
                  {/each}
                  {#if hasHalfStar}
                    <StarHalf class="w-3.5 h-3.5 text-[#ffcc00] fill-[#ffcc00] drop-shadow-md" />
                  {/if}
               </div>
               <span class="text-[11px] font-black text-white/95 tracking-wide drop-shadow-md">{rating}/5</span>
               <span class="text-[10px] text-white/70 tracking-wide font-medium ml-1">· {formattedSales} đã bán</span>
            </div>

            <p class="text-[12px] text-white/90 line-clamp-2 leading-relaxed italic font-medium drop-shadow-sm">
              <EditableWrapper path={v ? `variants[${product.variants.indexOf(v)}].attributes.short_description` : 'shortDescription'} label="SỬA MÔ TẢ NGẮN" as="span">
                  {@html getProcessedDescription(v)}
              </EditableWrapper>
            </p>
            
            <div class="flex flex-wrap gap-2 mt-1 pr-14">
              {#each metrics.slice(0, 3) as metric, i}
                {@const Icon = iconMap[metric.color] || Zap}
                <div class="flex items-center gap-1.5 px-2.5 py-1 bg-white/10 backdrop-blur-xl rounded-md border border-white/20 shadow-lg pointer-events-auto">
                    <Icon class="w-3 h-3 text-[#FFB7C5]" />
                    <EditableWrapper path="metadata.hero_metrics[{i}].value" value={metric.value} label="SỬA GIÁ TRỊ {i+1}" as="span">
                      <span class="metric-value text-[10px] font-bold text-white/90 tracking-tight">
                        {metric.value}
                      </span>
                    </EditableWrapper>
                </div>
              {/each}
            </div>

            <!-- VIRAL 2026: COMBO & GIFT INJECTION (Elite Ultra-Lean) -->
            {#if v?.attributes?.combo_qty || (v?.attributes?.gifts && v.attributes.gifts.length > 0)}
               <div class="mt-2 pr-14 space-y-1.5 pointer-events-auto">
                  {#if v.attributes.combo_qty && v.attributes.combo_qty > 1}
                     <div class="inline-flex items-center gap-1.5 px-2 py-0.5 bg-gradient-to-r from-[#FFB7C5] to-[#FF8FA3] rounded-full shadow-[0_4px_12px_rgba(255,183,197,0.3)] animate-pulse-gentle">
                        <Flame class="w-2.5 h-2.5 text-white fill-white" />
                        <span class="text-[10px] font-bold text-white uppercase tracking-widest italic leading-none">
                           TIẾT KIỆM COMBO X{v.attributes.combo_qty}
                        </span>
                     </div>
                  {/if}

                  {#if v.attributes.gifts && v.attributes.gifts.length > 0}
                     <div class="bg-black/40 backdrop-blur-3xl rounded-xl p-2.5 border border-white/10 shadow-2xl group/gift-box relative overflow-hidden max-w-[280px]">
                        <!-- Subtle Shimmer -->
                        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover/gift-box:translate-x-full transition-transform duration-1000"></div>
                        
                        <div class="flex items-center gap-3 relative z-10">
                           <div class="w-11 h-11 rounded-lg overflow-hidden bg-white/10 border border-white/10 shrink-0 shadow-inner">
                              <img 
                                 src={resolveMediaUrl((v.attributes.gifts[0] as GiftItem).image || product?.mobileImages?.[0] || product?.images?.[0])} 
                                 alt="Quà tặng đặc quyền - {product?.name || "Miccosmo"} " 
                                 loading="lazy"
                                 decoding="async"
                                 width="44"
                                 height="44"
                                 class="w-full h-full object-cover" 
                              />
                           </div>
                           
                           <div class="flex-1 min-w-0">
                              <div class="text-[10px] font-bold text-white/30 uppercase tracking-[0.15em] mb-0.5 font-mono leading-none">Quà tặng đặc quyền</div>
                              <div class="space-y-0.5">
                                 {#each (v.attributes.gifts as GiftItem[]) as gift}
                                    <div class="flex items-center justify-between gap-1.5">
                                       <span class="text-[10.5px] font-bold text-white drop-shadow-md truncate leading-tight">{gift.name}</span>
                                       <span class="text-[10px] font-black text-[#ffcc00] italic shrink-0">x{gift.qty}</span>
                                    </div>
                                 {/each}
                              </div>
                           </div>
                        </div>
                     </div>
                  {/if}
               </div>
            {/if}

            <!-- CTA Button (Elite 2026 Viral Pill) -->
            <div class="mt-2.5 w-full pr-14 relative z-surface pointer-events-auto">
                <button 
                   class="relative w-[285px] max-w-full group flex items-center justify-between p-1 pr-4 bg-white/10 backdrop-blur-[25px] border border-white/10 rounded-full shadow-[0_8px_32px_rgba(0,0,0,0.3)] active:scale-[0.98] transition-all duration-300 pointer-events-auto cursor-pointer"
                   onclick={() => {
                      // 🚀 ELITE V2.2: Hard-targeted navigation for treatment section
                      if (typeof navigator !== 'undefined' && navigator.vibrate) navigator.vibrate(10);
                      
                      const target = document.getElementById('offer-section');
                      if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                      } else {
                        // Fallback: Force scroll container to bottom
                        const container = document.querySelector('.mobile-snap-container');
                        if (container) {
                          container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
                        }
                      }
                   }}
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
                        <span class="cta-primary-text text-[12px] font-bold text-white tracking-wider leading-[1.1] mb-[1.5px]">Xem liệu trình</span>
                        <span class="cta-secondary-text text-[10px] font-bold text-[#FFB7C5] tracking-widest flex items-center gap-1 leading-none drop-shadow-md">
                           <Zap class="w-2.5 h-2.5" /> Freeship hỏa tốc
                        </span>
                     </div>
                  </div>
                  
                  <!-- Right: Countdown -->
                  <div class="flex flex-col items-end justify-center relative z-surface mt-[1px]">
                     <span class="cta-timer-label text-[10px] font-bold text-white/50 tracking-widest mb-[1.5px]">Kết thúc sau</span>
                     <span class="text-[11px] font-bold text-white font-mono tracking-tighter drop-shadow-md leading-none">{formattedTime}</span>
                  </div>
               </button>
            </div>
         </div>
      </div>
    {/each}
  </div>
</div>
