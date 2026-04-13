<script lang="ts">
  import ToastNotification from "$lib/components/admin/ui/ToastNotification.svelte";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { vuiController } from "$lib/vui";
  import XohiLogo from "$lib/components/admin/XohiLogo.svelte";
  import "../../../../routes/(admin)/admin.css";
  import type { Component, Snippet } from 'svelte';

  interface AdminDashboardProps {
    children?: Snippet;
    userEmail?: string;
    isMobile?: boolean;
    data?: import("../../../../routes/$types").PageData; // CNS V72.1: Optional data from parent
  }

  interface ShellProps {
    children?: Snippet;
  }

  interface ShellModule { default: Component<ShellProps> };

  import { permissionState } from "$lib/state/permissions.svelte";
  
  let { children, userEmail, isMobile }: AdminDashboardProps = $props();

  let innerWidth = $state(0);

  // Elite V2.2: Zero-Hydration aware state sync (SSOT Priority)
  const effectiveEmail = $derived(userEmail || permissionState.user);
  
  $effect(() => {
    if (effectiveEmail) {
      nanobot.setUserEmail(effectiveEmail);
    }
  });

  /**
   * ELITE V2.2: DYNAMIC SHELL RESOLUTION
   * Logic: Derived promise reacts to viewport changes while preserving code-splitting.
   */
  const isMobileDevice = $derived(isMobile || innerWidth < 768);
  
  const shellPromise = $derived.by((): Promise<ShellModule> => {
    if (isMobileDevice) {
       return import("$lib/components/admin/layout/mobile/MobileShell.svelte");
    }
    return import("$lib/components/admin/layout/DesktopLayout.svelte");
  });

  let lastTrig = $state(-1);
  $effect(() => {
    if (lastTrig === -1) {
      lastTrig = nanobot.voiceTrigger;
    } else if (nanobot.voiceTrigger > lastTrig) {
      lastTrig = nanobot.voiceTrigger;
      vuiController.startRecording();
    }
  });
</script>

<svelte:window bind:innerWidth />

{#await shellPromise}
  <!-- Essential Base Loading (Vantablack Minimal) -->
  <div
    class="fixed inset-0 bg-[#050505] flex items-center justify-center z-[var(--z-layout-header)]"
  >
    <div class="flex flex-col items-center gap-4">
      <XohiLogo size="lg" status="THINKING" />
      <span
        class="text-[10px] font-mono text-[#00FFFF]/40 uppercase tracking-[0.5em] animate-pulse"
        >Initializing Xohi OS...</span
      >
    </div>
  </div>
{:then mod}
  {@const LayoutComponent = mod.default}
  <LayoutComponent>
    {#if children}
      {@render children()}
    {/if}
  </LayoutComponent>
{:catch err}
  <div class="fixed inset-0 bg-[#050505] flex items-center justify-center z-[var(--z-vui-exit)]">
    <div class="text-red-500 font-mono text-center p-6 border border-red-500/20 bg-red-500/5 backdrop-blur-md">
      <div class="text-xs opacity-50 mb-2">[FATAL_SHELL_ERROR]</div>
      <div class="text-sm tracking-tight">{err.message}</div>
    </div>
  </div>
{/await}


<!-- Vault Modal Overlay (Highest z-index, shared) -->
<ToastNotification />
