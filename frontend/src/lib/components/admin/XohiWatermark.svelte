<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { vuiState } from "$lib/vui";
  import { scale, fade } from "svelte/transition";

  // Design Tokens - LUXURY DARK EDITION 2026
  const colors = {
    THINKING: "rgba(0, 255, 255, 0.4)", // Intense Cyan
    SPEAKING: "rgba(16, 185, 129, 0.4)", // Emerald Green
    LISTENING: "rgba(59, 130, 246, 0.4)", // Electric Blue
    ERROR: "rgba(239, 68, 68, 0.3)",      // Blood Red
    SUCCESS: "rgba(234, 179, 8, 0.3)",    // Gold
    IDLE: "rgba(255, 255, 255, 0.05)"     // Ghost White (ultra-subtle)
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
  let dynamicScale = $derived(1 + (phase === 'speaking' ? volume * 0.3 : phase === 'listening' ? volume * 0.05 : 0));
  let rotationSpeed = $derived(phase === 'thinking' ? '3s' : '25s');

</script>

<!-- Ambient Xohi Brand Watermark — VANTABLACK ELITE 2026 -->
<div
  class="absolute inset-0 flex items-center justify-center pointer-events-none select-none z-0 overflow-hidden bg-[#000000]/85"
>
  <div 
    class="relative flex items-center justify-center transition-all duration-1000"
    style="transform: scale({dynamicScale}); filter: drop-shadow(0 0 30px {activeColor.replace('0.4', '0.1').replace('0.3', '0.08')})"
  >
    <svg
      width="350"
      height="350"
      viewBox="0 0 280 280"
      fill="none"
      class="transition-all duration-700"
    >
      <defs>
        <!-- Thinking Scan-line Effect -->
        <linearGradient id="scan-gradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="transparent" />
          <stop offset="50%" stop-color={activeColor} stop-opacity="0.8" />
          <stop offset="100%" stop-color="transparent" />
        </linearGradient>

        <clipPath id="hamster-clip">
          <circle cx="140" cy="140" r="32" />
        </clipPath>

        <!-- Reactive Filter -->
        <filter id="hamster-reactive-filter">
          {#if phase === 'thinking' || status === 'THINKING'}
            <feColorMatrix type="saturate" values="0.2" />
            <feComponentTransfer>
               <feFuncR type="linear" slope="1.2" />
            </feComponentTransfer>
          {:else if phase === 'speaking'}
            <feComponentTransfer>
               <feFuncR type="linear" slope={1 + volume} />
               <feFuncG type="linear" slope={1 + volume} />
               <feFuncB type="linear" slope={1 + volume} />
            </feComponentTransfer>
          {/if}
        </filter>
      </defs>

      <!-- Outer Diamond Ring (Clockwise) -->
      <rect
        x="50"
        y="50"
        width="180"
        height="180"
        rx="28"
        stroke={activeColor}
        stroke-width="1.5"
        stroke-opacity="0.3"
        fill="none"
        class="transition-all duration-700 logo-ring-outer"
        style="animation: spin {rotationSpeed} cubic-bezier(0.4, 0, 0.2, 1) infinite"
      />

      <!-- Inner Diamond Ring (Counter-Clockwise) -->
      <rect
        x="75"
        y="75"
        width="130"
        height="130"
        rx="20"
        stroke={activeColor}
        stroke-width="1"
        stroke-opacity="0.2"
        fill="none"
        class="transition-all duration-1000 logo-ring-inner"
        style="animation: spin-reverse {rotationSpeed} cubic-bezier(0.4, 0, 0.2, 1) infinite"
      />

      <!-- Central Hamster Core (Reactive Edition) -->
      <g class="logo-core" transform-origin="140 140">
        <!-- Depth Ring -->
        <circle 
          cx="140" cy="140" r="38" 
          fill="black" 
          fill-opacity="0.6"
        />
        
        <!-- Glow backing -->
        <circle 
          cx="140" cy="140" r="35" 
          fill={activeColor} 
          fill-opacity="0.15"
          class="transition-all duration-500"
        />

        <image
          xlink:href="/hamster-core.png"
          x="105"
          y="105"
          width="70"
          height="70"
          clip-path="url(#hamster-clip)"
          class="transition-all duration-500"
          style="filter: url(#hamster-reactive-filter) drop-shadow(0 0 15px {activeColor})"
        />

        {#if phase === 'thinking' || status === 'THINKING'}
          <rect
            x="108" y="108" width="64" height="2"
            fill="url(#scan-gradient)"
            clip-path="url(#hamster-clip)"
          >
            <animateTransform
              attributeName="transform"
              type="translate"
              from="0 0"
              to="0 64"
              dur="2s"
              repeatCount="indefinite"
            />
          </rect>
        {/if}
        
        <!-- Luxury Border -->
        <circle 
          cx="140" cy="140" r="32" 
          stroke={activeColor} 
          stroke-width="2" 
          fill="none" 
          opacity="0.6"
          class="transition-all duration-500"
        />
      </g>

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
  /* C.O.R.E Motion Matrix: Optimized for Emotional Flow */
  .logo-ring-outer, .logo-ring-inner {
    transform-origin: 140px 140px;
    will-change: transform;
  }

  .logo-core {
    transform-origin: 140px 140px;
    animation: breathe 8s ease-in-out infinite;
  }

  @keyframes spin {
    from { transform: rotate(45deg); }
    to { transform: rotate(405deg); }
  }

  @keyframes spin-reverse {
    from { transform: rotate(45deg); }
    to { transform: rotate(-315deg); }
  }

  @keyframes breathe {
    0%, 100% { transform: scale(1); filter: brightness(1); }
    50% { transform: scale(1.08); filter: brightness(1.3); }
  }

  /* Centering Fix: Ensure we use modern flex centering and reset any legacy offsets */
  :global(.watermark-container) {
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
