<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import Users from "lucide-svelte/icons/users";
  import Shield from "lucide-svelte/icons/shield";
  import Paperclip from "lucide-svelte/icons/paperclip";
  import ChevronDown from "lucide-svelte/icons/chevron-down";
  import { fly, fade } from "svelte/transition";
</script>

{#if nanobot.showMobileDrawer}
  <!-- Backdrop -->
  <div
    transition:fade={{ duration: 200 }}
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60]"
    onclick={() => nanobot.toggleMobileDrawer()}
    aria-hidden="true"
  ></div>

  <!-- Bottom Sheet (Apple Glass Style) -->
  <div
    transition:fly={{ y: 400, duration: 600, opacity: 1 }}
    class="fixed bottom-0 left-0 right-0 bg-black/40 backdrop-blur-3xl border-t border-white/10 rounded-t-[40px] z-[70] p-8 pb-12 shadow-[0_-20px_50px_rgba(0,0,0,1)]"
  >
    <!-- Handle -->
    <div class="w-12 h-1.5 bg-white/10 rounded-full mx-auto mb-10"></div>

    <!-- Quick Action Grid -->
    <div class="grid grid-cols-2 gap-6 mb-12">
      <button
        onclick={() => {
          nanobot.processCommand("manage users", "text");
          nanobot.toggleMobileDrawer();
        }}
        class="flex flex-col items-center gap-3 group"
      >
        <div
          class="w-20 h-20 rounded-[28px] bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 group-hover:text-[#00FFFF] group-hover:border-[#00FFFF]/30 group-hover:bg-[#00FFFF]/5 transition-all duration-300"
        >
          <Users size={28} />
        </div>
        <span
          class="text-[10px] font-mono uppercase tracking-widest text-gray-500"
          >Users</span
        >
      </button>

      <button
        onclick={() => {
          nanobot.processCommand("manage permissions", "text");
          nanobot.toggleMobileDrawer();
        }}
        class="flex flex-col items-center gap-3 group"
      >
        <div
          class="w-20 h-20 rounded-[28px] bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 group-hover:text-[#00FFFF] group-hover:border-[#00FFFF]/30 group-hover:bg-[#00FFFF]/5 transition-all duration-300"
        >
          <Shield size={28} />
        </div>
        <span
          class="text-[10px] font-mono uppercase tracking-widest text-gray-500"
          >RBAC</span
        >
      </button>
    </div>

    <div class="h-px bg-white/5 mb-10"></div>

    <!-- Agentic Suggestions List -->
    <div class="space-y-4">
      <h3
        class="text-[9px] font-mono uppercase tracking-[0.3em] text-[#00FFFF]/60 mb-6 px-1"
      >
        Unified Agentic Flows
      </h3>
      {#each nanobot.agenticSuggestions as suggestion}
        <button
          onclick={() => {
            nanobot.processCommand(suggestion.command, "text");
            nanobot.toggleMobileDrawer();
          }}
          class="w-full flex items-center justify-between p-5 bg-white/[0.03] hover:bg-white/[0.08] border border-white/5 rounded-3xl transition-all duration-300 group"
        >
          <span
            class="text-xs font-medium text-gray-300 group-hover:text-white tracking-wide"
            >{suggestion.label}</span
          >
          <div
            class="w-8 h-8 rounded-full border border-white/5 flex items-center justify-center text-gray-500 group-hover:border-[#00FFFF]/50 group-hover:text-[#00FFFF] transition-all"
          >
            <ChevronDown size={14} class="-rotate-90" />
          </div>
        </button>
      {/each}
    </div>
  </div>
{/if}
