<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";

  // Reactive color based on Xohi status
  let color = $derived(
    nanobot.nanoBotStatus === "THINKING"
      ? "rgba(0,255,255,0.07)"
      : nanobot.nanoBotStatus === "ERROR"
        ? "rgba(255,60,60,0.05)"
        : nanobot.nanoBotStatus === "SUCCESS"
          ? "rgba(255,220,40,0.04)"
          : "rgba(0,255,255,0.035)",
  );
</script>

<!-- Ambient Xohi Brand Watermark — Always visible, non-interactive -->
<div
  class="absolute inset-0 flex items-center justify-center pointer-events-none select-none z-0 overflow-hidden"
>
  <svg
    width="280"
    height="280"
    viewBox="0 0 280 280"
    fill="none"
    class="opacity-100 transition-all duration-[2000ms]"
  >
    <!-- Outer Diamond Ring -->
    <rect
      x="140"
      y="20"
      width="170"
      height="170"
      rx="24"
      transform="rotate(45 140 140)"
      stroke={color}
      stroke-width="2"
      fill="none"
      class="transition-all duration-[2000ms]"
    />

    <!-- Inner Diamond Ring (offset) -->
    <rect
      x="140"
      y="55"
      width="120"
      height="120"
      rx="16"
      transform="rotate(45 140 140)"
      stroke={color}
      stroke-width="1.2"
      fill="none"
      opacity="0.6"
      class="transition-all duration-[2000ms]"
    />

    <!-- Central Square Core -->
    <rect
      x="115"
      y="115"
      width="50"
      height="50"
      rx="6"
      stroke={color}
      stroke-width="1.5"
      fill={color}
      fill-opacity="0.15"
      class="transition-all duration-[2000ms]"
    >
      <!-- Subtle breathing animation -->
      <animate
        attributeName="opacity"
        values="0.4;0.7;0.4"
        dur="6s"
        repeatCount="indefinite"
      />
    </rect>

    <!-- Accent Dots (corner nodes) -->
    <circle cx="140" cy="16" r="3.5" fill={color} opacity="0.5">
      <animate
        attributeName="opacity"
        values="0.3;0.7;0.3"
        dur="4s"
        repeatCount="indefinite"
      />
    </circle>
    <circle cx="264" cy="140" r="3" fill={color} opacity="0.4">
      <animate
        attributeName="opacity"
        values="0.2;0.5;0.2"
        dur="5s"
        repeatCount="indefinite"
      />
    </circle>
    <circle cx="140" cy="264" r="3.5" fill={color} opacity="0.5">
      <animate
        attributeName="opacity"
        values="0.4;0.7;0.4"
        dur="4.5s"
        repeatCount="indefinite"
      />
    </circle>
    <circle cx="16" cy="140" r="3" fill={color} opacity="0.35">
      <animate
        attributeName="opacity"
        values="0.2;0.6;0.2"
        dur="5.5s"
        repeatCount="indefinite"
      />
    </circle>

    <!-- Diagonal Cross Lines (subtle grid) -->
    <line
      x1="140"
      y1="35"
      x2="140"
      y2="65"
      stroke={color}
      stroke-width="0.5"
      opacity="0.25"
    />
    <line
      x1="140"
      y1="215"
      x2="140"
      y2="245"
      stroke={color}
      stroke-width="0.5"
      opacity="0.25"
    />
    <line
      x1="35"
      y1="140"
      x2="65"
      y2="140"
      stroke={color}
      stroke-width="0.5"
      opacity="0.25"
    />
    <line
      x1="215"
      y1="140"
      x2="245"
      y2="140"
      stroke={color}
      stroke-width="0.5"
      opacity="0.25"
    />
  </svg>
</div>
