<script lang="ts">
  import { fade, scale } from "svelte/transition";

  interface Props {
    size?: "sm" | "md" | "lg" | "xl" | "hero";
    status?: "IDLE" | "THINKING" | "SPEAKING" | "ERROR" | "SUCCESS";
    interactive?: boolean;
    className?: string;
  }

  let { 
    size = "md", 
    status = "IDLE", 
    interactive = false,
    className = "" 
  }: Props = $props();

  // 2026 AI Color Palette - Vantablack Optimized
  const theme = {
    IDLE: { core: "#00E5FF", aura: "rgba(0, 229, 255, 0.2)", glow: "rgba(0, 229, 255, 0.4)" },
    THINKING: { core: "#FF00FF", aura: "rgba(255, 0, 255, 0.3)", glow: "rgba(255, 0, 255, 0.6)" },
    SPEAKING: { core: "#00FF41", aura: "rgba(0, 255, 65, 0.3)", glow: "rgba(0, 255, 65, 0.6)" },
    ERROR: { core: "#FF3131", aura: "rgba(255, 49, 49, 0.3)", glow: "rgba(255, 49, 49, 0.6)" },
    SUCCESS: { core: "#FFD700", aura: "rgba(255, 215, 0, 0.3)", glow: "rgba(255, 215, 0, 0.6)" }
  };

  const dimensions = {
    sm: "w-8 h-8",
    md: "w-12 h-12",
    lg: "w-20 h-20",
    xl: "w-32 h-32",
    hero: "w-48 h-48"
  };

  let activeTheme = $derived(theme[status] || theme.IDLE);
  let isHovered = $state(false);
</script>

<div 
  class="relative flex items-center justify-center {dimensions[size]} {className} group"
  onmouseenter={() => interactive && (isHovered = true)}
  onmouseleave={() => interactive && (isHovered = false)}
>
  <!-- NEURAL RING O (Outer Liquid) -->
  <div 
    class="absolute inset-0 rounded-full border border-white/5 transition-all duration-700 {isHovered ? 'scale-125 opacity-100' : 'scale-100 opacity-60'}"
    style="box-shadow: 0 0 40px {activeTheme.aura}; border-color: {activeTheme.core}22"
  ></div>

  <!-- SVG QUANTUM MATRIX -->
  <svg 
    viewBox="0 0 100 100" 
    class="absolute inset-0 w-full h-full drop-shadow-[0_0_15px_{activeTheme.glow}]"
  >
    <defs>
      <filter id="chromatic-glitch" x="-20%" y="-20%" width="140%" height="140%">
        <feOffset in="SourceGraphic" dx="1" dy="0" result="red" />
        <feOffset in="SourceGraphic" dx="-1" dy="0" result="blue" />
        <feBlend in="red" in2="blue" mode="screen" />
      </filter>
      
      <linearGradient id="ring-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color={activeTheme.core} stop-opacity="0.8" />
        <stop offset="100%" stop-color="transparent" />
      </linearGradient>
    </defs>

    <!-- Neural Ring Segments -->
    <g class="neural-ring {status === 'THINKING' ? 'animate-spin-fast' : 'animate-spin-slow'}">
      <circle 
        cx="50" cy="50" r="45" 
        stroke="url(#ring-grad)" 
        stroke-width="0.5" 
        fill="none" 
        stroke-dasharray="2, 5" 
      />
      <circle 
        cx="50" cy="50" r="42" 
        stroke={activeTheme.core} 
        stroke-width="1" 
        fill="none" 
        stroke-dasharray="15, 30" 
        opacity="0.4"
      />
    </g>

    <!-- Inner Core Background -->
    <circle cx="50" cy="50" r="35" fill="black" />
    <circle 
      cx="50" cy="50" r="33" 
      fill={activeTheme.core} 
      fill-opacity="0.05" 
      class="transition-all duration-1000"
    />
  </svg>

  <!-- THE MASTER ICON (HAMSTER) -->
  <div 
    class="relative w-[70%] h-[70%] rounded-full overflow-hidden transition-transform duration-500 {isHovered ? 'scale-110' : 'scale-100'}"
    style="clip-path: circle(50%)"
  >
    <img 
      src="/hamster-icon.png" 
      alt="Xohi AI" 
      class="w-full h-full object-cover {status === 'THINKING' ? 'animate-pulse contrast-125' : ''}"
      style="filter: drop-shadow(0 0 10px {activeTheme.glow})"
    />
    
    <!-- Scanning Highlight Overlay -->
    {#if status === 'THINKING'}
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-white/20 to-transparent h-4 w-full animate-scan z-10"></div>
    {/if}
  </div>

  <!-- Orbital Data Nodes -->
  <div class="absolute inset-0 animate-spin-reverse pointer-events-none opacity-40">
    <div 
      class="absolute top-0 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full"
      style="background: {activeTheme.core}; box-shadow: 0 0 8px {activeTheme.core}"
    ></div>
    <div 
      class="absolute bottom-10 right-2 w-1.5 h-1.5 rounded-full"
      style="background: {activeTheme.core}; opacity: 0.5"
    ></div>
  </div>
</div>

<style>
  .animate-spin-slow {
    animation: spin 20s linear infinite;
  }
  .animate-spin-fast {
    animation: spin 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  }
  .animate-spin-reverse {
    animation: spin-reverse 15s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  @keyframes spin-reverse {
    from { transform: rotate(360deg); }
    to { transform: rotate(0deg); }
  }

  @keyframes scan {
    0% { transform: translateY(-100%); }
    100% { transform: translateY(300%); }
  }

  .animate-scan {
    animation: scan 2s linear infinite;
  }
</style>
