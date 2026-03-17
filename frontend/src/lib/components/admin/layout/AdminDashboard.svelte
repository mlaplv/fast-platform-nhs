<script lang="ts">
  import { type Component } from "svelte";
  import ToastNotification from "$lib/components/admin/ui/ToastNotification.svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiController } from "$lib/vui";

  let { children, userEmail, isMobile } = $props<{
    children?: import("svelte").Snippet;
    userEmail?: string;
    isMobile?: boolean;
  }>();
  let innerWidth = $state(0);
  let mounted = $state(false);

  // Dynamic Components
  let LayoutComponent = $state<Component>();

  $effect(() => {
    (async () => {
      innerWidth = window.innerWidth;
      if (userEmail) {
        nanobot.setUserEmail(userEmail);
      }

      const isMobileDevice = isMobile || window.innerWidth < 768;

      if (isMobileDevice) {
        LayoutComponent = (
          await import("$lib/components/admin/layout/mobile/MobileShell.svelte")
        ).default;
      } else {
        LayoutComponent = (
          await import("$lib/components/admin/layout/DesktopLayout.svelte")
        ).default;
      }

      mounted = true;
    })();
  });

  let lastTrig = -1;
  $effect(() => {
    if (lastTrig === -1) {
      // First mount: just capture the current value, do NOT start mic
      lastTrig = nanobot.voiceTrigger;
    } else if (nanobot.voiceTrigger > lastTrig) {
      lastTrig = nanobot.voiceTrigger;
      vuiController.startRecording();
    }
  });
</script>

<svelte:window bind:innerWidth />

{#if mounted && LayoutComponent}
  <LayoutComponent>
    {#if children}
      {@render children()}
    {/if}
  </LayoutComponent>
{:else}
  <!-- Essential Base Loading (Vantablack Minimal) -->
  <div
    class="fixed inset-0 bg-[#050505] flex items-center justify-center z-[100]"
  >
    <div class="flex flex-col items-center gap-4">
      <XohiLogo size="lg" status="THINKING" />
      <span
        class="text-[10px] font-mono text-[#00FFFF]/40 uppercase tracking-[0.5em] animate-pulse"
        >Initializing Hamster OS...</span
      >
    </div>
  </div>
{/if}

<!-- Vault Modal Overlay (Highest z-index, shared) -->
<ToastNotification />
