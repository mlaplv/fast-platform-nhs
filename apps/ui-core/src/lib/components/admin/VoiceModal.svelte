<script lang="ts">
  import { vuiState } from "$lib/vui";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fade } from "svelte/transition";
  import { playSciFiBeep, playSiriDing } from "$lib/utils/sfx";
  import VoiceOrb from "./vui/VoiceOrb.svelte";
  import VoiceStatusCaption from "./vui/VoiceStatusCaption.svelte";

  $effect(() => {
    if (nanobot.isVuiActive) playSciFiBeep();
  });

  let hasDinged = false;
  $effect(() => {
    if (vuiState.phase === "listening" && !hasDinged) {
      playSiriDing();
      hasDinged = true;
    } else if (vuiState.phase !== "listening") {
      hasDinged = false;
    }
  });

  let phase = $derived(vuiState.phase);
</script>

<svelte:window
  onkeydown={(e) => {
    if (e.key === "Escape" && nanobot.isVuiActive) {
      e.preventDefault();
      nanobot.interruptAll();
      nanobot.resetVui();
    }
  }}
/>

{#if nanobot.isVuiActive && !nanobot.isTraining}
  <div
    class="fixed inset-0 z-[1000] overflow-hidden bg-[#020204] md:bg-[#020204]/[0.97] md:backdrop-blur-3xl pointer-events-auto"
    transition:fade={{ duration: 300 }}
  >
    <!-- Close Button -->
    <button
      onclick={() => {
        nanobot.interruptAll();
        nanobot.resetVui();
      }}
      aria-label="Đóng"
      class="absolute top-5 right-5 md:top-7 md:right-7 z-50 w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 group cursor-pointer"
    >
      <span
        class="absolute -inset-3 rounded-full bg-[#80D0FF]/[0.05] blur-2xl group-hover:bg-[#80E8FF]/[0.1] group-hover:scale-[1.3] transition-all duration-700"
      ></span>
      <span
        class="absolute inset-0 rounded-full bg-gradient-to-b from-white/[0.06] via-white/[0.02] to-white/[0.04] border border-white/[0.08] group-hover:border-white/[0.15] backdrop-blur-2xl transition-all duration-300 shadow-[inset_0_1px_2px_rgba(255,255,255,0.06)]"
      ></span>
      <span class="absolute inset-[2px] rounded-full overflow-hidden">
        <span
          class="absolute top-0 left-[18%] right-[18%] h-[42%] rounded-full bg-gradient-to-b from-white/[0.18] via-white/[0.04] to-transparent"
        ></span>
      </span>
      <span
        class="absolute bottom-[2px] left-[22%] right-[22%] h-[22%] rounded-full bg-gradient-to-t from-[#80D0FF]/[0.06] to-transparent blur-[1px]"
      ></span>
      <svg
        class="relative z-10 w-5 h-5 group-hover:scale-110 transition-transform duration-500 drop-shadow-[0_0_4px_rgba(255,255,255,0.25)]"
        viewBox="0 0 24 24"
        fill="none"
      >
        <path
          d="M12 2 L13.5 8.5 L20 10 L13.5 11.5 L12 18 L10.5 11.5 L4 10 L10.5 8.5 Z"
          fill="white"
          fill-opacity="0.75"
        />
        <path
          d="M19 2 L19.8 4.5 L22 5.3 L19.8 6 L19 8.5 L18.2 6 L16 5.3 L18.2 4.5 Z"
          fill="white"
          fill-opacity="0.45"
        />
        <path
          d="M6 16 L6.6 17.8 L8.5 18.4 L6.6 19 L6 21 L5.4 19 L3.5 18.4 L5.4 17.8 Z"
          fill="white"
          fill-opacity="0.35"
        />
      </svg>
    </button>

    <div
      class="relative w-full h-full flex flex-col items-center justify-center"
    >
      <VoiceOrb {phase} />
      <VoiceStatusCaption {phase} />
    </div>
  </div>
{/if}
