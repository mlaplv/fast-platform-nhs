<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import { authStore } from '$lib/state/authStore.svelte';
  import UserLayout from '$lib/components/storefront/user/UserLayout.svelte';
  import { getNotificationState } from '$lib/state/notification.svelte';
  import { fade, fly } from 'svelte/transition';
  import { Bell, Package, User, LogIn, Check, Trash2, BellRing } from 'lucide-svelte';
  import { formatDate } from '$lib/utils/format';

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
    // Assuming there's a bulk action or just loop through unread
    const unreadIds = notifStore.notifications.filter(n => !n.isRead).map(n => n.id);
    for (const id of unreadIds) {
      await notifStore.markNotificationAsRead(id);
    }
  }

  onMount(() => {
    // CNS V90: One-time fetch on mount to prevent infinite loop (Fix 429 Error)
    if (authStore.isAuthenticated) {
      untrack(() => {
        notifStore.fetchNotifications();
      });
    }
  });
</script>

<UserLayout>
  <div class="space-y-8" in:fade>
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-stone-100 pb-5">
      <div>
        <h1 class="text-xl font-serif italic text-stone-800 tracking-wide">Thông Báo</h1>
        <p class="text-[13px] text-stone-400 mt-1 uppercase tracking-widest">Cập nhật những Bài viết mới nhất dành cho bạn</p>
      </div>

      {#if notifStore.unreadCount > 0}
        <button
          onclick={markAllAsRead}
          class="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-luxury-copper hover:text-stone-800 transition-colors"
        >
          <Check class="w-4 h-4" />
          Đánh dấu tất cả đã đọc
        </button>
      {/if}
    </div>

    <!-- Notification List -->
    <div class="space-y-4">
      {#if notifStore.notifications.length === 0}
        <div class="py-24 text-center border-2 border-dashed border-stone-50 rounded-lg">
          <div class="w-20 h-20 bg-stone-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <Bell class="w-10 h-10 text-stone-200" />
          </div>
          <p class="text-stone-400 font-serif italic">Hiện tại bạn chưa có thông báo nào.</p>
        </div>
      {:else}
        {#each notifStore.notifications as notif (notif.id)}
          {@const Icon = getIcon(notif.type)}
          <div
            class="group relative bg-white p-6 border border-stone-100 transition-all duration-500 hover:border-stone-200 hover:shadow-[0_10px_30px_rgba(0,0,0,0.03)] flex gap-6 {notif.isRead ? 'opacity-60' : ''}"
            in:fly={{ y: 10 }}
          >
            <div class="shrink-0">
              <div class="w-12 h-12 rounded-full flex items-center justify-center {notif.isRead ? 'bg-stone-50 text-stone-300' : 'bg-stone-50 text-luxury-copper'}">
                <Icon class="w-6 h-6" />
              </div>
            </div>

            <div class="flex-1 space-y-2">
              <div class="flex items-start justify-between gap-4">
                <p class="text-[14px] text-stone-800 font-medium leading-relaxed">
                  {notif.message}
                </p>
                {#if !notif.isRead}
                  <div class="mt-1.5 w-2 h-2 rounded-full bg-luxury-copper shrink-0 animate-pulse"></div>
                {/if}
              </div>

              <div class="flex items-center justify-between">
                <span class="text-[10px] text-stone-400 font-bold uppercase tracking-widest">
                  {formatDate(notif.created_at)}
                </span>

                {#if !notif.isRead}
                  <button
                    onclick={() => notifStore.markNotificationAsRead(notif.id)}
                    class="text-[10px] text-luxury-copper font-black uppercase tracking-tighter opacity-0 group-hover:opacity-100 transition-opacity hover:underline"
                  >
                    Đánh dấu đã đọc
                  </button>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      {/if}
    </div>

    <!-- Aesthetic Branding -->
    <div class="pt-16 text-center opacity-30">
       <div class="flex items-center justify-center gap-4 mb-2">
          <div class="h-[1px] w-20 bg-stone-200"></div>
          <span class="text-[10px] font-serif italic uppercase tracking-[5px] text-stone-800">Micsmo Zen Living</span>
          <div class="h-[1px] w-20 bg-stone-200"></div>
       </div>
    </div>
  </div>
</UserLayout>
