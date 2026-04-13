<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { page } from '$app/stores';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();

  const menuItems = [
    {
      label: 'Tài khoản của tôi',
      icon: '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>',
      href: '/user/profile',
      subItems: [
        { label: 'Hồ sơ', href: '/user/profile' },
        { label: 'Địa chỉ', href: '/user/address' },
        { label: 'Đổi mật khẩu', href: '/user/password' }
      ]
    },
    {
      label: 'Đơn mua',
      icon: '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>',
      href: '/user/purchase'
    }
  ];

  const currentPath = $derived($page.url.pathname);
</script>

<div class="max-w-[1200px] mx-auto px-4 xl:px-0 py-10 flex gap-7 min-h-[600px]">
  <!-- Sidebar -->
  <aside class="w-[180px] shrink-0">
    <div class="flex items-center gap-3 mb-8 px-1">
      <div class="w-12 h-12 rounded-full overflow-hidden border border-gray-100 bg-gray-50 shrink-0 shadow-sm">
        {#if authStore.user?.avatar_url}
          <img src={authStore.user.avatar_url} alt="Avatar" class="w-full h-full object-cover" />
        {:else}
          <div class="w-full h-full flex items-center justify-center text-sm font-black text-luxury-copper ring-1 ring-inset ring-black/5">
            {authStore.user?.name?.charAt(0).toUpperCase()}
          </div>
        {/if}
      </div>
      <div class="flex flex-col min-w-0">
        <span class="text-[14px] font-bold text-gray-900 truncate">{authStore.user?.username || authStore.user?.name}</span>
        <a href="/user/profile" class="text-[12px] text-gray-400 flex items-center gap-1 hover:text-gray-600 transition-colors">
          <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
          Sửa hồ sơ
        </a>
      </div>
    </div>

    <nav class="space-y-4">
      {#each menuItems as item}
        <div class="space-y-2">
          <a 
            href={item.href} 
            class="flex items-center gap-3 text-[14px] font-medium transition-colors {currentPath.startsWith(item.href) ? 'text-luxury-copper' : 'text-gray-700 hover:text-luxury-copper'}"
          >
            <span class="text-gray-400">{@html item.icon}</span>
            {item.label}
          </a>
          
          {#if item.subItems && currentPath.startsWith(item.href)}
            <div class="flex flex-col ml-8 space-y-2.5">
              {#each item.subItems as sub}
                <a 
                  href={sub.href} 
                  class="text-[13.5px] transition-colors {currentPath === sub.href ? 'text-luxury-copper font-semibold' : 'text-gray-600 hover:text-luxury-copper'}"
                >
                  {sub.label}
                </a>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </nav>
  </aside>

  <!-- Content -->
  <main class="flex-grow bg-white shadow-[0_1px_2px_0_rgba(0,0,0,0.05)] rounded-[2px] p-8 border border-gray-50">
    {@render children()}
  </main>
</div>
