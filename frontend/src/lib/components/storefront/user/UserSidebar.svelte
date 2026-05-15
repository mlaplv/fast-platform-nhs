<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { page } from '$app/stores';
  import Bell from "@lucide/svelte/icons/bell";
  import UserIcon from "@lucide/svelte/icons/user";
  import ShoppingBag from "@lucide/svelte/icons/shopping-bag";
  import MapPin from "@lucide/svelte/icons/map-pin";
  import Lock from "@lucide/svelte/icons/lock";
  import LogOut from "@lucide/svelte/icons/log-out";
  import Ticket from "@lucide/svelte/icons/ticket";
  import Star from "@lucide/svelte/icons/star";
  import { goto } from '$app/navigation';
  import Avatar from './Avatar.svelte';

  const menuItems = [
    {
      label: 'Tài khoản của tôi',
      icon: UserIcon,
      href: '/user/profile',
      subItems: [
        { label: 'Hồ sơ', href: '/user/profile', icon: UserIcon },
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
      label: 'Kho Voucher',
      icon: Ticket,
      href: '/user/vouchers'
    },
    {
      label: 'Điểm thưởng',
      icon: Star,
      href: '/user/loyalty'
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

  const currentPath = $derived($page.url.pathname);
</script>

<aside class="w-full md:w-[240px] shrink-0 hidden md:block space-y-10">
  <!-- Profile Header -->
  <div class="flex items-center gap-4 px-2">
    <Avatar
      src={authStore.user?.avatar_url}
      name={authStore.user?.name}
      size="sm"
      class="w-14 h-14 !p-0.5 shadow-sm"
    />
    <div class="flex flex-col min-w-0">
      <span class="text-[14px] font-bold text-stone-800 truncate tracking-wider">{authStore.user?.name || 'Quý khách'}</span>
      <a href="/user/profile" class="text-[11px] text-stone-400 tracking-widest flex items-center gap-1.5 hover:text-luxury-copper transition-colors mt-1">
        <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
        Tùy chỉnh
      </a>
    </div>
  </div>

  <!-- Navigation -->
  <nav class="flex flex-col h-full bg-transparent p-0">
    <div class="space-y-8 flex-grow">
      {#each menuItems as item}
        <div class="space-y-4">
          <a
            href={item.href}
            class="flex items-center gap-3 text-[12px] tracking-[2px] font-bold transition-all {currentPath.startsWith(item.href) ? 'text-stone-800' : 'text-stone-400 hover:text-stone-600'}"
          >
            <span class="{currentPath.startsWith(item.href) ? 'text-luxury-copper' : 'text-stone-300'}">
              <item.icon class="w-4 h-4" />
            </span>
            {item.label}
          </a>

          {#if item.subItems && (currentPath.startsWith(item.href) || item.subItems.some(s => s.href === currentPath))}
            <div class="flex flex-col ml-8 space-y-3 border-l border-stone-100 pl-4">
              {#each item.subItems as sub}
                <a
                  href={sub.href}
                  class="text-[13px] transition-all relative group {currentPath === sub.href ? 'text-luxury-copper font-medium' : 'text-stone-500 hover:text-stone-800'}"
                >
                  {sub.label}
                  {#if currentPath === sub.href}
                    <div class="absolute -left-[17px] top-1/2 -translate-y-1/2 w-1 h-1 bg-luxury-copper rounded-full"></div>
                  {/if}
                </a>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <!-- Logout Button -->
    <div class="pt-8 mt-8 border-t border-stone-100">
      <button
        onclick={handleLogout}
        class="flex items-center gap-3 text-[12px] tracking-[2px] font-bold text-stone-400 hover:text-red-400 transition-all w-full text-left"
      >
        <LogOut class="w-4 h-4" />
        Đăng xuất
      </button>
    </div>
  </nav>
</aside>
