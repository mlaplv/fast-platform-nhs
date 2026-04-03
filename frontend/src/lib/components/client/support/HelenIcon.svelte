<script lang="ts">
  const { size = 24, color = "currentColor", class: className = "", isPaused = false } = $props<{
    size?: number;
    color?: string;
    class?: string;
    isPaused?: boolean;
  }>();
</script>

<svg 
  width={size} 
  height={size} 
  viewBox="0 0 100 100" 
  fill="none" 
  xmlns="http://www.w3.org/2000/svg"
  class={className}
>
  <defs>
    <linearGradient id="helen-core-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color={color} />
      <stop offset="100%" stop-color="#005B99" />
    </linearGradient>
    
    <filter id="helen-glow-fx" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <mask id="helen-mask">
      <circle cx="50" cy="50" r="48" fill="white" />
    </mask>
  </defs>

  <!-- Neural Orbit Rings -->
  <g opacity="0.3">
    <circle cx="50" cy="50" r="42" stroke={color} stroke-width="0.5" stroke-dasharray="4 8">
      {#if !isPaused}
        <animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="20s" repeatCount="indefinite" />
      {/if}
    </circle>
    <circle cx="50" cy="50" r="36" stroke={color} stroke-width="0.5" stroke-dasharray="2 4">
      {#if !isPaused}
        <animateTransform attributeName="transform" type="rotate" from="360 50 50" to="0 50 50" dur="15s" repeatCount="indefinite" />
      {/if}
    </circle>
  </g>

  <!-- Liquid Morphing Core -->
  <g filter="url(#helen-glow-fx)" mask="url(#helen-mask)">
    <path fill="url(#helen-core-grad)" opacity="0.8">
      {#if !isPaused}
        <animate 
          attributeName="d" 
          dur="5s" 
          repeatCount="indefinite"
          values="
            M50,20 C65,20 80,35 80,50 C80,65 65,80 50,80 C35,80 20,65 20,50 C20,35 35,20 50,20;
            M50,25 C70,20 75,40 75,55 C75,70 65,75 50,75 C35,75 25,70 25,55 C25,40 30,20 50,25;
            M50,20 C65,20 80,35 80,50 C80,65 65,80 50,80 C35,80 20,65 20,50 C20,35 35,20 50,20
          "
        />
      {/if}
    </path>
    
    <!-- Central Neural Node -->
    <circle cx="50" cy="50" r="10" fill="white" opacity="0.9">
      {#if !isPaused}
        <animate attributeName="r" values="8;12;8" dur="2s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite" />
      {/if}
    </circle>
  </g>

  <!-- Synaptic Particles (Orbital) -->
  <g>
    <circle r="2" fill="white">
      {#if !isPaused}
        <animateMotion dur="4s" repeatCount="indefinite" path="M50,15 A35,35 0 1,1 50,85 A35,35 0 1,1 50,15" />
      {/if}
    </circle>
    <circle r="1.5" fill={color}>
      {#if !isPaused}
        <animateMotion dur="3s" repeatCount="indefinite" path="M85,50 A35,35 0 1,0 15,50 A35,35 0 1,0 85,50" />
      {/if}
    </circle>
  </g>
</svg>
