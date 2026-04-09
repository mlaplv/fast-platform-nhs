<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import ProductGrid from './ProductGrid.svelte';
  import CategoryBanner from './CategoryBanner.svelte';

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
    categoryName: string;
  }

  let { products = [], categoryName = "Danh mục" }: Props = $props();

  // --- STATE & LOGIC ---
  type SortType = 'popular' | 'sales' | 'latest' | 'price-asc' | 'price-desc';
  let activeSort = $state<SortType>('popular');

  // Price Slider State
  const MIN_VAL = 0;
  const MAX_VAL = 2000000;
  let minPrice = $state(89000);
  let maxPrice = $state(1430000);
  let sliderEl = $state<HTMLElement | null>(null);

  // Filter State
  let selectedBrands = $state<string[]>([]);
  let selectedOrigins = $state<string[]>([]);
  let pageSize = $state(12);
  let isLoading = $state(false);

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

  function clearAllFilters() {
    selectedBrands = [];
    selectedOrigins = [];
    minPrice = 89000;
    maxPrice = 1430000;
  }

  function removeBrand(brand: string) {
    selectedBrands = selectedBrands.filter(b => b !== brand);
  }

  function removeOrigin(origin: string) {
    selectedOrigins = selectedOrigins.filter(o => o !== origin);
  }

  function loadMore() {
    if (isLoading || displayProducts().length >= filteredProducts().length) return;
    isLoading = true;
    setTimeout(() => {
      pageSize += 12;
      isLoading = false;
    }, 400);
  }

  function setupInfiniteScroll(node: HTMLElement) {
    const observer = new IntersectionObserver((entries) => {
      const first = entries[0];
      if (first.isIntersecting) {
        loadMore();
      }
    }, { threshold: 0.1 });

    observer.observe(node);
    return {
      destroy() {
        observer.unobserve(node);
      }
    };
  }

  let hasActiveFilters = $derived(() => {
    return selectedBrands.length > 0 || selectedOrigins.length > 0 || minPrice !== 89000 || maxPrice !== 1430000;
  });

  const getPercent = (value: number) => ((value - MIN_VAL) / (MAX_VAL - MIN_VAL)) * 100;

  function handleSliderUpdate(e: PointerEvent, type: 'min' | 'max') {
    if (!sliderEl) return;
    const rect = sliderEl.getBoundingClientRect();
    const percent = Math.min(Math.max(0, (e.clientX - rect.left) / rect.width), 1);
    const value = Math.round(MIN_VAL + (MAX_VAL - MIN_VAL) * percent);

    if (type === 'min') {
      minPrice = Math.min(value, maxPrice - 50000);
    } else {
      maxPrice = Math.max(value, minPrice + 50000);
    }
  }

  function setupDraggable(node: HTMLElement, type: 'min' | 'max') {
    const handlePointerMove = (e: PointerEvent) => handleSliderUpdate(e, type);
    const handlePointerUp = () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
    };

    node.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      window.addEventListener('pointermove', handlePointerMove);
      window.addEventListener('pointerup', handlePointerUp);
    });
  }

  const brands = ['MartiDerm', 'SK-II', 'Sakura', 'Excel Therapy', 'Genie', 'ZO Skin Health'];
  const origins = ['Tây Ban Nha', 'Nhật Bản', 'Hàn Quốc', 'Mỹ', 'Đức'];
  const skinTypes = ['Da Dầu', 'Da Khô', 'Da Lão Hoá', 'Da Nhạy Cảm', 'Da Thường'];

  const enhancedProducts = $derived(() => {
    return products.map((p, i) => ({
      ...p,
      originalPrice: p.originalPrice || p.price * 1.55,
      sales: p.sales || 300 + (i * 15),
      rating: 5,
      ratingCount: 1 + (i % 10)
    }));
  });

  let filteredProducts = $derived(() => {
    let result = enhancedProducts().filter(p => {
      const matchPrice = p.price >= minPrice && p.price <= maxPrice;
      const matchBrand = selectedBrands.length === 0 || selectedBrands.includes('MartiDerm'); // Mock logic for brands
      const matchOrigin = selectedOrigins.length === 0 || selectedOrigins.includes('Nhật Bản'); // Mock logic for origins
      return matchPrice; // Temporarily just price for demo, can be expanded
    });

    if (activeSort === 'popular') result.sort((a, b) => (b.ratingCount || 0) - (a.ratingCount || 0));
    if (activeSort === 'sales') result.sort((a, b) => (b.sales || 0) - (a.sales || 0));
    if (activeSort === 'latest') result.sort((a, b) => b.id.localeCompare(a.id));
    if (activeSort === 'price-asc') result.sort((a, b) => a.price - b.price);
    if (activeSort === 'price-desc') result.sort((a, b) => b.price - a.price);
    
    return result;
  });

  let displayProducts = $derived(() => {
    return filteredProducts().slice(0, pageSize);
  });
</script>

<div class="bg-[#F5F5F5] min-h-screen pb-20">
  <!-- BREADCRUMB & TITLE BAR -->
  <div class="bg-white border-b border-gray-100">
    <div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-6">
      <!-- Breadcrumbs -->
      <nav class="flex items-center gap-2 text-[12px] text-gray-400 mb-4 font-medium uppercase tracking-wider">
        <a href="/" class="hover:text-[#ee4d2d] transition-colors">Trang chủ</a>
        <span>/</span>
        <span class="text-gray-900">{categoryName}</span>
      </nav>

      <!-- Category Title & Rating -->
      <div class="flex items-center gap-6">
        <h1 class="text-3xl font-black text-gray-900 tracking-tight">{categoryName}</h1>
        <div class="flex items-center gap-2 pt-1">
          <div class="flex text-[#ffac33] text-sm">
            {#each Array(5) as _}
              <svg class="w-4 h-4 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
            {/each}
          </div>
          <span class="text-[13px] text-blue-500 font-medium whitespace-nowrap">339 đánh giá</span>
        </div>
      </div>
    </div>
  </div>

  <!-- VIRAL BANNER ZONE -->
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 mt-6">
    <CategoryBanner products={enhancedProducts()} />
  </div>

  <!-- MAIN CONTENT: Sidebar + Grid -->
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 mt-6 flex gap-6">
    <!-- LEFT SIDEBAR (Sharp Elite / Glassmorphism) -->
    <aside class="w-[240px] shrink-0 space-y-6">
      <!-- Sidebar Header -->
      <div class="bg-black text-white p-5 rounded-none shadow-xl transform hover:-translate-y-1 transition-all duration-500 overflow-hidden relative group">
        <div class="absolute inset-0 bg-gradient-to-tr from-[#ee4d2d]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
        <h2 class="text-[14px] font-black uppercase tracking-[0.2em] relative z-10 flex items-center gap-3">
           <div class="w-1.5 h-1.5 bg-[#ee4d2d] rounded-full animate-pulse"></div>
           Bộ lọc Elite
        </h2>
      </div>

      <!-- Filters Group -->
      <div class="bg-white/70 backdrop-blur-xl border border-white p-6 space-y-8 rounded-none shadow-[0_10px_40px_rgba(0,0,0,0.03)] ring-1 ring-black/[0.01]">
        
        <!-- Price Range Filter (Liquid Design) -->
        <div class="space-y-6">
          <div class="flex items-center justify-between">
            <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Khoảng giá</h4>
            <svg class="w-3.5 h-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
          </div>
          
          <div class="flex flex-col gap-3">
             <div class="relative group/input">
                <input 
                  type="text" 
                  value={Math.round(minPrice).toLocaleString()} 
                  oninput={(e) => {
                    const val = parseInt((e.target as HTMLInputElement).value.replace(/\D/g, ''));
                    if (!isNaN(val)) minPrice = val;
                  }}
                  class="w-full h-12 bg-gray-50/50 border-none rounded-none px-4 pr-10 text-[14px] font-black text-gray-900 outline-none ring-2 ring-transparent focus:ring-[#ee4d2d]/10 transition-all" />
                <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs font-black">đ</span>
             </div>
             <div class="relative group/input">
                <input 
                  type="text" 
                  value={Math.round(maxPrice).toLocaleString()} 
                  oninput={(e) => {
                    const val = parseInt((e.target as HTMLInputElement).value.replace(/\D/g, ''));
                    if (!isNaN(val)) maxPrice = val;
                  }}
                  class="w-full h-12 bg-gray-50/50 border-none rounded-none px-4 pr-10 text-[14px] font-black text-gray-900 outline-none ring-2 ring-transparent focus:ring-[#ee4d2d]/10 transition-all" />
                <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs font-black">đ</span>
             </div>
          </div>

          <!-- Orange Slider Core (Neon Liquid) -->
          <div class="relative pt-2 px-1">
            <div bind:this={sliderEl} class="h-2 w-full bg-gray-100/50 rounded-full relative overflow-hidden">
              <!-- Active Range Fill (Gradient) -->
              <div 
                class="absolute h-full bg-gradient-to-r from-[#ee4d2d] to-[#ff7e5f] rounded-full shadow-[0_0_15px_rgba(238,77,45,0.4)]" 
                style="left: {getPercent(minPrice)}%; right: {100 - getPercent(maxPrice)}%"></div>
              
              <!-- Thumbs (Floating) -->
              <div 
                use:setupDraggable={'min'}
                class="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white border-[4px] border-[#ee4d2d] rounded-full shadow-xl cursor-grab active:cursor-grabbing z-20 hover:scale-110 transition-transform"
                style="left: calc({getPercent(minPrice)}% - 12px)"></div>
              
              <div 
                use:setupDraggable={'max'}
                class="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white border-[4px] border-[#ee4d2d] rounded-full shadow-xl cursor-grab active:cursor-grabbing z-20 hover:scale-110 transition-transform"
                style="left: calc({getPercent(maxPrice)}% - 12px)"></div>
            </div>
          </div>
        </div>

        <!-- Brands Checkbox (Minimalist Round) -->
        <div class="space-y-6 pt-4">
          <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Thương Hiệu</h4>
          <div class="flex flex-col gap-4">
            {#each brands as brand}
              <label class="flex items-center justify-between group cursor-pointer">
                <span class="text-[13px] font-bold {selectedBrands.includes(brand) ? 'text-black' : 'text-gray-400'} group-hover:text-black transition-all">
                   {brand}
                </span>
                <div 
                  onclick={() => toggleBrand(brand)}
                  class="w-5 h-5 rounded-full border-2 transition-all flex items-center justify-center {selectedBrands.includes(brand) ? 'border-[#ee4d2d] bg-[#ee4d2d]' : 'border-gray-100 bg-gray-50'} shadow-inner">
                   {#if selectedBrands.includes(brand)}
                      <div class="w-1.5 h-1.5 bg-white rounded-full"></div>
                   {/if}
                </div>
              </label>
            {/each}
          </div>
        </div>

        <!-- Origin Checkbox -->
        <div class="space-y-6 pt-4">
          <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Xuất Xứ</h4>
          <div class="flex flex-col gap-4">
            {#each origins as country}
              <label class="flex items-center justify-between group cursor-pointer">
                <span class="text-[13px] font-bold {selectedOrigins.includes(country) ? 'text-black' : 'text-gray-400'} group-hover:text-black transition-all">
                   {country}
                </span>
                <div 
                  onclick={() => toggleOrigin(country)}
                  class="w-5 h-5 rounded-full border-2 transition-all flex items-center justify-center {selectedOrigins.includes(country) ? 'border-[#ee4d2d] bg-[#ee4d2d]' : 'border-gray-100 bg-gray-50'}">
                   {#if selectedOrigins.includes(country)}
                      <div class="w-1.5 h-1.5 bg-white rounded-full"></div>
                   {/if}
                </div>
              </label>
            {/each}
          </div>
        </div>
      </div>
    </aside>

    <!-- RIGHT GRID AREA -->
    <main class="flex-1">
      <!-- UNIFIED SORT & FILTER BAR (Viral 2026 / Single Block) -->
      <div class="bg-white border border-gray-100 p-2 mb-8 flex flex-col gap-2 shadow-sm">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <button 
                onclick={() => activeSort = 'popular'}
                class="px-6 py-3 text-[12px] font-black tracking-tighter transition-all relative {activeSort === 'popular' ? 'text-[#ee4d2d]' : 'text-gray-400 hover:text-black'}">
                PHỔ BIẾN
                {#if activeSort === 'popular'}
                  <div in:scale={{duration: 400}} class="absolute bottom-1 left-1/2 -translate-x-1/2 w-8 h-[2px] bg-[#ee4d2d] rounded-full"></div>
                {/if}
              </button>
              
              <button 
                onclick={() => activeSort = 'sales'}
                class="px-6 py-3 text-[12px] font-black tracking-tighter transition-all relative {activeSort === 'sales' ? 'text-[#ee4d2d]' : 'text-gray-400 hover:text-black'}">
                BÁN CHẠY
                {#if activeSort === 'sales'}
                  <div in:scale={{duration: 400}} class="absolute bottom-1 left-1/2 -translate-x-1/2 w-8 h-[2px] bg-[#ee4d2d] rounded-full"></div>
                {/if}
              </button>

              <button 
                onclick={() => activeSort = 'latest'}
                class="px-6 py-3 text-[12px] font-black tracking-tighter transition-all relative {activeSort === 'latest' ? 'text-[#ee4d2d]' : 'text-gray-400 hover:text-black'}">
                MỚI NHẤT
                {#if activeSort === 'latest'}
                  <div in:scale={{duration: 400}} class="absolute bottom-1 left-1/2 -translate-x-1/2 w-8 h-[2px] bg-[#ee4d2d] rounded-full"></div>
                {/if}
              </button>
            </div>

            <!-- Price Sort Dropdown -->
            <div class="relative group/sort">
               <button class="bg-gray-50 border border-transparent px-5 py-2.5 text-[11px] font-black text-gray-800 flex items-center justify-between w-[200px] hover:border-gray-200 transition-all uppercase tracking-tighter">
                  <span>{activeSort === 'price-asc' ? 'GIÁ: THẤP ĐẾN CAO' : activeSort === 'price-desc' ? 'GIÁ: CAO ĐẾN THẤP' : 'SẮP XẾP THEO GIÁ'}</span>
                  <svg class="w-3.5 h-3.5 opacity-40 group-hover/sort:rotate-180 transition-transform duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7" /></svg>
               </button>
               <div class="absolute top-full right-0 w-full bg-white border border-gray-100 shadow-2xl opacity-0 group-hover/sort:opacity-100 invisible group-hover/sort:visible transition-all duration-300 z-[200] py-1">
                  <button 
                      onclick={() => activeSort = 'price-asc'}
                      class="w-full text-left px-5 py-3.5 text-[11px] font-black text-gray-500 hover:text-[#ee4d2d] hover:bg-gray-50 transition-all flex items-center justify-between group/item">
                      GIÁ: THẤP ĐẾN CAO
                      <div class="w-1 h-1 bg-[#ee4d2d] scale-0 group-hover/item:scale-100 transition-transform"></div>
                  </button>
                  <button 
                      onclick={() => activeSort = 'price-desc'}
                      class="w-full text-left px-5 py-3.5 text-[11px] font-black text-gray-500 hover:text-[#ee4d2d] hover:bg-gray-50 transition-all flex items-center justify-between group/item">
                      GIÁ: CAO ĐẾN THẤP
                      <div class="w-1 h-1 bg-[#ee4d2d] scale-0 group-hover/item:scale-100 transition-transform"></div>
                  </button>
               </div>
            </div>
          </div>

          <!-- INTEGRATED ACTIVE FILTERS (No Text Labels) -->
          {#if hasActiveFilters()}
            <div class="px-4 py-2 border-t border-gray-50 flex flex-wrap items-center gap-2 animate-in fade-in slide-in-from-top-2">
               {#each selectedBrands as brand}
                 <button 
                    onclick={() => removeBrand(brand)}
                    class="bg-gray-100 text-gray-600 px-3 py-1.5 text-[10px] font-black flex items-center gap-2 hover:bg-[#ee4d2d] hover:text-white transition-all transform active:scale-95">
                    {brand.toUpperCase()}
                    <svg class="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
                 </button>
               {/each}

               {#each selectedOrigins as country}
                 <button 
                    onclick={() => removeOrigin(country)}
                    class="bg-gray-100 text-gray-600 px-3 py-1.5 text-[10px] font-black flex items-center gap-2 hover:bg-[#ee4d2d] hover:text-white transition-all transform active:scale-95">
                    {country.toUpperCase()}
                    <svg class="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
                 </button>
               {/each}

               {#if minPrice !== 89000 || maxPrice !== 1430000}
                 <button 
                    onclick={() => { minPrice = 89000; maxPrice = 1430000; }}
                    class="bg-gray-100 text-gray-600 px-3 py-1.5 text-[10px] font-black flex items-center gap-2 hover:bg-[#ee4d2d] hover:text-white transition-all transform active:scale-95">
                    {Math.round(minPrice).toLocaleString()}Đ - {Math.round(maxPrice).toLocaleString()}Đ
                    <svg class="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
                 </button>
               {/if}

               <button 
                  onclick={clearAllFilters}
                  class="ml-2 text-[#ee4d2d] hover:underline text-[10px] font-black uppercase tracking-tighter">
                  Xóa tất cả
               </button>
            </div>
          {/if}
      </div>

      <div class="mt-8">
        <ProductGrid products={displayProducts()} />
      </div>

      <!-- AUTOMATIC PAGINATION (Infinite Scroll) -->
      {#if displayProducts().length < filteredProducts().length}
        <div class="mt-12 flex flex-col items-center gap-4 py-10" use:setupInfiniteScroll>
          <div class="text-[12px] text-gray-400 font-black uppercase tracking-widest">
            Đã tải <span class="text-black">{displayProducts().length}</span> / {filteredProducts().length} siêu phẩm
          </div>
          <div class="w-[200px] h-[2px] bg-gray-100 overflow-hidden relative">
             <div class="h-full bg-[#ee4d2d] transition-all duration-700" style="width: {(displayProducts().length / filteredProducts().length) * 100}%"></div>
             {#if isLoading}
                <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent animate-shimmer"></div>
             {/if}
          </div>
          
          {#if isLoading}
            <div class="flex items-center gap-3 text-[11px] font-black text-[#ee4d2d] animate-pulse uppercase tracking-tighter">
               <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
               Đang tải thêm...
            </div>
          {/if}
        </div>
      {:else}
        <div class="mt-16 text-center py-10 border-t border-gray-50">
           <span class="text-[11px] font-black text-gray-300 uppercase tracking-[0.5em]">Đã hiển thị toàn bộ sưu tập</span>
        </div>
      {/if}
    </main>
  </div>
</div>

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>