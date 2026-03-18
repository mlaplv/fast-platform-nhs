<script lang="ts">
  import { vuiState } from "$lib/vui";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import XohiLogo from "$lib/components/admin/XohiLogo.svelte";
  import { fade } from "svelte/transition";

  // Design Tokens - LUXURY DARK EDITION 2026
  // No longer needed here as XohiLogo handles color logic, 
  // but we keep the container styling.
</script>

<!-- Ambient Xohi Brand Watermark — VANTABLACK ELITE 2026 -->
<div
  class="absolute inset-0 flex items-center justify-center pointer-events-none select-none z-0 overflow-hidden bg-[#000000]/85"
  transition:fade={{ duration: 1000 }}
>
  <XohiLogo variant="watermark" size={350} />
</div>

<style>
  /* Centering Fix: Ensure we use modern flex centering and reset any legacy offsets */
  :global(.watermark-container) {
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
