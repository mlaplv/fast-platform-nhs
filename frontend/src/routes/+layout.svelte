<script lang="ts">
  import "./layout.css";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiState, vuiController } from "$lib/vui";
  import { Z_INDEX } from "$lib/core/constants/zIndex";
  import XohiLogo from "$lib/components/admin/XohiLogo.svelte";
  import { fade, scale, slide } from "svelte/transition";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import X from "lucide-svelte/icons/x";
  import VolumeX from "lucide-svelte/icons/volume-x";
  import Volume2 from "lucide-svelte/icons/volume-2";

  let { children } = $props();

  async function unlockAudio() {
    await vuiController.unlockAudio();
  }

  // God Mode: Bulletproof derive for hydration safety
  let capturedText = $derived(
    nanobot?.voice?.vuiUserQuery || vuiState?.liveText || "",
  );

  // Split captured text into individual phrases (2-3 word chunks)
  let capturedPhrases = $derived.by(() => {
    if (!capturedText) return [];
    const words = capturedText.trim().split(/\s+/);
    if (words.length <= 3) return [capturedText.trim()];

    // Smart split: group into 2-word chunks, detect repeated words
    const phrases: string[] = [];
    let i = 0;
    while (i < words.length) {
      // Try 2-word phrase first, then 3-word
      if (i + 2 <= words.length) {
        const twoWord = words.slice(i, i + 2).join(" ");
        // Check if next words start a clearly separate phrase
        if (i + 3 <= words.length && words[i + 2] !== words[i]) {
          const threeWord = words.slice(i, i + 3).join(" ");
          // If 3rd word seems part of this phrase (e.g. "hey so hi")
          if (i + 3 < words.length || words.length - i === 3) {
            phrases.push(threeWord);
            i += 3;
            continue;
          }
        }
        phrases.push(twoWord);
        i += 2;
      } else {
        phrases.push(words.slice(i).join(" "));
        i = words.length;
      }
    }
    // Deduplicate while preserving order
    return [...new Set(phrases)];
  });

  // Removed phrases (user clicked ×)
  let removedIndices = $state<Set<number>>(new Set());

  // Active phrases after user removes some
  let activePhrases = $derived(
    capturedPhrases.filter((_, i) => !removedIndices.has(i)),
  );

  function removePhrase(index: number) {
    removedIndices = new Set([...removedIndices, index]);
  }

  function confirmTraining() {
    if (activePhrases.length === 0) return;
    // Register ALL active phrases as individual wake/sleep words in one batch
    nanobot.completeTraining(activePhrases);
    removedIndices = new Set();
  }

  function cancelTraining() {
    removedIndices = new Set();
    nanobot.cancelTraining();
  }

  // Inject Z_INDEX as CSS variables for global CSS use (V66.8 Elite)
  const zIndexStyle = Object.entries(Z_INDEX)
    .map(([key, value]) => `--z-${key.toLowerCase()}: ${value};`)
    .join(" ");
</script>

<svelte:head>
  <link rel="icon" href="/favicon.svg" />
  <style>
    :root {
      {zIndexStyle}
    }
  </style>
</svelte:head>
{@render children()}

<!-- VUI Audio Unlock Overlay (Browser Compliance V66.5) -->
{#if vuiState.isAudioBlocked}
  <div 
    class="fixed bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-4"
    style="z-index: {Z_INDEX.SYSTEM};"
    transition:slide
  >
    <button
      onclick={unlockAudio}
      class="group relative flex items-center gap-3 px-6 py-3 bg-black/80 border border-cyan-500/50 rounded-full shadow-[0_0_30px_rgba(34,211,238,0.2)] hover:border-cyan-400 hover:shadow-[0_0_40px_rgba(34,211,238,0.4)] transition-all active:scale-95"
    >
      <div class="absolute inset-0 bg-cyan-500/10 blur-xl rounded-full group-hover:bg-cyan-500/20 transition-all"></div>
      
      <div class="relative flex items-center justify-center w-8 h-8 bg-cyan-500/10 rounded-full text-cyan-400 group-hover:scale-110 transition-transform">
        <Volume2 size={18} class="hidden group-hover:block" />
        <VolumeX size={18} class="group-hover:hidden" />
      </div>
      
      <span class="relative text-sm font-bold text-white uppercase tracking-[0.2em] drop-shadow-sm">
        Bật âm thanh XoHi
      </span>
      
      <div class="relative w-2 h-2 bg-red-500 rounded-full animate-pulse group-hover:bg-cyan-500"></div>
    </button>
    
    <p class="text-[10px] font-mono text-white/40 uppercase tracking-widest bg-black/20 px-3 py-1 rounded-md backdrop-blur-sm">
      Trình duyệt đang chặn âm thanh tự động
    </p>
  </div>
{/if}

<!-- V44.2 Absolute Surface: Neural Capture (Root Level to prevent clipping) -->
{#if nanobot.isTraining}
  <div
    class="fixed inset-0 flex items-center justify-center bg-black/5 backdrop-blur-sm pointer-events-none"
    style="z-index: {Z_INDEX.SYSTEM - 1};"
    transition:fade
  >
    <div
      class="w-[420px] p-12 bg-black/60 border border-cyan-500/20 rounded-[50px] shadow-[0_0_150px_rgba(34,211,238,0.15)] flex flex-col items-center text-center space-y-10 relative overflow-hidden pointer-events-auto"
      transition:scale={{ start: 0.9, duration: 400 }}
    >
      <!-- Sci-fi background scanline -->
      <div
        class="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.1)_50%)] z-0 pointer-events-none bg-[length:100%_4px]"
      ></div>

      <div class="relative z-10">
        <div
          class="absolute inset-0 bg-cyan-400/30 blur-3xl animate-pulse rounded-full"
        ></div>
        <div
          class="relative w-28 h-28 bg-black border-2 border-cyan-500/40 rounded-full flex items-center justify-center overflow-hidden"
        >
          <div class="absolute inset-0 w-20 h-20 bg-cyan-500/10 rounded-full animate-ping m-auto"></div>
          <XohiLogo variant="simple" size={80} />
        </div>
      </div>

      <div class="relative z-10">
        <h3 class="text-xl font-black text-white uppercase tracking-[0.3em]">
          Neural Capture
        </h3>
        <p
          class="text-[11px] font-mono text-cyan-500/80 uppercase tracking-[0.2em] mt-3"
        >
          {nanobot.trainingType === "wake"
            ? "Đang ghi nhận Wake Word"
            : "Đang ghi nhận Protocol Off"}...
        </p>
      </div>

      <!-- Phrase Chips Display -->
      <div
        class="w-full bg-white/5 border border-white/5 rounded-3xl p-6 min-h-[120px] flex flex-wrap gap-2 items-start justify-center relative z-10"
      >
        {#if capturedPhrases.length > 0}
          {#each capturedPhrases as phrase, i}
            {#if !removedIndices.has(i)}
              <div
                class="inline-flex items-center gap-2 bg-cyan-500/10 border border-cyan-500/30 rounded-xl px-4 py-2.5 group"
                transition:scale={{ start: 0.8, duration: 200 }}
              >
                <span class="text-sm font-mono text-white font-semibold"
                  >{phrase}</span
                >
                <button
                  onclick={() => removePhrase(i)}
                  class="w-5 h-5 flex items-center justify-center rounded-full bg-white/5 text-white/30 hover:bg-red-500/30 hover:text-red-400 transition-all"
                >
                  <X size={12} />
                </button>
              </div>
            {/if}
          {/each}
        {:else}
          <div
            class="flex flex-col items-center gap-3 w-full justify-center h-full"
          >
            <div class="flex gap-1">
              {#each Array(3) as _, i}
                <div
                  class="w-1.5 h-1.5 bg-cyan-500/40 rounded-full animate-bounce"
                  style="animation-delay: {i * 0.1}s"
                ></div>
              {/each}
            </div>
            <p
              class="text-[10px] font-mono text-white/20 uppercase tracking-[0.4em]"
            >
              Lắng nghe dữ liệu...
            </p>
          </div>
        {/if}
      </div>

      {#if activePhrases.length > 0}
        <p
          class="text-[9px] font-mono text-cyan-500/40 uppercase tracking-widest relative z-10"
        >
          {activePhrases.length} phrase{activePhrases.length > 1 ? "s" : ""} detected
          · Click × to remove
        </p>
      {/if}

      <div class="flex gap-5 w-full relative z-10">
        <button
          onclick={cancelTraining}
          class="flex-1 py-5 bg-white/[0.03] border border-white/10 rounded-2xl text-[10px] font-mono font-bold text-white/40 uppercase tracking-[0.3em] hover:bg-white/[0.08] hover:text-white transition-all"
        >
          Abort
        </button>
        <button
          onclick={confirmTraining}
          disabled={activePhrases.length === 0}
          class="flex-1 py-5 bg-cyan-500/10 border border-cyan-500/30 rounded-2xl text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-[0.3em] hover:bg-cyan-500/20 transition-all disabled:opacity-20 disabled:grayscale"
        >
          Register ({activePhrases.length})
        </button>
      </div>

      <div class="pt-4 opacity-20 relative z-10">
        <!-- Neural Sync Text Removed -->
      </div>
    </div>
  </div>
{/if}
