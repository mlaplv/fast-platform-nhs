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

  let wasActive = false;
  $effect(() => {
    // Only beep if transitioning from inactive to active (prevents autoplay on page load)
    if (nanobot.isVuiActive && !wasActive) {
      playSciFiBeep();
    }
    wasActive = nanobot.isVuiActive;
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
    class="absolute inset-0 z-[99999] flex flex-col pointer-events-none"
    transition:fade={{ duration: 400 }}
  >
    <!-- Main Container (Purely Transparent Overlay) -->
    <div class="relative w-full h-full pointer-events-none">
      <!-- VUI Content (Centered GPT-style) -->
      <div class="{nanobot.isExpanded ? 'absolute inset-0 block overflow-hidden' : 'absolute inset-0 flex justify-center items-center overflow-hidden p-4'}">
        <!-- Voice Caption pinned to top -->
        <div class="absolute top-4 left-0 w-full flex justify-center {nanobot.isExpanded ? 'z-[2000]' : 'z-[50]'}">
          <VoiceStatusCaption {phase} />
        </div>

        {#if nanobot.vuiResponse?.data?.category === "CONTENT_CREATE" || nanobot.vuiResponse?.data?.campaign_id}
          {@const step = nanobot.vuiResponse.data.step || 1}
          <div
            class="transition-all duration-300 {nanobot.isExpanded ? 'fixed inset-0 w-screen h-screen z-[100000] m-0 rounded-none p-6 md:p-12 md:pb-24 bg-[#030712]/98 backdrop-blur-3xl pointer-events-auto' : (step >= 3 ? 'w-[98%] h-[90vh] bg-black/40 rounded-3xl p-4 mt-12 shadow-2xl animate-in fade-in zoom-in-95' : 'w-[98%] h-[90vh] custom-scrollbar p-2 mt-12 animate-in fade-in zoom-in-95')} z-50 mx-auto relative pointer-events-auto flex flex-col"
            transition:fade={{ duration: 250 }}
          >
            <ContentReviewCard
              campaign_id={nanobot.vuiResponse.data.campaign_id}
              keywords={nanobot.vuiResponse.data.keywords ||
                nanobot.vuiResponse.data.data?.keywords}
              assets={nanobot.vuiResponse.data.assets ||
                nanobot.vuiResponse.data.data?.assets}
              outline={nanobot.vuiResponse.data.outline ||
                nanobot.vuiResponse.data.data?.outline}
              draft_content={nanobot.vuiResponse.data.draft_content ||
                nanobot.vuiResponse.data.data?.draft_content}
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
