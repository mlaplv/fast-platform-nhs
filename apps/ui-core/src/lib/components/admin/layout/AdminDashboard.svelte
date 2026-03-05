<script lang="ts">
  import { type Component } from "svelte";
  import ToastNotification from "$lib/components/admin/ui/ToastNotification.svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { omni } from "$lib/state/omni.svelte";

  let { children, userEmail, isMobile } = $props<{
    children?: import("svelte").Snippet;
    userEmail?: string;
    isMobile?: boolean;
  }>();
  let innerWidth = $state(0);
  let mounted = $state(false);

  // Dynamic Components
  let LayoutComponent = $state<Component<any>>();

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

  let lastTrig = nanobot.voiceTrigger;
  $effect(() => {
    if (nanobot.voiceTrigger > lastTrig) {
      lastTrig = nanobot.voiceTrigger;
      omni.startRec();
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
      <div
        class="w-10 h-10 border-2 border-[#00FFFF]/10 border-t-[#00FFFF] rounded-full animate-spin"
      ></div>
      <span
        class="text-[10px] font-mono text-[#00FFFF]/40 uppercase tracking-[0.5em] animate-pulse"
        >Initializing OS...</span
      >
    </div>
  </div>
{/if}

<!-- Vault Modal Overlay (Highest z-index, shared) -->
<ToastNotification />
