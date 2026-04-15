<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { goto } from '$app/navigation';
  import { Bell, User, ShoppingBag, MapPin, Lock, LogOut } from 'lucide-svelte';

  const menuItems = [
    {
      label: 'Tài khoản của tôi',
      icon: User,
      href: '/user/profile',
      subItems: [
        { label: 'Hồ sơ', href: '/user/profile', icon: User },
        { label: 'Địa chỉ', href: '/user/address', icon: MapPin },
        { label: 'Đổi mật khẩu', href: '/user/password', icon: Lock }
      ]
    },
    {
      label: 'Đơn mua',
      icon: ShoppingBag,
      href: '/user/purchase'
    },
    {
      label: 'Thông báo',
      icon: Bell,
      href: '/user/notifications'
    }
  ];

  function handleLogout() {
    authStore.logout();
    goto('/');
  }
</script>

<div class="fixed inset-0 bg-white z-[var(--z-modal)] flex flex-col">
    <!-- Header -->
    <header class="h-14 flex items-center px-4 border-b border-gray-100 shrink-0">
        <button onclick={() => history.back()} class="mr-4">
            <svg class="w-6 h-6 text-gray-800" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <span class="text-sm font-bold uppercase tracking-wider text-gray-900">Tài khoản của tôi</span>
    </header>

    <!-- Content -->
    <div class="flex-grow overflow-y-auto p-4 space-y-8">
        <div class="flex items-center gap-3">
             <div class="w-12 h-12 rounded-full overflow-hidden border border-stone-100 p-0.5">
                {#if authStore.user?.avatar_url}
                    <img src={authStore.user.avatar_url} alt="Avatar" class="w-full h-full object-cover rounded-full" />
                {:else}
                    <div class="w-full h-full flex items-center justify-center text-sm font-serif italic text-luxury-copper bg-stone-50 rounded-full">
                        {authStore.user?.name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                {/if}
            </div>
            <span class="text-[15px] font-bold text-stone-800 uppercase tracking-wider">{authStore.user?.name || 'Quý khách'}</span>
        </div>

        <nav class="space-y-6">
          {#each menuItems as item}
            <div class="space-y-4">
              <a href={item.href} class="flex items-center gap-3 text-xs uppercase tracking-[2px] font-bold text-stone-800">
                <item.icon class="w-4 h-4 text-luxury-copper" />
                {item.label}
              </a>
              {#if item.subItems}
                <div class="flex flex-col ml-7 space-y-3 pl-4 border-l border-stone-100">
                  {#each item.subItems as sub}
                    <a href={sub.href} class="text-sm text-stone-600">{sub.label}</a>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        </nav>

        <button onclick={handleLogout} class="flex items-center gap-3 text-xs uppercase tracking-[2px] font-bold text-stone-500 w-full pt-6 border-t border-gray-100">
            <LogOut class="w-4 h-4" />
            Đăng xuất
        </button>
    </div>
</div>
