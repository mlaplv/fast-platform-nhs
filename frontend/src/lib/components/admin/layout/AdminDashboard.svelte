<script lang="ts">
  import ToastNotification from "$lib/components/admin/ui/ToastNotification.svelte";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import { vuiController } from "$lib/vui";
  import XohiLogo from "$lib/components/admin/XohiLogo.svelte";
  import "../../../../routes/(admin)/admin.css";
  import type { Component, Snippet } from 'svelte';
  import DesktopLayout from "$lib/components/admin/layout/DesktopLayout.svelte";
  import MobileShell from "$lib/components/admin/layout/mobile/MobileShell.svelte";
  import { permissionState } from "$lib/state/permissions.svelte";
  
  interface AdminDashboardProps {
    children?: Snippet;
    userEmail?: string;
    isMobile?: boolean;
    data?: import("../../../../routes/$types").PageData; // CNS V72.1: Optional data from parent
  }

  let { children, userEmail, isMobile }: AdminDashboardProps = $props();

  let innerWidth = $state(isMobile ? 375 : 1024);
  let isMounted = $state(false);

  // Elite V2.2: Zero-Hydration aware state sync (SSOT Priority)
  const effectiveEmail = $derived(userEmail || permissionState.user);
  
  $effect(() => {
    isMounted = true;
    if (effectiveEmail) {
      nanobot.setUserEmail(effectiveEmail);
    }
  });

  const isMobileDevice = $derived(isMobile || (isMounted && innerWidth < 768));

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

{#if !isMounted}
  <!-- Essential Base Loading (Vantablack Minimal) -->
  <div
    class="fixed inset-0 bg-[#050505] flex items-center justify-center z-[var(--z-layout-header)]"
  >
    <div class="flex flex-col items-center gap-4">
      <XohiLogo size="lg" status="THINKING" />
      <span
        class="text-[10px] font-mono text-[#00FFFF]/40 tracking-[0.5em] animate-pulse"
        >Initializing Xohi OS...</span
      >
    </div>
  </div>
{:else if isMobileDevice}
  <MobileShell>
    {#if children}
      {@render children()}
    {/if}
  </MobileShell>
{:else}
  <DesktopLayout>
    {#if children}
      {@render children()}
    {/if}
  </DesktopLayout>
{/if}


<!-- Vault Modal Overlay (Highest z-index, shared) -->
<ToastNotification />
