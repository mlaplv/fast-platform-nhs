<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiState } from "$lib/vui";
  import { scale, fade } from "svelte/transition";

  // Design Tokens - Sync with XohiNanoSprite but optimized for watermark
  const colors = {
    THINKING: "rgba(0, 255, 255, 0.15)", // Cyan
    SPEAKING: "rgba(16, 185, 129, 0.15)", // Green
    LISTENING: "rgba(59, 130, 246, 0.15)", // Blue
    ERROR: "rgba(239, 68, 68, 0.12)",      // Red
    SUCCESS: "rgba(234, 179, 8, 0.12)",    // Yellow
    IDLE: "rgba(0, 255, 255, 0.04)"        // Default Cyan (ultra-subtle)
  };

  let phase = $derived(vuiState.phase);
  let status = $derived(nanobot.nanoBotStatus);
  let volume = $derived(vuiState.volume);

  // Determine active color based on phase or status
  let activeColor = $derived(
    phase === 'error' ? colors.ERROR :
    phase === 'thinking' ? colors.THINKING :
    phase === 'speaking' ? colors.SPEAKING :
    phase === 'listening' ? (vuiState.speechProb > 0.5 ? colors.SUCCESS : colors.LISTENING) :
    status === 'THINKING' ? colors.THINKING :
    status === 'ERROR' ? colors.ERROR :
    status === 'SUCCESS' ? colors.SUCCESS :
    colors.IDLE
  );

  // Premium Animation Scaling
  let dynamicScale = $derived(1 + (phase === 'speaking' ? volume * 0.4 : phase === 'listening' ? volume * 0.1 : 0));
  let rotationSpeed = $derived(phase === 'thinking' ? '2s' : '20s');

</script>

<!-- Ambient Xohi Brand Watermark — Enhanced 2026 Edition -->
<div
  class="absolute inset-0 flex items-center justify-center pointer-events-none select-none z-0 overflow-hidden"
>
  <div 
    class="relative flex items-center justify-center transition-all duration-1000"
    style="transform: scale({dynamicScale}); filter: drop-shadow(0 0 15px {activeColor.replace('0.15', '0.05').replace('0.12', '0.04')})"
  >
    <svg
      width="320"
      height="320"
      viewBox="0 0 280 280"
      fill="none"
      class="transition-all duration-700"
    >
      <!-- Outer Diamond Ring -->
      <rect
        x="55"
        y="55"
        width="170"
        height="170"
        rx="24"
        transform-origin="140 140"
        transform="rotate(45)"
        stroke={activeColor}
        stroke-width="2"
        fill="none"
        class="transition-all duration-700"
        style="animation: spin {rotationSpeed} linear infinite"
      />

      <!-- Inner Diamond Ring -->
      <rect
        x="80"
        y="80"
        width="120"
        height="120"
        rx="16"
        transform-origin="140 140"
        transform="rotate(45)"
        stroke={activeColor}
        stroke-width="1.2"
        fill="none"
        opacity="0.6"
        class="transition-all duration-1000"
        style="animation: spin-reverse {rotationSpeed} linear infinite"
      />

      <!-- Central Square Core -->
      <rect
        x="115"
        y="115"
        width="50"
        height="50"
        rx="8"
        stroke={activeColor}
        stroke-width="1.5"
        fill={activeColor}
        fill-opacity="0.15"
        class="transition-all duration-500"
      >
        {#if phase === 'thinking' || status === 'THINKING'}
          <animate
            attributeName="fill-opacity"
            values="0.15;0.6;0.15"
            dur="1.5s"
            repeatCount="indefinite"
          />
        {:else}
          <animate
            attributeName="fill-opacity"
            values="0.1;0.2;0.1"
            dur="4s"
            repeatCount="indefinite"
          />
        {/if}
      </rect>

      <!-- Accent Dots (Visual Nodes) -->
      <g class="transition-opacity duration-1000" opacity={phase !== 'idle' ? '0.8' : '0.4'}>
        <circle cx="140" cy="16" r="3.5" fill={activeColor}>
          <animate attributeName="opacity" values="0.3;1;0.3" dur="3s" repeatCount="indefinite" />
        </circle>
        <circle cx="264" cy="140" r="3.5" fill={activeColor}>
          <animate attributeName="opacity" values="1;0.3;1" dur="3s" repeatCount="indefinite" />
        </circle>
        <circle cx="140" cy="264" r="3.5" fill={activeColor}>
          <animate attributeName="opacity" values="0.3;1;0.3" dur="3s" repeatCount="indefinite" />
        </circle>
        <circle cx="16" cy="140" r="3.5" fill={activeColor}>
          <animate attributeName="opacity" values="1;0.3;1" dur="3s" repeatCount="indefinite" />
        </circle>
      </g>

      <!-- Connection Lines -->
      <g opacity="0.15" stroke={activeColor}>
         <line x1="140" y1="35" x2="140" y2="100" stroke-width="0.5" />
         <line x1="140" y1="180" x2="140" y2="245" stroke-width="0.5" />
         <line x1="35" y1="140" x2="100" y2="140" stroke-width="0.5" />
         <line x1="180" y1="140" x2="245" y2="140" stroke-width="0.5" />
      </g>
    </svg>
  </div>
</div>

<style>
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  @keyframes spin-reverse {
    from { transform: rotate(0deg); }
    to { transform: rotate(-360deg); }
  }

  /* Centering Fix: Ensure we use modern flex centering and reset any legacy offsets */
  :global(.watermark-container) {
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
