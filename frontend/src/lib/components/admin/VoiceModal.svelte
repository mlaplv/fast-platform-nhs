<script lang="ts">
  import { vuiState } from "$lib/vui";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { fade, fly } from "svelte/transition";
  import { playSciFiBeep, playSiriDing } from "$lib/utils/sfx";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import VoiceStatusCaption from "./vui/VoiceStatusCaption.svelte";
  import ContentReviewCard from "./ui/ContentReviewCard.svelte";
  import X from "lucide-svelte/icons/x";
  import { onMount } from "svelte";

  let holdProgress = $state(0);
  let isHardKillReady = $state(false);

  onMount(() => {
    // Rule R81.2: Stealth Wake on Mount — Check if there's an active campaign to resume
    // We send 'xohi' which is a wake word, but we handle it as a resume check on backend
    if (!nanobot.isVuiActive) {
      // Just check, don't necessarily open the modal unless there's a hit
      // This is handled by the orchestrator returning a RESUME_ROUTINE action
    }
  });

  let wasActive = false;
  $effect(() => {
    // Phase 47/63: Only beep if voice modality AND transitioning from inactive to active
    if (nanobot.isVuiActive && !wasActive && nanobot.modality === "voice") {
      const isSilentResume = nanobot.vuiResponse?.data?.isSilent === true;
      if (!isSilentResume) {
        playSciFiBeep();
      }
    }
    wasActive = nanobot.isVuiActive;
  });

  let hasDinged = false;
  $effect(() => {
    // Only ding for voice modality
    if (vuiState.phase === "listening" && !hasDinged && nanobot.modality === "voice") {
      playSiriDing();
      hasDinged = true;
    } else if (vuiState.phase !== "listening") {
      hasDinged = false;
    }
  });

  let phase = $derived(vuiState.phase);

  $effect(() => {
    if (nanobot.isVuiActive) {
    }
  });

  // Rule R82.11: Safety Unmount
  $effect(() => {
    if (
      nanobot.isVuiActive &&
      !nanobot.vuiResponse &&
      vuiState.phase === "idle" &&
      !vuiState.isStarting
    ) {
      console.warn(
        "[VoiceModal] Safety unmount triggered: isVuiActive=true but no response/phase.",
      );
      vuiState.showCampaign = false;
      nanobot.resetVui();
    }
  });

  // Elite 2026: Auto-hide campaign UI when starting a new conversation
  $effect(() => {
    if (vuiState.phase === 'listening' || vuiState.phase === 'thinking') {
      if (vuiState.showCampaign) vuiState.showCampaign = false;
    }
  });
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
    class="absolute inset-0 flex flex-col pointer-events-none transition-all duration-300"
    style="z-index: {Z_INDEX_ADMIN.OVERLAY};"
    transition:fade={{ duration: 300 }}
  >
    <!-- Main Container (Purely Transparent Overlay) -->
    <div class="relative w-full h-full pointer-events-none">
      <!-- Pure Minimalist Cyber-Exit (2026 Edition) -->
      <button
        onmousedown={(e) => {
          if (e.button !== 0) return;
          const start = Date.now();
          const timer = setInterval(() => {
            const elapsed = Date.now() - start;
            holdProgress = Math.min(elapsed / 600, 1);
            if (holdProgress >= 1) {
              isHardKillReady = true;
              clearInterval(timer);
            }
          }, 16);

          const endHold = () => {
            clearInterval(timer);
            const duration = Date.now() - start;
            if (duration >= 600) {
              nanobot.hardKill(nanobot.vuiResponse?.data?.campaign_id || nanobot.currentData?.campaign_id);
            } else {
              nanobot.softClose();
            }
            holdProgress = 0;
            isHardKillReady = false;
            window.removeEventListener('mouseup', endHold);
          };
          window.addEventListener('mouseup', endHold);
        }}
        class="absolute top-1 right-1 group pointer-events-auto transition-all duration-300 active:scale-90"
        style="z-index: {Z_INDEX_ADMIN.VUI_EXIT}"
        title="Short: Hide UI | Long: Kill Process (Hard Kill)"
      >
        <div class="relative w-8 h-8 flex items-center justify-center rounded-md hover:bg-white/10 transition-all duration-200">
           <!-- Progress Ring for Hard Kill (Subtle) -->
           <svg class="absolute inset-0 w-full h-full -rotate-90 pointer-events-none">
             <circle 
               cx="16" cy="16" r="12" 
               fill="none" 
               stroke="currentColor" 
               stroke-width="1.5" 
               stroke-dasharray="75.39"
               stroke-dashoffset={75.39 * (1 - holdProgress)}
               style="transition: stroke-dashoffset 0.1s linear"
               class={isHardKillReady ? "text-red-500" : "text-white/40"}
             />
           </svg>

           <X 
             size={16} 
             strokeWidth={2} 
             class="transition-all duration-300 {isHardKillReady ? 'text-red-500 scale-110' : 'text-white/70 group-hover:text-white'}" 
           />
        </div>
      </button>

      <!-- VUI Content (Centered GPT-style) -->
      <div class="{nanobot.isExpanded ? 'absolute inset-0 block overflow-hidden' : 'absolute inset-0 flex justify-center items-center overflow-hidden p-4'}">
        <!-- Voice Caption Layer (GPT-style Background/Overlay) -->
        <div class="absolute inset-0 left-0 w-full flex justify-center pointer-events-none" style="z-index: {nanobot.isExpanded ? Z_INDEX_ADMIN.VUI_CAPTION_EXPANDED : Z_INDEX_ADMIN.VUI_CAPTION}">
          <VoiceStatusCaption {phase} />
        </div>


      </div>
    </div>
  </div>
{/if}
