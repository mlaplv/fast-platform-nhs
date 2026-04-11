<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import SmartSearch from '../product/SmartSearch.svelte';

  const cartStore = getCartStore();
  const searchStore = getSearchStore();
  // Header Viral Immersive 2026 cho Mobile
  // Tuân thủ Elite V2.2: Hiệu ứng Gradient, Z-index tập trung
</script>

<header class="fixed top-0 w-full z-[var(--z-header)] px-4 py-3 pb-4 flex flex-col gap-3 text-white bg-[#0f0f0f] border-b border-gray-800 shadow-xl">
  <!-- Top Row: Logo & Icons -->
  <div class="flex justify-between items-center w-full">
    <div class="flex items-center gap-2">
      <div class="w-7 h-7 bg-gradient-to-br from-luxury-copper to-luxury-peach rounded-none flex items-center justify-center shadow-lg">
        <span class="text-[10px] font-black tracking-tighter text-white">M</span>
      </div>
      <div class="font-black text-lg tracking-tighter uppercase italic bg-gradient-to-r from-luxury-copper to-luxury-peach bg-clip-text text-transparent">MICSMO</div>
    </div>
    
    <div class="flex gap-4 items-center">
      <button class="relative hover:scale-110 transition-transform active:scale-95 text-gray-400">
         <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
      </button>
      <button onclick={() => cartStore.toggleCart()} class="relative hover:scale-110 transition-transform active:scale-95 text-gray-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
        {#if cartStore.totalItems > 0}
          <span class="absolute -top-1 -right-1 w-4 h-4 bg-luxury-copper text-[8px] flex items-center justify-center rounded-none font-bold border border-[#0f0f0f] animate-pulse">
            {cartStore.totalItems}
          </span>
        {/if}
      </button>
    </div>
  </div>

  <!-- Search Row: TikTok/Shopee Hybrid Style -->
  <div class="w-full relative">
    <div 
      onclick={() => searchStore.isOverlayOpen = true}
      role="presentation"
      class="w-full h-10 bg-white rounded-md flex items-center px-3 relative overflow-hidden group border-[1.5px] border-transparent transition-all cursor-text"
      style="border-image: linear-gradient(to right, #00f2ea, #ff0050) 1;"
    >
      <svg class="w-4 h-4 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      <input 
        type="text" 
        readonly
        placeholder={searchStore.searchPlaceholder}
        class="w-full bg-transparent text-[13px] text-[#00f2ea]/80 font-medium focus:outline-none pointer-events-none"
      />
      <div class="ml-auto text-pink-500 font-bold text-[13px] border-l border-gray-100 pl-3">
        Tìm kiếm
      </div>
    </div>
  </div>
</header>

{#if searchStore.isOverlayOpen}
  <SmartSearch variant="mobile-overlay" />
{/if}
