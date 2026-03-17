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
      <div class="relative w-16 h-16 flex items-center justify-center">
        <div class="absolute inset-0 border-2 border-[#00FFFF]/10 border-t-[#00FFFF] rounded-full animate-spin"></div>
        <img 
          src="/hamster-core.png" 
          alt="Xohi" 
          class="w-10 h-10 object-contain animate-pulse rounded-full"
          style="filter: drop-shadow(0 0 12px rgba(0, 255, 255, 0.4)); clip-path: circle(50%)"
        />
      </div>
      <span
        class="text-[10px] font-mono text-[#00FFFF]/40 uppercase tracking-[0.5em] animate-pulse"
        >Initializing Hamster OS...</span
      >
    </div>
  </div>
{/if}

<!-- Vault Modal Overlay (Highest z-index, shared) -->
<ToastNotification />
