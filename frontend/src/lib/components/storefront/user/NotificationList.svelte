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
</script>

<div class="space-y-4" in:fade>
  <div class="flex items-center justify-between">
    <h2 class="text-[12px] font-black uppercase tracking-widest text-stone-600">Thông báo</h2>
    {#if notifStore.unreadCount > 0}
      <button onclick={markAllAsRead} class="text-[10px] font-bold uppercase text-luxury-copper hover:underline">
        Đọc tất cả
      </button>
    {/if}
  </div>

  {#if notifStore.notifications.length === 0}
    <div class="py-10 text-center text-stone-400 italic text-sm">Không có thông báo mới.</div>
  {:else}
    {#each notifStore.notifications as notif (notif.id)}
      {@const Icon = getIcon(notif.type)}
      <div class="flex gap-4 p-4 border-b border-stone-50 {notif.isRead ? 'opacity-60' : ''}">
        <div class="w-10 h-10 rounded-full bg-stone-50 flex items-center justify-center shrink-0">
          <Icon class="w-5 h-5 text-luxury-copper" />
        </div>
        <div class="flex-1 space-y-1">
          <p class="text-[13px] text-stone-800 leading-relaxed">{notif.message}</p>
          <span class="text-[9px] text-stone-400 font-bold uppercase">{formatDate(notif.created_at)}</span>
        </div>
      </div>
    {/each}
  {/if}
</div>