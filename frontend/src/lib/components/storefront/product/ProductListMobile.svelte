<script lang="ts">
  import { goto } from '$app/navigation';
  import { trimProductName } from '$lib/utils/format';
  import ProductGrid from './ProductGrid.svelte';
  import { fade, fly } from 'svelte/transition';
  import { untrack } from 'svelte';
  import { ChevronLeft, Search, Filter } from 'lucide-svelte';
  import type { Product, ProductFacets } from '$lib/types';
  import BottomSheet from '$lib/components/mobile/BottomSheet.svelte';

  interface Props {
    products: Product[];
    categoryName?: string;
    searchQuery?: string;
    facets?: ProductFacets | null;
  }

  let { products = [], categoryName = "Danh mục", searchQuery, facets = null }: Props = $props();

  let activeTab = $state('CATEGORY'); // CATEGORY | BEST_SELLER | TOP_RATED | LATEST
  
  // --- FILTER STATE ---
  let isFilterDrawerOpen = $state(false);
  
  // Real active filters used for deriving results
  let selectedBrands = $state<string[]>([]);
  let selectedOrigins = $state<string[]>([]);
  let selectedServices = $state<string[]>([]);
  
  const MIN_VAL = $derived(facets?.price_min ?? 0);
  const MAX_VAL = $derived(facets?.price_max ?? 2000000);
  
  let minPrice = $state<number | null>(null);
  let maxPrice = $state<number | null>(null);

  // Constants
  const servicesList = ['Cam kết chính hãng', 'Tặng kèm mẫu thử', 'Gói quà cao cấp', 'Miễn phí vận chuyển', 'Tư vấn chuyên gia', 'Thanh toán linh hoạt'];

  // Helper to get attribute safely from multiple possible paths
  function getAttr(p: Product, key: string): string | null {
    const val = p.metadata?.[key] ?? p.attributes?.[key] ?? p.attributes?.[key === 'brand' ? 'Thương hiệu' : 'Xuất xứ'];
    return typeof val === 'string' ? val.trim() : null;
  }

  // Derived filter options
  const availableBrands = $derived(() => {
    if (facets?.brands && facets.brands.length > 0) return facets.brands;
    const set = new Set<string>();
    products.forEach(p => {
      const b = getAttr(p, 'brand');
      if (b) set.add(b);
    });
    return Array.from(set).sort();
  });

  const availableOrigins = $derived(() => {
    if (facets?.origins && facets.origins.length > 0) return facets.origins;
    const set = new Set<string>();
    products.forEach(p => {
      const o = getAttr(p, 'origin');
      if (o) set.add(o);
    });
    return Array.from(set).sort();
  });

  const filteredProducts = $derived(() => {
    let result = [...products];

    // Apply Brand Filter
    if (selectedBrands.length > 0) {
      result = result.filter(p => {
        const b = getAttr(p, 'brand');
        return b && selectedBrands.includes(b);
      });
    }

    // Apply Origin Filter
    if (selectedOrigins.length > 0) {
      result = result.filter(p => {
        const o = getAttr(p, 'origin');
        return o && selectedOrigins.includes(o);
      });
    }

    // Apply Price Filter
    if (minPrice !== null || maxPrice !== null) {
      result = result.filter(p => {
        const price = p.discountPrice ?? p.price;
        if (minPrice !== null && price < minPrice) return false;
        if (maxPrice !== null && price > maxPrice) return false;
        return true;
      });
    }

    // Sort Logic
    if (activeTab === 'BEST_SELLER') {
      result.sort((a, b) => (b.orderCount ?? 0) - (a.orderCount ?? 0));
    } else if (activeTab === 'TOP_RATED') {
      result.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
    } else if (activeTab === 'LATEST') {
      result.sort((a, b) => b.id.localeCompare(a.id));
    }
    return result;
  });

  function toggleBrand(brand: string) {
    selectedBrands = selectedBrands.includes(brand) ? selectedBrands.filter(b => b !== brand) : [...selectedBrands, brand];
  }

  function toggleOrigin(origin: string) {
    selectedOrigins = selectedOrigins.includes(origin) ? selectedOrigins.filter(o => o !== origin) : [...selectedOrigins, origin];
  }

  function toggleService(service: string) {
    selectedServices = selectedServices.includes(service) ? selectedServices.filter(s => s !== service) : [...selectedServices, service];
  }

  function setPriceRange(min: number | null, max: number | null) {
    if (minPrice === min && maxPrice === max) {
      minPrice = null;
      maxPrice = null;
    } else {
      minPrice = min;
      maxPrice = max;
    }
  }

  const hasActiveFilters = $derived.by(() => {
    return selectedBrands.length > 0 || selectedOrigins.length > 0 || selectedServices.length > 0 || minPrice !== null || maxPrice !== null;
  });

  function removeBrand(brand: string) {
    selectedBrands = selectedBrands.filter(b => b !== brand);
  }

  function removeOrigin(origin: string) {
    selectedOrigins = selectedOrigins.filter(o => o !== origin);
  }

  function removeService(service: string) {
    selectedServices = selectedServices.filter(s => s !== service);
  }

  function clearFilters() {
    selectedBrands = [];
    selectedOrigins = [];
    selectedServices = [];
    minPrice = null;
    maxPrice = null;
  }
</script>

<div class="min-h-screen bg-white pb-24 font-sans">
  <!-- SEARCH-STYLE VIRAL HEADER (Elite V2.2) -->
  <header class="sticky top-0 z-40 bg-white/95 backdrop-blur-xl border-b border-gray-100 flex flex-col">
    <!-- Row 1: Back & Search -->
    <div class="px-2 py-1 flex items-center gap-2 h-14">
       <button 
         onclick={() => goto('/')}
         class="p-2 text-gray-900 active:scale-90 transition-transform flex-shrink-0"
       >
         <ChevronLeft size={24} />
       </button>

       <div 
         onclick={() => goto('/')}
         role="presentation"
         class="flex-1 min-w-0 h-[42px] bg-gray-100 rounded-xl flex items-center px-4 gap-2 border border-gray-100 active:border-gray-200 transition-all cursor-pointer"
       >
          <Search size={18} class="text-gray-400 flex-shrink-0" />
          <span class="text-[14px] text-gray-400 font-bold truncate">
            {searchQuery || "Tìm kiếm sản phẩm..."}
          </span>
       </div>
    </div>

    <!-- Row 2: SEARCH-STYLE PILLS (Marketplace Standard) -->
    <div class="flex items-center px-3 pb-2 gap-2 overflow-hidden">
       <div class="flex-1 flex gap-1 overflow-x-auto no-scrollbar">
          {#each [
            { id: 'CATEGORY', label: categoryName },
            { id: 'TOP_RATED', label: 'Đánh giá cao' },
            { id: 'BEST_SELLER', label: 'Bán chạy' },
            { id: 'LATEST', label: 'Mới nhất' }
          ] as tab}
            <button 
              onclick={() => activeTab = tab.id}
              class="px-4 py-2 text-[12px] font-bold rounded-full transition-all whitespace-nowrap
                {activeTab === tab.id ? 'bg-[var(--color-brand-primary)] text-white' : 'bg-transparent text-gray-600 font-medium'}"
            >
               {tab.label}
            </button>
          {/each}
       </div>

       <!-- Filter Trigger -->
       <button 
         onclick={() => isFilterDrawerOpen = true}
         class="p-2 text-gray-700 active:scale-95 transition-all relative border-l border-gray-100 ml-1"
       >
         <Filter size={20} />
         {#if selectedBrands.length > 0 || selectedOrigins.length > 0 || selectedServices.length > 0 || minPrice !== null || maxPrice !== null}
           <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border border-white animate-pulse"></span>
         {/if}
       </button>
    </div>

    <!-- Row 3: ACTIVE FILTER CHIPS -->
    {#if hasActiveFilters}
      <div class="flex items-center gap-2 px-3 py-2 bg-gray-50/50 overflow-x-auto no-scrollbar border-t border-gray-50/50" transition:fade>
         {#each selectedBrands as brand}
           <button 
             onclick={() => removeBrand(brand)}
             class="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-[11px] font-bold text-gray-700 whitespace-nowrap shadow-sm active:scale-95 transition-all"
           >
             {brand}
             <svg class="w-3.5 h-3.5 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
           </button>
         {/each}

         {#each selectedOrigins as origin}
           <button 
             onclick={() => removeOrigin(origin)}
             class="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-[11px] font-bold text-gray-700 whitespace-nowrap shadow-sm active:scale-95 transition-all"
           >
             {origin}
             <svg class="w-3.5 h-3.5 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
           </button>
         {/each}

         {#each selectedServices as service}
           <button 
             onclick={() => removeService(service)}
             class="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-[11px] font-bold text-gray-700 whitespace-nowrap shadow-sm active:scale-95 transition-all"
           >
             {service}
             <svg class="w-3.5 h-3.5 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
           </button>
         {/each}

         {#if minPrice !== null || maxPrice !== null}
           <button 
             onclick={() => { minPrice = null; maxPrice = null; }}
             class="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-[11px] font-bold text-gray-700 whitespace-nowrap shadow-sm active:scale-95 transition-all"
           >
             {minPrice?.toLocaleString() ?? 0}đ - {maxPrice?.toLocaleString() ?? '...'}đ
             <svg class="w-3.5 h-3.5 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
           </button>
         {/if}

         <button 
           onclick={clearFilters}
           class="text-[11px] font-bold text-[var(--color-brand-primary)] px-2 whitespace-nowrap active:scale-95 transition-all"
         >
           Xoá tất cả
         </button>
      </div>
    {/if}
  </header>

  <!-- MAIN PRODUCT FEED -->
  <div class="p-4">
    {#if filteredProducts().length > 0}
      <ProductGrid products={filteredProducts()} />
    {:else}
      <div class="flex flex-col items-center justify-center py-24 px-10 text-center" in:fade>
        <div class="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mb-6">
           <Search size={40} class="text-gray-200" />
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

<!-- FILTER DRAWER (Mobile-First BottomSheet) -->
<BottomSheet title="Bộ Lọc Tìm Kiếm" bind:active={isFilterDrawerOpen}>
  <div class="flex flex-col gap-8 pb-32">
     <!-- Dịch vụ & Khuyến mãi -->
     <section>
        <h4 class="text-[14px] font-bold text-gray-800 mb-4 px-1">Dịch vụ & Khuyến mãi</h4>
        <div class="flex flex-wrap gap-2 px-1">
          {#each servicesList as service}
            <button
              onclick={() => toggleService(service)}
              class="px-4 py-2.5 rounded-xl text-[13px] font-bold border transition-all 
                {selectedServices.includes(service) 
                  ? 'border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/5 text-[var(--color-brand-primary)]' 
                  : 'bg-gray-50 text-gray-600 border-transparent hover:bg-gray-100'}"
            >
              {service}
            </button>
          {/each}
        </div>
     </section>

     <!-- Price Range Presets -->
     <section>
        <h4 class="text-[14px] font-bold text-gray-800 mb-4 px-1">Khoảng giá</h4>
        <div class="grid grid-cols-2 gap-2 px-1 mb-4">
           {#each [
             { label: 'Dưới 100Kđ', min: null, max: 100000 },
             { label: '100Kđ - 500Kđ', min: 100000, max: 500000 },
             { label: '500Kđ - 1000Kđ', min: 500000, max: 1000000 },
             { label: 'Trên 1 Triệu', min: 1000000, max: null },
           ] as range}
             <button
                onclick={() => setPriceRange(range.min, range.max)}
                class="px-2 py-3 rounded-xl text-[13px] font-bold border transition-all 
                  {minPrice === range.min && maxPrice === range.max 
                    ? 'border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/5 text-[var(--color-brand-primary)]' 
                    : 'bg-gray-50 text-gray-600 border-transparent'}"
             >
                {range.label}
             </button>
           {/each}
        </div>
        
        <div class="flex items-center gap-3 px-1">
          <div class="flex-1 bg-gray-50 rounded-xl flex items-center px-4 py-3 border border-transparent focus-within:border-[var(--color-brand-primary)] transition-all">
            <input 
              type="number" 
              placeholder="Từ" 
              bind:value={minPrice} 
              class="w-full text-[13px] font-bold bg-transparent outline-none text-gray-800" 
            />
            <span class="text-gray-400 text-[13px] ml-1">₫</span>
          </div>
          <div class="w-3 h-0.5 bg-gray-200"></div>
          <div class="flex-1 bg-gray-50 rounded-xl flex items-center px-4 py-3 border border-transparent focus-within:border-[var(--color-brand-primary)] transition-all">
            <input 
              type="number" 
              placeholder="Đến" 
              bind:value={maxPrice} 
              class="w-full text-[13px] font-bold bg-transparent outline-none text-gray-800" 
            />
            <span class="text-gray-400 text-[13px] ml-1">₫</span>
          </div>
        </div>
     </section>

     <!-- Brands -->
     {#if availableBrands().length > 0}
      <section>
        <h4 class="text-[14px] font-bold text-gray-800 mb-4 px-1">Thương hiệu</h4>
        <div class="flex flex-wrap gap-2 px-1">
          {#each availableBrands() as brand}
            <button
              onclick={() => toggleBrand(brand)}
              class="px-5 py-2.5 rounded-xl text-[13px] font-bold border transition-all 
                {selectedBrands.includes(brand) 
                  ? 'border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/5 text-[var(--color-brand-primary)]' 
                  : 'bg-gray-50 text-gray-600 border-transparent hover:bg-gray-100'}"
            >
              {brand}
            </button>
          {/each}
        </div>
      </section>
     {/if}

     <!-- Origins -->
     {#if availableOrigins().length > 0}
      <section>
        <h4 class="text-[14px] font-bold text-gray-800 mb-4 px-1">Xuất xứ</h4>
        <div class="flex flex-wrap gap-2 px-1">
          {#each availableOrigins() as origin}
            <button
              onclick={() => toggleOrigin(origin)}
              class="px-5 py-2.5 rounded-xl text-[13px] font-bold border transition-all 
                {selectedOrigins.includes(origin) 
                  ? 'border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/5 text-[var(--color-brand-primary)]' 
                  : 'bg-gray-50 text-gray-600 border-transparent hover:bg-gray-100'}"
            >
              {origin}
            </button>
          {/each}
        </div>
      </section>
     {/if}
  </div>

  <!-- Fix Footer Actions -->
  <div class="mt-auto pt-4 pb-0 flex items-center gap-4 bg-white sticky bottom-0 z-10 border-t border-gray-100">
    <button 
      onclick={clearFilters} 
      class="flex-1 py-4 bg-gray-50 text-gray-600 text-[14px] font-black uppercase tracking-widest rounded-2xl active:scale-95 transition-all"
    >
      Xóa
    </button>
    <button 
      onclick={() => isFilterDrawerOpen = false} 
      class="flex-2 w-[65%] py-4 bg-black text-white text-[14px] font-black uppercase tracking-widest rounded-2xl shadow-xl active:scale-95 transition-all"
    >
      Áp dụng
    </button>
  </div>
</BottomSheet>

<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>