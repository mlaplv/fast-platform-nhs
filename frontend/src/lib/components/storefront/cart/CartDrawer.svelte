<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { formatCurrency } from '$lib/utils/format';
  import { goto } from '$app/navigation';

  const cartStore = getCartStore();

  function handleCheckout() {
    cartStore.closeCart();
    goto('/checkout');
  }
</script>

{#if cartStore.isOpen}
  <!-- Backdrop Blur overlay -->
  <button
    class="fixed inset-0 bg-black/60 backdrop-blur-sm cursor-default"
    style="z-index: calc(var(--z-overlay, 500) + 10);"
    transition:fade={{ duration: 300 }}
    onclick={() => cartStore.closeCart()}
    aria-label="Close cart overlay"
  ></button>

  <!-- Cart Drawer Panel -->
  <div
    class="fixed top-0 right-0 w-[90vw] max-w-[420px] h-[100dvh] bg-slate-900/95 backdrop-blur-3xl border-l border-white/10 shadow-[0_0_100px_rgba(0,0,0,0.8)] flex flex-col"
    style="z-index: calc(var(--z-modal, 1000) + 10);"
    transition:fly={{ x: '100%', duration: 400, opacity: 1 }}
  >
    <!-- Header -->
    <div class="p-6 md:p-8 border-b border-white/10 flex justify-between items-center bg-black/20">
      <h2 class="text-2xl font-black text-white italic tracking-tighter uppercase flex items-center gap-3">
        Giỏ hàng
        <span class="w-2 h-2 rounded-full bg-red-600 animate-pulse shadow-[0_0_10px_#dc2626]"></span>
      </h2>
      <button
        onclick={() => cartStore.closeCart()}
        class="w-10 h-10 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/50 hover:text-white hover:bg-red-500/20 hover:border-red-500/50 transition-all active:scale-90"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>
    </div>

    <!-- Items List -->
    <div class="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 scrollbar-hide">
      {#if cartStore.items.length === 0}
        <div class="flex flex-col items-center justify-center h-full text-white/30 gap-6">
          <div class="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
            <span class="text-5xl grayscale opacity-50 drop-shadow-2xl">🛒</span>
          </div>
          <p class="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Giỏ hàng đang trống</p>
          <button onclick={() => cartStore.closeCart()} class="px-6 py-3 bg-white/5 hover:bg-white/10 text-white font-bold rounded-full uppercase tracking-widest text-[10px] transition-colors border border-white/10">
            Tiếp tục mua sắm
          </button>
        </div>
      {:else}
        {#each cartStore.items as item (item.id)}
          <div class="flex gap-5 items-center bg-white/[0.03] p-4 rounded-[1.5rem] border border-white/10 group hover:border-white/20 transition-colors">
            <!-- Product Image -->
            <div class="w-20 h-20 bg-black/50 rounded-xl overflow-hidden shrink-0 border border-white/5">
              <img src={item.product.image || item.product.images?.[0] || '/uploads/img/micsmo/sp1.png'} alt={item.product.name} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
            </div>

            <!-- Product Details -->
            <div class="flex-1 min-w-0">
              <div class="flex justify-between items-start gap-2">
                <h4 class="text-sm font-bold text-white leading-tight line-clamp-2">{item.product.name}</h4>
                <button onclick={() => cartStore.removeItem(item.id)} class="text-white/20 hover:text-red-500 transition-colors mt-0.5">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>

              {#if item.variant}
                <p class="text-[9px] text-sky-400 font-black uppercase tracking-widest mt-1.5 mb-1">{item.variant.sku}</p>
              {/if}

              <div class="flex items-end justify-between mt-3">
                <span class="text-red-500 font-black tracking-tighter text-lg">{formatCurrency(item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0)}</span>

                <!-- Qty Controls -->
                <div class="flex items-center gap-1 bg-black/60 rounded-full px-1.5 py-1 border border-white/10">
                  <button onclick={() => cartStore.updateQuantity(item.id, item.quantity - 1)} class="w-6 h-6 rounded-full bg-white/5 hover:bg-white/20 text-white/70 hover:text-white transition-colors flex items-center justify-center font-black">-</button>
                  <span class="text-[11px] font-black w-5 text-center text-white">{item.quantity}</span>
                  <button onclick={() => cartStore.updateQuantity(item.id, item.quantity + 1)} class="w-6 h-6 rounded-full bg-white/5 hover:bg-white/20 text-white/70 hover:text-white transition-colors flex items-center justify-center font-black">+</button>
                </div>
              </div>
            </div>
          </div>
        {/each}
      {/if}
    </div>

    <!-- Footer (Checkout Info) -->
    {#if cartStore.items.length > 0}
      <div class="p-6 md:p-8 border-t border-white/10 bg-black/60 backdrop-blur-md">
        <div class="flex justify-between items-end mb-6">
          <span class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Tổng thanh toán</span>
          <span class="text-4xl font-black text-white italic tracking-tighter drop-shadow-lg">{formatCurrency(cartStore.totalAmount)}</span>
        </div>
        <button
          onclick={handleCheckout}
          class="group relative w-full py-5 bg-gradient-to-r from-red-600 to-red-500 text-white font-black rounded-2xl transition-all active:scale-[0.98] shadow-[0_15px_30px_rgba(220,38,38,0.3)] uppercase tracking-widest italic text-sm overflow-hidden flex items-center justify-center gap-3"
        >
          <div class="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <span class="relative z-10">Thanh toán ngay</span>
          <svg class="w-5 h-5 relative z-10 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
        </button>
        <p class="text-[8px] text-center text-slate-500 uppercase tracking-widest font-bold mt-4 italic">Bảo mật thông tin & Miễn phí vận chuyển</p>
      </div>
    {/if}
  </div>
{/if}

<style>
  .scrollbar-hide::-webkit-scrollbar { display: none; }
  .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>