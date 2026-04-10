<script lang="ts">
  import { goto } from '$app/navigation';
  import { slugify } from '$lib/utils/format';
  import { fly } from 'svelte/transition';

  interface Product {
    id: string;
    name: string;
    price: number;
    image: string;
    sales?: number;
    originalPrice?: number;
    rating?: number;
    ratingCount?: number;
    isAiFeatured?: boolean;
    createdAt?: string;
  }

  interface Props {
    products: Product[];
  }

  let { products = [] }: Props = $props();

  let activeTab = $state('BEST_SELLER');

  // Logic Sắp xếp Phản xạ (Elite V2.2)
  const sortedProducts = $derived.by(() => {
    let list = [...products];
    switch (activeTab) {
      case 'AI':
        return list.sort((a, b) => Number(b.isAiFeatured || 0) - Number(a.isAiFeatured || 0));
      case 'LATEST':
        return list.sort((a, b) => (b.createdAt || '').localeCompare(a.createdAt || '') || b.id.localeCompare(a.id));
      case 'POPULAR':
        return list.sort((a, b) => (b.rating || 0) - (a.rating || 0) || (b.ratingCount || 0) - (a.ratingCount || 0));
      case 'BEST_SELLER':
      default:
        return list.sort((a, b) => (b.sales || 0) - (a.sales || 0));
    }
  });

  const tabs = [
    { id: 'AI', label: 'GỢI Ý AI', icon: 'sparkles', color: '#FFD700' },
    { id: 'LATEST', label: 'MỚI NHẤT', icon: 'clock', color: '#64748b' },
    { id: 'POPULAR', label: 'PHỔ BIẾN', icon: 'flame', color: '#ff4d4d' },
    { id: 'BEST_SELLER', label: 'BÁN CHẠY', icon: 'trophy', color: '#FFD700' }
  ];
</script>

<!-- GRID HEADER (Viral 2026 Tabs) -->
<div class="mb-4 bg-[#f8f9fa]/80 backdrop-blur-md rounded-2xl border border-white/50 shadow-sm overflow-hidden sticky top-[env(safe-area-inset-top,0px)] z-40">
  <div class="flex items-center justify-between px-4 lg:px-6">
    <div class="flex items-center gap-2 lg:gap-8 overflow-x-auto no-scrollbar py-3">
      {#each tabs as tab}
        <button
          onclick={() => activeTab = tab.id}
          class="group relative flex items-center gap-2 px-3 py-2 transition-all duration-300 whitespace-nowrap"
        >
          <!-- Icon Contextual -->
          <div class="w-5 h-5 flex items-center justify-center transition-transform group-hover:scale-110" style:color={tab.color}>
            {#if tab.icon === 'sparkles'}
              <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4"><path d="M12 2l1.5 5h5l-4 3 1.5 5-4-3-4 3 1.5-5-4-3h5z"/></svg>
            {:else if tab.icon === 'clock'}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            {:else if tab.icon === 'flame'}
              <svg viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4"><path d="M12 2c0 0-2 4-2 7 0 2.2 1.8 4 4 4s4-1.8 4-4c0-3-2-7-2-7" opacity="0.5"/><path d="M12 6c0 0-2 3-2 5 0 1.1 0.9 2 2 2s2-0.9 2-2c0-2-2-5-2-5"/></svg>
            {:else if tab.icon === 'trophy'}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M6 9H4.5a2.5 2.5 0 010-5H6M18 9h1.5a2.5 2.5 0 000-5H18M4.22 19.78a11 11 0 0015.56 0M12 15V21M8 21h8"/></svg>
            {/if}
          </div>
          
          <span 
            class="text-[11px] lg:text-[13px] font-extrabold tracking-widest transition-colors duration-300 uppercase"
            class:text-[#222]={activeTab === tab.id}
            class:text-gray-400={activeTab !== tab.id}
          >
            {tab.label}
          </span>

          {#if activeTab === tab.id}
            <div 
              class="absolute bottom-0 left-0 right-0 h-[3px] bg-gradient-to-r from-yellow-400 to-amber-500 rounded-full"
              in:fly={{ y: 2, duration: 300 }}
            ></div>
          {/if}
        </button>
      {/each}
    </div>

    <!-- Luxury Badge Badge -->
    <div class="hidden lg:flex items-center pl-4 border-l border-gray-100">
      <div class="px-4 py-1.5 rounded-full bg-gradient-to-r from-[#fafafa] to-white border border-[#eee] shadow-sm hover:shadow-md transition-all cursor-pointer group">
         <span class="text-[10px] font-black tracking-[0.2em] text-[#8b6e4e] uppercase group-hover:text-[#6a5237]">Luxury Collection 2026</span>
      </div>
    </div>
  </div>
</div>

<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
  {#each sortedProducts as product (product.id)}
    <a
      href={`/${slugify(product.name)}`}
      class="group/card relative bg-white border border-gray-100 hover:border-[#ee4d2d] transition-all duration-300 cursor-pointer flex flex-col active:scale-[0.98] shadow-sm hover:shadow-xl overflow-hidden no-underline"
      in:fly={{ y: 20, duration: 600, delay: 100 }}
    >
      <!-- IMAGE ZONE -->
      <div class="aspect-square w-full relative overflow-hidden bg-[#fafafa]">
        <!-- Flash Sale / Discount Tag -->
        <div class="absolute top-0 right-0 z-20">
          <div class="bg-[#ffd839] text-[#ee4d2d] text-[10px] font-black px-1.5 py-1 uppercase flex flex-col items-center leading-none relative">
            <span>-35%</span>
            <span class="text-[8px] mt-0.5 opacity-80">GIẢM</span>
            <!-- Bottom notch for Shopee style tag -->
            <div class="absolute -bottom-1 inset-x-0 h-1 bg-[#ffd839] [clip-path:polygon(0%_0%,50%_100%,100%_0%)]"></div>
          </div>
        </div>

        {#if product.sales && product.sales > 1000}
           <div class="absolute top-2 left-2 z-20">
              <span class="bg-[#ee4d2d] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-sm uppercase tracking-tighter">Bán chạy</span>
           </div>
        {/if}

        <img
          src={product.image}
          alt={product.name}
          class="w-full h-full object-cover transition-transform duration-500 group-hover/card:scale-105"
          loading="lazy"
        />
      </div>

      <!-- CONTENT ZONE -->
      <div class="p-3 flex flex-col flex-1 bg-white">
        <h3 class="text-gray-800 text-[12px] font-medium leading-normal line-clamp-2 h-[34px] mb-2 group-hover/card:text-[#ee4d2d] transition-colors">
          {product.name}
        </h3>

        <div class="mt-auto space-y-2">
          <!-- Price Section -->
          <div class="flex flex-col">
            <div class="flex items-center gap-1.5 h-4">
              <span class="text-[11px] text-gray-400 line-through tabular-nums decoration-gray-300">
                ₫{Math.round(product.originalPrice || product.price * 1.55).toLocaleString('vi-VN')}
              </span>
            </div>
            <p class="text-[#ee4d2d] font-bold text-lg tabular-nums flex items-baseline gap-0.5">
              <span class="text-sm font-medium">₫</span>{product.price.toLocaleString('vi-VN')}
            </p>
          </div>

          <!-- Bottom Footer Info -->
          <div class="pt-2 border-t border-gray-50 flex items-center justify-between">
            <div class="flex items-center gap-1 text-[#ffac33]">
               <svg class="w-2.5 h-2.5 fill-current" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
               <span class="text-[9px] font-bold text-gray-400">{product.rating || 5}</span>
            </div>
            <span class="text-[10px] text-gray-400 font-medium">Đã bán {product.sales || 0}</span>
          </div>
        </div>
      </div>
      
      <!-- Hover Interaction Background -->
      <div class="absolute inset-0 border-2 border-[#ee4d2d] opacity-0 group-hover/card:opacity-100 transition-opacity pointer-events-none z-30"></div>
    </a>
  {/each}
</div>

<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  /* Kỹ thuật Sticky Elite V2.2 */
  :global(.grid-header-sticky) {
    top: calc(var(--header-height, 60px) + 1px);
  }

  /* Hiệu ứng hover cho Tab */
  button {
    -webkit-tap-highlight-color: transparent;
  }
</style>
