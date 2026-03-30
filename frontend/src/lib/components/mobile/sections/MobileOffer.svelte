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

<div class="h-full flex flex-col justify-center px-6 py-20 bg-[#020617] relative">
  <!-- Scarcity Floating Header -->
  <div class="absolute top-10 left-0 right-0 flex justify-center z-10">
    <div class="bg-red-600/20 border border-red-500/30 px-6 py-2 rounded-full backdrop-blur-md flex items-center gap-3">
      <Clock class="w-4 h-4 text-red-400 animate-pulse" />
      <span class="text-[10px] text-red-200 font-black uppercase tracking-[0.2em]">{mkt.timer_prefix} <span class="tabular-nums ml-1">{formatTime(timeLeft)}</span></span>
    </div>
  </div>

  <div class="mb-10 mt-12 text-center">
    <h2 class="text-3xl font-black text-white leading-tight uppercase tracking-tighter italic mb-4">
      {@html mkt.headline}
    </h2>
    <p class="text-white/40 text-[10px] uppercase tracking-[0.3em] font-medium italic">{@html mkt.sub}</p>
  </div>

  <div class="grid gap-4">
    {#each variants as variant, i}
      <div 
        class="package-card p-6 rounded-[32px] border transition-all duration-300 relative overflow-hidden group {i === 1 ? 'bg-blue-600 border-blue-500 shadow-[0_20px_40px_rgba(37,99,235,0.25)]' : 'bg-white/5 border-white/10'}"
      >
        {#if i === 1}
          <div class="absolute top-0 right-0 bg-yellow-400 text-black px-4 py-1.5 rounded-bl-2xl font-black text-[9px] uppercase tracking-widest shadow-lg">{mkt.label_expert_choice}</div>
        {/if}

        <div class="flex justify-between items-start mb-4">
          <div>
            <h4 class="text-white font-black text-lg uppercase tracking-tight">{getVariantTitle(variant)}</h4>
            <div class="flex items-center gap-2 mt-1">
              <p class="text-[10px] uppercase tracking-widest {i === 1 ? 'text-white/80' : 'text-white/40'} font-bold">
                 {i === 0 ? mkt.label_activation : mkt.label_full_treatment}
              </p>
              {#if i === 1}
                <span class="px-2 py-0.5 bg-red-500 text-white text-[8px] font-black rounded-lg animate-bounce">MUA 2 TẶNG 1</span>
              {/if}
            </div>
          </div>
          <div class="text-right">
             <p class="text-[10px] text-white/40 line-through">{(variant.price).toLocaleString()}đ</p>
             <p class="text-2xl font-black text-white italic">{(variant.discountPrice || variant.price).toLocaleString()}đ</p>
             {#if i === 1}
               <p class="text-[9px] font-black text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full inline-block mt-1 uppercase tracking-tighter">TIẾT KIỆM KHỦNG</p>
             {/if}
          </div>
        </div>

        <div class="space-y-3 mb-6">
           {#if i > 0 || variant.discountPrice}
             <div class="flex items-center gap-2 text-[9px] font-black text-emerald-400/90 uppercase tracking-widest">
                <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full shadow-[0_0_8px_rgba(52,211,153,0.5)]"></span>
                MIỄN PHÍ VẬN CHUYỂN TOÀN QUỐC 🚚
             </div>
           {/if}
           <div class="flex items-center gap-2 text-[9px] font-black text-white/60 uppercase tracking-widest">
              <span class="w-1.5 h-1.5 bg-blue-400 rounded-full"></span>
              Kiểm hàng trước khi thanh toán
           </div>
        </div>

        <button 
          onclick={() => { 
            shopStore.selectVariant(variant); 
            if (i === 1) shopStore.setQuantity(3); // Mua 2 tặng 1
            shopStore.openCheckout(); 
          }}
          class="w-full py-4 rounded-2xl font-black text-[11px] uppercase tracking-[0.2em] flex items-center justify-center gap-3 transition-all duration-300 {i === 1 ? 'bg-white text-blue-600 hover:scale-[1.02]' : 'bg-blue-600 text-white hover:bg-blue-500'}"
        >
          {i === 0 ? mkt.cta_start : mkt.cta_full} <ShoppingCart class="w-4 h-4" />
        </button>
      </div>
    {/each}
  </div>

  <div class="mt-12 flex justify-center gap-6 opacity-30 grayscale invert">
    <div class="text-[9px] uppercase tracking-widest font-black text-white">{SHOP_CONFIG.trust_marks[2]}</div>
    <div class="text-[9px] uppercase tracking-widest font-black text-white">{SHOP_CONFIG.trust_marks[3]}</div>
  </div>
</div>
