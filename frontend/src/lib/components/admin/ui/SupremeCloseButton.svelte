<script lang="ts">
  import { X, Zap } from "lucide-svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { Z_INDEX } from "$lib/core/constants/zIndex";
  import { playTacticalPurge } from "$lib/utils/sfx";

  interface Props {
    campaign_id?: string;
    onClose?: () => void;
    class?: string;
    showIcon?: boolean;
    label?: string;
  }

  let { 
    campaign_id, 
    onClose = () => nanobot.closeUniversalModal(), 
    class: className = "",
    showIcon = true,
    label = ""
  }: Props = $props();

  let holdProgress = $state(0);
  let isHardKillReady = $state(false);

  function startHold(e: MouseEvent | TouchEvent) {
    if (e instanceof MouseEvent && e.button !== 0) return;
    
    const start = Date.now();
    const KILL_THRESHOLD = 6000; // 6 seconds - Ông Chủ Level
    
    const timer = setInterval(() => {
      const elapsed = Date.now() - start;
      holdProgress = Math.min(elapsed / KILL_THRESHOLD, 1);
      if (holdProgress >= 1) {
        isHardKillReady = true;
        clearInterval(timer);
      }
    }, 16);

    const endHold = () => {
      clearInterval(timer);
      const duration = Date.now() - start;
      
      if (duration >= KILL_THRESHOLD) {
        // SUPREME POWER: Kill everything
        nanobot.hardKill(campaign_id);
      } else {
        // Standard Close
        onClose();
      }
      
      holdProgress = 0;
      isHardKillReady = false;
      window.removeEventListener('mouseup', endHold);
      window.removeEventListener('touchend', endHold);
    };

    window.addEventListener('mouseup', endHold);
    window.addEventListener('touchend', endHold);
  }
</script>

<div class="relative pointer-events-auto {className}" style="z-index: {Z_INDEX.SUPREME_POWER};">
  <button
    oncontextmenu={(e) => e.preventDefault()}
    onmousedown={startHold}
    ontouchstart={startHold}
    class="relative min-w-[36px] h-9 px-2 rounded-lg border {isHardKillReady ? 'border-red-500 bg-red-500/40' : 'border-red-500/30 bg-red-500/10'} flex items-center justify-center hover:bg-red-500/30 transition-all group overflow-hidden active:scale-95 cursor-pointer isolate"
    title="Nhấn: Đóng | Giữ 6s: SUPREME KILL (Ngắt tất cả)"
  >
    <!-- Progress Ring for Hard Kill -->
    <svg class="absolute inset-0 w-full h-full -rotate-90 pointer-events-none scale-110">
      <circle 
        cx="18" cy="18" r="15" 
        fill="none" 
        stroke="currentColor" 
        stroke-width="2.5" 
        stroke-dasharray="94.25"
        stroke-dashoffset={94.25 * (1 - holdProgress)}
        style="transition: stroke-dashoffset 0.1s linear"
        class={isHardKillReady ? "text-red-400" : "text-white/20"}
      />
    </svg>

    <div class="flex items-center gap-1.5 z-10">
      {#if showIcon}
        {#if isHardKillReady}
          <Zap size={14} class="text-white animate-pulse" />
        {:else}
          <X size={14} class="text-red-400 group-hover:text-red-300 transition-colors" />
        {/if}
      {/if}
      {#if label}
        <span class="text-[10px] font-black uppercase tracking-widest {isHardKillReady ? 'text-white' : 'text-red-400/80 group-hover:text-red-300'}">{label}</span>
      {/if}
    </div>

    <!-- Pulsing Background when charging -->
    {#if holdProgress > 0}
      <div 
        class="absolute inset-0 bg-red-600/20 pointer-events-none"
        style="opacity: {holdProgress}"
      ></div>
    {/if}
  </button>
</div>

<style>
  @keyframes pulse {
    0%, 100% { opacity: 0.6; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.05); }
  }
</style>
