<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import { fomoStore } from '$lib/state/commerce/fomo.svelte.ts';
  import { SHOP_CONFIG, OFFER_CONSTANTS } from '$lib/constants/shop';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import type { ProductVariant } from '$lib/types';
  import { ShoppingCart, Clock, Zap, Check } from 'lucide-svelte';
  
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  let { product: propProduct } = $props();
  const shopStore = getShopStore();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : (propProduct || shopStore.product));
  const variants = $derived(product?.variants || []);
  const timeLeft = $derived(shopStore.timeLeft);
  const metadata = $derived(product?.metadata || {});

  const stripTags = (h: string) => h ? h.replace(/<[^>]*>?/gm, '').trim() : '';
  const legacyParts = $derived(metadata.offer_headline?.split('<br/>') || []);
  const h1 = $derived(metadata.offer_headline_1 || stripTags(legacyParts[0]) || product?.name || "Siêu ưu đãi độc quyền");
  const h2 = $derived(metadata.offer_headline_2 || stripTags(legacyParts[1]) || "");

  const foundIndex = $derived(variants.findIndex(v => v.id === shopStore.variant?.id));
  const selectedIndex = $derived(foundIndex !== -1 ? foundIndex : (variants.length > 1 ? 1 : 0));
  const selectedVariant = $derived(variants[selectedIndex] ?? variants[0]);

  const mkt = $derived({
    headline: metadata?.offer_headline || product?.name || "Ưu đãi đặc biệt",
    sub: metadata?.offer_subheadline || (product?.metadata?.brand ? `Thương hiệu: ${product.metadata.brand}` : "Cam kết hiệu quả từ gốc tế bào."),
    timer_prefix: metadata?.offer_timer_prefix || "Ưu đãi kết thúc sau:",
    shipping_prefix: metadata?.offer_shipping_prefix || "+ Phí vận chuyển:",
    savings_prefix: metadata?.offer_savings_prefix || "Tiết kiệm:",
    label_expert_choice: metadata?.offer_label_expert_choice || "Chuyên gia khuyên dùng",
    cta_start: metadata?.offer_cta_start || OFFER_CONSTANTS.labels.cta_start,
    cta_full: metadata?.offer_cta_full || OFFER_CONSTANTS.labels.cta_full,
  });

  const productVouchers = $derived.by(() => {
    // 1. Check if product has specific override vouchers in metadata
    if (Array.isArray(product?.metadata?.vouchers) && product.metadata.vouchers.length > 0) {
      return product.metadata.vouchers;
    }
    
    // 2. Fallback to global active vouchers from ShopStore (Elite V2.2)
    return (shopStore.vouchers || []).map(v => ({
      id: v.id,
      label: v.title || v.id,
      sub: v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : `Giảm ${v.value.toLocaleString()}đ`),
      type: v.type === 'SHIPPING' ? 'ship' : 'discount'
    }));
  });

  const formatTime = (s: number): string => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  function getVariantTitle(variant: ProductVariant): string {
    if (!product?.tierVariations?.length || !variant.tierIndex?.length) return variant.name || variant.sku || 'Combo';
    return variant.tierIndex.map((optIdx: number, tierIdx: number) => {
      const option = product.tierVariations![tierIdx]?.options[optIdx];
      if (typeof option === 'string') return option;
      if (typeof option === 'object' && option) return (option.name || option.label || '');
      return '';
    }).filter(Boolean).join(' - ') || variant.name || 'Combo';
  }

  function handleSelect(i: number) {
     if (variants[i]) {
       shopStore.selectVariant(variants[i]);
     }
  }

  const noiseSvg = `data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E`;
</script>

<div class="h-full w-full container flex flex-col !px-0 !max-w-none pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] relative overflow-hidden bg-black">
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


  <!-- Optimized Premium Scarcity HUD (Viral 2026) -->
  <div class="mt-3 mb-2 flex flex-col items-center gap-3 z-surface !px-2">
    <div class="flex items-center gap-1 p-1 bg-white/[0.03] border border-white/10 rounded-full backdrop-blur-3xl shadow-2xl overflow-hidden relative group">
       <!-- Active Glow Background -->
       <div class="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
       
       <!-- Inner Timer Pill -->
       <div class="bg-red-500/10 px-3 py-1.5 rounded-full flex items-center gap-2 border border-red-500/20 relative">
          <Clock class="w-3 h-3 text-red-500 animate-pulse" />
          <span class="text-[10px] text-white font-black tabular-nums tracking-widest">{formatTime(timeLeft)}</span>
       </div>

       <div class="w-[1px] h-3 bg-white/10 mx-1"></div>

       <!-- Viewers Tracking -->
       <div class="flex items-center gap-2 px-2">
          <div class="relative flex h-1.5 w-1.5">
             <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-500 opacity-75"></span>
             <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-blue-500"></span>
          </div>
          <span class="text-[9px] font-bold text-white/50">{fomoStore.viewers} đang xem</span>
       </div>

       <div class="w-[1px] h-3 bg-white/10 mx-1"></div>

       <!-- Scarcity Tag -->
       <div class="flex items-center gap-1.5 pr-3 pl-1">
          <Zap class="w-2.5 h-2.5 text-amber-500/80 animate-bounce" />
          <span class="text-[9px] font-bold text-amber-500/70">Sắp hết hàng</span>
       </div>
    </div>

    <!-- Master Branding Headline -->
    <div class="text-center mt-1 w-full !px-2">
      <div class="max-w-4xl mx-auto text-center relative mb-0">
      <h3 class="text-2xl font-black text-center text-white italic tracking-tighter uppercase mb-4">
        <EditableWrapper path="metadata.offer_headline_1" type="text" label="SỬA TIÊU ĐỀ 1" class="inline" as="span">
          {h1}
        </EditableWrapper>
        <br/>
        <EditableWrapper path="metadata.offer_headline_2" type="text" label="SỬA TIÊU ĐỀ 2" class="inline" as="span">
          {h2}
        </EditableWrapper>
      </h3>

      <p class="text-[10px] text-[#A6C0FE] tracking-widest font-bold opacity-70">
        <EditableWrapper path="metadata.offer_subheadline" type="text" label="SỬA MÔ TẢ PHỤ" as="span">
          {product?.metadata?.offer_subheadline || "Nhưng chúng tôi cam kết: Phá vỡ từ gốc tế bào."}
        </EditableWrapper>
      </p>
    </div>
  </div>
  </div>
  <div class="flex-1 flex flex-col z-surface overflow-y-auto pb-4 space-y-2.5 !px-0">
    <div class="mt-0 !w-full">
       <div class="grid grid-cols-1 gap-0">
         {#each variants as variant, i}
            {@const cQty = variant.attributes?.combo_qty || variant.attributes?.comboQty || 0}
            {@const vPrice = variant.discountPrice || variant.discount_price || variant.price}
            {@const vGifts = variant.attributes?.gifts || []}
            <button 
              onclick={() => handleSelect(i)}
             class="relative w-full text-left py-3 !px-0 border-y border-x-0 transition-all duration-700 active:scale-[0.98] {selectedIndex === i ? 'bg-white/[0.06] backdrop-blur-3xl text-white border-white/10 shadow-[0_25px_80px_rgba(0,0,0,0.3)] z-surface' : 'bg-transparent text-white/30 border-white/5 hover:bg-white/5'}"
            >
               <!-- Liquid Backglow (Only Active) -->
               {#if selectedIndex === i}
                  <div class="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-transparent pointer-events-none"></div>
               {/if}

               <!-- Internal Content Standard Alignment (Viral Symmetry) -->
               <div class="flex items-center gap-4 px-2 w-full">
                 <!-- Floating Selection Status (Liquid Stick - Left) -->
                 <div class="relative w-1 h-10 shrink-0">
                    {#if selectedIndex === i}
                       <div class="absolute inset-0 w-full bg-gradient-to-b from-blue-400 to-blue-600 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.8)]" in:fly={{ y: -10 }}></div>
                    {:else}
                       <div class="absolute inset-0 w-full bg-white/5 rounded-full"></div>
                    {/if}
                 </div>
                 <!-- Liquid Image Container (Premium iPhone 18 Style) -->
                 <div class="w-20 h-20 rounded-[2px] overflow-hidden flex items-center justify-center shrink-0 shadow-inner relative transition-all duration-700 {selectedIndex === i ? 'bg-white/10 scale-105 shadow-2xl ring-1 ring-white/20' : 'bg-white/5 border border-white/5 opacity-40'}">
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

                 <div class="flex-1 flex flex-col justify-center gap-1">
                    <div class="flex flex-wrap items-center gap-1.5 mb-1">
                       {#if i === 1}
                          <div class="bg-gradient-to-r from-amber-400/20 to-orange-500/20 border border-amber-500/30 text-amber-600 px-2.5 py-0.5 rounded-full font-black text-[7px] uppercase tracking-[0.15em] flex items-center gap-1 shadow-sm backdrop-blur-md">
                             <span class="text-[9px]"></span> {mkt.label_expert_choice}
                          </div>
                       {/if}
                       {#if cQty > 1}
                         <div class="bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full font-black text-[7px] uppercase tracking-widest">
                           Combo x{cQty}
                         </div>
                       {/if}
                    </div>
                   <span class="font-black uppercase tracking-tight italic text-[15px] leading-tight transition-colors duration-500 {selectedIndex === i ? 'text-white' : 'text-white/40'}">{getVariantTitle(variant)}</span>
                   <div class="flex items-center gap-3">
                     <span class="font-black text-[24px] italic tracking-tight leading-none transition-all duration-500 {selectedIndex === i ? 'text-blue-400' : 'text-blue-400/40'}">{vPrice.toLocaleString()}đ</span>
                     {#if variant.price > vPrice}
                       <span class="text-[12px] {selectedIndex === i ? 'text-white/20' : 'text-white/10'} line-through font-bold opacity-60">{(variant.price).toLocaleString()}đ</span>
                     {/if}
                   </div>

                   <!-- Mini Gifts (Viral 2026 UI) -->
                   {#if vGifts.length > 0}
                     <div class="mt-2 flex flex-wrap gap-2">
                       {#each vGifts as gift}
                         <div class="flex items-center gap-1.5 bg-white/5 py-1 px-1.5 rounded-lg border border-white/5 group/gift">
                            <div class="w-5 h-5 rounded-md overflow-hidden bg-black/40 border border-white/10 shrink-0">
                               {#if gift.image}
                                 <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                               {:else}
                                 <div class="w-full h-full flex items-center justify-center text-[6px] text-white/20 uppercase font-black">Gift</div>
                               {/if}
                            </div>
                            <span class="text-[8px] font-bold {selectedIndex === i ? 'text-white/70' : 'text-white/20'} truncate max-w-[60px]">{gift.name}</span>
                            <span class="text-[8px] font-black text-amber-500 opacity-80">x{gift.qty}</span>
                         </div>
                       {/each}
                     </div>
                   {/if}
                 </div>
               </div>
            </button>
         {/each}
       </div>
    </div>

    <!-- 🎁 VIRAL 2026: VOUCHER LISTING (Premium Glass HUD) -->
    {#if productVouchers.length > 0}
      <div class="mt-4 px-2">
        <div class="flex items-center gap-2 mb-3">
           <div class="w-1 h-3 bg-blue-500 rounded-full"></div>
           <span class="text-[10px] font-black text-white/40 uppercase tracking-widest italic">Mã giảm giá độc quyền</span>
        </div>
        <div class="flex gap-3 overflow-x-auto pb-2 no-scrollbar">
           {#each productVouchers as v}
             <div class="relative shrink-0 flex items-center gap-3 bg-white/[0.03] border border-white/10 p-2 pr-4 rounded-xl backdrop-blur-3xl group">
                <!-- Ticket Edge Cutouts -->
                <div class="absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-black rounded-full border border-white/10"></div>
                <div class="absolute -right-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-black rounded-full border border-white/10"></div>
                
                <div class="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                   <Zap class="w-4 h-4 text-blue-400" />
                </div>
                <div class="flex flex-col">
                   <span class="text-[11px] font-black text-blue-400 leading-none">{v.label}</span>
                   <span class="text-[8px] text-white/40 font-bold uppercase mt-1 tracking-tighter italic">{v.sub}</span>
                </div>
             </div>
           {/each}
        </div>
      </div>
    {/if}
  </div>
  
  <!-- Unified CTA (Liquid Sapphire Masterpiece - FOMO Optimized) -->
  <div class="mt-auto z-nav pt-1 pb-1 relative">
      <!-- Upsell/Incentive Header (Only if not optimal) -->
      <div class="flex flex-col gap-4 mb-6">
        {#each (metadata.active_deals || []) as deal}
          {@const isActive = shopStore.quantity === (deal.buy_qty + (deal.get_qty || 0))}
          {@const totalQty = deal.buy_qty + (deal.get_qty || 0)}
          {@const totalOriginal = shopStore.originalPrice * totalQty}
          {@const savings = totalOriginal - deal.fixed_price}
          
          <button 
             onclick={() => shopStore.setQuantity(totalQty)}
             class="w-full text-left relative transition-all duration-700 active:scale-[0.98] py-2 !px-0"
          >
             <!-- 🚀 Selection Backglow (Naked HUD Aesthetic) -->
             {#if isActive}
                <div 
                  class="absolute inset-[-15px] bg-blue-600/[0.07] blur-[30px] rounded-full pointer-events-none transition-all duration-700"
                  in:fade={{ duration: 800 }}
                ></div>
             {/if}

             <!-- Standard Internal Alignment (Viral Standard) -->
             <div class="relative flex items-center justify-between gap-2 px-2">
                <!-- 🎯 Absolute Top-Right Selection Stick (Badge Style) -->
                {#if isActive}
                   <div 
                      class="absolute -top-3 -right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center shadow-[0_4px_12px_rgba(59,130,246,0.6)] z-surface"
                      in:scale={{ duration: 400, start: 0.5 }}
                   >
                      <Check class="w-3.5 h-3.5 text-white stroke-[4]" />
                   </div>
                {/if}

                <div class="flex items-center gap-3 flex-1">
                   <!-- Floating Selection Status (Liquid Stick - Left) -->
                   <div class="relative w-1 h-8 shrink-0">
                      {#if isActive}
                         <div class="absolute inset-0 w-full bg-gradient-to-b from-blue-400 to-blue-600 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.8)]" in:fly={{ y: -10 }}></div>
                      {:else}
                         <div class="absolute inset-0 w-full bg-white/5 rounded-full"></div>
                      {/if}
                   </div>

                   <div class="flex flex-col gap-0.5">
                      <div class="flex items-center gap-2">
                        <span class="text-[11px] font-bold {isActive ? 'text-white/90' : 'text-white/30'} transition-all duration-500">
                           {deal.buy_qty > 0 ? `Mua ${deal.buy_qty}` : ''} {deal.get_qty > 0 ? `tặng ${deal.get_qty}` : ''}
                        </span>
                        {#if isActive}
                           <span class="text-[7.5px] font-black text-blue-400 uppercase tracking-widest bg-blue-500/5 px-1.5 py-0.5 rounded border border-blue-500/10">Khuyên dùng</span>
                        {/if}
                      </div>
                      <h3 class="text-[14px] font-semibold {isActive ? 'text-white' : 'text-white/20'} leading-tight tracking-tight">
                        {deal.label || 'Liệu trình cao cấp'}
                      </h3>
                      <div class="flex items-baseline gap-2 mt-0.5">
                         <span class="text-[18px] font-black {isActive ? 'text-blue-400' : 'text-blue-400/20'} italic tracking-tighter">{(deal.fixed_price).toLocaleString()}đ</span>
                         {#if totalOriginal > deal.fixed_price}
                            <div class="flex items-center gap-1.5 opacity-40">
                               <span class="text-[10px] text-white/20 line-through font-medium">{(totalOriginal).toLocaleString()}đ</span>
                               <span class="text-[9px] text-emerald-400 font-bold tracking-tight">| Freeship</span>
                            </div>
                         {/if}
                      </div>
                   </div>
                </div>

                <div class="flex flex-col items-end gap-1.5 self-end mb-1">
                   {#if savings > 0}
                      <div class="h-4 px-2 flex items-center justify-center bg-emerald-400/10 rounded-full">
                         <span class="text-[8px] font-black text-emerald-400 leading-none tracking-tighter italic">Tiết kiệm {savings.toLocaleString()}đ</span>
                      </div>
                   {/if}
                </div>
             </div>
          </button>
        {/each}
      </div>

      <!-- CTA Action Centered (Viral Standard) -->
      <div class="px-2 pb-2">
        <button 
           onclick={() => { 
             if (!selectedVariant) return;
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
           
           <div class="relative z-surface flex items-center justify-between w-full px-2 gap-2">
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
</div>
