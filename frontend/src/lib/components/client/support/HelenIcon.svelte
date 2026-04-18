<script lang="ts">
  /**
   * Helen AI Core Icon (Elite V2.2 - Tailwind 4 Optimized)
   * A mathematically centered, liquid morphing neural node.
   */
  const { size = 24, color = "currentColor", class: className = "", isPaused = false } = $props<{
    size?: number;
    color?: string;
    class?: string;
    isPaused?: boolean;
  }>();
</script>

<svg 
  viewBox="0 0 100 100" 
  fill="none" 
  xmlns="http://www.w3.org/2000/svg"
  class="inline-block align-middle antialiased {className}"
  style:width="{size}px"
  style:height="{size}px"
  style:--helen-color={color}
>
  <defs>
    <linearGradient id="helen-core-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="var(--helen-color)" />
      <stop offset="100%" stop-color="#FF8FA3" />
    </linearGradient>
    
    <filter id="helen-glow-fx" x="-25%" y="-25%" width="150%" height="150%">
      <feGaussianBlur stdDeviation="2.5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <mask id="helen-mask">
      <circle cx="50" cy="50" r="48" fill="white" />
    </mask>
  </defs>

  <!-- Neural Orbit Rings (Stable baseline) -->
  <g class="opacity-30">
    <circle cx="50" cy="50" r="42" stroke="var(--helen-color)" stroke-width="0.5" stroke-dasharray="4 8">
      {#if !isPaused}
        <animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="20s" repeatCount="indefinite" />
      {/if}
    </circle>
    <circle cx="50" cy="50" r="36" stroke="var(--helen-color)" stroke-width="0.5" stroke-dasharray="2 4">
      {#if !isPaused}
        <animateTransform attributeName="transform" type="rotate" from="360 50 50" to="0 50 50" dur="15s" repeatCount="indefinite" />
      {/if}
    </circle>
  </g>

  <!-- Liquid Morphing Core (Mathematically Balanced) -->
  <g filter="url(#helen-glow-fx)" mask="url(#helen-mask)">
    <path fill="url(#helen-core-grad)" class="opacity-85">
      {#if !isPaused}
        <animate 
          attributeName="d" 
          dur="6s" 
          repeatCount="indefinite"
          values="
            M50,20 C66,20 80,34 80,50 C80,66 66,80 50,80 C34,80 20,66 20,50 C20,34 34,20 50,20;
            M50,22 C72,18 78,38 78,50 C78,62 72,82 50,78 C28,82 22,62 22,50 C22,38 28,18 50,22;
            M50,20 C66,20 80,34 80,50 C80,66 66,80 50,80 C34,80 20,66 20,50 C20,34 34,20 50,20
          "
        />
      {/if}
    </path>
    
    <!-- Central Neural Node -->
    <circle cx="50" cy="50" r="10" fill="white" class="opacity-90">
      {#if !isPaused}
        <animate attributeName="r" values="8.5;11.5;8.5" dur="2.5s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.7;1;0.7" dur="2.5s" repeatCount="indefinite" />
      {/if}
    </circle>
  </g>

  <!-- Synaptic Particles (Symmetrical Precision) -->
  <g>
    <circle r="2" fill="white">
      {#if !isPaused}
        <animateMotion dur="4.5s" repeatCount="indefinite" path="M50,15 A35,35 0 1,1 50,85 A35,35 0 1,1 50,15" />
      {/if}
    </circle>
    <circle r="1.5" fill="var(--helen-color)">
      {#if !isPaused}
        <animateMotion dur="3.5s" repeatCount="indefinite" path="M85,50 A35,35 0 1,0 15,50 A35,35 0 1,0 85,50" />
      {/if}
    </circle>
  </g>
</svg>
