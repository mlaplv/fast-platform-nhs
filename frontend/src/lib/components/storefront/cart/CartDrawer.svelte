<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { formatCurrency } from '$lib/utils/format';
  import { goto } from '$app/navigation';

  const cartStore = getCartStore();
  const clientUi = getClientUi();

  // FOMO & Vouchers
  const vouchers = [
    { id: 'freeship', label: 'Miễn Phí Vận Chuyển', discount: 0, type: 'ship' },
    { id: 'disc30', label: 'Giảm ₫30k', discount: 30000, type: 'discount' },
  ];

  const FREESHIP_THRESHOLD = 500000;
  const freeshipProgress = $derived(Math.min(100, (cartStore.totalAmount / FREESHIP_THRESHOLD) * 100));
  const amountToFreeship = $derived(Math.max(0, FREESHIP_THRESHOLD - cartStore.totalAmount));

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
    class="fixed top-0 right-0 w-[90vw] max-w-[420px] h-[100dvh] bg-white border-l border-gray-100 shadow-2xl flex flex-col"
    style="z-index: calc(var(--z-modal, 1000) + 10);"
    transition:fly={{ x: '100%', duration: 400, opacity: 1 }}
  >
    <!-- Header -->
    <div class="p-6 md:p-8 border-b border-gray-100 flex justify-between items-center bg-white">
      <div class="flex flex-col">
        <h2 class="text-xl font-black text-gray-900 uppercase tracking-tight flex items-center gap-3">
          Giỏ hàng
          <span class="text-xs font-bold text-gray-400">({cartStore.totalItems} món)</span>
        </h2>
        {#if cartStore.items.length > 0}
          <label class="flex items-center gap-2 mt-2 cursor-pointer group">
            <input 
              type="checkbox" 
              class="w-4 h-4 rounded border-gray-300 text-[#ee4d2d] focus:ring-[#ee4d2d]"
              checked={cartStore.items.every(item => item.selected)}
              onchange={(e) => cartStore.toggleAll(e.currentTarget.checked)}
            />
            <span class="text-[10px] font-bold text-gray-500 uppercase tracking-widest group-hover:text-gray-700 transition-colors">Chọn tất cả</span>
          </label>
        {/if}
      </div>
      <button
        onclick={() => cartStore.closeCart()}
        class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:text-gray-900 hover:bg-gray-200 transition-all"
        aria-label="Đóng giỏ hàng"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>
    </div>

    <!-- Items List -->
    <div class="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 scrollbar-hide">
      {#if cartStore.items.length > 0}
        <!-- Freeship Progress (Shopee Style) -->
        <div class="mb-6 p-4 bg-orange-50 rounded-xl border border-orange-100">
           <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-black uppercase text-orange-600 tracking-widest">Ưu đãi vận chuyển</span>
              {#if amountToFreeship > 0}
                <span class="text-[10px] font-bold text-gray-500">Mua thêm {formatCurrency(amountToFreeship)} để được FREESHIP</span>
              {:else}
                <span class="text-[10px] font-black text-emerald-600">BẠN ĐÃ ĐƯỢC MIỄN PHÍ VẬN CHUYỂN!</span>
              {/if}
           </div>
           <div class="h-1.5 w-full bg-orange-200/30 rounded-full overflow-hidden">
              <div 
                class="h-full bg-orange-500 transition-all duration-700"
                style="width: {freeshipProgress}%"
              ></div>
           </div>
        </div>
      {/if}

      {#if cartStore.items.length === 0}
        <div class="flex flex-col items-center justify-center h-full text-gray-400 gap-4">
          <div class="w-20 h-20 rounded-full bg-gray-50 flex items-center justify-center">
            <span class="text-4xl">🛒</span>
          </div>
          <p class="text-xs font-bold uppercase tracking-widest text-gray-400">Giỏ hàng đang trống</p>
          <button onclick={() => cartStore.closeCart()} class="px-6 py-2.5 bg-gray-900 text-white font-bold rounded-lg uppercase tracking-widest text-[10px] transition-colors">
            Tiếp tục mua sắm
          </button>
        </div>
      {:else}
        {#each cartStore.items as item (item.id)}
          <div class="flex gap-4 items-center bg-white p-3 rounded-xl border border-gray-100 transition-all shadow-sm {item.selected ? 'border-[#ee4d2d]/30 bg-[#fff4f1]/10' : 'hover:border-gray-200'}">
            <!-- Selection Checkbox -->
            <input 
              type="checkbox" 
              class="w-4 h-4 rounded border-gray-300 text-[#ee4d2d] focus:ring-[#ee4d2d] shrink-0"
              checked={item.selected}
              onchange={() => cartStore.toggleItemSelection(item.id)}
            />

            <!-- Product Image -->
            <div class="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden shrink-0">
              <img src={item.product.image || item.product.images?.[0] || '/uploads/img/micsmo/sp1.png'} alt={item.product.name} class="w-full h-full object-cover" />
            </div>

            <!-- Product Details -->
            <div class="flex-1 min-w-0">
              <div class="flex justify-between items-start gap-2">
                <h4 class="text-xs font-bold text-gray-900 leading-snug line-clamp-2">{item.product.name}</h4>
                <button
                  onclick={() => {
                    cartStore.removeItem(item.id);
                    clientUi.showToast('Đã xóa sản phẩm khỏi giỏ', 'info');
                  }}
                  class="text-gray-400 hover:text-red-500 transition-colors shrink-0"
                  aria-label="Xóa sản phẩm"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>

              {#if item.variant}
                <p class="text-[9px] text-gray-500 font-bold uppercase mt-1">{item.variant.sku}</p>
              {/if}

              <div class="flex items-center justify-between mt-2">
                <div class="flex flex-col">
                  <span class="text-[10px] text-gray-400 line-through">{formatCurrency(item.variant?.price ?? item.product.price)}</span>
                  <span class="text-red-600 font-black text-sm">{formatCurrency(item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0)}</span>
                </div>

                <!-- Qty Controls -->
                <div class="flex items-center gap-2 border border-gray-200 rounded-lg p-0.5">
                  <button onclick={() => cartStore.updateQuantity(item.id, item.quantity - 1)} class="w-6 h-6 rounded flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors font-black">-</button>
                  <span class="text-xs font-black w-6 text-center text-gray-900">{item.quantity}</span>
                  <button onclick={() => cartStore.updateQuantity(item.id, item.quantity + 1)} class="w-6 h-6 rounded flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors font-black">+</button>
                </div>
              </div>
            </div>
          </div>
        {/each}

        <!-- Voucher Block (FOMO) -->
        <div class="mt-6 pt-4 border-t border-gray-100">
           <h4 class="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-3">Chọn mã giảm giá</h4>
           <div class="space-y-2">
             {#each vouchers as v}
                <button
                  onclick={() => cartStore.selectedVoucherId = cartStore.selectedVoucherId === v.id ? null : v.id}
                  class="flex items-center justify-between w-full p-2.5 rounded-lg border-2 transition-all {cartStore.selectedVoucherId === v.id ? 'border-[#ee4d2d] bg-[#fff4f1]' : 'border-gray-100 hover:border-gray-200'}"
                >
                   <div class="flex items-center gap-2">
                     <span class="w-4 h-4 rounded-full border-2 {cartStore.selectedVoucherId === v.id ? 'border-[#ee4d2d] bg-[#ee4d2d]' : 'border-gray-300'}"></span>
                     <span class="text-xs font-bold text-gray-700">{v.label}</span>
                   </div>
                   {#if v.discount > 0}
                     <span class="text-[10px] font-black text-[#ee4d2d] bg-[#ffdbd6] px-1.5 py-0.5 rounded">-{formatCurrency(v.discount)}</span>
                   {/if}
                </button>
             {/each}
           </div>
        </div>

        <!-- Trust Indicators -->
        <div class="grid grid-cols-2 gap-2 mt-6 pt-4 border-t border-gray-100">
           <div class="flex items-center gap-2 text-[9px] text-gray-500 font-bold uppercase">
              <svg class="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              100% Chính Hãng
           </div>
           <div class="flex items-center gap-2 text-[9px] text-gray-500 font-bold uppercase">
              <svg class="w-4 h-4 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
              Giao hàng 24h
           </div>
        </div>
      {/if}
    </div>

    <!-- Footer (Checkout Info) -->
    {#if cartStore.items.length > 0}
      <div class="p-6 border-t border-gray-100 bg-white">
        <div class="flex justify-between items-end mb-6">
          <div class="flex flex-col">
            <span class="text-[11px] font-bold uppercase tracking-widest text-gray-500">Tổng thanh toán</span>
            <span class="text-[9px] text-[#ee4d2d] font-bold mt-1 uppercase">Đã chọn {cartStore.selectedItemsCount} món</span>
          </div>
          <span class="text-3xl font-black text-gray-900 tracking-tighter">{formatCurrency(cartStore.totalAmount)}</span>
        </div>
        <button
          onclick={handleCheckout}
          disabled={cartStore.selectedItemsCount === 0}
          class="group relative w-full py-5 bg-[#ee4d2d] text-white font-black rounded-lg transition-all active:scale-[0.98] shadow-md hover:shadow-lg uppercase tracking-widest text-sm flex items-center justify-center gap-3 disabled:bg-gray-300 disabled:shadow-none disabled:cursor-not-allowed"
        >
          <span class="relative z-10">Thanh toán ngay ({cartStore.selectedItemsCount})</span>
          <svg class="w-5 h-5 relative z-10 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
        </button>
        <p class="text-[10px] text-center text-gray-400 uppercase tracking-widest font-bold mt-4">An toàn & Bảo mật</p>
      </div>
    {/if}
  </div>
{/if}

<style>
  .scrollbar-hide::-webkit-scrollbar { display: none; }
  .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>