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

  const formatTime = (s: number): string => {
    const mins = Math.floor(s / 60);
    const secs = (s % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const getFeatures = (variant: ProductVariant, idx: number, isActive: boolean): string[] => {
    const fallbackIdx = idx > 1 ? 1 : idx;
    let base = (variant as any).attributes?.features || SHOP_CONFIG.default_features[fallbackIdx] || [];
    let features = [...base].filter(f => !['Cam kết hoàn tiền ẩn danh', 'Tặng kèm Voucher'].some(term => f.includes(term)));
    
    // ĐỒNG BỘ: Tự động đổi '01' thành số combo áp dụng cho card đang chọn (Elite V2.2)
    if (isActive && shopStore.quantity > 1) {
        let displayQty = shopStore.quantity < 10 ? `0${shopStore.quantity}` : `${shopStore.quantity}`;
        features = features.map(f => {
            // Thay thế '01 ' hoặc '1 ' bằng số lượng
            return f.replace(/^(0?1)\s+/i, `${displayQty} `);
        });
    }
    return features;
  };

  const gridClass = $derived(variants.length >= 3 
    ? 'slider-track overflow-x-auto md:overflow-visible scrollbar-hide snap-x snap-mandatory flex md:grid md:grid-cols-3'
    : `grid grid-cols-1 ${variants.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-3'}`
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
      <div class="timer-badge px-8 py-2 rounded-full text-[10px] uppercase tracking-[0.4em] flex items-center gap-3 backdrop-blur-3xl shadow-[0_0_20px_rgba(255,183,197,0.1)]">
        <span class="w-2 h-2 rounded-full bg-luxury-sakura animate-pulse shadow-[0_0_12px_var(--luxury-sakura)]"></span>
        {#if !(metadata.offer_timer_prefix || '').startsWith('[OFF]') || liveEditStore.isEditMode}
          <EditableWrapper path="metadata.offer_timer_prefix" type="text" label="SỬA TIÊU ĐỀ HẸN GIỜ" class="inline" as="span">
            {mkt.timer_prefix}
          </EditableWrapper>
        {/if}
        <span class="font-black tabular-nums text-white">{formatTime(timeLeft)}</span>
      </div>
    </div>

    <div class="mt-1 mb-8 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-4 px-4 text-left">
      {#each (metadata.active_deals || []) as deal, dealIdx (dealIdx)}
        {@const isActive = shopStore.appliedDeal?.label === deal.label}
        <button 
           onclick={() => shopStore.setQuantity(deal.buy_qty + (deal.get_qty || 0))}
           class="liquid-glass-deal rounded-3xl px-8 py-5 flex items-center justify-between group active:scale-[0.98] {isActive ? 'active' : ''}"
        >
           <div class="flex items-center gap-5">
              <div class="liquid-orb {isActive ? 'animate-pulse' : 'inactive'}"></div>
              <div class="flex flex-col text-left">
                 <span class="text-[10px] font-black text-luxury-sakura uppercase tracking-[0.2em] mb-1">
                    Ưu đãi: {deal.label.replace('🎁', '')}
                    <span class="ml-1 text-white/50">(MUA {deal.buy_qty} + TẶNG {deal.get_qty || 0})</span>
                 </span>
                 <span class="text-white text-lg font-black italic tracking-tight uppercase leading-none">
                    CHỈ CÒN <span class="text-2xl not-italic ml-1">{(deal.fixed_price).toLocaleString()}đ</span>
                 </span>
              </div>
           </div>
           <div class="flex items-center gap-3">
              {#if isActive}
                 <CheckCircle2 class="w-6 h-6 text-luxury-sakura" strokeWidth={3} />
              {:else}
                 <span class="text-xl leading-none transition-transform group-hover:translate-x-2 text-white/40">→</span>
              {/if}
           </div>
        </button>
      {/each}
    </div>

    <div class="package-grid pt-20 {gridClass} gap-6 items-stretch">
      {#each variants as variant, idx (idx)}
          {@const isCardActive = shopStore.variant?.id === variant.id}
          {@const unitPrice = variant.discountPrice || variant.price}
          <div class="relative h-full z-10 {variants.length >= 3 ? 'min-w-[280px] snap-center' : ''}">
             <div class="absolute -top-4 left-1/2 -translate-x-1/2 flex flex-wrap gap-2 justify-center w-[120%] z-[60] pointer-events-none mt-1">
                {#if idx === 1 && !isCardActive}
                   <div class="px-5 py-2 expert-choice-ribbon text-white font-black text-[9px] uppercase tracking-[0.4em] rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] backdrop-blur-md">
                      {mkt.label_expert_choice}
                   </div>
                {/if}
                {#if isCardActive && shopStore.quantity > 1}
                   <div class="px-5 py-2 bg-gradient-to-r from-red-600 to-rose-500 text-white font-black text-[9px] uppercase tracking-widest rounded-xl shadow-[0_4px_30px_rgba(225,29,72,0.8)] animate-pulse flex items-center gap-1 border border-red-400/50">
                      <Zap class="w-3 h-3"/> ĐÃ ÁP DỤNG MỨC GIÁ SỈ
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
                <div class="variant-image-hero relative w-full h-[300px] mb-2 overflow-hidden">
                  <div class="absolute inset-0 bg-radial-at-t from-luxury-sakura/10 to-transparent pointer-events-none transition-opacity duration-700 {isCardActive ? 'opacity-100' : 'opacity-0'}"></div>
                  
                  <img 
                     src="{product?.images?.[0] ? resolveMediaUrl(product.images[0]) : ''}" 
                     alt="{getVariantTitle(variant)}" 
                     class="w-full h-full object-cover drop-shadow-[0_60px_40px_rgba(0,0,0,0.5)] transform hover:scale-110 transition-transform duration-1000"
                  />
                  
                  <!-- OVERLAY BADGE -->
                  <div class="absolute top-6 left-6 z-20">
                    <p class="text-[8px] font-black {idx === 1 ? 'text-luxury-sakura' : 'text-slate-200'} uppercase tracking-[0.4em] px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-md border border-white/10">
                       {idx === 0 ? mkt.label_activation : mkt.label_full_treatment}
                    </p>
                  </div>
                </div>

                <!-- CONTENT WRAPPER -->
                <div class="px-8 pb-8 pt-4 flex flex-col flex-grow">
                  <h5 class="text-xl font-black text-white mb-4 italic tracking-tight text-center md:text-left">{getVariantTitle(variant)}</h5>

                  <div class="flex items-baseline justify-center md:justify-start flex-nowrap gap-x-4 mb-2">
               {#if isCardActive && shopStore.quantity > 1}
                  <span class="original-price text-sm text-slate-600 line-through">{(variant.price * shopStore.quantity).toLocaleString()}đ</span>
                  <span class="text-4xl font-black text-white tabular-nums drop-shadow-[0_0_15px_rgba(255,183,197,0.5)]">
                    {(shopStore.totalAmount).toLocaleString()}đ
                  </span>
               {:else}
                  {#if variant.price > unitPrice}
                     <span class="original-price text-sm text-slate-600 line-through">{(variant.price).toLocaleString()}đ</span>
                  {:else}
                     <span class="text-sm text-transparent">0đ</span>
                  {/if}
                  <span class="text-3xl font-black text-white tabular-nums">
                    {(unitPrice).toLocaleString()}đ
                  </span>
               {/if}
             </div>

              <div class="flex flex-col gap-2 mt-2 items-center md:items-start">
                {#if isCardActive && shopStore.quantity > 1}
                  <p class="text-[12px] text-red-400 font-black uppercase tracking-widest flex items-center gap-3 bg-red-950/40 px-3 py-1.5 rounded-lg border border-red-900/50">
                     <span class="w-2 h-2 bg-red-500 rounded-full animate-bounce"></span>
                     TIẾT KIỆM KHỦNG: {((variant.price * shopStore.quantity) - shopStore.totalAmount).toLocaleString()}đ
                  </p>
                {:else if (variant.price - unitPrice) > 0}
                  {#if !(metadata.offer_savings_prefix || '').startsWith('[OFF]') || liveEditStore.isEditMode}
                    <p class="text-[10px] text-emerald-400 font-black uppercase tracking-widest flex items-center gap-3">
                       <span class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                       <EditableWrapper path="metadata.offer_savings_prefix" type="text" label="SỬA TIÊU ĐỀ TIẾT KIỆM" class="inline" as="span">
                         {mkt.savings_prefix}
                       </EditableWrapper>
                       {(variant.price - unitPrice).toLocaleString()}đ
                    </p>
                  {/if}
                {/if}
                <p class="flex items-center gap-2 text-[8px] font-black uppercase tracking-[0.2em] text-white/30 {isCardActive && shopStore.quantity > 1 ? 'mt-1' : ''}">
                  <span class="text-luxury-sakura animate-pulse">●</span> SPECS: {metadata.weight || "30G"} - {metadata.origin || "JAPAN"} | MÃ VẠCH: {variant.sku || product?.sku || 'N/A'}
                </p>
              </div>
           </div>

           <ul class="bullet-list mb-8 flex-grow space-y-2">
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
                         {shopStore.quantity} MÓN • {(shopStore.totalAmount).toLocaleString()}Đ
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
