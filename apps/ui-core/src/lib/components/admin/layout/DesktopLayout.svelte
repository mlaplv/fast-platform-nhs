<script lang="ts">
  import HeartbeatStream from "../HeartbeatStream.svelte";
  import DynamicCanvas from "../DynamicCanvas.svelte";
  import OmniCommand from "../OmniCommand.svelte";
  import XohiNanoSprite from "../XohiNanoSprite.svelte";
  import XohiWatermark from "../XohiWatermark.svelte";
  import VoiceModal from "../VoiceModal.svelte";
  import FullLogView from "../ui/FullLogView.svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import NotificationHud from "../hud/NotificationHud.svelte";
  import UserHud from "../hud/UserHud.svelte";
  import VaultModal from "../VaultModal.svelte";
  import ConfirmationModal from "../ui/ConfirmationModal.svelte";
  import UniversalModal from "../ui/UniversalModal.svelte";
  import { permissionState } from "$lib/state/permissions.svelte";
  import CurrentSessionStatus from "./HUD/CurrentSessionStatus.svelte";
  import TechStackFooter from "./TechStackFooter.svelte";

  let { children } = $props();
</script>

<div
  class="flex h-screen overflow-hidden bg-[#050505] text-gray-100 font-sans selection:bg-[#00FFFF]/30 relative"
>
  <!-- Liquid & Water Drop Background Layer (Restored for V30.0) -->
  <div
    class="absolute inset-0 z-0 pointer-events-none overflow-hidden bg-black"
  >
    <!-- Base Liquid Blobs -->
    <div
      class="absolute top-[-10%] left-[-10%] w-[80%] h-[80%] bg-[radial-gradient(circle_at_50%_50%,rgba(0,255,255,0.04),transparent_60%)] animate-[liquid_25s_ease-in-out_infinite]"
    ></div>
    <div
      class="absolute bottom-[-10%] right-[-10%] w-[90%] h-[90%] bg-[radial-gradient(circle_at_50%_50%,rgba(57,255,20,0.02),transparent_50%)] animate-[liquid_30s_ease-in-out_infinite_reverse]"
    ></div>

    <!-- Floating "Water Drops" (Specularity/Reflections) -->
    <div
      class="absolute top-[20%] left-[30%] w-[30%] h-[30%] bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.01),transparent_40%)] animate-[drop_15s_ease-in-out_infinite]"
    ></div>
    <div
      class="absolute bottom-[30%] right-[20%] w-[25%] h-[25%] bg-[radial-gradient(circle_at_50%_50%,rgba(0,255,255,0.02),transparent_45%)] animate-[drop_20s_ease-in-out_infinite_reverse]"
    ></div>

    <!-- Center Glow -->
    <div
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(0,0,0,0)_30%,rgba(0,255,255,0.01)_100%)]"
    ></div>
  </div>

  <!-- Left/Central Main Content -->
  <main class="flex-1 relative flex flex-col min-w-0">
    <!-- Header/Status Bar -->
    <header
      class="h-12 border-b border-[#1a1a1a] flex items-center justify-between px-5 bg-[#080808] z-30"
      class:hidden={nanobot.isVuiActive && !nanobot.isTraining}
    >
      <div class="flex items-center gap-3">
        <XohiNanoSprite />
        <div>
          <h1
            class="text-xs font-mono tracking-[0.2em] uppercase text-[#00FFFF] opacity-80"
          >
            Xohi Darkboard
          </h1>
          <p class="text-[10px] font-mono text-gray-500 uppercase">
            V55.0 Core // {nanobot.userEmail || "ADMIN_ACTIVE"}
          </p>
        </div>
      </div>

      <div class="flex gap-4 items-center">
        <!-- CONSOLIDATED HUD: SESSION & SYSTEM HEALTH -->
        <CurrentSessionStatus />

        <!-- HUD Widgets -->
        <div class="flex items-center gap-3 pl-4 border-l border-white/5">
          <NotificationHud />
          <UserHud />
        </div>
      </div>
    </header>

    <!-- Canvas Area -->
    <div class="flex-1 relative overflow-hidden z-10">
      <!-- CENTRAL BRANDING WATERMARK -->
      <XohiWatermark />

      <div class="relative z-10 w-full h-full p-6">
        <div class:hidden={nanobot.isVuiActive && !nanobot.isTraining}>
          <DynamicCanvas />
        </div>
        {@render children()}
      </div>

      <!-- XoHi Widget Modal (NOW scoped to Canvas Area only, NOT covering Footer/OmniCommand) -->
      <div class="absolute inset-0 z-50 pointer-events-none" class:hidden={nanobot.isVuiActive && !nanobot.isTraining}>
        <div class="{nanobot.universalModalOpen ? 'pointer-events-auto' : 'pointer-events-none'} w-full h-full">
          <UniversalModal />
        </div>
      </div>
    </div>

    <!-- OmniCommand: Floats over modal, wrapper is transparent + click-through -->
    <div
      class="relative z-[60] py-3 pointer-events-none"
      class:hidden={nanobot.isVuiActive && !nanobot.isTraining}
      class:omni-waterdrop={nanobot.universalModalOpen}
    >
      <div class="pointer-events-auto max-w-4xl mx-auto px-4 sm:px-6">
        <OmniCommand />
      </div>
    </div>

    <!-- Voice Modal (Pure Face) -->
    <VoiceModal />

    <!-- Version Footer -->
    <TechStackFooter />

    <!-- Mission Control Overlays (FullLog, Vault, Confirm — still full-screen) -->
    <div class:hidden={nanobot.isVuiActive && !nanobot.isTraining}>
      <FullLogView />
      <VaultModal />
      <ConfirmationModal />
    </div>
  </main>

  <!-- Right Sidebar: Heartbeat -->
  <aside
    class="w-[300px] xl:w-[350px] shrink-0 h-full relative z-20 shadow-[-20px_0_30px_rgba(0,0,0,0.5)] border-l border-[#1a1a1a] bg-[#080808]"
    class:hidden={nanobot.isVuiActive && !nanobot.isTraining}
  >
    <HeartbeatStream />
  </aside>
</div>

<style>
  /* Waterdrop Glass Effect — Safari iOS address bar style */
  /* Only target the plus button (.relative > button), NOT the mic button inside the input pill */
  :global(.omni-waterdrop) :global(.relative > button),
  :global(.omni-waterdrop) :global(.flex-1.rounded-full) {
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

  :global(.omni-waterdrop) :global(.relative > button:hover),
  :global(.omni-waterdrop) :global(.flex-1.rounded-full:focus-within) {
    border-color: rgba(0, 255, 255, 0.3) !important;
    box-shadow:
      0 8px 40px rgba(0, 255, 255, 0.12),
      inset 0 1px 0 rgba(255, 255, 255, 0.1),
      0 1px 3px rgba(0, 0, 0, 0.5) !important;
  }
</style>
