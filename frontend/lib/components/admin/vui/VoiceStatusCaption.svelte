<script lang="ts">
  import { vuiState } from "$lib/vui";
  import { VUI_CONFIG } from "$lib/vui/core/VuiConstants";
  import { scale } from "svelte/transition";
  import { typewriter } from "$lib/actions/typewriter";

  let { phase } = $props();
</script>

<div
  class="relative z-50 mt-12 text-center min-h-[4rem] max-w-2xl px-6 flex flex-col items-center justify-start"
>
  {#if phase === "listening" && vuiState.liveText}
    <p
      class="text-sm bg-black/40 px-6 py-3 rounded-full border border-white/10 text-white/90 font-light italic tracking-wide transition-all duration-500 shadow-[0_0_20px_rgba(255,255,255,0.05)] scale-105"
      style="transform: scale(calc(1 + var(--vol) * 0.2));"
    >
      "{vuiState.liveText}"
    </p>
  {:else if phase === "listening"}
    <p
      class="text-[10px] font-mono text-[#00FFFF]/60 uppercase tracking-[0.4em] animate-pulse"
    >
      {vuiState.hasSpoken
        ? VUI_CONFIG.UX.PHASE_LABELS.listening
        : "Neural Noise Gate Active"}
    </p>
  {:else if phase === "thinking"}
    <div class="flex flex-col items-center gap-2">
      <p
        class="text-[10px] font-mono text-[#9d4edd]/70 uppercase tracking-[0.3em] animate-pulse"
      >
        Neural Processing
      </p>
      {#if vuiState.activeTier}
        <div
          class="flex items-center gap-2 bg-purple-500/10 px-3 py-1 rounded border border-purple-500/20"
          in:scale={{ duration: 400, start: 0.95 }}
        >
          <span class="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping"
          ></span>
          <span
            class="text-[9px] font-mono text-purple-300 tracking-widest uppercase"
          >
            {vuiState.activeTier.replace("_", " ")}
          </span>
        </div>
      {/if}
    </div>
  {:else if phase === "executing"}
    <div class="flex flex-col items-center gap-2">
      <p
        class="text-[10px] font-mono text-pink-400/70 uppercase tracking-[0.3em] animate-pulse"
      >
        {VUI_CONFIG.UX.PHASE_LABELS.executing}
      </p>
      {#if vuiState.liveText}
        <div
          class="flex items-center gap-2 bg-pink-500/10 px-3 py-1 rounded border border-pink-500/20"
          in:scale={{ duration: 400, start: 0.95 }}
        >
          <span class="w-1.5 h-1.5 rounded-full bg-pink-400 animate-pulse"
          ></span>
          <span
            class="text-[9px] font-mono text-pink-300 tracking-widest uppercase"
          >
            {vuiState.liveText}
          </span>
        </div>
      {/if}
    </div>
  {:else if phase === "speaking"}
    <div class="flex flex-col items-center gap-3">
      <p
        class="text-[10px] font-mono text-[#00FFFF]/70 uppercase tracking-[0.3em] animate-pulse"
      >
        {VUI_CONFIG.UX.PHASE_LABELS.speaking}
      </p>
      {#if vuiState.systemMessage}
        <p
          class="text-lg md:text-xl text-white/90 font-medium tracking-wide drop-shadow-md leading-relaxed scifi-text w-full"
          use:typewriter={{
            speed: 0,
            text: vuiState.systemMessage,
            getVolume: () => vuiState.volume,
            isSpeaking: () => phase === "speaking",
          }}
        >
          {vuiState.systemMessage}
        </p>
      {/if}
    </div>
  {:else}
    <p class="text-[10px] font-mono text-white/20 uppercase tracking-[0.3em]">
      {VUI_CONFIG.UX.PHASE_LABELS.idle}
    </p>
  {/if}
  {#if vuiState.errorMsg}
    <p class="text-xs text-red-500 mt-2 font-mono tracking-wide">
      {vuiState.errorMsg}
    </p>
  {/if}
</div>

<style>
  .scifi-text {
    will-change: contents;
    contain: layout style;
    text-shadow: 0 0 6px rgba(128, 210, 255, 0.08);
  }

  :global(.tw-active) {
    color: #e0f4ff;
    text-shadow:
      0 0 12px rgba(128, 232, 255, 0.4),
      0 0 4px rgba(255, 255, 255, 0.15);
  }
</style>
