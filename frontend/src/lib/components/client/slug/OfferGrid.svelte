<script lang="ts">
  import { onMount } from 'svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getClientUi } from '$lib/state/commerce/ui.svelte.ts';
  import { getCartStore } from '$lib/state/commerce/cart.svelte.ts';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import type { Product, ProductVariant, Voucher } from '$lib/types';
  import { SHOP_CONFIG, OFFER_CONSTANTS } from '$lib/constants/shop';
  import { ShoppingCart, CheckCircle2, ArrowRight, Zap, Sparkles, Check, Ticket, ArrowUpDown, ArrowDownNarrowWide, ArrowUpWideNarrow } from 'lucide-svelte';
  import { scale, fade, fly } from 'svelte/transition';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { cubicOut, cubicIn } from 'svelte/easing';
  import DesktopProductDetailsModal from './DesktopProductDetailsModal.svelte';
  import "./OfferGrid.css";
  
  const shopStore = getShopStore();
  const ui = getClientUi();
  const cartStore = getCartStore();
  
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : shopStore.product);
  const timeLeft = $derived(shopStore.timeLeft);
  const variants = $derived(product?.variants || []);
  const metadata = $derived(product?.metadata || {});

  const stripTags = (h: string) => h ? h.replace(/<[^>]*>?/gm, '').trim() : '';
  const legacyParts = $derived(metadata.offer_headline?.split("<span class='text-luxury-gold'>") || []);
  const h1 = $derived(metadata.offer_headline_1 || stripTags(legacyParts[0]) || "CHẠM NGƯỠNG ĐỈNH CAO CỦA");
  const h2 = $derived(metadata.offer_headline_2 || stripTags(legacyParts[1]) || "SỰ TỰ TIN TUYỆT ĐỐI");
  
  const clean = (s: unknown) => {
    if (!s) return "";
    let val = String(s);
    if (val.startsWith('[OFF]')) return val.substring(5).trim();
    return val;
  };

  const mkt = $derived({
    sub: metadata.offer_subheadline || "",
    timer_prefix: clean(metadata.offer_timer_prefix || "Ưu đãi lột xác kết thúc sau:"),
    shipping_prefix: clean(metadata.offer_shipping_prefix || "+ VẬN CHUYỂN:"),
    savings_prefix: clean(metadata.offer_savings_prefix || "TIẾT KIỆM NGAY:"),
    booking_suffix: clean(metadata.offer_booking_suffix || "phụ nữ đã lột xác thành công tuần này"),
    trust_verified_by: clean(metadata.offer_trust_verified_by || "TIÊU CHUẨN Y KHOA NHẬT BẢN"),
    compliance_note: clean(metadata.offer_compliance_note || "* Giao hàng bảo mật, <br/> Đóng gói tinh tế như một món quà trang sức."),
    label_activation: metadata.offer_label_activation || "GIAI ĐOẠN ĐÁNH THỨC",
    label_full_treatment: metadata.offer_label_full_treatment || "LIỆU TRÌNH HOÀN MỸ",
    label_expert_choice: metadata.offer_label_expert_choice || "SỰ LỰA CHỌN CỦA PHÁI ĐẸP",
    cta_start: metadata.offer_cta_start || "BẮT ĐẦU TÁI SINH",
    cta_full: metadata.offer_cta_full || "SỞ HỮU SỰ KIÊU SA"
  });

  // --- Voucher Logic (Elite V2.2) ---
  let voucherSortOrder = $state<'none' | 'desc' | 'asc'>('none');
  
  function toggleVoucherSort() {
    if (voucherSortOrder === 'none') voucherSortOrder = 'desc';
    else if (voucherSortOrder === 'desc') voucherSortOrder = 'asc';
    else voucherSortOrder = 'none';
  }

  const productVouchers = $derived.by(() => {
    const rawVouchers = cartStore.vouchers && cartStore.vouchers.length > 0 ? cartStore.vouchers : [];
    let mapped = rawVouchers.map((v: Voucher) => ({
      id: v.id,
      label: v.id || v.title || 'ƯU ĐÃI',
      sub: v.type === 'SHIPPING' ? 'SHIPPING 0Đ' : (v.type === 'PERCENT' ? `${v.value}%` : `${v.value?.toLocaleString()}đ`),
      type: v.type === 'SHIPPING' ? 'ship' : 'discount',
      value: v.value || 0
    }));

    if (voucherSortOrder === 'desc') {
      return [...mapped].sort((a, b) => b.value - a.value);
    } else if (voucherSortOrder === 'asc') {
      return [...mapped].sort((a, b) => a.value - b.value);
    }
    return mapped;
  });

  // --- ĐỒNG BỘ HÓA VOUCHER (ELITE V5.8: REACTIVITY FIX) ---
  $effect(() => {
    if (cartStore.vouchers && cartStore.vouchers.length > 0) {
      shopStore.setVouchers(cartStore.vouchers);
    }
  });

  function handleVoucherClick(v: { id: string }) {
    if (v.id) {
      shopStore.toggleVoucher(v.id);
    }
  }

  let expandedVariantVouchers = $state<Record<number, boolean>>({});
  function toggleVouchers(idx: number) {
    expandedVariantVouchers[idx] = !expandedVariantVouchers[idx];
  }

  let activeOfferTab = $state<Record<number, 'vouchers' | 'gifts'>>({});
  function setOfferTab(vIdx: number, tab: 'vouchers' | 'gifts') {
    activeOfferTab[vIdx] = tab;
  }

  function getActiveTab(vIdx: number, hasVouchers: boolean, hasGifts: boolean) {
    if (activeOfferTab[vIdx]) return activeOfferTab[vIdx];
    if (hasVouchers) return 'vouchers';
    if (hasGifts) return 'gifts';
    return 'vouchers';
  }

  let openPopoverId = $state<string | null>(null);
  function togglePopover(id: string | null) {
    if (openPopoverId === id) openPopoverId = null;
    else openPopoverId = id;
  }
  
  const mark1 = $derived(metadata.offer_trust_verified_by || "TIÊU CHUẨN Y KHOA NHẬT BẢN");
  const mark2 = $derived(metadata.offer_trust_mark_2 || "HIỆU QUẢ KIỂM CHỨNG");
  const mark3 = $derived(metadata.offer_trust_mark_3 || "DƯỢC MỸ PHẨM CAO CẤP");

  let isDetailsOpen = $state(false);
  
  function getVariantTitle(variant: ProductVariant): string {
    const qty = variant.attributes?.combo_qty || 1;
    const qtySuffix = qty > 1 ? ` - BỘ ${qty} MÓN` : '';
    
    if (!product?.tierVariations?.length || !variant.tierIndex?.length) return (variant.sku || 'Combo') + qtySuffix;
    const title = variant.tierIndex.map((optIdx: number, tierIdx: number) => {
      const option = product.tierVariations![tierIdx]?.options[optIdx];
      return option || '';
    }).filter(Boolean).join(' - ') || 'Combo';
    
    return title + qtySuffix;
  }

  const displayQty = $derived(shopStore.variant?.attributes?.combo_qty || shopStore.quantity);
  const totalDisplayPrice = $derived(shopStore.totalAmount);

  const formatTime = (s: number): string => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const getFeatures = (variant: ProductVariant, idx: number, isActive: boolean): string[] => {
    const variantRaw = variant as ProductVariant & { attributes?: { features?: string[]; combo_qty?: number } };
    
    // ƯU TIÊN: Đặc tính cụ thể từ Variant attributes trong DB (V2.2)
    let features = [...(variantRaw.attributes?.features || [])];
    
    // FALLBACK: Nếu không có đặc tính riêng, dùng bộ mặc định theo index (với logic index n-1)
    if (features.length === 0) {
        const fallbackIdx = idx > 0 ? 1 : 0;
        features = [...(SHOP_CONFIG.default_features[fallbackIdx] || [])];
    }

    // CLEANUP: Loại bỏ các cam kết đã hiển thị ở phần khác
    features = features.filter(f => !['Cam kết hoàn tiền ẩn danh', 'Tặng kèm Voucher'].some(term => f.includes(term)));
    
    // ĐỒNG BỘ: Tự động đổi '01' thành số combo của variant đang chọn/active
    let currentQty = isActive ? displayQty : (variantRaw.attributes?.combo_qty || 1);
    let displayQtyStr = currentQty < 10 ? `0${currentQty}` : `${currentQty}`;
    
    return features.map(f => {
        // Thay thế '01 ' hoặc '1 ' bằng số lượng thực tế của combo
        return f.replace(/^(0?1)\s+/i, `${displayQtyStr} `);
    });
  };

  const gridClass = $derived(variants.length >= 3 
    ? 'slider-track overflow-x-auto lg:overflow-visible scrollbar-hide snap-x snap-mandatory flex lg:grid lg:grid-cols-3'
    : `grid grid-cols-1 ${variants.length === 2 ? 'md:grid-cols-2' : 'lg:grid-cols-3'}`
  );

  onMount(() => {
    if (variants.length > 0 && !shopStore.variant) {
      shopStore.selectVariant(variants[0]);
      shopStore.setQuantity(1);
    }
  });

  function selectVariant(variant: ProductVariant) {
    shopStore.selectVariant(variant);
    // Elite V2.2: Set quantity to match combo volume (e.g. 2 or 3)
    const qty = variant.attributes?.combo_qty || 1;
    shopStore.setQuantity(qty);
  }

  function handleCheckout(e: MouseEvent, variant: ProductVariant) {
    e.stopPropagation();
    // Elite V7.6: Force select variant immediately on buy now click
    shopStore.selectVariant(variant);
    const qty = variant.attributes?.combo_qty || 1;
    shopStore.setQuantity(qty);
    
    if (product) {
        // Elite V7.4: Ensure selected vouchers are synced to cart for correct checkout price
        cartStore.buyNow(product, variant, qty, shopStore.selectedVoucherIds);
    }
    window.location.href = '/checkout';
  }
</script>

<section class="offer-section relative overflow-hidden" style:padding-top="var(--standard-pt)">
  <div class="absolute inset-0 bg-radial-at-t from-luxury-sakura/10 to-transparent pointer-events-none"></div>
  <div class="liquid-orb top-[10%] left-[-10%] w-[800px] h-[800px] pointer-events-none" style:background-color="var(--luxury-sakura)" style:opacity="0.1"></div>
  <div class="liquid-orb bottom-[-10%] right-[-10%] w-[600px] h-[600px] pointer-events-none" style:background-color="var(--luxury-gold)" style:opacity="0.05"></div>

  <div class="container mx-auto px-3 max-w-6xl relative z-surface">
    <div class="text-center">
      <h2 class="elite-session-headline mb-8 text-center offer-grid-headline">
        {#if !(metadata.offer_headline_1 || '').startsWith('[OFF]') || liveEditStore.isEditMode}
          <EditableWrapper path="metadata.offer_headline_1" type="text" label="SỬA TIÊU ĐỀ 1" class="inline" as="span">
            {h1}
          </EditableWrapper>
        {/if}

        {#if (!(metadata.offer_headline_1 || '').startsWith('[OFF]') && !(metadata.offer_headline_2 || '').startsWith('[OFF]')) || liveEditStore.isEditMode}
          <br class="md:hidden"/>
        {/if}

        {#if !(metadata.offer_headline_2 || '').startsWith('[OFF]') || liveEditStore.isEditMode}
          <span class="text-luxury-gold md:ml-3">
             <EditableWrapper path="metadata.offer_headline_2" type="text" label="SỬA TIÊU ĐỀ 2" class="inline" as="span">
               {h2}
             </EditableWrapper>
          </span>
        {/if}
      </h2>

      <div class="flex items-center justify-center gap-4 mt-8 opacity-60 grayscale hover:grayscale-0 transition-all duration-700">
         <EditableWrapper path="metadata.offer_trust_verified_by" type="text" label="SỬA CHỨNG NHẬN 1" class="inline" as="span">
           <span class="text-[8px] uppercase tracking-[0.6em] font-medium text-slate-400">{clean(mark1)}</span>
         </EditableWrapper>
         
         {#if (!mark1.startsWith('[OFF]') && !mark2.startsWith('[OFF]')) || liveEditStore.isEditMode}
            <div class="h-px w-10 bg-white/5"></div>
         {/if}

         <EditableWrapper path="metadata.offer_trust_mark_2" type="text" label="SỬA CHỨNG NHẬN 2" class="inline" as="span">
           <span class="text-[9px] uppercase tracking-[0.3em] font-black text-luxury-sakura">{clean(mark2)}</span>
         </EditableWrapper>
         
         {#if (!mark2.startsWith('[OFF]') && !mark3.startsWith('[OFF]')) || liveEditStore.isEditMode}
            <div class="h-px w-10 bg-white/5"></div>
         {/if}

         <EditableWrapper path="metadata.offer_trust_mark_3" type="text" label="SỬA CHỨNG NHẬN 3" class="inline" as="span">
            <span class="text-[8px] uppercase tracking-[0.6em] font-medium text-slate-400">{clean(mark3)}</span>
         </EditableWrapper>
      </div>
    </div>

    <div class="flex justify-center mb-10 mt-6 relative z-surface">
      <div class="flex flex-col items-center gap-6">
        <div class="elite-status-pill px-8 py-2 shadow-[0_0_20px_rgba(255,183,197,0.1)]">
          <span class="w-2 h-2 rounded-full bg-luxury-sakura mr-3 shadow-[0_0_8px_var(--luxury-sakura)]"></span>
          {#if !(metadata.offer_timer_prefix || '').startsWith('[OFF]') || liveEditStore.isEditMode}
            <EditableWrapper path="metadata.offer_timer_prefix" type="text" label="SỬA TIÊU ĐỀ HẸN GIỜ" class="inline" as="span">
              <span class="text-[10px] uppercase tracking-[0.4em]">{mkt.timer_prefix}</span>
            </EditableWrapper>
          {/if}
          <span class="font-black tabular-nums text-white text-[10px] tracking-[0.4em]">{formatTime(timeLeft)}</span>
        </div>
      </div>
    </div>


    <div class="package-grid pt-8 {gridClass} gap-6 items-stretch">
      {#each variants as variant, idx (idx)}
          <!-- 🧮 REACTIVE COMPUTATION CLUSTER (ELITE V5.8: REACTION FORCED) -->
          {@const unitPrice = variant.discountPrice || variant.price}
          {@const priceInfo = shopStore.calculateAdjustedPrice(variant, 1, shopStore.selectedVoucherIds)}
          {@const finalPrice = priceInfo.final}
          {@const voucherDiscount = priceInfo.voucherDiscount}
          {@const totalSavings = (variant.price - unitPrice) + voucherDiscount}
          
          {@const isCardActive = shopStore.variant?.id === variant.id}
          {@const hasVouchers = productVouchers.length > 0}
          {@const hasGifts = !!(variant.attributes?.gifts?.length)}
          {@const currentTab = getActiveTab(idx, hasVouchers, hasGifts)}
          {@const selectedVouchers = (shopStore.vouchers || []).filter(v => shopStore.selectedVoucherIds.includes(v.id))}
          {@const shippingVoucher = selectedVouchers.find(v => v.type === 'SHIPPING')}
          {@const discountVoucher = selectedVouchers.find(v => v.type !== 'SHIPPING')}

          <div class="relative h-full z-10 {variants.length >= 3 ? 'min-w-[300px] md:min-w-[420px] lg:min-w-0 snap-center' : ''}">
              <div class="absolute -top-4 left-1/2 -translate-x-1/2 flex flex-wrap gap-2 justify-center w-[120%] z-[60] pointer-events-none mt-1">
                {#if idx === 1 && !isCardActive}
                   <div class="px-5 py-2 expert-choice-ribbon text-white font-black text-[9px] uppercase tracking-[0.4em] rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-md">
                      {mkt.label_expert_choice}
                   </div>
                {/if}
              </div>

              <div 
                onclick={() => selectVariant(variant)}
                onkeydown={(e) => e.key === 'Enter' && selectVariant(variant)}
                role="button"
                tabindex="0"
                class="package-card overflow-hidden text-left flex flex-col h-full relative cursor-pointer {idx === 1 ? 'popular' : ''} {isCardActive ? 'active border-luxury-sakura shadow-[0_0_80px_rgba(255,183,197,0.3)]' : ''}"
              >
                <div class="variant-image-hero relative w-full h-[320px] overflow-hidden">
                  <div class="absolute inset-0 bg-radial-at-t from-luxury-sakura/10 to-transparent pointer-events-none transition-opacity duration-700 {isCardActive ? 'opacity-100' : 'opacity-0'}"></div>
                  <img 
                     src="{product?.images?.[idx] || product?.images?.[0] ? resolveMediaUrl(product.images[idx] || product.images[0]) : ''}" 
                     alt="{getVariantTitle(variant)}" 
                     class="w-full h-full object-cover drop-shadow-[0_40px_30px_rgba(0,0,0,0.7)] transform hover:scale-110 transition-transform duration-1000 z-10 relative"
                  />
                  
                  <!-- IMAGE REFLECTION -->
                  <img 
                     src="{product?.images?.[idx] || product?.images?.[0] ? resolveMediaUrl(product.images[idx] || product.images[0]) : ''}" 
                     alt="" 
                     class="absolute top-[75%] left-0 w-full h-full object-cover scale-y-[-1] opacity-30 blur-lg grayscale pointer-events-none"
                  />
                  
                  <!-- OVERLAY BADGE -->
                  <div class="absolute top-6 left-6 z-20">
                    <p class="text-[8px] font-black {idx >= 1 ? 'text-luxury-sakura' : 'text-slate-200'} uppercase tracking-[0.4em] px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-md border border-white/10">
                       {idx === 0 ? mkt.label_activation : mkt.label_full_treatment}
                    </p>
                  </div>
                </div>

                <!-- CONTENT WRAPPER -->
                <div class="px-5 pb-6 pt-2 flex flex-col flex-grow relative z-20">
                   <!-- 💎 ELITE PRICE CLUSTER -->
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
                      
                      <!-- 🎫 DUAL VOUCHER STICKERS -->
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
                           {#if !(metadata.offer_savings_prefix || '').startsWith('[OFF]') || liveEditStore.isEditMode}
                             <div class="ultimate-savings-box text-[8px] text-black font-black uppercase tracking-wider flex items-center gap-1.5 bg-gradient-to-r from-[#FFD700] via-[#FDB931] to-[#FFD700] px-2.5 py-1 rounded-full border border-white/20 shadow-lg transform active:scale-95 transition-all">
                                <span class="w-1.5 h-1.5 rounded-full bg-red-600 animate-led-red-pulse shadow-[0_0_8px_#ff0000]"></span>
                                <EditableWrapper path="metadata.offer_savings_prefix" type="text" label="SỬA TIÊU ĐỀ TIẾT KIỆM" class="inline" as="span">
                                  {mkt.savings_prefix}
                                </EditableWrapper>
                                <span class="tabular-nums">{(totalSavings).toLocaleString()}đ</span>
                             </div>
                           {/if}
                        </div>
                      {/if}
                   </div>

                   <p class="flex items-center gap-2 text-[8px] font-bold uppercase tracking-[0.1em] text-white/40 border-t border-white/5 pt-2">
                      <span class="text-luxury-sakura">●</span> SPECS: {metadata.weight || "30G"} - {metadata.origin || "JAPAN"} | MÃ VẠCH: {variant.sku || product?.sku || 'N/A'}
                   </p>

                  <ul class="bullet-list space-y-3 mb-6 mt-4">
                    {#each getFeatures(variant, idx, isCardActive) as feature, featureIdx}
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

                  <!-- 💎 Elite Offer Box -->
                  {#if hasVouchers || hasGifts}
                    <div 
                      onclick={(e) => { e.stopPropagation(); togglePopover(variant.id); }}
                      role="button"
                      tabindex="0"
                      class="package-offer-box mt-auto mb-2 bg-gradient-to-br from-luxury-sakura/15 via-black/40 to-transparent p-4 pl-0.5 rounded-2xl transition-all duration-500 cursor-pointer relative z-30"
                    >
                      <div class="viral-liquid-border"></div>
                      <div class="flex items-center justify-start mb-1 px-0.5 pointer-events-none">
                         <span class="text-[9px] text-luxury-sakura font-black uppercase tracking-[0.2em] flex items-center gap-2">
                            <span class="w-1.5 h-1.5 rounded-full bg-luxury-sakura animate-pulse"></span>
                            {hasVouchers ? (hasGifts ? 'Ưu đãi & Quà tặng' : 'Mã giảm giá') : 'Quà tặng độc quyền'}
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
                         {:else if hasVouchers}
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

                  <!-- 🚀 ELITE CTA BUTTON (UNIFIED INSIDE CARD) -->
                  <button 
                    onclick={(e) => handleCheckout(e, variant)}
                    class="liquid-cta-viral text-white min-h-[76px] rounded-2xl font-black shadow-2xl relative overflow-hidden flex flex-col items-center justify-center px-5 w-full mt-4 transition-all duration-500 {isCardActive ? 'scale-[1.03] cursor-pointer ring-2 ring-white/30' : 'pointer-events-auto cursor-pointer'}"
                  >
                     <!-- ⚡ FOMO HEADER (VIRAL 2026: ULTRA-MINIMALIST) -->
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

                <!-- 🌪️ LOCAL IN-CARD SHEET (ELITE V5.7: BOTTOM-ANCHORED) -->
                {#if String(openPopoverId) === String(variant.id)}
                   <div 
                     class="absolute inset-x-0 bottom-0 h-[85%] z-50 flex flex-col bg-[#060606] rounded-t-[2.5rem] border-t border-white/10 shadow-[0_-20px_60px_rgba(0,0,0,0.8)] overflow-hidden"
                     in:fly={{ y: '100%', duration: 500, easing: cubicOut }}
                     out:fly={{ y: '100%', duration: 400, easing: cubicIn }}
                   >
                      <!-- 💎 SHEET DRAG HANDLE -->
                      <div class="flex justify-center pt-4 pb-1 shrink-0">
                         <div class="w-8 h-1 rounded-full bg-white/10"></div>
                      </div>

                      <div class="px-5 pb-4 flex-grow overflow-y-auto scrollbar-hide">
                         <!-- TABS (MINI) -->
                         <div class="offer-tabs-nav flex items-center gap-6 mb-4 border-b border-white/5 sticky top-0 bg-[#060606] z-20 pt-1 pb-2">
                           {#if hasVouchers}
                             <button 
                               onclick={(e) => { e.stopPropagation(); setOfferTab(idx, 'vouchers'); }}
                               class="text-[9px] font-black uppercase tracking-wider transition-all {currentTab === 'vouchers' ? 'text-luxury-sakura' : 'text-white/30'}"
                             >
                               ƯU ĐÃI
                             </button>
                           {/if}
                           {#if hasGifts}
                             <button 
                               onclick={(e) => { e.stopPropagation(); setOfferTab(idx, 'gifts'); }}
                               class="text-[9px] font-black uppercase tracking-wider transition-all {currentTab === 'gifts' ? 'text-luxury-sakura' : 'text-white/30'}"
                             >
                               QUÀ TẶNG
                             </button>
                           {/if}

                           <!-- ⚡ ELITE SORT TOGGLE -->
                           {#if currentTab === 'vouchers' && productVouchers.length > 1}
                             <button 
                               onclick={(e) => { e.stopPropagation(); toggleVoucherSort(); }}
                               class="ml-auto flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all active:scale-95"
                             >
                               <span class="text-[7px] font-black text-white/40 uppercase tracking-tighter">
                                 {voucherSortOrder === 'none' ? 'Mặc định' : (voucherSortOrder === 'desc' ? 'Giá trị cao' : 'Giá trị thấp')}
                               </span>
                               {#if voucherSortOrder === 'desc'}
                                 <ArrowDownNarrowWide size={10} class="text-luxury-sakura" />
                               {:else if voucherSortOrder === 'asc'}
                                 <ArrowUpWideNarrow size={10} class="text-luxury-sakura" />
                               {:else}
                                 <ArrowUpDown size={10} class="text-white/20" />
                               {/if}
                             </button>
                           {/if}
                         </div>

                         {#if currentTab === 'vouchers' && hasVouchers}
                           <div class="flex flex-col gap-3 py-1 mb-24">
                             {#each productVouchers as v}
                               {@const isApplied = shopStore.selectedVoucherIds.includes(v.id)}
                               <div class="viral-voucher-tag-mini relative h-[60px] flex items-center bg-white/5 rounded-xl border border-white/5 overflow-hidden">
                                  <div class="w-10 h-full bg-white/5 flex items-center justify-center border-r border-dashed border-white/10 shrink-0">
                                     <Ticket class="text-luxury-sakura opacity-40" size={14} />
                                  </div>
                                  <div class="flex-grow px-3 flex items-center justify-between gap-1 overflow-hidden">
                                     <div class="flex flex-col text-left truncate">
                                        <span class="text-[10px] font-black text-white truncate leading-none uppercase">{v.label}</span>
                                        <span class="text-[7px] font-bold text-white/30 uppercase truncate">{v.sub}</span>
                                     </div>
                                     <button 
                                       onclick={(e) => { e.stopPropagation(); handleVoucherClick(v); }}
                                       class="voucher-action-btn-mini {isApplied ? 'active' : ''} transition-all active:scale-90"
                                     >
                                        {isApplied ? 'ĐANG DÙNG' : 'SỬ DỤNG'}
                                     </button>
                                  </div>
                               </div>
                             {/each}
                           </div>
                         {:else if currentTab === 'gifts' && hasGifts}
                           <div class="flex flex-col gap-2 py-1 mb-24">
                              {#each variant.attributes?.gifts || [] as gift}
                               <div class="flex items-center gap-3 p-3 rounded-2xl bg-white/5 border border-white/5">
                                 <div class="w-8 h-8 rounded-lg overflow-hidden shrink-0 bg-black/40 flex items-center justify-center">
                                   {#if gift.image}
                                     <img src={resolveMediaUrl(gift.image)} alt="" class="w-full h-full object-cover" />
                                   {/if}
                                 </div>
                                 <div class="flex flex-col">
                                    <span class="text-[9px] text-white/90 font-bold truncate tracking-tight">{gift.name}</span>
                                    <span class="text-[7px] text-luxury-gold font-black uppercase tracking-tighter">x{gift.qty}</span>
                                 </div>
                               </div>
                             {/each}
                           </div>
                         {/if}
                      </div>

                      <div class="absolute inset-x-0 bottom-0 px-5 pt-8 pb-10 done-area-mini z-30">
                        <button 
                          onclick={(e) => { e.stopPropagation(); togglePopover(null); }}
                          class="liquid-done-btn-mini w-full py-4 rounded-2xl font-black text-[12px] uppercase tracking-[0.2em] transition-all"
                        >
                           XONG
                        </button>
                      </div>
                   </div>
                {/if}
              </div>
           </div>
        {/each}
      </div>
    </div>
  </section>

<DesktopProductDetailsModal bind:active={isDetailsOpen} {product} />
