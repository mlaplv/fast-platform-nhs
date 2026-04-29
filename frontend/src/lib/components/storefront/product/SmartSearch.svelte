<script lang="ts">
  import { tick, untrack } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { trimProductName, formatCurrency } from '$lib/utils/format';
  import { isAdminDomain } from '$lib/state/nanobot/env';
  import { fade, fly, slide } from 'svelte/transition';
  import { Z_INDEX_CLIENT, Z_INDEX_ADMIN } from '$lib/core/constants/zIndex';

  let { variant = 'desktop' } = $props<{
    variant?: 'desktop' | 'mobile-overlay';
  }>();

  // Elite V2.2: Context-Aware Intelligence
  const isNewsContext = $derived($page.data.type === 'news' || $page.url.pathname.includes('/bai-viet') || $page.url.pathname.includes('/tin-tuc'));

  const searchStore = getSearchStore();

  let isFocused = $state(false);
  let containerElement = $state<HTMLElement>();
  let inputElement = $state<HTMLInputElement>();

  // Local state for immediate responsiveness
  let localQuery = $state(searchStore.searchQuery);
  let searchTimer: ReturnType<typeof setTimeout>;

  // Elite V2.2: Sync local input with store (important when navigating back/forth or direct URL access)
  // Use untrack so typing in localQuery doesn't trigger this effect to reset itself
  $effect(() => {
    const storeVal = searchStore.searchQuery;
    untrack(() => {
      if (storeVal !== localQuery) {
        localQuery = storeVal;
      }
    });
  });

  $effect(() => {
    // Elite V2.2: Read localQuery synchronously to establish Svelte 5 $effect tracking.
    // Reading inside setTimeout (async) would make $effect blind to changes.
    const query = localQuery;
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchStore.triggerSearch(query);
    }, 300);
    return () => clearTimeout(searchTimer);
  });

  function handleSearch(term: string) {
    if (!term.trim()) return;
    searchStore.searchQuery = term;
    searchStore.addSearch(term);
    isFocused = false;
    searchStore.isOverlayOpen = false;
  }

  function commitSearch(term: string) {
    if (!term.trim()) return;
    searchStore.searchQuery = term;
    searchStore.addSearch(term);
    isFocused = false;
    searchStore.isOverlayOpen = false;
    goto(`/products?q=${encodeURIComponent(term.trim())}`);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      commitSearch(localQuery);
    }
  }

  $effect(() => {
    if (variant === 'mobile-overlay' && searchStore.isOverlayOpen && inputElement) {
      tick().then(() => {
        if (inputElement) {
          inputElement.focus();
        }
      });
    }
  });

  $effect(() => {
    if (variant === 'desktop' && isFocused && inputElement) {
      tick().then(() => {
        if (inputElement) {
          inputElement.focus();
        }
      });
    }
  });

  // Click outside to close (Desktop)
  $effect(() => {
    if (variant !== 'desktop' || !isFocused) return;

    const handleOutsideClick = (e: MouseEvent) => {
      if (containerElement && !containerElement.contains(e.target as Node)) {
        isFocused = false;
      }
    };

    const timeout = setTimeout(() => {
      window.addEventListener('click', handleOutsideClick);
    }, 0);

    return () => {
      clearTimeout(timeout);
      window.removeEventListener('click', handleOutsideClick);
    };
  });

  // Viral 2026: Deterministic Social Proof
  function getHeatColor(count: number) {
    if (count > 20) return 'text-red-500';
    if (count > 10) return 'text-orange-500';
    return 'text-luxury-copper';
  }

  function getPseudoViews(id: string) {
    let hash = 0;
    for (let i = 0; i < id.length; i++) hash = (hash << 5) - hash + id.charCodeAt(i);
    return (Math.abs(hash) % 25) + 6; // 6-30 range
  }
</script>

{#if variant === 'desktop'}
  <div bind:this={containerElement} class="w-full relative group" style:z-index={Z_INDEX_CLIENT.HEADER + 1}>
    <div 
      class="w-full flex items-center bg-white rounded-none border border-gray-200 relative focus-within:border-luxury-copper transition-all shadow-sm focus-within:shadow-md"
      style:z-index={Z_INDEX_CLIENT.HEADER + 2}
    >
      <input
        bind:this={inputElement}
        type="search"
        role="searchbox"
        name="q"
        autocomplete="off"
        bind:value={localQuery}
        onfocus={() => isFocused = true}
        onclick={(e) => { e.stopPropagation(); isFocused = true; }}
        onkeydown={handleKeyDown}
        placeholder={searchStore.searchPlaceholder}
        class="flex-grow h-[42px] pl-[15px] pr-10 text-[15px] text-gray-800 bg-transparent focus:outline-none placeholder:text-gray-300 font-bold pointer-events-auto relative transition-all"
        style:z-index={Z_INDEX_CLIENT.HEADER + 3}
      />
      {#if localQuery}
        <button 
          onclick={() => { 
            localQuery = ''; 
            searchStore.searchQuery = ''; 
            inputElement?.focus(); 
          }}
          class="absolute right-[88px] top-1/2 -translate-y-1/2 text-gray-300 hover:text-[#fe2c55] transition-colors p-1 group/clear"
          style:z-index={Z_INDEX_CLIENT.HEADER + 4}
        >
          <svg class="w-[18px] h-[18px] bg-gray-200 group-hover/clear:bg-[#fe2c55] text-white rounded-full p-[3px] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      {/if}
      <button 
        onclick={() => commitSearch(localQuery)}
        class="bg-gradient-to-br from-luxury-copper to-luxury-peach min-w-[80px] h-[42px] flex items-center justify-center rounded-none hover:brightness-110 active:scale-95 transition-all shadow-lg"
        aria-label="Tìm kiếm"
      >
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      </button>
    </div>

    <!-- Smart Dropdown Layer -->
    {#if isFocused && (searchStore.searchQuery ? true : (searchStore.recentSearches.length > 0 || searchStore.featuredProducts.length > 0))}
      <div 
        in:fly={{ y: 5, duration: 300 }}
        class="absolute top-full left-0 w-full bg-white shadow-[0_20px_100px_rgba(0,0,0,0.5)] border border-gray-100 overflow-hidden"
        style:z-index={Z_INDEX_CLIENT.HEADER + 1}
      >
        <!-- Viral Scanning Progress (Elite V2.2) -->
        {#if searchStore.isSearching}
          <div class="h-0.5 w-full bg-gradient-to-r from-transparent via-luxury-copper to-transparent animate-scanning opacity-70"></div>
        {/if}
        
        <div class="flex flex-col p-4 gap-6 max-h-[600px] overflow-y-auto scrollbar-thin">
          
          <!-- Case 1: Empty Search -->
          {#if !searchStore.searchQuery}
            <!-- History Section -->
            {#if searchStore.recentSearches.length > 0}
              <section>
                <div class="flex items-center justify-between mb-3">
                  <span class="text-[10px] font-black uppercase tracking-widest text-gray-400">Lịch sử tìm kiếm</span>
                  <button onclick={() => searchStore.clearHistory()} class="text-[10px] font-bold text-luxury-copper hover:underline">Xóa tất cả</button>
                </div>
                <div class="flex flex-wrap gap-2">
                  {#each searchStore.recentSearches as item}
                    <button 
                      onclick={() => commitSearch(item)}
                      class="px-3 py-1.5 bg-gray-50 hover:bg-luxury-copper/10 hover:text-luxury-copper text-gray-600 text-[12px] font-medium transition-all flex items-center gap-2"
                    >
                      {item}
                      <span onclick={(e) => { e.stopPropagation(); searchStore.removeSearch(item); }} class="opacity-30 hover:opacity-100">✕</span>
                    </button>
                  {/each}
                </div>
              </section>
            {/if}

              <section>
                <div class="flex items-center gap-2 mb-4 px-2">
                  <span class="w-1.5 h-1.5 bg-[#fe2c55] rounded-full animate-pulse"></span>
                  <span class="text-[10px] font-black uppercase tracking-widest text-gray-400">Xu hướng tìm kiếm</span>
                </div>
                <div class="grid grid-cols-2 gap-x-6 gap-y-0.5 px-0">
                  {#each searchStore.featuredProducts as p, i}
                    <button 
                      onclick={() => commitSearch(p.name)}
                      class="flex items-center text-left group px-2 py-1.5 hover:bg-gray-50/50 transition-all rounded-none min-w-0"
                    >
                      <div class="w-9 h-9 shrink-0 rounded-sm overflow-hidden bg-gray-50 border border-gray-100 group-hover:scale-110 transition-transform">
                        {#if p.images?.length > 0 || p.metadata?.image_url}
                          <img src={p.images?.[0] ?? p.metadata?.image_url} alt={p.name} class="w-full h-full object-contain mix-blend-multiply" loading="lazy" />
                        {/if}
                      </div>
                      <div class="flex flex-col ml-1.5 flex-grow min-w-0">
                        <span class="text-[13px] font-bold text-gray-700 group-hover:text-[#fe2c55] line-clamp-1 transition-colors leading-tight">
                          {trimProductName(p.name)}
                        </span>
                         <div class="flex items-center gap-2">
                            <span class="text-[11px] text-black font-black">
                              {formatCurrency(p.discountPrice ?? p.price)}
                            </span>
                            {#if p.discountPrice}
                              <span class="text-[9px] text-gray-300 line-through font-bold">{formatCurrency(p.price)}</span>
                            {/if}
                         </div>
                      </div>
                      {#if p.metadata?.is_bestseller || p.orderCount > 50}
                        <span class="shrink-0 text-[8px] bg-[#fe2c55] text-white px-1 py-0.5 font-black uppercase tracking-tighter rounded-xs shadow-sm ml-1">Bán chạy</span>
                      {/if}
                    </button>
                  {/each}
                </div>
              </section>
          {:else}
            <!-- Case 2: Suggestions (Products & News) -->
            <section class="flex flex-col gap-6">
              {#if searchStore.isSearching}
                 <div class="py-10 text-center flex flex-col items-center gap-3">
                    <div class="w-6 h-6 border-2 border-luxury-copper/20 border-t-luxury-copper rounded-full animate-spin"></div>
                    <span class="text-gray-400 text-[11px] font-bold uppercase tracking-widest">Đang trích xuất dữ liệu...</span>
                 </div>
              {:else}
                <!-- Dynamic Re-ordering -->
                {#if isNewsContext}
                   {#if searchStore.searchArticleResults.length === 0 && searchStore.searchQuery}
                      <div class="px-4 py-8 text-center bg-gray-50/50 border border-dashed border-gray-200 rounded-none mb-4">
                         <div class="text-[11px] font-black uppercase tracking-[0.2em] text-luxury-copper opacity-60 mb-2">Thông tin bối cảnh</div>
                         <div class="text-[14px] font-bold text-gray-400 italic">Không tìm thấy kiến thức phù hợp với từ khóa của bạn.</div>
                      </div>
                   {/if}
                   {@render articleResults()}
                   {@render productResults()}
                {:else}
                   {@render productResults()}
                   {@render articleResults()}
                {/if}

                {#if searchStore.searchResults.length === 0 && searchStore.searchArticleResults.length === 0}
                  <div class="py-20 text-center px-10">
                    <span class="text-gray-300 font-bold uppercase tracking-widest text-[13px]">Không tìm thấy kết quả phù hợp.</span>
                  </div>
                {/if}
              {/if}
            </section>
          {/if}

          <!-- Desktop Snippets -->
          {#snippet productResults()}
             {#if searchStore.searchResults.length > 0}
                <div class="flex flex-col gap-1">
                  <div class="text-[10px] font-black uppercase tracking-widest text-[#C18F7E] mb-2 px-2">{isNewsContext ? 'Sản phẩm liên quan' : 'Sản phẩm dành cho bạn'}</div>
                  {#each searchStore.searchResults as p}
                    <a 
                      href="/{p.slug}"
                      onclick={() => { 
                        searchStore.addSearch(p.name);
                        isFocused = false; 
                        searchStore.isOverlayOpen = false; 
                      }}
                      class="px-4 py-3 bg-white hover:bg-gray-50 flex items-start gap-4 border-b border-gray-100 transition-colors group"
                    >
                      <div class="w-16 h-16 flex-shrink-0 relative overflow-hidden bg-white">
                        {#if p.images?.[0]}
                           <img src={p.images[0]} class="w-full h-full object-contain mix-blend-multiply" alt={p.name} />
                        {/if}
                      </div>
                      <div class="flex flex-col flex-grow min-w-0">
                        <h4 class="text-[15px] font-bold text-gray-800 line-clamp-1 mb-1">{trimProductName(p.name)}</h4>
                        <div class="text-[14px] font-black text-black tabular-nums">
                          {formatCurrency(p.discountPrice ?? p.price)}
                        </div>
                      </div>
                    </a>
                  {/each}
                </div>
             {/if}
          {/snippet}

          {#snippet articleResults()}
             {#if searchStore.searchArticleResults.length > 0}
                <div class="flex flex-col gap-1">
                  <div class="text-[10px] font-black uppercase tracking-widest text-[#C18F7E] mb-2 px-2">{isNewsContext ? 'Kết quả kiến thức hàng đầu' : 'Kiến thức chuyên sâu'}</div>
                  {#each searchStore.searchArticleResults as art}
                    <a 
                      href="/{art.slug}"
                      onclick={() => { 
                        searchStore.addSearch(art.title); 
                        isFocused = false; 
                        searchStore.isOverlayOpen = false; 
                      }}
                      class="px-4 py-4 bg-white hover:bg-gray-50 flex items-start gap-5 border-b border-gray-100 transition-all group"
                    >
                      <div class="w-20 h-20 flex-shrink-0 relative overflow-hidden bg-gray-100 rounded-sm">
                        {#if art.featuredImage}
                          <img src={art.featuredImage} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" alt={art.title} />
                        {/if}
                      </div>
                      <div class="flex flex-col flex-grow min-w-0">
                        <div class="flex items-center justify-between mb-1.5">
                           <span class="text-[9px] font-black text-[#C18F7E] uppercase tracking-wider">{art.category}</span>
                           {#if art.match_score}
                              <span class="text-[9px] font-bold text-green-500 bg-green-50 px-1.5 py-0.5 rounded-none">{Math.round(art.match_score * 100)}% Match</span>
                           {/if}
                        </div>
                        <h4 class="text-[16px] font-bold text-gray-900 group-hover:text-luxury-copper transition-colors uppercase italic leading-snug line-clamp-2">{art.title}</h4>
                      </div>
                    </a>
                  {/each}
                </div>
             {/if}
          {/snippet}

          <!-- Visual Product Preview (Elite Touch) — chỉ hiện khi không search -->
          {#if !searchStore.searchQuery && searchStore.featuredProducts.length > 0}
            <section class="border-t border-gray-50 pt-4">
              <div class="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-3">Có thể bạn quan tâm</div>
              <div class="flex gap-4 overflow-x-auto pb-2 -mx-1 px-1 no-scrollbar">
                {#each searchStore.featuredProducts.slice(0, 4) as p}
                  <a href="/{p.slug}" class="min-w-[120px] max-w-[120px] flex flex-col gap-2 group cursor-pointer" onclick={() => searchStore.isOverlayOpen = false}>
                    <div class="aspect-square bg-gray-100 relative overflow-hidden rounded">
                       {#if p.images?.length > 0 || p.metadata?.image_url}
                          <img src={p.images?.[0] ?? p.metadata?.image_url} alt={p.name} class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" loading="lazy" />
                       {/if}
                    </div>
                    <div class="text-[12px] font-bold line-clamp-2 leading-tight" title={p.name}>{trimProductName(p.name)}</div>
                  </a>
                {/each}
              </div>
            </section>
          {/if}
        </div>
      </div>
    {/if}
  </div>

{:else if variant === 'mobile-overlay' && searchStore.isOverlayOpen}
  <div 
    in:fade={{ duration: 150 }} 
    class="fixed inset-0 bg-white flex flex-col font-sans"
    style:z-index={Z_INDEX_CLIENT.MODAL + 10}
  >
    <header class="w-full px-2 py-2 flex items-center bg-white z-20 relative border-b border-gray-50/50 h-12">
      <button onclick={() => searchStore.isOverlayOpen = false} class="p-1 -ml-1 text-gray-900 active:scale-90 transition-transform">
        <svg class="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
      </button>

      <div class="search-ring-mobile flex-grow ml-1">
        <div class="search-inner-mobile">
          <svg class="w-[18px] h-[18px] flex-shrink-0 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            bind:this={inputElement}
            bind:value={localQuery}
            type="text"
            onkeydown={handleKeyDown}
            placeholder={searchStore.searchPlaceholder}
            class="search-input-mobile"
          />
          {#if localQuery}
            <button onclick={() => { localQuery = ''; inputElement?.focus(); }} class="search-clear-mobile">
              <svg class="w-4 h-4 bg-gray-200 text-white rounded-full p-[2px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          {/if}
        </div>
      </div>
    </header>

    <div class="flex-grow overflow-y-auto bg-white flex flex-col pb-10">
      {#if !localQuery}
        <!-- History / Trends -->
        {#if searchStore.recentSearches.length > 0}
          <div class="flex flex-col mb-4">
             {#each searchStore.recentSearches.slice(0, 5) as item}
               <button onclick={() => commitSearch(item)} class="flex items-center px-4 py-4 border-b border-gray-50 text-[15px] text-gray-700 font-bold active:bg-gray-50 transition-colors">
                 <svg class="w-5 h-5 text-gray-300 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                 {item}
               </button>
             {/each}
          </div>
        {/if}
      {:else}
        <div class="flex flex-col bg-white">
          {#if searchStore.isSearching}
             <div class="py-20 text-center flex flex-col items-center gap-3">
                <div class="w-8 h-8 border-2 border-luxury-copper/20 border-t-luxury-copper rounded-full animate-spin"></div>
                <span class="text-gray-400 text-[13px] font-black uppercase tracking-widest">Neural Scanning...</span>
             </div>
          {:else}
             {#if isNewsContext}
                {#if searchStore.searchArticleResults.length === 0 && localQuery}
                  <div class="px-6 py-10 text-center flex flex-col items-center gap-3 bg-gray-50/50">
                    <svg class="w-10 h-10 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.181 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>
                    <div class="text-[13px] font-bold text-gray-400 italic">Mục kiến thức không có kết quả phù hợp.</div>
                  </div>
                {/if}
                {@render mobileArticles()}
                {@render mobileProducts()}
             {:else}
                {@render mobileProducts()}
                {@render mobileArticles()}
             {/if}

             {#if searchStore.searchResults.length === 0 && searchStore.searchArticleResults.length === 0}
                <div class="py-20 text-center px-10 text-gray-300 font-bold uppercase tracking-widest text-[13px]">Không tìm thấy kỳ quan nào.</div>
             {/if}
          {/if}
        </div>
      {/if}
    </div>
  </div>
{/if}

<!-- Snippets -->
{#snippet mobileProducts()}
  {#if searchStore.searchResults.length > 0}
    <div class="flex flex-col">
       <h3 class="px-4 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-50 bg-gray-50/20">{isNewsContext ? 'Sản phẩm tham khảo' : 'Sản phẩm Elite'}</h3>
       {#each searchStore.searchResults as p}
        <a href="/{p.slug}" onclick={() => { searchStore.addSearch(p.name); searchStore.isOverlayOpen = false; }} class="flex items-center gap-4 px-4 py-4 border-b border-gray-100 active:bg-gray-50">
           <div class="w-20 h-20 shrink-0 bg-white border border-gray-100 rounded-sm overflow-hidden p-1">
             {#if p.images?.[0]}
                <img src={p.images[0]} class="w-full h-full object-contain mix-blend-multiply" alt={p.name} />
             {/if}
           </div>
           <div class="flex flex-col min-w-0">
              <h4 class="text-[14px] font-black text-gray-900 uppercase italic line-clamp-2 leading-tight mb-1">{p.name}</h4>
              <div class="text-[16px] font-black text-black">
                {formatCurrency(p.discountPrice ?? p.price)}
              </div>
           </div>
        </a>
       {/each}
    </div>
  {/if}
{/snippet}

{#snippet mobileArticles()}
  {#if searchStore.searchArticleResults.length > 0}
    <div class="flex flex-col">
       <h3 class="px-4 py-4 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-50 bg-gray-50/20">{isNewsContext ? 'Kết quả hàng đầu' : 'Kiến thức & Tin tức'}</h3>
       {#each searchStore.searchArticleResults as art}
        <a href="/{art.slug}" onclick={() => { searchStore.addSearch(art.title); searchStore.isOverlayOpen = false; }} class="flex flex-col gap-3 px-4 py-5 border-b border-gray-100 active:bg-gray-50">
           <div class="flex items-center gap-4">
              <div class="w-16 h-16 shrink-0 bg-gray-100 rounded-sm overflow-hidden">
                {#if art.featuredImage}
                   <img src={art.featuredImage} class="w-full h-full object-cover" alt={art.title} />
                {/if}
              </div>
              <div class="flex flex-col min-w-0">
                 <div class="text-[9px] font-black text-[#C18F7E] uppercase tracking-widest mb-1">{art.category}</div>
                 <h4 class="text-[15px] font-black text-gray-900 uppercase italic leading-snug line-clamp-2">{art.title}</h4>
                 {#if art.match_score}
                    <div class="mt-2 text-[10px] font-bold text-green-500 uppercase">Độ phù hợp: {Math.round(art.match_score * 100)}%</div>
                 {/if}
              </div>
           </div>
        </a>
       {/each}
    </div>
  {/if}
{/snippet}

<style>
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
  
  @keyframes scanning {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  .animate-scanning { animation: scanning 2s linear infinite; }

  .search-ring-mobile {
    height: 38px;
    flex: 1;
    border-radius: 9999px;
    background: #F2F2F2;
    overflow: hidden;
  }
  .search-inner-mobile {
    display: flex;
    align-items: center;
    padding: 0 12px;
    height: 100%;
  }
  .search-input-mobile {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    font-size: 15px;
    font-weight: 500;
    margin-left: 8px;
    color: #000;
  }
</style>
