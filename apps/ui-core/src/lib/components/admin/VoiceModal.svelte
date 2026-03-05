<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { omni } from "$lib/state/omni.svelte";
  import { fade, scale } from "svelte/transition";
  import Mic from "lucide-svelte/icons/mic";
  import { playSciFiBeep, playSiriDing } from "$lib/utils/sfx";
  import { typewriter } from "$lib/actions/typewriter";

  $effect(() => {
    if (nanobot.isVuiActive) playSciFiBeep();
  });

  // Siri ding when mic activates
  $effect(() => {
    if (omni.rec) playSiriDing();
  });

  let phase = $derived(
    omni.isGhostSpeaking
      ? "speaking"
      : omni.rec
        ? "listening"
        : nanobot.nanoBotStatus === "THINKING"
          ? "thinking"
          : "idle",
  );

  let hasContent = $derived(!!omni.dText || !!nanobot.voice.vuiUserQuery);
</script>

<svelte:window
  onkeydown={(e) => {
    if (e.key === "Escape" && nanobot.isVuiActive) {
      e.preventDefault();
      omni.stopRec();
      omni.stopAudio();
      nanobot.resetVui();
    }
  }}
/>

{#if nanobot.isVuiActive && !nanobot.isTraining}
  <div
    class="fixed inset-0 z-[1000] overflow-hidden bg-[#020204] md:bg-[#020204]/[0.97] md:backdrop-blur-3xl pointer-events-auto"
    transition:fade={{ duration: 300 }}
  >
    <!-- Close — Glass Orb + Sparkle Stars ✦ -->
    <button
      onclick={() => {
        omni.stopRec();
        omni.stopAudio();
        nanobot.resetVui();
      }}
      aria-label="Đóng"
      class="absolute top-5 right-5 md:top-7 md:right-7 z-50 w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 group cursor-pointer"
    >
      <!-- Ambient aura -->
      <span
        class="absolute -inset-3 rounded-full bg-[#80D0FF]/[0.05] blur-2xl group-hover:bg-[#80E8FF]/[0.1] group-hover:scale-[1.3] transition-all duration-700"
      ></span>
      <!-- Glass body -->
      <span
        class="absolute inset-0 rounded-full bg-gradient-to-b from-white/[0.06] via-white/[0.02] to-white/[0.04] border border-white/[0.08] group-hover:border-white/[0.15] backdrop-blur-2xl transition-all duration-300 shadow-[inset_0_1px_2px_rgba(255,255,255,0.06)]"
      ></span>
      <!-- Top specular arc -->
      <span class="absolute inset-[2px] rounded-full overflow-hidden">
        <span
          class="absolute top-0 left-[18%] right-[18%] h-[42%] rounded-full bg-gradient-to-b from-white/[0.18] via-white/[0.04] to-transparent"
        ></span>
      </span>
      <!-- Bottom caustic -->
      <span
        class="absolute bottom-[2px] left-[22%] right-[22%] h-[22%] rounded-full bg-gradient-to-t from-[#80D0FF]/[0.06] to-transparent blur-[1px]"
      ></span>
      <!-- Sparkle Stars ✦ -->
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

    <!-- ═══ PURE EMOTION CENTER STAGE ═══ -->
    <div
      class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-40 transition-all duration-700"
    >
      <!-- Energy Orb Container -->
      <div
        class="relative flex items-center justify-center w-[300px] h-[300px]"
      >
        <!-- 1. Listening State (Ripple Rings based on Mic Volume) -->
        {#if phase === "listening"}
          <span
            class="absolute inset-0 rounded-full border border-[#00FFFF] transition-all duration-100 ease-out"
            style:transform="scale({0.5 + omni.vol * 1.5})"
            style:opacity={0.1 + omni.vol * 0.4}
          ></span>
          <span
            class="absolute inset-0 rounded-full border-[2px] border-[#00FFFF] transition-all duration-75 ease-out shadow-[0_0_30px_rgba(0,255,255,0.4)]"
            style:transform="scale({0.4 + omni.vol * 1.0})"
            style:opacity={0.3 + omni.vol * 0.5}
          ></span>

          <!-- 2. Thinking State (Spinning Quantum Core) -->
        {:else if phase === "thinking"}
          <div
            class="absolute inset-0 flex items-center justify-center animate-spin"
            style="animation-duration: 3s;"
          >
            <svg
              width="180"
              height="180"
              viewBox="0 0 180 180"
              fill="none"
              class="opacity-70"
            >
              <circle
                cx="90"
                cy="90"
                r="70"
                stroke="url(#think-gradient)"
                stroke-width="2"
                stroke-dasharray="60 40 20 40"
                class="origin-center animate-[spin_4s_linear_reverse_infinite]"
              />
              <circle
                cx="90"
                cy="90"
                r="55"
                stroke="#9d4edd"
                stroke-width="1.5"
                stroke-dasharray="30 20"
                opacity="0.6"
                class="origin-center animate-[spin_2s_linear_infinite]"
              />
              <defs>
                <linearGradient
                  id="think-gradient"
                  x1="0"
                  y1="0"
                  x2="180"
                  y2="180"
                >
                  <stop offset="0%" stop-color="#00FFFF" />
                  <stop offset="50%" stop-color="#9d4edd" />
                  <stop offset="100%" stop-color="#00FFFF" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div class="absolute inset-0 flex items-center justify-center">
            <div
              class="w-16 h-16 rounded-full bg-gradient-to-tr from-[#9d4edd] to-[#00FFFF] opacity-20 blur-xl animate-pulse"
            ></div>
          </div>

          <!-- 3. Speaking State (Pulsing Glow based on TTS Volume) -->
        {:else if phase === "speaking"}
          <span
            class="absolute inset-0 flex items-center justify-center transition-all duration-75 ease-out"
          >
            <!-- Core glow -->
            <div
              class="rounded-full bg-[#00FFFF] transition-all duration-75 ease-out shadow-[0_0_50px_rgba(0,255,255,0.8)]"
              style:width="{80 + omni.vol * 120}px"
              style:height="{80 + omni.vol * 120}px"
              style:opacity={0.4 + omni.vol * 0.5}
            ></div>
          </span>
          <!-- Dynamic equalizer ring -->
          <svg
            width="220"
            height="220"
            viewBox="0 0 220 220"
            class="absolute transition-all duration-100 ease-out"
            style:transform="scale({1 + omni.vol * 0.2})"
          >
            <circle
              cx="110"
              cy="110"
              r="90"
              fill="none"
              stroke="#00FFFF"
              stroke-width="1"
              stroke-dasharray="4 8"
              opacity="0.5"
              class="animate-[spin_10s_linear_infinite]"
            />
          </svg>

          <!-- 4. Idle State (Gentle Breathing) -->
        {:else}
          <div class="absolute inset-0 flex items-center justify-center">
            <div
              class="w-20 h-20 rounded-full border border-[#00FFFF]/20 shadow-[0_0_20px_rgba(0,255,255,0.1)] animate-[pulse_4s_ease-in-out_infinite]"
            ></div>
            <div
              class="absolute w-12 h-12 rounded-full bg-[#00FFFF]/5 blur-md animate-[pulse_3s_ease-in-out_infinite]"
            ></div>
            <Mic size={24} class="absolute text-[#00FFFF]/30" />
          </div>
        {/if}

        <!-- Central Anchor Dot (Always visible) -->
        <div class="absolute inset-0 flex items-center justify-center z-10">
          <div
            class="w-3 h-3 rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)] transition-all duration-300"
            class:scale-150={phase === "listening"}
            class:bg-[#00FFFF]={phase === "speaking"}
            class:bg-[#9d4edd]={phase === "thinking"}
          ></div>
        </div>
      </div>

      <!-- Minimalist Status Caption & Text Response -->
      <div
        class="mt-12 text-center min-h-[4rem] max-w-2xl px-6 flex flex-col items-center justify-start"
      >
        {#if phase === "listening" && omni.liveTrans}
          <p
            class="text-sm bg-black/40 px-4 py-2 rounded-full border border-white/5 text-white/70 font-light italic tracking-wide transition-opacity duration-300"
          >
            "{omni.liveTrans}"
          </p>
        {:else if phase === "thinking"}
          <p
            class="text-[10px] font-mono text-[#9d4edd]/70 uppercase tracking-[0.3em] animate-pulse"
          >
            Processing
          </p>
        {:else if phase === "speaking"}
          <div class="flex flex-col items-center gap-3">
            <p
              class="text-[10px] font-mono text-[#00FFFF]/70 uppercase tracking-[0.3em] animate-pulse"
            >
              Transmitting
            </p>
            {#if omni.dText}
              <p
                class="text-lg md:text-xl text-white/90 font-medium tracking-wide drop-shadow-md leading-relaxed scifi-text w-full"
                use:typewriter={{
                  speed: 30,
                  text: omni.dText,
                  getVolume: () => omni.vol,
                  isSpeaking: () => omni.isGhostSpeaking,
                }}
              >
                {omni.dText}
              </p>
            {/if}
          </div>
        {:else}
          <p
            class="text-[10px] font-mono text-white/20 uppercase tracking-[0.3em]"
          >
            Standby
          </p>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .scifi-text {
    will-change: contents;
    contain: layout style;
    text-shadow: 0 0 6px rgba(128, 210, 255, 0.08);
  }

  /* Typewriter emotion: active chars glow brighter */
  :global(.tw-active) {
    color: #e0f4ff;
    text-shadow:
      0 0 12px rgba(128, 232, 255, 0.4),
      0 0 4px rgba(255, 255, 255, 0.15);
  }
</style>
