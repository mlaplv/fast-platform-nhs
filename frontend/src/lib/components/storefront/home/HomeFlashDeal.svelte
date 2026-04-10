<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import type { Product } from '$lib/types';

  interface Props {
    products: Product[];
  }

  let { products = [] }: Props = $props();

  // Elite 2.2: Actual Data Sync matching Mobile Logic
  const flashDeals = $derived(
    products
      .filter(p => !!p.discountPrice && p.discountPrice < p.price)
      .map((p, i) => {
        const dPrice = p.discountPrice!;
        const oPrice = p.price;
        const discountPct = (oPrice - dPrice) / oPrice;
        
        return {
          ...p,
          finalPrice: dPrice,
          oldPrice: oPrice,
          discountPct,
          discountLabel: Math.round(discountPct * 100),
          image: p.images?.[0] || '/images/placeholder-product.webp',
          soldText: p.metadata?.reviews_count_text || (20 + (i * 5) % 80).toString(), 
          isHot: (p.metadata?.scarcity_seconds || 0) > 0 || (p.discountPrice && p.discountPrice / p.price < 0.5),
          progress: 50 + (i * 10) % 45 // Simulated progress based on index for variety
        };
      })
      .sort((a, b) => b.discountPct - a.discountPct)
  );

  // Countdown: sync with mobile logic (15h57m17s base)
  let seconds = $state(15 * 3600 + 57 * 60 + 17);
  let timer: ReturnType<typeof setInterval>;

  const hh = $derived(String(Math.floor(seconds / 3600)).padStart(2, '0'));
  const mm = $derived(String(Math.floor((seconds % 3600) / 60)).padStart(2, '0'));
  const ss = $derived(String(seconds % 60).padStart(2, '0'));

  onMount(() => {
    timer = setInterval(() => {
      if (seconds > 0) seconds--;
    }, 1000);
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });
</script>

<div class="desktop-flash-sale bg-white rounded-sm shadow-[0_1px_1px_0_rgba(0,0,0,0.05)] overflow-hidden mb-4">
  <div class="flex flex-row items-center justify-between px-5 py-4 border-b border-gray-100">
    <div class="flex items-center gap-4">
      <!-- Micsmo Lightning Flash Sale Header -->
      <div class="flex items-center group cursor-default">
        <h2 class="text-2xl font-black text-[#ee4d2d] italic tracking-tighter uppercase flex items-center gap-1">
          <span>F</span>
          <svg class="w-5 h-5 fill-[#ee4d2d] animate-pulse" viewBox="0 0 24 24">
            <path d="M13 2L4 14h7l-1 8 9-12h-7z"/>
          </svg>
          <span>LASH SALE</span>
        </h2>
      </div>

      <!-- Sync Countdown Block -->
      <div class="flex items-center gap-1.5 ml-4">
        <span class="bg-black text-white px-2 py-0.5 rounded-sm font-bold text-sm min-w-[30px] text-center shadow-lg">{hh}</span>
        <span class="font-black text-black">:</span>
        <span class="bg-black text-white px-2 py-0.5 rounded-sm font-bold text-sm min-w-[30px] text-center shadow-lg">{mm}</span>
        <span class="font-black text-black">:</span>
        <span class="bg-black text-white px-2 py-0.5 rounded-sm font-bold text-sm min-w-[30px] text-center shadow-lg">{ss}</span>
      </div>
    </div>
    
    <a href="/deals" class="text-[#ee4d2d] font-normal text-sm hover:underline flex items-center gap-1 group">
      Xem tất cả
      <span class="text-xs group-hover:translate-x-1 transition-transform">›</span>
    </a>
  </div>

  <!-- VIRAL SCROLL TRACK: Desktop Horizontal Version -->
  <div class="flash-deals-scroller flex overflow-x-auto no-scrollbar scroll-smooth gap-0 border-t border-gray-50">
    {#each flashDeals as deal}
      <button
        onclick={() => goto(`/${deal.slug || deal.id}`)}
        class="flex-shrink-0 w-[200px] p-4 border-r border-gray-100 last:border-r-0 hover:bg-black/[0.01] transition-all group relative overflow-hidden"
      >
        <div class="aspect-square w-full relative mb-4 overflow-hidden">
          <!-- Discount Sticker -->
          <div class="absolute top-0 right-0 bg-[#ffd839] text-[#ee4d2d] text-[11px] font-black px-1.5 py-0.5 z-10 text-center rounded-sm shadow-md">
            <div>{deal.discountLabel}%</div>
            <div class="text-[9px] uppercase font-bold text-white bg-[#ee4d2d] px-1 -mx-0.5 mt-0.5 rounded-sm">GIẢM</div>
          </div>
          
          <img 
            src={deal.image} 
            alt={deal.name} 
            class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" 
            loading="lazy"
          />
          
          <!-- Liquid Overlay -->
          <div class="absolute inset-0 bg-gradient-to-t from-black/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
        </div>

        <div class="flex flex-col items-center">
          <!-- Price Display -->
          <div class="flex flex-col items-center gap-0.5 mb-3">
            <p class="text-[#ee4d2d] font-black text-2xl tracking-tighter leading-none flex items-end">
              <span class="text-sm mb-1 mr-0.5 underline">đ</span>{deal.finalPrice.toLocaleString('vi-VN')}
            </p>
            {#if deal.oldPrice}
              <p class="text-gray-300 text-xs line-through font-medium tabular-nums capitalize">
                đ{deal.oldPrice.toLocaleString('vi-VN')}
              </p>
            {/if}
          </div>

          <!-- Progress Bar (Elite V2.2 Style) -->
          <div class="w-full h-4 bg-[#ffbda6] rounded-full relative overflow-hidden shadow-inner flex items-center justify-center">
            <div 
              class="absolute left-0 top-0 h-full bg-gradient-to-r from-[#ee4d2d] to-[#ff4d4d] rounded-full transition-all duration-1000" 
              style="width: {deal.progress}%"
            ></div>
            <span class="relative z-10 text-[9px] font-black text-white uppercase tracking-widest drop-shadow-sm truncate px-2">
              {#if deal.progress > 85}
                🔥 Đang cháy hàng
              {:else}
                Đã bán {deal.soldText}
              {/if}
            </span>
            <!-- Shine reflection animate -->
            <div class="absolute inset-0 bg-white/10 w-1/3 -skew-x-12 animate-shiver pointer-events-none"></div>
          </div>
        </div>
      </button>
    {/each}

    {#if flashDeals.length === 0}
      <div class="w-full py-20 flex flex-col items-center justify-center text-gray-400 gap-4 opacity-50">
          <svg class="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="text-sm font-bold uppercase tracking-widest">Hết phiên Flash Sale</span>
      </div>
    {/if}
  </div>
</div>

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

  @keyframes shiver {
    from { transform: translateX(-200%) skewX(-12deg); }
    to { transform: translateX(300%) skewX(-12deg); }
  }
  .animate-shiver {
    animation: shiver 3s infinite linear;
  }

  .flash-deals-scroller {
    cursor: grab;
  }
  .flash-deals-scroller:active {
    cursor: grabbing;
  }
</style>
