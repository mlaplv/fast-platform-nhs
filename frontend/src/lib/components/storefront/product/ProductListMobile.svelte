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

  let { products, searchQuery }: Props = $props();

  let activeTab = $state('FOR_YOU');
</script>

<div class="min-h-screen bg-[#F7F8F9] pb-24">
  <!-- SIMPLIFIED VIRAL HEADER (Marketplace Standard) -->
  <div class="sticky top-0 z-40 bg-white/95 backdrop-blur-xl border-b border-gray-100 shadow-sm flex flex-col">
    <!-- Row 1: Back & Search -->
    <div class="px-2 py-2.5 flex items-center gap-2">
       <!-- Back Button -->
       <button 
         onclick={() => goto('/')}
         class="p-1 text-gray-900 active:scale-90 transition-transform flex-shrink-0"
       >
         <svg class="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
       </button>

       <!-- Unified Search Bar -->
       <div 
         onclick={() => goto('/')}
         role="presentation"
         class="flex-1 min-w-0 h-[38px] bg-gray-100/80 rounded-lg flex items-center px-3 gap-2 border border-transparent active:border-gray-200 transition-all cursor-pointer"
       >
          <svg class="w-[18px] h-[18px] text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
          <span class="text-[13px] text-gray-400 font-bold truncate">
            {searchQuery || "Tìm kiếm siêu phẩm..."}
          </span>
       </div>
    </div>

    <!-- Row 2: PREMIUM VIRAL TABS (Elite V3.0) -->
    <div class="flex items-center border-t border-gray-50 bg-white shadow-sm overflow-hidden">
       <button 
         onclick={() => activeTab = 'FOR_YOU'}
         class="flex-1 py-4 flex flex-col items-center justify-center gap-1.5 transition-all relative
           {activeTab === 'FOR_YOU' ? 'text-[#fe2c55]' : 'text-gray-400 font-medium'}"
       >
          <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M7.5 5.6L10 7L8.6 4.5L10 2L7.5 3.4L5 2L6.4 4.5L5 7L7.5 5.6zM18.5 15.6L21 17L19.6 14.5L21 12L18.5 13.4L16 12L17.4 14.5L16 17L18.5 15.6zM20 2L17.5 3.4L15 2L16.4 4.5L15 7L17.5 5.6L20 7L18.6 4.5L20 2z"/>
          </svg>
          <span class="text-[12px] font-black tracking-tight">Dành cho bạn</span>
          {#if activeTab === 'FOR_YOU'}
            <div class="absolute bottom-0 inset-x-4 h-[3px] bg-[#fe2c55] rounded-t-full"></div>
          {/if}
       </button>

       <button 
         onclick={() => activeTab = 'BEST_SELLER'}
         class="flex-1 py-4 flex flex-col items-center justify-center gap-1.5 transition-all relative
           {activeTab === 'BEST_SELLER' ? 'text-[#fe2c55]' : 'text-gray-400 font-medium'}"
       >
          <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M17.5 11c-.5-1.5-1.5-3-3-4.5C13 5 12 3 12 1s-.5 2.5-3 5c-1.5 1.5-2.5 3-2.5 5.5s1.5 5.5 5.5 6 5.5-3.5 5.5-6zm-5.5 7.5c-2.5 0-4-1.5-4-3.5 0-1 .5-2 1.5-3 0 0 0 2 1.5 3s3.5-.5 3.5-2.5c0-.5-.5-1.5-1.5-2.5 1.5 1 2.5 2.5 2.5 4s-1.5 4.5-3.5 4.5z"/>
          </svg>
          <span class="text-[12px] font-black tracking-tight">Bán chạy</span>
          {#if activeTab === 'BEST_SELLER'}
            <div class="absolute bottom-0 inset-x-4 h-[3px] bg-[#fe2c55] rounded-t-full"></div>
          {/if}
       </button>

       <button 
         onclick={() => activeTab = 'TOP_RATED'}
         class="flex-1 py-4 flex flex-col items-center justify-center gap-1.5 transition-all relative
           {activeTab === 'TOP_RATED' ? 'text-[#fe2c55]' : 'text-gray-400 font-medium'}"
       >
          <svg class="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M17 10.43V2H7v8.43c0 .35.18.68.49.86l4.01 2.35-4.01 2.35c-.31.18-.49.51-.49.86V22h10v-5.15c0-.35-.18-.68-.49-.86l-4.01-2.35 4.01-2.35c.31-.18.49-.51.49-.86z"/>
          </svg>
          <span class="text-[12px] font-black tracking-tight">Đánh giá</span>
          {#if activeTab === 'TOP_RATED'}
            <div class="absolute bottom-0 inset-x-4 h-[3px] bg-[#fe2c55] rounded-t-full"></div>
          {/if}
       </button>
    </div>
  </div>

  <!-- MAIN PRODUCT FEED -->
  <div class="px-2 pt-3">
    {#if products.length > 0}
      <ProductGrid {products} {activeTab} />
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
</div>

<style>
  /* Elite Scroll Optimization */
  :global(body) {
    background-color: #F7F8F9;
  }
</style>