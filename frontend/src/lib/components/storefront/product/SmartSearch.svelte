<script lang="ts">
  import { onMount, tick, untrack } from 'svelte';
  import { goto } from '$app/navigation';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { isAdminDomain } from '$lib/state/nanobot/env';
  import { fade, fly, slide } from 'svelte/transition';
  import { Z_INDEX_CLIENT, Z_INDEX_ADMIN } from '$lib/core/constants/zIndex';

  const searchStore = getSearchStore();
  
  let { variant = 'desktop' } = $props<{
    variant?: 'desktop' | 'mobile-overlay';
  }>();

  let isFocused = $state(false);
  let inputElement = $state<HTMLInputElement>();

  // Local state for immediate responsiveness
  let localQuery = $state(searchStore.searchQuery);
  
  $effect(() => {
    searchStore.triggerSearch(localQuery);
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
          console.log("Search input focused (Mobile)");
        }
      });
    }
  });

  $effect(() => {
    if (variant === 'desktop' && isFocused && inputElement) {
      tick().then(() => {
        if (inputElement) {
          inputElement.focus();
          console.log("Search input focused (Desktop)");
        }
      });
    }
  });
</script>

{#if variant === 'desktop'}
  <div class="w-full relative group" style:z-index={Z_INDEX_CLIENT.HEADER + 1}>
    <div 
      class="w-full flex items-center bg-white rounded-none border border-gray-200 relative focus-within:border-luxury-copper transition-all shadow-sm focus-within:shadow-md"
      style:z-index={Z_INDEX_CLIENT.HEADER + 2}
    >
      <input
        bind:this={inputElement}
        type="text"
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
          onclick={() => { localQuery = ''; inputElement?.focus(); }}
          class="absolute right-[88px] text-gray-300 hover:text-gray-400 transition-colors p-1"
          style:z-index={Z_INDEX_CLIENT.HEADER + 4}
        >
          <svg class="w-[18px] h-[18px] bg-gray-200 hover:bg-gray-300 text-white rounded-full p-[3px] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
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
        in:fly={{ y: 10, duration: 300 }}
        class="absolute top-[calc(100%+8px)] left-0 w-full bg-white shadow-[0_20px_100px_rgba(0,0,0,0.5)] border border-gray-100 overflow-hidden"
        style:z-index={Z_INDEX_CLIENT.HEADER + 1}
      >
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

            <!-- Trending Section -->
            {#if searchStore.featuredProducts.length > 0}
              <section>
                <div class="flex items-center gap-2 mb-3">
                  <span class="w-1.5 h-1.5 bg-luxury-copper rounded-full animate-pulse"></span>
                  <span class="text-[10px] font-black uppercase tracking-widest text-gray-400">Xu hướng tìm kiếm</span>
                </div>
                <div class="grid grid-cols-2 gap-y-3">
                  {#each searchStore.featuredProducts as p, i}
                    <button 
                      onclick={() => commitSearch(p.name)}
                      class="flex items-center gap-3 text-left group"
                    >
                      <span class="w-5 text-[12px] font-black text-gray-300 group-hover:text-luxury-copper">{i + 1}</span>
                      <span class="text-[13px] font-bold text-gray-700 group-hover:text-luxury-copper line-clamp-1 transition-colors">{p.name}</span>
                      {#if i < 2}
                        <span class="text-[8px] bg-red-500 text-white px-1 py-0.5 font-black uppercase tracking-tighter rounded-sm">Hot</span>
                      {/if}
                    </button>
                  {/each}
                </div>
              </section>
            {/if}
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
                      onclick={() => { isFocused = false; searchStore.isOverlayOpen = false; }}
                      class="p-2 text-left hover:bg-gray-50 flex items-center gap-3 group rounded"
                    >
                      <div class="w-10 h-10 bg-gray-100 rounded flex-shrink-0 overflow-hidden border border-gray-100">
                        {#if p.images?.length > 0 || p.metadata?.image_url}
                           <img src={p.images?.[0] ?? p.metadata?.image_url} class="w-full h-full object-cover" alt={p.name} />
                        {/if}
                      </div>
                      <span class="text-[14px] font-medium text-gray-800 line-clamp-1 flex-grow">{p.name}</span>
                      <span class="text-[13px] text-luxury-copper font-bold tabular-nums">{p.price?.toLocaleString('vi-VN')}đ</span>
                    </a>
                  {/each}
                </div>
              {/if}
            </section>
          {/if}

          <!-- Visual Product Preview (Elite Touch) -->
          {#if searchStore.featuredProducts.length > 0}
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
                    <div class="text-[12px] font-bold line-clamp-2 leading-tight group-hover:text-luxury-copper transition-colors" title={p.name}>{p.name}</div>
                    <div class="text-[14px] font-black text-luxury-copper tabular-nums tracking-tight">{p.price.toLocaleString('vi-VN')}đ</div>
                  </a>
                {/each}
              </div>
            </section>
          {/if}
        </div>
      </div>
    {/if}
  </div>

{:else if variant === 'mobile-overlay'}
  <div 
    in:fade={{ duration: 150 }} 
    class="fixed inset-0 bg-white flex flex-col font-['Outfit']"
    style:z-index={Z_INDEX_CLIENT.MODAL + 10}
  >
    <!-- TikTok Exact Header -->
    <header class="w-full px-[8px] py-[6px] flex items-center gap-2 bg-white z-20 relative border-b border-gray-100">
      <!-- Back -->
      <button onclick={() => searchStore.isOverlayOpen = false} class="p-1 -ml-1 text-black active:bg-gray-100 rounded-full transition-colors flex-shrink-0">
        <svg class="w-[26px] h-[26px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg>
      </button>

    <!-- Gray Search Box (No border, bg-gray, rounded-8px) & CTA Inside -->
      <div class="flex-grow flex items-center h-[36px] bg-[#f1f1f2] rounded-[8px] pl-2.5 pr-1.5 gap-2">
        <svg class="w-[18px] h-[18px] text-gray-500 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
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
          spellcheck="false"
          autofocus
          class="flex-grow min-w-0 bg-transparent text-[15px] text-black focus:outline-none placeholder:text-gray-400"
        />
        {#if localQuery}
          <button onclick={() => localQuery = ''} class="text-gray-400 p-0.5 flex-shrink-0">
            <svg class="w-[16px] h-[16px] bg-[#d1d1d6] text-white rounded-full p-[2px]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        {/if}

        <button 
          onclick={() => commitSearch(localQuery)}
          class="text-[#fe2c55] font-[700] text-[15px] pl-1 pr-0.5 whitespace-nowrap active:opacity-60 transition-opacity flex-shrink-0"
        >
          Tìm kiếm
        </button>
      </div>
    </header>

    <!-- Content Area: Actual TikTok Layout -->
    <div class="flex-grow overflow-y-auto bg-white relative z-10 flex flex-col pb-8">
      
      {#if !localQuery}
        <!-- Recent Searches List Style -->
        {#if searchStore.recentSearches.length > 0}
          <div class="flex flex-col pt-1">
            {#each searchStore.recentSearches.slice(0, 4) as item}
               <div class="flex items-center px-4 py-[14px]">
                 <svg class="w-5 h-5 text-gray-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" /></svg>
                 <button onclick={() => commitSearch(item)} class="flex-grow text-left text-[15px] text-black font-[600] ml-3 truncate tracking-tight">{item}</button>
                 <button onclick={(e) => { e.stopPropagation(); searchStore.removeSearch(item); }} class="p-2 -mr-2 active:opacity-50 transition-opacity"><svg class="w-[18px] h-[18px] text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
               </div>
            {/each}
            {#if searchStore.recentSearches.length > 4}
              <button class="py-3 text-[13px] text-gray-500 flex items-center justify-center gap-1 active:bg-gray-50">
                Xem thêm <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
              </button>
            {/if}
          </div>
        {/if}

        <!-- You might also like (Real Featured Products) -->
        {#if searchStore.featuredProducts.length > 0}
          <div class="px-4 py-3 mt-1">
            <h3 class="text-[16px] font-[800] text-black mb-4 tracking-tight">Có thể bạn cũng thích</h3>
            <div class="flex flex-col gap-[18px]">
               {#each searchStore.featuredProducts as p}
                 <a href="/{p.slug}" onclick={() => searchStore.isOverlayOpen = false} class="flex items-center gap-3.5 w-full text-left active:opacity-70 transition-opacity">
                   <!-- Square thumbnail -->
                   <div class="w-[50px] h-[50px] rounded-[8px] bg-gray-100 flex-shrink-0 border border-gray-100/50 overflow-hidden relative">
                      {#if p.images?.length > 0 || p.metadata?.image_url}
                         <img src={p.images?.[0] ?? p.metadata?.image_url} alt={p.name} class="w-full h-full object-cover" loading="lazy" />
                      {/if}
                   </div>
                   <div class="flex flex-col">
                      <span class="text-[14px] text-black font-[600] tracking-tight line-clamp-1 leading-snug">{p.name}</span>
                      <span class="text-[13px] text-[#fe2c55] font-[700] mt-0.5 tracking-tight">{p.price.toLocaleString('vi-VN')}đ</span>
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
               <div class="py-10 text-center text-gray-400 text-[13px]">Đang trích xuất dữ liệu...</div>
            {:else}
              {#each searchStore.searchResults as p}
                <a 
                  href="/{p.slug}"
                  onclick={() => searchStore.isOverlayOpen = false}
                  class="flex items-center px-4 py-3 active:bg-gray-50 transition-colors border-b border-gray-50/50"
                >
                   <div class="w-10 h-10 bg-gray-100 rounded-[6px] flex-shrink-0 overflow-hidden border border-gray-100">
                     {#if p.images?.length > 0 || p.metadata?.image_url}
                        <img src={p.images?.[0] ?? p.metadata?.image_url} class="w-full h-full object-cover" alt={p.name} />
                     {/if}
                   </div>
                   <span class="flex-grow text-left text-[14px] text-[#161823] font-[600] ml-3 line-clamp-2 tracking-tight leading-snug">{p.name}</span>
                </a>
              {/each}
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
</style>
