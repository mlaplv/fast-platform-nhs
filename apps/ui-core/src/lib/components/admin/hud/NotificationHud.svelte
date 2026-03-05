<script lang="ts">
  import { fade, slide, scale } from "svelte/transition";
  import LucideBell from "lucide-svelte/icons/bell";
  import LucideActivity from "lucide-svelte/icons/activity";
  import { nanobot } from "$lib/state/nanobot.svelte";

  function toggleDropdown() {
    nanobot.toggleHudPopup("NOTIFICATIONS");
    if (nanobot.activeHudPopup === "NOTIFICATIONS") {
      nanobot.fetchNotifications();
    }
  }

  $effect(() => {
    // Polling interval for real-time feel (initial fetch done in nanobot state init)
    const interval = setInterval(() => {
      nanobot.fetchNotifications();
    }, 30000); // Doubled to 30s to reduce backend load
    return () => clearInterval(interval);
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
      class="absolute right-0 mt-4 w-80 bg-black/80 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] z-50 overflow-hidden"
    >
      <div
        class="p-4 border-b border-white/5 flex items-center justify-between"
      >
        <h3
          class="text-[10px] font-mono text-gray-500 uppercase tracking-widest flex items-center gap-2"
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
            onclick={() => nanobot.markNotificationAsRead(note.id)}
            class="w-full text-left p-4 border-b border-white/5 hover:bg-white/[0.02] transition-colors group relative"
          >
            {#if !note.isRead}
              <div
                class="absolute left-1 top-1/2 -translate-y-1/2 w-1 h-8 bg-[#00FFFF] rounded-full shadow-[0_0_8px_#00FFFF]"
              ></div>
            {/if}
            <div class="flex items-start justify-between mb-1">
              <span
                class="text-[9px] font-bold tracking-tighter uppercase {note.type ===
                'SECURITY'
                  ? 'text-amber-400'
                  : 'text-[#00FFFF]'}"
              >
                {note.type}
              </span>
              <span class="text-[9px] font-mono text-gray-700"
                >{new Date(note.createdAt).toLocaleTimeString()}</span
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
            <p class="text-[10px] font-mono text-gray-600 uppercase">
              No logs detected
            </p>
          </div>
        {/each}
      </div>

      <button
        onclick={() => {
          if (nanobot.activityLogs.length > 0) {
            nanobot.showFullLog(
              nanobot.activityLogs[nanobot.activityLogs.length - 1],
            );
          }
          nanobot.toggleHudPopup("NOTIFICATIONS");
        }}
        class="w-full py-3 bg-white/5 text-[9px] font-mono text-[#00FFFF] uppercase tracking-[widest] hover:bg-[#00FFFF]/10 transition-all border-t border-white/5"
      >
        View Full System Audit
      </button>
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
