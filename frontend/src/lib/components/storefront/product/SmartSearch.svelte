<script lang="ts">
  import { tick, untrack } from 'svelte';
  import { goto } from '$app/navigation';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { trimProductName } from '$lib/utils/format';
  import { isAdminDomain } from '$lib/state/nanobot/env';
  import { fade, fly, slide } from 'svelte/transition';
  import { Z_INDEX_CLIENT, Z_INDEX_ADMIN } from '$lib/core/constants/zIndex';

  let { variant = 'desktop' } = $props<{
    variant?: 'desktop' | 'mobile-overlay';
  }>();

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
                             <span class="text-[#C18F7E]">đ</span>{(p.discountPrice ?? p.price).toLocaleString('vi-VN')}
                           </span>
                           {#if p.discountPrice}
                             <span class="text-[9px] text-gray-300 line-through font-bold">đ{p.price.toLocaleString('vi-VN')}</span>
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
            <!-- Case 2: Suggestions (Real DB Products) -->
            <section>
              {#if searchStore.searchResults.length > 0}
                <div class="text-[10px] font-black uppercase tracking-widest text-[#161823] mb-2">Sản phẩm</div>
              {/if}
              {#if searchStore.isSearching}
                 <div class="py-4 text-center text-gray-400 text-xs">Đang tìm kiếm...</div>
              {:else}
                <div class="flex flex-col gap-1">
                  {#each searchStore.searchResults as p}
                    <a 
                      href="/{p.slug}"
                      onclick={() => { 
                        if (variant === 'desktop') searchStore.addSearch(p.name);
                        isFocused = false; 
                        searchStore.isOverlayOpen = false; 
                      }}
                      class="px-4 py-3 bg-white hover:bg-gray-50 flex items-start gap-4 border-b border-gray-100 transition-colors group"
                    >
                      <!-- Image viewport (Elite V2.2: Consistent 64px) -->
                      <div class="w-16 h-16 flex-shrink-0 relative overflow-hidden bg-white">
                        {#if p.images?.length > 0 || p.metadata?.image_url}
                           <img src={p.images?.[0] ?? p.metadata?.image_url} class="w-full h-full object-contain mix-blend-multiply" alt={p.name} />
                        {/if}
                      </div>
                      
                      <!-- Product Intelligence Info -->
                      <div class="flex flex-col flex-grow min-w-0">
                        <!-- Product Name: High contrast blue-grey -->
                        <h4 class="text-[15px] font-bold text-[#374151] line-clamp-1 mb-0.5 leading-tight group-hover:text-luxury-copper transition-colors">{trimProductName(p.name)}</h4>
                        
                        <!-- SKU & Dynamic Category Tag -->
                        <div class="flex items-center justify-between gap-4 mb-2">
                           <span class="text-[12px] text-gray-500 font-medium">Mã sản phẩm: {p.sku || p.id.split('-')[0].toUpperCase()}</span>
                           
                           {#if p.category}
                             <div class="bg-[#ff9a9a]/20 text-[#ff6b6b] px-2 py-1 flex items-center gap-1.5 rounded-sm shadow-sm border border-[#ff9a9a]/30">
                                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>
                                <span class="text-[10px] font-black uppercase tracking-tight">{p.category}</span>
                             </div>
                           {/if}
                        </div>
                        
                        <!-- Pricing Intelligence (Literal Match) -->
                        <div class="flex items-center gap-2 mt-auto">
                           <span class="text-[15px] text-gray-900 font-black tabular-nums">
                             <span class="text-[#C18F7E] mr-0.5">đ</span>{(p.discountPrice ?? p.price).toLocaleString('vi-VN')}
                           </span>
                           {#if p.discountPrice}
                             <span class="text-[12px] text-gray-300 line-through font-medium tabular-nums px-1">
                               đ{p.price.toLocaleString('vi-VN')}
                             </span>
                           {/if}
                        </div>
                      </div>
                    </a>
                  {/each}
                </div>
              {/if}
            </section>
          {/if}


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
                      <div class="absolute inset-0 bg-gradient-to-tr from-luxury-copper/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                      {#if p.metadata?.landing_type === 'XOHI'}
                        <div class="absolute bottom-1 left-1 text-[8px] font-black bg-white/90 px-1.5 py-0.5 text-luxury-copper rounded-sm shadow-sm hover:scale-105 transition-transform">MẬT MÃ XOHI</div>
                      {/if}
                    </div>
                    <div class="text-[12px] font-bold line-clamp-2 leading-tight group-hover:text-luxury-copper transition-colors" title={p.name}>{trimProductName(p.name)}</div>
                    <div class="flex flex-col">
                       <div class="text-[14px] font-black text-black tabular-nums tracking-toggle">
                         <span class="text-[#C18F7E]">đ</span>{(p.discountPrice ?? p.price).toLocaleString('vi-VN')}
                       </div>
                       {#if p.discountPrice}
                         <div class="text-[10px] text-gray-300 line-through font-bold tabular-nums tracking-tight">đ{p.price.toLocaleString('vi-VN')}</div>
                       {/if}
                    </div>
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
    <!-- TikTok Exact Header - Matched with MobileSearchHeader.svelte -->
    <header class="w-full px-2 py-2 flex items-center bg-white z-20 relative border-b border-gray-50/50 h-12">
      <button onclick={() => searchStore.isOverlayOpen = false} class="p-1 -ml-1 text-gray-900 active:scale-90 transition-transform flex-shrink-0">
        <svg class="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
      </button>

      <div class="search-ring-mobile flex-grow ml-1">
        <div class="search-inner-mobile">
          <svg class="w-[18px] h-[18px] flex-shrink-0 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            bind:this={inputElement}
            bind:value={localQuery}
            type="text"
            onkeydown={handleKeyDown}
            placeholder={searchStore.searchPlaceholder}
            autocomplete="off"
            class="search-input-mobile"
          />
          {#if localQuery}
            <button 
              onclick={() => { localQuery = ''; inputElement?.focus(); }}
              class="search-clear-mobile"
            >
              <svg class="w-4 h-4 bg-gray-200 text-white rounded-full p-[2px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          {/if}
          <button 
            onclick={() => commitSearch(localQuery)}
            class="search-cta-mobile"
          >
            Tìm kiếm
          </button>
        </div>
      </div>
    </header>

    <!-- Content Area: Actual TikTok Layout -->
    <div class="flex-grow overflow-y-auto bg-white relative z-10 flex flex-col pb-8">
      
      {#if !localQuery}
        <!-- RECENT HISTORY (List Style with Clock Icons) -->
        {#if searchStore.recentSearches.length > 0}
          <div class="flex flex-col mb-4">
            {#each searchStore.recentSearches.slice(0, 5) as item}
               <div class="flex items-center px-4 py-[14px] border-b border-gray-50/50">
                 <svg class="w-5 h-5 text-gray-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                 <button onclick={() => commitSearch(item)} class="flex-grow text-left text-[15px] text-gray-700 font-bold ml-3 truncate tracking-tight">{item}</button>
                 <button onclick={(e) => { e.stopPropagation(); searchStore.removeSearch(item); }} class="p-2 -mr-2 text-gray-300 active:text-red-500 transition-colors">
                    <svg class="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                 </button>
               </div>
            {/each}
          </div>
        {/if}

        <!-- YOU MIGHT ALSO LIKE (Vertical High-Density List) -->
        {#if searchStore.featuredProducts.length > 0}
          <div class="px-4">
            <h3 class="text-[16px] font-black text-gray-900 mb-5 tracking-tight">Có thể bạn cũng thích</h3>
            <div class="flex flex-col gap-6">
               {#each searchStore.featuredProducts as p}
                 <a href="/{p.slug}" onclick={() => searchStore.isOverlayOpen = false} class="flex items-center gap-4 w-full active:opacity-70 transition-opacity">
                   <div class="w-[54px] h-[54px] rounded-lg bg-gray-50 flex-shrink-0 border border-gray-100 overflow-hidden">
                      {#if p.images?.length > 0 || p.metadata?.image_url}
                         <img src={p.images?.[0] ?? p.metadata?.image_url} alt={p.name} class="w-full h-full object-cover" loading="lazy" />
                      {/if}
                   </div>
                   <div class="flex flex-col justify-center flex-1">
                      <span class="text-[14px] text-gray-800 font-bold tracking-tight line-clamp-1 leading-tight mb-1">{trimProductName(p.name)}</span>
                      <div class="flex items-center gap-2">
                         <span class="text-[15px] text-black font-black tracking-tight">
                           <span class="text-[#C18F7E]">đ</span>{(p.discountPrice ?? p.price).toLocaleString('vi-VN')}
                         </span>
                         {#if p.discountPrice}
                           <span class="text-[11px] text-gray-300 line-through font-bold">đ{(p.price).toLocaleString('vi-VN')}</span>
                         {/if}
                      </div>
                   </div>
                 </a>
               {/each}
            </div>
          </div>
        {/if}

      {:else}
        <!-- Real-time DB Suggestions: Minimalist TikTok -->
        <div class="flex flex-col pt-1 bg-white">
            {#if searchStore.isSearching}
               <div class="py-20 text-center flex flex-col items-center gap-3">
                  <div class="w-8 h-8 border-2 border-luxury-copper/20 border-t-luxury-copper rounded-full animate-spin"></div>
                  <span class="text-gray-400 text-[13px] font-bold uppercase tracking-widest">Đang trích xuất dữ liệu...</span>
               </div>
            {:else}
              {#each searchStore.searchResults as p}
                <a 
                  href="/{p.slug}"
                  onclick={() => { 
                     searchStore.addSearch(p.name); 
                     searchStore.isOverlayOpen = false; 
                  }}
                  class="flex items-center px-4 py-[14px] active:bg-gray-50 transition-colors border-b border-gray-50/50 relative overflow-hidden group"
                >
                   <div class="w-[68px] h-[68px] bg-gray-50 rounded-none flex-shrink-0 overflow-hidden border border-gray-100 relative shadow-sm">
                     {#if p.images?.length > 0 || p.metadata?.image_url}
                        <img src={p.images?.[0] ?? p.metadata?.image_url} class="w-full h-full object-cover" alt={p.name} />
                     {/if}
                     {#if p.discountPrice}
                        <div class="absolute top-0 right-0 bg-[#fe2c55] text-white text-[8px] font-black px-1.5 py-0.5 shadow-lg">
                           GIẢM GIÁ
                        </div>
                     {/if}
                   </div>
                   <div class="flex flex-col ml-4 flex-grow min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="text-[14px] text-gray-900 font-bold line-clamp-1 tracking-tight leading-snug">{trimProductName(p.name)}</span>
                      </div>
                      <div class="flex items-center justify-between">
                         <div class="flex flex-col">
                            <div class="flex items-center gap-2">
                               <span class="text-[16px] text-black font-black tracking-tighter">
                                 <span class="text-[#C18F7E]">đ</span>{(p.discountPrice ?? p.price).toLocaleString('vi-VN')}
                               </span>
                               {#if p.discountPrice}
                                 <span class="text-[11px] text-gray-300 line-through font-bold">đ{(p.price).toLocaleString('vi-VN')}</span>
                               {/if}
                            </div>
                            <div class="flex items-center gap-2 mt-1">
                               <span class="flex items-center gap-1">
                                 <span class="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                                 <span class="text-[10px] text-luxury-copper font-black uppercase">{getPseudoViews(p.id)} ĐANG XEM</span>
                               </span>
                            </div>
                         </div>
                         <div class="flex flex-col items-end gap-1">
                            {#if p.orderCount && p.orderCount > 0}
                              <span class="text-[10px] text-gray-400 font-black uppercase tracking-tighter opacity-70 underline decoration-luxury-copper/20 underline-offset-2">Đã bán {p.orderCount}</span>
                            {/if}
                            {#if p.stock < 10 && p.stock > 0}
                              <span class="text-[8px] font-black text-white bg-red-500 px-1.5 py-0.5 animate-pulse">SẮP HẾT</span>
                            {/if}
                         </div>
                      </div>
                   </div>
                </a>
              {/each}
              {#if searchStore.searchResults.length === 0}
                 <div class="py-20 text-center px-10">
                    <span class="text-gray-300 font-bold uppercase tracking-widest text-[13px]">Không tìm thấy kỳ quan nào phù hợp với mã khóa của bạn.</span>
                 </div>
              {/if}
            {/if}
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  @keyframes scanning {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  .animate-scanning {
    animation: scanning 1.5s linear infinite;
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  @keyframes pulse-soft {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }

  .search-ring-mobile {
    height: 36px;
    flex: 1;
    min-width: 0;
    border: 1.5px solid transparent;
    border-radius: 8px;
    overflow: hidden;
    background-image:
      linear-gradient(white, white), 
      linear-gradient(90deg, #06d6d6, #fe2c55);
    background-origin: border-box;
    background-clip: padding-box, border-box;
    transform: translateZ(0); 
  }

  .search-inner-mobile {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 0 8px 0 10px;
    height: 100%;
    width: 100%;
  }

  .search-input-mobile {
    flex: 1;
    min-width: 0;
    font-size: 14px;
    font-weight: 600;
    color: #111;
    background: transparent;
    border: none;
    outline: none;
  }
  .search-input-mobile::placeholder {
    color: #9ca3af;
    font-weight: 500;
  }

  .search-cta-mobile {
    background: none;
    border: none;
    padding: 0 4px 0 0;
    cursor: pointer;
    font-size: 15px;
    font-weight: 800;
    color: #fe2c55;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .search-clear-mobile {
    padding: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
</style>
