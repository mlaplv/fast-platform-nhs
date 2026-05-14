<script lang="ts">
  import { goto } from '$app/navigation';

  import ProductGrid from './ProductGrid.svelte';
  import CategoryBanner from './CategoryBanner.svelte';
  import type { Product } from '$lib/types';
  import type { ProductFacets } from '$lib/types';
  import type { Category } from '$lib/types';
  import { onMount } from 'svelte';
  import { scale } from 'svelte/transition';
  import MessageCircleQuestion from "@lucide/svelte/icons/message-circle-question";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import ArrowUpDown from "@lucide/svelte/icons/arrow-up-down";
  import ProductReviews from '../product-detail/shared/ProductReviews.svelte';
  import type { ReviewStats } from '$lib/types';


  interface Props {
    products: Product[];
    categoryName: string;
    categorySlug: string;
    serverTotal: number;
    facets?: ProductFacets | null;
    category?: Category | null;
  }

  let { 
    products = [], 
    categoryName = "Danh mục",
    categorySlug,
    serverTotal,
    facets = null,
    category = null,
  }: Props = $props();

  // --- STATE & LOGIC ---
  let allProducts = $state<Product[]>([...products]);
  let currentOffset = $state(49);
  let pageSize = $state(12);
  let isLoading = $state(false);

  type SortType = 'popular' | 'sales' | 'latest' | 'price-asc' | 'price-desc';
  let activeSort = $state<SortType>('popular');

  const MIN_VAL = facets?.price_min ?? 0;
  const MAX_VAL = facets?.price_max ?? 2000000;
  const isSearchMode = !categorySlug;
  let minPrice = $state(MIN_VAL);
  let maxPrice = $state(MAX_VAL);
  let sliderEl = $state<HTMLElement | null>(null);

  let selectedBrands = $state<string[]>([]);
  let selectedOrigins = $state<string[]>([]);

  function toggleBrand(brand: string) {
    selectedBrands = selectedBrands.includes(brand) ? selectedBrands.filter(b => b !== brand) : [...selectedBrands, brand];
  }

  function toggleOrigin(origin: string) {
    selectedOrigins = selectedOrigins.includes(origin) ? selectedOrigins.filter(o => o !== origin) : [...selectedOrigins, origin];
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
    const gridAvailable = allProducts.length - 1;
    if (gridVisible < gridAvailable) {
      isLoading = true;
      setTimeout(() => { pageSize += 12; isLoading = false; }, 300);
      return;
    }
    if (allProducts.length >= serverTotal || !categorySlug) return;
    isLoading = true;
    try {
      const res = await fetch(`/api/v1/client/products?category_slug=${categorySlug}&limit=48&offset=${currentOffset}&status=ACTIVE`);
      if (res.ok) {
        const data = await res.json();
        const newItems = (data.data || []) as Product[];
        allProducts = [...allProducts, ...newItems];
        currentOffset += newItems.length;
        pageSize += 12;
      }
    } catch (e) { console.error('[LOAD MORE FAILED]', e); } finally { isLoading = false; }
  }

  function setupInfiniteScroll(node: HTMLElement) {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) loadMore();
    }, { threshold: 0.1 });
    observer.observe(node);
    return { destroy() { observer.unobserve(node); } };
  }

  let hasActiveFilters = $derived(() => selectedBrands.length > 0 || selectedOrigins.length > 0 || minPrice !== MIN_VAL || maxPrice !== MAX_VAL);
  const getPercent = (value: number) => ((value - MIN_VAL) / (MAX_VAL - MIN_VAL)) * 100;

  function handleSliderUpdate(e: PointerEvent, type: 'min' | 'max') {
    if (!sliderEl) return;
    const rect = sliderEl.getBoundingClientRect();
    const percent = Math.min(Math.max(0, (e.clientX - rect.left) / rect.width), 1);
    const value = Math.round(MIN_VAL + (MAX_VAL - MIN_VAL) * percent);
    if (type === 'min') minPrice = Math.min(value, maxPrice - 50000);
    else maxPrice = Math.max(value, minPrice + 50000);
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

  function getAttr(p: Product, key: string): string | null {
    const val = p.metadata?.[key] ?? p.attributes?.[key] ?? p.attributes?.[key === 'brand' ? 'Thương hiệu' : 'Xuất xứ'];
    return typeof val === 'string' ? val.trim() : null;
  }

  const brands = $derived(() => {
    if (facets?.brands?.length) return facets.brands;
    const set = new Set<string>();
    allProducts.forEach(p => { const b = getAttr(p, 'brand'); if (b) set.add(b); });
    return Array.from(set).sort();
  });

  const origins = $derived(() => {
    if (facets?.origins?.length) return facets.origins;
    const set = new Set<string>();
    allProducts.forEach(p => { const o = getAttr(p, 'origin'); if (o) set.add(o); });
    return Array.from(set).sort();
  });

  const enhancedProducts = $derived.by(() => allProducts.map(p => ({
    ...p,
    image: p.images?.[0] || '',
    originalPrice: p.discountPrice ? p.price : undefined,
    sales: p.orderCount ?? 0,
  })));

  const filteredProducts = $derived.by(() => {
    let result = enhancedProducts.filter(p => {
      const price = p.discountPrice ?? p.price;
      const matchPrice = price >= minPrice && price <= maxPrice;
      const matchBrand = selectedBrands.length === 0 || (() => { const b = getAttr(p, 'brand'); return b && selectedBrands.includes(b); })();
      const matchOrigin = selectedOrigins.length === 0 || (() => { const o = getAttr(p, 'origin'); return o && selectedOrigins.includes(o); })();
      return matchPrice && matchBrand && matchOrigin;
    });
    if (!isSearchMode) {
      if (activeSort === 'popular') result.sort((a, b) => (b.ratingCount || 0) - (a.ratingCount || 0));
      if (activeSort === 'sales') result.sort((a, b) => (b.sales || 0) - (a.sales || 0));
      if (activeSort === 'latest') result.sort((a, b) => b.id.localeCompare(a.id));
    }
    if (activeSort === 'price-asc') result.sort((a, b) => a.price - b.price);
    if (activeSort === 'price-desc') result.sort((a, b) => b.price - a.price);
    return result;
  });

  const bannerProduct = $derived(isSearchMode ? null : (filteredProducts[0] ?? null));
  const displayProducts = $derived.by(() => isSearchMode ? filteredProducts.slice(0, pageSize) : filteredProducts.slice(1, 1 + pageSize));
  
  const faqs = $derived(category?.metadata?.faqs || category?.category_metadata?.faqs || []);
  let stats = $state<ReviewStats | null>(null);

  onMount(async () => {
    if (!isSearchMode && category?.id) {
      try {
        const res = await fetch(`/api/v1/client/reviews/stats?entity_type=CATEGORY&entity_id=${category.id}`);
        if (res.ok) stats = await res.json();
      } catch (e) {
        console.error('Failed to load category stats:', e);
      }
    }
  });
</script>

<div class="bg-[#F5F5F5] min-h-screen pb-20">
  <div class="bg-white border-b border-gray-100">
    <div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-6">
      <nav class="flex items-center gap-2 text-[12px] text-gray-400 mb-4 font-medium tracking-wider">
        <a href="/" class="hover:text-[#ee4d2d] transition-colors">Trang chủ</a>
        <span>/</span>
        <span class="text-gray-900">{isSearchMode ? "Tìm kiếm" : categoryName}</span>
      </nav>

      <div class="flex items-center gap-6">
        <h1 class="text-3xl font-black text-gray-900 tracking-tight">{categoryName}</h1>
        {#if !isSearchMode}
        <div class="flex items-center gap-2 pt-1">
          <div class="flex text-[#ffac33] text-sm">
            {#each Array(5) as _, i}
              <svg class="w-4 h-4 {i < Math.floor(stats?.average_rating || 5) ? 'fill-current' : 'fill-gray-200'}" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
            {/each}
          </div>
          <span class="text-[13px] text-blue-500 font-medium whitespace-nowrap">{stats?.total_count || 0} đánh giá</span>
        </div>
        {/if}
      </div>
    </div>
  </div>

  {#if !isSearchMode}
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 mt-6">
    <CategoryBanner product={bannerProduct} />
  </div>
  {/if}

  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 mt-6 flex gap-6">
    {#if !isSearchMode}
    <aside class="w-[240px] shrink-0 space-y-6">
      <div class="bg-zinc-900 text-white p-5 shadow-2xl relative group overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none"></div>
        <h2 class="text-[12px] font-black tracking-[0.2em] relative z-10 flex items-center gap-3 italic">
           <div class="w-1.5 h-1.5 bg-[#C18F7E] rounded-full animate-pulse shadow-[0_0_10px_rgba(193,143,126,0.8)]"></div>
           Bộ lọc tối ưu
        </h2>
      </div>

      <div class="bg-white/70 backdrop-blur-xl border border-white px-0 py-4 space-y-6 shadow-sm">
        <div class="space-y-4 px-2">
           <div class="flex items-center justify-between">
              <h4 class="text-[9px] font-black text-gray-400 tracking-widest flex items-center gap-1.5">
                 <div class="w-1 h-1 bg-[#C18F7E] rounded-full"></div>
                 Khoảng giá
              </h4>
              <span class="text-[10px] font-mono text-[#C18F7E] font-bold">VND</span>
           </div>
           
           <div class="flex items-center gap-2">
              <div class="flex-1 relative group">
                 <div class="absolute inset-0 bg-[#C18F7E]/5 blur-sm opacity-0 group-focus-within:opacity-100 transition-opacity"></div>
                 <input 
                    type="text" 
                    value={Math.round(minPrice).toLocaleString()} 
                    readonly 
                    class="relative w-full h-8 bg-black/5 border border-gray-100/50 group-hover:border-[#C18F7E]/30 focus:border-[#C18F7E]/50 text-[11px] font-black text-gray-900 text-center outline-none transition-all rounded-md" 
                 />
              </div>
              <div class="w-2 h-px bg-gray-200"></div>
              <div class="flex-1 relative group">
                 <div class="absolute inset-0 bg-[#C18F7E]/5 blur-sm opacity-0 group-focus-within:opacity-100 transition-opacity"></div>
                 <input 
                    type="text" 
                    value={Math.round(maxPrice).toLocaleString()} 
                    readonly 
                    class="relative w-full h-8 bg-black/5 border border-gray-100/50 group-hover:border-[#C18F7E]/30 focus:border-[#C18F7E]/50 text-[11px] font-black text-gray-900 text-center outline-none transition-all rounded-md" 
                 />
              </div>
           </div>

           <div class="relative pt-4 pb-6 px-4">
             <div bind:this={sliderEl} class="h-1 w-full bg-gray-100 rounded-full relative">
               <div class="absolute h-full bg-[#C18F7E] rounded-full shadow-[0_0_10px_rgba(193,143,126,0.3)]" style="left: {getPercent(minPrice)}%; right: {100 - getPercent(maxPrice)}%"></div>
               
               <!-- Milestones -->
               <div class="absolute inset-0 flex justify-between px-0.5">
                  {#each [0, 500000, 1000000, 1500000, 2000000] as mark}
                     <div class="relative flex flex-col items-center">
                        <div class="w-1 h-1 rounded-full {mark >= minPrice && mark <= maxPrice ? 'bg-[#C18F7E]' : 'bg-gray-200'} transition-colors"></div>
                        <span class="absolute top-3 text-[7px] font-black text-gray-300 tracking-tighter">
                           {mark === 0 ? '0' : (mark / 1000000) + 'M'}
                        </span>
                     </div>
                  {/each}
               </div>

               <!-- Min Handle -->
               <div 
                  use:setupDraggable={'min'} 
                  class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-[#C18F7E] rounded-full shadow-lg cursor-pointer transition-transform flex items-center justify-center group/handle z-10" 
                  style="left: calc({getPercent(minPrice)}% - 8px)"
               >
                  <div class="absolute -top-7 left-1/2 -translate-x-1/2 px-1.5 py-0.5 bg-black text-white text-[9px] font-black rounded opacity-0 group-hover/handle:opacity-100 transition-opacity whitespace-nowrap shadow-xl">
                    {minPrice === 0 ? '0₫' : (minPrice < 1000 ? minPrice + '₫' : Math.round(minPrice / 1000) + 'k')}
                    <div class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-black rotate-45"></div>
                  </div>
                  <div class="w-1 h-1 bg-[#C18F7E] rounded-full animate-pulse"></div>
               </div>

               <!-- Max Handle -->
               <div 
                  use:setupDraggable={'max'} 
                  class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-[#C18F7E] rounded-full shadow-lg cursor-pointer transition-transform flex items-center justify-center group/handle z-10" 
                  style="left: calc({getPercent(maxPrice)}% - 8px)"
               >
                  <div class="absolute -top-7 left-1/2 -translate-x-1/2 px-1.5 py-0.5 bg-black text-white text-[9px] font-black rounded opacity-0 group-hover/handle:opacity-100 transition-opacity whitespace-nowrap shadow-xl">
                    {maxPrice === 0 ? '0₫' : (maxPrice < 1000 ? maxPrice + '₫' : Math.round(maxPrice / 1000) + 'k')}
                    <div class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-black rotate-45"></div>
                  </div>
                  <div class="w-1 h-1 bg-[#C18F7E] rounded-full animate-pulse"></div>
               </div>
             </div>
           </div>
        </div>

        {#if brands().length > 0}
        <div class="space-y-6 pt-4 px-2">
          <h4 class="text-[11px] font-black text-gray-400 tracking-widest">Thương hiệu</h4>
          <div class="flex flex-col gap-4">
            {#each brands() as brand}
              <button onclick={() => toggleBrand(brand)} class="flex items-center justify-between group w-full text-left">
                <span class="text-[13px] font-bold {selectedBrands.includes(brand) ? 'text-black' : 'text-gray-400'}">{brand}</span>
                <div class="w-5 h-5 rounded-full border-2 {selectedBrands.includes(brand) ? 'border-[#ee4d2d] bg-[#ee4d2d]' : 'border-gray-100'}"></div>
              </button>
            {/each}
          </div>
        </div>
        {/if}

        {#if origins().length > 0}
        <div class="space-y-6 pt-4 px-2">
          <h4 class="text-[11px] font-black text-gray-400 tracking-widest">Xuất xứ</h4>
          <div class="flex flex-col gap-4">
            {#each origins() as country}
              <button onclick={() => toggleOrigin(country)} class="flex items-center justify-between group w-full text-left">
                <span class="text-[13px] font-bold {selectedOrigins.includes(country) ? 'text-black' : 'text-gray-400'}">{country}</span>
                <div class="w-5 h-5 rounded-full border-2 {selectedOrigins.includes(country) ? 'border-[#ee4d2d] bg-[#ee4d2d]' : 'border-gray-100'}"></div>
              </button>
            {/each}
          </div>
        </div>
        {/if}

        {#if faqs.length > 0}
        <div class="space-y-3 pt-6 border-t border-gray-100 px-2">
           <div class="flex items-center gap-2 mb-2">
              <div class="w-1 h-4 bg-orange-500/40 rounded-full"></div>
              <h4 class="text-[10px] font-black text-gray-900 tracking-widest flex items-center gap-1.5">
                 <MessageCircleQuestion size={11} class="text-orange-500" /> Faq Core
              </h4>
           </div>
           <div class="space-y-2">
              {#each faqs as faq, i}
                 <details open={i === 0} class="group bg-gray-50/40 rounded-[5px] border border-transparent hover:border-orange-500/10 hover:bg-white transition-all overflow-hidden">
                    <summary class="text-[11px] font-bold text-gray-700 list-none cursor-pointer py-2.5 px-3 pr-8 relative select-none leading-tight">
                       {faq.question}
                       <div class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 rounded-md bg-white border border-gray-100 flex items-center justify-center transition-transform group-open:rotate-180 group-open:bg-orange-500 group-open:border-orange-600 shadow-sm">
                          <svg class="w-2.5 h-2.5 text-gray-400 group-open:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="4">
                             <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                          </svg>
                       </div>
                    </summary>
                    <div class="px-3 pb-3 text-[11px] text-gray-500 leading-relaxed font-medium animate-in fade-in slide-in-from-top-1 duration-200">
                       <div class="pt-2 border-t border-gray-50/50">
                          {faq.answer}
                       </div>
                    </div>
                 </details>
              {/each}
           </div>
        </div>
        {/if}
      </div>
    </aside>
    {/if}

    <main class="flex-1 min-w-0">
      <div class="bg-white border border-gray-100 shadow-sm p-8">
        {#if !isSearchMode}
        <div class="border-b border-gray-50 pb-2 mb-8 flex flex-col gap-2">
            <div class="flex items-center gap-6 bg-white/50 backdrop-blur-md p-2 rounded-none border border-gray-50 shadow-sm">
              <div class="flex items-center bg-gray-50/50 p-1 rounded-none border border-gray-50">
                {#each ['popular', 'sales', 'latest'] as sort}
                  <button 
                    onclick={() => activeSort = sort}
                    class="px-8 py-2.5 text-[11px] font-black tracking-widest transition-all relative rounded-none {activeSort === sort ? 'bg-zinc-900 text-white shadow-lg' : 'text-gray-400 hover:text-gray-900'}">
                    {sort === 'popular' ? 'Phổ biến' : sort === 'sales' ? 'Bán chạy' : 'Mới nhất'}
                  </button>
                {/each}
              </div>

              <div class="ml-auto relative group/sort">
                 <button class="bg-white/80 backdrop-blur-sm border-b-2 border-luxury-copper/20 px-6 py-2.5 text-[11px] font-black text-gray-800 flex items-center justify-between w-[220px] hover:border-luxury-copper hover:bg-white transition-all shadow-sm">
                    <div class="flex items-center gap-3">
                       <ArrowUpDown size={14} class="text-luxury-copper/60 group-hover/sort:text-luxury-copper transition-colors" />
                       <span class="opacity-80 group-hover/sort:opacity-100 transition-opacity">{activeSort === 'price-asc' ? 'Giá: Thấp đến cao' : activeSort === 'price-desc' ? 'Giá: Cao đến thấp' : 'Sắp xếp theo giá'}</span>
                    </div>
                    <ChevronDown size={14} class="text-gray-300 group-hover/sort:rotate-180 transition-transform duration-500" />
                 </button>
                 <div class="absolute top-[calc(100%+4px)] right-0 w-full bg-white/95 backdrop-blur-xl border border-gray-100 shadow-[0_20px_50px_rgba(0,0,0,0.06)] opacity-0 translate-y-2 group-hover/sort:opacity-100 group-hover/sort:translate-y-0 invisible group-hover/sort:visible transition-all duration-300 py-2 z-50 rounded-none">
                    <button onclick={() => activeSort = 'price-asc'} class="w-full text-left px-6 py-4 text-[10px] font-black text-gray-500 hover:text-luxury-copper hover:bg-gray-50/50 flex items-center justify-between tracking-widest transition-colors">
                       Giá: Thấp đến cao
                       {#if activeSort === 'price-asc'}<div class="w-1.5 h-1.5 bg-luxury-copper rounded-full shadow-[0_0_8px_rgba(193,143,126,0.4)]"></div>{/if}
                    </button>
                    <div class="mx-4 h-px bg-gray-50"></div>
                    <button onclick={() => activeSort = 'price-desc'} class="w-full text-left px-6 py-4 text-[10px] font-black text-gray-500 hover:text-luxury-copper hover:bg-gray-50/50 flex items-center justify-between tracking-widest transition-colors">
                       Giá: Cao đến thấp
                       {#if activeSort === 'price-desc'}<div class="w-1.5 h-1.5 bg-luxury-copper rounded-full shadow-[0_0_8px_rgba(193,143,126,0.4)]"></div>{/if}
                    </button>
                 </div>
              </div>
            </div>
            {#if hasActiveFilters()}
              <div class="px-4 py-2 border-t border-gray-50 flex flex-wrap items-center gap-2">
                 <button onclick={clearAllFilters} class="text-[#ee4d2d] hover:underline text-[10px] font-black tracking-tighter">Xóa tất cả bộ lọc</button>
              </div>
            {/if}
        </div>
        {/if}

      <div class="mt-2">
        {#if filteredProducts.length > 0}
          <ProductGrid products={displayProducts} />
        {:else}
          <div class="bg-white border-2 border-dashed border-gray-200 py-32 flex flex-col items-center justify-center text-center">
             <h3 class="text-xl font-black text-gray-900 mb-3 tracking-tight">Không tìm thấy sản phẩm!</h3>
             <button onclick={() => goto('/')} class="px-8 py-3.5 bg-black text-white text-[11px] font-black tracking-[0.1em]">Về trang chủ</button>
          </div>
        {/if}
      </div>

      {#if (allProducts.length < serverTotal || displayProducts.length < filteredProducts.length - 1) && filteredProducts.length > 0}
        <div class="mt-12 flex flex-col items-center gap-4 py-10" use:setupInfiniteScroll>
          <div class="text-[12px] text-gray-400 font-black tracking-widest">Đã tải <span class="text-black">{displayProducts.length + 1}</span> / {serverTotal} sản phẩm</div>
          {#if isLoading}
            <div class="text-[11px] font-black text-[#ee4d2d] animate-pulse">Đang tải thêm...</div>
          {/if}
        </div>
        {:else if serverTotal > 0}
          <div class="mt-12 text-center py-6 border-t border-gray-50">
             <span class="text-[10px] font-bold text-gray-400 tracking-widest opacity-60 flex items-center justify-center gap-3">
               <div class="w-8 h-px bg-gray-200"></div>
               Đã hiển thị toàn bộ {serverTotal} sản phẩm
               <div class="w-8 h-px bg-gray-200"></div>
             </span>
          </div>
        {/if}
      </div>
      
      {#if !isSearchMode && category}
        <div class="mt-8">
          <ProductReviews product={category} entityType="CATEGORY" />
        </div>
      {/if}
    </main>
  </div>
</div>

<style>
  details summary::-webkit-details-marker { display: none; }
</style>
