<script lang="ts">
  import OmniCommand from "../OmniCommand.svelte";
  import VoiceModal from "../VoiceModal.svelte";
  import XohiNanoSprite from "../XohiNanoSprite.svelte";
  import MobileActionDrawer from "./MobileActionDrawer.svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fade, fly } from "svelte/transition";
  import HeartbeatStream from "../HeartbeatStream.svelte";
  import DynamicCanvas from "../DynamicCanvas.svelte";
  import XohiWatermark from "../XohiWatermark.svelte";
  import UniversalModal from "../ui/UniversalModal.svelte";

  let { children } = $props();

  const versions: Record<string, string> =
    typeof (globalThis as Record<string, unknown>).__APP_VERSIONS__ === "object"
      ? ((globalThis as Record<string, unknown>).__APP_VERSIONS__ as Record<
          string,
          string
        >)
      : {
          svelte: "5.x",
          tailwind: "4.x",
          sqlalchemy: "2.x",
          alembic: "1.x",
          litestar: "2.x",
          pydantic_ai: "0.x",
          litellm: "1.x",
          python: "3.x",
          caddy: "2.x",
        };

  // Safari-style Scroll Logic
  let scrollY = $state(0);
  let lastScrollY = 0;
  let isScrollingDown = $state(false);
  let isAtTop = $derived(scrollY < 20);

  function handleScroll(e: Event) {
    const target = e.target as HTMLElement;
    scrollY = target.scrollTop;
    isScrollingDown = scrollY > lastScrollY && scrollY > 50;
    lastScrollY = scrollY;
  }
</script>

<div
  class="fixed inset-0 flex flex-col overflow-hidden bg-[#020202] text-gray-100 font-sans"
>
  <!-- Liquid & Water Drop Background Layer (Apple/Next-Gen Style) -->
  <div
    class="absolute inset-0 z-0 pointer-events-none overflow-hidden bg-black"
  >
    <!-- Base Liquid Blobs -->
    <div
      class="absolute top-[-10%] left-[-10%] w-[80%] h-[80%] bg-[radial-gradient(circle_at_50%_50%,rgba(0,255,255,0.06),transparent_60%)] animate-[liquid_20s_ease-in-out_infinite]"
    ></div>
    <div
      class="absolute bottom-[-10%] right-[-10%] w-[90%] h-[90%] bg-[radial-gradient(circle_at_50%_50%,rgba(57,255,20,0.03),transparent_50%)] animate-[liquid_25s_ease-in-out_infinite_reverse]"
    ></div>

    <!-- Floating "Water Drops" (Specularity/Reflections) -->
    <div
      class="absolute top-[20%] left-[30%] w-[40%] h-[40%] bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.02),transparent_40%)] animate-[drop_12s_ease-in-out_infinite]"
    ></div>
    <div
      class="absolute bottom-[30%] right-[20%] w-[30%] h-[30%] bg-[radial-gradient(circle_at_50%_50%,rgba(0,255,255,0.03),transparent_45%)] animate-[drop_18s_ease-in-out_infinite_reverse]"
    ></div>

    <!-- Center Glow -->
    <div
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(0,0,0,0)_30%,rgba(0,255,255,0.01)_100%)]"
    ></div>
  </div>

  <!-- Glass Header (Safari Style - Fixed) -->
  <header
    class="fixed top-0 left-0 right-0 h-14 border-b border-white/5 flex items-center justify-between px-6 bg-black/40 backdrop-blur-3xl z-50 transition-all duration-500 {isScrollingDown
      ? 'translate-y-[-100%]'
      : 'translate-y-0'}"
    class:hidden={nanobot.isVuiActive && !nanobot.isTraining}
  >
    <div class="flex items-center gap-3">
      <XohiNanoSprite />
      <span
        class="text-[10px] font-mono tracking-[0.3em] uppercase text-[#00FFFF]/80"
        >Xohi OS</span
      >
    </div>

    <div
      class="text-[8px] font-mono text-gray-500 uppercase tracking-widest opacity-60"
    >
      NODE_V55 // PRO
    </div>
  </header>

  <!-- Full-Height Main Content -->
  <main class="relative flex-1 z-10 overflow-hidden flex flex-col">
    <!-- CENTRAL BRANDING WATERMARK -->
    <XohiWatermark />
    <!-- Full-Height Log Stream -->
    <div
      onscroll={handleScroll}
      class="flex-1 overflow-y-auto overscroll-touch relative scroll-smooth selection:bg-[#00FFFF]/20"
    >
      <div class:hidden={nanobot.isVuiActive && !nanobot.isTraining}>
        <HeartbeatStream hideHeader={true} />
      </div>
    </div>

    <!-- Safari-style Floating Bottom Bar: MUST stay mounted during VUI -->
    <div
      class="fixed bottom-0 left-0 right-0 pb-10 pt-4 z-[60] pointer-events-none transition-all duration-[700ms] ease-[cubic-bezier(0.25, 1, 0.5, 1)] {isScrollingDown
        ? 'translate-y-4 scale-[0.96] opacity-60'
        : 'translate-y-0 scale-100 opacity-100'}"
      class:hidden={nanobot.isVuiActive && !nanobot.isTraining}
      class:omni-waterdrop-mobile={nanobot.universalModalOpen}
    >
      <div class="pointer-events-auto">
        <OmniCommand />
      </div>
    </div>

    <!-- XoHi Widget Modal (covers full main area on mobile) -->
    <div
      class="absolute inset-0 z-50 pointer-events-none"
      class:hidden={nanobot.isVuiActive && !nanobot.isTraining}
    >
      <div class="{nanobot.universalModalOpen ? 'pointer-events-auto' : 'pointer-events-none'} w-full h-full">
        <UniversalModal />
      </div>
    </div>

    {@render children()}
  </main>

  <div class:hidden={nanobot.isVuiActive && !nanobot.isTraining}>
    <MobileActionDrawer />
  </div>

  <!-- Version Footer (1-line, subtle — sits just below OmniCommand safe area) -->
  <div
    class="fixed bottom-0 right-0 z-30 pr-3 pb-0.5 pointer-events-none"
    class:hidden={nanobot.isVuiActive && !nanobot.isTraining}
  >
    <p
      class="text-[7px] font-mono text-gray-500/50 tracking-widest uppercase select-none"
    >
      Sv{versions.svelte} · TW{versions.tailwind} · SQLA{versions.sqlalchemy} · Alb{versions.alembic} · Lite{versions.litestar} · PAI{versions.pydantic_ai} · LLM{versions.litellm} · Cad{versions.caddy} · Py{versions.python}
    </p>
  </div>

  <!-- Voice Modal (Pure Face) -->
  <VoiceModal />
</div>

<style>
  @keyframes liquid {
    0%,
    100% {
      transform: translate(0, 0) scale(1) rotate(0deg);
    }
    33% {
      transform: translate(5%, -5%) scale(1.05) rotate(2deg);
    }
    66% {
      transform: translate(-3%, 8%) scale(0.95) rotate(-1deg);
    }
  }

  @keyframes drop {
    0%,
    100% {
      transform: translate(0, 0) scale(1) skew(0deg);
      opacity: 0.3;
    }
    50% {
      transform: translate(-10px, 20px) scale(1.1) skew(2deg);
      opacity: 0.6;
    }
  }

  /* Mobile Waterdrop Glass Effect for OmniCommand */
  :global(.omni-waterdrop-mobile) :global(.relative > button),
  :global(.omni-waterdrop-mobile) :global(.flex-1.rounded-full) {
    background: rgba(0, 255, 255, 0.04) !important;
    backdrop-filter: blur(24px) saturate(1.4) !important;
    -webkit-backdrop-filter: blur(24px) saturate(1.4) !important;
    border-color: rgba(0, 255, 255, 0.15) !important;
    box-shadow:
      0 4px 30px rgba(0, 255, 255, 0.08),
      inset 0 1px 0 rgba(255, 255, 255, 0.06),
      0 1px 3px rgba(0, 0, 0, 0.4) !important;
    transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1) !important;
  }
</style>
