<script lang="ts">
  import { onMount } from 'svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { getClientUi } from '$lib/state/commerce/ui.svelte.ts';
  import { getCartStore } from '$lib/state/commerce/cart.svelte.ts';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import type { Product, ProductVariant } from '$lib/types';
  import { SHOP_CONFIG, OFFER_CONSTANTS } from '$lib/constants/shop';
  import { ShoppingCart, CheckCircle2, ArrowRight, Zap } from 'lucide-svelte';
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
  
  const mark1 = $derived(metadata.offer_trust_verified_by || "TIÊU CHUẨN Y KHOA NHẬT BẢN");
  const mark2 = $derived(metadata.offer_trust_mark_2 || "HIỆU QUẢ KIỂM CHỨNG");
  const mark3 = $derived(metadata.offer_trust_mark_3 || "DƯỢC MỸ PHẨM CAO CẤP");

  let isDetailsOpen = $state(false);
  
  function getVariantTitle(variant: ProductVariant): string {
    if (!product?.tierVariations?.length || !variant.tierIndex?.length) return variant.sku || 'Combo';
    return variant.tierIndex.map((optIdx: number, tierIdx: number) => {
      const option = product.tierVariations![tierIdx]?.options[optIdx];
      return option || '';
    }).filter(Boolean).join(' - ') || 'Combo';
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

  function handleSelect(variant: ProductVariant) {
    const isActive = shopStore.variant?.id === variant.id;
    if (isActive) {
        if (product) {
            cartStore.buyNow(product, variant, shopStore.quantity);
        }
        window.location.href = '/checkout';
    } else {
        shopStore.selectVariant(variant);
        // Resync quantity: For combo variants in OfferGrid, we usually want quantity=1 
        // but display it using combo_qty.
        shopStore.setQuantity(1);
    }
  }
</script>

<section class="offer-section relative overflow-hidden" style:padding-top="var(--standard-pt)">
  <div class="absolute inset-0 bg-radial-at-t from-luxury-sakura/10 to-transparent pointer-events-none"></div>
  <div class="liquid-orb top-[10%] left-[-10%] w-[800px] h-[800px] pointer-events-none" style:background-color="var(--luxury-sakura)" style:opacity="0.1"></div>
  <div class="liquid-orb bottom-[-10%] right-[-10%] w-[600px] h-[600px] pointer-events-none" style:background-color="var(--luxury-gold)" style:opacity="0.05"></div>

  <div class="container mx-auto px-6 max-w-6xl relative z-surface">
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

    <div class="flex justify-center mb-10 mt-6">
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


    <div class="package-grid pt-8 {gridClass} gap-6 items-stretch">
      {#each variants as variant, idx (idx)}
          {@const isCardActive = shopStore.variant?.id === variant.id}
          {@const unitPrice = variant.discountPrice || variant.price}
          <div class="relative h-full z-10 {variants.length >= 3 ? 'min-w-[300px] md:min-w-[420px] lg:min-w-0 snap-center' : ''}">
             <div class="absolute -top-4 left-1/2 -translate-x-1/2 flex flex-wrap gap-2 justify-center w-[120%] z-[60] pointer-events-none mt-1">
                {#if idx === 1 && !isCardActive}
                   <div class="px-5 py-2 expert-choice-ribbon text-white font-black text-[9px] uppercase tracking-[0.4em] rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-md">
                      {mkt.label_expert_choice}
                   </div>
                {/if}

              </div>

              <div 
                onclick={() => handleSelect(variant)}
                onkeydown={(e) => e.key === 'Enter' && handleSelect(variant)}
                role="button"
                tabindex="0"
                class="package-card overflow-hidden text-left flex flex-col h-full relative cursor-pointer {idx === 1 ? 'popular' : ''} {isCardActive ? 'active border-luxury-sakura shadow-[0_0_80px_rgba(255,183,197,0.3)]' : ''}"
              >
                <!-- TOP HERO IMAGE -->
                <div class="variant-image-hero relative w-full h-[320px] overflow-hidden">
                  <div class="absolute inset-0 bg-radial-at-t from-luxury-sakura/10 to-transparent pointer-events-none transition-opacity duration-700 {isCardActive ? 'opacity-100' : 'opacity-0'}"></div>
                  
                  <img 
                     src="{product?.images?.[0] ? resolveMediaUrl(product.images[0]) : ''}" 
                     alt="{getVariantTitle(variant)}" 
                     class="w-full h-full object-cover drop-shadow-[0_40px_30px_rgba(0,0,0,0.7)] transform hover:scale-110 transition-transform duration-1000 z-10 relative animate-breathing-zoom"
                  />
                  
                  <!-- IMAGE REFLECTION (LOWER OPACITY) -->
                  <img 
                     src="{product?.images?.[0] ? resolveMediaUrl(product.images[0]) : ''}" 
                     alt="" 
                     class="absolute top-[75%] left-0 w-full h-full object-cover scale-y-[-1] opacity-30 blur-lg grayscale pointer-events-none animate-breathing-zoom"
                  />
                  
                  <!-- OVERLAY BADGE -->
                  <div class="absolute top-6 left-6 z-20">
                    <p class="text-[8px] font-black {idx >= 1 ? 'text-luxury-sakura' : 'text-slate-200'} uppercase tracking-[0.4em] px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-md border border-white/10">
                       {idx === 0 ? mkt.label_activation : mkt.label_full_treatment}
                    </p>
                  </div>
                </div>

                <!-- CONTENT WRAPPER -->
                <div class="px-8 pb-8 pt-6 flex flex-col flex-grow relative z-20">
                  <h5 class="text-xl font-black text-white mb-4 italic tracking-tight text-center md:text-left">{getVariantTitle(variant)}</h5>

                  <div class="flex items-baseline justify-center md:justify-start flex-nowrap gap-x-4 mb-2">
                  {#if variant.price > unitPrice}
                     <span class="original-price text-sm text-slate-600 line-through">{(variant.price).toLocaleString()}đ</span>
                  {:else}
                     <span class="text-sm text-transparent">0đ</span>
                  {/if}
                  <span class="text-3xl font-black text-white tabular-nums">
                    {(unitPrice).toLocaleString()}đ
                  </span>
             </div>

              <div class="flex flex-col gap-2 mt-2 items-center md:items-start">
                {#if (variant.price - unitPrice) > 0}
                  {#if !(metadata.offer_savings_prefix || '').startsWith('[OFF]') || liveEditStore.isEditMode}
                    <div class="text-[10px] text-emerald-400 font-bold uppercase tracking-wider flex items-center gap-2 bg-emerald-500/10 px-3 py-1 rounded-md border border-emerald-500/20">
                       <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                       <EditableWrapper path="metadata.offer_savings_prefix" type="text" label="SỬA TIÊU ĐỀ TIẾT KIỆM" class="inline" as="span">
                         {mkt.savings_prefix}
                       </EditableWrapper>
                       {(variant.price - unitPrice).toLocaleString()}đ
                    </div>
                  {/if}
                {/if}
                <p class="flex items-center gap-2 text-[8px] font-bold uppercase tracking-[0.1em] text-white/40 mt-3 border-t border-white/5 pt-3">
                  <span class="text-luxury-sakura">●</span> SPECS: {metadata.weight || "30G"} - {metadata.origin || "JAPAN"} | MÃ VẠCH: {variant.sku || product?.sku || 'N/A'}
                </p>
              </div>


              <ul class="bullet-list space-y-2 mb-6">
                {#each getFeatures(variant, idx, isCardActive) as feature}
                   <li class="flex items-center gap-3">
                     <span class="text-luxury-sakura font-black">✦</span>
                     <span class="text-[11px] font-black uppercase tracking-wide text-white/80">{feature.replace(/^[+!-]/, '')}</span>
                   </li>
                {/each}
                <li class="flex items-center gap-3">
                  <span class="text-luxury-sakura font-black">✦</span>
                  <a href="/chinh-sach-kiem-hang" target="_blank" rel="noopener noreferrer" class="text-[11px] font-black uppercase tracking-wide text-luxury-sakura hover:underline">
                    Kiểm tra hàng trước nhận
                  </a>
                </li>
                <li class="flex items-center gap-3">
                  <span class="text-luxury-sakura font-black">✦</span>
                  <a href="/chinh-sach-doi-tra-hoan-tien" target="_blank" rel="noopener noreferrer" class="text-[11px] font-black uppercase tracking-wide text-luxury-sakura hover:underline">
                    Đổi trả 7 ngày
                  </a>
                </li>
              </ul>

              <!-- Premium Combo & Gift Flow (Viral 2026 / Elite V2.2) - Moved to bottom for layout stability -->
              {#if variant.attributes?.gifts && variant.attributes.gifts.length > 0}
                <div class="gift-section-wrapper mt-auto mb-2">
                  <div class="flex flex-col gap-2 bg-gradient-to-br from-luxury-sakura/20 via-luxury-sakura/5 to-transparent p-4 rounded-2xl border border-luxury-sakura/20 shadow-[0_10px_30px_rgba(255,183,197,0.1)] group/gift-box hover:border-luxury-sakura/40 transition-all duration-500">
                    <div class="flex items-center justify-between mb-2">
                      <span class="text-[10px] text-luxury-sakura font-black uppercase tracking-[0.2em] flex items-center gap-2">
                         <span class="w-1.5 h-1.5 rounded-full bg-luxury-sakura mr-2"></span>
                         QUÀ TẶNG ĐỘC QUYỀN
                      </span>
                      {#if variant.attributes?.combo_qty && variant.attributes.combo_qty > 1}
                        <span class="text-[9px] bg-luxury-gold/20 text-luxury-gold px-2 py-0.5 rounded-full font-black border border-luxury-gold/10">COMBO X{variant.attributes.combo_qty}</span>
                      {/if}
                    </div>
                    
                    <div class="flex flex-col gap-2.5">
                      {#each variant.attributes.gifts as gift}
                        <div class="flex items-center gap-3 group/gift-item">
                          <div class="w-8 h-8 rounded-lg overflow-hidden shrink-0 border border-white/10 bg-black/40 flex items-center justify-center p-0.5 group-hover/gift-item:border-luxury-sakura/50 transition-colors">
                            {#if gift.image}
                              <img src={resolveMediaUrl(gift.image)} alt={gift.name} class="w-full h-full object-cover rounded-sm" loading="lazy" />
                            {:else}
                              <Zap size={14} class="text-luxury-sakura/40" />
                            {/if}
                          </div>
                          <div class="flex flex-col">
                             <span class="text-[11px] text-white/90 font-bold tracking-wide group-hover/gift-item:text-luxury-sakura transition-colors">{gift.name}</span>
                             <span class="text-[9px] text-luxury-gold font-black uppercase tracking-tighter">Số lượng: x{gift.qty}</span>
                          </div>
                        </div>
                      {/each}
                    </div>
                  </div>
                </div>
              {/if}
            </div>

           <div class="liquid-cta-viral text-white min-h-[64px] rounded-2xl font-black shadow-2xl relative overflow-hidden flex items-center justify-center px-4 w-full mt-4 pointer-events-none transition-all duration-500 {isCardActive ? 'border-2 border-luxury-sakura bg-luxury-sakura/10 scale-[1.03]' : ''}">
              <div class="relative z-10 flex items-center gap-4 w-full justify-center">
                {#if isCardActive}
                   <ShoppingCart class="w-6 h-6 shrink-0 text-luxury-sakura animate-pulse drop-shadow-md" strokeWidth={2.5} />
                   <div class="flex flex-col text-left justify-center flex-1 max-w-[75%]">
                      <span class="text-[14px] font-black uppercase tracking-[0.2em] text-white leading-none mb-1 mt-0.5 flex items-center justify-between">
                         MUA NGAY
                         <ArrowRight class="w-4 h-4 text-luxury-sakura" />
                      </span>
                      <span class="text-[10px] text-luxury-sakura uppercase font-black tracking-[0.15em] truncate">
                          Sở hữu ngay • {unitPrice.toLocaleString()}đ
                      </span>
                   </div>
                {:else}
                   <ShoppingCart class="w-5 h-5 shrink-0" strokeWidth={3} />
                   <EditableWrapper 
                      path={idx === 0 ? "metadata.offer_cta_start" : "metadata.offer_cta_full"} 
                      type="text" 
                      label="SỬA TEXT NÚT" 
                      class="inline" 
                      as="span"
                    >
                      <span class="uppercase tracking-[0.2em] text-[11px] text-center leading-tight">{idx === 0 ? mkt.cta_start : mkt.cta_full}</span>
                    </EditableWrapper>
                {/if}
              </div>
           </div>
          </div>
         </div>
      {/each}
    </div>

    <DesktopProductDetailsModal bind:active={isDetailsOpen} {product} />
  </div>
</section>
