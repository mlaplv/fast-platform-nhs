<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import { getNotificationState } from '$lib/state/notification.svelte';
  import { Bell, Package, User, LogIn, Check } from 'lucide-svelte';
  import { formatDate } from '$lib/utils/format';
  import { fade, fly } from 'svelte/transition';

  const notifStore = getNotificationState();

  const getIcon = (type: string) => {
    switch(type) {
      case 'ORDER': return Package;
      case 'USER': return User;
      case 'AUTH': return LogIn;
      default: return Bell;
    }
  };

  async function markAllAsRead() {
    const unreadIds = notifStore.notifications.filter(n => !n.isRead).map(n => n.id);
    for (const id of unreadIds) {
      await notifStore.markNotificationAsRead(id);
    }
  }

  onMount(() => {
    untrack(() => {
      notifStore.fetchNotifications();
    });
  });

  let isLoading = $derived(notifStore.isLoading);
</script>

<div class="space-y-8" in:fade={{ duration: 400 }}>
  <div class="flex items-center justify-between border-b border-stone-100 pb-4">
    <div class="flex items-center gap-2">
      <div class="w-1.5 h-1.5 rounded-full bg-luxury-copper animate-pulse"></div>
      <h2 class="text-[12px] font-black uppercase tracking-[3px] text-stone-800">Thông báo của Quý khách</h2>
    </div>
    {#if notifStore.unreadCount > 0}
      <button
        onclick={markAllAsRead}
        class="text-[10px] font-bold uppercase tracking-widest text-luxury-copper hover:text-stone-900 transition-colors"
      >
        Đánh dấu tất cả đã đọc
      </button>
    {/if}
  </div>

  {#if isLoading}
    <div class="py-20 flex flex-col items-center justify-center space-y-4">
      <div class="w-8 h-8 border-2 border-luxury-copper border-t-transparent animate-spin rounded-full"></div>
      <p class="text-[10px] text-stone-400 uppercase tracking-widest animate-pulse">Đang truy xuất thông báo...</p>
    </div>
  {:else}
    {#if notifStore.notifications.length === 0}
      <div class="py-20 text-center border-2 border-dashed border-stone-50 rounded-2xl" in:fade>
        <div class="w-16 h-16 bg-stone-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <Bell class="w-8 h-8 text-stone-200" />
        </div>
        <p class="text-stone-400 font-serif italic">Hộp thư hiện đang trống.</p>
      </div>
    {:else}
      <div class="space-y-4">
        {#each notifStore.notifications as notif, i (notif.id)}
          {@const Icon = getIcon(notif.type)}
          <div
            class="group relative flex gap-5 p-5 transition-all duration-500 hover:bg-stone-50/50 rounded-xl {notif.isRead ? 'opacity-50 grayscale-[0.5]' : 'bg-white shadow-[0_4px_20px_rgba(0,0,0,0.02)]'}"
            in:fly={{ y: 20, delay: i * 50 }}
          >
            {#if !notif.isRead}
              <div class="absolute top-5 left-2 w-1.5 h-1.5 rounded-full bg-luxury-copper"></div>
            {/if}

            <div class="w-12 h-12 rounded-full bg-stone-50 border border-stone-100 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-500">
              <Icon class="w-5 h-5 text-luxury-copper" />
            </div>

            <div class="flex-1 space-y-2">
              <p class="text-[14px] text-stone-800 leading-relaxed font-medium">
                {notif.message}
              </p>
              <div class="flex items-center gap-3">
                <span class="text-[9px] text-stone-400 font-black uppercase tracking-[2px]">{formatDate(notif.created_at)}</span>
                {#if !notif.isRead}
                  <span class="w-1 h-1 rounded-full bg-stone-200"></span>
                  <span class="text-[9px] text-luxury-copper font-black uppercase tracking-[2px]">Mới</span>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}

  <div class="pt-10 flex items-center justify-center opacity-10">
     <div class="h-px w-24 bg-stone-900"></div>
  </div>
</div>

<style>
  :global(.text-luxury-copper) {
    color: #c5a059;
  }
</style>
