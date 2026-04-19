<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getCartStore } from '$lib/state/commerce/cart.svelte.ts';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import type { Product, ProductVariant } from '$lib/types';
  import { SHOP_CONFIG } from '$lib/constants/shop';
  import { ShoppingCart, ArrowRight, Zap, Sparkles, Ticket } from 'lucide-svelte';
  import OfferVoucherSheet from './OfferVoucherSheet.svelte';

  const { 
    variant, 
    idx, 
    product, 
    variantsCount,
    mkt,
    productVouchers,
    onOpenVouchers
  } = $props<{
    variant: ProductVariant;
    idx: number;
    product: Product | null;
    variantsCount: number;
    mkt: any;
    productVouchers: any[];
    onOpenVouchers: (id: string) => void;
  }>();

  const shopStore = getShopStore();
  const cartStore = getCartStore();

  const isCardActive = $derived(shopStore.variant?.id === variant.id);
  const displayQty = $derived(isCardActive ? (shopStore.variant?.attributes?.combo_qty || shopStore.quantity) : (variant.attributes?.combo_qty || 1));

  // --- MEMOIZED PRICING DATA (ELITE V2.2: ZERO-LAG) ---
  const priceInfo = $derived(shopStore.calculateAdjustedPrice(variant, 1, shopStore.selectedVoucherIds));
  const finalPrice = $derived(priceInfo.final);
  const voucherDiscount = $derived(priceInfo.voucherDiscount);
  const totalSavings = $derived((variant.price - (variant.discountPrice || variant.price)) + voucherDiscount);
  
  const selectedVouchers = $derived((shopStore.vouchers || []).filter(v => shopStore.selectedVoucherIds.includes(v.id)));
  const shippingVoucher = $derived(selectedVouchers.find(v => v.type === 'SHIPPING'));
  const discountVoucher = $derived(selectedVouchers.find(v => v.type !== 'SHIPPING'));

  // --- MEMOIZED FEATURES (ELITE V2.2: NO FUNCTION-IN-RENDER) ---
  const features = $derived.by(() => {
    const variantRaw = variant as ProductVariant & { attributes?: { features?: string[]; combo_qty?: number } };
    let list = [...(variantRaw.attributes?.features || [])];
    if (list.length === 0) {
        const fallbackIdx = idx > 0 ? 1 : 0;
        list = [...(SHOP_CONFIG.default_features[fallbackIdx] || [])];
    }
    list = list.filter(f => !['Cam kết hoàn tiền ẩn danh', 'Tặng kèm Voucher'].some(term => f.includes(term)));
    
    let currentQty = displayQty;
    let displayQtyStr = currentQty < 10 ? `0${currentQty}` : `${currentQty}`;
    return list.map(f => f.replace(/^(0?1)\s+/i, `${displayQtyStr} `));
  });

  let isNavigating = $state(false);

  function selectVariant() {
    shopStore.selectVariant(variant);
    const qty = variant.attributes?.combo_qty || 1;
    shopStore.setQuantity(qty);
  }

  function handleCheckout(e: MouseEvent) {
    e.stopPropagation();
    if (isNavigating) return;
    
    isNavigating = true;
    shopStore.selectVariant(variant);
    const qty = variant.attributes?.combo_qty || 1;
    shopStore.setQuantity(qty);
    if (product) {
        cartStore.buyNow(product, variant, qty, shopStore.selectedVoucherIds);
    }
    
    // Elite V2.2: Smooth cinematic delay before navigation
    setTimeout(() => {
        window.location.href = '/checkout';
    }, 150);
  }

  function getVariantTitle(v: ProductVariant): string {
    const qty = v.attributes?.combo_qty || 1;
    const qtySuffix = qty > 1 ? ` - BỘ ${qty} MÓN` : '';
    if (!product?.tierVariations?.length || !v.tierIndex?.length) return (v.sku || 'Combo') + qtySuffix;
    const title = v.tierIndex.map((optIdx: number, tIdx: number) => {
      const option = product.tierVariations![tIdx]?.options[optIdx];
      return option || '';
    }).filter(Boolean).join(' - ') || 'Combo';
    return title + qtySuffix;
  }
</script>

<div class="relative h-full z-10 {variantsCount >= 3 ? 'min-w-[300px] md:min-w-[420px] lg:min-w-0 snap-center' : ''}">
  <div class="absolute -top-4 left-1/2 -translate-x-1/2 flex flex-wrap gap-2 justify-center w-[120%] z-[60] pointer-events-none mt-1">
    {#if idx === 1 && !isCardActive}
       <div class="px-5 py-2 expert-choice-ribbon text-white font-black text-[9px] uppercase tracking-[0.4em] rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-md">
          {mkt.label_expert_choice}
       </div>
    {/if}
  </div>

  <div 
    onclick={selectVariant}
    onkeydown={(e) => e.key === 'Enter' && selectVariant()}
    role="button"
    tabindex="0"
    class="package-card overflow-hidden text-left flex flex-col h-full relative cursor-pointer {idx === 1 ? 'popular' : ''} {isCardActive ? 'active border-luxury-sakura shadow-[0_0_80px_rgba(255,183,197,0.3)]' : ''}"
  >
    <div class="variant-image-hero relative w-full h-[320px] overflow-hidden">
      <div class="absolute inset-0 bg-radial-at-t from-luxury-sakura/10 to-transparent pointer-events-none transition-opacity duration-700 {isCardActive ? 'opacity-100' : 'opacity-0'}"></div>
      <img 
         src="{product?.images?.[idx] || product?.images?.[0] ? resolveMediaUrl(product.images[idx] || product.images[0]) : ''}" 
         alt={getVariantTitle(variant)} 
         class="w-full h-full object-cover drop-shadow-[0_40px_30px_rgba(0,0,0,0.7)] transform hover:scale-110 transition-transform duration-1000 z-10 relative"
      />
      <img 
         src="{product?.images?.[idx] || product?.images?.[0] ? resolveMediaUrl(product.images[idx] || product.images[0]) : ''}" 
         alt="" 
         class="absolute top-[75%] left-0 w-full h-full object-cover scale-y-[-1] opacity-30 blur-lg grayscale pointer-events-none"
      />
      <div class="absolute top-6 left-6 z-20">
        <p class="text-[8px] font-black {idx >= 1 ? 'text-luxury-sakura' : 'text-slate-200'} uppercase tracking-[0.4em] px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-md border border-white/10">
           {idx === 0 ? mkt.label_activation : mkt.label_full_treatment}
        </p>
      </div>
    </div>

    <div class="px-5 pb-6 pt-2 flex flex-col flex-grow relative z-20">
       <div class="elite-price-cluster flex flex-col items-center md:items-start gap-0 mb-2">
           {#if variant.attributes?.combo_qty && variant.attributes.combo_qty > 1}
              <div class="combo-volume-badge mb-1.5 flex items-center gap-1 px-2.5 py-1 rounded-md bg-luxury-sakura/10 border border-luxury-sakura/20">
                 <Ticket class="w-2.5 h-2.5 text-luxury-sakura" />
                 <span class="text-[9px] font-black text-luxury-sakura uppercase tracking-[0.2em]">SỐ LƯỢNG: {variant.attributes.combo_qty} SẢN PHẨM</span>
              </div>
           {/if}
          <h5 class="text-[15px] font-black text-white italic tracking-tighter text-center md:text-left leading-none mb-1">{getVariantTitle(variant)}</h5>
          <div class="flex items-center gap-2 leading-none">
             {#if variant.price > finalPrice}
                <span class="original-price text-[11px] text-white/20 line-through tabular-nums decoration-luxury-sakura/50">{(variant.price).toLocaleString()}đ</span>
             {/if}
             <span class="text-3xl font-black text-white tabular-nums leading-none tracking-tighter">{(finalPrice).toLocaleString()}đ</span>
          </div>
          
          {#if shippingVoucher || discountVoucher}
            <div class="active-vouchers-row flex flex-wrap gap-2 mt-0.5">
               {#if shippingVoucher}
                  <div class="elite-voucher-sticker freeship flex items-center h-4 rounded-full bg-black/40 border border-luxury-sakura/20 overflow-hidden shadow-sm">
                     <div class="px-1.5 bg-luxury-sakura/20 h-full flex items-center">
                        <span class="text-[6px] font-black text-luxury-sakura uppercase tracking-tighter">FREE</span>
                      </div>
                      <div class="px-1.5 h-full flex items-center">
                        <span class="text-[5px] font-bold text-white/40 uppercase">SHIP</span>
                      </div>
                  </div>
               {/if}
               {#if discountVoucher}
                  <div class="elite-voucher-sticker discount flex items-center h-4 rounded-full bg-black/40 border border-luxury-gold/20 overflow-hidden shadow-sm">
                     <div class="px-1.5 bg-luxury-gold/20 h-full flex items-center">
                        <span class="text-[6px] font-black text-luxury-gold uppercase tracking-tighter">DISCOUNT</span>
                     </div>
                     <div class="px-1.5 h-full flex items-center">
                        <span class="text-[6px] font-bold text-white/80 tabular-nums">-{discountVoucher.value?.toLocaleString()}đ</span>
                     </div>
                  </div>
               {/if}
            </div>
          {/if}

          {#if totalSavings > 0}
            <div class="mt-[3px] flex items-center">
                 <div class="ultimate-savings-box text-[8px] text-black font-black uppercase tracking-wider flex items-center gap-1.5 bg-gradient-to-r from-[#FFD700] via-[#FDB931] to-[#FFD700] px-2.5 py-1 rounded-full border border-white/20 shadow-lg transform active:scale-95 transition-all">
                    <span class="w-1.5 h-1.5 rounded-full bg-red-600 animate-led-red-pulse shadow-[0_0_8px_#ff0000]"></span>
                    <span>{mkt.savings_prefix}</span>
                    <span class="tabular-nums">{(totalSavings).toLocaleString()}đ</span>
                 </div>
            </div>
          {/if}
       </div>

       <p class="flex items-center gap-2 text-[8px] font-bold uppercase tracking-[0.1em] text-white/40 border-t border-white/5 pt-2">
          <span class="text-luxury-sakura">●</span> SPECS: {product?.metadata?.weight || "30G"} - {product?.metadata?.origin || "JAPAN"} | MÃ VẠCH: {variant.sku || product?.sku || 'N/A'}
       </p>

      <ul class="bullet-list space-y-3 mb-6 mt-4">
        {#each features as feature, featureIdx}
           <li class="flex items-start gap-3">
             <span class="text-luxury-sakura font-black text-[10px] mt-0.5 shrink-0">✦</span>
             <EditableWrapper path="variants.{idx}.attributes.features.{featureIdx}" type="text" label="SỬA ĐẶC TÍNH" class="block" as="div">
                <span class="text-[11px] font-black uppercase tracking-widest text-white/90 leading-relaxed block">{feature.replace(/^[+!-]/, '')}</span>
             </EditableWrapper>
           </li>
        {/each}
        <li class="flex items-start gap-3">
          <span class="text-luxury-sakura font-black text-[10px] mt-0.5 shrink-0">✦</span>
          <a href="/chinh-sach-kiem-hang" target="_blank" rel="noopener noreferrer" class="text-[11px] font-black uppercase tracking-widest text-luxury-sakura hover:underline leading-relaxed flex-1">
            Kiểm tra hàng trước nhận
          </a>
        </li>
        <li class="flex items-start gap-3">
          <span class="text-luxury-sakura font-black text-[10px] mt-0.5 shrink-0">✦</span>
          <a href="/chinh-sach-doi-tra-hoan-tien" target="_blank" rel="noopener noreferrer" class="text-[11px] font-black uppercase tracking-widest text-luxury-sakura hover:underline leading-relaxed flex-1">
            Đổi trả 7 ngày
          </a>
        </li>
      </ul>

      {#if productVouchers.length > 0 || !!(variant.attributes?.gifts?.length)}
        <div 
          onclick={(e) => { e.stopPropagation(); onOpenVouchers(variant.id); }}
          role="button"
          tabindex="0"
          class="package-offer-box mt-auto mb-2 bg-gradient-to-br from-luxury-sakura/15 via-black/40 to-transparent p-4 pl-0.5 rounded-2xl transition-all duration-500 cursor-pointer relative z-30"
        >
          <div class="viral-liquid-border"></div>
          <div class="flex items-center justify-start mb-1 px-0.5 pointer-events-none">
             <span class="text-[9px] text-luxury-sakura font-black uppercase tracking-[0.2em] flex items-center gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-luxury-sakura animate-pulse"></span>
                {productVouchers.length > 0 ? (variant.attributes?.gifts?.length ? 'Ưu đãi & Quà tặng' : 'Mã giảm giá') : 'Quà tặng độc quyền'}
             </span>
          </div>

           <div class="flex items-center gap-1.5 mt-3 pointer-events-none overflow-x-auto scrollbar-hide pl-3">
             {#if (productVouchers.filter(v => shopStore.selectedVoucherIds.includes(v.id))).length > 0}
               {#each productVouchers.filter(v => shopStore.selectedVoucherIds.includes(v.id)) as v}
                 <div class="sticker-mini-preview flex items-center gap-1.5 bg-luxury-sakura/10 px-1 py-1.5 rounded-lg border border-luxury-sakura/20 shadow-[0_0_10px_rgba(255,183,197,0.1)]">
                   <span class="text-[9px] font-black text-luxury-sakura uppercase leading-none">{v.label}</span>
                   <span class="w-px h-2 bg-luxury-sakura/20"></span>
                   <span class="text-[10px] text-white uppercase font-black truncate leading-none">{v.sub}</span>
                 </div>
               {/each}
             {:else if productVouchers.length > 0}
               {@const bestV = productVouchers[0]}
               <div class="sticker-mini-preview flex items-center gap-1.5 bg-white/5 px-1 py-1.5 rounded-lg border border-white/10">
                 <span class="text-[9px] font-black text-luxury-sakura uppercase leading-none">{bestV.label}</span>
                 <span class="w-px h-2 bg-white/10"></span>
                 <span class="text-[10px] text-white uppercase font-black truncate leading-none">{bestV.sub}</span>
               </div>
             {/if}
           </div>

          <p class="text-[8px] text-white/30 uppercase font-bold tracking-widest mt-4 flex items-center gap-2 pointer-events-none pl-3">
            Bấm để xem chi tiết <ArrowRight size={8} class="text-luxury-sakura" />
          </p>
        </div>
      {/if}

      <button 
        onclick={handleCheckout}
        disabled={isNavigating}
        class="liquid-cta-viral text-white min-h-[76px] rounded-2xl font-black shadow-2xl relative overflow-hidden flex flex-col items-center justify-center px-5 w-full mt-4 transition-all duration-500 {isCardActive ? 'scale-[1.03] ring-2 ring-white/30' : ''} {isNavigating ? 'opacity-90 saturate-[0.8] cursor-wait' : 'cursor-pointer'}"
      >
         {#if isNavigating}
            <div class="absolute inset-0 bg-white/10 backdrop-blur-sm z-20 flex items-center justify-center">
               <div class="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            </div>
         {/if}
         <div class="fomo-header-viral text-[7px] font-black tracking-[0.3em] text-white/60 mb-1 flex items-center justify-center gap-3 uppercase w-full">
            <div class="flex items-center gap-1">
               <Zap size={8} class="text-yellow-300/80 fill-yellow-300/80" />
               CHỈ CÒN {variant.stock || 5} SUẤT
            </div>
            <span class="w-1 h-1 rounded-full bg-white/20"></span>
            <div class="flex items-center gap-1">
               <Sparkles size={8} class="text-blue-200/80" />
               MIỄN PHÍ VẬN CHUYỂN
            </div>
         </div>

         <div class="relative z-10 flex items-center justify-between w-full pointer-events-none">
           <div class="flex items-center gap-3.5 text-left">
              <div class="bg-white/15 p-2 rounded-xl backdrop-blur-xl border border-white/10 shadow-[inner_0_1px_1px_rgba(255,255,255,0.2)]">
                 <ShoppingCart class="w-6 h-6 text-white drop-shadow-md" strokeWidth={2} />
              </div>
              <div class="flex flex-col justify-center">
                 <span class="text-[14px] font-black uppercase tracking-[0.2em] text-white leading-none mb-1 text-shadow-sm">
                    MUA NGAY
                 </span>
                 <span class="text-[9px] text-white/80 uppercase font-bold tracking-[0.1em]">
                     Sở hữu ngay • {finalPrice.toLocaleString()}đ
                 </span>
              </div>
           </div>
           <div class="bg-white/10 p-2 rounded-full border border-white/5 shadow-lg">
              <ArrowRight class="w-3.5 h-3.5 text-white/90 animate-bounce-x" />
           </div>
         </div>
       </button>
    </div>

    <!-- 🌙 VOUCHER BOTTOM SHEET (NESTED FOR TIKTOK EFFECT) -->
    {#if liveEditStore.openPopoverId === variant.id}
       <OfferVoucherSheet 
          {variant} 
          idx={idx} 
          {productVouchers}
          voucherSortOrder={shopStore.voucherSortOrder || 'none'}
          activeOfferTab={shopStore.activeOfferTab || {}}
          onClose={() => liveEditStore.togglePopover(null)}
          onToggleSort={() => shopStore.toggleVoucherSort()}
          onVoucherClick={(v) => shopStore.toggleVoucher(v.id)}
          onSetTab={(i, tab) => shopStore.setOfferTab(i, tab)}
       />
    {/if}
  </div>
</div>
