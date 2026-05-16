<script lang="ts">

  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { formatCurrency, trimProductName } from '$lib/utils/format';
  import { fade } from 'svelte/transition';
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import Search from "@lucide/svelte/icons/search";
  import Filter from "@lucide/svelte/icons/filter";
  import type { Product, ProductFacets } from '$lib/types';

  import BottomSheet from '$lib/components/mobile/BottomSheet.svelte';
  import SmartSearch from '$lib/components/storefront/product/SmartSearch.svelte';

  const searchStore = getSearchStore();

  let { products = [], searchQuery = '', facets = null, loading = false } = $props<{
    products: Product[];
    searchQuery?: string;
    facets?: ProductFacets | null;
    loading?: boolean;
  }>();

  let activeTab = $state('RELEVANT');
  let isFilterDrawerOpen = $state(false);

  // Filter State
  let selectedBrands = $state<string[]>([]);
  let selectedOrigins = $state<string[]>([]);
  let selectedServices = $state<string[]>([]);
  let minPrice = $state<number | null>(null);
  let maxPrice = $state<number | null>(null);

  // Constants
  const servicesList = ['Cam kết chính hãng', 'Tặng kèm mẫu thử', 'Gói quà cao cấp', 'Miễn phí vận chuyển', 'Tư vấn chuyên gia', 'Thanh toán linh hoạt'];

  // Derived filters
  const availableBrands = $derived(facets?.brands ?? []);
  const availableOrigins = $derived(facets?.origins?.length ? facets.origins : ['Hà Nội', 'Hồ Chí Minh', 'Bắc Ninh']);

  // Combined logic: Sort + Filter
  const sortedProducts = $derived(() => {
    let result = [...products];

    if (minPrice !== null || maxPrice !== null) {
        result = result.filter(p => {
             const price = Number(p.discountPrice) || Number(p.price);
             if (minPrice !== null && price < minPrice) return false;
             if (maxPrice !== null && price > maxPrice) return false;
             return true;
        });
    }

    if (selectedBrands.length > 0) {
      result = result.filter(p => {
        const brand = p.attributes?.brand;
        return typeof brand === 'string' && selectedBrands.includes(brand);
      });
    }
    if (selectedOrigins.length > 0) {
      result = result.filter(p => {
        const origin = p.attributes?.origin;
        return typeof origin === 'string' && selectedOrigins.includes(origin);
      });
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
  function toggleService(service: string) {
    selectedServices = selectedServices.includes(service) ? selectedServices.filter(s => s !== service) : [...selectedServices, service];
  }
  function toggleOrigin(origin: string) {
    selectedOrigins = selectedOrigins.includes(origin) ? selectedOrigins.filter(o => o !== origin) : [...selectedOrigins, origin];
  }
  function setPriceRange(min: number | null, max: number | null) {
      // Toggle off if same range clicked
      if (minPrice === min && maxPrice === max) {
          minPrice = null;
          maxPrice = null;
      } else {
          minPrice = min;
          maxPrice = max;
      }
  }
  function clearFilters() {
      selectedBrands = [];
      selectedServices = [];
      selectedOrigins = [];
      minPrice = null;
      maxPrice = null;
  }
</script>

<div class="min-h-screen bg-white pb-20 font-sans">
  <!-- Viral Mobile Header -->
  <header class="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-gray-100 flex flex-col">
    <div class="px-2 py-1 flex items-center gap-2 h-12 relative" style:z-index="40">
      <button onclick={() => window.location.href = '/'} class="p-2 text-gray-900 active:scale-90 transition-transform relative z-50">
        <ChevronLeft size={24} />
      </button>
      <button 
        onclick={() => searchStore.isOverlayOpen = true}
        class="flex-1 h-10 bg-gray-100 rounded-xl flex items-center px-4 gap-2 border border-gray-100 active:scale-[0.98] transition-all cursor-pointer overflow-hidden group"
      >
        <Search size={18} class="text-gray-400 group-active:text-luxury-copper transition-colors" />
        <span class="text-[14px] font-bold text-gray-900 truncate">{searchQuery || "Tìm kiếm sản phẩm..."}</span>
      </button>
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
               {activeTab === tab.id ? 'bg-[var(--color-brand-primary)] text-white' : 'bg-transparent text-gray-600'}"
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
    {#if loading}
      <div class="grid grid-cols-2 gap-3">
        {#each Array(4) as _}
           <div class="bg-white rounded-2xl border border-gray-50 overflow-hidden shadow-sm animate-pulse">
             <div class="aspect-square bg-gray-100"></div>
             <div class="p-3">
               <div class="h-4 bg-gray-100 rounded mb-2"></div>
               <div class="h-4 bg-gray-100 rounded w-1/2"></div>
             </div>
           </div>
        {/each}
      </div>
    {:else if sortedProducts().length > 0}
      <div class="grid grid-cols-2 gap-3">
        {#each sortedProducts() as p}
          <a href="/{p.slug}" class="bg-white rounded-2xl border border-gray-50 overflow-hidden shadow-sm hover:shadow-md transition-shadow active:scale-[0.98] transition-transform">
            <div class="aspect-square bg-gray-50 overflow-hidden relative">
              <img src={p.images?.[0] ?? p.metadata?.image_url} alt={p.name} class="w-full h-full object-cover transition-transform duration-500 hover:scale-105" loading="lazy" decoding="async" />
              {#if p.discountPrice}
                <div class="absolute top-2 left-2 bg-[var(--color-brand-primary)] text-white text-[9px] font-black px-1.5 py-0.5 rounded-sm shadow-md">GIẢM</div>
              {/if}
            </div>
            <div class="p-3">
              <h3 class="text-[13px] font-bold text-gray-800 line-clamp-2 leading-tight mb-2 min-h-[34px]">{trimProductName(p.name)}</h3>
              <div class="flex items-end justify-between">
                <span class="text-[15px] font-black text-[#ee4d2d]">{formatCurrency(Number(p.discountPrice) || Number(p.price))}</span>
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
        <p class="text-[14px] text-gray-500">Không tìm thấy sản phẩm nào.</p>
      </div>
    {/if}
  </div>

  <!-- Filter Modal (Slide from Bottom) -->
  <BottomSheet title="Bộ Lọc" bind:active={isFilterDrawerOpen}>
    <div class="overflow-y-auto pb-4 flex flex-col gap-6">

      <!-- Dịch vụ và khuyến mãi -->
      <div>
        <h4 class="text-[14px] font-bold text-gray-800 mb-3 px-1">Dịch vụ và khuyến mãi</h4>
        <div class="flex flex-wrap gap-2 px-1">
          {#each servicesList as service}
            <button
              onclick={() => toggleService(service)}
              class="px-3 py-2 rounded-md text-[13px] border relative transition-colors {selectedServices.includes(service) ? 'bg-red-50 text-[var(--color-brand-primary)] border-[var(--color-brand-primary)]' : 'bg-gray-50 text-gray-700 border-transparent hover:bg-gray-100'}"
            >
              {service}
            </button>
          {/each}
        </div>
      </div>

      <!-- Khoảng giá -->
      <div>
        <h4 class="text-[14px] font-bold text-gray-800 mb-3 px-1">Khoảng giá</h4>
        <div class="grid grid-cols-2 gap-2 px-1 mb-4">
           {#each [
             { label: 'Dưới 100K', min: null, max: 100000 },
             { label: '100K - 200K', min: 100000, max: 200000 },
             { label: '200K - 350K', min: 200000, max: 350000 },
             { label: 'Trên 350K', min: 350000, max: null },
           ] as range}
             <button
                onclick={() => setPriceRange(range.min, range.max)}
                class="px-2 py-2 rounded-md text-[13px] border relative transition-colors {minPrice === range.min && maxPrice === range.max ? 'bg-red-50 text-[var(--color-brand-primary)] border-[var(--color-brand-primary)]' : 'bg-gray-50 text-gray-700 border-transparent hover:bg-gray-100'}"
             >
                {range.label}
             </button>
           {/each}
        </div>
        <div class="flex items-center gap-3 px-1">
          <div class="flex-1 bg-gray-50 rounded-md flex items-center px-3 py-2 border border-transparent focus-within:border-[var(--color-brand-primary)]">
            <span class="text-gray-400 text-[13px] mr-1">đ</span>
            <input type="number" placeholder="Tối thiểu" bind:value={minPrice} class="w-full text-[13px] bg-transparent outline-none text-gray-800" />
          </div>
          <div class="w-3 h-[1px] bg-gray-400"></div>
          <div class="flex-1 bg-gray-50 rounded-md flex items-center px-3 py-2 border border-transparent focus-within:border-[var(--color-brand-primary)]">
            <span class="text-gray-400 text-[13px] mr-1">đ</span>
            <input type="number" placeholder="Tối đa" bind:value={maxPrice} class="w-full text-[13px] bg-transparent outline-none text-gray-800" />
          </div>
        </div>
      </div>

      <!-- Vận chuyển từ -->
      <div>
        <div class="flex items-center justify-between px-1 mb-3">
           <h4 class="text-[14px] font-bold text-gray-800">Vận chuyển từ</h4>
           <div class="flex flex-row items-center cursor-pointer text-gray-500 hover:text-gray-700">
             <span class="text-[12px] font-medium mr-1">Hiển thị thêm</span>
             <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mt-[1px]"><polyline points="6 9 12 15 18 9"></polyline></svg>
           </div>
        </div>
        <div class="flex flex-wrap gap-2 px-1">
          {#each availableOrigins as origin}
            <button
              onclick={() => toggleOrigin(origin)}
              class="px-4 py-2 rounded-md text-[13px] border relative transition-colors {selectedOrigins.includes(origin) ? 'bg-red-50 text-[var(--color-brand-primary)] border-[var(--color-brand-primary)]' : 'bg-gray-50 text-gray-700 border-transparent hover:bg-gray-100'}"
            >
              {origin}
            </button>
          {/each}
        </div>
      </div>

      <!-- Brands/Thương hiệu -->
      {#if availableBrands.length > 0}
        <div class="">
          <div class="flex items-center justify-between px-1 mb-3">
             <h4 class="text-[14px] font-bold text-gray-800">Thương hiệu</h4>
          </div>
          <div class="flex flex-wrap gap-2 px-1">
            {#each availableBrands as brand}
              <button
                onclick={() => toggleBrand(brand)}
                 class="px-4 py-2 rounded-md text-[13px] border relative transition-colors {selectedBrands.includes(brand) ? 'bg-red-50 text-[var(--color-brand-primary)] border-[var(--color-brand-primary)]' : 'bg-gray-50 text-gray-700 border-transparent hover:bg-gray-100'}"
              >
                {brand}
                {#if brand === 'Miccosmo'}
                  <span class="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                {/if}
              </button>
            {/each}
          </div>
        </div>
      {/if}

    </div>

    <!-- Bottom Actions sticky block -->
    <div class="mt-auto pt-2 pb-0 flex items-center gap-3 bg-white sticky bottom-0 z-10 before:absolute border-t border-gray-100 top-[-1px] left-0 right-0">
      <button onclick={clearFilters} class="w-[30%] py-2.5 bg-white border border-gray-200 text-gray-700 text-[14px] font-bold rounded-lg hover:bg-gray-50 transition-colors">
        Xóa
      </button>
      <button onclick={() => isFilterDrawerOpen = false} class="flex-1 py-2.5 bg-[var(--color-brand-primary)] text-white text-[14px] font-bold rounded-lg shadow-[0_4px_12px_rgba(var(--color-brand-primary),0.25)] active:scale-95 transition-all">
        Hiển thị kết quả
      </button>
    </div>
  </BottomSheet>

  <!-- Smart Search Overlay -->
  <SmartSearch variant="mobile-overlay" />
</div>
