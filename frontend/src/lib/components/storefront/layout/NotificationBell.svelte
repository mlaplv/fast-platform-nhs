<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { onMount } from 'svelte';
  import Bell from "@lucide/svelte/icons/bell";
  import BellRing from "@lucide/svelte/icons/bell-ring";
  import Package from "@lucide/svelte/icons/package";
  import User from "@lucide/svelte/icons/user";
  import LogIn from "@lucide/svelte/icons/log-in";
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getNotificationState } from '$lib/state/notification.svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import { browser } from '$app/environment';
  import { formatDate } from '$lib/utils/format';

  import { untrack } from 'svelte';

  const ui = getClientUi();
  const notifStore = getNotificationState();

  let isOpen = $state(false);
  let bellContainer = $state<HTMLElement>();

  // Elite V3.0 Reactivity: Automatically fetch when authenticated
  // CNS V89: Using untrack and small delay to prevent hydration race conditions (Fix 409 Conflict)
  $effect(() => {
    if (browser && authStore.isAuthenticated) {
      const timer = setTimeout(() => {
        untrack(() => {
          notifStore.fetchNotifications();
        });
      }, 300);
      return () => clearTimeout(timer);
    } else {
      isOpen = false;
    }
  });

  onMount(() => {
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

  // Elite V3.2: Filter out technical/admin metrics from storefront view
  const userNotifications = $derived(
    notifStore.notifications.filter(n => {
      const msg = n.message.toLowerCase();
      const isTechnical = msg.includes('độ trễ') || msg.includes('latency') || msg.includes('tăng cao');
      return !isTechnical;
    })
  );

  const unreadCount = $derived(userNotifications.filter(n => !n.isRead).length);
</script>

<div class="relative flex items-center h-full" bind:this={bellContainer}>
  <button 
    onclick={() => isOpen = !isOpen}
    class="flex items-center gap-1 group transition-all duration-300 px-2 py-1 hover:text-luxury-copper"
  >
    <div class="relative flex items-center justify-center">
      {#if unreadCount > 0}
        <BellRing class="w-[18px] h-[18px] text-luxury-copper animate-pulse" />
        <span class="absolute -top-1.5 -right-1.5 min-w-[14px] h-[14px] px-0.5 bg-red-500 text-white text-[8px] font-black rounded-full flex items-center justify-center border border-white pointer-events-none shadow-sm ring-1 ring-red-500/10">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      {:else}
        <Bell class="w-[18px] h-[18px] text-gray-500 group-hover:text-luxury-copper transition-colors" />
      {/if}
    </div>
    <span class="text-[11px] font-medium text-gray-500 group-hover:text-luxury-copper transition-colors">Thông Báo</span>
  </button>

  {#if isOpen}
    <div 
      in:fly={{ y: 8, duration: 400, opacity: 0 }} 
      out:fade={{ duration: 200 }}
      class="absolute right-0 top-[calc(100%+8px)] w-80 z-[var(--z-toast)] origin-top-right"
    >
      <!-- Arrow Indicator -->
      <div class="absolute -top-1 right-[24px] w-3 h-3 bg-white rotate-45 z-[0] border-t border-l border-black/5 shadow-[-2px_-2px_5px_rgba(0,0,0,0.02)]"></div>

      <!-- Premium Glass Menu - Liquid Aesthetic -->
      <div class="relative z-[1] bg-white/98 backdrop-blur-2xl border border-gray-100 shadow-[0_20px_50px_-12px_rgba(0,0,0,0.15)] rounded-xl overflow-hidden ring-1 ring-black/5">
        
        <div class="px-4 py-3 bg-gray-50/50 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-[11px] font-black tracking-widest text-gray-800">Thông báo mới nhận</h3>
          <button 
            onclick={() => notifStore.fetchNotifications()}
            class="text-[10px] text-luxury-copper font-bold hover:underline"
          >
            Làm mới
          </button>
        </div>

        <div class="max-h-[360px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-200">
          {#if userNotifications.length > 0}
            <div class="flex flex-col divide-y divide-gray-50">
              {#each userNotifications as notif (notif.id)}
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
                    <span class="text-[9px] text-gray-400 font-bold tracking-tighter">
                      {formatDate(notif.created_at)}
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
              <div class="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-gray-100">
                <Bell class="w-6 h-6 text-gray-200" />
              </div>
              <p class="text-[11px] text-gray-400 font-medium tracking-widest leading-loose">
                Hiện tại chưa có<br/>thông báo mới nào
              </p>
            </div>
          {/if}
        </div>

        <div class="px-4 py-3 bg-gray-50/50 border-t border-gray-100 text-center">
          <a href="/user/notifications" class="text-[11px] font-black text-gray-500 hover:text-luxury-copper transition-colors tracking-widest block w-full">
            Xem tất cả thông báo
          </a>
        </div>
      </div>
    </div>
  {/if}
</div>

