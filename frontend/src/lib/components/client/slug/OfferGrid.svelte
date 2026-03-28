<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { Product, ProductVariant } from '$lib/types';
  import { SHOP_CONFIG, OFFER_CONSTANTS } from '$lib/constants/shop';
  import "./OfferGrid.css";
  
  // ELITE V2.2: Centralized Marketing Strings for easier maintenance thưa Sếp!
  const MARKETING = {
    headline: "Chúng tôi không thể thay đổi <br/> cơ địa của bạn.",
    sub: "Nhưng cam kết: <span class=\"bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent font-bold\">Khóa Mùi 48H.</span>",
    timer_prefix: "Ưu đãi nội bộ kết thúc sau:",
    shipping_prefix: "+ Phí vận chuyển:",
    savings_prefix: "Tiết kiệm:",
    booking_suffix: "người đã đặt trong 24h qua",
    trust_verified_by: "Được kiểm định bởi",
    compliance_note: "* Giao hàng tận nơi nhanh chóng, <br/> bảo mật thông tin khách hàng tuyệt đối."
  };

  let { product, timeLeft = OFFER_CONSTANTS.timers.default_seconds } = $props<{ product: Product, timeLeft?: number }>();
  const variants = $derived(product?.variants || []);

  /**
   * ELITE V2.2: Deterministic Social Proof thưa sếp!
   * Generating 'random-looking' but stable numbers based on product ID to avoid hydration mismatch.
   */
  function getDeterministicPoints(seed: string, index: number): number {
    if (!seed) return 40 + index;
    // Simple fast hash thưa Sếp!
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
      hash = ((hash << 5) - hash) + seed.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash + index) % 20 + 40;
  }

  const bookingPoints = $derived(variants.map((_, i) => getDeterministicPoints(product.id || 'default', i)));

  // Layout logic refined for Elite V2.2 Responsive thưa Sếp!
  // Force slider on mobile for 3+ variants, but keep grid on desktop
  const isSlider = $derived(variants.length >= 3); 
  const gridClass = $derived(
    isSlider 
      ? 'slider-track overflow-x-auto scrollbar-hide snap-x snap-mandatory flex lg:grid lg:grid-cols-3' 
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

<section id="offers" class="offer-section snap-session pt-16 pb-0 relative overflow-hidden">
  <!-- Dynamic Atmospheric Layers thưa Sếp! -->
  <div class="absolute inset-0 bg-radial-at-t from-blue-900/10 to-transparent pointer-events-none"></div>
  <div class="liquid-orb top-[10%] left-[-10%] w-[800px] h-[800px] bg-blue-600/10"></div>
  <div class="liquid-orb bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-cyan-400/5"></div>

  <div class="container mx-auto px-6 max-w-5xl text-center relative z-10">
    
    <!-- Minimalist Status Bar -->
    <div class="flex justify-center mb-10">
      <div class="timer-badge px-6 py-1.5 rounded-full text-[9px] uppercase tracking-[0.3em] flex items-center gap-3">
        <span class="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_#22d3ee]"></span>
        {MARKETING.timer_prefix} <span class="font-bold tabular-nums">{formatTime(timeLeft)}</span>
      </div>
    </div>

    <!-- Professional Headline Hierarchy thưa sếp! -->
    <div class="max-w-4xl mx-auto text-center" style="margin-bottom: var(--headline-mb)">
      <h3 class="headline-title">
        {@html MARKETING.headline}
      </h3>
      <p class="headline-sub">
        {@html MARKETING.sub}
      </p>
      
      <!-- Integrated Trust Proof thưa sếp! -->
      <div class="flex items-center justify-center gap-4 mt-12 opacity-40 grayscale hover:grayscale-0 transition-all duration-500">
         <span class="text-[8px] uppercase tracking-[0.4em] font-bold text-slate-400">{MARKETING.trust_verified_by}</span>
         <div class="h-px w-8 bg-slate-800"></div>
         <span class="text-[9px] uppercase tracking-[0.2em] font-black text-slate-300">{SHOP_CONFIG.trust_marks[2]}</span>
         <div class="h-px w-8 bg-slate-800"></div>
         <span class="text-[8px] uppercase tracking-[0.4em] font-bold text-slate-400">{SHOP_CONFIG.trust_marks[3]}</span>
      </div>
    </div>

    <!-- Package Architecture -->
    <div class="package-grid {gridClass} gap-5 items-stretch" style="--cols: {isSlider ? 3 : variants.length}">
      
      {#each variants as variant, idx (variant.sku || idx)}
         <!-- Card thưa sếp! -->
          <div class="package-card p-8 md:p-10 text-left flex flex-col h-full border-white/5 relative {isSlider ? 'min-w-[300px] md:min-w-[340px] snap-center' : ''} {idx === 1 ? 'popular md:scale-[1.03]' : ''}">
           {#if idx === 1}
              <div class="absolute -top-3 right-8 px-4 py-1.5 bg-blue-600/90 text-white font-black text-[8px] uppercase tracking-[0.3em] rounded-md shadow-xl backdrop-blur-md">
                {OFFER_CONSTANTS.labels.expert_choice}
              </div>
           {/if}

           <div class="mb-6">
             <div class="flex items-center justify-between mb-4">
               <p class="text-[8px] font-bold {idx === 1 ? 'text-cyan-400' : 'text-slate-500'} uppercase tracking-[0.4em]">
                  {idx === 0 ? OFFER_CONSTANTS.labels.activation : OFFER_CONSTANTS.labels.full_treatment}
               </p>
               {#if idx > 0}
                 <div class="flex items-center gap-1.5 px-2 py-0.5 bg-red-500/10 border border-red-500/20 rounded text-[7px] font-black text-red-400 uppercase tracking-wider animate-pulse">
                   <span class="w-1 h-1 bg-red-400 rounded-full"></span>
                   {OFFER_CONSTANTS.labels.scarcity}
                 </div>
               {/if}
             </div>
             <h5 class="text-xl font-bold text-white mb-4">{getVariantTitle(variant)}</h5>
             
             <div class="flex items-baseline gap-3 mb-2">
               {#if variant.price > (variant.discountPrice || variant.price)}
                  <span class="text-xs text-slate-600 line-through">{(variant.price).toLocaleString()}đ</span>
               {/if}
               <span class="text-3xl font-black text-white">{(variant.discountPrice || variant.price).toLocaleString()}đ</span>
             </div>
             
              {#if idx === 0}
                 <p class="text-[9px] text-blue-400 font-bold uppercase tracking-widest">{MARKETING.shipping_prefix} {SHOP_CONFIG.shipping.fixed_cost.toLocaleString()}đ</p>
              {:else}
                 <div class="flex flex-col gap-1">
                   <p class="text-[9px] text-emerald-400 font-bold uppercase tracking-widest">{MARKETING.savings_prefix} {(variant.price - (variant.discountPrice || variant.price)).toLocaleString()}đ</p>
                   <p class="text-[8px] text-slate-500 italic opacity-60">🔥 {bookingPoints[idx]} {MARKETING.booking_suffix}</p>
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

           <button 
             onclick={() => { shopStore.setQuantity(idx + 1); shopStore.openCheckout(); }} 
             class="btn-buy primary w-full text-[9px] uppercase tracking-[0.2em] {idx !== 1 ? 'opacity-90 hover:opacity-100' : 'shadow-[0_0_20px_rgba(59,130,246,0.3)]'}"
           >
             {idx === 0 ? OFFER_CONSTANTS.labels.cta_start : OFFER_CONSTANTS.labels.cta_full}
           </button>
          </div>
      {/each}

    </div>

    <!-- Pharmacy Trust Footer - Viral Liquid Glass thưa sếp! -->
    <div class="w-full mb-[-1px]">
      <div class="pharmacy-footer group">
        <!-- Specular Sheen Effect -->
        <div class="absolute inset-0 overflow-hidden rounded-[inherit] pointer-events-none">
          <div class="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-[2000ms] ease-in-out"></div>
        </div>

        <div class="info-grid">
          <!-- Identity -->
          <div class="contact-item">
            <span class="label">PHÂN PHỐI CHÍNH HÃNG</span>
            <span class="value text-white font-bold text-lg block mb-2">{SHOP_CONFIG.pharmacy.name}</span>
            <div class="flex items-start gap-2">
              <svg class="w-3.5 h-3.5 text-slate-500 mt-1 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
              <span class="value text-[11px] text-slate-400">{SHOP_CONFIG.pharmacy.address}</span>
            </div>
          </div>

          <!-- Connectivity -->
          <div class="contact-item">
            <span class="label">HỖ TRỢ TRỰC TUYẾN</span>
            <div class="space-y-3">
              <a href="tel:{SHOP_CONFIG.pharmacy.phone.replace(/\s/g, '')}" class="flex items-center gap-3 group/link">
                <div class="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20 group-hover/link:bg-blue-500/20 transition-colors">
                  <svg class="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 005.47 5.47l.772-1.547a1 1 0 011.06-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z"/></svg>
                </div>
                <span class="value font-bold text-blue-400">{SHOP_CONFIG.pharmacy.phone}</span>
              </a>
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
                  <span class="text-[10px] font-black text-cyan-400">Zalo</span>
                </div>
                <span class="value text-slate-300">{SHOP_CONFIG.pharmacy.zalo}</span>
              </div>
            </div>
          </div>

          <!-- Trust Markers -->
          <div class="contact-item">
            <span class="label">CAM KẾT DỊCH VỤ</span>
            <div class="flex flex-wrap gap-2 mb-4">
               <span class="px-3 py-1 bg-white/5 text-white text-[9px] font-bold rounded-lg border border-white/10 backdrop-blur-md">{SHOP_CONFIG.trust_marks[0]}</span>
               <span class="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-[9px] font-bold rounded-lg border border-emerald-500/20 backdrop-blur-md">{SHOP_CONFIG.trust_marks[1]}</span>
            </div>
            <p class="text-[10px] text-slate-500 italic leading-relaxed">
              {@html MARKETING.compliance_note}
            </p>
          </div>
        </div>

        <!-- Compliance Label -->
        <div class="license-tag">
          <span class="px-4 py-1.5 bg-black/40 rounded-full border border-white/5">
            {SHOP_CONFIG.pharmacy.license}
          </span>
        </div>
      </div>
    </div>
  </div>

  <!-- Dynamic Line Wave Divider - High Impact Edition thưa Sếp! -->
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
