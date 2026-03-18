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
  class="flex h-screen overflow-hidden bg-[#000000] text-gray-100 font-sans selection:bg-[#00FFFF]/30 relative"
>
  <!-- Liquid & Water Drop Background Layer (Vantablack 70% Darker) -->
  <div
    class="absolute inset-0 z-0 pointer-events-none overflow-hidden bg-black"
  >
    <!-- Base Liquid Blobs (70% Opacity Reduction) -->
    <div
      class="absolute top-[-10%] left-[-10%] w-[80%] h-[80%] bg-[radial-gradient(circle_at_50%_50%,rgba(0,255,255,0.012),transparent_60%)] animate-[liquid_25s_ease-in-out_infinite]"
    ></div>
    <div
      class="absolute bottom-[-10%] right-[-10%] w-[90%] h-[90%] bg-[radial-gradient(circle_at_50%_50%,rgba(57,255,20,0.006),transparent_50%)] animate-[liquid_30s_ease-in-out_infinite_reverse]"
    ></div>

    <!-- Floating "Water Drops" -->
    <div
      class="absolute top-[20%] left-[30%] w-[30%] h-[30%] bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.003),transparent_40%)] animate-[drop_15s_ease-in-out_infinite]"
    ></div>
    <div
      class="absolute bottom-[30%] right-[20%] w-[25%] h-[25%] bg-[radial-gradient(circle_at_50%_50%,rgba(0,255,255,0.006),transparent_45%)] animate-[drop_20s_ease-in-out_infinite_reverse]"
    ></div>

    <!-- Center Glow -->
    <div
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(0,0,0,0)_30%,rgba(0,255,255,0.005)_100%)]"
    ></div>
  </div>

  <!-- Left/Central Main Content -->
  <main class="flex-1 relative flex flex-col min-w-0">
    <!-- Header/Status Bar -->
    <header
      class="h-12 border-b border-white/5 flex items-center justify-between px-5 bg-[#010101] z-30"
      class:hidden={nanobot.isVuiActive && !nanobot.isTraining}
    >
      <div class="flex items-center gap-3">
        <XohiNanoSprite />
        <button
          onclick={() => nanobot.toggleHeartbeat()}
          class="flex flex-col items-start hover:brightness-125 transition-all group/xohi"
          title={nanobot.heartbeatCollapsed
            ? "Mở rộng Heartbeat"
            : "Thu gọn Heartbeat"}
        >
          <h1
            class="text-xs font-mono tracking-[0.2em] uppercase text-[#00FFFF] opacity-80 group-hover/xohi:opacity-100 group-hover/xohi:drop-shadow-[0_0_8px_rgba(0,255,255,0.5)] transition-all"
          >
            &gt;_Xohi
          </h1>
          <p
            class="text-[10px] font-mono text-gray-500 uppercase group-hover/xohi:text-gray-400 transition-colors"
          >
            Core // {nanobot.userEmail || "ADMIN_ACTIVE"}
          </p>
        </button>
      </div>

      <div class="flex gap-4 items-center">
        <!-- CONSOLIDATED HUD: SESSION & SYSTEM HEALTH -->
        <CurrentSessionStatus />

        <!-- HUD Widgets -->
        <div class="flex items-center gap-3 pl-4 border-l border-white/5">
          <NotificationHud />
          <UserHud />
          
          <!-- V71.2: Dynamic Toggle visibility - Always show Expand button if sidebar is not visible -->
          <button
            onclick={() => nanobot.toggleHeartbeat()}
            class="flex items-center justify-center w-9 h-9 rounded-md hover:bg-white/5 text-neon-cyan/60 hover:text-neon-cyan transition-colors"
            class:hidden={nanobot.heartbeatCollapsed === false}
            title="Mở rộng Heartbeat"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><path d="M15 3v18"/></svg>
          </button>
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
        <VoiceModal />
      </div>

      <div
        class="absolute inset-0 z-[160000] pointer-events-none"
      >
        <div
          class="{nanobot.universalModalOpen
            ? 'pointer-events-auto'
            : 'pointer-events-none'} w-full h-full"
        >
          <UniversalModal />
        </div>
      </div>
    </div>

    <!-- OmniCommand: Floats over everything, persistent for VUI control -->
    <div
      class="relative z-[1100] pt-3 pb-6 pointer-events-none"
      class:omni-waterdrop={nanobot.universalModalOpen}
    >
      <div class="pointer-events-auto max-w-4xl mx-auto px-4 sm:px-6">
        <OmniCommand />
      </div>
    </div>

    <div class:hidden={nanobot.isVuiActive && !nanobot.isTraining}>
      <FullLogView />
      <VaultModal />
      <ConfirmationModal />
    </div>
  </main>

  <!-- Right Sidebar: Heartbeat -->
  <aside
    class="relative h-full z-[100] shadow-[-20px_0_30px_rgba(0,0,0,0.5)] border-l border-white/5 bg-[#010101] transition-all duration-300 ease-in-out group/sidebar overflow-visible"
    class:heartbeat-manual-collapse={nanobot.heartbeatCollapsed === true}
    class:heartbeat-manual-expand={nanobot.heartbeatCollapsed === false}
    id="heartbeat-sidebar"
  >
    <div class="h-full w-full transition-opacity duration-300 sidebar-content">
      <HeartbeatStream />
    </div>

  </aside>

  <!-- Version Footer (Global Bottom) -->
  <TechStackFooter />
</div>

<style>
  /* Adaptive Heartbeat Sidebar Logic */
  #heartbeat-sidebar {
    --sidebar-w: 300px;
    width: var(--sidebar-w);
    min-width: var(--sidebar-w);
  }

  /* Default: Hidden (Manual Toggle Only) */
  #heartbeat-sidebar {
    --sidebar-w: 0px;
  }
  #heartbeat-sidebar .sidebar-content {
    opacity: 0;
    pointer-events: none;
  }
  #heartbeat-sidebar .vertical-indicator {
    display: none;
  }

  /* Manual Override: Force Collapse (Trumps Auto) */
  :global(.heartbeat-manual-collapse) {
    --sidebar-w: 0px !important;
    border-left: none !important;
  }
  :global(.heartbeat-manual-collapse) .sidebar-content {
    opacity: 0 !important;
    pointer-events: none !important;
  }
  :global(.heartbeat-manual-collapse) .vertical-indicator {
    display: none !important;
  }

  /* Manual Override: Force Expand (Trumps Auto) */
  :global(.heartbeat-manual-expand) {
    --sidebar-w: 300px !important;
  }
  @media (min-width: 1280px) {
    :global(.heartbeat-manual-expand) {
      --sidebar-w: 350px !important; /* XL width on large screens */
    }
  }
  :global(.heartbeat-manual-expand) .sidebar-content {
    opacity: 1 !important;
    pointer-events: auto !important;
  }
  :global(.heartbeat-manual-expand) .vertical-indicator {
    opacity: 0 !important;
  }

  /* Standard Waterdrop Styles */
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
