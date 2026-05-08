<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { fade, slide } from "svelte/transition";
  import LucideBell from "@lucide/svelte/icons/bell";
  import LucideActivity from "@lucide/svelte/icons/activity";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Info from "@lucide/svelte/icons/info";
  import type { BaseWidgetProps } from "$lib/types";

  let { data = {} } = $props<BaseWidgetProps>();

  function getIcon(type: string) {
    switch (type) {
      case "SECURITY":
        return ShieldCheck;
      case "INFO":
        return Info;
      default:
        return LucideBell;
    }
  }

  function getColor(type: string) {
    switch (type) {
      case "SECURITY":
        return "text-amber-400";
      case "INFO":
        return "text-neon-cyan";
      default:
        return "text-[#39FF14]";
    }
  }
</script>

<div class="h-full flex flex-col">
  <div class="flex-1 space-y-3 pr-2 scrollbar-mission overflow-y-auto">
    {#each nanobot.notifications as note (note.id)}
      {@const Icon = getIcon(note.type)}
      <div
        class="relative p-5 bg-white/[0.02] border border-white/5 group hover:border-white/10 hover:bg-white/[0.04] transition-all cursor-pointer"
        onclick={() => nanobot.markNotificationAsRead(note.id)}
        onkeydown={(e) =>
          e.key === "Enter" && nanobot.markNotificationAsRead(note.id)}
        role="button"
        tabindex="0"
      >
        {#if !note.isRead}
          <div
            class="absolute left-0 top-0 bottom-0 w-1 bg-neon-cyan shadow-[0_0_10px_#00FFFF]"
          ></div>
        {/if}

        <div class="flex items-start justify-between">
          <div class="flex items-start gap-4">
            <div
              class="mt-1 {getColor(
                note.type,
              )} opacity-60 group-hover:opacity-100 transition-opacity"
            >
              <Icon size={16} />
            </div>
            <div>
              <p
                class="text-[13px] {note.isRead
                  ? 'text-gray-500'
                  : 'text-gray-300'} leading-relaxed max-w-2xl"
              >
                {note.message}
              </p>
            </div>
          </div>
          <div class="text-right">
            <span
              class="text-[10px] font-mono text-white/20 uppercase tracking-widest block"
              >{new Date(note.createdAt).toLocaleDateString()}</span
            >
            <span class="text-[10px] font-mono text-white/40 tabular-nums"
              >{new Date(note.createdAt).toLocaleTimeString()}</span
            >
          </div>
        </div>
      </div>
    {:else}
      <div
        class="h-64 flex flex-col items-center justify-center border border-dashed border-white/5"
      >
        <div class="w-12 h-1 bg-white/5 animate-pulse mb-4"></div>
        <p
          class="text-[11px] font-mono text-gray-700 uppercase tracking-widest"
        >
          No spectral traces detected in the audit stream
        </p>
      </div>
    {/each}
  </div>
</div>
