<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import ProductGrid from './ProductGrid.svelte';
  import { fade, fly } from 'svelte/transition';
  import { untrack } from 'svelte';
  import type { Product, ProductFacets } from '$lib/types';

  interface Props {
    products: Product[];
    searchQuery?: string;
    facets?: ProductFacets | null;
  }

  let { products = [], searchQuery, facets = null }: Props = $props();

  let activeTab = $state('FOR_YOU');
  
  // --- FILTER STATE ---
  let isFilterDrawerOpen = $state(false);
  
  // Real active filters used for deriving results
  let selectedBrands = $state<string[]>([]);
  let selectedOrigins = $state<string[]>([]);
  
  const MIN_VAL = $derived(facets?.price_min ?? 0);
  const MAX_VAL = $derived(facets?.price_max ?? 2000000);
  
  let minPrice = $state(0);
  let maxPrice = $state(2000000);

  // Initialize prices when facets arrive
  $effect(() => {
    if (facets) {
      untrack(() => {
        minPrice = facets.price_min;
        maxPrice = facets.price_max;
      });
    }
  });

  // Derived filter options (fallback if facets missing)
  const availableBrands = $derived(() => {
    if (facets?.brands && facets.brands.length > 0) return facets.brands;
    const set = new Set<string>();
    products.forEach(p => {
      const b = p.attributes?.brand ?? p.attributes?.["Thương hiệu"];
      if (typeof b === 'string' && b.trim()) set.add(b.trim());
    });
    return Array.from(set).sort();
  });

  const availableOrigins = $derived(() => {
    if (facets?.origins && facets.origins.length > 0) return facets.origins;
    const set = new Set<string>();
    products.forEach(p => {
      const o = p.attributes?.origin ?? p.attributes?.["Xuất xứ"];
      if (typeof o === 'string' && o.trim()) set.add(o.trim());
    });
    return Array.from(set).sort();
  });

  const filteredProducts = $derived(() => {
    let result = [...products];

    // Apply Filters
    if (selectedBrands.length > 0) {
      result = result.filter(p => {
        const b = p.attributes?.brand ?? p.attributes?.["Thương hiệu"];
        return typeof b === 'string' && selectedBrands.includes(b.trim());
      });
    }

    if (selectedOrigins.length > 0) {
      result = result.filter(p => {
        const o = p.attributes?.origin ?? p.attributes?.["Xuất xứ"];
        return typeof o === 'string' && selectedOrigins.includes(o.trim());
      });
    }

    result = result.filter(p => {
      const price = p.discountPrice ?? p.price;
      return price >= minPrice && price <= maxPrice;
    });

    // Sort Logic
    if (activeTab === 'BEST_SELLER') {
      result.sort((a, b) => (b.orderCount ?? 0) - (a.orderCount ?? 0));
    } else if (activeTab === 'TOP_RATED') {
      result.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
    }
    return result;
  });

  function toggleBrand(brand: string) {
    if (selectedBrands.includes(brand)) {
      selectedBrands = selectedBrands.filter(b => b !== brand);
    } else {
      selectedBrands = [...selectedBrands, brand];
    }
  }

  function toggleOrigin(origin: string) {
    if (selectedOrigins.includes(origin)) {
      selectedOrigins = selectedOrigins.filter(o => o !== origin);
    } else {
      selectedOrigins = [...selectedOrigins, origin];
    }
  }

  function clearFilters() {
    selectedBrands = [];
    selectedOrigins = [];
    minPrice = MIN_VAL;
    maxPrice = MAX_VAL;
  }

  // --- SLIDER LOGIC (Optimized for Touch) ---
  let sliderEl = $state<HTMLElement | null>(null);
  const getPercent = (value: number) => ((value - MIN_VAL) / (MAX_VAL - MIN_VAL)) * 100;

  function handleTouchMove(e: TouchEvent, type: 'min' | 'max') {
    if (!sliderEl) return;
    const rect = sliderEl.getBoundingClientRect();
    const touch = e.touches[0];
    const percent = Math.min(Math.max(0, (touch.clientX - rect.left) / rect.width), 1);
    const value = Math.round(MIN_VAL + percent * (MAX_VAL - MIN_VAL));
    
    if (type === 'min') {
      minPrice = Math.min(value, maxPrice - 1000);
    } else {
      maxPrice = Math.max(value, minPrice + 1000);
    }
  }

  // --- DRAWER SCROLL LOCK ---
  $effect(() => {
    if (isFilterDrawerOpen) {
      document.body.classList.add('filter-open');
    } else {
      document.body.classList.remove('filter-open');
    }
    return () => document.body.classList.remove('filter-open');
  });
</script>

<div class="min-h-screen bg-[#F7F8F9] pb-24">
  <!-- SIMPLIFIED VIRAL HEADER (Marketplace Standard) -->
  <div class="sticky top-0 z-40 bg-white/95 backdrop-blur-xl border-b border-gray-100 shadow-sm flex flex-col">
    <!-- Row 1: Back & Search -->
    <div class="px-2 h-[48px] flex items-center gap-2">
       <button 
         onclick={() => goto('/')}
         class="p-1 text-gray-900 active:scale-90 transition-transform flex-shrink-0"
       >
         <svg class="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
       </button>

       <div 
         onclick={() => goto('/')}
         role="presentation"
         class="flex-1 min-w-0 h-9 bg-gray-100/80 rounded-lg flex items-center px-3 gap-2 border border-transparent active:border-gray-200 transition-all cursor-pointer"
       >
          <svg class="w-[18px] h-[18px] text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
          <span class="text-[13px] text-gray-400 font-bold truncate">
            {searchQuery || "Tìm kiếm sản phẩm..."}
          </span>
       </div>

       <!-- Filter Trigger -->
       <button 
         onclick={() => isFilterDrawerOpen = true}
         class="p-2 text-gray-700 active:scale-95 transition-all relative"
       >
         <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
         {#if selectedBrands.length > 0 || selectedOrigins.length > 0 || minPrice !== MIN_VAL || maxPrice !== MAX_VAL}
           <span class="absolute top-1 right-1 w-2.5 h-2.5 bg-[#fe2c55] rounded-full border-2 border-white animate-pulse"></span>
         {/if}
       </button>
    </div>

    <!-- Row 2: PREMIUM VIRAL TABS (Elite V3.0) -->
    <div class="flex items-center border-t border-gray-50 bg-white shadow-sm overflow-hidden">
       <button 
         onclick={() => activeTab = 'FOR_YOU'}
         class="flex-1 py-3.5 flex flex-col items-center justify-center gap-1 transition-all relative
           {activeTab === 'FOR_YOU' ? 'text-[#fe2c55]' : 'text-gray-400 font-medium'}"
       >
          <span class="text-[12px] font-black tracking-tight uppercase">Dành cho bạn</span>
          {#if activeTab === 'FOR_YOU'}
            <div class="absolute bottom-0 inset-x-6 h-[2.5px] bg-[#fe2c55] rounded-t-full"></div>
          {/if}
       </button>

       <button 
         onclick={() => activeTab = 'BEST_SELLER'}
         class="flex-1 py-3.5 flex flex-col items-center justify-center gap-1 transition-all relative
           {activeTab === 'BEST_SELLER' ? 'text-[#fe2c55]' : 'text-gray-400 font-medium'}"
       >
          <span class="text-[12px] font-black tracking-tight uppercase">Bán chạy</span>
          {#if activeTab === 'BEST_SELLER'}
            <div class="absolute bottom-0 inset-x-6 h-[2.5px] bg-[#fe2c55] rounded-t-full"></div>
          {/if}
       </button>

       <button 
         onclick={() => activeTab = 'TOP_RATED'}
         class="flex-1 py-3.5 flex flex-col items-center justify-center gap-1 transition-all relative
           {activeTab === 'TOP_RATED' ? 'text-[#fe2c55]' : 'text-gray-400 font-medium'}"
       >
          <span class="text-[12px] font-black tracking-tight uppercase">Đánh giá</span>
          {#if activeTab === 'TOP_RATED'}
            <div class="absolute bottom-0 inset-x-6 h-[2.5px] bg-[#fe2c55] rounded-t-full"></div>
          {/if}
       </button>
    </div>
  </div>

  <!-- MAIN PRODUCT FEED -->
  <div class="px-2 pt-3">
    {#if filteredProducts().length > 0}
      <ProductGrid products={filteredProducts()} {activeTab} />
    {:else}
      <div class="flex flex-col items-center justify-center py-24 px-10 text-center" in:fade>
        <div class="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-6">
           <svg class="w-12 h-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Không tìm thấy kết quả</h3>
        <p class="text-sm text-gray-500 leading-relaxed">Sếp ơi, em không tìm thấy sản phẩm nào khớp với bộ lọc này.</p>
        <button 
          onclick={clearFilters}
          class="mt-8 px-8 py-3 bg-black text-white text-[13px] font-black uppercase tracking-widest rounded-full shadow-xl active:scale-95 transition-all"
        >
          Xoá bộ lọc
        </button>
      </div>
    {/if}
  </div>
</div>

<!-- FILTER DRAWER (Premium Glassmorphism) -->
{#if isFilterDrawerOpen}
  <!-- Backdrop -->
  <button 
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[1001]"
    onclick={() => isFilterDrawerOpen = false}
    transition:fade={{ duration: 300 }}
  ></button>

  <!-- Drawer Panel -->
  <div 
    class="fixed inset-y-0 right-0 w-[85%] bg-white z-[1002] shadow-2xl flex flex-col overflow-hidden"
    transition:fly={{ x: '100%', duration: 400 }}
  >
    <!-- Header -->
    <div class="px-6 py-5 border-b border-gray-100 flex items-center justify-between bg-white sticky top-0 z-10">
      <h2 class="text-lg font-black italic tracking-tighter uppercase">Bộ Lọc Tìm Kiếm</h2>
      <button 
        onclick={() => isFilterDrawerOpen = false}
        class="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center text-gray-400 active:scale-90 transition-all"
      >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6 space-y-10 pb-32">
       <!-- Price Range -->
       <section class="space-y-6">
         <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Khoảng Giá (VNĐ)</h4>
         <div class="flex items-center gap-4">
            <div class="flex-1 bg-gray-50 rounded-xl p-3 border border-gray-100">
              <span class="text-[9px] font-black text-gray-400 uppercase block mb-1">Từ</span>
              <span class="text-[14px] font-black">{minPrice.toLocaleString()}Đ</span>
            </div>
            <div class="w-4 h-[1px] bg-gray-300"></div>
            <div class="flex-1 bg-gray-50 rounded-xl p-3 border border-gray-100">
              <span class="text-[9px] font-black text-gray-400 uppercase block mb-1">Đến</span>
              <span class="text-[14px] font-black">{maxPrice.toLocaleString()}Đ</span>
            </div>
         </div>

         <!-- Double Slider -->
         <div class="relative h-20 pt-10 px-2">
            <div bind:this={sliderEl} class="relative h-1.5 w-full bg-gray-100 rounded-full">
               <div 
                 class="absolute h-full bg-[#fe2c55] rounded-full" 
                 style="left: {getPercent(minPrice)}%; right: {100 - getPercent(maxPrice)}%"
               ></div>
               
               <!-- Thumb Min -->
               <div 
                 class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-7 h-7 bg-white rounded-full border-2 border-[#fe2c55] shadow-lg touch-none flex items-center justify-center active:scale-125 transition-transform"
                 style="left: {getPercent(minPrice)}%"
                 ontouchmove={(e) => handleTouchMove(e, 'min')}
               >
                 <div class="w-1.5 h-1.5 bg-[#fe2c55] rounded-full"></div>
               </div>

               <!-- Thumb Max -->
               <div 
                 class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-7 h-7 bg-white rounded-full border-2 border-[#fe2c55] shadow-lg touch-none flex items-center justify-center active:scale-125 transition-transform"
                 style="left: {getPercent(maxPrice)}%"
                 ontouchmove={(e) => handleTouchMove(e, 'max')}
               >
                 <div class="w-1.5 h-1.5 bg-[#fe2c55] rounded-full"></div>
               </div>
            </div>
         </div>
       </section>

       <!-- Brands -->
       {#if availableBrands().length > 0}
       <section class="space-y-6">
         <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Thương Hiệu</h4>
         <div class="grid grid-cols-2 gap-2">
            {#each availableBrands() as brand}
              <button 
                onclick={() => toggleBrand(brand)}
                class="px-4 py-3 rounded-xl border-2 text-[12px] font-bold text-center transition-all
                  {selectedBrands.includes(brand) ? 'border-[#fe2c55] bg-[#fe2c55]/5 text-[#fe2c55]' : 'border-gray-50 bg-gray-50 text-gray-500'}"
              >
                {brand}
              </button>
            {/each}
         </div>
       </section>
       {/if}

       <!-- Origins -->
       {#if availableOrigins().length > 0}
       <section class="space-y-6">
         <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Xuất Xứ</h4>
         <div class="grid grid-cols-2 gap-2">
            {#each availableOrigins() as origin}
              <button 
                onclick={() => toggleOrigin(origin)}
                class="px-4 py-3 rounded-xl border-2 text-[12px] font-bold text-center transition-all
                  {selectedOrigins.includes(origin) ? 'border-[#fe2c55] bg-[#fe2c55]/5 text-[#fe2c55]' : 'border-gray-50 bg-gray-50 text-gray-500'}"
              >
                {origin}
              </button>
            {/each}
         </div>
       </section>
       {/if}
    </div>

    <!-- Footer -->
    <div class="p-6 border-t border-gray-100 bg-white grid grid-cols-2 gap-4">
       <button 
         onclick={clearFilters}
         class="py-4 bg-gray-100 text-gray-600 font-black text-[12px] uppercase tracking-widest rounded-2xl active:scale-95 transition-all"
       >
         Thiết lập lại
       </button>
       <button 
         onclick={() => isFilterDrawerOpen = false}
         class="py-4 bg-black text-white font-black text-[12px] uppercase tracking-widest rounded-2xl shadow-xl active:scale-95 transition-all"
       >
         Áp dụng
       </button>
    </div>
  </div>
{/if}

<style>
  /* Elite Scroll Optimization */
  :global(body) {
    background-color: #F7F8F9;
  }
  
  /* Disable background scroll when drawer is open */
  :global(body.filter-open) {
    overflow: hidden;
    overscroll-behavior: none;
    touch-action: none;
  }
</style>