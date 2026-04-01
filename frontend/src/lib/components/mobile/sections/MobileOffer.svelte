<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';
  import { SHOP_CONFIG, OFFER_CONSTANTS } from '$lib/constants/shop';
  import { ShoppingCart, Clock } from 'lucide-svelte';
  
  let { product } = $props();
  const shopStore = getShopStore();
  const variants = $derived(product?.variants || []);
  const timeLeft = $derived(shopStore.timeLeft);
  const metadata = $derived(product?.metadata || {});

  const mkt = $derived({
    headline: metadata.offer_headline || "Chúng tôi không thể thay đổi <br/> cơ địa của bạn.",
    sub: metadata.offer_subheadline || "Nhưng cam kết: <span class=\"text-blue-400 font-bold\">Khóa Mùi 48H.</span>",
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

  function getVariantTitle(variant: any): string {
    if (!product.tierVariations?.length || !variant.tierIndex?.length) return variant.sku || 'Combo';
    return variant.tierIndex.map((optIdx: number, tierIdx: number) => {
      const option = product.tierVariations![tierIdx]?.options[optIdx];
      if (typeof option === 'string') return option;
      if (typeof option === 'object' && option) return (option.name || option.label || '');
      return '';
    }).filter(Boolean).join(' - ') || 'Combo';
  }
</script>

<div class="h-full flex flex-col px-6 pt-[var(--mobile-top-space)] pb-[var(--mobile-bottom-space)] bg-[#030303] relative overflow-hidden">
  <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-80 bg-blue-600/10 blur-[100px] pointer-events-none"></div>

  <!-- Scarcity Floating Header -->
  <div class="mt-6 flex justify-center z-10">
    <div class="bg-black/40 border border-white/10 px-6 py-2.5 rounded-2xl backdrop-blur-3xl flex items-center gap-3 shadow-2xl">
      <Clock class="w-4 h-4 text-red-500 animate-pulse" />
      <div class="flex flex-col">
        <span class="text-[7px] text-white/30 font-black uppercase tracking-[0.3em]">{mkt.timer_prefix}</span>
        <span class="text-[11px] text-white font-black tabular-nums tracking-widest italic">{formatTime(timeLeft)}</span>
      </div>
    </div>
  </div>

  <div class="mt-8 mb-8 text-center">
    <h2 class="text-4xl font-black text-white leading-none uppercase tracking-tighter italic mb-4">
      {@html mkt.headline}
    </h2>
    <p class="text-white/30 text-[9px] uppercase tracking-[0.5em] font-black italic">{@html mkt.sub}</p>
  </div>

  <div class="flex-1 space-y-6 overflow-y-auto pr-1 pb-10">
    {#each variants as variant, i}
      <div 
        class="package-card p-6 rounded-[3rem] border transition-all duration-500 relative overflow-hidden group {i === 1 ? 'bg-blue-600 border-white/20 shadow-[0_20px_50px_rgba(37,99,235,0.3)] scale-[1.02]' : 'bg-white/[0.03] border-white/10 backdrop-blur-2xl'}"
      >
        {#if i === 1}
          <div class="absolute top-0 right-0 bg-yellow-400 text-black px-5 py-2 rounded-bl-3xl font-black text-[9px] uppercase tracking-widest shadow-xl animate-pulse z-20">
            {mkt.label_expert_choice}
          </div>
        {/if}

        <div class="flex justify-between items-start mb-6">
          <div>
            <h4 class="text-white font-black text-xl uppercase tracking-tighter italic drop-shadow-md">{getVariantTitle(variant)}</h4>
            <div class="flex items-center gap-2 mt-2">
              <span class="px-2.5 py-1 bg-white/10 rounded-full text-[8px] font-black uppercase tracking-widest text-white/80 backdrop-blur-md">
                 {i === 0 ? mkt.label_activation : mkt.label_full_treatment}
              </span>
              {#if i === 1}
                <span class="px-2.5 py-1 bg-red-500 text-white text-[8px] font-black rounded-full shadow-lg border border-white/20">MUA 2 TẶNG 1</span>
              {/if}
            </div>
          </div>
          <div class="text-right flex flex-col items-end">
             <span class="text-xs text-white/40 line-through font-bold opacity-50">{(variant.price).toLocaleString()}đ</span>
             <span class="text-3xl font-black text-white italic tracking-tighter">{(variant.discountPrice || variant.price).toLocaleString()}đ</span>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-8">
           <div class="flex items-center gap-2 bg-white/5 p-3 rounded-2xl border border-white/5">
              <div class="w-1.5 h-1.5 bg-emerald-400 rounded-full shadow-[0_0_8px_rgba(52,211,153,0.6)]"></div>
              <span class="text-[7px] font-black text-white/60 uppercase tracking-widest leading-tight">Freeship <br/>Toàn quốc</span>
           </div>
           <div class="flex items-center gap-2 bg-white/5 p-3 rounded-2xl border border-white/5">
              <div class="w-1.5 h-1.5 bg-blue-400 rounded-full shadow-[0_0_8px_rgba(96,165,250,0.6)]"></div>
              <span class="text-[7px] font-black text-white/60 uppercase tracking-widest leading-tight">Kiểm hàng <br/>Thanh toán</span>
           </div>
        </div>

        <button 
          onclick={() => { 
            shopStore.selectVariant(variant); 
            if (i === 1) shopStore.setQuantity(3); // Mua 2 tặng 1
            shopStore.openCheckout(); 
          }}
          class="w-full py-6 rounded-[2rem] font-black text-[14px] uppercase tracking-[0.2em] flex items-center justify-center gap-3 transition-all duration-300 italic {i === 1 ? 'bg-white text-blue-600 shadow-2xl hover:scale-[1.03] active:scale-95' : 'bg-white/10 text-white border border-white/10 hover:bg-white/20'}"
        >
          {i === 0 ? mkt.cta_start : mkt.cta_full} <ShoppingCart class="w-5 h-5" />
        </button>
      </div>
    {/each}
  </div>

  <div class="mt-4 flex justify-center gap-6 opacity-30 invert pb-10">
    <div class="text-[9px] uppercase tracking-widest font-black text-white">{SHOP_CONFIG.trust_marks[2]}</div>
    <div class="text-[9px] uppercase tracking-widest font-black text-white">{SHOP_CONFIG.trust_marks[3]}</div>
  </div>
</div>
