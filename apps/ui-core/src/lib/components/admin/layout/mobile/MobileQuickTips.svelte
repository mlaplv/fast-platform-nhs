<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { omni } from "$lib/state/omni.svelte";
  import { fade, fly } from "svelte/transition";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import X from "lucide-svelte/icons/x";
  import { playTick } from "$lib/utils/sfx";

  function selectTip(command: string) {
    playTick();
    omni.cmd = command;
    nanobot.toggleQuickTips();
    // Auto-execute the command
    omni.wasVoice = false;
    omni.execCmd();
  }
</script>

{#if nanobot.showQuickTips}
  <!-- Backdrop -->
  <div
    role="presentation"
    onclick={() => nanobot.toggleQuickTips()}
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
    transition:fade={{ duration: 200 }}
  ></div>

  <!-- Quick Tips Menu (Slide up from bottom-right area) -->
  <div
    class="fixed bottom-28 right-5 w-[260px] bg-black/80 backdrop-blur-3xl border border-white/10 rounded-3xl z-[110] shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex flex-col overflow-hidden"
    transition:fly={{ y: 20, duration: 300, opacity: 0 }}
  >
    <div class="px-5 py-4 border-b border-white/5 flex items-center justify-between bg-white/5">
      <div class="flex items-center gap-2">
        <Sparkles size={14} class="text-neon-cyan" />
        <span class="text-[11px] font-bold uppercase tracking-widest text-white/70">Gợi ý nhanh</span>
      </div>
      <button 
        onclick={() => nanobot.toggleQuickTips()}
        class="text-white/30 hover:text-white transition-colors"
      >
        <X size={16} />
      </button>
    </div>

    <div class="p-2 max-h-[350px] overflow-y-auto custom-scrollbar">
      {#each nanobot.agenticSuggestions as suggestion}
        <button
          onclick={() => selectTip(suggestion.command)}
          class="w-full text-left p-3.5 rounded-2xl hover:bg-white/10 active:scale-[0.98] transition-all border border-transparent hover:border-white/5 group"
        >
          <div class="text-[14px] font-medium text-white/90 group-hover:text-neon-cyan transition-colors">
            {suggestion.label}
          </div>
          <div class="text-[10px] font-mono text-white/20 mt-1 uppercase tracking-tighter">
            {suggestion.command}
          </div>
        </button>
      {/each}
    </div>

    <div class="px-5 py-3 bg-neon-cyan/5 border-t border-neon-cyan/10">
      <div class="text-[9px] font-mono text-neon-cyan/40 text-center uppercase tracking-widest leading-relaxed">
        Hệ thống hỗ trợ sếp tối đa<br/>Trí tuệ XoHi Core
      </div>
    </div>
  </div>
{/if}

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 0px;
  }
</style>
