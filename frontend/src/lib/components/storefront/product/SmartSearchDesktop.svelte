<script lang="ts">
  import { tick, untrack } from 'svelte';
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { trimProductName, formatCurrency } from '$lib/utils/format';
  import { fade, fly } from 'svelte/transition';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';

  const searchStore = getSearchStore();
  const isNewsContext = $derived(page.data.type === 'news' || page.url.pathname.includes('/tin-tuc'));
  const contextPlaceholder = $derived(
    page.data.product?.name 
      ? `Tìm "${page.data.product.name}"...` 
      : searchStore.searchPlaceholder
  );

  let isFocused = $state(false);
  let containerElement = $state<HTMLElement>();
  let inputElement = $state<HTMLInputElement>();
  let localQuery = $state(searchStore.searchQuery);
  let searchTimer: ReturnType<typeof setTimeout>;

  // Sync store -> local
  $effect(() => {
    const storeVal = searchStore.searchQuery;
    untrack(() => {
      if (storeVal !== localQuery) localQuery = storeVal;
    });
  });

  // Debounced Search
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
    isFocused = false;
    goto(`/products?q=${encodeURIComponent(term.trim())}`);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') commitSearch(localQuery);
    if (e.key === 'Escape') isFocused = false;
  }

  // Focus management
  $effect(() => {
    if (isFocused && inputElement) {
      tick().then(() => inputElement?.focus());
    }
  });

  // Click outside
  $effect(() => {
    if (!isFocused) return;
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerElement && !containerElement.contains(e.target as Node)) {
        isFocused = false;
      }
    };
    const timeout = setTimeout(() => window.addEventListener('click', handleOutsideClick), 0);
    return () => {
      clearTimeout(timeout);
      window.removeEventListener('click', handleOutsideClick);
    };
  });
</script>

<div bind:this={containerElement} class="w-full relative group" style:z-index={Z_INDEX_CLIENT.HEADER + 1}>
  <!-- SEARCH BAR -->
  <div class="w-full flex items-center bg-white border border-gray-100 transition-all duration-300 relative group/s-bar shadow-sm hover:border-luxury-copper/30">
    <input
      bind:this={inputElement}
      type="search"
      bind:value={localQuery}
      onfocus={() => isFocused = true}
      onkeydown={handleKeyDown}
      placeholder={contextPlaceholder}
      class="flex-grow h-[40px] pl-4 pr-10 text-[14px] text-gray-800 bg-transparent focus:outline-none placeholder:text-gray-400/40 font-medium"
    />
    
    {#if localQuery}
      <button 
        onclick={() => { localQuery = ''; searchStore.searchQuery = ''; inputElement?.focus(); }}
        class="absolute right-12 top-1/2 -translate-y-1/2 text-gray-300 hover:text-luxury-copper p-1"
      >
        <svg class="w-4 h-4 bg-gray-200 text-white rounded-full p-[2px]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>
    {/if}

    <button 
      onclick={() => commitSearch(localQuery)}
      class="bg-luxury-copper w-12 h-10 flex items-center justify-center text-white hover:bg-[#A67B6C] transition-all shrink-0"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
    </button>
  </div>

  <!-- DROPDOWN LAYER -->
  {#if isFocused && (searchStore.searchQuery ? true : (searchStore.recentSearches.length > 0 || searchStore.featuredProducts.length > 0))}
    <div 
      in:fly={{ y: 5, duration: 200 }}
      class="absolute top-full left-0 w-full bg-white shadow-[0_20px_60px_rgba(0,0,0,0.15)] border border-gray-100 mt-1 py-4 overflow-hidden"
    >
      {#if searchStore.isSearching}
        <div class="h-0.5 w-full bg-gradient-to-r from-transparent via-luxury-copper to-transparent animate-scanning"></div>
      {/if}

      <div class="max-h-[500px] overflow-y-auto px-4 flex flex-col gap-6 scrollbar-thin">
        {#if !searchStore.searchQuery}
          <!-- EMPTY STATE: HISTORY & TRENDS -->
          {#if searchStore.recentSearches.length > 0}
            <section>
              <div class="flex items-center justify-between mb-3">
                <span class="text-[10px] font-black tracking-widest text-gray-400 uppercase">Lịch sử</span>
                <button onclick={() => searchStore.clearHistory()} class="text-[10px] font-bold text-luxury-copper hover:underline">Xóa tất cả</button>
              </div>
              <div class="flex flex-wrap gap-2">
                {#each searchStore.recentSearches as item}
                  <button onclick={() => commitSearch(item)} class="px-3 py-1.5 bg-gray-50 hover:bg-luxury-copper/10 hover:text-luxury-copper text-gray-600 text-[12px] font-medium transition-all flex items-center gap-2 group">
                    {item}
                    <span onclick={(e) => { e.stopPropagation(); searchStore.removeSearch(item); }} class="opacity-0 group-hover:opacity-100 ml-1">✕</span>
                  </button>
                {/each}
              </div>
            </section>
          {/if}

          {#if searchStore.featuredProducts.length > 0}
            <section>
              <div class="flex items-center gap-2 mb-3">
                <span class="w-1.5 h-1.5 bg-[#fe2c55] rounded-full animate-pulse"></span>
                <span class="text-[10px] font-black tracking-widest text-gray-400 uppercase">Xu hướng tìm kiếm</span>
              </div>
              <div class="grid grid-cols-2 gap-3">
                {#each searchStore.featuredProducts as p}
                  <button onclick={() => commitSearch(p.name)} class="flex items-center p-2 hover:bg-gray-50 transition-all text-left">
                    <div class="w-10 h-10 shrink-0 bg-white border border-gray-100 p-1">
                      <img src={p.images?.[0] ?? p.metadata?.image_url} alt="" class="w-full h-full object-contain mix-blend-multiply" />
                    </div>
                    <div class="ml-2 min-w-0">
                      <div class="text-[13px] font-bold text-gray-700 truncate">{trimProductName(p.name)}</div>
                      <div class="text-[11px] font-black text-black">{formatCurrency(p.discountPrice ?? p.price)}</div>
                    </div>
                  </button>
                {/each}
              </div>
            </section>
          {/if}
        {:else}
          <!-- SEARCH RESULTS -->
          {#if searchStore.searchResults.length > 0}
            <section>
              <div class="text-[10px] font-black tracking-widest text-luxury-copper mb-3 uppercase">Sản phẩm</div>
              <div class="flex flex-col gap-1">
                {#each searchStore.searchResults as p}
                  <a href="/{p.slug}" onclick={() => { searchStore.addSearch(p.name); isFocused = false; }} class="flex items-center gap-4 p-2 hover:bg-gray-50 transition-colors group">
                    <div class="w-12 h-12 shrink-0 bg-white border border-gray-100 p-1">
                      <img src={p.images?.[0]} alt="" class="w-full h-full object-contain mix-blend-multiply" />
                    </div>
                    <div class="flex-grow min-w-0">
                      <h4 class="text-[14px] font-bold text-gray-800 truncate">{trimProductName(p.name)}</h4>
                      <div class="text-[13px] font-black text-black">{formatCurrency(p.discountPrice ?? p.price)}</div>
                    </div>
                  </a>
                {/each}
              </div>
            </section>
          {/if}

          {#if searchStore.searchArticleResults.length > 0}
            <section>
              <div class="text-[10px] font-black tracking-widest text-luxury-copper mb-3 uppercase">Kiến thức chuyên sâu</div>
              <div class="flex flex-col gap-2">
                {#each searchStore.searchArticleResults as art}
                  <a href="/{art.slug}" onclick={() => { searchStore.addSearch(art.title); isFocused = false; }} class="flex items-center gap-4 p-2 hover:bg-gray-50 transition-colors group">
                    <div class="w-14 h-14 shrink-0 bg-gray-100 overflow-hidden">
                      <img src={art.featuredImage} alt="" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                    </div>
                    <div class="flex-grow min-w-0">
                      <div class="text-[9px] font-black text-luxury-copper mb-1">{art.category}</div>
                      <h4 class="text-[14px] font-bold text-gray-800 line-clamp-2 leading-snug">{art.title}</h4>
                    </div>
                  </a>
                {/each}
              </div>
            </section>
          {/if}

          {#if searchStore.searchResults.length === 0 && searchStore.searchArticleResults.length === 0 && !searchStore.isSearching}
            <div class="py-10 text-center text-gray-400 font-bold italic">Không tìm thấy kết quả phù hợp</div>
          {/if}
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  @keyframes scanning {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  .animate-scanning { animation: scanning 1.5s linear infinite; }
</style>
