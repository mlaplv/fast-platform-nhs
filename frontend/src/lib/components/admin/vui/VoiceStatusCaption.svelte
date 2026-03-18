<script lang="ts">
  import { vuiState } from "$lib/vui";
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
  import { onMount, tick } from "svelte";

  let { phase } = $props();
  const theme = VUI_CONFIG.UX.THEME;

  // Elite 2026: Command Center Timer
  let timer = $state(0);
  let intervalId: ReturnType<typeof setInterval> | null = null;

  $effect(() => {
    if (phase === "listening") {
      timer = 0;
      if (!intervalId) intervalId = setInterval(() => timer++, 1000);
    } else if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
    return () => { if (intervalId) clearInterval(intervalId); };
  });

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const rs = s % 60;
    return `${m.toString().padStart(2, "0")}:${rs.toString().padStart(2, "0")}`;
  };

  // Elite 2026: Sentinel-Based Intelligent Scrolling
  let scrollContainer = $state<HTMLDivElement>();
  let sentinel = $state<HTMLDivElement>();
  let isAtBottom = $state(true);

  onMount(() => {
    if (!scrollContainer || !sentinel) return;
    
    const observer = new IntersectionObserver(
      ([entry]) => { isAtBottom = entry.isIntersecting; },
      { root: scrollContainer, threshold: 0.1 }
    );
    
    observer.observe(sentinel);
    return () => observer.disconnect();
  });

  const scrollToSentinel = async (force = false) => {
    if (!sentinel) return;
    if (force || isAtBottom) {
      await tick();
      sentinel.scrollIntoView({ behavior: force ? "auto" : "smooth", block: "end" });
    }
  };

  // Reactive Anchor: Elite 2026 Auto-Command
  $effect(() => {
    const _len = vuiState.history.length;
    const _live = vuiState.liveText;
    const _sys = vuiState.systemMessage;
    const _phase = phase; 
    
    // Command: Always stay at bottom during active conversation
    if (_phase !== "idle") {
      requestAnimationFrame(() => scrollToSentinel(true));
    }
  });
</script>

<!-- Elite 2026: Snippet Architecture (Modular & Ultra-Clean) -->
{#snippet ActionIcons({ opacity = theme.ACTION_ICON_OPACITY_HISTORY })}
  <div class="flex items-center gap-5 pt-2 opacity-{opacity} hover:opacity-100 transition-opacity duration-300 pointer-events-auto">
    <button class="hover:text-white transition-colors"><Copy size={16} /></button>
    <button class="hover:text-white transition-colors"><ThumbsUp size={16} /></button>
    <button class="hover:text-white transition-colors"><ThumbsDown size={16} /></button>
    <button class="hover:text-white transition-colors"><Share2 size={16} /></button>
    <button class="hover:text-white transition-colors"><MoreHorizontal size={16} /></button>
  </div>
{/snippet}

{#snippet UserBubble({ text, italic = false })}
  <div class="w-full flex justify-end mb-4">
    <div 
      class="max-w-[70%] px-6 py-3 rounded-[24px] rounded-tr-[4px] shadow-sm border border-white/5" 
      style="background: {theme.USER_BUBBLE_BG}; color: {theme.USER_BUBBLE_TEXT}"
    >
      <p class="text-[15px] font-normal tracking-wide {italic ? 'italic' : ''}">"{text}"</p>
    </div>
  </div>
{/snippet}

{#snippet AiMessage({ text, active = false, animate = true })}
  <div class="w-full space-y-6">
    <p 
      class="text-xl md:text-2xl font-normal tracking-tight leading-relaxed text-start max-w-4xl scifi-text" 
      style="color: {theme.AI_TEXT_COLOR}"
      use:typewriter={{ 
        speed: animate ? 30 : 0, 
        text, 
        getVolume: () => vuiState.volume, 
        isSpeaking: () => active && (phase === "speaking" || phase === "executing") 
      }}
    >
      {text}
    </p>
    {#if !active}
      {@render ActionIcons({ opacity: "30" })}
    {:else}
       <div transition:fade={{ delay: 500 }}>
          {@render ActionIcons({ opacity: theme.ACTION_ICON_OPACITY_ACTIVE })}
       </div>
    {/if}
  </div>
{/snippet}

<div class="relative w-full h-full overflow-hidden pointer-events-none">
  <div
    bind:this={scrollContainer}
    class="relative w-full h-full overflow-y-auto scroll-smooth pointer-events-auto p-8 md:p-12 pb-[45vh] transition-all duration-500 {nanobot.vuiResponse?.data?.campaign_id ? 'opacity-10 blur-md pointer-events-none' : ''}"
    style="--history-spacing: {theme.HISTORY_SPACING}"
  >
    <div class="max-w-5xl mx-auto flex flex-col space-y-[var(--history-spacing)]">
      <!-- Elite 2026: Conversation Metadata -->
      <div class="w-full flex justify-between items-center mb-4 opacity-40 hover:opacity-100 transition-opacity duration-300">
        <div class="text-[11px] font-mono tracking-[0.2em] text-white/50 uppercase">ELITE_CONVO_STREAM_v5.0</div>
        <div class="flex items-center gap-4">
          <button onclick={() => vuiState.newChat()} class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-all text-xs border border-white/10">
            <Plus size={14} /> <span>Elite Reset</span>
          </button>
          <button onclick={() => vuiState.clearHistory()} class="p-2 rounded-full hover:bg-red-500/10 text-white/30 hover:text-red-400 transition-all">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <!-- History Stream -->
      {#each vuiState.history as item (item.id)}
        <div class="w-full flex flex-col space-y-4 pointer-events-auto">
          {@render UserBubble({ text: item.userQuery, italic: true })}
          {#if item.aiResponse}
            {@render AiMessage({ text: item.aiResponse, active: false, animate: false })}
          {/if}
        </div>
      {/each}

      <!-- Current Elite Interaction Zone -->
      {#if phase !== "idle" || vuiState.isWaitingForAction}
        <div class="w-full flex flex-col relative pointer-events-auto">
          <!-- Live User Speech -->
          {#if (phase === "listening" || vuiState.transcript) && vuiState.liveText}
            <div in:fade={{ duration: 200 }}>
              {@render UserBubble({ text: vuiState.liveText })}
            </div>
          {/if}

          <!-- Command Center (Mic/Timer) -->
          <div class="w-full flex justify-end items-center gap-2 mb-6 opacity-80">
            <div class="flex items-center gap-3 px-4 py-2 rounded-full bg-white/5 border border-white/10 font-mono text-[14px] tracking-widest text-white shadow-2xl backdrop-blur-xl">
              <Mic size={16} class={phase === "listening" ? "text-red-500 animate-pulse" : "text-blue-400"} />
              <span class="min-w-[45px]">{formatTime(timer)}</span>
            </div>
          </div>

          <!-- Active AI Output -->
          <div class="w-full flex flex-col items-start gap-8">
            {#if (phase === "speaking" || phase === "executing") && vuiState.systemMessage}
               {@render AiMessage({ text: vuiState.systemMessage, active: true })}
            {/if}

            {#if phase === "thinking"}
              <div class="flex gap-2 items-center mt-2 pl-4">
                <div class="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:-0.3s] shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
                <div class="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.15s] shadow-[0_0_10px_rgba(96,165,250,0.5)]"></div>
                <div class="w-2 h-2 rounded-full bg-blue-300 animate-bounce shadow-[0_0_10px_rgba(147,197,253,0.5)]"></div>
              </div>
            {/if}

            {#if vuiState.errorMsg}
              <div class="text-xs text-red-400 bg-red-400/5 px-4 py-2 rounded-xl border border-red-500/10 mt-6 font-mono tracking-wider animate-pulse">
                CRITICAL_SYSTEM_FAIL: {vuiState.errorMsg}
              </div>
            {/if}
          </div>
        </div>
      {/if}

      <!-- Elite 2026: The Sentinel (Anchor) -->
      <div bind:this={sentinel} class="h-1 w-full pointer-events-none opacity-0"></div>
    </div>

    <!-- Empty State Hero -->
    {#if phase === "listening" && !vuiState.liveText && !vuiState.history.length}
      <div class="absolute bottom-[50px] left-0 right-0 flex justify-center pointer-events-none z-[1200]" transition:fade={{ duration: 300 }}>
         <div class="w-full max-w-4xl px-4 sm:px-6 flex justify-center">
            <h2 class="text-[28px] md:text-[34px] font-medium text-white tracking-tight text-center glass-text">
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
  .glass-text {
    text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
  }
  :global(.tw-active) {
    color: #ffffff;
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.4);
  }
  div::-webkit-scrollbar { width: 5px; }
  div::-webkit-scrollbar-track { background: transparent; }
  div::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.08); border-radius: 10px; }
  div::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.15); }
</style>
