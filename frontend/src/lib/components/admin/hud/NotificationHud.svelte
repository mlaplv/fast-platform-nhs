<script lang="ts">
  import { fade, slide, scale } from "svelte/transition";
  import LucideBell from "@lucide/svelte/icons/bell";
  import LucideActivity from "@lucide/svelte/icons/activity";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import type { Notification } from "$lib/state/types";
  const nanobot = useNanobot();

  function toggleDropdown() {
    nanobot.toggleHudPopup("NOTIFICATIONS");
    if (nanobot.activeHudPopup === "NOTIFICATIONS") {
      nanobot.fetchNotifications();
    }
  }

  async function handleNotificationClick(note: Notification) {
    // 1. Mark as read
    nanobot.markNotificationAsRead(note.id);
    
    // 2. Close notification dropdown
    nanobot.toggleHudPopup("NOTIFICATIONS");
    
    // 3. Routing logic based on notification type and payload
    const type = note.type?.toUpperCase() || "";
    const payload = note.payload || {};
    
    if (type === "ORDER" || type === "ORDER_CANCEL") {
      const orderId = payload.order_id || note.id;
      nanobot.openWidget("ORDER_MANAGEMENT", { order_id: orderId } as unknown as import("$lib/state/types").CampaignData);
    } else if (type === "URGENT_SUPPORT") {
      const phone = payload.phone || "";
      nanobot.setSupportSearchTerm(phone);
      nanobot.openWidget("SUPPORT_INBOX", { session_id: "" } as unknown as import("$lib/state/types").CampaignData);
    } else if (type === "CHAT" || type === "SUPPORT_INBOX" || note.id.startsWith("chat-")) {
      const sessionId = payload.session_id || note.id.split("-")[1] || "";
      nanobot.openWidget("SUPPORT_INBOX", { session_id: sessionId } as unknown as import("$lib/state/types").CampaignData);
    } else if (type === "CONTENT_CREATE") {
      const campaignId = payload.campaign_id || note.id;
      nanobot.openWidget("CAMPAIGNS", { campaign_id: campaignId } as unknown as import("$lib/state/types").CampaignData);
    }
  }

  $effect(() => {
    let interval: ReturnType<typeof setInterval>;
    
    function startPolling() {
      if (interval) clearInterval(interval);
      interval = setInterval(() => {
        // R1.10: Smart Lifecycle - Only poll if tab is active and visible
        if (document.visibilityState === 'visible') {
            nanobot.fetchNotifications();
        }
      }, 30000); // 30s polling
    }

    function handleVisibility() {
        if (document.visibilityState === 'visible') {
            nanobot.fetchNotifications(); // Fetch immediately on return
            startPolling();
        } else {
            if (interval) clearInterval(interval); // Stop polling when hidden
        }
    }

    startPolling();
    document.addEventListener('visibilitychange', handleVisibility);

    return () => {
        if (interval) clearInterval(interval);
        document.removeEventListener('visibilitychange', handleVisibility);
    };
  });
</script>

<div class="relative">
  <button
    onclick={toggleDropdown}
    class="p-2 rounded-lg bg-white/5 border border-white/10 hover:border-[#00FFFF]/50 hover:bg-[#00FFFF]/5 transition-all relative group"
  >
    <LucideBell
      size={18}
      class="text-gray-400 group-hover:text-[#00FFFF] transition-colors"
    />
    {#if nanobot.unreadNotificationsCount > 0}
      <span
        class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-black animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]"
      ></span>
    {/if}
  </button>

  {#if nanobot.activeHudPopup === "NOTIFICATIONS"}
    <div
      in:scale={{ duration: 200, start: 0.95 }}
      out:fade={{ duration: 150 }}
      class="absolute right-0 mt-4 w-80 bg-black/95 md:bg-black/80 md:backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] z-50 overflow-hidden"
    >
      <div
        class="p-4 border-b border-white/5 flex items-center justify-between"
      >
        <h3
          class="text-[10px] font-mono text-gray-500 tracking-widest flex items-center gap-2"
        >
          <LucideActivity size={12} class="text-[#00FFFF]" />
          System Notifications
        </h3>
        <span class="text-[9px] font-mono text-[#00FFFF]/40"
          >{nanobot.unreadNotificationsCount} New</span
        >
      </div>

      <div class="max-h-96 overflow-y-auto custom-scrollbar">
        {#each nanobot.notifications as note (note.id)}
          <button
            onclick={() => handleNotificationClick(note)}
            class="w-full text-left p-4 border-b border-white/5 hover:bg-white/[0.02] transition-colors group relative"
          >
            {#if !note.isRead}
              <div
                class="absolute left-1 top-1/2 -translate-y-1/2 w-1 h-8 bg-[#00FFFF] rounded-full shadow-[0_0_8px_#00FFFF]"
              ></div>
            {/if}
            <div class="flex items-start justify-between mb-1">
              <span
                class="text-[9px] font-bold tracking-tighter {note.type ===
                'SECURITY'
                  ? 'text-amber-400'
                  : 'text-[#00FFFF]'}"
              >
                {note.type}
              </span>
              <span class="text-[9px] font-mono text-gray-700"
                >{new Date(note.createdAt || note.created_at || new Date()).toLocaleTimeString()}</span
              >
            </div>
            <p
              class="text-[11px] font-medium {note.isRead
                ? 'text-gray-500'
                : 'text-gray-300'} leading-relaxed group-hover:text-white transition-colors"
            >
              {note.message}
            </p>
          </button>
        {:else}
          <div class="p-8 text-center">
            <p class="text-[10px] font-mono text-gray-600 ">
              No logs detected
            </p>
          </div>
        {/each}
      </div>

      <div class="flex border-t border-white/5">
        <button
          onclick={() => {
            if (nanobot.activityLogs.length > 0) {
              nanobot.showFullLog(
                nanobot.activityLogs[nanobot.activityLogs.length - 1],
              );
            }
            nanobot.toggleHudPopup("NOTIFICATIONS");
          }}
          class="flex-1 py-3 bg-white/5 text-[9px] font-mono text-gray-400 hover:text-white tracking-[widest] hover:bg-white/[0.08] transition-all border-r border-white/5"
        >
          System Audit
        </button>
        <button
          onclick={() => {
            nanobot.openWidget("NOTIFICATION_MANAGEMENT");
            nanobot.toggleHudPopup("NOTIFICATIONS");
          }}
          class="flex-1 py-3 bg-white/5 text-[9px] font-mono text-[#00FFFF] tracking-[widest] hover:bg-[#00FFFF]/10 transition-all"
        >
          Manage Signals
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 255, 0.2);
  }
</style>
