<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { formatCurrency } from '$lib/utils/format';
  import { fly, fade } from 'svelte/transition';
  import { ShoppingCart } from 'lucide-svelte';
  import { goto } from '$app/navigation';

  const cartStore = getCartStore();

  // Elite V2.2: Show only last 5 added items for peak FOMO efficiency
  const recentItems = $derived(cartStore.items.slice(-5).reverse());
</script>

<div
  class="absolute right-0 top-[100%] w-[400px] bg-white shadow-[0_1px_31px_0_rgba(0,0,0,0.09)] ring-1 ring-black/5 origin-top-right"
  style="z-index: var(--z-popup)"
  in:fly={{ y: 10, duration: 250, opacity: 0 }}
  out:fade={{ duration: 150 }}
>
  <!-- Triangle Arrow -->
  <div 
    class="absolute -top-[7px] right-6 w-3 h-3 bg-white rotate-45 border-t border-l border-black/5"
    style="z-index: var(--z-popup-indicator)"
  ></div>

  <div class="relative bg-white z-10 rounded-sm overflow-hidden">
    {#if cartStore.items.length === 0}
      <div class="flex flex-col items-center justify-center py-12 px-4 text-center">
        <div class="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
           <ShoppingCart size={32} class="text-gray-300" />
        </div>
        <p class="text-[14px] text-gray-500 font-medium">Chưa có sản phẩm</p>
      </div>
    {:else}
      <!-- Header -->
      <div class="px-3 py-3 border-b border-gray-50 flex items-center justify-between">
        <span class="text-[14px] text-gray-400 font-medium">Sản phẩm mới thêm</span>
      </div>

      <!-- Product List -->
      <div class="max-h-[350px] overflow-y-auto">
        {#each recentItems as item (item.id)}
          <a
            href="/{item.product.slug}"
            class="flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors group/item border-b border-gray-50 last:border-0"
          >
            <div class="w-10 h-10 shrink-0 border border-gray-100 rounded-sm overflow-hidden bg-white">
              <img
                src={item.product.image || item.product.images?.[0] || '/uploads/img/osmo/sp1.png'}
                alt={item.product.name}
                class="w-full h-full object-cover"
              />
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-[14px] text-gray-800 font-medium truncate group-hover/item:text-[#ee4d2d] transition-colors">
                {item.product.name}
              </h4>
              {#if item.variant}
                <p class="text-[11px] text-gray-400 mt-0.5 truncate uppercase font-bold tracking-tighter">
                  {item.variant.sku}
                </p>
              {/if}
            </div>
            <div class="shrink-0 text-right">
              <span class="text-[14px] font-medium text-[#ee4d2d]">
                {formatCurrency(item.variant?.discountPrice ?? item.variant?.price ?? item.product.discountPrice ?? item.product.price ?? 0)}
              </span>
            </div>
          </a>
        {/each}
      </div>

      <!-- Footer -->
      <div class="px-3 py-3 bg-gray-50/30 flex items-center justify-between">
        <span class="text-[12px] text-gray-400 font-medium">
          {cartStore.totalItems} Thêm Hàng Vào Giỏ
        </span>
        <a
          href="/checkout"
          class="px-5 py-2.5 bg-[#ee4d2d] hover:bg-[#d0011b] text-white text-[14px] font-bold rounded-sm shadow-sm active:scale-[0.98] transition-all uppercase tracking-tight inline-block text-center"
        >
          Xem Giỏ Hàng
        </a>
      </div>
    {/if}
  </div>
</div>

<style>
  /* Custom Scrollbar for Shopee-style cleanliness */
  div::-webkit-scrollbar {
    width: 4px;
  }
  div::-webkit-scrollbar-track {
    background: transparent;
  }
  div::-webkit-scrollbar-thumb {
    background: #e5e7eb;
    border-radius: 10px;
  }
</style>
