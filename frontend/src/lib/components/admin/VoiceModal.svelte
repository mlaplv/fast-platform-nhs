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
      console.log("[VoiceModal] ACTIVE. Category:", nanobot.vuiResponse?.data?.category, "CampaignID:", nanobot.vuiResponse?.data?.campaign_id);
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
        onclick={() => {
          nanobot.interruptAll();
          nanobot.resetVui();
        }}
        class="absolute top-[14px] right-6 z-[110000] group pointer-events-auto transition-all duration-300 active:scale-75"
        title="Close Session"
      >
        <div class="relative w-10 h-10 flex items-center justify-center transition-all duration-300">
           <X 
             size={20} 
             strokeWidth={2} 
             class="text-white/20 group-hover:text-red-500 group-hover:scale-125 transition-all duration-300 group-hover:drop-shadow-[0_0_8px_rgba(239,68,68,0.8)]" 
           />
           
           <!-- Modern Red Glow on Hover -->
           <div class="absolute inset-0 opacity-0 group-hover:opacity-40 bg-red-500/20 blur-xl transition-all duration-500 -z-10"></div>
        </div>
      </button>

      <!-- VUI Content (Centered GPT-style) -->
      <div class="{nanobot.isExpanded ? 'absolute inset-0 block overflow-hidden' : 'absolute inset-0 flex justify-center items-center overflow-hidden p-4'}">
        <!-- Voice Caption Layer (GPT-style Background/Overlay) -->
        <div class="absolute inset-0 left-0 w-full flex justify-center {nanobot.isExpanded ? 'z-[2000]' : 'z-[50]'} pointer-events-none">
          <VoiceStatusCaption {phase} />
        </div>

        {#if nanobot.vuiResponse?.data?.category === "CONTENT_CREATE" || nanobot.vuiResponse?.data?.campaign_id}
          <div
            class="transition-all duration-300 {nanobot.isExpanded ? 'fixed inset-0 w-screen h-screen z-[100000] m-0 rounded-none p-6 md:p-12 md:pb-24 bg-[#030712]/98 backdrop-blur-3xl' : 'fixed inset-0 w-full h-full md:relative md:w-[98%] md:h-[90vh] md:bg-black/40 md:rounded-3xl md:mt-12 md:shadow-2xl bg-[#020202] z-[50000] flex flex-col'} mx-auto pointer-events-auto"
            transition:fade={{ duration: 250 }}
          >
            <ContentReviewCard
              campaign_id={nanobot.vuiResponse.data.campaign_id}
              bind:keywords={nanobot.vuiResponse.data.keywords}
              bind:assets={nanobot.vuiResponse.data.assets}
              bind:outline={nanobot.vuiResponse.data.outline}
              bind:draft_content={nanobot.vuiResponse.data.draft_content}
              bind:step={nanobot.vuiResponse.data.step}
              bind:status={nanobot.vuiResponse.data.status}
              bind:progress_msg={nanobot.vuiResponse.data.progress_msg}
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
