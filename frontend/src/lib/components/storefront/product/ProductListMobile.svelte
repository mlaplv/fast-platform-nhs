<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import ProductGrid from './ProductGrid.svelte';
  import { fade, fly } from 'svelte/transition';

  interface Product {
    id: string;
    name: string;
    price: number;
    image: string;
    sales?: number;
    originalPrice?: number;
    rating?: number;
    ratingCount?: number;
  }

  interface Props {
    products: Product[];
    searchQuery?: string;
  }
  let { products, searchQuery }: Props = $props();
</script>

<div class="min-h-screen bg-[#F7F8F9] pb-24">
  <!-- SEARCH SUMMARY LAYER (Elite V2.2) -->
  <div class="sticky top-0 z-30 bg-white/90 backdrop-blur-xl border-b border-gray-100 shadow-sm">
    <div class="px-4 py-3 flex items-center justify-between">
      <div class="flex flex-col">
        <span class="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400">
          {searchQuery ? `Kết quả cho: "${searchQuery}"` : 'Kết quả tìm kiếm'}
        </span>
        <h2 class="text-[15px] font-bold text-gray-900 tracking-tight">Tìm thấy {products.length} siêu phẩm</h2>
      </div>
      
      <!-- Filter Badge Placeholder -->
      <button class="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-50 border border-gray-100 active:scale-90 transition-transform">
        <svg class="w-5 h-5 text-gray-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
      </button>
    </div>
  </div>

  <!-- MAIN PRODUCT FEED -->
  <div class="px-3 pt-3">
    {#if products.length > 0}
      <ProductGrid {products} />
    {:else}
      <div class="flex flex-col items-center justify-center py-24 px-10 text-center" in:fade>
        <div class="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-6">
           <svg class="w-12 h-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Không tìm thấy kết quả</h3>
        <p class="text-sm text-gray-500 leading-relaxed">Sếp ơi, em không tìm thấy sản phẩm nào khớp với từ khóa này. Sếp thử tìm từ khóa khác xem sao?</p>
        <button 
          onclick={() => goto('/')}
          class="mt-8 px-8 py-3 bg-black text-white text-[13px] font-black uppercase tracking-widest rounded-full shadow-xl active:scale-95 transition-all"
        >
          Về trang chủ
        </button>
      </div>
    {/if}
  </div>

  <!-- VIRAL RECOMMENDATIONS (Phase 2 readiness) -->
  {#if products.length > 0}
    <div class="mt-8 px-4 py-8 border-t border-gray-100">
      <div class="flex items-center gap-3 mb-6">
         <div class="w-1 h-6 bg-luxury-copper rounded-full"></div>
         <h3 class="text-[14px] font-black uppercase tracking-widest text-gray-400">Có thể sếp sẽ thích</h3>
      </div>
      <!-- Add a horizontal scroll of recommendations here later -->
    </div>
  {/if}
</div>

<style>
  /* Elite Scroll Optimization */
  :global(body) {
    background-color: #F7F8F9;
  }
</style>