<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { fly, fade } from 'svelte/transition';
  import SmartSearch from '../product/SmartSearch.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import NotificationBell from './NotificationBell.svelte';
  
  const ui = getClientUi();
  const cartStore = getCartStore();
  const searchStore = getSearchStore();
  let showAccountMenu = $state(false);
  let menuContainer = $state<HTMLElement>();

  function toggleAccountMenu(e: MouseEvent) {
    e.stopPropagation();
    if (!authStore.isAuthenticated) {
      ui.openLogin();
    } else {
      showAccountMenu = !showAccountMenu;
    }
  }

  $effect(() => {
    if (!showAccountMenu) return;
    const handleOutsideClick = (e: MouseEvent) => {
      if (menuContainer && !menuContainer.contains(e.target as Node)) {
        showAccountMenu = false;
      }
    };
    window.addEventListener('click', handleOutsideClick);
    return () => window.removeEventListener('click', handleOutsideClick);
  });
</script>

<header class="sticky top-0 w-full z-[var(--z-header)] bg-white border-b border-gray-100 shadow-[0_4px_30px_rgba(0,0,0,0.02)]">
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0">
    <!-- Top Navbar - Micsmo Elite 2026 -->
    <div class="flex items-center justify-between h-[28px] text-[11px] text-gray-500 border-b border-gray-50 bg-gray-50/30 -mx-4 px-4 xl:-mx-0 xl:px-0">
      <div class="flex items-center space-x-3">
        <button type="button" class="hover:text-luxury-copper transition-colors">Kênh Người Bán</button>
        <span class="w-[1px] h-3 bg-gray-200"></span>
        <button type="button" class="hover:text-luxury-copper transition-colors">Trở thành Người bán Micsmo</button>
        <span class="w-[1px] h-3 bg-gray-200"></span> 
        <a href="/tin-tuc" class="hover:text-luxury-copper transition-colors">Tin tức</a>
        <!--
        <span class="w-[1px] h-3 bg-gray-200"></span>
        <div class="flex items-center gap-1">
          <span>Kết nối</span>
          <button type="button" class="hover:text-luxury-copper transition-colors text-lg italic">f</button>
          <button type="button" class="hover:text-luxury-copper transition-colors text-lg italic">in</button>
        </div> 
        -->
      </div>
      <div class="flex items-center space-x-4">
        {#if authStore.isAuthenticated}
          <div class="flex items-center -ml-2">
            <NotificationBell />
          </div>
        {/if}
        <button type="button" class="flex items-center gap-1 hover:text-luxury-copper transition-colors">
          <span>❔</span> Hỗ Trợ
        </button>
        <button class="flex items-center gap-1 hover:text-luxury-copper transition-colors uppercase font-bold tracking-tighter">
          🌐 Tiếng Việt
        </button>
        <span class="w-[1px] h-3 bg-gray-200"></span>
        
        {#if !authStore.isAuthenticated}
          <button onclick={() => ui.openRegister()} type="button" class="hover:text-luxury-copper font-bold uppercase transition-colors tracking-tighter">Đăng Ký</button>
          <span class="w-[1px] h-3 bg-gray-200"></span>
          <button onclick={() => ui.openLogin()} type="button" class="hover:text-luxury-copper font-bold uppercase transition-colors tracking-tighter">Đăng Nhập</button>
        {:else}
          <div class="relative flex items-center group/topacc" bind:this={menuContainer}>
            <button 
              onclick={toggleAccountMenu}
              class="hover:opacity-80 transition-opacity flex items-center gap-2 py-1"
            >
              <div class="w-5 h-5 rounded-full overflow-hidden border border-white shadow-sm ring-1 ring-gray-100 bg-gray-50 flex items-center justify-center shrink-0">
                {#if authStore.user?.avatar_url}
                  <img src={authStore.user.avatar_url} alt="Avatar" class="w-full h-full object-cover" />
                {:else}
                  <div class="w-full h-full bg-luxury-grad flex items-center justify-center text-[8px] font-black text-white">
                    {authStore.user?.name?.charAt(0).toUpperCase()}
                  </div>
                {/if}
              </div>
              <span class="text-[11px] font-bold text-gray-700 truncate max-w-[120px]">{authStore.user?.name}</span>
              <svg class="w-3 h-3 text-gray-400 group-hover/topacc:text-luxury-copper transition-colors {showAccountMenu ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg>
            </button>

            {#if showAccountMenu}
              <div 
                in:fly={{ y: 8, duration: 300, opacity: 0 }} 
                out:fade={{ duration: 200 }} 
                class="absolute right-0 top-[100%] mt-1 w-44 z-[var(--z-popup)] origin-top-right shadow-[0_1px_20px_0_rgba(0,0,0,0.12)] bg-white ring-1 ring-black/5" 
                onclick={(e) => e.stopPropagation()}
              >
                <div class="absolute -top-1 right-[22px] w-3 h-3 bg-white rotate-45 z-[var(--z-popup-indicator)] border-t border-l border-black/5"></div>
                <div class="flex flex-col text-left py-1 relative z-[var(--z-popup)]">
                  <a href="/user/profile" class="px-4 py-2.5 text-[13px] text-gray-700 hover:text-luxury-copper hover:bg-gray-50 transition-colors font-medium">Hồ sơ của tôi</a>
                  <a href="/user/purchase" class="px-4 py-2.5 text-[13px] text-gray-700 hover:text-luxury-copper hover:bg-gray-50 transition-colors font-medium">Đơn mua</a>
                  <button 
                    onclick={() => authStore.logout()}
                    class="px-4 py-2.5 text-[13px] text-gray-700 hover:text-luxury-copper hover:bg-gray-50 transition-colors font-medium text-left w-full border-t border-gray-50"
                  >
                    Đăng xuất
                  </button>
                </div>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    </div>

    <div class="flex flex-col pt-4 pb-2">
      <!-- Top Row: Main Interaction -->
      <div class="flex items-center gap-6">
        <!-- Logo Section -->
        <div class="flex shrink-0 items-center">
          <a href="/" class="flex flex-col group transition-all active:scale-95">
            <span class="text-2xl font-black tracking-[0.22em] uppercase leading-none bg-gradient-to-r from-luxury-copper via-luxury-peach to-luxury-copper bg-clip-text text-transparent drop-shadow-sm group-hover:tracking-[0.25em] transition-all duration-700">
                MICSMO
            </span>
            <span class="text-[9px] font-black tracking-[0.11em] text-gray-400 uppercase mt-1.5 px-0.5 whitespace-nowrap border-t border-gray-100/50 pt-1">
                Bật tông trắng sáng
            </span>
          </a>
        </div>

        <div class="flex-grow">
          <SmartSearch variant="desktop" />
        </div>

        <!-- Actions Section -->
        <div class="flex items-center gap-6 shrink-0 h-[48px]">
          <!-- Hotline -->
          <div class="hidden lg:flex flex-col items-end text-gray-700 justify-center">
            <span class="text-[9px] uppercase tracking-[0.1em] font-black opacity-30 leading-none mb-1">Hotline</span>
            <a href="tel:0949901122" class="text-[13px] font-bold tracking-tight hover:text-[#C18F7E] transition-colors tabular-nums">0949 901 122</a>
          </div>


          <!-- Cart Section -->
          <div class="flex items-center h-full">
            <button onclick={() => cartStore.toggleCart()} class="relative flex flex-col items-center justify-center gap-1 group transition-all active:scale-95 min-w-[60px]">
              <div class="text-gray-700 group-hover:text-luxury-copper transition-colors">
                <svg class="w-7 h-7 stroke-current" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
                {#if cartStore.totalItems > 0}
                  <span class="absolute top-0 right-1 bg-gradient-to-br from-luxury-copper to-luxury-peach text-white border border-white text-[10px] font-bold px-1.5 min-w-[18px] h-4 rounded-none flex items-center justify-center shadow-lg ring-1 ring-white/20">
                    {cartStore.totalItems}
                  </span>
                {/if}
              </div>
              <span class="text-[9px] text-gray-400 font-black uppercase tracking-tighter group-hover:text-luxury-copper transition-colors">Giỏ hàng</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</header>
