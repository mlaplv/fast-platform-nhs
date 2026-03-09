<script lang="ts">
  import { vuiState } from "$lib/vui";
  import Mic from "lucide-svelte/icons/mic";
  import { scale } from "svelte/transition";

  let { phase } = $props();

  // VUI 2026: Animation Bypass Rule (Rule 1.7)
  function orbAnimator(node: HTMLElement) {
    let afId: number;
    function loop() {
      let v = vuiState.volume;
      if (v < 0.01) {
        v = 0.005 + Math.sin(Date.now() / 1500) * 0.004;
      }
      const time = Date.now();

      node.style.setProperty("--vol", v.toString());
      node.style.setProperty("--t400s", Math.sin(time / 400).toString());
      node.style.setProperty("--t400c", Math.cos(time / 400).toString());
      node.style.setProperty("--t900s", Math.sin(time / 900).toString());
      node.style.setProperty("--t900c", Math.cos(time / 900).toString());
      node.style.setProperty("--t1100s", Math.sin(time / 1100).toString());
      node.style.setProperty("--t1100c", Math.cos(time / 1100).toString());
      node.style.setProperty("--t750s", Math.sin(time / 750).toString());
      node.style.setProperty("--t750c", Math.cos(time / 750).toString());
      node.style.setProperty("--t80s", Math.sin(time / 80).toString());

      afId = requestAnimationFrame(loop);
    }
    loop();
    return {
      destroy() {
        cancelAnimationFrame(afId);
      },
    };
  }
</script>

<div
  class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-40 transition-all duration-700"
  use:orbAnimator
>
  <div class="relative flex items-center justify-center w-[400px] h-[400px] transition-transform duration-500 {phase !== 'idle' ? 'translate-y-[-110px]' : '-translate-y-20'}">
    <div
      class="absolute inset-0 flex items-center justify-center pointer-events-none"
      style="filter: url(#gooey) contrast(1.2) saturate(1.4);"
    >
      <div
        class="absolute w-[200px] h-[200px] rounded-full bg-cyan-500/20 blur-[60px] transition-all duration-1000"
        style="transform: scale(calc(1 + var(--vol) * 1.5))"
      ></div>

      {#if phase === "listening" || phase === "speaking"}
        <div
          class="absolute w-32 h-32 rounded-full transition-all duration-150 ease-out shadow-[0_0_40px_rgba(0,255,255,0.4)]"
          style:background={phase === "listening"
            ? "#00FFFF"
            : "linear-gradient(to top right, #3b82f6, #06b6d4)"}
          style="transform: scale(calc(1 + var(--vol) * 1.8)) translate(calc(var(--t400s) * 20px), calc(var(--t400c) * 20px)); opacity: calc(0.9 + var(--vol));"
        ></div>

        <div
          class="absolute w-20 h-20 rounded-full bg-cyan-400 transition-all duration-200"
          style="transform: translate(calc(var(--t900c) * 100px * (1 + var(--vol))), calc(var(--t900s) * 100px * (1 + var(--vol)))) scale(calc(0.8 + var(--vol)));"
        ></div>

        <div
          class="absolute w-16 h-16 rounded-full bg-indigo-500/90 transition-all duration-300"
          style="transform: translate(calc(var(--t1100s) * -110px * (1 + var(--vol))), calc(var(--t1100c) * -110px * (1 + var(--vol)))) scale(calc(0.7 + var(--vol)));"
        ></div>

        <div
          class="absolute w-24 h-24 rounded-full bg-teal-400/80 transition-all duration-150"
          style="transform: translate(calc(var(--t750c) * -60px), calc(var(--t750s) * 60px)) scale(calc(0.9 + var(--vol) * 2));"
        ></div>
      {:else if phase === "thinking" || phase === "executing"}
        <div
          class="absolute w-36 h-36 rounded-full bg-gradient-to-tr from-indigo-600 via-purple-500 to-cyan-400 animate-pulse blur-[1px]"
          style:background={phase === "executing"
            ? "linear-gradient(to bottom right, #8b5cf6, #ec4899)"
            : ""}
          style="transform: scale(calc(1.1 + var(--t80s) * 0.2))"
        ></div>
        <div
          class="absolute w-24 h-24 rounded-full bg-white/20 animate-ping opacity-40"
        ></div>
      {:else}
        <div
          class="absolute w-32 h-32 rounded-full bg-cyan-500/20 animate-[pulse_5s_infinite] blur-xl"
        ></div>
        <div
          class="absolute w-16 h-16 rounded-full border-2 border-cyan-400/30 flex items-center justify-center backdrop-blur-sm"
        >
          <Mic size={24} class="text-cyan-400/40" />
        </div>
      {/if}
    </div>

    <div
      class="absolute inset-0 flex items-center justify-center z-10 pointer-events-none"
    >
      <div
        class="w-4 h-4 rounded-full bg-white shadow-[0_0_15px_rgba(255,255,255,1)] transition-all duration-300 flex items-center justify-center overflow-visible"
        style="transform: scale(calc(1 + var(--vol) * 1.5)); opacity: calc(0.8 + var(--vol) * 0.2);"
      >
        {#if phase === "listening"}
          <div in:scale={{ duration: 400, start: 0.5 }} class="absolute">
            <Mic
              size={14}
              class="text-[#00FFFF] drop-shadow-[0_0_8px_rgba(0,255,255,0.8)]"
              strokeWidth={3}
            />
          </div>
        {/if}
      </div>
    </div>
  </div>

  <svg
    class="absolute w-0 h-0 overflow-hidden pointer-events-none"
    aria-hidden="true"
  >
    <defs>
      <filter id="gooey">
        <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur" />
        <feColorMatrix
          in="blur"
          mode="matrix"
          values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -9"
          result="goo"
        />
        <feComposite in="SourceGraphic" in2="goo" operator="atop" />
      </filter>
    </defs>
  </svg>
</div>
