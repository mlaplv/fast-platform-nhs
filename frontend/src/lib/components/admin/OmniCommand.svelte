<script lang="ts">
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { vuiState } from "$lib/vui";
  import Plus from "@lucide/svelte/icons/plus";
  import ArrowUp from "@lucide/svelte/icons/arrow-up";
  import Mic from "@lucide/svelte/icons/mic";
  import CategoryMenu from "./CategoryMenu.svelte";
  import { playTick } from "$lib/utils/sfx";

  let menuOpen = $state(false);

  $effect(() => {
    if (nanobot.isProcessingSpeech && vuiState.phase === "listening") {
      nanobot.stopRecording();
    }
  });

  function executeCommand() {
    if (!vuiState.cmdBuffer.trim()) return;
    // Note: execTextCmd is not yet proxied, adding it to logic below or proxying it
    nanobot.processCommand(vuiState.cmdBuffer);
    vuiState.cmdBuffer = "";
  }
</script>

<div
  class="w-full max-w-4xl mx-auto z-[var(--z-admin-hud)] px-4 sm:px-6 relative transition-all duration-700 opacity-100 translate-y-0"
>
  <!-- Command Input Bar (SILENCE / CHAT FLOW) -->
  <div class="flex items-center gap-2 md:gap-3">
    <div class="relative">
      <button
        onclick={(e) => {
          e.stopPropagation();
          menuOpen = !menuOpen;
        }}
        class="w-11 h-11 md:w-12 md:h-12 shrink-0 md:backdrop-blur-md rounded-full flex items-center justify-center transition-all duration-500 shadow-2xl {menuOpen
          ? 'bg-[#1a1a1a]/80 text-[#00FFFF] border border-[#00FFFF]/30 shadow-[0_0_20px_rgba(0,255,255,0.15)]'
          : 'bg-[#1a1a1a]/80 text-gray-400 border border-white/5 hover:text-[#00FFFF]'}"
      >
        <div
          class="transition-transform duration-500"
          class:rotate-[135deg]={menuOpen}
        >
          <Plus size={22} />
        </div>
      </button>
      <CategoryMenu bind:open={menuOpen} />
    </div>

    <div
      class="flex-1 bg-[#1a1a1a]/80 md:backdrop-blur-2xl border border-white/5 rounded-full flex items-center p-1 shadow-2xl focus-within:border-[#00FFFF]/30"
    >
      <input
        id="cmd-input"
        bind:value={vuiState.cmdBuffer}
        type="text"
        placeholder="Hỏi bất kỳ điều gì..."
        autocomplete="off"
        spellcheck="false"
        onkeydown={(e) => {
          if (e.key === "Enter") {
            if (e.isComposing) return;
            e.preventDefault();
            executeCommand();
          }
        }}
        class="flex-1 bg-transparent text-gray-100 placeholder:text-gray-600 focus:outline-none py-2 px-5 text-[15px] min-w-0"
      />
      <button
        onclick={vuiState.cmdBuffer
          ? () => executeCommand()
          : () => {
              if (vuiState.phase === 'listening') {
                // Clicking while listening means "Stop and process"
                nanobot.stopRecording();
              } else if (nanobot.isVuiActive) {
                // If it's active but stuck (thinking/error/speaking), click means "Retry/New Query"
                playTick();
                nanobot.startRecording();
              } else {
                // Just starting
                playTick();
                nanobot.startRecording();
              }
            }}
        class="p-2 mr-1 flex items-center justify-center transition-all {vuiState.cmdBuffer
          ? 'text-black bg-white rounded-full'
          : vuiState.phase === 'listening'
            ? 'text-red-500 animate-pulse'
            : nanobot.isVuiActive
              ? 'text-white/80'
              : 'text-gray-500 hover:text-white'}"
      >
        {#if vuiState.cmdBuffer}
          <ArrowUp size={18} strokeWidth={2.5} />
        {:else}
          <Mic size={20} />
        {/if}
      </button>
    </div>
  </div>
</div>

<style>
  /* Prevent browser autofill from turning background white, especially when password fields appear elsewhere */
  input:-webkit-autofill,
  input:-webkit-autofill:hover, 
  input:-webkit-autofill:focus, 
  input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 30px #1a1a1a inset !important;
    -webkit-text-fill-color: #f3f4f6 !important;
    transition: background-color 5000s ease-in-out 0s;
  }
</style>
