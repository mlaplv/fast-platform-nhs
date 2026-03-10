<script lang="ts">
  import { vuiState } from "$lib/vui";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { fade } from "svelte/transition";
  import { playSciFiBeep, playSiriDing } from "$lib/utils/sfx";
  import VoiceStatusCaption from "./vui/VoiceStatusCaption.svelte";
  import ContentReviewCard from "./ui/ContentReviewCard.svelte";
  import { onMount } from "svelte";

  onMount(() => {
    // Rule R81.2: Stealth Wake on Mount — Check if there's an active campaign to resume
    // We send 'xohi' which is a wake word, but we handle it as a resume check on backend
    if (!nanobot.isVuiActive) {
      // Just check, don't necessarily open the modal unless there's a hit
      // This is handled by the orchestrator returning a RESUME_ROUTINE action
    }
  });

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

  // Rule R82.11: Safety Unmount — If for some reason we are active but have no data and not listening, close it.
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
    class="absolute inset-0 z-[900] flex flex-col pointer-events-none"
    transition:fade={{ duration: 400 }}
  >
    <!-- Main Container (Purely Transparent Overlay) -->
    <div class="relative w-full h-full pointer-events-none">
      <!-- VUI Content (Centered GPT-style) -->
      <div class="absolute inset-0 flex flex-col items-center">
        <VoiceStatusCaption {phase} />

        {#if nanobot.vuiResponse?.data?.category === "CONTENT_CREATE"}
          <div
            class="mt-8 w-full max-w-4xl animate-in fade-in zoom-in-95 duration-500 z-50 relative pointer-events-auto mb-12"
            transition:fade={{ duration: 250 }}
          >
            <ContentReviewCard
              campaign_id={nanobot.vuiResponse.data.campaign_id}
              keywords={nanobot.vuiResponse.data.keywords ||
                nanobot.vuiResponse.data.data?.keywords}
              assets={nanobot.vuiResponse.data.assets ||
                nanobot.vuiResponse.data.data?.assets}
              step={nanobot.vuiResponse.data.step || 1}
              status={nanobot.vuiResponse.data.status || "WAITING_FOR_REVIEW"}
              progress_msg={nanobot.vuiResponse.data.progress_msg || ""}
            />
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
