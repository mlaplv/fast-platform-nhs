<script lang="ts">
  /**
   * ELITE V2.2 - MOBILE OFFER SECTION (iPhone 18 Aesthetic)
   * TikTok Shop Viral Strategy Implementation.
   * Following R00: NO HARDCODING | SENIOR ARCHITECT STANDARDS.
   */
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import { fomoStore } from '$lib/state/commerce/fomo.svelte.ts';
  import { SHOP_CONFIG, OFFER_CONSTANTS, PRIVACY_CONSTANTS } from '$lib/constants/shop';
  import { resolveMediaUrl } from '$lib/state/utils';
  import type { ProductVariant, Product, Voucher } from '$lib/types';
  import { 
    ShoppingCart, Clock, Zap, Check, Gift, Truck, 
    ShieldCheck, Eye, Sparkles, Flame, ShieldAlert, Lock
  } from 'lucide-svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';

  // --- Props & State (Runes) ---
  let { product: propProduct } = $props();
  const shopStore = getShopStore();
  
  // Single Source of Truth for Product Data
  const product: Product | null = $derived(
    liveEditStore.isEditMode && liveEditStore.dirtyProduct 
      ? liveEditStore.dirtyProduct 
      : (propProduct || shopStore.product)
  );

  const variants: ProductVariant[] = $derived(product?.variants || []);
  const timeLeft: number = $derived(shopStore.timeLeft);
  const metadata = $derived(product?.metadata || {});

  // --- Calculated Props ($derived) ---
  const foundIndex: number = $derived(variants.findIndex(v => v.id === shopStore.variant?.id));
  const selectedIndex: number = $derived(foundIndex !== -1 ? foundIndex : (variants.length > 1 ? 1 : 0));
  const selectedVariant: ProductVariant | null = $derived(variants[selectedIndex] ?? variants[0] ?? null);

  const h1: string = $derived(
    metadata.offer_headline_1 || (product?.name ? product.name.split(' ')[0] : "Siêu ưu đãi")
  );
  const h2: string = $derived(
    metadata.offer_headline_2 || (product?.name ? product.name.split(' ').slice(1).join(' ') : "độc quyền")
  );

  const productVouchers = $derived.by(() => {
    const rawVouchers = Array.isArray(product?.metadata?.vouchers) && product.metadata.vouchers.length > 0
      ? product.metadata.vouchers
      : (shopStore.vouchers || []);

    return rawVouchers.map((v: any) => ({
      id: v.id,
      label: v.title || v.id || OFFER_CONSTANTS.labels.voucher_viral_title,
      sub: v.subtitle || (v.type === 'SHIPPING' ? 'Miễn phí vận chuyển' : `Giảm ${v.value?.toLocaleString()}đ`),
      type: v.type === 'SHIPPING' ? 'ship' : 'discount',
      value: v.value || 0,
      type_raw: v.type,
      used_percent: Math.min(95, 60 + Math.floor(Math.random() * 20)) // Viral scarcity simulation
    }));
  });

  // --- Formatting Helpers ---
  const formatTime = (s: number): string => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  /** Architect Note: Explicitly typed title generation */
  function getVariantTitle(v: ProductVariant): string {
    if (!product?.tierVariations?.length || !v.tierIndex?.length) return v.sku || 'Combo';
    return v.tierIndex.map((optIdx: number, tierIdx: number) => {
      const option = product.tierVariations![tierIdx]?.options[optIdx];
      return typeof option === 'string' ? option : (typeof option === 'object' && option ? (option.name || option.label || '') : '');
    }).filter(Boolean).join(' - ') || v.sku || 'Combo';
  }

  // --- Event Handlers ---
  const handleSelect = (i: number) => {
    const v = variants[i];
    if (v) {
      shopStore.selectVariant(v);
      // Tự động đồng bộ số lượng tương ứng với Combo được chọn
      const cQty = v.attributes?.combo_qty || 1;
      shopStore.setQuantity(cQty);
    }
  };

  const noiseSvg = `data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E`;
</script>

<div class="h-full w-full container flex flex-col !px-0 !max-w-none pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] relative overflow-hidden bg-black text-white">
  <!-- 🌊 Premium Ambient Liquid Background -->
  <div class="absolute inset-0 pointer-events-none overflow-hidden">
    <div class="absolute top-[-10%] left-[-10%] w-[120%] h-[120%] opacity-40">
      <div class="absolute top-[20%] right-[-10%] w-[70%] h-[70%] rounded-full bg-blue-600/20 blur-[120px] animate-[pulse_8s_infinite]"></div>
      <div class="absolute bottom-[10%] left-[-20%] w-[80%] h-[80%] rounded-full bg-emerald-600/10 blur-[140px] animate-[pulse_12s_infinite_reverse]"></div>
      <div class="absolute top-[40%] left-[10%] w-[40%] h-[40%] rounded-full bg-indigo-500/15 blur-[100px] animate-pulse"></div>
    </div>
    <div class="absolute inset-0 opacity-[0.03] mix-blend-overlay pointer-events-none" style="background-image: url('{noiseSvg}')"></div>
  </div>

  <!-- 🔥 Optimized Premium Scarcity HUD -->
  <div class="mt-3 mb-2 flex flex-col items-center gap-3 z-surface !px-2">
    <div class="flex items-center gap-1 p-1 bg-white/[0.03] border border-white/10 rounded-full backdrop-blur-3xl shadow-2xl overflow-hidden relative group">
       <div class="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
       <div class="bg-red-500/10 px-3 py-1.5 rounded-full flex items-center gap-2 border border-red-500/20 relative">
          <Clock class="w-3 h-3 text-red-500 animate-pulse" />
          <span class="text-[10px] font-black tabular-nums tracking-widest">{formatTime(timeLeft)}</span>
       </div>
       <div class="w-[1px] h-3 bg-white/10 mx-1"></div>
       <div class="flex items-center gap-2 px-2">
          <div class="relative flex h-1.5 w-1.5"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-500 opacity-75"></span><span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-blue-500"></span></div>
          <span class="text-[9px] font-bold text-white/50">{fomoStore.viewers} đang xem</span>
       </div>
       <div class="w-[1px] h-3 bg-white/10 mx-1 text-white/20">|</div>
       <div class="flex items-center gap-1.5 pr-2">
          <Flame class="w-2.5 h-2.5 text-amber-500 animate-bounce" />
          <span class="text-[9px] font-bold text-amber-500/70">{OFFER_CONSTANTS.labels.scarcity}</span>
       </div>
    </div>

    <!-- Master Branding Headline -->
    <div class="text-center mt-1 w-full !px-3">
      <h3 class="text-2xl font-black text-center text-white italic tracking-tighter uppercase leading-tight mb-2">
        <EditableWrapper path="metadata.offer_headline_1" type="text" label="SỬA TIÊU ĐỀ 1" class="inline" as="span">{h1}</EditableWrapper>
        <br/>
        <EditableWrapper path="metadata.offer_headline_2" type="text" label="SỬA TIÊU ĐỀ 2" class="inline" as="span">{h2}</EditableWrapper>
      </h3>
      <p class="text-[10px] text-[#A6C0FE] tracking-widest font-bold opacity-70 uppercase">
        <EditableWrapper path="metadata.offer_subheadline" type="text" label="SỬA MÔ TẢ PHỤ" as="span">
          {product?.metadata?.offer_subheadline || "SẢN PHẨM KHUYÊN DÙNG ĐỂ ĐẠT HIỆU QUẢ CAO NHẤT"}
        </EditableWrapper>
      </p>
    </div>
  </div>

  <div class="flex-1 flex flex-col z-[var(--z-surface)] overflow-y-auto no-scrollbar pb-6 space-y-4 !px-0">
    <!-- 🎛️ VARIANT SELECTOR (Top HUD) -->
    <div class="mt-0 !w-full">
       <div class="grid grid-cols-1 gap-0">
         {#each variants as variant, i}
            {@const cQty = variant.attributes?.combo_qty || 0}
            {@const vPrice = variant.discountPrice || variant.price}
            {@const isActive = selectedIndex === i}
            
            <button 
              onclick={() => handleSelect(i)}
              class="relative w-full text-left py-4 !px-0 border-y border-x-0 transition-all duration-700 {isActive ? 'bg-white/[0.08] backdrop-blur-3xl text-white border-white/10 z-surface scale-[1.01] shadow-2xl' : 'bg-transparent text-white/30 border-white/5 hover:bg-white/5'}"
            >
               {#if isActive}
                  <div class="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-transparent pointer-events-none transition-all duration-1000"></div>
                  <div class="absolute left-0 top-0 bottom-0 w-1.5 bg-blue-500 animate-pulse"></div>
               {/if}

               <div class="flex items-center gap-4 px-4 w-full">
                 <div class="w-20 h-20 rounded-xl overflow-hidden flex items-center justify-center shrink-0 shadow-inner relative transition-all duration-700 {isActive ? 'bg-white/10 scale-110 rotate-1 ring-2 ring-blue-500/30 shadow-blue-500/20 shadow-xl' : 'bg-white/5 opacity-40'}">
                    {#if (product?.tierVariations?.[0]?.images?.[variant.tierIndex?.[0]]) || variant.image_url || variant.imageUrl || variant.image || (product?.images && product.images[i]?.url) || (product?.images && product.images[0]?.url)}
                      <img 
                        src={resolveMediaUrl(product?.tierVariations?.[0]?.images?.[variant.tierIndex?.[0]] || variant.image_url || variant.imageUrl || (product?.images && product.images[i]) || (product?.images && product.images[0]))} 
                        alt={variant.sku} 
                        class="w-full h-full object-cover transition-all duration-1000 {isActive ? 'scale-110 brightness-110' : 'grayscale brightness-50'}" 
                        loading="lazy"
                      />
                    {/if}
                    <div class="absolute inset-0 bg-gradient-to-tr from-white/20 to-transparent pointer-events-none opacity-30"></div>
                 </div>

                 <div class="flex-1 flex flex-col justify-center gap-1.5">
                    <div class="flex flex-wrap items-center gap-2 mb-1">
                       {#if i === 1}
                          <div class="bg-amber-400 text-black px-2 py-0.5 rounded-md font-black text-[8px] uppercase tracking-widest shadow-lg shadow-amber-400/20">{OFFER_CONSTANTS.labels.expert_choice}</div>
                       {/if}
                       {#if cQty > 1}
                         <div class="bg-blue-500/20 border border-blue-500/30 text-blue-400 px-2 py-0.5 rounded-md font-black text-[8px] uppercase tracking-widest">COMBO X{cQty}</div>
                       {/if}
                    </div>
                   <span class="font-black uppercase tracking-tight italic text-[16px] leading-tight transition-all {isActive ? 'text-white' : 'text-white/40'}">{getVariantTitle(variant)}</span>
                   <div class="flex items-center gap-3">
                     <span class="font-black text-[22px] italic tracking-tighter leading-none transition-all {isActive ? 'text-blue-400 drop-shadow-[0_0_10px_rgba(96,165,250,0.5)]' : 'text-blue-400/40'}">{vPrice.toLocaleString()}đ</span>
                     {#if variant.price > vPrice}
                       <span class="text-[12px] text-white/20 line-through font-bold opacity-60">{(variant.price).toLocaleString()}đ</span>
                     {/if}
                   </div>
                 </div>
               </div>
            </button>
         {/each}
       </div>
    </div>

    <!-- 🎫 VIRAL VOUCHER SECTION (TikTok Style) -->
    {#if productVouchers.length > 0}
      <div class="px-2 py-4">
         <div class="flex items-center justify-between mb-5 px-2">
            <div class="flex items-center gap-2">
               <Sparkles class="w-4 h-4 text-blue-500 animate-pulse" />
               <span class="text-[12px] font-black text-white/60 italic uppercase tracking-[0.2em]">{OFFER_CONSTANTS.labels.voucher_viral_title}</span>
            </div>
            <div class="flex items-center gap-1.5 px-2 py-1 bg-white/10 rounded-full border border-white/5">
              <Eye class="w-3 h-3 text-blue-400" />
              <span class="text-[8px] font-black text-white/50">{fomoStore.recentOrders} người vừa mua</span>
            </div>
         </div>
         
         <div class="flex flex-col gap-4 px-1">
            {#each productVouchers as v}
              {@const isApplied = shopStore.selectedVoucherIds.includes(v.id)}
              <button 
                onclick={() => shopStore.toggleVoucher(v.id)}
                class="w-full text-left relative transition-all duration-500 active:scale-[0.98] group/voucher"
              >
                 {#if isApplied}
                    <div class="absolute inset-[-6px] bg-blue-500/20 blur-[20px] rounded-2xl pointer-events-none transition-all duration-700"></div>
                 {/if}

                 <div class="relative flex h-[90px] bg-[#0F0F0F] border border-white/10 rounded-2xl overflow-hidden transition-all duration-700 {isApplied ? 'border-blue-500/60 shadow-2xl' : 'hover:border-white/20 shadow-lg'}">
                    <!-- Ticket Dashed Perforation -->
                    <div class="absolute left-[85px] top-0 bottom-0 w-px border-l border-dashed border-white/20 z-10 flex flex-col justify-between py-1 opacity-40">
                       {#each Array(6) as _}<div class="w-1.5 h-1.5 -ml-[4px] bg-black rounded-full border border-white/5"></div>{/each}
                    </div>

                    <!-- LEFT: THE VISUAL HOOK -->
                    <div class="w-[88px] h-full bg-gradient-to-br {isApplied ? 'from-blue-600 to-indigo-700 shadow-inner' : 'from-gray-900 to-black'} flex flex-col items-center justify-center transition-all duration-700 shrink-0">
                       <span class="text-[8px] font-black text-white/40 uppercase tracking-tighter mb-1">TIẾT KIỆM</span>
                       <span class="text-[20px] font-black text-white italic tracking-tighter drop-shadow-md">
                          {v.type_raw === 'SHIPPING' ? 'SHIP' : (v.value >= 1000 ? `-${Math.round(v.value/1000)}K` : `-${v.value}%`)}
                       </span>
                    </div>

                    <!-- RIGHT: INFO & PROGRESS -->
                    <div class="flex-1 h-full p-4 pl-6 flex flex-col justify-center relative min-w-0">
                       {#if isApplied}
                          <div class="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-0.5 bg-blue-500 rounded-lg shadow-lg" in:scale>
                             <Check class="w-2.5 h-2.5 text-white stroke-[4]" />
                             <span class="text-[7px] font-black text-white uppercase tracking-widest">ĐÃ LƯU</span>
                          </div>
                       {/if}

                       <div class="flex flex-col gap-1">
                          <span class="text-[14px] font-black italic tracking-tight transition-all {isApplied ? 'text-white' : 'text-blue-400/80'} uppercase">{v.label}</span>
                          <span class="text-[9px] text-white/30 font-bold uppercase tracking-tight truncate">{v.sub}</span>
                          
                          <!-- 📈 Viral Scarcity Progress Bar -->
                          <div class="mt-2.5 space-y-1">
                             <div class="flex items-center justify-between">
                                <span class="text-[7px] font-black text-white/20 uppercase tracking-widest">HẠN DÙNG CÓ HẠN</span>
                                <span class="text-[7px] font-black text-amber-500 italic">{v.used_percent}% {OFFER_CONSTANTS.labels.voucher_used_label}</span>
                             </div>
                             <div class="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
                                <div 
                                  class="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(59,130,246,0.5)]" 
                                  style="width: {v.used_percent}%"
                                ></div>
                             </div>
                          </div>
                       </div>
                    </div>
                 </div>
              </button>
            {/each}
         </div>
      </div>
    {/if}

    <!-- 🎁 SELECTED BENEFIT DETAIL (Promotion Summary) -->
    <div class="px-3">
      <div 
        class="bg-gradient-to-tr from-white/[0.03] to-white/[0.05] border border-white/10 rounded-[2rem] p-6 backdrop-blur-3xl relative overflow-hidden group border-dashed"
      >
         <div class="absolute -right-20 -top-20 w-48 h-48 bg-emerald-500/10 rounded-full blur-[60px] pointer-events-none transition-all group-hover:bg-emerald-500/20"></div>
         
         <div class="flex flex-col gap-5 relative z-10">
            <div class="flex items-center justify-between">
               <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 shadow-inner">
                     <Gift class="w-6 h-6 text-emerald-400" />
                  </div>
                  <div class="flex flex-col">
                     <h4 class="text-[14px] font-black text-white italic uppercase tracking-tight">{OFFER_CONSTANTS.labels.benefit_detail_title}</h4>
                     <p class="text-[9px] text-white/40 font-bold tracking-tight">Quyền lợi đặc biệt tại {product?.metadata?.brand || SHOP_CONFIG.pharmacy.name}</p>
                  </div>
               </div>
               <div class="text-[11px] font-black text-emerald-400 italic">FREESHIP ★</div>
            </div>

            <div class="space-y-2.5">
               {#if selectedVariant?.attributes?.gifts?.length > 0}
                  {#each selectedVariant.attributes.gifts as gift}
                     <div class="flex items-center gap-3 bg-white/[0.04] p-2.5 rounded-2xl border border-white/5 group/gift transition-all hover:border-emerald-500/30">
                        <div class="w-12 h-12 rounded-xl overflow-hidden bg-black/40 border border-white/5 shrink-0">
                           {#if gift.image}
                              <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover" />
                           {:else}
                              <div class="w-full h-full flex items-center justify-center"><Gift class="w-4 h-4 text-white/10" /></div>
                           {/if}
                        </div>
                        <div class="flex flex-col overflow-hidden">
                           <span class="text-[12px] font-black text-emerald-400 italic truncate uppercase">{gift.name}</span>
                           <span class="text-[9px] text-white/40 font-bold uppercase tracking-tighter">Gói Quà Tặng Cao Cấp • SL: {gift.qty}</span>
                        </div>
                     </div>
                  {/each}
               {:else}
                  <div class="bg-white/5 p-4 rounded-xl border border-white/5 text-center">
                    <span class="text-[10px] font-black text-white/20 uppercase tracking-[0.2em]">SẢN PHẨM CHÍNH HÃNG 100%</span>
                  </div>
               {/if}
            </div>

            <div class="flex items-center justify-between mt-2 pt-4 border-t border-white/5">
                <div class="flex items-center gap-2">
                   <Truck class="w-4 h-4 text-blue-400" />
                   <span class="text-[10px] font-black text-blue-400/80 uppercase">Giao hàng {product?.metadata?.brand || SHOP_CONFIG.pharmacy.name}</span>
                </div>
                <div class="flex items-center gap-1.5 px-2 py-1 bg-white/5 rounded-full">
                   <div class="w-1 h-1 rounded-full bg-emerald-500 animate-pulse"></div>
                   <span class="text-[9px] font-black text-white/30 uppercase tracking-tighter">{OFFER_CONSTANTS.labels.sold_count_prefix} {(product?.order_count || 2300).toLocaleString()} suất</span>
                </div>
            </div>
         </div>
      </div>
    </div>

    <!-- 🛡️ HIGH-PRIVACY CAPSULE (Moved to bottom & Optimized for Viral) -->
    <div class="px-3 pt-4">
      <div 
        class="relative overflow-hidden p-6 rounded-[3rem] bg-gradient-to-br from-[#FFF8F8] to-[#FFFAF5] border border-orange-200/40 shadow-2xl transition-all duration-700 {shopStore.isStealthMode ? 'scale-[1.01] shadow-orange-500/10' : 'grayscale-[0.6] opacity-70'}"
      >
        <!-- Liquid Glow Accent -->
        <div class="absolute -right-12 -top-12 w-48 h-48 bg-orange-400/10 rounded-full blur-[50px] pointer-events-none"></div>
        <div class="absolute left-10 bottom-0 w-24 h-1 bg-gradient-to-r from-transparent via-orange-500/20 to-transparent"></div>
        
        <div class="flex items-center justify-between gap-4 mb-5">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 shrink-0 rounded-[1.2rem] bg-gradient-to-br from-[#FF4D4D] to-[#F43F5E] shadow-xl shadow-red-500/40 flex items-center justify-center text-white relative">
              <div class="absolute inset-0 bg-white/20 animate-pulse rounded-[1.2rem]"></div>
              <Lock class="w-6 h-6 stroke-[2.5] relative z-10" />
            </div>
            <div class="flex flex-col">
              <h4 class="text-[14px] font-black text-[#111827] tracking-tighter uppercase leading-tight italic">{PRIVACY_CONSTANTS.title}</h4>
              <p class="text-[9px] text-[#6B7280] font-bold mt-0.5 tracking-tight leading-none">{PRIVACY_CONSTANTS.sub}</p>
            </div>
          </div>
          
          <!-- Premium Viral Toggle -->
          <button 
            onclick={() => shopStore.toggleStealthMode()}
            class="relative w-[60px] h-[34px] shrink-0 rounded-full transition-all duration-500 {shopStore.isStealthMode ? 'bg-[#FF4D4D]' : 'bg-gray-200'}"
          >
            <div class="absolute inset-0.5 bg-black/5 rounded-full"></div>
            <div 
              class="absolute top-1 left-1 w-[26px] h-[26px] bg-white rounded-full transition-all duration-500 flex items-center justify-center shadow-[0_4px_10px_rgba(0,0,0,0.1)] {shopStore.isStealthMode ? 'translate-x-[26px]' : ''}"
            >
               <span class="block w-1 h-3 bg-red-100 rounded-full opacity-40"></span>
            </div>
          </button>
        </div>

        <!-- Privileges Grid (Refined) -->
        <div class="grid grid-cols-2 gap-x-6 gap-y-3 pl-1">
          {#each PRIVACY_CONSTANTS.benefits as benefit}
            <div class="flex items-center gap-2 group transition-all">
              <div class="w-4 h-4 rounded-full bg-red-500/10 flex items-center justify-center shrink-0">
                 <Check class="w-2.5 h-2.5 text-red-500 stroke-[4]" />
              </div>
              <span class="text-[8px] font-black text-[#FF4D4D] tracking-tight truncate uppercase italic opacity-90">{benefit}</span>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>
  
  <!-- 🛰️ Unified CTA HUD (Cinematic Sapphire) -->
  <div class="mt-auto z-[var(--z-nav)] pt-2 pb-2 relative bg-gradient-to-t from-black via-black/95 to-transparent">
      <div class="px-3 pb-2">
        <button
           onclick={() => { if (!selectedVariant) return; shopStore.openCheckout(); }}
           class="w-full h-[75px] rounded-[2rem] font-black text-[15px] uppercase tracking-[0.15em] flex items-center justify-center transition-all duration-700 italic active:scale-95 bg-white/10 backdrop-blur-3xl border border-white/20 shadow-[0_25px_60px_rgba(59,130,246,0.3)] overflow-hidden relative group"
         >
           <div class="absolute inset-0 bg-gradient-to-r from-blue-600/30 via-transparent to-blue-600/30 opacity-0 group-hover:opacity-100 transition-opacity"></div>
           <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-[shimmer_3s_infinite] pointer-events-none"></div>

           <div class="relative z-[var(--z-surface)] flex items-center justify-between w-full px-6 gap-3">
              <div class="flex flex-col text-left leading-tight min-w-0 flex-1">
                <span class="text-white text-[14px] font-black drop-shadow-md whitespace-normal leading-[1.1] uppercase italic">{selectedIndex === 0 ? OFFER_CONSTANTS.labels.cta_start : OFFER_CONSTANTS.labels.cta_full}</span>
                <span class="text-[9px] text-white/50 font-bold uppercase tracking-[0.1em] mt-1 italic">Số lượng: {shopStore.quantity}</span>
              </div>

              <div class="flex items-center gap-2.5 shrink-0 ml-auto">
                 <div class="flex flex-col items-end leading-none gap-0.5">
                    {#if (shopStore.originalPrice * shopStore.quantity) > shopStore.totalAmount}
                      <span class="text-[9px] text-white/30 line-through font-bold">{(shopStore.originalPrice * shopStore.quantity).toLocaleString()}đ</span>
                    {/if}
                    <span class="text-blue-400 text-[20px] sm:text-[22px] drop-shadow-[0_0_15px_rgba(59,130,246,0.6)] font-black whitespace-nowrap">{shopStore.totalAmount.toLocaleString()}đ</span>
                 </div>
                 <div class="w-10 h-10 rounded-2xl bg-blue-500/20 flex items-center justify-center border border-blue-400/30 shadow-lg shadow-blue-500/10">
                    <ShoppingCart class="w-5 h-5 text-blue-400" />
                 </div>
              </div>
           </div>
        </button>
      </div>
  </div>
</div>

<style>
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>
