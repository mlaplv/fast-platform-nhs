<script lang="ts">
  import { tick, untrack } from 'svelte';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { trimProductName, formatCurrency } from '$lib/utils/format';
  import { fade, fly } from 'svelte/transition';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import Search from "@lucide/svelte/icons/search";
  import TrendingUp from "@lucide/svelte/icons/trending-up";
  import History from "@lucide/svelte/icons/history";
  import ChevronLeft from "@lucide/svelte/icons/chevron-left";
  import X from "@lucide/svelte/icons/x";
  import Zap from "@lucide/svelte/icons/zap";
  import Eye from "@lucide/svelte/icons/eye";

  const searchStore = getSearchStore();
  const contextPlaceholder = $derived(
    page.data.product?.name 
      ? `Tìm "${page.data.product.name}"...` 
      : searchStore.searchPlaceholder
  );

  let inputElement = $state<HTMLInputElement>();
  let localQuery = $state(searchStore.searchQuery);
  let searchTimer: ReturnType<typeof setTimeout>;


  $effect(() => {
    const storeVal = searchStore.searchQuery;
    untrack(() => {
      if (storeVal !== localQuery) localQuery = storeVal;
    });
  });

  $effect(() => {
    const query = localQuery;
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchStore.triggerSearch(query);
    }, 300);
    return () => clearTimeout(searchTimer);
  });

  function commitSearch(term: string) {
    if (!term.trim()) return;
    searchStore.searchQuery = term;
    searchStore.addSearch(term);
    searchStore.isOverlayOpen = false;
    goto(`/search?q=${encodeURIComponent(term.trim())}`);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') commitSearch(localQuery);
  }

  $effect(() => {
    if (typeof document !== 'undefined') {
      if (searchStore.isOverlayOpen) {
        document.body.style.overflow = 'hidden';
        searchStore.ensureFeaturedLoaded();
        if (inputElement) {
          tick().then(() => inputElement?.focus());
        }
      } else {
        document.body.style.overflow = '';
      }
    }
  });
</script>

{#if searchStore.isOverlayOpen}
  <div 
    in:fade={{ duration: 150 }}
    class="fixed inset-0 bg-white flex flex-col font-sans overflow-hidden"
    style:z-index={Z_INDEX_CLIENT.MODAL + 50}
  >
    <!-- INDUSTRIAL SHARP HEADER -->
    <header class="w-full px-[5px] pt-3 pb-1 flex items-center bg-white z-50 shrink-0 gap-1 border-b border-gray-100">
      <button 
        onclick={() => searchStore.isOverlayOpen = false} 
        class="w-10 h-10 flex items-center justify-center text-gray-900 active:bg-gray-50 transition-colors"
      >
        <ChevronLeft size={24} />
      </button>

      <div class="flex-grow h-10 bg-gray-100 flex items-center px-3 gap-2 relative">
        <Search size={16} class="text-gray-400 shrink-0 z-10" />
        <input
          bind:this={inputElement}
          bind:value={localQuery}
          type="text"
          onkeydown={handleKeyDown}
          placeholder={contextPlaceholder}
          class="flex-grow bg-transparent border-none outline-none text-[14px] font-bold text-gray-900 placeholder:text-gray-400 z-10"
        />
        {#if localQuery}
          <button onclick={() => { localQuery = ''; inputElement?.focus(); }} class="p-1 z-10">
            <X size={14} class="bg-gray-300 text-white rounded-full p-0.5" />
          </button>
        {/if}
      </div>
    </header>

    <!-- ULTRA-LEAN BODY -->
    <div class="flex-grow overflow-y-auto flex flex-col relative bg-white">
      {#if searchStore.isSearching}
        <div class="absolute top-0 left-0 right-0 h-0.5 z-50 overflow-hidden">
          <div class="h-full bg-gradient-to-r from-transparent via-luxury-copper to-transparent animate-scanning"></div>
        </div>
      {/if}

      <div class="flex flex-col px-[5px] py-2">
        {#if !localQuery}
          <!-- SHARP TRENDING RANKING -->
          <section class="mb-6">
            <div class="flex items-center justify-between mb-3 px-1">
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 bg-[#FF3B30] rounded-full animate-pulse shadow-sm"></div>
                <span class="text-[10px] font-black tracking-[0.2em] text-gray-400 ">Xu hướng bùng nổ</span>
              </div>
              <TrendingUp size={12} class="text-luxury-copper" />
            </div>

            {#if searchStore.featuredProducts.length > 0}
              <div class="grid grid-cols-1 gap-px bg-gray-100 border border-gray-100">
                {#each searchStore.featuredProducts as p, i}
                  <button 
                    onclick={() => commitSearch(p.name)} 
                    class="group relative flex items-center gap-3 p-3 bg-white active:bg-gray-50 transition-colors text-left"
                  >
                    <div class="w-16 h-16 shrink-0 bg-white p-1 border border-gray-50 relative">
                      <img src={p.images?.[0] ?? p.metadata?.image_url} alt={p.name} class="w-full h-full object-contain mix-blend-multiply" />
                      <div class="absolute -top-1 -right-1 w-5 h-5 bg-[#FF3B30] text-white text-[9px] font-black flex items-center justify-center border border-white">
                        {i + 1}
                      </div>
                    </div>

                    <div class="flex flex-col flex-grow min-w-0">
                      <h4 class="text-[13px] font-bold text-gray-900 line-clamp-1 mb-0.5 leading-tight">{trimProductName(p.name)}</h4>
                      <div class="flex items-center gap-3">
                        <span class="text-[15px] font-black text-luxury-copper tabular-nums">{formatCurrency(Number(p.discountPrice) || Number(p.price))}</span>
                        {#if p.discountPrice}
                          <span class="text-[10px] text-gray-300 line-through font-bold">{formatCurrency(p.price)}</span>
                        {/if}
                      </div>
                      <!-- Real DB Rating -->
                      {#if p.metadata?.reviews_trust_score}
                        <div class="flex items-center gap-1 mt-0.5">
                          <span class="text-[#FF5722] text-[10px] font-black leading-none tracking-[-0.05em]">★★★★★</span>
                          <span class="text-[10px] font-black text-[#FF5722] leading-none">{p.metadata.reviews_trust_score.toFixed(1)}</span>
                          {#if p.metadata.review_count}
                            <span class="text-[9px] text-gray-400 font-bold leading-none">&middot; {p.metadata.review_count}</span>
                          {/if}
                        </div>
                      {/if}
                      {#if p.views}
                        <div class="flex items-center gap-1.5 mt-1">
                          <Eye size={10} class="text-gray-400" />
                          <span class="text-[9px] font-bold text-gray-400">{p.views} người đang xem</span>
                        </div>
                      {:else if p.orderCount}
                        <div class="flex items-center gap-1.5 mt-1">
                          <Zap size={10} class="text-luxury-copper" />
                          <span class="text-[9px] font-bold text-gray-400">{p.orderCount} người đã mua</span>
                        </div>
                      {/if}
                    </div>
                    
                    <Zap size={14} class="text-luxury-copper/20" />
                  </button>
                {/each}
              </div>
            {/if}
          </section>

          <!-- SHARP HISTORY -->
          {#if searchStore.recentSearches.length > 0}
            <section class="mb-6">
              <div class="flex items-center justify-between mb-3 px-1">
                <div class="flex items-center gap-2">
                  <History size={12} class="text-gray-400" />
                  <span class="text-[10px] font-black tracking-[0.2em] text-gray-400 ">Tìm kiếm gần đây</span>
                </div>
                <button onclick={() => searchStore.clearHistory()} class="text-[10px] font-bold text-gray-300 hover:text-gray-900 transition-colors">Xóa sạch</button>
              </div>
              <div class="flex flex-wrap gap-1.5 px-1">
                {#each searchStore.recentSearches.slice(0, 10) as item}
                  <button 
                    onclick={() => commitSearch(item)} 
                    class="px-3 py-1.5 bg-gray-100 text-[12px] font-bold text-gray-600 hover:bg-gray-200 transition-colors"
                  >
                    {item}
                  </button>
                {/each}
              </div>
            </section>
          {/if}
        {:else}
          <!-- SHARP SEARCH RESULTS -->
          <div class="flex flex-col gap-5">
            {#if searchStore.searchResults.length > 0}
              <section>
                <div class="flex items-center gap-2 mb-3 px-1">
                   <div class="w-1.5 h-1.5 bg-luxury-copper rounded-full"></div>
                   <span class="text-[10px] font-black tracking-[0.2em] text-gray-400 ">Sản phẩm</span>
                </div>
                <div class="grid grid-cols-1 gap-px bg-gray-100 border border-gray-100">
                  {#each searchStore.searchResults as p}
                    <a 
                      href="/{p.slug}" 
                      onclick={() => { searchStore.addSearch(p.name); searchStore.isOverlayOpen = false; }} 
                      class="flex items-center gap-3 p-3 bg-white active:bg-gray-50 transition-colors"
                    >
                      <div class="w-16 h-16 shrink-0 bg-white p-1.5 border border-gray-50">
                        <img src={p.images?.[0]} class="w-full h-full object-contain mix-blend-multiply" alt={p.name} />
                      </div>
                      <div class="flex flex-col min-w-0">
                        <h4 class="text-[13px] font-bold text-gray-900 line-clamp-2 leading-tight mb-1">{p.name}</h4>
                        <div class="text-[15px] font-black text-luxury-copper tabular-nums">
                          {formatCurrency(Number(p.discountPrice) || Number(p.price))}
                        </div>
                        <!-- Real DB Rating -->
                        {#if p.metadata?.reviews_trust_score}
                          <div class="flex items-center gap-1 mt-0.5">
                            <span class="text-[#FF5722] text-[10px] font-black leading-none tracking-[-0.05em]">★★★★★</span>
                            <span class="text-[10px] font-black text-[#FF5722] leading-none">{p.metadata.reviews_trust_score.toFixed(1)}</span>
                            {#if p.metadata.review_count}
                              <span class="text-[9px] text-gray-400 font-bold leading-none">&middot; {p.metadata.review_count}</span>
                            {/if}
                          </div>
                        {/if}
                      </div>
                    </a>
                  {/each}
                </div>
              </section>
            {/if}

            {#if searchStore.searchArticleResults.length > 0}
              <section>
                <div class="flex items-center gap-2 mb-3 px-1">
                   <div class="w-1.5 h-1.5 bg-[#4CD964] rounded-full"></div>
                   <span class="text-[10px] font-black tracking-[0.2em] text-gray-400 ">Kiến thức chuyên gia</span>
                </div>
                <div class="flex flex-col gap-px bg-gray-100 border border-gray-100">
                  {#each searchStore.searchArticleResults as art}
                    <a 
                      href="/{art.slug}.html" 
                      onclick={() => { searchStore.addSearch(art.title); searchStore.isOverlayOpen = false; }} 
                      class="flex flex-col gap-3 p-4 bg-white active:bg-gray-50 transition-colors"
                    >
                      <div class="flex items-center gap-3">
                        <div class="w-14 h-14 shrink-0 bg-gray-50 border border-gray-100 overflow-hidden">
                          {#if art.featuredImage}
                            <img src={art.featuredImage} class="w-full h-full object-cover" alt={art.title} />
                          {/if}
                        </div>
                        <div class="flex-grow min-w-0">
                          <div class="text-[8px] font-black text-luxury-copper tracking-widest mb-0.5 ">{art.category}</div>
                          <h4 class="text-[14px] font-bold text-gray-900 leading-snug line-clamp-2 italic">{art.title}</h4>
                        </div>
                      </div>
                    </a>
                  {/each}
                </div>
              </section>
            {/if}

            {#if searchStore.searchResults.length === 0 && searchStore.searchArticleResults.length === 0 && !searchStore.isSearching}
              <div class="py-20 text-center flex flex-col items-center gap-3">
                <Search size={24} class="text-gray-200" />
                <span class="text-gray-300 font-black tracking-[0.2em] text-[10px] ">Không tìm thấy kết quả</span>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    </div>

    <!-- INDUSTRIAL TICKER -->
    <footer class="h-8 bg-gray-50 border-t border-gray-100 flex items-center overflow-hidden shrink-0">
       <div class="flex items-center gap-4 px-2 whitespace-nowrap animate-ticker">
          <span class="text-[8px] font-black text-luxury-copper tracking-widest ">Live Pulse</span>
          <span class="text-[9px] font-bold text-gray-400">Cộng đồng đang quan tâm đến Kem dưỡng trắng da cổ Miccosmo...</span>
          <span class="text-[9px] font-bold text-gray-400">Vừa có lượt mua mới tại Hà Nội...</span>
       </div>
    </footer>
  </div>
{/if}

<style>
  @keyframes scanning {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  .animate-scanning { animation: scanning 1.5s linear infinite; }

  @keyframes ticker {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
  }
  .animate-ticker { 
    animation: ticker 30s linear infinite;
    display: flex;
    width: fit-content;
  }
</style>

