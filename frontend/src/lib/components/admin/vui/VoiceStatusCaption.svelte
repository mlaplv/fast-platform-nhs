<script lang="ts">
  import { vuiState, type VuiInteraction } from "$lib/vui";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { VUI_CONFIG } from "$lib/vui/core/VuiConstants";
  import { fade, scale } from "svelte/transition";
  import { typewriter } from "$lib/actions/typewriter";
  import Copy from "lucide-svelte/icons/copy";
  import ThumbsUp from "lucide-svelte/icons/thumbs-up";
  import ThumbsDown from "lucide-svelte/icons/thumbs-down";
  import Share2 from "lucide-svelte/icons/share-2";
  import MoreHorizontal from "lucide-svelte/icons/more-horizontal";
  import Mic from "lucide-svelte/icons/mic";
  import Plus from "lucide-svelte/icons/plus";
  import Trash2 from "lucide-svelte/icons/trash-2";
  let { phase } = $props();
  const theme = VUI_CONFIG.UX.THEME;

  // GPT Style Timer Simulation
  let timer = $state(0);
  let intervalId: ReturnType<typeof setInterval> | null = null;

  $effect(() => {
    if (phase === "listening") {
      timer = 0;
      if (!intervalId) {
        intervalId = setInterval(() => timer++, 1000);
      }
    } else {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };
  });

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const rs = s % 60;
    return `${m.toString().padStart(2, "0")}:${rs.toString().padStart(2, "0")}`;
  };

  // Auto-scroll logic: Ultra-Smooth & Resilient (Phase 76.3 Optimization)
  let scrollContainer = $state<HTMLDivElement>();
  let lastScrollHeight = 0;

  const scrollToBottom = (force = false) => {
    if (!scrollContainer) return;
    const { scrollHeight, clientHeight, scrollTop } = scrollContainer;
    const isNearBottom = scrollHeight - clientHeight - scrollTop < 150;

    if (force || isNearBottom) {
      scrollContainer.scrollTo({
        top: scrollHeight,
        behavior: force ? "auto" : "smooth",
      });
    }
  };

  $effect(() => {
    const _len = vuiState.history.length;
    requestAnimationFrame(() => scrollToBottom(_len > 0 && phase === "idle"));
  });

  $effect(() => {
    if (!scrollContainer) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const height = entry.target.scrollHeight;
        if (height !== lastScrollHeight) {
          lastScrollHeight = height;
          scrollToBottom();
        }
      }
    });

    const content = scrollContainer.firstElementChild;
    if (content) observer.observe(content);

    return () => observer.disconnect();
  });
</script>

{#snippet ActionIcons({ opacity = theme.ACTION_ICON_OPACITY_HISTORY })}
  <div
    class="flex items-center gap-5 pt-2 opacity-{opacity} hover:opacity-100 transition-opacity duration-300 pointer-events-auto"
  >
    <button class="hover:text-white transition-colors"><Copy size={16} /></button>
    <button class="hover:text-white transition-colors"><ThumbsUp size={16} /></button>
    <button class="hover:text-white transition-colors"><ThumbsDown size={16} /></button>
    <button class="hover:text-white transition-colors"><Share2 size={16} /></button>
    <button class="hover:text-white transition-colors"><MoreHorizontal size={16} /></button>
  </div>
{/snippet}

<div class="relative w-full h-full overflow-hidden pointer-events-none">
  <!-- Main Content Layer (Scrollable) -->  <div
    bind:this={scrollContainer}
    class="relative w-full h-full overflow-y-auto scroll-smooth pointer-events-auto p-8 md:p-12 mb-20 transition-all duration-500 {nanobot.vuiResponse?.data?.campaign_id ? 'opacity-10 blur-md pointer-events-none' : ''}"
    style="--history-spacing: {theme.HISTORY_SPACING}"
  >
    <div class="max-w-5xl mx-auto flex flex-col space-y-[var(--history-spacing)]">
      <!-- Chat Management Toolbar -->
      <div class="w-full flex justify-between items-center mb-4 opacity-40 hover:opacity-100 transition-opacity duration-300">
        <div class="text-[11px] font-mono tracking-[0.2em] text-white/50 uppercase">CONVERSATION_LOG_v4.5</div>
        <div class="flex items-center gap-4">
          <button onclick={() => vuiState.newChat()} class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-all text-xs border border-white/10">
            <Plus size={14} /> <span>New Chat</span>
          </button>
          <button onclick={() => vuiState.clearHistory()} class="p-2 rounded-full hover:bg-red-500/10 text-white/30 hover:text-red-400 transition-all">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <!-- History Interactions -->
      {#each vuiState.history as item (item.id)}
        <div class="w-full flex flex-col space-y-4 pointer-events-auto" transition:fade>
          <div class="w-full flex justify-end">
            <div class="max-w-[70%] px-6 py-3 rounded-[24px] rounded-tr-[4px] shadow-sm border border-white/5" style="background: {theme.USER_BUBBLE_BG}; color: {theme.USER_BUBBLE_TEXT}">
              <p class="text-[15px] font-normal tracking-wide italic">"{item.userQuery}"</p>
            </div>
          </div>
          {#if item.aiResponse}
            <div class="w-full space-y-4">
              <p class="text-xl md:text-2xl font-normal tracking-tight leading-relaxed text-start max-w-4xl scifi-text" style="color: {theme.AI_TEXT_COLOR}">{item.aiResponse}</p>
              {@render ActionIcons({ opacity: "30" })}
            </div>
          {/if}
        </div>
      {/each}

      <!-- CURRENT Active Interaction -->
      {#if phase !== "idle"}
        <div class="w-full flex flex-col relative pointer-events-auto">
          <!-- User Query -->
          <div class="w-full flex justify-end mb-4">
            {#if (phase === "listening" || vuiState.transcript) && vuiState.liveText}
              <div class="max-w-[70%] px-6 py-3 rounded-[24px] rounded-tr-[4px] shadow-xl border border-white/5 transition-all duration-300 {vuiState.isLiveTextStable ? 'opacity-100 scale-100' : 'opacity-70 scale-[0.98] italic'}" style="background: {theme.USER_BUBBLE_BG}; color: {theme.USER_BUBBLE_TEXT}" in:scale={{ duration: 400, start: 0.95, opacity: 0 }}>
                <p class="text-[15px] font-normal tracking-wide">
                  "{vuiState.liveText}"
                  {#if !vuiState.isLiveTextStable && phase === 'listening'}
                    <span class="inline-block w-1 h-4 ml-1 bg-white/30 animate-pulse align-middle"></span>
                  {/if}
                </p>
              </div>
            {/if}
          </div>

          <!-- Timer -->
          <div class="w-full flex justify-end items-center gap-2 mb-4 opacity-60">
            <div class="flex items-center gap-2 text-white/80 font-mono text-[13px] tracking-widest">
              <Mic size={14} class={phase === "listening" ? "text-red-500 animate-pulse" : ""} />
              <span>{formatTime(timer)}</span>
            </div>
          </div>

          <!-- AI Response -->
          <div class="w-full flex flex-col items-start gap-8">
            {#if (phase === "speaking" || phase === "executing") && vuiState.systemMessage}
              <div class="w-full space-y-6">
                <p class="text-xl md:text-2xl font-normal tracking-tight leading-relaxed text-start max-w-4xl scifi-text" style="color: {theme.AI_TEXT_COLOR}" use:typewriter={{ speed: 0, text: vuiState.systemMessage, getVolume: () => vuiState.volume, isSpeaking: () => phase === "speaking" || phase === "executing" }}>
                  {vuiState.systemMessage}
                </p>
                <div transition:fade={{ delay: 500 }}>
                  {@render ActionIcons({ opacity: theme.ACTION_ICON_OPACITY_ACTIVE })}
                </div>
              </div>
            {/if}

            {#if phase === "thinking"}
              <div class="flex gap-1.5 items-center mt-2 pl-2">
                <div class="w-1.5 h-1.5 rounded-full bg-white/30 animate-bounce [animation-delay:-0.3s]"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-white/30 animate-bounce [animation-delay:-0.15s]"></div>
                <div class="w-1.5 h-1.5 rounded-full bg-white/30 animate-bounce"></div>
              </div>
            {/if}

            {#if vuiState.errorMsg}
              <p class="text-xs text-red-400 bg-red-400/5 px-4 py-2 rounded-xl border border-red-500/10 mt-6 font-mono tracking-wider">SYSTEM_ERR: {vuiState.errorMsg}</p>
            {/if}
          </div>
        </div>
      {/if}
    </div>

    <!-- Start Talking Hero Overlay -->
    {#if phase === "listening" && !vuiState.liveText && !vuiState.history.length}
      <div class="absolute bottom-[50px] left-0 right-0 flex justify-center pointer-events-none z-[1200]" transition:fade={{ duration: 300 }}>
         <div class="w-full max-w-4xl px-4 sm:px-6 flex justify-center">
            <h2 class="text-[28px] md:text-[34px] font-medium text-white tracking-tight text-center">
               {VUI_CONFIG.UX.PHASE_LABELS.listening}
            </h2>
         </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .scifi-text {
    font-family: "Inter", -apple-system, sans-serif;
    word-break: break-word;
  }
  :global(.tw-active) {
    color: #ffffff;
    text-shadow: 0 0 1px rgba(255, 255, 255, 0.2);
  }
  div::-webkit-scrollbar { width: 6px; }
  div::-webkit-scrollbar-track { background: transparent; }
  div::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
  div::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.1); }
</style>
