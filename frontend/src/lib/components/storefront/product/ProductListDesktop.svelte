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
  type SortType = 'popular' | 'latest' | 'price-asc' | 'price-desc';
  let activeSort = $state<SortType>('popular');

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

  let displayProducts = $derived(() => {
    let result = [...enhancedProducts()];
    if (activeSort === 'price-asc') result.sort((a, b) => a.price - b.price);
    if (activeSort === 'price-desc') result.sort((a, b) => b.price - a.price);
    return result;
  });
</script>

<div class="bg-[#F5F5F5] min-h-screen pb-20">
  <!-- BREADCRUMB & TITLE BAR -->
  <div class="bg-white border-b border-gray-100">
    <div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-6">
      <!-- Breadcrumbs -->
      <nav class="flex items-center gap-2 text-[12px] text-gray-400 mb-4 font-medium">
        <a href="/" class="hover:text-[#ee4d2d] transition-colors">Trang chủ</a>
        <span>/</span>
        <a href="/danh-muc" class="hover:text-[#ee4d2d] transition-colors">Mỹ phẩm Làm Đẹp</a>
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

  <!-- HORIZONTAL FILTER DROPDAWNS -->
  <div class="bg-white border-b border-gray-100 sticky top-[var(--z-header)] z-[90]">
    <div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-3 flex items-center justify-between">
      <div class="flex items-center gap-1">
        <button class="px-5 py-2.5 bg-white border border-gray-100 text-[12px] font-bold text-gray-700 hover:border-[#ee4d2d] hover:text-[#ee4d2d] transition-all shadow-sm flex items-center gap-2">
          GIAO NHANH 2H <div class="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse"></div>
        </button>
        <button class="px-5 py-2.5 bg-white border border-gray-100 text-[12px] font-bold text-gray-700 hover:border-[#ee4d2d] hover:text-[#ee4d2d] transition-all shadow-sm">
          VOUCHER GIẢM SÂU
        </button>
        <button class="px-5 py-2.5 bg-white border border-gray-100 text-[12px] font-bold text-gray-700 hover:border-[#ee4d2d] hover:text-[#ee4d2d] transition-all shadow-sm">
          HÀNG CHÍNH HÃNG 
        </button>
      </div>
      
      <div class="flex items-center gap-6">
         <!-- Sort Toggle -->
         <div class="flex items-center gap-3">
            <span class="text-[12px] text-gray-400 font-medium">Sắp xếp theo:</span>
            <div class="flex border border-gray-100 bg-gray-50/50 p-1">
               <button 
                onclick={() => activeSort = 'popular'}
                class="px-3 py-1 text-[12px] font-bold transition-all {activeSort === 'popular' ? 'bg-white shadow-sm text-[#ee4d2d]' : 'text-gray-500 hover:text-gray-900'}">Phổ biến nhất</button>
               <button 
                onclick={() => activeSort = 'latest'}
                class="px-3 py-1 text-[12px] font-bold transition-all {activeSort === 'latest' ? 'bg-white shadow-sm text-[#ee4d2d]' : 'text-gray-500 hover:text-gray-900'}">Mới nhất</button>
            </div>
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
    <!-- LEFT SIDEBAR -->
    <aside class="w-[240px] shrink-0 space-y-4">
      <!-- Category List -->
      <div class="bg-white border border-gray-100 p-5 space-y-4 shadow-sm">
        <h3 class="text-[14px] font-black uppercase text-gray-900 pb-3 border-b border-gray-50 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg> Danh mục
        </h3>
        <div class="flex flex-col gap-2.5">
          <a href="#" class="text-[13px] font-black text-[#ee4d2d] flex items-center gap-2">
             <div class="w-1.5 h-1.5 bg-[#ee4d2d] rotate-45"></div> {categoryName} Mặt
          </a>
          <a href="#" class="text-[13px] font-medium text-gray-600 hover:text-[#ee4d2d] transition-colors pl-3.5 italic">
             {categoryName} Body
          </a>
        </div>
      </div>

      <!-- Filters Group -->
      <div class="bg-white border border-gray-100 p-5 space-y-6 shadow-sm">
        <!-- Price Range -->
        <div class="space-y-4">
          <h4 class="text-[12px] font-black uppercase tracking-wider text-gray-900 border-b border-gray-50 pb-2">Giá Sản Phẩm</h4>
          <div class="flex items-center gap-2">
            <input type="text" placeholder="₫ TỪ" class="w-full h-8 border border-gray-100 px-2 text-[11px] font-medium outline-none focus:border-[#ee4d2d]" />
            <div class="w-2 h-px bg-gray-300"></div>
            <input type="text" placeholder="₫ ĐẾN" class="w-full h-8 border border-gray-100 px-2 text-[11px] font-medium outline-none focus:border-[#ee4d2d]" />
          </div>
          <button class="w-full bg-[#ee4d2d] text-white text-[10px] font-black uppercase py-2 hover:brightness-110 active:scale-95 transition-all">Áp dụng</button>
        </div>

        <!-- Brands Checkbox -->
        <div class="space-y-4">
          <h4 class="text-[12px] font-black uppercase tracking-wider text-gray-900 border-b border-gray-50 pb-2">Thương Hiệu</h4>
          <div class="flex flex-col gap-2.5 max-h-[200px] overflow-y-auto no-scrollbar pr-2">
            {#each brands as brand}
              <label class="flex items-center gap-2.5 group cursor-pointer">
                <input type="checkbox" class="w-4 h-4 accent-[#ee4d2d] border-gray-200" />
                <span class="text-[12px] font-medium text-gray-600 group-hover:text-black transition-colors">{brand}</span>
              </label>
            {/each}
          </div>
          <button class="text-[11px] font-bold text-gray-400 hover:text-[#ee4d2d] flex items-center gap-1 mt-1 transition-colors">
             Xem thêm <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>
        </div>

        <!-- Origin Checkbox -->
        <div class="space-y-4">
          <h4 class="text-[12px] font-black uppercase tracking-wider text-gray-900 border-b border-gray-50 pb-2">Xuất Xứ</h4>
          <div class="flex flex-col gap-2.5">
            {#each origins as country}
              <label class="flex items-center gap-2.5 group cursor-pointer">
                <input type="checkbox" class="w-4 h-4 accent-[#ee4d2d] border-gray-200" />
                <span class="text-[12px] font-medium text-gray-600 group-hover:text-black transition-colors">{country}</span>
              </label>
            {/each}
          </div>
        </div>
      </div>
    </aside>

    <!-- RIGHT GRID AREA -->
    <main class="flex-1">
      <!-- Sorting & Info Bar -->
      <div class="bg-gray-100/50 p-3 mb-4 flex items-center justify-between">
         <div class="flex items-center gap-3">
            <span class="text-[12px] text-gray-500 font-medium">Sắp xếp theo:</span>
            <button class="px-5 py-2 bg-white text-[12px] font-bold text-[#ee4d2d] shadow-sm">Phổ biến nhất</button>
            <button class="px-5 py-2 text-[12px] font-medium text-gray-600 hover:bg-white/50 transition-all">Bán chạy</button>
            <button class="px-5 py-2 text-[12px] font-medium text-gray-600 hover:bg-white/50 transition-all">Mới nhất</button>
         </div>
         <div class="flex items-center gap-4">
            <span class="text-[12px] text-gray-400 font-medium">1/20</span>
            <div class="flex border border-gray-200 bg-white">
               <button class="p-2 opacity-30 cursor-not-allowed border-r border-gray-100 hover:bg-gray-50">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
               </button>
               <button class="p-2 hover:bg-gray-50">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
               </button>
            </div>
         </div>
      </div>

      <ProductGrid products={displayProducts()} />
    </main>
  </div>
</div>

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>