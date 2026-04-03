<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { SHOP_CONFIG, OFFER_CONSTANTS } from '$lib/constants/shop';
  import { resolveMediaUrl } from '$lib/state/utils';
  import type { ProductVariant } from '$lib/types';
  import { ShoppingCart, Clock, CheckCircle2, Lock, Users, Zap } from 'lucide-svelte';
  
  let { product } = $props();
  const shopStore = getShopStore();
  const variants = $derived(product?.variants || []);
  const timeLeft = $derived(shopStore.timeLeft);
  const metadata = $derived(product?.metadata || {});

  let selectedIndex = $state(1);
  const selectedVariant = $derived(variants[selectedIndex] ?? variants[0]);
  const mainDeal = $derived(metadata.active_deals?.[0]);


  const mkt = $derived({
    headline: metadata.offer_headline || "CHÚNG TÔI KHÔNG THỂ <br/> THAY ĐỔI CƠ ĐỊA CỦA BẠN.",
    sub: metadata.offer_subheadline || "NHƯNG CAM KẾT: <span class=\"text-blue-400 font-black\">KHÓA MÙI 48H.</span>",
    timer_prefix: metadata.offer_timer_prefix || "Ưu đãi nội bộ kết thúc sau:",
    shipping_prefix: metadata.offer_shipping_prefix || "+ Phí vận chuyển:",
    savings_prefix: metadata.offer_savings_prefix || "Tiết kiệm:",
    label_activation: metadata.offer_label_activation || OFFER_CONSTANTS.labels.activation,
    label_full_treatment: metadata.offer_label_full_treatment || OFFER_CONSTANTS.labels.full_treatment,
    label_expert_choice: metadata.offer_label_expert_choice || OFFER_CONSTANTS.labels.expert_choice,
    label_scarcity: metadata.offer_label_scarcity || OFFER_CONSTANTS.labels.scarcity,
    cta_start: metadata.offer_cta_start || OFFER_CONSTANTS.labels.cta_start,
    cta_full: metadata.offer_cta_full || OFFER_CONSTANTS.labels.cta_full,
  });

  const formatTime = (s: number): string => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  function getVariantTitle(variant: ProductVariant): string {
    if (!product.tierVariations?.length || !variant.tierIndex?.length) return variant.sku || 'Combo';
    return variant.tierIndex.map((optIdx: number, tierIdx: number) => {
      const option = product.tierVariations![tierIdx]?.options[optIdx];
      if (typeof option === 'string') return option;
      if (typeof option === 'object' && option) return (option.name || option.label || '');
      return '';
    }).filter(Boolean).join(' - ') || 'Combo';
  }

  function handleSelect(i: number) {
     selectedIndex = i;
     shopStore.setQuantity(1);
  }

  const noiseSvg = `data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E`;
</script>

<div class="h-full flex flex-col px-0 pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] relative overflow-hidden bg-black">
  <!-- Premium Ambient Liquid Background (iPhone 18 Aesthetic) -->
  <div class="absolute inset-0 pointer-events-none overflow-hidden">
    <div class="absolute top-[-10%] left-[-10%] w-[120%] h-[120%] opacity-40">
      <!-- Sapphire Liquid Orb -->
      <div 
        class="absolute top-[20%] right-[-10%] w-[70%] h-[70%] rounded-full bg-blue-600/20 blur-[120px] animate-[pulse_8s_infinite]"
      ></div>
      <!-- Emerald Liquid Orb -->
      <div 
        class="absolute bottom-[10%] left-[-20%] w-[80%] h-[80%] rounded-full bg-emerald-600/10 blur-[140px] animate-[pulse_12s_infinite_reverse]"
      ></div>
      <!-- Diamond Glow -->
      <div 
        class="absolute top-[40%] left-[10%] w-[40%] h-[40%] rounded-full bg-indigo-500/15 blur-[100px] animate-pulse"
      ></div>
    </div>
    <!-- Soft Glass Noise Overlay -->
    <div class="absolute inset-0 opacity-[0.03] mix-blend-overlay pointer-events-none" style="background-image: url('{noiseSvg}')"></div>
  </div>


  <!-- Scarcity Floating Header -->
  <div class="mt-2 flex justify-center z-10">
    <div class="bg-black/40 border border-white/10 px-6 py-2.5 rounded-2xl backdrop-blur-3xl flex items-center gap-3 shadow-2xl">
      <Clock class="w-4 h-4 text-red-500 animate-pulse" />
      <div class="flex flex-col">
        <span class="text-[7px] text-white/30 font-black uppercase tracking-[0.3em]">{mkt.timer_prefix}</span>
        <span class="text-[11px] text-white font-black tabular-nums tracking-widest italic">{formatTime(timeLeft)}</span>
      </div>
    </div>
  </div>

  <div class="mt-2 mb-1 text-center z-10 px-6">
    <div class="flex items-center justify-center gap-2 mb-3">
       <div class="bg-red-500/10 border border-red-500/20 px-3 py-1 rounded-full flex items-center gap-2 backdrop-blur-xl">
          <Users class="w-3 h-3 text-red-500 animate-pulse" />
          <span class="text-[9px] font-black text-red-400 uppercase tracking-widest">289 người đang xem</span>
       </div>
       <div class="bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-full flex items-center gap-2 backdrop-blur-xl">
          <Zap class="w-3 h-3 text-amber-500 animate-bounce" />
          <span class="text-[9px] font-black text-amber-400 uppercase tracking-widest">Sắp cháy hàng</span>
       </div>
    </div>
    <h2 class="text-[20px] font-black text-white leading-[1.2] uppercase tracking-tighter italic mb-2 drop-shadow-[0_0_20px_rgba(59,130,246,0.6)]">
      {@html mkt.headline}
    </h2>
    <p class="text-[10px] text-[#A6C0FE] uppercase tracking-[0.2em] font-black italic mt-1 opacity-80">{@html mkt.sub}</p>
  </div>
  <div class="flex-1 flex flex-col z-10 overflow-y-auto pb-4 space-y-2.5">
    <div class="px-1 mt-0">
       <div class="text-[9px] text-white/40 uppercase tracking-[0.4em] font-black mb-4 ml-1 flex items-center gap-2">
          <div class="w-1 h-1 bg-blue-500 rounded-full animate-ping"></div> LỰA CHỌN GÓI:
       </div>
       <div class="grid grid-cols-1 gap-0">
         {#each variants as variant, i}
            <button 
              onclick={() => handleSelect(i)}
              class="relative w-full text-left py-3 px-4 border-y border-x-0 transition-all duration-700 flex items-center gap-4 group active:scale-[0.98] {selectedIndex === i ? 'bg-white/[0.06] backdrop-blur-3xl text-white border-white/10 shadow-[0_25px_80px_rgba(0,0,0,0.3)] z-10' : 'bg-transparent text-white/30 border-white/5 hover:bg-white/5'}"
            >
               <!-- Liquid Border Accent (Only Active) -->
               {#if selectedIndex === i}
                  <div class="absolute left-0 top-0 bottom-0 w-[3px] bg-gradient-to-b from-blue-500 via-indigo-500 to-purple-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]"></div>
                  <div class="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-transparent pointer-events-none"></div>
               {/if}

                 
                 <!-- Liquid Image Container (Premium iPhone 18 Style) -->
                 <div class="w-28 h-28 rounded-[2px] overflow-hidden flex items-center justify-center shrink-0 shadow-inner relative transition-all duration-700 {selectedIndex === i ? 'bg-white/10 scale-105 shadow-2xl ring-1 ring-white/20' : 'bg-white/5 border border-white/5 opacity-40'}">
                    {#if (product.tierVariations?.[0]?.images?.[variant.tierIndex?.[0]]) || variant.image_url || variant.imageUrl || variant.image || (product.images && product.images[i]?.url) || (product.images && product.images[0]?.url)}
                      <img 
                        src={resolveMediaUrl(product.tierVariations?.[0]?.images?.[variant.tierIndex?.[0]] || variant.image_url || variant.imageUrl || variant.image || (product.images && product.images[i]) || (product.images && product.images[0]))} 
                        alt={variant.sku} 
                        class="w-full h-full object-cover transition-all duration-1000 {selectedIndex === i ? 'scale-110 rotate-1 brightness-110' : 'grayscale brightness-50'}" 
                        loading="lazy"
                      />
                    {:else}
                      <div class="flex flex-col items-center justify-center text-[8px] font-black opacity-5 uppercase tracking-widest text-center">
                         Liquid<br/>Glass
                      </div>
                    {/if}
                    
                    <!-- Premium Glass Reflective Coating -->
                    <div class="absolute inset-0 bg-gradient-to-tr from-white/20 to-transparent pointer-events-none opacity-30"></div>
                 </div>

               <div class="flex-1 flex flex-col justify-center gap-1 px-1">
                   <div class="flex flex-wrap items-center gap-1.5 mb-1">
                      {#if i === 1}
                         <div class="bg-gradient-to-r from-amber-400/20 to-orange-500/20 border border-amber-500/30 text-amber-600 px-2.5 py-0.5 rounded-full font-black text-[7px] uppercase tracking-[0.15em] flex items-center gap-1 shadow-sm backdrop-blur-md">
                            <span class="text-[9px]"></span> {mkt.label_expert_choice}
                         </div>
                      {/if}
                   </div>
                  <span class="font-black uppercase tracking-tight italic text-[15px] leading-tight transition-colors duration-500 {selectedIndex === i ? 'text-white' : 'text-white/40'}">{getVariantTitle(variant)}</span>
                  <div class="flex items-center gap-3">
                    <span class="font-black text-[24px] italic tracking-tight leading-none transition-all duration-500 {selectedIndex === i ? 'text-blue-400' : 'text-blue-400/40'}">{(variant.discountPrice || variant.price).toLocaleString()}đ</span>
                    {#if variant.price > (variant.discountPrice || variant.price)}
                      <span class="text-[12px] {selectedIndex === i ? 'text-white/20' : 'text-white/10'} line-through font-bold opacity-60">{(variant.price).toLocaleString()}đ</span>
                    {/if}
                  </div>
               </div>
               
            </button>
         {/each}
       </div>
    </div>

    <!-- Locked Free-ship Badge (Elite FOMO) -->
    <div class="flex items-center justify-center gap-4 py-1">
       <div class="bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-2xl flex items-center gap-3 backdrop-blur-2xl shadow-lg relative overflow-hidden group">
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
          <div class="relative w-6 h-6 flex items-center justify-center bg-emerald-500 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.4)]">
             <Lock class="w-3 h-3 text-white" />
          </div>
          <div class="flex flex-col">
             <span class="text-[9px] font-black text-white uppercase tracking-[0.1em]">Ưu đãi đã được khóa</span>
             <span class="text-[8px] font-bold text-emerald-400/80 uppercase">FREESHIP TOÀN QUỐC CHO BẠN</span>
          </div>
       </div>
       
       <div class="bg-blue-500/10 border border-blue-500/20 px-4 py-2 rounded-2xl flex items-center gap-3 backdrop-blur-2xl shadow-lg">
          <div class="w-6 h-6 flex items-center justify-center bg-blue-500 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.4)]">
             <CheckCircle2 class="w-3.5 h-3.5 text-white" />
          </div>
          <div class="flex flex-col">
             <span class="text-[9px] font-black text-white uppercase tracking-[0.1em]">Kiểm duyệt Elite</span>
             <span class="text-[8px] font-bold text-blue-400/80 uppercase">KIỂM HÀNG - THANH TOÁN</span>
          </div>
       </div>
    </div>
    
  </div>
  
  <!-- Unified CTA (Liquid Sapphire Masterpiece - FOMO Optimized) -->
  <div class="mt-auto z-20 pt-1 pb-1 px-4 relative">
      <!-- Upsell/Incentive Header (Only if not optimal) -->
      <div class="flex flex-col gap-1.5 mb-4 px-4">
        {#each (metadata.active_deals || []) as deal}
          <button 
             onclick={() => shopStore.setQuantity(deal.buy_qty + (deal.get_qty || 0))}
             class="w-full bg-blue-500/10 backdrop-blur-3xl border border-blue-500/20 rounded-2xl px-4 py-1.5 flex items-center justify-between group active:scale-[0.98] transition-all"
          >
             <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 bg-blue-500 rounded-full {shopStore.quantity === (deal.buy_qty + (deal.get_qty || 0)) ? 'animate-ping' : ''}"></div>
                <span class="text-[9px] font-black text-blue-400 uppercase tracking-widest leading-none">
                   Ưu đãi: {deal.label} chỉ còn <span class="text-white">{(deal.fixed_price).toLocaleString()}đ</span>
                </span>
             </div>
             <div class="flex items-center gap-1.5 h-5">
                {#if shopStore.quantity === (deal.buy_qty + (deal.get_qty || 0))}
                   <CheckCircle2 class="w-3.5 h-3.5 text-blue-400" />
                   <span class="text-[8px] font-black text-blue-400">ĐÃ ÁP DỤNG</span>
                {:else}
                   <span class="text-[8px] font-black text-white/40 group-hover:text-white transition-colors uppercase tracking-widest">Áp dụng -></span>
                {/if}
             </div>
          </button>
        {/each}
      </div>

      <button 
         onclick={() => { 
           if (!selectedVariant) return;
           shopStore.selectVariant(selectedVariant); 
           if (mainDeal) shopStore.setQuantity(mainDeal.buy_qty + (mainDeal.get_qty || 0)); 
           else shopStore.setQuantity(1);
           shopStore.openCheckout(); 
         }}
         class="w-full h-[72px] rounded-full font-black text-[15px] uppercase tracking-[0.12em] flex items-center justify-center gap-4 transition-all duration-700 italic active:scale-95 active:brightness-90 bg-white/10 backdrop-blur-3xl border border-white/20 shadow-[0_20px_50px_rgba(59,130,246,0.2)] overflow-hidden relative group"
       >
         <!-- Liquid Sapphire Gradient Fill (Hover/Active) -->
         <div class="absolute inset-0 bg-gradient-to-r from-blue-600/20 via-emerald-500/20 to-indigo-600/20 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
         
         <!-- Internal Fluid Shimmer (Enhanced) -->
         <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-[shimmer_2s_infinite] pointer-events-none"></div>
         
         <!-- Orbital Glow Pulse (FOMO) -->
         <div class="absolute inset-0 rounded-full border border-blue-400/20 animate-pulse opacity-50"></div>
         
         <div class="relative z-10 flex items-center justify-between w-full px-5 gap-2">
            <span class="text-white drop-shadow-md text-[14px] font-black leading-tight flex-1 pr-2">{selectedIndex === 0 ? mkt.cta_start : mkt.cta_full}</span>

            <div class="flex items-center gap-3 shrink-0">
               <div class="flex flex-col items-end leading-tight">
                  {#if (shopStore.originalPrice * shopStore.quantity) > shopStore.totalAmount}
                    <span class="text-[10px] text-white/30 line-through font-bold opacity-60">{(shopStore.originalPrice * shopStore.quantity).toLocaleString()}đ</span>
                  {/if}
                  <span class="text-blue-400 text-[20px] drop-shadow-[0_0_15px_rgba(59,130,246,0.5)] font-black">{shopStore.totalAmount.toLocaleString()}đ</span>
               </div>
               <div class="w-9 h-9 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-400/30">
                  <ShoppingCart class="w-4.5 h-4.5 text-blue-400" />
               </div>
            </div>
         </div>
      </button>
  </div>
</div>
