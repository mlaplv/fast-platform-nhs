<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  const cartStore = getCartStore();
  // Header Viral Immersive 2026 cho Mobile
  // Tuân thủ Elite V2.2: Hiệu ứng Gradient, Z-index tập trung
</script>

<header class="fixed top-0 w-full z-[var(--z-header)] p-5 flex justify-between items-center text-white bg-gradient-to-b from-black/80 via-black/40 to-transparent backdrop-blur-[2px]">
  <div class="flex items-center gap-3">
    <div class="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center shadow-lg shadow-red-600/40">
      <span class="text-[10px] font-black tracking-tighter">M</span>
    </div>
    <div class="font-black text-xl tracking-tighter uppercase italic">MICSMO</div>
  </div>

  <div class="flex gap-6 items-center">
    <button class="hover:scale-110 transition-transform active:scale-95">
      <span class="text-2xl drop-shadow-md">🔍</span>
    </button>
    <button onclick={() => cartStore.toggleCart()} class="relative hover:scale-110 transition-transform active:scale-95">
      <span class="text-2xl drop-shadow-md">🛒</span>
      {#if cartStore.totalItems > 0}
        <span class="absolute -top-1 -right-1 w-4 h-4 bg-red-600 text-[8px] flex items-center justify-center rounded-full font-bold border border-white animate-bounce">
          {cartStore.totalItems}
        </span>
      {/if}
    </button>
  </div>
</header>
