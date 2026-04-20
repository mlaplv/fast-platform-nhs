<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import ProductGrid from './ProductGrid.svelte';
  import CategoryBanner from './CategoryBanner.svelte';
  import type { Product, ProductFacets, Category } from '$lib/types';
  import { scale } from 'svelte/transition';

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
      const res = await fetch(`/api/client/products?category_slug=${categorySlug}&limit=48&offset=${currentOffset}&status=ACTIVE`);
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
  
  const faqs = $derived(category?.category_metadata?.faqs || []);
</script>

<div class="bg-[#F5F5F5] min-h-screen pb-20">
  <div class="bg-white border-b border-gray-100">
    <div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-6">
      <nav class="flex items-center gap-2 text-[12px] text-gray-400 mb-4 font-medium uppercase tracking-wider">
        <a href="/" class="hover:text-[#ee4d2d] transition-colors">Trang chủ</a>
        <span>/</span>
        <span class="text-gray-900">{isSearchMode ? "Tìm kiếm" : categoryName}</span>
      </nav>

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
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 mt-6">
    <CategoryBanner product={bannerProduct} />
  </div>
  {/if}

  <div class="max-w-[1200px] mx-auto px-4 xl:px-0 mt-6 flex gap-6">
    {#if !isSearchMode}
    <aside class="w-[240px] shrink-0 space-y-6">
      <div class="bg-black text-white p-5 shadow-xl relative group">
        <h2 class="text-[14px] font-black uppercase tracking-[0.2em] relative z-10 flex items-center gap-3">
           <div class="w-1.5 h-1.5 bg-[#ee4d2d] rounded-full animate-pulse"></div>
           Bộ lọc
        </h2>
      </div>

      <div class="bg-white/70 backdrop-blur-xl border border-white p-6 space-y-8 shadow-sm">
        <div class="space-y-6">
          <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Khoảng giá</h4>
          <div class="flex flex-col gap-3">
             <div class="relative group/input">
                <input type="text" value={Math.round(minPrice).toLocaleString()} readonly class="w-full h-12 bg-gray-50/50 border-none px-4 pr-10 text-[14px] font-black text-gray-900 outline-none" />
                <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs font-black">đ</span>
             </div>
             <div class="relative group/input">
                <input type="text" value={Math.round(maxPrice).toLocaleString()} readonly class="w-full h-12 bg-gray-50/50 border-none px-4 pr-10 text-[14px] font-black text-gray-900 outline-none" />
                <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs font-black">đ</span>
             </div>
          </div>
          <div class="relative pt-2 px-1">
            <div bind:this={sliderEl} class="h-2 w-full bg-gray-100 rounded-full relative">
              <div class="absolute h-full bg-[#ee4d2d] rounded-full" style="left: {getPercent(minPrice)}%; right: {100 - getPercent(maxPrice)}%"></div>
              <div use:setupDraggable={'min'} class="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white border-4 border-[#ee4d2d] rounded-full shadow-xl cursor-pointer" style="left: calc({getPercent(minPrice)}% - 12px)"></div>
              <div use:setupDraggable={'max'} class="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white border-4 border-[#ee4d2d] rounded-full shadow-xl cursor-pointer" style="left: calc({getPercent(maxPrice)}% - 12px)"></div>
            </div>
          </div>
        </div>

        {#if brands().length > 0}
        <div class="space-y-6 pt-4">
          <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Thương Hiệu</h4>
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
        <div class="space-y-6 pt-4">
          <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Xuất Xứ</h4>
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
        <div class="space-y-6 pt-8 border-t border-gray-100">
           <h4 class="text-[11px] font-black text-gray-400 uppercase tracking-widest">Câu hỏi thường gặp</h4>
           <div class="space-y-4">
              {#each faqs as faq}
                 <details class="group">
                    <summary class="text-[12px] font-bold text-gray-800 list-none cursor-pointer hover:text-[#ee4d2d] transition-colors pr-4 relative">
                       {faq.question}
                       <svg class="w-3 h-3 absolute right-0 top-1/2 -translate-y-1/2 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7" /></svg>
                    </summary>
                    <div class="pt-2 text-[11px] text-gray-500 leading-relaxed">
                       {faq.answer}
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
      {#if !isSearchMode}
      <div class="bg-white border border-gray-100 p-2 mb-8 flex flex-col gap-2 shadow-sm">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              {#each ['popular', 'sales', 'latest'] as sort}
                <button 
                  onclick={() => activeSort = sort}
                  class="px-6 py-3 text-[12px] font-black tracking-tighter transition-all relative {activeSort === sort ? 'text-[#ee4d2d]' : 'text-gray-400'}">
                  {sort === 'popular' ? 'PHỔ BIẾN' : sort === 'sales' ? 'BÁN CHẠY' : 'MỚI NHẤT'}
                  {#if activeSort === sort}
                    <div class="absolute bottom-1 left-1/2 -translate-x-1/2 w-8 h-[2px] bg-[#ee4d2d] rounded-full"></div>
                  {/if}
                </button>
              {/each}
            </div>
            <div class="relative group/sort">
               <button class="bg-gray-50 border px-5 py-2.5 text-[11px] font-black text-gray-800 flex items-center justify-between w-[200px] uppercase tracking-tighter">
                  <span>{activeSort === 'price-asc' ? 'GIÁ: THẤP ĐẾN CAO' : activeSort === 'price-desc' ? 'GIÁ: CAO ĐẾN THẤP' : 'SẮP XẾP THEO GIÁ'}</span>
               </button>
               <div class="absolute top-full right-0 w-full bg-white border shadow-2xl opacity-0 group-hover/sort:opacity-100 invisible group-hover/sort:visible transition-all py-1 z-50">
                  <button onclick={() => activeSort = 'price-asc'} class="w-full text-left px-5 py-3.5 text-[11px] font-black text-gray-500 hover:text-[#ee4d2d] hover:bg-gray-50">GIÁ: THẤP ĐẾN CAO</button>
                  <button onclick={() => activeSort = 'price-desc'} class="w-full text-left px-5 py-3.5 text-[11px] font-black text-gray-500 hover:text-[#ee4d2d] hover:bg-gray-50">GIÁ: CAO ĐẾN THẤP</button>
               </div>
            </div>
          </div>
          {#if hasActiveFilters()}
            <div class="px-4 py-2 border-t border-gray-50 flex flex-wrap items-center gap-2">
               <button onclick={clearAllFilters} class="text-[#ee4d2d] hover:underline text-[10px] font-black uppercase tracking-tighter">Xóa tất cả bộ lọc</button>
            </div>
          {/if}
      </div>
      {/if}

      <div class="mt-8">
        {#if filteredProducts.length > 0}
          <ProductGrid products={displayProducts} />
        {:else}
          <div class="bg-white border-2 border-dashed border-gray-200 py-32 flex flex-col items-center justify-center text-center">
             <h3 class="text-xl font-black text-gray-900 mb-3 tracking-tight uppercase">Không tìm thấy sản phẩm!</h3>
             <button onclick={() => goto('/')} class="px-8 py-3.5 bg-black text-white text-[11px] font-black uppercase tracking-[0.2em]">Về trang chủ</button>
          </div>
        {/if}
      </div>

      {#if (allProducts.length < serverTotal || displayProducts.length < filteredProducts.length - 1) && filteredProducts.length > 0}
        <div class="mt-12 flex flex-col items-center gap-4 py-10" use:setupInfiniteScroll>
          <div class="text-[12px] text-gray-400 font-black uppercase tracking-widest">Đã tải <span class="text-black">{displayProducts.length + 1}</span> / {serverTotal} sản phẩm</div>
          {#if isLoading}
            <div class="text-[11px] font-black text-[#ee4d2d] animate-pulse uppercase">Đang tải thêm...</div>
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
  details summary::-webkit-details-marker { display: none; }
</style>
