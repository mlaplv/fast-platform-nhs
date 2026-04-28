<script lang="ts">
  import { goto } from '$app/navigation';
  import { trimProductName } from '$lib/utils/format';
  import ProductGrid from './ProductGrid.svelte';
  import { fade, fly } from 'svelte/transition';
  import { ChevronLeft, Search, Filter, MessageCircleQuestion } from 'lucide-svelte';
  import type { Product, ProductFacets, Category } from '$lib/types';
  import BottomSheet from '$lib/components/mobile/BottomSheet.svelte';
  import ProductMobileReviews from '../product-detail/ProductMobileReviews.svelte';


  interface Props {
    products: Product[];
    categoryName?: string;
    searchQuery?: string;
    facets?: ProductFacets | null;
    category?: Category | null;
  }

  let { products = [], categoryName = "Danh mục", searchQuery, facets = null, category = null }: Props = $props();

  let activeTab = $state('CATEGORY');
  let isFilterDrawerOpen = $state(false);
  let selectedBrands = $state<string[]>([]);
  let selectedOrigins = $state<string[]>([]);
  let selectedServices = $state<string[]>([]);
  
  const MIN_VAL = $derived(facets?.price_min ?? 0);
  const MAX_VAL = $derived(facets?.price_max ?? 2000000);
  
  let minPrice = $state<number | null>(null);
  let maxPrice = $state<number | null>(null);

  const servicesList = ['Cam kết chính hãng', 'Tặng kèm mẫu thử', 'Gói quà cao cấp', 'Miễn phí vận chuyển', 'Tư vấn chuyên gia', 'Thanh toán linh hoạt'];

  function getAttr(p: Product, key: string): string | null {
    const val = p.metadata?.[key] ?? p.attributes?.[key] ?? p.attributes?.[key === 'brand' ? 'Thương hiệu' : 'Xuất xứ'];
    return typeof val === 'string' ? val.trim() : null;
  }

  const availableBrands = $derived(() => {
    if (facets?.brands?.length) return facets.brands;
    const set = new Set<string>();
    products.forEach(p => { const b = getAttr(p, 'brand'); if (b) set.add(b); });
    return Array.from(set).sort();
  });

  const availableOrigins = $derived(() => {
    if (facets?.origins?.length) return facets.origins;
    const set = new Set<string>();
    products.forEach(p => { const o = getAttr(p, 'origin'); if (o) set.add(o); });
    return Array.from(set).sort();
  });

  const filteredProducts = $derived(() => {
    let result = [...products];
    if (selectedBrands.length > 0) result = result.filter(p => { const b = getAttr(p, 'brand'); return b && selectedBrands.includes(b); });
    if (selectedOrigins.length > 0) result = result.filter(p => { const o = getAttr(p, 'origin'); return o && selectedOrigins.includes(o); });
    if (minPrice !== null || maxPrice !== null) {
      result = result.filter(p => {
        const price = p.discountPrice ?? p.price;
        if (minPrice !== null && price < minPrice) return false;
        if (maxPrice !== null && price > maxPrice) return false;
        return true;
      });
    }
    if (activeTab === 'BEST_SELLER') result.sort((a, b) => (b.orderCount ?? 0) - (a.orderCount ?? 0));
    else if (activeTab === 'TOP_RATED') result.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
    else if (activeTab === 'LATEST') result.sort((a, b) => b.id.localeCompare(a.id));
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
    if (minPrice === min && maxPrice === max) { minPrice = null; maxPrice = null; }
    else { minPrice = min; maxPrice = max; }
  }
  const hasActiveFilters = $derived.by(() => selectedBrands.length > 0 || selectedOrigins.length > 0 || selectedServices.length > 0 || minPrice !== null || maxPrice !== null);
  function clearFilters() { selectedBrands = []; selectedOrigins = []; selectedServices = []; minPrice = null; maxPrice = null; }

  const faqs = $derived(category?.metadata?.faqs || category?.category_metadata?.faqs || []);
</script>

<div class="min-h-screen bg-white pb-24 font-sans">
  <header class="sticky top-0 z-40 bg-white/95 backdrop-blur-xl border-b border-gray-100 flex flex-col">
    <div class="px-2 py-1 flex items-center gap-2 h-14">
       <button onclick={() => goto('/')} class="p-2 text-gray-900 flex-shrink-0"><ChevronLeft size={24} /></button>
       <div onclick={() => goto('/')} role="presentation" class="flex-1 min-w-0 h-[42px] bg-gray-100 rounded-xl flex items-center px-4 gap-2 border border-gray-100 cursor-pointer">
          <Search size={18} class="text-gray-400 flex-shrink-0" />
          <span class="text-[14px] text-gray-400 font-bold truncate">{searchQuery || "Tìm kiếm sản phẩm..."}</span>
       </div>
    </div>

    <div class="flex items-center px-3 pb-2 gap-2 overflow-hidden">
       <div class="flex-1 flex gap-1 overflow-x-auto no-scrollbar">
          {#each [
            { id: 'CATEGORY', label: categoryName },
            { id: 'TOP_RATED', label: 'Đánh giá cao' },
            { id: 'BEST_SELLER', label: 'Bán chạy' },
            { id: 'LATEST', label: 'Mới nhất' }
          ] as tab}
            <button onclick={() => activeTab = tab.id} class="px-4 py-2 text-[12px] font-bold rounded-full transition-all whitespace-nowrap {activeTab === tab.id ? 'bg-[var(--color-brand-primary)] text-white' : 'bg-transparent text-gray-600 font-medium'}">{tab.label}</button>
          {/each}
       </div>
       <button onclick={() => isFilterDrawerOpen = true} class="p-2 text-gray-700 relative border-l border-gray-100 ml-1">
         <Filter size={20} />
         {#if hasActiveFilters}<span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border border-white animate-pulse"></span>{/if}
       </button>
    </div>
  </header>

  <div class="p-4">
    {#if filteredProducts().length > 0}
      <ProductGrid products={filteredProducts()} />
    {:else}
      <div class="flex flex-col items-center justify-center py-24 px-10 text-center" in:fade>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Không tìm thấy kết quả</h3>
        <button onclick={clearFilters} class="mt-8 px-8 py-3 bg-black text-white text-[13px] font-black uppercase tracking-widest rounded-full">Xoá bộ lọc</button>
      </div>
    {/if}

    <div class="mt-8 text-center py-4 bg-white border border-gray-100 shadow-sm rounded-2xl mb-4">
       <span class="text-[9px] font-bold text-gray-400 uppercase tracking-widest opacity-60 flex items-center justify-center gap-3">
         <div class="w-6 h-px bg-gray-200"></div>
         Đã hiển thị toàn bộ {products.length} sản phẩm
         <div class="w-6 h-px bg-gray-200"></div>
       </span>
    </div>

    {#if faqs.length > 0}
      <div class="mt-12 pt-8 border-t border-gray-100 flex flex-col gap-5">
         <div class="flex items-center gap-3 px-1">
            <div class="w-9 h-9 rounded-xl bg-orange-500/10 flex items-center justify-center border border-orange-500/20">
               <MessageCircleQuestion size={20} class="text-orange-500" />
            </div>
            <div class="flex flex-col">
               <h4 class="text-[14px] font-black uppercase tracking-widest text-gray-900 leading-tight">FAQ_SCHEMA_CORE</h4>
               <span class="text-[8px] text-gray-400 font-bold uppercase tracking-widest">Hỗ trợ trích dẫn bởi AI Search 2026</span>
            </div>
         </div>
         <div class="space-y-3">
            {#each faqs as faq, i}
               <div 
                 class="bg-gray-50/80 backdrop-blur-sm rounded-2xl p-4 border border-gray-100/50 shadow-sm group active:scale-[0.98] transition-all"
                 in:fly={{ y: 20, delay: i * 100 }}
               >
                  <div class="flex items-start gap-3">
                     <span class="w-5 h-5 rounded-md bg-white border border-gray-100 flex items-center justify-center text-[9px] font-black text-orange-500 shrink-0 shadow-sm">{i + 1}</span>
                     <div class="flex flex-col gap-2">
                        <p class="text-[13px] font-black text-gray-900 leading-tight">{faq.question}</p>
                        <div class="h-px w-6 bg-orange-500/20"></div>
                        <p class="text-[12px] text-gray-500 leading-relaxed font-medium">{faq.answer}</p>
                     </div>
                  </div>
               </div>
            {/each}
         </div>
      </div>
    {/if}
    {#if category}
      <div class="mt-6">
        <ProductMobileReviews product={category} entityType="CATEGORY" />
      </div>
    {/if}
  </div>
</div>

<BottomSheet title="Bộ Lọc Tìm Kiếm" bind:active={isFilterDrawerOpen}>
  <div class="flex flex-col gap-8 pb-32">
     <section>
        <h4 class="text-[14px] font-bold text-gray-800 mb-4 px-1">Dịch vụ & Khuyến mãi</h4>
        <div class="flex flex-wrap gap-2 px-1">
          {#each servicesList as service}
            <button onclick={() => toggleService(service)} class="px-4 py-2.5 rounded-xl text-[13px] font-bold border transition-all {selectedServices.includes(service) ? 'border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/5 text-[var(--color-brand-primary)]' : 'bg-gray-50 text-gray-600 border-transparent'}">{service}</button>
          {/each}
        </div>
     </section>
     <section>
        <h4 class="text-[14px] font-bold text-gray-800 mb-4 px-1">Khoảng giá</h4>
        <div class="flex items-center gap-3 px-1">
          <div class="flex-1 bg-gray-50 rounded-xl flex items-center px-4 py-3 border border-transparent"><input type="number" placeholder="Từ" bind:value={minPrice} class="w-full text-[13px] font-bold bg-transparent outline-none" /><span class="text-gray-400 text-[13px] ml-1">₫</span></div>
          <div class="w-3 h-0.5 bg-gray-200"></div>
          <div class="flex-1 bg-gray-50 rounded-xl flex items-center px-4 py-3 border border-transparent"><input type="number" placeholder="Đến" bind:value={maxPrice} class="w-full text-[13px] font-bold bg-transparent outline-none" /><span class="text-gray-400 text-[13px] ml-1">₫</span></div>
        </div>
     </section>
     {#if availableBrands().length > 0}
      <section>
        <h4 class="text-[14px] font-bold text-gray-800 mb-4 px-1">Thương hiệu</h4>
        <div class="flex flex-wrap gap-2 px-1">
          {#each availableBrands() as brand}
            <button onclick={() => toggleBrand(brand)} class="px-5 py-2.5 rounded-xl text-[13px] font-bold border transition-all {selectedBrands.includes(brand) ? 'border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/5 text-[var(--color-brand-primary)]' : 'bg-gray-50 text-gray-600 border-transparent'}">{brand}</button>
          {/each}
        </div>
      </section>
     {/if}
  </div>
  <div class="mt-auto pt-4 pb-0 flex items-center gap-4 bg-white sticky bottom-0 z-10 border-t border-gray-100">
    <button onclick={clearFilters} class="flex-1 py-4 bg-gray-50 text-gray-600 text-[14px] font-black uppercase tracking-widest rounded-2xl">Xóa</button>
    <button onclick={() => isFilterDrawerOpen = false} class="flex-2 w-[65%] py-4 bg-black text-white text-[14px] font-black uppercase tracking-widest rounded-2xl shadow-xl">Áp dụng</button>
  </div>
</BottomSheet>

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
