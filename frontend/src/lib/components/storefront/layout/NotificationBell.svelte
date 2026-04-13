<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import { getContext, onMount } from 'svelte';
  import { Bell, BellRing, Package, User, LogIn, Settings } from 'lucide-svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  
  // Assuming notification state is available via context or import
  // For Elite V3.0, we use a global notification state
  import { createNotificationState } from '$lib/state/notification.svelte';
  
  import { getNotificationState } from '$lib/state/notification.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  
  const ui = getClientUi();
  const notifStore = getNotificationState();

  let isOpen = $state(false);
  let bellContainer = $state<HTMLElement>();

  onMount(() => {
    // Only fetch if authenticated and empty to prevent redundant requests
    if (authStore.isAuthenticated && notifStore.notifications.length === 0) {
      notifStore.fetchNotifications();
    }

    const handleOutsideClick = (e: MouseEvent) => {
      if (bellContainer && !bellContainer.contains(e.target as Node)) {
        isOpen = false;
      }
    };
    window.addEventListener('click', handleOutsideClick);
    return () => window.removeEventListener('click', handleOutsideClick);
  });

  const getIcon = (type: string) => {
    switch(type) {
      case 'ORDER': return Package;
      case 'USER': return User;
      case 'AUTH': return LogIn;
      default: return Bell;
    }
  };
</script>

<div class="relative flex items-center" bind:this={bellContainer}>
  <button 
    onclick={() => isOpen = !isOpen}
    class="relative p-2 group transition-all duration-300"
  >
    {#if notifStore.unreadCount > 0}
      <BellRing class="w-5 h-5 text-luxury-copper animate-pulse" />
      <span class="absolute top-1.5 right-1.5 w-3.5 h-3.5 bg-red-500 text-white text-[8px] font-black rounded-full flex items-center justify-center border-2 border-white pointer-events-none ring-2 ring-red-500/20">
        {notifStore.unreadCount}
      </span>
    {:else}
      <Bell class="w-5 h-5 text-gray-500 group-hover:text-luxury-copper transition-colors" />
    {/if}
  </button>

  {#if isOpen}
    <div 
      in:fly={{ y: 10, duration: 400 }} 
      out:fade={{ duration: 200 }}
      class="absolute right-[-40px] top-[calc(100%+12px)] w-80 z-[var(--z-toast)] origin-top-right"
    >
      <!-- Premium Glass Menu - Liquid Aesthetic -->
      <div class="bg-white/98 backdrop-blur-2xl border border-gray-100 shadow-[0_30px_80px_-15px_rgba(0,0,0,0.25)] rounded-2xl overflow-hidden ring-1 ring-black/5">
        
        <div class="px-4 py-3 bg-gray-50/50 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-[12px] font-black uppercase tracking-widest text-gray-800">Thông báo Pulse</h3>
          <button 
            onclick={() => notifStore.fetchNotifications()}
            class="text-[10px] text-luxury-copper font-bold hover:underline"
          >
            Làm mới
          </button>
        </div>

        <div class="max-h-[360px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-200">
          {#if notifStore.notifications.length > 0}
            <div class="flex flex-col divide-y divide-gray-50">
              {#each notifStore.notifications as notif (notif.id)}
                {@const Icon = getIcon(notif.type)}
                <button 
                  onclick={() => {
                    notifStore.markNotificationAsRead(notif.id);
                  }}
                  class="px-4 py-3 text-left hover:bg-gray-50/80 transition-all group flex gap-3 {notif.isRead ? 'opacity-60' : ''}"
                >
                  <div class="mt-1">
                    <Icon class="w-4 h-4 {notif.isRead ? 'text-gray-400' : 'text-luxury-copper'}" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-[12px] text-gray-800 font-medium leading-[1.4] mb-1">
                      {notif.message}
                    </p>
                    <span class="text-[9px] text-gray-400 font-bold uppercase tracking-tighter">
                      {new Date(notif.created_at).toLocaleString('vi-VN')}
                    </span>
                  </div>
                  {#if !notif.isRead}
                    <div class="mt-2 w-1.5 h-1.5 rounded-full bg-luxury-copper"></div>
                  {/if}
                </button>
              {/each}
            </div>
          {:else}
            <div class="px-8 py-12 text-center">
              <Bell class="w-8 h-8 text-gray-200 mx-auto mb-3" />
              <p class="text-[11px] text-gray-400 font-medium uppercase tracking-widest leading-loose">
                Hiện tại chưa có<br/>thông báo mới nào
              </p>
            </div>
          {/if}
        </div>

        <div class="px-4 py-3 bg-gray-50/50 border-t border-gray-100 text-center">
          <a href="/user/notifications" class="text-[11px] font-black text-gray-500 hover:text-luxury-copper transition-colors uppercase tracking-widest">
            Xem tất cả thông báo
          </a>
        </div>
      </div>
    </div>
  {/if}
</div>
