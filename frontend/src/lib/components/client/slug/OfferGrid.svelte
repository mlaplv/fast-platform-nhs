<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { Product, ProductVariant } from '$lib/types';
  import { SHOP_CONFIG, OFFER_CONSTANTS } from '$lib/constants/shop';
  import { ShoppingCart, CheckCircle2, Info } from 'lucide-svelte';
  import DesktopProductDetailsModal from './DesktopProductDetailsModal.svelte';
  import "./OfferGrid.css";
  
  const shopStore = getShopStore();
  
  // ELITE V2.2: Centralized Marketing Strings for easier maintenance!
  const metadata = $derived(product?.metadata || {});

  const mkt = $derived({
    headline: metadata.offer_headline || "Chúng tôi không thể thay đổi <br/> cơ địa của bạn.",
    sub: metadata.offer_subheadline || "Nhưng cam kết: <span class=\"bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent font-bold\">Khóa Mùi 48H.</span>",
    timer_prefix: metadata.offer_timer_prefix || "Ưu đãi nội bộ kết thúc sau:",
    shipping_prefix: metadata.offer_shipping_prefix || "+ Phí vận chuyển:",
    savings_prefix: metadata.offer_savings_prefix || "Tiết kiệm:",
    booking_suffix: metadata.offer_booking_suffix || "người đã đặt trong 24h qua",
    trust_verified_by: metadata.offer_trust_verified_by || "Được kiểm định bởi",
    compliance_note: metadata.offer_compliance_note || "* Giao hàng tận nơi nhanh chóng, <br/> bảo mật thông tin khách hàng tuyệt đối.",
    label_activation: metadata.offer_label_activation || OFFER_CONSTANTS.labels.activation,
    label_full_treatment: metadata.offer_label_full_treatment || OFFER_CONSTANTS.labels.full_treatment,
    label_expert_choice: metadata.offer_label_expert_choice || OFFER_CONSTANTS.labels.expert_choice,
    label_scarcity: metadata.offer_label_scarcity || OFFER_CONSTANTS.labels.scarcity,
    cta_start: metadata.offer_cta_start || OFFER_CONSTANTS.labels.cta_start,
    cta_full: metadata.offer_cta_full || OFFER_CONSTANTS.labels.cta_full,
    label_distributor: (metadata.offer_label_distributor as string) || 'PHÂN PHỐI CHÍNH HÃNG',
    pharmacy_name: (metadata.offer_pharmacy_name as string) || SHOP_CONFIG.pharmacy.name,
    label_support: (metadata.offer_label_support as string) || 'HỖ TRỢ TRỰC TUYẾN',
    label_commitment: (metadata.offer_label_commitment as string) || 'CAM KẾT DỊCH VỤ',
    label_license: (metadata.offer_label_license as string) || SHOP_CONFIG.pharmacy.license,
    pharmacy_address: (metadata.offer_pharmacy_address as string) || SHOP_CONFIG.pharmacy.address,
    pharmacy_phone: (metadata.offer_pharmacy_phone as string) || SHOP_CONFIG.pharmacy.phone,
    pharmacy_zalo: (metadata.offer_pharmacy_zalo as string) || SHOP_CONFIG.pharmacy.zalo,
    trust_mark_2: (metadata.offer_trust_mark_2 as string) || SHOP_CONFIG.trust_marks[2],
    trust_mark_3: (metadata.offer_trust_mark_3 as string) || SHOP_CONFIG.trust_marks[3]
  });

  const product = $derived(shopStore.product);
  const timeLeft = $derived(shopStore.timeLeft);
  const variants = $derived(product?.variants || []);
  let isDetailsOpen = $state(false);

  /**
   * ELITE V2.2: Deterministic Social Proof!
   * Generating 'random-looking' but stable numbers based on product ID to avoid hydration mismatch.
   */
  function getDeterministicPoints(seed: string, index: number): number {
    if (!seed) return 40 + index;
    // Simple fast hash!
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
      hash = ((hash << 5) - hash) + seed.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash + index) % 20 + 40;
  }

  const bookingPoints = $derived(variants.map((_, i) => getDeterministicPoints(product.id || 'default', i)));

  // Layout logic refined for Elite V2.2 Responsive!
  // Force slider on mobile for 3+ variants, but keep grid on desktop
  const isSlider = $derived(variants.length >= 3); 
  const gridClass = $derived(
    isSlider 
      ? 'slider-track overflow-x-auto scrollbar-hide snap-x snap-mandatory flex md:grid md:grid-cols-3' 
      : `grid grid-cols-1 ${variants.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-3'}`
  );

  function getVariantTitle(variant: ProductVariant): string {
    if (!product.tierVariations?.length || !variant.tierIndex?.length) return variant.sku || 'Combo';
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

  const getFeatures = (variant: ProductVariant, idx: number): string[] => {
    return (variant.attributes?.features as string[]) || SHOP_CONFIG.default_features[idx > 0 ? 1 : 0] || [];
  };
</script>

<section class="offer-section relative overflow-hidden">
  <!-- Dynamic Atmospheric Layers! -->
  <div class="absolute inset-0 bg-radial-at-t from-blue-900/10 to-transparent pointer-events-none"></div>
  <div class="liquid-orb top-[10%] left-[-10%] w-[800px] h-[800px]" style:background-color="var(--elite-blue)" style:opacity="0.1"></div>
  <div class="liquid-orb bottom-[-10%] right-[-10%] w-[600px] h-[600px]" style:background-color="var(--elite-cyan)" style:opacity="0.05"></div>

  <div class="container mx-auto px-4 md:px-6 max-w-6xl text-center relative z-10 pt-[var(--standard-pt)]">
    
    

    <!-- Professional Headline Hierarchy! -->
    <div class="max-w-4xl mx-auto text-center" style:margin-bottom="var(--headline-mb)">
      <h3 class="headline-title">
        {@html mkt.headline}
      </h3>
      <p class="headline-sub">
        {@html mkt.sub}
      </p>

      <!-- Integrated Trust Proof! -->
      <div class="flex items-center justify-center gap-4 mt-12 opacity-40 grayscale hover:grayscale-0 transition-all duration-500">
         <span class="text-[8px] uppercase tracking-[0.4em] font-bold text-slate-400">{mkt.trust_verified_by}</span>
         <div class="h-px w-8 bg-slate-800"></div>
         <span class="text-[9px] uppercase tracking-[0.2em] font-black text-slate-300">{mkt.trust_mark_2}</span>
         <div class="h-px w-8 bg-slate-800"></div>
         <span class="text-[8px] uppercase tracking-[0.4em] font-bold text-slate-400">{mkt.trust_mark_3}</span>
      </div>
    </div>

    <!-- Minimalist Status Bar -->
    <div class="flex justify-center mb-10">
      <div class="timer-badge px-6 py-1.5 rounded-full text-[9px] uppercase tracking-[0.3em] flex items-center gap-3">
        <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_#22d3ee]"></span>
        {mkt.timer_prefix} <span class="font-bold tabular-nums">{formatTime(timeLeft)}</span>
      </div>
    </div>

    <!-- ELITE V2.2: Liquid Glass Multi-Deal Bar (iPhone 18 Aesthetic) -->
    <div class="mt-2 mb-12 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-4 px-4">
      {#each (metadata.active_deals || []) as deal}
        {@const isActive = shopStore.quantity === (deal.buy_qty + (deal.get_qty || 0))}
        <button 
           onclick={() => shopStore.setQuantity(deal.buy_qty + (deal.get_qty || 0))}
           class="liquid-glass-deal rounded-3xl px-8 py-5 flex items-center justify-between group active:scale-[0.98] {isActive ? 'active' : ''}"
        >
           <div class="glare-effect"></div>
           
           <div class="flex items-center gap-5 relative z-10">
              <div class="liquid-orb {isActive ? 'animate-pulse' : 'inactive'}"></div>
              <div class="flex flex-col text-left">
                 <span class="text-[10px] font-black text-blue-400 uppercase tracking-[0.2em] mb-1 opacity-80 group-hover:opacity-100 transition-opacity">Ưu đãi: {deal.label.replace('🎁', '')}</span>
                 <span class="text-white text-lg font-black italic tracking-tight uppercase leading-none">
                    CHỈ CÒN <span class="text-2xl not-italic ml-1">{(deal.fixed_price).toLocaleString()}đ</span>
                 </span>
              </div>
           </div>

           <div class="flex items-center gap-3 relative z-10">
              {#if isActive}
                 <div class="flex flex-col items-end">
                    <CheckCircle2 class="w-6 h-6 text-blue-400 mb-1" strokeWidth={3} />
                    <span class="text-[8px] font-black text-blue-400 tracking-widest uppercase">ĐÃ ÁP DỤNG</span>
                 </div>
              {:else}
                 <span class="text-[9px] font-black text-white/30 group-hover:text-white transition-all uppercase tracking-[0.2em] flex items-center gap-2">
                    ÁP DỤNG NGAY
                    <span class="text-lg leading-none transition-transform group-hover:translate-x-1">→</span>
                 </span>
              {/if}
           </div>
        </button>
      {/each}
    </div>

    <!-- Package Architecture -->
    <div class="package-grid {gridClass} gap-5 items-stretch" style:--cols={isSlider ? 3 : variants.length}>

      {#each variants as variant, idx (variant.sku || idx)}
         <!-- Card! -->
          <div class="package-card p-8 md:p-10 text-left flex flex-col h-full border-white/5 relative {isSlider ? 'min-w-[300px] md:min-w-[340px] snap-center' : ''} {idx === 1 ? 'popular md:scale-[1.03]' : ''}">
           <div class="absolute -top-3 right-8 flex flex-wrap gap-2 justify-end">
              {#if idx === 1}
                 <div class="px-4 py-1.5 bg-blue-600/90 text-white font-black text-[8px] uppercase tracking-[0.3em] rounded-md shadow-xl backdrop-blur-md">
                   {mkt.label_expert_choice}
                 </div>
              {/if}
           </div>

           <div class="mb-6">
             <div class="flex items-center justify-between mb-4">
               <p class="text-[8px] font-bold {idx === 1 ? 'text-cyan-400' : 'text-slate-500'} uppercase tracking-[0.4em]">
                  {idx === 0 ? mkt.label_activation : mkt.label_full_treatment}
               </p>
               {#if idx > 0}
                 <div class="flex items-center gap-1.5 px-2 py-0.5 bg-red-500/10 border border-red-500/20 rounded text-[7px] font-black text-red-400 uppercase tracking-wider animate-pulse">
                   <span class="w-1 h-1 bg-red-400 rounded-full"></span>
                   {mkt.label_scarcity}
                 </div>
               {/if}
             </div>
             <h5 class="text-xl font-bold text-white mb-4">{getVariantTitle(variant)}</h5>

             <div class="flex items-baseline gap-3 mb-2">
               {#if (shopStore.originalPrice * shopStore.quantity) > shopStore.totalAmount && shopStore.selectedVariant?.sku === variant.sku}
                  <span class="text-xs text-slate-600 line-through">{(shopStore.originalPrice * shopStore.quantity).toLocaleString()}đ</span>
               {:else if variant.price > (variant.discountPrice || variant.price)}
                  <span class="text-xs text-slate-600 line-through">{(variant.price).toLocaleString()}đ</span>
               {/if}
               <span class="text-3xl font-black text-white">
                 {shopStore.selectedVariant?.sku === variant.sku ? shopStore.totalAmount.toLocaleString() : (variant.discountPrice || variant.price).toLocaleString()}đ
               </span>
             </div>

              {#if idx === 0}
                 <p class="text-[9px] text-blue-400 font-bold uppercase tracking-widest">{mkt.shipping_prefix} {SHOP_CONFIG.shipping.fixed_cost.toLocaleString()}đ</p>
              {:else}
                 <div class="flex flex-col gap-1">
                   <p class="text-[9px] text-emerald-400 font-bold uppercase tracking-widest">{mkt.savings_prefix} {(variant.price - (variant.discountPrice || variant.price)).toLocaleString()}đ</p>
                   <p class="text-[8px] text-slate-500 italic opacity-60">🔥 {bookingPoints[idx]} {mkt.booking_suffix}</p>
                 </div>
              {/if}
           </div>

           <ul class="bullet-list mb-8 flex-grow space-y-2">
             {#each getFeatures(variant, idx) as feature}
                <li class="flex items-center gap-2 {feature.startsWith('+') ? 'font-bold text-slate-200' : ''} {feature.startsWith('!') ? 'text-emerald-400' : ''} {feature.startsWith('-') ? 'opacity-20' : ''}">
                  <span class="icon-check {feature.startsWith('!') ? 'text-emerald-400' : 'text-cyan-400'}">
                    {feature.startsWith('-') ? '−' : '✦'}
                  </span>
                  <span>{feature.replace(/^[+!-]/, '')}</span>
                </li>
             {/each}
           </ul>

           <div class="flex gap-2 items-stretch mt-auto">
             <button
               onclick={() => { shopStore.selectVariant(variant); shopStore.openCheckout(); }}
               class="flex-[1.8] bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white h-[52px] rounded-xl font-black text-[9px] uppercase tracking-[0.2em] shadow-[0_10px_30px_rgba(37,99,235,0.2)] hover:shadow-[0_15px_40px_rgba(37,99,235,0.4)] transition-all active:scale-[0.98] group relative overflow-hidden flex items-center justify-center px-4"
             >
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite] pointer-events-none"></div>
                <div class="flex items-center gap-2">
                  <ShoppingCart class="w-3.5 h-3.5 mb-0.5" strokeWidth={3} />
                  <span>{idx === 0 ? mkt.cta_start : mkt.cta_full}</span>
                </div>
             </button>

             <button 
               onclick={() => isDetailsOpen = true}
               class="flex-1 bg-white/[0.03] hover:bg-white/[0.08] backdrop-blur-3xl border border-white/10 rounded-xl h-[52px] flex items-center justify-center transition-all active:scale-[0.98] group gap-2 px-2"
             >
               <Info class="w-3.5 h-3.5 text-white/40 group-hover:text-blue-400 transition-colors" />
               <span class="text-[8px] font-black text-white/40 group-hover:text-white uppercase tracking-[0.1em] leading-tight text-left">XEM<br/>CHI TIẾT</span>
             </button>
           </div>
          </div>
      {/each}

    </div>


    <DesktopProductDetailsModal bind:active={isDetailsOpen} {product} />

    <!-- Pharmacy Trust Footer - Viral Liquid Glass! -->
    <div class="w-full">
      <div class="pharmacy-footer group">
        <!-- Specular Sheen Effect -->
        <div class="absolute inset-0 overflow-hidden rounded-[inherit] pointer-events-none">
          <div class="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-[2000ms] ease-in-out"></div>
        </div>

        <div class="info-grid">
          <!-- Identity -->
          <div class="contact-item">
            <span class="label uppercase">{mkt.label_distributor}</span>
            <span class="value text-white font-bold text-lg block mb-2">{mkt.pharmacy_name}</span>
            <div class="flex items-start gap-2">
              <svg class="w-3.5 h-3.5 text-slate-500 mt-1 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
              <span class="value text-[11px] text-slate-400">{mkt.pharmacy_address}</span>
            </div>
          </div>

          <!-- Connectivity -->
          <div class="contact-item">
            <span class="label uppercase">{mkt.label_support}</span>
            <div class="space-y-3">
              <a href="tel:{mkt.pharmacy_phone.replace(/\s/g, '')}" class="flex items-center gap-3 group/link">
                <div class="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20 group-hover/link:bg-blue-500/20 transition-colors">
                  <svg class="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 005.47 5.47l.772-1.547a1 1 0 011.06-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z"/></svg>
                </div>
                <span class="value font-bold text-blue-400">{mkt.pharmacy_phone}</span>
              </a>
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
                  <span class="text-[10px] font-black text-cyan-400">Zalo</span>
                </div>
                <span class="value text-slate-300">{mkt.pharmacy_zalo}</span>
              </div>
            </div>
          </div>

          <!-- Trust Markers -->
          <div class="contact-item">
            <span class="label uppercase">{mkt.label_commitment}</span>
            <div class="flex flex-wrap gap-2 mb-4">
               <span class="px-3 py-1 bg-white/5 text-white text-[9px] font-bold rounded-lg border border-white/10 backdrop-blur-md">{SHOP_CONFIG.trust_marks[0]}</span>
               <span class="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-[9px] font-bold rounded-lg border border-emerald-500/20 backdrop-blur-md">{SHOP_CONFIG.trust_marks[1]}</span>
            </div>
            <p class="text-[10px] text-slate-500 italic leading-relaxed">
              {@html mkt.compliance_note}
            </p>
          </div>
        </div>

        <!-- Compliance Label (Liquid Glass Edition) -->
        <div class="license-tag">
          <div class="inline-block px-6 py-2 bg-white/[0.03] backdrop-blur-2xl rounded-full border border-white/10 shadow-[0_5px_15px_rgba(0,0,0,0.3)]">
            <span class="text-[10px] font-medium text-slate-400 tracking-wide">
              {mkt.label_license}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Dynamic Line Wave Divider - High Impact Edition! -->
  <div class="wave-container">
    <svg viewBox="0 0 1440 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
      <defs>
        <linearGradient id="wave-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#3b82f6" stop-opacity="0" />
          <stop offset="50%" stop-color="#22d3ee" stop-opacity="1" />
          <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
        </linearGradient>
      </defs>
      <!-- Multi-layered lines for 'strength' -->
      <path class="wave-line opacity-20" d="M0,160 C320,300 420,20 720,160 C1020,300 1120,20 1440,160" />
      <path class="wave-line" d="M0,200 C320,340 420,60 720,200 C1020,340 1120,60 1440,200" />
      <path class="wave-line secondary" d="M0,240 C320,100 420,380 720,240 C1020,100 1120,380 1440,240" />
      <path class="wave-line opacity-30" d="M0,100 C320,240 420,-40 720,100 C1020,240 1120,-40 1440,100" />
    </svg>
  </div>
</section>
