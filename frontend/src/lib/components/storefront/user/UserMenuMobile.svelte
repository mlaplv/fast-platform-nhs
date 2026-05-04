<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex';
  import { page } from '$app/state';
  import { authStore } from '$lib/state/authStore.svelte';
  import { goto } from '$app/navigation';
  import { X, LogOut, ChevronRight, Home, User as UserIcon, Package, MapPin, Key, Bell, Sparkles, Ticket } from 'lucide-svelte';

  interface Props {
    active: boolean;
    onClose: () => void;
  }
  let { active = $bindable(), onClose }: Props = $props();

  const links = [
    { label: 'Hồ sơ', href: '/user/profile', icon: UserIcon },
    { label: 'Đơn mua', href: '/user/purchase', icon: Package },
    { label: 'Kho Voucher', href: '/user/vouchers', icon: Ticket },
    { label: 'Tích điểm', href: '/user/loyalty', icon: Sparkles },
    { label: 'Địa chỉ', href: '/user/address', icon: MapPin },
    { label: 'Mật khẩu', href: '/user/password', icon: Key },
    { label: 'Thông báo', href: '/user/notifications', icon: Bell },
  ];


  function handleLogout() {
    authStore.logout();
    onClose();
    goto('/');
  }
</script>

{#if active}
  <div
    class="fixed inset-0 bg-white"
    style="z-index: {Z_INDEX_CLIENT.MODAL};"
    transition:fade={{ duration: 300 }}
  >
    <!-- Background Aesthetic -->
    <div class="absolute inset-0 opacity-[0.03] pointer-events-none">
       <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="menu-grid" width="30" height="30" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="1" fill="#c5a059" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#menu-grid)" />
       </svg>
    </div>

    <div
      class="relative h-full flex flex-col p-6 overflow-y-auto no-scrollbar"
      style="padding-top: calc(env(safe-area-inset-top) + 1.5rem);"
    >
      <!-- Header Area -->
      <div class="flex items-center justify-between mb-12">
        <div class="flex items-center gap-3" in:fly={{ x: -20, duration: 600 }}>
           <div class="w-10 h-10 rounded-full bg-luxury-copper/10 flex items-center justify-center">
              <Sparkles class="w-5 h-5 text-luxury-copper" />
           </div>
           <div>
             <h2 class="text-[13px] font-black uppercase tracking-[3px] text-stone-900">osmo Elite</h2>
             <p class="text-[9px] text-stone-400 uppercase tracking-widest mt-0.5">Luxury Experience</p>
           </div>
        </div>

        <button
          onclick={onClose}
          class="w-10 h-10 flex items-center justify-center rounded-full bg-stone-50 text-stone-900 active:scale-90 transition-transform"
        >
          <X class="w-6 h-6" />
        </button>
      </div>

      <!-- Navigation Links -->
      <div class="flex-1 space-y-12">
        <div class="space-y-6">
          <p class="text-[10px] uppercase tracking-[5px] text-stone-400 font-bold opacity-60" in:fade={{ delay: 100 }}>Tài khoản của tôi</p>
          <nav class="space-y-2">
            {#each links as link, i}
              <div in:fly={{ x: -20, delay: 100 + i * 50, duration: 600 }}>
                <a
                  href={link.href}
                  onclick={onClose}
                  class="flex items-center justify-between py-5 border-b border-stone-50 group relative overflow-hidden"
                >
                  <div class="flex items-center gap-5">
                    <div class="w-10 h-10 rounded-full flex items-center justify-center transition-all {page.url.pathname === link.href ? 'bg-luxury-copper text-white' : 'bg-stone-50 text-stone-400 group-active:text-luxury-copper'}">
                       <link.icon class="w-4 h-4" />
                    </div>
                    <span class="text-xl font-serif italic tracking-wide transition-colors {page.url.pathname === link.href ? 'text-stone-900' : 'text-stone-500 group-active:text-stone-900'}">
                      {link.label}
                    </span>
                  </div>

                  <ChevronRight
                    class="w-5 h-5 transition-transform group-active:translate-x-1 {page.url.pathname === link.href ? 'text-luxury-copper' : 'text-stone-200'}"
                  />

                  {#if page.url.pathname === link.href}
                    <div class="absolute bottom-0 left-0 w-full h-[1px] bg-luxury-copper"></div>
                  {/if}
                </a>
              </div>
            {/each}
          </nav>
        </div>

        <div class="space-y-6" in:fade={{ delay: 400 }}>
           <p class="text-[10px] uppercase tracking-[5px] text-stone-400 font-bold opacity-60">Khám phá</p>
           <a
             href="/"
             onclick={onClose}
             class="flex items-center gap-5 py-2 group"
           >
              <div class="w-10 h-10 rounded-full bg-stone-50 text-stone-400 flex items-center justify-center transition-all group-active:text-luxury-copper">
                 <Home class="w-4 h-4" />
              </div>
              <span class="text-lg font-serif italic text-stone-500 group-active:text-stone-900">Về trang chủ</span>
           </a>
        </div>
      </div>

      <!-- Footer Area -->
      <div class="pt-10 pb-6" in:fade={{ delay: 500 }}>
        <button
          onclick={handleLogout}
          class="w-full group relative py-4 bg-stone-50 overflow-hidden transition-all duration-500 active:scale-[0.98]"
        >
          <div class="absolute inset-0 bg-red-50 translate-x-[-100%] group-active:translate-x-0 transition-transform duration-500"></div>
          <div class="relative z-10 flex items-center justify-center gap-3">
            <LogOut class="w-4 h-4 text-stone-400 group-active:text-red-500" />
            <span class="text-[11px] uppercase tracking-[4px] font-black text-stone-400 group-active:text-red-500">
              Đăng xuất tài khoản
            </span>
          </div>
        </button>

        <p class="text-[9px] text-center text-stone-300 uppercase tracking-[2px] mt-8">
          Elite Member Experience • osmo 2026
        </p>
      </div>
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
  :global(.text-luxury-copper) {
    color: #c5a059;
  }
  :global(.bg-luxury-copper) {
    background-color: #c5a059;
  }
</style>
