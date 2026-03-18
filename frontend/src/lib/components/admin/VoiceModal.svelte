<script lang="ts">
  import { vuiState } from "$lib/vui";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fade } from "svelte/transition";
  import { playSciFiBeep, playSiriDing } from "$lib/utils/sfx";
  import VoiceStatusCaption from "./vui/VoiceStatusCaption.svelte";
  import ContentReviewCard from "./ui/ContentReviewCard.svelte";
  import X from "lucide-svelte/icons/x";
  import { onMount } from "svelte";

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
      nanobot.resetVui();
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
    class="absolute inset-0 z-[99999] flex flex-col pointer-events-none"
    transition:fade={{ duration: 400 }}
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
            if (typeof holdProgress !== 'undefined') holdProgress = Math.min(elapsed / 600, 1);
            if (typeof isHardKillReady !== 'undefined' && holdProgress >= 1) {
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
            if (typeof holdProgress !== 'undefined') holdProgress = 0;
            if (typeof isHardKillReady !== 'undefined') isHardKillReady = false;
            window.removeEventListener('mouseup', endHold);
          };
          window.addEventListener('mouseup', endHold);
        }}
        class="absolute top-1 right-1 z-[110000] group pointer-events-auto transition-all duration-300 active:scale-90"
        title="Short: Hide UI | Long: Kill Process (Hard Kill)"
      >
        <div class="relative w-8 h-8 flex items-center justify-center rounded-full bg-black/20 backdrop-blur-md border border-white/10 hover:border-white/20 transition-all duration-300">
           <!-- Progress Ring for Hard Kill -->
           <svg class="absolute inset-0 w-full h-full -rotate-90 pointer-events-none">
             <circle 
               cx="16" cy="16" r="14" 
               fill="none" 
               stroke="currentColor" 
               stroke-width="1.5" 
               class="text-white/5"
             />
             <circle 
               cx="16" cy="16" r="14" 
               fill="none" 
               stroke="currentColor" 
               stroke-width="1.5" 
               stroke-dasharray="87.96"
               stroke-dashoffset={87.96 * (1 - holdProgress)}
               style="transition: stroke-dashoffset 0.1s linear"
               class={isHardKillReady ? "text-red-500" : "text-white/60"}
             />
           </svg>

           <X 
             size={12} 
             strokeWidth={isHardKillReady ? 3 : 2} 
             class="transition-all duration-300 {isHardKillReady ? 'text-red-500 scale-125' : 'text-white group-hover:scale-110'}" 
           />
           
           <!-- Modern Red Glow on Hover -->
           <div class="absolute inset-0 opacity-0 group-hover:opacity-40 bg-red-500/20 blur-xl transition-all duration-500 -z-10"></div>
        </div>
      </button>

      <!-- VUI Content (Centered GPT-style) -->
      <div class="{nanobot.isExpanded ? 'absolute inset-0 block overflow-hidden' : 'absolute inset-0 flex justify-center items-center overflow-hidden p-4'}">
        <!-- Voice Caption Layer (GPT-style Background/Overlay) -->
        <div class="absolute inset-0 left-0 w-full flex justify-center {nanobot.isExpanded ? 'z-[5]' : 'z-[50]'} pointer-events-none">
          <VoiceStatusCaption {phase} />
        </div>

        {#if nanobot.vuiResponse?.data?.category === "CONTENT_CREATE" || nanobot.vuiResponse?.data?.campaign_id}
          <div
            class="transition-all duration-300 {nanobot.isExpanded ? 'fixed inset-0 w-screen h-screen z-[150000] m-0 rounded-none p-6 md:p-12 md:pb-24 bg-[#030712]/98 backdrop-blur-3xl' : 'fixed inset-0 w-full h-full md:relative md:w-[98%] md:h-[90vh] md:bg-black/40 md:rounded-3xl md:mt-12 md:shadow-2xl bg-[#020202] z-[120000] flex flex-col'} mx-auto pointer-events-auto"
            transition:fade={{ duration: 250 }}
          >
            <ContentReviewCard
              campaign_id={nanobot.vuiResponse.data.campaign_id}
              bind:keywords={nanobot.vuiResponse.data.keywords}
              bind:assets={nanobot.vuiResponse.data.assets}
              bind:reserve_assets={nanobot.vuiResponse.data.reserve_assets}
              bind:outline={nanobot.vuiResponse.data.outline}
              bind:draft_content={nanobot.vuiResponse.data.draft_content}
              bind:step={nanobot.vuiResponse.data.step}
              bind:status={nanobot.vuiResponse.data.status}
              bind:progress_msg={nanobot.vuiResponse.data.progress_msg}
              bind:finalHtml={nanobot.vuiResponse.data.final_html}
              bind:selectedAvatarUrl={nanobot.vuiResponse.data.selectedAvatarUrl}
              bind:selectedAssetIndex={nanobot.vuiResponse.data.selectedAssetIndex}
              bind:creation_config={nanobot.vuiResponse.data.creation_config}
              bind:analysis_cache={nanobot.vuiResponse.data.analysis_cache}
              bind:analysis_metrics={nanobot.vuiResponse.data.analysis_metrics}
            />
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
