<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import SmartSearch from '../product/SmartSearch.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { User, Bell, ShoppingCart } from 'lucide-svelte';
  
  const ui = getClientUi();

  const cartStore = getCartStore();
  const searchStore = getSearchStore();
  
  function handleUserClick() {
    if (!authStore.isAuthenticated) {
      ui.openLogin();
    } else {
      window.location.href = '/user/profile';
    }
  }
</script>

<header class="fixed top-0 w-full z-[var(--z-header)] px-4 py-3 pb-4 flex flex-col gap-3 bg-white/98 backdrop-blur-md border-b border-gray-100 shadow-sm transition-all duration-300">
  <!-- Top Row: Logo & Icons -->
  <div class="flex justify-between items-center w-full">
    <div class="flex items-center gap-2">
      <div class="w-8 h-8 bg-gradient-to-br from-luxury-copper to-luxury-peach rounded-none flex items-center justify-center shadow-md">
        <span class="text-[11px] font-black tracking-tighter text-white">M</span>
      </div>
      <div class="font-black text-xl tracking-tighter uppercase italic bg-gradient-to-r from-luxury-copper via-luxury-peach to-luxury-copper bg-clip-text text-transparent drop-shadow-sm">
        MICSMO
      </div>
    </div>
    
    <div class="flex gap-4 items-center">
      <!-- User Profile Trigger -->
      <button 
        onclick={handleUserClick}
        class="relative p-1 hover:scale-110 transition-transform active:scale-95 text-gray-700 hover:text-luxury-copper"
      >
         {#if authStore.isAuthenticated}
           <div class="w-6 h-6 bg-gradient-to-br from-luxury-copper to-luxury-peach flex items-center justify-center text-[10px] font-black text-white border border-white ring-1 ring-luxury-copper/20 shadow-sm">
             {authStore.user?.name?.charAt(0).toUpperCase()}
           </div>
         {:else}
           <User class="w-6 h-6" strokeWidth={2.5} />
         {/if}
      </button>

      <button class="relative p-1 hover:scale-110 transition-transform active:scale-95 text-gray-700 hover:text-luxury-copper">
         <Bell class="w-6 h-6" strokeWidth={2.5} />
      </button>
      
      <button onclick={() => cartStore.toggleCart()} class="relative p-1 hover:scale-110 transition-transform active:scale-95 text-gray-700 hover:text-luxury-copper">
        <ShoppingCart class="w-6 h-6" strokeWidth={2.5} />
        {#if cartStore.totalItems > 0}
          <span class="absolute -top-0 -right-0 min-w-4 h-4 px-1 bg-luxury-copper text-[8px] flex items-center justify-center rounded-none font-black text-white border-2 border-white shadow-sm">
            {cartStore.totalItems}
          </span>
        {/if}
      </button>
    </div>
  </div>

  <!-- Search Row -->
  <div class="w-full relative">
    <div 
      onclick={() => searchStore.isOverlayOpen = true}
      role="presentation"
      class="w-full h-11 bg-gray-50 rounded-none flex items-center px-4 relative overflow-hidden group border border-gray-100 transition-all cursor-text"
    >
      <svg class="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      <input 
        type="text" 
        readonly
        placeholder={searchStore.searchPlaceholder}
        class="w-full bg-transparent text-[14px] text-gray-900 font-medium focus:outline-none pointer-events-none"
      />
      <div class="ml-auto text-luxury-copper font-black text-[10px] border-l border-gray-200 pl-3 uppercase tracking-widest">
        Tìm kiếm
      </div>
    </div>
  </div>
</header>

{#if searchStore.isOverlayOpen}
  <SmartSearch variant="mobile-overlay" />
{/if}
