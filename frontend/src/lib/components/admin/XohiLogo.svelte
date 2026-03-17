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

  // 2026 AI Color Palette - Minimalist & Elegant
  const theme = {
    IDLE: { core: "#00E5FF", glow: "rgba(0, 229, 255, 0.4)" },
    THINKING: { core: "#FF00FF", glow: "rgba(255, 0, 255, 0.6)" },
    SPEAKING: { core: "#00FF41", glow: "rgba(0, 255, 65, 0.6)" },
    ERROR: { core: "#FF3131", glow: "rgba(255, 49, 49, 0.6)" },
    SUCCESS: { core: "#FFD700", glow: "rgba(255, 215, 0, 0.6)" }
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
  role="presentation"
>
  <!-- SVG QUANTUM CORE (Streamlined) -->
  <svg 
    viewBox="0 0 100 100" 
    class="absolute inset-0 w-full h-full overflow-visible drop-shadow-[0_0_15px_{activeTheme.glow}]"
  >
    <!-- Neural Data Processing (Minimalist Dots) -->
    <g class="neural-processing">
      <!-- Fast Inner Particles -->
      <circle 
        cx="50" cy="50" r="42" 
        stroke={activeTheme.core} 
        stroke-width="1.5" 
        fill="none" 
        stroke-dasharray="2 15" 
        class="animate-data-flow"
        opacity="0.4"
      />
      <!-- Slow Outer Pulse Particles -->
      <circle 
        cx="50" cy="50" r="39" 
        stroke={activeTheme.core} 
        stroke-width="0.5" 
        fill="none" 
        stroke-dasharray="1 8" 
        class="animate-pulse-magnetic"
      />
    </g>

    <!-- Core Shadow -->
    <circle cx="50" cy="50" r="35" fill="black" />
  </svg>

  <!-- THE MASTER ICON (HAMSTER) -->
  <div 
    class="relative w-[70%] h-[70%] rounded-full overflow-hidden transition-all duration-700 {isHovered ? 'scale-110' : 'scale-100'}"
    style="clip-path: circle(50%)"
  >
    <img 
      src="/hamster-icon.png" 
      alt="Xohi AI" 
      class="w-full h-full object-cover {status === 'THINKING' ? 'animate-pulse contrast-125 saturate-150' : ''}"
      style="filter: drop-shadow(0 0 8px {activeTheme.glow})"
    />
  </div>

  <!-- Orbital Scanning Node (Elegant Single Point) -->
  <div class="absolute inset-0 animate-spin-slow pointer-events-none">
    <div 
      class="absolute top-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full"
      style="background: {activeTheme.core}; box-shadow: 0 0 10px {activeTheme.core}"
    ></div>
  </div>
</div>

<style>
  .animate-data-flow {
    animation: spin 8s linear infinite;
  }
  .animate-pulse-magnetic {
    animation: pulse-magnetic 4s ease-in-out infinite;
    transform-origin: center;
  }
  .animate-spin-slow {
    animation: spin 20s linear infinite;
  }

  @keyframes pulse-magnetic {
    0%, 100% { transform: scale(1); opacity: 0.1; }
    50% { transform: scale(1.05); opacity: 0.5; }
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>
