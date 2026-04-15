<script lang="ts">
  import { goto } from '$app/navigation';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { trimProductName } from '$lib/utils/format';
  import { fade } from 'svelte/transition';
  import { ChevronLeft, Search, Filter } from 'lucide-svelte';

  let { products = [], searchQuery = '', facets = null } = $props<{
    products: any[];
    searchQuery?: string;
    facets?: any | null;
  }>();

  let activeTab = $state('RELEVANT');
  let isFilterDrawerOpen = $state(false);

  // Filter State
  let selectedBrands = $state<string[]>([]);
  let selectedOrigins = $state<string[]>([]);
  let minPrice = $state(facets?.price_min ?? 0);
  let maxPrice = $state(facets?.price_max ?? 2000000);

  // Derived filters
  const availableBrands = $derived(facets?.brands ?? []);
  const availableOrigins = $derived(facets?.origins ?? []);

  // Combined logic: Sort + Filter
  const sortedProducts = $derived(() => {
    let result = products.filter(p => p.price >= minPrice && p.price <= maxPrice);

    if (selectedBrands.length > 0) {
      result = result.filter(p => selectedBrands.includes(p.attributes?.brand));
    }
    if (selectedOrigins.length > 0) {
      result = result.filter(p => selectedOrigins.includes(p.attributes?.origin));
    }

    if (activeTab === 'LATEST') {
        result.sort((a, b) => b.id.localeCompare(a.id));
    } else if (activeTab === 'BEST_SELLER') {
        result.sort((a, b) => (b.orderCount ?? 0) - (a.orderCount ?? 0));
    } else if (activeTab === 'TOP_RATED') {
        result.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
    }
    return result;
  });

  function toggleBrand(brand: string) {
    selectedBrands = selectedBrands.includes(brand) ? selectedBrands.filter(b => b !== brand) : [...selectedBrands, brand];
  }
</script>

<div class="min-h-screen bg-white pb-20 font-['Outfit']">
  <!-- Viral Mobile Header -->
  <header class="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-gray-100 flex flex-col">
    <div class="px-2 py-2 flex items-center gap-2">
      <button onclick={() => goto('/')} class="p-2 text-gray-900 active:scale-90 transition-transform">
        <ChevronLeft size={24} />
      </button>
      <div class="flex-1 h-10 bg-gray-100 rounded-xl flex items-center px-4 gap-2 border border-gray-100">
        <Search size={18} class="text-gray-400" />
        <span class="text-[14px] font-bold text-gray-900 truncate">{searchQuery || "Tìm kiếm sản phẩm..."}</span>
      </div>
    </div>

    <!-- Tabs + Filter Row -->
    <div class="flex items-center px-2 pb-1">
      <div class="flex-1 flex gap-0.5 overflow-x-auto no-scrollbar">
        {#each [
          {id: 'RELEVANT', label: 'Khớp nhất'},
          {id: 'TOP_RATED', label: 'Đánh giá cao'},
          {id: 'BEST_SELLER', label: 'Bán chạy'},
          {id: 'LATEST', label: 'Mới nhất'}
        ] as tab}
           <button
             onclick={() => activeTab = tab.id}
             class="px-3 py-2 text-[12px] font-bold rounded-full transition-all whitespace-nowrap
               {activeTab === tab.id ? 'bg-[#fe2c55] text-white' : 'bg-transparent text-gray-600'}"
           >
             {tab.label}
           </button>
        {/each}
      </div>
      <button
        onclick={() => isFilterDrawerOpen = true}
        class="px-0 py-2 text-gray-700 bg-transparent border-none outline-none active:scale-90 transition-transform"
      >
        <Filter size={20} />
      </button>
    </div>
  </header>

  <!-- Search Results Grid -->
  <div class="p-3">
    {#if sortedProducts().length > 0}
      <div class="grid grid-cols-2 gap-3">
        {#each sortedProducts() as p}
          <a href="/{p.slug}" class="bg-white rounded-2xl border border-gray-50 overflow-hidden shadow-sm hover:shadow-md transition-shadow active:scale-[0.98] transition-transform">
            <div class="aspect-square bg-gray-50 overflow-hidden relative">
              <img src={p.images?.[0] ?? p.metadata?.image_url} alt={p.name} class="w-full h-full object-cover transition-transform duration-500 hover:scale-105" loading="lazy" />
              {#if p.discountPrice}
                <div class="absolute top-2 left-2 bg-[#fe2c55] text-white text-[9px] font-black px-1.5 py-0.5 rounded-sm shadow-md">GIẢM</div>
              {/if}
            </div>
            <div class="p-3">
              <h3 class="text-[13px] font-bold text-gray-800 line-clamp-2 leading-tight mb-2 min-h-[34px]">{trimProductName(p.name)}</h3>
              <div class="flex items-end justify-between">
                <span class="text-[15px] font-black text-luxury-copper">đ{(p.discountPrice ?? p.price).toLocaleString('vi-VN')}</span>
              </div>
            </div>
          </a>
        {/each}
      </div>
    {:else}
      <div class="flex flex-col items-center justify-center py-20 text-center" in:fade>
        <div class="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-4">
           <Search size={32} class="text-gray-300" />
        </div>
        <p class="text-[14px] text-gray-500">Sếp ơi, không tìm thấy sản phẩm nào khớp ạ.</p>
      </div>
    {/if}
  </div>

  <!-- Filter Modal (Slide from Bottom) -->
  {#if isFilterDrawerOpen}
    <button
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[1001]"
      onclick={() => isFilterDrawerOpen = false}
      transition:fade={{ duration: 300 }}
    ></button>

    <div
      class="fixed bottom-0 left-0 right-0 max-h-[85vh] bg-white z-[1002] rounded-t-3xl shadow-2xl flex flex-col overflow-hidden"
      transition:fly={{ y: '100%', duration: 400 }}
    >
      <div class="p-6 overflow-y-auto pb-32">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-black italic tracking-tighter uppercase">Bộ Lọc</h2>
          <button onclick={() => isFilterDrawerOpen = false} class="text-gray-400">Đóng</button>
        </div>

        <!-- Brands -->
        {#if availableBrands.length > 0}
          <div class="mb-6">
            <h4 class="text-[12px] font-bold text-gray-500 mb-3">Thương hiệu</h4>
            <div class="flex flex-wrap gap-2">
              {#each availableBrands as brand}
                <button onclick={() => toggleBrand(brand)} class="px-3 py-1.5 rounded-full text-[12px] font-bold border {selectedBrands.includes(brand) ? 'bg-[#fe2c55] text-white border-[#fe2c55]' : 'bg-gray-100 text-gray-600 border-gray-100'}">
                  {brand}
                </button>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Price -->
        <div class="mb-6">
            <h4 class="text-[12px] font-bold text-gray-500 mb-3">Giá từ ({minPrice.toLocaleString()} - {maxPrice.toLocaleString()})</h4>
            <input type="range" min={facets?.price_min ?? 0} max={facets?.price_max ?? 2000000} bind:value={maxPrice} class="w-full" />
        </div>
      </div>

      <div class="fixed bottom-0 left-0 right-0 p-6 bg-white border-t border-gray-100">
        <button onclick={() => isFilterDrawerOpen = false} class="w-full py-4 bg-[#fe2c55] text-white font-bold rounded-2xl shadow-lg">
          Áp dụng ({sortedProducts().length} sản phẩm)
        </button>
      </div>
    </div>
  {/if}
</div>
