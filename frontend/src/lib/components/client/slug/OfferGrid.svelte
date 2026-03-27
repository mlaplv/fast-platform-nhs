<script lang="ts">
  import { shopStore } from '$lib/state/commerce/shop.svelte.ts';
  
  let { timeLeft = 1800 }: { timeLeft?: number } = $props();

  const formatTime = (s: number) => `${Math.floor(s/60)}:${(s%60).toString().padStart(2, '0')}`;
</script>

<section class="offer-section py-32 bg-canvas border-t border-subtle">
    <div class="container mx-auto px-6 max-w-5xl text-center">
      <div class="timer-badge px-8 py-3 text-white font-black text-xs uppercase tracking-[0.3em] rounded-full inline-block mb-24 animate-pulse">
        Ưu đãi kết thúc sau: {formatTime(timeLeft)}
      </div>
      <h3 class="offer-title text-6xl font-black leading-[0.85] tracking-tighter uppercase mb-24">
        CHỌN LIỆU TRÌNH <br/> <span class="text-blue-500">THAY ĐỔI CUỘC SỐNG.</span>
      </h3>

      <div class="grid grid-cols-1 gap-8 package-grid">
         <div class="package-card group bg-surface border border-subtle p-12 rounded-[4rem] text-left transition-all">
            <h4 class="package-label text-xl font-bold opacity-30 mb-4 tracking-widest uppercase">Combo Cơ Bản</h4>
            <div class="package-price text-5xl font-black mb-12">{(shopStore.currentPrice).toLocaleString()}Đ</div>
            <button onclick={() => shopStore.openCheckout()} class="btn-ghost w-full py-6 elite-glass rounded-3xl font-black transition-all text-sm tracking-widest uppercase">CHỌN GÓI NÀY</button>
         </div>

         <div class="package-card package-card--popular bg-surface border-2 border-blue-500 p-12 rounded-[4rem] text-left relative">
            <div class="popular-tag absolute -top-5 left-1/2 -translate-x-1/2 px-8 py-2 bg-blue-500 text-white font-black text-[10px] uppercase tracking-widest rounded-full">Phổ biến nhất</div>
            <h4 class="package-label text-xl font-bold text-blue-500 mb-4 tracking-widest uppercase">Combo Elite</h4>
            <div class="package-price text-6xl font-black mb-12">{(shopStore.currentPrice * 2 * 0.9).toLocaleString()}Đ</div>
            <button onclick={() => shopStore.openCheckout()} class="btn-primary w-full py-6 bg-blue-500 text-white rounded-3xl font-black shadow-xl hover:scale-[1.03] active:scale-95 transition-all text-sm tracking-widest uppercase">MUA NGAY</button>
         </div>
      </div>
    </div>
  </section>

<style lang="postcss">
  .offer-section {
    container-type: inline-size;
  }

  .timer-badge {
    background-color: #dc2626;
  }

  .package-card:hover {
    border-color: rgba(59, 130, 246, 0.5);
  }

  .package-card--popular {
    box-shadow: 0 25px 50px -12px rgba(59, 130, 246, 0.2);
  }

  .btn-ghost:hover {
    background-color: #3b82f6;
    color: white;
  }

  @container (min-width: 768px) {
    .offer-title {
      font-size: 6rem;
    }
    .package-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @container (max-width: 600px) {
    .offer-title {
      font-size: 3rem;
    }
    .package-card {
      padding: 2rem;
    }
  }
</style>
