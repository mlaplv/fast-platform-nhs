<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import ProductGrid from './ProductGrid.svelte';
  import CategoryBanner from './CategoryBanner.svelte';
  import type { Product, ProductFacets } from '$lib/types';

  interface Props {
    products: Product[];
    categoryName: string;
    categorySlug: string;
    serverTotal: number;
    facets?: ProductFacets | null;
  }

  let { 
    products = [], 
    categoryName = "Danh mục",
    categorySlug,
    serverTotal,
    facets = null,
  }: Props = $props();

  // --- STATE & LOGIC ---
  // allProducts là "Single Source of Truth" có thể mở rộng
  let allProducts = $state<Product[]>([...products]);
  let currentOffset = $state(49); // Lần fetch tiếp theo bắt đầu từ 49
  let pageSize = $state(12); // Số lượng item hiện trong grid (không tính banner)
  let isLoading = $state(false);

  type SortType = 'popular' | 'sales' | 'latest' | 'price-asc' | 'price-desc';
  let activeSort = $state<SortType>('popular');

  // Price Slider State
  // Elite V2.2: Use backend facets for real price range, fallback to full range
  const MIN_VAL = facets?.price_min ?? 0;
  const MAX_VAL = facets?.price_max ?? 2000000;
  const isSearchMode = !categorySlug;
  let minPrice = $state(MIN_VAL);
  let maxPrice = $state(MAX_VAL);
  let sliderEl = $state<HTMLElement | null>(null);

  // Filter State
  let selectedBrands = $state<string[]>([]);
  let selectedOrigins = $state<string[]>([]);

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
    minPrice = MIN_VAL;
    maxPrice = MAX_VAL;
  }

  function removeBrand(brand: string) {
    selectedBrands = selectedBrands.filter(b => b !== brand);
  }

  function removeOrigin(origin: string) {
    selectedOrigins = selectedOrigins.filter(o => o !== origin);
  }

  async function loadMore() {
    if (isLoading) return;

    const gridVisible = displayProducts().length;
    const gridAvailable = allProducts.length - 1; // trừ banner

    // Giai đoạn 1: Mở rộng từ data đã có (SSR load 49 sp)
    if (gridVisible < gridAvailable) {
      isLoading = true;
      setTimeout(() => {
        pageSize += 12;
        isLoading = false;
      }, 300);
      return;
    }

    // Giai đoạn 2: Hết data local → Fetch API proxy
    if (allProducts.length >= serverTotal) return;
    // Elite V2.2: Search mode has no category_slug for API fetch
    if (!categorySlug) return;

    isLoading = true;
    try {
      const res = await fetch(`/api/client/products?category_slug=${categorySlug}&limit=48&offset=${currentOffset}&status=ACTIVE`);
      if (res.ok) {
        const data = await res.json();
        const newItems = (data.data || []) as Product[];
        allProducts = [...allProducts, ...newItems];
        currentOffset += newItems.length;
        pageSize += 12;
      }
    } catch (e) {
      console.error('[LOAD MORE FAILED]', e);
    } finally {
      isLoading = false;
    }
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
    return selectedBrands.length > 0 || selectedOrigins.length > 0 || minPrice !== MIN_VAL || maxPrice !== MAX_VAL;
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
  // Helper to get attribute safely from multiple possible paths
  function getAttr(p: Product, key: string): string | null {
    const val = p.metadata?.[key] ?? p.attributes?.[key] ?? p.attributes?.[key === 'brand' ? 'Thương hiệu' : 'Xuất xứ'];
    return typeof val === 'string' ? val.trim() : null;
  }

  // Elite V2.2: Filter options — prefer backend facets, fallback to client-side derivation
  // CẤM hardcode brands/origins — mọi dữ liệu phải flow từ DB
  const brands = $derived(() => {
    if (facets?.brands && facets.brands.length > 0) return facets.brands;
    const set = new Set<string>();
    allProducts.forEach(p => {
      const b = getAttr(p, 'brand');
      if (b) set.add(b);
    });
    return Array.from(set).sort();
  });

  const origins = $derived(() => {
    if (facets?.origins && facets.origins.length > 0) return facets.origins;
    const set = new Set<string>();
    allProducts.forEach(p => {
      const o = getAttr(p, 'origin');
      if (o) set.add(o);
    });
    return Array.from(set).sort();
  });

  const enhancedProducts = $derived.by(() => {
    return allProducts.map(p => ({
      ...p,
      image: p.images && p.images.length > 0 ? p.images[0] : '',
      // Elite V2.2: Dùng discountPrice từ DB — CẤM tự nhân giá ảo
      originalPrice: p.discountPrice ? p.price : undefined,
      // Elite V2.2: Dùng order_count thực từ DB — CẤM tự bơm số ảo
      sales: p.orderCount ?? 0,
      rating: p.rating ?? undefined,
      ratingCount: p.ratingCount ?? undefined,
    }));
  });

  const filteredProducts = $derived.by(() => {
    let result = enhancedProducts.filter(p => {
      const price = p.discountPrice ?? p.price;
      const matchPrice = price >= minPrice && price <= maxPrice;
      
      // Brand Filter
      const matchBrand = selectedBrands.length === 0 || (() => {
        const b = getAttr(p, 'brand');
        return b && selectedBrands.includes(b);
      })();

      // Origin Filter
      const matchOrigin = selectedOrigins.length === 0 || (() => {
        const o = getAttr(p, 'origin');
        return o && selectedOrigins.includes(o);
      })();

      return matchPrice && matchBrand && matchOrigin;
    });

    // Elite V2.2: Search mode → giữ nguyên backend ranking (Hybrid Search Engine)
    // Category mode → sort theo user chọn
    if (!isSearchMode) {
      if (activeSort === 'popular') result.sort((a, b) => (b.ratingCount || 0) - (a.ratingCount || 0));
      if (activeSort === 'sales') result.sort((a, b) => (b.sales || 0) - (a.sales || 0));
      if (activeSort === 'latest') result.sort((a, b) => b.id.localeCompare(a.id));
    }
    if (activeSort === 'price-asc') result.sort((a, b) => a.price - b.price);
    if (activeSort === 'price-desc') result.sort((a, b) => b.price - a.price);
    
    return result;
  });

  // Elite V2.2: Search mode → no banner (banner steals the #1 match result)
  // Category mode → item[0] → banner, item[1..N] → grid
  const bannerProduct = $derived(isSearchMode ? null : (filteredProducts[0] ?? null));

  const displayProducts = $derived.by(() => {
    if (isSearchMode) {
      // Search mode: show all products in grid (no banner skip)
      return filteredProducts.slice(0, pageSize);
    }
    // Category mode: skip index 0 (used for banner)
    return filteredProducts.slice(1, 1 + pageSize);
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
        <span class="text-gray-900">{isSearchMode ? "Tìm kiếm" : categoryName}</span>
      </nav>

      <!-- Category Title & Rating -->
      <div class="flex items-center gap-6">
        <h1 class="text-3xl font-black text-gray-900 tracking-tight">{categoryName}</h1>
        {#if !isSearchMode}
        <div class="flex items-center gap-2 pt-1">
          <div class="flex text-[#ffac33] text-sm">
            {#each Array(5) as _}
              <svg class="w-4 h-4 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
            {/each}
          </div>
          <span class="text-[13px] text-blue-500 font-medium whitespace-nowrap">339 đánh giá</span>
        </div>
        {/if}
      </div>
    </div>
  </div>

  {#if !isSearchMode}
  <!-- VIRAL BANNER ZONE: đọc 1 lần duy nhất / tab → item[0] làm banner -->
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 mt-6">
    <CategoryBanner product={bannerProduct} />
  </div>
  {/if}

  <!-- MAIN CONTENT: Sidebar + Grid -->
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 mt-6 flex gap-6">
    {#if !isSearchMode}
    <!-- LEFT SIDEBAR (Sharp Elite / Glassmorphism) -->
    <aside class="w-[240px] shrink-0 space-y-6">
      <!-- Sidebar Header -->
      <div class="bg-black text-white p-5 rounded-none shadow-xl transform hover:-translate-y-1 transition-all duration-500 overflow-hidden relative group">
        <div class="absolute inset-0 bg-gradient-to-tr from-[#ee4d2d]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
        <h2 class="text-[14px] font-black uppercase tracking-[0.2em] relative z-10 flex items-center gap-3">
           <div class="w-1.5 h-1.5 bg-[#ee4d2d] rounded-full animate-pulse"></div>
           Bộ lọc
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
                class="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white border-[4px] border-[#ee4d2d] rounded-full shadow-xl cursor-grab active:cursor-grabbing z-[var(--z-content)] hover:scale-110 transition-transform"
                style="left: calc({getPercent(minPrice)}% - 12px)"></div>

              <div
                use:setupDraggable={'max'}
                class="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white border-[4px] border-[#ee4d2d] rounded-full shadow-xl cursor-grab active:cursor-grabbing z-[var(--z-content)] hover:scale-110 transition-transform"
                style="left: calc({getPercent(maxPrice)}% - 12px)"></div>
            </div>
          </div>
        </div>

        <!-- Brands Checkbox (Minimalist Round) -->
        {#if brands().length > 0}
        <div class="space-y-6 pt-4">
          <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Thương Hiệu</h4>
          <div class="flex flex-col gap-4">
            {#each brands() as brand}
              <button 
                onclick={() => toggleBrand(brand)}
                class="flex items-center justify-between group cursor-pointer w-full text-left"
              >
                <span class="text-[13px] font-bold {selectedBrands.includes(brand) ? 'text-black' : 'text-gray-400'} group-hover:text-black transition-all">
                   {brand}
                </span>
                <div 
                  class="w-5 h-5 rounded-full border-2 transition-all flex items-center justify-center {selectedBrands.includes(brand) ? 'border-[#ee4d2d] bg-[#ee4d2d]' : 'border-gray-100 bg-gray-50'} shadow-inner">
                   {#if selectedBrands.includes(brand)}
                      <div class="w-1.5 h-1.5 bg-white rounded-full"></div>
                   {/if}
                </div>
              </button>
            {/each}
          </div>
        </div>
        {/if}

        <!-- Origin Checkbox -->
        {#if origins().length > 0}
        <div class="space-y-6 pt-4">
          <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Xuất Xứ</h4>
          <div class="flex flex-col gap-4">
            {#each origins() as country}
              <button 
                onclick={() => toggleOrigin(country)}
                class="flex items-center justify-between group cursor-pointer w-full text-left"
              >
                <span class="text-[13px] font-bold {selectedOrigins.includes(country) ? 'text-black' : 'text-gray-400'} group-hover:text-black transition-all">
                   {country}
                </span>
                <div 
                  class="w-5 h-5 rounded-full border-2 transition-all flex items-center justify-center {selectedOrigins.includes(country) ? 'border-[#ee4d2d] bg-[#ee4d2d]' : 'border-gray-100 bg-gray-50'}">
                   {#if selectedOrigins.includes(country)}
                      <div class="w-1.5 h-1.5 bg-white rounded-full"></div>
                   {/if}
                </div>
              </button>
            {/each}
          </div>
        </div>
        {/if}
      </div>
    </aside>
    {/if}

    <!-- RIGHT GRID AREA -->
    <main class="flex-1 min-w-0">
      <!-- UNIFIED SORT & FILTER BAR (Viral 2026 / Single Block) -->
      {#if !isSearchMode}
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
               <div class="absolute top-full right-0 w-full bg-white border border-gray-100 shadow-2xl opacity-0 group-hover/sort:opacity-100 invisible group-hover/sort:visible transition-all duration-300 z-[var(--z-dropdown)] py-1">
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

               {#if minPrice !== MIN_VAL || maxPrice !== MAX_VAL}
                 <button 
                    onclick={() => { minPrice = MIN_VAL; maxPrice = MAX_VAL; }}
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
      {/if}

      <div class="mt-8">
        {#if filteredProducts.length > 0}
          <ProductGrid products={displayProducts} />
        {:else}
          <!-- ELITE EMPTY STATE (Premium 2026) -->
          <div class="bg-white/80 backdrop-blur-xl border border-dashed border-gray-200 py-32 flex flex-col items-center justify-center text-center shadow-sm">
             <div class="relative mb-8">
                <!-- Outer Ring -->
                <div class="absolute inset-0 bg-[#ee4d2d]/5 rounded-full scale-150 blur-2xl animate-pulse"></div>
                <!-- Main Icon Circle -->
                <div class="relative w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center border border-gray-100 shadow-inner">
                   <svg class="w-10 h-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                   </svg>
                   <!-- Floating 0 Badge -->
                   <div class="absolute -top-1 -right-1 w-8 h-8 bg-black text-white text-[12px] font-black rounded-full flex items-center justify-center border-4 border-white">0</div>
                </div>
             </div>

             <h3 class="text-xl font-black text-gray-900 mb-3 tracking-tight uppercase italic">
                Rất tiếc, không tìm thấy sản phẩm!
             </h3>
             <p class="text-[13px] text-gray-500 max-w-[400px] leading-relaxed mb-10 font-medium">
                Sản phẩm trong nội dung hiện chưa có kết quả nào khớp với bộ lọc. Quý khách vui lòng <span class="text-black font-bold">xóa bớt bộ lọc</span> hoặc quay lại sau nhé.
             </p>

             <div class="flex items-center gap-4">
                {#if hasActiveFilters()}
                  <button 
                    onclick={clearAllFilters}
                    class="px-8 py-3.5 bg-black text-white text-[11px] font-black uppercase tracking-[0.2em] transition-all active:scale-95 shadow-2xl"
                  >
                    Xóa tất cả bộ lọc
                  </button>
                {/if}
                <button 
                  onclick={() => goto('/')}
                  class="px-8 py-3.5 bg-white border border-gray-200 text-gray-900 text-[11px] font-black uppercase tracking-[0.2em] hover:bg-gray-50 transition-all active:scale-95"
                >
                  Về trang chủ
                </button>
             </div>
          </div>
        {/if}
      </div>

      <!-- AUTOMATIC PAGINATION (Infinite Scroll) -->
      <!-- AUTOMATIC PAGINATION (Infinite Scroll Elite) -->
      {#if (allProducts.length < serverTotal || displayProducts.length < filteredProducts.length - 1) && filteredProducts.length > 0}
        <div class="mt-12 flex flex-col items-center gap-4 py-10" use:setupInfiniteScroll>
          <div class="text-[12px] text-gray-400 font-black uppercase tracking-widest">
            Đã tải <span class="text-black">{displayProducts.length + 1}</span> / {serverTotal} sản phẩm
          </div>
          <div class="w-[200px] h-[2px] bg-gray-100 overflow-hidden relative">
             <div class="h-full bg-[#ee4d2d] transition-all duration-700" style="width: {( (displayProducts.length + 1) / serverTotal) * 100}%"></div>
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
      {:else if serverTotal > 0}
        <div class="mt-16 text-center py-10 border-t border-gray-50">
           <span class="text-[11px] font-black text-gray-300 uppercase tracking-[0.5em]">Đã hiển thị toàn bộ {serverTotal} sản phẩm</span>
        </div>
      {/if}
    </main>
  </div>
</div>

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>