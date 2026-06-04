<script lang="ts">
  import { fomoStore } from '$lib/state/commerce/fomo.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { onDestroy } from 'svelte';
  import { browser } from '$app/environment';

  const ui = getClientUi();
  const isEnabled = $derived(browser && (ui.settings?.conversions?.fomo_enabled ?? false));

  const shouldShow = $derived(isEnabled && fomoStore.isActivityVisible && fomoStore.currentActivity);

  onDestroy(() => {
    fomoStore.dispose();
  });
</script>

{#if shouldShow}
  <div
    class="tiktok-fomo-root fixed pointer-events-none"
    style="z-index: var(--z-fomo, 9999);"
    in:fly={{ x: -20, duration: 600, easing: cubicOut }}
    out:fade={{ duration: 300 }}
  >
    <div class="tiktok-fomo-pill">
      <span class="live-dot"></span>
      <div class="tiktok-fomo-text">
        {#if fomoStore.currentActivity.type === 'ORDER'}
          <span class="user-name">{fomoStore.currentActivity.name}</span>
          <span class="action-text">{fomoStore.currentActivity.action}</span>
        {:else}
          <span class="action-text">{fomoStore.currentActivity.msg}</span>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .tiktok-fomo-root {
    bottom: 220px;
    left: 12px;
  }

  .tiktok-fomo-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    background: rgba(18, 18, 20, 0.78);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 9999px;
    border: 0.5px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  }

  .live-dot {
    width: 5px;
    height: 5px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 6px #10b981;
    animation: live-pulse 2s infinite;
  }

  @keyframes live-pulse {
    0% { transform: scale(0.9); opacity: 0.8; }
    50% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 8px #10b981; }
    100% { transform: scale(0.9); opacity: 0.8; }
  }

  .tiktok-fomo-text {
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
  }

  .user-name {
    font-size: 11px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.95);
    letter-spacing: -0.01em;
  }

  .action-text {
    font-size: 11px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.95);
    letter-spacing: -0.01em;
  }
</style>
