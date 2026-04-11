<script lang="ts">
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { fly, fade } from 'svelte/transition';
  import SmartSearch from '../product/SmartSearch.svelte';
  import { getSearchStore } from '$lib/state/commerce/search.svelte';
  
  const cartStore = getCartStore();
  const searchStore = getSearchStore();
  let showAccountMenu = $state(false);

  function toggleAccountMenu(e: MouseEvent) {
    e.stopPropagation();
    showAccountMenu = !showAccountMenu;
  }
</script>

<svelte:window onclick={() => showAccountMenu = false} />

<header class="sticky top-0 w-full z-[var(--z-header)] bg-white border-b border-gray-100 shadow-[0_4px_30px_rgba(0,0,0,0.02)]">
  <div class="max-w-[1200px] mx-auto px-4 xl:px-0">
    <!-- Top Navbar - Micsmo Elite 2026 -->
    <div class="flex items-center justify-between h-[28px] text-[11px] text-gray-500 border-b border-gray-50 bg-gray-50/30 -mx-4 px-4 xl:-mx-0 xl:px-0">
      <div class="flex items-center space-x-3">
        <button type="button" class="hover:text-luxury-copper transition-colors">Kênh Người Bán</button>
        <span class="w-[1px] h-3 bg-gray-200"></span>
        <button type="button" class="hover:text-luxury-copper transition-colors">Trở thành Người bán Micsmo</button>
        <span class="w-[1px] h-3 bg-gray-200"></span>
        <button type="button" class="hover:text-luxury-copper transition-colors">Tải ứng dụng</button>
        <span class="w-[1px] h-3 bg-gray-200"></span>
        <div class="flex items-center gap-1">
          <span>Kết nối</span>
          <button type="button" class="hover:text-luxury-copper transition-colors text-lg italic">f</button>
          <button type="button" class="hover:text-luxury-copper transition-colors text-lg italic">in</button>
        </div>
      </div>
      <div class="flex items-center space-x-4">
        <button type="button" class="flex items-center gap-1 hover:text-luxury-copper transition-colors">
          <span>🔔</span> Thông Báo
        </button>
        <button type="button" class="flex items-center gap-1 hover:text-luxury-copper transition-colors">
          <span>❔</span> Hỗ Trợ
        </button>
        <button class="flex items-center gap-1 hover:text-luxury-copper transition-colors uppercase font-bold tracking-tighter">
          🌐 Tiếng Việt
        </button>
        <span class="w-[1px] h-3 bg-gray-200"></span>
        <button type="button" class="hover:text-luxury-copper font-bold uppercase transition-colors tracking-tighter">Đăng Ký</button>
        <span class="w-[1px] h-3 bg-gray-200"></span>
        <button type="button" class="hover:text-luxury-copper font-bold uppercase transition-colors tracking-tighter">Đăng Nhập</button>
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

          <!-- Account -->
          <div class="relative flex items-center h-full">
            <button 
              onclick={toggleAccountMenu}
              class="flex flex-col items-center justify-center gap-1 group transition-all active:scale-95 px-2"
            >
              <div class="text-gray-700 group-hover:text-[#C18F7E] transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
              </div>
              <span class="text-[9px] text-gray-400 font-black uppercase tracking-tighter group-hover:text-[#C18F7E] transition-colors">Tài khoản</span>
            </button>

            {#if showAccountMenu}
              <div 
                in:fly={{ y: 15, duration: 400, opacity: 0 }} 
                out:fade={{ duration: 200 }} 
                class="absolute right-0 top-[100%] mt-2 w-60 z-50 origin-top-right filter drop-shadow-[0_25px_25px_rgba(0,0,0,0.2)]" 
                onclick={(e) => e.stopPropagation()}
                onkeydown={(e) => e.key === 'Escape' && (showAccountMenu = false)}
                role="presentation"
              >
                <div class="absolute -top-1.5 right-[22px] w-3 h-3 bg-white border-t border-l border-gray-100 rotate-45 z-[51]"></div>
                <div class="bg-white/98 backdrop-blur-3xl rounded-none border border-gray-100 overflow-hidden shadow-2xl relative z-50">
                  <div class="px-5 py-4 bg-gradient-to-br from-gray-50/80 to-white flex items-center gap-3 border-b border-gray-100">
                    <div class="w-10 h-10 rounded-none bg-gradient-to-tr from-[#C18F7E] to-[#E3B5A4] flex items-center justify-center text-white font-bold text-sm shadow-lg ring-2 ring-white">S</div>
                    <div class="flex flex-col">
                      <span class="text-gray-800 font-bold text-[15px]">Xin chào!</span>
                      <span class="text-[#C18F7E] text-[9.5px] font-black uppercase tracking-[0.15em] bg-[#C18F7E]/10 px-2 py-0.5 rounded-none w-fit mt-1 ring-1 ring-[#C18F7E]/20">Thành viên Cao Cấp</span>
                    </div>
                  </div>
                  <div class="p-0 flex flex-col text-left">
                    <a href="/user/profile" class="flex items-center justify-between px-5 py-3 text-[13px] text-gray-700 hover:bg-gradient-to-r hover:from-[#C18F7E] hover:to-[#E3B5A4] hover:text-white transition-all duration-300 group/item">
                      <div class="flex items-center gap-3"><svg xmlns="http://www.w3.org/2000/svg" class="w-4.5 h-4.5 opacity-70 group-hover/item:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg><span class="font-medium">Tài khoản của tôi</span></div>
                    </a>
                    <a href="/user/purchase" class="flex items-center justify-between px-5 py-3 text-[13px] text-gray-700 hover:bg-gradient-to-r hover:from-[#C18F7E] hover:to-[#E3B5A4] hover:text-white transition-all duration-300 group/item border-t border-gray-50/50">
                      <div class="flex items-center gap-3"><svg xmlns="http://www.w3.org/2000/svg" class="w-4.5 h-4.5 opacity-70 group-hover/item:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg><span class="font-medium">Đơn mua</span></div>
                      <span class="bg-[#C18F7E] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-none group-hover/item:bg-white group-hover/item:text-[#C18F7E]">3</span>
                    </a>
                    <button class="flex items-center gap-3 px-5 py-3 text-[13px] text-red-500 hover:bg-red-50 transition-all duration-300 group/item w-full border-t border-gray-50/50 text-left"><svg xmlns="http://www.w3.org/2000/svg" class="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg><span class="font-semibold">Đăng xuất</span></button>
                  </div>
                </div>
              </div>
            {/if}
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
