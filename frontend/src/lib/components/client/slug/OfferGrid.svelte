<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  import type { Product } from '$lib/types';
  import "./OfferGrid.css";
  
  let { timeLeft = 1800 }: { timeLeft?: number } = $props();

  const formatTime = (s: number) => `${Math.floor(s/60)}:${(s%60).toString().padStart(2, '0')}`;
</script>

<section id="offers" class="offer-section snap-session bg-[#020617] border-t border-white/5 relative">
    <div class="container mx-auto px-6 max-w-5xl text-center my-auto">
      <div class="timer-badge px-8 py-3 text-white font-black text-xs uppercase tracking-[0.3em] rounded-full inline-block mb-16 animate-pulse">
        Ưu đãi kết thúc sau: {formatTime(timeLeft)}
      </div>
      <h3 class="offer-title text-5xl md:text-6xl font-black leading-[0.85] tracking-tighter uppercase mb-24 text-white">
        CHỌN LIỆU TRÌNH <br/> <span class="text-blue-500">THAY ĐỔI CUỘC SỐNG.</span>
      </h3>

      <div class="package-grid grid grid-cols-1 gap-8">
         <div class="package-card group bg-[#020617] border border-white/5 p-12 text-left">
            <h4 class="text-xl font-bold opacity-30 mb-4 tracking-widest uppercase text-slate-400">Combo Cơ Bản</h4>
            <div class="text-5xl font-black mb-12 text-white">{(shopStore.currentPrice).toLocaleString()}Đ</div>
            <button onclick={() => shopStore.openCheckout()} class="btn-buy ghost w-full py-6 elite-glass rounded-3xl font-black transition-all text-sm tracking-widest uppercase border border-white/10 backdrop-blur-md">CHỌN GÓI NÀY</button>
         </div>

         <div class="package-card popular bg-[#030a1f] p-12 text-left relative overflow-hidden">
            <div class="absolute -top-5 left-1/2 -translate-x-1/2 px-8 py-2 bg-blue-600 text-white font-black text-[10px] uppercase tracking-widest rounded-full" style:z-index="var(--z-surface)">Phổ biến nhất</div>
            <h4 class="text-xl font-bold text-blue-500 mb-4 tracking-widest uppercase">Combo Elite</h4>
            <div class="text-6xl font-black mb-12 text-white">{(shopStore.currentPrice * 2 * 0.9).toLocaleString()}Đ</div>
            <button onclick={() => shopStore.openCheckout()} class="btn-buy primary w-full py-6 bg-blue-600 text-white rounded-3xl font-black shadow-[0_10px_30px_rgba(37,99,235,0.3)] transition-all text-sm tracking-widest uppercase active:scale-95">MUA NGAY</button>
         </div>
      </div>
    </div>
  </section>
