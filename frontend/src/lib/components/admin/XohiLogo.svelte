<script lang="ts">
  /**
   * XohiLogo.svelte - DEFINITIVE BRAND UNIT 2026
   * One file. One size. One color. One vision.
   */
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { scale, fade } from "svelte/transition";
  import { vuiState } from "$lib/vui";

  let { 
    variant = "simple", // "hero" | "header" | "watermark" | "simple"
    size = 0, // override
    interactive = false,
    status = "", // override
    className = ""
  } = $props<{
    variant?: "hero" | "header" | "watermark" | "simple";
    size?: number | "sm" | "md" | "lg" | "xl" | "hero";
    interactive?: boolean;
    status?: string;
    className?: string;
  }>();

  // Unified State Mapping
  const localStatus = $derived(status || nanobot?.nanoBotStatus || "IDLE");
  const phase = $derived(vuiState.phase);
  const volume = $derived(vuiState.volume);
  const speechProb = $derived(vuiState.speechProb);

  // Standard Dimension Map
  const sizeMap = {
    hero: 240,
    watermark: 240,
    header: 36,
    simple: 80,
    sm: 32,
    md: 48,
    lg: 80,
    xl: 128
  };

  const svgSize = $derived(
    typeof size === 'number' && size > 0 ? size : (sizeMap[size] || sizeMap[variant] || 80)
  );

  // Unified Identity Color - 100% Neural Cyan (Elite Standard)
  // We use the raw RGB values to support both hex-like fill and rgba glow
  const BRAND_COLOR = "var(--color-neon-cyan-raw, 0, 229, 255)";
  const ERROR_COLOR = "var(--color-alert-red-raw, 255, 49, 49)";

  let activeColor = $derived(
    phase === 'error' || localStatus === 'ERROR' ? "#FF3131" : "#00E5FF"
  );
  
  // High-visibility Debug Color (will be removed once confirmed)
  let debugBorder = $state(false);

  // Status Animation Logic (Monochromatic but Alive)
  let rotationSpeed = $derived((phase === 'thinking' || localStatus === 'THINKING') ? '3s' : '25s');
  let dynamicScale = $derived(1 + (phase === 'speaking' ? volume * 0.2 : phase === 'listening' ? volume * 0.05 : 0));
  let glowOpacity = $derived(variant === "watermark" ? "0.15" : "0.5");

  function handleClick() {
    if (interactive || variant === "header") {
      if (localStatus === "IDLE") {
        nanobot?.startRecording();
      } else {
        nanobot?.setVuiActive(true);
      }
    }
  }
</script>

<div 
  class="relative flex items-center justify-center transition-all duration-700 {interactive || variant === 'header' ? 'cursor-pointer active:scale-95 group' : 'pointer-events-none'} {className}"
  style="width: {svgSize}px; height: {svgSize}px; transform: scale({dynamicScale});"
  onclick={handleClick}
  role="presentation"
>
  <svg
    width={svgSize}
    height={svgSize}
    viewBox="0 0 280 280"
    fill="none"
    class="transition-all duration-1000"
    style="filter: drop-shadow(0 0 {svgSize/10}px {activeColor}); opacity: {variant === 'watermark' ? 0.2 : 0.8}"
  >
    <defs></defs>

    <!-- Outer Diamond Ring -->
    <rect
      x="50" y="50" width="180" height="180" rx="28"
      stroke={activeColor}
      stroke-width={svgSize < 50 ? "4" : (variant === "hero" ? "2" : "1.5")}
      stroke-opacity={variant === "watermark" ? "0.2" : "0.5"}
      fill="none"
      class="logo-ring-outer"
      style="animation: spin {rotationSpeed} linear infinite"
    />

    <!-- Inner Diamond Ring -->
    <rect
      x="75" y="75" width="130" height="130" rx="20"
      stroke={activeColor}
      stroke-width={svgSize < 50 ? "3" : (variant === "hero" ? "1.5" : "1")}
      stroke-opacity={variant === "watermark" ? "0.15" : "0.4"}
      fill="none"
      class="logo-ring-inner"
      style="animation: spin-reverse {rotationSpeed} linear infinite"
    />

    <!-- Central Core (STATIONARY PER SẾP'S ORDER) -->
    <g class="logo-core">
      <circle cx="140" cy="140" r="38" fill="black" fill-opacity="0.8" />
      <circle cx="140" cy="140" r="35" fill={activeColor} fill-opacity={svgSize < 50 ? "0.2" : "0.1"} class:thinking-pulse={phase === 'thinking' || localStatus === 'THINKING'} />
      
      <text
        x="140" y="155"
        text-anchor="middle"
        class="font-mono font-black select-none"
        class:thinking-shimmer={phase === 'thinking' || localStatus === 'THINKING'}
        style="fill: {activeColor}; font-size: {svgSize < 50 ? '54px' : '42px'}; filter: drop-shadow(0 0 {svgSize < 50 ? '4px' : '12px'} {activeColor})"
      >
        X
      </text>

      <circle cx="140" cy="140" r="32" stroke={activeColor} stroke-width={svgSize < 50 ? "3" : "2"} fill="none" opacity="0.6" />
    </g>

    <!-- Accent Dots -->
    <g opacity={(phase !== 'idle' || localStatus !== 'IDLE') ? '1' : '0.4'}>
      <circle cx="140" cy="16" r="4" fill={activeColor}>
        <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" />
      </circle>
      <circle cx="264" cy="140" r="4" fill={activeColor} />
      <circle cx="140" cy="264" r="4" fill={activeColor} />
      <circle cx="16" cy="140" r="4" fill={activeColor} />
    </g>
  </svg>

  <!-- Status Label (Variant: Header Only) -->
  {#if variant === "header" && localStatus !== "IDLE"}
    <div
      in:scale={{ duration: 200 }}
      class="absolute -top-7 left-1/2 -translate-x-1/2 text-[7px] font-black tracking-widest uppercase whitespace-nowrap px-2 py-0.5 rounded-full bg-black/80 border border-white/10 {localStatus === 'ERROR' ? 'text-alert-red' : 'text-neon-cyan'} shadow-glow-sm"
    >
      {localStatus}
    </div>
  {/if}
</div>

<style>
  .logo-ring-outer, .logo-ring-inner {
    transform-origin: 140px 140px;
  }

  .logo-core {
    transform-origin: 140px 140px;
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
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
  }

  .thinking-shimmer {
    animation: shimmer 1.5s ease-in-out infinite;
  }

  .thinking-pulse {
    animation: thinking-pulse 2s ease-in-out infinite;
  }

  @keyframes shimmer {
    0%, 100% { opacity: 1; filter: brightness(1) drop-shadow(0 0 12px rgba(var(--color-neon-cyan-raw), 0.8)); }
    50% { opacity: 0.7; filter: brightness(1.5) drop-shadow(0 0 20px rgba(var(--color-neon-cyan-raw), 1)); }
  }

  @keyframes thinking-pulse {
    0% { opacity: 0.2; }
    50% { opacity: 0.4; }
    100% { opacity: 0.2; }
  }
</style>
