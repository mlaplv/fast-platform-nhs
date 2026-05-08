<script lang="ts">
  import { vuiState, vuiController } from "$lib/vui";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { spring } from "svelte/motion";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import Mic from "@lucide/svelte/icons/mic";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Menu from "@lucide/svelte/icons/menu";
  import { playTick } from "$lib/utils/sfx";

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      if (e.isComposing) return;
      e.preventDefault();
      vuiController.execTextCmd(vuiState.cmdBuffer);
      vuiState.cmdBuffer = "";
    }
  }

  let isFocused = $state(false);
  let lastPos = 0;
  let isScrollingUp = $state(false);

  // Spring-based smoothing for the buttery Safari experience
  const scrollSpring = spring(1, {
    stiffness: 0.08,
    damping: 0.75,
  });

  $effect(() => {
    const pos = nanobot.mobileScrollPosition;
    isScrollingUp = pos < lastPos && pos > 10;
    lastPos = pos;

    // Phase 13.3: Hyper-Aggressive multi-stage factor logic (x3 intensity)
    let targetFactor = 1;

    if (isFocused || vuiState.cmdBuffer || isScrollingUp || pos < 20) {
      targetFactor = 1; // Stage 0: Fully expanded
    } else if (pos > 250) {
      targetFactor = 0.1; // Stage 3: Hyper Minimal
    } else if (pos > 120) {
      targetFactor = 0.25; // Stage 2: Ultra Compact
    } else if (pos > 40) {
      targetFactor = 0.5; // Stage 1: Strong Shrink
    }

    scrollSpring.set(targetFactor);
  });
</script>

<div
  class="fixed bottom-0 left-0 right-0 z-[var(--z-admin-mobile-input)] pb-[env(safe-area-inset-bottom)] flex flex-col items-center pointer-events-none transition-opacity duration-300"
  style:transform="translateY({(1 - $scrollSpring) * 35}px)"
  style:opacity={0.4 + $scrollSpring * 0.6}
>
  <!-- Progressive Blur Material -->
  <div
    class="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-black via-black/80 to-transparent pointer-events-none -z-10"
  ></div>

  <div
    class="w-full px-1.5 pb-10 flex items-center justify-center gap-1.5 max-w-lg pointer-events-auto"
  >
    <!-- Menu Button (Left) -->
    <button
      onclick={() => nanobot.toggleMobileDrawer()}
      class="w-11 h-11 shrink-0 rounded-full bg-white/10 backdrop-blur-3xl border border-white/10 flex items-center justify-center text-white active:scale-90 transition-all duration-500 shadow-xl"
      style:transform="scale({0.5 + $scrollSpring * 0.5})"
      style:opacity={0.2 + $scrollSpring * 0.8}
    >
      <Menu size={20} strokeWidth={2.5} />
    </button>

    <!-- The Adaptive Pill (Hyper-Aggressive Expansion - Wide Edition) -->
    <div
      class="flex-1 min-w-0 flex items-center gap-2 bg-black/70 backdrop-blur-[40px] border border-white/20 rounded-full px-4 py-1.5 shadow-[0_12px_48px_rgba(0,0,0,0.6)] transition-all duration-500 {isFocused
        ? 'border-neon-cyan/50 ring-1 ring-neon-cyan/20'
        : ''}"
      style:transform="scale({0.8 + $scrollSpring * 0.2})"
      style:max-width="{(0.4 + $scrollSpring * 0.6) * 100}%"
    >
      <div
        class="flex-1 flex items-center min-w-0"
        style:opacity={$scrollSpring > 0.3 ? 1 : 0}
      >
        <input
          bind:value={vuiState.cmdBuffer}
          onkeydown={handleKeydown}
          onfocus={() => (isFocused = true)}
          onblur={() => (isFocused = false)}
          type="text"
          placeholder="Hỏi XoHi..."
          class="flex-1 bg-transparent text-[15px] font-medium text-white placeholder:text-white/20 focus:outline-none min-w-0"
        />
      </div>

      <button
        onclick={vuiState.cmdBuffer
          ? () => {
              vuiController.execTextCmd(vuiState.cmdBuffer);
              vuiState.cmdBuffer = "";
            }
          : () => {
              if (nanobot.isVuiActive) {
                nanobot.interruptAll();
                nanobot.resetVui();
              } else {
                playTick();
                vuiController.startRecording();
              }
            }}
        class="w-9 h-9 shrink-0 flex items-center justify-center rounded-full transition-all duration-300 active:scale-90 {vuiState.cmdBuffer
          ? 'bg-neon-cyan/20 text-neon-cyan shadow-[0_0_15px_rgba(0,255,255,0.2)]'
          : nanobot.isVuiActive
            ? 'text-red-500 animate-pulse'
            : 'text-white/50'}"
      >
        {#if vuiState.cmdBuffer}
          <ArrowUp size={19} strokeWidth={3} />
        {:else}
          <Mic size={19} strokeWidth={2.5} />
        {/if}
      </button>
    </div>

    <!-- QuickTips Button (Right - Yellow) -->
    <button
      onclick={() => nanobot.toggleQuickTips()}
      class="w-11 h-11 shrink-0 rounded-full bg-white/10 backdrop-blur-3xl border border-white/10 flex items-center justify-center text-yellow-400 active:scale-90 transition-all duration-500 shadow-xl"
      style:transform="scale({0.5 + $scrollSpring * 0.5})"
      style:opacity={0.2 + $scrollSpring * 0.8}
    >
      <Sparkles size={20} strokeWidth={2.5} />
    </button>
  </div>
</div>
